"""Static-site health gates for freshness, size budgets, and release traceability."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_AGE_DAYS = 7
DEFAULT_SIZE_BUDGETS = {
    "design/free-china-ai-index.html": 1024 * 1024,
    "models/center/index.html": 1024 * 1024,
    "models/all/index.html": 1024 * 1024,
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_iso_date(value: object) -> date:
    if not isinstance(value, str) or not ISO_DATE_RE.fullmatch(value):
        raise ValueError(f"invalid ISO date: {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"invalid ISO date: {value!r}") from error


def check_freshness(
    values: Sequence[object],
    as_of: date,
    max_age_days: int,
    label: str = "freshness",
) -> list[str]:
    errors = []
    for index, value in enumerate(values):
        try:
            observed = parse_iso_date(value)
        except ValueError as error:
            errors.append(f"{label} item {index}: {error}")
            continue
        age = (as_of - observed).days
        if age < 0:
            errors.append(f"{label} item {index}: date {value} is in the future relative to {as_of}")
        elif age > max_age_days:
            errors.append(f"{label} item {index}: date {value} is {age} days old; maximum is {max_age_days}")
    return errors


def check_size_budget(path: Path, budget: int) -> list[str]:
    if not path.is_file():
        return [f"{path}: file does not exist"]
    size = path.stat().st_size
    if size > budget:
        return [f"{path}: {size} bytes exceeds {budget}-byte budget"]
    return []


def resolve_release_sha(env: Mapping[str, str] | None = None, git_head: str | None = None) -> str:
    environment = os.environ if env is None else env
    candidate = environment.get("GITHUB_SHA") or git_head
    if not candidate or not SHA_RE.fullmatch(candidate.strip()):
        raise RuntimeError("release SHA is unavailable or invalid")
    return candidate.strip().lower()


def current_git_head(root: Path = ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(
    root: Path = ROOT,
    *,
    as_of: date | None = None,
    env: Mapping[str, str] | None = None,
    git_head: str | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> dict:
    checked_on = as_of or date.today()
    errors: list[str] = []
    try:
        release_sha = resolve_release_sha(env, current_git_head(root) if git_head is None else git_head)
    except RuntimeError as error:
        release_sha = None
        errors.append(str(error))

    sizes = {}
    for relative_path, budget in DEFAULT_SIZE_BUDGETS.items():
        path = root / relative_path
        sizes[relative_path] = {"bytes": path.stat().st_size if path.is_file() else None, "budget": budget}
        errors.extend(check_size_budget(path, budget))

    offers_path = root / "data" / "offers.json"
    models_path = root / "data" / "models.json"
    try:
        offers = _read_json(offers_path)
        errors.extend(check_freshness(
            [item.get("lastVerifiedAt") for item in offers if isinstance(item, dict)],
            checked_on,
            max_age_days,
            "offers freshness",
        ))
    except (OSError, json.JSONDecodeError, TypeError) as error:
        errors.append(f"offers data cannot be checked: {error}")
    try:
        models = _read_json(models_path)
        errors.extend(check_freshness(
            [item.get("lastSeenAt") for item in models if isinstance(item, dict)],
            checked_on,
            max_age_days,
            "models freshness",
        ))
    except (OSError, json.JSONDecodeError, TypeError) as error:
        errors.append(f"models data cannot be checked: {error}")

    return {
        "asOf": checked_on.isoformat(),
        "releaseSha": release_sha,
        "sizes": sizes,
        "maxAgeDays": max_age_days,
        "errors": errors,
        "ok": not errors,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--as-of", help="Override the date used for freshness checks (YYYY-MM-DD)")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--report", help="Write the JSON report to this path")
    args = parser.parse_args(argv)
    try:
        as_of = parse_iso_date(args.as_of) if args.as_of else None
    except ValueError as error:
        parser.error(str(error))
    report = build_report(Path(args.root), as_of=as_of, max_age_days=args.max_age_days)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not report["ok"]:
        print("site health check failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
