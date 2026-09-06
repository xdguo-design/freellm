import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_static import build


class BuildStaticTests(unittest.TestCase):
    def test_build_replaces_offer_data_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "offers.json"
            html_path = root / "index.html"
            data_path.write_text(json.dumps([{
                "id": "x", "order": 1, "date": "2026-09-06", "name": "X", "provider": "X", "model": "X", "type": ["free"], "productType": "api", "freeMechanism": "permanent", "freeSummary": "free", "validitySummary": "ongoing", "accessSummary": "global", "title": "X", "why": "x", "mechanism": "x", "validity": "x", "access": "x", "command": "x", "register": "https://example.com", "links": [["x", "https://example.com"]], "sourceUrls": ["https://example.com"], "evidence": "x", "status": "verified", "confidence": "high", "lastVerifiedAt": "2026-09-06"
            }]), encoding="utf-8")
            html_path.write_text('<script type="application/json" id="offer-data">\n[]\n</script>', encoding="utf-8")
            self.assertTrue(build(data_path, html_path))
            self.assertIn('"id": "x"', html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
