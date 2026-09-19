"""Measure the API-gateway round-trip latency of every provider in the model catalog.

Keyless by design: the probe owns no provider credentials, so it calls each
provider's documented model-listing endpoint and times how long the API gateway
takes to answer. A 401/403 still counts as a successful measurement - the point
is the network path and the gateway, not authorization.

Candidates per provider come from the catalog itself (`accessEndpoint`, then
`sourceEndpoint`, plus their `/models` variants). The best candidate wins:
a JSON API response beats an HTML landing page, and among equals the lowest
median wins.

This measures *API gateway latency only*. It does not and cannot measure model
inference speed (tokens/second) or time-to-first-token, which needs a real key.

Read-only with respect to every tracked data file except the report it writes.
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

UA = "Mozilla/5.0 (compatible; freellm-endpoint-latency/1.0)"
ATTEMPTS = 3
_ctx = ssl.create_default_context()

VANTAGE = "本机大陆网络直连"
METHOD_NOTE = "GET 服务商官方 API 端点（模型列表），预热 1 次后取 3 次成功请求往返延迟的中位数"
NOTE = "只测量 API 网关的往返延迟，不代表模型生成速度、免费额度或注册门槛"


# --------------------------------------------------------------------------- #
# candidates
# --------------------------------------------------------------------------- #
def _bare_base(url: str) -> bool:
    """True when the URL is just a host (optionally with a trailing slash)."""
    return urllib.parse.urlsplit(url).path.strip("/") == ""


def candidate_urls(model: dict) -> list[str]:
    """Every documented API URL for this provider, most specific first."""
    urls: list[str] = []

    def add(url: object) -> None:
        text = str(url or "").strip().rstrip("/")
        if not text.startswith("http") or text in urls:
            return
        urls.append(text)

    for raw in (model.get("accessEndpoint"), model.get("sourceEndpoint")):
        base = str(raw or "").strip().rstrip("/")
        if not base.startswith("http"):
            continue
        bases = [base, f"{base}/v1"] if _bare_base(base) else [base]
        for candidate in bases:
            add(candidate)
            add(f"{candidate}/models")
    return urls


# --------------------------------------------------------------------------- #
# measurement
# --------------------------------------------------------------------------- #
def _one_request(url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": UA, "Accept": "application/json"})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ctx) as response:
            body = response.read(256).decode("utf-8", "replace")
            return {"status": response.status, "ms": int((time.monotonic() - started) * 1000), "body": body}
    except urllib.error.HTTPError as error:
        body = error.read(256).decode("utf-8", "replace")
        return {"status": error.code, "ms": int((time.monotonic() - started) * 1000), "body": body}
    except Exception as exc:  # noqa: BLE001 - failures are data here
        reason = getattr(exc, "reason", None)
        kind = "DNS" if isinstance(reason, socket.gaierror) else type(exc).__name__
        return {"status": None, "ms": int((time.monotonic() - started) * 1000), "error": kind}


def _looks_like_json(body: str) -> bool:
    return body.lstrip().startswith(("{", "["))


def measure(url: str, timeout: float) -> dict:
    """Warm up the DNS/TLS path once, then take the median of three attempts."""
    warmup = _one_request(url, timeout)
    attempts = [_one_request(url, timeout) for _ in range(ATTEMPTS)]
    good = [entry for entry in attempts if entry["status"] is not None]
    latencies = [entry["ms"] for entry in good]
    sample = good[0] if good else warmup
    return {
        "url": url,
        "status": sample["status"],
        "json": _looks_like_json(sample.get("body") or ""),
        "ms": int(statistics.median(latencies)) if latencies else None,
        "attempts": latencies,
        "warmupMs": warmup["ms"],
        "okAttempts": len(good),
        "error": None if good else sample.get("error"),
    }


def rank(entry: dict) -> int:
    """Lower is better. A JSON API answer always beats an HTML landing page."""
    if entry["status"] is None:
        return 5
    if entry["json"]:
        if entry["status"] == 200:
            return 0
        if entry["status"] in {401, 403, 422}:
            return 1
        return 2
    return 3 if entry["status"] == 200 else 4


VERDICTS = {
    0: "ok",
    1: "needs_key",
    2: "alive",
    3: "docs_html",
    4: "http_error",
    5: "network_error",
}


def probe_provider(provider_id: str, provider: str, models: list[dict], timeout: float) -> dict:
    candidates: list[str] = []
    for model in models:
        for url in candidate_urls(model):
            if url not in candidates:
                candidates.append(url)
    if not candidates:
        return {
            "providerId": provider_id,
            "provider": provider,
            "modelCount": len(models),
            "endpoint": None,
            "verdict": "unverified",
            "ms": None,
            "attempts": [],
            "note": "目录未给出可探测的官方 API 端点",
        }

    measured = [measure(url, timeout) for url in candidates]
    best = min(measured, key=lambda entry: (rank(entry), entry["ms"] if entry["ms"] is not None else 10**9))
    verdict = VERDICTS[rank(best)]
    # An HTML landing page is not an API gateway: refuse to report a latency for it.
    reported = None if rank(best) >= 3 else best["ms"]
    payload = {
        "providerId": provider_id,
        "provider": provider,
        "modelCount": len(models),
        "endpoint": best["url"],
        "status": best["status"],
        "verdict": verdict,
        "ms": reported,
        "attempts": best["attempts"],
        "warmupMs": best["warmupMs"],
    }
    if reported is None:
        payload["note"] = (
            "端点未公开可直接探测的接口（仅返回 HTML 页面）"
            if best["status"] is not None
            else f"探测失败：{best.get('error') or 'unknown'}"
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="data/models.json")
    parser.add_argument("--output", default="data/endpoint-latency.json")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--date", default=None, help="override checkedAt (YYYY-MM-DD)")
    args = parser.parse_args()

    models = json.loads(Path(args.models).read_text(encoding="utf-8"))
    if not isinstance(models, list):
        raise SystemExit("--models must point at a JSON array")

    grouped: dict[str, list[dict]] = {}
    for model in models:
        grouped.setdefault(str(model.get("providerId") or ""), []).append(model)

    checked_at = args.date or time.strftime("%Y-%m-%d")
    print(f"probing {len(grouped)} provider endpoint(s)", flush=True)
    providers = []
    for provider_id in sorted(grouped):
        rows = grouped[provider_id]
        name = str(rows[0].get("provider") or provider_id)
        entry = probe_provider(provider_id, name, rows, args.timeout)
        entry["checkedAt"] = checked_at
        providers.append(entry)
        ms = f"{entry['ms']}ms" if entry["ms"] is not None else "—"
        print(f"  {provider_id:<16} {entry['verdict']:<14} {ms:>8}  {entry.get('endpoint') or '-'}", flush=True)

    report = {
        "schemaVersion": 1,
        "checkedAt": checked_at,
        "vantage": VANTAGE,
        "method": METHOD_NOTE,
        "note": NOTE,
        "providers": providers,
    }
    out = Path(args.output)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    measured = sum(1 for entry in providers if entry["ms"] is not None)
    print(f"wrote {out}: {measured}/{len(providers)} endpoints measured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
