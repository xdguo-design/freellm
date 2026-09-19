import tempfile
import unittest
from pathlib import Path

from scripts.check_internal_links import check_internal_links, check_sitemaps


class InternalLinkChecksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "design").mkdir()
        (self.root / "models" / "all").mkdir(parents=True)
        (self.root / "design" / "free-china-ai-index.html").write_text(
            '<link rel="canonical" href="https://freellm.top/">'
            '<meta name="robots" content="index,follow">'
            '<a href="/models/all/">Models</a>',
            encoding="utf-8",
        )
        (self.root / "models" / "all" / "index.html").write_text(
            '<link rel="canonical" href="https://freellm.top/models/all/">'
            '<meta name="robots" content="index,follow">'
            '<a href="/">Home</a>',
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_internal_links_accept_existing_canonical_paths(self):
        self.assertEqual(check_internal_links(self.root), [])

    def test_internal_links_reject_locale_query_and_missing_target(self):
        page = self.root / "models" / "all" / "index.html"
        page.write_text(
            '<a href="/models/missing/?lang=en">Broken</a>',
            encoding="utf-8",
        )
        errors = check_internal_links(self.root)
        self.assertTrue(any("locale query URL" in error for error in errors))
        self.assertTrue(any("broken internal link" in error for error in errors))

    def test_sitemap_rejects_noindex_pages(self):
        for filename in (
            "sitemap-pages.xml",
            "sitemap-offers.xml",
            "sitemap-providers.xml",
            "sitemap-models.xml",
        ):
            (self.root / filename).write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',
                encoding="utf-8",
            )
        (self.root / "sitemap-pages.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://freellm.top/models/all/</loc></url>'
            '</urlset>',
            encoding="utf-8",
        )
        page = self.root / "models" / "all" / "index.html"
        page.write_text(
            '<link rel="canonical" href="https://freellm.top/models/all/">'
            '<meta name="robots" content="noindex,follow">',
            encoding="utf-8",
        )
        errors = check_sitemaps(self.root)
        self.assertTrue(any("noindex page included in sitemap" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
