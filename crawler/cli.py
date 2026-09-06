"""Command-line entry point for validation, public scans, diffs and snapshots."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .diff import build_review_queue, compare_offers
from .fetch import fetch_public_page
from .schema import validate_offers


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="free-ai-index")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("path")

    diff = commands.add_parser("diff")
    diff.add_argument("--previous", required=True)
    diff.add_argument("--current", required=True)
    diff.add_argument("--out", required=True)

    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--input", required=True)
    snapshot.add_argument("--dir", required=True)

    scan = commands.add_parser("scan")
    scan.add_argument("--sources", required=True)
    scan.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    if args.command == "validate":
        errors = validate_offers(args.path)
        if errors:
            print("invalid:")
            print("\n".join(f"- {error}" for error in errors))
            return 1
        count = len(_read_json(args.path))
        print(f"valid: {count} offers")
        return 0
    if args.command == "diff":
        changes = compare_offers(_read_json(args.previous), _read_json(args.current))
        queue = build_review_queue(changes)
        _write_json(args.out, queue)
        print(f"review queue: {len(queue)} changes")
        return 0
    if args.command == "snapshot":
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = Path(args.dir) / f"offers-{timestamp}.json"
        _write_json(target, _read_json(args.input))
        print(f"snapshot: {target}")
        return 0
    if args.command == "scan":
        results = []
        for source in _read_json(args.sources):
            for url in source["urls"]:
                results.append({"offerId": source["offerId"], **fetch_public_page(url, source["allowedDomains"])})
        _write_json(args.out, results)
        failed = sum(1 for result in results if result["status"] != "ok")
        print(f"scan: {len(results)} sources, {failed} failed or rejected")
        return 1 if failed else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
