"""「每日发现」 rules (2026-10-12): first-seen ids, 7-day window, editorial copy."""

import json
import re
from pathlib import Path

from scripts import daily_discoveries as dd
from scripts.build_seo_pages import render_daily_log_page

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "data" / "daily-log"


def _logs():
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(LOG_DIR.glob("20??-??-??.json"))]


def _log(day, events=(), curated=()):
    return {"date": day, "events": list(events), "curatedEvents": list(curated),
            "sourceHealth": {"models": {"status": "ok"}, "offers": {"status": "ok"}}}


def test_an_id_counts_only_on_its_first_date_and_once_per_log():
    logs = [
        _log("2026-10-11", [{"eventType": "new", "id": "a", "kind": "offer", "title": "A"}]),
        _log("2026-10-12",
             [{"eventType": "new", "id": "a", "kind": "offer", "title": "A",
               "reason": "not present in the previous successful snapshot"},
              {"eventType": "new_route", "id": "b", "kind": "model", "title": "B"}],
             [{"eventType": "new_route", "id": "b", "kind": "model", "title": "B"},
              {"eventType": "recovered", "id": "c", "kind": "offer", "title": "C"}]),
    ]
    first = dd.first_seen_discoveries(logs)
    assert [e["id"] for e in first["2026-10-11"]] == ["a"]
    assert [e["id"] for e in first["2026-10-12"]] == ["b"]


def test_week_covers_seven_calendar_days_and_marks_missing_logs_honestly():
    logs = [_log("2026-10-12", curated=[{"eventType": "new", "id": "x", "kind": "tool", "title": "X"}]),
            _log("2026-10-09")]
    week = dd.discovery_week(logs)
    assert [day["date"] for day in week] == [
        "2026-10-12", "2026-10-11", "2026-10-10", "2026-10-09", "2026-10-08", "2026-10-07", "2026-10-06"]
    assert [day["logged"] for day in week] == [True, False, False, True, False, False, False]
    page = render_daily_log_page(logs, "https://freellm.top")
    assert page.count(dd.NOT_SCANNED_LABEL + "，") == 5
    assert dd.NO_DISCOVERY_LABEL in page
    assert "近 7 天发现 · 共 <strong data-discovery-week-total>1</strong> 项" in page


def test_rows_read_as_editorial_lines_and_hide_scanner_reasons():
    event = {"eventType": "new", "id": "u2", "kind": "offer", "title": "云知声 U2 Flash · 国庆免费月 API",
             "details": {"provider": "Unisound MaaS", "status": "verified", "validitySummary": "限时免费至 2026-10-31"}}
    assert dd.headline(event) == "云知声 U2 Flash · 国庆免费月 API，限时免费到 10-31"
    raw = {"eventType": "new", "id": "o/m", "kind": "model", "title": "mistral-large-4",
           "reason": "not present in the previous successful snapshot",
           "details": {"provider": "Ollama", "status": "online"}}
    assert dd.headline(raw) == "Ollama 上新模型 mistral-large-4"
    assert dd.summary(raw) == ""
    assert "snapshot" not in dd.human_reason(raw)
    assert dd.status_label(raw) == "官方列表可见，未实测"
    page = render_daily_log_page([_log("2026-10-12", [raw, event])], "https://freellm.top")
    assert "previous successful snapshot" not in page
    assert "Ollama 上新模型 mistral-large-4" in page


def test_published_logs_page_shows_latest_week_from_real_logs():
    logs = _logs()
    latest = dd.latest_log_date(logs)
    week = dd.discovery_week(logs)
    total = sum(len(day["events"]) for day in week)
    page = (ROOT / "logs" / "index.html").read_text(encoding="utf-8")
    assert "<title>每日发现 · FreeLLM" in page
    assert f'id="discovery-day-{latest}"' in page
    assert f"<strong data-discovery-week-total>{total}</strong>" in page
    assert "previous successful snapshot" not in page
    assert page.index('id="discovery-week"') < page.index('class="ref-update-metrics"')
    for day in week:
        state = "logged" if day["logged"] else "not-scanned"
        assert re.search(rf'data-discovery-day="{day["date"]}" data-discovery-state="{state}" data-discovery-count="{len(day["events"])}"', page)


def test_joycode_first_listed_on_1011_and_momo_code_curated_on_1012():
    logs = {log["date"]: log for log in _logs()}
    first = dd.first_seen_discoveries(list(logs.values()))
    joycode_days = [day for day, items in first.items() if any(e.get("id") == "joycode" for e in items)]
    assert joycode_days == ["2026-10-11"]
    # The 10-12 scanner re-detection of JoyCode was removed from the log itself.
    assert not any(e.get("id") == "joycode" for e in logs["2026-10-12"].get("events") or [])
    momo = [e for e in logs["2026-10-12"].get("curatedEvents") or [] if e.get("id") == "momo-code"]
    assert len(momo) == 1
    details = momo[0]["details"]
    assert details["sourceUrl"] == "https://github.com/momozi1996/momo-code"
    assert details["license"] == "MIT" and details["release"] == "v2.0.0" and details["stars"] == 1087
    assert "实验" in momo[0]["title"]
    agents = json.loads((ROOT / "data" / "featured_agents.json").read_text(encoding="utf-8"))
    assert any(agent["id"] == "momo-code" for agent in agents)
