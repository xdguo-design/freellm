import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.generate_news_article import (
    build_related_link_candidates,
    build_prompt,
    generate_article,
    main,
    published_news_ids,
    validate_article,
)

CONFIG = json.loads(Path("data/wechat-news-config.json").read_text(encoding="utf-8"))
PROVIDERS = json.loads(Path("data/providers.json").read_text(encoding="utf-8"))
REPO_ROOT = Path(".").resolve()


def _digest(items=None, **overrides):
    digest = {
        "schemaVersion": 1,
        "date": "2026-10-22",
        "windowDays": 3,
        "generatedAt": "2026-10-22T08:00:00+08:00",
        "accepted": items if items is not None else [
            {
                "newsId": "qbitai:aaa",
                "account": "量子位",
                "title": "DeepSeek 开源推理引擎，API 免费额度同步调整",
                "url": "https://mp.weixin.qq.com/s?aaa",
                "publishedAt": "2026-10-21T12:00:00+08:00",
                "description": "DeepSeek 宣布开源推理引擎，免费额度调整。",
                "matchedEntities": ["DeepSeek"],
                "matchedKeywords": ["开源", "免费"],
            },
            {
                "newsId": "xinzhiyuan:bbb",
                "account": "新智元",
                "title": "Claude Code 自产自审：九成代码不再经过人类",
                "url": "https://mp.weixin.qq.com/s?bbb",
                "publishedAt": "2026-10-21T10:00:00+08:00",
                "description": "Claude Code 新能力实测。",
                "matchedEntities": ["Claude"],
                "matchedKeywords": ["代码"],
            },
            {
                "newsId": "jiqizhixin:ccc",
                "account": "机器之心",
                "title": "OpenAI 三个神秘模型曝光",
                "url": "https://mp.weixin.qq.com/s?ccc",
                "publishedAt": "2026-10-20T20:00:00+08:00",
                "description": "红绿蓝模型浮出水面。",
                "matchedEntities": ["GPT"],
                "matchedKeywords": ["模型"],
            },
        ],
        "rejected": [],
    }
    digest.update(overrides)
    return digest


VALID_PAYLOAD = {
    "titleZh": "AI 日报：DeepSeek 开源推理引擎，Claude Code 开始自审代码",
    "summaryZh": "当日要点：DeepSeek 开源推理引擎并调整免费额度，Claude Code 具备自产自审能力，OpenAI 三个新模型曝光。",
    "items": [
        {"newsId": "qbitai:aaa", "summaryZh": "DeepSeek 宣布开源推理引擎，同时调整 API 免费额度，开发者可自行部署推理服务。", "tags": ["开源", "API"], "relatedLinks": [{"label": "免费模型目录", "url": "/models/"}]},
        {"newsId": "xinzhiyuan:bbb", "summaryZh": "实测显示 Claude Code 可以自行生成并审查代码，人工审查比例下降到约一成。", "tags": ["编程"], "relatedLinks": []},
        {"newsId": "jiqizhixin:ccc", "summaryZh": "OpenAI 内部三个代号红绿蓝的神秘模型浮出水面，定位与发布时间尚未公开。", "tags": ["模型"], "relatedLinks": [{"label": "每日发现日志", "url": "/logs/"}]},
    ],
}


def _client(payload):
    def client(prompt, config):
        return json.dumps(payload, ensure_ascii=False)
    return client


