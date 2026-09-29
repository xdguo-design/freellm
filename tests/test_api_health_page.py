import unittest
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


if __name__ == "__main__":
    unittest.main()
