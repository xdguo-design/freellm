"""Regression contract: an unavailable scan summary must not leak stale metrics."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ScanTrustFallbackTests(unittest.TestCase):
    def test_scan_fetch_failure_hides_every_shared_metric_surface(self):
        script = (ROOT / "js" / "scan-trust.js").read_text(encoding="utf-8")
        self.assertIn("if (!response.ok) throw new Error('scan source unavailable')", script)
        fallback = script.split("} catch (error) {", 1)[1]
        for selector in (
            ".prototype-stats .prototype-stat strong:not(.prototype-top10)",
            "[data-scan-stat]",
            ".ref-update-metrics > article strong",
            ".ref-update-snapshot .log-snapshot-card strong",
            "heroCount",
            "daily-log-badge",
            ".hero-intel-head > span",
            "[data-scan-date]",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, fallback)
        self.assertIn("最近扫描：暂无记录", fallback)
        self.assertIn("document.querySelectorAll('.mini-chart').forEach(n=>n.remove())", fallback)

if __name__ == "__main__":
    unittest.main()
