"""End-to-end checks: HTML/data contract, daily workflow, and page behavior.

The Playwright tests run against a local browser when available and skip
cleanly otherwise (CI uses the zero-install stdlib policy).
"""

import base64
import json
import re
import threading
import tempfile
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "design" / "free-china-ai-index.html"
HOMEPAGE_CSS_PATH = ROOT / "css" / "homepage.css"
HOMEPAGE_EDITORIAL_CSS_PATH = ROOT / "css" / "homepage-editorial.css"
HOMEPAGE_JS_PATH = ROOT / "js" / "homepage.js"
HOMEPAGE_I18N_JS_PATH = ROOT / "js" / "homepage-i18n.js"
OFFERS_PATH = ROOT / "data" / "offers.json"
OFFERS_RANKED_PATH = ROOT / "data" / "offers-ranked.json"
OFFERS_BUNDLE_PATH = ROOT / "data" / "offers.js"
SIGNALS_PATH = ROOT / "data" / "community-signals.json"
ROBOTS_PATH = ROOT / "robots.txt"
SITEMAP_PATH = ROOT / "sitemap.xml"
ADS_PATH = ROOT / "ads.txt"
GUIDE_PATH = ROOT / "guides" / "free-llm" / "index.html"
LOG_PATH = ROOT / "logs" / "index.html"
SUBMIT_PATH = ROOT / "submit" / "index.html"


def read_offers() -> list:
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


def read_ranked_offers() -> list:
    return json.loads(OFFERS_RANKED_PATH.read_text(encoding="utf-8"))


def read_signals() -> list:
    return json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))


def bundled_offer_data() -> list:
    source = OFFERS_BUNDLE_PATH.read_text(encoding="utf-8").strip()
    prefix = "window.FREELLM_OFFERS = "
    if not source.startswith(prefix) or not source.endswith(";"):
        raise AssertionError("data/offers.js has an unexpected wrapper")
    return json.loads(source[len(prefix):-1])


