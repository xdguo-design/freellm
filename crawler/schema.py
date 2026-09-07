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
PRODUCT_TYPES = {"free_ide", "api", "coding_plan", "open_weights", "payg"}
MECHANISMS = {"permanent", "monthly_quota", "daily_quota", "weekly_quota", "trial", "first_month_promo", "limited_time_free", "open_weights", "not_confirmed"}
STATUSES = {"verified", "changed", "expired", "unavailable", "needs_review"}
CONFIDENCES = {"high", "medium", "low"}
REQUIREMENT_VALUES = {"yes", "no", "unknown"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


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
