import json
import re
import unittest
from pathlib import Path

from scripts.build_tools_index import load_registry

ROOT = Path(__file__).resolve().parents[1]


class P0ConvergenceTests(unittest.TestCase):
    def test_p1_5_unfinished_dark_mode_is_hidden_and_light_palette_is_accessible(self):
        nav = (ROOT / "js" / "site-navigation.js").read_text(encoding="utf-8")
        menu = (ROOT / "css" / "primary-menu.css").read_text(encoding="utf-8")
        core = (ROOT / "css" / "aurora-core.css").read_text(encoding="utf-8")
        home = (ROOT / "css" / "aurora-home.css").read_text(encoding="utf-8")

        # The old toggle changed root variables while many cards stayed white.
        # Remove the control from navigation and hide static prototype controls.
        self.assertNotIn("themeButton", nav)
        self.assertIn("removeAttribute('data-theme')", nav)
        for cls in (".fl-site-theme-toggle", ".prototype-theme-toggle", ".ml-rail-theme", ".theme-toggle"):
            self.assertIn(cls, menu)
        self.assertIn("display: none !important", menu)

        for css in (core, home):
            self.assertIn("--fl-theme-surface:var(--aurora-surface)", css)
            self.assertIn("--fl-theme-ink:var(--aurora-ink)", css)
            self.assertIn("--aurora-ink-3:#526a86", css)
        for cls in ("blockquote", ".callout", ".about-stat-card", ".weekly-scan-cards > article"):
            self.assertIn(cls, core)

        def luminance(value):
            channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
            return sum(x * weight for x, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

        def contrast(foreground, background):
            high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
            return (high + 0.05) / (low + 0.05)

        # WCAG AA for normal-sized text over the palest card/page surfaces.
        for foreground in ("#102745", "#526a86"):
            for background in ("#ffffff", "#f5f9ff", "#f1f7ff"):
                self.assertGreaterEqual(contrast(foreground, background), 4.5)

    def test_tools_first_paint_is_real_static_content(self):
        _, tools = load_registry()
        page = (ROOT / "tools" / "index.html").read_text(encoding="utf-8")
        self.assertGreater(len(tools), 0)
        self.assertIn(f'id="tool-total">{len(tools)}</strong>', page)
        self.assertNotIn("显示 0 / 0", page)
        self.assertNotIn('id="tool-total">0</strong>', page)
        self.assertGreaterEqual(page.count('class="tool-card static-tool-card"'), 24)
        first_id = tools[0]["id"]
        self.assertIn(f'href="/tools/tools/{first_id}.html"', page)

    def test_p1_3_tool_use_case_links_and_runtime_filter_contract(self):
        page = (ROOT / "tools" / "index.html").read_text(encoding="utf-8")
        runtime = (ROOT / "tools" / "js" / "app.js").read_text(encoding="utf-8")
        _, tools = load_registry()
        tool_ids = {tool["id"] for tool in tools}
        tool_cats = {tool["cat"] for tool in tools}
        category_links = {
            "dev": "开发工具",
            "productivity": "生产力",
            "analytics": "数据分析",
            "media": "语音视频",
            "design": "设计创作",
        }
        for key, label in category_links.items():
            self.assertIn(
                f'data-use-case-cat="{key}" href="/tools/?category={key}">{label}</a>',
                page,
            )
        self.assertIn('data-static-tool-cat="dev"', page)
        self.assertIn("new URLSearchParams(location.search).get('category')", runtime)
        self.assertIn("if (!matchesCategory(t, activeCat)) return false;", runtime)
        self.assertIn("useCaseCount(requestedCategory) > 0", runtime)
        self.assertIn("category=dev", page)
        # Virtual groups may never resolve to an unfiltered directory or an empty result.
        self.assertTrue({"text", "datetime", "util"} <= tool_cats)
        self.assertTrue({"css", "image"} <= tool_cats)
        self.assertTrue({"tts", "audio-record", "video2gif", "spectrum", "whitenoise"} <= tool_ids)
        self.assertTrue({"csv-json", "csv-format", "excel-convert", "jsonpath"} <= tool_ids)

    def test_models_landing_uses_four_explicit_data_counts(self):
        models = json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8"))
        page = (ROOT / "models" / "index.html").read_text(encoding="utf-8")
        all_models = (ROOT / "models" / "all" / "index.html").read_text(encoding="utf-8")
        curated_count = page.count('class="featured-model-card"')
        self.assertIn("精选模型", page)
        self.assertIn(f"({curated_count})", page)
        self.assertIn('href="/models/all/"', page)
        self.assertGreaterEqual(len(models), curated_count)
        self.assertIn(f"{len(models)}+", page)
        self.assertIn("模型目录", all_models)

    def test_home_models_logs_and_about_share_canonical_daily_scan(self):
        summary = json.loads((ROOT / "data" / "scan-summary.json").read_text(encoding="utf-8"))
        logs = sorted((ROOT / "data" / "daily-log").glob("*.json"))
        self.assertTrue(logs, "daily log data is required for public freshness metadata")
        latest = json.loads(logs[-1].read_text(encoding="utf-8"))
        self.assertEqual(summary["date"], latest["date"])
        self.assertEqual(summary["source"], f'/data/daily-log/{latest["date"]}.json')
        self.assertEqual(summary["models"], len(latest["observed"]["models"]))
        self.assertEqual(summary["offers"], len(latest["observed"]["offers"]))
        events = [*latest.get("events", []), *latest.get("curatedEvents", [])]
        fresh = [event for event in events if event.get("eventType") in {"new", "new_route"}]
        self.assertEqual(summary["newCount"], len(fresh))

        home = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        logs_page = (ROOT / "logs" / "index.html").read_text(encoding="utf-8")
        about = (ROOT / "about" / "index.html").read_text(encoding="utf-8")
        year, month, day = summary["date"].split("-")
        self.assertIn(f"▣ &nbsp;{year} 年 {int(month)} 月 {int(day)} 日", home)
        for page in (home, logs_page, about):
            self.assertIn("/js/scan-trust.js", page)

        # Static first paint must agree with runtime data, including the original About cards.
        for key in ("models", "offers"):
            self.assertIn(
                f'data-scan-stat="{key}">{summary[key]}</strong>',
                about,
            )
        self.assertNotIn("已验证的免费资源</span>", about)
        for label, key in (("今日新增", "newCount"), ("模型记录", "models"), ("已收录资源", "offers")):
            self.assertRegex(
                logs_page,
                rf"<span>{label}</span><strong>{summary[key]}</strong>",
            )
        self.assertIn(f"<strong>{summary['date']}</strong>", logs_page)

        # Directory counts are a separate layer and must not overwrite scan counts.
        models = json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8"))
        models_page = (ROOT / "models" / "index.html").read_text(encoding="utf-8")
        all_models = (ROOT / "models" / "all" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/models/all/"', models_page)
        self.assertIn(f"{len(models)}", all_models)

    def test_home_surfaces_high_intent_seo_guides_above_catalog(self):
        page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        hero_end = page.index("</section>", page.index('class="catalog-hero"'))
        hero = page[page.index('class="catalog-hero"'):hero_end]
        for href in (
            "/guides/free-openai-compatible-apis/",
            "/guides/china-free-ai-api/",
            "/guides/free-openai-api-alternatives/",
            "/guides/free-ai-coding-tools/",
        ):
            self.assertIn(f'href="{href}"', hero)

    def test_skill_page_prioritizes_freellm_testing(self):
        tests = json.loads((ROOT / "data" / "skill-tests.json").read_text(encoding="utf-8"))["entries"]
        page = (ROOT / "skills" / "index.html").read_text(encoding="utf-8")
        skills = json.loads((ROOT / "data" / "skills.json").read_text(encoding="utf-8"))
        self.assertEqual(len(tests), len(skills))
        self.assertIn("AGENT SKILLS / WORKFLOWS", page)
        self.assertIn('id="skills-title"', page)
        self.assertIn("沙箱真实验收已重跑", page)
        self.assertGreaterEqual(page.count('class="freellm-test-strip'), len(tests))
        self.assertIn("测试任务", page)
        self.assertIn("查看真实测试任务、限制与评价", page)
        levels = {entry.get("testLevel") for entry in tests.values()}
        self.assertEqual(levels, {"e2e", "artifact", "task", "partial", "blocked"})
        self.assertIn("BLOCKED", page)
        self.assertIn("PARTIAL", page)

    def test_home_latest_scan_strip_has_real_metrics_without_invented_growth(self):
        page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        summary = json.loads((ROOT / "data" / "scan-summary.json").read_text(encoding="utf-8"))
        section = re.search(
            r'<section id="weekly-changes"[^>]*>.*?</section>', page, re.S
        )
        self.assertIsNotNone(section, "latest scan is required above the catalog")
        weekly = section.group(0)
        self.assertEqual(weekly.count("<article>"), 4)
        for key in ("newCount", "newModels", "models", "offers"):
            self.assertIn(f'data-scan-stat="{key}">{summary[key]}</strong>', weekly)
        self.assertIn(f'<span data-scan-date>{summary["date"]}</span>', weekly)
        self.assertIn('href="/logs/"', weekly)
        self.assertIn("未建立可比较的同口径历史基线", weekly)
        self.assertNotRegex(weekly, r"(?:↑|↓|环比\\s*[+\\-]?\\d+%|较上周\\s*[+\\-]?\\d+%)")
        self.assertNotIn('class="prototype-hot-card"', weekly)

    def test_primary_navigation_has_exactly_seven_items(self):
        page = (ROOT / "models" / "index.html").read_text(encoding="utf-8")
        match = re.search(r'<nav class="fl-site-nav">(.*?)</nav>', page, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).count("<a "), 7)
        for label in ("首页", "模型", "Skills", "工具", "工作流", "今日发现", "关于"):
            self.assertIn(f"<span>{label}</span>", match.group(1))

    def test_no_duplicate_global_top_nav_on_key_pages(self):
        for relative in (
            "design/free-china-ai-index.html",
            "models/index.html",
            "skills/index.html",
            "tools/index.html",
            "about/index.html",
            "links/index.html",
            "privacy/index.html",
            "terms/index.html",
            "favorites/index.html",
            "submit/index.html",
        ):
            page = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('class="fl-site-rail"', page, relative)
            self.assertNotIn('class="top-nav"', page, relative)

    def test_model_subpages_use_internal_tabs(self):
        for relative in (
            "models/index.html",
            "models/all/index.html",
            "providers/index.html",
        ):
            page = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('class="model-section-tabs', page, relative)
            for href in ("/models/", "/models/all/", "/providers/", "/category/api/"):
                self.assertIn(f'href="{href}"', page, relative)

    def test_model_center_legacy_route_redirects_to_featured_models(self):
        page = (ROOT / "models" / "center" / "index.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh" content="0;url=/models/"', page)
        self.assertIn('href="/models/"', page)


if __name__ == "__main__":
    unittest.main()
