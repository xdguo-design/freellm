"""Regression tests for trustworthy, evidence-based GEO measurement."""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("geo_checker", ROOT / "seo" / "ai-reference-checker.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

HEADER = list(checker.REQUIRED_FIELDS)
QUERY = "free llm api"
KEYWORDS = [{"query": QUERY, "page": "https://freellm.top/guides/free-openai-compatible-apis/", "group": "treatment"}]


def row(**overrides):
    item = {
        "checked_at": "2026-10-14T08:00:00+08:00", "engine": "chatgpt_search",
        "query": QUERY, "result": "cited",
        "cited_url": "https://freellm.top/guides/free-openai-compatible-apis/",
        "evidence_url": "https://chatgpt.com/share/valid-example", "evidence_path": "", "notes": "",
    }
    item.update(overrides)
    return item


class GEOCheckerTests(unittest.TestCase):
    def write_csv(self, rows):
        folder = tempfile.TemporaryDirectory()
        path = Path(folder.name) / "observations.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(rows)
        return folder, path

    def test_url_host_boundary_and_https(self):
        self.assertEqual(checker.site_path("https://www.freellm.top/guides/free-llm/?src=chat"), "/guides/free-llm/")
        for value in (
            "http://freellm.top/a/", "https://freellm.top.evil.test/a/",
            "https://evil.test/?url=https://freellm.top/", "https://freellm.top@evil.test/",
            "https://anotherfreellm.top/", "javascript:https://freellm.top/",
        ):
            self.assertIsNone(checker.site_path(value), value)

    def test_missing_observations_are_unknown_not_zero(self):
        report = checker.build_report(KEYWORDS, [])
        self.assertEqual(report["keywords"][0]["checks"]["chatgpt_search"]["status"], "not_checked")
        self.assertEqual(report["summary"]["perplexity"]["not_checked"], 1)

    def test_manual_positive_and_explicit_negative(self):
        folder, path = self.write_csv([
            row(), row(engine="perplexity", result="not_cited", cited_url="", evidence_url=""),
        ])
        try:
            records = checker.load_observations(path, {QUERY})
            report = checker.build_report(KEYWORDS, records)
            self.assertEqual(report["keywords"][0]["checks"]["chatgpt_search"]["status"], "cited")
            self.assertEqual(report["keywords"][0]["checks"]["perplexity"]["status"], "not_cited")
            self.assertEqual(report["keywords"][0]["checks"]["gemini"]["status"], "not_checked")
            self.assertEqual(report["summary"]["chatgpt_search"]["cited"], 1)
        finally:
            folder.cleanup()

    def test_latest_snapshot_replaces_earlier_result(self):
        folder, path = self.write_csv([
            row(checked_at="2026-10-13T08:00:00+08:00"),
            row(checked_at="2026-10-14T08:00:00+08:00", result="not_cited", cited_url="", evidence_url=""),
        ])
        try:
            report = checker.build_report(KEYWORDS, checker.load_observations(path, {QUERY}))
            self.assertEqual(report["keywords"][0]["checks"]["chatgpt_search"]["status"], "not_cited")
        finally:
            folder.cleanup()

    def test_no_citation_without_evidence_or_target_url(self):
        for overrides in (
            {"evidence_url": ""},
            {"cited_url": "https://freellm.top.fake/a/"},
            {"checked_at": "2026-10-14"},
            {"result": "not_cited"},
        ):
            folder, path = self.write_csv([row(**overrides)])
            try:
                with self.assertRaises(ValueError):
                    checker.load_observations(path, {QUERY})
            finally:
                folder.cleanup()

    def test_keyword_configuration_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "keywords.json"
            path.write_text(json.dumps(KEYWORDS * 2), encoding="utf-8")
            with self.assertRaises(ValueError):
                checker.load_keywords(path)

    def test_same_timestamp_cannot_be_both_cited_and_not_cited(self):
        folder, path = self.write_csv([
            row(), row(result="not_cited", cited_url="", evidence_url=""),
        ])
        try:
            with self.assertRaises(ValueError):
                checker.build_report(KEYWORDS, checker.load_observations(path, {QUERY}))
        finally:
            folder.cleanup()


if __name__ == "__main__":
    unittest.main()
