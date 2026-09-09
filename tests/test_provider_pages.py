import json
from pathlib import Path

from scripts.build_seo_pages import build_site


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
PROVIDERS_PATH = ROOT / "data" / "provider-catalog.json"


def test_build_site_creates_provider_directory_and_detail_pages(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    providers = json.loads(PROVIDERS_PATH.read_text(encoding="utf-8"))
    page = (tmp_path / "providers" / "index.html").read_text(encoding="utf-8")
    ollama = (tmp_path / "providers" / "ollama-cloud" / "index.html").read_text(encoding="utf-8")

    assert f'{len(providers)} 家厂商' in page
    assert 'href="/providers/ollama-cloud/"' in page
    assert "Ollama Cloud" in page
    assert '9 <span lang="zh-CN">个模型</span>' in page
    assert '<link rel="canonical" href="https://freellm.top/providers/ollama-cloud/"' in ollama
    assert "deepseek-v4-pro" in ollama
    assert "目录发现" in ollama
    assert "2026-09-09" in ollama
    assert "https://freellm.top/models/" in ollama
