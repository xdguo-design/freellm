import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvaluationFrameworkTests(unittest.TestCase):
    def test_evaluation_framework_has_evidence_levels_and_agent_suites(self):
        payload = json.loads((ROOT / "data" / "evaluation-framework.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "freellm-eval-v1")
        levels = {row["id"] for row in payload["evidenceLevels"]}
        self.assertEqual(levels, {"official_verified", "connectivity_tested", "full_evaluated"})
        suites = {row["id"] for row in payload["suites"]}
        self.assertTrue({"text-api-v1", "coding-agent-v1", "tool-use-v1", "web-research-v1", "multimodal-v1"} <= suites)
        self.assertIn("rawEvidencePath", payload["requiredRunMetadata"])

    def test_ai_radar_uses_only_https_official_registry_urls(self):
        rows = json.loads((ROOT / "data" / "ai-radar-sources.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(rows), 6)
        self.assertTrue(all(row["url"].startswith("https://") for row in rows))
        self.assertEqual(len({row["id"] for row in rows}), len(rows))


if __name__ == "__main__":
    unittest.main()
