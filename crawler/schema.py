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
MODEL_REQUIRED_FIELDS = {
    "id", "providerId", "provider", "model", "score", "context", "maxOutput",
    "modality", "rateLimit", "released", "usageActivity", "status", "sourceUrl",
    "sourceKind", "lastSeenAt",
}
MODEL_STATUSES = {"online", "offline", "degraded", "unknown", "needs_review"}
FRESHNESS_STATUSES = {"new", "current", "stale"}
OPERATION_PRODUCT_TYPES = {"api", "cli", "web", "download", "ide"}
ACCESS_STATUSES = {"current", "needs_review", "unknown", "stale", "retired"}
LICENSE_ACCEPTANCE_VALUES = {"yes", "no", "unknown", "model_dependent"}
VERIFICATION_STATUSES = {"verified", "partial", "unverified"}
REGION_POLICY_TYPES = {
    "allowlist", "denylist", "cloud_region", "model_specific",
    "provider_model_dynamic", "unknown",
}
SEARCH_METHODS = {
    "official_model_catalog", "official_model_api", "client_model_selector",
    "official_docs", "official_website_console", "retired_service",
}
REGISTRATION_STATUSES = {"available", "unavailable"}
COUNTRY_CODE_RE = re.compile(r"^[A-Z]{2}$")
PROVIDER_ACCESS_REQUIRED_FIELDS = {
    "providerId", "profileId", "registerUrl", "accountRequired", "emailRequired",
    "phoneRequired", "identityRequired", "cardRequired", "billingRequired",
    "apiKeyRequired", "licenseAcceptance", "modelApproval", "gpuRequired",
    "overageBehavior", "searchMethod", "regionPolicyId", "registrationSteps",
    "registrationStatus", "sourceUrls", "lastVerifiedAt", "verificationStatus",
    "confidence", "notes",
}
MODEL_ACCESS_REQUIRED_FIELDS = {
    "modelId", "providerId", "registrationProfileId", "modelSearchName",
    "extraRequirements", "regionOverridePolicyId", "quotaOverride",
    "accessStatus", "replacement", "sourceUrls", "lastVerifiedAt",
    "verificationStatus", "notes",
}
OPERATION_PLACEHOLDERS_RE = re.compile(r"(?:YOUR[_ -]?|REPLACE[_ -]?|TODO|PLACEHOLDER|<[^>]+>|\.\.\.)", re.IGNORECASE)
OPERATION_SECRET_RE = re.compile(r"(?:sk|key|token)-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9_-]{20,}", re.IGNORECASE)


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

    free_models = offer.get("freeModels")
    if free_models is not None:
        if not isinstance(free_models, list) or not free_models:
            errors.append("freeModels must be a non-empty list")
        else:
            for entry in free_models:
                if not isinstance(entry, dict):
                    errors.append("freeModels entries must be objects")
                    continue
                for field in ("model", "quota"):
                    value = entry.get(field)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"freeModels entry must contain a non-empty {field}")
                for field in ("label", "contextWindow", "note"):
                    if field in entry and (not isinstance(entry[field], str) or not entry[field].strip()):
                        errors.append(f"freeModels {field} must be a non-empty string")
                source = entry.get("sourceUrl")
                if source is not None and not _https_url(source):
                    errors.append("freeModels sourceUrl must be an https URL without credentials")

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


