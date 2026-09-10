import json
from pathlib import Path

import pytest

from crawler.schema import (
    validate_model_access,
    validate_model_access_file,
    validate_access_references,
    validate_provider_access,
    validate_provider_access_file,
    validate_region_policies,
)
from scripts.build_seo_pages import _cn_status_for_model, _cn_status_for_policy, _operation_hints, _load_access_context, build_site, render_model_aggregate_page, render_provider_page

ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
MODELS_PATH = ROOT / "data" / "models.json"
CATALOG_PATH = ROOT / "data" / "provider-catalog.json"
POLICIES_PATH = ROOT / "data" / "region-policies.json"
PROVIDER_ACCESS_PATH = ROOT / "data" / "provider-access.json"
MODEL_ACCESS_PATH = ROOT / "data" / "model-access.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_curated_data_files_pass_schema_validation():
    assert validate_region_policies(POLICIES_PATH) == []
    assert validate_provider_access_file(PROVIDER_ACCESS_PATH) == []
    assert validate_model_access_file(MODEL_ACCESS_PATH) == []


def test_every_catalog_provider_has_a_registration_card():
    catalog_ids = {provider["id"] for provider in _load(CATALOG_PATH)}
    card_ids = {card["providerId"] for card in _load(PROVIDER_ACCESS_PATH)}
    assert card_ids == catalog_ids


def test_every_catalog_model_has_exactly_one_access_card():
    model_ids = [model["id"] for model in _load(MODELS_PATH)]
    cards = {card["modelId"]: card for card in _load(MODEL_ACCESS_PATH)}
    for model_id in model_ids:
        assert model_id in cards, f"missing access card: {model_id}"
        assert cards[model_id]["providerId"] == next(
            model["providerId"] for model in _load(MODELS_PATH) if model["id"] == model_id
        )


def test_access_cards_only_reference_known_region_policies():
    policies = _load(POLICIES_PATH)
    policy_ids = {policy["id"] for policy in policies["policies"]}
    for card in _load(PROVIDER_ACCESS_PATH):
        assert card["regionPolicyId"] in policy_ids
    for card in _load(MODEL_ACCESS_PATH):
        if card["regionOverridePolicyId"] is not None:
            assert card["regionOverridePolicyId"] in policy_ids


def test_region_policies_pin_mainland_china_as_default_audience():
    policies = _load(POLICIES_PATH)
    assert policies["defaultCountryCode"] == "CN"
    assert policies["defaultCountryCode"] in policies["priorityCountries"]


def test_retired_models_record_replacement_and_official_evidence():
    retired = [card for card in _load(MODEL_ACCESS_PATH) if card["accessStatus"] == "retired"]
    assert retired, "GitHub Models cards must be marked retired"
    for card in retired:
        assert card["verificationStatus"] == "verified"
        assert card["replacement"]
        assert card["lastVerifiedAt"]
        assert all(url.startswith("https://") for url in card["sourceUrls"])
    provider_cards = {card["providerId"]: card for card in _load(PROVIDER_ACCESS_PATH)}
    github_card = provider_cards["github-models"]
    assert github_card["registrationStatus"] == "unavailable"
    assert github_card["replacement"]
    assert "https://docs.github.com/en/github-models" in github_card["sourceUrls"]


def test_unverified_cards_never_claim_official_verification():
    for label, cards in (
        ("provider", _load(PROVIDER_ACCESS_PATH)),
        ("model", _load(MODEL_ACCESS_PATH)),
    ):
        for card in cards:
            if card["verificationStatus"] == "unverified":
                assert card["lastVerifiedAt"] is None, f"{label} card claims a date without verification"


