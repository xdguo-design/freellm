import unittest

from crawler.fetch import extract_evidence, extract_page_links, fetch_public_page, read_limited


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
        malformed = fetch_public_page("https://example.com/free plan", ["example.com"])
        self.assertEqual(insecure["status"], "rejected")
        self.assertEqual(unknown["status"], "rejected")
        self.assertEqual(malformed["status"], "rejected")

    def test_extracts_official_discovery_links_from_page(self):
        html = '<a href="pricing">免费额度</a><a href="https://evil.example/free">免费</a>'

        links = extract_page_links(html, "https://mimo.mi.com/docs/home", ["mimo.mi.com"])

        self.assertEqual(links, ["https://mimo.mi.com/docs/pricing"])

    def test_read_limited_reads_only_one_byte_beyond_max_for_size_check(self):
        class ChunkedBody:
            def __init__(self):
                self.chunks = [b"1234", b"5678", b"90"]

            def read(self, size):
                return self.chunks.pop(0) if self.chunks else b""

        self.assertEqual(read_limited(ChunkedBody(), 7), b"12345678")


if __name__ == "__main__":
    unittest.main()
