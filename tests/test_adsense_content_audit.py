import tempfile
import unittest
from pathlib import Path
from datetime import date

from scripts.audit_adsense_content import VisibleText, _audit_source_data, audit


class AdsenseContentAuditTests(unittest.TestCase):
    def test_only_visible_main_text_is_counted(self):
        parser = VisibleText()
        parser.feed('<html><head><script>fake</script></head><body><nav>nav</nav><main><h1>Useful</h1><p>Evidence</p><a href="https://docs.example.com/api">Source</a></main><footer>foot</footer></body></html>')
        self.assertEqual(parser.main, ["Useful", "Evidence", "Source"])
        self.assertEqual(parser.source_hosts, {"docs.example.com"})

    def test_flags_short_guide_and_unverified_sources_as_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sitemap-pages.xml").write_text('<urlset><loc>https://freellm.top/guides/sample/</loc></urlset>', encoding="utf-8")
            page = root / "guides/sample/index.html"
            page.parent.mkdir(parents=True)
            page.write_text('<html><body><main><h1>Example</h1><p>Short guide.</p></main></body></html>', encoding="utf-8")
            result = audit(root)
            row = result["rows"][0]
            self.assertIn("thin_editorial_text_review", row["flags"])
            self.assertIn("external_evidence_review", row["flags"])
            self.assertFalse(row.get("error"))

    def test_missing_target_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sitemap-pages.xml").write_text('<urlset><loc>https://freellm.top/missing/</loc></urlset>', encoding="utf-8")
            self.assertEqual(audit(root)["rows"][0]["error"], "missing_sitemap_target")

    def test_current_site_has_crawlable_pages(self):
        root = Path(__file__).resolve().parents[1]
        result = audit(root)
        self.assertGreaterEqual(result["total"], 100)
        self.assertFalse([r for r in result["rows"] if r.get("error")])
        quality = result["sourceData"]["offers"]
        self.assertEqual(quality["expiredSitemapLeaks"], [])
        self.assertEqual(quality["verifiedPastExpiry"], [])
        self.assertEqual(quality["nonIndexableSitemapLeaks"], [])
        self.assertEqual(quality["missingChineseWhy"], [])
        self.assertEqual(quality["missingChineseFreeSummary"], [])
        self.assertEqual(quality["missingOfficialEvidence"], [])

    def test_source_data_audit_flags_expired_leaks_and_review_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            (data / "offers.json").write_text(
                '[{"id":"old","status":"expired","lastVerifiedAt":"2026-10-01",'
                '"why":"Expired campaign","freeSummary":"Expired","sourceUrls":["https://official.example"]},'
                '{"id":"current","status":"verified","lastVerifiedAt":"2026-08-01",'
                '"why":"English only","freeSummary":"Free quota","expires_at":"2026-10-01","register":"https://official.example"}]',
                encoding="utf-8",
            )
            (data / "models.json").write_text(
                '[{"id":"model-1","status":"online","lastSeenAt":"2026-08-01","sourceUrl":""}]',
                encoding="utf-8",
            )
            report = _audit_source_data(
                root,
                indexed_paths={"/offers/old/"},
                today=date(2026, 10, 20),
            )
            offers = report["offers"]
            self.assertEqual(offers["expiredSitemapLeaks"], ["old"])
            self.assertEqual(offers["nonIndexableSitemapLeaks"], ["old"])
            self.assertEqual(offers["staleVerificationReview"][0]["id"], "current")
            self.assertEqual(offers["verifiedPastExpiry"][0]["id"], "current")
            self.assertEqual(offers["missingChineseWhy"], ["current"])
            self.assertEqual(offers["missingChineseFreeSummary"], ["current"])
            self.assertEqual(report["models"]["missingOfficialSource"], ["model-1"])
            self.assertEqual(report["models"]["staleObservationReview"][0]["id"], "model-1")


if __name__ == "__main__":
    unittest.main()
