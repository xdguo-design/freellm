"""Skill 实测例子 + 学习文档 (secondary directory of the Skills section)."""
import json
import re
import unittest
from pathlib import Path

from scripts import build_seo_pages as seo

ROOT = Path(__file__).resolve().parents[1]

FIXTURE = {
    "runAt": "2026-10-09 16:40 CST (UTC+08:00)",
    "vantage": "GitHub Actions 托管运行器（美国）",
    "models": [
        {"id": "modelscope", "provider": "魔搭 ModelScope", "model": "deepseek-ai/DeepSeek-V4.1-Flash"},
        {"id": "nvidia", "provider": "NVIDIA NIM", "model": "z-ai/glm-5.3"},
    ],
    "skills": [
        {
            "id": "demo-pass", "name": "Demo Pass", "task": "写一个 <script> 安全的函数", "bestVerdict": "通过",
            "runs": [
                {"provider": "魔搭 ModelScope", "model": "deepseek-ai/DeepSeek-V4.1-Flash", "callOk": True, "verdict": "通过",
                 "score": 10.0, "passedChecks": 3, "totalChecks": 3, "ttftMs": 1500, "totalMs": 25442,
                 "excerpt": "def f():\n    return '<b>'", "judgedBy": "auto",
                 "checks": [{"label": "有 def", "pass": True}, {"label": "能解析", "pass": True, "note": "通过"}, {"label": "有测试", "pass": True}]},
                {"provider": "NVIDIA NIM", "model": "z-ai/glm-5.3", "callOk": False, "verdict": "调用失败", "score": None,
                 "passedChecks": 0, "totalChecks": 3, "totalMs": 274629, "error": "模型返回空内容（可能思考耗尽 max_tokens）",
                 "checks": [], "excerpt": ""},
            ],
        },
        {
            "id": "demo-fail", "name": "Demo Fail", "task": "任务二", "bestVerdict": "调用失败",
            "runs": [
                {"provider": "魔搭 ModelScope", "model": "deepseek-ai/DeepSeek-V4.1-Flash", "callOk": False, "verdict": "调用失败",
                 "score": None, "passedChecks": 0, "totalChecks": 4, "error": "HTTP 429: too many", "checks": [], "excerpt": ""},
            ],
        },
    ],
}
SKILLS = [{"id": "demo-pass", "name": "Demo Pass", "githubUrl": "https://github.com/example/demo"},
          {"id": "demo-fail", "name": "Demo Fail"}]


class SkillExamplesRenderTests(unittest.TestCase):
    def setUp(self):
        self.page = seo.render_skill_examples_page(SKILLS, FIXTURE, "https://freellm.top")

    def article(self, skill_id):
        m = re.search(rf'<article class="skill-example" id="{skill_id}">(.*?)</article>', self.page, re.S)
        self.assertIsNotNone(m, skill_id)
        return m.group(1)

    def test_example_shows_task_output_platform_verdict_time_and_repro(self):
        body = self.article("demo-pass")
        self.assertIn("写一个 &lt;script&gt; 安全的函数", body)  # task input, escaped
        self.assertIn("return &#x27;&lt;b&gt;&#x27;", body)  # real output excerpt, escaped
        self.assertIn("魔搭 ModelScope", body)
        self.assertIn("deepseek-ai/DeepSeek-V4.1-Flash", body)
        self.assertIn("达成情况：通过", body)
        self.assertIn("3/3 项检查通过", body)
        self.assertIn("耗时 25.4s（首字 1.5s）", body)
        self.assertIn("python scripts/eval_skills.py --only demo-pass --models modelscope", body)
        self.assertIn("https://github.com/example/demo", body)

    def test_call_failures_are_labeled_and_never_scored(self):
        body = self.article("demo-pass")
        failed = re.search(r'<div class="skill-run" data-verdict="调用失败">(.*?)复现', body, re.S).group(1)
        self.assertIn('status-failed">调用失败', failed)
        self.assertIn("未获得可评分输出，不计分", failed)
        self.assertIn("模型返回空内容", failed)
        self.assertNotIn("项检查通过", failed)
        self.assertNotIn("<pre>", failed)
        self.assertIn("--models nvidia", body)
        only_failed = self.article("demo-fail")
        self.assertIn("达成情况：调用失败", only_failed)
        self.assertIn("HTTP 429", only_failed)
        self.assertIn('id="call-failed"', self.page)

    def test_summary_counts_and_links(self):
        self.assertIn("通过 1 · 部分通过 0 · 未通过 0 · 调用失败 2", self.page)
        self.assertIn('href="/evaluations/"', self.page)
        self.assertIn('href="/skills/learn/"', self.page)

    def test_empty_results_render_placeholder(self):
        page = seo.render_skill_examples_page(SKILLS, {}, "https://freellm.top")
        self.assertIn("暂无实测结果", page)

    def test_learn_page_lists_only_observed_failure_types(self):
        page = seo.render_skill_learn_page(SKILLS, FIXTURE, "https://freellm.top")
        self.assertIn("空输出（思考耗尽 max_tokens）：1 次", page)
        self.assertIn("限流 HTTP 429：1 次", page)
        self.assertNotIn("单次调用超时被中止", page)
        self.assertIn("SKILL.md", page)
        self.assertIn('href="/skills/examples/"', page)


