"""Shared rules for the public 「每日发现」 (Daily discoveries) view.

One rule set feeds /logs/, the homepage summary and data/scan-summary.json:

* a discovery is a ``new`` / ``new_route`` event from ``events`` or
  ``curatedEvents``; the same id inside one log counts once;
* an id is a discovery only on the FIRST log date it appears on -- a later
  scanner re-detection of the same id is not a new discovery;
* the week view covers the 7 calendar days ending on the latest log date;
  a day without a log file is shown as 「当日未扫描」, never filled in.

Copy helpers turn event fields into editorial Chinese and never surface the
scanner's internal reason strings (e.g. "not present in the previous
successful snapshot").
"""

from __future__ import annotations

import re
from datetime import date, timedelta

DISCOVERY_EVENT_TYPES = frozenset({"new", "new_route"})
WEEK_DAYS = 7
NOT_SCANNED_LABEL = "当日未扫描"
NO_DISCOVERY_LABEL = "当日已记录，没有新发现"
WEEKDAYS_ZH = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

_INTERNAL_REASON_PATTERNS = (
    re.compile(r"previous successful snapshot", re.I),
    re.compile(r"not present in the previous", re.I),
    re.compile(r"\bsnapshot\b", re.I),
)
_CJK = re.compile(r"[\u3400-\u9fff]")
_END_DATE = re.compile(r"(?:至|到|截止(?:到)?|until)\s*(20\d\d)-(\d\d)-(\d\d)", re.I)

KIND_LABELS = {
    "model": "模型",
    "offer": "额度与活动",
    "tool": "开发工具",
    "agent": "AI Agent",
    "skill": "Skill",
    "news": "资讯",
}
STATUS_LABELS = {
    "verified": "已核对官方来源",
    "online": "官方列表可见，未实测",
    "pending_verification": "待核验",
    "needs_review": "待核验",
    "experimental": "实验阶段",
}
FALLBACK_REASON = "自动扫描首次在官方来源看到这一项，详细条款尚未整理。"


def event_identity(event: dict) -> str:
    event_id = str(event.get("id") or "").strip()
    if event_id:
        return event_id
    return "|".join((str(event.get("kind") or "").strip(), str(event.get("title") or "").strip()))


def log_discoveries(log: dict) -> list[dict]:
    """Unique new/new_route events of one log, in file order."""
    seen: set[str] = set()
    items: list[dict] = []
    for field in ("events", "curatedEvents"):
        events = log.get(field)
        if not isinstance(events, list):
            continue
        for event in events:
            if not isinstance(event, dict) or event.get("eventType") not in DISCOVERY_EVENT_TYPES:
                continue
            identity = event_identity(event)
            if identity in seen:
                continue
            seen.add(identity)
            items.append(event)
    return items


def _valid_date(value) -> str:
    text = str(value or "")
    return text if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else ""


def first_seen_discoveries(logs: list[dict]) -> dict[str, list[dict]]:
    """Map log date -> discoveries whose id was never seen on an earlier date."""
    dated = sorted(
        (log for log in logs if isinstance(log, dict) and _valid_date(log.get("date"))),
        key=lambda log: str(log["date"]),
    )
    seen: set[str] = set()
    result: dict[str, list[dict]] = {}
    for log in dated:
        day = str(log["date"])
        fresh = []
        for event in log_discoveries(log):
            identity = event_identity(event)
            if identity in seen:
                continue
            seen.add(identity)
            fresh.append(event)
        result.setdefault(day, []).extend(fresh)
    return result


def latest_log_date(logs: list[dict]) -> str:
    dates = [_valid_date(log.get("date")) for log in logs if isinstance(log, dict)]
    dates = [day for day in dates if day]
    return max(dates) if dates else ""


def discovery_week(logs: list[dict], days: int = WEEK_DAYS) -> list[dict]:
    """The last ``days`` calendar days ending on the latest log date, newest first."""
    end = latest_log_date(logs)
    if not end:
        return []
    logged = {_valid_date(log.get("date")) for log in logs if isinstance(log, dict)}
    first_seen = first_seen_discoveries(logs)
    end_day = date.fromisoformat(end)
    week = []
    for offset in range(days):
        day = (end_day - timedelta(days=offset)).isoformat()
        week.append({
            "date": day,
            "logged": day in logged,
            "events": list(first_seen.get(day, [])) if day in logged else [],
        })
    return week


