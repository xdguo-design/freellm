"""Audit crawl-facing static HTML metadata and crawl-budget hazards.

This intentionally treats deliberate noindex pages as informational, not failures.
It mirrors common site-audit thresholds closely enough to catch regressions before
an external crawler reports them.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIXES = (
    "data/snapshots/",
    "docs/marketing/",
    "design/prototypes/",
    "design/visual-directions/",
    "seo/",
)
TITLE_MIN = 20
TITLE_MAX = 65
DESC_MIN = 70
DESC_MAX = 170
LOW_TEXT_MIN = 300
LARGE_IMAGE_BYTES = 200_000


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _attr(page: str, name: str) -> str:
    pattern = rf'<meta\s+name=["\']{re.escape(name)}["\']\s+content=["\']([^"\']*)["\']'
    match = re.search(pattern, page, re.I)
    if not match:
        pattern = rf'<meta\s+content=["\']([^"\']*)["\']\s+name=["\']{re.escape(name)}["\']'
        match = re.search(pattern, page, re.I)
    return html.unescape(match.group(1)).strip() if match else ""


def _title(page: str) -> str:
    match = re.search(r"<title>(.*?)</title>", page, re.I | re.S)
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip() if match else ""


def _visible_text(page: str) -> str:
    page = re.sub(r"<script\b[\s\S]*?</script>", " ", page, flags=re.I)
    page = re.sub(r"<style\b[\s\S]*?</style>", " ", page, flags=re.I)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page)).strip()


def _local_image_refs(page: str) -> set[str]:
    refs: set[str] = set()
    patterns = (
        r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']',
        r'<meta\b[^>]*(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]*\bcontent=["\']([^"\']+)["\']',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, page, re.I):
            value = match.group(1).strip()
            if value.startswith("https://freellm.top/"):
                value = "/" + value.split("https://freellm.top/", 1)[1]
            if value.startswith("/") and not value.startswith("//"):
                refs.add(value.split("?", 1)[0].split("#", 1)[0])
    return refs


def main() -> int:
    pages = [
        path for path in ROOT.rglob("*.html")
        if not any(_rel(path).startswith(prefix) for prefix in SKIP_PREFIXES)
    ]
    issues: dict[str, list[tuple[str, object]]] = {
        "missing_title": [],
        "title_short": [],
        "title_long": [],
        "missing_description": [],
        "description_short": [],
        "description_long": [],
        "low_word_count": [],
        "meta_refresh": [],
    }
    noindex: list[str] = []
    image_refs: set[str] = set()
    image_referrers: dict[str, set[str]] = {}
    page_cache: dict[str, str] = {}

    for path in pages:
        rel = _rel(path)
        page = path.read_text(encoding="utf-8", errors="replace")
        page_cache[rel] = page
        title = _title(page)
        desc = _attr(page, "description")
        robots = _attr(page, "robots")
        indexable = "noindex" not in robots.lower()

        if "noindex" in robots.lower():
            noindex.append(rel)
        if indexable:
            if not title:
                issues["missing_title"].append((rel, 0))
            elif len(title) < TITLE_MIN:
                issues["title_short"].append((rel, len(title)))
            elif len(title) > TITLE_MAX:
                issues["title_long"].append((rel, len(title)))
            if not desc:
                issues["missing_description"].append((rel, 0))
            elif len(desc) < DESC_MIN:
                issues["description_short"].append((rel, len(desc)))
            elif len(desc) > DESC_MAX:
                issues["description_long"].append((rel, len(desc)))
            visible = _visible_text(page)
            if len(visible) < LOW_TEXT_MIN:
                issues["low_word_count"].append((rel, len(visible)))
        if re.search(r'<meta\s+http-equiv=["\']refresh["\']', page, re.I):
            issues["meta_refresh"].append((rel, "refresh"))
        refs = _local_image_refs(page)
        image_refs |= refs
        for ref in refs:
            image_referrers.setdefault(ref, set()).add(rel)

    large_images = []
    for ref in sorted(image_refs):
        target = ROOT / ref.lstrip("/")
        if target.is_file() and target.stat().st_size > LARGE_IMAGE_BYTES:
            large_images.append((ref, target.stat().st_size, sorted(image_referrers.get(ref, set()))))

    groups: dict[str, int] = {}
    for rel in noindex:
        top = rel.split("/", 1)[0]
        groups[top] = groups.get(top, 0) + 1
    print(f"pages={len(pages)} intentional_noindex={len(noindex)} noindex_by_section={groups}")
    print(f"referenced_large_images={len(large_images)}")
    for ref, size, referrers in large_images:
        print(f"  IMAGE {size:>9} {ref}")
        for page in referrers[:20]:
            print(f"    referenced-by {page}")
    failure_count = 0
    for name, rows in issues.items():
        print(f"{name}={len(rows)}")
        for rel, value in rows[:40]:
            print(f"  {name} {value!s:>5} {rel}")
        if name != "meta_refresh":
            failure_count += len(rows)
    # Meta-refresh pages are legacy redirects and are reported separately.
    # Deliberate noindex pages are also informational; sitemap tests enforce
    # that they are not submitted for indexing.
    return 1 if failure_count or large_images else 0


if __name__ == "__main__":
    raise SystemExit(main())
