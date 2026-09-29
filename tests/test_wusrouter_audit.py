import unittest

from scripts.audit_wusrouter import _classify_error, _zeroish, extract_zero_cost_models


class WusRouterAuditTests(unittest.TestCase):
    def test_extracts_only_explicit_zero_cost_models(self):
        payload = {
            "models": [
                {"model": "glm-5.3-flash", "input_price": 0, "output_price": "$0.00"},
                {"model": "paid-model", "input_price": 0, "output_price": 1},
                {"name": "qwen-free", "cost": "0 credits"},
                {"name": "metadata-only", "latency": 0},
            ]
        }
        self.assertEqual(extract_zero_cost_models(payload), ["glm-5.3-flash", "qwen-free"])

    def test_zeroish_rejects_nonzero_or_missing_numbers(self):
        self.assertTrue(_zeroish("$0.000"))
        self.assertTrue(_zeroish("0 credits"))
        self.assertFalse(_zeroish("free"))
        self.assertFalse(_zeroish("0 input / 1 output"))

    def test_classifies_cloudflare_challenge_separately(self):
        self.assertEqual(
            _classify_error(403, "<title>Just a moment...</title> Cloudflare cf-chl", ""),
            "cloudflare_challenge",
        )
        self.assertEqual(_classify_error(401, "", ""), "auth_required")
        self.assertEqual(_classify_error(429, "", ""), "rate_limited")


if __name__ == "__main__":
    unittest.main()
