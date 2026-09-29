"""Audit WusRouter public evidence and optional authenticated OpenAI-compatible access.

The audit is intentionally conservative: public price/status checks can discover
zero-cost candidates, but only an API-key-backed model-list + chat probe can mark
end-to-end access as verified. External failures are reported, not raised, so a
provider outage or Cloudflare challenge never breaks the site's daily CI gate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler

USER_AGENT = "FreeAIIndexResearch/0.2 (+public-source-monitor; contact site maintainer)"
DIRECT_OPENER = build_opener(ProxyHandler({}))
PRICE_KEY_RE = re.compile(r"(?:^|_)(?:price|cost|input|output|prompt|completion|credit)(?:_|$)", re.I)
MODEL_KEY_PRIORITY = ("model", "model_id", "modelId", "name", "slug", "id")
ZERO_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _zeroish(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return float(value) == 0.0
    if not isinstance(value, str):
        return False
    numbers = ZERO_NUMBER_RE.findall(value.replace(",", ""))
    return bool(numbers) and all(float(number) == 0.0 for number in numbers)


def _model_id(record: dict[str, Any]) -> str | None:
    for key in MODEL_KEY_PRIORITY:
        value = record.get(key)
        if isinstance(value, str) and value.strip() and len(value.strip()) <= 160:
            return value.strip()
    return None


def extract_zero_cost_models(payload: Any) -> list[str]:
    """Return model-like records whose explicit price/cost fields are all zero."""
    found: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            model = _model_id(node)
            price_values = [
                value
                for key, value in node.items()
                if PRICE_KEY_RE.search(str(key)) and not isinstance(value, (dict, list))
            ]
            if model and price_values and all(_zeroish(value) for value in price_values):
                found.add(model)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(payload)
    return sorted(found)


def _classify_error(status: int | None, text: str, reason: str) -> str:
    lowered = f"{text} {reason}".lower()
    if status == 401:
        return "auth_required"
    if status == 429:
        return "rate_limited"
    if status == 403 and ("cloudflare" in lowered or "just a moment" in lowered or "cf-chl" in lowered):
        return "cloudflare_challenge"
    if status == 403:
        return "forbidden"
    if status is not None and status >= 500:
        return "upstream_error"
    if "name resolution" in lowered or "temporary failure in name resolution" in lowered or "nodename nor servname" in lowered:
        return "dns_error"
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    return "network_error"


def probe_json(url: str, timeout: int, api_key: str | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = None
    method = "GET"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
        method = "POST"
    request = Request(url, headers=headers, data=data, method=method)
    try:
        with DIRECT_OPENER.open(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                return {"url": url, "status": "source_limit", "httpStatus": response.status}
            text = raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            content_type = response.headers.get_content_type()
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                classification = _classify_error(response.status, text, "non-json response")
                return {
                    "url": url,
                    "status": "non_json",
                    "classification": classification,
                    "httpStatus": response.status,
                    "contentType": content_type,
                    "sample": text[:240],
                }
            return {
                "url": url,
                "status": "ok",
                "classification": "ok",
                "httpStatus": response.status,
                "contentType": content_type,
                "payload": payload,
            }
    except HTTPError as error:
        raw = error.read(32_768)
        text = raw.decode("utf-8", errors="replace")
        return {
            "url": url,
            "status": "failed",
            "classification": _classify_error(error.code, text, str(error)),
            "httpStatus": error.code,
            "sample": text[:240],
        }
    except (URLError, TimeoutError, OSError, ValueError) as error:
        reason = str(getattr(error, "reason", error))
        return {
            "url": url,
            "status": "failed",
            "classification": _classify_error(None, "", reason),
            "reason": reason,
        }


def _redact_probe(probe: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in probe.items() if key != "payload"}
    payload = probe.get("payload")
    if payload is not None:
        if isinstance(payload, list):
            result["payloadShape"] = "list"
            result["recordCount"] = len(payload)
        elif isinstance(payload, dict):
            result["payloadShape"] = "object"
            result["topLevelKeys"] = sorted(str(key) for key in payload.keys())[:40]
        else:
            result["payloadShape"] = type(payload).__name__
    return result


def audit(base_url: str, timeout: int, api_key: str | None) -> dict[str, Any]:
    base = base_url.rstrip("/")
    pricing = probe_json(f"{base}/api/pricing", timeout)
    status = probe_json(f"{base}/api/status", timeout)
    models = probe_json(f"{base}/v1/models", timeout, api_key=api_key)

    free_models = extract_zero_cost_models(pricing.get("payload")) if pricing.get("status") == "ok" else []
    chat = None
    verified_model = None
    if api_key and free_models:
        verified_model = free_models[0]
        chat = probe_json(
            f"{base}/v1/chat/completions",
            timeout,
            api_key=api_key,
            body={
                "model": verified_model,
                "messages": [{"role": "user", "content": "Reply with exactly: freellm-ok"}],
                "max_tokens": 12,
                "temperature": 0,
            },
        )

    if chat and chat.get("status") == "ok":
        verdict = "verified_e2e"
    elif api_key and models.get("status") == "ok" and free_models:
        verdict = "partial_authenticated"
    elif free_models:
        verdict = "free_candidates_public_only"
    else:
        verdict = "needs_review"

    blockers = []
    for name, probe in (("pricing", pricing), ("status", status), ("models", models)):
        classification = probe.get("classification")
        if classification not in {"ok", "auth_required"}:
            blockers.append({"check": name, "classification": classification})
    if not api_key:
        blockers.append({"check": "e2e", "classification": "api_key_not_configured"})
    elif not free_models:
        blockers.append({"check": "e2e", "classification": "no_zero_cost_model_from_public_pricing"})
    elif chat and chat.get("status") != "ok":
        blockers.append({"check": "chat", "classification": chat.get("classification")})

    return {
        "providerId": "wusrouter",
        "generatedAt": _now_iso(),
        "verdict": verdict,
        "authenticated": bool(api_key),
        "zeroCostCandidates": free_models,
        "verifiedModel": verified_model if chat and chat.get("status") == "ok" else None,
        "checks": {
            "pricing": _redact_probe(pricing),
            "status": _redact_probe(status),
            "models": _redact_probe(models),
            "chat": _redact_probe(chat) if chat else None,
        },
        "blockers": blockers,
        "publishable": verdict == "verified_e2e",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://api.wusrouter.com")
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = audit(args.base_url, args.timeout, os.getenv("WUSROUTER_API_KEY") or None)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "providerId": report["providerId"],
        "verdict": report["verdict"],
        "zeroCostCandidates": len(report["zeroCostCandidates"]),
        "publishable": report["publishable"],
        "blockers": report["blockers"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
