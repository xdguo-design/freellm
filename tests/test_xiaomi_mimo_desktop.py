import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_xiaomi_mimo_desktop_is_curated_as_an_invitation_beta_offer():
    offers = json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8"))
    offer = next(item for item in offers if item["id"] == "xiaomi-mimo-desktop")

    assert offer["productType"] == "desktop_ai_app"
    assert offer["freeMechanism"] == "limited_time_free"
    assert offer["status"] == "verified"
    assert offer["register"] == "https://mimo.xiaomimimo.com/desktop/invite/"
    assert "https://mimo-ai.xiaomimimo.com/desktop/invite/" in offer["sourceUrls"]
    assert "MiMo-X-Pro-Preview" in offer["model"]
    assert "MiMo-X-Flash-Preview" in offer["model"]
    assert "invitation" in offer["access"].lower()
    assert "limited" in offer["quota"].lower()
    assert any("mimo-desktop" in url for url in offer["sourceUrls"])
    assert offer["usageGuide"]["steps"]
    assert offer["capabilities"] == ["desktop_app"]
