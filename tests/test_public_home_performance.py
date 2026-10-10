import unittest

from scripts.check_public_home_performance import expected_assets, expected_data_asset


class PublicHomePerformanceTests(unittest.TestCase):
    def test_expected_assets_deduplicates_noscript_fallback_links(self):
        assets = expected_assets()
        self.assertEqual(len(assets), 4)
        self.assertEqual(len(assets), len(set(assets)))
        self.assertEqual(sum(path.endswith(".css") for path in assets), 2)
        self.assertEqual(sum(path.endswith(".js") for path in assets), 2)
        self.assertFalse(any(path.endswith(".json") for path in assets))

    def test_homepage_data_asset_is_separate_from_immutable_assets(self):
        assets = expected_assets()
        data_asset = expected_data_asset()

        self.assertEqual(data_asset, "data/offers-ranked.json")
        self.assertNotIn(data_asset, assets)


if __name__ == "__main__":
    unittest.main()
