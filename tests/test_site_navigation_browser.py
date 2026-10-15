"""Chromium regression: sidebar navigation must retain the document and rail.

Run locally with: python -m unittest tests.test_site_navigation_browser -v
"""
import unittest
from tests.test_e2e_static import ROOT, _LocalSite, start_playwright


class PersistentSidebarBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.started = start_playwright()
        if cls.started is None:
            raise unittest.SkipTest("Playwright Chromium not available")
        cls.manager, cls.browser = cls.started

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.manager.stop()

    def setUp(self):
        self.site = _LocalSite(ROOT)
        self.addCleanup(self.site.stop)

    def test_seven_sidebar_links_do_not_reload_document(self):
        context = self.browser.new_context(locale="zh-CN")
        self.addCleanup(context.close)
        page = context.new_page()
        self.addCleanup(page.close)
        page.set_default_timeout(12000)
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"{self.site.url}/design/free-china-ai-index.html", wait_until="domcontentloaded")
        page.wait_for_function("!!window.FreeLLMNavigation && !!document.querySelector('.fl-site-nav a')")
        page.evaluate("""() => {
            window.__persistentRail = document.querySelector('.fl-site-rail');
            window.__documentSentinel = { key: 'same-document' };
        }""")
        for route, section in (
            ("/models/", "models"),
            ("/skills/", "skills"),
            ("/tools/", "tools"),
            ("/workflow/", "workflow"),
            ("/logs/", "logs"),
            ("/about/", "about"),
            ("/", "home"),
        ):
            with self.subTest(route=route):
                page.locator(f'.fl-site-rail a[data-site-nav="{section}"]').click()
                page.wait_for_function(
                    """([route, section]) =>
                    location.pathname === route &&
                    document.body.dataset.flSection === section &&
                    !window.FreeLLMNavigation.isNavigating()""",
                    arg=[route, section],
                    timeout=12000,
                )
                self.assertTrue(page.evaluate("""() =>
                    window.__persistentRail === document.querySelector('.fl-site-rail') &&
                    window.__documentSentinel?.key === 'same-document'
                """), f"{route} reloaded the page or sidebar")
                self.assertEqual(page.locator('.fl-site-nav a[aria-current="page"]').get_attribute("data-site-nav"), section)
        self.assertFalse(errors, f"Browser errors during sidebar navigation: {errors[:8]}")

    def test_back_and_forward_keep_sidebar(self):
        context = self.browser.new_context(locale="zh-CN")
        self.addCleanup(context.close)
        page = context.new_page()
        self.addCleanup(page.close)
        page.goto(f"{self.site.url}/models/", wait_until="domcontentloaded")
        page.wait_for_function("!!window.FreeLLMNavigation")
        page.evaluate("window.__navigationRail = document.querySelector('.fl-site-rail')")
        page.locator('.fl-site-rail a[data-site-nav="about"]').click()
        page.wait_for_function("location.pathname === '/about/' && !window.FreeLLMNavigation.isNavigating()", timeout=12000)
        page.go_back(wait_until="domcontentloaded")
        page.wait_for_function("location.pathname === '/models/' && document.body.dataset.flSection === 'models' && !window.FreeLLMNavigation.isNavigating()", timeout=12000)
        self.assertTrue(page.evaluate("window.__navigationRail === document.querySelector('.fl-site-rail')"))


if __name__ == "__main__":
    unittest.main()
