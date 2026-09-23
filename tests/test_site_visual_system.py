import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "css" / "freellm-pastel-ui.css"
AURORA = ROOT / "css" / "freellm-aurora.css"
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
            ".fl-site-theme-toggle",
            ".fl-skip-link",
            "overflow-x:auto !important",
            "@media (max-width:480px)",
            "--fl-content-max:1220px",
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
            "installSiteUiPolish",
            "fl-site-theme-toggle",
            "fl-skip-link",
            "rel.add('noopener')",
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
        self.assertIn("freellm-pastel-ui.css?v=20260920c", page)

    def test_aurora_phase_one_is_homepage_only(self):
        css = AURORA.read_text(encoding="utf-8")
        page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        self.assertIn("FreeLLM Aurora v1", css)
        self.assertIn("--au-page:#f4f9ff", css)
        self.assertIn("body.theme-aurora[data-fl-section=\"home\"] .catalog-hero", css)
        self.assertIn("#catalog-offer-rows.offer-grid", css)
        self.assertIn("@media(max-width:700px)", css)
        self.assertIn('class="fl-ui-v2 theme-aurora"', page)
        self.assertIn("freellm-aurora.css?v=20260923a", page)

        for relative in ("models/index.html", "skills/index.html", "tools/index.html", "skills/lab/index.html", "logs/index.html", "about/index.html"):
            other = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("freellm-aurora.css", other, relative)
            self.assertNotIn("theme-aurora", other, relative)

    def test_homepage_information_hierarchy_is_freshness_then_catalog_then_student(self):
        page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        positions = {
            "today": page.index('class="today-latest"'),
            "offers": page.index('id="catalog-offers"'),
            "student": page.index('id="student-offers"'),
            "compare": page.index('id="catalog-compare"'),
        }
        self.assertLess(positions["today"], positions["offers"])
        self.assertLess(positions["offers"], positions["student"])
        self.assertLess(positions["student"], positions["compare"])

    def test_generated_pages_render_visual_classes_and_chrome_server_side(self):
        for relative in ("skills/index.html", "models/index.html", "logs/index.html", "tools/index.html", "about/index.html", "submit/index.html"):
            page = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("fl-pastel-ui", page, relative)
            self.assertIn("fl-ui-v2", page, relative)
            self.assertIn("freellm-pastel-ui.css?v=20260920c", page, relative)
            self.assertIn('class="fl-site-rail"', page, relative)
            self.assertIn('class="fl-site-ribbon"', page, relative)
            self.assertNotIn('class="top-nav"', page, relative)


    def test_tool_registry_ids_are_unique_and_every_tool_has_a_page(self):
        source = (ROOT / "tools" / "js" / "tools.js").read_text(encoding="utf-8")
        start = source.index("const TOOLS = [")
        end = source.index("];", start)
        ids = re.findall(r"id:\s*'([^']+)'", source[start:end])
        self.assertEqual(len(ids), len(set(ids)), "tools/js/tools.js contains duplicate tool ids")

        pages = {path.stem for path in (ROOT / "tools" / "tools").glob("*.html")}
        self.assertEqual(set(ids), pages, "tool registry and generated tool pages drifted")

        index = (ROOT / "tools" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'<strong id="tool-total">{len(ids)}</strong>', index)
        self.assertIn(f'显示 24 / {len(ids)}', index)

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
