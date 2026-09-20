import json
from pathlib import Path

from crawler.schema import validate_offers
from scripts.build_seo_pages import build_site

ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"


def test_manual_offers_added_after_policy_date_require_freellm_test():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))
    errors = validate_offers(offers)
    assert errors == []
    governed = [
        offer for offer in offers
        if offer.get("checkedBy") == "manual" and str(offer.get("date") or "") >= "2026-09-20"
    ]
    assert governed
    for offer in governed:
        test = offer.get("freeLLMTest")
        assert isinstance(test, dict), offer["id"]
        assert test["testedAt"]
        assert test["task"]
        assert test["method"]
        assert test["result"]
        assert test["limitations"]
        assert test["evidence"]


def test_codearts_test_does_not_claim_signed_in_usage_without_evidence():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))
    offer = next(item for item in offers if item["id"] == "huawei-codearts-daily-token")
    test = offer["freeLLMTest"]
    assert test["testLevel"] == "preflight"
    assert test["status"] == "partial"
    assert test["actualUsageVerified"] is False
    assert "Token 实际到账" in test["result"]
    assert "不标记“实测好用”" in test["limitations"]


def test_offer_and_daily_log_render_freellm_test_explanation(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    offer_page = (tmp_path / "offers" / "huawei-codearts-daily-token" / "index.html").read_text(encoding="utf-8")
    log_page = (tmp_path / "logs" / "index.html").read_text(encoding="utf-8")
    for page in (offer_page, log_page):
        assert "FreeLLM 自测" in page
        assert "预检通过" in page
        assert "登录态实测待补" in page
        assert "真实登录使用" in page
        assert "未验证 / 限制" in page
    assert "△ FreeLLM 预检" in offer_page
    assert "✓ FreeLLM 实测" not in offer_page
