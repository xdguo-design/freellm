import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "css" / "freellm-pastel-ui.css"
SYNC = ROOT / "js" / "freellm-sync.js"
SEO_BUILD = ROOT / "scripts" / "build_seo_pages.py"
STATIC_BUILD = ROOT / "scripts" / "build_static.py"
TOOL_BUILD = ROOT / "scripts" / "build_tool_pages.py"


class SiteVisualSystemTests(unittest.TestCase):
    def test_global_theme_exists_and_covers_major_page_families(self):
        css = THEME.read_text(encoding="utf-8")
        for needle in (
            ".fl-site-rail",
            ".catalog-hero",
            ".skill-card",
            ".workflow-card",
            ".tools-page",
            ".tool-head",
            ".provider-card",
            ".model-directory",
            "@media (max-width:700px)",
            "prefers-reduced-motion",
        ):
            self.assertIn(needle, css)

    def test_shared_runtime_loads_theme_and_site_chrome(self):
        js = SYNC.read_text(encoding="utf-8")
        for needle in (
            "freellm-site-theme",
            "/css/freellm-pastel-ui.css",
            "fl-ui-v2",
            "fl-site-rail",
            "sectionFor(path)",
        ):
            self.assertIn(needle, js)

    def test_generators_persist_theme_link(self):
        self.assertIn("freellm-pastel-ui.css", SEO_BUILD.read_text(encoding="utf-8"))
        self.assertIn("freellm-pastel-ui.css", STATIC_BUILD.read_text(encoding="utf-8"))
        self.assertIn("freellm-pastel-ui.css", TOOL_BUILD.read_text(encoding="utf-8"))

    def test_homepage_renders_visual_shell_without_runtime_javascript(self):
        page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        self.assertIn('class="fl-pastel-ui"', page)
        self.assertIn('class="fl-ui-v2"', page)
        self.assertIn('class="fl-site-rail"', page)
        self.assertIn('class="fl-site-ribbon"', page)
        self.assertIn("freellm-pastel-ui.css?v=20260920b", page)

    def test_generated_pages_render_visual_classes_server_side(self):
        for relative in ("skills/index.html", "models/index.html", "logs/index.html"):
            page = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("fl-pastel-ui", page, relative)
            self.assertIn("fl-ui-v2", page, relative)
            self.assertIn("freellm-pastel-ui.css?v=20260920b", page, relative)

    def test_theme_braces_are_balanced(self):
        css = THEME.read_text(encoding="utf-8")
        depth = 0
        for char in css:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)


if __name__ == "__main__":
    unittest.main()
