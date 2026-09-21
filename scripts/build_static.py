"""Embed the JSON source into the static HTML fallback block."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.schema import validate_offers

START = '<script type="application/json" id="offer-data">'
END = "</script>"
LD_START = '<script type="application/ld+json" id="ld-dynamic">'
STATIC_OFFER_START = '<!-- STATIC-OFFERS:START -->'
STATIC_OFFER_END = '<!-- STATIC-OFFERS:END -->'
SITE_URL = "https://freellm.top"


SITE_CHROME = '''<aside class="fl-site-rail" aria-label="FreeLLM 主导航">
  <a class="fl-site-brand" href="/">
    <span class="fl-site-brand-mark" aria-hidden="true">AI</span>
    <span class="fl-site-brand-copy"><strong>FreeLLM</strong><small>让 AI 更自由地被使用</small></span>
  </a>
  <nav class="fl-site-nav">
    <a href="/" data-site-nav="home" aria-current="page"><span class="fl-site-nav-icon" aria-hidden="true">⌂</span><span>首页</span></a>
    <a href="/models/" data-site-nav="models"><span class="fl-site-nav-icon" aria-hidden="true">▣</span><span>模型</span></a>
    <a href="/skills/" data-site-nav="skills"><span class="fl-site-nav-icon" aria-hidden="true">✦</span><span>Skills</span></a>
    <a href="/tools/" data-site-nav="tools"><span class="fl-site-nav-icon" aria-hidden="true">⌘</span><span>工具</span></a>
    <a href="/skills/lab/" data-site-nav="workflow"><span class="fl-site-nav-icon" aria-hidden="true">⌁</span><span>工作流</span></a>
    <a href="/logs/" data-site-nav="logs"><span class="fl-site-nav-icon" aria-hidden="true">◷</span><span>更新</span></a>
    <a href="/about/" data-site-nav="about"><span class="fl-site-nav-icon" aria-hidden="true">ⓘ</span><span>关于</span></a>
  </nav>
  <div class="fl-site-rail-note"><span>好的 AI 资源</span><br>让更多人真正受益 ♡</div>
</aside>
<div class="fl-site-ribbon">
  <span class="fl-site-ribbon-title">FREE AI INDEX / 免费 AI 资源导航</span>
  <span class="fl-site-ribbon-actions"><a href="/favorites/">我的收藏</a><a href="/skills/">Skills 实测 ↗</a></span>
</div>'''


def remove_legacy_global_nav(html: str) -> str:
    """The universal rail owns site navigation; page headers keep only local actions."""
    return re.sub(r'<nav class="top-nav"[^>]*>.*?</nav>', "", html, flags=re.I | re.S)


def ensure_pastel_shell(html: str) -> str:
    """Render the visual shell in HTML itself instead of depending on JS to add it."""
    updated = html
    updated = re.sub(
        r'<html(?![^>]*\bclass=)([^>]*)>',
        r'<html class="fl-pastel-ui"\1>',
        updated,
        count=1,
        flags=re.I,
    )
    updated = re.sub(
        r'<html([^>]*\bclass=")([^"]*)(")',
        lambda m: f'<html{m.group(1)}{m.group(2)}{" " if m.group(2) else ""}fl-pastel-ui{m.group(3)}'
        if "fl-pastel-ui" not in m.group(2).split()
        else m.group(0),
        updated,
        count=1,
        flags=re.I,
    )
    body_match = re.search(r'<body([^>]*)>', updated, flags=re.I)
    if body_match:
        attrs = body_match.group(1)
        if 'class="' in attrs:
            attrs = re.sub(
                r'class="([^"]*)"',
                lambda m: f'class="{m.group(1)}{" " if m.group(1) else ""}fl-ui-v2"' if "fl-ui-v2" not in m.group(1).split() else m.group(0),
                attrs,
                count=1,
            )
        else:
            attrs += ' class="fl-ui-v2"'
        if 'data-fl-section=' not in attrs:
            attrs += ' data-fl-section="home"'
        replacement = f'<body{attrs}>'
        updated = updated[:body_match.start()] + replacement + updated[body_match.end():]

    theme_tag = '<link rel="stylesheet" href="../css/freellm-pastel-ui.css?v=20260920c">'
    updated = re.sub(
        r'<link rel="stylesheet" href="(?:\.\./|/)?css/freellm-pastel-ui\.css(?:\?[^"]*)?">',
        theme_tag,
        updated,
        count=1,
    )
    if "freellm-pastel-ui.css" not in updated and "</head>" in updated:
        updated = updated.replace("</head>", theme_tag + "</head>", 1)

    # Always normalize the shell. Older generated HTML may already contain
    # a ten-item rail, so "only inject if missing" would preserve stale navigation.
    shell_pattern = r'<aside class="fl-site-rail"[^>]*>.*?</aside>\s*<div class="fl-site-ribbon"[^>]*>.*?</div>'
    if re.search(shell_pattern, updated, flags=re.I | re.S):
        updated = re.sub(shell_pattern, SITE_CHROME, updated, count=1, flags=re.I | re.S)
    else:
        updated = re.sub(
            r'(<body[^>]*>)',
            lambda m: m.group(1) + "\n" + SITE_CHROME,
            updated,
            count=1,
            flags=re.I,
        )
    return updated



def offer_href(offer: dict) -> str:
    offer_id = str(offer.get("id") or "").strip()
    if not offer_id:
        raise ValueError("Offer is missing id")
    return f"/offers/{quote(offer_id, safe='')}/"


def key_first(offers: list[dict]) -> list[dict]:
    """重点资源排在可用列表最前面，其余保持原有 order。"""
    return sorted(offers, key=lambda offer: (not offer.get("key"), int(offer.get("order") or 0)))


NETWORK_REGION_LABELS = {
    "both": "国内外均可用",
    "cn": "仅国内可用",
    "intl": "仅国外可用",
}
NETWORK_METHOD = "本机大陆网络直连 + check-host.net 海外节点（US×2 / DE / SG / JP / UK）"
NETWORK_NOTE = "仅实测网络可达性与往返延迟，不代表注册门槛或模型生成速度"


def render_network_chips(offer: dict) -> list[str]:
    """绿色实测标签：网络可达性 + 国内/国外分类 + 往返延迟。

    数据来自 scripts/probe_offer_network.py 的双视角实测（大陆直连 +
    check-host.net 海外节点），只描述网络层，不描述注册门槛或模型生成速度。
    """
    check = offer.get("networkCheck")
    if not isinstance(check, dict):
        return []
    region = check.get("region")
    if region not in NETWORK_REGION_LABELS and region != "none":
        return []

    latencies = []
    if check.get("cnMs"):
        latencies.append(f"国内 {check['cnMs']}ms")
    if check.get("intlMs"):
        latencies.append(f"海外 {check['intlMs']}ms")
    speed = " · ".join(latencies)
    title = f"实测于 {check.get('checkedAt')}｜{NETWORK_METHOD}"
    if check.get("cnHost"):
        title += f"｜国内经 {check['cnHost']}"
    if speed:
        title += f"｜{speed}"
    title += f"｜{NETWORK_NOTE}"
    title = html_lib.escape(title)

    if region == "none":
        chips = [f'<span class="flag-chip flag-net-fail" title="{title}">✗ 本次未连通</span>']
    else:
        chips = [
            f'<span class="flag-chip flag-net-ok" title="{title}">✓ 实测通过</span>',
            f'<span class="flag-chip flag-net-region">{NETWORK_REGION_LABELS[region]}</span>',
        ]
        if speed:
            chips.append(f'<span class="flag-chip flag-net-speed">{html_lib.escape(speed)}</span>')

    dead = [str(url) for url in (check.get("deadTargets") or [])]
    if dead:
        dead_title = html_lib.escape("域名无法解析：" + "；".join(dead))
        chips.append(f'<span class="flag-chip flag-net-dead" title="{dead_title}">⚠ {len(dead)} 个链接解析失败</span>')
    return chips


def render_offer_flags(offer: dict) -> str:
    chips = []
    featured = offer.get("featured")
    if isinstance(featured, dict) and featured.get("reason"):
        title = html_lib.escape(f"加精｜{featured['reason']}")
        chips.append(f'<span class="flag-chip flag-featured" title="{title}">◆ 加精</span>')
    if offer.get("key"):
        chips.append('<span class="flag-chip flag-key">★ 重点</span>')
    chips.extend(render_network_chips(offer))
    edition_of = offer.get("editionOf")
    editions = offer.get("editions") or []
    if edition_of == "cn":
        chips.append('<span class="flag-chip flag-edition">国内版</span>')
    elif edition_of == "intl":
        chips.append('<span class="flag-chip flag-edition">国际版</span>')
    elif "cn" in editions and "intl" in editions:
        chips.append('<span class="flag-chip flag-edition">国内+国际双入口</span>')
    elif "cn" in editions:
        chips.append('<span class="flag-chip flag-edition">国内版</span>')
    elif "intl" in editions:
        chips.append('<span class="flag-chip flag-edition">国际版</span>')
    sibling = offer.get("siblingEditionId")
    if sibling:
        label = "也有国内版" if edition_of == "intl" else "也有国际版"
        chips.append(f'<a class="flag-chip flag-sibling" href="/offers/{quote(str(sibling), safe="")}/">{label} ↗</a>')
    if offer.get("handsOn"):
        chips.append('<span class="flag-chip flag-hands-on">✓ 实测好用</span>')
    elif offer.get("endpointCheck") and offer["endpointCheck"].get("verdict") != "NETWORK_ERROR":
        check = offer["endpointCheck"]
        label = "接口已验证" if offer.get("usageGuide", {}).get("endpoint") else "官网已验证"
        ms = check.get("ms")
        suffix = f" · {int(ms)}ms" if isinstance(ms, int) else ""
        chips.append(f'<span class="flag-chip flag-endpoint">✓ {label}{suffix}</span>')
    if not chips:
        return ""
    return '<div class="offer-card-flags">' + "".join(chips) + "</div>"


def render_static_catalog(data: list[dict], limit: int = 20) -> str:
    cards = []
    for offer in key_first(data)[:limit]:
        href = offer_href(offer)
        title = html_lib.escape(str(offer.get("title") or offer.get("name") or "AI offer"))
        provider = html_lib.escape(str(offer.get("provider") or "Official provider"))
        summary = html_lib.escape(str(offer.get("freeSummary") or offer.get("mechanism") or "See official terms"))
        validity = html_lib.escape(str(offer.get("validitySummary") or offer.get("validity") or "See official terms"))
        access = html_lib.escape(str(offer.get("accessSummary") or offer.get("access") or "See official terms"))
        checked = html_lib.escape(str(offer.get("lastVerifiedAt") or "Unknown"))
        cards.append(
            f'<article class="offer static-offer" data-detail="{html_lib.escape(str(offer["id"]))}">'
            f'<div class="offer-card-top"><div class="provider-name"><strong>{title}</strong>'
            f'<small>{provider}</small></div><a class="row-arrow" href="{href}" aria-label="查看 {title} 详情">→</a></div>'
            f'{render_offer_flags(offer)}'
            f'<div class="offer-card-body"><div class="offer-card-metrics">'
            f'<div class="offer-card-metric"><label>免费方式</label><p>{summary}</p></div>'
            f'<div class="offer-card-metric"><label>有效期</label><p>{validity}</p></div>'
            f'<div class="offer-card-metric"><label>地区</label><p>{access}</p></div>'
            f'</div></div><div class="offer-card-footer"><small>核验于 {checked}</small>'
            f'<a class="offer-detail-link" href="{href}">查看详情 ↗</a></div></article>'
        )
    return STATIC_OFFER_START + "".join(cards) + STATIC_OFFER_END


def replace_static_catalog(html: str, data: list[dict]) -> str:
    count = len(data)
    updated = re.sub(r'(<b id="heroCount">)[^<]*(</b>)', rf"\g<1>{count}\g<2>", html, count=1)
    updated = re.sub(
        r'(<b data-category-count="all">)[^<]*(</b>)',
        rf"\g<1>{count}\g<2>",
        updated,
        count=1,
    )
    updated = re.sub(
        r'(<button class="filter-chip active" data-filter="all"[^>]*>[^<]*<em>)[^<]*(</em>)',
        rf"\g<1>{count}\g<2>",
        updated,
        count=1,
    )
    updated = re.sub(
        r'(<p id="catalog-result-count">Showing )\d+( offers</p>)',
        rf"\g<1>{count}\g<2>",
        updated,
        count=1,
    )
    static_catalog = render_static_catalog(data)
    marker_pattern = rf"({re.escape(STATIC_OFFER_START)}).*?({re.escape(STATIC_OFFER_END)})"
    if re.search(marker_pattern, updated, flags=re.S):
        updated = re.sub(marker_pattern, static_catalog, updated, count=1, flags=re.S)
    else:
        updated = re.sub(
            r'(<div id="catalog-offer-rows"[^>]*>)\s*</div>',
            rf"\g<1>{static_catalog}</div>",
            updated,
            count=1,
        )
    return updated


def update_trust_copy(html: str) -> str:
    return (
        html
        .replace("每日核验 · 真实免费", "官方来源 · 条件透明")
        .replace("通过人工核验，确认可免费使用", "显示官方条件与最近核验日期")
    )


def remove_legacy_app(html: str) -> str:
    return re.sub(
        r'\s*<div class="app legacy-app">.*?(?=\s*<script type="application/json" id="offer-data">)',
        "\n",
        html,
        count=1,
        flags=re.S,
    )


def update_daily_log_summary(html: str, data_path: Path) -> str:
    log_dir = data_path.parent / "daily-log"
    log_paths = sorted(log_dir.glob("*.json")) if log_dir.is_dir() else []
    if not log_paths:
        return html
    try:
        latest = json.loads(log_paths[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return html
    date = latest.get("date") if isinstance(latest, dict) else None
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return html
    events = [
        event
        for key in ("events", "curatedEvents")
        for event in (latest.get(key) or [])
        if isinstance(event, dict)
    ]
    new_count = sum(1 for event in events if event.get("eventType") in {"new", "new_route"})
    change_count = sum(1 for event in events if event.get("eventType") in {"new", "new_route", "recovered", "offline", "source_unavailable"})
    badge = f"新增 {new_count} 项" if new_count else ("今日有变化" if change_count else "今日无新增")
    year, month, day = date.split("-")
    label = f"{year} 年 {int(month)} 月 {int(day)} 日"
    replacement = f'▣ &nbsp;{label}</span><a class="intel-log-link" href="/logs/">查看今日变化 →</a>'
    updated = re.sub(r"▣\s*&nbsp;[^<]+</span>(?:<a class=\"intel-log-link\"[^>]*>查看(?:今日更新|今日变化) →</a>)?", replacement, html, count=1)
    badge_markup = f'<span class="intel-update-badge" id="daily-log-badge" data-new-count="{new_count}" data-change-count="{change_count}">{badge}</span>'
    return re.sub(r'<span[^>]*id="daily-log-badge"[^>]*>.*?</span>', badge_markup, updated, count=1, flags=re.S)


def update_static_item_list(html: str, data: list[dict]) -> str:
    start = html.find(LD_START)
    if start < 0:
        return html
    content_start = start + len(LD_START)
    end = html.find(END, content_start)
    if end < 0:
        raise SystemExit("Missing JSON-LD script closing tag in static HTML")
    try:
        structured = json.loads(html[content_start:end])
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid static JSON-LD: {error}") from error
    structured["@graph"][0]["itemListElement"] = [
        {
            "@type": "ListItem",
            "position": index,
            "name": offer["title"],
            "url": f"{SITE_URL}{offer_href(offer)}",
        }
        for index, offer in enumerate(data, start=1)
    ]
    replacement = "\n  " + json.dumps(structured, ensure_ascii=False, indent=2) + "\n  "
    return html[:content_start] + replacement + html[end:]


def build(data_path: Path, html_path: Path, check: bool = False) -> bool:
    errors = validate_offers(data_path)
    if errors:
        raise SystemExit("Invalid offers data:\n" + "\n".join(errors))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")
    start = html.find(START)
    if start < 0:
        raise SystemExit(f"Missing {START} in {html_path}")
    content_start = start + len(START)
    end = html.find(END, content_start)
    if end < 0:
        raise SystemExit(f"Missing JSON script closing tag in {html_path}")
    replacement = "\n  " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n  "
    updated = html[:content_start] + replacement + html[end:]
    updated = update_trust_copy(updated)
    updated = remove_legacy_app(updated)
    updated = replace_static_catalog(updated, data)
    updated = update_static_item_list(updated, data)
    updated = update_daily_log_summary(updated, data_path)
    updated = ensure_pastel_shell(remove_legacy_global_nav(updated))
    if check:
        if updated != html:
            print(f"stale: {html_path} does not contain the current offers JSON")
            return False
        print(f"current: {html_path}")
        return True
    html_path.write_text(updated, encoding="utf-8")
    print(f"built: {html_path} from {data_path} ({len(data)} offers)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--html", default="design/free-china-ai-index.html")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return 0 if build(Path(args.data), Path(args.html), args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
