#!/usr/bin/env python3
"""Live MiMo-V2.6-Flash smoke test for verified FreeLLM routes.

This script deliberately requires the caller's own credential. It never reads,
prints, stores, or commits token values. Use --check-config to verify routing
without making a model request.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROUTES = {
    "opencode": {
        "label": "OpenCode Zen / MiMo-V2.6-Flash Free",
        "endpoint": "https://opencode.ai/zen/v1/chat/completions",
        "model": "mimo-v2.6-flash-free",
        "env": "OPENCODE_API_KEY",
    },
    "puter": {
        "label": "Puter / Xiaomi MiMo-V2.6-Flash",
        "endpoint": "https://api.puter.com/puterai/openai/v1/chat/completions",
        "model": "xiaomi/mimo-v2.6-flash",
        "env": "PUTER_AUTH_TOKEN",
    },
}

DEFAULT_PROMPT = "Reply with exactly: MiMo OK"


def build_payload(route: dict[str, str], prompt: str) -> bytes:
    return json.dumps(
        {
            "model": route["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 32,
        },
        ensure_ascii=False,
    ).encode("utf-8")


def extract_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts).strip()
    return ""


def run(provider: str, prompt: str, timeout: int) -> int:
    route = ROUTES[provider]
    token = os.environ.get(route["env"], "").strip()
    if not token:
        print(
            f"BLOCKED: {route['env']} is not set. "
            f"Provide your own credential to run a real generation test.",
            file=sys.stderr,
        )
        return 2

    request = urllib.request.Request(
        route["endpoint"],
        data=build_payload(route, prompt),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "FreeLLM-MiMo-V2.6-live-test/1.0",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:1200]
        print(f"FAILED: HTTP {error.code} from {route['label']}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"FAILED: network error from {route['label']}: {error.reason}", file=sys.stderr)
        return 1

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"FAILED: HTTP {status} returned non-JSON data", file=sys.stderr)
        return 1

    text = extract_text(payload)
    if not text:
        print(
            f"FAILED: HTTP {status} returned no assistant text. "
            f"response keys={sorted(payload.keys())}",
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "status": "passed",
                "provider": provider,
                "route": route["label"],
                "model": route["model"],
                "httpStatus": status,
                "latencyMs": elapsed_ms,
                "output": text,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=sorted(ROUTES), default="opencode")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Print route/model/env names without sending a request or reading a token.",
    )
    args = parser.parse_args()

    route = ROUTES[args.provider]
    if args.check_config:
        print(
            json.dumps(
                {
                    "provider": args.provider,
                    "label": route["label"],
                    "endpoint": route["endpoint"],
                    "model": route["model"],
                    "credentialEnv": route["env"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    return run(args.provider, args.prompt, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
