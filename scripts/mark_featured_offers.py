"""给「接口速度好 + 免费额度高」的 offer 打上 `featured`（加精）标签。

判定只用两条已经实测/已核验过的证据，不引入任何人工印象：

1. 速度 —— `endpointCheck.ms`，即 scripts/probe_offer_endpoints.py 从本机大陆网络
   直连、预热 1 次后取 3 次请求往返延迟的中位数。没有实测值的 offer 一律不参与
   评选（而不是用官网延迟或感觉代替）。
2. 额度 —— `freeMechanism` 加上 `quota` / `freeSummary` 里能读到的数量级。

档位定义（改这里就等于改标准，改动会被 tests/test_featured_offers.py 盯住）：

    速度   very_fast  ms <= 200
           fast       ms <= 400
           其它       不参评

    额度   very_high  长期免费 且（价目表标价 ¥0，或有达到门槛的大额数量）
           high       长期免费且有可读的数量，或有大额数量
           其它       不参评

入选条件：速度达标 **且** 额度达标。`first_month_promo`（首月优惠价，本质要付钱）、
`not_confirmed`、`open_weights` 三类直接不参评。

`since` 只在首次入选时写入，重复运行不会把日期改新——标签的生效日期是历史事实，
不能因为重跑脚本就漂移。

保持 data/offers.json 的手工格式不变：indent=1、ensure_ascii=False、LF、结尾一个换行。
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# --- 速度门槛（本机大陆直连实测的 API 网关往返中位数） ---
SPEED_VERY_FAST_MS = 200
SPEED_FAST_MS = 400

# --- 额度门槛 ---
QUOTA_HIGH_TOKENS = 1_000_000
QUOTA_HIGH_REQUESTS = 100_000
QUOTA_HIGH_CREDITS = 50_000

# 长期免费：额度会持续刷新，而不是一次性试用或限时活动。
LONG_TERM_MECHANISMS = {"permanent"}
# 直接不参评：首月优惠价要付钱，另两类根本没有免费额度可谈。
EXCLUDED_MECHANISMS = {"first_month_promo", "not_confirmed", "open_weights"}

TIER_THRESHOLDS = {
    "tokens": QUOTA_HIGH_TOKENS,
    "requests": QUOTA_HIGH_REQUESTS,
    "credits": QUOTA_HIGH_CREDITS,
}
UNIT_LABELS_ZH = {"tokens": "tokens", "requests": "次请求", "credits": "积分"}
UNIT_LABELS_EN = {"tokens": "tokens", "requests": "requests", "credits": "credits"}

# 官方把单价写成 0，等于「用多少都免费」，比任何具体数字都强。
FREE_UNIT_PRICE_RE = re.compile(r"(?:¥|￥|\$)\s*0(?![\d.])")
FREE_UNIT_PRICE_WORDS_RE = re.compile(
    r"(?:输入|输出|缓存命中|单价|标价|input|output|cache|price)[^。；;]{0,48}?(?:free|免费|¥0|\$0|0\.00)",
    re.IGNORECASE,
)
# 官方正文自己说 free/免费：对「长期免费但只限速、不设总量」的条目是有效证据。
FREE_WORD_RE = re.compile(r"(?:\bfree\b|免费|¥\s*0(?![\d.])|\$\s*0(?![\d.]))", re.IGNORECASE)

_NUMBER_RE = re.compile(r"(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>万|亿)?")
_UNIT_ALIASES = (
    (("token", "tokens", "令牌"), "tokens"),
    (("request", "requests", "req", "call", "calls", "query", "queries", "次", "查询"), "requests"),
    (("credit", "credits", "point", "points", "积分"), "credits"),
)
# 数字和单位必须出现在同一段文本里，避免把「$4 / 1,000 requests」的 1,000 当成免费额度。
_UNIT_LOOKAHEAD = 40


def speed_tier(offer: dict) -> tuple[str, int | None]:
    """从实测接口延迟读速度档；没有实测值就是 unknown，绝不猜。"""
    check = offer.get("endpointCheck")
    if not isinstance(check, dict):
        return "unknown", None
    ms = check.get("ms")
    if isinstance(ms, bool) or not isinstance(ms, int) or ms < 0:
        return "unknown", None
    if ms <= SPEED_VERY_FAST_MS:
        return "very_fast", ms
    if ms <= SPEED_FAST_MS:
        return "fast", ms
    return "unknown", ms


def _parse_amount(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def quota_amounts(offer: dict) -> list[tuple[str, float]]:
    """读出 `quota` / `freeSummary` 里所有「数字 + 单位」的额度读数，按数值降序。"""
    found: dict[str, float] = {}
    for field in ("quota", "freeSummary"):
        text = offer.get(field)
        if not isinstance(text, str):
            continue
        for match in _NUMBER_RE.finditer(text):
            amount = _parse_amount(match.group("num"))
            if amount is None:
                continue
            # "2/次"、"500/hour" 里的数字是分母，不是额度，跳过。
            if text[match.end(): match.end() + 1].strip() == "/":
                continue
            scale = match.group("scale")
            if scale == "万":
                amount *= 10_000
            elif scale == "亿":
                amount *= 100_000_000
            window = text[match.end(): match.end() + _UNIT_LOOKAHEAD].lower()
            unit = next(
                (canonical for aliases, canonical in _UNIT_ALIASES if any(alias in window for alias in aliases)),
                None,
            )
            if unit is None:
                continue
            if unit not in found or amount > found[unit]:
                found[unit] = amount
    return sorted(found.items(), key=lambda item: -item[1])


def large_amounts(offer: dict) -> list[tuple[str, float]]:
    """达到门槛的额度读数。"""
    return [item for item in quota_amounts(offer) if item[1] >= TIER_THRESHOLDS[item[0]]]


def _texts(offer: dict) -> list[str]:
    return [text for field in ("quota", "freeSummary") if isinstance(text := offer.get(field), str)]


def has_free_unit_price(offer: dict) -> bool:
    """官方是否把单价标成 0（长期免费的最强证据）。"""
    return any(FREE_UNIT_PRICE_RE.search(text) or FREE_UNIT_PRICE_WORDS_RE.search(text) for text in _texts(offer))


def mentions_free(offer: dict) -> bool:
    """官方正文自己写着 free/免费——对「长期免费、只限速不设总量」的条目是有效证据。"""
    return any(FREE_WORD_RE.search(text) for text in _texts(offer))


def quota_tier(offer: dict) -> str:
    """额度档位：very_high / high / none。"""
    mechanism = str(offer.get("freeMechanism") or "")
    if mechanism in EXCLUDED_MECHANISMS:
        return "none"
    long_term = mechanism in LONG_TERM_MECHANISMS
    if long_term and has_free_unit_price(offer):
        return "very_high"
    if long_term and large_amounts(offer):
        return "very_high"
    if long_term and (quota_amounts(offer) or mentions_free(offer)):
        return "high"
    if large_amounts(offer):
        return "high"
    return "none"


def featured_reason(offer: dict, ms: int, quota: str) -> tuple[str, str]:
    """把两条证据拼成一句可核对的中英文理由。

    理由会跟着每一条 offer 一起进入首页内嵌 JSON，所以刻意写短：测量口径统一放在
    页面上的图例里说明一次，不在这里重复八遍。
    """
    head_zh = f"实测 {ms}ms"
    head_en = f"{ms} ms measured"
    amounts = large_amounts(offer)
    if quota == "very_high" and has_free_unit_price(offer) and not amounts:
        tail_zh, tail_en = "长期免费，价目表 ¥0", "permanently free, ¥0 list price"
    elif quota == "very_high":
        unit, amount = amounts[0]
        tail_zh = f"长期免费，额度 {amount:,.0f} {UNIT_LABELS_ZH[unit]}"
        tail_en = f"permanently free, {amount:,.0f} {UNIT_LABELS_EN[unit]}"
    elif quota == "high" and str(offer.get("freeMechanism")) in LONG_TERM_MECHANISMS:
        tail_zh, tail_en = "官方长期免费", "permanently free"
    else:
        unit, amount = amounts[0]
        tail_zh = f"免费额度 {amount:,.0f} {UNIT_LABELS_ZH[unit]}"
        tail_en = f"free quota {amount:,.0f} {UNIT_LABELS_EN[unit]}"
    return f"{head_zh} · {tail_zh}", f"{head_en} · {tail_en}"


def compute_featured(offer: dict, today: str) -> dict | None:
    speed, ms = speed_tier(offer)
    if speed == "unknown" or ms is None:
        return None
    quota = quota_tier(offer)
    if quota == "none":
        return None
    reason_zh, reason_en = featured_reason(offer, ms, quota)
    existing = offer.get("featured")
    since = existing.get("since") if isinstance(existing, dict) else None
    if not isinstance(since, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since):
        since = today
    return {
        "since": since,
        "speedMs": ms,
        "speedTier": speed,
        "quotaTier": quota,
        "reason": reason_zh,
        "reasonEn": reason_en,
    }


def apply(offers: list[dict], today: str) -> tuple[list[dict], list[str], list[str]]:
    granted: list[str] = []
    revoked: list[str] = []
    for offer in offers:
        featured = compute_featured(offer, today)
        had = isinstance(offer.get("featured"), dict)
        if featured is None:
            if had:
                del offer["featured"]
                revoked.append(str(offer.get("id")))
            continue
        if had and offer["featured"] == featured:
            continue
        offer["featured"] = featured
        granted.append(
            "{id}  {ms}ms/{speed}  {quota}  {reason}".format(
                id=str(offer.get("id")),
                ms=featured["speedMs"],
                speed=featured["speedTier"],
                quota=featured["quotaTier"],
                reason=featured["reason"].split(" · ", 1)[-1],
            )
        )
    return offers, granted, revoked


def render(offers: list[dict]) -> str:
    return json.dumps(offers, indent=1, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--date", default=None, help="首次入选时写入的 since（YYYY-MM-DD）")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        print("--date must use YYYY-MM-DD", file=sys.stderr)
        return 2

    data_path = Path(args.data)
    raw = data_path.read_bytes()
    offers = json.loads(raw.decode("utf-8"))
    today = args.date or datetime.date.today().isoformat()

    offers, granted, revoked = apply(offers, today)
    rendered = render(offers)

    if args.check:
        if rendered.encode("utf-8") != raw:
            print(f"stale: {data_path} does not match the featured-offer rule")
            return 1
        print(f"current: {data_path}")
        return 0

    with data_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)

    total = sum(1 for offer in offers if isinstance(offer.get("featured"), dict))
    for line in granted:
        print(f"  ★  {line}")
    for line in revoked:
        print(f"  --  revoked {line}")
    print(f"wrote {data_path}: {total} featured offers ({len(granted)} changed, {len(revoked)} revoked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
