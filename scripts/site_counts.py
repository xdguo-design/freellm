"""Single source of truth for every public count shown on freellm.top.

Every page (home, /about/, /logs/, /models/, /models/all/, /skills/) must take
its headline numbers from :func:`compute_site_counts` (directly, or through
``data/scan-summary.json`` which embeds the same values).  Do not recount
offers or models inline in a renderer: that is how the site ended up showing
71 / 72 / 74 / 75 resources and 236 / 258 models at the same time.

Count definitions (also published as ``countDefinitions`` in
``data/scan-summary.json``):

* ``offers``         – active offers: records in ``data/offers.json`` whose
                       status is not ``expired`` and whose ``expires_at`` (if
                       any) is not before the reference date.  This is the
                       homepage "全部" chip, hero total, /about/ "已收录资源".
* ``offersTotal``    – every record in ``data/offers.json`` (active + ended).
* ``offersExpired``  – ``offersTotal - offers``.
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
    "offers": "当前有效资源：data/offers.json 中 status 不是 expired 且 expires_at 未早于参考日期的记录（首页“全部”、/about/“已收录资源”同一口径）",
    "offersTotal": "存档资源总数：data/offers.json 全部记录（含已结束）",
    "offersExpired": "已结束资源：存档总数减去当前有效资源",
    "models": "模型目录记录：data/models.json 全部记录（与 /models/all/ 列表一致）",
    "scannedModels": "最近一次自动扫描观测到的模型记录数，仅表示扫描覆盖，不是目录总数",
    "scannedOffers": "最近一次自动扫描观测到的资源记录数，仅表示扫描覆盖，不是目录总数",
}


def is_active_offer(offer: dict, reference_date: str) -> bool:
    """One lifecycle predicate shared by SSR counters, cards and JS mirror."""
    if offer.get("status") == "expired":
        return False
    expires = str(offer.get("expires_at") or "")
    return not (_ISO_DATE.fullmatch(expires) and expires < reference_date)


def reference_date_for(latest_log_date: str | None) -> str:
    value = str(latest_log_date or "")
    return value if _ISO_DATE.fullmatch(value) else date.today().isoformat()


def compute_site_counts(offers: list[dict], models: list[dict], reference_date: str) -> dict[str, int]:
    offers = [offer for offer in offers or [] if isinstance(offer, dict)]
    active = sum(1 for offer in offers if is_active_offer(offer, reference_date))
    return {
        "offers": active,
        "offersTotal": len(offers),
        "offersExpired": len(offers) - active,
        "models": len([model for model in models or [] if isinstance(model, dict)]),
    }
