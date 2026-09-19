"""Probe every offer endpoint listed in data/offers.json.

Keyless by design: the probe never owns provider credentials, so a 200 means
the free path works without signup, and 401/403 means "endpoint alive, key
required as documented". Results land in a JSON report for the hands-on
(实测好用) review flow.

Every probe warms the DNS/TLS path once and then takes the median of three
measured attempts, so the reported `ms` is a call latency rather than a
connection-setup spike.
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode

UA = "Mozilla/5.0 (compatible; freellm-endpoint-probe/1.0)"
_TIMEOUT = 20.0
ATTEMPTS = 3
_ctx = ssl.create_default_context()

_VERDICTS = {
    200: "OK",
    401: "NEEDS_KEY",
    402: "NEEDS_KEY",
    403: "NEEDS_KEY",
    404: "PATH_CHECK",
    405: "METHOD_CHECK",
    422: "ALIVE",
    429: "RATE_LIMITED",
}


def verdict_from_status(status: int) -> str:
    if status in _VERDICTS:
        return _VERDICTS[status]
    if 500 <= status <= 599:
        return "SERVER_ERROR"
    return f"HTTP_{status}"


def derive_models_url(endpoint: str) -> str | None:
    """OpenAI-style /models listing from a chat/completions endpoint."""
    match = re.match(r"^(https://[^/]+/.*/v1(?:/beta)?)/chat/completions/?$", endpoint)
    if not match:
        match = re.match(r"^(https://[^/]+/v\d+)/chat/completions/?$", endpoint)
    return f"{match.group(1)}/models" if match else None


def _request(url: str, *, method: str = "GET", body: dict | None = None, headers: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json", **(headers or {})},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT, context=_ctx) as response:
            payload = response.read(512)
            return {"status": response.status, "ms": int((time.monotonic() - started) * 1000), "snippet": payload.decode("utf-8", "replace")[:200]}
    except urllib.error.HTTPError as error:
        payload = error.read(512)
        return {"status": error.code, "ms": int((time.monotonic() - started) * 1000), "snippet": payload.decode("utf-8", "replace")[:200]}
    except Exception as exc:  # noqa: BLE001 - network errors are results, not bugs
        kind = type(exc).__name__
        if "timed out" in str(exc).lower() or isinstance(exc, TimeoutError):
            kind = "Timeout"
        return {"status": None, "ms": int((time.monotonic() - started) * 1000), "error": kind}


def measure(url: str, *, method: str = "GET", body: dict | None = None, headers: dict | None = None) -> dict:
    """Warm the connection path once, then report the median of three attempts.

    A single keyless request mostly measures DNS + TLS setup (seconds on a
    cold cross-border path), which is not what "how fast is this API" means.
    """
    warmup = _request(url, method=method, body=body, headers=headers)
    attempts = [_request(url, method=method, body=body, headers=headers) for _ in range(ATTEMPTS)]
    good = [entry for entry in attempts if entry["status"] is not None]
    latencies = [entry["ms"] for entry in good]
    sample = good[0] if good else warmup
    return {
        **sample,
        "ms": int(statistics.median(latencies)) if latencies else sample["ms"],
        "msSamples": latencies,
        "msWarmup": warmup["ms"],
        "okAttempts": len(good),
    }


def _chat_model(offer: dict) -> str:
    models = offer.get("freeModels") or []
    if models and models[0].get("model"):
        return str(models[0]["model"])
    return str(offer.get("model") or "test")[:60]


def build_probes(offer: dict) -> list[dict]:
    """One or two probes per offer: the documented call plus /models when derivable."""
    guide = offer.get("usageGuide") or {}
    endpoint = str(guide.get("endpoint") or "").rstrip("/")
    if not endpoint:
        return []
    probes: list[dict] = []
    if ":generateContent" in endpoint:
        probes.append({"name": "generateContent", "method": "POST", "url": endpoint, "body": {"contents": [{"parts": [{"text": "ping"}]}]}})
    elif endpoint.endswith("/chat/completions"):
        probes.append({"name": "chat", "method": "POST", "url": endpoint, "body": {"model": _chat_model(offer), "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}})
        models_url = derive_models_url(endpoint)
        if models_url:
            probes.append({"name": "models", "method": "GET", "url": models_url})
    elif endpoint.endswith("/models"):
        probes.append({"name": "models", "method": "GET", "url": endpoint})
    elif "search.brave.com" in endpoint:
        probes.append({"name": "search", "method": "GET", "url": f"{endpoint}?{urlencode({'q': 'ping'})}"})
    elif endpoint.endswith(("/search", "/agent", "/mcp", "/sessions")):
        probes.append({"name": "call", "method": "POST", "url": endpoint, "body": {"query": "ping"}})
    else:
        probes.append({"name": "root", "method": "GET", "url": endpoint})
        probes.append({"name": "root-post", "method": "POST", "url": endpoint, "body": {"ping": True}})
    return probes


def probe_offer(offer: dict, *, site_check: bool = True) -> dict:
    result = {
        "id": offer.get("id"),
        "originCountry": offer.get("originCountry"),
        "productType": offer.get("productType"),
        "probes": [],
    }
    for probe in build_probes(offer):
        headers = {"Authorization": "Bearer freellm-probe"} if probe["name"] in {"chat", "generateContent", "call", "root-post"} else {}
        outcome = measure(probe["url"], method=probe["method"], body=probe.get("body"), headers=headers)
        status = outcome.get("status")
        verdict = "NETWORK_ERROR" if status is None else verdict_from_status(status)
        snippet = outcome.get("snippet", "")
        if status == 200 and probe["name"] == "models" and not snippet.lstrip().startswith(("{", "[")):
            verdict = "OK_NON_JSON"
        result["probes"].append({
            "name": probe["name"],
            "method": probe["method"],
            "url": probe["url"],
            "status": status,
            "verdict": verdict,
            "ms": outcome.get("ms"),
            "msSamples": outcome.get("msSamples"),
            "msWarmup": outcome.get("msWarmup"),
            **({"error": outcome["error"]} if outcome.get("error") else {}),
            **({"snippet": snippet} if snippet else {}),
        })
    if not result["probes"] and site_check and offer.get("register"):
        outcome = measure(str(offer["register"]))
        status = outcome.get("status")
        result["probes"].append({
            "name": "official-site",
            "method": "GET",
            "url": offer["register"],
            "status": status,
            "verdict": "NETWORK_ERROR" if status is None else verdict_from_status(status),
            "ms": outcome.get("ms"),
            "msSamples": outcome.get("msSamples"),
            "msWarmup": outcome.get("msWarmup"),
            **({"error": outcome["error"]} if outcome.get("error") else {}),
        })
    return result


def summarize(results: list[dict]) -> dict:
    best = []
    for entry in results:
        verdicts = [probe["verdict"] for probe in entry["probes"]]
        if "OK" in verdicts:
            best.append("OK")
        elif verdicts:
            best.append(sorted(verdicts)[0])
    counts: dict[str, int] = {}
    for verdict in best:
        counts[verdict] = counts.get(verdict, 0) + 1
    return {"probed": len(results), "bestVerdicts": counts}


def main() -> int:
    global _TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--output", default=".tmp-endpoint-test-report.json")
    parser.add_argument("--timeout", type=float, default=_TIMEOUT)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--no-site-checks", action="store_true", help="skip official-site probes for offers without endpoints")
    args = parser.parse_args()
    _TIMEOUT = args.timeout

    offers = json.loads(Path(args.data).read_text(encoding="utf-8"))
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(probe_offer, offer, site_check=not args.no_site_checks): offer for offer in offers}
        for future in as_completed(futures):
            results.append(future.result())

    order = {offer["id"]: index for index, offer in enumerate(offers)}
    results.sort(key=lambda entry: order.get(entry["id"], 10_000))

    report = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"), "summary": summarize(results), "results": results}
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    for entry in results:
        for probe in entry["probes"]:
            status = str(probe["status"]) if probe["status"] is not None else probe.get("error", "err")
            print(f"{entry['id']:<34} {probe['name']:<14} {status:>5}  {probe['verdict']:<14} {probe.get('ms', '?'):>6}ms")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
