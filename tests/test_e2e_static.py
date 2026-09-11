"""End-to-end checks: HTML/data contract, daily workflow, and page behavior.

The Playwright tests run against a local browser when available and skip
cleanly otherwise (CI uses the zero-install stdlib policy).
"""

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
ASSET_PATH = ROOT / "design" / "assets" / "free-method-night-window.png"
OFFERS_PATH = ROOT / "data" / "offers.json"
SIGNALS_PATH = ROOT / "data" / "community-signals.json"
ROBOTS_PATH = ROOT / "robots.txt"
SITEMAP_PATH = ROOT / "sitemap.xml"
ADS_PATH = ROOT / "ads.txt"
GUIDE_PATH = ROOT / "guides" / "free-llm" / "index.html"
LOG_PATH = ROOT / "logs" / "index.html"


def read_offers() -> list:
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


def read_signals() -> list:
    return json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))


def embedded_offer_data(html: str):
    match = re.search(r'<script type="application/json" id="offer-data">(.*?)</script>', html, re.S)
    return json.loads(match.group(1)) if match else None


class StaticContractTests(unittest.TestCase):
    def setUp(self):
        self.html = HTML_PATH.read_text(encoding="utf-8")

    def test_embedded_data_matches_offers_json(self):
        self.assertEqual(embedded_offer_data(self.html), read_offers())

    def test_page_has_required_data_hooks(self):
        for needle in (
            'id="offer-data"', 'id="catalog-offer-rows"', 'id="catalog-search"',
            'id="catalog-sort"', 'id="catalog-result-count"', 'id="ld-dynamic"',
            "renderOffers", "loadOffers", "showDataError",
            'id="studentList"', 'id="catalog-download-list"', 'id="catalog-last-checked"',
            'assets/free-method-night-window.png', "offerCategories", "timeWindow",
        ):
            self.assertIn(needle, self.html)
        self.assertIn('"id": "doubao"', self.html)
        self.assertIn('"id": "aliyun-qwen-free-quota"', self.html)
        self.assertIn('"id": "agnes-ai-free"', self.html)
        self.assertIn('"id": "stepfun-limited-time-free"', self.html)
        self.assertIn('"id": "longcat-2-0"', self.html)
        self.assertNotIn('"id": "longcat-api"', self.html)
        self.assertNotIn('"id": "longcat-download"', self.html)

    def test_seo_guides_are_linked_from_the_homepage(self):
        for href in (
            '/guides/free-openai-api-alternatives/',
            '/guides/claude-code-free-alternatives/',
        ):
            self.assertIn(f'href="{href}"', self.html)

    def test_mobile_navigation_keeps_core_directory_entries_visible(self):
        """Narrow screens must keep the directory navigation discoverable."""
        self.assertIn('href="/logs/"', self.html)
        for href in (
            'href="/models/"',
            'href="/models/center/"',
            'href="/models/all/"',
            'href="/providers/"',
        ):
            self.assertIn(href, self.html)
        mobile_block = re.search(
            r'@media \(max-width: 700px\) \{(?P<body>.*?)\n    \}',
            self.html,
            re.S,
        )
        self.assertIsNotNone(mobile_block)
        self.assertNotRegex(mobile_block.group("body"), r'\.top-nav\s*\{\s*display:\s*none')
        self.assertRegex(mobile_block.group("body"), r'\.top-nav\s*\{[^}]*overflow-x:\s*auto')

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
            ">297</strong>",
            ">25</strong>",
            ">39</strong>",
        ):
            self.assertIn(needle, log)
        self.assertNotIn("首次建立基线", log)
        self.assertIn('<details class="log-new-card">', log)
        self.assertIn('<summary class="log-card-summary">', log)

    def test_daily_updates_story_is_visible_in_homepage_and_log(self):
        log = LOG_PATH.read_text(encoding="utf-8")
        for needle in (
            'data-nav-key="daily-log"',
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
            'hunyuan-mark img',
        ):
            self.assertIn(needle, self.html)

    def test_offer_card_header_and_detail_buttons_share_one_layout(self):
        self.assertIn('.offer-card-top { display: flex;', self.html)
        self.assertIn('.row-arrow { width: 38px; height: 38px;', self.html)
        self.assertIn('border-radius: 50%;', self.html)
        self.assertIn('type="button" class="row-arrow"', self.html)

    def test_page_has_locale_routing_hooks(self):
        for needle in (
            'SUPPORTED_LOCALES',
            'resolveLocale',
            'applyLocale',
            'data-i18n',
            'data-locale-toggle',
            'free-ai-index-locale',
            'URLSearchParams',
            '?lang=',
        ):
            self.assertIn(needle, self.html)

    def test_homepage_exposes_chinese_static_seo_metadata(self):
        self.assertIn('<html lang="zh-CN">', self.html)
        self.assertIn(
            '<meta name="description" content="FreeLLM 整理可核验的免费 AI 模型、API、编程 IDE、学生优惠和开源权重',
            self.html,
        )
        self.assertIn('<link rel="canonical" href="https://freellm.top/" />', self.html)
        self.assertIn('<meta property="og:image" content="https://freellm.top/freellm-01-hero.png" />', self.html)
        self.assertIn('<meta name="twitter:image" content="https://freellm.top/freellm-01-hero.png" />', self.html)
        self.assertEqual(len(re.findall(r'<h1(?:\s|>)', self.html)), 1)

    def test_homepage_exposes_language_alternates(self):
        self.assertIn('<link rel="alternate" hreflang="zh-CN" href="https://freellm.top/" />', self.html)
        self.assertIn('<link rel="alternate" hreflang="en" href="https://freellm.top/?lang=en" />', self.html)
        self.assertIn('<link rel="alternate" hreflang="x-default" href="https://freellm.top/" />', self.html)

    def test_homepage_makes_freellm_brand_explicit_in_search_and_first_view(self):
        self.assertIn(
            '<title>FreeLLM — 免费 AI 模型、API、IDE 与额度索引</title>',
            self.html,
        )
        self.assertIn('<div class="brand-name">FreeLLM</div>', self.html)
        self.assertIn('<h1>FreeLLM：发现真正好用的<span>免费 AI</span></h1>', self.html)

    def test_homepage_includes_vercel_web_analytics(self):
        self.assertIn('window.va = window.va || function ()', self.html)
        self.assertIn('window.vaq = window.vaq || []', self.html)
        self.assertIn('<script defer src="/_vercel/insights/script.js"></script>', self.html)

    def test_page_exposes_crawlable_internal_seo_links(self):
        self.assertIn("const offerHref = `/offers/${encodeURIComponent(item.id)}/`;", self.html)
        self.assertIn('class="offer-detail-link"', self.html)
        for slug in ("free-quota", "free-ide", "api", "promo", "student", "web", "open-weights"):
            self.assertIn(f'href="/category/{slug}/"', self.html)

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
            "qwenFeaturedTitle",
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
        for name in ("free_quota", "credits", "ide", "promo", "student", "web", "download_lowcost"):
            self.assertIn(f'data-filter="{name}"', self.html)
        self.assertTrue(ASSET_PATH.is_file())
        self.assertGreater(ASSET_PATH.stat().st_size, 1000)
        catalog_html = self.html.split('<div class="app legacy-app">', 1)[0]
        for name in ("search", "fetch", "extract", "crawl", "map", "browser", "agent"):
            self.assertNotIn(f'data-filter="{name}"', catalog_html)

    def test_page_has_adsense_site_verification_script(self):
        self.assertIn(
            'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2461062743308239',
            self.html,
        )
        self.assertIn('crossorigin="anonymous"', self.html)

    def test_seo_files_point_search_engines_to_canonical_site(self):
        robots = ROBOTS_PATH.read_text(encoding="utf-8")
        sitemap = SITEMAP_PATH.read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://freellm.top/sitemap.xml", robots)
        self.assertIn("<loc>https://freellm.top/</loc>", sitemap)

    def test_ads_txt_declares_current_adsense_publisher(self):
        self.assertTrue(ADS_PATH.is_file())
        self.assertIn(
            "google.com, pub-2461062743308239, DIRECT, f08c47fec0942fa0",
            ADS_PATH.read_text(encoding="utf-8"),
        )

    def test_web_usage_guide_hooks_exist(self):
        for hook in ("drawerUsageGuide", "drawerPrerequisites", "drawerSteps", "drawerEndpoint", "drawerExample", "drawerQuotaGuard", "drawerCommonIssues"):
            self.assertIn(f'id="{hook}"', self.html)
        self.assertIn('"id": "tinyfish-search-fetch-free"', self.html)

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
        context = self._browser.new_context()
        self.addCleanup(context.close)
        page = context.new_page()
        problems = []
        page.on("console", lambda message: problems.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: problems.append(str(error)))
        page.problems = problems
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
        self.assertEqual(self.visible_offers(page), 27)
        self.assertEqual(page.locator("#heroCount").inner_text(), "27")
        self.assertEqual(page.locator(".filter-strip [data-filter='free_quota'] em").inner_text(), "08")
        self.assertEqual(page.locator(".category-card[data-filter='free_quota'] [data-category-count]").inner_text(), "08")
        self.assertEqual(page.locator(".filter-strip [data-filter='ide'] em").inner_text(), "08")
        self.assertEqual(page.locator(".filter-strip [data-filter='student'] em").inner_text(), "02")
        self.assertEqual(page.locator("#studentList .student-item").count(), 2)
        self.assertEqual(page.locator(".offer .provider-icon-img").count(), 27)
        self.assertEqual(page.locator(".offer .provider-mark-fallback").count(), 27)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_mobile_navigation_exposes_core_directory_entries(self):
        page = self.new_page()
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")
        self.assertTrue(page.locator('.top-nav').is_visible())
        for href in ("/logs/", "/models/", "/models/center/", "/models/all/", "/providers/"):
            self.assertGreater(page.locator(f'.top-nav a[href="{href}"]').count(), 0)
        self.assertEqual(
            page.locator('.top-nav a').evaluate_all("links => links.map(link => link.dataset.navKey)"),
            ["daily-log", "resources", "model-center", "all-models", "providers"],
        )

    def test_file_protocol_search_filter_and_drawer(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click(".category-card[data-filter='ide']")
        self.assertEqual(self.visible_offers(page), 8)

        page.fill("#catalog-search", "Qwen3")
        self.assertEqual(self.visible_offers(page), 1)

        page.fill("#catalog-search", "")
        page.click(".offer[data-detail='comate'] .row-arrow")
        page.wait_for_selector("#drawer.open")
        register = page.locator("#drawerRegister")
        self.assertEqual(register.get_attribute("href"), "https://comate.baidu.com/zh")
        self.assertIn("Auto-Free", page.locator("#drawerTitle").inner_text())
        page.keyboard.press("Escape")
        self.assertNotIn("open", page.locator("#drawer").get_attribute("class"))
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_featured_resource_link_filters_catalog(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.fill("#catalog-search", "Qwen3")
        page.click(".featured-resource-link[aria-label='查看免费 IDE']")
        page.wait_for_function(
            """document.querySelector('.filter-chip[data-filter="ide"]')?.classList.contains('active')"""
        )
        self.assertEqual(self.visible_offers(page), 8)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_featured_resource_link_filters_catalog_without_stale_query(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click(".featured-resource-link[aria-label='查看免费额度']")
        page.wait_for_function(
            """document.querySelector('.filter-chip[data-filter="free_quota"]')?.classList.contains('active')"""
        )
        self.assertEqual(self.visible_offers(page), 8)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_web_offer_drawer_shows_usage_guide(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click(".filter-strip [data-filter='web']")
        page.click(".offer[data-detail='tinyfish-search-fetch-free'] .row-arrow")
        page.wait_for_selector("#drawer.open")
        self.assertIn("Search and Fetch", page.locator("#drawerTitle").inner_text())
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
        self.assertEqual(self.visible_offers(page), 27)
        item_list = page.evaluate("JSON.parse(document.getElementById('ld-dynamic').textContent)['@graph'][0]['itemListElement']")
        self.assertEqual(len(item_list), 27)
        self.assertEqual(item_list[3]["name"], "Baidu Comate · Auto-Free mode")
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_locale_query_switches_shell_language(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}?lang=en#catalog-offers")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        self.assertEqual(page.evaluate("document.documentElement.lang"), "en")
        self.assertEqual(page.locator(".top-nav").inner_text().splitlines()[0], "Daily updates")
        self.assertEqual(page.locator("[data-locale-toggle]").inner_text(), "中文")

        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}?lang=zh-CN#catalog-offers")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        self.assertEqual(page.evaluate("document.documentElement.lang"), "zh-CN")
        self.assertEqual(page.locator(".top-nav").inner_text().splitlines()[0], "每日更新")
        self.assertEqual(page.locator("[data-locale-toggle]").inner_text(), "EN")
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_locale_toggle_updates_query_and_preserves_hash(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}?lang=zh-CN#catalog-offers")
        page.wait_for_function("document.body.dataset.dataSource !== undefined")
        page.click("[data-locale-toggle]")
        self.assertEqual(page.evaluate("document.documentElement.lang"), "en")
        self.assertTrue(page.url.endswith("?lang=en#catalog-offers"), page.url)
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_http_protocol_falls_back_to_embedded_when_json_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            design = Path(directory) / "design"
            design.mkdir()
            (design / HTML_PATH.name).write_text(HTML_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            site = _LocalSite(Path(directory))
            self.addCleanup(site.stop)
            page = self.new_page()
            page.goto(f"{site.url}/{self.PAGE_URL_PATH}")
            page.wait_for_function("document.body.dataset.dataSource === 'embedded-fallback'")
            self.assertEqual(self.visible_offers(page), 27)
            self.assertEqual(len(page.problems), 0, page.problems)

    def test_missing_data_shows_readable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            design = Path(directory) / "design"
            design.mkdir()
            stripped = re.sub(
                r'(<script type="application/json" id="offer-data">).*?(</script>)',
                r"\1[]\2",
                HTML_PATH.read_text(encoding="utf-8"),
                flags=re.S,
            )
            (design / HTML_PATH.name).write_text(stripped, encoding="utf-8")
            site = _LocalSite(Path(directory))
            self.addCleanup(site.stop)
            page = self.new_page()
            page.goto(f"{site.url}/{self.PAGE_URL_PATH}")
            page.wait_for_selector(".offer-error")
            self.assertIn("Offer data unavailable", page.locator(".offer-error").inner_text())
            self.assertEqual(page.locator("#catalog-result-count").inner_text(), "Showing 0 offers")


if __name__ == "__main__":
    unittest.main()
