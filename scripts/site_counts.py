"""Single source of truth for every public count shown on freellm.top.

Every page (home, /about/, /logs/, /models/, /models/all/, /skills/) must take
its headline numbers from :func:`compute_site_counts` (directly, or through
``data/scan-summary.json`` which embeds the same values).  Do not recount
offers or models inline in a renderer: that is how the site ended up showing
71 / 72 / 74 / 75 resources and 236 / 258 models at the same time.

Count definitions (also published as ``countDefinitions`` in
``data/scan-summary.json``):

* ``offers``         – active offers: only ``verified`` records whose
                       ``expires_at`` (if present) is not before the reference date.
                       This is the homepage "全部" chip, hero total and /about/ active count.
* ``offersTotal``    – every record in ``data/offers.json``.
* ``offersExpired``  – records explicitly expired or past their published end date.
* ``offersNeedsReview`` – records held for manual review; never count as active.
* ``offersInactive`` – ``offersTotal - offers``, including ended and review-held records.
* ``models``         – every record in the published model catalog
                       (``data/models.json``), i.e. exactly what
                       /models/all/ lists.
* ``scannedModels`` / ``scannedOffers`` – how many records the latest
                       automated scan observed.  A scan-coverage figure only;
                       never presented as a catalog total.

The reference date is the latest daily-log date (deterministic from repo data)
so rebuilding on a different calendar day does not silently change counts.
"""
from __future__ import annotations

import re
from datetime import date

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

COUNT_DEFINITIONS = {
    "offers": "当前有效资源：data/offers.json 中 status 为 verified 且 expires_at 未早于参考日期的记录（首页“全部”与 /about/ 同一口径）",
    "offersTotal": "存档资源总数：data/offers.json 全部记录",
    "offersExpired": "已结束资源：status 为 expired 或公开结束日期早于参考日期的记录",
    "offersNeedsReview": "待核验资源：status 为 needs_review 的记录，不计入当前有效资源",
    "offersInactive": "非当前可用资源：存档总数减去当前有效资源（含已结束和待核验）",
    "models": "模型目录记录：data/models.json 全部记录（与 /models/all/ 列表一致）",
    "scannedModels": "最近一次自动扫描观测到的模型记录数，仅表示扫描覆盖，不是目录总数",
    "scannedOffers": "最近一次自动扫描观测到的资源记录数，仅表示扫描覆盖，不是目录总数",
}


def is_active_offer(offer: dict, reference_date: str) -> bool:
    """Only verified, not-yet-expired offers count as current."""
    if offer.get("status") != "verified":
        return False
    expires = str(offer.get("expires_at") or "")
    return not (_ISO_DATE.fullmatch(expires) and expires < reference_date)


def is_expired_offer(offer: dict, reference_date: str) -> bool:
    """A record is ended when its lifecycle status or published end date says so."""
    if offer.get("status") == "expired":
        return True
    expires = str(offer.get("expires_at") or "")
    return bool(_ISO_DATE.fullmatch(expires) and expires < reference_date)


def reference_date_for(latest_log_date: str | None) -> str:
    value = str(latest_log_date or "")
    return value if _ISO_DATE.fullmatch(value) else date.today().isoformat()


def compute_site_counts(offers: list[dict], models: list[dict], reference_date: str) -> dict[str, int]:
    offers = [offer for offer in offers or [] if isinstance(offer, dict)]
    active = sum(1 for offer in offers if is_active_offer(offer, reference_date))
    expired = sum(1 for offer in offers if is_expired_offer(offer, reference_date))
    needs_review = sum(1 for offer in offers if offer.get("status") == "needs_review")
    return {
        "offers": active,
        "offersTotal": len(offers),
        "offersExpired": expired,
        "offersNeedsReview": needs_review,
        "offersInactive": len(offers) - active,
        "models": len([model for model in models or [] if isinstance(model, dict)]),
    }
