import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_mimo_v26_flash_is_in_curated_and_published_model_catalogs():
    expected = {
        "xiaomi-mimo/mimo-v2-6-flash": ("mimo-v2.6-flash", "1000000", "131072"),
        "opencode/mimo-v2-6-flash-free": ("mimo-v2.6-flash-free", "1000000", "131072"),
    }
    for path in ("data/models-curated.json", "data/models.json"):
        rows = {row["id"]: row for row in _load(path)}
        for model_id, (canonical, context, max_output) in expected.items():
            assert model_id in rows
            row = rows[model_id]
            assert row["canonicalModelId"] == canonical
            assert row["context"] == context
            assert row["maxOutput"] == max_output
            assert {"text", "image", "video", "audio"}.issubset(set(row["modality"]))
            assert row["lastVerifiedAt"] == "2026-09-23"


def test_opencode_offer_names_the_v26_free_variant_and_does_not_call_xiaomi_api_free():
    offer = next(row for row in _load("data/offers.json") if row["id"] == "opencode-zen-free")
    assert "MiMo-V2.6-Flash Free" in offer["model"]
    assert "mimo-v2.6-flash-free" in offer["usageGuide"]["examples"]["curl"]
    assert "https://opencode.ai/docs/en/zen/" in offer["sourceUrls"]
    assert offer["endpointCheck"]["verdict"] == "OK"
    assert "Xiaomi" in offer["why"]
    assert "paid official API" in offer["why"]


def test_mimo_access_records_keep_paid_official_and_free_hosted_routes_separate():
    rows = {row["modelId"]: row for row in _load("data/model-access.json")}
    official = rows["xiaomi-mimo/mimo-v2-6-flash"]
    free = rows["opencode/mimo-v2-6-flash-free"]
    assert official["registrationProfileId"] == "xiaomi-mimo-api"
    assert free["registrationProfileId"] == "opencode-api"
    assert official["verificationStatus"] == "verified"
    assert free["verificationStatus"] == "verified"


def test_wechat_article_states_test_boundary_and_free_route():
    page = (ROOT / "docs/wechat/mimo-v2-6-flash.html").read_text(encoding="utf-8")
    assert "OpenCode Zen" in page
    assert "mimo-v2.6-flash-free" in page
    assert "小米官方 API 不是免费 API" in page
    assert "端到端推理请求仍需凭据" in page
