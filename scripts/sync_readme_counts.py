#!/usr/bin/env python3
"""Keep README catalog numbers in sync with published FreeLLM source data.

The README is a public factual claim, so generated catalog updates must update
both languages instead of leaving yesterday's numbers in the repository.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZH = re.compile(
    r"^- \*\*\d+ 个\*\*资源目录记录（\d+ 条当前有效、\d+ 条已结束；最近一次扫描观测到 \d+ 条资源），另有 \*\*\d+ 条\*\*第三方模型目录记录和 \*\*\d+ 家\*\*厂家目录$",
    re.M,
)
EN = re.compile(
    r"^- \*\*\d+\*\* curated offer records \(\d+ currently active and \d+ ended; the latest scan observed \d+ offers\), plus \*\*\d+\*\* third-party model-directory records across \*\*\d+\*\* providers$",
    re.M,
)


def render(text: str, scan: dict, offers: list, models: list, providers: list) -> str:
    total = len(offers)
    model_count = len(models)
    provider_count = len(providers)
    active = scan.get("offers")
    expired = scan.get("offersExpired")
    seen = scan.get("scannedOffers")
    for key, value in {"offers": active, "offersExpired": expired, "scannedOffers": seen}.items():
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"missing or invalid scan summary count: {key}")
    if active + expired != total:
        raise ValueError("scan summary active and expired totals do not match source offers")
    zh = (
        f"- **{total} 个**资源目录记录（{active} 条当前有效、{expired} 条已结束；最近一次扫描观测到 {seen} 条资源），"
        f"另有 **{model_count} 条**第三方模型目录记录和 **{provider_count} 家**厂家目录"
    )
    en = (
        f"- **{total}** curated offer records ({active} currently active and {expired} ended; "
        f"the latest scan observed {seen} offers), plus **{model_count}** "
        f"third-party model-directory records across **{provider_count}** providers"
    )
    updated, zh_count = ZH.subn(lambda _: zh, text)
    updated, en_count = EN.subn(lambda _: en, updated)
    if zh_count != 1 or en_count != 1:
        raise ValueError(f"README catalog count anchors changed (zh={zh_count}, en={en_count})")
    return updated


def run(root: Path, check: bool = False) -> bool:
    source = root / "README.md"
    scan = json.loads((root / "data/scan-summary.json").read_text(encoding="utf-8"))
    offers = json.loads((root / "data/offers.json").read_text(encoding="utf-8"))
    models = json.loads((root / "data/models.json").read_text(encoding="utf-8"))
    providers = json.loads((root / "data/providers.json").read_text(encoding="utf-8"))
    before = source.read_text(encoding="utf-8")
    after = render(before, scan, offers, models, providers)
    if check:
        if before != after:
            print("stale README catalog counts; run python scripts/sync_readme_counts.py")
            return False
        print("current README catalog counts")
        return True
    if before != after:
        source.write_text(after, encoding="utf-8")
        print("updated README catalog counts")
    else:
        print("README catalog counts already current")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    return 0 if run(args.root, args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
