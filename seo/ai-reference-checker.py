#!/usr/bin/env python3
"""Evidence-based AI search citation audit.

This does NOT scrape chatbot answers, query DuckDuckGo for shared conversations,
or infer citations from brand mentions. Each checked answer is recorded manually
with a source link or screenshot reference. Missing observations stay UNKNOWN.

Usage:
  python seo/ai-reference-checker.py
  python seo/ai-reference-checker.py --input private/geo-observations.csv --output private/geo-report.json
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEYWORDS = ROOT / "seo" / "geo-keywords.json"
DEFAULT_OBSERVATIONS = ROOT / "seo" / "geo-observations.example.csv"
ENGINES = ("chatgpt_search", "perplexity", "gemini", "google_ai_mode")
REQUIRED_FIELDS = ("checked_at", "engine", "query", "result", "cited_url", "evidence_url", "evidence_path", "notes")
VALID_RESULTS = {"cited", "not_cited"}


def site_path(url: str, host: str = "freellm.top") -> str | None:
    """Only count a direct, HTTPS link to the target host (not a lookalike)."""
    try:
        parsed = urlsplit(url.strip())
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
            return None
        if hostname not in {host, "www." + host} or parsed.port not in {None, 443}:
            return None
        path = parsed.path or "/"
        return "/" if path == "/" else "/" + path.strip("/") + "/"
    except ValueError:
        return None


def load_keywords(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("keyword configuration must be a nonempty JSON list")
    seen = set()
    for item in data:
        if not isinstance(item, dict) or not all(item.get(k) for k in ("query", "page", "group")):
            raise ValueError("each keyword needs query, page and group")
        if item["query"] in seen or item["group"] not in {"treatment", "control"}:
            raise ValueError("duplicate keyword or invalid experiment group")
        if site_path(item["page"]) is None:
            raise ValueError("keyword page must be an HTTPS URL on freellm.top")
        seen.add(item["query"])
    return data


def load_observations(path: Path, queries: set[str]) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    records = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or any(field not in reader.fieldnames for field in REQUIRED_FIELDS):
            raise ValueError("CSV is missing required columns: " + ", ".join(REQUIRED_FIELDS))
        for row_number, row in enumerate(reader, start=2):
            row = {field: (row.get(field) or "").strip() for field in REQUIRED_FIELDS}
            if not any(row.values()):
                continue
            if row["query"] not in queries or row["engine"] not in ENGINES or row["result"] not in VALID_RESULTS:
                raise ValueError(f"invalid query, engine or result at CSV row {row_number}")
            try:
                checked_at = datetime.fromisoformat(row["checked_at"].replace("Z", "+00:00"))
                if checked_at.tzinfo is None or checked_at.utcoffset() is None:
                    raise ValueError("timezone required")
            except ValueError as exc:
                raise ValueError(f"invalid checked_at at CSV row {row_number}: {exc}") from exc
            if row["result"] == "cited":
                if site_path(row["cited_url"]) is None:
                    raise ValueError(f"cited link is not a direct freellm.top HTTPS URL at row {row_number}")
                if not row["evidence_url"] and not row["evidence_path"]:
                    raise ValueError(f"a citation needs answer URL or screenshot evidence at row {row_number}")
            elif row["cited_url"]:
                raise ValueError(f"not_cited must not contain cited_url at row {row_number}")
            if row["evidence_url"] and urlsplit(row["evidence_url"]).scheme not in {"http", "https"}:
                raise ValueError(f"invalid evidence_url at row {row_number}")
            row["_checked_at"] = checked_at.astimezone(timezone.utc)
            records.append(row)
    return records


def build_report(keywords: list[dict], records: list[dict]) -> dict:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "human-observed answers with answer URL or screenshot evidence; not automated citation verification",
        "warning": "not_checked is UNKNOWN, not zero; cited means manually observed, not verified by provider API or Google ranking",
        "keywords": [],
        "summary": {engine: {"cited": 0, "not_cited": 0, "not_checked": 0} for engine in ENGINES},
    }
    for keyword in keywords:
        checks = {}
        for engine in ENGINES:
            matches = [r for r in records if r["query"] == keyword["query"] and r["engine"] == engine]
            if not matches:
                checks[engine] = {"status": "not_checked", "checked_at": None, "cited_pages": [], "evidence": []}
                report["summary"][engine]["not_checked"] += 1
                continue
            latest = max(r["_checked_at"] for r in matches)
            latest_rows = [r for r in matches if r["_checked_at"] == latest]
            results = {r["result"] for r in latest_rows}
            if len(results) > 1:
                raise ValueError(f"contradictory evidence for {keyword['query']} / {engine} at {latest.isoformat()}")
            result = results.pop()
            pages = sorted({site_path(r["cited_url"]) for r in latest_rows if r["result"] == "cited"})
            evidence = sorted({r["evidence_url"] or r["evidence_path"] for r in latest_rows if r["evidence_url"] or r["evidence_path"]})
            checks[engine] = {
                "status": result, "checked_at": latest.isoformat(), "cited_pages": pages,
                "evidence": evidence, "observations": len(latest_rows),
            }
            report["summary"][engine][result] += 1
        report["keywords"].append({**keyword, "checks": checks})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS)
    parser.add_argument("--input", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--output", type=Path, help="optional output JSON path; otherwise print to stdout")
    args = parser.parse_args()
    try:
        keywords = load_keywords(args.keywords)
        observations = load_observations(args.input, {item["query"] for item in keywords})
        report = build_report(keywords, observations)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print(f"Wrote {args.output}: manual observations only; unknown checks remain not_checked")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
