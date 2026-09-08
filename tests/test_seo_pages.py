import json
from pathlib import Path

from scripts.build_seo_pages import (
    CATEGORY_DEFINITIONS,
    build_site,
    categorize_offer,
    category_url,
    guide_url,
    models_url,
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


def test_models_url_is_stable():
    assert models_url() == "/models/"


def test_offer_categories_match_existing_catalog_semantics():
    offers = {offer["id"]: offer for offer in read_offers()}

    assert "free-ide" in categorize_offer(offers["qoder"])
    assert "promo" in categorize_offer(offers["doubao"])
    assert "open-weights" in categorize_offer(offers["longcat-download"])
    assert "web" in categorize_offer(offers["tinyfish-search-fetch-free"])
    assert "student" in categorize_offer(offers["github-copilot-free"])


def test_stepfun_offer_covers_official_limited_free_models_and_api():
    offers = {offer["id"]: offer for offer in read_offers()}

    stepfun = offers["stepfun-limited-time-free"]
    assert stepfun["provider"] == "StepFun"
    assert stepfun["productType"] == "api"
    assert stepfun["freeMechanism"] == "limited_time_free"
    assert set(("api", "free")) <= set(stepfun["type"])
    for model_id in ("step-audio-r1.1", "step-1x-edit", "step-2x-large"):
        assert model_id in stepfun["model"]
    assert stepfun["usageGuide"]["endpoint"] == "https://api.stepfun.com/v1/chat/completions"
    assert stepfun["usageGuide"]["docsUrl"] == "https://platform.stepfun.com/docs/zh/quickstart/overview"
    assert "https://platform.stepfun.com/docs/zh/guides/pricing/details" in stepfun["sourceUrls"]
    assert "${STEP_API_KEY}" in stepfun["usageGuide"]["examples"]["curl"]
    assert "api" in categorize_offer(stepfun)


def test_agnes_ai_offer_covers_official_multimodal_models_and_free_api_access():
    offers = {offer["id"]: offer for offer in read_offers()}

    agnes = offers["agnes-ai-free"]
    assert agnes["provider"] == "Agnes AI"
    assert agnes["productType"] == "api"
    assert set(("api", "free")) <= set(agnes["type"])
    assert "model_api" in agnes["capabilities"]
    for model_id in (
        "agnes-2.5-flash",
        "agnes-image-2.1-flash",
        "agnes-video-v2.0",
    ):
        assert model_id in agnes["model"]
    assert agnes["usageGuide"]["endpoint"] == "https://apihub.agnes-ai.com/v1/chat/completions"
    assert agnes["usageGuide"]["docsUrl"] == "https://agnes-ai.com/en/docs/overview"
    assert any(url.startswith("https://github.com/AgnesAI-Labs/AgnesAI-Models") for url in agnes["sourceUrls"])
    assert "${AGNES_API_KEY}" in agnes["usageGuide"]["examples"]["curl"]
    assert "api" in categorize_offer(agnes)


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
    assert (tmp_path / "offers" / "agnes-ai-free" / "index.html").is_file()
    assert (tmp_path / "category" / "free-ide" / "index.html").is_file()
    assert (tmp_path / "models" / "index.html").is_file()
    assert (tmp_path / "guides" / "free-llm" / "index.html").is_file()
    assert (tmp_path / "guides" / "free-openai-api-alternatives" / "index.html").is_file()
    assert (tmp_path / "guides" / "claude-code-free-alternatives" / "index.html").is_file()

    detail = (tmp_path / "offers" / "codebuddy" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="zh-CN">' in detail
    assert "<title>CodeBuddy" in detail
    assert '<meta name="description"' in detail
    assert "请以官方页面为准" in detail
    assert '<link rel="canonical" href="https://freellm.top/offers/codebuddy/"' in detail
    assert '<meta property="og:image" content="https://freellm.top/freellm-01-hero.png">' in detail
    assert '<meta name="twitter:image" content="https://freellm.top/freellm-01-hero.png">' in detail
    assert 'window.va = window.va || function ()' in detail
    assert '<script defer src="/_vercel/insights/script.js"></script>' in detail
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
    assert '<script defer src="/_vercel/insights/script.js"></script>' in category
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
    assert '<script defer src="/_vercel/insights/script.js"></script>' in guide

    openai_guide = (tmp_path / "guides" / "free-openai-api-alternatives" / "index.html").read_text(encoding="utf-8")
    assert "OpenAI API alternatives" in openai_guide
    assert "OpenAI&#x27;s official API is not presented as permanently free" in openai_guide
    assert '<link rel="canonical" href="https://freellm.top/guides/free-openai-api-alternatives/"' in openai_guide
    assert "https://console.groq.com/docs/openai" in openai_guide

    claude_guide = (tmp_path / "guides" / "claude-code-free-alternatives" / "index.html").read_text(encoding="utf-8")
    assert "Free Claude Code Alternatives" in claude_guide
    assert "not Claude&#x27;s official free service" in claude_guide
    assert '<link rel="canonical" href="https://freellm.top/guides/claude-code-free-alternatives/"' in claude_guide
    assert "https://docs.bigmodel.cn/cn/coding-plan/faq" in claude_guide

    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://freellm.top/" in sitemap
    assert "https://freellm.top/offers/codebuddy/" in sitemap
    assert "https://freellm.top/offers/agnes-ai-free/" in sitemap
    assert "https://freellm.top/category/free-ide/" in sitemap
    assert "https://freellm.top/guides/free-llm/" in sitemap
    assert "https://freellm.top/guides/free-openai-api-alternatives/" in sitemap
    assert "https://freellm.top/guides/claude-code-free-alternatives/" in sitemap
    assert "https://freellm.top/models/" in sitemap
    assert sitemap.count("<loc>") == 5 + result.offer_count + result.category_count


def test_models_page_is_bilingual_directory_with_registration_links(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    offers = read_offers()
    page = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")

    assert '<html lang="zh-CN">' in page
    assert "全部免费 AI 模型与 API 一览" in page
    assert "All Free AI Models" in page
    assert '<link rel="canonical" href="https://freellm.top/models/"' in page
    assert '<meta property="og:image" content="https://freellm.top/freellm-01-hero.png">' in page
    assert 'window.va = window.va || function ()' in page
    assert "注册领取 Register ↗" in page
    assert "最后核验 last checked" in page

    # Every offer appears with its detail link and official registration URL.
    for offer in offers:
        assert offer_url(offer) in page
        if offer.get("register"):
            assert f'href="{offer["register"]}"' in page

    # Category sections use bilingual headers from the shared definitions.
    assert "免费额度 <span lang=\"en\">Free AI quota</span>" in page
    assert "开源权重模型 <span lang=\"en\">Open-weight AI models</span>" in page

    # Structured data lists every offer for crawlers.
    assert '"@type": "CollectionPage"' in page
    assert '"numberOfItems": %d' % len(offers) in page

    # The homepage and category pages link to the directory for crawl depth.
    homepage = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
    assert 'href="/models/"' in homepage
    category = (tmp_path / "category" / "free-ide" / "index.html").read_text(encoding="utf-8")
    assert "https://freellm.top/models/" in category


def test_build_site_check_detects_stale_output(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")

    assert build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top", check=True)
    sitemap = tmp_path / "sitemap.xml"
    sitemap.write_text(sitemap.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top", check=True)


def test_sensecore_offer_lists_token_plan_free_models():
    offers = {offer["id"]: offer for offer in read_offers()}

    sensecore = offers["sensecore"]
    assert sensecore["status"] == "verified"
    assert sensecore["cardRequired"] == "no"
    assert sensecore["register"] == "https://platform.sensenova.cn/token-plan"
    assert sensecore["usageGuide"]["endpoint"] == "https://token.sensenova.cn/v1/chat/completions"
    models = [entry["model"] for entry in sensecore["freeModels"]]
    assert models == ["sensenova-6.8-flash-lite", "sensenova-u1-fast"]
    assert all(entry["quota"].strip() for entry in sensecore["freeModels"])
    assert "https://www.sensenova.cn/token-plan" in sensecore["sourceUrls"]


def test_multi_model_offers_expose_free_models_lists():
    offers = {offer["id"]: offer for offer in read_offers()}

    stepfun_models = [entry["model"] for entry in offers["stepfun-limited-time-free"]["freeModels"]]
    assert stepfun_models == ["step-audio-r1.1", "step-1x-edit", "step-2x-large"]
    siliconflow_models = offers["siliconflow-free-models"]["freeModels"]
    assert len(siliconflow_models) == 6
    assert all(entry["quota"].strip() for entry in siliconflow_models)


def test_offer_page_renders_per_model_free_quota_table():
    from scripts.build_seo_pages import render_offer_page

    offers = read_offers()
    by_id = {offer["id"]: offer for offer in offers}
    html = render_offer_page(by_id["sensecore"], offers, "https://freellm.top")

    assert "免费模型逐个看" in html
    assert "sensenova-6.8-flash-lite" in html
    assert "sensenova-u1-fast" in html
    assert "60,000 积分 / 5 小时" in html

    plain = render_offer_page(by_id["doubao"], offers, "https://freellm.top")
    assert "免费模型逐个看" not in plain
