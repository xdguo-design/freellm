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


    def test_sitemap_crawl_budget_requires_review_before_large_expansion(self) -> None:
        """Keep a new-domain sitemap from silently ballooning back to hundreds of URLs.

        These are review budgets, not Google limits. Crossing either number should
        trigger an explicit SEO review before a catalog import publishes more
        crawl targets.
        """
        all_urls: list[str] = []
        for sitemap in sorted(ROOT.glob("sitemap-*.xml")):
            root = ET.parse(sitemap).getroot()
            all_urls.extend(
                (loc.text or "").strip()
                for loc in root.findall("sm:url/sm:loc", SITEMAP_NS)
                if (loc.text or "").strip()
            )

        model_root = ET.parse(ROOT / "sitemap-models.xml").getroot()
        model_urls = [
            (loc.text or "").strip()
            for loc in model_root.findall("sm:url/sm:loc", SITEMAP_NS)
            if (loc.text or "").strip()
        ]

        self.assertLessEqual(
            len(all_urls),
            200,
            f"sitemap crawl target budget exceeded ({len(all_urls)} > 200); review SEO scope before publishing",
        )
        self.assertLessEqual(
            len(model_urls),
            60,
            f"model sitemap budget exceeded ({len(model_urls)} > 60); select higher-value model landing pages",
        )

    def test_homepage_prioritizes_indexable_hubs_and_not_thin_categories(self) -> None:
        home = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")

        # Thin category pages remain usable for humans, but the homepage should
        # not promote their noindex URLs as crawl-priority text links.
        for page in sorted((ROOT / "category").glob("*/index.html")):
            html = page.read_text(encoding="utf-8")
            match = META_ROBOTS_RE.search(html)
            if match and "noindex" in match.group(1).lower():
                url = f"/category/{page.parent.name}/"
                self.assertNotIn(
                    f'href="{url}"',
                    home,
                    f"homepage should not promote noindex category {url}",
                )

        # These hubs represent the site's core intent: verified free access,
        # practical guides, then the curated resource/provider directories.
        priority_hubs = (
            "/guides/china-free-ai-api/",
            "/guides/free-openai-compatible-apis/",
            "/guides/free-ai-coding-tools/",
            "/guides/free-ai-search-apis/",
            "/category/free-quota/",
            "/category/api/",
            "/models/",
            "/providers/",
        )
        for url in priority_hubs:
            self.assertIn(f'href="{url}"', home, f"priority hub missing from homepage: {url}")

        self.assertGreaterEqual(
            home.count('href="/offers/'),
            10,
            "homepage should expose a meaningful set of verified offer detail links",
        )


    def test_all_canonical_urls_use_https_freellm(self) -> None:
        """Every emitted canonical must stay on the production HTTPS origin."""
        canonical_re = re.compile(
            r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        offenders: list[str] = []
        missing: list[str] = []

        for path in _published_html_files():
            html = path.read_text(encoding="utf-8")
            matches = canonical_re.findall(html)
            if not matches:
                missing.append(str(path.relative_to(ROOT)))
                continue
            for canonical in matches:
                if not canonical.startswith(SITE_URL + "/"):
                    offenders.append(
                        f"{path.relative_to(ROOT)}: {canonical}"
                    )

        self.assertEqual(
            offenders,
            [],
            "canonical URLs must use the production HTTPS origin: " + "; ".join(offenders),
        )
        self.assertEqual(
            missing,
            [],
            "published HTML pages must emit a canonical URL: " + ", ".join(missing),
        )

    def test_published_pages_do_not_link_to_http_freellm(self) -> None:
        """Prevent internal links from reintroducing the HTTP host.

        Root-relative links such as /offers/... are intentionally allowed and
        inherit HTTPS from the current page.
        """
        href_re = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        offenders: list[str] = []

        for path in _published_html_files():
            html = path.read_text(encoding="utf-8")
            for href in href_re.findall(html):
                normalized = href.strip().lower()
                if (
                    normalized.startswith("http://freellm.top")
                    or normalized.startswith("http://www.freellm.top")
                    or normalized.startswith("//freellm.top")
                    or normalized.startswith("//www.freellm.top")
                ):
                    offenders.append(
                        f"{path.relative_to(ROOT)}: {href}"
                    )

        self.assertEqual(
            offenders,
            [],
            "internal links must not use HTTP or protocol-relative FreeLLM URLs: "
            + "; ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
