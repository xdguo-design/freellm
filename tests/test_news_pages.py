import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_seo_pages import (
    NEWS_PAGE_PATH,
    _load_news,
    _visual_section_for_path,
    news_url,
    render_feed,
    render_news_article_page,
    render_news_index_page,
    sitemap_section_paths,
)

SITE_URL = "https://freellm.top"

RECORD = {
    "schemaVersion": 1,
    "date": "2026-10-22",
    "titleZh": "AI 日报：DeepSeek 开源推理引擎，Claude Code 开始自审代码",
    "summaryZh": "今日要点：DeepSeek 开源推理引擎并调整 API 免费额度；Claude Code 具备自产自审能力。",
    "items": [
        {
            "newsId": "xixiaoyao:111",
            "title": "刚刚，DeepSeek又掀桌了！开源推理引擎",
            "account": "夕小瑶科技说",
            "publishedAt": "2026-10-20T19:03:00+08:00",
            "url": "https://mp.weixin.qq.com/s?__biz=TESTA&mid=1&idx=1&sn=aaa",
            "summaryZh": "DeepSeek 开源推理引擎，官方称同等硬件下吞吐显著提升，并同步调整 API 免费额度。",
            "tags": ["开源", "API"],
            "relatedLinks": [{"label": "免费模型目录", "url": "/models/"}],
        },
        {
            "newsId": "xinzhiyuan:222",
            "title": "Claude Code「自产自审」：九成代码不再经过人类",
            "account": "新智元",
            "publishedAt": "2026-10-21T09:10:00+08:00",
            "url": "https://mp.weixin.qq.com/s?__biz=TESTB&mid=2&idx=1&sn=bbb",
            "summaryZh": "报道称 Claude Code 新流程可以自行生成并审查代码，人工审查比例下降到约一成。",
            "tags": ["编程"],
            "relatedLinks": [],
        },
    ],
    "digestRef": "data/news-digest/2026-10-22.json",
    "generatedBy": "deepseek-ai/DeepSeek-V3",
    "createdAt": "2026-10-22T00:05:00+08:00",
}


class NewsUrlTests(unittest.TestCase):
    def test_news_url_uses_the_record_date(self):
        self.assertEqual(news_url(RECORD), "/news/2026-10-22/")
        self.assertEqual(NEWS_PAGE_PATH, "/news/")

    def test_news_section_is_mapped_for_navigation(self):
        self.assertEqual(_visual_section_for_path(Path("news/index.html")), "news")
        self.assertEqual(_visual_section_for_path(Path("news/2026-10-22/index.html")), "news")


class NewsLoaderTests(unittest.TestCase):
    def test_loader_reads_records_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "news").mkdir()
            (data_dir / "news" / "2026-10-21.json").write_text(json.dumps(dict(RECORD, date="2026-10-21"), ensure_ascii=False), encoding="utf-8")
            (data_dir / "news" / "2026-10-22.json").write_text(json.dumps(RECORD, ensure_ascii=False), encoding="utf-8")
            (data_dir / "news" / "notes.json").write_text('{"no": "date"}', encoding="utf-8")
            records = _load_news(data_dir / "offers.json")
            self.assertEqual([record["date"] for record in records], ["2026-10-22", "2026-10-21"])

    def test_loader_tolerates_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_load_news(Path(tmp) / "offers.json"), [])


