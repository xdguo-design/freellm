from pathlib import Path
import unittest


class WechatNewsWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = Path(".github/workflows/wechat-news.yml").read_text(encoding="utf-8")

    def test_workflow_has_both_triggers_and_serializes_runs(self):
        self.assertIn("schedule:", self.workflow)
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("concurrency:", self.workflow)
        self.assertIn("group: wechat-ai-news", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)
        self.assertIn("contents: write", self.workflow)

    def test_steps_run_in_pipeline_order(self):
        positions = [
            self.workflow.index("wechat-scan"),
            self.workflow.index("wechat-score"),
            self.workflow.index("generate_news_article.py"),
            self.workflow.index("build_seo_pages.py --data"),
            self.workflow.index("Gate - news pipeline unit tests"),
            self.workflow.index("Gate - generated output is current"),
            self.workflow.index("Commit and push the daily article"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_checkout_follows_the_resolved_target_branch(self):
        self.assertIn("ref: ${{ steps.ctx.outputs.target }}", self.workflow)
        self.assertIn('git push origin "HEAD:${TARGET}"', self.workflow)

    def test_daily_run_is_idempotent(self):
        self.assertIn("Idempotency guard", self.workflow)
        self.assertIn('data/news/${{ steps.ctx.outputs.today }}.json', self.workflow)
        self.assertIn("steps.guard.outputs.exists != 'true'", self.workflow)

    def test_commit_requires_a_generated_article(self):
        commit_block = self.workflow.split("Commit and push the daily article", 1)[1]
        self.assertIn("if: steps.article.outputs.written == 'true'", commit_block)
        self.assertIn("git diff --cached --quiet", commit_block)
        # Content is staged explicitly, never with a blanket `git add -A`.
        self.assertNotIn("git add -A", commit_block)

    def test_news_gates_cover_tests_rendering_audit_and_sitemap(self):
        for gate in (
            "Gate - news pipeline unit tests",
            "Gate - generated output is current",
            "Gate - news pages pass the page audit",
            "Gate - sitemap entries resolve to generated files",
        ):
            self.assertIn(gate, self.workflow)
        self.assertIn("tests.test_wechat_news", self.workflow)
        self.assertIn("tests.test_news_pages", self.workflow)
        self.assertIn("tests.test_wechat_news_workflow", self.workflow)
        self.assertIn("--check", self.workflow)

    def test_llm_credentials_come_from_repository_secrets(self):
        self.assertIn("NEWS_LLM_API_KEY: ${{ secrets.SILICONFLOW_API_KEY }}", self.workflow)
        self.assertNotIn("sk-", self.workflow)

    def test_digest_evidence_is_uploaded_but_not_committed(self):
        self.assertIn("data/news-digest/", self.workflow)
        commit_block = self.workflow.split("Commit and push the daily article", 1)[1].split("Upload audit evidence", 1)[0]
        self.assertNotIn("data/news-digest", commit_block)


class DailyCheckNewsPathsTests(unittest.TestCase):
    def test_daily_check_reacts_to_news_changes(self):
        workflow = Path(".github/workflows/daily-check.yml").read_text(encoding="utf-8")
        for path in (
            '"data/news/**"',
            '"news/**"',
            '"data/wechat-news-sources.json"',
            '"data/wechat-news-config.json"',
            '"scripts/generate_news_article.py"',
            '".github/workflows/wechat-news.yml"',
        ):
            self.assertIn(path, workflow)


if __name__ == "__main__":
    unittest.main()
