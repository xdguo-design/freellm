"""Combine user confirmations and sanitized probe samples without inventing reliability.

A single user confirmation is useful, but never a synthetic successful probe.
Public success-rate metrics require >=20 authenticated calls across >=3 UTC dates,
with the most recent sample no older than 72 hours. Reports are audit artifacts:
this script never edits published site status or data/offers.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
from pathlib import Path

PROVIDER_ID = "hcnsec-gateway"
MIN_SAMPLES = 20
MIN_DAYS = 3
MAX_AGE_HOURS = 72
GOOD_OUTCOME = "success"
VALID_OUTCOMES = {
    "success", "authentication_rejected", "permission_denied", "rate_limited",
    "network_error", "invalid_response", "server_error", "http_error", "redirect_rejected"
}


def _timestamp(text: str) -> dt.datetime | None:
    if not isinstance(text, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(dt.timezone.utc) if parsed.tzinfo else None


def _percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * fraction + 0.999999)))
    return ordered[index]


def evaluate(observations: dict, reports: list[dict], *, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    user_records = [
        item for item in observations.get("observations", [])
        if isinstance(item, dict)
        and item.get("providerId") == PROVIDER_ID
        and item.get("sourceType") == "first_party_user_report"
        and item.get("outcome") == "reported_success"
        and item.get("countedForAvailabilityMetrics") is False
    ]
    docs = []
    authenticated = []
    for sample in reports:
        if not isinstance(sample, dict) or sample.get("providerId") != PROVIDER_ID or sample.get("schemaVersion") != 1:
            continue
        timestamp = _timestamp(sample.get("checkedAt"))
        if timestamp is None or timestamp > now + dt.timedelta(minutes=5) or timestamp < now - dt.timedelta(days=90):
            continue
        typ = sample.get("probeType")
        if typ == "documentation" and sample.get("outcome") == "reachable":
            docs.append(sample)
        if (
            typ == "authenticated_chat"
            and sample.get("evidenceSource") == "freellm_automated_probe"
            and sample.get("outcome") in VALID_OUTCOMES
            and isinstance(sample.get("latencyMs"), int)
            and not isinstance(sample.get("latencyMs"), bool)
            and 0 <= sample["latencyMs"] <= 120000
        ):
            authenticated.append((timestamp, sample))
    authenticated.sort(key=lambda pair: pair[0])
    dates = {time.date() for time, _ in authenticated}
    latest = authenticated[-1][0] if authenticated else None
    recent = latest is not None and now - latest <= dt.timedelta(hours=MAX_AGE_HOURS)
    enough = len(authenticated) >= MIN_SAMPLES and len(dates) >= MIN_DAYS and recent
    successes = [item for _, item in authenticated if item["outcome"] == GOOD_OUTCOME]
    latencies = [item["latencyMs"] for item in successes]
    counts = {}
    for _, item in authenticated:
        code = item["outcome"]
        counts[code] = counts.get(code, 0) + 1
    status = (
        "MEASURED_WINDOW" if enough else
        "INSUFFICIENT_SAMPLES" if authenticated else
        "USER_CONFIRMED" if user_records else
        "DOCUMENT_ONLY" if docs else "UNKNOWN"
    )
    return {
        "providerId": PROVIDER_ID,
        "evaluatedAt": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "evidenceStatus": status,
        "userSuccessReports": len(user_records),
        "documentReachabilityObservations": len(docs),
        "authenticatedSamples": len(authenticated),
        "authenticatedSuccessSamples": len(successes),
        "sampleDays": len(dates),
        "latestAuthenticatedAt": latest.isoformat().replace("+00:00", "Z") if latest else None,
        "successRatePercent": round(len(successes) * 100 / len(authenticated), 2) if enough else None,
        "p50LatencyMs": int(statistics.median(latencies)) if enough and latencies else None,
        "p95LatencyMs": _percentile(latencies, 0.95) if enough and latencies else None,
        "outcomes": counts,
        "metricGate": {"minSamples": MIN_SAMPLES, "minUtcDays": MIN_DAYS, "maxSampleAgeHours": MAX_AGE_HOURS},
        "note": "Website/document availability != authenticated API success. User reports do not enter API sample metrics.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", default="data/public-api-observations.json")
    parser.add_argument("--reports-dir", default=".tmp/public-api/reports")
    parser.add_argument("--output", default=".tmp/public-api/evaluation.json")
    args = parser.parse_args(argv)
    observations = json.loads(Path(args.observations).read_text(encoding="utf-8"))
    source = Path(args.reports_dir)
    reports: list[dict] = []
    if source.is_dir():
        for file in sorted(source.glob("*.json"))[:400]:
            if file.stat().st_size > 65536:
                continue
            try:
                doc = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(doc, dict):
                    reports.append(doc)
            except (ValueError, UnicodeError, OSError):
                continue
    result = evaluate(observations, reports)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidenceStatus": result["evidenceStatus"], "samples": result["authenticatedSamples"],
                      "userReports": result["userSuccessReports"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
