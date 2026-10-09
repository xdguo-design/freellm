"""Release gate for 2026-10-09 homepage refresh; only public deterministic artifacts."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomeReleaseGate(unittest.TestCase):
    def test_today_keeps_scanned_data_and_both_editorials(self):
        log = json.loads((ROOT / "data/daily-log/2026-10-09.json").read_text(encoding="utf-8"))
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        ids = [e["id"] for e in log["curatedEvents"]]
        self.assertIn("stepfun-step-5-preview-free-week", ids)
        self.assertIn("phanthycode-free-trial", ids)
        self.assertEqual(ids.count("phanthycode-free-trial"), 1)
        self.assertEqual(summary["date"], "2026-10-09")
        self.assertEqual(summary["snapshotDate"], "2026-10-09")
        self.assertTrue(summary["scanRunToday"])
        self.assertEqual(summary["models"], len(log["observed"]["models"]))
        self.assertEqual(summary["offers"], len(log["observed"]["offers"]))
        self.assertEqual(summary["newCount"], 2)
        self.assertEqual(summary["sourceChecks"], 2)

    def test_homepage_uses_sourced_discovery_and_incremental_cards(self):
        homepage = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        js = (ROOT / "js/homepage.js").read_text(encoding="utf-8")
        build = (ROOT / "scripts/build_static.py").read_text(encoding="utf-8")
        self.assertNotIn('class="prototype-home"', homepage)
        self.assertNotIn("今日新增资源12", homepage)
        self.assertNotIn("较上周 +35%", homepage)
        self.assertIn("PhanthyCode", homepage)
        self.assertIn('href="/logs/#log-day-2026-10-09"', homepage)
        self.assertIn("def update_home_latest_discovery(", build)
        self.assertIn("def update_home_scan_snapshot(", build)
        self.assertIn('<b id="heroCount">70</b>', homepage)
        self.assertIn("updated = update_home_latest_discovery(updated, data_path)", build)
        self.assertIn("entry = events[-1] if events else None", build)
        self.assertIn("HOME_OFFERS_PAGE_SIZE = 24", js)
        self.assertIn("matchedRows.slice(0, visibleOfferLimit)", js)
        self.assertIn("offerGrid.replaceChildren(...visibleCards)", js)
        self.assertIn("rows.sort((a,b) =>", js)
        self.assertIn("applyOfferBodyClamps(offerGrid)", js)
        self.assertLess(homepage.index('id="catalog-offers"'), homepage.index('id="weekly-changes"'))
        asset = hashlib.sha1(b"blob " + str(len(js.encode())).encode() + b"\0" + js.encode()).hexdigest()[:10]
        self.assertIn(f"../js/homepage.{asset}.js", homepage)
        self.assertEqual((ROOT / f"js/homepage.{asset}.js").read_text(encoding="utf-8"), js)

    def test_logs_keep_both_discoveries_visible(self):
        html = (ROOT / "logs/index.html").read_text(encoding="utf-8")
        self.assertIn("Step 5 Preview", html)
        self.assertIn("PhanthyCode", html)
        self.assertIn("phanthycode-free-trial", html)
        self.assertIn("待实测", html)
        self.assertIn("https://code.phanthy.com/token-plan", html)

    def test_legacy_routes_and_unread_indicator(self):
        v = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        routes = {row["source"]: row for row in v["redirects"]}
        for old, new in (("/updates", "/logs/"), ("/updates/", "/logs/"),
                         ("/en/updates", "/en/logs/"), ("/en/updates/", "/en/logs/")):
            self.assertEqual(routes[old]["destination"], new)
            self.assertTrue(routes[old]["permanent"])
        nav = (ROOT / "js/site-navigation.js").read_text(encoding="utf-8")
        css = (ROOT / "css/primary-menu.css").read_text(encoding="utf-8")
        self.assertIn("freellm-last-read-update", nav)
        self.assertIn("getLastReadUpdate() !== lastUpdateDate", nav)
        self.assertIn(".ref-topbar.ref-topbar.ref-topbar", css)
        self.assertIn(".catalog-load-more", css)


if __name__ == "__main__":
    unittest.main()
