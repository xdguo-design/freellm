import unittest
from pathlib import Path


class SkillTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("skills/free-ai-offer-research")

    def test_skill_is_small_and_references_exist(self):
        skill = self.root.joinpath("SKILL.md")
        self.assertLess(len(skill.read_text(encoding="utf-8").splitlines()), 500)
        for name in ("source-policy.md", "offer-schema.md", "review-checklist.md", "report-template.md"):
            self.assertTrue(self.root.joinpath("references", name).exists())

    def test_skill_contains_safety_gate(self):
        text = self.root.joinpath("SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不登录", text)
        self.assertIn("人工审核", text)
        self.assertIn("free-ai-offer-research", text)

    def test_skill_requires_discovery_coverage_and_publish_gate(self):
        text = self.root.joinpath("SKILL.md").read_text(encoding="utf-8")
        self.assertIn("data/providers.json", text)
        self.assertIn("data/candidates.json", text)
        self.assertIn("crawler.cli discover", text)
        self.assertIn("coverage report", text)
        self.assertIn("不直接发布", text)


if __name__ == "__main__":
    unittest.main()
