import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from crawler.wechat_news import (
    BEIJING,
    collect_wechat_news,
    news_id,
    parse_feed,
    parse_feed_datetime,
    validate_source_registry,
    within_window,
)

RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>测试账号</title>
    <link>https://wechat2rss.xlab.app/feed/test.xml</link>
    <description>test feed</description>
    <item>
      <title>DeepSeek 发布新模型，API 免费额度调整</title>
      <link>https://mp.weixin.qq.com/s?__biz=TEST&amp;mid=1&amp;idx=1&amp;sn=aaa</link>
      <description>DeepSeek 宣布 V4.1-Flash 上线，<b>免费</b>额度同步调整。</description>
      <pubDate>Wed, 21 Oct 2026 09:30:00 +0800</pubDate>
      <content:encoded><![CDATA[<p>正文全文……</p>]]></content:encoded>
    </item>
    <item>
      <title>重复条目应当去重</title>
      <link>https://mp.weixin.qq.com/s?__biz=TEST&amp;mid=1&amp;idx=1&amp;sn=aaa</link>
      <description>同一条链接出现两次。</description>
      <pubDate>Wed, 21 Oct 2026 09:30:00 +0800</pubDate>
    </item>
    <item>
      <title>旧闻超出时间窗</title>
      <link>https://mp.weixin.qq.com/s?__biz=TEST&amp;mid=1&amp;idx=2&amp;sn=bbb</link>
      <description>十天前的文章。</description>
      <pubDate>Sat, 10 Oct 2026 09:30:00 +0800</pubDate>
    </item>
    <item>
      <title>无链接条目应被忽略</title>
      <description>没有 link。</description>
      <pubDate>Wed, 21 Oct 2026 09:30:00 +0800</pubDate>
    </item>
  </channel>
</rss>
"""

ATOM_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>测试 Atom 账号</title>
  <entry>
    <title>开源权重模型上线 HuggingFace</title>
    <link rel="alternate" href="https://mp.weixin.qq.com/s?__biz=ATOM&amp;mid=9"/>
    <updated>2026-10-20T20:00:00+08:00</updated>
    <summary>权重已开放下载。</summary>
  </entry>
</feed>
"""

NOW = datetime(2026, 10, 22, 8, 0, 0, tzinfo=BEIJING)


