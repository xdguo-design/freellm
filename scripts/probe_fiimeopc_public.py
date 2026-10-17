"""Anonymous FiimeOPC preflight. NEVER register, authenticate or create a model job.

A reachable website or 401 on /models is not evidence of free quotas or real
inference. This script intentionally never marks a candidate as verified.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://opc.fiime.cn"
PATHS = ["/zh-cn/", "/register", "/api/model-service/v1/models"]
MAX_BODY = 200_000


def get_status(url: str, timeout: float = 15) -> dict:
    req = request.Request(url, headers={
        "User-Agent": "FreeLLM-FiimeOPC-Preflight/1.0 (read-only; no credentials)",
        "Accept": "text/html,application/json",
    })
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read(MAX_BODY + 1)
            return {
                "url": url, "httpStatus": response.status,
                "contentType": response.headers.get("Content-Type", ""),
                "bodyTruncated": len(body) > MAX_BODY,
            }
    except error.HTTPError as exc:
        return {"url": url, "httpStatus": exc.code, "authenticated": False}
    except (error.URLError, TimeoutError, OSError) as exc:
        return {"url": url, "error": type(exc).__name__, "message": str(exc)[:160]}


def main() -> int:
    rows = [get_status(HOST + path) for path in PATHS]
    report = {
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "FiimeOPC", "tests": rows,
        "registered": False, "authProvided": False, "inferenceTested": False,
        "rewardVerified": False, "publicationVerdict": "draft_pending_review",
    }
    output = ROOT / ".tmp" / "fiimeopc-public-preflight.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # A network outage is not proof of fraud; leave candidate in review.
    # Only fail on invalid script logic (for example an empty check list).
    return 0 if len(rows) == len(PATHS) else 2


if __name__ == "__main__":
    raise SystemExit(main())
