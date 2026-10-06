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

try:  # direct script execution puts scripts/ on sys.path
    from site_budgets import HOME_HTML_MAX_BYTES
except ImportError:  # package import from the repository root
    from scripts.site_budgets import HOME_HTML_MAX_BYTES


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_AGE_DAYS = 7
# 首页是一份自包含的应用壳：整份 offers JSON 内嵌在 HTML 里（约占 44%），
# 再加静态兜底卡片、内联 CSS/JS。每加一个内容字段，这个文件就长一点，
# 所以预算按「当前实测 + 约 2% 余量」维护，而不是钉死一个旧数字。
# 首页仍保留内嵌兜底数据；模型目录已进一步降为 26 条/页，
# 模型中心仅保留 24 条快速预览，避免重复内嵌完整模型表。
# Homepage budget is shared with the browser performance check.
DEFAULT_SIZE_BUDGETS = {
    "design/free-china-ai-index.html": HOME_HTML_MAX_BYTES,
    "models/center/index.html": 600 * 1024,
    "models/all/index.html": 340 * 1024,
}
# 分页页数随目录涨缩（301 模型时 5 页、220 模型时 3 页），按 models.json 现值
# 动态生成预算，避免目录瘦身后再为已删除的分页页保预算、或新分页漏保。
def _models_page_budgets() -> dict[str, int]:
    budgets: dict[str, int] = {}
    models_path = ROOT / "data" / "models.json"
    try:
        models = json.loads(models_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return budgets
    try:
        from build_seo_pages import MODELS_PER_PAGE  # 直接运行时 scripts/ 在 sys.path
    except ImportError:
        from .build_seo_pages import MODELS_PER_PAGE  # 作为 scripts.site_health 导入时

    total_pages = max(1, -(-len(models) // MODELS_PER_PAGE)) if models else 1
    for page_num in range(2, total_pages + 1):
        budgets[f"models/all/page/{page_num}/index.html"] = 350 * 1024
    return budgets


DEFAULT_SIZE_BUDGETS.update(_models_page_budgets())
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


def load_enabled_model_sources(root: Path) -> tuple[list[dict] | None, str | None]:
    """Load the tracked source identities used to verify observation evidence."""
    path = root / "data" / "official-model-sources.json"
    try:
        registry = _read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return None, f"official model source registry cannot be checked: {error}"
    if not isinstance(registry, list):
        return None, "official model source registry must be a JSON list"
    enabled_sources: list[dict] = []
    seen_ids: set[str] = set()
    for index, source in enumerate(registry):
        if not isinstance(source, dict):
            return None, f"official model source registry item {index} is not an object"
        enabled = source.get("enabled", True)
        if type(enabled) is not bool:
            return None, f"official model source registry item {index} has an invalid enabled flag"
        if not enabled:
            continue
        source_id = source.get("id")
        url = source.get("url")
        if not isinstance(source_id, str) or not source_id.strip() or not isinstance(url, str) or not url.strip():
            return None, f"official model source registry item {index} is missing an enabled source id or URL"
        if source_id in seen_ids:
            return None, f"official model source registry has duplicate enabled source id: {source_id}"
        seen_ids.add(source_id)
        enabled_sources.append({"id": source_id, "url": url})
    return enabled_sources, None


def check_model_observation(
    path: Path,
    as_of: date,
    max_age_days: int,
    expected_sources: Sequence[Mapping[str, str]] | None = None,
) -> dict:
    """Validate successful official-source scan evidence, never runtime availability."""
    result = {
        "status": "unavailable",
        "fresh": False,
        "complete": False,
        "asOf": None,
        "ageDays": None,
        "sourceCount": 0,
        "evidencePath": str(path),
        "errors": [],
    }
    try:
        report = _read_json(path)
    except FileNotFoundError:
        result["errors"].append(f"model source observation evidence is unavailable: {path} does not exist")
        return result
    except (OSError, json.JSONDecodeError) as error:
        result["status"] = "invalid"
        result["errors"].append(f"model source observation evidence is invalid: {error}")
        return result

    if not isinstance(report, dict) or report.get("schemaVersion") != 1 or report.get("observationKind") != "official_model_source_scan":
        result["status"] = "invalid"
        result["errors"].append("model source observation evidence has an unsupported schema or observation kind")
        return result
    try:
        observed = parse_iso_date(report.get("asOf"))
    except ValueError as error:
        result["status"] = "invalid"
        result["errors"].append(f"model source observation date is invalid: {error}")
        return result

    enabled = report.get("enabledSourceIds")
    sources = report.get("sources")
    failures = report.get("failures")
    if not isinstance(enabled, list) or not all(isinstance(item, str) and item.strip() for item in enabled) \
            or not isinstance(sources, list) or not isinstance(failures, list):
        result["status"] = "invalid"
        result["errors"].append("model source observation evidence is missing enabled sources or source results")
        return result
    age = (as_of - observed).days
    if type(report.get("complete")) is not bool or report.get("status") not in {"complete", "partial", "unavailable"}:
        result["status"] = "invalid"
        result["errors"].append("model source observation status fields are invalid")
        return result
    if not enabled and not sources and not failures and report.get("status") == "unavailable" and report.get("complete") is False:
        if expected_sources:
            result["status"] = "invalid"
            result["errors"].append("model source observation evidence omits enabled registry sources")
        result.update({"asOf": observed.isoformat(), "ageDays": age})
        result["errors"].append("model source observation evidence is unavailable: no enabled sources were scanned")
        return result

    source_ids: list[str] = []
    source_by_id: dict[str, dict] = {}
    malformed = False
    for item in sources:
        if not isinstance(item, dict):
            malformed = True
            continue
        source_id = item.get("id")
        url = item.get("url")
        status = item.get("status")
        row_count = item.get("rowCount")
        truncated = item.get("truncated")
        valid = (
            isinstance(source_id, str) and bool(source_id.strip())
            and isinstance(url, str) and bool(url.strip())
            and isinstance(status, str) and status in {"success", "failed"}
        )
        valid = valid and type(row_count) is int and row_count >= 0 and type(truncated) is bool
        if status == "failed":
            valid = valid and isinstance(item.get("reason"), str) and bool(item["reason"].strip())
        if not valid:
            malformed = True
            continue
        source_ids.append(source_id)
        source_by_id[source_id] = item

    failure_ids: list[str] = []
    for item in failures:
        if not isinstance(item, dict):
            malformed = True
            continue
        source_id = item.get("providerId")
        url = item.get("url")
        reason = item.get("reason")
        status = item.get("status")
        if not all(isinstance(value, str) and value.strip() for value in (source_id, url, reason, status)):
            malformed = True
            continue
        failure_ids.append(source_id)
        source = source_by_id.get(source_id)
        if source is None or source.get("status") != "failed" or source.get("url") != url:
            malformed = True

    if (len(set(enabled)) != len(enabled) or len(set(source_ids)) != len(source_ids)
            or len(set(failure_ids)) != len(failure_ids) or sorted(source_ids) != sorted(enabled)):
        malformed = True
    failed_source_ids = {source_id for source_id, item in source_by_id.items() if item.get("status") == "failed"}
    if failed_source_ids != set(failure_ids):
        malformed = True
    if expected_sources is not None:
        expected_pairs = [
            (item.get("id"), item.get("url"))
            for item in expected_sources
            if isinstance(item, Mapping)
        ]
        actual_pairs = [
            (item.get("id"), item.get("url"))
            for item in sources
            if isinstance(item, dict)
        ]
        pairs_are_strings = (
            len(expected_pairs) == len(expected_sources)
            and all(isinstance(source_id, str) and isinstance(url, str) for source_id, url in expected_pairs)
            and all(isinstance(source_id, str) and isinstance(url, str) for source_id, url in actual_pairs)
        )
        if not pairs_are_strings:
            malformed = True
        elif (len(expected_pairs) != len(actual_pairs)
              or len({source_id for source_id, _ in expected_pairs}) != len(expected_pairs)
              or set(expected_pairs) != set(actual_pairs)):
            malformed = True
    computed_complete = all(
        isinstance(item, dict) and item.get("status") == "success" and item.get("truncated") is False
        for item in sources
    ) and not failures
    expected_status = "complete" if computed_complete else "partial"
    if report.get("status") != expected_status or report.get("complete") is not computed_complete:
        malformed = True
    if malformed:
        result.update({"status": "invalid", "asOf": observed.isoformat(), "ageDays": age, "sourceCount": len(enabled)})
        result["errors"].append("model source observation evidence contains malformed, duplicate, or inconsistent source records")
        return result

    complete = computed_complete
    result.update({
        "status": "complete" if complete else "failed",
        "complete": complete,
        "asOf": observed.isoformat(),
        "ageDays": age,
        "sourceCount": len(enabled),
    })
    if not complete:
        result["errors"].append("model source observation scan is partial or failed; every enabled source must succeed")
    if age < 0:
        result["status"] = "invalid"
        result["errors"].append(f"model source observation date {observed} is in the future relative to {as_of}")
    elif age > max_age_days:
        result["status"] = "stale"
        result["errors"].append(f"model source observation date {observed} is {age} days old; maximum is {max_age_days}")
    result["fresh"] = complete and 0 <= age <= max_age_days
    return result


def build_report(
    root: Path = ROOT,
    *,
    as_of: date | None = None,
    env: Mapping[str, str] | None = None,
    git_head: str | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    model_observation_path: Path | None = None,
) -> dict:
    checked_on = as_of or date.today()
    errors: list[str] = []
    warnings: list[str] = []
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
        offer_freshness = check_freshness(
            [item.get("lastVerifiedAt") for item in offers if isinstance(item, dict)],
            checked_on,
            max_age_days,
            "offers freshness",
        )
        warnings.extend(message for message in offer_freshness if "days old; maximum is" in message)
        errors.extend(message for message in offer_freshness if "days old; maximum is" not in message)
    except (OSError, json.JSONDecodeError, TypeError) as error:
        errors.append(f"offers data cannot be checked: {error}")
    try:
        models = _read_json(models_path)
        if not isinstance(models, list):
            errors.append("models data cannot be checked: expected a JSON list")
        else:
            model_freshness = check_freshness(
                [item.get("lastSeenAt") for item in models if isinstance(item, dict)],
                checked_on,
                max_age_days,
                "models freshness",
            )
            warnings.extend(message for message in model_freshness if "days old; maximum is" in message)
            errors.extend(message for message in model_freshness if "days old; maximum is" not in message)
    except (OSError, json.JSONDecodeError, TypeError) as error:
        errors.append(f"models data cannot be checked: {error}")
    observation_path = model_observation_path or root / ".tmp" / "model-audit" / "model-source-health.json"
    expected_sources, registry_error = load_enabled_model_sources(root)
    model_observation = check_model_observation(
        observation_path,
        checked_on,
        max_age_days,
        expected_sources=expected_sources,
    )
    if registry_error:
        model_observation["status"] = "invalid"
        model_observation["fresh"] = False
        model_observation["errors"].append(registry_error)
    errors.extend(model_observation["errors"])

    return {
        "asOf": checked_on.isoformat(),
        "releaseSha": release_sha,
        "sizes": sizes,
        "maxAgeDays": max_age_days,
        "modelObservation": model_observation,
        "warnings": warnings,
        "staleCount": len(warnings),
        "errors": errors,
        "ok": not errors,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--as-of", help="Override the date used for freshness checks (YYYY-MM-DD)")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--model-observation", help="Official model-source scan health JSON; defaults to ROOT/.tmp/model-audit/model-source-health.json")
    parser.add_argument("--report", help="Write the JSON report to this path")
    args = parser.parse_args(argv)
    try:
        as_of = parse_iso_date(args.as_of) if args.as_of else None
    except ValueError as error:
        parser.error(str(error))
    root = Path(args.root)
    observation_path = Path(args.model_observation) if args.model_observation else root / ".tmp" / "model-audit" / "model-source-health.json"
    report = build_report(root, as_of=as_of, max_age_days=args.max_age_days, model_observation_path=observation_path)
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
