"""Validation for the public Free AI Index data contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FIELDS = {
    "id", "order", "date", "name", "provider", "model", "type", "productType",
    "freeMechanism", "freeSummary", "validitySummary", "accessSummary", "title",
    "why", "mechanism", "validity", "access", "command", "register", "links",
    "sourceUrls", "evidence", "status", "confidence", "lastVerifiedAt",
}
PRODUCT_TYPES = {"free_ide", "api", "coding_plan", "open_weights", "payg", "web_infrastructure"}
MECHANISMS = {"permanent", "monthly_quota", "daily_quota", "weekly_quota", "trial", "first_month_promo", "limited_time_free", "open_weights", "not_confirmed"}
STATUSES = {"verified", "changed", "expired", "unavailable", "needs_review"}
CONFIDENCES = {"high", "medium", "low"}
REQUIREMENT_VALUES = {"yes", "no", "unknown"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CAPABILITIES = {
    "search", "fetch", "extract", "crawl", "map", "browser", "agent",
    "model_api", "free_ide", "coding_plan", "open_weights",
}
API_CAPABILITIES = {
    "search", "fetch", "extract", "crawl", "map", "browser", "agent", "model_api",
}
PRICING_MODELS = {
    "permanent_free", "monthly_quota", "daily_quota", "weekly_quota",
    "free_rate_limited", "free_credits", "trial", "limited_time_free",
    "payg", "metered_paid", "not_confirmed",
}
OVERAGE_BEHAVIORS = {"stop", "metered", "wallet", "auto_reload", "unknown"}
FREE_PRICING_MODELS = {
    "monthly_quota", "daily_quota", "weekly_quota", "free_rate_limited",
    "free_credits", "trial", "limited_time_free",
}
WEB_REQUIRED_FIELDS = {
    "providerId", "productId", "offerVariant", "capabilities", "pricingModel",
    "freePolicy", "limits", "billing", "usageGuide",
}


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def _validate_usage_guide(guide: object, capabilities: list[str]) -> list[str]:
    if not isinstance(guide, dict):
        return ["usageGuide must be an object"]

    errors: list[str] = []
    if not isinstance(guide.get("summary"), str) or not guide["summary"].strip():
        errors.append("usageGuide summary must be a non-empty string")
    if not isinstance(guide.get("prerequisites"), list) or not guide["prerequisites"]:
        errors.append("usageGuide prerequisites must be a non-empty list")
    if not isinstance(guide.get("steps"), list) or len(guide["steps"]) < 2:
        errors.append("usageGuide steps must contain at least two items")
    docs_url = guide.get("docsUrl")
    if docs_url is not None and not _https_url(docs_url):
        errors.append("usageGuide docsUrl must be an https URL without credentials")
    examples = guide.get("examples")
    if not isinstance(examples, dict) or not examples:
        errors.append("usageGuide examples must be a non-empty object")
    else:
        for code in examples.values():
            if not isinstance(code, str) or not code.strip() or "..." in code or "TODO" in code.upper():
                errors.append("usageGuide examples must be executable")
                break

    if set(capabilities) & API_CAPABILITIES:
        for field in ("endpoint", "method", "authentication"):
            if not isinstance(guide.get(field), str) or not guide[field].strip():
                errors.append(f"usageGuide {field} is required for API capabilities")
        if isinstance(guide.get("endpoint"), str) and not _https_url(guide["endpoint"]):
            errors.append("usageGuide endpoint must be an https URL without credentials")
        if isinstance(guide.get("method"), str) and guide["method"].upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            errors.append("usageGuide method is not supported")
    return errors


def _validate_structured_offer_fields(offer: dict) -> list[str]:
    errors: list[str] = []
    product_type = offer.get("productType")
    if product_type == "web_infrastructure":
        missing = sorted(WEB_REQUIRED_FIELDS - offer.keys())
        errors.extend(f"missing field: {field}" for field in missing)

    if any(field in offer for field in ("providerId", "productId", "offerVariant")):
        for field in ("providerId", "productId", "offerVariant"):
            if field in offer and (not isinstance(offer[field], str) or not offer[field].strip()):
                errors.append(f"{field} must be a non-empty string")

    capabilities = offer.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list) or not capabilities or not all(isinstance(item, str) for item in capabilities):
            errors.append("capabilities must be a non-empty list of strings")
            capabilities = []
        else:
            errors.extend(f"unsupported capability: {item}" for item in capabilities if item not in CAPABILITIES)

    pricing_model = offer.get("pricingModel")
    if pricing_model is not None and pricing_model not in PRICING_MODELS:
        errors.append(f"pricingModel is not supported: {pricing_model}")

    if pricing_model in FREE_PRICING_MODELS and not isinstance(offer.get("freePolicy"), dict):
        errors.append("freePolicy must be an object for free pricing models")
    if "freePolicy" in offer and offer["freePolicy"] is not None and not isinstance(offer["freePolicy"], dict):
        errors.append("freePolicy must be an object or null")

    limits = offer.get("limits")
    if limits is not None:
        if not isinstance(limits, dict):
            errors.append("limits must be an object")
        else:
            for field, value in limits.items():
                if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                    errors.append(f"limits.{field} must be a non-negative integer or null")

    billing = offer.get("billing")
    if billing is not None:
        if not isinstance(billing, dict):
            errors.append("billing must be an object")
        else:
            if not isinstance(billing.get("walletRequired"), bool):
                errors.append("billing.walletRequired must be a boolean")
            if billing.get("cardRequired") not in REQUIREMENT_VALUES:
                errors.append("billing.cardRequired must be yes, no or unknown")
            if billing.get("autoReload") not in {"yes", "no", "unknown"}:
                errors.append("billing.autoReload must be yes, no or unknown")
            if billing.get("overageBehavior") not in OVERAGE_BEHAVIORS:
                errors.append("billing.overageBehavior is not supported")
            prices = billing.get("prices")
            if not isinstance(prices, list):
                errors.append("billing.prices must be a list")
            else:
                for price in prices:
                    if not isinstance(price, dict) or not all(isinstance(price.get(field), str) and price[field].strip() for field in ("capability", "unit", "price")):
                        errors.append("billing.prices must contain capability, unit and price")
                        break
                if pricing_model in {"payg", "metered_paid"} and not prices:
                    errors.append("billing.prices must contain a unit price")

    if "usageGuide" in offer:
        errors.extend(_validate_usage_guide(offer["usageGuide"], capabilities or []))
    return errors


def validate_offer(offer: object) -> list[str]:
    if not isinstance(offer, dict):
        return ["offer must be an object"]

    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - offer.keys())
    errors.extend(f"missing field: {field}" for field in missing)

    if "id" in offer and (not isinstance(offer["id"], str) or not offer["id"].strip()):
        errors.append("id must be a non-empty string")
    if "order" in offer and not isinstance(offer["order"], int):
        errors.append("order must be an integer")
    for field in ("date", "lastVerifiedAt"):
        if field in offer and (not isinstance(offer[field], str) or not DATE_RE.fullmatch(offer[field])):
            errors.append(f"{field} must use YYYY-MM-DD")
    if "type" in offer and (not isinstance(offer["type"], list) or not all(isinstance(item, str) for item in offer["type"])):
        errors.append("type must be a list of strings")
    if "productType" in offer and offer["productType"] not in PRODUCT_TYPES:
        errors.append(f"productType is not supported: {offer['productType']}")
    if "freeMechanism" in offer and offer["freeMechanism"] not in MECHANISMS:
        errors.append(f"freeMechanism is not supported: {offer['freeMechanism']}")
    if "status" in offer and offer["status"] not in STATUSES:
        errors.append(f"status is not supported: {offer['status']}")
    if "confidence" in offer and offer["confidence"] not in CONFIDENCES:
        errors.append(f"confidence is not supported: {offer['confidence']}")
    if "register" in offer and not _https_url(offer["register"]):
        errors.append("register must be an https URL without credentials")
    if "sourceUrls" in offer:
        if not isinstance(offer["sourceUrls"], list) or not offer["sourceUrls"]:
            errors.append("sourceUrls must be a non-empty list")
        else:
            errors.extend("sourceUrls contains a non-https URL" for url in offer["sourceUrls"] if not _https_url(url))
    if "links" in offer:
        if not isinstance(offer["links"], list):
            errors.append("links must be a list")
        else:
            for link in offer["links"]:
                if not isinstance(link, list) or len(link) != 2 or not isinstance(link[0], str) or not _https_url(link[1]):
                    errors.append("links must contain [label, https_url] pairs")
    for field in ("phoneRequired", "cardRequired"):
        if field in offer and offer[field] not in REQUIREMENT_VALUES:
            errors.append(f"{field} must be yes, no or unknown")
    for field in ("name", "provider", "model", "title", "why", "mechanism", "validity", "access", "command", "evidence"):
        if field in offer and (not isinstance(offer[field], str) or not offer[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    errors.extend(_validate_structured_offer_fields(offer))
    return errors


def validate_offers(source: str | Path | list[dict]) -> list[str]:
    data = json.loads(Path(source).read_text(encoding="utf-8")) if isinstance(source, (str, Path)) else source
    if not isinstance(data, list):
        return ["offers file must contain a JSON list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, offer in enumerate(data):
        for error in validate_offer(offer):
            errors.append(f"offers[{index}]: {error}")
        if isinstance(offer, dict) and isinstance(offer.get("id"), str):
            if offer["id"] in ids:
                errors.append(f"duplicate id: {offer['id']}")
            ids.add(offer["id"])
    return errors
