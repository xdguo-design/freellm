"""Guard Google canonical host consolidation against silent regression."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CanonicalHostRedirectTests(unittest.TestCase):
    def test_www_redirects_permanently_to_apex_preserving_path(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        candidates = [
            rule for rule in config["redirects"]
            if any(condition.get("type") == "host" and condition.get("value") == "www.freellm.top"
                   for condition in rule.get("has", []))
        ]
        self.assertEqual(len(candidates), 1, candidates)
        rule = candidates[0]
        self.assertEqual(rule["source"], "/:path*")
        self.assertEqual(rule["destination"], "https://freellm.top/:path*")
        self.assertTrue(rule["permanent"])

    def test_host_redirect_does_not_capture_canonical_domain(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirect = next(r for r in config["redirects"] if r.get("destination") == "https://freellm.top/:path*")
        self.assertEqual(redirect["has"], [{"type": "host", "value": "www.freellm.top"}])
        self.assertEqual(config["redirects"][0], redirect, "host consolidation should be first")


if __name__ == "__main__":
    unittest.main()
