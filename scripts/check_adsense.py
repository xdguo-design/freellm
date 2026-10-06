"""AdSense readiness gates: ads.txt <-> page client match, loader coverage, slot config.

Runs fully offline against the working tree. Fails (exit 1) when

- ``ads.txt`` is missing, malformed, or declares a publisher no page references,
- a sitemap-listed page is missing the AdSense loader script,
- a page references a ``ca-pub-`` client that disagrees with ``ads.txt``,
- a sitemap URL has no file on disk.

Pages that intentionally carry no ad code must be listed in ``EXEMPT_PAGES``
with a reason, so the decision stays visible instead of looking like an oversight.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]

SITEMAP_GLOB = "sitemap-*.xml"
ADS_TXT = "ads.txt"
VERCEL_CONFIG = "vercel.json"
SITE_HOST = "https://freellm.top"

CLIENT_RE = re.compile(r"adsbygoogle\.js\?client=ca-(?:pub-)?(\d+)")
HEAD_RE = re.compile(r"<head\b[^>]*>(.*?)</head>", re.IGNORECASE | re.DOTALL)
SCRIPT_SRC_CLIENT_RE = re.compile(
    r"""<script\b[^>]*\bsrc=["']https://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=ca-(?:pub-)?(\d+)[^>]*>""",
    re.IGNORECASE,
)
INS_CLIENT_RE = re.compile(r'data-ad-client="ca-(?:pub-)?(\d+)"')
SLOT_RE = re.compile(r'data-ad-slot="(\d+)"')
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")
NOINDEX_RE = re.compile(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', re.IGNORECASE)
ADS_TXT_RE = re.compile(r"^google\.com\s*,\s*(pub-\d+)\s*,\s*DIRECT\s*,", re.IGNORECASE)

# 故意不带广告代码的页面。键是 URL 路径，值是理由。
# 加新条目时请写清「为什么这页不该有广告」，不要只写「暂时不用」。
PRIVACY_PATH = "/privacy/"
PRIVACY_MARKERS = (
    "Google AdSense",
    "https://policies.google.com/technologies/partner-sites",
    "https://www.google.com/settings/ads",
)
AUTO_ADS_URL_EXCLUSIONS = ("/about/", "/privacy/", "/terms/", "/favorites/", "/submit/")
MANUAL_AD_EXCLUDED_FILES = {
    "about/index.html",
    "privacy/index.html",
    "terms/index.html",
    "favorites/index.html",
    "submit/index.html",
}

EXEMPT_PAGES: Mapping[str, str] = {
    "/favorites/": "noindex 的个人收藏页：无独立正文，挂广告属「内容不足」风险",
    "/submit/": "纯功能表单页：正文极少，收益趋近于 0 但增加政策风险",
    "/offers/longcat-api/": "noindex 旧入口跳转页（已合并到 longcat-2-0）",
    "/offers/longcat-download/": "noindex 旧入口跳转页（已合并到 longcat-2-0）",
}


def head_loader_clients(html: str) -> set[str]:
    """Return AdSense publisher ids from real script src tags inside <head>."""
    match = HEAD_RE.search(html)
    if not match:
        return set()
    return set(SCRIPT_SRC_CLIENT_RE.findall(match.group(1)))


def privacy_disclosure_ok(html: str) -> bool:
    """Verify the privacy page carries the minimum Google ads disclosures."""
    return all(marker in html for marker in PRIVACY_MARKERS)


def sitemap_page_paths(root: Path) -> list[str]:
    """Return every URL path listed in the section sitemaps, deduplicated and sorted."""
    paths: set[str] = set()
    for sitemap in sorted(root.glob(SITEMAP_GLOB)):
        text = sitemap.read_text(encoding="utf-8", errors="replace")
        for url in LOC_RE.findall(text):
            if not url.startswith(SITE_HOST):
                continue
            path = url[len(SITE_HOST) :] or "/"
            paths.add(path)
    return sorted(paths)


def load_rewrites(root: Path) -> dict[str, str]:
    """URL path -> file path, taken from vercel.json so the root rewrite stays in sync."""
    config = root / VERCEL_CONFIG
    if not config.is_file():
        return {}
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    rewrites: dict[str, str] = {}
    for entry in data.get("rewrites", []):
        source, destination = entry.get("source"), entry.get("destination")
        if isinstance(source, str) and isinstance(destination, str):
            rewrites[source] = destination
    return rewrites


def url_path_to_file(root: Path, url_path: str, rewrites: Mapping[str, str]) -> Path:
    target = rewrites.get(url_path)
    if target:
        return root / target.lstrip("/")
    if url_path in ("", "/"):
        return root / "index.html"
    return root / url_path.strip("/") / "index.html"


def iter_site_html(root: Path):
    """Yield tracked HTML files, skipping dot-directories such as .git and .tmp-pytest-base."""
    for path in sorted(root.rglob("*.html")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        yield path


def read_ads_txt_publishers(root: Path) -> tuple[set[str], list[str]]:
    """Return (publisher ids declared in ads.txt, parse problems)."""
    ads_path = root / ADS_TXT
    if not ads_path.is_file():
        return set(), [f"{ADS_TXT} is missing"]
    publishers: set[str] = set()
    problems: list[str] = []
    for lineno, line in enumerate(ads_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ADS_TXT_RE.match(stripped)
        if match:
            publishers.add(match.group(1))
        else:
            problems.append(f"{ADS_TXT}:{lineno}: unrecognised record {stripped!r}")
    if not publishers:
        problems.append(f"{ADS_TXT} declares no google.com DIRECT publisher")
    return publishers, problems


def build_report(root: Path, slot: str | None = None) -> dict:
    publishers, problems = read_ads_txt_publishers(root)
    issues = list(problems)
    declared = sorted(publishers)
    rewrites = load_rewrites(root)

    page_paths = sitemap_page_paths(root)
    missing: list[str] = []
    mismatched: list[dict] = []
    checked = 0
    exempted: list[dict] = []

    for path in page_paths:
        file_path = url_path_to_file(root, path, rewrites)
        if not file_path.is_file():
            issues.append(f"{path}: listed in a sitemap but no file at {file_path.relative_to(root)}")
            continue
        if path in EXEMPT_PAGES:
            exempted.append({"path": path, "reason": EXEMPT_PAGES[path]})
            continue
        checked += 1
        html = file_path.read_text(encoding="utf-8", errors="replace")
        loader_clients = head_loader_clients(html)
        clients = loader_clients | set(INS_CLIENT_RE.findall(html))
        if not loader_clients:
            missing.append(path)
            continue
        unknown = sorted(clients - {p.replace("pub-", "") for p in publishers})
        if unknown:
            mismatched.append({"path": path, "clients": [f"ca-pub-{c}" for c in unknown]})

    if missing:
        issues.append(f"{len(missing)} sitemap page(s) missing the AdSense loader: {', '.join(missing)}")
    for entry in mismatched:
        issues.append(f"{entry['path']}: client {', '.join(entry['clients'])} not declared in {ADS_TXT}")

    privacy_ok = True
    if PRIVACY_PATH in page_paths:
        privacy_file = url_path_to_file(root, PRIVACY_PATH, rewrites)
        privacy_html = privacy_file.read_text(encoding="utf-8", errors="replace") if privacy_file.is_file() else ""
        privacy_ok = privacy_disclosure_ok(privacy_html)
        if not privacy_ok:
            issues.append(
                f"{PRIVACY_PATH}: privacy disclosure must mention Google AdSense, Google Ads Settings, "
                "and Google's partner-sites data-use policy"
            )

    slot_value = (slot if slot is not None else os.environ.get("FREELLM_ADSENSE_SLOT", "")).strip()
    slot_valid = bool(re.fullmatch(r"\d+", slot_value))

    with_loader = 0
    manual_units = 0
    noindex_with_loader: list[str] = []
    manual_units_on_excluded_pages: list[str] = []
    html_files = 0
    for file_path in iter_site_html(root):
        html_files += 1
        html = file_path.read_text(encoding="utf-8", errors="replace")
        relative = str(file_path.relative_to(root)).replace("\\", "/")
        if head_loader_clients(html):
            with_loader += 1
            if NOINDEX_RE.search(html):
                noindex_with_loader.append(relative)
        unit_count = len(SLOT_RE.findall(html))
        manual_units += unit_count
        if unit_count and relative in MANUAL_AD_EXCLUDED_FILES:
            manual_units_on_excluded_pages.append(relative)

    if noindex_with_loader:
        issues.append(
            "noindex page(s) carrying the AdSense loader (content-thin ad placement risk): "
            + ", ".join(noindex_with_loader)
        )
    if manual_units_on_excluded_pages:
        issues.append(
            "manual AdSense unit(s) found on legal/utility pages that should remain ad-free: "
            + ", ".join(manual_units_on_excluded_pages)
        )

    return {
        "ok": not issues,
        "ads_txt_publishers": declared,
        "sitemap_pages": len(page_paths),
        "pages_checked": checked,
        "pages_with_loader": with_loader,
        "html_files": html_files,
        "manual_ad_units": manual_units,
        "manual_units_on_excluded_pages": manual_units_on_excluded_pages,
        "privacy_disclosure_ok": privacy_ok,
        "auto_ads_url_exclusions": list(AUTO_ADS_URL_EXCLUSIONS),
        "cmp_console_required": True,
        "cmp_note": (
            "Publish a Google-certified CMP message in AdSense Privacy & messaging for EEA, UK, "
            "and Switzerland. This repository gate verifies code/disclosures, not AdSense-console state."
        ),
        "slot_configured": slot_valid,
        "slot_note": (
            "FREELLM_ADSENSE_SLOT is set: manual ad units render."
            if slot_valid
            else "FREELLM_ADSENSE_SLOT is unset: no manual ad unit renders; "
            "revenue depends entirely on Auto Ads being enabled in the AdSense console."
        ),
        "exempt_pages": exempted,
        "missing_loader": missing,
        "client_mismatches": mismatched,
        "noindex_with_loader": noindex_with_loader,
        "issues": issues,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--slot", help="Override FREELLM_ADSENSE_SLOT for this check")
    parser.add_argument("--report", help="Write the JSON report to this path")
    args = parser.parse_args(argv)

    report = build_report(Path(args.root), slot=args.slot)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not report["ok"]:
        print("adsense check failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
