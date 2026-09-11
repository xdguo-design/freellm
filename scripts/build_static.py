"""Embed the JSON source into the static HTML fallback block."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.schema import validate_offers

START = '<script type="application/json" id="offer-data">'
END = "</script>"
LD_START = '<script type="application/ld+json" id="ld-dynamic">'


def update_daily_log_summary(html: str, data_path: Path) -> str:
    log_dir = data_path.parent / "daily-log"
    log_paths = sorted(log_dir.glob("*.json")) if log_dir.is_dir() else []
    if not log_paths:
        return html
    try:
        latest = json.loads(log_paths[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return html
    date = latest.get("date") if isinstance(latest, dict) else None
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return html
    events = [
        event
        for key in ("events", "curatedEvents")
        for event in (latest.get(key) or [])
        if isinstance(event, dict)
    ]
    new_count = sum(1 for event in events if event.get("eventType") in {"new", "new_route"})
    change_count = sum(1 for event in events if event.get("eventType") in {"new", "new_route", "recovered", "offline", "source_unavailable"})
    badge = f"新增 {new_count} 项" if new_count else ("今日有变化" if change_count else "今日无新增")
    year, month, day = date.split("-")
    label = f"{year} 年 {int(month)} 月 {int(day)} 日"
    replacement = f'▣ &nbsp;{label}</span><a class="intel-log-link" href="/logs/">查看今日变化 →</a>'
    updated = re.sub(r"▣\s*&nbsp;[^<]+</span>(?:<a class=\"intel-log-link\"[^>]*>查看(?:今日更新|今日变化) →</a>)?", replacement, html, count=1)
    badge_markup = f'<span class="intel-update-badge" id="daily-log-badge" data-new-count="{new_count}" data-change-count="{change_count}">{badge}</span>'
    return re.sub(r'<span[^>]*id="daily-log-badge"[^>]*>.*?</span>', badge_markup, updated, count=1, flags=re.S)


def update_static_item_list(html: str, data: list[dict]) -> str:
    start = html.find(LD_START)
    if start < 0:
        return html
    content_start = start + len(LD_START)
    end = html.find(END, content_start)
    if end < 0:
        raise SystemExit("Missing JSON-LD script closing tag in static HTML")
    try:
        structured = json.loads(html[content_start:end])
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid static JSON-LD: {error}") from error
    structured["@graph"][0]["itemListElement"] = [
        {"@type": "ListItem", "position": index, "name": offer["title"]}
        for index, offer in enumerate(data, start=1)
    ]
    replacement = "\n  " + json.dumps(structured, ensure_ascii=False, indent=2) + "\n  "
    return html[:content_start] + replacement + html[end:]


def build(data_path: Path, html_path: Path, check: bool = False) -> bool:
    errors = validate_offers(data_path)
    if errors:
        raise SystemExit("Invalid offers data:\n" + "\n".join(errors))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")
    start = html.find(START)
    if start < 0:
        raise SystemExit(f"Missing {START} in {html_path}")
    content_start = start + len(START)
    end = html.find(END, content_start)
    if end < 0:
        raise SystemExit(f"Missing JSON script closing tag in {html_path}")
    replacement = "\n  " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n  "
    updated = html[:content_start] + replacement + html[end:]
    updated = update_static_item_list(updated, data)
    updated = update_daily_log_summary(updated, data_path)
    if check:
        if updated != html:
            print(f"stale: {html_path} does not contain the current offers JSON")
            return False
        print(f"current: {html_path}")
        return True
    html_path.write_text(updated, encoding="utf-8")
    print(f"built: {html_path} from {data_path} ({len(data)} offers)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--html", default="design/free-china-ai-index.html")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return 0 if build(Path(args.data), Path(args.html), args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
