"""Fold the measured endpoint call latency into data/offers.json as `endpointCheck.ms`.

Only the latency and its check date are written: the hand-written `verdict` and
`note` stay exactly as they are, and an offer whose probe could not get an HTTP
answer keeps its record untouched rather than gaining a fabricated number.

`checkedAt` is refreshed together with `ms`, because the probe that produced the
latency is itself an endpoint check. The script warns (without writing) when the
probe's verdict contradicts the stored one, so a human can look before the
number goes live.

Keeps the hand-maintained formatting of data/offers.json byte-identical apart
from the new field: indent=1, ensure_ascii=False, one trailing newline, LF.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The documented call first: it is what "接口调用速度" means. The model listing
# and the marketing site are fallbacks, in that order.
CALL_PROBES = ("chat", "generateContent", "search", "call", "root-post", "root")
FALLBACK_PROBES = ("models", "official-site")
# Any of these means "the endpoint answered", which is all the latency needs.
ALIVE_VERDICTS = {
    "OK",
    "OK_NON_JSON",
    "NEEDS_KEY",
    "ALIVE",
    "RATE_LIMITED",
    "PATH_CHECK",
    "METHOD_CHECK",
    "HTTP_400",
}


def pick_probe(probes: list[dict]) -> dict | None:
    """The probe whose latency best represents a real API call."""
    usable = [
        probe
        for probe in probes
        if isinstance(probe, dict) and probe.get("status") is not None and isinstance(probe.get("ms"), int)
    ]
    for name in CALL_PROBES + FALLBACK_PROBES:
        match = next((probe for probe in usable if probe.get("name") == name), None)
        if match is not None:
            return match
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=".tmp-endpoint-test-report.json")
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--date", default=None, help="override checkedAt (YYYY-MM-DD)")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    checked_at = args.date or report["generatedAt"][:10]

    data_path = Path(args.data)
    raw = data_path.read_bytes()
    offers = json.loads(raw.decode("utf-8"))
    by_id = {entry["id"]: entry for entry in report["results"]}

    missing = [offer["id"] for offer in offers if offer["id"] not in by_id]
    if missing:
        print(f"report is missing {len(missing)} offers: {', '.join(missing[:6])}", file=sys.stderr)
        return 1

    written: list[str] = []
    skipped: list[str] = []
    conflicts: list[str] = []
    for offer in offers:
        check = offer.get("endpointCheck")
        if not isinstance(check, dict):
            skipped.append(f"{offer['id']} (no endpointCheck record)")
            continue
        probe = pick_probe(by_id[offer["id"]].get("probes") or [])
        if probe is None:
            skipped.append(f"{offer['id']} (no HTTP answer)")
            continue
        probe_verdict = str(probe.get("verdict") or "")
        if probe_verdict not in ALIVE_VERDICTS:
            skipped.append(f"{offer['id']} ({probe_verdict or 'no verdict'})")
            continue
        stored = str(check.get("verdict") or "")
        if stored and probe_verdict != stored and stored not in ALIVE_VERDICTS:
            conflicts.append(f"{offer['id']}: stored {stored} vs probed {probe_verdict}")
            continue
        if stored and probe_verdict != stored:
            conflicts.append(f"{offer['id']}: stored {stored}, probed {probe_verdict} (both alive; latency kept)")
        check["ms"] = int(probe["ms"])
        check["checkedAt"] = checked_at
        written.append(f"{offer['id']} {probe['name']} {probe['ms']}ms")

    rendered = json.dumps(offers, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if rendered.encode("utf-8") != raw:
            print(f"stale: {data_path} does not match the current endpoint report")
            return 1
        print(f"current: {data_path}")
        return 0

    with data_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)
    for line in written:
        print(f"  ms  {line}")
    for line in skipped:
        print(f"  --  skipped {line}")
    for line in conflicts:
        print(f"  !!  verdict note: {line}")
    print(f"wrote {data_path}: {len(written)} latencies, {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