class SourceRegistryTests(unittest.TestCase):
    def test_seed_registry_is_valid(self):
        sources = json.loads(Path("data/wechat-news-sources.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(sources), 8)
        self.assertEqual(validate_source_registry(sources), [])

    def test_registry_rejects_duplicate_ids_and_foreign_hosts(self):
        errors = validate_source_registry([
            {
                "id": "dup",
                "account": "账号甲",
                "feedUrl": "https://wechat2rss.xlab.app/feed/a.xml",
                "tags": [],
                "enabled": True,
            },
            {
                "id": "dup",
                "account": "账号乙",
                "feedUrl": "https://wechat2rss.xlab.app/feed/b.xml",
                "tags": [],
                "enabled": True,
            },
            {
                "id": "foreign",
                "account": "账号丙",
                "feedUrl": "https://evil.example/feed.xml",
                "tags": [],
                "enabled": True,
            },
        ])
        self.assertIn("duplicate source id: dup", errors)
        self.assertTrue(any("allowed relay host" in error for error in errors))

    def test_registry_rejects_http_and_userinfo_urls(self):
        errors = validate_source_registry([
            {"id": "a", "account": "甲", "feedUrl": "http://wechat2rss.xlab.app/feed/a.xml"},
            {"id": "b", "account": "乙", "feedUrl": "https://user:pw@wechat2rss.xlab.app/feed/b.xml"},
        ])
        self.assertEqual(len(errors), 2)


class FeedParsingTests(unittest.TestCase):
    def test_rss_items_are_normalized_and_deduplicated(self):
        items, error = parse_feed(RSS_SAMPLE, source_id="test", account="测试账号")
        self.assertEqual(error, "")
        self.assertEqual(len(items), 2)
        first = items[0]
        self.assertEqual(first["title"], "DeepSeek 发布新模型，API 免费额度调整")
        self.assertTrue(first["url"].startswith("https://mp.weixin.qq.com/s?"))
        self.assertEqual(first["publishedAt"].utcoffset(), timedelta(hours=8))
        self.assertEqual(first["account"], "测试账号")
        self.assertIn("免费", first["description"])
        self.assertNotIn("<b>", first["description"])
        self.assertEqual(first["newsId"], news_id("test", first["url"]))

    def test_atom_entries_are_supported(self):
        items, error = parse_feed(ATOM_SAMPLE, source_id="atom", account="Atom 账号")
        self.assertEqual(error, "")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://mp.weixin.qq.com/s?__biz=ATOM&mid=9")

    def test_malformed_xml_reports_error(self):
        items, error = parse_feed("<rss><channel>", source_id="test", account="测试账号")
        self.assertEqual(items, [])
        self.assertIn("malformed feed XML", error)

    def test_feed_without_entries_reports_error(self):
        items, error = parse_feed(
            '<?xml version="1.0"?><rss version="2.0"><channel><title>空</title></channel></rss>',
            source_id="test",
            account="测试账号",
        )
        self.assertEqual(items, [])
        self.assertIn("no entries", error)

    def test_parse_feed_datetime_handles_rfc2822_and_iso(self):
        self.assertEqual(
            parse_feed_datetime("Wed, 21 Oct 2026 09:30:00 +0800").isoformat(),
            "2026-10-21T09:30:00+08:00",
        )
        self.assertEqual(
            parse_feed_datetime("2026-10-20T20:00:00+08:00").isoformat(),
            "2026-10-20T20:00:00+08:00",
        )
        self.assertIsNone(parse_feed_datetime(""))
        self.assertIsNone(parse_feed_datetime("not a date"))


class WindowTests(unittest.TestCase):
    def test_items_inside_window_are_kept(self):
        self.assertTrue(within_window(datetime(2026, 10, 21, 9, 0, tzinfo=BEIJING), NOW, 3))

    def test_items_outside_window_are_dropped(self):
        self.assertFalse(within_window(datetime(2026, 10, 18, 23, 59, tzinfo=BEIJING), NOW, 3))

    def test_items_without_publish_time_are_dropped(self):
        self.assertFalse(within_window(None, NOW, 3))


class CollectTests(unittest.TestCase):
    def _sources(self):
        return [
            {"id": "a", "account": "账号甲", "feedUrl": "https://wechat2rss.xlab.app/feed/a.xml", "enabled": True},
            {"id": "b", "account": "账号乙", "feedUrl": "https://wechat2rss.xlab.app/feed/b.xml", "enabled": True},
            {"id": "c", "account": "账号丙", "feedUrl": "https://wechat2rss.xlab.app/feed/c.xml", "enabled": False},
        ]

    def test_collect_merges_sources_and_records_failures(self):
        def fake_fetch(url):
            if url.endswith("a.xml"):
                return {"status": "ok", "content": RSS_SAMPLE}
            return {"status": "failed", "reason": "HTTP 503"}

        digest = collect_wechat_news(self._sources(), fetch=fake_fetch, window_days=3, now=NOW)
        self.assertEqual(digest["schemaVersion"], 1)
        self.assertEqual(digest["windowDays"], 3)
        statuses = {row["id"]: row for row in digest["sources"]}
        self.assertEqual(statuses["a"]["status"], "ok")
        self.assertEqual(statuses["a"]["items"], 1)
        self.assertEqual(statuses["b"]["status"], "failed")
        self.assertEqual(statuses["c"]["status"], "disabled")
        self.assertEqual(len(digest["items"]), 1)
        self.assertEqual(digest["items"][0]["title"], "DeepSeek 发布新模型，API 免费额度调整")

    def test_collect_survives_a_single_malformed_feed(self):
        def fake_fetch(url):
            if url.endswith("a.xml"):
                return {"status": "ok", "content": "<rss><channel>"}
            return {"status": "ok", "content": ATOM_SAMPLE}

        digest = collect_wechat_news(self._sources(), fetch=fake_fetch, window_days=3, now=NOW)
        statuses = {row["id"]: row for row in digest["sources"]}
        self.assertEqual(statuses["a"]["status"], "parse_error")
        self.assertEqual(statuses["b"]["status"], "ok")
        self.assertEqual(len(digest["items"]), 1)

    def test_collect_rejects_oversized_feed_without_parsing(self):
        def fake_fetch(url):
            return {"status": "source_limit", "reason": "response exceeds maximum size"}

        digest = collect_wechat_news(self._sources(), fetch=fake_fetch, window_days=3, now=NOW)
        self.assertTrue(all(row["status"] == "source_limit" for row in digest["sources"] if row["id"] != "c"))
        self.assertEqual(digest["items"], [])

    @patch("crawler.wechat_news.fetch_public_text_resource")
    def test_default_fetcher_uses_polite_bounded_fetch(self, fetch_text):
        fetch_text.return_value = {"status": "ok", "content": ATOM_SAMPLE}
        sources = [{"id": "a", "account": "账号甲", "feedUrl": "https://wechat2rss.xlab.app/feed/a.xml", "enabled": True}]
        digest = collect_wechat_news(sources, window_days=3, now=NOW)
        self.assertEqual(fetch_text.call_args.kwargs["max_bytes"], 4_000_000)
        self.assertEqual(fetch_text.call_args.args[1], ["wechat2rss.xlab.app"])
        self.assertEqual(len(digest["items"]), 1)


if __name__ == "__main__":
    unittest.main()
