"""Update offer observation timestamps from a public-source scan.

This intentionally does not change lastVerifiedAt, status, confidence, or any
human-reviewed claim. An offer is observed only when at least one configured
official source returned status=ok in the supplied scan.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def sync_offer_observations(offers: list[dict], scan_results: list[dict], as_of: str) -> list[dict]:
    observed_ids = {
        str(row.get("offerId"))
        for row in scan_results
        if isinstance(row, dict) and row.get("status") == "ok" and row.get("offerId")
    }
    merged: list[dict] = []
    for offer in offers:
        item = dict(offer)
        if str(item.get("id")) in observed_ids:
            item["lastObservedAt"] = as_of
        merged.append(item)
    return merged


def _read_list(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{path} must contain a JSON list")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offers", required=True)
    parser.add_argument("--scan", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args(argv)

    offers = _read_list(Path(args.offers))
    scan_results = _read_list(Path(args.scan))
    merged = sync_offer_observations(offers, scan_results, args.as_of)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    updated = sum(
        1
        for before, after in zip(offers, merged)
        if before.get("lastObservedAt") != after.get("lastObservedAt")
    )
    observed = sum(1 for row in merged if row.get("lastObservedAt") == args.as_of)
    print(f"offer observations: {observed} observed today, {updated} timestamps updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
