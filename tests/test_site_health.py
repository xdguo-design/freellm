import json
import re
import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from scripts.site_health import (
    DEFAULT_SIZE_BUDGETS,
    build_report,
    check_model_observation,
    check_freshness,
    check_size_budget,
    resolve_release_sha,
)
from scripts.site_budgets import HOME_HTML_MAX_BYTES
from scripts.public_assets import homepage_data_asset


ROOT = Path(__file__).resolve().parents[1]


def write_source_registry(root: Path, sources: list[dict]) -> None:
    path = root / "data" / "official-model-sources.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sources), encoding="utf-8")


class SiteHealthTests(unittest.TestCase):
    def test_homepage_performance_budget_matches_site_health_budget(self):
        self.assertEqual(
            HOME_HTML_MAX_BYTES,
            DEFAULT_SIZE_BUDGETS["design/free-china-ai-index.html"],
        )

    def test_freshness_accepts_recent_dates(self):
        as_of = date(2026, 9, 11)
        self.assertEqual(check_freshness(["2026-09-10", "2026-09-06"], as_of, 7), [])

    def test_freshness_rejects_missing_invalid_future_and_stale_dates(self):
        as_of = date(2026, 9, 11)
        errors = check_freshness([None, "not-a-date", "2026-09-12", "2026-09-01"], as_of, 7)
        self.assertEqual(len(errors), 4)
        self.assertTrue(all("freshness" in error.lower() for error in errors))

    def test_source_observation_report_accepts_fresh_complete_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "offers.json").write_text('[{"lastVerifiedAt":"2026-10-05"}]', encoding="utf-8")
            (root / "data" / "models.json").write_text('[{"lastSeenAt":"2000-01-01"}]', encoding="utf-8")
            write_source_registry(root, [
                {"id": "source-a", "url": "https://a.example/models", "enabled": True},
                {"id": "source-b", "url": "https://b.example/models", "enabled": True},
            ])
            report_path = root / ".tmp" / "model-audit" / "source-health.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(json.dumps({
                "schemaVersion": 1,
                "observationKind": "official_model_source_scan",
                "asOf": "2026-10-06",
                "status": "complete",
                "complete": True,
                "enabledSourceIds": ["source-a", "source-b"],
                "sources": [
                    {"id": "source-a", "url": "https://a.example/models", "status": "success", "rowCount": 4, "truncated": False},
                    {"id": "source-b", "url": "https://b.example/models", "status": "success", "rowCount": 0, "truncated": False},
                ],
                "failures": [],
            }), encoding="utf-8")
            result = build_report(root, as_of=date(2026, 10, 6), env={"GITHUB_SHA": "a" * 40}, model_observation_path=report_path)

        self.assertTrue(result["modelObservation"]["fresh"])
        self.assertTrue(result["modelObservation"]["complete"])
        self.assertFalse(any("models freshness" in error for error in result["errors"]))

    def test_source_observation_rejects_stale_partial_unavailable_and_invalid_evidence(self):
        cases = [
            ({"schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-09-28", "status": "complete", "complete": True, "enabledSourceIds": ["a"], "sources": [{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 0, "truncated": False}], "failures": []}, "stale"),
            ({"schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-10-06", "status": "partial", "complete": False, "enabledSourceIds": ["a", "b"], "sources": [{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 1, "truncated": False}, {"id": "b", "url": "https://b.example/models", "status": "failed", "rowCount": 0, "truncated": False, "reason": "timeout"}], "failures": [{"providerId": "b", "url": "https://b.example/models", "status": "failed", "reason": "timeout"}]}, "failed"),
            (None, "unavailable"),
            ({"schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "not-date", "status": "complete", "complete": True, "enabledSourceIds": ["a"], "sources": [{"id": "a", "status": "success"}], "failures": []}, "invalid"),
        ]
        for evidence, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "data").mkdir()
                (root / "data" / "offers.json").write_text("[]", encoding="utf-8")
                (root / "data" / "models.json").write_text("[]", encoding="utf-8")
                if evidence is not None:
                    source_rows = evidence.get("sources", [])
                    registry_ids = evidence.get("enabledSourceIds", ["a"])
                    registry_rows = []
                    for index, source_id in enumerate(registry_ids):
                        source_row = source_rows[index] if index < len(source_rows) and isinstance(source_rows[index], dict) else {}
                        registry_rows.append({"id": source_id, "url": source_row.get("url", f"https://{source_id}.example/models"), "enabled": True})
                    write_source_registry(root, registry_rows)
                else:
                    write_source_registry(root, [{"id": "a", "url": "https://a.example/models", "enabled": True}])
                path = root / ".tmp" / "source-health.json"
                if evidence is not None:
                    path.parent.mkdir(parents=True)
                    path.write_text(json.dumps(evidence), encoding="utf-8")
                result = build_report(root, as_of=date(2026, 10, 6), env={"GITHUB_SHA": "a" * 40}, model_observation_path=path)
                self.assertEqual(result["modelObservation"]["status"], expected)
                self.assertFalse(result["modelObservation"]["fresh"])

    def test_fresh_model_scan_does_not_replace_manual_offer_verification_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "offers.json").write_text('[{"lastVerifiedAt":"2026-09-01"}]', encoding="utf-8")
            (root / "data" / "models.json").write_text('[{"lastSeenAt":"2000-01-01"}]', encoding="utf-8")
            write_source_registry(root, [{"id": "a", "url": "https://a.example/models", "enabled": True}])
            path = root / "source-health.json"
            path.write_text(json.dumps({"schemaVersion": 1, "observationKind":"official_model_source_scan", "asOf":"2026-10-06", "status":"complete", "complete":True,
                "enabledSourceIds":["a"], "sources":[{"id":"a", "url":"https://a.example/models", "status":"success", "rowCount":0, "truncated":False}], "failures":[]}), encoding="utf-8")
            result = build_report(root, as_of=date(2026, 10, 6), env={"GITHUB_SHA": "a" * 40}, model_observation_path=path)

        self.assertTrue(result["modelObservation"]["fresh"])
        self.assertTrue(any("offers freshness" in warning for warning in result["warnings"]))
        self.assertGreaterEqual(result["staleCount"], 1)

    def test_model_observation_rejects_malformed_duplicate_and_inconsistent_source_records(self):
        valid = {
            "schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-10-06",
            "status": "complete", "complete": True, "enabledSourceIds": ["a"],
            "sources": [{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 0, "truncated": False}],
            "failures": [],
        }
        cases = [
            (valid | {"sources": [{"id": "a", "status": "success"}]}, "missing required source fields"),
            (valid | {"sources": [{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": True, "truncated": False}]}, "boolean row count"),
            (valid | {"sources": [{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 0}]}, "missing truncated"),
            (valid | {"enabledSourceIds": ["a", "a"], "sources": [valid["sources"][0], valid["sources"][0]]}, "duplicate source"),
            (valid | {"status": "partial", "complete": False, "sources": [{"id": "a", "url": "https://a.example/models", "status": "failed", "rowCount": 0, "truncated": False, "reason": "timeout"}], "failures": []}, "missing failure record"),
            (valid | {"failures": [{"providerId": "a", "url": "https://a.example/models", "reason": "timeout"}]}, "failure conflicts with success"),
            (valid | {"failures": [{"providerId": "other", "url": "https://other.example/models", "reason": "timeout"}]}, "unknown failure source"),
        ]
        for evidence, label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "source-health.json"
                path.write_text(json.dumps(evidence), encoding="utf-8")
                result = check_model_observation(path, date(2026, 10, 6), 7)
                self.assertFalse(result["fresh"])
                self.assertIn(result["status"], {"failed", "invalid"})

    def test_model_observation_accepts_explicit_zero_row_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source-health.json"
            path.write_text(json.dumps({
                "schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-10-06",
                "status": "complete", "complete": True, "enabledSourceIds": ["empty"],
                "sources": [{"id": "empty", "url": "https://empty.example/models", "status": "success", "rowCount": 0, "truncated": False}],
                "failures": [],
            }), encoding="utf-8")
            result = check_model_observation(path, date(2026, 10, 6), 7)
        self.assertTrue(result["fresh"])

    def test_model_observation_rejects_null_source_record_without_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source-health.json"
            path.write_text(json.dumps({
                "schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-10-06",
                "status": "complete", "complete": True, "enabledSourceIds": ["a"],
                "sources": [None], "failures": [],
            }), encoding="utf-8")
            result = check_model_observation(path, date(2026, 10, 6), 7, expected_sources=[{"id": "a", "url": "https://a.example/models"}])
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["fresh"])

    def test_model_observation_rejects_mixed_type_source_pairs_without_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source-health.json"
            path.write_text(json.dumps({
                "schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-10-06",
                "status": "complete", "complete": True, "enabledSourceIds": ["a", "b"],
                "sources": [
                    {"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 0, "truncated": False},
                    {"id": None, "url": ["https://b.example/models"], "status": "success", "rowCount": 0, "truncated": False},
                ],
                "failures": [],
            }), encoding="utf-8")
            result = check_model_observation(path, date(2026, 10, 6), 7, expected_sources=[
                {"id": "a", "url": "https://a.example/models"},
                {"id": "b", "url": "https://b.example/models"},
            ])
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["fresh"])

    def test_build_report_compares_observation_sources_with_tracked_registry_id_and_url_pairs(self):
        expected = [
            {"id": "source-a", "url": "https://a.example/models"},
            {"id": "source-b", "url": "https://b.example/models"},
        ]
        artifact_cases = [
            expected[:1],
            [expected[0], {"id": "source-b", "url": "https://attacker.example/models"}],
        ]
        for actual in artifact_cases:
            with self.subTest(actual=actual), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "data").mkdir()
                (root / "data" / "offers.json").write_text("[]", encoding="utf-8")
                (root / "data" / "models.json").write_text("[]", encoding="utf-8")
                write_source_registry(root, [item | {"enabled": True} for item in expected])
                artifact = root / "source-health.json"
                artifact.write_text(json.dumps({
                    "schemaVersion": 1, "observationKind": "official_model_source_scan", "asOf": "2026-10-06",
                    "status": "complete", "complete": True,
                    "enabledSourceIds": [item["id"] for item in actual],
                    "sources": [item | {"status": "success", "rowCount": 1, "truncated": False} for item in actual],
                    "failures": [],
                }), encoding="utf-8")
                result = build_report(root, as_of=date(2026, 10, 6), env={"GITHUB_SHA": "a" * 40}, model_observation_path=artifact)
                self.assertFalse(result["modelObservation"]["fresh"])
                self.assertEqual(result["modelObservation"]["status"], "invalid")

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
        global_headers = next(item for item in config["headers"] if item["source"] == "/(.*)")
        values = {item["key"]: item["value"] for item in global_headers["headers"]}
        self.assertEqual(values["Strict-Transport-Security"], "max-age=63072000; includeSubDomains")
        self.assertEqual(values["X-Content-Type-Options"], "nosniff")
        self.assertEqual(values["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(values["Permissions-Policy"], "camera=(), microphone=(), geolocation=()")
        self.assertEqual(values["X-Frame-Options"], "SAMEORIGIN")
        self.assertIn("object-src 'none'", values["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'self'", values["Content-Security-Policy"])

    def test_vercel_keeps_homepage_rewrite(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertIn(
            {"source": "/", "destination": "/design/free-china-ai-index.html"},
            config["rewrites"],
        )

    def test_vercel_caches_the_homepage_data_asset(self):
        html = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
        body = re.search(r"<body\b[^>]*>", html, flags=re.IGNORECASE)
        self.assertIsNotNone(body)
        data_url = re.search(r'data-offers-url="([^"]+)"', body.group(0))
        self.assertIsNotNone(data_url)
        path = urlsplit(urljoin("https://freellm.top/", data_url.group(1))).path
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        rule = next((item for item in config.get("headers", []) if item["source"] == path), None)
        self.assertIsNotNone(rule)
        values = {header["key"]: header["value"] for header in rule["headers"]}
        self.assertEqual(values["Cache-Control"], "public, max-age=300, must-revalidate")
        self.assertEqual(values["CDN-Cache-Control"], "public, max-age=60")

    def test_performance_probe_resolves_data_asset_from_homepage_markup(self):
        self.assertEqual(
            homepage_data_asset(
                '<body data-offers-url="../data/offers-ranked.json">',
                "https://freellm.top/",
            ),
            "data/offers-ranked.json",
        )

    def test_homepage_data_asset_rejects_a_different_origin(self):
        with self.assertRaisesRegex(ValueError, "public site origin"):
            homepage_data_asset(
                '<body data-offers-url="https://attacker.example/offers.json">',
                "https://freellm.top/",
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
        # About reports the canonical daily scan, not the catalog's separate
        # 78 offers / 258 model records (including expired/retired rows).
        scan = json.loads((ROOT / "data" / "scan-summary.json").read_text(encoding="utf-8"))
        about = (ROOT / "about" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'data-scan-stat="offers">{scan["offers"]}</strong>', about)
        self.assertIn(f'data-scan-stat="models">{scan["models"]}</strong>', about)
        provider_cards = len(json.loads((ROOT / "data" / "provider-access.json").read_text(encoding="utf-8")))
        models_page = (ROOT / "models" / "all" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"{provider_cards} 家提供商", models_page)


if __name__ == "__main__":
    unittest.main()
