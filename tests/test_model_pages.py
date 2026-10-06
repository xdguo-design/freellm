import json
import re
from collections import Counter
from html import unescape
from pathlib import Path

import pytest

from scripts.build_seo_pages import (
    MODELS_PER_PAGE,
    _exclude_retired_models,
    _load_featured_agents,
    _load_access_context,
    _load_model_access,
    _cn_status_for_model,
    _model_catalog_row,
    build_site,
    model_record_groups,
    render_models_landing_page,
)


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
MODELS_PATH = ROOT / "data" / "models.json"


def build_featured_fixture_page():
    model = {
        "id": "fixture/model",
        "providerId": "fixture",
        "provider": "Fixture Provider",
        "model": "Fixture Model",
        "modality": ["image", "audio", "video"],
    }
    return render_models_landing_page(
        offers=[], models=[model], vendor_directory=[],
        site_url="https://freellm.top", curated_models=[model],
    )


def test_featured_cards_show_unknown_and_untested_states():
    page = build_featured_fixture_page()

    assert "待核实" in page
    assert "未实测" in page
    assert "图片·方向待核实" in page


def test_featured_agent_registry_drives_models_page(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")
    agent_cards = re.findall(r'<article class="featured-agent-card"', page)

    assert len(agent_cards) == 13
    assert "当前收录 13 个 AI Agent" in page
    assert "13 个 Agent" in page
    assert 'href="/offers/manus-free-agent/"' in page
    assert 'href="/offers/workbuddy/"' in page
    assert 'href="https://grok.com/" target="_blank" rel="noopener noreferrer"' in page
    assert 'href="https://chatgpt.com/" target="_blank" rel="noopener noreferrer"' in page
    assert 'href="https://agent.space/agents" target="_blank" rel="noopener noreferrer"' in page
    assert 'data-icon-host="muse.ai"' in page
    assert page.count('class="brand-icon-fallback"') >= 13
    assert 'data-search-text="grok' in page
    assert 'data-search-text="claude code' in page
    assert 'lang="en">General assistant' in page


def test_featured_agent_registry_is_validated(tmp_path):
    agents = _load_featured_agents(ROOT / "data")

    assert len(agents) == 13
    assert len({agent["id"] for agent in agents}) == len(agents)
    assert all(agent["url"].startswith("https://") for agent in agents)

    invalid_registry = tmp_path / "featured_agents.json"
    invalid_registry.write_text(json.dumps([
        {"id": "duplicate", "url": "https://example.com"},
        {"id": "duplicate", "url": "http://example.com"},
    ]), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        _load_featured_agents(tmp_path)


def test_featured_page_includes_region_and_capability_filters():
    page = build_featured_fixture_page()

    assert 'data-filter="region"' in page
    assert 'data-filter="capability"' in page
    assert 'id="featured-model-count"' in page
    assert 'id="featured-model-comparison"' in page
    assert 'data-compare-toggle' in page
    assert '/js/models-discovery.js?v=' in page
    assert 'placeholder="搜索模型 / Search models"' in page
    assert 'placeholder="<span lang=' not in page
    assert '<em><span lang="zh-CN">AI Agent</span>' in page
    assert 'aria-label="精选模型对比 / Featured model comparison"' in page
    assert "挑选并实测" not in page


def test_featured_benchmark_attributes_include_comparison_protocol():
    model = {
        "id": "fixture/model", "providerId": "fixture", "provider": "Fixture Provider",
        "model": "Fixture Model", "servicePath": "https://provider.example/v1/chat/completions",
        "benchmark": {
            "protocolVersion": "text-stream-v1", "taskId": "short-answer-zh-v1", "language": "zh",
            "samplingMode": "temperature-0", "temperature": 0, "maxOutputTokens": 256,
            "warmups": 1, "sampleCount": 3, "ttftMsMedian": 420,
            "outputTokensPerSecondMedian": 36.4, "testRegion": "domestic",
            "servicePath": "https://provider.example/v1/chat/completions", "testedAt": "2026-10-04",
            "rawResultRef": "data/benchmarks/example.json",
        },
    }
    page = render_models_landing_page(
        offers=[], models=[model], vendor_directory=[],
        site_url="https://freellm.top", curated_models=[model],
    )

    assert 'data-benchmark-sampling-mode="temperature-0"' in page
    assert 'data-benchmark-temperature="0"' in page
    assert 'data-benchmark-max-output="256"' in page
    assert 'data-benchmark-warmups="1"' in page
    assert 'data-benchmark-sample-count="3"' in page


def model_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def test_build_site_creates_model_aggregation_pages(tmp_path):
    result = build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    models = _exclude_retired_models(
        json.loads(MODELS_PATH.read_text(encoding="utf-8")),
        _load_model_access(OFFERS_PATH),
    )
    groups = model_record_groups(models)
    multi_record_slugs = {slug for slug, records in groups.items() if len(records) > 1}

    assert multi_record_slugs, "fixture expectation: catalog must contain multi-provider models"
    assert result.page_count >= 49 + len(multi_record_slugs)

    rich_slug = sorted(multi_record_slugs)[0]
    records = groups[rich_slug]
    page = (tmp_path / "models" / rich_slug / "index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="https://freellm.top/models/{rich_slug}/"' in page
    # Every provider contributing a record to the aggregate must be represented.
    for provider_name in sorted({str(record.get("provider") or "") for record in records}):
        assert provider_name in page
    # The page must surface the freshness date that is actually in the catalog.
    # Derive it from the data instead of hardcoding a literal: the crawler re-stamps
    # lastSeenAt on every sync, which would otherwise break this test each time.
    expected_freshness = {
        record["lastSeenAt"]
        for record in records
        if record.get("lastSeenAt")
    }
    assert expected_freshness, "fixture expectation: aggregate records must carry lastSeenAt"
    for seen_at in expected_freshness:
        assert seen_at in page
    assert '"@type": "ItemList"' in page


def test_single_record_model_pages_are_noindex_and_kept_out_of_sitemaps(tmp_path):
    """Aggregates over exactly one catalog row duplicate /models/all/ content, so they
    stay reachable for humans but are noindex and excluded from every sitemap."""
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    groups = model_record_groups(models)
    thin = next(slug for slug, records in groups.items() if len(records) == 1)
    rich = next(slug for slug, records in groups.items() if len(records) > 1)

    thin_page = (tmp_path / "models" / thin / "index.html").read_text(encoding="utf-8")
    rich_page = (tmp_path / "models" / rich / "index.html").read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,follow">' in thin_page
    assert f'<link rel="canonical" href="https://freellm.top/models/{thin}/"' in thin_page
    assert '<meta name="robots" content="index,follow,max-image-preview:large"' in rich_page

    models_sitemap = (tmp_path / "sitemap-models.xml").read_text(encoding="utf-8")
    assert f"https://freellm.top/models/{rich}/" in models_sitemap
    assert f"https://freellm.top/models/{thin}/" not in models_sitemap


def _all_catalog_pages(tmp_path) -> str:
    """Concatenate every paginated model-catalog page (page 1 + page/2..N)."""
    base = tmp_path / "models" / "all"
    pages = [base / "index.html"]
    pages.extend(sorted(base.glob("page/*/index.html")))
    return "".join(page.read_text(encoding="utf-8") for page in pages if page.is_file())


def test_model_rows_link_only_to_indexable_aggregation_pages(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    models = _exclude_retired_models(
        json.loads(MODELS_PATH.read_text(encoding="utf-8")),
        _load_model_access(OFFERS_PATH),
    )
    groups = model_record_groups(models)
    rich = next(slug for slug, records in groups.items() if len(records) > 1)
    thin = next(slug for slug, records in groups.items() if len(records) == 1)
    all_pages = _all_catalog_pages(tmp_path)

    # Rich aggregate pages are crawlable destinations; thin single-record pages
    # stay reachable by direct URL but are noindex and therefore not promoted
    # by the model directory.
    assert f'href="/models/{rich}/"' in all_pages
    assert f'href="/models/{thin}/"' not in all_pages
    last_provider_href = f'href="/providers/{model_slug(models[-1].get("providerId"))}/"'
    assert last_provider_href in all_pages


def test_models_landing_separates_offer_model_vendor_and_provider_id_counts(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    overview = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")
    all_models_page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    provider_pages = list((tmp_path / "providers").glob("*/index.html"))
    curated = json.loads((ROOT / "data" / "models-curated.json").read_text(encoding="utf-8"))

    assert "精选模型与 AI Agent" in overview
    assert "精选模型" in overview
    assert "AI Agent 精选" in overview
    assert f"完整目录含 {len(models)}+ 个模型" in overview
    assert f"当前收录 {len(curated)} 个模型" in overview
    assert provider_pages
    assert 'href="/models/all/"' in overview
    assert 'href="/providers/"' in overview
    assert 'href="/category/api/"' in overview
    assert "实时模型目录" in all_models_page


def test_models_landing_shows_curated_models_and_links_to_the_complete_directory(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")
    curated = json.loads((ROOT / "data" / "models-curated.json").read_text(encoding="utf-8"))
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))

    assert "精选模型" in page
    assert "全部模型" in page
    assert 'id="featured-models"' in page
    assert f'href="/models/all/"' in page
    assert page.count('class="featured-model-card"') == len(curated)
    assert page.count("团队精选") == len(curated)
    assert f'data-model-id="{curated[0]["id"]}"' in page
    assert curated[0]["model"] in page
    assert "可用的免费模型入口" not in page


def test_model_center_legacy_route_redirects_to_featured_models(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "center" / "index.html").read_text(encoding="utf-8")

    assert 'http-equiv="refresh" content="0;url=/models/"' in page
    assert 'href="/models/"' in page
    assert '<meta name="robots" content="noindex,follow">' in page


def test_model_rows_carry_score_data_for_catalog_ranking():
    row = _model_catalog_row({
        "id": "alpha/model",
        "providerId": "alpha",
        "provider": "Alpha",
        "model": "model",
        "score": 94,
        "sourceUrl": "https://directory.example/model",
    })
    assert 'data-score="94"' in row
    assert 'class="model-id" title="alpha/model">alpha/model</small>' in row
    assert "#1744E8" in (ROOT / "scripts" / "build_seo_pages.py").read_text(encoding="utf-8")


def test_model_directory_rows_store_each_record_once_and_keep_card_mode(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    # The table is the complete static fallback. Card view should be a visual
    # transformation of the same rows, rather than a second copy of every model.
    assert 'data-catalog-view="cards"' in page
    assert 'aria-label="中国大陆可用性"' not in page  # Labels are attached at runtime only in card mode.
    assert 'cell.setAttribute(\'aria-label\', cardLabels[cellIndex] || \'\')' in page
    assert 'content: attr(aria-label)' in page
    assert 'catalog-card-row' not in page
    assert page.count('class="catalog-row"') == MODELS_PER_PAGE


def test_generated_model_directory_pages_fit_health_budget_and_preserve_all_records(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    pages = [tmp_path / "models" / "all" / "index.html"]
    pages.extend(sorted((tmp_path / "models" / "all").glob("page/*/index.html")))

    assert pages
    assert all(page.stat().st_size <= 340 * 1024 for page in pages)
    rendered = "".join(page.read_text(encoding="utf-8") for page in pages)
    expected = _exclude_retired_models(
        json.loads(MODELS_PATH.read_text(encoding="utf-8")),
        _load_model_access(OFFERS_PATH),
    )
    rendered_ids = Counter(
        unescape(model_id)
        for model_id in re.findall(
            r'<tr class="catalog-row"[^>]*>.*?<small class="model-id"[^>]*>([^<]*)</small>',
            rendered,
            flags=re.DOTALL,
        )
    )
    expected_ids = Counter(str(model.get("id") or "") for model in expected)
    assert rendered_ids == expected_ids


def test_model_directory_shows_activity_column_and_clear_result_count(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert "中国大陆可用性" in page
    assert "显示" in page
    assert "共" in page
    assert "Catalog source" in page
    assert "Showing ${visible.length} / ${pairs.length}" in page


def test_model_directory_exposes_evidence_backed_scenario_filters(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert 'aria-label="场景快捷筛选 / Scenario filters"' in page
    assert 'data-chip-context-min="128000"' in page
    assert '128K+ 上下文' in page
    assert '128K+ context' in page
    assert 'data-chip-modality="image"' in page
    assert 'data-chip-modality="audio"' in page
    assert 'data-chip-region="available"' in page
    assert 'aria-pressed="false"' in page
    # No scenario claims a capability that the model schema does not record.
    assert "编程专家" not in page
    assert "Coding specialist" not in page


def test_model_directory_scenario_filters_use_catalog_evidence_and_compose():
    source = (ROOT / "scripts" / "build_seo_pages.py").read_text(encoding="utf-8")

    assert "row.dataset.context" in source
    assert "row.dataset.modality" in source
    assert "row.dataset.cn" in source
    assert "contextMin" in source
    assert "Number.isFinite(contextValue)" in source
    assert "contextValue >= contextMin" in source
    # Scenario predicates are added to, rather than replacing, existing filters.
    assert "&& (!providerId || row.dataset.providerId === providerId)" in source
    assert "&& (!regionFilter || row.dataset.cn === regionFilter)" in source
    assert "&& (!modalityFilter || modalities.includes(modalityFilter))" in source
    assert "&& matchesContext" in source
    assert "contextMin = 0" in source
    assert "chip.setAttribute('aria-pressed', String(Boolean(active)))" in source
    assert 'id="model-catalog-empty" class="catalog-empty" hidden' in source
    assert "No models match this filter." in source


def test_scenario_filter_row_evidence_matches_catalog_context_modalities_and_region_policy(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page_text = _all_catalog_pages(tmp_path)
    rows = {
        unescape(model_id): (region, modality.split(",") if modality else [], context)
        for model_id, region, modality, context in re.findall(
            r'<tr class="catalog-row" data-model-id="([^"]*)" data-provider-id="[^"]*" '
            r'data-cn="([^"]*)" data-modality="([^"]*)" data-context="([^"]*)"',
            page_text,
        )
    }
    models = _exclude_retired_models(
        json.loads(MODELS_PATH.read_text(encoding="utf-8")),
        _load_model_access(OFFERS_PATH),
    )
    provider_cards, policies, model_access = _load_access_context(ROOT / "data")
    model_by_id = {str(model.get("id") or ""): model for model in models}

    long_context = [model for model in models if str(model.get("context") or "").isdigit() and int(model["context"]) >= 128000]
    image_models = [model for model in models if "image" in (model.get("modality") or [])]
    audio_models = [model for model in models if "audio" in (model.get("modality") or [])]
    missing_context = [model for model in models if not str(model.get("context") or "").isdigit()]

    assert long_context and all(int(rows[model["id"]][2]) >= 128000 for model in long_context)
    assert image_models and all("image" in rows[model["id"]][1] for model in image_models)
    assert audio_models and all("audio" in rows[model["id"]][1] for model in audio_models)
    assert missing_context and all(rows[model["id"]][2] == "" for model in missing_context)
    assert all(
        rows[model_id][0] == _cn_status_for_model(model, provider_cards, policies, model_access)
        for model_id, model in model_by_id.items()
    )
    # A policy-backed filter can correctly return no rows; absence of CN evidence
    # must remain unknown instead of being promoted to available.
    if not any(_cn_status_for_model(model, provider_cards, policies, model_access) == "available" for model in models):
        assert not any(region == "available" for region, _, _ in rows.values())


def test_model_center_legacy_route_is_not_in_sitemap(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    sitemap = (tmp_path / "sitemap-pages.xml").read_text(encoding="utf-8")

    assert "https://freellm.top/models/center/" not in sitemap


def test_previous_longcat_routes_redirect_to_merged_page(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")

    for legacy_route in ("longcat-api", "longcat-download"):
        page = (tmp_path / "offers" / legacy_route / "index.html").read_text(encoding="utf-8")
        assert 'http-equiv="refresh"' in page
        assert "/offers/longcat-2-0/" in page