def validate_model(model: object) -> list[str]:
    if not isinstance(model, dict):
        return ["model must be an object"]

    errors: list[str] = []
    missing = sorted(MODEL_REQUIRED_FIELDS - model.keys())
    errors.extend(f"missing field: {field}" for field in missing)
    for field in ("id", "providerId", "provider", "model", "sourceKind"):
        if field in model and (not isinstance(model[field], str) or not model[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    score = model.get("score")
    if score is not None and (not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100):
        errors.append("score must be an integer from 0 to 100 or null")
    for field in ("context", "maxOutput", "rateLimit", "released", "usageActivity", "status"):
        if field in model and not isinstance(model[field], str):
            errors.append(f"{field} must be a string")
    modality = model.get("modality")
    if not isinstance(modality, list) or not modality or not all(isinstance(item, str) and item.strip() for item in modality):
        errors.append("modality must be a non-empty list of strings")
    if "status" in model and model["status"] not in MODEL_STATUSES:
        errors.append(f"status is not supported: {model['status']}")
    if "freshnessStatus" in model and model["freshnessStatus"] not in FRESHNESS_STATUSES:
        errors.append(f"freshnessStatus is not supported: {model['freshnessStatus']}")
    for field in ("lastSeenAt", "lastVerifiedAt"):
        if field in model and (not isinstance(model[field], str) or not DATE_RE.fullmatch(model[field])):
            errors.append(f"{field} must use YYYY-MM-DD")
    if "sourceUrl" in model and not _https_url(model["sourceUrl"]):
        errors.append("sourceUrl must be an https URL without credentials")
    return errors


def validate_models(source: str | Path | list[dict]) -> list[str]:
    data = json.loads(Path(source).read_text(encoding="utf-8")) if isinstance(source, (str, Path)) else source
    if not isinstance(data, list):
        return ["models file must contain a JSON list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, model in enumerate(data):
        for error in validate_model(model):
            errors.append(f"models[{index}]: {error}")
        if isinstance(model, dict) and isinstance(model.get("id"), str):
            if model["id"] in ids:
                errors.append(f"duplicate id: {model['id']}")
            ids.add(model["id"])
    return errors


def validate_operation_guides(source: object, label: str = "operation guides") -> list[str]:
    """Validate detailed, reproducible access instructions for a provider."""
    if isinstance(source, (str, Path)):
        source = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(source, dict):
        return [f"{label} must be an object"]

    errors: list[str] = []
    provider_id = source.get("providerId")
    if not isinstance(provider_id, str) or not provider_id.strip():
        errors.append(f"{label} providerId must be a non-empty string")
    paths = source.get("paths")
    if not isinstance(paths, list) or not paths:
        return errors + [f"{label} paths must be a non-empty list"]

    path_ids: set[str] = set()
    for index, path in enumerate(paths):
        prefix = f"{label}.paths[{index}]"
        if not isinstance(path, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("id", "label", "validation"):
            if not isinstance(path.get(field), str) or not path[field].strip():
                errors.append(f"{prefix} {field} must be a non-empty string")
        path_id = path.get("id")
        if isinstance(path_id, str):
            if path_id in path_ids:
                errors.append(f"duplicate operation path id: {path_id}")
            path_ids.add(path_id)
        product_type = path.get("productType")
        if product_type not in OPERATION_PRODUCT_TYPES:
            errors.append(f"{prefix} productType is not supported: {product_type}")
        prerequisites = path.get("prerequisites")
        if not isinstance(prerequisites, list) or not prerequisites or not all(isinstance(item, str) and item.strip() for item in prerequisites):
            errors.append(f"{prefix} prerequisites must be a non-empty list of strings")
        steps = path.get("steps")
        if not isinstance(steps, list) or len(steps) < 3:
            errors.append(f"{prefix} steps must contain at least three items")
        else:
            for step_index, step in enumerate(steps):
                step_prefix = f"{prefix}.steps[{step_index}]"
                if isinstance(step, str):
                    if not step.strip():
                        errors.append(f"{step_prefix} must not be empty")
                    continue
                if not isinstance(step, dict) or not isinstance(step.get("title"), str) or not step["title"].strip() or not isinstance(step.get("detail"), str) or not step["detail"].strip():
                    errors.append(f"{step_prefix} must contain title and detail")
                    continue
                command = step.get("command")
                if command is not None and (not isinstance(command, str) or not command.strip()):
                    errors.append(f"{step_prefix} command must be a non-empty string")
                if isinstance(command, str) and (_operation_has_placeholder(command) or _operation_has_secret(command)):
                    errors.append(f"{step_prefix} command contains a placeholder or plaintext secret")

        source_urls = path.get("sourceUrls")
        if not isinstance(source_urls, list) or not source_urls:
            errors.append(f"{prefix} sourceUrls must be a non-empty list")
        elif any(not _https_url(url) for url in source_urls):
            errors.append(f"{prefix} sourceUrls must contain only HTTPS URLs")

        for field in ("endpoint", "example"):
            value = path.get(field)
            if isinstance(value, str) and (_operation_has_placeholder(value) or _operation_has_secret(value)):
                errors.append(f"{prefix} {field} contains a placeholder or plaintext secret")
        if product_type == "api":
            for field in ("endpoint", "auth", "example"):
                if not isinstance(path.get(field), str) or not path[field].strip():
                    errors.append(f"{prefix} {field} is required for API operation paths")
            if isinstance(path.get("endpoint"), str) and not _https_url(path["endpoint"]):
                errors.append(f"{prefix} endpoint must be an HTTPS URL")

    return errors


def _operation_has_placeholder(value: str) -> bool:
    return bool(OPERATION_PLACEHOLDERS_RE.search(value))


def _operation_has_secret(value: str) -> bool:
    return bool(OPERATION_SECRET_RE.search(value))


def _validate_verification_pair(errors: list[str], prefix: str, record: dict) -> None:
    verification = record.get("verificationStatus")
    if verification not in VERIFICATION_STATUSES:
        errors.append(f"{prefix} verificationStatus must be one of {sorted(VERIFICATION_STATUSES)}")
        return
    last_verified = record.get("lastVerifiedAt")
    if verification == "unverified":
        if last_verified is not None:
            errors.append(f"{prefix} lastVerifiedAt must be null when verificationStatus is unverified")
    else:
        if not isinstance(last_verified, str) or not DATE_RE.fullmatch(last_verified):
            errors.append(f"{prefix} lastVerifiedAt must use YYYY-MM-DD when verificationStatus is verified or partial")


def _validate_country_codes(errors: list[str], prefix: str, field: str, value: object) -> None:
    if not isinstance(value, list) or not all(isinstance(code, str) for code in value):
        errors.append(f"{prefix} {field} must be a list of ISO-3166 alpha-2 strings")
        return
    for code in value:
        if not COUNTRY_CODE_RE.fullmatch(code):
            errors.append(f"{prefix} {field} contains an invalid ISO-3166 alpha-2 code: {code}")


def validate_region_policy(policy: object) -> list[str]:
    if not isinstance(policy, dict):
        return ["region policy must be an object"]

    errors: list[str] = []
    for field in ("id", "type", "notes"):
        if not isinstance(policy.get(field), str) or not policy[field].strip():
            errors.append(f"region policy {field} must be a non-empty string")
    policy_type = policy.get("type")
    if policy_type is not None and policy_type not in REGION_POLICY_TYPES:
        errors.append(f"region policy type is not supported: {policy_type}")
    _validate_country_codes(errors, "region policy", "allowedCountries", policy.get("allowedCountries"))
    _validate_country_codes(errors, "region policy", "blockedCountries", policy.get("blockedCountries"))
    if policy_type == "allowlist" and isinstance(policy.get("allowedCountries"), list) and not policy["allowedCountries"]:
        if policy.get("countriesComplete") is not False:
            errors.append("allowlist policies with an empty country list must set countriesComplete to false")
    if policy_type == "cloud_region":
        endpoints = policy.get("endpoints")
        if not isinstance(endpoints, list) or not endpoints:
            errors.append("cloud_region policies must list their endpoints")
        else:
            for index, endpoint in enumerate(endpoints):
                if not isinstance(endpoint, dict) or not isinstance(endpoint.get("id"), str) or not endpoint["id"].strip():
                    errors.append(f"endpoints[{index}] must contain a non-empty id")
                if isinstance(endpoint, dict) and not _https_url(endpoint.get("url")):
                    errors.append(f"endpoints[{index}] url must be an https URL without credentials")
    source_urls = policy.get("sourceUrls")
    if policy_type != "unknown":
        if not isinstance(source_urls, list) or not source_urls:
            errors.append("region policy sourceUrls must be a non-empty list unless type is unknown")
        elif any(not _https_url(url) for url in source_urls):
            errors.append("region policy sourceUrls must contain only HTTPS URLs")
    elif source_urls is not None and not isinstance(source_urls, list):
        errors.append("region policy sourceUrls must be a list")
    _validate_verification_pair(errors, "region policy", policy)
    return errors


def validate_region_policies(source: str | Path | dict) -> list[str]:
    data = json.loads(Path(source).read_text(encoding="utf-8")) if isinstance(source, (str, Path)) else source
    if not isinstance(data, dict) or not isinstance(data.get("policies"), list) or not data["policies"]:
        return ["region policies file must contain an object with a non-empty policies list"]
    errors: list[str] = []
    if "priorityCountries" in data:
        _validate_country_codes(errors, "region policies", "priorityCountries", data["priorityCountries"])
    if "defaultCountryCode" in data:
        default_code = data["defaultCountryCode"]
        _validate_country_codes(errors, "region policies", "defaultCountryCode", [default_code] if isinstance(default_code, str) else default_code)
        priority = data.get("priorityCountries")
        if isinstance(default_code, str) and isinstance(priority, list) and default_code not in priority:
            errors.append("defaultCountryCode must be included in priorityCountries")
    if "defaultCountryNote" in data and (not isinstance(data["defaultCountryNote"], str) or not data["defaultCountryNote"].strip()):
        errors.append("defaultCountryNote must be a non-empty string")
    ids: set[str] = set()
    for index, policy in enumerate(data["policies"]):
        for error in validate_region_policy(policy):
            errors.append(f"policies[{index}]: {error}")
        if isinstance(policy, dict) and isinstance(policy.get("id"), str):
            if policy["id"] in ids:
                errors.append(f"duplicate region policy id: {policy['id']}")
            ids.add(policy["id"])
    return errors


def validate_provider_access(card: object) -> list[str]:
    if not isinstance(card, dict):
        return ["provider access card must be an object"]

    errors: list[str] = []
    missing = sorted(PROVIDER_ACCESS_REQUIRED_FIELDS - card.keys())
    errors.extend(f"missing field: {field}" for field in missing)
    for field in ("providerId", "profileId", "searchMethod", "regionPolicyId"):
        if field in card and (not isinstance(card[field], str) or not card[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    for field in ("accountRequired", "emailRequired", "phoneRequired", "identityRequired",
                  "cardRequired", "billingRequired", "apiKeyRequired", "modelApproval", "gpuRequired"):
        if field in card and card[field] not in REQUIREMENT_VALUES:
            errors.append(f"{field} must be yes, no or unknown")
    if "licenseAcceptance" in card and card["licenseAcceptance"] not in LICENSE_ACCEPTANCE_VALUES:
        errors.append(f"licenseAcceptance must be one of {sorted(LICENSE_ACCEPTANCE_VALUES)}")
    if "overageBehavior" in card and card["overageBehavior"] not in OVERAGE_BEHAVIORS:
        errors.append(f"overageBehavior is not supported: {card['overageBehavior']}")
    if "searchMethod" in card and card["searchMethod"] not in SEARCH_METHODS:
        errors.append(f"searchMethod is not supported: {card['searchMethod']}")
    if "registrationStatus" in card and card["registrationStatus"] not in REGISTRATION_STATUSES:
        errors.append(f"registrationStatus is not supported: {card['registrationStatus']}")
    if "confidence" in card and card["confidence"] not in CONFIDENCES:
        errors.append(f"confidence is not supported: {card['confidence']}")
    register_url = card.get("registerUrl")
    if register_url is not None and not _https_url(register_url):
        errors.append("registerUrl must be an https URL without credentials or null")
    steps = card.get("registrationSteps")
    if steps is not None and (not isinstance(steps, list) or not all(isinstance(step, str) and step.strip() for step in steps)):
        errors.append("registrationSteps must be a list of non-empty strings")
    source_urls = card.get("sourceUrls")
    if "sourceUrls" in card:
        if not isinstance(source_urls, list) or not source_urls:
            errors.append("sourceUrls must be a non-empty list")
        elif any(not _https_url(url) for url in source_urls):
            errors.append("sourceUrls must contain only HTTPS URLs")
    notes = card.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("notes must be a string or null")
    if card.get("registrationStatus") == "unavailable":
        if not isinstance(card.get("replacement"), str) or not card["replacement"].strip():
            errors.append("replacement must be a non-empty string when registrationStatus is unavailable")
    _validate_verification_pair(errors, "provider access card", card)
    return errors


def validate_provider_access_file(source: str | Path | list[dict]) -> list[str]:
    data = json.loads(Path(source).read_text(encoding="utf-8")) if isinstance(source, (str, Path)) else source
    if not isinstance(data, list):
        return ["provider access file must contain a JSON list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, card in enumerate(data):
        for error in validate_provider_access(card):
            errors.append(f"providerAccess[{index}]: {error}")
        if isinstance(card, dict) and isinstance(card.get("providerId"), str):
            if card["providerId"] in ids:
                errors.append(f"duplicate providerId: {card['providerId']}")
            ids.add(card["providerId"])
    return errors


def validate_model_access(card: object) -> list[str]:
    if not isinstance(card, dict):
        return ["model access card must be an object"]

    errors: list[str] = []
    missing = sorted(MODEL_ACCESS_REQUIRED_FIELDS - card.keys())
    errors.extend(f"missing field: {field}" for field in missing)
    for field in ("modelId", "providerId", "registrationProfileId", "modelSearchName"):
        if field in card and (not isinstance(card[field], str) or not card[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    extra = card.get("extraRequirements")
    if extra is not None and (not isinstance(extra, list) or not all(isinstance(item, str) and item.strip() for item in extra)):
        errors.append("extraRequirements must be a list of non-empty strings")
    quota = card.get("quotaOverride")
    if quota is not None and (not isinstance(quota, str) or not quota.strip()):
        errors.append("quotaOverride must be a non-empty string or null")
    region_override = card.get("regionOverridePolicyId")
    if region_override is not None and (not isinstance(region_override, str) or not region_override.strip()):
        errors.append("regionOverridePolicyId must be a non-empty string or null")
    replacement = card.get("replacement")
    if replacement is not None and (not isinstance(replacement, str) or not replacement.strip()):
        errors.append("replacement must be a non-empty string or null")
    notes = card.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("notes must be a string or null")
    if "accessStatus" in card and card["accessStatus"] not in ACCESS_STATUSES:
        errors.append(f"accessStatus is not supported: {card['accessStatus']}")
    source_urls = card.get("sourceUrls")
    if "sourceUrls" in card:
        if not isinstance(source_urls, list) or not source_urls:
            errors.append("sourceUrls must be a non-empty list")
        elif any(not _https_url(url) for url in source_urls):
            errors.append("sourceUrls must contain only HTTPS URLs")
    if card.get("accessStatus") == "retired":
        if not isinstance(card.get("replacement"), str) or not card["replacement"].strip():
            errors.append("retired cards must record a replacement")
        if not isinstance(source_urls, list) or not source_urls:
            errors.append("retired cards must cite official sourceUrls")
    _validate_verification_pair(errors, "model access card", card)
    return errors


def validate_model_access_file(source: str | Path | list[dict]) -> list[str]:
    data = json.loads(Path(source).read_text(encoding="utf-8")) if isinstance(source, (str, Path)) else source
    if not isinstance(data, list):
        return ["model access file must contain a JSON list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, card in enumerate(data):
        for error in validate_model_access(card):
            errors.append(f"modelAccess[{index}]: {error}")
        if isinstance(card, dict) and isinstance(card.get("modelId"), str):
            if card["modelId"] in ids:
                errors.append(f"duplicate modelId: {card['modelId']}")
            ids.add(card["modelId"])
    return errors


def validate_access_references(provider_cards: list[dict], model_cards: list[dict], policy_ids: set[str]) -> list[str]:
    """Validate cross-file references used by the access-card renderer."""
    errors: list[str] = []
    provider_ids = {str(card.get("providerId") or "") for card in provider_cards if isinstance(card, dict)}
    for card in provider_cards:
        if not isinstance(card, dict):
            errors.append("provider access card must be an object")
            continue
        policy_id = card.get("regionPolicyId")
        if policy_id not in policy_ids:
            errors.append(f"provider {card.get('providerId')} references unknown region policy: {policy_id}")
    for card in model_cards:
        if not isinstance(card, dict):
            errors.append("model access card must be an object")
            continue
        if card.get("providerId") not in provider_ids:
            errors.append(f"model {card.get('modelId')} references unknown provider: {card.get('providerId')}")
        override = card.get("regionOverridePolicyId")
        if override is not None and override not in policy_ids:
            errors.append(f"model {card.get('modelId')} references unknown region policy: {override}")
    return errors
