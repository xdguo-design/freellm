import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_PATH = ROOT / "data" / "skills.json"
RECIPES_PATH = ROOT / "data" / "skill-recipes.json"

EXPECTED_CATEGORIES = {
    "product-design",
    "ecommerce",
    "seo-content",
    "email-office",
    "planning-office",
    "data-office",
    "file-office",
    "documents",
    "presentations",
    "resume",
    "writing",
}


class SkillsDataTests(unittest.TestCase):
    def test_skill_catalog_has_eleven_categories_of_ten_components(self):
        self.assertTrue(SKILLS_PATH.is_file(), "data/skills.json must exist")
        skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))

        self.assertEqual(len(skills), 110)
        self.assertEqual({item["category"] for item in skills}, EXPECTED_CATEGORIES)
        for category in EXPECTED_CATEGORIES:
            self.assertEqual(sum(item["category"] == category for item in skills), 10)
        for item in skills:
            self.assertTrue(
                {
                    "id",
                    "name",
                    "category",
                    "description",
                    "githubUrl",
                    "cloneCommand",
                    "compatibility",
                    "status",
                    "source",
                    "lastCheckedAt",
                } <= item.keys()
            )
            self.assertIn(item["status"], {"candidate", "needs_review"})


class RecipeDataTests(unittest.TestCase):
    def test_skill_recipes_are_curated_and_reference_existing_components(self):
        self.assertTrue(RECIPES_PATH.is_file(), "data/skill-recipes.json must exist")
        skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
        recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
        skill_ids = {item["id"] for item in skills}

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
            self.assertIn("Agent Skills", page.read_text(encoding="utf-8"))
            self.assertIn("Skill Lab", lab.read_text(encoding="utf-8"))
            sitemap = (output_root / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.test/skills/", sitemap)
            self.assertIn("https://example.test/skills/lab/", sitemap)

    def test_skill_validation_reports_missing_required_fields(self):
        from scripts.build_seo_pages import validate_skills

        errors = validate_skills([{"id": "broken"}])

        self.assertTrue(errors)
        self.assertTrue(any("name" in error for error in errors))

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
            'class="skills-page"',
            'class="skill-source-link"',
        ):
            self.assertIn(needle, page)

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
            'data-category="product-design"',
            'data-category="ecommerce"',
            'data-category="seo-content"',
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
