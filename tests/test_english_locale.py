"""P1-4 English URLs and reciprocal locale/canonical regression checks."""
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://freellm.top"
PAIRS = {
    "/": "/en/",
    "/models/": "/en/models/",
    "/models/all/": "/en/models/all/",
    "/providers/": "/en/providers/",
    "/skills/": "/en/skills/",
    "/tools/": "/en/tools/",
    "/workflow/": "/en/workflow/",
    "/logs/": "/en/logs/",
    "/about/": "/en/about/",
}


def page_for(path):
    return ROOT / ("design/free-china-ai-index.html" if path == "/" else path.lstrip("/") + "index.html")


class EnglishLocaleTests(unittest.TestCase):
    def test_placeholder_english_pairs_are_noindex_without_hreflang(self):
        """2026-10-10 audit: /en/ pages are ~1k-char placeholders, so they stay
        reachable but noindex, and no page announces them via hreflang."""
        for zh, en in PAIRS.items():
            chinese = page_for(zh).read_text(encoding="utf-8")
            english = page_for(en).read_text(encoding="utf-8")
            with self.subTest(path=en):
                self.assertIn('rel="canonical" href="' + BASE + en + '"', english)
                self.assertIn('<meta name="robots" content="noindex,follow">', english)
                self.assertNotIn('hreflang="en" href=', english)
                self.assertIn('<html lang="en">', english)
                self.assertIn('href="' + zh + '" hreflang="zh-CN"', english)
            with self.subTest(path=zh):
                self.assertIn('rel="canonical" href="' + BASE + zh + '"', chinese)
                self.assertNotIn('hreflang="en" href="' + BASE + en + '"', chinese)
                self.assertNotIn('content="noindex', chinese)

    def test_english_routes_have_original_content_and_navigation(self):
        for zh, en in PAIRS.items():
            page = page_for(en).read_text(encoding="utf-8")
            with self.subTest(path=en):
                self.assertIn('<main id="main"', page)
                self.assertIn('Skip to content', page)
                self.assertIn('aria-label="Primary navigation"', page)
                self.assertGreaterEqual(page.count('<section class="en-panel">'), 2)
                for path in ("/en/", "/en/models/", "/en/skills/", "/en/tools/", "/en/logs/", "/en/about/"):
                    self.assertIn('href="' + path + '"', page)

    def test_sitemap_excludes_placeholder_english_urls(self):
        index = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn(BASE + "/sitemap-english.xml", index)
        self.assertFalse((ROOT / "sitemap-english.xml").exists())
        for name in ("sitemap-pages.xml", "sitemap-offers.xml", "sitemap-providers.xml", "sitemap-models.xml"):
            self.assertNotIn(BASE + "/en/", (ROOT / name).read_text(encoding="utf-8"))

    def test_untranslated_details_do_not_claim_nonexistent_english_pages(self):
        for path in ("/offers/codebuddy/", "/category/free-ide/", "/providers/openrouter/"):
            page = page_for(path).read_text(encoding="utf-8")
            self.assertNotIn('hreflang="en"', page)

    def test_english_counts_use_scan_summary_not_fake_growth(self):
        script = (ROOT / "js/en-scan.js").read_text(encoding="utf-8")
        self.assertIn("/data/scan-summary.json", script)
        self.assertIn("Number.isInteger(v)", script)
        self.assertNotIn("Math.random", script)


if __name__ == "__main__":
    unittest.main()
