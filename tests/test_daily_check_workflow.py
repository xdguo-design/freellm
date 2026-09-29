from pathlib import Path
import unittest


class DailyCheckWorkflowTests(unittest.TestCase):
    def test_wusrouter_audit_is_uploaded_and_review_queue_is_not_self_overwritten(self):
        workflow = Path(".github/workflows/daily-check.yml").read_text(encoding="utf-8")
        self.assertIn("Audit WusRouter public pricing and API compatibility", workflow)
        self.assertIn(".tmp/provider-audit/", workflow)
        self.assertIn("WUSROUTER_API_KEY", workflow)
        self.assertNotIn(
            "diff --previous data/offers.json --current data/offers.json --out data/review-queue.json",
            workflow,
        )
        self.assertIn("python -m json.tool data/review-queue.json", workflow)


if __name__ == "__main__":
    unittest.main()
