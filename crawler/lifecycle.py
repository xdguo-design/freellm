"""Lifecycle helpers for time-limited offers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


INACTIVE_STATUSES = {"expired", "unavailable"}


def parse_offer_datetime(value: object) -> datetime | None:
    """Parse an ISO-8601 offer timestamp and require an explicit timezone."""
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("offer datetime must be a string")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("offer datetime must include an explicit timezone")
    return parsed


def offer_is_public(offer: dict, now: datetime | None = None) -> bool:
    """Return whether an offer should appear in public listings/build output."""
    if offer.get("status") in INACTIVE_STATUSES:
        return False

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        current = current.replace(tzinfo=timezone.utc)

    starts_at = parse_offer_datetime(offer.get("startsAt"))
    ends_at = parse_offer_datetime(offer.get("endsAt"))
    if starts_at and current < starts_at:
        return False
    if ends_at and current > ends_at:
        return False
    return True


def public_offers(offers: Iterable[dict], now: datetime | None = None) -> list[dict]:
    """Filter offers for public site generation while keeping source data intact."""
    return [offer for offer in offers if offer_is_public(offer, now=now)]
