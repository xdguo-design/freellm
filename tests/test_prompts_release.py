"""Release gate for the newly published, previously broken Prompts index."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PromptReleaseTests(unittest.TestCase):
    def test_prompt_page_exists_with_real_templates_and_assets(self):
        page = ROOT / "prompts" / "index.html"
        self.assertTrue(page.exists(), "The /prompts/ sitemap and nav link must resolve")
        html = page.read_text(encoding="utf-8")
        self.assertIn("24 个模板", html)
        self.assertEqual(html.count('data-prompt-card data-prompt-id='), 24)
        self.assertIn('id="prompt-template-data"', html)
        self.assertIn("/js/prompt-library.js", html)
        self.assertIn("/css/prompt-library.css", html)
        self.assertIn("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js", html)
        self.assertIn('<link rel="canonical" href="https://freellm.top/prompts/">', html)
        self.assertTrue((ROOT / "js" / "prompt-library.js").exists())
        self.assertTrue((ROOT / "css" / "prompt-library.css").exists())

    def test_global_navigation_has_the_same_nine_routes_on_generated_pages(self):
        required = ["home", "models", "skills", "prompts", "public-api", "tools", "workflow", "logs", "about"]
        for path in ["prompts/index.html", "skills/index.html", "models/index.html", "offers/requesty-free/index.html"]:
            html = (ROOT / path).read_text(encoding="utf-8")
            nav = re.search(r'<nav class="fl-site-nav">(.*?)</nav>', html, re.S)
            self.assertIsNotNone(nav, path)
            self.assertEqual(re.findall(r'data-site-nav="([^"]+)"', nav.group(1)), required, path)


if __name__ == "__main__":
    unittest.main()
