"""Fetch official AI release/changelog pages and track content fingerprints."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\\s+")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def normalize_text(raw: str) -> str:
    raw = re.sub(r"<script\\b[\\s\\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style\\b[\\s\\S]*?</style>", " ", raw, flags=re.I)
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", raw))).strip()


def fetch_source(source: dict, timeout: int) -> dict:
    url = str(source["url"])
    request = urllib.request.Request(url, headers={"User-Agent": "FreeLLM-AI-Radar/1.0 (+https://freellm.top/)"})
    row = {"id": source["id"], "vendor": source.get("vendor"), "kind": source.get("kind"), "url": url, "status": "error"}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_bytes = response.read(int(source.get("maxBytes") or 2_000_000))
            raw = raw_bytes.decode("utf-8", errors="replace")
            visible = normalize_text(raw)
            title_match = TITLE_RE.search(raw)
            title = normalize_text(title_match.group(1)) if title_match else ""
            lower = visible.casefold()
            row.update({
                "status": "ok",
                "httpStatus": getattr(response, "status", 200),
                "finalUrl": response.geturl(),
                "title": title,
                "bytes": len(raw_bytes),
                "sha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
                "matchedKeywords": [keyword for keyword in source.get("keywords", []) if str(keyword).casefold() in lower],
            })
    except urllib.error.HTTPError as exc:
        row.update({"status": "http_error", "httpStatus": exc.code, "error": str(exc)})
    except Exception as exc:
        row.update({"status": "fetch_error", "error": str(exc)})
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()

    sources = read_json(Path(args.sources), [])
    if not isinstance(sources, list) or not sources:
        raise SystemExit("AI radar source registry must be a non-empty list")
    previous_payload = read_json(Path(args.baseline), {}) if args.baseline else {}
    previous_rows = {str(row.get("id")): row for row in (previous_payload.get("sources") or []) if isinstance(row, dict) and row.get("id")}

    rows = []
    for source in sources:
        row = fetch_source(source, args.timeout)
        previous = previous_rows.get(str(row["id"]))
        old_hash = previous.get("sha256") if previous else None
        row["changed"] = bool(old_hash and row.get("sha256") and old_hash != row["sha256"])
        row["previousSha256"] = old_hash
        rows.append(row)

    payload = {
        "checkedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sourceCount": len(rows),
        "okCount": sum(row["status"] == "ok" for row in rows),
        "changedCount": sum(bool(row.get("changed")) for row in rows),
        "sources": rows,
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("sourceCount", "okCount", "changedCount")}, ensure_ascii=False))
    for row in rows:
        marker = "CHANGED" if row.get("changed") else row["status"].upper()
        print(f"{marker:10} {row['vendor']}: {row['url']}")
    return 1 if payload["okCount"] == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
