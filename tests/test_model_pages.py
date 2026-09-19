import json
import re
from pathlib import Path

from scripts.build_seo_pages import (
    _exclude_retired_models,
    _load_model_access,
    _model_catalog_row,
    build_site,
    model_record_groups,
)


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
MODELS_PATH = ROOT / "data" / "models.json"


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


def test_model_rows_link_to_local_aggregation_pages(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    models = _exclude_retired_models(
        json.loads(MODELS_PATH.read_text(encoding="utf-8")),
        _load_model_access(OFFERS_PATH),
    )
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")
    all_pages = _all_catalog_pages(tmp_path)

    assert re.findall(r'href="/models/[a-z0-9-]+/"', page)
    # The catalog is paginated, so the first row and a provider that lives beyond
    # page one must both resolve somewhere in the paginated catalog pages.
    first_model_href = f'href="/models/{model_slug(models[0]["model"])}/"'
    assert first_model_href in all_pages
    last_provider_href = f'href="/providers/{model_slug(models[-1].get("providerId"))}/"'
    assert last_provider_href in all_pages


def test_new_model_directory_is_additive_and_preserves_previous_models_page(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    previous_page = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")
    all_models_page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert "card-grid" in previous_page
    assert "模型大列表" not in previous_page
    assert "实时模型目录" in all_models_page
    retired_ids = {
        card["modelId"]
        for card in json.loads((ROOT / "data" / "model-access.json").read_text(encoding="utf-8"))
        if card["accessStatus"] == "retired"
    }
    visible_models = sum(model["id"] not in retired_ids for model in json.loads(MODELS_PATH.read_text(encoding="utf-8")))
    assert str(visible_models) in all_models_page


def test_model_center_combines_original_feature_page_and_model_directory_tabs(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "center" / "index.html").read_text(encoding="utf-8")
    original_home = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")

    assert '<html lang="zh-CN" data-default-locale="zh-CN">' in page
    assert 'id="model-center-tab-featured"' in page
    assert 'id="model-center-tab-all-models"' in page
    assert 'aria-controls="categories"' in page
    assert 'id="model-center-all-models-panel"' in page
    assert "url.hash = 'all-models'" in page
    assert "发现真正好用的" in page
    assert "模型大列表" not in page
    assert "model-center-all-heading" not in page
    assert "02 / 全部模型" not in page
    assert 'id="model-directory"' in page
    assert "const syncLocale = () => {{" not in page
    assert "new MutationObserver(syncLocale).observe(document.documentElement, {{" not in page
    assert page.index('class="model-center-tabs"') < page.index('id="model-directory"')
    assert 'href="/models/center/"' in original_home
    assert "发现真正好用的" in original_home
    assert 'data-nav-key="model-center"' in original_home
    assert 'data-i18n="resourceDirectory"' in original_home
    assert page.index('class="catalog-hero"') < page.index('class="model-center-tabs"')
    assert page.index('class="model-center-tabs"') < page.index('id="model-center-all-models-panel"')
    assert page.index('id="model-center-all-models-panel"') < page.index('id="categories"')


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
    assert "#1744E8" in (ROOT / "scripts" / "build_seo_pages.py").read_text(encoding="utf-8")


def test_model_directory_shows_activity_column_and_clear_result_count(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert "中国大陆可用性" in page
    assert "显示" in page
    assert "共" in page
    assert "Catalog source" in page
    assert "Showing ${visible.length} / ${pairs.length}" in page


def test_model_center_tabs_are_localized_and_model_catalog_uses_gradient_score(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "center" / "index.html").read_text(encoding="utf-8")

    assert '<span lang="zh-CN">精选资源</span><span lang="en">Featured resources</span>' in page
    assert '<span lang="zh-CN">全部模型</span><span lang="en">All models</span>' in page
    assert "#1744E8" in page
    assert "Catalog source" in page


def test_previous_longcat_routes_redirect_to_merged_page(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")

    for legacy_route in ("longcat-api", "longcat-download"):
        page = (tmp_path / "offers" / legacy_route / "index.html").read_text(encoding="utf-8")
        assert 'http-equiv="refresh"' in page
        assert "/offers/longcat-2-0/" in page