def day_label(day: str) -> str:
    parsed = date.fromisoformat(day)
    return f"{parsed.month} 月 {parsed.day} 日 · {WEEKDAYS_ZH[parsed.weekday()]}"


SCANNER_REASONS = {
    "not present in the previous successful snapshot": "自动扫描首次在官方来源看到这一项，详细条款尚未整理。",
    "missing from the successful snapshot": "扫描成功，但官方来源里已经找不到这一项。",
    "same model observed through a new provider or route": "同一个模型出现了新的接入渠道。",
    "previously absent or offline and observed again": "之前缺失或下线，这次扫描又在官方来源看到了。",
    "status changed to expired": "官方活动已到期。",
    "source scan failed": "这次没能读取来源页面，不代表项目已下线。",
}


def is_internal_reason(text: str) -> bool:
    """True for empty text and the scanner's machine reason strings."""
    text = str(text or "").strip()
    if not text:
        return True
    if text.lower() in SCANNER_REASONS:
        return True
    return any(pattern.search(text) for pattern in _INTERNAL_REASON_PATTERNS)


def human_reason(event: dict) -> str:
    """Editorial reason, or a plain-Chinese rendering of a scanner reason."""
    reason = str(event.get("reason") or "").strip()
    if not is_internal_reason(reason):
        return reason
    return SCANNER_REASONS.get(reason.lower(), FALLBACK_REASON)


def provider_label(event: dict) -> str:
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    return str(details.get("provider") or details.get("providerId") or event.get("provider") or "").strip()


def _short_provider(provider: str) -> str:
    return provider.split(" · ")[0].strip()


def _provider_tokens(provider: str) -> list[str]:
    parts = re.split(r"\s*(?:·|/|／)\s*", provider)
    return [part.strip() for part in parts if len(part.strip()) >= 2]


def display_title(event: dict) -> str:
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    return str(event.get("title") or details.get("model") or details.get("name") or event.get("id") or "未命名记录").strip()


def end_date_clause(event: dict) -> str:
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    for field in ("validitySummary", "freeSummary"):
        text = str(details.get(field) or "")
        match = _END_DATE.search(text)
        if match:
            month_day = f"{match.group(2)}-{match.group(3)}"
            return f"，限时免费到 {month_day}" if "免费" in text else f"，有效期到 {month_day}"
    return ""


def headline(event: dict) -> str:
    """One editorial line such as 「云知声 U2 Flash · 国庆免费月 API，限时免费到 10-31」."""
    title = display_title(event)
    provider = provider_label(event)
    lowered = title.lower()
    # Editorial titles (Chinese copy or "Product · offer") already read as a
    # sentence; bare scanner names such as "mistral-large-4" get the provider.
    editorial = bool(_CJK.search(title)) or " · " in title or "：" in title
    if provider and not editorial and not any(token.lower() in lowered for token in _provider_tokens(provider)):
        short = _short_provider(provider)
        kind = str(event.get("kind") or "").lower()
        if kind == "model":
            title = f"{short} 上新模型 {title}"
        elif kind in {"tool", "agent"}:
            title = f"{short} 推出 {title}"
        else:
            title = f"{short}：{title}"
    clause = end_date_clause(event)
    if clause and clause.split("到 ")[-1] not in title:
        title += clause
    return title


def summary(event: dict) -> str:
    """A plain sentence about what is free, or '' when nothing honest is known."""
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    free = str(details.get("freeSummary") or "").strip()
    if free:
        return free
    reason = str(event.get("reason") or "").strip()
    return "" if is_internal_reason(reason) else reason


def kind_label(event: dict) -> str:
    return KIND_LABELS.get(str(event.get("kind") or "").lower(), "目录记录")


def status_label(event: dict) -> str:
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    status = str(details.get("status") or "").strip().lower()
    return STATUS_LABELS.get(status, "未核实")


def source_url(event: dict) -> str:
    details = event.get("details") if isinstance(event.get("details"), dict) else {}
    url = str(details.get("sourceUrl") or event.get("sourceUrl") or "")
    return url if url.startswith("https://") else ""
