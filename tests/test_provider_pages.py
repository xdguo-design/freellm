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
    assert "Ollama Cloud" in page
    assert '9 <span lang="zh-CN">个模型</span>' in page
    assert '<link rel="canonical" href="https://freellm.top/providers/ollama-cloud/"' in ollama
    assert "deepseek-v4-pro" in ollama
    assert "目录发现" in ollama
    # Surface the freshness date that is actually in the catalog, derived from the data.
    # A hardcoded literal breaks on every crawler sync, because lastSeenAt is re-stamped.
    ollama_models = [m for m in _load_models(OFFERS_PATH) if m.get("providerId") == "ollama-cloud"]
    expected_freshness = {m["lastSeenAt"] for m in ollama_models if m.get("lastSeenAt")}
    assert expected_freshness, "fixture expectation: ollama-cloud must have catalog records"
    for seen_at in expected_freshness:
        assert seen_at in ollama
    assert "https://freellm.top/models/" in ollama
