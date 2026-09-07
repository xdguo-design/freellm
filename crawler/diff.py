"""Compare normalized offer data and create human-reviewable changes."""

from __future__ import annotations

from datetime import datetime, timezone

KEY_FIELDS = (
    "productType", "capabilities", "pricingModel", "freePolicy", "limits", "billing",
    "usageGuide", "freeMechanism", "quota", "validity", "renewal", "availability",
    "phoneRequired", "cardRequired", "officialActionUrl", "sourceUrls", "status",
)


def compare_offers(previous: list[dict], current: list[dict]) -> list[dict]:
    old = {item["id"]: item for item in previous}
    new = {item["id"]: item for item in current}
    changes: list[dict] = []
    for offer_id in sorted(new.keys() - old.keys()):
        changes.append({"offerId": offer_id, "changeType": "added", "before": None, "after": new[offer_id], "needsReview": True})
    for offer_id in sorted(old.keys() - new.keys()):
        changes.append({"offerId": offer_id, "changeType": "removed", "before": old[offer_id], "after": None, "needsReview": True})
    for offer_id in sorted(old.keys() & new.keys()):
        fields = {field: {"before": old[offer_id].get(field), "after": new[offer_id].get(field)} for field in KEY_FIELDS if old[offer_id].get(field) != new[offer_id].get(field)}
        if fields:
            changes.append({"offerId": offer_id, "changeType": "changed", "fields": fields, "needsReview": True})
    return changes


def build_review_queue(changes: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return [{"createdAt": now, "state": "pending", **change} for change in changes]
