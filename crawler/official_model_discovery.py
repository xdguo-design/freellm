"""Discover model rows from each provider's own sources.

Design rules, in order of importance:

1. **Official first.** A provider's own model API or catalogue page is the
   preferred source and is labelled ``sourceKind="official"``.
2. **Public APIs are a labelled supplement.** When a provider publishes no
   machine-readable catalogue we may read a public model API, but the row is
   labelled ``sourceKind="public_api"`` so a reader can tell the two apart.
3. **Never a competing directory.** Nothing here reads another directory's
   rows. Every row is attributed to the endpoint it came from.
4. **Assert only what the source states.** Fields the source does not publish
   are left empty rather than guessed or copied from somewhere else.

The source registry lives in ``data/official-model-sources.json``.

This module only *discovers* rows. Reconciling them against the published
catalogue — preserving manual review fields and marking rows that stopped
appearing as stale — is ``scripts/sync_model_catalog.py``'s job, so there is
exactly one merge implementation in the codebase.
"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Callable

from crawler.fetch import fetch_public_text_resource

# Parser implementations we know how to run. ``openai_models`` covers any
# OpenAI-compatible ``GET /v1/models`` endpoint; ``openrouter_models`` handles
# OpenRouter's richer catalogue payload; ``ollama_tags`` reads Ollama's own
# registry listing.
SUPPORTED_SOURCE_TYPES = {"openai_models", "openrouter_models", "ollama_tags"}
SUPPORTED_KINDS = {"official", "public_api"}

# A source may only claim these; anything else is a configuration error.
_FIELD_TYPES = {
    "id": str,
    "providerId": str,
    "provider": str,
    "kind": str,
    "type": str,
    "url": str,
    "allowedDomains": list,
    "modelPageTemplate": str,
}


def _slug(value: object) -> str:
    """Slug used for the per-model page path. Kept deliberately conservative."""
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def validate_source_registry(sources: object) -> list[str]:
    """Return a list of configuration errors, empty when the registry is valid."""
    if not isinstance(sources, list):
        return ["official model source registry must contain a list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field, expected in _FIELD_TYPES.items():
            value = source.get(field)
            if value is None:
                errors.append(f"{prefix}: {field} is required")
            elif not isinstance(value, expected):
                errors.append(f"{prefix}: {field} must be a {expected.__name__}")
        source_id = source.get("id")
        if isinstance(source_id, str) and source_id.strip():
            if source_id in ids:
                errors.append(f"duplicate source id: {source_id}")
            ids.add(source_id)
        kind = source.get("kind")
        if isinstance(kind, str) and kind not in SUPPORTED_KINDS:
            errors.append(f"{prefix}: unsupported kind: {kind}")
        source_type = source.get("type")
        if isinstance(source_type, str) and source_type not in SUPPORTED_SOURCE_TYPES:
            errors.append(f"{prefix}: unsupported type: {source_type}")
        domains = source.get("allowedDomains")
        if isinstance(domains, list):
            if not domains or not all(isinstance(d, str) and d.strip() for d in domains):
                errors.append(f"{prefix}: allowedDomains must contain at least one domain")
        template = source.get("modelPageTemplate")
        # A per-model page normally carries a placeholder, but some catalogues
        # publish one shared page for every model. Either is acceptable; a
        # non-URL is not.
        if isinstance(template, str) and not template.startswith("https://"):
            errors.append(f"{prefix}: modelPageTemplate must be an https URL")
        if "freeOnly" in source and not isinstance(source["freeOnly"], bool):
            errors.append(f"{prefix}: freeOnly must be boolean")
        if "maxBytes" in source and not isinstance(source["maxBytes"], int):
            errors.append(f"{prefix}: maxBytes must be an integer")
    return errors


def _model_page_url(source: dict, **values: str) -> str:
    try:
        return str(source["modelPageTemplate"]).format(**values)
    except (KeyError, IndexError):
        return str(source["url"])


def _is_zero_price(value: object) -> bool:
    try:
        return float(str(value)) == 0.0
    except (TypeError, ValueError):
        return False


def parse_openai_models(payload: object, source: dict) -> list[dict]:
    """Parse an OpenAI-compatible ``GET /v1/models`` payload.

    These endpoints publish identifiers only, so context, modality and rate
    limits stay empty: the source does not state them and we do not guess.
    """
    if isinstance(payload, dict):
        rows = payload.get("data")
    else:
        rows = payload
    if not isinstance(rows, list):
        return []
    provider_id = str(source["providerId"])
    parsed: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("id") or "").strip()
        if not raw_id:
            continue
        owner, _, name = raw_id.partition("/")
        name = name or owner
        parsed.append({
            "providerId": provider_id,
            "provider": str(source["provider"]),
            "model": name,
            "modelSlug": _slug(name),
            "context": "",
            "maxOutput": "",
            "modality": ["unknown"],
            "rateLimit": "",
            "released": "",
            "usageActivity": "",
            "status": "online",
            "sourceUrl": _model_page_url(source, owner=owner, model=name, id=raw_id),
            "sourceKind": str(source["kind"]),
            "sourceEndpoint": str(source["url"]),
        })
    return parsed


def parse_openrouter_models(payload: object, source: dict) -> list[dict]:
    """Parse OpenRouter's catalogue payload, keeping only the free entries.

    OpenRouter is a public API rather than a provider's own catalogue, so these
    rows are labelled with whatever ``kind`` the registry declares. A model is
    treated as free only when the payload prices both prompt and completion at
    zero, which is the source's own statement about its own pricing.
    """
    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    provider_id = str(source["providerId"])
    free_only = bool(source.get("freeOnly", True))
    parsed: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("id") or "").strip()
        if not raw_id:
            continue
        pricing = row.get("pricing") if isinstance(row.get("pricing"), dict) else {}
        is_free = _is_zero_price(pricing.get("prompt")) and _is_zero_price(pricing.get("completion"))
        if free_only and not is_free:
            continue
        architecture = row.get("architecture") if isinstance(row.get("architecture"), dict) else {}
        modalities = [
            str(item).strip().lower()
            for key in ("input_modalities", "output_modalities")
            for item in (architecture.get(key) or [])
            if str(item).strip()
        ]
        params = row.get("supported_parameters") or []
        if isinstance(params, list) and "reasoning" in params:
            modalities.append("reasoning")
        # De-duplicate while preserving a stable order.
        modality = sorted(set(modalities)) or ["unknown"]
        top_provider = row.get("top_provider") if isinstance(row.get("top_provider"), dict) else {}
        context_length = row.get("context_length") or top_provider.get("context_length")
        max_output = top_provider.get("max_completion_tokens")
        name = str(row.get("name") or raw_id).strip()
        parsed.append({
            "providerId": provider_id,
            "provider": str(source["provider"]),
            "model": name,
            "modelSlug": _slug(raw_id),
            "context": str(context_length) if context_length else "",
            "maxOutput": str(max_output) if max_output else "",
            "modality": modality,
            "rateLimit": "",
            "released": "",
            "usageActivity": "",
            "status": "online",
            "sourceUrl": _model_page_url(source, id=raw_id),
            "sourceKind": str(source["kind"]),
            "sourceEndpoint": str(source["url"]),
            "freePricingConfirmed": is_free,
        })
    return parsed


def parse_ollama_tags(payload: object, source: dict) -> list[dict]:
    """Parse Ollama's own registry listing (``GET ollama.com/api/tags``).

    The payload states the model name and its on-disk size; it says nothing
    about context window, modality or rate limits, so those stay empty. The
    size is deliberately not carried into the catalogue: the published schema
    has no field for it and inventing one is out of scope here.
    """
    rows = payload.get("models") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    provider_id = str(source["providerId"])
    parsed: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("model") or "").strip()
        if not name:
            continue
        parsed.append({
            "providerId": provider_id,
            "provider": str(source["provider"]),
            "model": name,
            "modelSlug": _slug(name),
            "context": "",
            "maxOutput": "",
            "modality": ["unknown"],
            "rateLimit": "",
            "released": "",
            "usageActivity": "",
            "status": "online",
            "sourceUrl": _model_page_url(source, name=name, model=name, id=name),
            "sourceKind": str(source["kind"]),
            "sourceEndpoint": str(source["url"]),
        })
    return parsed


_PARSERS: dict[str, Callable[[object, dict], list[dict]]] = {
    "openai_models": parse_openai_models,
    "openrouter_models": parse_openrouter_models,
    "ollama_tags": parse_ollama_tags,
}


def _failure(source_id: str, url: str, response: dict) -> dict:
    return {
        "providerId": source_id,
        "url": url,
        "sourceKind": "official_model_source",
        "status": response.get("status", "failed"),
        "reason": response.get("reason", "official source was unavailable"),
    }


def discover_official_model_sources(
    sources: object,
    fetcher: Callable[[str, list[str], int, int], dict] = fetch_public_text_resource,
    max_models: int = 1000,
) -> dict:
    """Fetch every enabled source and return ``{"models": [...], "failures": [...]}``.

    A source that fails, times out or exceeds its size budget produces a failure
    record and the remaining sources still run.
    """
    errors = validate_source_registry(sources)
    if errors:
        raise ValueError("invalid official model source registry: " + "; ".join(errors))

    models: list[dict] = []
    failures: list[dict] = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        source_id = str(source["id"])
        parser = _PARSERS[str(source["type"])]
        domains = list(source["allowedDomains"])
        max_bytes = int(source.get("maxBytes", 200_000))
        response = fetcher(str(source["url"]), domains, int(source.get("timeout", 15)), max_bytes)
        if response.get("status") != "ok":
            failures.append(_failure(source_id, str(source["url"]), response))
            continue
        try:
            payload = json.loads(str(response.get("content") or ""))
        except json.JSONDecodeError as error:
            failures.append(_failure(source_id, str(source["url"]), {"status": "failed", "reason": f"invalid JSON: {error}"}))
            continue
        for row in parser(payload, source):
            if len(models) >= max_models:
                break
            models.append(row)
    return {"models": models, "failures": failures}


def write_json(path, value: object) -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def today() -> str:
    return date.today().isoformat()
