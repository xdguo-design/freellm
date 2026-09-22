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
        offers = json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8"))
        models = json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8"))
        provider_pages = list((ROOT / "providers").glob("*/index.html"))
        active_ids = {str(row.get("providerId") or "").strip() for row in models if row.get("providerId")}
        page = (ROOT / "models" / "index.html").read_text(encoding="utf-8")
        for count, label in (
            (len(models), "模型记录"),
            (len(provider_pages), "厂家目录"),
            (len(active_ids), "当前数据 Provider ID"),
            (len(offers), "免费资源"),
        ):
            self.assertIn(f"<strong>{count}</strong><span>{label}", page)
        self.assertNotIn("0 个厂商", page)

    def test_home_models_and_logs_share_latest_snapshot(self):
        offers = json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8"))
        models = json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8"))
        log_paths = sorted((ROOT / "data" / "daily-log").glob("*.json"))
        self.assertTrue(log_paths, "daily log data is required for public freshness metadata")
        latest = json.loads(log_paths[-1].read_text(encoding="utf-8"))
        latest_date = latest["date"]
        year, month, day = latest_date.split("-")

        home = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        models_page = (ROOT / "models" / "index.html").read_text(encoding="utf-8")
        logs_page = (ROOT / "logs" / "index.html").read_text(encoding="utf-8")

        self.assertIn(f"▣ &nbsp;{year} 年 {int(month)} 月 {int(day)} 日", home)
        self.assertIn(f"<strong>{len(models)}</strong><span>模型记录", models_page)
        self.assertIn(f"<strong>{latest_date}</strong>", logs_page)
        self.assertIn(
            f'<span lang="zh-CN">模型</span><span lang="en">Models</span></span><strong>{len(models)}</strong>',
            logs_page,
        )
        self.assertIn(
            f'<span lang="zh-CN">资源</span><span lang="en">Offers</span></span><strong>{len(offers)}</strong>',
            logs_page,
        )

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
        self.assertEqual(len(tests), 68)
        self.assertIn("这些 Skill，能跑的真跑；跑不了的明确写阻塞", page)
        self.assertIn("沙箱真实验收已重跑", page)
        self.assertGreaterEqual(page.count('class="freellm-test-strip'), 68)
        self.assertIn("测试任务", page)
        self.assertIn("查看真实测试任务、限制与评价", page)
        levels = {entry.get("testLevel") for entry in tests.values()}
        self.assertEqual(levels, {"e2e", "artifact", "task", "partial", "blocked"})
        self.assertIn("BLOCKED", page)
        self.assertIn("PARTIAL", page)

    def test_primary_navigation_has_exactly_seven_items(self):
        page = (ROOT / "models" / "index.html").read_text(encoding="utf-8")
        match = re.search(r'<nav class="fl-site-nav">(.*?)</nav>', page, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).count("<a "), 7)
        for label in ("首页", "模型", "Skills", "工具", "工作流", "更新", "关于"):
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
            "models/center/index.html",
            "providers/index.html",
        ):
            page = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('class="model-section-tabs"', page, relative)
            for href in ("/models/", "/models/all/", "/providers/", "/category/api/"):
                self.assertIn(f'href="{href}"', page, relative)


if __name__ == "__main__":
    unittest.main()
