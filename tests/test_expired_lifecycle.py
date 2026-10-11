"""Series 3 (2026-10-10 audit): expired offers, delisted models and the Kilo scanner.

Guards:
- an expired offer page always shows the expired banner and never a 「实测通过」
  (or any other positive verification) badge;
- counts only include active (non-expired) offers;
- models delisted upstream are kept as records but marked offline with a date
  and reason, and provider pages never show them (or account-404 models) as 在线;
- curated rows can no longer freeze a provider that has a live scanner source.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from scripts import build_eval_report, build_static, eval_pages
from scripts.build_model_catalog import assert_curated_does_not_mask_sources, discover_rows
from scripts.build_seo_pages import (
    model_status_display,
    offer_is_expired,
    render_offer_page,
    render_provider_page,
)
from crawler.official_model_discovery import (
    discover_official_model_sources,
    parse_openrouter_models,
    validate_source_registry,
)

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://freellm.top"
POSITIVE_BADGES = ("实测通过", "实测好用", "接口已验证", "官网已验证", "◆ 加精", "★ 重点")


def _offers() -> list[dict]:
    return json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8"))


def _models() -> list[dict]:
    return json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8"))


def _header(page: str) -> str:
    return page.split("<header>", 1)[1].split("</header>", 1)[0]


# --------------------------------------------------------------------------- offers


def test_every_expired_offer_page_has_banner_and_no_pass_badge():
    offers = _offers()
    expired = [offer for offer in offers if offer.get("status") == "expired"]
    assert expired, "fixture expectation: the catalogue keeps at least one expired record"
    for offer in expired:
        page = render_offer_page(offer, offers, SITE)
        assert 'class="offer-expired-banner"' in page, offer["id"]
        assert "已过期" in page and "Expired" in page, offer["id"]
        for badge in POSITIVE_BADGES:
            assert badge not in _header(page), (offer["id"], badge)
        assert "实测通过" not in page, offer["id"]


def test_expired_guard_is_generic_not_per_offer():
    """Flip a verified offer with network/endpoint evidence to expired: badges must vanish."""
    offers = _offers()
    candidate = next(
        offer for offer in offers
        if offer.get("status") == "verified"
        and isinstance(offer.get("networkCheck"), dict)
        and offer["networkCheck"].get("region") in {"both", "cn", "intl"}
    )
    live_page = render_offer_page(candidate, offers, SITE)
    assert "实测通过" in live_page
    assert 'class="offer-expired-banner"' not in live_page

    ended = copy.deepcopy(candidate)
    ended["status"] = "expired"
    ended["expires_at"] = "2026-01-01"
    ended["featured"] = {"reason": "fast", "reasonEn": "fast", "since": "2026-01-01"}
    ended["handsOn"] = {"testedAt": "2026-01-01", "note": "ok"}
    ended["freeLLMTest"] = {"testLevel": "full", "status": "passed", "testedAt": "2026-01-01", "actualUsageVerified": True}
    page = render_offer_page(ended, offers, SITE)
    assert offer_is_expired(ended)
    assert 'class="offer-expired-banner"' in page
    assert "2026-01-01" in page.split('class="offer-expired-banner"', 1)[1].split("</div>", 1)[0]
    assert "实测通过" not in page
    for badge in POSITIVE_BADGES:
        assert badge not in _header(page), badge


def test_homepage_flags_drop_positive_chips_for_expired_offers():
    offer = next(o for o in _offers() if isinstance(o.get("networkCheck"), dict) and o["networkCheck"].get("region") == "both")
    assert "实测通过" in build_static.render_offer_flags(offer)
    ended = dict(offer, status="expired")
    flags = build_static.render_offer_flags(ended)
    for badge in ("实测通过", "实测好用", "接口已验证", "官网已验证", "加精", "重点"):
        assert badge not in flags
    js = (ROOT / "js" / "homepage.js").read_text(encoding="utf-8")
    body = js.split("const offerFlagsMarkup = item => {", 1)[1].split("const ", 1)[0] + js.split("const offerFlagsMarkup = item => {", 1)[1][:2500]
    assert "const expired = isExpiredOffer(item);" in body
    assert "if (!expired) chips.push(...offerNetworkFlags(item));" in body


def test_counts_exclude_expired_offers():
    offers = _offers()
    today = "2026-10-10"
    active = [o for o in offers if build_static.is_active_offer(o, today)]
    assert all(o.get("status") != "expired" for o in active)
    assert len(active) == len(offers) - sum(
        o.get("status") == "expired" or bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(o.get("expires_at") or "")) and o["expires_at"] < today)
        for o in offers
    )
    # A past expires_at counts as ended even before someone flips the status.
    assert not build_static.is_active_offer({"status": "verified", "expires_at": "2026-10-09"}, today)
    assert build_static.is_active_offer({"status": "verified", "expires_at": "2026-10-10"}, today)

    html = (
        '<b data-category-count="all">0</b>'
        '<button class="filter-chip active" data-filter="all" type="button">全部<em>0</em></button>'
    )
    data = [
        {"id": "a", "status": "verified", "productType": "api"},
        {"id": "b", "status": "expired", "productType": "api"},
        {"id": "c", "status": "verified", "expires_at": "2000-01-01", "productType": "api"},
    ]
    rendered = build_static.replace_static_catalog(html, data)
    assert '<b data-category-count="all">1</b>' in rendered
    assert "全部<em>1</em>" in rendered


def test_stepfun_limited_free_lists_only_official_stepaudio3_previews():
    offer = {o["id"]: o for o in _offers()}["stepfun-limited-time-free"]
    expected = [
        "stepaudio-3-realtime-preview",
        "stepaudio-3-chat-preview",
        "stepaudio-3-gen-preview",
        "stepaudio-3-music-preview",
    ]
    assert offer["model"] == " · ".join(expected)
    assert [entry["model"] for entry in offer["freeModels"]] == expected
    blob = json.dumps({k: offer[k] for k in ("model", "freeSummaryEn", "freeModels", "command")}, ensure_ascii=False)
    for gone in ("step-audio-r1.1", "step-1x-edit"):
        assert gone not in blob
    assert "step-2x-large" not in json.dumps(offer["freeModels"])


def test_time_boxed_offers_carry_expires_at():
    by_id = {o["id"]: o for o in _offers()}
    assert by_id["autoclaw-glm-5-3-flash-oct-2026"]["expires_at"] == "2026-10-11"
    step5 = by_id["stepfun-step-5-preview-free-week"]
    assert step5["expires_at"] == "2026-10-15"
    assert step5.get("expires_at_estimated") is True  # official post says "a week" from 10-08


def test_opencode_zen_drops_mimo_v25_free():
    zen = {o["id"]: o for o in _offers()}["opencode-zen-free"]
    assert "MiMo-V2.5 Free" not in zen["model"]
    for name in ("Step 5 Preview Free", "Ling 3.1 Flash Free", "LongCat 2.5 Preview Free"):
        assert name in zen["model"]


def test_step_plan_expired_copy_no_longer_advertises_75_days():
    plan = {o["id"]: o for o in _offers()}["stepfun-step-plan-promo"]
    assert plan["status"] == "expired"
    for field in ("title", "titleZh", "titleEn", "freeSummaryEn"):
        assert "最高 75 天免费" not in str(plan.get(field) or "")
        assert not str(plan.get(field) or "").startswith("Current Step Plan promotion")


# --------------------------------------------------------------------------- models

DELISTED = {
    "openrouter": [
        "qwen-qwen3-8-27b-free", "z-ai-glm-5-2-free", "deepseek-deepseek-v4-flash-0731-free",
        "inclusionai-ling-3-0-flash-fin-free", "inclusionai-ling-3-0-flash-sante-free",
        "inclusionai-ling-3-0-flash-vl-free", "nex-agi-nex-n2-5-mini-free", "nex-agi-nex-n2-5-pro-free",
        "stealth-union-alpha",
    ],
    "kilo": [
        "qwen-qwen3-8-27b-free", "z-ai-glm-5-2-free", "deepseek-deepseek-v4-flash-0731-free",
        "inclusionai-ling-3-0-flash-fin-free", "inclusionai-ling-3-0-flash-sante-free",
        "inclusionai-ling-3-0-flash-vl-free", "nex-agi-nex-n2-5-mini-free", "nex-agi-nex-n2-5-pro-free",
    ],
    "nvidia-nim": ["deepseek-v4-flash-0731", "mistral-nemotron", "riva-translate-4b-instruct-v1-1"],
    "llm7-io": ["claude-haiku-4-5", "gpt-5-5", "mimo-v2-5", "mimo-v2-5-pro", "minimax-m2-7"],
}


def test_delisted_models_are_kept_but_marked_offline_with_date_and_reason():
    by_id = {m["id"]: m for m in _models()}
    for provider, slugs in DELISTED.items():
        for slug in slugs:
            row = by_id[f"{provider}/{slug}"]
            assert row["status"] == "offline", row["id"]
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["offlineAt"]), row["id"]
            assert row["offlineReason"].strip(), row["id"]
            assert row["offlineEvidenceUrl"].startswith("https://"), row["id"]


def test_offline_rows_survive_the_daily_sync_while_missing_upstream():
    from scripts.sync_model_catalog import sync_model_catalog

    previous = [m for m in _models() if m["id"] == "openrouter/stealth-union-alpha"]
    merged = sync_model_catalog([], previous, "2026-10-11")
    assert merged[0]["status"] == "offline"
    assert merged[0]["freshnessStatus"] == "stale"


def test_status_cell_never_claims_online_for_offline_stale_or_unavailable_rows():
    css, label, title = model_status_display({"status": "offline", "offlineAt": "2026-10-10", "offlineReason": "gone"})
    assert css == "offline" and "已下线" in label and "在线" not in label and "gone" in title
    css, label, _ = model_status_display({"status": "online", "freshnessStatus": "stale", "providerId": "x", "model": "zz-not-evaluated"})
    assert "在线" not in label and "待复核" in label


NVIDIA_404 = [
    "deepseek-coder-6.7b-instruct", "codellama-70b", "codegemma-7b", "mistral-large",
    "nemotron-4-340b-instruct", "dbrx-instruct", "vila", "palmyra-creative-122b", "palmyra-med-70b",
    "palmyra-fin-70b-32k", "palmyra-med-70b-32k", "granite-34b-code-instruct",
]


def _provider_rows(provider_id: str) -> dict[str, str]:
    models = _models()
    offers = _offers()
    provider_models = [m for m in models if m["providerId"] == provider_id]
    provider = {"id": provider_id, "name": provider_models[0]["provider"], "modelIds": [m["id"] for m in provider_models]}
    page = render_provider_page(provider, provider_models, offers, SITE)
    rows = {}
    for row in re.findall(r"<tr>.*?</tr>", page, re.S):
        match = re.search(r'<small class="model-id"[^>]*>([^<]+)</small>', row)
        if match:
            rows[match.group(1)] = row
    return rows


def test_nvidia_account_404_models_match_evaluations_page():
    rows = _provider_rows("nvidia-nim")
    for name in NVIDIA_404:
        model_id = "nvidia-nim/" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        kind, _ = eval_pages.lookup("nvidia-nim", name)
        assert kind == "unavailable", name
        row = rows[model_id]
        assert "本账号实测不可用，待复核" in row, name
        assert ">在线<" not in row and "在线</span>" not in row, name


def test_provider_pages_do_not_render_delisted_models_as_online():
    for provider in ("openrouter", "kilo", "llm7-io", "nvidia-nim"):
        rows = _provider_rows(provider)
        for slug in DELISTED[provider]:
            row = rows[f"{provider}/{slug}"]
            assert "已下线" in row, (provider, slug)
            assert "在线</span>" not in row, (provider, slug)


# --------------------------------------------------------------------------- Kilo scanner


def test_kilo_has_a_live_scanner_source_and_no_frozen_curated_rows():
    sources = json.loads((ROOT / "data" / "official-model-sources.json").read_text(encoding="utf-8"))
    assert validate_source_registry(sources) == []
    kilo = [s for s in sources if s["providerId"] == "kilo" and s.get("enabled", True)]
    assert len(kilo) == 1
    assert kilo[0]["url"] == "https://api.kilo.ai/api/openrouter/models"
    assert kilo[0]["type"] == "openrouter_models"
    curated = json.loads((ROOT / "data" / "models-curated.json").read_text(encoding="utf-8"))
    assert not [row for row in curated if row["providerId"] == "kilo"]
    # Same rule for every provider: curated rows may not shadow a live scanner.
    assert_curated_does_not_mask_sources(curated, sources)


def test_curated_rows_shadowing_a_scanned_provider_fail_loudly(tmp_path):
    sources = [{
        "id": "kilo-src", "providerId": "kilo", "provider": "Kilo", "kind": "public_api", "type": "openrouter_models",
        "url": "https://api.kilo.ai/api/openrouter/models", "allowedDomains": ["api.kilo.ai"],
        "modelPageTemplate": "https://kilo.ai/models", "enabled": True,
    }]
    with pytest.raises(ValueError, match="kilo"):
        assert_curated_does_not_mask_sources([{"id": "kilo/old", "providerId": "kilo"}], sources)
    sources_path = tmp_path / "sources.json"
    curated_path = tmp_path / "curated.json"
    sources_path.write_text(json.dumps(sources), encoding="utf-8")
    curated_path.write_text(json.dumps([{"id": "kilo/stale-snapshot", "providerId": "kilo"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="shadow live scanner"):
        discover_rows(sources_path, curated_path=curated_path)


def test_kilo_scan_reflects_the_fresh_payload_not_a_snapshot():
    source = {
        "id": "kilo-src", "providerId": "kilo", "provider": "Kilo Gateway", "kind": "public_api", "type": "openrouter_models",
        "url": "https://api.kilo.ai/api/openrouter/models", "allowedDomains": ["api.kilo.ai"],
        "modelPageTemplate": "https://kilo.ai/models", "freeOnly": True, "enabled": True,
        "rowDefaults": {"rateLimit": "Shared upstream free pool", "accessEndpoint": "https://api.kilo.ai/api/gateway/v1"},
    }
    payload = {"data": [
        {"id": "cohere/north-mini-code:free", "name": "North Mini Code (free)", "pricing": {"prompt": "0", "completion": "0"}, "isFree": True},
        {"id": "google/lyria-3-pro-preview", "name": "Lyria", "pricing": {"prompt": "0", "completion": "0"}, "isFree": False},
        {"id": "qwen/qwen3.8-27b", "name": "Qwen paid", "pricing": {"prompt": "0.0000004", "completion": "0.000001"}},
    ]}
    result = discover_official_model_sources(
        [source], fetcher=lambda *_args: {"status": "ok", "content": json.dumps(payload)}
    )
    ids = [row["modelSlug"] for row in result["models"]]
    assert ids == ["cohere-north-mini-code-free"]  # isFree=false and paid rows excluded
    row = result["models"][0]
    assert row["rateLimit"] == "Shared upstream free pool"
    assert row["accessEndpoint"] == "https://api.kilo.ai/api/gateway/v1"
    assert row["sourceEndpoint"] == "https://api.kilo.ai/api/openrouter/models"

    failed = discover_official_model_sources([source], fetcher=lambda *_args: {"status": "failed", "reason": "HTTP 503"})
    assert failed["models"] == []
    assert failed["failures"] and failed["failures"][0]["reason"] == "HTTP 503"
    assert parse_openrouter_models({"data": []}, source) == []


# --------------------------------------------------------------------------- evaluations


def test_no_provider_400_maps_to_no_serving_provider():
    m = {"errors": ["HTTP 400"], "errorDetail": '{"error":{"message":"Model id : MiniMax/MiniMax-M3 , has no provider supported"}}'}
    assert build_eval_report.reason_zh(m) == "无可用服务商"
    assert eval_pages.unavailable_reason(m)[0] == "无可用服务商"
    assert build_eval_report.reason_zh({"errors": ["HTTP 400"], "errorDetail": "bad param"}) == "请求被拒绝（参数不支持）"
