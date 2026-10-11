"""S6 (2026-10-10 content/nav audit): hubs, nav entries, expiry block, placeholders."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "design" / "free-china-ai-index.html"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class NavigationTests(unittest.TestCase):
    def test_global_rail_has_evaluations_and_stays_at_seven(self):
        for rel in ("design/free-china-ai-index.html", "models/index.html", "offers/groq-free/index.html", "evaluations/index.html", "health/index.html"):
            with self.subTest(rel=rel):
                rail = re.search(r'<nav class="fl-site-nav">(.*?)</nav>', _read(rel), re.S).group(1)
                self.assertEqual(rail.count("<a "), 7)
                self.assertIn('href="/evaluations/" data-site-nav="evaluations"', rail)
        evaluations = _read("evaluations/index.html")
        self.assertIn('data-site-nav="evaluations" aria-current="page"', evaluations)
        self.assertIn('data-fl-nav="evaluations"', evaluations)

    def test_homepage_secondary_menu_is_chinese_and_links_hubs(self):
        menu = re.search(r'<nav class="category-seo-links"[^>]*>(.*?)</nav>', _read("design/free-china-ai-index.html"), re.S).group(1)
        labels = re.findall(r'>([^<]+)</a>', menu)
        self.assertTrue(labels)
        for label in labels:
            self.assertRegex(label, r"[\u4e00-\u9fff]", f"secondary menu label must be Chinese: {label}")
        for href in ("/guides/getting-started/", "/guides/", "/offers/", "/category/"):
            self.assertIn(f'href="{href}"', menu)
        i18n = _read("js/homepage-i18n.js")
        for key in re.findall(r'data-i18n="([^"]+)"', menu):
            self.assertGreaterEqual(i18n.count(f"{key}:"), 2, f"{key} needs zh and en labels")

    def test_model_tabs_link_offers_hub(self):
        self.assertIn('<a href="/offers/">全部优惠</a>', _read("models/all/index.html"))


class HubPageTests(unittest.TestCase):
    def test_hubs_exist_indexable_and_list_real_records(self):
        offers = json.loads(_read("data/offers.json"))
        public = [offer for offer in offers if offer.get("status") != "needs_review"]
        hub = _read("offers/index.html")
        self.assertIn("index,follow", hub)
        for offer in public:
            self.assertIn(f'href="https://freellm.top/offers/{offer["id"]}/"', hub, offer["id"])
        self.assertIn(f"共 {len(public)} 条公开资源记录", hub)
        category = _read("category/index.html")
        for slug in ("free-quota", "free-ide", "api"):
            self.assertIn(f'href="https://freellm.top/category/{slug}/"', category)
        guides = _read("guides/index.html")
        self.assertIn('href="https://freellm.top/guides/getting-started/"', guides)
        self.assertLess(guides.index("getting-started"), guides.index("china-free-ai-api"))
        for page in (hub, category, guides):
            self.assertNotIn("Follow the model-specific steps", page)
            self.assertNotIn("正在计算", page)

    def test_offer_pages_drop_quick_start_placeholder(self):
        for page in (ROOT / "offers").glob("*/index.html"):
            self.assertNotIn("Follow the model-specific steps to register", page.read_text(encoding="utf-8"), page)


class ExpiryBoardTests(unittest.TestCase):
    def test_expiry_block_lists_only_offers_within_14_days_or_is_hidden(self):
        from datetime import date

        html = _read("design/free-china-ai-index.html")
        section = re.search(r'<section id="expiring-soon"[^>]*>.*?</section>', html, re.S).group(0)
        as_of = re.search(r'data-expiry-as-of="([^"]+)"', section).group(1)
        self.assertEqual(as_of, json.loads(_read("data/scan-summary.json"))["date"])
        start = date.fromisoformat(as_of)
        expected = sorted(
            offer["id"]
            for offer in json.loads(_read("data/offers.json"))
            if offer.get("status") == "verified"
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(offer.get("expires_at") or ""))
            and 0 <= (date.fromisoformat(offer["expires_at"]) - start).days <= 14
        )
        listed = sorted(re.findall(r'href="/offers/([^"/]+)/">查看官方条件', section))
        self.assertEqual(listed, expected[:6])
        if not expected:
            self.assertIn(" hidden", section.split(">", 1)[0])
        self.assertNotIn("正在核验活动到期日", section)

    def test_render_expiry_board_hides_when_empty(self):
        from scripts.build_static import render_expiry_board

        offers = [
            {"id": "a", "status": "verified", "expires_at": "2026-10-20", "title": "A"},
            {"id": "b", "status": "verified", "expires_at": "2026-11-30", "title": "B"},
            {"id": "c", "status": "expired", "expires_at": "2026-10-12", "title": "C"},
        ]
        shown = render_expiry_board(offers, "2026-10-11")
        self.assertIn("/offers/a/", shown)
        self.assertNotIn("/offers/b/", shown)
        self.assertNotIn("/offers/c/", shown)
        empty = render_expiry_board(offers, "2026-12-15")
        self.assertIn("hidden", empty)
        self.assertNotIn("即将到期", empty)
        script = _read("js/offer-expiry-board.js")
        self.assertIn("board.hidden=true", script)
        self.assertNotIn("x.days<=30", script)


if __name__ == "__main__":
    unittest.main()