class CandidateTests(unittest.TestCase):
    def test_static_candidates_exist_and_provider_pages_are_added(self):
        digest = _digest()
        candidates = build_related_link_candidates(PROVIDERS, digest, REPO_ROOT)
        urls = {candidate["url"] for candidate in candidates}
        self.assertIn("/models/", urls)
        self.assertIn("/logs/", urls)
        self.assertTrue(all(url.startswith("/") for url in urls))
        # DeepSeek appears as a matched entity and must map to its provider page.
        self.assertTrue(any(url.startswith("/providers/") for url in urls), urls)

    def test_providers_without_pages_are_not_offered_as_candidates(self):
        digest = _digest()
        candidates = build_related_link_candidates(PROVIDERS, digest, REPO_ROOT)
        urls = {candidate["url"] for candidate in candidates}
        for provider in PROVIDERS:
            page = REPO_ROOT / "providers" / str(provider.get("id")) / "index.html"
            if not page.is_file():
                self.assertNotIn(f"/providers/{provider.get('id')}/", urls)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.items = _digest()["accepted"]
        self.candidates = build_related_link_candidates(PROVIDERS, _digest(), REPO_ROOT)

    def test_valid_payload_passes(self):
        self.assertEqual(validate_article(VALID_PAYLOAD, self.items, self.candidates, CONFIG), [])

    def test_hallucinated_news_id_is_rejected(self):
        payload = json.loads(json.dumps(VALID_PAYLOAD))
        payload["items"][0]["newsId"] = "made:up"
        errors = validate_article(payload, self.items, self.candidates, CONFIG)
        self.assertTrue(any("not in the digest" in error for error in errors))
        self.assertTrue(any("missing from the article" in error for error in errors))

    def test_hallucinated_related_link_is_rejected(self):
        payload = json.loads(json.dumps(VALID_PAYLOAD))
        payload["items"][0]["relatedLinks"] = [{"label": "外部", "url": "https://evil.example/"}]
        errors = validate_article(payload, self.items, self.candidates, CONFIG)
        self.assertTrue(any("not an allowed site page" in error for error in errors))

    def test_missing_digest_item_is_rejected(self):
        payload = json.loads(json.dumps(VALID_PAYLOAD))
        payload["items"] = payload["items"][:2]
        errors = validate_article(payload, self.items, self.candidates, CONFIG)
        self.assertTrue(any("missing from the article" in error for error in errors))

    def test_title_with_url_is_rejected(self):
        payload = json.loads(json.dumps(VALID_PAYLOAD))
        payload["titleZh"] = "看这个 https://example.com 很厉害"
        errors = validate_article(payload, self.items, self.candidates, CONFIG)
        self.assertTrue(any("must not contain URLs" in error for error in errors))

    def test_summary_length_bounds(self):
        payload = json.loads(json.dumps(VALID_PAYLOAD))
        payload["items"][0]["summaryZh"] = "太短"
        errors = validate_article(payload, self.items, self.candidates, CONFIG)
        self.assertTrue(any("summaryZh must be 20-400" in error for error in errors))


class GenerateTests(unittest.TestCase):
    def test_valid_output_copies_source_fields_from_digest(self):
        article, reason = generate_article(_digest(), CONFIG, PROVIDERS, REPO_ROOT, llm_client=_client(VALID_PAYLOAD))
        self.assertIsNotNone(article)
        self.assertEqual(reason, "")
        self.assertEqual(article["date"], "2026-10-22")
        self.assertEqual(len(article["items"]), 3)
        first = article["items"][0]
        # Source identity always comes from the digest, never from the LLM.
        self.assertEqual(first["url"], "https://mp.weixin.qq.com/s?aaa")
        self.assertEqual(first["account"], "量子位")
        self.assertEqual(first["title"], "DeepSeek 开源推理引擎，API 免费额度同步调整")
        self.assertEqual(article["digestRef"], "data/news-digest/2026-10-22.json")

    def test_already_published_items_are_excluded(self):
        article, reason = generate_article(
            _digest(),
            CONFIG,
            PROVIDERS,
            REPO_ROOT,
            llm_client=_client(VALID_PAYLOAD),
            published={"qbitai:aaa"},
        )
        self.assertIsNone(article)
        self.assertIn("after dedupe", reason)

    def test_too_few_new_items_blocks_publication(self):
        digest = _digest(items=_digest()["accepted"][:2])
        article, reason = generate_article(digest, CONFIG, PROVIDERS, REPO_ROOT, llm_client=_client(VALID_PAYLOAD))
        self.assertIsNone(article)
        self.assertIn("after dedupe", reason)

    def test_llm_failure_then_retry_success(self):
        calls = {"count": 0}

        def flaky(prompt, config):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("HTTP 500")
            return json.dumps(VALID_PAYLOAD, ensure_ascii=False)

        article, reason = generate_article(_digest(), CONFIG, PROVIDERS, REPO_ROOT, llm_client=flaky)
        self.assertIsNotNone(article)
        self.assertEqual(calls["count"], 2)

    def test_persistent_llm_failure_produces_no_article(self):
        def broken(prompt, config):
            return "not json at all"

        article, reason = generate_article(_digest(), CONFIG, PROVIDERS, REPO_ROOT, llm_client=broken)
        self.assertIsNone(article)
        self.assertIn("attempt 2", reason)

    def test_validation_failure_twice_produces_no_article(self):
        payload = json.loads(json.dumps(VALID_PAYLOAD))
        payload["items"][0]["relatedLinks"] = [{"label": "外链", "url": "https://evil.example/"}]
        article, reason = generate_article(_digest(), CONFIG, PROVIDERS, REPO_ROOT, llm_client=_client(payload))
        self.assertIsNone(article)
        self.assertIn("not an allowed site page", reason)

    def test_prompt_embeds_digest_and_candidates(self):
        candidates = build_related_link_candidates(PROVIDERS, _digest(), REPO_ROOT)
        prompt = build_prompt(CONFIG, _digest(), candidates)
        self.assertIn("qbitai:aaa", prompt)
        self.assertIn("/models/", prompt)
        self.assertIn("近 3 天", prompt)


