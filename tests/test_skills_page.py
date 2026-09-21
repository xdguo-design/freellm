import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_PATH = ROOT / "data" / "skills.json"
RECIPES_PATH = ROOT / "data" / "skill-recipes.json"
STYLES_PATH = ROOT / "data" / "skill-styles.json"
TESTS_PATH = ROOT / "data" / "skill-tests.json"
CONTENT_DIR = ROOT / "data" / "skill-content"


class SkillsDataTests(unittest.TestCase):
    def setUp(self):
        self.skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))

    def test_catalog_contains_verified_entries_with_unique_ids(self):
        self.assertGreaterEqual(len(self.skills), 30, "catalog must keep a useful body of verified skills")
        ids = [item["id"] for item in self.skills]
        self.assertEqual(len(ids), len(set(ids)), "skill ids must be unique")

    def test_every_entry_is_source_verified_and_carries_content(self):
        for item in self.skills:
            prefix = f"skill {item.get('id')}"
            self.assertEqual(item.get("status"), "verified", f"{prefix} must be verified")
            self.assertEqual(item.get("linkCheck"), "ok", f"{prefix} must have a reachable source")
            self.assertEqual(item.get("source"), "github-verified", f"{prefix} must be sourced from a verified repo")
            self.assertTrue(str(item.get("githubUrl", "")).startswith("https://github.com/"), prefix)
            self.assertTrue(str(item.get("contentUrl", "")).startswith("https://"), prefix)
            self.assertLessEqual(str(item.get("contentPath", "")).count("/"), 2, prefix)
            content_file = ROOT / "data" / str(item.get("contentPath", "missing/missing"))
            self.assertTrue(content_file.is_file(), f"{prefix} must have a local SKILL.md copy")
            self.assertGreater(content_file.stat().st_size, 0, prefix)
            stats = item.get("repoStats") or {}
            self.assertIsInstance(stats.get("stars"), int, f"{prefix} must record GitHub stars")

    def test_every_entry_has_a_non_empty_chinese_display_description(self):
        translations_path = ROOT / "data" / "skills-i18n.json"
        translations = json.loads(translations_path.read_text(encoding="utf-8"))
        self.assertEqual(set(translations), {item["id"] for item in self.skills})
        for skill_id, description in translations.items():
            self.assertIsInstance(description.get("description_zh"), str, skill_id)
            self.assertTrue(description["description_zh"].strip(), skill_id)

    def test_reviews_are_attributed_and_linked(self):
        for item in self.skills:
            for review in item.get("reviews") or []:
                self.assertTrue({"source", "url", "quote"} <= review.keys(), item["id"])
                self.assertTrue(str(review["url"]).startswith("https://"), item["id"])
                self.assertTrue(str(review["quote"]).strip(), item["id"])
                self.assertIn(review.get("sentiment"), {"positive", "mixed", "negative", "neutral"}, item["id"])

    def test_categories_stay_inside_the_supported_set(self):
        from scripts.build_seo_pages import SKILL_CATEGORY_DEFINITIONS

        categories = {item["category"] for item in self.skills}
        self.assertTrue(categories, "catalog must use at least one category")
        self.assertLessEqual(categories, set(SKILL_CATEGORY_DEFINITIONS))



class SkillBenchmarkDataTests(unittest.TestCase):
    def setUp(self):
        self.skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
        self.payload = json.loads(TESTS_PATH.read_text(encoding="utf-8"))
        self.entries = self.payload["entries"]

    def test_every_skill_has_a_freellm_test_record(self):
        self.assertEqual({item["id"] for item in self.skills}, set(self.entries))
        self.assertEqual(len(self.entries), len(self.skills))

    def test_test_records_never_fake_unexecuted_scores(self):
        scored = 0
        allowed = {"e2e", "task", "artifact", "partial", "blocked"}
        for skill_id, entry in self.entries.items():
            level = entry.get("testLevel")
            self.assertIn(level, allowed, skill_id)
            self.assertTrue(str(entry.get("testedAt") or "").strip(), skill_id)
            self.assertTrue(str(entry.get("environment") or "").strip(), skill_id)
            self.assertTrue(str(entry.get("task") or "").strip(), skill_id)
            self.assertTrue(str(entry.get("evaluation") or "").strip(), skill_id)
            if level in {"blocked", "partial"}:
                self.assertIsNone(entry.get("score"), skill_id)
            else:
                self.assertIsInstance(entry.get("score"), (int, float), skill_id)
                scored += 1
                self.assertGreaterEqual(entry["score"], 0, skill_id)
                self.assertLessEqual(entry["score"], 10, skill_id)
        self.assertEqual(scored, 34)

    def test_internal_evidence_targets_exist(self):
        for skill_id, entry in self.entries.items():
            for evidence in entry.get("evidence") or []:
                url = evidence if isinstance(evidence, str) else evidence.get("url")
                if not url or not url.startswith("/skills/test-artifacts/"):
                    continue
                target = ROOT / url.lstrip("/")
                if url.endswith("/"):
                    target = target / "index.html"
                self.assertTrue(target.is_file(), f"{skill_id}: missing evidence {url}")


