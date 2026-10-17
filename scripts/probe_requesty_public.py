"""Validate Requesty's anonymous public price catalog; never send an API key.

This checks the 13 $0 model *routes* published in FreeLLM. It is not an
inference benchmark and does not qualify a provider for the featured badge.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://router.requesty.ai/v1/models"


def report_public_catalog(root: Path = ROOT, timeout: float = 25) -> dict:
    offers = json.loads((root / "data/offers.json").read_text(encoding="utf-8"))
    models = json.loads((root / "data/models.json").read_text(encoding="utf-8"))
    offer = next(offer for offer in offers if offer.get("id") == "requesty-free")
    expected = {row["model"] for row in offer["freeModels"]}
    declared = {model["canonicalModelId"] for model in models if model.get("providerId") == "requesty"}
    if len(expected) != 13 or expected != declared:
        raise ValueError(f"FreeLLM route contract mismatch: offer={len(expected)} directory={len(declared)}")

    req = urllib.request.Request(API, headers={"Accept": "application/json", "User-Agent": "FreeLLM-SourceAudit/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"Catalog HTTP {response.status}")
        raw = response.read(10_000_001)
        if len(raw) > 10_000_000:
            raise ValueError("Catalog response exceeds safety limit")
    payload = json.loads(raw.decode("utf-8"))
    entries = payload.get("data")
    if not isinstance(entries, list):
        raise ValueError("Unexpected Requesty response shape")

    def zero(value: object) -> bool:
        return type(value) in (int, float) and value == 0

    free = {row["id"]: row for row in entries
            if isinstance(row, dict) and isinstance(row.get("id"), str)
            and zero(row.get("input_price")) and zero(row.get("output_price"))}
    missing = sorted(expected - set(free))
    extra = sorted(set(free) - expected)
    inspected = []
    for route in sorted(expected & set(free)):
        row = free[route]
        inspected.append({
            "id": route,
            "context_window": row.get("context_window"),
            "data_used_for_training": row.get("data_used_for_training"),
            "data_retention": row.get("data_retention"),
            "data_retention_days": row.get("data_retention_days"),
        })
    return {
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": API,
        "modelCount": len(entries),
        "freeRouteCount": len(free),
        "expectedRouteCount": len(expected),
        "missingFromFree": missing,
        "extraFreeRoutes": extra,
        "routes": inspected,
        "inferenceTested": False,
        "result": "match" if not missing and not extra else "changed",
    }


def main() -> int:
    try:
        result = report_public_catalog()
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, StopIteration, json.JSONDecodeError) as exc:
        print(f"REQUESTY_PUBLIC_CATALOG_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    output = ROOT / ".tmp" / "requesty-public-catalog.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "match" else 1


if __name__ == "__main__":
    raise SystemExit(main())
