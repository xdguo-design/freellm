"""Requesty catalog, no-fake-feature and first-discovery regression checks."""
import json
import unittest
from pathlib import Path

from scripts import daily_discoveries as discoveries
from scripts.mark_featured_offers import compute_featured

ROOT = Path(__file__).resolve().parents[1]


class RequestyCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.offers = json.loads((ROOT / "data/offers.json").read_text(encoding="utf-8"))
        cls.models = json.loads((ROOT / "data/models.json").read_text(encoding="utf-8"))
        cls.today = json.loads((ROOT / "data/daily-log/2026-10-17.json").read_text(encoding="utf-8"))
        cls.requesty = next(x for x in cls.offers if x["id"] == "requesty-free")

    def test_thirteen_free_routes_are_consistent(self):
        ids = [row["model"] for row in self.requesty["freeModels"]]
        canonical = [row["canonicalModelId"] for row in self.models if row["providerId"] == "requesty"]
        self.assertEqual(len(ids), 13)
        self.assertEqual(len(set(ids)), 13)
        self.assertEqual(set(ids), set(canonical))
        self.assertEqual(self.requesty["freePolicy"]["amount"], 200)
        self.assertEqual(self.requesty["cardRequired"], "no")

    def test_no_featured_without_actual_speed(self):
        item = self.requesty
        self.assertFalse(item["freeLLMTest"]["actualUsageVerified"])
        self.assertNotIn("featured", item)
        self.assertIsNone(compute_featured(item, "2026-10-17"))

    def test_single_daily_discovery_and_official_sources(self):
        hits = [e for e in discoveries.log_discoveries(self.today) if e["id"] == "requesty-free"]
        self.assertEqual(len(hits), 1)
        item = hits[0]
        self.assertEqual((item["kind"], item["eventType"], item["asOf"]), ("offer", "new", "2026-10-17"))
        self.assertEqual(item["details"]["sourceKind"], "official")
        self.assertEqual(item["details"]["freeLLMTest"]["actualUsageVerified"], False)
        self.assertTrue(item["details"]["sourceUrl"].startswith("https://docs.requesty.ai/"))


if __name__ == "__main__":
    unittest.main()
