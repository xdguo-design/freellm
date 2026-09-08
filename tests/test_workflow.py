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
            "data/candidates.json",
            "docs/discovery-latest.md",
            "crawler.cli discover",
            "crawler.cli report",
            "gh pr create",
            "git add -f data/candidates.json",
            "git diff --cached --quiet",
        ):
            self.assertIn(needle, workflow)
        self.assertNotIn("git add data/offers.json", workflow)
        self.assertNotIn("--out data/offers.json", workflow)
