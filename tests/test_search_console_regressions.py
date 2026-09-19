from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://freellm.top"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
META_ROBOTS_RE = re.compile(
    r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _published_html_files() -> list[Path]:
    pages = list(ROOT.rglob("index.html"))
    design_home = ROOT / "design" / "free-china-ai-index.html"
    if design_home.exists():
        pages.append(design_home)
    return sorted(set(pages))


def _url_to_file(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "freellm.top":
        raise AssertionError(f"unexpected sitemap host: {url}")

    path = parsed.path
    if path == "/":
        return ROOT / "design" / "free-china-ai-index.html"
    if not path.endswith("/"):
        raise AssertionError(f"sitemap URL must use canonical trailing slash: {url}")
    return ROOT / path.lstrip("/") / "index.html"


class SearchConsoleRegressionTests(unittest.TestCase):
    """Guards against URL multiplication and stale sitemap entries.

    Search Console previously discovered hundreds of locale-query variants
    (for example /about/?lang=en) and stale generated pages. These checks run
    in the normal unittest gate so generated artifacts cannot silently
    reintroduce those crawlable duplicates.
    """

    def test_published_pages_do_not_emit_locale_query_links(self) -> None:
        offenders: list[str] = []
        for path in _published_html_files():
            text = path.read_text(encoding="utf-8")
            if "?lang=" in text or "&lang=" in text:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(
            offenders,
            [],
            "crawlable locale query URLs reintroduced in: " + ", ".join(offenders),
        )

    def test_sitemaps_only_publish_clean_canonical_urls(self) -> None:
        offenders: list[str] = []
        sitemap_files = sorted(ROOT.glob("sitemap-*.xml"))
        self.assertTrue(sitemap_files, "expected child sitemaps")

        for sitemap in sitemap_files:
            root = ET.parse(sitemap).getroot()
            for loc in root.findall("sm:url/sm:loc", SITEMAP_NS):
                url = (loc.text or "").strip()
                parsed = urlparse(url)
                if parsed.query or parsed.fragment:
                    offenders.append(f"{sitemap.name}: {url}")
                if not url.startswith(SITE_URL + "/"):
                    offenders.append(f"{sitemap.name}: wrong host {url}")

        self.assertEqual(
            offenders,
            [],
            "sitemap must contain only clean canonical URLs: " + "; ".join(offenders),
        )

    def test_sitemap_urls_exist_and_are_indexable(self) -> None:
        missing: list[str] = []
        noindex: list[str] = []

        for sitemap in sorted(ROOT.glob("sitemap-*.xml")):
            root = ET.parse(sitemap).getroot()
            for loc in root.findall("sm:url/sm:loc", SITEMAP_NS):
                url = (loc.text or "").strip()
                page = _url_to_file(url)
                if not page.is_file():
                    missing.append(f"{url} -> {page.relative_to(ROOT)}")
                    continue

                html = page.read_text(encoding="utf-8")
                match = META_ROBOTS_RE.search(html)
                if match and "noindex" in match.group(1).lower():
                    noindex.append(url)

        self.assertEqual(
            missing,
            [],
            "sitemap contains stale/nonexistent pages: " + "; ".join(missing),
        )
        self.assertEqual(
            noindex,
            [],
            "sitemap contains pages explicitly marked noindex: " + "; ".join(noindex),
        )


if __name__ == "__main__":
    unittest.main()
