"""Regression tests for the VibeX browser product (not a free external API)."""
import json
from pathlib import Path

from crawler.schema import validate_offers, validate_operation_guides

ROOT = Path(__file__).resolve().parents[1]


def test_vibex_public_offer_has_safe_quota_claims():
    offers = json.loads((ROOT / "data/offers.json").read_text(encoding="utf-8"))
    item = next(o for o in offers if o["id"] == "vibex-runninghub-daily")
    assert validate_offers(offers) == []
    assert item["providerId"] == "runninghub"
    assert item["productType"] == "coding_plan"
    assert item["capabilities"] == ["coding_plan"]
    assert item["status"] == "needs_review"
    assert item["freeMechanism"] == "not_confirmed"
    assert "宣传" in item["freeSummary"]
    assert "待" in item["freeSummary"]
    assert item["quota"].find("UNKNOWN") >= 0
    assert "api" not in item["type"]


def test_vibex_provider_and_operation_guide_are_linked():
    providers = json.loads((ROOT / "data/providers.json").read_text(encoding="utf-8"))
    provider = next(p for p in providers if p["id"] == "runninghub")
    assert "vibex.runninghub.cn" in provider["allowedDomains"]
    ops = json.loads((ROOT / "data/operations/runninghub.json").read_text(encoding="utf-8"))
    assert ops["offerIds"] == ["vibex-runninghub-daily"]
    assert validate_operation_guides(ops) == []