class StaticContractTests(unittest.TestCase):
    def setUp(self):
        self.document_html = HTML_PATH.read_text(encoding="utf-8")
        self.homepage_css = HOMEPAGE_CSS_PATH.read_text(encoding="utf-8")
        self.homepage_editorial_css = HOMEPAGE_EDITORIAL_CSS_PATH.read_text(encoding="utf-8")
        self.homepage_js = HOMEPAGE_JS_PATH.read_text(encoding="utf-8")
        self.homepage_i18n_js = HOMEPAGE_I18N_JS_PATH.read_text(encoding="utf-8")
        self.offer_bundle = OFFERS_BUNDLE_PATH.read_text(encoding="utf-8")
        self.html = "\n".join((
            self.document_html,
            self.homepage_css,
            self.homepage_editorial_css,
            self.homepage_js,
            self.homepage_i18n_js,
            self.offer_bundle,
        ))
        self.runtime_source = self.html

    def test_external_offer_bundle_matches_ranked_runtime_json(self):
        self.assertEqual(bundled_offer_data(), read_ranked_offers())
        self.assertEqual(
            {item["id"] for item in read_ranked_offers()},
            {item["id"] for item in read_offers()},
        )

    def test_page_has_required_data_hooks(self):
        for needle in (
            'id="catalog-offer-rows"', 'id="catalog-search"',
            'id="catalog-sort"', 'id="catalog-result-count"', 'id="ld-dynamic"',
            "renderOffers", "loadOffers", "showDataError",
            'id="studentList"', 'id="catalog-download-list"', 'id="catalog-last-checked"',
            "offerCategories", "timeWindow",
        ):
            self.assertIn(needle, self.runtime_source)
        for pattern in (
            r'\.\./css/homepage\.[0-9a-f]{10}\.css',
            r'\.\./css/homepage-editorial\.[0-9a-f]{10}\.css',
            r'\.\./js/homepage\.[0-9a-f]{10}\.js',
            r'\.\./js/homepage-i18n\.[0-9a-f]{10}\.js',
        ):
            self.assertRegex(self.document_html, pattern)
        offer_ids = {item["id"] for item in bundled_offer_data()}
        self.assertTrue({"doubao", "aliyun-qwen-free-quota", "agnes-ai-free", "stepfun-limited-time-free", "longcat-2-0"} <= offer_ids)
        self.assertNotIn("longcat-api", offer_ids)
        self.assertNotIn("longcat-download", offer_ids)

    def test_third_party_network_scripts_are_deferred(self):
        self.assertNotIn(
            '<script async src="https://www.googletagmanager.com/gtag/js',
            self.document_html,
        )
        self.assertNotIn(
            '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js',
            self.document_html,
        )
        self.assertIn("requestIdleCallback", self.document_html)
        self.assertIn(
            "https://www.googletagmanager.com/gtag/js?id=G-JMK4R9519M",
            self.document_html,
        )
        self.assertIn(
            "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2461062743308239",
            self.document_html,
        )
        self.assertIn("if (!slot) return;", self.document_html)

    def test_homepage_exposes_real_action_and_filter_hooks(self):
        for needle in (
            'href="/submit/"',
            "document.write('<script src=\"/js/freellm-sync.js\"><\\/script>')",
            'id="catalog-method-filter"',
            'id="catalog-capability-filter"',
            'id="catalog-freshness-filter"',
            'data-region-chip="china"',
            'data-region-chip="global"',
            'window.FreeLLM?.Sync?.bind(container)',
        ):
            self.assertIn(needle, self.runtime_source)
        self.assertNotIn('<div class="app legacy-app">', self.html)

    def test_seo_guides_are_linked_from_the_homepage(self):
        for href in (
            '/guides/free-openai-api-alternatives/',
            '/guides/claude-code-free-alternatives/',
        ):
            self.assertIn(f'href="{href}"', self.html)

    def test_indexable_legal_pages_have_crawler_and_share_metadata(self):
        for relative in ("about/index.html", "terms/index.html", "privacy/index.html"):
            page = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="index,follow,max-image-preview:large"', page)
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', page)
            self.assertIsNotNone(canonical)
            self.assertIn(f'<meta name="twitter:url" content="{canonical.group(1)}"', page)

    def test_submit_page_explains_evidence_requirements(self):
        page = SUBMIT_PATH.read_text(encoding="utf-8")
        for needle in ("官方链接", "免费方式", "地区限制", "官方价格页", "xdguo0527@gmail.com"):
            self.assertIn(needle, page)

    def test_mobile_navigation_keeps_core_directory_entries_visible(self):
        """The static first paint exposes exactly one seven-item global rail."""
        rail = re.search(r'<nav class="fl-site-nav">(.*?)</nav>', self.html, re.S)
        self.assertIsNotNone(rail)
        self.assertEqual(rail.group(1).count("<a "), 7)
        for key, href in (
            ("home", "/"),
            ("models", "/models/"),
            ("skills", "/skills/"),
            ("tools", "/tools/"),
            ("workflow", "/skills/lab/"),
            ("logs", "/logs/"),
            ("about", "/about/"),
        ):
            self.assertIn(f'data-site-nav="{key}"', rail.group(1))
            self.assertIn(f'href="{href}"', rail.group(1))
        self.assertNotIn('class="top-nav"', self.html)

    def test_file_preview_navigation_maps_site_routes_to_local_pages(self):
        """The file:// preview must resolve root navigation to workspace index pages."""
        self.assertIn("window.location.protocol !== 'file:'", self.html)
        self.assertIn("document.body.classList.contains('model-center-page') ? '../../' : '../'", self.html)
        self.assertIn("${siteRoot}${path.slice(1)}index.html${query}", self.html)

    def test_daily_log_dashboard_exposes_baseline_snapshot(self):
        log = LOG_PATH.read_text(encoding="utf-8")
        for needle in (
            'class="daily-log-dashboard"',
            'class="log-hero"',
            'class="log-stat-card blue"',
            'id="static-locale-script"',
            '.log-overview-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:14px; margin-top:18px; align-items:start; }',
            '.log-stat-card { min-height:92px;',
            '.log-days::before { content:"";',
            '.log-registration { margin:12px 0;',
            ".log-event-grid { display:grid; grid-template-columns:1fr; gap:12px; }",
        ):
            self.assertIn(needle, log)
        # Snapshot counters must track the live data, not a frozen literal: the
        # page renders today's directory totals and every historical day uses the
        # totals captured in that day's log JSON.
        models = len(json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8")))
        latest_log_path = sorted((ROOT / "data" / "daily-log").glob("*.json"))[-1]
        latest = json.loads(latest_log_path.read_text(encoding="utf-8"))
        observed_models = len(latest["observed"]["models"])
        self.assertRegex(log, rf'<strong>{observed_models} <span lang="zh-CN">模型</span>')
        self.assertIn(f'<strong>{models}</strong><small><span lang="zh-CN">当前观测到的模型记录</span>', log)
        self.assertRegex(log, r'<strong>\d+ <span lang="zh-CN">模型</span>')
        self.assertRegex(log, r'<strong>\d+ <span lang="zh-CN">提供商</span>')
        self.assertRegex(log, r'<strong>\d+ <span lang="zh-CN">资源</span>')
        self.assertNotIn("首次建立基线", log)
        self.assertIn('<details class="log-new-card">', log)
        self.assertIn('<summary class="log-card-summary">', log)

    def test_daily_updates_story_is_visible_in_homepage_and_log(self):
        log = LOG_PATH.read_text(encoding="utf-8")
        for needle in (
            'data-site-nav="logs"',
            '今天的 AI 资源有什么变化？',
            '我们每天检查官方来源，记录新增、恢复、下线和异常。',
            '查看今日变化',
            'id="daily-log-badge"',
        ):
            self.assertIn(needle, self.html)
        self.assertIn('每日更新', self.html)
        self.assertIn('今天的 AI 资源有什么变化？', log)
        self.assertIn('我们每天检查官方来源，记录新增、恢复、下线和异常。', log)
        self.assertIn('查看今日变化', self.html)

    def test_homepage_links_to_theme_guides(self):
        for slug in (
            "free-openai-compatible-apis",
            "free-ai-coding-tools",
            "free-ai-search-apis",
            "open-weight-models",
            "model-context-windows",
            "china-free-ai-api",
        ):
            self.assertIn(f'href="/guides/{slug}/"', self.html)

        self.assertIn("免费 LLM API / OpenAI 兼容", self.html)
        llm_api_guide = (ROOT / "guides" / "free-openai-compatible-apis" / "index.html").read_text(encoding="utf-8")
        self.assertIn("免费 LLM API 与 OpenAI 兼容接口", llm_api_guide)
        self.assertIn("Compare free or trial LLM APIs", llm_api_guide)

    def test_external_signals_are_available_for_current_offer_set(self):
        offer_ids = {offer["id"] for offer in read_offers()}
        signals = read_signals()
        self.assertGreater(len(signals), 0)
        self.assertTrue({signal["offerId"] for signal in signals} <= offer_ids)
        for needle in ("renderSignalSummary", "offer-card-signal", "signalIndex[item.id]"):
            self.assertIn(needle, self.html)

    def test_catalog_cards_override_legacy_table_grid(self):
        self.assertIn(
            '.offer-grid .offer { grid-template-columns: minmax(0, 1fr);',
            self.html,
        )
        self.assertIn('.offer-card-metric p > small { display: block;', self.html)

    def test_catalog_cards_make_official_sources_clickable(self):
        for needle in (
            'renderOfferSource',
            'offerLinks',
            'renderOfferAccessPaths',
            'drawerAccessPathsBlock',
            'class="offer-source-link"',
            'target="_blank" rel="noreferrer noopener"',
            'renderOfferModels',
            'class="offer-model-row"',
        ):
            self.assertIn(needle, self.html)

    def test_catalog_search_indexes_nested_models_and_cards_have_stable_height(self):
        for needle in (
            "const modelSearchText = (item.freeModels || []).flatMap",
            ".offer-grid .offer-card-body.is-clamped { max-height: 236px;",
            ".offer-grid .offer.model-expanded .offer-card-body.is-clamped { max-height: none;",
            "const OFFER_BODY_CLAMP = 236;",
            "applyOfferBodyClamps",
            'class="offer-models-toggle offer-body-toggle" hidden',
            "placeholder=\"搜索模型、平台或功能，例如 DeepSeek、Qwen3\"",
            "searchPlaceholder: '搜索模型、平台或功能，例如 DeepSeek、Qwen3'",
            "searchPlaceholder: 'Search models, platforms or capabilities, e.g. DeepSeek, Qwen3'",
        ):
            self.assertIn(needle, self.html)

    def test_official_source_links_navigate_in_current_tab(self):
        self.assertNotIn(
            'class="offer-source-link" href="${escapeHtml(href)}" target="_blank"',
            self.html,
        )

    def test_featured_resource_links_are_wired_to_catalog_filters(self):
        self.assertIn('class="featured-resource-link"', self.html)
        self.assertIn(
            "document.querySelectorAll('.featured-resource-link').forEach",
            self.html,
        )
        self.assertIn("const clearCatalogSearch = () =>", self.html)
        self.assertIn("document.getElementById('catalog-search').value = ''", self.html)

    def test_offer_cards_load_company_icons_with_initial_fallback(self):
        for needle in (
            'provider-icon-img',
            'iconHostFromUrl',
            'PROVIDER_ICON_HOSTS',
            "'qwen-download': 'www.aliyun.com'",
            "'glm-download': 'bigmodel.cn'",
            'PROVIDER_ICON_ASSETS',
            "'qwen-download': 'https://github.com/QwenLM.png?size=128'",
            "'glm-download': 'https://github.com/zai-org.png?size=128'",
            'providerIconHost',
            'hydrateProviderIcons',
            'data-icon-host',
            'www.google.com/s2/favicons',
            'provider-mark-fallback',
            'resource-logo img',
        ):
            self.assertIn(needle, self.html)
        self.assertNotIn('editor-pick', self.html)

    def test_offer_card_header_and_detail_buttons_share_one_layout(self):
        self.assertIn('.offer-card-top { display: flex;', self.html)
        self.assertIn('.row-arrow { width: 38px; height: 38px;', self.html)
        self.assertIn('border-radius: 50%;', self.html)
        self.assertIn('type="button" class="row-arrow"', self.html)

    def test_page_has_locale_routing_hooks(self):
        # '?lang=' is deliberately absent: locale switching is localStorage-only
        # since the locale-query purge (search-console regression test forbids it).
        for needle in (
            'SUPPORTED_LOCALES',
            'resolveLocale',
            'applyLocale',
            'data-i18n',
            'data-locale-toggle',
            'free-ai-index-locale',
            'URLSearchParams',
        ):
            self.assertIn(needle, self.html)

    def test_homepage_exposes_chinese_static_seo_metadata(self):
        self.assertRegex(self.html, r'<html[^>]*lang="zh-CN"')
        self.assertIn(
            '<meta name="description" content="FreeLLM 每日核验免费 AI 模型、LLM API、OpenAI 兼容接口、AI 编程工具',
            self.html,
        )
        self.assertIn('<link rel="canonical" href="https://freellm.top/" />', self.html)
        self.assertIn('<meta property="og:image" content="https://freellm.top/freellm-06-faq.png" />', self.html)
        self.assertIn('<meta name="twitter:image" content="https://freellm.top/freellm-06-faq.png" />', self.html)
        self.assertEqual(len(re.findall(r'<h1(?:\s|>)', self.html)), 1)

    def test_homepage_omits_locale_hreflang_variants(self):
        # Query-parameter hreflang variants caused duplicate Search Console
        # URLs; they stay out until languages have distinct crawlable URLs.
        self.assertNotIn('<link rel="alternate" hreflang=', self.html)

    def test_homepage_makes_freellm_brand_explicit_in_search_and_first_view(self):
        self.assertIn(
            '<title>免费 AI 模型与 LLM API 大全（每日核验）｜FreeLLM</title>',
            self.html,
        )
        self.assertIn('<div class="brand-name">FreeLLM</div>', self.html)
        self.assertIn('<h1>免费 AI 模型与 API，<span>每天核验</span></h1>', self.html)
        self.assertIn("免费 LLM API、OpenAI 兼容接口、模型、IDE 与试用入口", self.html)
        self.assertIn("<span>✓</span> 每日核验 · 官方来源", self.html)

    def test_homepage_includes_vercel_web_analytics(self):
        self.assertIn('window.va = window.va || function ()', self.html)
        self.assertIn('window.vaq = window.vaq || []', self.html)
        self.assertIn("if (window.location.protocol === 'https:')", self.html)
        self.assertIn("vercelInsights.src = '/_vercel/insights/script.js'", self.html)

    def test_page_exposes_crawlable_internal_seo_links(self):
        self.assertIn("const offerHref = `/offers/${encodeURIComponent(item.id)}/`;", self.html)
        self.assertIn('class="offer-detail-link"', self.html)

        # Only indexable category landing pages should receive crawl-priority
        # homepage links. Thin categories remain available through the catalog
        # filters, but their noindex URLs must not be promoted as SEO links.
        for slug in ("free-quota", "free-ide", "api", "promo", "web"):
            self.assertIn(f'href="/category/{slug}/"', self.html)
        for slug in ("student", "open-weights"):
            self.assertNotIn(f'href="/category/{slug}/"', self.html)

        self.assertIn('data-filter="student"', self.html)
        self.assertIn('data-filter="download_lowcost"', self.html)

    def test_free_llm_guide_page_remains_available(self):
        self.assertTrue(GUIDE_PATH.is_file())
        guide = GUIDE_PATH.read_text(encoding="utf-8")
        self.assertIn("Free-LLM — 免费 AI 与 LLM API 开放目录", guide)
        self.assertIn("MIT License", guide)

    def test_page_exposes_public_contact_email(self):
        self.assertIn('href="mailto:xdguo0527@gmail.com"', self.html)
        self.assertIn('data-footer-contact-label', self.html)
        self.assertIn("contactLabel: 'Contact'", self.html)
        self.assertIn("contactLabel: '联系我'", self.html)

    def test_model_context_window_is_structured_and_rendered(self):
        offers = read_offers()
        model_offers = [offer for offer in offers if offer.get("contextWindow")]
        self.assertGreaterEqual(len(model_offers), 3)
        self.assertTrue(any(offer["id"] == "qwen-download" for offer in model_offers))
        self.assertTrue(all(offer["productType"] in {"api", "open_weights", "coding_plan"} for offer in model_offers))
        for needle in ("contextWindow", "renderModelContext", "drawerContextWindow", "contextWindowLabel"):
            self.assertIn(needle, self.html)

    def test_english_locale_covers_catalog_static_and_offer_copy(self):
        for needle in (
            "guideNav",
            "doubaoSearch",
            "localizedOfferText",
            "hasChineseText",
            "englishSafeText",
            "localeValue(path.label",
            "localeValue(entry.quota",
            "localeValue(label, 'Official link')",
            "allModels",
            "registerLabelEn",
            "category-seo-links a:nth-child(7)",
        ):
            self.assertIn(needle, self.html)

    def test_locale_switch_updates_url_and_document_language(self):
        for needle in (
            'document.documentElement.lang',
            'history.replaceState',
            'localStorage.setItem',
            'navigator.languages',
            'zh-CN',
            'data-i18n-placeholder',
        ):
            self.assertIn(needle, self.html)

    def test_catalog_compare_surfaces_cheapest_routes(self):
        for needle in (
            'id="catalog-compare"',
            '最便宜的入口先看',
            '北京区 · 新用户',
            '¥0<small>免费额度</small>',
            '有效期 90 天',
            '¥9.9<small>首月 / 月</small>',
            '后续续费 ¥40 / 月',
            '权重免费',
        ):
            self.assertIn(needle, self.html)

    def test_page_uses_free_method_categories(self):
        for name in ("free_quota", "model", "credits", "ide", "promo", "student", "web", "download_lowcost"):
            self.assertIn(f'data-filter="{name}"', self.html)
        catalog_html = self.html.split('<div class="app legacy-app">', 1)[0]
        for name in ("search", "fetch", "extract", "crawl", "map", "browser", "agent"):
            self.assertNotIn(f'data-filter="{name}"', catalog_html)

    def test_page_has_adsense_site_verification_script(self):
        self.assertIn(
            'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2461062743308239',
            self.html,
        )
        self.assertIn("script.crossOrigin = 'anonymous'", self.html)
        self.assertIn("if (!slot) return;", self.html)

    def test_seo_files_point_search_engines_to_canonical_site(self):
        robots = ROBOTS_PATH.read_text(encoding="utf-8")
        sitemap = SITEMAP_PATH.read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://freellm.top/sitemap.xml", robots)
        # sitemap.xml is a sitemap index; page URLs live in the section sitemaps.
        self.assertIn("<sitemapindex", sitemap)
        self.assertIn("<loc>https://freellm.top/sitemap-pages.xml</loc>", sitemap)
        pages_sitemap = SITEMAP_PATH.with_name("sitemap-pages.xml").read_text(encoding="utf-8")
        self.assertIn("<loc>https://freellm.top/</loc>", pages_sitemap)
        self.assertIn("<loc>https://freellm.top/submit/</loc>", pages_sitemap)

    def test_ads_txt_declares_current_adsense_publisher(self):
        self.assertTrue(ADS_PATH.is_file())
        self.assertIn(
            "google.com, pub-2461062743308239, DIRECT, f08c47fec0942fa0",
            ADS_PATH.read_text(encoding="utf-8"),
        )

    def test_web_usage_guide_hooks_exist(self):
        for hook in ("drawerUsageGuide", "drawerPrerequisites", "drawerSteps", "drawerEndpoint", "drawerExample", "drawerQuotaGuard", "drawerCommonIssues"):
            self.assertIn(f'id="{hook}"', self.html)
        self.assertIn('"id":"tinyfish-search-fetch-free"', self.html)

    def test_page_has_external_signal_hooks_without_local_scoring(self):
        for needle in (
            "community-signals.json",
            'id="drawerSignals"',
            "External platform signals",
            "No public rating found",
            "sourcePlatform",
            "sourceType",
        ):
            self.assertIn(needle, self.html)
        self.assertNotIn("composite score", self.html.lower())
        self.assertNotIn("本站评分", self.html)

    def test_hardcoded_offers_are_gone(self):
        self.assertNotIn("const offers = {", self.html)
        self.assertNotIn("slice(0, 4)", self.html)
        static_articles = re.findall(r'<article class="offer" data-type="(?!")', self.html)
        self.assertEqual(static_articles, [])

    def test_dynamic_plain_text_has_safe_dom_boundaries_and_date_fallback(self):
        for needle in ("const renderClock", "clock.replaceChildren()", "checkedDateLabel", "dateUnknown", "error.textContent"):
            self.assertIn(needle, self.html)
        for forbidden in (
            "if (clock) clock.innerHTML",
            "hero-intel-head > span').innerHTML",
            "container.innerHTML = '<div class=\"offer-error\"",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_static_itemlist_fallback_lists_every_offer_title(self):
        block = re.search(r'<script type="application/ld\+json" id="ld-dynamic">(.*?)</script>', self.html, re.S)
        self.assertIsNotNone(block, "ld-dynamic JSON-LD block missing")
        names = [item["name"] for item in json.loads(block.group(1))["@graph"][0]["itemListElement"]]
        self.assertEqual(names, [offer["title"] for offer in read_offers()])


class DailyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / ".github" / "workflows" / "daily-check.yml").read_text(encoding="utf-8")

    def test_workflow_runs_daily_without_dependencies(self):
        self.assertIn("cron:", self.text)
        self.assertIn("python-version", self.text)
        self.assertNotIn("pip install", self.text)

    def test_workflow_validates_scans_diffs_and_uploads(self):
        for needle in ("crawler.cli validate", "crawler.cli scan", "crawler.cli discover", "crawler.cli coverage", "scripts/site_health.py", "site-health-report.json", "upload-artifact", "if: always()"):
            self.assertIn(needle, self.text)

    def test_workflow_ingests_external_signals_without_publishing_them_as_offers(self):
        self.assertIn("crawler.cli signals", self.text)
        self.assertIn("data/community-signals.json", self.text)
        self.assertIn("community-signals", self.text)
        self.assertNotIn("综合推荐分", self.text)

    def test_workflow_never_pushes_public_data(self):
        self.assertNotIn("git push", self.text)
        self.assertNotIn("git commit", self.text)

    def test_browser_smoke_workflow_installs_chromium_separately(self):
        workflow = (ROOT / ".github" / "workflows" / "browser-smoke.yml").read_text(encoding="utf-8")
        self.assertIn("playwright install --with-deps chromium", workflow)
        self.assertIn("tests.test_e2e_static", workflow)


class _LocalSite:
    """Serve a directory over HTTP on an ephemeral localhost port."""

    def __init__(self, directory: Path):
        handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


def start_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        manager = sync_playwright().start()
    except Exception:
        return None
    try:
        browser = manager.chromium.launch()
    except Exception:
        manager.stop()
        return None
    return manager, browser


class BrowserPageTests(unittest.TestCase):
    PAGE_URL_PATH = "design/free-china-ai-index.html"

    @classmethod
    def setUpClass(cls):
        cls._started = start_playwright()
        if cls._started is None:
            raise unittest.SkipTest("playwright chromium not available")
        cls._manager, cls._browser = cls._started

    @classmethod
    def tearDownClass(cls):
        cls._browser.close()
        cls._manager.stop()

    def setUp(self):
        self.site = _LocalSite(ROOT)
        self.addCleanup(self.site.stop)

    def new_page(self):
        # 固定中文 locale：页面的默认语言跟随 navigator.languages，
        # 不固定的话中英文断言会随运行环境的浏览器语言漂移。
        context = self._browser.new_context(locale="zh-CN")
        self.addCleanup(context.close)
        page = context.new_page()
        problems = []

        def record_console_problem(message):
            if message.type != "error":
                return
            text = message.text
            if "Framing 'https://www.google.com/'" in text and "report-only Content Security Policy directive" in text:
                return
            problems.append(text)

        page.on("console", record_console_problem)
        page.on("pageerror", lambda error: problems.append(str(error)))
        page.problems = problems
        bad_responses = []
        page.on("response", lambda response: bad_responses.append((response.status, response.url)) if response.status >= 400 else None)
        page.bad_responses = bad_responses
        # 图标服务对个别域名会间歇性 404，落到本地 1x1 PNG，让控制台断言不受外部抖动影响。
        favicon_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        for pattern in ("**/faviconV2*", "**/s2/favicons*"):
            page.route(pattern, lambda route: route.fulfill(status=200, content_type="image/png", body=favicon_png))
        self.addCleanup(page.close)
        return page

    def visible_offers(self, page):
        page.wait_for_selector(".offer", state="attached")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        return page.locator(".offer:not(.hidden)").count()

    def test_file_protocol_renders_embedded_data(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")
        self.assertEqual(self.visible_offers(page), len(read_offers()))
        self.assertEqual(page.locator("#heroCount").inner_text(), str(len(read_offers())))
        self.assertEqual(page.locator(".filter-strip [data-filter='free_quota'] em").inner_text(), "20")
        self.assertEqual(page.locator(".category-card[data-filter='free_quota'] [data-category-count]").inner_text(), "20")
        ide_count = sum(1 for offer in read_offers() if offer.get("productType") == "free_ide")
        self.assertEqual(page.locator(".filter-strip [data-filter='ide'] em").inner_text(), f"{ide_count:02d}")
        self.assertEqual(page.locator(".filter-strip [data-filter='student'] em").inner_text(), "02")
        model_count = sum(1 for offer in read_offers() if offer.get("productType") == "api")
        self.assertEqual(
            page.locator(".filter-strip [data-filter='model'] em").inner_text(),
            f"{model_count:02d}",
        )
        self.assertEqual(page.locator(".category-card[data-filter='model'] [data-category-count]").inner_text(), f"{model_count:02d}")
        # 加精 chip 的标签按 data-filter 做 i18n，不能被位置映射串到别的分类名。
        self.assertTrue(page.locator(".filter-strip [data-filter='featured']").inner_text().strip().startswith("◆"))
        self.assertEqual(page.locator("#studentList .student-item").count(), 2)
        self.assertEqual(page.locator(".offer .provider-icon-img").count(), len(read_offers()))
        self.assertEqual(page.locator(".offer .provider-mark-fallback").count(), len(read_offers()))
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_mobile_navigation_exposes_core_directory_entries(self):
        page = self.new_page()
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")
        self.assertTrue(page.locator('.fl-site-rail').is_visible())
        self.assertEqual(page.locator('.fl-site-nav > a').count(), 7)
        for key in ("home", "models", "skills", "tools", "workflow", "logs", "about"):
            link = page.locator(f'.fl-site-nav a[data-site-nav="{key}"]')
            self.assertEqual(link.count(), 1)
            self.assertTrue(link.is_visible(), f"mobile nav item {key} must be visible without opening another menu")

    def test_primary_pages_support_dark_theme_and_mobile_without_page_overflow(self):
        routes = (
            ("design/free-china-ai-index.html", ".catalog-app"),
            ("models/", 'body[data-fl-section="models"]'),
            ("skills/", ".skills-page"),
            ("tools/", ".tools-page"),
            ("skills/lab/", ".skill-lab-page"),
            ("logs/", ".daily-log-dashboard"),
            ("about/", 'body[data-fl-section="about"]'),
        )
        for width, height in ((1280, 900), (390, 844)):
            for route, selector in routes:
                with self.subTest(route=route, width=width):
                    page = self.new_page()
                    page.set_viewport_size({"width": width, "height": height})
                    page.add_init_script("localStorage.setItem('freellm-theme', 'dark')")
                    page.goto(f"{self.site.url}/{route}")
                    page.wait_for_selector(selector)
                    page.wait_for_function("document.documentElement.dataset.theme === 'dark'")
                    self.assertTrue(page.locator(".fl-site-rail").is_visible(), route)
                    self.assertEqual(page.locator(".fl-site-nav > a").count(), 7, route)
                    self.assertLessEqual(
                        page.evaluate("document.documentElement.scrollWidth"),
                        width + 4,
                        f"{route} creates page-level horizontal overflow at {width}px",
                    )
                    body_color = page.evaluate("getComputedStyle(document.body).color")
                    self.assertNotIn("rgb(16, 43, 89)", body_color, f"{route} kept light-theme ink in dark mode")
                    page.close()

    def test_visual_regression_equal_height_cards_and_home_hierarchy(self):
        page = self.new_page()
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.goto(f"{self.site.url}/design/free-china-ai-index.html")
        page.wait_for_selector("#catalog-offer-rows .offer")

        order = page.evaluate("""() => {
            const ids = ['today-latest', 'catalog-offers', 'student-offers', 'catalog-compare'];
            const nodes = {
                'today-latest': document.querySelector('.today-latest'),
                'catalog-offers': document.getElementById('catalog-offers'),
                'student-offers': document.getElementById('student-offers'),
                'catalog-compare': document.getElementById('catalog-compare'),
            };
            return ids.map(id => [id, Array.from(document.body.querySelectorAll('*')).indexOf(nodes[id])]);
        }""")
        positions = dict(order)
        self.assertLess(positions["today-latest"], positions["catalog-offers"])
        self.assertLess(positions["catalog-offers"], positions["student-offers"])
        self.assertLess(positions["student-offers"], positions["catalog-compare"])
        page.close()

        checks = (
            ("design/free-china-ai-index.html", "#catalog-offer-rows .offer:not(.hidden)"),
            ("models/", ".models-overview-grid > article"),
            ("skills/", "#skill-grid .skill-card:not([hidden])"),
            ("tools/", "#tool-grid .tool-card:not([hidden])"),
            ("skills/lab/", ".workflow-grid .workflow-card"),
            ("logs/", ".log-stat-grid .log-stat-card"),
            ("about/", ".stat-row .stat"),
        )
        for route, selector in checks:
            with self.subTest(route=route):
                page = self.new_page()
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.goto(f"{self.site.url}/{route}")
                page.wait_for_selector(selector)
                heights = page.eval_on_selector_all(
                    selector,
                    """els => {
                        const visible = els
                          .filter(el => {
                            const s = getComputedStyle(el);
                            const r = el.getBoundingClientRect();
                            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 10 && r.height > 10;
                          })
                          .map(el => {
                            const r = el.getBoundingClientRect();
                            return { top: r.top, height: r.height };
                          });
                        if (!visible.length) return [];
                        const firstTop = Math.min(...visible.map(item => item.top));
                        return visible.filter(item => Math.abs(item.top - firstTop) <= 3).map(item => item.height);
                    }""",
                )
                self.assertGreaterEqual(len(heights), 2, f"{route}: expected at least two cards in first desktop row")
                self.assertLessEqual(
                    max(heights) - min(heights),
                    2.0,
                    f"{route}: first-row card heights drifted: {heights}",
                )
                page.close()

    def test_visual_regression_mobile_chrome_has_no_duplicate_headers_or_overlap(self):
        routes = (
            ("skills/", ".skills-page", ".skills-header"),
            ("tools/", ".tools-page", ".tools-header"),
        )
        for route, root_selector, legacy_header in routes:
            with self.subTest(route=route):
                page = self.new_page()
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(f"{self.site.url}/{route}")
                page.wait_for_selector(root_selector)
                self.assertEqual(page.locator(legacy_header).evaluate("el => getComputedStyle(el).display"), "none")
                rail = page.locator(".fl-site-rail").bounding_box()
                hero = page.locator(".skills-hero, .tools-hero").first.bounding_box()
                self.assertIsNotNone(rail)
                self.assertIsNotNone(hero)
                self.assertGreaterEqual(hero["y"], rail["y"] + rail["height"] + 6)
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 394)
                page.close()

    def test_visual_regression_dark_theme_uses_neo_tokens_on_primary_pages(self):
        routes = (
            ("design/free-china-ai-index.html", ".today-latest"),
            ("models/", ".models-overview"),
            ("skills/", ".skills-hero"),
            ("tools/", ".tools-hero"),
            ("skills/lab/", ".lab-hero"),
            ("logs/", ".log-hero"),
            ("about/", 'body[data-fl-section="about"] > header'),
        )
        for route, surface in routes:
            with self.subTest(route=route):
                page = self.new_page()
                page.set_viewport_size({"width": 1280, "height": 900})
                page.add_init_script("localStorage.setItem('freellm-theme', 'dark')")
                page.goto(f"{self.site.url}/{route}")
                page.wait_for_selector(surface)
                page.wait_for_function("document.documentElement.dataset.theme === 'dark'")
                tokens = page.evaluate("""() => {
                    const s = getComputedStyle(document.documentElement);
                    return {
                      canvas: s.getPropertyValue('--fl-canvas').trim(),
                      ink: s.getPropertyValue('--fl-ink').trim(),
                      mint: s.getPropertyValue('--fl-mint').trim()
                    };
                }""")
                self.assertEqual(tokens["canvas"].lower(), "#050b18")
                self.assertEqual(tokens["ink"].lower(), "#f5f9ff")
                self.assertEqual(tokens["mint"].lower(), "#6ef0c4")
                text_color = page.locator(surface).evaluate("el => getComputedStyle(el).color")
                self.assertNotEqual(text_color, "rgb(16, 43, 89)")
                page.close()

    def test_theme_toggle_persists_between_primary_pages(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/skills/")
        page.wait_for_selector(".fl-site-theme-toggle")
        page.click(".fl-site-theme-toggle")
        page.wait_for_function("document.documentElement.dataset.theme === 'dark'")
        self.assertEqual(page.evaluate("localStorage.getItem('freellm-theme')"), "dark")
        page.goto(f"{self.site.url}/tools/")
        page.wait_for_function("document.documentElement.dataset.theme === 'dark'")
        self.assertEqual(page.evaluate("localStorage.getItem('freellm-theme')"), "dark")

    def test_skill_detail_dialog_stays_inside_narrow_viewports(self):
        page = self.new_page()
        page.set_viewport_size({"width": 720, "height": 700})
        page.goto(f"{self.site.url}/skills/")
        page.click('.skill-details[data-skill-id="anthropics-docx"]')
        page.wait_for_selector("#skill-dialog[open]")
        self.assertTrue(page.locator("#dialog-skill-test").is_visible())
        self.assertIn("BLOCKED", page.locator("#dialog-skill-test").inner_text())
        self.assertTrue(page.locator("#dialog-skill-preview").is_hidden())
        self.assertTrue(page.locator("#dialog-style-section").is_hidden())

        for width, height in ((720, 700), (390, 844)):
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(50)
            dialog_box = page.locator("#skill-dialog").bounding_box()
            heading_box = page.locator("#dialog-skill-name").bounding_box()
            self.assertIsNotNone(dialog_box)
            self.assertIsNotNone(heading_box)
            self.assertGreaterEqual(dialog_box["x"], -0.5)
            self.assertGreaterEqual(dialog_box["y"], -0.5)
            self.assertLessEqual(dialog_box["x"] + dialog_box["width"], width + 0.5)
            self.assertLessEqual(dialog_box["y"] + dialog_box["height"], height + 0.5)
            self.assertGreaterEqual(heading_box["x"], dialog_box["x"] + 8)

        page.click(".skill-dialog-close")
        page.set_viewport_size({"width": 720, "height": 700})
        page.click('.skill-details[data-skill-id="anthropics-pdf"]')
        page.wait_for_selector("#skill-dialog[open]")
        self.assertIn("8.7/10", page.locator("#dialog-skill-test").inner_text())
        self.assertIn("端到端通过", page.locator("#dialog-skill-test").inner_text())
        self.assertIn("真实生成 2 页退款 PDF", page.locator("#dialog-skill-test").inner_text())
        self.assertTrue(page.locator("#dialog-skill-preview").is_hidden())

        self.assertEqual(
            [problem for problem in page.problems if not problem.startswith("Failed to load resource")],
            [],
            page.problems,
        )

    def test_file_protocol_search_filter_and_drawer(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click(".category-card[data-filter='ide']")
        ide_count = sum(1 for offer in read_offers() if offer.get("productType") == "free_ide")
        self.assertEqual(self.visible_offers(page), ide_count)

        page.fill("#catalog-search", "Qwen3")
        self.assertEqual(self.visible_offers(page), 3)

        page.fill("#catalog-search", "")
        page.click(".offer[data-detail='comate'] .row-arrow")
        page.wait_for_selector("#drawer.open")
        register = page.locator("#drawerRegister")
        self.assertEqual(register.get_attribute("href"), "https://comate.baidu.com/zh")
        self.assertIn("Auto-Free", page.locator("#drawerTitle").inner_text())
        page.keyboard.press("Escape")
        self.assertNotIn("open", page.locator("#drawer").get_attribute("class"))
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_homepage_aurora_phase_one_visual_contracts(self):
        page = self.new_page()
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")

        self.assertEqual(page.locator("body").get_attribute("data-visual-style"), "aurora")
        self.assertEqual(page.locator(".fl-site-theme-toggle").evaluate("el => getComputedStyle(el).display"), "none")

        hero = page.locator(".catalog-hero").bounding_box()
        today = page.locator(".today-latest").bounding_box()
        offers = page.locator("#catalog-offers").bounding_box()
        student = page.locator("#student-offers").bounding_box()
        self.assertIsNotNone(hero)
        self.assertIsNotNone(today)
        self.assertIsNotNone(offers)
        self.assertIsNotNone(student)
        self.assertLess(hero["y"], today["y"])
        self.assertLess(today["y"], offers["y"])
        self.assertLess(offers["y"], student["y"])

        heights = page.eval_on_selector_all(
            "#catalog-offer-rows .offer:not(.hidden)",
            """els => {
              const items = els.slice(0, 6).map(el => {
                const r = el.getBoundingClientRect();
                return {top:r.top,height:r.height};
              });
              if (!items.length) return [];
              const firstTop = items[0].top;
              return items.filter(x => Math.abs(x.top-firstTop) <= 3).map(x => x.height);
            }"""
        )
        self.assertGreaterEqual(len(heights), 2)
        self.assertLessEqual(max(heights) - min(heights), 2.0, heights)

    def test_homepage_aurora_phase_one_mobile_layout(self):
        page = self.new_page()
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")

        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 394)
        self.assertEqual(page.locator(".fl-site-nav > a").count(), 7)
        for index in range(7):
            self.assertTrue(page.locator(".fl-site-nav > a").nth(index).is_visible())

        hero = page.locator(".catalog-hero").bounding_box()
        search = page.locator(".hero-search").bounding_box()
        self.assertIsNotNone(hero)
        self.assertIsNotNone(search)
        self.assertLessEqual(search["x"] + search["width"], 390)
        self.assertGreaterEqual(search["x"], 0)

    def test_featured_resource_link_filters_catalog(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        # featured 区精简后只剩「免费额度」这一个筛选入口；残留的搜索词必须被它清掉。
        page.fill("#catalog-search", "Qwen3")
        page.click(".featured-resource-link[aria-label='查看免费额度']")
        page.wait_for_function(
            """document.querySelector('.filter-chip[data-filter="free_quota"]')?.classList.contains('active')"""
        )
        self.assertEqual(self.visible_offers(page), 20)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_featured_resource_link_filters_catalog_without_stale_query(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click(".featured-resource-link[aria-label='查看免费额度']")
        page.wait_for_function(
            """document.querySelector('.filter-chip[data-filter="free_quota"]')?.classList.contains('active')"""
        )
        self.assertEqual(self.visible_offers(page), 20)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_web_offer_drawer_shows_usage_guide(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click(".filter-strip [data-filter='web']")
        page.click(".offer[data-detail='tinyfish-search-fetch-free'] .row-arrow")
        page.wait_for_selector("#drawer.open")
        self.assertIn("Search + Fetch", page.locator("#drawerTitle").inner_text())
        self.assertNotEqual(page.locator("#drawerUsageGuide").inner_text().strip(), "")
        self.assertIn("TinyFish", page.locator("#drawerPrerequisites").inner_text())
        self.assertGreaterEqual(page.locator("#drawerSteps").inner_text().count("·"), 1)
        self.assertIn("https://", page.locator("#drawerEndpoint").inner_text())
        self.assertNotEqual(page.locator("#drawerExample").inner_text().strip(), "")
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_http_protocol_prefers_network_json(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}")
        page.wait_for_function("document.body.dataset.dataSource === 'network'")
        ranked = read_ranked_offers()
        self.assertEqual(self.visible_offers(page), len(ranked))
        item_list = page.evaluate("JSON.parse(document.getElementById('ld-dynamic').textContent)['@graph'][0]['itemListElement']")
        self.assertEqual(len(item_list), len(ranked))
        self.assertEqual(
            [entry["name"] for entry in item_list[:5]],
            [item["title"] for item in ranked[:5]],
        )
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_locale_query_switches_shell_language(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}?lang=en#catalog-offers")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        self.assertEqual(page.evaluate("document.documentElement.lang"), "en")
        self.assertEqual(page.locator('[data-site-nav="logs"] span:last-child').inner_text(), "Updates")
        self.assertEqual(page.locator("[data-locale-toggle]").inner_text(), "中文")

        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}?lang=zh-CN#catalog-offers")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        self.assertEqual(page.evaluate("document.documentElement.lang"), "zh-CN")
        self.assertEqual(page.locator('[data-site-nav="logs"] span:last-child').inner_text(), "更新")
        self.assertEqual(page.locator("[data-locale-toggle]").inner_text(), "EN")
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_locale_toggle_keeps_query_clean_and_preserves_hash(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}?lang=zh-CN#catalog-offers")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        page.click("[data-locale-toggle]")
        self.assertEqual(page.evaluate("document.documentElement.lang"), "en")
        # Locale lives in local storage now; the URL stays canonical (no ?lang=) with its hash.
        self.assertNotIn("?lang=", page.url)
        self.assertTrue(page.url.endswith("#catalog-offers"), page.url)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_http_protocol_falls_back_to_embedded_when_json_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            design = Path(directory) / "design"
            design.mkdir()
            (design / HTML_PATH.name).write_text(HTML_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            js = Path(directory) / "js"
            js.mkdir()
            (js / "freellm-sync.js").write_text((ROOT / "js" / "freellm-sync.js").read_text(encoding="utf-8"), encoding="utf-8")
            for source in (ROOT / "js").glob("homepage*.js"):
                (js / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            css = Path(directory) / "css"
            css.mkdir()
            (css / "freellm-pastel-ui.css").write_text((ROOT / "css" / "freellm-pastel-ui.css").read_text(encoding="utf-8"), encoding="utf-8")
            (css / "aurora-home.css").write_text((ROOT / "css" / "aurora-home.css").read_text(encoding="utf-8"), encoding="utf-8")
            for source in (ROOT / "css").glob("homepage*.css"):
                (css / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            data = Path(directory) / "data"
            data.mkdir()
            (data / "offers.js").write_text(OFFERS_BUNDLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            site = _LocalSite(Path(directory))
            self.addCleanup(site.stop)
            page = self.new_page()
            page.goto(f"{site.url}/{self.PAGE_URL_PATH}")
            page.wait_for_function("document.body.dataset.dataSource === 'embedded-fallback'")
            self.assertEqual(self.visible_offers(page), len(read_ranked_offers()))
            # 场景本身就是两个 data JSON 404；除此之外不允许任何失败请求或 JS 错误。
            self.assertEqual(
                sorted(url.rsplit("/", 1)[-1] for _, url in page.bad_responses),
                ["community-signals.json", "offers-ranked.json"],
            )
            self.assertEqual([p for p in page.problems if not p.startswith("Failed to load resource")], [], page.problems)

    def test_missing_data_shows_readable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            design = Path(directory) / "design"
            design.mkdir()
            (design / HTML_PATH.name).write_text(HTML_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            js = Path(directory) / "js"
            js.mkdir()
            (js / "freellm-sync.js").write_text((ROOT / "js" / "freellm-sync.js").read_text(encoding="utf-8"), encoding="utf-8")
            for source in (ROOT / "js").glob("homepage*.js"):
                (js / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            css = Path(directory) / "css"
            css.mkdir()
            (css / "freellm-pastel-ui.css").write_text((ROOT / "css" / "freellm-pastel-ui.css").read_text(encoding="utf-8"), encoding="utf-8")
            (css / "aurora-home.css").write_text((ROOT / "css" / "aurora-home.css").read_text(encoding="utf-8"), encoding="utf-8")
            for source in (ROOT / "css").glob("homepage*.css"):
                (css / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            site = _LocalSite(Path(directory))
            self.addCleanup(site.stop)
            page = self.new_page()
            page.goto(f"{site.url}/{self.PAGE_URL_PATH}")
            page.wait_for_selector(".offer-error")
            self.assertIn("Offer data unavailable", page.locator(".offer-error").inner_text())
            self.assertEqual(page.locator("#catalog-result-count").inner_text(), "0 条资源")


if __name__ == "__main__":
    unittest.main()
