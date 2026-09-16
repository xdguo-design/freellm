import json

from crawler.change_log import build_daily_log, merge_daily_log
from crawler.cli import main as cli_main


def model(model_id="alpha/model-x", provider="Alpha", model="Model X", **extra):
    record = {
        "id": model_id,
        "providerId": model_id.split("/", 1)[0],
        "provider": provider,
        "model": model,
        "sourceUrl": f"https://freellm.net/models/{model_id}",
        "status": "online",
        "context": "128K",
        "modality": ["text", "vision"],
        "rateLimit": "30 RPM",
    }
    record.update(extra)
    return record


def offer(offer_id="alpha", **extra):
    record = {
        "id": offer_id,
        "title": "Alpha free API",
        "provider": "Alpha",
        "productType": "api",
        "freeMechanism": "monthly_quota",
        "quota": "100 requests/day",
        "validity": "Monthly",
        "access": "Global",
        "register": "https://alpha.example/register",
        "sourceUrls": ["https://alpha.example/pricing"],
        "status": "verified",
        "evidence": "Official pricing documents a free tier.",
    }
    record.update(extra)
    return record


def log_with(models=None, offers=None, baseline=False):
    return {
        "baseline": baseline,
        "observed": {"models": models or [], "offers": offers or []},
    }


def test_first_run_establishes_baseline_without_calling_every_existing_record_new():
    result = build_daily_log(
        None,
        [model()],
        [offer()],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    assert result["baseline"] is True
    assert result["events"] == []
    assert result["observed"]["models"] == [{
        "id": "alpha/model-x",
        "providerId": "alpha",
        "provider": "Alpha",
        "model": "Model X",
        "sourceUrl": "https://freellm.net/models/alpha/model-x",
        "status": "online",
    }]
    assert result["known"]["models"] == []


def test_new_records_keep_detailed_model_and_offer_fields():
    previous = log_with([model("alpha/old", model="Old Model")], [offer("old")])
    result = build_daily_log(
        previous,
        [model("alpha/new", model="New Model"), model("alpha/old", model="Old Model")],
        [offer(), offer("old")],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    events = {(item["kind"], item["eventType"]): item for item in result["events"]}
    new_model = events[("model", "new")]
    new_offer = events[("offer", "new")]
    assert new_model["details"]["context"] == "128K"
    assert new_model["details"]["sourceUrl"].endswith("alpha/new")
    assert new_offer["details"]["quota"] == "100 requests/day"
    assert new_offer["details"]["sourceUrls"] == ["https://alpha.example/pricing"]
    assert new_offer["details"]["evidence"]


def test_new_offer_keeps_registration_documentation_for_daily_log():
    previous = log_with([model()], [offer("old")])
    current = offer(
        "manus-free-agent",
        register="https://manus.im/login?type=signUp",
        registrationSteps=["打开注册入口", "选择登录方式", "进入免费计划"],
        links=[["官方定价", "https://manus.im/pricing"]],
        usageGuide={"docsUrl": "https://manus.im/docs"},
    )
    result = build_daily_log(
        previous,
        [model()],
        [offer("old"), current],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    event = next(item for item in result["events"] if item["id"] == "manus-free-agent")
    assert event["details"]["registrationSteps"] == ["打开注册入口", "选择登录方式", "进入免费计划"]
    assert event["details"]["links"] == [["官方定价", "https://manus.im/pricing"]]
    assert event["details"]["usageGuide"]["docsUrl"] == "https://manus.im/docs"


def test_missing_records_are_not_marked_offline_when_model_source_failed():
    previous = log_with([model()], [offer()])
    result = build_daily_log(
        previous,
        [],
        [offer()],
        "2026-09-10",
        {"models": {"status": "failed", "reason": "timeout"}, "offers": {"status": "ok"}},
    )

    assert not any(event["eventType"] == "offline" for event in result["events"])
    assert any(
        event["kind"] == "source" and event["eventType"] == "source_unavailable"
        for event in result["events"]
    )


def test_offline_and_recovered_events_use_state_transitions():
    previous = log_with([model()], [offer("gone")])
    offline = build_daily_log(
        previous,
        [],
        [],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )
    assert {(event["kind"], event["eventType"]) for event in offline["events"]} == {
        ("model", "offline"),
        ("offer", "offline"),
    }

    recovered = build_daily_log(
        offline,
        [model()],
        [offer("gone")],
        "2026-09-11",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )
    assert {(event["kind"], event["eventType"]) for event in recovered["events"]} == {
        ("model", "recovered"),
        ("offer", "recovered"),
    }


def test_same_model_from_new_provider_is_logged_as_new_route():
    previous = log_with([model("alpha/model-x")])
    result = build_daily_log(
        previous,
        [model("alpha/model-x"), model("beta/model-x", provider="Beta")],
        [],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    routes = [event for event in result["events"] if event["eventType"] == "new_route"]
    assert len(routes) == 1
    assert routes[0]["details"]["provider"] == "Beta"


def test_failed_initial_scan_does_not_make_next_successful_scan_report_everything_new():
    failed_baseline = build_daily_log(
        None,
        [],
        [],
        "2026-09-10",
        {"models": {"status": "failed"}, "offers": {"status": "ok"}},
    )

    recovered_scan = build_daily_log(
        failed_baseline,
        [model()],
        [offer()],
        "2026-09-11",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    assert not any(event["kind"] == "model" and event["eventType"] == "new" for event in recovered_scan["events"])


def test_log_cli_reads_previous_log_and_writes_date_partitioned_json(tmp_path):
    models_path = tmp_path / "models.json"
    offers_path = tmp_path / "offers.json"
    previous_path = tmp_path / "2026-09-09.json"
    output_path = tmp_path / "2026-09-10.json"
    models_path.write_text(json.dumps([model()]), encoding="utf-8")
    offers_path.write_text(json.dumps([offer()]), encoding="utf-8")
    previous_path.write_text(json.dumps(log_with([model("alpha/old")], [offer("old")])), encoding="utf-8")

    exit_code = cli_main([
        "log",
        "--models", str(models_path),
        "--offers", str(offers_path),
        "--previous", str(previous_path),
        "--out", str(output_path),
        "--as-of", "2026-09-10",
    ])

    assert exit_code == 0
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["date"] == "2026-09-10"
    assert {event["eventType"] for event in written["events"]} == {"new", "new_route", "offline"}


def test_same_day_merge_unions_events_from_both_runs_without_duplicates():
    previous = log_with([model("alpha/old", model="Old Model")], [offer("old")])
    morning = build_daily_log(
        previous,
        [model("alpha/old", model="Old Model"), model("alpha/morning", model="Morning Model")],
        [offer("old")],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )
    evening = build_daily_log(
        previous,
        [
            model("alpha/old", model="Old Model"),
            model("alpha/morning", model="Morning Model"),
            model("alpha/evening", model="Evening Model"),
        ],
        [offer("old")],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    merged = merge_daily_log(morning, evening)

    new_ids = [event["id"] for event in merged["events"] if event["eventType"] == "new"]
    assert sorted(new_ids) == ["alpha/evening", "alpha/morning"]
    assert merged["date"] == "2026-09-10"
    observed_ids = {item["id"] for item in merged["observed"]["models"]}
    assert observed_ids == {"alpha/old", "alpha/morning", "alpha/evening"}


def test_same_day_merge_prefers_latest_events_and_keeps_curated_entries():
    previous = log_with(
        [model(), model("alpha/flip", model="Flip Model"), model("alpha/morning-only", model="Morning Only")],
        [offer()],
    )
    morning = build_daily_log(
        previous,
        [model()],
        [offer()],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )
    morning["curatedEvents"] = [{
        "kind": "offer",
        "eventType": "new",
        "id": "hand-curated",
        "title": "人工确认新增",
        "asOf": "2026-09-10",
        "details": {},
    }]
    evening = build_daily_log(
        previous,
        [model(), model("alpha/flip", model="Flip Model")],
        [offer()],
        "2026-09-10",
        {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    )

    merged = merge_daily_log(morning, evening)

    assert [event["id"] for event in merged["curatedEvents"]] == ["hand-curated"]
    # 两次运行都报告了同样的 offline 事件，合并后按 (kind, eventType, id) 去重。
    offline_ids = [event["id"] for event in merged["events"] if event["eventType"] == "offline"]
    assert sorted(offline_ids) == ["alpha/flip", "alpha/morning-only"]
    # 盘中恢复的项目不再保留早上误报的 offline 之外的事件，但仍留在当日快照里。
    observed_ids = {item["id"] for item in merged["observed"]["models"]}
    known_ids = {item["id"] for item in merged["known"]["models"]}
    assert observed_ids == {"alpha/model-x", "alpha/flip"}
    assert "alpha/morning-only" in known_ids
    assert "alpha/morning-only" not in observed_ids


def test_merge_rejects_logs_from_different_dates():
    morning = log_with([model()])
    morning["date"] = "2026-09-10"
    evening = log_with([model()])
    evening["date"] = "2026-09-11"

    try:
        merge_daily_log(morning, evening)
    except ValueError:
        pass
    else:
        raise AssertionError("merge_daily_log should reject different dates")


def test_log_cli_merge_accumulates_same_day_reruns(tmp_path):
    models_path = tmp_path / "models.json"
    offers_path = tmp_path / "offers.json"
    previous_path = tmp_path / "2026-09-09.json"
    output_path = tmp_path / "2026-09-10.json"
    models_path.write_text(json.dumps([model("alpha/model-x", model="Model X")]), encoding="utf-8")
    offers_path.write_text(json.dumps([offer()]), encoding="utf-8")
    previous_path.write_text(
        json.dumps(log_with([model("alpha/old", model="Old Model")], [offer("old")])),
        encoding="utf-8",
    )

    common = [
        "log",
        "--models", str(models_path),
        "--offers", str(offers_path),
        "--previous", str(previous_path),
        "--out", str(output_path),
        "--as-of", "2026-09-10",
    ]
    assert cli_main(common) == 0
    models_path.write_text(
        json.dumps([model("alpha/model-x", model="Model X"), model("alpha/second", model="Second Model")]),
        encoding="utf-8",
    )
    assert cli_main(common + ["--merge"]) == 0

    written = json.loads(output_path.read_text(encoding="utf-8"))
    new_ids = sorted(
        event["id"] for event in written["events"]
        if event["eventType"] == "new" and event["kind"] == "model"
    )
    assert new_ids == ["alpha/model-x", "alpha/second"]
