import unittest

from crawler.diff import build_review_queue, compare_offers


def offer(offer_id, quota="100 credits", status="verified"):
    return {"id": offer_id, "quota": quota, "status": status, "productType": "free_ide"}


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


if __name__ == "__main__":
    unittest.main()
