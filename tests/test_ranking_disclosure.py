import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_about_page_discloses_configured_ranking_weights_and_neutral_behavior():
    config = json.loads((ROOT / "data" / "ranking-config.json").read_text(encoding="utf-8"))
    behavior = json.loads((ROOT / "data" / "ranking-behavior.json").read_text(encoding="utf-8"))
    page = (ROOT / "about" / "index.html").read_text(encoding="utf-8")
    neutral_score = config["behavior"]["neutralScore"]

    assert 'id="ranking-methodology"' in page
    for factor, weight in config["weights"].items():
        assert re.search(
            rf'data-ranking-factor="{re.escape(factor)}"\s+data-ranking-weight="{weight:.2f}"',
            page,
        ), f"about page must publish {factor} weight {weight:.2f}"
    assert sum(config["weights"].values()) == 1.0
    assert "availability (40%)" in page
    assert "quota (30%)" in page
    assert "access convenience (20%)" in page
    assert "verification recency (10%)" in page
    assert "per-offer value" in page and "provider reference" in page
    assert f"neutral score of {neutral_score}" in page
    assert "No manual boosts or deductions are configured" in page
    assert "no paid placement" in page.lower()
    assert "placement is not sold or commercially weighted" in page

    if not behavior.get("items"):
        assert "missing item-level aggregate data" in page
