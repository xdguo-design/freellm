"""Validate generated first-party links, canonical URLs, and sitemap entries.

This gate is intentionally offline: it validates the static artifact tree that Vercel
will publish, so broken internal URLs or duplicate locale query URLs fail before deploy.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse


SITE_URL = "https://freellm.top"
DEFAULT_ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE_FILE = Path("design/free-china-ai-index.html")
SITEMAPS = (
    "sitemap-pages.xml",
    "sitemap-offers.xml",
    "sitemap-providers.xml",
    "sitemap-models.xml",
)
SCAN_ROOTS = (
    "about",
    "links",
    "terms",
    "privacy",
    "submit",
    "offers",
    "category",
    "guides",
    "models",
    "providers",
    "logs",
    "skills",
)
ROBOTS_RE = re.compile(
    r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CANONICAL_RE = re.compile(
    r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = dict(attrs)
        href = values.get("href")
        if href:
            self.hrefs.append(href.strip())


def public_url_for_file(relative: Path) -> str:
    if relative == HOMEPAGE_FILE:
        return "/"
    posix = relative.as_posix()
    if posix.endswith("/index.html"):
        return "/" + posix[: -len("index.html")]
    return "/" + posix


def local_path_for_url(root: Path, path: str) -> Path | None:
    parsed = urlparse(path)
    clean = parsed.path or "/"
    if clean == "/":
        return root / HOMEPAGE_FILE
    if clean.startswith("/api/"):
        return None
    relative = clean.lstrip("/")
    candidate = root / relative
    if clean.endswith("/"):
        return candidate / "index.html"
    if candidate.is_file():
        return candidate
    if candidate.suffix:
        return candidate
    return candidate / "index.html"


def iter_html_files(root: Path):
    homepage = root / HOMEPAGE_FILE
    if homepage.is_file():
        yield homepage
    for dirname in SCAN_ROOTS:
        base = root / dirname
        if base.is_dir():
            yield from base.rglob("*.html")


def check_internal_links(root: Path) -> list[str]:
    errors: list[str] = []
    seen: set[Path] = set()
    for html_path in iter_html_files(root):
        if html_path in seen:
            continue
        seen.add(html_path)
        relative = html_path.relative_to(root)
        page_url = SITE_URL.rstrip("/") + public_url_for_file(relative)
        parser = LinkParser()
        try:
            parser.feed(html_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as error:
            errors.append(f"{relative}: cannot read HTML: {error}")
            continue
        for href in parser.hrefs:
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(page_url, href)
            parsed = urlparse(absolute)
            if parsed.netloc and parsed.netloc != "freellm.top":
                continue
            if "lang" in parse_qs(parsed.query, keep_blank_values=True):
                errors.append(f"{relative}: locale query URL must not be linked: {href}")
            target = local_path_for_url(root, parsed.path)
            if target is None:
                continue
            if not target.is_file():
                errors.append(f"{relative}: broken internal link {href} -> {target.relative_to(root)}")
    return errors


def _extract_meta(html: str, regex: re.Pattern[str]) -> str | None:
    match = regex.search(html)
    return match.group(1).strip() if match else None


def check_sitemaps(root: Path) -> list[str]:
    errors: list[str] = []
    for filename in SITEMAPS:
        sitemap = root / filename
        if not sitemap.is_file():
            errors.append(f"{filename}: missing sitemap")
            continue
        try:
            tree = ET.parse(sitemap)
        except (ET.ParseError, OSError) as error:
            errors.append(f"{filename}: invalid XML: {error}")
            continue
        for loc in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            url = (loc.text or "").strip()
            if not url:
                errors.append(f"{filename}: empty <loc>")
                continue
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.netloc != "freellm.top":
                errors.append(f"{filename}: non-canonical host in sitemap: {url}")
                continue
            if "lang" in parse_qs(parsed.query, keep_blank_values=True):
                errors.append(f"{filename}: locale query URL in sitemap: {url}")
            target = local_path_for_url(root, parsed.path)
            if target is None or not target.is_file():
                errors.append(f"{filename}: sitemap URL has no generated file: {url}")
                continue
            if target.suffix.lower() != ".html":
                continue
            html = target.read_text(encoding="utf-8")
            robots = (_extract_meta(html, ROBOTS_RE) or "").lower()
            if "noindex" in robots:
                errors.append(f"{filename}: noindex page included in sitemap: {url}")
            canonical = _extract_meta(html, CANONICAL_RE)
            expected = SITE_URL.rstrip("/") + parsed.path
            if canonical != expected:
                errors.append(
                    f"{filename}: canonical mismatch for {url}: expected {expected!r}, found {canonical!r}"
                )
    return errors


def check_site(root: Path) -> list[str]:
    return check_internal_links(root) + check_sitemaps(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    errors = check_site(root)
    if errors:
        print("static link validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("static link validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
