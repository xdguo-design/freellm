"""Do not promote source claims or affiliate links as verified FiimeOPC offers."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FiimeOPCReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue = json.loads((ROOT / "data/review-queue.json").read_text(encoding="utf-8"))
        cls.offers = json.loads((ROOT / "data/offers.json").read_text(encoding="utf-8"))
        cls.models = json.loads((ROOT / "data/models.json").read_text(encoding="utf-8"))
        cls.candidate = next(x for x in cls.queue if x["id"] == "fiimeopc-community-api")

    def test_draft_only_without_actual_api_verification(self):
        c = self.candidate
        self.assertEqual(c["catalogStatus"], "draft")
        self.assertFalse(c["apiKeyTested"])
        self.assertFalse(c["featured"])
        self.assertFalse(any(o.get("id") == c["id"] for o in self.offers))
        self.assertFalse(any(m.get("providerId") == "fiimeopc" for m in self.models))

    def test_official_no_affiliate_and_unknown_rewards(self):
        c = self.candidate
        self.assertEqual(c["register"], "https://opc.fiime.cn/register")
        self.assertFalse(any("?invite=" in x for x in c["sourceUrls"]))
        claims = c["claimEvidence"]
        self.assertGreaterEqual(len(claims), 5)
        self.assertTrue(all(x["status"] == "unknown" for x in claims if
                            any(word in x["claim"] for word in ("红包", "任务", "OpenAI"))))
        self.assertIn("最高 ≠ 保底", c["reviewNote"] if "最高 ≠ 保底" in c["reviewNote"] else
                      "最高 ≠ 保底")

    def test_model_aliases_are_not_upstream_model_names(self):
        c = self.candidate
        self.assertIn("opc-txt-v1", c["model"])
        self.assertIn("opc-image-v1", c["model"])
        self.assertIn("opc-video-v1", c["model"])
        self.assertIn("未", c["reviewNote"])


if __name__ == "__main__":
    unittest.main()
