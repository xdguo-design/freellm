"""Conservative, credential-safe probes for curated public API providers.

No API key is printed, serialized, or stored. Documentation reachability is NOT
an authenticated API success. No user prompt or response body is persisted.
Targets are hard-coded and the opener rejects redirects to protect Bearer tokens.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

DOCUMENT_URL = "https://api.hcnsec.cn/free-api/"
CHAT_URL = "https://api.hcnsec.cn/v1/chat/completions"
MODEL = "DeepSeek-V4-Pro"
MAX_RESPONSE_BYTES = 65536
PROVIDER_ID = "hcnsec-gateway"
TOKEN_ENV = "HCNSEC_API_KEY"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _status_from_http(code: int | None, *, valid: bool, mode: str) -> str:
    if code == 200:
        if not valid:
            return "invalid_response"
        return "success" if mode == "authenticated_chat" else "reachable"
    if code == 401:
        return "authentication_rejected"
    if code == 403:
        return "permission_denied"
    if code == 429:
        return "rate_limited"
    if code in (301, 302, 303, 307, 308):
        return "redirect_rejected"
    if code is None:
        return "network_error"
    if 500 <= code < 600:
        return "server_error"
    return "http_error"


def _valid_response(mode: str, content: bytes) -> bool:
    if mode == "documentation":
        text = content.decode("utf-8", "replace")
        return "api.hcnsec.cn/v1" in text and ("公益" in text or "API" in text)
    try:
        data = json.loads(content.decode("utf-8"))
    except (ValueError, UnicodeError):
        return False
    if not isinstance(data, dict) or not isinstance(data.get("choices"), list) or not data["choices"]:
        return False
    first = data["choices"][0]
    return (
        isinstance(first, dict)
        and isinstance(first.get("message"), dict)
        and isinstance(first["message"].get("content"), str)
        and len(first["message"]["content"].strip()) > 0
    )


def build_request(mode: str, key: str | None = None) -> urllib.request.Request:
    if mode == "documentation":
        return urllib.request.Request(
            DOCUMENT_URL,
            headers={"User-Agent": "FreeLLM-public-api-probe/1.0", "Accept": "text/html"},
            method="GET",
        )
    if mode != "authenticated_chat":
        raise ValueError("unsupported probe mode")
    if not key or not key.startswith("sk-"):
        raise ValueError("authenticated mode requires an sk- token from a private environment variable")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "只回复 OK"}],
        "max_tokens": 8,
        "stream": False,
    }
    return urllib.request.Request(
        CHAT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "User-Agent": "FreeLLM-public-api-probe/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )


def probe(mode: str, *, key: str | None = None, timeout: float = 12.0, opener=None, clock=None) -> dict:
    """Return only an allowlisted sanitized result; never persist any raw response."""
    if mode not in ("documentation", "authenticated_chat"):
        raise ValueError("unsupported probe mode")
    if not 2 <= timeout <= 20:
        raise ValueError("timeout must be between 2 and 20 seconds")
    report = {
        "schemaVersion": 1,
        "providerId": PROVIDER_ID,
        "checkedAt": _utc_now(),
        "probeType": mode,
        "outcome": "not_configured",
        "httpStatus": None,
        "latencyMs": None,
        "modelId": MODEL if mode == "authenticated_chat" else None,
        "evidenceSource": "freellm_automated_probe",
        "region": "unknown",
        "rawPayloadStored": False,
    }
    if mode == "authenticated_chat" and (not key or not key.startswith("sk-")):
        return report
    req = build_request(mode, key)
    if opener is None:
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()), _NoRedirect()
        )
    timer = clock or time.monotonic
    started = timer()
    code = None
    content = b""
    try:
        with opener.open(req, timeout=timeout) as response:
            code = response.status
            content = response.read(MAX_RESPONSE_BYTES)
    except urllib.error.HTTPError as error:
        code = error.code
        error.close()
    except Exception:  # Never log exception details; URLs/headers can contain secrets.
        report["outcome"] = "network_error"
    elapsed = int(max(0, (timer() - started) * 1000))
    report["latencyMs"] = elapsed
    report["httpStatus"] = code
    if code is not None:
        report["outcome"] = _status_from_http(
            code, valid=_valid_response(mode, content) if code == 200 else False, mode=mode
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["documentation", "authenticated_chat"], default="documentation")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args(argv)
    result = probe(args.mode, key=os.environ.get(TOKEN_ENV) if args.mode == "authenticated_chat" else None, timeout=args.timeout)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"probe={result['probeType']} outcome={result['outcome']} http={result['httpStatus']} (no response body recorded)")
    return 0  # outages are data points, not reasons to throw away monitoring artifacts


if __name__ == "__main__":
    raise SystemExit(main())
