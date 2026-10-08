import json
import re
import unittest
from pathlib import Path

from scripts.build_tools_index import load_registry

ROOT = Path(__file__).resolve().parents[1]


class P0ConvergenceTests(unittest.TestCase):
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

    def test_home_hotspot_strip_is_compact_and_current(self):
        page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        hot = re.search(r'<section class="prototype-hot".*?</section>', page, re.S)
        self.assertIsNotNone(hot)
        section = hot.group(0)
        self.assertEqual(section.count('class="prototype-hot-card"'), 5)
        self.assertNotIn("prototype-hot-card is-featured", section)
        for slug in (
            "OtvEeIj4z_hGSK_2O5VszA",
            "jMaAj8UILhcoPn3COEbIKg",
            "Z5xlMKnqVR7Ihzzt5bCOZA",
            "Ustvh8JxyRc192SNnSisUg",
            "2-6pjoxc4ln3E83B5UwFJg",
        ):
            self.assertIn(slug, section)
        self.assertIn("模型 / API", section)
        self.assertIn("Agent 观察", section)
        self.assertIn("官方核验", section)
        self.assertNotIn("技术拆解", section)
        self.assertIn("查看今日发现", section)

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
