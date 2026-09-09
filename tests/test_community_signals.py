import json
import tempfile
import unittest
from pathlib import Path

from crawler.community_signals import (
    group_signals_by_offer,
    merge_signals,
    redact_excerpt,
    validate_signal_record,
    validate_signals,
)


def rating_signal(**overrides):
    record = {
        "offerId": "qwen3-4b",
        "sourcePlatform": "hugging_face",
        "sourceType": "rating",
        "sourceUrl": "https://huggingface.co/Qwen/Qwen3-4B",
        "value": 4.3,
        "scaleMax": 5,
        "sampleCount": 128,
        "rawLabel": "4.3 / 5 · 128 ratings",
        "excerpt": "Strong coding results in recent reviews.",
        "capturedAt": "2026-09-07T00:00:00+00:00",
        "status": "observed",
    }
    record.update(overrides)
    return record


class CommunitySignalValidationTests(unittest.TestCase):
    def test_valid_rating_signal_preserves_platform_native_value(self):
        self.assertEqual(validate_signal_record(rating_signal()), [])

    def test_rejects_invalid_url_unknown_type_and_non_rating_score_fields(self):
        errors = validate_signal_record(rating_signal(
            sourceUrl="http://ratings.example/model",
            sourceType="score",
        ))

        self.assertTrue(any("sourceUrl" in error for error in errors))
        self.assertTrue(any("sourceType" in error for error in errors))

        errors = validate_signal_record(rating_signal(sourceType="review"))
        self.assertTrue(any("value" in error for error in errors))

    def test_redact_excerpt_removes_secrets_and_personal_email(self):
        excerpt = redact_excerpt(
            "Great model.\nAPI_KEY=sk-live-secret\nContact me at person@example.com",
        )

        self.assertIn("Great model.", excerpt)
        self.assertNotIn("sk-live-secret", excerpt)
        self.assertNotIn("person@example.com", excerpt)

    def test_validate_signals_reports_record_indexes(self):
        errors = validate_signals([rating_signal(), {"offerId": "missing-fields"}])

        self.assertTrue(any(error.startswith("signals[1]") for error in errors))


class CommunitySignalMergeTests(unittest.TestCase):
    def test_merge_replaces_same_platform_signal_and_keeps_other_platforms(self):
        old = rating_signal(value=4.1, rawLabel="4.1 / 5", capturedAt="2026-09-06T00:00:00+00:00")
        new = rating_signal(value=4.3, rawLabel="4.3 / 5", capturedAt="2026-09-07T00:00:00+00:00")
        downloads = rating_signal(
            sourcePlatform="modelscope",
            sourceType="downloads",
            value=12400,
            scaleMax=None,
            sampleCount=None,
            rawLabel="12.4K downloads",
            excerpt="",
        )

        merged = merge_signals([old], [new, downloads], captured_at="2026-09-07T00:00:00+00:00")

        self.assertEqual(len(merged), 2)
        self.assertEqual(next(item for item in merged if item["sourcePlatform"] == "hugging_face")["value"], 4.3)
        self.assertEqual(next(item for item in merged if item["sourcePlatform"] == "modelscope")["sourceType"], "downloads")

    def test_merge_keeps_distinct_models_under_one_offer(self):
        first = rating_signal(modelId="model-a", rawLabel="model-a 4.1 / 5")
        second = rating_signal(modelId="model-b", rawLabel="model-b 4.2 / 5")

        merged = merge_signals([], [first, second])

        self.assertEqual(len(merged), 2)

    def test_group_signals_by_offer_does_not_create_missing_scores(self):
        grouped = group_signals_by_offer([
            rating_signal(),
            rating_signal(offerId="copilot-free", sourcePlatform="github", sourceType="stars", value=2100, scaleMax=None, sampleCount=None, rawLabel="2.1K Stars", excerpt=""),
        ])

        self.assertEqual(set(grouped), {"qwen3-4b", "copilot-free"})
        self.assertEqual(grouped["copilot-free"][0]["value"], 2100)


class CommunitySignalCliTests(unittest.TestCase):
    def test_signals_cli_merges_snapshot_and_preserves_existing_on_invalid_input(self):
        from crawler.cli import main as cli_main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "snapshot.json"
            output_path = root / "community-signals.json"
            existing = [rating_signal(value=4.0, rawLabel="4.0 / 5")]
            input_path.write_text(json.dumps([rating_signal(value=4.3)]), encoding="utf-8")
            output_path.write_text(json.dumps(existing), encoding="utf-8")

            exit_code = cli_main(["signals", "--input", str(input_path), "--out", str(output_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))[0]["value"], 4.3)

            input_path.write_text(json.dumps([{"offerId": "broken"}]), encoding="utf-8")
            exit_code = cli_main(["signals", "--input", str(input_path), "--out", str(output_path)])

            self.assertEqual(exit_code, 1)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))[0]["value"], 4.3)


if __name__ == "__main__":
    unittest.main()
