from pathlib import Path

from scripts.build_seo_pages import _exclude_retired_models, _load_model_access, _load_operations, _load_models, _provider_catalog_from_models, build_site


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"


def visible_providers() -> list[dict]:
    """Providers generated from the current model catalog and operation guides."""
    models = _exclude_retired_models(_load_models(OFFERS_PATH), _load_model_access(OFFERS_PATH))
    return _provider_catalog_from_models(models, _load_operations(OFFERS_PATH))


def test_build_site_creates_provider_directory_and_detail_pages(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "providers" / "index.html").read_text(encoding="utf-8")
    ollama = (tmp_path / "providers" / "ollama-cloud" / "index.html").read_text(encoding="utf-8")

    assert f'{len(visible_providers())} 家厂商' in page
    assert 'href="/providers/ollama-cloud/"' in page
    provider_names = {provider["id"]: provider.get("name") for provider in visible_providers()}
    assert provider_names["ollama-cloud"] in page
    # Derive the per-provider model count from the catalog instead of a literal:
    # every crawler sync shifts these numbers.
    models = _exclude_retired_models(_load_models(OFFERS_PATH), _load_model_access(OFFERS_PATH))
    ollama_model_count = sum(1 for model in models if model.get("providerId") == "ollama-cloud")
    assert f'{ollama_model_count} <span lang="zh-CN">个模型</span>' in page
    assert '<link rel="canonical" href="https://freellm.top/providers/ollama-cloud/"' in ollama
    assert "deepseek-v4-pro" in ollama
    assert "全部模型记录" in ollama
    # Surface the freshness date that is actually in the catalog, derived from the data.
    # A hardcoded literal breaks on every crawler sync, because lastSeenAt is re-stamped.
    ollama_models = [m for m in _load_models(OFFERS_PATH) if m.get("providerId") == "ollama-cloud"]
    expected_freshness = {m["lastSeenAt"] for m in ollama_models if m.get("lastSeenAt")}
    assert expected_freshness, "fixture expectation: ollama-cloud must have catalog records"
    for seen_at in expected_freshness:
        assert seen_at in ollama
    assert "https://freellm.top/models/" in ollama
