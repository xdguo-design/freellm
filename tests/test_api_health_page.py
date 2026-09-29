import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "health" / "index.html"
SYNC = ROOT / "js" / "freellm-sync.js"
SITEMAP = ROOT / "sitemap-pages.xml"


class ApiHealthPageTests(unittest.TestCase):
    def test_health_page_has_primary_workbench_features(self):
        page = PAGE.read_text(encoding="utf-8")
        for needle in (
            "免费 API 健康台",
            "actionReasons",
            "providerActionItems",
            "actionPriorityRank",
            "priorityCounts",
            "actionKeysForLevel",
            "priorityOrderedRecords",
            "rowsForCurrentFilter",
            "dataset.p0Order",
            "dataset.p1Order",
            "dataset.p2Order",
            'id="m-public"',
            'id="m-keyed"',
            'id="m-p0"',
            'id="m-p1"',
            'id="m-p2"',
            'data-filter="p0"',
            'data-filter="p1"',
            'data-filter="p2"',
            "data-priority",
            "缺公开端点检测",
            "CORS 快检失败",
            "活动已到期",
            'id="action-list"',
            'id="expiry-list"',
            'id="channel-list"',
            'data-action="cors"',
            "deepCommand",
            "refreshPool",
            "exportState",
            "importState",
            "https://openrouter.ai/api/v1/models",
            "catalog-cloudflare-workers-ai",
            "catalog-nvidia-nim",
            "catalog-z-ai",
        ):
            self.assertIn(needle, page)

    def test_health_page_never_collects_or_persists_real_api_keys(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn("$env:API_KEY", page)
        self.assertIn("真实 API Key 不保存到 FreeLLM", page)
        self.assertNotIn("localStorage.setItem", page)
        self.assertNotIn('type="password"', page)
        self.assertNotIn("apiKeyInput", page)

    def test_health_page_renders_shared_site_chrome_without_runtime_js(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn('class="fl-pastel-ui"', page)
        self.assertIn('class="fl-ui-v2"', page)
        self.assertIn('class="fl-site-rail"', page)
        self.assertIn('class="fl-site-ribbon"', page)
        self.assertIn('href="/health/" data-site-nav="health" aria-current="page"', page)

    def test_shared_navigation_and_sitemap_include_health_page(self):
        sync = SYNC.read_text(encoding="utf-8")
        sitemap = SITEMAP.read_text(encoding="utf-8")
        self.assertIn("path.indexOf('/health') === 0", sync)
        self.assertIn("railLink('/health/', '⌁', 'API 健康', 'health', current)", sync)
        self.assertIn("https://freellm.top/health/", sitemap)


    def test_limited_semantics_are_shared_by_filter_and_action_queue(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn("function hasExpiringPolicy(r){return isLimited(r)}", page)
        self.assertIn("'rate_limited','daily_quota','monthly_credits','permanent_free','free_models','catalog_access'", page)


class _LocalSite:
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


class ApiHealthBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright not available")
        cls._manager = sync_playwright().start()
        try:
            cls._browser = cls._manager.chromium.launch()
        except Exception:
            cls._manager.stop()
            raise unittest.SkipTest("playwright chromium not available")

    @classmethod
    def tearDownClass(cls):
        cls._browser.close()
        cls._manager.stop()

    def setUp(self):
        self.site = _LocalSite(ROOT)
        self.addCleanup(self.site.stop)
        self.context = self._browser.new_context(locale="zh-CN")
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.addCleanup(self.page.close)

    def load_health(self):
        self.page.goto(f"{self.site.url}/health/")
        self.page.wait_for_function("document.getElementById('m-total').textContent !== '—'")
        self.page.wait_for_selector("#action-list .action-item")
        return self.page

    def test_action_queue_is_provider_unique_and_sorted_by_priority(self):
        page = self.load_health()
        rows = page.locator("#action-list .action-item")
        provider_ids = rows.evaluate_all("els => els.map(el => el.dataset.providerId)")
        priorities = rows.evaluate_all("els => els.map(el => el.dataset.priority)")
        self.assertTrue(provider_ids)
        self.assertEqual(len(provider_ids), len(set(provider_ids)))
        rank = {"P0": 0, "P1": 1, "P2": 2}
        self.assertTrue(all(priority in rank for priority in priorities))
        self.assertEqual([rank[p] for p in priorities], sorted(rank[p] for p in priorities))
        # The action list is intentionally capped at eight providers. Verify the
        # ordering contract rather than freezing provider names/counts that move
        # whenever verified offers are added.
        for previous, current in zip(priorities, priorities[1:]):
            self.assertLessEqual(rank[previous], rank[current])

    def test_endpoint_summary_and_row_badges_distinguish_public_from_key_required(self):
        page = self.load_health()
        alive = int(page.locator("#m-alive").inner_text())
        public = int(page.locator("#m-public").inner_text())
        keyed = int(page.locator("#m-keyed").inner_text())
        total = int(page.locator("#m-total").inner_text())
        self.assertGreaterEqual(total, alive)
        self.assertGreaterEqual(alive, public + keyed)
        self.assertGreater(public, 0)
        self.assertGreater(keyed, 0)

        openrouter = page.locator('.health-row[data-id="openrouter-free"]')
        groq = page.locator('.health-row[data-id="groq-free"]')
        amd = page.locator('.health-row[data-id="amd-radeon-cloud-free"]')
        self.assertIn("公开可读", openrouter.locator(".badge").first.inner_text())
        self.assertIn("需 KEY", groq.locator(".badge").first.inner_text())
        self.assertIn("未检测", amd.locator(".badge").first.inner_text())

    def test_priority_metrics_and_filters_partition_actionable_providers(self):
        page = self.load_health()
        action_list = page.locator("#action-list")

        for priority in ("p0", "p1", "p2"):
            metric_count = int(page.locator(f"#m-{priority}").inner_text())
            filter_count = int(page.locator(f"#f-{priority}").inner_text())
            self.assertEqual(metric_count, filter_count)

            action_order_raw = action_list.get_attribute(f"data-{priority}-order") or ""
            action_order = [value for value in action_order_raw.split(",") if value]
            self.assertEqual(len(action_order), len(set(action_order)))

            page.locator(f'[data-filter="{priority}"]').click()
            visible_provider_ids = page.locator(
                "#channel-list .health-row"
            ).evaluate_all("els => els.map(el => el.dataset.providerId)")
            self.assertEqual(len(visible_provider_ids), metric_count)

            # Multiple offers can belong to one provider. The health table groups
            # those records by the provider ordering used by today's action list.
            unique_visible = list(dict.fromkeys(visible_provider_ids))
            self.assertEqual(unique_visible, action_order)

    def test_cors_failure_is_aggregated_and_promoted_to_p0(self):
        page = self.load_health()
        page.route("https://openrouter.ai/api/v1/models", lambda route: route.abort())
        page.locator('.health-row[data-id="openrouter-free"] button[data-action="cors"]').click()
        page.wait_for_function(
            """document.querySelector('#action-list .action-item[data-provider-id="openrouter"]')?.innerText.includes('CORS 快检失败')"""
        )
        item = page.locator('#action-list .action-item[data-provider-id="openrouter"]')
        self.assertEqual(item.get_attribute("data-priority"), "P0")
        text = item.inner_text()
        self.assertIn("CORS 快检失败", text)
        self.assertIn("官方信息超过", text)


    def test_limited_filter_excludes_rate_limited_ongoing_offers(self):
        page = self.load_health()
        page.locator('[data-filter="limited"]').click()
        page.wait_for_function(
            """document.querySelector('.filter[data-filter="limited"]')?.classList.contains('active')"""
        )
        visible_ids = page.locator("#channel-list .health-row").evaluate_all(
            "els => els.map(el => el.dataset.id)"
        )

        # These are semantic anchors for explicit trials / limited-time offers.
        # The complete list is data-driven and is expected to grow as discovery
        # adds verified offers.
        for included in (
            "sensecore",
            "xiaomi-mimo-v2-5-tts-free",
            "aliyun-decision-model-preview-free",
            "alibaba-model-studio-intl-free-quota",
        ):
            self.assertIn(included, visible_ids)

        # Ongoing rate-limited/permanent-free entries must never be mistaken for
        # expiring promotions merely because they have request limits.
        for excluded in (
            "google-ai-studio-free",
            "groq-free",
            "mistral-free-mode",
            "cohere-trial-key",
            "modelscope-api-inference-free",
            "agnes-ai-free",
            "catalog-nvidia-nim",
        ):
            self.assertNotIn(excluded, visible_ids)


    def test_health_first_screen_matches_reference_layout_system(self):
        page = self.load_health()
        page.set_viewport_size({"width": 1536, "height": 1024})
        page.wait_for_timeout(50)

        rail = page.locator(".fl-site-rail").bounding_box()
        ribbon = page.locator(".fl-site-ribbon").bounding_box()
        hero = page.locator(".health-hero").bounding_box()
        metrics = page.locator(".summary-grid .metric").evaluate_all(
            "els => els.map(el => ({height: el.getBoundingClientRect().height, radius: getComputedStyle(el).borderRadius, border: getComputedStyle(el).borderTopWidth}))"
        )
        active_filter = page.locator('.filter[data-filter="all"]')
        active_bg = active_filter.evaluate("el => getComputedStyle(el).backgroundColor")
        hero_side_bg = page.locator(".hero-side").evaluate("el => getComputedStyle(el).backgroundImage")

        self.assertIsNotNone(rail)
        self.assertIsNotNone(ribbon)
        self.assertIsNotNone(hero)
        self.assertAlmostEqual(rail["width"], 230, delta=1)
        self.assertAlmostEqual(ribbon["height"], 78, delta=1)
        self.assertLessEqual(hero["height"], 360)
        self.assertEqual(len(metrics), 5)
        self.assertLessEqual(max(m["height"] for m in metrics) - min(m["height"] for m in metrics), 1)
        self.assertTrue(all(m["radius"] == "0px" for m in metrics))
        self.assertTrue(all(m["border"] == "1px" for m in metrics))
        self.assertIn("16, 17, 19", active_bg)
        self.assertIn("free-method-night-window.png", hero_side_bg)


if __name__ == "__main__":
    unittest.main()