class SkillStylesDataTests(unittest.TestCase):
    def setUp(self):
        self.skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
        self.entries = json.loads(STYLES_PATH.read_text(encoding="utf-8"))["entries"]

    def test_every_skill_has_a_presentation_style_entry(self):
        self.assertEqual({item["id"] for item in self.skills}, set(self.entries))

    def test_style_entries_are_shaped_for_rendering(self):
        for skill_id, entry in self.entries.items():
            self.assertTrue(str(entry["format"]).strip(), skill_id)
            self.assertTrue(str(entry["summary"]).strip(), skill_id)
            self.assertIsInstance(entry["hasStyles"], bool, skill_id)
            for item in entry.get("items") or []:
                self.assertIsInstance(item, str, skill_id)
                self.assertTrue(item.strip(), skill_id)

    def test_visual_skills_expose_named_styles(self):
        named = sorted(skill_id for skill_id, entry in self.entries.items() if entry.get("items"))
        self.assertGreaterEqual(len(named), 15)
        self.assertIn("lewislulu-html-ppt-skill", named)
        self.assertIn("rendercv-rendercv", named)

    def test_style_validation_reports_unknown_and_missing_ids(self):
        from scripts.build_seo_pages import validate_skill_styles

        entry = {"format": "f", "summary": "s", "hasStyles": True}
        errors = validate_skill_styles({"entries": {"missing-skill": entry}}, [{"id": "known"}])
        self.assertTrue(any("unknown skill id" in error for error in errors))
        errors = validate_skill_styles({"entries": {}}, [{"id": "known"}])
        self.assertTrue(any("missing" in error for error in errors))


class RecipeDataTests(unittest.TestCase):
    def test_skill_recipes_are_curated_and_reference_existing_components(self):
        recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
        skill_ids = {item["id"] for item in json.loads(SKILLS_PATH.read_text(encoding="utf-8"))}

        self.assertEqual(len(recipes), 6)
        self.assertEqual(len({recipe["id"] for recipe in recipes}), 6)
        for recipe in recipes:
            self.assertTrue(
                {"id", "title", "description", "input", "output", "steps"}
                <= recipe.keys()
            )
            self.assertGreaterEqual(len(recipe["steps"]), 3)
            for step in recipe["steps"]:
                self.assertIn("skillId", step)
                self.assertIn(step["skillId"], skill_ids)