def test_valid_and_invalid_card_examples():
    base_provider = {
        "providerId": "example",
        "profileId": "example-api",
        "registerUrl": None,
        "accountRequired": "unknown",
        "emailRequired": "unknown",
        "phoneRequired": "unknown",
        "identityRequired": "unknown",
        "cardRequired": "unknown",
        "billingRequired": "unknown",
        "apiKeyRequired": "yes",
        "licenseAcceptance": "model_dependent",
        "modelApproval": "unknown",
        "gpuRequired": "unknown",
        "overageBehavior": "unknown",
        "searchMethod": "official_model_catalog",
        "regionPolicyId": "policy-unknown-default",
        "registrationSteps": [],
        "registrationStatus": "available",
        "replacement": None,
        "sourceUrls": ["https://example.com/docs"],
        "lastVerifiedAt": None,
        "verificationStatus": "unverified",
        "confidence": "low",
        "notes": "",
    }
    assert validate_provider_access(base_provider) == []
    assert "replacement must be a non-empty string when registrationStatus is unavailable" in validate_provider_access(
        base_provider | {"registrationStatus": "unavailable"}
    )

    base_model = {
        "modelId": "example/demo",
        "providerId": "example",
        "registrationProfileId": "example-api",
        "modelSearchName": "demo",
        "extraRequirements": [],
        "regionOverridePolicyId": None,
        "quotaOverride": None,
        "accessStatus": "needs_review",
        "replacement": None,
        "sourceUrls": ["https://example.com/models/demo"],
        "lastVerifiedAt": None,
        "verificationStatus": "unverified",
        "notes": "",
    }
    assert validate_model_access(base_model) == []
    errors = validate_model_access(base_model | {"accessStatus": "retired"})
    assert any("replacement" in error for error in errors)
    assert "duplicate modelId: example/demo" in validate_model_access_file([base_model, base_model])


def test_cn_region_status_derivation_is_evidence_bound():
    assert _cn_status_for_policy({"type": "denylist", "blockedCountries": ["CN"]}) == "unavailable"
    assert _cn_status_for_policy({"type": "denylist", "blockedCountries": ["KP"]}) == "unknown"
    assert _cn_status_for_policy({"type": "allowlist", "allowedCountries": ["CN"], "countriesComplete": True}) == "available"
    assert _cn_status_for_policy({"type": "allowlist", "allowedCountries": ["US"], "countriesComplete": True}) == "unavailable"
    # An incomplete allowlist must not be read as "CN unavailable".
    assert _cn_status_for_policy({"type": "allowlist", "allowedCountries": [], "countriesComplete": False}) == "unknown"
    assert _cn_status_for_policy({"type": "unknown"}) == "unknown"
    assert _cn_status_for_policy(None) == "unknown"


def test_model_region_override_takes_precedence_over_provider_policy():
    provider_cards = {"demo": {"registrationStatus": "available", "regionPolicyId": "provider-policy"}}
    policies = {
        "provider-policy": {"type": "denylist", "blockedCountries": ["CN"]},
        "model-policy": {"type": "allowlist", "allowedCountries": ["CN"], "countriesComplete": True},
    }
    model = {"id": "demo/model", "providerId": "demo"}
    access_cards = {"demo/model": {"regionOverridePolicyId": "model-policy", "accessStatus": "needs_review"}}
    assert _cn_status_for_model(model, provider_cards, policies, access_cards) == "available"


def test_operation_hints_do_not_treat_no_registration_as_account_required(tmp_path):
    operation = {
        "providerId": "demo",
        "lastVerifiedAt": "2026-09-10",
        "paths": [{"prerequisites": ["无需注册", "无需 API key"], "sourceUrls": []}],
    }
    (tmp_path / "demo.json").write_text(json.dumps(operation), encoding="utf-8")
    hints = _operation_hints(tmp_path)
    assert hints["demo"]["accountRequired"] is None
    assert hints["demo"]["apiKeyRequired"] is None


def test_access_references_reject_unknown_model_policy():
    provider_cards = [{"providerId": "demo", "regionPolicyId": "known"}]
    model_cards = [{"modelId": "demo/model", "providerId": "demo", "regionOverridePolicyId": "missing"}]
    assert any("unknown region policy" in error for error in validate_access_references(provider_cards, model_cards, {"known"}))


