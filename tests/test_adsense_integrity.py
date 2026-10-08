"""AdSense/content-integrity regression tests for static crawlable pages."""
from __future__ import annotations

import json
import re
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class AdsenseIntegrityTests(unittest.TestCase):
    def test_public_contact_page_is_real_and_in_sitemap(self):
        html = (ROOT / "contact/index.html").read_text(encoding="utf-8")
        sitemap = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://freellm.top/contact/">', html)
        self.assertIn('mailto:xdguo0527@gmail.com', html)
        self.assertIn('https://freellm.top/contact/', sitemap)
        self.assertNotIn('noindex', html)

    def test_static_home_does_not_advertise_expired_promotions(self):
        html = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        offers = json.loads((ROOT / "data/offers.json").read_text(encoding="utf-8"))
        for offer in offers:
            if offer.get("status") == "expired":
                self.assertNotIn(f'data-detail="{offer["id"]}"', html)
        self.assertNotIn("300+ 优质模型", html)
        self.assertNotIn("获取社区奖励", html)

    def test_facet_fallback_counts_are_not_placeholders(self):
        html = (ROOT / "design/free-china-ai-index.html").read_text(encoding="utf-8")
        for category in ("free_quota", "model", "credits", "ide", "promo", "student", "web", "download_lowcost"):
            self.assertRegex(html, rf'data-category-count="{category}">[0-9]+</b>')

    def test_skill_evidence_targets_and_anchors_exist(self):
        html = (ROOT / "skills/index.html").read_text(encoding="utf-8")
        urls = set(re.findall(r'"url":"(/skills/test-artifacts/[^"]+)"', html))
        self.assertGreater(len(urls), 0)
        for url in urls:
            path = urlsplit(url)
            target = ROOT / path.path.lstrip("/")
            if path.path.endswith("/"):
                target = target / "index.html"
            with self.subTest(url=url):
                self.assertTrue(target.is_file(), f"Missing target: {url}")
                if path.fragment and target.suffix == ".html":
                    self.assertIn(f'id="{path.fragment}"', target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