class SkillSectionTabsTests(unittest.TestCase):
    PAGES = {"skills/index.html": "Skill 目录", "skills/examples/index.html": "实测例子", "skills/learn/index.html": "学习文档"}

    def test_generated_pages_have_secondary_tabs_and_seven_global_nav_items(self):
        for rel, current in self.PAGES.items():
            html = (ROOT / rel).read_text(encoding="utf-8")
            tabs = re.search(r'<nav class="model-section-tabs skill-section-tabs"[^>]*>(.*?)</nav>', html, re.S)
            self.assertIsNotNone(tabs, rel)
            links = re.findall(r'<a href="([^"]+)"', tabs.group(1))
            self.assertEqual(links, ["/skills/", "/skills/examples/", "/skills/learn/", "/evaluations/"], rel)
            self.assertIn(f'aria-current="page">{current}</a>', tabs.group(1), rel)
            rail = re.search(r'<aside class="fl-site-rail".*?</aside>', html, re.S).group(0)
            self.assertEqual(len(re.findall(r'data-site-nav="', rail)), 7, rel)
            self.assertIn('data-site-nav="skills" aria-current="page"', rail, rel)

    def test_tabs_only_in_skills_section(self):
        self.assertNotIn("skill-section-tabs", (ROOT / "models" / "index.html").read_text(encoding="utf-8"))
        self.assertNotIn("skill-section-tabs", (ROOT / "workflow" / "index.html").read_text(encoding="utf-8"))

    def test_sitemap_lists_new_pages(self):
        sitemap = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
        self.assertIn("https://freellm.top/skills/examples/", sitemap)
        self.assertIn("https://freellm.top/skills/learn/", sitemap)

    def test_examples_page_matches_committed_results(self):
        results_path = ROOT / "data" / "evaluations" / "skills-latest.json"
        if not results_path.is_file():
            self.skipTest("no skill eval results yet")
        results = json.loads(results_path.read_text(encoding="utf-8"))
        html = (ROOT / "skills" / "examples" / "index.html").read_text(encoding="utf-8")
        for skill in results["skills"]:
            m = re.search(rf'<article class="skill-example" id="{re.escape(skill["id"])}">(.*?)</article>', html, re.S)
            self.assertIsNotNone(m, skill["id"])
            self.assertIn(f'达成情况：{skill["bestVerdict"]}', m.group(1), skill["id"])
            verdicts = re.findall(r'<div class="skill-run" data-verdict="([^"]+)"', m.group(1))
            self.assertEqual(verdicts, [r["verdict"] for r in skill["runs"]], skill["id"])


if __name__ == "__main__":
    unittest.main()
