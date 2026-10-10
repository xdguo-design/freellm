"""Regression guards for the 2026-10-09 FreeLLM UX / daily-update audit.

These tests check repository artifacts. They complement, but cannot replace,
real desktop/mobile screenshot testing on a deployed preview.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AuditRegressions(unittest.TestCase):
    def test_legacy_update_route_redirects(self):
        redirects = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))["redirects"]
        mapping = {item["source"]: item for item in redirects}
        for path, target in (
            ("/updates", "/logs/"),
            ("/updates/", "/logs/"),
            ("/en/updates", "/en/logs/"),
            ("/en/updates/", "/en/logs/"),
        ):
            self.assertEqual(mapping[path]["destination"], target)
            self.assertTrue(mapping[path]["permanent"])

    def test_workflow_search_and_mobile_title_have_strong_overrides(self):
        css = (ROOT / "css/primary-menu.css").read_text(encoding="utf-8")
        patch = css.split("/* UX-20261009-P0: workflow", 1)[1]
        self.assertIn(".ref-topbar.ref-topbar.ref-topbar", patch)
        self.assertIn("background: rgba(255,255,255,.98) !important", patch)
        self.assertIn(".ref-search.ref-search.ref-search", patch)
        self.assertIn("background: #fff !important", patch)
        self.assertIn("@media (max-width: 700px)", patch)
        self.assertIn("white-space: normal !important", patch)
        self.assertIn("height: auto !important", patch)
        self.assertIn("padding-right: 18px !important", patch)
        self.assertIn(".lab-hero::after", patch)

    def test_red_dot_requires_unread_update(self):
        script = (ROOT / "js/site-navigation.js").read_text(encoding="utf-8")
        self.assertIn("freellm-last-read-update", script)
        self.assertIn("getLastReadUpdate() !== lastUpdateDate", script)
        self.assertIn("markUpdateRead()", script)

    def test_manual_discovery_preserves_scan_provenance(self):
        discovery = json.loads((ROOT / "data/daily-log/2026-10-09.json").read_text(encoding="utf-8"))
        self.assertEqual(discovery["date"], "2026-10-09")
        # This merged release contains both the actual Oct 9 scan and manually
        # curated discoveries. Keep them distinct while retaining both sources.
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        self.assertEqual(discovery["initialized"]["models"], summary["scanRunToday"])
        self.assertEqual(discovery["initialized"]["offers"], summary["scanRunToday"])
        # The Oct 9 record is historical; compare its observations to that
        # dated snapshot instead of today's rolling summary.
        self.assertEqual(len(discovery["observed"]["models"]), 244)
        self.assertEqual(len(discovery["observed"]["offers"]), 70)
        latest_scan = json.loads((ROOT / "data/daily-log/2026-10-10.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["snapshotDate"], latest_scan["date"])
        self.assertEqual(len(latest_scan["observed"]["models"]), summary["models"])
        self.assertEqual(len(latest_scan["observed"]["offers"]), summary["offers"])
        entries = [event for event in discovery["curatedEvents"] if event["id"] == "phanthycode-free-trial"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["eventType"], "new")
        self.assertIn("待实测", entries[0]["title"])
        queue = json.loads((ROOT / "data/review-queue.json").read_text(encoding="utf-8"))
        matching = [item for item in queue if item["id"] == "phanthycode-free-trial"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["catalogStatus"], "draft")
        self.assertIsNone(matching[0]["apiEndpoint"])
        source = (ROOT / "scripts/build_seo_pages.py").read_text(encoding="utf-8")
        self.assertIn("def _latest_scanned_log(", source)
        self.assertIn('"snapshotDate": str(latest_scanned_log.get("date") or "")', source)
        self.assertIn('snapshot = _log_snapshot(day_scan)', source)

    def test_homepage_progressive_list_preserves_search(self):
        script = (ROOT / "js/homepage.js").read_text(encoding="utf-8")
        html = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        self.assertIn("HOME_OFFERS_PAGE_SIZE = 24", script)
        self.assertIn("rows.forEach(row => {", script)
        self.assertIn("matchedRows.slice(0, visibleOfferLimit)", script)
        self.assertIn("offerGrid.replaceChildren(...visibleCards)", script)
        self.assertIn("loadMoreOffersButton.addEventListener('click'", script)
        self.assertIn("rows.sort((a,b) =>", script)
        self.assertIn("applyFilters();", script)
        self.assertNotIn("prototype-home", html)
        self.assertNotIn("今日新增资源12", html)
        self.assertNotIn("较上周 +35%", html)
        self.assertIn("最近发现 · 扫描快照", html)
        self.assertLess(html.index('id="categories"'), html.index('id="catalog-offers"'))
        self.assertLess(html.index('id="catalog-offers"'), html.index('id="weekly-changes"'))
        self.assertLess(html.index('id="weekly-changes"'), html.index('id="expiring-soon"'))
        self.assertIn('id="home-latest-discovery"', html)
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        self.assertIn(f'href="/logs/#log-day-{summary["snapshotDate"]}"', html)
        generator = (ROOT / "scripts/build_static.py").read_text(encoding="utf-8")
        self.assertIn("def update_home_latest_discovery(", generator)
        self.assertIn("updated = update_home_latest_discovery(updated, data_path)", generator)

    def test_editorial_date_cannot_masquerade_as_scan_date(self):
        script = (ROOT / "js/scan-trust.js").read_text(encoding="utf-8")
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        self.assertIn("scan.snapshotDate || scan.date", script)
        self.assertIn("scan.scanRunToday === true", script)
        self.assertIn("editorialCurrent", script)
        self.assertIn("scanCurrent ? scanDate : latest", script)
        self.assertEqual(summary["date"], "2026-10-10")
        self.assertEqual(summary["snapshotDate"], "2026-10-10")
        self.assertTrue(summary["scanRunToday"])
        latest_log = json.loads((ROOT / "data/daily-log/2026-10-10.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["snapshotDate"], latest_log["date"])

    def test_model_catalog_is_already_paginated(self):
        html = (ROOT / "models/all/index.html").read_text(encoding="utf-8")
        row_count = len(re.findall(r'<tr\s+class="catalog-row', html))
        self.assertGreater(row_count, 0)
        self.assertLessEqual(row_count, 26)
        self.assertIn('class="catalog-pagination"', html)
        self.assertIn('href="/models/all/page/2/"', html)


    def test_mobile_scan_cards_use_compact_two_column_layout(self):
        css = (ROOT / "css/primary-menu.css").read_text(encoding="utf-8")
        patch = css.split("/* UX-20261009-P1-11: compact mobile scan statistics */", 1)[1]
        self.assertIn("@media (max-width: 700px)", patch)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr)) !important', patch)
        self.assertIn('.weekly-scan-cards > article', patch)
        self.assertIn('overflow-wrap: anywhere', patch)
        self.assertIn('font-variant-numeric: tabular-nums', patch)

if __name__ == "__main__":
    unittest.main()
