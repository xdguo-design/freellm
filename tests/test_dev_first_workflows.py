"""Regression tests for dev-first scheduled repository writes."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITERS = (
    ".github/workflows/daily-log.yml",
    ".github/workflows/update-tools-data.yml",
)


class DevFirstWorkflowTests(unittest.TestCase):
    def test_scheduled_writers_checkout_and_push_only_dev(self):
        for filename in WRITERS:
            with self.subTest(workflow=filename):
                contents = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("schedule:", contents)
                self.assertIn("- uses: actions/checkout@v4\n        with:\n          ref: dev\n", contents)
                self.assertIn("git push origin HEAD:dev", contents)
                self.assertNotIn("git push origin HEAD:main", contents)
                self.assertNotIn("git push origin HEAD:${{ github.ref_name }}", contents)
                self.assertNotIn("\n            git push\n", contents)


if __name__ == "__main__":
    unittest.main()
