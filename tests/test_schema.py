import json
import unittest
from pathlib import Path

from crawler.schema import validate_offer, validate_offers


def valid_offer():
    return {
        "id": "valid-offer",
        "order": 1,
        "date": "2026-09-07",
        "name": "Valid offer",
        "provider": "Valid provider",
        "model": "Valid model",
        "type": ["api"],
        "productType": "api",
        "freeMechanism": "permanent",
        "freeSummary": "Free test access",
        "validitySummary": "Ongoing",
        "accessSummary": "Global",
        "title": "Valid offer",
        "why": "A valid test offer.",
        "mechanism": "Free access",
        "validity": "Ongoing",
        "access": "Global",
        "command": "Use the official API quickstart.",
        "register": "https://example.com/register",
        "links": [["Docs", "https://example.com/docs"]],
        "sourceUrls": ["https://example.com/pricing"],
        "evidence": "Official pricing page",
        "status": "verified",
        "confidence": "high",
        "lastVerifiedAt": "2026-09-07",
    }


def valid_web_offer():
    offer = valid_offer()
    offer.update({
        "providerId": "tinyfish",
        "productId": "tinyfish-web",
        "offerVariant": "search-fetch-free",
        "productType": "web_infrastructure",
        "capabilities": ["search", "fetch"],
        "pricingModel": "free_rate_limited",
        "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
        "limits": {"requestsPerMinute": 30, "urlsPerMinute": 150},
        "billing": {
            "walletRequired": False,
            "cardRequired": "no",
            "autoReload": "unknown",
            "overageBehavior": "stop",
            "prices": [],
        },
        "usageGuide": {
            "summary": "搜索和抓取网页",
            "prerequisites": ["注册账号"],
            "steps": ["创建访问凭据", "发送请求"],
            "endpoint": "https://api.tinyfish.io/search",
            "method": "POST",
            "authentication": "Authorization: Bearer ${API_KEY}",
            "examples": {"curl": "curl --request POST https://api.tinyfish.io/search"},
            "docsUrl": "https://future.tinyfish.io/pricing",
        },
    })
    return offer


class SchemaTests(unittest.TestCase):
    def test_all_seed_offers_have_required_fields(self):
        self.assertEqual(validate_offers(Path("data/offers.json")), [])

    def test_global_opencode_offer_is_in_the_directory(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        opencode = next(offer for offer in offers if offer["id"] == "opencode-zen-free")
        self.assertEqual(opencode["originCountry"], "International")
        self.assertEqual(opencode["freeMechanism"], "limited_time_free")
        self.assertIn("opencode.ai", opencode["register"])

    def test_global_coding_peers_are_in_the_directory(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        offer_ids = {offer["id"] for offer in offers}
        self.assertTrue({
            "github-copilot-free",
            "cursor-hobby",
            "amazon-q-free",
            "google-antigravity-free",
        }.issubset(offer_ids))

    def test_doubao_and_qwen_are_explicitly_discoverable(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        doubao = next(offer for offer in offers if offer["id"] == "doubao")
        qwen = next(offer for offer in offers if offer["id"] == "aliyun-qwen-free-quota")
        self.assertIn("豆包", doubao["name"])
        self.assertIn("通义千问", qwen["providerMeta"])
        self.assertEqual(qwen["freeMechanism"], "trial")
        self.assertIn("90 days", qwen["validity"])
        self.assertIn("bailian.console.aliyun.com", qwen["register"])

    def test_invalid_product_type_is_rejected(self):
        errors = validate_offer({"id": "x", "productType": "unknown"})
        self.assertTrue(any("productType" in error for error in errors))

    def test_duplicate_ids_are_rejected(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        duplicate = [offers[0], offers[0]]
        errors = validate_offers(duplicate)
        self.assertTrue(any("duplicate id" in error for error in errors))

    def test_web_offer_requires_capabilities_limits_billing_and_usage_guide(self):
        self.assertEqual(validate_offer(valid_web_offer()), [])

    def test_usage_guide_rejects_ellipsis_and_missing_capability_fields(self):
        offer = valid_web_offer()
        offer["usageGuide"]["examples"] = {"curl": "curl ..."}
        errors = validate_offer(offer)
        self.assertIn("usageGuide examples must be executable", errors)

    def test_paid_web_offer_requires_unit_price(self):
        offer = valid_web_offer()
        offer["pricingModel"] = "payg"
        offer["billing"]["prices"] = []
        self.assertIn("billing.prices must contain a unit price", validate_offer(offer))

    def test_every_public_offer_has_usage_guide_and_capabilities(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        for offer in offers:
            self.assertIn("usageGuide", offer, offer["id"])
            self.assertTrue(offer["usageGuide"]["steps"], offer["id"])
            self.assertTrue(offer.get("capabilities"), offer["id"])

    def test_mvp_web_offers_have_independent_variants(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        web = [item for item in offers if item.get("productType") == "web_infrastructure"]
        keys = {(item["providerId"], item["productId"], item["offerVariant"]) for item in web}
        self.assertEqual(len(keys), len(web))

    def test_coding_plans_are_not_labeled_as_free_ides(self):
        offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
        for offer in offers:
            if offer["productType"] == "coding_plan":
                self.assertEqual(offer["capabilities"], ["coding_plan"], offer["id"])


if __name__ == "__main__":
    unittest.main()
