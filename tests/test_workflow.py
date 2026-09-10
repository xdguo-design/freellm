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

    def test_daily_log_workflow_persists_detailed_logs_and_only_commits_log_outputs(self):
        workflow = (ROOT / ".github" / "workflows" / "daily-log.yml").read_text(encoding="utf-8")

        for needle in (
            "schedule:",
            "workflow_dispatch:",
            "contents: write",
            "scripts/build_model_catalog.py",
            "python -m crawler.cli log",
            "data/daily-log",
            "scripts/build_seo_pages.py",
            "logs/index.html",
            "git diff --cached --quiet",
        ):
            self.assertIn(needle, workflow)
        self.assertIn("--models-status", workflow)
        self.assertNotIn("git add data/offers.json", workflow)
