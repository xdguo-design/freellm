"""Build append-only daily records for newly observed and unavailable entries."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .source_tiers import THIRD_PARTY_RELAY_TIER, is_third_party_relay


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OFFLINE_STATES = {"offline", "expired", "retired", "unavailable", "removed"}
KINDS = ("models", "offers")
# One date convention for the daily log, the Atom feed and the homepage.
# Every public date is a calendar date in Asia/Shanghai (Beijing time):
# * daily-log/<date>.json is the Beijing date the scan or curation ran;
# * an offer's public listing date is the date of the first daily log that
#   records it as "new" (curated or scanned) -- see public_listing_dates();
# * only offers that never appeared in a log fall back to offer["date"].
# The feed uses exactly this, so /logs/, the homepage badge and feed.xml can
# never show two different days for the same entry.
LISTING_TIMEZONE = "Asia/Shanghai"
LISTING_UTC_OFFSET = "+08:00"
HEALTHY_STATES = {"ok", "success", "healthy"}


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
    return status in HEALTHY_STATES


def listing_date(offer: dict, first_logged: dict[str, str] | None = None) -> str:
    """The single public listing date of an offer (Asia/Shanghai, YYYY-MM-DD).

    ``first_logged`` comes from public_listing_dates(daily_logs); when the
    offer appears there, that daily-log date wins over offer["date"].
    """
    offer_id = str((offer or {}).get("id") or "")
    if first_logged and offer_id in first_logged:
        return first_logged[offer_id]
    value = str((offer or {}).get("date") or "")
    return value if DATE_RE.fullmatch(value) else ""


def public_listing_dates(logs: list[dict]) -> dict[str, str]:
    """Offer id -> Beijing date of the first daily log announcing it as new."""
    first: dict[str, str] = {}
    for log in logs or []:
        day = str((log or {}).get("date") or "")
        if not DATE_RE.fullmatch(day):
            continue
        for key in ("curatedEvents", "events"):
            for event in log.get(key) or []:
                if not isinstance(event, dict) or event.get("kind") != "offer" or event.get("eventType") != "new":
                    continue
                offer_id = str(event.get("id") or "").strip()
                if offer_id and (offer_id not in first or day < first[offer_id]):
                    first[offer_id] = day
    return first


def atom_timestamp(day: str) -> str:
    """Atom timestamp for a Beijing calendar date (midnight, explicit +08:00)."""
    return f"{_validate_date(day)}T00:00:00{LISTING_UTC_OFFSET}"


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
    details = dict(record)
    if kind == "model" and is_third_party_relay({"kind": kind, "id": _record_id(record), "details": details}):
        details["sourceTier"] = THIRD_PARTY_RELAY_TIER
    value = {
        "kind": kind,
        "eventType": event_type,
        "id": _record_id(record),
        "title": _record_title(record, kind),
        "asOf": as_of,
        "details": details,
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
        else (
            "id", "title", "name", "provider", "productType", "status", "register",
            "registerLabel", "sourceUrls", "links", "registrationSteps", "usageGuide",
            "evidence", "freeSummary", "validitySummary", "accessSummary",
        )
    )
    return {field: record[field] for field in fields if field in record and record[field] not in (None, "", [])}


def snapshot_fingerprint(records: list[dict], kind: str = "model") -> str:
    """Stable hash of the active snapshot records a log would store."""
    rows = sorted(
        (_snapshot_record(item, kind) for item in _records(records) if not _is_offline(item)),
        key=lambda item: _record_id(item),
    )
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _observed_fingerprint(log: dict | None, plural: str = "models") -> str:
    records = ((log or {}).get("observed") or {}).get(plural) or []
    return snapshot_fingerprint(records, plural[:-1])


def detect_stalled_scan(previous_log: dict | None, current_models: list[dict], as_of: str) -> str:
    """Return a reason when today's model scan is byte-identical to an earlier day.

    The 2026-10-03..10-09 incident: the scanner kept producing the same 244-row
    snapshot every day while sourceHealth said ``ok``. A real scan of ~240
    upstream catalogues changes daily, so an identical snapshot on a later
    date means the scan did not really run (cache, stale artefact or copy).
    Returns "" when the scan looks fresh or there is nothing to compare.
    """
    as_of = _validate_date(as_of)
    if not previous_log or not _records(current_models):
        return ""
    previous_date = str(previous_log.get("date") or "")
    if not DATE_RE.fullmatch(previous_date) or previous_date >= as_of:
        return ""
    if not _records((previous_log.get("observed") or {}).get("models")):
        return ""
    if snapshot_fingerprint(current_models, "model") != _observed_fingerprint(previous_log, "models"):
        return ""
    return f"model scan snapshot identical to {previous_date}; scan likely stalled (cached or not re-run)"


def scan_health_errors(today_log: dict | None, previous_log: dict | None, as_of: str) -> list[str]:
    """Health gate for the daily scan: fail loudly instead of reporting ``ok``.

    Errors when today's log is missing / not dated today, when any source is
    not healthy, or when the observed model snapshot did not change since the
    previous log (the scan was not really updated).
    """
    as_of = _validate_date(as_of)
    if not today_log:
        return [f"daily log for {as_of} is missing: today's scan did not run or was not committed"]
    errors: list[str] = []
    if str(today_log.get("date") or "") != as_of:
        errors.append(f"latest daily log is dated {today_log.get('date')!r}, expected {as_of}")
    for plural, item in sorted((today_log.get("sourceHealth") or {}).items()):
        status = str((item or {}).get("status") or "unknown").lower()
        if status not in HEALTHY_STATES:
            reason = (item or {}).get("reason") or "no reason given"
            errors.append(f"{plural} source health is {status!r}: {reason}")
    if previous_log and _records((today_log.get("observed") or {}).get("models")):
        previous_date = str(previous_log.get("date") or "")
        if previous_date < as_of and _observed_fingerprint(today_log) == _observed_fingerprint(previous_log):
            message = f"observed model snapshot is identical to {previous_date}; the scan result was not updated"
            if not any(message in error for error in errors):
                errors.append(message)
    return errors


def announced_offer_ids(logs: list[dict]) -> set[str]:
    """Offer ids already announced as curated new events in any of ``logs``."""
    found: set[str] = set()
    for log in logs:
        found.update(_curated_offer_ids(log))
    return found


def _curated_offer_ids(log: dict | None) -> dict[str, dict]:
    """Offers a human already announced in that log as new (curatedEvents)."""
    found: dict[str, dict] = {}
    for event in (log or {}).get("curatedEvents") or []:
        if isinstance(event, dict) and event.get("kind") == "offer" and event.get("eventType") in {"new", "new_route", "recovered"}:
            event_id = str(event.get("id") or "").strip()
            if event_id:
                found[event_id] = dict(event.get("details") or {"id": event_id})
    return found


def build_daily_log(
    previous_log: dict | None,
    current_models: list[dict],
    current_offers: list[dict],
    as_of: str,
    source_health: dict | None = None,
    announced_offer_ids: set[str] | None = None,
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
        # An offer announced yesterday as a curated "new" event is not new again today.
        announced = (set(_curated_offer_ids(previous_log)) | set(announced_offer_ids or ())) if plural == "offers" else set()

        if not source_ok:
            status = dict(health.get(plural) or {"status": "failed"})
            events.append(_event("source", "source_unavailable", {"id": plural, **status}, as_of, "source scan failed"))
            active_now = dict(previous_active)
        else:
            active_now = {item_id: item for item_id, item in current_all.items() if not _is_offline(item)}

            if previous_initialized:
                for item_id, item in sorted(active_now.items()):
                    if item_id in previous_active or item_id in announced:
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


def merge_daily_log(existing: dict, incoming: dict) -> dict:
    """Fold a same-day re-run into the existing log so repeated runs only add events.

    Events are deduplicated by (kind, eventType, id) with the incoming scan
    winning conflicts; hand-curated events always survive a rebuild. Snapshot
    maps are merged so records seen only by an earlier run stay known.
    """
    existing_date = _validate_date(str(existing.get("date") or ""))
    incoming_date = _validate_date(str(incoming.get("date") or ""))
    if existing_date != incoming_date:
        raise ValueError("merge_daily_log requires two logs for the same date")

    def event_key(event: dict) -> tuple[str, str, str]:
        return (str(event.get("kind") or ""), str(event.get("eventType") or ""), str(event.get("id") or ""))

    events: dict[tuple[str, str, str], dict] = {}
    for source in (existing, incoming):
        for event in source.get("events") or []:
            if isinstance(event, dict) and any(event_key(event)):
                events[event_key(event)] = event

    curated: dict[tuple[str, str, str], dict] = {}
    for source in (incoming, existing):
        for event in source.get("curatedEvents") or []:
            if isinstance(event, dict) and any(event_key(event)):
                curated.setdefault(event_key(event), event)

    observed: dict[str, list[dict]] = {}
    known: dict[str, list[dict]] = {}
    initialized: dict[str, bool] = {}
    for plural in KINDS:
        incoming_observed = {_record_id(item): item for item in _records((incoming.get("observed") or {}).get(plural))}
        existing_observed = {_record_id(item): item for item in _records((existing.get("observed") or {}).get(plural))}
        known_now = {
            _record_id(item): item
            for source in (existing, incoming)
            for item in _records((source.get("known") or {}).get(plural))
        }
        known_now.update({
            item_id: item for item_id, item in existing_observed.items() if item_id not in incoming_observed
        })
        observed[plural] = [incoming_observed[item_id] for item_id in sorted(incoming_observed)]
        known[plural] = [known_now[item_id] for item_id in sorted(known_now) if item_id not in incoming_observed]
        initialized[plural] = bool(
            ((existing.get("initialized") or {}).get(plural))
            or ((incoming.get("initialized") or {}).get(plural))
        )

    merged = dict(incoming)
    merged["date"] = incoming_date
    merged["baseline"] = bool(incoming.get("baseline") or existing.get("baseline"))
    merged["events"] = [events[key] for key in sorted(events)]
    if curated:
        merged["curatedEvents"] = [curated[key] for key in sorted(curated)]
    merged["observed"] = observed
    merged["known"] = known
    merged["initialized"] = initialized
    return merged


def write_daily_log(path: str | Path, log: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
