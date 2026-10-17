import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from scripts.check_public_home_performance import expected_assets, expected_data_asset, fetch


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

    @patch("scripts.check_public_home_performance.time.sleep")
    @patch("scripts.check_public_home_performance.urllib.request.urlopen")
    def test_fetch_retries_transient_connection_timeout(self, urlopen, _sleep):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = b"ok"
        response.headers.items.return_value = [("Cache-Control", "max-age=300")]
        urlopen.side_effect = [
            urllib.error.URLError(TimeoutError("temporary timeout")),
            response,
        ]

        result = fetch("https://example.test/asset")

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["body"], b"ok")
        self.assertEqual(result["headers"]["cache-control"], "max-age=300")
        self.assertEqual(urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
