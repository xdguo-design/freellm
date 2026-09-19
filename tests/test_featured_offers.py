"""「加精」标签：判定规则、数据一致性，以及三个渲染出口。

加精是本站唯一一个由脚本算出来的「推荐」标记，所以测试重点不是样式，而是
**它不能说谎**：速度必须等于实测值，额度必须有官方文本可依，规则改动必须被看见。
"""

import json
import re
import sys
from pathlib import Path

import pytest

from crawler.schema import validate_offers
from scripts.build_seo_pages import render_category_page, render_offer_page
from scripts.build_static import render_offer_flags
from scripts.mark_featured_offers import (
    EXCLUDED_MECHANISMS,
    LONG_TERM_MECHANISMS,
    QUOTA_HIGH_CREDITS,
    QUOTA_HIGH_REQUESTS,
    QUOTA_HIGH_TOKENS,
    SPEED_FAST_MS,
    SPEED_VERY_FAST_MS,
    apply,
    compute_featured,
    featured_reason,
    has_free_unit_price,
    large_amounts,
    quota_amounts,
    quota_tier,
    speed_tier,
)


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
HOMEPAGE_PATH = ROOT / "design" / "free-china-ai-index.html"


def load_offers() -> list[dict]:
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


def offer(offer_id: str) -> dict:
    return next(entry for entry in load_offers() if entry["id"] == offer_id)


# --------------------------------------------------------------------------- #
# 规则本身
# --------------------------------------------------------------------------- #
def test_thresholds_are_the_documented_ones():
    """门槛就是写在脚本里的那两个数，改动必须是有意的。"""
    assert (SPEED_VERY_FAST_MS, SPEED_FAST_MS) == (200, 400)
    assert (QUOTA_HIGH_TOKENS, QUOTA_HIGH_REQUESTS, QUOTA_HIGH_CREDITS) == (1_000_000, 100_000, 50_000)
    assert LONG_TERM_MECHANISMS == {"permanent"}
    assert EXCLUDED_MECHANISMS == {"first_month_promo", "not_confirmed", "open_weights"}


def test_speed_tier_reads_the_measurement_and_never_guesses():
    assert speed_tier({"endpointCheck": {"ms": 199}}) == ("very_fast", 199)
    assert speed_tier({"endpointCheck": {"ms": 200}}) == ("very_fast", 200)
    assert speed_tier({"endpointCheck": {"ms": 201}}) == ("fast", 201)
    assert speed_tier({"endpointCheck": {"ms": 400}}) == ("fast", 400)
    assert speed_tier({"endpointCheck": {"ms": 401}}) == ("unknown", 401)
    # 没有实测值就是不参评，而不是拿别的数字顶上。
    assert speed_tier({"endpointCheck": {"verdict": "OK"}}) == ("unknown", None)
    assert speed_tier({}) == ("unknown", None)
    assert speed_tier({"endpointCheck": {"ms": True}}) == ("unknown", None)
    assert speed_tier({"endpointCheck": {"ms": None}}) == ("unknown", None)


def test_quota_amounts_read_chinese_scales_and_ignore_denominators():
    assert quota_amounts({"quota": "注册赠 1 亿 Token"}) == [("tokens", 100_000_000.0)]
    assert quota_amounts({"quota": "60,000 积分 / 5 小时"}) == [("credits", 60_000.0)]
    assert quota_amounts({"quota": "1,500,000 tokens/minute"}) == [("tokens", 1_500_000.0)]
    assert quota_amounts({"quota": "通常 100 万 tokens"}) == [("tokens", 1_000_000.0)]
    # "2/次" 是单次扣费，不是额度。
    assert quota_amounts({"quota": "旗舰模型 2/次"}) == []
    assert quota_amounts({"quota": "Fetch 1,000/day"}) == []


def test_large_amounts_apply_the_documented_thresholds():
    assert large_amounts({"quota": "1,000,000 tokens"}) == [("tokens", 1_000_000.0)]
    assert large_amounts({"quota": "999,999 tokens"}) == []
    assert large_amounts({"quota": "100,000 requests / month"}) == [("requests", 100_000.0)]
    assert large_amounts({"quota": "50,000 积分"}) == [("credits", 50_000.0)]
    assert large_amounts({"quota": "500 credits / month"}) == []


