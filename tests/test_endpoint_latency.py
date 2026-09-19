"""The measured API-gateway latency layer: probe helpers, data file, and rendering.

Every number on the site has to trace back to a real probe run, so these tests
cover both ends: the scripts that write the data, and the renderers that must
refuse to invent a latency when a probe never got an HTTP answer.
"""

import json
import sys
from pathlib import Path

import pytest

from scripts.apply_endpoint_check import ALIVE_VERDICTS, pick_probe
from scripts.build_seo_pages import _load_endpoint_latency, _model_catalog_row, render_offer_page
from scripts.build_static import render_offer_flags
from scripts.probe_endpoint_latency import candidate_urls, rank


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
MODELS_PATH = ROOT / "data" / "models.json"
LATENCY_PATH = ROOT / "data" / "endpoint-latency.json"


def load_offers() -> list[dict]:
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# probe helpers
# --------------------------------------------------------------------------- #
def test_candidate_urls_cover_documented_forms_without_duplicates():
    model = {
        "providerId": "demo",
        "accessEndpoint": "https://api.demo.example",
        "sourceEndpoint": "https://llm.demo.example/v1/models",
    }
    urls = candidate_urls(model)
    assert urls[0] == "https://api.demo.example"
    assert "https://api.demo.example/v1/models" in urls
    assert "https://llm.demo.example/v1/models" in urls
    assert len(urls) == len(set(urls))


def test_rank_prefers_a_json_api_over_an_html_landing_page():
    api = {"status": 200, "json": True, "ms": 900}
    needs_key = {"status": 401, "json": True, "ms": 100}
    html_page = {"status": 200, "json": False, "ms": 10}
    dead = {"status": None, "json": False, "ms": None}
    assert rank(api) < rank(needs_key) < rank(html_page) < rank(dead)


def test_pick_probe_prefers_the_documented_call_over_the_model_listing():
    probes = [
        {"name": "models", "status": 200, "ms": 100},
        {"name": "chat", "status": 401, "ms": 250},
    ]
    assert pick_probe(probes)["name"] == "chat"


def test_pick_probe_skips_probes_that_never_answered():
    assert pick_probe([{"name": "chat", "status": None, "ms": 9000}]) is None
    assert pick_probe([{"name": "chat", "status": 401, "ms": None}]) is None
    assert pick_probe([]) is None
    fallback = pick_probe([{"name": "official-site", "status": 200, "ms": 120}])
    assert fallback["name"] == "official-site"


