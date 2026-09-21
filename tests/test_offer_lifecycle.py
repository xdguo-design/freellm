from __future__ import annotations

import unittest
from datetime import datetime, timezone

from crawler.lifecycle import offer_is_public, parse_offer_datetime, public_offers
from crawler.schema import validate_offer


class OfferLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)

    def test_active_timed_offer_is_public(self) -> None:
        offer = {
            "status": "verified",
            "startsAt": "2026-09-18T10:00:00+08:00",
            "endsAt": "2026-09-30T23:59:59+08:00",
        }
        self.assertTrue(offer_is_public(offer, now=self.now))

    def test_future_and_expired_offers_are_hidden(self) -> None:
        future = {"status": "verified", "startsAt": "2026-10-01T00:00:00+08:00"}
        expired = {"status": "verified", "endsAt": "2026-09-20T23:59:59+08:00"}
        self.assertFalse(offer_is_public(future, now=self.now))
        self.assertFalse(offer_is_public(expired, now=self.now))
        self.assertEqual(public_offers([future, expired], now=self.now), [])

    def test_inactive_status_is_hidden_without_dates(self) -> None:
        self.assertFalse(offer_is_public({"status": "expired"}, now=self.now))
        self.assertFalse(offer_is_public({"status": "unavailable"}, now=self.now))

    def test_datetime_requires_timezone(self) -> None:
        with self.assertRaises(ValueError):
            parse_offer_datetime("2026-09-30T23:59:59")

    def test_schema_rejects_invalid_lifecycle_range(self) -> None:
        offer = {
            "id": "test",
            "order": 1,
            "date": "2026-09-21",
            "name": "Test",
            "provider": "Test",
            "model": "Test",
            "type": ["free"],
            "productType": "free_ide",
            "freeMechanism": "limited_time_free",
            "freeSummary": "Free",
            "validitySummary": "Limited",
            "accessSummary": "Account",
            "title": "Test",
            "why": "Test offer",
            "mechanism": "Free",
            "validity": "Limited",
            "access": "Account",
            "command": "Use it",
            "register": "https://example.com/",
            "links": [["Official", "https://example.com/"]],
            "sourceUrls": ["https://example.com/"],
            "evidence": "Official source",
            "status": "verified",
            "confidence": "high",
            "lastVerifiedAt": "2026-09-21",
            "startsAt": "2026-09-30T23:59:59+08:00",
            "endsAt": "2026-09-18T10:00:00+08:00",
            "claimRequired": False,
        }
        errors = validate_offer(offer)
        self.assertIn("endsAt must be later than startsAt", errors)


if __name__ == "__main__":
    unittest.main()
