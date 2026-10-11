"""S6 (2026-10-10 audit): the sitemap lists only indexable, real-content pages."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://freellm.top"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _page_file(url: str) -> Path:
    path = url[len(BASE):]
    if path == "/":
        return ROOT / "design" / "free-china-ai-index.html"
    return ROOT / path.lstrip("/") / "index.html"


def _sitemap_urls() -> list[str]:
    index = ET.parse(ROOT / "sitemap.xml").getroot()
    urls: list[str] = []
    for loc in index.findall("s:sitemap/s:loc", NS):
        name = loc.text.rsplit("/", 1)[-1]
        child = ET.parse(ROOT / name).getroot()
        urls += [node.text for node in child.findall("s:url/s:loc", NS)]
    return urls


def _robots(html: str) -> str:
    match = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"', html, re.I)
    return match.group(1).lower() if match else ""


class SitemapIndexableTests(unittest.TestCase):
    def test_every_sitemap_url_is_an_existing_indexable_page(self):
        urls = _sitemap_urls()
        self.assertGreater(len(urls), 100)
        self.assertEqual(len(urls), len(set(urls)), "duplicate sitemap URLs")
        problems = []
        for url in urls:
            self.assertTrue(url.startswith(BASE + "/"), url)
            page = _page_file(url)
            if not page.is_file():
                problems.append(f"{url}: no page file")
                continue
            html = page.read_text(encoding="utf-8")
            if "noindex" in _robots(html):
                problems.append(f"{url}: noindex page in sitemap")
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
            if canonical and canonical.group(1) != url:
                problems.append(f"{url}: canonical points to {canonical.group(1)}")
        self.assertEqual(problems, [])

    def test_no_noindex_page_is_listed_anywhere(self):
        listed = set(_sitemap_urls())
        noindex = []
        for page in ROOT.glob("**/index.html"):
            rel = page.relative_to(ROOT)
            if rel.parts[0] in {"node_modules", "data", "design", "seo", ".git"}:
                continue
            if "noindex" in _robots(page.read_text(encoding="utf-8")):
                noindex.append(BASE + "/" + rel.parent.as_posix().strip(".") + "/")
        self.assertTrue(noindex, "expected some noindex pages (thin models, /en/, /health/)")
        self.assertEqual(sorted(set(noindex) & listed), [])

    def test_placeholder_routes_are_noindex_and_evaluations_is_listed(self):
        listed = set(_sitemap_urls())
        self.assertIn(BASE + "/evaluations/", listed)
        self.assertFalse((ROOT / "sitemap-english.xml").exists())
        for path in ("/health/", "/en/", "/en/models/", "/en/workflow/"):
            with self.subTest(path=path):
                self.assertNotIn(BASE + path, listed)
                self.assertIn("noindex", _robots(_page_file(BASE + path).read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