# --------------------------------------------------------------------------- #
# data file
# --------------------------------------------------------------------------- #
def test_endpoint_latency_file_is_well_formed_and_provider_complete():
    payload = json.loads(LATENCY_PATH.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert payload["checkedAt"]
    assert payload["method"] and payload["vantage"]
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    catalog_providers = {str(model.get("providerId") or "") for model in models}
    measured = {str(entry["providerId"]) for entry in payload["providers"]}
    assert measured == catalog_providers
    for entry in payload["providers"]:
        ms = entry["ms"]
        # A latency is either a real measurement or absent - never a guess.
        assert ms is None or (isinstance(ms, int) and not isinstance(ms, bool) and ms > 0)
        if ms is not None:
            assert entry["endpoint"].startswith("http")
            assert entry["attempts"], "a measured latency keeps its samples"
            assert entry["checkedAt"]


def test_model_rows_render_the_measured_latency_and_stay_honest_without_one():
    latencies = {"demo": {"checkedAt": "2026-09-19", "endpoint": "https://api.demo.example/v1/models", "ms": 412}}
    model = {"id": "demo/model", "providerId": "demo", "provider": "Demo", "model": "model"}
    measured = _model_catalog_row(model, {}, 1, latencies, {"vantage": "本机大陆网络直连"})
    assert 'data-ms="412"' in measured
    assert '<span class="latency-value">412ms</span>' in measured
    assert "3 次成功请求的中位数" in measured

    unknown = _model_catalog_row({**model, "providerId": "nope"}, {}, 1, latencies, {})
    assert 'data-ms=""' in unknown
    assert "latency-unknown" in unknown
    assert "ms</span>" not in unknown


def test_model_catalog_loader_rejects_a_broken_latency_file(tmp_path, monkeypatch):
    (tmp_path / "endpoint-latency.json").write_text('{"providers": "nope"}', encoding="utf-8")
    monkeypatch.setattr("scripts.build_seo_pages.ACCESS_DATA_DIR", tmp_path)
    with pytest.raises(SystemExit):
        _load_endpoint_latency()


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _offer(offer_id: str) -> dict:
    return next(offer for offer in load_offers() if offer["id"] == offer_id)


def test_offer_page_shows_the_measured_call_latency():
    offer = _offer("groq-free")
    ms = offer["endpointCheck"]["ms"]
    page = render_offer_page(offer, [offer], "https://freellm.top")
    assert f"接口已验证 · {ms}ms" in page
    assert f"调用耗时 {ms}ms" in page
    assert offer["usageGuide"]["endpoint"] in page


def test_offer_page_omits_the_latency_when_the_endpoint_was_not_measured():
    offer = _offer("mistral-free-mode")
    assert "ms" not in offer["endpointCheck"]
    page = render_offer_page(offer, [offer], "https://freellm.top")
    assert "✓ 接口已验证" in page
    assert "调用耗时" not in page


def test_homepage_static_flags_carry_the_latency():
    offer = _offer("groq-free")
    assert f"✓ 接口已验证 · {offer['endpointCheck']['ms']}ms" in render_offer_flags(offer)


# --------------------------------------------------------------------------- #
# applying a probe report
# --------------------------------------------------------------------------- #
def _report(offer_id: str, probes: list[dict]) -> dict:
    return {
        "generatedAt": "2026-09-19T08:00:00",
        "summary": {},
        "results": [{"id": offer_id, "probes": probes}],
    }


def _run_apply(tmp_path: Path, monkeypatch, offers: list[dict], report: dict) -> dict:
    data_path = tmp_path / "offers.json"
    data_path.write_text(json.dumps(offers, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["apply_endpoint_check", "--data", str(data_path), "--report", str(report_path)],
    )
    import scripts.apply_endpoint_check as apply_module

    assert apply_module.main() == 0
    return json.loads(data_path.read_text(encoding="utf-8"))[0]


def test_apply_endpoint_check_adds_the_latency_and_keeps_the_hand_written_note(tmp_path, monkeypatch):
    offer = {
        "id": "demo",
        "endpointCheck": {"checkedAt": "2026-09-18", "verdict": "NEEDS_KEY", "note": "接口存活，鉴权正常，需注册 API Key"},
    }
    updated = _run_apply(
        tmp_path,
        monkeypatch,
        [offer],
        _report(
            "demo",
            [
                {"name": "models", "status": 200, "verdict": "OK", "ms": 90},
                {"name": "chat", "status": 401, "verdict": "NEEDS_KEY", "ms": 412},
            ],
        ),
    )
    check = updated["endpointCheck"]
    assert check["ms"] == 412
    assert check["checkedAt"] == "2026-09-19"
    assert check["note"] == "接口存活，鉴权正常，需注册 API Key"
    assert check["verdict"] == "NEEDS_KEY"


def test_apply_endpoint_check_never_invents_a_latency(tmp_path, monkeypatch):
    offer = {
        "id": "demo",
        "endpointCheck": {"checkedAt": "2026-09-18", "verdict": "NEEDS_KEY", "note": "接口存活"},
    }
    updated = _run_apply(
        tmp_path,
        monkeypatch,
        [offer],
        _report("demo", [{"name": "chat", "status": None, "verdict": "NETWORK_ERROR", "ms": 10240, "error": "URLError"}]),
    )
    assert updated["endpointCheck"] == offer["endpointCheck"]


def test_alive_verdicts_cover_every_stored_verdict_that_carries_a_latency():
    stored = {
        str(offer.get("endpointCheck", {}).get("verdict"))
        for offer in load_offers()
        if offer.get("endpointCheck", {}).get("ms")
    }
    assert stored <= ALIVE_VERDICTS
