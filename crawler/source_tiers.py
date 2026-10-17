"""One definition of which catalogue sources are third-party relays.

LLM7 and Kilo re-serve other labs' models (Kilo is an OpenRouter white-label).
Their rows are useful, but they must never read as the model maker's own
official free tier. Every page, the homepage and the daily log use this module
instead of hard-coding provider ids.
"""

from __future__ import annotations

THIRD_PARTY_RELAY_TIER = "third_party_relay"
THIRD_PARTY_RELAY_PROVIDERS: dict[str, str] = {
    "llm7-io": "LLM7",
    "kilo": "Kilo Gateway",
    "kilo-code": "Kilo Code",
}
THIRD_PARTY_LABEL_ZH = "第三方聚合 · 非官方"
THIRD_PARTY_LABEL_EN = "Third-party aggregator · not official"
THIRD_PARTY_SHORT_ZH = "第三方"


def provider_id_of(record: dict | None) -> str:
    """Best-effort provider id for a model, provider or daily-log event."""
    if not isinstance(record, dict):
        return ""
    details = record.get("details") if isinstance(record.get("details"), dict) else {}
    for value in (record.get("providerId"), details.get("providerId")):
        if str(value or "").strip():
            return str(value).strip().lower()
    if record.get("kind") in (None, "model"):
        record_id = str(record.get("id") or details.get("id") or "")
        if "/" in record_id:
            return record_id.split("/", 1)[0].strip().lower()
    return ""


def is_third_party_relay(record: dict | None = None, provider_id: str = "") -> bool:
    """True for third-party relays/aggregators (by provider id or explicit tier)."""
    if provider_id and provider_id.strip().lower() in THIRD_PARTY_RELAY_PROVIDERS:
        return True
    if not isinstance(record, dict):
        return False
    details = record.get("details") if isinstance(record.get("details"), dict) else {}
    for source in (record, details):
        if str(source.get("sourceTier") or "").lower() == THIRD_PARTY_RELAY_TIER:
            return True
        if str(source.get("sourceKind") or "").lower() == "third_party_aggregator":
            return True
    if record.get("kind") not in (None, "model"):
        return False
    return provider_id_of(record) in THIRD_PARTY_RELAY_PROVIDERS