def test_quota_tier_skips_promotions_and_unconfirmed_offers():
    for mechanism in EXCLUDED_MECHANISMS:
        assert quota_tier({"freeMechanism": mechanism, "quota": "1,000,000 tokens"}) == "none"
    # 首月优惠价要付钱，不是免费额度。
    assert quota_tier({"freeMechanism": "first_month_promo", "quota": "Pro 140,000 credits"}) == "none"
    # 一次性试用但额度很大，算「较高」。
    assert quota_tier({"freeMechanism": "trial", "quota": "1,000,000 tokens"}) == "high"
    # 长期免费且官方标价 ¥0，是最强证据。
    assert quota_tier({"freeMechanism": "permanent", "quota": "¥0 unit price for the listed models"}) == "very_high"
    # 长期免费但没有任何可读额度，不参评。
    assert quota_tier({"freeMechanism": "permanent", "freeSummary": "CNB 平台内置 CodeBuddy Web 能力"}) == "none"


def test_free_unit_price_detection_does_not_fire_on_paid_unit_prices():
    assert has_free_unit_price({"quota": "¥0 unit price for the listed models"})
    assert has_free_unit_price({"quota": "输入/输出/缓存命中均 $0/M tokens"})
    assert not has_free_unit_price({"quota": "Agent $0.016 / step; Browser $0.002 / minute"})
    assert not has_free_unit_price({"quota": "$20 signup credits + $10 credits / month"})


def test_compute_featured_keeps_the_original_since_date():
    base = {"freeMechanism": "permanent", "quota": "1,000,000 tokens", "endpointCheck": {"ms": 150}}
    first = compute_featured(base, "2026-09-19")
    assert first["since"] == "2026-09-19"
    again = compute_featured({**base, "featured": first}, "2026-12-31")
    assert again["since"] == "2026-09-19", "重跑脚本不能让标签生效日期漂移"
    assert compute_featured({"freeMechanism": "permanent", "quota": "1,000,000 tokens"}, "2026-09-19") is None


def test_featured_reason_quotes_the_measurement_and_the_quota():
    reason_zh, reason_en = featured_reason(
        {"freeMechanism": "limited_time_free", "quota": "1,500,000 tokens/minute"}, 243, "high"
    )
    assert "243ms" in reason_zh and "1,500,000" in reason_zh
    assert "243 ms" in reason_en
    # 长期免费的条目理由里说「长期免费」，不再堆数字。
    permanent_zh, _ = featured_reason({"freeMechanism": "permanent", "quota": "500 credits / month"}, 222, "high")
    assert "长期免费" in permanent_zh


# --------------------------------------------------------------------------- #
# 真实数据必须满足规则
# --------------------------------------------------------------------------- #
def test_every_featured_offer_satisfies_the_rule():
    offers = load_offers()
    featured = [entry for entry in offers if isinstance(entry.get("featured"), dict)]
    assert featured, "加精标签不该是空的"
    for entry in featured:
        block = entry["featured"]
        speed, ms = speed_tier(entry)
        assert speed in {"very_fast", "fast"}, entry["id"]
        assert block["speedMs"] == ms, f"{entry['id']} 引用的速度必须等于实测值"
        assert block["speedTier"] == speed
        assert block["quotaTier"] == quota_tier(entry)
        assert block["quotaTier"] in {"very_high", "high"}
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", block["since"])
        assert str(ms) in block["reason"]


def test_fast_offers_without_quota_evidence_stay_out():
    """速度快但额度说不清的条目不能入选——这就是「额度高」这一半的分量。"""
    offers = {entry["id"]: entry for entry in load_offers()}
    for offer_id in ("glm", "deepseek", "xiaomi-mimo-desktop", "stepfun-limited-time-free", "cnb-ai"):
        entry = offers[offer_id]
        assert speed_tier(entry)[0] in {"very_fast", "fast"}, offer_id
        assert quota_tier(entry) == "none", offer_id
        assert "featured" not in entry, offer_id


def test_offers_data_is_current_against_the_rule():
    """数据文件必须已经是脚本的输出，不能靠手工维护。"""
    offers, granted, revoked = apply(load_offers(), "2026-09-19")
    assert (granted, revoked) == ([], []), f"data/offers.json 已过期：+{granted} -{revoked}"
    assert offers == load_offers()


def test_offers_data_validates_against_the_schema():
    assert validate_offers(OFFERS_PATH) == []


