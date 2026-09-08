import json
from pathlib import Path

from scripts.build_seo_pages import (
    CATEGORY_DEFINITIONS,
    build_site,
    categorize_offer,
    category_url,
    guide_url,
    offer_url,
)


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"


def read_offers():
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


def test_offer_and_category_urls_are_stable_crawlable_paths():
    offers = read_offers()

    assert offer_url(offers[0]) == "/offers/codebuddy/"
    assert all(url.startswith("/offers/") and url.endswith("/") for url in map(offer_url, offers))
    assert category_url("free-ide") == "/category/free-ide/"
    assert all(slug.islower() for slug in CATEGORY_DEFINITIONS)


def test_guide_url_is_stable():
    assert guide_url() == "/guides/free-llm/"


def test_offer_categories_match_existing_catalog_semantics():
    offers = {offer["id"]: offer for offer in read_offers()}

    assert "free-ide" in categorize_offer(offers["qoder"])
    assert "promo" in categorize_offer(offers["doubao"])
    assert "open-weights" in categorize_offer(offers["longcat-download"])
    assert "web" in categorize_offer(offers["tinyfish-search-fetch-free"])
    assert "student" in categorize_offer(offers["github-copilot-free"])


def test_build_site_generates_indexable_detail_category_pages_and_sitemap(tmp_path):
    result = build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    offers = read_offers()
    non_empty_categories = {
        category
        for offer in offers
        for category in categorize_offer(offer)
    }

    assert result.offer_count == len(offers)
    assert result.category_count == len(non_empty_categories)
    assert (tmp_path / "offers" / "codebuddy" / "index.html").is_file()
    assert (tmp_path / "category" / "free-ide" / "index.html").is_file()
    assert (tmp_path / "guides" / "free-llm" / "index.html").is_file()

    detail = (tmp_path / "offers" / "codebuddy" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="zh-CN">' in detail
    assert "<title>CodeBuddy" in detail
    assert '<meta name="description"' in detail
    assert "请以官方页面为准" in detail
    assert '<link rel="canonical" href="https://freellm.top/offers/codebuddy/"' in detail
    assert '<meta property="og:image" content="https://freellm.top/freellm-01-hero.png">' in detail
    assert '<meta name="twitter:image" content="https://freellm.top/freellm-01-hero.png">' in detail
    assert 'data-offer-id="codebuddy"' in detail
    assert "https://www.codebuddy.cn/" in detail
    assert "/category/free-ide/" in detail

    qwen_detail = (tmp_path / "offers" / "qwen-download" / "index.html").read_text(encoding="utf-8")
    assert "上下文窗口" in qwen_detail
    assert "原生 32K" in qwen_detail
    assert "YaRN 131K" in qwen_detail

    category = (tmp_path / "category" / "free-ide" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="zh-CN">' in category
    assert "免费 AI IDE" in category
    assert '<link rel="canonical" href="https://freellm.top/category/free-ide/"' in category
    assert '<meta property="og:image" content="https://freellm.top/freellm-01-hero.png">' in category
    assert '<meta name="twitter:image" content="https://freellm.top/freellm-01-hero.png">' in category
    assert "/offers/codebuddy/" in category
    assert 'href="https://freellm.top/"' in category

    guide = (tmp_path / "guides" / "free-llm" / "index.html").read_text(encoding="utf-8")
    assert "为什么需要这个项目" in guide
    assert "Quick Start" in guide
    assert "Quick Reference" in guide
    assert "https://github.com/nejib1/Free-LLM/blob/main/README.zh-CN.md" in guide
    assert "MIT License" in guide
    assert '<link rel="canonical" href="https://freellm.top/guides/free-llm/"' in guide
    assert '<meta property="og:image" content="https://freellm.top/freellm-01-hero.png">' in guide
    assert '<meta name="twitter:image" content="https://freellm.top/freellm-01-hero.png">' in guide

    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://freellm.top/" in sitemap
    assert "https://freellm.top/offers/codebuddy/" in sitemap
    assert "https://freellm.top/category/free-ide/" in sitemap
    assert "https://freellm.top/guides/free-llm/" in sitemap
    assert sitemap.count("<loc>") == 2 + result.offer_count + result.category_count


def test_build_site_check_detects_stale_output(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")

    assert build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top", check=True)
    sitemap = tmp_path / "sitemap.xml"
    sitemap.write_text(sitemap.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top", check=True)
