import datetime as dt
import json
import unittest
import urllib.error
from unittest.mock import Mock

from scripts.probe_public_api import build_request, probe, _status_from_http, _valid_response
from scripts.evaluate_public_api import evaluate


UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 15, 9, 0, tzinfo=UTC)


class FakeResponse:
    status = 200
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return self.body[:limit]


class PublicApiProbeTests(unittest.TestCase):
    def test_document_check_does_not_count_as_api_success(self):
        opener = Mock()
        opener.open.return_value = FakeResponse("公益 API https://api.hcnsec.cn/v1".encode())
        report = probe("documentation", opener=opener, clock=lambda: 1.0)
        self.assertEqual(report["outcome"], "reachable")
        self.assertIsNone(report["modelId"])
        self.assertEqual(report["probeType"], "documentation")
        self.assertNotIn("success", report["outcome"])

    def test_success_requires_valid_response_body_not_status_only(self):
        opener = Mock()
        opener.open.return_value = FakeResponse(b"<html>fake success</html>")
        report = probe("authenticated_chat", key="sk-fake-test-only", opener=opener, clock=lambda: 2.0)
        self.assertEqual(report["outcome"], "invalid_response")
        self.assertEqual(report["httpStatus"], 200)

    def test_authenticated_payload_validates_and_never_stores_secret(self):
        fake_key = "sk-not-a-real-secret"
        req = build_request("authenticated_chat", fake_key)
        self.assertEqual(req.full_url, "https://api.hcnsec.cn/v1/chat/completions")
        self.assertIn("Authorization", req.headers)
        opener = Mock()
        opener.open.return_value = FakeResponse(b'{"choices":[{"message":{"content":"OK"}}]}')
        report = probe("authenticated_chat", key=fake_key, opener=opener, clock=lambda: 3.0)
        self.assertEqual(report["outcome"], "success")
        self.assertNotIn(fake_key, json.dumps(report))
        self.assertFalse(report["rawPayloadStored"])

    def test_no_key_skips_probe(self):
        outcome = probe("authenticated_chat", key=None)
        self.assertEqual(outcome["outcome"], "not_configured")
        self.assertIsNone(outcome["latencyMs"])

    def test_non_200_status_not_confused_with_success(self):
        self.assertEqual(_status_from_http(401, valid=False, mode="authenticated_chat"), "authentication_rejected")
        self.assertEqual(_status_from_http(403, valid=False, mode="authenticated_chat"), "permission_denied")
        self.assertEqual(_status_from_http(429, valid=False, mode="authenticated_chat"), "rate_limited")
        self.assertEqual(_status_from_http(302, valid=False, mode="authenticated_chat"), "redirect_rejected")
        self.assertFalse(_valid_response("authenticated_chat", b"{}"))


class PublicApiEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.obs = {"observations": [{
            "providerId": "hcnsec-gateway", "sourceType": "first_party_user_report",
            "outcome": "reported_success", "countedForAvailabilityMetrics": False
        }]}

    def make_report(self, days_back, ok=True):
        time = NOW - dt.timedelta(days=days_back)
        return {
            "schemaVersion": 1, "providerId": "hcnsec-gateway",
            "checkedAt": time.isoformat(),
            "probeType": "authenticated_chat",
            "evidenceSource": "freellm_automated_probe",
            "outcome": "success" if ok else "rate_limited",
            "latencyMs": 150 if ok else 200,
        }

    def test_user_report_is_positive_but_not_synthetic_100_percent(self):
        score = evaluate(self.obs, [], now=NOW)
        self.assertEqual(score["evidenceStatus"], "USER_CONFIRMED")
        self.assertEqual(score["userSuccessReports"], 1)
        self.assertEqual(score["authenticatedSamples"], 0)
        self.assertIsNone(score["successRatePercent"])

    def test_two_reports_are_insufficient(self):
        report = evaluate(self.obs, [self.make_report(0), self.make_report(1)], now=NOW)
        self.assertEqual(report["evidenceStatus"], "INSUFFICIENT_SAMPLES")
        self.assertIsNone(report["p95LatencyMs"])

    def test_measured_metrics_require_minimum_count_and_days_and_recent_data(self):
        rows = [self.make_report(i % 3, ok=(i != 19)) for i in range(20)]
        report = evaluate(self.obs, rows, now=NOW)
        self.assertEqual(report["evidenceStatus"], "MEASURED_WINDOW")
        self.assertEqual(report["successRatePercent"], 95.0)
        self.assertEqual(report["p50LatencyMs"], 150)
        self.assertEqual(report["sampleDays"], 3)

    def test_stale_successes_cannot_claim_current_reliability(self):
        rows = [self.make_report(i % 3 + 5) for i in range(30)]
        report = evaluate(self.obs, rows, now=NOW)
        self.assertEqual(report["evidenceStatus"], "INSUFFICIENT_SAMPLES")
        self.assertIsNone(report["successRatePercent"])

    def test_public_document_response_never_counts_in_authenticated_sample(self):
        report = evaluate(self.obs, [{
            "schemaVersion": 1, "providerId": "hcnsec-gateway",
            "checkedAt": NOW.isoformat(), "probeType": "documentation", "outcome": "reachable"
        }], now=NOW)
        self.assertEqual(report["documentReachabilityObservations"], 1)
        self.assertEqual(report["authenticatedSamples"], 0)


if __name__ == "__main__":
    unittest.main()
