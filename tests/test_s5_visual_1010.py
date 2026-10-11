"""S5 (2026-10-10 visual audit) regression contracts.

Static checks always run. Browser checks (390px drawer navigation, no horizontal
overflow, locale switch of the catalog filters) need Playwright Chromium and are
skipped where it cannot launch (e.g. aarch64 sandboxes); CI browser-smoke runs them.
"""

import re
import unittest
from pathlib import Path

from tests.test_e2e_static import _LocalSite, start_playwright

ROOT = Path(__file__).resolve().parents[1]
MAIN_PAGES = (
    ("design/free-china-ai-index.html", ".catalog-hero"),
    ("models/", 'body[data-fl-section="models"]'),
    ("links/", "body > main"),
    ("evaluations/", ".fl-eval"),
    ("skills/", ".skills-page"),
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class StaticVisualContracts(unittest.TestCase):
    def test_select_options_never_hold_bilingual_spans(self):
        for page in ("models/index.html", "en/models/index.html"):
            path = ROOT / page
            if not path.exists():
                continue
            html = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"<option[^>]*>\s*<span", html), page)
        self.assertIn('data-zh="推荐排序" data-en="Featured">推荐排序</option>', read("models/index.html"))

    def test_chinese_chrome_has_no_english_index_leftovers(self):
        for page in ("links/index.html", "providers/index.html", "models/index.html", "evaluations/index.html", "design/free-china-ai-index.html"):
            html = read(page)
            self.assertNotIn("FREE AI INDEX", html, page)
            self.assertNotIn(">Free AI Index</a>", html, page)
            self.assertNotIn("PROVIDER DIRECTORY", html, page)
            self.assertNotIn("MODEL AGGREGATION", html, page)

    def test_homepage_filter_labels_and_locale_strings(self):
        js = read("js/homepage.js")
        self.assertIn("['method', 'capability', 'updated'].forEach", js, "third filter label is freshness, not region")
        for key in ("s5ExpiredChip", "s5Fresh", "s5SiteSearch", "s5TodayFind"):
            self.assertEqual(js.count(f"{key}:"), 2, key)
        self.assertIn("expired: 's5ExpiredChip'", js)
        self.assertIn("'catalog-freshness-filter'", js)
        self.assertIn(".ref-topbar input[type=\"search\"]", js)

    def test_english_fallback_does_not_emit_stripped_cjk_fragments(self):
        js = read("js/homepage.js")
        self.assertIn("cjkCount / visible > 0.25", js)

    def test_evaluations_cards_do_not_break_words_mid_word(self):
        css = read("scripts/eval_report.css")
        self.assertNotIn(".award b{display:block;font-size:15px;margin:4px 0;word-break:break-all}", css)
        self.assertIn("white-space:nowrap", css)
        self.assertIn(".fl-eval .tbl{max-width:100%;overflow-x:auto", css)
        self.assertIn(css, read("evaluations/index.html"))

    def test_shared_navigation_loads_visual_fixes_last(self):
        nav = read("js/site-navigation.js")
        self.assertIn("/css/s5-visual-fixes.css", nav)
        self.assertTrue((ROOT / "css" / "s5-visual-fixes.css").is_file())
        css = read("css/s5-visual-fixes.css")
        self.assertIn('[data-fl-section="about"]:not([data-about-static]):not([data-reference-style]) > main', css)
        self.assertIn(".filter-chip.active em", css)
        self.assertIn('[data-locale-switch="zh-CN"]', css)


class MobileBrowserContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._started = start_playwright()
        if cls._started is None:
            raise unittest.SkipTest("playwright chromium not available")
        cls._manager, cls._browser = cls._started

    @classmethod
    def tearDownClass(cls):
        cls._browser.close()
        cls._manager.stop()

    def setUp(self):
        self.site = _LocalSite(ROOT)
        self.addCleanup(self.site.stop)

    def open(self, route, width, height=844):
        context = self._browser.new_context(locale="zh-CN", viewport={"width": width, "height": height})
        self.addCleanup(context.close)
        page = context.new_page()
        page.route("**/pagead2.googlesyndication.com/**", lambda r: r.fulfill(status=200, body=""))
        page.goto(f"{self.site.url}/{route}")
        return page

    def test_main_pages_390_have_drawer_nav_and_no_horizontal_overflow(self):
        for route, selector in MAIN_PAGES:
            with self.subTest(route=route):
                page = self.open(route, 390)
                page.wait_for_selector(selector, state="attached")
                page.wait_for_selector("#fl-shared-site-menu .fl-mobile-menu-button", state="attached")
                menu = page.locator("#fl-shared-site-menu .fl-mobile-menu-button")
                self.assertTrue(menu.is_visible(), route)
                first = page.locator("#fl-shared-site-menu .fl-site-nav > a").first
                self.assertFalse(first.is_visible(), route)
                menu.click()
                self.assertEqual(menu.get_attribute("aria-expanded"), "true", route)
                self.assertTrue(first.is_visible(), route)
                page.keyboard.press("Escape")
                width = page.evaluate("document.documentElement.scrollWidth")
                inner = page.evaluate("innerWidth")
                offenders = page.evaluate("""() => Array.from(document.querySelectorAll('body *'))
                    .filter(el => { const r = el.getBoundingClientRect(); return r.width > 1 && (r.right > innerWidth + 2 || r.left < -2)
                        && !el.closest('.tbl, .filter-strip, .model-section-tabs, [style*="overflow"]'); })
                    .slice(0, 5).map(el => el.tagName + '.' + el.className)""")
                self.assertLessEqual(width, inner, f"{route}: scrollWidth {width} > {inner}; {offenders}")

    def test_main_pages_1440_do_not_overflow(self):
        for route, selector in MAIN_PAGES:
            with self.subTest(route=route):
                page = self.open(route, 1440, 1000)
                page.wait_for_selector(selector, state="attached")
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 1440, route)

    def test_links_main_aligns_with_header(self):
        page = self.open("links/", 1440, 1000)
        page.wait_for_selector("body > main")
        header = page.locator("body > header").bounding_box()
        main = page.locator("body > main").bounding_box()
        self.assertLessEqual(abs(header["x"] - main["x"]), 4, (header, main))

    def test_english_switch_localizes_catalog_filters_and_ended_chip(self):
        page = self.open("design/free-china-ai-index.html?lang=en", 1440, 1000)
        page.wait_for_selector("#catalog-freshness-filter")
        page.wait_for_function("document.documentElement.lang === 'en'")
        self.assertEqual(page.locator('#catalog-freshness-filter option[value="fresh"]').inner_text(), "Within 7 days")
        self.assertEqual(page.locator('#catalog-method-filter option[value="all"]').inner_text(), "All")
        self.assertEqual(page.locator('.catalog-filter-bar > label:nth-child(3) b').inner_text(), "Last checked")
        self.assertTrue(page.locator('.filter-chip[data-filter="expired"]').inner_text().startswith("Ended"))
        cjk = page.evaluate("""() => Array.from(document.querySelectorAll('.offer'))
            .map(el => el.innerText).filter(t => /·\\s*·/.test(t)).length""")
        self.assertEqual(cjk, 0)


if __name__ == "__main__":
    unittest.main()
