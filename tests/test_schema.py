import json
import unittest
from pathlib import Path

from crawler.schema import validate_offer, validate_offers


class SchemaTests(unittest.TestCase):
    def test_all_seed_offers_have_required_fields(self):
        self.assertEqual(validate_offers(Path("data/offers.json")), [])

    def test_global_opencode_offer_is_in_the_directory(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        opencode = next(offer for offer in offers if offer["id"] == "opencode-zen-free")
        self.assertEqual(opencode["originCountry"], "International")
        self.assertEqual(opencode["freeMechanism"], "limited_time_free")
        self.assertIn("opencode.ai", opencode["register"])

    def test_global_coding_peers_are_in_the_directory(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        offer_ids = {offer["id"] for offer in offers}
        self.assertTrue({
            "github-copilot-free",
            "cursor-hobby",
            "amazon-q-free",
            "google-antigravity-free",
        }.issubset(offer_ids))

    def test_invalid_product_type_is_rejected(self):
        errors = validate_offer({"id": "x", "productType": "unknown"})
        self.assertTrue(any("productType" in error for error in errors))

    def test_duplicate_ids_are_rejected(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        duplicate = [offers[0], offers[0]]
        errors = validate_offers(duplicate)
        self.assertTrue(any("duplicate id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
