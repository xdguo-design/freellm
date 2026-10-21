import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from crawler.wechat_relevance import (
    BEIJING,
    build_relevant_digest,
    digest_is_publishable,
    extract_site_entities,
    load_config,
    score_item,
)

CONFIG = load_config("data/wechat-news-config.json")

PROVIDERS = [
    {"id": "deepseek", "name": "DeepSeek", "aliases": ["深度求索"]},
    {"id": "zhipu", "name": "Zhipu AI", "aliases": ["智谱", "GLM"]},
]
MODELS = [
    {"providerId": "deepseek", "provider": "DeepSeek", "model": "DeepSeek V4.1 Flash"},
    {"providerId": "zhipu", "provider": "Zhipu AI", "model": "GLM-5.3"},
]


def _item(**overrides):
    item = {
        "newsId": "src:abc",
        "sourceId": "src",
        "account": "测试账号",
        "title": "",
        "url": "https://mp.weixin.qq.com/s?abc",
        "publishedAt": "2026-10-21T09:00:00+08:00",
        "description": "",
    }
    item.update(overrides)
    return item


def _raw(items, **overrides):
    raw = {
        "schemaVersion": 1,
        "generatedAt": "2026-10-22T08:00:00+08:00",
        "windowDays": 3,
        "sources": [{"id": "src", "status": "ok", "items": len(items)}],
        "items": items,
    }
    raw.update(overrides)
    return raw


class EntityExtractionTests(unittest.TestCase):
    def test_entities_come_from_providers_models_and_extras(self):
        entities = extract_site_entities(MODELS, PROVIDERS, ["ChatGPT"])
        self.assertIn("DeepSeek", entities)
        self.assertIn("深度求索", entities)
        self.assertIn("GLM", entities)
        self.assertIn("GLM-5.3", entities)
        self.assertIn("DeepSeek V4.1 Flash", entities)
        self.assertIn("DeepSeek", entities)  # family name from model title
        self.assertIn("ChatGPT", entities)

    def test_short_and_numeric_names_are_dropped(self):
        entities = extract_site_entities(
            [{"provider": "12", "model": "ab"}],
            [{"name": "xy", "aliases": ["123"]}],
        )
        self.assertEqual(entities, [])

    def test_seed_config_is_complete(self):
        self.assertEqual(CONFIG["schemaVersion"], 1)
        self.assertGreaterEqual(len(CONFIG["topicKeywords"]), 20)
        self.assertGreaterEqual(len(CONFIG["blacklistKeywords"]), 10)
        self.assertGreaterEqual(len(CONFIG["extraEntities"]), 20)
        self.assertIn("{digest_json}", CONFIG["promptTemplate"])


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.entities = extract_site_entities(MODELS, PROVIDERS, CONFIG["extraEntities"])

    def test_entity_hit_passes_threshold(self):
        verdict = score_item(_item(title="DeepSeek 发布 V4.1，编程能力提升"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "accept")
        self.assertIn("DeepSeek", verdict["matchedEntities"])
        self.assertGreaterEqual(verdict["score"], 3)

    def test_two_keywords_pass_without_entity(self):
        verdict = score_item(_item(title="某厂商宣布免费 API 额度调整", description="新的定价与免费额度细则"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "accept")
        self.assertGreaterEqual(len(verdict["matchedKeywords"]), 2)

    def test_single_keyword_is_rejected(self):
        verdict = score_item(_item(title="一场关于 Agent 的圆桌交流"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "reject")
        self.assertEqual(verdict["reason"], "below_threshold")

    def test_blacklist_rejects_even_with_entity_and_keywords(self):
        verdict = score_item(_item(title="DeepSeek 团队招聘资深工程师，免费内推"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "reject")
        self.assertTrue(verdict["reason"].startswith("blacklist:"))

    def test_car_and_conference_noise_is_rejected(self):
        verdict = score_item(_item(title="轻舟智航城市NOA击穿10-20万体验天花板，4个月9款车落地"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "reject")
        verdict = score_item(_item(title="量子位MEET2027智能未来大会启动，年度榜单征集进行中"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "reject")

    def test_entity_matching_is_case_insensitive(self):
        verdict = score_item(_item(title="chatgpt 免费版调整思考能力"), self.entities, CONFIG)
        self.assertEqual(verdict["decision"], "accept")
        self.assertIn("ChatGPT", verdict["matchedEntities"])


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.entities = extract_site_entities(MODELS, PROVIDERS, CONFIG["extraEntities"])

    def test_digest_splits_accepted_and_rejected_with_stats(self):
        raw = _raw([
            _item(newsId="a:1", title="DeepSeek 开源推理引擎，API 免费额度同步调整"),
            _item(newsId="b:1", title="某团队招聘内推"),
            _item(newsId="c:1", title="与站点无关的财经消息"),
        ])
        digest = build_relevant_digest(raw, self.entities, CONFIG)
        self.assertEqual(digest["date"], "2026-10-22")
        self.assertEqual(digest["stats"], {"collected": 3, "accepted": 1, "rejected": 2})
        self.assertEqual(digest["accepted"][0]["newsId"], "a:1")
        self.assertEqual(digest["sourceHealth"], {"ok": 1, "failed": 0, "disabled": 0})

    def test_digest_records_failed_sources(self):
        raw = _raw([], sources=[{"id": "a", "status": "failed"}, {"id": "b", "status": "disabled"}])
        digest = build_relevant_digest(raw, self.entities, CONFIG)
        self.assertEqual(digest["sourceHealth"], {"ok": 0, "failed": 1, "disabled": 1})

    def test_publishable_requires_minimum_items(self):
        self.assertEqual(digest_is_publishable({"accepted": []}, CONFIG), (False, "no relevant news in window"))
        self.assertEqual(
            digest_is_publishable({"accepted": [1, 2]}, CONFIG),
            (False, "only 2 relevant item(s), need at least 3"),
        )
        ok, reason = digest_is_publishable({"accepted": [1, 2, 3]}, CONFIG)
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_accepted_items_are_capped_but_stay_chronological(self):
        config = dict(CONFIG, maxAcceptedItems=2)
        raw = _raw([
            _item(newsId="a:1", title="DeepSeek 发布新模型 API 免费", publishedAt="2026-10-20T09:00:00+08:00"),
            _item(newsId="a:2", title="Kimi 上下文调整 发布", publishedAt="2026-10-21T09:00:00+08:00"),
            _item(newsId="a:3", title="智谱 GLM 上线 免费额度", publishedAt="2026-10-19T09:00:00+08:00"),
        ])
        # a:3 matches two entities and scores highest; a:1 beats a:2 on score.
        digest = build_relevant_digest(raw, self.entities, config)
        self.assertEqual([row["newsId"] for row in digest["accepted"]], ["a:1", "a:3"])


if __name__ == "__main__":
    unittest.main()