class SkillsBuildTests(unittest.TestCase):
    def test_build_site_writes_skills_page_and_sitemap_entry(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")

            page = output_root / "skills" / "index.html"
            lab = output_root / "skills" / "lab" / "index.html"
            self.assertTrue(page.is_file())
            self.assertTrue(lab.is_file())
            page_html = page.read_text(encoding="utf-8")
            self.assertIn("Agent Skills", page_html)
            self.assertIn("FreeLLM 真测", page_html)
            self.assertIn('class="freellm-test-strip', page_html)
            self.assertIn("测试任务", page_html)
            self.assertIn("查看真实测试任务、限制与评价", page_html)
            self.assertIn("环境：", page_html)
            self.assertIn("沙箱真实验收已重跑", page_html)
            self.assertIn("Skill Lab", lab.read_text(encoding="utf-8"))
            sitemap = (output_root / "sitemap-pages.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.test/skills/", sitemap)
            self.assertIn("https://example.test/skills/lab/", sitemap)

    def test_build_site_emits_skill_content_documents(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")

            skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
            self.assertGreater(len(skills), 0)
            for item in skills:
                doc_path = output_root / "skills" / "content" / f"{item['id']}.json"
                self.assertTrue(doc_path.is_file(), f"missing content document for {item['id']}")
                document = json.loads(doc_path.read_text(encoding="utf-8"))
                self.assertEqual(document["id"], item["id"])
                self.assertTrue(str(document["content"]).strip())

    def test_skill_validation_reports_missing_required_fields(self):
        from scripts.build_seo_pages import validate_skills

        errors = validate_skills([{"id": "broken"}])

        self.assertTrue(errors)
        self.assertTrue(any("name" in error for error in errors))

    def test_skill_validation_rejects_bad_review_entries(self):
        from scripts.build_seo_pages import validate_skills

        base = {
            "id": "sample", "name": "sample", "category": "documents",
            "description": "d", "githubUrl": "https://github.com/o/r",
            "cloneCommand": "git clone https://github.com/o/r.git",
            "compatibility": ["Claude Code"], "status": "needs_review",
            "source": "user-submitted", "lastCheckedAt": None,
        }
        bad = {**base, "reviews": [{"source": "HN", "url": "javascript:alert(1)", "quote": "x"}]}
        errors = validate_skills([bad])
        self.assertTrue(any("url" in error for error in errors))

    def test_recipe_validation_reports_unknown_component(self):
        from scripts.build_seo_pages import validate_skill_recipes

        errors = validate_skill_recipes(
            [{"id": "recipe", "title": "Recipe", "steps": [{"skillId": "missing"}]}],
            [{"id": "known"}],
        )

        self.assertTrue(errors)
        self.assertTrue(any("missing" in error for error in errors))

    def test_existing_skills_page_keeps_the_original_directory(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")
            page = (output_root / "skills" / "index.html").read_text(encoding="utf-8")

        for needle in (
            '<link rel="canonical" href="https://example.test/skills/">',
            'id="skill-data"',
            'id="skill-search"',
            'id="skill-status"',
            'id="skill-grid"',
            'id="skill-dialog"',
            'id="copy-command"',
            'id="dialog-skill-content"',
            'id="dialog-skill-reviews"',
            'class="skills-page"',
            'class="skill-source-link"',
        ):
            self.assertIn(needle, page)

    def test_skills_page_surfaces_presentation_styles(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")
            page = (output_root / "skills" / "index.html").read_text(encoding="utf-8")
            lab = (output_root / "skills" / "lab" / "index.html").read_text(encoding="utf-8")

        for needle in (
            'id="dialog-style-section"',
            'class="skill-style"',
            "呈现样式",
            "tokyo-night",
            "Ocean Depths",
        ):
            self.assertIn(needle, page)
        self.assertIn("component-dialog-styles", lab)

    def test_skills_page_exposes_compact_cards_and_visual_preview(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")
            page = (output_root / "skills" / "index.html").read_text(encoding="utf-8")

        for needle in (
            "align-items:start",
            "-webkit-line-clamp:4",
            ".skill-preview-canvas",
            "section.id = 'dialog-skill-preview'",
            'id="dialog-preview-format"',
            'id="dialog-preview-tags"',
            'id="dialog-preview-canvas"',
            "renderPreview",
        ):
            self.assertIn(needle, page)

    def test_skills_page_exposes_bilingual_skill_descriptions_and_searches_them(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")
            page = (output_root / "skills" / "index.html").read_text(encoding="utf-8")

        self.assertIn('class="skill-description-zh" lang="zh-CN"', page)
        self.assertIn('class="skill-description-en" lang="en"', page)
        self.assertIn("description_zh", page)
        self.assertIn("skill.description_zh", page)

    def test_skill_lab_page_exposes_workflow_behaviors_and_seo(self):
        from scripts.build_seo_pages import build_site

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            build_site(ROOT / "data" / "offers.json", output_root, site_url="https://example.test")
            page = (output_root / "skills" / "lab" / "index.html").read_text(encoding="utf-8")

        for needle in (
            '<link rel="canonical" href="https://example.test/skills/lab/">',
            'id="skill-data"',
            'id="skill-library-search"',
            'id="skill-library-category"',
            'data-category="',
            'class="workflow-grid"',
            'id="component-library"',
            'id="workflow-dialog"',
            'id="copy-workflow-command"',
            'id="copy-component-command"',
            'navigator.clipboard.writeText',
            "window.location.protocol !== 'file:'",
            'skill-lab-page',
            'class="component-source-link"',
            'rel="nofollow noopener"',
            '"@type": "ItemList"',
            '"@type": "HowTo"',
            '没有找到匹配的组件',
        ):
            self.assertIn(needle, page)

        self.assertEqual(page.count('class="workflow-card"'), 6)
        self.assertNotIn('<article class="component-card"', page)

    def test_homepage_template_links_to_skill_directory(self):
        homepage = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")

        self.assertIn('href="/skills/"', homepage)


if __name__ == "__main__":
    unittest.main()
