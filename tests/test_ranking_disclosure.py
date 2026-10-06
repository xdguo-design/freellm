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
    assert "access convenience (20%) and verification recency (10%)" in page
    assert "per-offer value" in page and "provider reference" in page
    assert "manual boosts or deductions" in page
    cards = {
        factor: markup
        for factor, markup in re.findall(
            r'<article class="about-card" data-ranking-factor="([^"]+)"[^>]*>(.*?)</article>',
            page,
            flags=re.DOTALL,
        )
    }
    free_value_heading = re.search(r"<h3>(.*?)</h3>", cards["freeValue"], re.DOTALL).group(1)
    free_value_copy = re.search(r"<p>(.*?)</p>", cards["freeValue"], re.DOTALL).group(1)
    assert "Free value · 30%" in free_value_heading
    assert "Combines configured" not in free_value_heading
    assert "40%" in free_value_copy and "核验时效" in free_value_copy
    assert "Convenience reflects" in free_value_copy and "核验时效" in free_value_copy

    popularity_heading = re.search(r"<h3>(.*?)</h3>", cards["popularity"], re.DOTALL).group(1)
    popularity_copy = re.search(r"<p>(.*?)</p>", cards["popularity"], re.DOTALL).group(1)
    assert "Popularity reference · 20%" in popularity_heading
    assert "per-offer value" not in popularity_heading
    assert "单条资源" in popularity_copy and "厂商" in popularity_copy and "默认分" in popularity_copy
    assert "per-offer value" in popularity_copy and "provider reference" in popularity_copy
    assert "人工加减分" in page and "均未配置" in page

    if not behavior.get("items"):
        assert f"中性分 {neutral_score}" in page
        assert f"neutral score of {neutral_score}" in page
        assert "不基于个人浏览历史进行个性化排序" in page
    else:
        assert "没有条目级汇总行为数据" not in page
        assert "There is currently no item-level aggregate behavior data" not in page

    assert "不进行主观评分或排名" not in page
    assert "所有资源按照分类和更新时间展示" not in page
    assert "No paid placement" in page
    assert "No commercial ranking" not in page
