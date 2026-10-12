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


class RecipeDataTests(unittest.TestCase):
    def test_skill_recipes_are_curated_and_reference_existing_components(self):
        recipes = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
        skill_ids = {item["id"] for item in json.loads(SKILLS_PATH.read_text(encoding="utf-8"))}

        self.assertEqual(len(recipes), 15)
        self.assertEqual(len({recipe["id"] for recipe in recipes}), 15)
        for recipe in recipes:
            self.assertTrue(
                {"id", "title", "description", "input", "output", "steps"}
                <= recipe.keys()
            )
            self.assertGreaterEqual(len(recipe["steps"]), 3)
            for step in recipe["steps"]:
                self.assertIn("skillId", step)
                self.assertIn(step["skillId"], skill_ids)
                self.assertTrue(str(step.get("demo") or "").strip(), recipe["id"])


if __name__ == "__main__":
    unittest.main()
