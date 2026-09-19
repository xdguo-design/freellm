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

    def test_free_models_per_model_quota_list_is_accepted(self):
        offer = valid_offer()
        offer["freeModels"] = [
            {
                "model": "sensenova-6.8-flash-lite",
                "label": "SenseNova 6.8 Flash Lite",
                "quota": "60,000 积分 / 5 小时",
                "note": "轻量多模态",
                "sourceUrl": "https://www.sensenova.cn/token-plan",
            },
        ]
        self.assertEqual(validate_offer(offer), [])

    def test_free_models_reject_missing_quota_and_insecure_source(self):
        offer = valid_offer()
        offer["freeModels"] = [{"model": "some-model", "quota": " ", "sourceUrl": "http://example.com/plan"}]
        errors = validate_offer(offer)
        self.assertIn("freeModels entry must contain a non-empty quota", errors)
        self.assertIn("freeModels sourceUrl must be an https URL without credentials", errors)

    def test_free_models_must_be_a_non_empty_list(self):
        offer = valid_offer()
        offer["freeModels"] = []
        self.assertIn("freeModels must be a non-empty list", validate_offer(offer))

    def test_edition_key_and_hands_on_marks_are_accepted(self):
        offer = valid_offer()
        offer["key"] = True
        offer["editions"] = ["cn", "intl"]
        offer["editionOf"] = "cn"
        offer["siblingEditionId"] = "intl-twin"
        offer["handsOn"] = {"testedAt": "2026-09-17", "note": "实测调用通过"}
        self.assertEqual(validate_offer(offer), [])

    def test_edition_marks_reject_unknown_values(self):
        offer = valid_offer()
        offer["editions"] = ["cn", "overseas"]
        offer["key"] = "yes"
        offer["handsOn"] = {"testedAt": "2026-09-17"}
        errors = validate_offer(offer)
        self.assertIn("editions must be a non-empty list drawn from: cn, intl", errors)
        self.assertIn("key must be a boolean", errors)
        self.assertIn("handsOn.note must be a non-empty string", errors)

        mismatched = valid_offer()
        mismatched["editions"] = ["cn"]
        mismatched["editionOf"] = "intl"
        self.assertIn("editionOf must be one of the product's editions", validate_offer(mismatched))

    def test_sibling_edition_id_must_reference_a_known_offer(self):
        offer = valid_offer()
        offer["siblingEditionId"] = "missing-offer"
        errors = validate_offers([offer])
        self.assertIn("offers[0]: siblingEditionId does not match any offer id: missing-offer", errors)

    def test_endpoint_check_mark_is_accepted(self):
        offer = valid_offer()
        offer["endpointCheck"] = {"checkedAt": "2026-09-18", "verdict": "NEEDS_KEY", "note": "接口存活，鉴权正常"}
        self.assertEqual(validate_offer(offer), [])

        site_only = valid_offer()
        site_only["endpointCheck"] = {"checkedAt": "2026-09-18", "verdict": "OK"}
        self.assertEqual(validate_offer(site_only), [])

    def test_endpoint_check_mark_rejects_bad_verdict_and_date(self):
        offer = valid_offer()
        offer["endpointCheck"] = {"checkedAt": "2026-09-18", "verdict": "MAYBE", "note": ""}
        errors = validate_offer(offer)
        self.assertIn("endpointCheck.verdict must be one of: ALIVE, NEEDS_KEY, NETWORK_ERROR, OK, PATH_CHECK", errors)
        self.assertIn("endpointCheck.note must be a non-empty string when present", errors)

        bad_date = valid_offer()
        bad_date["endpointCheck"] = {"checkedAt": "09/18/2026", "verdict": "OK"}
        self.assertIn("endpointCheck.checkedAt must use YYYY-MM-DD", validate_offer(bad_date))

    def test_network_check_mark_is_accepted(self):
        offer = valid_offer()
        offer["networkCheck"] = {
            "checkedAt": "2026-09-18",
            "method": "本机大陆网络直连 + check-host.net 海外节点",
            "region": "both",
            "cnMs": 266,
            "intlMs": 516,
            "speedGrade": "normal",
        }
        self.assertEqual(validate_offer(offer), [])

        unreachable = valid_offer()
        unreachable["networkCheck"] = {
            "checkedAt": "2026-09-18",
            "region": "none",
            "cnMs": None,
            "intlMs": None,
            "speedGrade": None,
        }
        self.assertEqual(validate_offer(unreachable), [])

    def test_network_check_mark_rejects_bad_region_speed_and_latency(self):
        offer = valid_offer()
        offer["networkCheck"] = {
            "checkedAt": "09/18/2026",
            "region": "mars",
            "speedGrade": "blazing",
            "cnMs": -5,
        }
        errors = validate_offer(offer)
        self.assertIn("networkCheck.checkedAt must use YYYY-MM-DD", errors)
        self.assertIn("networkCheck.region must be one of: both, cn, intl, none", errors)
        self.assertIn("networkCheck.speedGrade must be one of: fast, normal, slow, very_slow", errors)
        self.assertIn("networkCheck.cnMs must be a non-negative integer or null", errors)

    def test_public_edition_marks_validate_against_the_contract(self):
        self.assertEqual(validate_offers(Path(__file__).resolve().parents[1] / "data" / "offers.json"), [])


if __name__ == "__main__":
    unittest.main()
