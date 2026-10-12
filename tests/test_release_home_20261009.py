"""Release gate for 2026-10-09 homepage refresh; only public deterministic artifacts."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomeReleaseGate(unittest.TestCase):
    def test_approved_homepage_has_exactly_the_four_selected_hot_articles(self):
        homepage = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        hotspot = re.search(r'<section class="prototype-hot"[^>]*>.*?</section>', homepage, re.S)
        self.assertIsNotNone(hotspot, "the approved homepage hotspot section must be present")
        links = re.findall(
            r'<a\b[^>]*href="(https://mp\.weixin\.qq\.com/s/[^\"]+)"',
            hotspot.group(0),
        )
        self.assertEqual(
            links,
            [
                "https://mp.weixin.qq.com/s/O8U-o7VMSCOmlWWzCd_8VA",
                "https://mp.weixin.qq.com/s/0wpj7RwonsMLfYKYcogVLA",
                "https://mp.weixin.qq.com/s/ulrLlqKxFyw6sXyAodUo7g",
                "https://mp.weixin.qq.com/s/N5xBX4TgvzlzBrkNTA7kRw",
            ],
        )
        self.assertEqual(len(re.findall(r'<article class="prototype-hot-card(?: is-featured)?"', hotspot.group(0))), 4)
        self.assertNotIn('id="project-feature-news"', homepage)

    def test_four_hot_articles_keep_equal_desktop_grid_cells(self):
        css = (ROOT / "css/home-prototype-exact.css").read_text(encoding="utf-8")
        self.assertIn(".prototype-hot-grid{grid-template-columns:repeat(4,minmax(0,1fr))", css)
        self.assertRegex(
            css,
            r"\.prototype-hot-card\.is-featured\{[^}]*grid-column:auto!important;grid-row:auto!important",
        )
        self.assertRegex(
            css,
            r"\.prototype-hot-card\.is-featured\{[^}]*height:236px!important",
        )

    def test_prototype_counters_match_the_canonical_scan_summary(self):
        homepage = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        for key in ("newCount", "newModels", "offers", "models"):
            self.assertRegex(
                homepage,
                rf'<strong data-scan-stat="{key}">{summary[key]}</strong>',
            )
        self.assertNotRegex(homepage, r"↑\s*\+\d+%")
        self.assertIn('data-scan-date>', homepage)

    def test_updates_page_renders_accessible_filters_and_sort_control(self):
        updates = (ROOT / "logs/index.html").read_text(encoding="utf-8")
        script = (ROOT / "js/reference-shell.js").read_text(encoding="utf-8")
        for category in ("all", "model", "tool", "offer", "recovered", "offline"):
            self.assertIn(f'data-history-filter="{category}"', updates)
        self.assertIn('data-history-sort="desc"', updates)
        self.assertIn('data-history-row', updates)
        self.assertIn('aria-live="polite"', updates)
        self.assertIn("data-history-filter", script)
        self.assertIn("data-history-sort", script)

    def test_today_keeps_scanned_data_and_both_editorials(self):
        log = json.loads((ROOT / "data/daily-log/2026-10-09.json").read_text(encoding="utf-8"))
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        ids = [e["id"] for e in log["curatedEvents"]]
        self.assertIn("stepfun-step-5-preview-free-week", ids)
        self.assertIn("phanthycode-free-trial", ids)
        self.assertEqual(ids.count("phanthycode-free-trial"), 1)
        latest_log = json.loads(sorted((ROOT / "data/daily-log").glob("20??-??-??.json"))[-1].read_text(encoding="utf-8"))
        self.assertEqual(summary["date"], latest_log["date"])
        self.assertEqual(summary["snapshotDate"], latest_log["date"])
        self.assertTrue(summary["scanRunToday"])
        self.assertEqual(summary["scannedModels"], len(latest_log["observed"]["models"]))
        self.assertEqual(summary["scannedOffers"], len(latest_log["observed"]["offers"]))
        # 2026-10-10 series 4: the duplicate Step 5 / back-dated scan events were
        # removed and officially verified additions curated; count from the log.
        new_events = [e for key in ("events", "curatedEvents") for e in latest_log.get(key) or [] if e.get("eventType") in {"new", "new_route"}]
        self.assertEqual(summary["newCount"], len(new_events))
        self.assertEqual(summary["sourceChecks"], 2)

    def test_homepage_uses_sourced_discovery_and_incremental_cards(self):
        homepage = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        js = (ROOT / "js/homepage.js").read_text(encoding="utf-8")
        build = (ROOT / "scripts/build_static.py").read_text(encoding="utf-8")
        self.assertIn('class="prototype-home"', homepage)
        self.assertNotIn("今日新增资源12", homepage)
        self.assertNotIn("较上周 +35%", homepage)
        summary = json.loads((ROOT / "data/scan-summary.json").read_text(encoding="utf-8"))
        self.assertIn(f'href="/logs/#log-day-{summary["snapshotDate"]}"', homepage)
        self.assertIn("def update_home_latest_discovery(", build)
        self.assertIn("def sync_home_scan_snapshot(", build)
        self.assertIn(f'<b id="heroCount">{summary["offers"]}</b>', homepage)
        self.assertIn("updated = update_home_latest_discovery(updated, data_path)", build)
        # newest official (non third-party relay) discovery, curated first
        self.assertIn("entry = curated[0] if curated else (official[-1] if official else None)", build)
        self.assertIn("HOME_OFFERS_PAGE_SIZE = 24", js)
        self.assertIn("matchedRows.slice(0, visibleOfferLimit)", js)
        self.assertIn("offerGrid.replaceChildren(...visibleCards)", js)
        self.assertIn("rows.sort((a,b) =>", js)
        self.assertIn("applyOfferBodyClamps(offerGrid)", js)
        self.assertLess(homepage.index('id="catalog-offers"'), homepage.index('id="weekly-changes"'))
        asset = hashlib.sha1(b"blob " + str(len(js.encode())).encode() + b"\0" + js.encode()).hexdigest()[:10]
        self.assertIn(f"../js/homepage.{asset}.js", homepage)
        self.assertEqual((ROOT / f"js/homepage.{asset}.js").read_text(encoding="utf-8"), js)

    def test_homepage_layout_styles_are_loaded_before_first_paint(self):
        homepage = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        navigation = re.search(
            r'<link\b(?=[^>]*primary-menu\.css\?v=20261009-ux-p0)[^>]*>', homepage
        )
        self.assertIsNotNone(navigation)
        self.assertIn('rel="stylesheet"', navigation.group(0))
        self.assertNotIn('media="print"', navigation.group(0))
        self.assertIn('data-fl-shared-navigation-styles="1"', navigation.group(0))
        self.assertIn('<aside id="fl-shared-site-menu"', homepage)
        self.assertIn('home-prototype-critical.css?v=20261011-approved-homepage', homepage)

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