def test_schema_rejects_a_featured_speed_that_does_not_match_the_measurement(tmp_path):
    offer = {
        "id": "demo",
        "title": "Demo",
        "freeMechanism": "permanent",
        "endpointCheck": {"checkedAt": "2026-09-19", "verdict": "OK", "ms": 500},
        "featured": {
            "since": "2026-09-19",
            "speedMs": 120,
            "speedTier": "very_fast",
            "quotaTier": "high",
            "reason": "接口实测 120ms",
            "reasonEn": "120 ms",
        },
    }
    path = tmp_path / "offers.json"
    path.write_text(json.dumps([offer], ensure_ascii=False), encoding="utf-8")
    errors = validate_offers(path)
    assert "offers[0]: featured.speedMs must equal the measured endpointCheck.ms" in errors


def test_schema_rejects_a_malformed_featured_block(tmp_path):
    offer = {
        "id": "demo",
        "title": "Demo",
        "freeMechanism": "permanent",
        "featured": {"since": "2026/09/19", "speedMs": 120, "speedTier": "blazing", "quotaTier": "huge", "reason": ""},
    }
    path = tmp_path / "offers.json"
    path.write_text(json.dumps([offer], ensure_ascii=False), encoding="utf-8")
    errors = validate_offers(path)
    assert any("featured.since" in error for error in errors)
    assert any("featured.speedTier" in error for error in errors)
    assert any("featured.quotaTier" in error for error in errors)
    assert any("featured.reason" in error for error in errors)


# --------------------------------------------------------------------------- #
# 渲染
# --------------------------------------------------------------------------- #
def test_offer_page_shows_the_featured_chip_and_its_reason():
    entry = offer("siliconflow-free-models")
    page = render_offer_page(entry, load_offers(), "https://freellm.top")
    assert 'class="flag-chip flag-featured"' in page
    assert "◆ 加精" in page
    assert entry["featured"]["reason"] in page
    assert entry["featured"]["reasonEn"] in page


def test_offer_page_omits_the_featured_chip_when_not_featured():
    entry = offer("groq-free")
    assert "featured" not in entry
    page = render_offer_page(entry, load_offers(), "https://freellm.top")
    # 样式表里始终有 .flag-featured，这里看的是标签本身没有渲染出来。
    assert 'class="flag-chip flag-featured"' not in page
    assert 'class="featured-note"' not in page


def test_homepage_static_cards_carry_the_featured_chip():
    entry = offer("comate")
    markup = render_offer_flags(entry)
    assert 'class="flag-chip flag-featured"' in markup
    assert entry["featured"]["reason"] in markup
    assert "flag-featured" not in render_offer_flags(offer("groq-free"))


def test_category_page_marks_featured_offers():
    entry = offer("comate")
    page = render_category_page("free-ide", load_offers(), "https://freellm.top")
    assert entry["title"] in page
    assert 'class="flag-chip flag-featured"' in page


def test_homepage_exposes_the_featured_filter_and_explanation():
    page = HOMEPAGE_PATH.read_text(encoding="utf-8")
    assert 'data-filter="featured"' in page
    assert "data-featured=" in page
    assert "'featured', 'free_quota'" in page or "'all', 'featured'" in page
    assert "featuredPick" in page and "featuredNote" in page
    assert ".flag-featured" in page


def test_mark_featured_offers_check_mode_is_clean(tmp_path, monkeypatch):
    import scripts.mark_featured_offers as module

    monkeypatch.setattr(sys, "argv", ["mark_featured_offers", "--data", str(OFFERS_PATH), "--check"])
    assert module.main() == 0


def test_mark_featured_offers_revokes_a_tag_that_no_longer_qualifies(tmp_path):
    offers = [
        {
            "id": "demo",
            "freeMechanism": "permanent",
            "quota": "1,000,000 tokens",
            "endpointCheck": {"ms": 120},
            "featured": {"since": "2026-09-19"},
        }
    ]
    updated, granted, revoked = apply(offers, "2026-09-19")
    assert granted and not revoked
    # 实测变慢之后标签必须被撤掉，而不是留在页面上。
    offers[0]["endpointCheck"]["ms"] = 900
    updated, granted, revoked = apply(offers, "2026-09-19")
    assert revoked == ["demo"] and "featured" not in updated[0]
