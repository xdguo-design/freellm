import json
from pathlib import Path

from scripts.build_seo_pages import (
    CATEGORY_DEFINITIONS,
    LEGACY_OFFER_REDIRECTS,
    _exclude_retired_models,
    _load_model_access,
    build_site,
    categorize_offer,
    category_url,
    guide_url,
    models_url,
    offer_url,
    render_category_page,
    render_models_page,
    render_offer_page,
    _expected_files,
    _adsense_slot_markup,
    render_daily_log_page,
)


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
MODELS_PATH = ROOT / "data" / "models.json"


def read_offers():
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


def read_models():
    return json.loads(MODELS_PATH.read_text(encoding="utf-8"))


def read_visible_models():
    return _exclude_retired_models(read_models(), _load_model_access(OFFERS_PATH))


THEME_GUIDES = {
    "free-openai-compatible-apis",
    "free-ai-coding-tools",
    "free-ai-search-apis",
    "open-weight-models",
    "model-context-windows",
    "china-free-ai-api",
}


def test_expected_files_include_theme_guides():
    files, _ = _expected_files(read_offers(), "https://freellm.top", read_models())
    generated = {path.parts[1] for path in files if path.parts[:1] == ("guides",)}
    assert THEME_GUIDES <= generated


def test_theme_guides_render_unique_metadata_and_verified_rows(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    for slug in THEME_GUIDES:
        page = (tmp_path / "guides" / slug / "index.html").read_text(encoding="utf-8")
        assert page.count("<h1>") == 1
        assert f"https://freellm.top/guides/{slug}/" in page
        assert '<meta name="description"' in page
        assert "adsbygoogle.js?client=ca-pub-2461062743308239" in page


def test_context_window_guide_exposes_model_parameters(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "guides" / "model-context-windows" / "index.html").read_text(encoding="utf-8")
    assert "Context window" in page
    assert "tokens" in page
    assert "source" in page.lower()


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
    longcat = offers["longcat-2-0"]
    assert "longcat-api" not in offers
    assert "longcat-download" not in offers
    assert {path["id"] for path in longcat["accessPaths"]} == {"api", "open_weights"}
    assert {"api", "open-weights"}.issubset(set(categorize_offer(longcat)))
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


def test_longcat_page_renders_both_access_paths():
    from scripts.build_seo_pages import render_offer_page

    offers = read_offers()
    by_id = {offer["id"]: offer for offer in offers}
    page = render_offer_page(by_id["longcat-2-0"], offers, "https://freellm.top")

    assert page.count("LongCat-2.0") >= 3
    assert "API 调用" in page
    assert "下载权重" in page
    assert "免费额度未确认" in page
    assert "权重免费，算力不免费" in page


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

    adsense_script = 'adsbygoogle.js?client=ca-pub-2461062743308239'
    for generated_page in (detail, category, guide):
        assert adsense_script in generated_page

    openai_guide = (tmp_path / "guides" / "free-openai-api-alternatives" / "index.html").read_text(encoding="utf-8")
    assert "OpenAI API alternatives" in openai_guide
    assert "OpenAI&#x27;s official API is not presented as permanently free" in openai_guide
    assert '<link rel="canonical" href="https://freellm.top/guides/free-openai-api-alternatives/"' in openai_guide
    assert "https://console.groq.com/docs/openai" in openai_guide
    assert adsense_script in openai_guide

    claude_guide = (tmp_path / "guides" / "claude-code-free-alternatives" / "index.html").read_text(encoding="utf-8")
    assert "Free Claude Code Alternatives" in claude_guide
    assert "not Claude&#x27;s official free service" in claude_guide
    assert '<link rel="canonical" href="https://freellm.top/guides/claude-code-free-alternatives/"' in claude_guide
    assert "https://docs.bigmodel.cn/cn/coding-plan/faq" in claude_guide
    assert adsense_script in claude_guide

    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://freellm.top/" in sitemap
    assert "https://freellm.top/offers/codebuddy/" in sitemap
    assert "https://freellm.top/offers/agnes-ai-free/" in sitemap
    assert "https://freellm.top/category/free-ide/" in sitemap
    assert "https://freellm.top/guides/free-llm/" in sitemap
    assert "https://freellm.top/guides/free-openai-api-alternatives/" in sitemap
    assert "https://freellm.top/guides/claude-code-free-alternatives/" in sitemap
    assert "https://freellm.top/models/" in sitemap
    assert "https://freellm.top/models/center/" in sitemap
    # page_count includes sitemap.xml itself but excludes the three static legal
    # pages (about/terms/privacy), which are hand-maintained and only referenced in the sitemap.
    static_legal_pages = 3
    assert sitemap.count("<loc>") == result.page_count - len(LEGACY_OFFER_REDIRECTS) + static_legal_pages
    for legal_path in ("/about/", "/terms/", "/privacy/"):
        assert f"https://freellm.top{legal_path}" in sitemap


def test_models_page_is_bilingual_directory_with_registration_links(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    offers = read_offers()
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    assert '<html lang="zh-CN">' in page
    assert "全部免费 AI 模型与 API 一览" in page
    assert "All Free AI Models" in page
    assert '<link rel="canonical" href="https://freellm.top/models/all/"' in page
    assert '<meta property="og:image" content="https://freellm.top/freellm-01-hero.png">' in page
    assert 'window.va = window.va || function ()' in page
    assert '<span lang="zh-CN">注册领取</span><span lang="en">Register</span>' in page
    assert '<span lang="zh-CN">模型同步</span><span lang="en">Models synced</span>' in page
    assert '<span lang="zh-CN">资源核验</span><span lang="en">Offers checked</span>' in page

    # Every offer appears with its detail link and official registration URL.
    for offer in offers:
        assert offer_url(offer) in page
        if offer.get("register"):
            assert f'href="{offer["register"]}"' in page

    # Category sections use bilingual headers from the shared definitions.
    assert '<span lang="zh-CN">免费额度</span><span lang="en">Free AI quota</span>' in page
    assert '<span lang="zh-CN">开源权重模型</span><span lang="en">Open-weight AI models</span>' in page

    # Structured data lists every visible catalog model for crawlers.
    assert '"@type": "CollectionPage"' in page
    assert '"numberOfItems": %d' % len(read_visible_models()) in page
    expected_date_modified = max(
        [model["lastSeenAt"] for model in models]
        + [offer["lastVerifiedAt"] for offer in offers]
    )
    assert '"dateModified": "%s"' % expected_date_modified in page

    # The homepage and category pages link to the directory for crawl depth.
    homepage = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
    assert 'href="/models/"' in homepage
    assert 'href="/models/all/"' in homepage
    assert 'href="/providers/"' in homepage
    category = (tmp_path / "category" / "free-ide" / "index.html").read_text(encoding="utf-8")
    assert "https://freellm.top/models/" in category


def test_model_directory_intents_have_distinct_metadata_and_hreflang(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    resource_directory = (tmp_path / "models" / "index.html").read_text(encoding="utf-8")
    all_models = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")

    title = lambda page: page.split("<title>", 1)[1].split("</title>", 1)[0]
    description = lambda page: page.split('<meta name="description" content="', 1)[1].split('">', 1)[0]
    assert title(resource_directory) != title(all_models)
    assert description(resource_directory) != description(all_models)
    for page, canonical in (
        (resource_directory, "https://freellm.top/models/"),
        (all_models, "https://freellm.top/models/all/"),
    ):
        assert f'<link rel="alternate" hreflang="zh-CN" href="{canonical}"' in page
        assert f'<link rel="alternate" hreflang="en" href="{canonical}?lang=en"' in page
        assert f'<link rel="alternate" hreflang="x-default" href="{canonical}"' in page


def test_all_bilingual_html_pages_emit_hreflang_links(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")

    pages = [
        tmp_path / "offers" / "codebuddy" / "index.html",
        tmp_path / "models" / "all" / "index.html",
        tmp_path / "category" / "free-ide" / "index.html",
        tmp_path / "guides" / "free-llm" / "index.html",
        tmp_path / "providers" / "index.html",
        tmp_path / "providers" / "agnes-ai" / "index.html",
    ]

    for page_path in pages:
        page = page_path.read_text(encoding="utf-8")
        canonical = page.split('<link rel="canonical" href="', 1)[1].split('"', 1)[0]
        assert page.count('rel="alternate" hreflang="zh-CN"') == 1
        assert page.count('rel="alternate" hreflang="en"') == 1
        assert page.count('rel="alternate" hreflang="x-default"') == 1
        assert f'<link rel="alternate" hreflang="zh-CN" href="{canonical}"' in page
        assert f'<link rel="alternate" hreflang="en" href="{canonical}?lang=en"' in page
        assert f'<link rel="alternate" hreflang="x-default" href="{canonical}"' in page


def test_explicit_adsense_slot_is_opt_in():
    markup = _adsense_slot_markup("1234567890")
    assert 'data-ad-client="ca-pub-2461062743308239"' in markup
    assert 'data-ad-slot="1234567890"' in markup
    assert ".push({})" in markup
    assert _adsense_slot_markup("") == ""
    assert _adsense_slot_markup("not-a-slot") == ""


def _all_catalog_pages(tmp_path) -> str:
    """Concatenate every paginated model-catalog page (page 1 + page/2..N)."""
    base = tmp_path / "models" / "all"
    pages = [base / "index.html"]
    pages.extend(sorted(base.glob("page/*/index.html")))
    return "".join(page.read_text(encoding="utf-8") for page in pages if page.is_file())


def test_models_page_renders_queryable_provider_model_catalog(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "models" / "all" / "index.html").read_text(encoding="utf-8")
    all_pages = _all_catalog_pages(tmp_path)
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))

    assert 'id="model-catalog-search"' in page
    assert 'id="model-catalog-provider"' in page
    assert 'data-group-mode="provider"' in page
    assert 'data-group-mode="model"' in page
    assert f'{len(read_visible_models())} 个模型' in page
    # The catalog is paginated; ollama-cloud lives beyond page one, so scan all
    # pages — the queryable catalog contract must hold on every page.
    assert 'data-model-id="ollama-cloud/deepseek-v4-pro"' in all_pages
    assert 'Ollama Cloud' in all_pages
    assert 'deepseek-v4-pro' in all_pages
    assert 'Score' in page
    assert '目录来源' in page


def test_static_seo_pages_can_follow_the_saved_locale_without_mixed_visible_copy(tmp_path):
    offers = [
        {
            "id": "example",
            "title": "Example English title",
            "titleZh": "示例中文标题",
            "provider": "Example",
            "providerMeta": "示例供应商",
            "providerMetaEn": "International provider",
            "freeSummary": "中文免费额度说明",
            "freeSummaryEn": "Recurring free quota",
            "validitySummary": "长期有效",
            "validitySummaryEn": "Ongoing access",
            "accessSummary": "需要注册",
            "accessSummaryEn": "Registration required",
            "freeMechanism": "monthly_quota",
            "productType": "api",
            "type": ["api"],
            "badges": ["FREE"],
            "register": "https://example.com/register",
            "order": 1,
        }
    ]

    category = render_category_page("free-quota", offers, "https://freellm.top")
    models = render_models_page(offers, "https://freellm.top")
    detail = render_offer_page(offers[0], offers, "https://freellm.top")

    for page in (category, models, detail):
        assert 'data-static-locale="true"' in page
        assert 'html[data-locale="en"] [lang="zh-CN"]' in page
        assert 'html[data-locale="zh-CN"] [lang="en"]' in page
        assert 'href="?lang=en"' in page
        assert 'href="?lang=zh"' in page

    assert '<span lang="zh-CN">免费额度</span><span lang="en">Free AI quota</span>' in category
    assert '<span lang="zh-CN">示例中文标题</span><span lang="en">Example English title</span>' in models
    assert '<span lang="zh-CN">这个资源提供什么</span><span lang="en">What this offer provides</span>' in detail
    assert "中文免费额度说明 / Recurring free quota" not in category


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


def test_groq_models_are_structured_with_individual_context_windows():
    offers = {offer["id"]: offer for offer in read_offers()}
    groq = offers["groq-free"]

    expected_models = {
        "canopylabs/orpheus-arabic-saudi",
        "canopylabs/orpheus-v1-english",
        "groq/compound",
        "groq/compound-mini",
        "meta-llama/llama-prompt-guard-2-22m",
        "meta-llama/llama-prompt-guard-2-86m",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-safeguard-20b",
        "qwen/qwen3.6-27b",
        "qwen/qwen3.8-27b",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
    }

    free_models = groq["freeModels"]
    assert {entry["model"] for entry in free_models} == expected_models
    assert len(free_models) == len(expected_models)
    assert all(entry["contextWindow"].strip() for entry in free_models)
    assert all(entry["quota"].strip() for entry in free_models)


def test_offer_page_renders_per_model_free_quota_table():
    from scripts.build_seo_pages import render_offer_page

    offers = read_offers()
    by_id = {offer["id"]: offer for offer in offers}
    html = render_offer_page(by_id["sensecore"], offers, "https://freellm.top")

    assert "免费模型逐个看" in html
    assert "sensenova-6.8-flash-lite" in html
    assert "sensenova-u1-fast" in html
    assert "60,000 积分 / 5 小时" in html

    groq_html = render_offer_page(by_id["groq-free"], offers, "https://freellm.top")
    assert "上下文窗口" in groq_html
    assert '<a href="https://console.groq.com/docs/models"' in groq_html
    assert "131,072 tokens" in groq_html
    assert "512 tokens" in groq_html
    assert groq_html.count("<tr>") >= 14
    assert '<span lang="en">openai/gpt-oss-120b</span> ↗</a>' in groq_html
    assert '<span lang="en">qwen/qwen3.8-27b</span> ↗</a>' in groq_html

    plain = render_offer_page(by_id["doubao"], offers, "https://freellm.top")
    assert "免费模型逐个看" not in plain


def test_daily_log_page_expands_new_entries_with_detailed_access_and_evidence_fields():
    logs = [{
        "schemaVersion": 1,
        "date": "2026-09-10",
        "baseline": False,
        "events": [{
            "kind": "offer",
            "eventType": "new",
            "id": "alpha",
            "title": "Alpha free API",
            "asOf": "2026-09-10",
            "details": {
                "provider": "Alpha",
                "productType": "api",
                "freeMechanism": "monthly_quota",
                "quota": "100 requests/day",
                "validity": "Monthly",
                "access": "Global",
                "phoneRequired": "no",
                "cardRequired": "no",
                "register": "https://alpha.example/register",
                "sourceUrls": ["https://alpha.example/pricing"],
                "registrationSteps": ["打开注册入口", "创建账号", "生成 API Key"],
                "links": [["注册文档", "https://alpha.example/docs/signup"]],
                "evidence": "Official pricing documents a free tier.",
                "status": "verified",
            },
        }],
        "observed": {"models": [], "offers": []},
        "known": {"models": [], "offers": []},
        "sourceHealth": {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    }]

    page = render_daily_log_page(logs, "https://freellm.top")

    assert "今天的 AI 资源有什么变化？" in page
    assert "Alpha free API" in page
    assert "monthly_quota" in page
    assert "100 requests/day" in page
    assert "https://alpha.example/pricing" in page
    assert "Official pricing documents a free tier." in page
    assert "phoneRequired" in page
    assert "注册与文档" in page
    assert "创建账号" in page
    assert "https://alpha.example/docs/signup" in page
    assert "/logs/" in page


def test_daily_log_dashboard_renders_baseline_snapshot_and_health():
    logs = [{
        "schemaVersion": 1,
        "date": "2026-09-10",
        "baseline": True,
        "events": [],
        "observed": {
            "models": [
                {"providerId": f"provider-{index % 25}", "model": f"model-{index}"}
                for index in range(297)
            ],
            "offers": [{"id": f"offer-{index}"} for index in range(37)],
        },
        "known": {"models": [], "offers": []},
        "sourceHealth": {
            "models": {"status": "ok"},
            "offers": {"status": "ok"},
        },
    }]

    page = render_daily_log_page(logs, "https://freellm.top")

    assert 'class="daily-log-dashboard"' in page
    assert 'class="log-hero"' in page
    assert page.count('class="log-stat-card ') == 4
    assert "首次基线" in page
    assert "297" in page
    assert "25" in page
    assert "37" in page
    assert "模型源" in page and "正常" in page
    assert "资源源" in page and "正常" in page
    assert "今日扫描完成" in page
    assert ".log-days::before" in page
    assert "class=\"log-registration\"" not in page
    assert "首次建立基线" not in page
    assert "class=\"log-empty baseline-empty\"" not in page


def test_daily_log_dashboard_distinguishes_no_change_from_baseline_and_lists_dates():
    logs = [
        {
            "schemaVersion": 1,
            "date": "2026-09-10",
            "baseline": False,
            "events": [],
            "observed": {"models": [], "offers": []},
            "sourceHealth": {"models": {"status": "ok"}, "offers": {"status": "ok"}},
        },
        {
            "schemaVersion": 1,
            "date": "2026-09-09",
            "baseline": False,
            "events": [],
            "observed": {"models": [], "offers": []},
            "sourceHealth": {"models": {"status": "ok"}, "offers": {"status": "ok"}},
        },
    ]

    page = render_daily_log_page(logs, "https://freellm.top")

    assert "今日扫描完成，未发现变化" in page
    assert "首次建立基线" not in page
    assert 'class="log-date-nav"' in page
    assert "2026-09-10" in page
    assert "2026-09-09" in page


def test_daily_log_dashboard_renders_curated_additions_on_timeline():
    page = render_daily_log_page([{
        "schemaVersion": 1,
        "date": "2026-09-10",
        "baseline": True,
        "events": [],
        "curatedEvents": [{
            "kind": "offer",
            "eventType": "new",
            "curated": True,
            "id": "manus-free-agent",
            "title": "Manus AI · 免费 Agent 计划",
            "reason": "人工确认新增",
            "details": {
                "provider": "Manus AI",
                "register": "https://manus.im/login?type=signUp",
                "registrationSteps": ["打开 Manus 注册入口", "选择登录方式"],
                "sourceUrls": ["https://open.manus.ai/docs/v2/introduction"],
            },
        }],
        "observed": {"models": [], "offers": []},
        "sourceHealth": {"models": {"status": "ok"}, "offers": {"status": "ok"}},
    }], "https://freellm.top")

    assert "首次建立基线，以下为人工确认新增" not in page
    assert "Curated new" in page
    assert "Manus AI" in page
    assert "注册与文档" in page
    assert '<details class="log-new-card">' in page
    assert '<summary class="log-card-summary">' in page
    assert 'class="log-card-body"' in page
    assert '<details class="log-new-card" open>' not in page
    assert '.log-event-grid { display:grid; grid-template-columns:1fr; gap:12px; }' in page
    assert ".log-days::before" in page


def test_expected_files_and_sitemap_include_daily_logs(tmp_path):
    files, _ = _expected_files(read_offers(), "https://freellm.top", read_models())
    assert Path("logs/index.html") in files

    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://freellm.top/logs/" in sitemap
