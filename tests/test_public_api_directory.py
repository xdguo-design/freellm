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

    def test_page_is_linked_and_css_and_scripts_exist(self):
        home = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        links = (ROOT / "links/index.html").read_text(encoding="utf-8")
        self.assertIn('href="/public-api/"', home)
        self.assertIn('href="/public-api/"', links)
        self.assertIn("https://freellm.top/public-api/", (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "css/aurora-public-api.css").is_file())
        self.assertTrue((ROOT / "js/public-api-directory.js").is_file())
        self.assertIn('"public-api",', (ROOT / "scripts/check_internal_links.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
