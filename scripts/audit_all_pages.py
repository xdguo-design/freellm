"""Audit every deployable HTML page and emit a machine-readable report.

Default mode is report-only so one new warning never hides the rest of the daily evidence.
Use --strict when the report has been triaged and should become a release gate.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://freellm.top"
EXCLUDE_PREFIXES = (
    "data/snapshots/",
    "design/prototypes/",
    "design/verification/",
    "design/visual-directions/",
    "skills/test-artifacts/",
    "seo/",
)
EXCLUDE_FILES = {"design/about.html", "design/updates.html"}
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DESC_RE = re.compile(r"<meta\\s+name=[\"']description[\"']\\s+content=[\"']([^\"']*)[\"']", re.I)
CANONICAL_RE = re.compile(r"<link\\s+rel=[\"']canonical[\"']\\s+href=[\"']([^\"']+)[\"']", re.I)
ROBOTS_RE = re.compile(r"<meta\\s+name=[\"']robots[\"']\\s+content=[\"']([^\"']*)[\"']", re.I)
H1_RE = re.compile(r"<h1(?:\\s|>)", re.I)
ID_RE = re.compile(r"\\bid=[\"']([^\"']+)[\"']", re.I)


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.images: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag.lower() == "a" and values.get("href"):
            self.hrefs.append(values["href"].strip())
        if tag.lower() == "img":
            self.images.append(values)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_pages() -> list[Path]:
    pages: list[Path] = []
    for path in ROOT.rglob("*.html"):
        name = rel(path)
        if name in EXCLUDE_FILES or any(name.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        pages.append(path)
    return sorted(pages)


def public_path(path: Path) -> str:
    name = rel(path)
    if name == "design/free-china-ai-index.html":
        return "/"
    if name.endswith("/index.html"):
        return "/" + name[:-len("index.html")]
    return "/" + name


def local_target(url_path: str) -> Path | None:
    clean = urlparse(url_path).path or "/"
    if clean == "/":
        return ROOT / "design" / "free-china-ai-index.html"
    if clean.startswith(("/api/", "/_vercel/")):
        return None
    candidate = ROOT / clean.lstrip("/")
    if clean.endswith("/"):
        return candidate / "index.html"
    if candidate.suffix:
        return candidate
    return candidate / "index.html"


def audit_page(path: Path) -> dict:
    name = rel(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    robots_match = ROBOTS_RE.search(text)
    robots = (robots_match.group(1) if robots_match else "").lower()
    indexable = "noindex" not in robots
    errors: list[str] = []
    warnings: list[str] = []

    title = TITLE_RE.search(text)
    desc = DESC_RE.search(text)
    canonical = CANONICAL_RE.search(text)
    if indexable and not title:
        errors.append("missing title")
    if indexable and not desc:
        errors.append("missing meta description")
    if indexable and not canonical:
        errors.append("missing canonical")
    if canonical:
        parsed = urlparse(canonical.group(1).strip())
        if parsed.scheme != "https" or parsed.netloc != "freellm.top":
            errors.append(f"canonical outside production origin: {canonical.group(1).strip()}")

    h1_count = len(H1_RE.findall(text))
    if indexable and h1_count > 1:
        errors.append(f"multiple h1 elements: {h1_count}")
    elif indexable and h1_count == 0:
        warnings.append("no h1")

    ids = ID_RE.findall(text)
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in ids:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        warnings.append("duplicate ids: " + ", ".join(sorted(duplicates)[:10]))

    parser = AuditParser()
    try:
        parser.feed(text)
    except Exception as exc:
        errors.append(f"HTML parse error: {exc}")

    page_url = SITE.rstrip("/") + public_path(path)
    for href in parser.hrefs:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")) or "${" in href:
            continue
        absolute = urljoin(page_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc and parsed.netloc not in {"freellm.top", "www.freellm.top"}:
            continue
        if "lang" in parse_qs(parsed.query, keep_blank_values=True):
            errors.append(f"internal locale query link: {href}")
        target = local_target(parsed.path)
        if target is not None and not target.is_file():
            errors.append(f"broken internal link: {href}")

    missing_alt = sum(1 for attrs in parser.images if attrs.get("alt") is None)
    if missing_alt:
        warnings.append(f"images missing alt attribute: {missing_alt}")

    size = path.stat().st_size
    if size > 1_000_000:
        errors.append(f"page exceeds 1 MB: {size} bytes")
    elif size > 500_000:
        warnings.append(f"large page: {size} bytes")

    return {
        "path": name,
        "publicPath": public_path(path),
        "indexable": indexable,
        "bytes": size,
        "h1Count": h1_count,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="all-pages-audit.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    rows = [audit_page(path) for path in iter_pages()]
    error_count = sum(len(row["errors"]) for row in rows)
    warning_count = sum(len(row["warnings"]) for row in rows)
    report = {
        "pageCount": len(rows),
        "pagesWithErrors": sum(bool(row["errors"]) for row in rows),
        "pagesWithWarnings": sum(bool(row["warnings"]) for row in rows),
        "errorCount": error_count,
        "warningCount": warning_count,
        "pages": rows,
    }
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("pageCount", "pagesWithErrors", "pagesWithWarnings", "errorCount", "warningCount")}, ensure_ascii=False))
    for row in rows:
        for error in row["errors"][:8]:
            print(f"ERROR {row['path']}: {error}")
    return 1 if args.strict and error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
