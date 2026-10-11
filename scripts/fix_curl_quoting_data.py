#!/usr/bin/env python3
"""Rewrite curl examples in source data so ``$VAR`` sits in double quotes.

Bash does not expand variables inside single quotes, so a stored example like
``-H 'Authorization: Bearer ${KEY}'`` produces a 401 when pasted.  This script
applies :func:`scripts.shell_examples.fix_curl_quoting` to every string in
``data/offers.json`` and ``data/operations/*.json``.  It only changes curl
lines (JSON bodies without variables keep their single quotes) and is
idempotent.  Use ``--check`` in CI to fail when a bad example sneaks back in.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.shell_examples import fix_curl_quoting, single_quoted_curl_vars  # noqa: E402

DEFAULT_FILES = ["data/offers.json", "data/operations/*.json"]


def _walk(value, path: str, problems: list[tuple[str, str, str]]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _walk(item, f"{path}.{key}", problems)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk(item, f"{path}[{index}]", problems)
    elif isinstance(value, str) and single_quoted_curl_vars(value):
        problems.append((path, value, fix_curl_quoting(value) or value))


def _rewrite(text: str, problems: list[tuple[str, str, str]]) -> str:
    """Replace each bad string in place so the file's own formatting survives."""
    for _path, old, new in problems:
        if json.dumps(old, ensure_ascii=False) not in text and json.dumps(new, ensure_ascii=False) in text:
            continue  # identical string already rewritten (e.g. command == examples.curl)
        for ensure_ascii in (False, True):
            old_literal = json.dumps(old, ensure_ascii=ensure_ascii)
            if old_literal in text:
                text = text.replace(old_literal, json.dumps(new, ensure_ascii=ensure_ascii))
                break
        else:  # pragma: no cover - only for unusual escaping
            raise SystemExit(f"could not locate string at {_path} for in-place rewrite")
    return text


def iter_files(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(ROOT.glob(pattern)))
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report problems without writing")
    parser.add_argument("files", nargs="*", default=DEFAULT_FILES)
    args = parser.parse_args(argv)
    total = 0
    for file in iter_files(args.files):
        text = file.read_text(encoding="utf-8")
        data = json.loads(text)
        problems: list[tuple[str, str, str]] = []
        _walk(data, "$", problems)
        if not problems:
            continue
        total += len(problems)
        rel = file.relative_to(ROOT)
        print(f"{rel}: {len(problems)} curl example(s) with $VAR inside single quotes")
        if not args.check:
            rewritten = _rewrite(text, problems)
            json.loads(rewritten)  # still valid JSON
            file.write_text(rewritten, encoding="utf-8")
    if args.check and total:
        print(f"FAIL: {total} curl example(s) need double quotes around $VAR", file=sys.stderr)
        return 1
    print(f"{'checked' if args.check else 'fixed'}: {total} example(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
