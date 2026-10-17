import io
import json
import unittest
import zipfile
from scripts.restore_public_api_history import extract_authenticated_report, list_artifacts


def make_zip(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for key, value in entries.items():
            archive.writestr(key, value)
    return out.getvalue()


class PublicApiHistoryTests(unittest.TestCase):
    def test_extract_only_allowlisted_credential_free_fields(self):
        sample = {
            "schemaVersion": 1, "providerId": "hcnsec-gateway",
            "checkedAt": "2026-10-15T01:00:00Z",
            "probeType": "authenticated_chat", "outcome": "success",
            "httpStatus": 200, "latencyMs": 500, "rawPayloadStored": False,
            "evidenceSource": "freellm_automated_probe",
            "secret": "sk-not-real"
        }
        bundle = make_zip({
            "reports/auth.json": json.dumps(sample),
            "../potential-leak.txt": "SHOULD NEVER BE EXTRACTED",
        })
        restored = extract_authenticated_report(bundle)
        self.assertEqual(restored["outcome"], "success")
        self.assertNotIn("secret", restored)
        self.assertNotIn("SHOULD NEVER BE EXTRACTED", json.dumps(restored))

    def test_reject_documentation_only_and_large_payload(self):
        doc = {"schemaVersion": 1, "providerId": "hcnsec-gateway",
               "probeType": "documentation", "rawPayloadStored": False}
        self.assertIsNone(extract_authenticated_report(make_zip({"reports/auth.json": json.dumps(doc)})))
        self.assertIsNone(extract_authenticated_report(b"x" * 512001))


if __name__ == "__main__":
    unittest.main()
