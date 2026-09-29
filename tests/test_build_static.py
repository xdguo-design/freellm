import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_static import build, update_trust_copy


class BuildStaticTests(unittest.TestCase):
    def test_trust_copy_distinguishes_source_and_verification_status(self):
        rendered = update_trust_copy("每日核验 · 真实免费 / 通过人工核验，确认可免费使用")
        self.assertIn("官方来源 · 条件透明", rendered)
        self.assertIn("显示官方条件与最近核验日期", rendered)
        self.assertNotIn("每日核验 · 真实免费", rendered)

    def test_build_renders_current_count_static_offer_and_detail_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            html_path = root / "index.html"
            offer = {
                "id": "x", "order": 1, "date": "2026-09-06", "name": "X",
                "provider": "X", "model": "X", "type": ["free"],
                "productType": "api", "freeMechanism": "permanent",
                "freeSummary": "每月免费额度", "validitySummary": "长期",
                "accessSummary": "全球", "title": "X", "why": "x",
                "mechanism": "x", "validity": "x", "access": "x",
                "command": "x", "register": "https://example.com",
                "links": [["官方", "https://example.com"]],
                "sourceUrls": ["https://example.com"], "evidence": "x",
                "status": "verified", "confidence": "high",
                "lastVerifiedAt": "2026-09-06",
            }
            data_path.write_text(json.dumps([offer]), encoding="utf-8")
            html_path.write_text(
                '<b id="heroCount">27</b>'
                '<b data-category-count="all">27</b>'
                '<div id="catalog-offer-rows"></div>'
                '<script type="application/json" id="offer-data">[]</script>'
                '<script type="application/ld+json" id="ld-dynamic">'
                '{"@graph":[{"itemListElement":[]}]}</script>',
                encoding="utf-8",
            )

            self.assertTrue(build(data_path, html_path))
            rendered = html_path.read_text(encoding="utf-8")

            self.assertIn('<b id="heroCount">1</b>', rendered)
            self.assertIn('<b data-category-count="all">1</b>', rendered)
            self.assertIn('href="/offers/x/"', rendered)
            self.assertIn('"url": "https://freellm.top/offers/x/"', rendered)

    def test_build_writes_external_offer_bundle_and_removes_legacy_inline_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            html_path = root / "index.html"
            data_path.write_text(json.dumps([{
                "id": "x", "order": 1, "date": "2026-09-06", "name": "X", "provider": "X", "model": "X", "type": ["free"], "productType": "api", "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing", "accessSummary": "global", "title": "X", "why": "x", "mechanism": "x", "validity": "x", "access": "x", "command": "x", "register": "https://example.com", "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"], "evidence": "x", "status": "verified", "confidence": "high", "lastVerifiedAt": "2026-09-06"
            }]), encoding="utf-8")
            html_path.write_text('<script type="application/json" id="offer-data">\n[]\n</script>', encoding="utf-8")
            self.assertTrue(build(data_path, html_path))
            rendered = html_path.read_text(encoding="utf-8")
            bundle = data_path.with_suffix(".js").read_text(encoding="utf-8")
            self.assertNotIn('id="offer-data"', rendered)
            self.assertIn('"id":"x"', bundle)
            self.assertTrue(bundle.startswith("window.FREELLM_OFFERS = "))

    def test_static_catalog_pins_key_offers_first_and_renders_marks(self):
        from scripts.build_static import render_static_catalog

        def offer(offer_id, order, **extra):
            base = {
                "id": offer_id, "order": order, "date": "2026-09-06", "name": offer_id,
                "provider": "P", "model": "M", "type": ["free"], "productType": "api",
                "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing",
                "accessSummary": "global", "title": offer_id, "why": "x", "mechanism": "x",
                "validity": "x", "access": "x", "command": "x", "register": "https://example.com",
                "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"],
                "evidence": "x", "status": "verified", "confidence": "high",
                "lastVerifiedAt": "2026-09-06",
            }
            base.update(extra)
            return base

        data = [
            offer("plain", 1),
            offer("keyed", 2, key=True),
            offer("cn-twin", 3, key=True, editions=["cn", "intl"], editionOf="cn", siblingEditionId="intl-twin"),
            offer("intl-twin", 4, editions=["cn", "intl"], editionOf="intl", siblingEditionId="cn-twin",
                  handsOn={"testedAt": "2026-09-15", "note": "实测通过"}),
            offer("dual-entry", 5, editions=["cn", "intl"], handsOn={"testedAt": "2026-09-15", "note": "x"}),
        ]
        rendered = render_static_catalog(data)

        self.assertLess(rendered.index('data-detail="keyed"'), rendered.index('data-detail="plain"'))
        self.assertLess(rendered.index('data-detail="cn-twin"'), rendered.index('data-detail="plain"'))
        self.assertIn("★ 重点", rendered)
        self.assertIn("国内版", rendered)
        self.assertIn("国际版", rendered)
        self.assertIn("国内+国际双入口", rendered)
        self.assertIn('href="/offers/intl-twin/"', rendered)
        self.assertIn("也有国际版", rendered)
        self.assertIn("也有国内版", rendered)
        self.assertIn("✓ 实测好用", rendered)

    def test_build_injects_latest_daily_log_date_and_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            log_dir = root / "daily-log"
            html_path = root / "index.html"
            offer = {"id": "x", "order": 1, "date": "2026-09-06", "name": "X", "provider": "X", "model": "X", "type": ["free"], "productType": "api", "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing", "accessSummary": "global", "title": "X", "why": "x", "mechanism": "x", "validity": "x", "access": "x", "command": "x", "register": "https://example.com", "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"], "evidence": "x", "status": "verified", "confidence": "high", "lastVerifiedAt": "2026-09-06"}
            data_path.write_text(json.dumps([offer]), encoding="utf-8")
            log_dir.mkdir()
            (log_dir / "2026-09-10.json").write_text(json.dumps({"date": "2026-09-10", "events": [{"eventType": "new"}]}), encoding="utf-8")
            html_path.write_text('<span>▣ &nbsp;2026 年 9 月 7 日</span><script type="application/json" id="offer-data">[]</script><script type="application/ld+json" id="ld-dynamic">{"@graph":[{}]}</script>', encoding="utf-8")
            self.assertTrue(build(data_path, html_path))
            rendered = html_path.read_text(encoding="utf-8")
            self.assertIn("2026 年 9 月 10 日", rendered)
            self.assertIn('href="/logs/"', rendered)

    def test_build_injects_dynamic_daily_update_badge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            log_dir = root / "daily-log"
            html_path = root / "index.html"
            offer = {"id": "x", "order": 1, "date": "2026-09-06", "name": "X", "provider": "X", "model": "X", "type": ["free"], "productType": "api", "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing", "accessSummary": "global", "title": "X", "why": "x", "mechanism": "x", "validity": "x", "access": "x", "command": "x", "register": "https://example.com", "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"], "evidence": "x", "status": "verified", "confidence": "high", "lastVerifiedAt": "2026-09-06"}
            data_path.write_text(json.dumps([offer]), encoding="utf-8")
            log_dir.mkdir()
            (log_dir / "2026-09-10.json").write_text(json.dumps({
                "date": "2026-09-10",
                "events": [{"eventType": "new"}],
                "curatedEvents": [{"eventType": "new"}, {"eventType": "recovered"}],
            }), encoding="utf-8")
            html_path.write_text('<span>▣ &nbsp;2026 年 9 月 7 日</span><span id="daily-log-badge" data-new-count="0" data-change-count="0">今日有更新</span><script type="application/json" id="offer-data">[]</script><script type="application/ld+json" id="ld-dynamic">{"@graph":[{}]}</script>', encoding="utf-8")

            self.assertTrue(build(data_path, html_path))
            rendered = html_path.read_text(encoding="utf-8")
            self.assertIn('id="daily-log-badge" data-new-count="2" data-change-count="3">新增 2 项</span>', rendered)


    def test_build_emits_ranked_runtime_data_when_ranking_artifact_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            html_path = root / "index.html"

            def offer(offer_id, order):
                return {
                    "id": offer_id, "order": order, "date": "2026-09-01", "name": offer_id,
                    "provider": "Example", "model": offer_id, "type": ["free"], "productType": "api",
                    "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing",
                    "accessSummary": "global", "title": offer_id, "why": "x", "mechanism": "x",
                    "validity": "x", "access": "x", "command": "x", "register": "https://example.com",
                    "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"],
                    "evidence": "x", "status": "verified", "confidence": "high",
                    "lastVerifiedAt": "2026-09-01",
                }

            data_path.write_text(json.dumps([offer("old-first", 1), offer("ranked-first", 2)]), encoding="utf-8")
            (root / "ranked-offers.json").write_text(json.dumps({
                "version": 1,
                "asOf": "2026-09-22",
                "items": [
                    {
                        "rank": 1, "id": "ranked-first", "rankingScore": 88.5,
                        "components": {"freshnessScore": 100}, "penaltyScore": 0,
                        "penalties": [], "manualBoost": 0, "pinned": False,
                    },
                    {
                        "rank": 2, "id": "old-first", "rankingScore": 55.0,
                        "components": {"freshnessScore": 20}, "penaltyScore": 0,
                        "penalties": [], "manualBoost": 0, "pinned": False,
                    },
                ],
            }), encoding="utf-8")
            html_path.write_text(
                '<body><div id="catalog-offer-rows"></div>'
                '<script type="application/ld+json" id="ld-dynamic">'
                '{"@graph":[{"itemListElement":[]}]}</script></body>',
                encoding="utf-8",
            )

            self.assertTrue(build(data_path, html_path))

            ranked = json.loads((root / "offers-ranked.json").read_text(encoding="utf-8"))
            self.assertEqual([item["id"] for item in ranked], ["ranked-first", "old-first"])
            self.assertEqual([item["order"] for item in ranked], [1, 2])
            self.assertEqual(ranked[0]["sourceOrder"], 2)
            self.assertEqual(ranked[0]["rankingScore"], 88.5)
            self.assertEqual(ranked[0]["ranking"]["asOf"], "2026-09-22")

            bundle = (root / "offers.js").read_text(encoding="utf-8")
            self.assertLess(bundle.index('"id":"ranked-first"'), bundle.index('"id":"old-first"'))
            rendered = html_path.read_text(encoding="utf-8")
            self.assertIn('data-offers-url="../data/offers-ranked.json"', rendered)

    def test_build_rejects_stale_ranking_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            html_path = root / "index.html"
            offer = {
                "id": "current", "order": 1, "date": "2026-09-01", "name": "current",
                "provider": "Example", "model": "current", "type": ["free"], "productType": "api",
                "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing",
                "accessSummary": "global", "title": "current", "why": "x", "mechanism": "x",
                "validity": "x", "access": "x", "command": "x", "register": "https://example.com",
                "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"],
                "evidence": "x", "status": "verified", "confidence": "high",
                "lastVerifiedAt": "2026-09-01",
            }
            data_path.write_text(json.dumps([offer]), encoding="utf-8")
            (root / "ranked-offers.json").write_text(json.dumps({
                "version": 1, "asOf": "2026-09-22",
                "items": [{"rank": 1, "id": "stale", "rankingScore": 50}],
            }), encoding="utf-8")
            html_path.write_text("<body></body>", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "does not match offers data"):
                build(data_path, html_path)


if __name__ == "__main__":
    unittest.main()
