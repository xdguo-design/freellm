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
OFFERS_PATH = ROOT / "data" / "offers.json"


def read_offers() -> list:
    return json.loads(OFFERS_PATH.read_text(encoding="utf-8"))


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
            'id="offer-data"', 'id="offerRows"', 'id="ld-dynamic"',
            "renderOffers", "loadOffers", "showDataError",
            'id="ideHighlightGrid"', 'id="downloadList"', 'id="lastChecked"',
        ):
            self.assertIn(needle, self.html)

    def test_hardcoded_offers_are_gone(self):
        self.assertNotIn("const offers = {", self.html)
        self.assertNotIn("slice(0, 4)", self.html)
        static_articles = re.findall(r'<article class="offer" data-type="(?!")', self.html)
        self.assertEqual(static_articles, [])

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
        for needle in ("crawler.cli validate", "crawler.cli scan", "crawler.cli discover", "crawler.cli coverage", "upload-artifact", "if: always()"):
            self.assertIn(needle, self.text)

    def test_workflow_never_pushes_public_data(self):
        self.assertNotIn("git push", self.text)
        self.assertNotIn("git commit", self.text)


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
        self.assertEqual(self.visible_offers(page), 17)
        self.assertEqual(page.locator(".hero-side .big").inner_text(), "17")
        self.assertEqual(page.locator(".tabs [data-filter='ide'] em").inner_text(), "08")
        self.assertEqual(page.locator("#ideHighlightGrid .ide-highlight-card").count(), 8)
        self.assertIn("Browse all 8 free IDEs", page.locator("#ideHighlightButton").inner_text())
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_file_protocol_search_filter_and_drawer(self):
        page = self.new_page()
        page.goto(HTML_PATH.as_uri())
        page.wait_for_function("document.body.dataset.dataSource === 'embedded'")

        page.click("#ideHighlightButton")
        self.assertEqual(self.visible_offers(page), 4)

        page.fill("#search", "Qwen3")
        self.assertEqual(self.visible_offers(page), 1)

        page.fill("#search", "")
        page.click(".offer[data-detail='comate'] .row-arrow")
        page.wait_for_selector("#drawer.open")
        register = page.locator("#drawerRegister")
        self.assertEqual(register.get_attribute("href"), "https://comate.baidu.com/zh")
        self.assertIn("Auto-Free", page.locator("#drawerTitle").inner_text())
        page.keyboard.press("Escape")
        self.assertNotIn("open", page.locator("#drawer").get_attribute("class"))
        self.assertEqual(len(page.problems), 0, page.problems)

    def test_http_protocol_prefers_network_json(self):
        page = self.new_page()
        page.goto(f"{self.site.url}/{self.PAGE_URL_PATH}")
        page.wait_for_function("document.body.dataset.dataSource === 'network'")
        self.assertEqual(self.visible_offers(page), 17)
        item_list = page.evaluate("JSON.parse(document.getElementById('ld-dynamic').textContent)['@graph'][0]['itemListElement']")
        self.assertEqual(len(item_list), 17)
        self.assertEqual(item_list[3]["name"], "Baidu Comate · Auto-Free mode")
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
            self.assertEqual(self.visible_offers(page), 17)
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
            self.assertEqual(page.locator("#resultCount").inner_text(), "Showing 0 offers")


if __name__ == "__main__":
    unittest.main()
