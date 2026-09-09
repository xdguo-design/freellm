"""Reconcile a fresh model-directory snapshot with the previous catalog."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MANUAL_FIELDS = {
    "verificationStatus",
    "lastVerifiedAt",
    "manualNote",
    "reviewNotes",
    "verificationNotes",
    "canonicalModel",
    "aliasOf",
}


def _validate_date(value: str) -> str:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError("as_of must use YYYY-MM-DD")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("as_of must use YYYY-MM-DD") from exc
    return value


def _stable_key(record: dict) -> tuple[str, str, str]:
    provider_id = str(record.get("providerId") or "").strip()
    model_id = str(record.get("modelId") or record.get("id") or record.get("model") or "").strip()
    directory_url = str(record.get("directoryUrl") or record.get("sourceUrl") or "").strip()
    if not provider_id or not model_id or not directory_url:
        raise ValueError("each model record needs providerId, modelId/id/model and directoryUrl/sourceUrl")
    return provider_id, model_id, directory_url


def _index(records: list[dict]) -> dict[tuple[str, str, str], dict]:
    indexed: dict[tuple[str, str, str], dict] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("model catalog records must be objects")
        key = _stable_key(record)
        if key in indexed:
            raise ValueError(f"duplicate model catalog key: {'/'.join(key)}")
        indexed[key] = record
    return indexed


def sync_model_catalog(discovered: list[dict], previous: list[dict], as_of: str) -> list[dict]:
    """Merge a discovery snapshot while retaining manual review fields and stale rows."""
    as_of = _validate_date(as_of)
    current = _index(discovered)
    old = _index(previous)
    merged: list[dict] = []

    for key, record in current.items():
        item = dict(record)
        prior = old.get(key)
        if prior:
            for field in MANUAL_FIELDS:
                if field in prior:
                    item[field] = prior[field]
            item["freshnessStatus"] = "current"
        else:
            item["freshnessStatus"] = "new"
        item["lastSeenAt"] = as_of
        merged.append(item)

    for key, record in old.items():
        if key in current:
            continue
        item = dict(record)
        item["freshnessStatus"] = "stale"
        item.setdefault("staleSince", as_of)
        merged.append(item)

    return sorted(merged, key=lambda item: (str(item.get("providerId") or ""), str(item.get("modelId") or item.get("id") or ""), str(item.get("sourceUrl") or item.get("directoryUrl") or "")))


def _read_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge a model discovery snapshot into the stable catalog")
    parser.add_argument("--input", required=True, help="Fresh discovery JSON list")
    parser.add_argument("--output", required=True, help="Merged catalog JSON output")
    parser.add_argument("--as-of", required=True, help="Snapshot date in YYYY-MM-DD")
    parser.add_argument("--previous", help="Previous catalog JSON; defaults to the output file when it exists")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    previous_path = Path(args.previous) if args.previous else output_path
    discovered = _read_records(input_path)
    previous = _read_records(previous_path) if previous_path.is_file() else []
    merged = sync_model_catalog(discovered, previous, args.as_of)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {status: sum(item.get("freshnessStatus") == status for item in merged) for status in ("new", "current", "stale")}
    print(f"synced model catalog: {len(merged)} records ({counts['new']} new, {counts['current']} current, {counts['stale']} stale)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
