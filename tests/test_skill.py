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

    def test_skill_requires_github_peer_discovery_safety_and_provenance(self):
        text = self.root.joinpath("SKILL.md").read_text(encoding="utf-8")
        for needle in (
            "data/github-peers.json",
            "github_peer",
            "needs_review",
            "不执行仓库脚本",
            "commit/path provenance",
            "--github-peers",
        ):
            self.assertIn(needle, text)

    def test_github_peer_discovery_skill_has_workflow_references_and_style_boundary(self):
        root = Path("skills/github-peer-discovery")
        skill = root.joinpath("SKILL.md")
        self.assertLess(len(skill.read_text(encoding="utf-8").splitlines()), 500)
        for name in ("README.md", "references/discovery-checklist.md", "references/style-reference-checklist.md", "references/report-template.md"):
            self.assertTrue(root.joinpath(name).exists())
        text = skill.read_text(encoding="utf-8")
        for needle in (
            "github-peer-discovery",
            "Devansh-365/freellm",
            "commitSha",
            "sourceKind=github_peer",
            "needs_review",
            "不执行仓库脚本",
            "网站风格",
            "不复制",
        ):
            self.assertIn(needle, text)

    def test_freellmapi_is_a_fixed_peer_data_source(self):
        peer_text = Path("data/github-peers.json").read_text(encoding="utf-8")
        discovery_skill = Path("skills/github-peer-discovery/SKILL.md").read_text(encoding="utf-8")
        offer_skill = Path("skills/free-ai-offer-research/SKILL.md").read_text(encoding="utf-8")
        workflow = Path(".github/workflows/daily-check.yml").read_text(encoding="utf-8")

        self.assertIn("https://github.com/tashfeenahmed/freellmapi", peer_text)
        self.assertIn("tashfeenahmed/freellmapi", discovery_skill)
        self.assertIn("tashfeenahmed/freellmapi", offer_skill)
        self.assertIn("--github-peers data/github-peers.json", workflow)

    def test_community_signals_skill_forbids_local_scoring_and_requires_attribution(self):
        root = Path("skills/model-community-signals")
        skill = root.joinpath("SKILL.md")
        self.assertLess(len(skill.read_text(encoding="utf-8").splitlines()), 500)
        for name in ("README.md", "references/source-policy.md", "references/report-template.md"):
            self.assertTrue(root.joinpath(name).exists())
        text = skill.read_text(encoding="utf-8")
        for needle in (
            "model-community-signals",
            "sourcePlatform",
            "sourceType",
            "sourceUrl",
            "capturedAt",
            "不自评分",
            "不跨平台换算",
            "needs_review",
            "不登录",
            "不抓取私人内容",
        ):
            self.assertIn(needle, text)

    def test_workflow_orchestrator_chains_research_signals_design_and_release_gates(self):
        root = Path("skills/free-ai-index-workflow")
        skill = root.joinpath("SKILL.md")
        self.assertLess(len(skill.read_text(encoding="utf-8").splitlines()), 500)
        for name in ("README.md", "references/handoff-contract.md", "references/approval-gates.md", "references/runbook.md"):
            self.assertTrue(root.joinpath(name).exists())
        text = skill.read_text(encoding="utf-8")
        for needle in (
            "free-ai-index-workflow",
            "github-peer-discovery",
            "free-ai-offer-research",
            "model-community-signals",
            "huashu-design",
            "tdd-master",
            "frontend-code-review",
            "needs_review",
            "不自动发布",
            "用户选择",
            "tashfeenahmed/freellmapi",
        ):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
