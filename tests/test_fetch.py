import unittest

from crawler.fetch import extract_evidence, fetch_public_page


class FetchTests(unittest.TestCase):
    def test_extracts_title_and_free_evidence_without_script_text(self):
        html = "<html><head><title>Pricing</title><script>free secret</script></head><body><h1>Free plan</h1><p>500 credits per month.</p></body></html>"
        result = extract_evidence(html)
        self.assertEqual(result["title"], "Pricing")
        self.assertIn("Free plan", result["evidence"])
        self.assertNotIn("free secret", result["text"])

    def test_rejects_non_https_or_unapproved_domains(self):
        insecure = fetch_public_page("http://example.com", ["example.com"])
        unknown = fetch_public_page("https://example.com", ["official.example"])
        self.assertEqual(insecure["status"], "rejected")
        self.assertEqual(unknown["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
