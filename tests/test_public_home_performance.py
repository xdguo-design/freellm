import unittest

from scripts.check_public_home_performance import expected_assets


class PublicHomePerformanceTests(unittest.TestCase):
    def test_expected_assets_deduplicates_noscript_fallback_links(self):
        assets = expected_assets()
        self.assertEqual(len(assets), 4)
        self.assertEqual(len(assets), len(set(assets)))
        self.assertEqual(sum(path.endswith(".css") for path in assets), 2)
        self.assertEqual(sum(path.endswith(".js") for path in assets), 2)


if __name__ == "__main__":
    unittest.main()
