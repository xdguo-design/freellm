import unittest

from scripts.sync_offer_observations import sync_offer_observations


class OfferObservationSyncTests(unittest.TestCase):
    def test_ok_source_updates_observation_without_touching_manual_verification(self):
        offers = [{
            "id": "alpha",
            "lastVerifiedAt": "2026-09-17",
            "status": "verified",
            "confidence": "high",
        }]
        scan = [
            {"offerId": "alpha", "url": "https://example.com/pricing", "status": "ok"},
            {"offerId": "alpha", "url": "https://example.com/docs", "status": "blocked"},
        ]
        result = sync_offer_observations(offers, scan, "2026-10-05")
        self.assertEqual(result[0]["lastObservedAt"], "2026-10-05")
        self.assertEqual(result[0]["lastVerifiedAt"], "2026-09-17")
        self.assertEqual(result[0]["status"], "verified")
        self.assertEqual(result[0]["confidence"], "high")

    def test_blocked_limited_or_failed_sources_do_not_refresh_observation(self):
        offers = [{"id": "alpha", "lastObservedAt": "2026-09-30"}]
        scan = [
            {"offerId": "alpha", "status": "blocked"},
            {"offerId": "alpha", "status": "source_limit"},
            {"offerId": "alpha", "status": "failed"},
        ]
        result = sync_offer_observations(offers, scan, "2026-10-05")
        self.assertEqual(result[0]["lastObservedAt"], "2026-09-30")

    def test_unrelated_offer_is_unchanged(self):
        offers = [{"id": "alpha"}, {"id": "beta"}]
        scan = [{"offerId": "alpha", "status": "ok"}]
        result = sync_offer_observations(offers, scan, "2026-10-05")
        self.assertEqual(result[0]["lastObservedAt"], "2026-10-05")
        self.assertNotIn("lastObservedAt", result[1])


if __name__ == "__main__":
    unittest.main()
