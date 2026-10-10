"""Series 4 (2026-10-10): news corrections, scanner health gate, feed/date convention, relays."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crawler.change_log import (  # noqa: E402
    announced_offer_ids,
    atom_timestamp,
    build_daily_log,
    detect_stalled_scan,
    listing_date,
    public_listing_dates,
    scan_health_errors,
)
from crawler.source_tiers import THIRD_PARTY_RELAY_TIER, is_third_party_relay  # noqa: E402
from scripts.build_seo_pages import render_feed  # noqa: E402

DATA = ROOT / "data"
OFFERS = {offer["id"]: offer for offer in json.loads((DATA / "offers.json").read_text(encoding="utf-8"))}


def _logs() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted((DATA / "daily-log").glob("*.json"))]


def _log(day: str) -> dict:
    return json.loads((DATA / "daily-log" / f"{day}.json").read_text(encoding="utf-8"))


def _model(i: int, provider: str = "openrouter") -> dict:
    return {"id": f"{provider}/m{i}", "providerId": provider, "provider": provider, "model": f"m{i}", "status": "online"}


# ---------------------------------------------------------------- Qoder / Cerebras corrections

def test_qoder_qwen38_flash_extension_is_not_shown_as_ended():
    qoder = OFFERS["qoder"]
    assert qoder["status"] != "expired"
    assert "expires_at" not in qoder and "expired_scope" not in qoder
    assert "https://docs.qoder.com/zh/events/flashoffer" in qoder["sourceUrls"]
    assert "延期" in qoder["freeSummary"] and "10 月 1 日起继续" in qoder["freeSummary"]
    text = json.dumps(qoder, ensure_ascii=False)
    assert "PROMO ENDED" not in text
    assert "活动于 2026-09-30 结束" not in text
    page = (ROOT / "offers" / "qoder" / "index.html").read_text(encoding="utf-8")
    assert "PROMO ENDED" not in page and "已结束" not in page


def test_cerebras_free_credit_requires_card_and_expires_after_30_days():
    cerebras = OFFERS["cerebras-free"]
    assert cerebras["cardRequired"] == "yes"
    assert "需绑卡" in cerebras["freeSummary"] and "30 天" in cerebras["freeSummary"]
    assert "注册后送" not in json.dumps(cerebras, ensure_ascii=False)
    assert "Add a valid payment method" in cerebras["evidence"]
    assert "https://www.cerebras.ai/pricing" in cerebras["sourceUrls"]


# ---------------------------------------------------------------- scanner health gate

def test_identical_model_snapshot_on_a_later_day_is_flagged_as_stalled():
    models = [_model(i) for i in range(5)]
    previous = build_daily_log(None, models, [], "2026-10-03")
    assert "identical to 2026-10-03" in detect_stalled_scan(previous, copy.deepcopy(models), "2026-10-04")
    changed = models[:-1] + [_model(9)]
    assert detect_stalled_scan(previous, changed, "2026-10-04") == ""
    # a same-day re-run is not a stall
    assert detect_stalled_scan(previous, models, "2026-10-03") == ""


def test_health_gate_fails_when_today_matches_previous_day_and_passes_when_updated():
    models = [_model(i) for i in range(5)]
    previous = build_daily_log(None, models, [], "2026-10-08")
    stale_today = build_daily_log(previous, models, [], "2026-10-09")
    errors = scan_health_errors(stale_today, previous, "2026-10-09")
    assert any("identical to 2026-10-08" in error for error in errors)

    fresh_today = build_daily_log(previous, models + [_model(7)], [], "2026-10-09")
    assert scan_health_errors(fresh_today, previous, "2026-10-09") == []

    assert scan_health_errors(None, previous, "2026-10-09")[0].startswith("daily log for 2026-10-09 is missing")
    stale_status = build_daily_log(previous, models + [_model(7)], [], "2026-10-09", {"models": {"status": "stale", "reason": "x"}})
    assert any("'stale'" in error for error in scan_health_errors(stale_status, previous, "2026-10-09"))


def test_the_real_october_stall_would_have_failed_the_gate():
    errors = scan_health_errors(_log("2026-10-09"), _log("2026-10-08"), "2026-10-09")
    assert any("identical to 2026-10-08" in error for error in errors)
    assert scan_health_errors(_log("2026-10-10"), _log("2026-10-09"), "2026-10-10") == []


def _cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "crawler.cli", *args], cwd=ROOT, capture_output=True, text=True)


def test_cli_log_marks_unchanged_scan_stale_instead_of_ok_and_scan_health_exits_nonzero(tmp_path):
    logs = tmp_path / "daily-log"
    logs.mkdir()
    models = [_model(i) for i in range(4)]
    (tmp_path / "models.json").write_text(json.dumps(models), encoding="utf-8")
    (tmp_path / "offers.json").write_text("[]", encoding="utf-8")
    first = build_daily_log(None, models, [], "2026-10-08")
    (logs / "2026-10-08.json").write_text(json.dumps(first), encoding="utf-8")

    result = _cli("log", "--models", str(tmp_path / "models.json"), "--offers", str(tmp_path / "offers.json"),
                  "--previous", str(logs / "2026-10-08.json"), "--out", str(logs / "2026-10-09.json"), "--as-of", "2026-10-09",
                  cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    written = json.loads((logs / "2026-10-09.json").read_text(encoding="utf-8"))
    assert written["sourceHealth"]["models"]["status"] == "stale"
    assert any(event["eventType"] == "source_unavailable" for event in written["events"])

    gate = _cli("scan-health", "--dir", str(logs), "--as-of", "2026-10-09", cwd=tmp_path)
    assert gate.returncode == 1 and "scan health" in gate.stdout
    missing = _cli("scan-health", "--dir", str(logs), "--as-of", "2026-10-10", cwd=tmp_path)
    assert missing.returncode == 1 and "missing" in missing.stdout

    models.append(_model(8))
    (tmp_path / "models.json").write_text(json.dumps(models), encoding="utf-8")
    (logs / "2026-10-09.json").unlink()
    _cli("log", "--models", str(tmp_path / "models.json"), "--offers", str(tmp_path / "offers.json"),
         "--previous", str(logs / "2026-10-08.json"), "--out", str(logs / "2026-10-09.json"), "--as-of", "2026-10-09", cwd=tmp_path)
    ok = _cli("scan-health", "--dir", str(logs), "--as-of", "2026-10-09", cwd=tmp_path)
    assert ok.returncode == 0, ok.stdout


def test_daily_log_workflow_runs_the_scan_health_gate_last_and_always():
    workflow = (ROOT / ".github" / "workflows" / "daily-log.yml").read_text(encoding="utf-8")
    gate = workflow.index("python -m crawler.cli scan-health")
    assert gate > workflow.index("git push origin HEAD:dev")
    assert "if: always()" in workflow[workflow.rindex("- name:", 0, gate):gate]


# ---------------------------------------------------------------- feed + one date convention

def _feed_entries(feed: str) -> list[dict]:
    pattern = re.compile(r"<entry>\s*<title>(.*?)</title>\s*<link href=\"(.*?)\"/>\s*<id>(.*?)</id>\s*<updated>(.*?)</updated>", re.S)
    return [dict(zip(("title", "link", "id", "updated"), match)) for match in pattern.findall(feed)]


def test_feed_uses_asia_shanghai_dates_and_has_the_2026_10_10_entries():
    feed = (ROOT / "feed.xml").read_text(encoding="utf-8")
    entries = _feed_entries(feed)
    assert entries and "T00:00:00Z" not in feed
    assert all(entry["updated"].endswith("T00:00:00+08:00") for entry in entries)
    titles_today = {entry["title"] for entry in entries if entry["updated"].startswith("2026-10-10")}
    assert any("Claude 订阅附送 API 额度" in title for title in titles_today)
    assert any("Qoder" in title and "延期" in title for title in titles_today)
    assert len({entry["id"] for entry in entries}) == len(entries)
    assert len({entry["title"] for entry in entries}) == len(entries)


def test_laya_is_not_titled_as_ant_ling_anywhere_in_the_feed():
    laya = OFFERS["vercel-laya-free"]
    assert "Ling" not in laya["titleZh"] and "百灵" not in laya["titleZh"]
    assert "ling-3.1" not in json.dumps(laya.get("freeLLMTest") or {}, ensure_ascii=False).lower()
    feed = (ROOT / "feed.xml").read_text(encoding="utf-8")
    assert feed.count("<title>蚂蚁百灵 Ling-3.1-flash · 限时免费 API</title>") == 1
    laya_entry = next(entry for entry in _feed_entries(feed) if entry["link"].endswith("/offers/vercel-laya-free/"))
    assert laya_entry["title"].startswith("Laya")


def test_each_offer_is_announced_as_new_at_most_once_from_october():
    seen: dict[str, list[str]] = {}
    for log in _logs():
        if log["date"] < "2026-10-01":
            continue
        for key in ("events", "curatedEvents"):
            for event in log.get(key) or []:
                if event.get("kind") == "offer" and event.get("eventType") == "new":
                    seen.setdefault(event["id"], []).append(log["date"])
    duplicates = {offer_id: days for offer_id, days in seen.items() if len(days) > 1}
    assert duplicates == {}
    assert seen.get("stepfun-step-5-preview-free-week") == ["2026-10-09"]


def test_feed_dates_equal_the_first_daily_log_date_for_every_logged_offer():
    logs = _logs()
    first = public_listing_dates(logs)
    feed = (ROOT / "feed.xml").read_text(encoding="utf-8")
    for entry in _feed_entries(feed):
        match = re.search(r"/offers/([^/]+)/$", entry["link"])
        if not match or match.group(1) not in OFFERS:
            continue
        offer = OFFERS[match.group(1)]
        assert entry["updated"] == atom_timestamp(listing_date(offer, first)), offer["id"]
        if offer["id"] in first:
            assert entry["updated"].startswith(first[offer["id"]])
    # the audit's examples now agree between feed and /logs/
    for offer_id in ("autoclaw-glm-5-3-flash-oct-2026", "zhipu-glm-4-7-flash-free-api", "unisound-u2-flash-free-month"):
        assert first[offer_id] == "2026-10-08" == OFFERS[offer_id]["date"]


def test_render_feed_includes_curated_news_and_skips_offer_title_duplicates():
    offers = [{"id": "a", "date": "2026-10-09", "title": "A offer", "freeSummary": "s"}]
    logs = [{"date": "2026-10-10", "curatedEvents": [
        {"kind": "news", "eventType": "changed", "id": "n1", "title": "News one", "reason": "r"},
        {"kind": "model", "eventType": "new", "id": "x/a", "title": "A offer", "reason": "dup of offer"},
        {"kind": "offer", "eventType": "new", "id": "a", "title": "A offer", "reason": "listing"},
    ]}]
    entries = _feed_entries(render_feed(offers, "https://example.test", logs))
    assert sorted(entry["title"] for entry in entries) == ["A offer", "News one"]
    offer_entry = next(entry for entry in entries if entry["title"] == "A offer")
    assert offer_entry["updated"] == "2026-10-10T00:00:00+08:00"  # first logged date wins


def test_build_daily_log_does_not_reannounce_curated_offers():
    offer = {"id": "o1", "title": "O1", "status": "verified"}
    previous = build_daily_log(None, [], [], "2026-10-08")
    previous["curatedEvents"] = [{"kind": "offer", "eventType": "new", "id": "o1", "title": "O1", "asOf": "2026-10-08"}]
    log = build_daily_log(previous, [], [offer], "2026-10-09")
    assert not [event for event in log["events"] if event["id"] == "o1"]
    older = build_daily_log(build_daily_log(None, [], [], "2026-10-08"), [], [offer], "2026-10-10", None, {"o1"})
    assert not [event for event in older["events"] if event["id"] == "o1"]
    assert "o1" in announced_offer_ids([previous])


# ---------------------------------------------------------------- third-party relays

@pytest.mark.parametrize("provider", ["llm7-io", "kilo", "kilo-code"])
def test_llm7_and_kilo_are_third_party_relays(provider):
    assert is_third_party_relay({"providerId": provider})
    assert is_third_party_relay({"kind": "model", "id": f"{provider}/x", "details": {}})
    log = build_daily_log(build_daily_log(None, [], [], "2026-10-01"), [_model(1, provider)], [], "2026-10-02")
    assert log["events"][0]["details"]["sourceTier"] == THIRD_PARTY_RELAY_TIER
    assert not is_third_party_relay({"providerId": "groq"})


def test_relays_are_marked_in_data_and_ui():
    catalog = {item["id"]: item for item in json.loads((DATA / "provider-catalog.json").read_text(encoding="utf-8"))}
    for provider in ("llm7-io", "kilo", "kilo-code"):
        assert catalog[provider]["sourceTier"] == THIRD_PARTY_RELAY_TIER
    relay_events = [event for event in _log("2026-10-10")["events"] if str(event["id"]).startswith(("llm7-io/", "kilo/"))]
    assert relay_events and all(event["details"]["sourceTier"] == THIRD_PARTY_RELAY_TIER for event in relay_events)
    logs_page = (ROOT / "logs" / "index.html").read_text(encoding="utf-8")
    assert "log-third-party" in logs_page and "第三方" in logs_page
    for provider in ("kilo", "llm7-io"):
        page = (ROOT / "providers" / provider / "index.html")
        if page.is_file():
            assert "第三方聚合" in page.read_text(encoding="utf-8")


# ---------------------------------------------------------------- officially verified additions

def test_officially_verified_news_items_are_recorded_with_source_and_date():
    log = _log("2026-10-10")
    curated = {event["id"]: event for event in log.get("curatedEvents") or []}
    expected = {
        "claude-max-team-api-credits": "https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers",
        "claude-startups-program-paused": "https://claude.com/programs/startups",
        "google-ai-studio-free": "https://discuss.ai.google.dev/t/daily-usage-limits-for-models-in-ai-studio/185935",
        "google-gemini-app-free-tier-2026-10": "https://support.google.com/gemini/answer/17004136",
        "opencode/exo-free": "https://opencode.ai/docs/en/zen/",
        "opencode/longcat-2.5-preview-free": "https://opencode.ai/docs/en/zen/",
        "addyosmani-code-review-and-quality": "https://github.com/addyosmani/agent-skills",
        "mattpocock-skills-v1.3": "https://github.com/mattpocock/skills/releases/tag/v1.3.1",
    }
    for event_id, url in expected.items():
        assert event_id in curated, event_id
        assert curated[event_id]["asOf"] == "2026-10-10"
        assert curated[event_id]["details"]["sourceUrl"] == url
    assert "workbuddy" not in json.dumps(log.get("curatedEvents"), ensure_ascii=False).lower()
    assert "space bunny" not in json.dumps(log.get("curatedEvents"), ensure_ascii=False).lower()
    assert "已暂停" in curated["claude-startups-program-paused"]["title"]
    assert "claude-startups" not in " ".join(OFFERS)  # paused: news only, not a claimable offer


def test_claude_credits_offer_is_labelled_as_subscriber_bonus_not_free_tier():
    offer = OFFERS["claude-max-team-api-credits"]
    assert offer["date"] == "2026-10-10" and offer["status"] == "verified"
    assert "不是免费档" in offer["notes"] or "NOT A FREE TIER" in offer["kicker"]
    assert "Claude Code" in offer["freeSummary"]


def test_zen_and_skill_additions_are_in_the_catalog():
    zen = OFFERS["opencode-zen-free"]
    models = {item["model"] for item in zen.get("freeModels") or []}
    assert {"exo-free", "longcat-2.5-preview-free"} <= models
    assert "longcat-2.5-preview-free" in json.dumps(OFFERS["longcat-2-0"], ensure_ascii=False)
    skills = {item["id"]: item for item in json.loads((DATA / "skills.json").read_text(encoding="utf-8"))}
    addy = skills["addyosmani-code-review-and-quality"]
    assert addy["githubUrl"].startswith("https://github.com/addyosmani/agent-skills/")
    assert (DATA / addy["contentPath"]).is_file()