class NewsArticleRenderTests(unittest.TestCase):
    def setUp(self):
        self.html = render_news_article_page(RECORD, SITE_URL)

    def test_article_carries_indexable_seo_metadata(self):
        self.assertIn("<title>AI 日报：DeepSeek 开源推理引擎，Claude Code 开始自审代码 · FreeLLM</title>", self.html)
        self.assertIn('<link rel="canonical" href="https://freellm.top/news/2026-10-22/">', self.html)
        self.assertIn('content="index,follow,max-image-preview:large"', self.html)
        self.assertEqual(len(re.findall(r"<h1", self.html)), 1)

    def test_article_declares_news_article_structured_data(self):
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', self.html, re.S)
        self.assertIsNotNone(match)
        schema = json.loads(match.group(1))
        self.assertEqual(schema["@type"], "NewsArticle")
        self.assertEqual(schema["url"], "https://freellm.top/news/2026-10-22/")
        self.assertEqual(schema["author"]["name"], "FreeLLM")

    def test_each_item_links_back_to_its_origin(self):
        self.assertEqual(self.html.count("mp.weixin.qq.com"), 2)
        self.assertEqual(self.html.count('rel="nofollow noopener"'), 2)
        self.assertIn("夕小瑶科技说", self.html)
        self.assertIn("2026-10-20 19:03", self.html)
        self.assertIn('class="news-tag">开源</span>', self.html)

    def test_related_links_stay_on_site(self):
        self.assertIn('class="news-related"', self.html)
        self.assertIn('href="https://freellm.top/models/"', self.html)

    def test_adsense_and_source_disclosure_are_present(self):
        self.assertIn("adsbygoogle", self.html)
        self.assertIn("不构成全文转载", self.html)
        self.assertIn("deepseek-ai/DeepSeek-V3", self.html)


class NewsIndexRenderTests(unittest.TestCase):
    def test_index_lists_articles_newest_first(self):
        older = dict(RECORD, date="2026-10-21", titleZh="AI 日报：前一天的要点汇总内容")
        html = render_news_index_page([older, RECORD], SITE_URL)
        self.assertIn("/news/2026-10-22/", html)
        self.assertIn("/news/2026-10-21/", html)
        self.assertLess(html.index("/news/2026-10-22/"), html.index("/news/2026-10-21/"))
        self.assertIn("2 期日报", html)
        self.assertIn('content="index,follow,max-image-preview:large"', html)

    def test_empty_index_is_noindex_and_carries_no_ads(self):
        html = render_news_index_page([], SITE_URL)
        self.assertIn('content="noindex,follow"', html)
        self.assertNotIn("adsbygoogle", html)
        self.assertIn("日报即将开始", html)


class NewsSitemapAndFeedTests(unittest.TestCase):
    def test_sitemap_section_only_exists_with_articles(self):
        with_news = sitemap_section_paths([], [], models=[], providers=[], news=[RECORD])
        self.assertEqual(with_news["news"], ["/news/", "/news/2026-10-22/"])
        without_news = sitemap_section_paths([], [], models=[], providers=[], news=[])
        self.assertEqual(without_news["news"], [])

    def test_feed_includes_news_entries(self):
        feed = render_feed([], SITE_URL, [], [RECORD])
        self.assertIn("https://freellm.top/news/2026-10-22/", feed)
        self.assertIn("AI 日报：DeepSeek 开源推理引擎", feed)

    def test_feed_without_news_is_unchanged(self):
        feed = render_feed([], SITE_URL, [], [])
        self.assertNotIn("/news/", feed)


class BuildIntegrationTests(unittest.TestCase):
    def test_build_renders_news_pages_with_shared_chrome(self):
        import scripts.build_seo_pages as seo

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with patch.object(seo, "_load_news", return_value=[RECORD]):
                seo.build_site(Path("data/offers.json"), output, site_url=SITE_URL)
            index = (output / "news" / "index.html").read_text(encoding="utf-8")
            article = (output / "news" / "2026-10-22" / "index.html").read_text(encoding="utf-8")
            # The rail contract stays untouched (no ninth entry); /news/ is
            # reachable from the daily-log hero, the sitemap and the feed.
            for page in (index, article):
                self.assertIn('class="fl-site-rail"', page)
                self.assertIn("/js/site-navigation.js", page)
                self.assertIn("/css/freellm-pastel-ui.css", page)
                self.assertEqual(re.findall(r'<nav class="fl-site-nav">(.*?)</nav>', page, re.S)[0].count("<a "), 8)
            logs = (output / "logs" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="https://freellm.top/news/"', logs)
            sitemap = (output / "sitemap-news.xml").read_text(encoding="utf-8")
            self.assertIn("https://freellm.top/news/2026-10-22/", sitemap)
            index_sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("sitemap-news.xml", index_sitemap)


if __name__ == "__main__":
    unittest.main()