def test_provider_and_model_pages_render_registration_requirements():
    provider = {"id": "demo", "name": "Demo", "sourceKind": "catalog"}
    model = {"id": "demo/model", "providerId": "demo", "provider": "Demo", "model": "model", "score": 1, "context": "1", "maxOutput": "1", "modality": ["text"], "rateLimit": "1", "released": "", "usageActivity": "", "status": "online", "lastSeenAt": "2026-09-10", "sourceUrl": "https://example.com/model"}
    card = {"providerId": "demo", "registerUrl": "https://example.com/register", "accountRequired": "yes", "emailRequired": "yes", "phoneRequired": "no", "identityRequired": "unknown", "cardRequired": "no", "billingRequired": "no", "apiKeyRequired": "yes", "licenseAcceptance": "no", "modelApproval": "no", "gpuRequired": "no", "registrationSteps": ["注册账号", "创建 API Key"], "registrationStatus": "available", "notes": "demo"}
    provider_html = render_provider_page(provider, [model], [], "https://freellm.top", [], {"demo": card})
    model_html = render_model_aggregate_page("model", [model], [], "https://freellm.top", {"demo": card})
    for html in (provider_html, model_html):
        assert "注册要求" in html
        assert "手机号" in html
        assert "API Key" in html
        assert "创建 API Key" in html


def test_access_context_fails_when_required_file_is_invalid(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "provider-access.json").write_text("{bad", encoding="utf-8")
    (data_dir / "region-policies.json").write_text("{}", encoding="utf-8")
    (data_dir / "model-access.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr("scripts.build_seo_pages.ACCESS_DATA_DIR", data_dir)
    with pytest.raises(SystemExit):
        _load_access_context()


def test_model_catalog_page_exposes_mainland_cn_filter(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    all_models_page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")
    center_page = (tmp_path / "models" / "center" / "index.html").read_text(encoding="utf-8")

    for page in (all_models_page, center_page):
        assert 'id="model-catalog-region"' in page
        assert 'data-label-zh="全部状态"' in page
        assert "大陆待核验" in page
        assert 'data-cn="unknown"' in page
        assert "colSpan = 12" in page
    # The default option is "all statuses": with mostly unverified data the CN lens
    # annotates every row instead of hiding them.
    assert '<option value="" data-label-zh="全部状态" data-label-en="All statuses" selected>' in all_models_page


def test_models_page_seo_surfaces_cn_availability(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    all_models_page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")
    china_guide = (tmp_path / "guides" / "china-free-ai-api" / "index.html").read_text(encoding="utf-8")

    # Title, meta description and structured data carry the CN availability keywords.
    assert "（含中国大陆可用性标注）" in all_models_page
    assert '"keywords"' in all_models_page
    assert "mainland-China availability" in all_models_page
    # A crawlable static section explains the labels and links out.
    assert 'id="mainland-cn-availability"' in all_models_page
    assert 'href="https://freellm.top/guides/china-free-ai-api/"' in all_models_page
    assert 'href="https://freellm.top/providers/"' in all_models_page
    # The China guide links back to the filterable directory.
    assert "mainland CN availability" in china_guide
    assert 'href="https://freellm.top/models/all/"' in china_guide


def test_built_site_never_renders_retired_models(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    all_models_page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")
    providers_index = (tmp_path / "providers" / "index.html").read_text(encoding="utf-8")

    # The retirement explainer may mention GitHub Models in prose, but no catalog
    # row, provider page or model slug may render it as available.
    assert 'data-model-id="github-models/' not in all_models_page
    assert "github-models" not in providers_index
    assert not (tmp_path / "providers" / "github-models").exists()
    for model_slug in ("ai21-jamba-1-5-large", "mistral-large-2411", "phi-4"):
        assert model_slug not in all_models_page
    assert "2026-07-30" in all_models_page  # retirement notice stays crawlable
