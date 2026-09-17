"""Build the provider/model catalog from provider-official sources.

Sources are declared in ``data/official-model-sources.json``. A row is labelled
``sourceKind="official"`` when it comes from the provider's own catalogue and
``sourceKind="public_api"`` when it comes from a public model API used as a
labelled supplement. Nothing here reads a competing directory.

This script only *produces a snapshot*. Reconciling that snapshot into the
published ``data/models.json`` — preserving manual review fields and marking
rows that stopped appearing as stale — is ``scripts/sync_model_catalog.py``'s
job.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.fetch import fetch_public_text_resource
from crawler.official_model_discovery import (
    discover_official_model_sources,
    to_catalog_rows,
    validate_source_registry,
)


def _write_json(path: str | Path, value: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_source_registry(path: str | Path) -> list[dict]:
    """Read and validate the official model source registry."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_source_registry(data)
    if errors:
        raise ValueError("invalid official model source registry: " + "; ".join(errors))
    return data


def build_model_catalog(rows: list[dict], last_seen_at: str) -> list[dict]:
    """Normalize discovery rows into one stable, provider/model query record."""
    models = to_catalog_rows(rows)
    for model in models:
        model["lastSeenAt"] = last_seen_at
    return models


def build_provider_catalog(models: list[dict], last_seen_at: str, operation_guides: list[dict] | None = None) -> list[dict]:
    grouped: dict[str, dict] = {}
    for model in models:
        provider_id = str(model["providerId"])
        provider = grouped.setdefault(provider_id, {
            "id": provider_id,
            "name": model["provider"],
            "modelCount": 0,
            "modelIds": [],
            "sourceKind": "catalog",
            "lastSeenAt": last_seen_at,
        })
        provider["modelCount"] += 1
        provider["modelIds"].append(model["id"])
    for guide in operation_guides or []:
        provider_id = str(guide.get("providerId") or "").strip()
        if provider_id and provider_id not in grouped:
            grouped[provider_id] = {
                "id": provider_id,
                "name": str(guide.get("provider") or provider_id),
                "modelCount": 0,
                "modelIds": [],
                "sourceKind": "operation",
                "lastSeenAt": str(guide.get("lastVerifiedAt") or last_seen_at),
            }
    return [grouped[key] for key in sorted(grouped)]


def load_operation_guides(directory: str | Path) -> list[dict]:
    operation_dir = Path(directory)
    if not operation_dir.is_dir():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(operation_dir.glob("*.json"))]


def load_curated(path: str | Path) -> list[dict]:
    """Hand-verified rows that no discovery source publishes.

    These are our own records, so they take precedence over anything a source
    reports for the same ``id``.
    """
    target = Path(path)
    if not target.is_file():
        return []
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{target} must contain a JSON list")
    for index, row in enumerate(data):
        if not isinstance(row, dict) or not str(row.get("id") or "").strip():
            raise ValueError(f"{target}[{index}] must be an object with an id")
    return data


def discover_rows(sources_path: str | Path, max_models: int = 1000, timeout: int = 20, curated_path: str | Path | None = None) -> dict:
    """Fetch every enabled source; return ``{"models": [...], "failures": [...]}``.

    Hand-curated rows are prepended so that, if a source ever reports the same
    ``id``, our own verified record wins.
    """
    sources = load_source_registry(sources_path)
    result = discover_official_model_sources(
        sources,
        fetcher=lambda url, domains, source_timeout, max_bytes: fetch_public_text_resource(
            url, domains, timeout=timeout or source_timeout, max_bytes=max_bytes
        ),
        max_models=max_models,
    )
    if curated_path:
        result["models"] = load_curated(curated_path) + result["models"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="data/official-model-sources.json")
    parser.add_argument("--curated", default="data/models-curated.json")
    parser.add_argument("--models-out", default="data/models.json")
    parser.add_argument("--providers-out", default="data/provider-catalog.json")
    parser.add_argument("--date", required=True, help="Snapshot date in YYYY-MM-DD format")
    parser.add_argument("--max-models", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    result = discover_rows(args.sources, max_models=args.max_models, timeout=args.timeout, curated_path=args.curated)
    models = build_model_catalog(result["models"], args.date)
    providers = build_provider_catalog(models, args.date, load_operation_guides(Path(args.providers_out).parent / "operations"))
    _write_json(args.models_out, models)
    _write_json(args.providers_out, providers)
    # A source that fails must be visible, not silently absent from the catalog.
    for failure in result["failures"]:
        print(f"source failed: {failure['providerId']} ({failure['url']}): {failure['reason']}")
    # So must rows a source listed twice under different names: dropping them is
    # right, but it has to show up in the build output.
    collapsed = len(result["models"]) - len(models)
    summary = f"model catalog: {len(models)} models across {len(providers)} providers, {len(result['failures'])} source failures"
    if collapsed:
        summary += f", {collapsed} duplicate ids collapsed"
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
