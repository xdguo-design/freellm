import unittest

from scripts.sync_readme_counts import render


class ReadmeCountsSyncTests(unittest.TestCase):
    def test_updates_both_language_counts_and_is_idempotent(self):
        text = (
            "- **80 个**资源目录记录（75 条当前有效、3 条已结束、2 条待核验；最近一次扫描观测到 78 条资源），另有 **265 条**第三方模型目录记录和 **57 家**厂家目录\n"
            "- **80** curated offer records (75 currently active, 3 ended and 2 held for review; the latest scan observed 78 offers), plus **265** third-party model-directory records across **57** providers\n"
        )
        scan = {"offers": 75, "offersExpired": 3, "offersNeedsReview": 2, "scannedOffers": 78}
        output = render(text, scan, [{}] * 80, [{}] * 267, [{}] * 57)
        self.assertIn("75 条当前有效、3 条已结束、2 条待核验", output)
        self.assertIn("**267 条**", output)
        self.assertIn("75 currently active, 3 ended and 2 held for review", output)
        self.assertIn("**267** third-party", output)
        self.assertEqual(render(output, scan, [{}] * 80, [{}] * 267, [{}] * 57), output)

    def test_missing_bilingual_count_anchor_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "anchors changed"):
            render("README without numeric catalog summary", {
                "offers": 0, "offersExpired": 0, "offersNeedsReview": 0, "scannedOffers": 0
            }, [], [], [])

    def test_rejects_conflicting_source_counts(self):
        text = (
            "- **80 个**资源目录记录（77 条当前有效、3 条已结束；最近一次扫描观测到 78 条资源），另有 **265 条**第三方模型目录记录和 **57 家**厂家目录\n"
            "- **80** curated offer records (77 currently active and 3 ended; the latest scan observed 78 offers), plus **265** third-party model-directory records across **57** providers\n"
        )
        with self.assertRaisesRegex(ValueError, "do not match"):
            render(text, {"offers": 76, "offersExpired": 3, "offersNeedsReview": 0, "scannedOffers": 78}, [{}] * 80, [{}], [{}])


if __name__ == "__main__":
    unittest.main()
