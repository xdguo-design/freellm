#!/usr/bin/env python3
"""Required real MiMo-V2.6-Flash smoke test through the official OpenCode CLI.

OpenCode's hosted free tier rejects direct anonymous HTTP clients, but the
official OpenCode client can use models explicitly listed in its free pool.
This release gate installs/runs the normal CLI, verifies the exact model ID is
present, sends a minimal generation request, and requires real assistant text.

No API key, browser login, mock response, or skip path is used.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time

MODEL = "opencode/mimo-v2.6-flash-free"
PROMPT = "Reply with exactly: MiMo OK"


def _run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def extract_text(jsonl: str) -> str:
    parts: list[str] = []
    for raw in jsonl.splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if isinstance(event.get("text"), str) and event["text"].strip():
            parts.append(event["text"].strip())

        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())

    return "\n".join(parts).strip()


def run(timeout: int) -> int:
    binary = shutil.which("opencode")
    if not binary:
        print(
            "BLOCKED: OpenCode CLI is not installed. Install opencode-ai first.",
            file=sys.stderr,
        )
        return 2

    version = _run([binary, "--version"], timeout=30)
    if version.returncode != 0:
        print(f"FAILED: opencode --version: {version.stderr[:1000]}", file=sys.stderr)
        return 1
    cli_version = version.stdout.strip()

    models = _run([binary, "models", "opencode", "--refresh"], timeout=60)
    if models.returncode != 0:
        print(f"FAILED: unable to refresh OpenCode models: {models.stderr[:1500]}", file=sys.stderr)
        return 1
    if MODEL not in models.stdout.split():
        print(f"FAILED: {MODEL} is not present in the refreshed OpenCode model list", file=sys.stderr)
        return 1

    started = time.perf_counter()
    try:
        generation = _run(
            [
                binary,
                "run",
                "--model",
                MODEL,
                "--format",
                "json",
                PROMPT,
            ],
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"FAILED: real MiMo generation exceeded {timeout}s", file=sys.stderr)
        return 1

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    if generation.returncode != 0:
        diagnostic = (generation.stderr or generation.stdout)[-2000:]
        print(f"FAILED: OpenCode/MiMo exited {generation.returncode}: {diagnostic}", file=sys.stderr)
        return 1

    text = extract_text(generation.stdout)
    if not text:
        print("FAILED: OpenCode completed but returned no assistant text", file=sys.stderr)
        return 1
    if "MiMo OK" not in text:
        print(f"FAILED: unexpected model output: {text[:500]}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "passed",
                "provider": "OpenCode Zen free tier",
                "client": "OpenCode CLI",
                "clientVersion": cli_version,
                "model": MODEL,
                "latencyMs": elapsed_ms,
                "output": text[:240],
                "actualUsageVerified": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=150)
    args = parser.parse_args()
    return run(args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
