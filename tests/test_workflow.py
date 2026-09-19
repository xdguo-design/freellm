from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryWorkflowTests(unittest.TestCase):
    def test_discovery_workflow_creates_batch_review_pr_without_publishing_offers(self):
        workflow = (ROOT / ".github" / "workflows" / "discovery-pr.yml").read_text(encoding="utf-8")

        for needle in (
            "schedule:",
            "workflow_dispatch:",
            "contents: write",
            "pull-requests: write",
            "data/discovery-queries.json",
            "data/third-party-discovery-sources.json",
            "data/candidates.json",
            "docs/discovery-latest.md",
            "crawler.cli discover",
            "--third-party-sources data/third-party-discovery-sources.json",
            "crawler.cli report",
            "gh pr create",
            "git add -f data/candidates.json",
            "git diff --cached --quiet",
        ):
            self.assertIn(needle, workflow)
        self.assertNotIn("git add data/offers.json", workflow)
        self.assertNotIn("--out data/offers.json", workflow)

    def test_daily_log_workflow_persists_detailed_logs_and_commits_regenerated_outputs(self):
        workflow = (ROOT / ".github" / "workflows" / "daily-log.yml").read_text(encoding="utf-8")

        for needle in (
            "schedule:",
            "workflow_dispatch:",
            "contents: write",
            "scripts/build_model_catalog.py",
            "python -m crawler.cli log",
            "--merge",
            "data/daily-log",
            "scripts/build_seo_pages.py",
            "scripts/check_internal_links.py",
            # 全量提交再生产物：只提交日志会让模型/分类页和分片 sitemap 与数据漂移。
            "offers category guides models providers logs skills",
            "sitemap-pages.xml",
            "feed.xml",
            "git diff --cached --quiet",
        ):
            self.assertIn(needle, workflow)
        self.assertIn("--models-status", workflow)
        # 每日更新只保留北京时间 07:00 的一次调度（UTC 23:00）。
        self.assertIn('cron: "0 23 * * *"', workflow)
        self.assertNotIn("git add data/offers.json", workflow)
