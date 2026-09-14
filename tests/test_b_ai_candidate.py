import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def test_b_ai_is_registered_for_bounded_discovery():
    providers = _read("providers.json")
    provider = next(item for item in providers if item["id"] == "b-ai")
    assert provider["allowedDomains"] == ["b.ai"]
    assert "https://b.ai/" in provider["discoveryUrls"]


def test_b_ai_candidate_is_review_only_and_not_a_public_offer():
    candidates = _read("candidates.json")
    candidate = next(item for item in candidates if item.get("providerId") == "b-ai")
    assert candidate["status"] == "needs_review"
    assert candidate["sourceKind"] == "official"
    assert candidate["officiality"] == "official"
    assert set(["minimax-m3", "hunyuan-hy3", "glm-5.3-flash"]).issubset(
        set(candidate["mentionedModels"])
    )
    assert "300,000" in candidate["evidence"]

    offers = _read("offers.json")
    assert not any(item["id"] == "b-ai-free" for item in offers)
