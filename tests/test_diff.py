import unittest

from crawler.diff import build_review_queue, compare_offers


def offer(offer_id, quota="100 credits", status="verified"):
    return {"id": offer_id, "quota": quota, "status": status, "productType": "free_ide"}


def web_offer(offer_id="web", limits=None, usage_guide=None):
    return {
        "id": offer_id,
        "productType": "web_infrastructure",
        "limits": limits or {"requestsPerMinute": 30},
        "usageGuide": usage_guide or {"steps": ["open", "run"]},
    }


class DiffTests(unittest.TestCase):
    def test_detects_added_and_changed_offers(self):
        changes = compare_offers([offer("a")], [offer("a", quota="50 credits"), offer("b")])
        self.assertEqual([change["changeType"] for change in changes], ["added", "changed"])
        queue = build_review_queue(changes)
        self.assertTrue(all(item["needsReview"] and item["state"] == "pending" for item in queue))

    def test_detects_status_change(self):
        changes = compare_offers([offer("a")], [offer("a", status="expired")])
        self.assertEqual(changes[0]["fields"]["status"]["after"], "expired")

    def test_same_snapshot_has_no_changes(self):
        self.assertEqual(compare_offers([offer("a")], [offer("a")]), [])

    def test_detects_nested_limits_and_usage_guide_changes(self):
        previous = [web_offer(limits={"requestsPerMinute": 30})]
        current = [web_offer(limits={"requestsPerMinute": 20})]
        changes = compare_offers(previous, current)
        self.assertEqual(changes[0]["changeType"], "changed")
        self.assertIn("limits", changes[0]["fields"])


if __name__ == "__main__":
    unittest.main()
