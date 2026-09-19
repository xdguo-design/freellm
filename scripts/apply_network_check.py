"""Fold the network probe report into data/offers.json as `networkCheck`.

Keeps the hand-maintained formatting of data/offers.json byte-identical apart
from the new field: indent=1, ensure_ascii=False, one trailing newline, LF.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGION_VALUES = {"both", "cn", "intl", "none"}
SPEED_GRADES = {"fast", "normal", "slow", "very_slow"}


def build_entry(entry: dict) -> dict:
    """Only what the cards actually render.

    The homepage embeds every offer inline, and the page has a hard byte
    budget, so the shared method/note text lives in the renderers as a
    constant instead of being repeated 45 times in the payload.
    """
    region = entry.get("region")
    if region not in REGION_VALUES:
        raise SystemExit(f"unexpected region {region!r} for {entry.get('id')}")
    speed = entry.get("speedGrade")
    if speed is not None and speed not in SPEED_GRADES:
        raise SystemExit(f"unexpected speedGrade {speed!r} for {entry.get('id')}")
    payload = {
        "checkedAt": None,  # filled by caller
        "region": region,
        "cnHost": entry.get("cnHost"),
        "cnMs": entry.get("cnMs"),
        "intlMs": entry.get("intlMs"),
    }
    dead = entry.get("deadTargets") or []
    if dead:
        payload["deadTargets"] = dead
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=".tmp-network-report.json")
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--date", default=None, help="override checkedAt (YYYY-MM-DD)")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    checked_at = args.date or report["generatedAt"][:10]

    data_path = Path(args.data)
    raw = data_path.read_bytes()
    offers = json.loads(raw.decode("utf-8"))
    by_id = {entry["id"]: entry for entry in report["results"]}

    missing = [offer["id"] for offer in offers if offer["id"] not in by_id]
    if missing:
        print(f"report is missing {len(missing)} offers: {', '.join(missing[:6])}", file=sys.stderr)
        return 1

    for offer in offers:
        payload = build_entry(by_id[offer["id"]])
        payload["checkedAt"] = checked_at
        offer["networkCheck"] = payload

    rendered = json.dumps(offers, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if rendered.encode("utf-8") != raw:
            print(f"stale: {data_path} does not match the current network report")
            return 1
        print(f"current: {data_path}")
        return 0

    with data_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)
    counts: dict[str, int] = {}
    for offer in offers:
        region = offer["networkCheck"]["region"]
        counts[region] = counts.get(region, 0) + 1
    print(f"wrote {data_path}: {json.dumps(counts, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
