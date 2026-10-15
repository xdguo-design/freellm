import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.hrefs = []
        self.cards = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "article" and "pub-card" in d.get("class", "").split():
            self.cards.append(d)
        if tag == "a":
            self.hrefs.append(d.get("href", ""))


class PublicApiDirectoryTests(unittest.TestCase):
    def test_static_pages_and_registry_match(self):
        page = (ROOT / "public-api/index.html").read_text(encoding="utf-8")
        sources = json.loads((ROOT / "data/public-api-directory.json").read_text(encoding="utf-8"))
        parser = Cards()
        parser.feed(page)
        self.assertEqual(len(parser.cards), len(sources["resources"]))
        self.assertEqual(len({item["id"] for item in sources["resources"]}), len(sources["resources"]))
        self.assertEqual(sum(c["data-kind"] == "directory" for c in parser.cards), 2)
        self.assertEqual(sum(c["data-kind"] == "official" for c in parser.cards), 4)
        self.assertIn('href="https://freellm.top/public-api/"', page)
        for item in sources["resources"]:
            self.assertIn(item["url"], parser.hrefs)
            self.assertEqual(item["apiProbe"], "not_performed")
        self.assertIn('id="pub-search"', page)
        self.assertIn('id="pub-result-status"', page)
        self.assertIn('id="pub-no-results"', page)
        self.assertIn("未进行实时可用性探测", page)

    def test_independent_review_math_and_pages(self):
        data = json.loads((ROOT / "data/public-api-directory.json").read_text(encoding="utf-8"))
        for resource in data["resources"]:
            review = resource["review"]
            axes = review["axes"]
            expected = axes["evidence"] * 7 + axes["terms"] * 6 + axes["access"] * 4 + axes["privacy"] * 3
            self.assertEqual(review["score"], expected)
            for value in axes.values():
                self.assertIn(value, range(6))
            self.assertEqual(review["liveProbe"], "not_performed")
            self.assertTrue(review["sources"])
            path = ROOT / "public-api" / "reviews" / resource["id"] / "index.html"
            self.assertTrue(path.is_file(), str(path))
            page = path.read_text(encoding="utf-8")
            self.assertIn(f"https://freellm.top/public-api/reviews/{resource['id']}/", page)
            self.assertIn(f"{review['score']}<small>/100</small>", page)
            self.assertIn("UNKNOWN", page)
            self.assertIn("未执行", page)
            for source in review["sources"]:
                self.assertIn(source["url"], page)

    def test_all_review_pages_are_in_generated_sitemap(self):
        data = json.loads((ROOT / "data/public-api-directory.json").read_text(encoding="utf-8"))
        sitemap = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
        generator = (ROOT / "scripts/build_seo_pages.py").read_text(encoding="utf-8")
        self.assertIn("def public_api_review_urls()", generator)
        for resource in data["resources"]:
            self.assertIn(f"https://freellm.top/public-api/reviews/{resource['id']}/", sitemap)

    def test_public_api_feedback_routes_are_reachable(self):
        community = (ROOT / "community/index.html").read_text(encoding="utf-8")
        submit = (ROOT / "submit/index.html").read_text(encoding="utf-8")
        self.assertIn('href="/public-api/"', community)
        self.assertIn('href="/public-api/"', submit)
        self.assertIn("aurora-secondary-hub.css", community)
        self.assertIn("aurora-secondary-hub.css", submit)
        self.assertIn("不要提交完整 Key", community)
        self.assertIn("Bearer Token", submit)

    def test_page_is_linked_and_css_and_scripts_exist(self):
        home = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        links = (ROOT / "links/index.html").read_text(encoding="utf-8")
        self.assertIn('href="/public-api/"', home)
        self.assertIn('href="/public-api/"', links)
        self.assertIn("https://freellm.top/public-api/", (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "css/aurora-public-api.css").is_file())
        self.assertTrue((ROOT / "js/public-api-directory.js").is_file())
        self.assertIn('"public-api",', (ROOT / "scripts/check_internal_links.py").read_text(encoding="utf-8"))
        discovered = json.loads((ROOT / "data/third-party-discovery-sources.json").read_text(encoding="utf-8"))
        self.assertTrue(any(item["id"] == "hcnsec-public-api" and item["enabled"] is False for item in discovered))


if __name__ == "__main__":
    unittest.main()
