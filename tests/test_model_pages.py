import json
import re
from pathlib import Path

from scripts.build_seo_pages import _model_catalog_row, build_site


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
MODELS_PATH = ROOT / "data" / "models.json"


def model_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def test_build_site_creates_model_aggregation_pages(tmp_path):
    result = build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    duplicate_models = {
        model_slug(model["model"])
        for model in models
        if sum(item["model"].lower() == model["model"].lower() for item in models) > 1
    }

    assert len(duplicate_models) >= 10
    assert result.page_count >= 49 + len(duplicate_models)

    page = (tmp_path / "models" / "llama-3-1-70b" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://freellm.top/models/llama-3-1-70b/"' in page
    assert "Llama 3.1 70B" in page
    assert "Chutes.ai" in page
    assert "Cerebras" in page
    assert "目录发现" in page
    assert "2026-09-09" in page
    assert '"@type": "ItemList"' in page


def test_model_rows_link_to_local_aggregation_pages(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert 'href="/models/llama-3-1-70b/"' in page
    assert 'href="/models/longcat-2-0/"' in page
    assert 'href="/providers/ollama-cloud/"' in page


def test_new_model_directory_is_additive_and_preserves_previous_models_page(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    previous_page = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")
    all_models_page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert "card-grid" in previous_page
    assert "模型大列表" not in previous_page
    assert "模型大列表" in all_models_page
    assert "296" in all_models_page


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


def test_model_rows_render_score_as_a_circular_indicator():
    row = _model_catalog_row({
        "id": "alpha/model",
        "providerId": "alpha",
        "provider": "Alpha",
        "model": "model",
        "score": 94,
        "sourceUrl": "https://directory.example/model",
    })
    assert 'class="score-ring"' in row
    assert "--score:94" in row
    assert 'aria-label="Score 94"' in row
    assert "#7c3aed" in (ROOT / "scripts" / "build_seo_pages.py").read_text(encoding="utf-8")


def test_model_directory_shows_activity_column_and_clear_result_count(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert "Usage / Activity" in page
    assert "显示" in page
    assert "共" in page
    assert "Catalog source" in page
    assert "Showing ${visible.length} / ${rows.length}" in page


def test_model_center_tabs_are_localized_and_model_catalog_uses_gradient_score(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "center" / "index.html").read_text(encoding="utf-8")

    assert '<span lang="zh-CN">精选资源</span><span lang="en">Featured resources</span>' in page
    assert '<span lang="zh-CN">全部模型</span><span lang="en">All models</span>' in page
    assert "#7c3aed" in page
    assert "Catalog source" in page


def test_previous_longcat_routes_redirect_to_merged_page(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")

    for legacy_route in ("longcat-api", "longcat-download"):
        page = (tmp_path / "offers" / legacy_route / "index.html").read_text(encoding="utf-8")
        assert 'http-equiv="refresh"' in page
        assert "/offers/longcat-2-0/" in page
