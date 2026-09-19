"""Two-vantage network reachability probe for every offer shown on the homepage.

Vantage points:
  * cn   - direct requests from this machine on a mainland-China network.
           Every distinct host the offer itself links to is tried, in order,
           stopping at the first one that answers. An offer counts as
           China-reachable if any of its own entry points works.
  * intl - independent checks executed from foreign check-host.net nodes
           (US x2, DE, SG, JP, UK). The offer's primary target is used, because
           check-host rate-limits submissions.

"Reachable" means the HTTP layer answered at all (any status code counts,
including 401/403/404/405 - the point is whether the network path works).
A DNS / TCP / TLS failure means not reachable from that vantage.

This script only measures *network reachability and latency*. It does not and
cannot measure model inference speed, because the probe owns no provider keys.

Read-only with respect to data/offers.json: it writes a report file only.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (compatible; freellm-network-probe/1.0)"
PROBE_TOKEN = "freellm-probe-no-key"
_ctx = ssl.create_default_context()

CHECK_HOST = "https://check-host.net"
OVERSEAS_NODES = [
    "us1.node.check-host.net",
    "us2.node.check-host.net",
    "de1.node.check-host.net",
    "sg1.node.check-host.net",
    "jp1.node.check-host.net",
    "uk1.node.check-host.net",
]
NODE_LABELS = {
    "us1.node.check-host.net": "US-East",
    "us2.node.check-host.net": "US-West",
    "de1.node.check-host.net": "DE",
    "sg1.node.check-host.net": "SG",
    "jp1.node.check-host.net": "JP",
    "uk1.node.check-host.net": "UK",
}
CN_ATTEMPTS = 3
CN_MIN_OK = 2
MAX_TARGETS = 4

# 451 = Unavailable For Legal Reasons. A 403 from a foreign node against a
# China-only product is the usual shape of a regional block, so both count as
# "the path works but the service refuses this region".
BLOCK_CODES = {403, 451}


def classify_node(http_code: int | None) -> str:
    if http_code is None:
        return "unreachable"
    if http_code in BLOCK_CODES:
        return "blocked"
    return "alive"


# --------------------------------------------------------------------------- #
# target selection
# --------------------------------------------------------------------------- #
def _method_for(endpoint: str, declared: str) -> str:
    method = str(declared or "GET").strip().upper()
    if ":generateContent" in endpoint or endpoint.endswith("/chat/completions"):
        return "POST"
    return method if method in {"GET", "POST", "HEAD"} else "GET"


def resolve_targets(offer: dict) -> list[dict]:
    """Every distinct host the offer points at, primary target first."""
    targets: list[dict] = []
    seen_hosts: set[str] = set()

    def add(kind: str, method: str, url: object) -> None:
        text = str(url or "").strip()
        if not text.startswith("http"):
            return
        host = urllib.parse.urlsplit(text).netloc.lower()
        if not host or host in seen_hosts:
            return
        seen_hosts.add(host)
        targets.append({"kind": kind, "method": method, "url": text, "host": host})

    guide = offer.get("usageGuide") or {}
    endpoint = str(guide.get("endpoint") or "").strip()
    if endpoint:
        add("api", _method_for(endpoint, guide.get("method")), endpoint)
    add("site", "GET", offer.get("register"))
    for link in offer.get("links") or []:
        if isinstance(link, (list, tuple)) and len(link) >= 2:
            add("site", "GET", link[1])
    return targets[:MAX_TARGETS]


# --------------------------------------------------------------------------- #
# cn vantage
# --------------------------------------------------------------------------- #
def _one_request(url: str, method: str, timeout: float) -> dict:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    body = None
    if method == "POST":
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {PROBE_TOKEN}"
        body = json.dumps({"model": "probe", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}).encode()
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ctx) as response:
            snippet = response.read(256).decode("utf-8", "replace")
            return {"ok": True, "status": response.status, "ms": int((time.monotonic() - started) * 1000), "snippet": snippet[:160]}
    except urllib.error.HTTPError as error:
        snippet = error.read(256).decode("utf-8", "replace")
        return {"ok": True, "status": error.code, "ms": int((time.monotonic() - started) * 1000), "snippet": snippet[:160]}
    except Exception as exc:  # noqa: BLE001 - failures are data here
        reason = getattr(exc, "reason", None)
        kind = "DNS" if isinstance(reason, socket.gaierror) else type(exc).__name__
        return {"ok": False, "status": None, "ms": int((time.monotonic() - started) * 1000), "error": kind}


def probe_cn_target(target: dict, timeout: float) -> dict:
    attempts = [_one_request(target["url"], target["method"], timeout) for _ in range(CN_ATTEMPTS)]
    good = [a for a in attempts if a["ok"]]
    statuses = {a["status"] for a in good}
    errors = {a["error"] for a in attempts if not a["ok"]}
    return {
        "kind": target["kind"],
        "url": target["url"],
        "host": target["host"],
        "reachable": len(good) >= CN_MIN_OK,
        "okAttempts": len(good),
        "status": good[0]["status"] if good else None,
        "blocked": bool(statuses) and statuses <= BLOCK_CODES,
        "ms": int(statistics.median([a["ms"] for a in good])) if good else None,
        "dnsFailure": bool(errors) and errors <= {"DNS"},
        "snippet": good[0].get("snippet") if good else None,
        "samples": [{"ok": a["ok"], "status": a["status"], "ms": a["ms"], **({"error": a["error"]} if a.get("error") else {})} for a in attempts],
    }


def probe_cn(targets: list[dict], timeout: float) -> dict:
    """Try each host the offer points at.

    Stops early only on a clean sweep (every attempt answered), because mainland
    access to some hosts - github.com is the classic case - is intermittent. An
    offer counts as China-reachable when at least one of its own entry points
    answers reliably.
    """
    tried = []
    for target in targets:
        result = probe_cn_target(target, timeout)
        tried.append(result)
        if result["okAttempts"] == CN_ATTEMPTS:
            break
    clean = next((entry for entry in tried if entry["okAttempts"] == CN_ATTEMPTS), None)
    winner = clean or next((entry for entry in tried if entry["reachable"]), None)
    return {
        "reachable": winner is not None,
        "status": winner["status"] if winner else None,
        "ms": winner["ms"] if winner else None,
        "blocked": bool(winner and winner["blocked"]),
        "host": winner["host"] if winner else None,
        "url": winner["url"] if winner else None,
        "stable": clean is not None,
        "tried": tried,
    }


# --------------------------------------------------------------------------- #
# overseas vantage (check-host.net)
# --------------------------------------------------------------------------- #
def _ch_get(path: str, timeout: float = 25.0) -> dict:
    request = urllib.request.Request(CHECK_HOST + path, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout, context=_ctx) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def submit_overseas(url: str) -> str | None:
    query = "&".join(f"node={urllib.parse.quote(n, safe='')}" for n in OVERSEAS_NODES)
    path = f"/check-http?host={urllib.parse.quote(url, safe='')}&{query}"
    for attempt in range(4):
        try:
            payload = _ch_get(path)
            if "request_id" in payload:
                return str(payload["request_id"])
            time.sleep(2.0 * (attempt + 1))
        except urllib.error.HTTPError as error:
            if error.code == 429:
                time.sleep(5.0 * (attempt + 1))
                continue
            return None
        except Exception:  # noqa: BLE001
            time.sleep(2.0 * (attempt + 1))
    return None


def parse_overseas(payload: dict) -> dict:
    """check-host row shape: [flag, seconds, status_text, http_code, ip].

    `flag` is 1 only for 2xx, so it is useless for reachability. What matters is
    whether `http_code` is null: null means the node never got an HTTP response
    (DNS / TCP / TLS failure), anything else proves the path works.
    """
    nodes = []
    for node in OVERSEAS_NODES:
        entry = payload.get(node)
        if not entry or not isinstance(entry, list) or not entry[0]:
            nodes.append({"node": NODE_LABELS.get(node, node), "state": "unreachable", "error": "no_result"})
            continue
        row = entry[0]
        if not isinstance(row, list) or len(row) < 2:
            nodes.append({"node": NODE_LABELS.get(node, node), "state": "unreachable", "error": "bad_shape"})
            continue
        seconds = row[1]
        status_text = row[2] if len(row) > 2 else None
        raw_code = row[3] if len(row) > 3 else None
        ip = row[4] if len(row) > 4 else None
        http_code = int(raw_code) if str(raw_code).strip().isdigit() else None
        state = classify_node(http_code)
        nodes.append({
            "node": NODE_LABELS.get(node, node),
            "state": state,
            "ms": int(float(seconds) * 1000) if state != "unreachable" and seconds else None,
            "status": http_code,
            "statusText": status_text,
            "ip": ip,
        })
    alive = [n for n in nodes if n["state"] == "alive"]
    blocked = [n for n in nodes if n["state"] == "blocked"]
    unreachable = [n for n in nodes if n["state"] == "unreachable"]
    latencies = [n["ms"] for n in alive + blocked if n["ms"]]
    return {
        "reachable": len(alive) > len(nodes) / 2,
        "blocked": len(alive) == 0 and len(blocked) > 0,
        "aliveNodes": len(alive),
        "blockedNodes": len(blocked),
        "unreachableNodes": len(unreachable),
        "totalNodes": len(nodes),
        "ms": int(statistics.median(latencies)) if latencies else None,
        "bestMs": min(latencies, default=None),
        "nodes": nodes,
    }


def _run_overseas_batches(pending: list[tuple[str, str]], results: dict[str, dict], *, batch: int, spacing: float, wait: float) -> None:
    for start in range(0, len(pending), batch):
        chunk = pending[start:start + batch]
        inflight: list[tuple[str, str]] = []
        for offer_id, url in chunk:
            rid = submit_overseas(url)
            if rid:
                inflight.append((offer_id, rid))
            else:
                results[offer_id] = {"reachable": False, "aliveNodes": 0, "blockedNodes": 0, "unreachableNodes": len(OVERSEAS_NODES), "totalNodes": len(OVERSEAS_NODES), "ms": None, "bestMs": None, "nodes": [], "error": "submit_failed"}
            time.sleep(spacing)

        deadline = time.monotonic() + wait
        while inflight and time.monotonic() < deadline:
            still: list[tuple[str, str]] = []
            for offer_id, rid in inflight:
                try:
                    payload = _ch_get(f"/check-result/{rid}", timeout=20.0)
                except Exception:  # noqa: BLE001
                    still.append((offer_id, rid))
                    continue
                if isinstance(payload, dict) and payload.get("error"):
                    results[offer_id] = {"reachable": False, "aliveNodes": 0, "blockedNodes": 0, "unreachableNodes": len(OVERSEAS_NODES), "totalNodes": len(OVERSEAS_NODES), "ms": None, "bestMs": None, "nodes": [], "error": "expired"}
                    continue
                if isinstance(payload, dict) and all(payload.get(n) for n in OVERSEAS_NODES):
                    results[offer_id] = parse_overseas(payload)
                    continue
                still.append((offer_id, rid))
            inflight = still
            if inflight:
                time.sleep(2.5)
        for offer_id, _rid in inflight:
            results.setdefault(offer_id, {"reachable": False, "aliveNodes": 0, "blockedNodes": 0, "unreachableNodes": len(OVERSEAS_NODES), "totalNodes": len(OVERSEAS_NODES), "ms": None, "bestMs": None, "nodes": [], "error": "timeout"})
        print(f"  overseas batch {start // batch + 1}/{(len(pending) + batch - 1) // batch} done ({len(results)} settled)", flush=True)


def collect_overseas(targets: list[tuple[str, str]], *, batch: int = 8, spacing: float = 1.6, wait: float = 60.0) -> dict[str, dict]:
    """Submit checks in polite batches and poll until every request settles.

    check-host.net occasionally answers "No such device or address" for a host
    that is actually fine, which would read as a regional block. Anything that
    fails on every node without a single HTTP status gets one retry pass.
    """
    results: dict[str, dict] = {}
    pending = [(offer_id, url) for offer_id, url in targets if url]
    for offer_id, url in targets:
        if not url:
            results[offer_id] = {"reachable": False, "aliveNodes": 0, "blockedNodes": 0, "unreachableNodes": len(OVERSEAS_NODES), "totalNodes": len(OVERSEAS_NODES), "ms": None, "bestMs": None, "nodes": [], "error": "no_target"}

    _run_overseas_batches(pending, results, batch=batch, spacing=spacing, wait=wait)

    retry = [
        (offer_id, url)
        for offer_id, url in pending
        if results.get(offer_id, {}).get("aliveNodes", 0) == 0
        and results.get(offer_id, {}).get("blockedNodes", 0) == 0
    ]
    if retry:
        print(f"  retrying {len(retry)} all-failed target(s) once", flush=True)
        _run_overseas_batches(retry, results, batch=batch, spacing=spacing, wait=wait)
    return results


# --------------------------------------------------------------------------- #
# dns sanity check (AliDNS DoH, reachable from the mainland)
# --------------------------------------------------------------------------- #
ALIDNS = "https://dns.alidns.com/resolve"


def resolve_host(host: str, timeout: float = 10.0) -> str:
    """'ok' / 'nxdomain' / 'unknown' for a hostname, via a mainland resolver.

    A documented endpoint whose hostname no longer exists would otherwise be
    reported as a regional block, which is misleading: the link is simply dead.
    """
    query = f"{ALIDNS}?name={urllib.parse.quote(host, safe='')}&type=A"
    request = urllib.request.Request(query, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ctx) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        return "unknown"
    status = payload.get("Status")
    if status == 3:
        return "nxdomain"
    if status == 0 and payload.get("Answer"):
        return "ok"
    return "unknown"


def check_hosts(hosts: list[str]) -> dict[str, str]:
    unique = sorted({host for host in hosts if host})
    return {host: resolve_host(host) for host in unique}


# --------------------------------------------------------------------------- #
# verdict
# --------------------------------------------------------------------------- #
def classify(cn: dict, intl: dict) -> str:
    if cn.get("reachable") and intl.get("reachable"):
        return "both"
    if cn.get("reachable"):
        return "cn"
    if intl.get("reachable"):
        return "intl"
    return "none"


def speed_grade(ms: int | None) -> str | None:
    if ms is None:
        return None
    if ms < 200:
        return "fast"
    if ms < 600:
        return "normal"
    if ms < 1500:
        return "slow"
    return "very_slow"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--output", default=".tmp-network-report.json")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=0, help="probe only the first N offers (0 = all)")
    parser.add_argument("--skip-intl", action="store_true")
    parser.add_argument("--reuse-cn", default=None, help="reuse the cn phase from an earlier report and only re-run the overseas phase")
    args = parser.parse_args()

    offers = json.loads(Path(args.data).read_text(encoding="utf-8"))
    if args.limit:
        offers = offers[: args.limit]

    resolved = {offer["id"]: resolve_targets(offer) for offer in offers}

    all_hosts = [target["host"] for targets in resolved.values() for target in targets]
    host_status = check_hosts(all_hosts)
    dead_hosts = sorted(host for host, state in host_status.items() if state == "nxdomain")
    print(f"[0/3] dns sanity: {len(dead_hosts)} dead host(s) of {len(host_status)}", flush=True)
    for host in dead_hosts:
        print(f"  NXDOMAIN {host}", flush=True)

    cn_results: dict[str, dict] = {}
    if args.reuse_cn:
        previous = json.loads(Path(args.reuse_cn).read_text(encoding="utf-8"))
        cn_results = {entry["id"]: entry["cn"] for entry in previous["results"]}
        print(f"[1/3] cn vantage: reused {len(cn_results)} results from {args.reuse_cn}", flush=True)
    else:
        print(f"[1/3] cn vantage: {len(offers)} offers", flush=True)
        for offer in offers:
            targets = resolved[offer["id"]]
            if not targets:
                cn_results[offer["id"]] = {"reachable": False, "status": None, "ms": None, "host": None, "url": None, "tried": []}
                continue
            cn_results[offer["id"]] = probe_cn(targets, args.timeout)
            row = cn_results[offer["id"]]
            flag = "OK  " if row["reachable"] else "FAIL"
            print(f"  {offer['id']:<34} {flag} {str(row.get('status')):>5} {str(row.get('ms')):>6}ms  {row.get('host') or '-'}  (tried {len(row['tried'])})", flush=True)

    intl_results: dict[str, dict] = {}
    intl_targets: list[tuple[str, str]] = []
    for offer in offers:
        targets = resolved[offer["id"]]
        if not targets:
            intl_targets.append((offer["id"], ""))
            continue
        # Test the entry point that actually answered from the mainland, so a
        # dead documented endpoint does not masquerade as a regional block.
        cn_winner = cn_results.get(offer["id"], {}).get("url")
        intl_targets.append((offer["id"], cn_winner or targets[0]["url"]))
    if args.skip_intl:
        intl_results = {o["id"]: {"reachable": False, "aliveNodes": 0, "blockedNodes": 0, "unreachableNodes": len(OVERSEAS_NODES), "totalNodes": len(OVERSEAS_NODES), "ms": None, "bestMs": None, "nodes": [], "error": "skipped"} for o in offers}
    else:
        print(f"[2/3] overseas vantage: {len(offers)} targets x {len(OVERSEAS_NODES)} nodes", flush=True)
        intl_results = collect_overseas(intl_targets)

    results = []
    for offer in offers:
        offer_id = offer["id"]
        targets = resolved[offer_id]
        cn = cn_results.get(offer_id, {})
        intl = intl_results.get(offer_id, {})
        region = classify(cn, intl)
        dead = [t["url"] for t in targets if host_status.get(t["host"]) == "nxdomain"]
        results.append({
            "id": offer_id,
            "targetKind": targets[0]["kind"] if targets else "none",
            "target": targets[0]["url"] if targets else "",
            "targets": [t["url"] for t in targets],
            "intlTarget": dict(intl_targets).get(offer_id, ""),
            "region": region,
            "cnReachable": bool(cn.get("reachable")),
            "cnStable": bool(cn.get("stable")),
            "cnMs": cn.get("ms"),
            "cnStatus": cn.get("status"),
            "cnHost": cn.get("host"),
            "intlReachable": bool(intl.get("reachable")),
            "intlMs": intl.get("ms"),
            "intlBlocked": bool(intl.get("blocked")),
            "intlAliveNodes": intl.get("aliveNodes"),
            "intlTotalNodes": intl.get("totalNodes"),
            "speedGrade": speed_grade(cn.get("ms")),
            "deadTargets": dead,
            "cn": cn,
            "intl": intl,
        })

    summary: dict[str, int] = {}
    for entry in results:
        summary[entry["region"]] = summary.get(entry["region"], 0) + 1

    report = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "method": "本机大陆网络直连 + check-host.net 海外节点（US x2 / DE / SG / JP / UK）",
        "nodes": [NODE_LABELS[n] for n in OVERSEAS_NODES],
        "summary": summary,
        "results": results,
    }
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"summary": summary, "total": len(results)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
