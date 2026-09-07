"""Validate and aggregate public platform signals without inventing scores."""

from __future__ import annotations

from datetime import datetime
import math
import re
from urllib.parse import urlparse


SIGNAL_TYPES = {"rating", "review", "stars", "likes", "downloads", "rank", "sentiment"}
SIGNAL_STATUSES = {"observed", "needs_review", "source_unavailable"}
REQUIRED_FIELDS = {"offerId", "sourcePlatform", "sourceType", "sourceUrl", "rawLabel", "capturedAt", "status"}
SENSITIVE_ASSIGNMENT = re.compile(r"(?:api[_-]?key|password|secret|access[_-]?token|token)\s*[:=]", re.I)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PRIVATE_ADDRESS = re.compile(r"\b(?:localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b", re.I)


def _https_url(value: object) -> bool:
    if not isinstance(value, str) or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def redact_excerpt(text: object, limit: int = 240) -> str:
    """Keep a short public excerpt while removing obvious sensitive data."""
    if not isinstance(text, str):
        return ""
    safe_lines = [line for line in text.splitlines() if not SENSITIVE_ASSIGNMENT.search(line)]
    safe = "\n".join(safe_lines)
    safe = EMAIL.sub("[redacted email]", safe)
    safe = PRIVATE_ADDRESS.sub("[redacted private address]", safe)
    return " ".join(safe.split())[:limit]


def validate_signal_record(record: object) -> list[str]:
    if not isinstance(record, dict):
        return ["signal must be an object"]

    errors: list[str] = []
    errors.extend(f"missing field: {field}" for field in sorted(REQUIRED_FIELDS - record.keys()))
    for field in ("offerId", "sourcePlatform", "rawLabel"):
        if field in record and (not isinstance(record[field], str) or not record[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    source_type = record.get("sourceType")
    if source_type not in SIGNAL_TYPES:
        errors.append(f"sourceType is not supported: {source_type}")
    if "sourceUrl" in record and not _https_url(record["sourceUrl"]):
        errors.append("sourceUrl must be an HTTPS URL without credentials")
    captured_at = record.get("capturedAt")
    if isinstance(captured_at, str):
        try:
            datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("capturedAt must be an ISO-8601 timestamp")
    if record.get("status") not in SIGNAL_STATUSES:
        errors.append(f"status is not supported: {record.get('status')}")

    if source_type == "rating":
        value = record.get("value")
        scale_max = record.get("scaleMax")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            errors.append("rating value must be a finite number")
        if not isinstance(scale_max, (int, float)) or isinstance(scale_max, bool) or scale_max <= 0:
            errors.append("rating scaleMax must be a positive number")
        if isinstance(value, (int, float)) and isinstance(scale_max, (int, float)) and value > scale_max:
            errors.append("rating value cannot exceed scaleMax")
    elif source_type in {"review", "sentiment"}:
        if "value" in record or "scaleMax" in record:
            errors.append(f"{source_type} cannot carry a platform rating value")
    else:
        value = record.get("value")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
            errors.append(f"{source_type} value must be a non-negative number")

    sample_count = record.get("sampleCount")
    if sample_count is not None and (not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 0):
        errors.append("sampleCount must be a non-negative integer")
    if "excerpt" in record and not isinstance(record["excerpt"], str):
        errors.append("excerpt must be a string")
    return errors


def validate_signals(records: object) -> list[str]:
    if not isinstance(records, list):
        return ["signals must contain a list"]
    errors: list[str] = []
    for index, record in enumerate(records):
        errors.extend(f"signals[{index}]: {error}" for error in validate_signal_record(record))
    return errors


def _signal_key(record: dict) -> tuple[str, str, str, str]:
    return (
        str(record.get("offerId", "")),
        str(record.get("sourcePlatform", "")),
        str(record.get("sourceType", "")),
        str(record.get("sourceUrl", "")),
    )


def _safe_record(record: dict, captured_at: str | None = None) -> dict:
    safe = dict(record)
    if not safe.get("capturedAt") and captured_at:
        safe["capturedAt"] = captured_at
    if "excerpt" in safe:
        safe["excerpt"] = redact_excerpt(safe["excerpt"])
    return safe


def merge_signals(existing: list[dict], discovered: list[dict], captured_at: str | None = None) -> list[dict]:
    """Replace a stale copy of the same platform signal and keep other platforms."""
    merged: dict[tuple[str, str, str, str], dict] = {}
    for record in [*existing, *discovered]:
        if not isinstance(record, dict) or validate_signal_record(record):
            continue
        safe = _safe_record(record, captured_at=captured_at)
        merged[_signal_key(safe)] = safe
    return sorted(
        merged.values(),
        key=lambda record: (
            str(record.get("offerId", "")),
            str(record.get("sourcePlatform", "")),
            str(record.get("sourceType", "")),
            str(record.get("sourceUrl", "")),
        ),
    )


def group_signals_by_offer(signals: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for record in signals:
        if not isinstance(record, dict) or validate_signal_record(record):
            continue
        offer_id = str(record["offerId"])
        grouped.setdefault(offer_id, []).append(dict(record))
    for records in grouped.values():
        records.sort(key=lambda record: (str(record.get("sourcePlatform", "")), str(record.get("sourceType", ""))))
    return dict(sorted(grouped.items()))
