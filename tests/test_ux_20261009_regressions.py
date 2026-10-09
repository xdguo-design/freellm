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
        self.assertFalse(discovery["initialized"]["models"])
        self.assertFalse(discovery["initialized"]["offers"])
        self.assertFalse(discovery.get("observed"))
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

    def test_model_catalog_is_already_paginated(self):
        html = (ROOT / "models/all/index.html").read_text(encoding="utf-8")
        row_count = len(re.findall(r'<tr\s+class="catalog-row', html))
        self.assertGreater(row_count, 0)
        self.assertLessEqual(row_count, 26)
        self.assertIn('class="catalog-pagination"', html)
        self.assertIn('href="/models/all/page/2/"', html)


if __name__ == "__main__":
    unittest.main()
