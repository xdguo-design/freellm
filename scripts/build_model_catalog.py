"""Build the queryable provider/model catalog from a public directory snapshot."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.fetch import fetch_public_text_resource
from crawler.freellm_net_discovery import discover_freellm_net_sources


def _write_json(path: str | Path, value: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _score(value: object) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def _modality(value: object) -> list[str]:
    return [item.strip().lower() for item in re.split(r"[,/·|]+", str(value or "")) if item.strip()]


def _status(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"online", "offline", "degraded"} else "unknown"


def build_model_catalog(rows: list[dict], last_seen_at: str) -> list[dict]:
    """Normalize discovery rows into one stable, provider/model query record."""
    models: list[dict] = []
    seen_ids: set[str] = set()
    for row in rows:
        provider_id = str(row.get("directoryProviderSlug") or "").strip()
        model_slug = str(row.get("modelSlug") or "").strip()
        if not provider_id or not model_slug:
            continue
        model_id = f"{provider_id}/{model_slug}"
        if model_id in seen_ids:
            continue
        seen_ids.add(model_id)
        models.append({
            "id": model_id,
            "providerId": provider_id,
            "provider": str(row.get("directoryProvider") or "").strip(),
            "model": str(row.get("model") or "").strip(),
            "score": _score(row.get("score")),
            "context": str(row.get("context") or "").strip(),
            "maxOutput": str(row.get("maxOutput") or "").strip(),
            "modality": _modality(row.get("modality")) or ["unknown"],
            "rateLimit": str(row.get("rateLimit") or "").strip(),
            "released": str(row.get("released") or "").strip(),
            "usageActivity": str(row.get("usageActivity") or "").strip(),
            "status": _status(row.get("directoryStatus") or row.get("status")),
            "sourceUrl": str(row.get("directoryUrl") or "").strip(),
            "sourceKind": "third_party_directory",
            "lastSeenAt": last_seen_at,
            "directoryFree": bool(row.get("directoryFree")),
            "directoryNoCard": bool(row.get("directoryNoCard")),
            "directoryVerified": bool(row.get("directoryVerified")),
            "tierType": str(row.get("tierType") or "").strip(),
        })
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


def discover_rows(sources_path: str | Path, max_models: int = 1000, timeout: int = 20) -> list[dict]:
    sources = json.loads(Path(sources_path).read_text(encoding="utf-8"))
    return discover_freellm_net_sources(
        sources,
        fetcher=lambda url, domains: fetch_public_text_resource(
            url, domains, timeout=timeout, max_bytes=5_000_000
        ),
        max_models=max_models,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="data/third-party-discovery-sources.json")
    parser.add_argument("--models-out", default="data/models.json")
    parser.add_argument("--providers-out", default="data/provider-catalog.json")
    parser.add_argument("--date", required=True, help="Snapshot date in YYYY-MM-DD format")
    parser.add_argument("--max-models", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    records = discover_rows(args.sources, max_models=args.max_models, timeout=args.timeout)
    models = build_model_catalog(records, args.date)
    providers = build_provider_catalog(models, args.date, load_operation_guides(Path(args.providers_out).parent / "operations"))
    _write_json(args.models_out, models)
    _write_json(args.providers_out, providers)
    print(f"model catalog: {len(models)} models across {len(providers)} providers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
