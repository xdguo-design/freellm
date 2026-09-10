"""Build append-only daily records for newly observed and unavailable entries."""

from __future__ import annotations

import json
import re
from pathlib import Path


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OFFLINE_STATES = {"offline", "expired", "retired", "unavailable", "removed"}
KINDS = ("models", "offers")


def _validate_date(value: str) -> str:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError("as_of must use YYYY-MM-DD")
    return value


def _record_id(record: dict) -> str:
    return str(record.get("id") or record.get("modelId") or record.get("model") or "").strip()


def _record_title(record: dict, kind: str) -> str:
    if kind == "model":
        return str(record.get("model") or record.get("id") or "Unknown model")
    return str(record.get("title") or record.get("name") or record.get("id") or "Unknown resource")


def _state(record: dict) -> str:
    return str(record.get("status") or "").strip().lower()


def _is_offline(record: dict) -> bool:
    return _state(record) in OFFLINE_STATES


def _healthy(source_health: dict, kind: str) -> bool:
    status = str((source_health.get(kind) or {}).get("status") or "ok").lower()
    return status in {"ok", "success", "healthy"}


def _records(value: object) -> list[dict]:
    return [item for item in value or [] if isinstance(item, dict) and _record_id(item)]


def _maps(previous_log: dict | None, key: str) -> tuple[dict[str, dict], dict[str, dict]]:
    observed = (previous_log or {}).get("observed") or {}
    known = (previous_log or {}).get("known") or {}
    observed_records = {_record_id(item): item for item in _records(observed.get(key))}
    known_records = {_record_id(item): item for item in _records(known.get(key))}
    known_records.update(observed_records)
    return observed_records, known_records


def _event(kind: str, event_type: str, record: dict, as_of: str, reason: str = "") -> dict:
    value = {
        "kind": kind,
        "eventType": event_type,
        "id": _record_id(record),
        "title": _record_title(record, kind),
        "asOf": as_of,
        "details": dict(record),
    }
    if reason:
        value["reason"] = reason
    return value


def _canonical_model(record: dict) -> str:
    return str(record.get("model") or _record_id(record).rsplit("/", 1)[-1]).strip().lower()


def _snapshot_record(record: dict, kind: str) -> dict:
    fields = (
        ("id", "providerId", "provider", "model", "sourceUrl", "status")
        if kind == "model"
        else ("id", "title", "name", "provider", "productType", "status", "register", "sourceUrls")
    )
    return {field: record[field] for field in fields if field in record and record[field] not in (None, "", [])}


def build_daily_log(
    previous_log: dict | None,
    current_models: list[dict],
    current_offers: list[dict],
    as_of: str,
    source_health: dict | None = None,
) -> dict:
    """Compare successful snapshots and return one deterministic daily log.

    A missing previous log creates a baseline without emitting false "new" events.
    Failed sources carry their previous active records forward and cannot emit
    offline events.
    """
    as_of = _validate_date(as_of)
    health = source_health or {}
    current_by_kind = {"models": _records(current_models), "offers": _records(current_offers)}
    events: list[dict] = []
    observed: dict[str, list[dict]] = {}
    known: dict[str, list[dict]] = {}
    initialized: dict[str, bool] = {}

    for plural in KINDS:
        kind = plural[:-1]
        previous_active, previous_known = _maps(previous_log, plural)
        previous_initialized = bool(
            ((previous_log or {}).get("initialized") or {}).get(plural, previous_log is not None)
        )
        current_all = {item_id: item for item_id, item in ((_record_id(item), item) for item in current_by_kind[plural]) if item_id}
        source_ok = _healthy(health, plural)

        if not source_ok:
            status = dict(health.get(plural) or {"status": "failed"})
            events.append(_event("source", "source_unavailable", {"id": plural, **status}, as_of, "source scan failed"))
            active_now = dict(previous_active)
        else:
            active_now = {item_id: item for item_id, item in current_all.items() if not _is_offline(item)}

            if previous_initialized:
                for item_id, item in sorted(active_now.items()):
                    if item_id in previous_active:
                        continue
                    if item_id in previous_known:
                        events.append(_event(kind, "recovered", item, as_of, "previously absent or offline and observed again"))
                    elif kind == "model" and any(
                        _canonical_model(item) == _canonical_model(previous)
                        for previous in previous_known.values()
                    ):
                        events.append(_event(kind, "new_route", item, as_of, "same model observed through a new provider or route"))
                    else:
                        events.append(_event(kind, "new", item, as_of, "not present in the previous successful snapshot"))

                for item_id, item in sorted(previous_active.items()):
                    if item_id not in current_all:
                        events.append(_event(kind, "offline", item, as_of, "missing from the successful snapshot"))

                for item_id, item in sorted(current_all.items()):
                    if item_id in previous_active and _is_offline(item):
                        events.append(_event(kind, "offline", item, as_of, f"status changed to {_state(item)}"))

        known_now = dict(previous_known)
        known_now.update(current_all)
        observed[plural] = [_snapshot_record(active_now[item_id], kind) for item_id in sorted(active_now)]
        known[plural] = [
            _snapshot_record(known_now[item_id], kind)
            for item_id in sorted(known_now)
            if item_id not in active_now
        ]
        initialized[plural] = previous_initialized or source_ok

    events.sort(key=lambda item: (item["kind"], item["eventType"], item["id"]))
    return {
        "schemaVersion": 1,
        "date": as_of,
        "baseline": previous_log is None,
        "events": events,
        "observed": observed,
        "known": known,
        "initialized": initialized,
        "sourceHealth": health,
    }


def write_daily_log(path: str | Path, log: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