class CliTests(unittest.TestCase):
    def test_existing_article_is_skipped_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            news_dir = Path(tmp) / "news"
            news_dir.mkdir()
            existing = news_dir / "2026-10-22.json"
            existing.write_text('{"schemaVersion": 1}', encoding="utf-8")
            digest_path = Path(tmp) / "digest.json"
            digest_path.write_text(json.dumps(_digest(), ensure_ascii=False), encoding="utf-8")
            with patch("scripts.generate_news_article.REPO_ROOT", Path(tmp).resolve()):
                exit_code = main([
                    "--digest", str(digest_path),
                    "--news-dir", str(news_dir),
                ])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(existing.read_text(encoding="utf-8")), {"schemaVersion": 1})

    def test_cli_writes_article_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            news_dir = Path(tmp) / "news"
            news_dir.mkdir()
            digest_path = Path(tmp) / "digest.json"
            digest_path.write_text(json.dumps(_digest(), ensure_ascii=False), encoding="utf-8")
            out_path = news_dir / "2026-10-22.json"
            out_path.write_text('{"schemaVersion": 1}', encoding="utf-8")
            with patch("scripts.generate_news_article.default_llm_client", _client(VALID_PAYLOAD)):
                exit_code = main([
                    "--digest", str(digest_path),
                    "--news-dir", str(news_dir),
                    "--force",
                ])
            self.assertEqual(exit_code, 0)
            record = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(record["date"], "2026-10-22")
            self.assertEqual(len(record["items"]), 3)

    def test_published_news_ids_reads_existing_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            news_dir = Path(tmp) / "news"
            news_dir.mkdir()
            (news_dir / "2026-10-21.json").write_text(json.dumps(VALID_PAYLOAD, ensure_ascii=False), encoding="utf-8")
            ids = published_news_ids(news_dir)
            self.assertEqual(ids, {"qbitai:aaa", "xinzhiyuan:bbb", "jiqizhixin:ccc"})

    def test_cli_exits_nonzero_when_llm_output_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            digest_path = Path(tmp) / "digest.json"
            digest_path.write_text(json.dumps(_digest(), ensure_ascii=False), encoding="utf-8")
            with patch("scripts.generate_news_article.default_llm_client", lambda prompt, config: "not json"):
                exit_code = main(["--digest", str(digest_path), "--news-dir", str(Path(tmp) / "news")])
            self.assertEqual(exit_code, 3)
            self.assertFalse((Path(tmp) / "news" / "2026-10-22.json").exists())

    def test_cli_exits_zero_on_a_quiet_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            digest_path = Path(tmp) / "digest.json"
            digest_path.write_text(json.dumps(_digest(items=_digest()["accepted"][:1]), ensure_ascii=False), encoding="utf-8")
            exit_code = main(["--digest", str(digest_path), "--news-dir", str(Path(tmp) / "news")])
            self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
