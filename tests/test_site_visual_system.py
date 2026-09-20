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
