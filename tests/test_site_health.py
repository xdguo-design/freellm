import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.site_health import (
    DEFAULT_SIZE_BUDGETS,
    check_freshness,
    check_size_budget,
    resolve_release_sha,
)


ROOT = Path(__file__).resolve().parents[1]


class SiteHealthTests(unittest.TestCase):
    def test_freshness_accepts_recent_dates(self):
        as_of = date(2026, 9, 11)
        self.assertEqual(check_freshness(["2026-09-10", "2026-09-06"], as_of, 7), [])

    def test_freshness_rejects_missing_invalid_future_and_stale_dates(self):
        as_of = date(2026, 9, 11)
        errors = check_freshness([None, "not-a-date", "2026-09-12", "2026-09-01"], as_of, 7)
        self.assertEqual(len(errors), 4)
        self.assertTrue(all("freshness" in error.lower() for error in errors))

    def test_size_budget_reports_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_bytes(b"12345")
            self.assertEqual(check_size_budget(path, 4), [f"{path}: 5 bytes exceeds 4-byte budget"])
            self.assertEqual(check_size_budget(path, 5), [])

    def test_default_budgets_cover_current_key_pages(self):
        for relative_path, budget in DEFAULT_SIZE_BUDGETS.items():
            path = ROOT / relative_path
            self.assertTrue(path.is_file(), relative_path)
            self.assertLessEqual(path.stat().st_size, budget, relative_path)

    def test_release_sha_prefers_ci_value_then_git_head(self):
        self.assertEqual(resolve_release_sha({"GITHUB_SHA": "a" * 40}, "b" * 40), "a" * 40)
        self.assertEqual(resolve_release_sha({}, "b" * 40), "b" * 40)

    def test_release_sha_fails_when_unavailable(self):
        with self.assertRaisesRegex(RuntimeError, "release SHA"):
            resolve_release_sha({}, None)


class VercelHeaderContractTests(unittest.TestCase):
    def test_vercel_has_baseline_security_headers_for_every_route(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual(config["headers"][0]["source"], "/(.*)")
        values = {item["key"]: item["value"] for item in config["headers"][0]["headers"]}
        self.assertEqual(values["Strict-Transport-Security"], "max-age=63072000; includeSubDomains")
        self.assertEqual(values["X-Content-Type-Options"], "nosniff")
        self.assertEqual(values["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(values["Permissions-Policy"], "camera=(), microphone=(), geolocation=()")
        self.assertEqual(values["X-Frame-Options"], "SAMEORIGIN")

    def test_vercel_keeps_homepage_rewrite(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertIn(
            {"source": "/", "destination": "/design/free-china-ai-index.html"},
            config["rewrites"],
        )


class ReadmeFactsTests(unittest.TestCase):
    def test_readme_counts_match_current_data(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        offers = len(json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8")))
        models = len(json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8")))
        providers = len(json.loads((ROOT / "data" / "providers.json").read_text(encoding="utf-8")))
        self.assertIn(f"{offers} 个", readme)
        self.assertIn(f"{models} 条", readme)
        self.assertIn(f"{providers} 家", readme)
        self.assertIn(f"**{offers}** curated", readme)
        self.assertIn(f"**{models}** third-party", readme)

    def test_about_and_generated_model_page_counts_match_current_data(self):
        offers = len(json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8")))
        models = len(json.loads((ROOT / "data" / "models.json").read_text(encoding="utf-8")))
        self.assertIn(f">{offers}<", (ROOT / "about" / "index.html").read_text(encoding="utf-8"))
        self.assertIn(f">{models}+<", (ROOT / "about" / "index.html").read_text(encoding="utf-8"))
        provider_cards = len(json.loads((ROOT / "data" / "provider-access.json").read_text(encoding="utf-8")))
        models_page = (ROOT / "models" / "all" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"{provider_cards} 家提供商", models_page)


if __name__ == "__main__":
    unittest.main()
