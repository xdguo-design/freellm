"""Validate the machine-readable FreeLLM evaluation framework."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_LEVELS = {"official_verified", "connectivity_tested", "full_evaluated"}
REQUIRED_SUITES = {"text-api-v1", "coding-agent-v1", "tool-use-v1", "web-research-v1", "multimodal-v1"}


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/evaluation-framework.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("version") != "freellm-eval-v1":
        errors.append("unexpected framework version")
    levels = {row.get("id") for row in payload.get("evidenceLevels", []) if isinstance(row, dict)}
    suites = {row.get("id") for row in payload.get("suites", []) if isinstance(row, dict)}
    if not REQUIRED_LEVELS <= levels:
        errors.append("missing evidence levels: " + ", ".join(sorted(REQUIRED_LEVELS - levels)))
    if not REQUIRED_SUITES <= suites:
        errors.append("missing evaluation suites: " + ", ".join(sorted(REQUIRED_SUITES - suites)))
    for suite in payload.get("suites", []):
        if not suite.get("dimensions"):
            errors.append(f"suite {suite.get('id')} has no dimensions")
    required_meta = set(payload.get("requiredRunMetadata", []))
    for field in ("provider", "modelId", "runAt", "rawEvidencePath", "successRate"):
        if field not in required_meta:
            errors.append(f"missing required run metadata field: {field}")
    if errors:
        for error in errors:
            print("ERROR", error)
        return 1
    print(f"evaluation framework ok: {len(levels)} evidence levels, {len(suites)} suites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
