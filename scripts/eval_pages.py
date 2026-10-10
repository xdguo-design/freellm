"""FreeLLM's own evaluation results rendered for secondary pages.

Secondary pages are the provider pages (``providers/*/``), the provider
directory, model aggregate pages (``models/<slug>/``), category pages
(``category/*/``) and offer detail pages. Everything here reads
``data/evaluations/latest.json`` + ``verdicts.json`` through
:mod:`scripts.eval_integration`, so the weekly ``model-eval`` workflow only has
to rebuild the pages to refresh them.

Matching rules (same contract as the /models/ cards in eval_integration):

* same channel (the evaluated provider *is* this page's provider) -> the real
  measured numbers: score, 7 dimension scores, success rate, first-token
  latency p50/p95, tokens/s, strengths/weaknesses, suitable use cases;
* same channel but a low success rate -> the success rate first, the score only
  as "受失败请求影响";
* same channel but the endpoint failed outright -> "本账号/本端点不可用，待复核";
* same model measured on *another* channel -> only "同款模型经 X 实测 N 分",
  never that other channel's speed;
* anything else -> an explicit "未实测". Nothing is invented.
"""
from __future__ import annotations

import html
import json
import re
from functools import lru_cache
from pathlib import Path

from scripts.eval_integration import REPORT_URL, anchor, load_results, model_key

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = ROOT / "data" / "evaluations" / "verdicts.json"
RAW_DATA_URL = "https://github.com/xdguo-design/freellm/blob/main/data/evaluations/latest.json"
RELIABLE_SUCCESS_RATE = 80

# Evaluated provider id (data/evaluations/latest.json) -> site provider page id
# (providers/<id>/). Kept explicit: a provider page only shows "real" numbers
# when the evaluation actually called that platform.
EVAL_TO_SITE_PROVIDER = {
    "groq": "groq",
    "siliconflow": "siliconflow",
    "modelscope": "modelscope",
    "nvidia": "nvidia-nim",
    "zhipu": "zhipu-glm",
    "openrouter": "openrouter",
}
SITE_TO_EVAL_PROVIDER = {site: eval_id for eval_id, site in EVAL_TO_SITE_PROVIDER.items()}

# Offer label aliases per evaluated provider (offers carry free-text provider names).
_OFFER_PROVIDER_ALIASES = {
    "groq": ("groq",),
    "siliconflow": ("siliconflow", "硅基流动"),
    "modelscope": ("modelscope", "魔搭"),
    "nvidia": ("nvidia nim",),
    "zhipu": ("zhipu bigmodel", "智谱"),
    "openrouter": ("openrouter",),
}

DIM_ORDER = ("chinese_knowledge", "reasoning_math", "coding", "instruction_format", "long_context", "tool_calling", "honesty")
DIM_EN = {
    "chinese_knowledge": "Chinese knowledge",
    "reasoning_math": "Reasoning & math",
    "coding": "Coding",
    "instruction_format": "Format following",
    "long_context": "Long context",
    "tool_calling": "Tool calling",
    "honesty": "Anti-hallucination",
}


def _e(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _pair(zh: str, en: str) -> str:
    return f'<span lang="zh-CN">{_e(zh)}</span><span lang="en">{_e(en)}</span>'


def _pair_html(zh_html: str, en_html: str) -> str:
    return f'<span lang="zh-CN">{zh_html}</span><span lang="en">{en_html}</span>'


@lru_cache(maxsize=1)
def load_verdicts() -> dict:
    if not VERDICTS.exists():
        return {}
    try:
        return json.loads(VERDICTS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def clear_cache() -> None:
    load_results.cache_clear()
    load_verdicts.cache_clear()


def _models() -> list[dict]:
    return [m for m in load_results().get("models", []) if isinstance(m, dict) and m.get("model")]


def run_date() -> str:
    raw = str(load_results().get("runAt", ""))
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return match.group(0) if match else raw[:10]


def suite_name() -> str:
    return str(load_results().get("suite") or "")


def case_count() -> int:
    cases = load_results().get("cases")
    return cases if isinstance(cases, int) else len(cases or [])


def _usable(m: dict) -> bool:
    return bool(m.get("available")) and m.get("score") is not None


def _reliable(m: dict) -> bool:
    return _usable(m) and (m.get("successRate") or 0) >= RELIABLE_SUCCESS_RATE


def report_href(m: dict) -> str:
    return f"{REPORT_URL}#{anchor(m)}"


def site_provider_for(m: dict) -> str:
    return EVAL_TO_SITE_PROVIDER.get(str(m.get("providerId") or ""), "")


def provider_results(site_provider_id: str) -> list[dict]:
    eval_id = SITE_TO_EVAL_PROVIDER.get(str(site_provider_id or ""))
    if not eval_id:
        return []
    return [m for m in _models() if m.get("providerId") == eval_id]


def _status_of(m: dict) -> str:
    if not _usable(m):
        return "unavailable"
    if (m.get("successRate") or 0) < RELIABLE_SUCCESS_RATE:
        return "low_success"
    return "measured"


def lookup(site_provider_id: str, model_name: str) -> tuple[str, dict | None]:
    """Classify one (provider page, model) pair.

    Returns (kind, result) with kind in measured | low_success | unavailable |
    reference | untested. ``reference`` results belong to another channel.
    """
    key = model_key(model_name)
    if not key:
        return "untested", None
    same_model = [m for m in _models() if model_key(m["model"]) == key]
    eval_id = SITE_TO_EVAL_PROVIDER.get(str(site_provider_id or ""))
    if eval_id:
        exact = [m for m in same_model if m.get("providerId") == eval_id]
        if exact:
            best = max(exact, key=lambda m: (_usable(m), m.get("successRate") or 0, m.get("score") or 0))
            return _status_of(best), best
    refs = [m for m in same_model if m.get("providerId") != eval_id and _reliable(m)]
    if refs:
        return "reference", max(refs, key=lambda m: m["score"])
    return "untested", None


def unavailable_reason(m: dict) -> tuple[str, str]:
    """Short zh/en reason for a failed endpoint. Never echoes raw error bodies (they can carry account ids)."""
    errors = [str(x) for x in (m.get("errors") or [])]
    detail = str(m.get("errorDetail") or "").lower()
    code = next((x.replace("HTTP ", "") for x in errors if x.startswith("HTTP ")), "")
    if code == "404":
        zh, en = "返回 404", "HTTP 404"
    elif code == "429":
        zh, en = ("免费额度用尽（429）", "quota exhausted (429)") if "quota" in detail else ("被限流（429）", "rate-limited (429)")
    elif code == "403":
        zh, en = ("返回 403，仅限指定 Agent 应用", "HTTP 403, agent apps only") if "agentic" in detail else ("返回 403", "HTTP 403")
    elif code == "400" and "no provider" in detail:
        zh, en = "返回「没有可用服务商」", "no serving provider"
    elif code:
        zh, en = f"返回 {code}", f"HTTP {code}"
    elif errors:
        zh, en = errors[0], errors[0]
    else:
        zh, en = "无响应", "no response"
    return zh, en


def _short(model: str) -> str:
    return str(model).split("/")[-1]


def _fmt_ms(value) -> str:
    return f"{float(value):.0f} ms" if isinstance(value, (int, float)) else "—"


def _fmt_tps(value) -> str:
    return f"{float(value):.0f} token/s" if isinstance(value, (int, float)) else "—"


def auto_tags(m: dict) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Strengths / weaknesses derived from measured numbers only (mirrors build_eval_report.auto_tags)."""
    dims = m.get("dimensions") or {}
    good: list[tuple[str, str]] = []
    bad: list[tuple[str, str]] = []
    ttft, tps = m.get("p50TtftMs"), m.get("medianTokensPerSec")
    if isinstance(ttft, (int, float)) and ttft < 350:
        good.append(("首字极快", "Very fast first token"))
    if isinstance(tps, (int, float)) and tps >= 300:
        good.append(("高吞吐", "High throughput"))
    if m.get("thinksByDefault"):
        bad.append(("默认长思考，响应慢", "Thinks by default, slower"))
    labels = load_results().get("dimensions") or {}
    for dim in DIM_ORDER:
        value = dims.get(dim)
        if value is None:
            continue
        zh = labels.get(dim, dim)
        if value == 100:
            good.append((f"{zh}满分", f"Full marks: {DIM_EN.get(dim, dim)}"))
        elif value <= 34:
            special = {"honesty": ("容易编造", "Tends to fabricate"), "tool_calling": ("工具调用弱", "Weak tool calling")}
            bad.append(special.get(dim, (f"{zh}弱", f"Weak: {DIM_EN.get(dim, dim)}")))
    if (m.get("successRate") or 100) < 90:
        bad.append((f"请求成功率 {m['successRate']}%", f"{m['successRate']}% request success"))
    return good[:5], bad[:4]


def verdict_for(m: dict) -> dict:
    verdict = (load_verdicts().get("models") or {}).get(str(m.get("model")))
    return verdict if isinstance(verdict, dict) else {}


# ---------------------------------------------------------------- small cells

def status_cell(site_provider_id: str, model_name: str) -> str:
    """One compact cell for catalog tables: real numbers, reference, unavailable or 未实测."""
    kind, m = lookup(site_provider_id, model_name)
    if m:
        prov, score, rate = m.get("provider"), m.get("score"), m.get("successRate")
        ttft, tps = _fmt_ms(m.get("p50TtftMs")), _fmt_tps(m.get("medianTokensPerSec"))
    if kind == "measured":
        return (
            f'<a class="fl-eval-pill is-measured" href="{_e(report_href(m))}">{_pair(f"实测 {score} 分", f"Score {score}")}</a>'
            f'<small>{_pair(f"首 token {ttft} · {tps}", f"TTFT {ttft} · {tps}")}</small>'
        )
    if kind == "low_success":
        return (
            f'<a class="fl-eval-pill is-warn" href="{_e(report_href(m))}">{_pair(f"成功率 {rate}%", f"{rate}% success")}</a>'
            f'<small>{_pair("限流/失败较多，分数不具代表性", "Many failed requests")}</small>'
        )
    if kind == "unavailable":
        zh, en = unavailable_reason(m)
        return (
            f'<a class="fl-eval-pill is-down" href="{_e(report_href(m))}">{_pair("本账号/本端点不可用", "Unavailable for our key")}</a>'
            f'<small>{_pair(f"{zh}，待复核", f"{en}, pending recheck")}</small>'
        )
    if kind == "reference":
        return (
            f'<a class="fl-eval-pill is-reference" href="{_e(report_href(m))}">{_pair(f"同款模型经 {prov} 实测 {score} 分", f"Same model on {prov}: {score}")}</a>'
            f'<small>{_pair("本渠道速度未实测", "This route: speed untested")}</small>'
        )
    return f'<span class="fl-eval-pill is-untested">{_pair("未实测", "Not tested")}</span>'


def _dims_markup(m: dict) -> str:
    dims = m.get("dimensions") or {}
    labels = load_results().get("dimensions") or {}
    rows = []
    for dim in DIM_ORDER:
        value = dims.get(dim)
        label = _pair(labels.get(dim, dim), DIM_EN.get(dim, dim))
        if value is None:
            rows.append(f'<li><span>{label}</span><b>—</b><i aria-hidden="true"></i></li>')
            continue
        rows.append(
            f'<li><span>{label}</span><b>{_e(value)}</b>'
            f'<i aria-hidden="true"><em style="width:{max(0, min(100, int(value)))}%"></em></i></li>'
        )
    return f'<ul class="fl-eval-dims">{"".join(rows)}</ul>'


def _tags_markup(m: dict) -> str:
    good, bad = auto_tags(m)
    if not good and not bad:
        return ""
    chips = "".join(f'<span class="fl-eval-tag is-good">{_pair(zh, en)}</span>' for zh, en in good)
    chips += "".join(f'<span class="fl-eval-tag is-bad">{_pair(zh, en)}</span>' for zh, en in bad)
    return f'<div class="fl-eval-tags">{chips}</div>'


def _verdict_markup(m: dict) -> str:
    verdict = verdict_for(m)
    parts = []
    if verdict.get("tagline"):
        parts.append(f'<p class="fl-eval-tagline">{_e(verdict["tagline"])}</p>')
    uses = []
    if verdict.get("bestFor"):
        uses.append(f'<div><dt>{_pair("适合", "Good for")}</dt><dd>{_e(verdict["bestFor"])}</dd></div>')
    if verdict.get("avoid"):
        uses.append(f'<div><dt>{_pair("不建议", "Avoid for")}</dt><dd>{_e(verdict["avoid"])}</dd></div>')
    if uses:
        parts.append(f'<dl class="fl-eval-uses">{"".join(uses)}</dl>')
    return "".join(parts)


def _links_markup(m: dict) -> str:
    return (
        f'<p class="fl-eval-links"><a href="{_e(report_href(m))}">{_pair("在实测报告中查看", "Open in test report")} →</a>'
        f'<a href="{_e(RAW_DATA_URL)}" target="_blank" rel="noopener">{_pair("逐题原始输出", "Raw per-case outputs")} ↗</a></p>'
    )


def measured_card(m: dict, heading_tag: str = "h3") -> str:
    """Full same-channel card: score, success rate, latency p50/p95, tokens/s, dims, tags, verdict, links."""
    kind = _status_of(m)
    rate, score = m.get("successRate"), m.get("score")
    if kind == "low_success":
        headline = (
            f'<span class="fl-eval-score is-warn">{_e(rate)}<small>%</small></span>'
            f'<span class="fl-eval-score-note">{_pair(f"请求成功率；限流/失败较多，{score} 分受失败请求影响", f"request success; score {score} is dragged down by failures")}</span>'
        )
    else:
        headline = f'<span class="fl-eval-score">{_e(m.get("score"))}<small>{_pair("分", "pts")}</small></span>'
    facts = [
        ("综合分", "Score", f'{m.get("score")} / 100'),
        ("成功率", "Success rate", f'{rate}%（{m.get("answered", "—")}/{m.get("total", case_count())} 题有回答）' if rate is not None else "—"),
        ("首 token p50 / p95", "TTFT p50 / p95", f'{_fmt_ms(m.get("p50TtftMs"))} / {_fmt_ms(m.get("p95TtftMs"))}'),
        ("生成速度（中位）", "Tokens/s (median)", _fmt_tps(m.get("medianTokensPerSec"))),
    ]
    facts_markup = "".join(f'<div class="fact"><strong>{_pair(zh, en)}</strong><span>{_e(value)}</span></div>' for zh, en, value in facts)
    return (
        f'<article class="fl-eval-card" id="eval-{_e(anchor(m))}">'
        f'<div class="fl-eval-card-head"><div><{heading_tag}>{_e(_short(m["model"]))}</{heading_tag}>'
        f'<small>{_e(m["model"])} · {_e(m.get("provider"))}{" · " + _pair("默认思考模式", "thinks by default") if m.get("thinksByDefault") else ""}</small></div>{headline}</div>'
        f'<div class="facts">{facts_markup}</div>'
        f'{_dims_markup(m)}{_tags_markup(m)}{_verdict_markup(m)}{_links_markup(m)}</article>'
    )


def reference_card(m: dict, heading_tag: str = "h3") -> str:
    """Another channel's result for the same model: score + dims only, no speed claims."""
    prov = m.get("provider")
    return (
        f'<article class="fl-eval-card is-reference">'
        f'<div class="fl-eval-card-head"><div><{heading_tag}>{_pair(f"同款模型经 {prov} 实测", f"Same model tested on {prov}")}</{heading_tag}>'
        f'<small>{_e(m["model"])}</small></div><span class="fl-eval-score">{_e(m.get("score"))}<small>{_pair("分", "pts")}</small></span></div>'
        f'<p class="fl-eval-note">{_pair(f"以下是 {prov} 渠道的能力得分，仅供参考；本渠道的首 token 延迟、生成速度和成功率未实测，不能套用。", f"Capability scores from {prov} for reference only; this route’s latency, speed and success rate were not measured.")}</p>'
        f'{_dims_markup(m)}{_verdict_markup(m)}{_links_markup(m)}</article>'
    )


def _section_head(title_zh: str, title_en: str, intro_html: str, section_id: str = "freellm-eval") -> str:
    meta = f"{suite_name()} · {case_count()} 题 · 7 维度 · {run_date()}"
    return (
        f'<section class="fl-eval-section" id="{_e(section_id)}">'
        f'<div class="eyebrow">{_pair("FreeLLM 实测", "FreeLLM test")} · {_e(meta)}</div>'
        f'<h2>{_pair(title_zh, title_en)}</h2>{intro_html}'
    )


def _method_note() -> str:
    data = load_results()
    vantage = str(data.get("vantage") or "")
    return (
        f'<p class="fl-eval-method muted">{_pair(f"方法：同一套 {case_count()} 道固定题、temperature=0、全部自动评分；测试节点：{vantage}。数字只代表该时间点、我们的账号和该测试节点，地区与账号不同结果会不同。", f"Method: the same {case_count()} fixed cases, temperature 0, auto-graded; vantage: GitHub Actions (US). Numbers reflect that run, our accounts and that vantage only.")} '
        f'<a href="{REPORT_URL}">{_pair("完整报告", "Full report")} →</a></p>'
    )


# ---------------------------------------------------------------- provider pages

def provider_summary_table(results: list[dict]) -> str:
    usable = [m for m in results if _usable(m)]
    if not usable:
        return ""
    rows = []
    for m in sorted(usable, key=lambda m: (_status_of(m) != "measured", -(m.get("score") or 0))):
        low = _status_of(m) == "low_success"
        score_cell = (f'{m.get("score")} <small>{_pair("受失败影响", "affected by failures")}</small>' if low else f'<strong>{_e(m.get("score"))}</strong>')
        rows.append(
            f'<tr><td class="model-cell"><a href="#eval-{_e(anchor(m))}"><strong class="model-name">{_e(_short(m["model"]))}</strong></a><small class="model-id">{_e(m["model"])}</small></td>'
            f'<td>{score_cell}</td><td>{_e(m.get("successRate"))}%</td>'
            f'<td>{_e(_fmt_ms(m.get("p50TtftMs")))}<small>p95 {_e(_fmt_ms(m.get("p95TtftMs")))}</small></td>'
            f'<td>{_e(_fmt_tps(m.get("medianTokensPerSec")))}</td>'
            f'<td><a href="{_e(report_href(m))}">{_pair("报告", "Report")} →</a></td></tr>'
        )
    head = "".join(f"<th>{_pair(zh, en)}</th>" for zh, en in (("模型", "Model"), ("综合分", "Score"), ("成功率", "Success"), ("首 token p50", "TTFT p50"), ("生成速度", "Tokens/s"), ("报告", "Report")))
    return f'<div class="catalog-table-wrap fl-eval-table-wrap"><table class="catalog-table fl-eval-table"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def unavailable_list(results: list[dict]) -> str:
    down = [m for m in results if not _usable(m)]
    if not down:
        return ""
    items = []
    for m in down:
        zh, en = unavailable_reason(m)
        items.append(
            f'<li><code>{_e(m["model"])}</code> — {_pair(f"本账号/本端点不可用（{zh}），待复核", f"unavailable for our key/endpoint ({en}), pending recheck")}'
            f' · <a href="{_e(report_href(m))}">{_pair("记录", "Record")}</a></li>'
        )
    return (
        f'<div class="fl-eval-down"><h3>{_pair(f"不可用的端点（{len(down)} 个）", f"Unavailable endpoints ({len(down)})")}</h3>'
        f'<p class="muted">{_pair("这些模型出现在平台模型列表里，但用我们的账号真实调用失败。这是账号权限、额度或接入限制，不代表模型能力，也不代表你的账号一定不可用。", "Listed by the platform but failed when called with our key: an account, quota or access limit, not a model-quality verdict.")}</p>'
        f'<ul class="fl-eval-down-list">{"".join(items)}</ul></div>'
    )


def provider_section(site_provider_id: str, provider_name: str, catalog_models: list[dict] | None = None) -> str:
    """Section for providers/<id>/: all measured models of this platform, or an explicit 未实测."""
    results = provider_results(site_provider_id)
    name = str(provider_name or site_provider_id)
    if results:
        usable = [m for m in results if _usable(m)]
        reliable = [m for m in usable if _status_of(m) == "measured"]
        low = [m for m in usable if _status_of(m) == "low_success"]
        down = len(results) - len(usable)
        intro_zh = f"我们用自己的账号对 {name} 上 {len(results)} 个标称免费的模型发起真实 API 调用：{len(reliable)} 个稳定可用并计分"
        intro_zh += f"，{len(low)} 个限流或失败较多" if low else ""
        intro_zh += f"，{down} 个本账号/本端点不可用（待复核）。" if down else "。"
        intro_en = f"We called {len(results)} free-listed models on {name} with our own key: {len(reliable)} scored reliably, {len(low)} had many failures, {down} unavailable."
        cards = "".join(measured_card(m) for m in sorted(usable, key=lambda m: (_status_of(m) != "measured", -(m.get("score") or 0))))
        body = (
            f'<p class="lead">{_pair(intro_zh, intro_en)}</p>{provider_summary_table(results)}'
            f'<div class="fl-eval-grid">{cards}</div>{unavailable_list(results)}{_method_note()}'
        )
        return _section_head(f"{name} 实测表现", f"{name}: FreeLLM test results", body) + "</section>"
    refs = []
    seen = set()
    for record in catalog_models or []:
        kind, m = lookup(site_provider_id, str(record.get("model") or ""))
        if kind == "reference" and anchor(m) not in seen:
            seen.add(anchor(m))
            refs.append((record, m))
    ref_markup = ""
    if refs:
        lines = []
        for record, m in refs:
            prov, score = m.get("provider"), m.get("score")
            label = _pair(f"同款模型经 {prov} 实测 {score} 分（本渠道速度与成功率未实测）", f"same model on {prov}: {score} (this route untested)")
            lines.append(f'<li><strong>{_e(record.get("model"))}</strong> — {label} · <a href="{_e(report_href(m))}">{_pair("报告", "Report")} →</a></li>')
        items = "".join(lines)
        ref_markup = f'<ul class="fl-eval-ref-list">{items}</ul>'
    intro = _pair(
        f"{name} 尚未纳入 FreeLLM 实测：本页没有我们自己的分数、延迟或成功率（未实测）。" + (" 下面几个模型在其他渠道测过，只能作为能力参考。" if refs else ""),
        f"{name} is not tested by FreeLLM yet: no scores, latency or success rates of our own on this page." + (" The models below were tested on other routes and are capability references only." if refs else ""),
    )
    body = f'<p><span class="fl-eval-pill is-untested">{_pair("未实测", "Not tested")}</span> {intro}</p>{ref_markup}{_method_note()}'
    return _section_head(f"{name} 实测表现", f"{name}: FreeLLM test results", body) + "</section>"


def provider_directory_chip(site_provider_id: str) -> str:
    results = provider_results(site_provider_id)
    reliable = [m for m in results if _usable(m) and _status_of(m) == "measured"]
    if results:
        top = max(reliable, key=lambda m: m["score"]) if reliable else None
        zh = f"实测 {len(results)} 个模型" + (f" · 最高 {top['score']} 分" if top else "")
        en = f"{len(results)} models tested" + (f" · best {top['score']}" if top else "")
        return f'<p class="fl-eval-chip-row"><a class="fl-eval-pill is-measured" href="/providers/{_e(site_provider_id)}/#freellm-eval">{_pair(zh, en)}</a></p>'
    return f'<p class="fl-eval-chip-row"><span class="fl-eval-pill is-untested">{_pair("未实测", "Not tested")}</span></p>'


# ---------------------------------------------------------------- model aggregate pages

def model_section(model_name: str, records: list[dict]) -> str:
    rows = []
    exact_cards, refs = [], {}
    for record in records:
        pid = str(record.get("providerId") or "")
        kind, m = lookup(pid, str(record.get("model") or model_name))
        rows.append(f'<li><strong>{_e(record.get("provider") or pid)}</strong>{status_cell(pid, str(record.get("model") or model_name))}</li>')
        if kind in ("measured", "low_success") and m and anchor(m) not in {a for a, _ in exact_cards}:
            exact_cards.append((anchor(m), m))
        elif kind == "reference" and m:
            refs[anchor(m)] = m
    exact_anchors = {a for a, _ in exact_cards}
    cards = "".join(measured_card(m) for _, m in exact_cards)
    cards += "".join(reference_card(m) for a, m in refs.items() if a not in exact_anchors)
    if not cards and not any("fl-eval-pill is-down" in row for row in rows):
        intro = _pair(
            f"{model_name} 在本页列出的渠道上都未实测：FreeLLM 没有它的分数、延迟或成功率。",
            f"{model_name} has not been tested by FreeLLM on any route listed here.",
        )
        body = f'<p><span class="fl-eval-pill is-untested">{_pair("未实测", "Not tested")}</span> {intro}</p>{_method_note()}'
        return _section_head(f"{model_name} 实测表现", f"{model_name}: FreeLLM test results", body) + "</section>"
    intro = _pair(
        "按渠道列出：只有实际调用过的渠道显示分数和速度；其他渠道标注「未实测」或只给同款模型的能力参考。",
        "Per route: only routes we actually called show scores and speed; others are marked untested or reference-only.",
    )
    grid = f'<div class="fl-eval-grid">{cards}</div>' if cards else ""
    body = (
        f'<p class="lead">{intro}</p><ul class="fl-eval-route-list">{"".join(rows)}</ul>'
        f'{grid}{_method_note()}'
    )
    return _section_head(f"{model_name} 实测表现", f"{model_name}: FreeLLM test results", body) + "</section>"


# ---------------------------------------------------------------- offers / categories

def offer_eval_provider(offer: dict) -> str:
    label = " ".join(str(offer.get(field) or "") for field in ("provider",)).lower()
    for eval_id, aliases in _OFFER_PROVIDER_ALIASES.items():
        if any(alias in label for alias in aliases):
            return eval_id
    return ""


def _offer_model_tokens(offer: dict) -> list[str]:
    text = str(offer.get("model") or "")
    pieces = re.split(r"\s*(?:/|·|,|，|、|\+|;|；|\|)\s*", text)
    return [p for p in (model_key(piece) for piece in pieces) if len(p) >= 4]


def offer_results(offer: dict) -> tuple[list[dict], list[dict]]:
    """(same-channel results, other-channel references) for one offer."""
    eval_id = offer_eval_provider(offer)
    same = [m for m in _models() if eval_id and m.get("providerId") == eval_id]
    refs: dict[str, dict] = {}
    for token in _offer_model_tokens(offer):
        for m in _models():
            if m.get("providerId") == eval_id or not _reliable(m) or model_key(m["model"]) != token:
                continue
            if token not in refs or m["score"] > refs[token]["score"]:
                refs[token] = m
    return same, list(refs.values())


def offer_chip(offer: dict) -> str:
    same, refs = offer_results(offer)
    if same:
        usable = [m for m in same if _usable(m) and _status_of(m) == "measured"]
        top = max(usable, key=lambda m: m["score"]) if usable else None
        zh = f"FreeLLM 实测 {len(same)} 个模型" + (f" · 最高 {top['score']} 分" if top else "")
        en = f"FreeLLM tested {len(same)} models" + (f" · best {top['score']}" if top else "")
        return f'<span class="fl-eval-pill is-measured">{_pair(zh, en)}</span>'
    if refs:
        m = max(refs, key=lambda m: m["score"])
        prov, score = m.get("provider"), m.get("score")
        return f'<span class="fl-eval-pill is-reference">{_pair(f"同款模型经 {prov} 实测 {score} 分", f"Same model on {prov}: {score}")}</span>'
    return f'<span class="fl-eval-pill is-untested">{_pair("未实测", "Not tested")}</span>'


def _offer_row(offer: dict, offer_href: str) -> str:
    same, refs = offer_results(offer)
    title = offer.get("titleZh") or offer.get("title") or offer.get("name") or offer.get("id")
    if same:
        usable = [m for m in same if _usable(m)]
        reliable = sorted([m for m in usable if _status_of(m) == "measured"], key=lambda m: -m["score"])
        down = len(same) - len(usable)
        best = reliable[0] if reliable else None
        best_txt = (
            f'{_e(_short(best["model"]))} <strong>{_e(best["score"])}</strong> · {_e(_fmt_ms(best.get("p50TtftMs")))} · {_e(_fmt_tps(best.get("medianTokensPerSec")))}'
            if best else _pair("无稳定可用模型", "No reliable model")
        )
        site_pid = EVAL_TO_SITE_PROVIDER.get(offer_eval_provider(offer), "")
        detail = _pair(
            f"测 {len(same)} 个 · 稳定可用 {len(reliable)} 个" + (f" · 本账号/本端点不可用 {down} 个（待复核）" if down else ""),
            f"{len(same)} tested · {len(reliable)} reliable" + (f" · {down} unavailable" if down else ""),
        )
        link = f'<a href="/providers/{_e(site_pid)}/#freellm-eval">{_pair("逐个模型", "Per model")} →</a>' if site_pid else ""
        return f'<tr><td><a href="{_e(offer_href)}">{_e(title)}</a><small>{_pair("同渠道实测", "Same-route test")}</small></td><td>{detail}</td><td>{best_txt}</td><td>{link}</td></tr>'
    m = max(refs, key=lambda m: m["score"])
    prov = m.get("provider")
    return (
        f'<tr><td><a href="{_e(offer_href)}">{_e(title)}</a><small>{_pair("仅同款模型参考", "Reference only")}</small></td>'
        f'<td>{_pair(f"同款模型经 {prov} 实测", f"Same model on {prov}")}</td>'
        f'<td>{_e(_short(m["model"]))} <strong>{_e(m["score"])}</strong> · {_pair("本渠道速度未实测", "route speed untested")}</td>'
        f'<td><a href="{_e(report_href(m))}">{_pair("报告", "Report")} →</a></td></tr>'
    )


def category_section(offers: list[dict], offer_href) -> str:
    """'本类实测表现' block for a category page. ``offer_href`` maps an offer to its URL."""
    measured = [offer for offer in offers if any(offer_results(offer))]
    untested = len(offers) - len(measured)
    if not measured:
        body = (
            f'<p><span class="fl-eval-pill is-untested">{_pair("未实测", "Not tested")}</span> '
            f'{_pair(f"本类 {len(offers)} 个资源暂无 FreeLLM 文本模型实测数据，下面每条都标为「未实测」。", f"None of the {len(offers)} resources in this category has FreeLLM test data yet.")}</p>{_method_note()}'
        )
        return _section_head("本类实测表现", "Tested in this category", body) + "</section>"
    head = "".join(f"<th>{_pair(zh, en)}</th>" for zh, en in (("资源", "Resource"), ("实测范围", "Coverage"), ("最佳模型 · 首 token · 速度", "Best model · TTFT · speed"), ("明细", "Details")))
    rows = "".join(_offer_row(offer, offer_href(offer)) for offer in measured)
    body = (
        f'<p class="lead">{_pair(f"本类 {len(offers)} 个资源中，{len(measured)} 个有 FreeLLM 实测数据；其余 {untested} 个未实测，在下方列表中单独标注。", f"{len(measured)} of {len(offers)} resources here have FreeLLM test data; the other {untested} are marked untested below.")}</p>'
        f'<div class="catalog-table-wrap fl-eval-table-wrap"><table class="catalog-table fl-eval-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
        f'<p class="fl-eval-note">{_pair("「同渠道实测」是我们用该平台账号直接调用得到的数字；「仅同款模型参考」只说明同一模型在别的平台的能力得分，不代表本资源的速度和成功率。", "Same-route numbers come from calling that platform directly; reference rows only show the same model’s capability score elsewhere.")}</p>'
        f'{_method_note()}'
    )
    return _section_head("本类实测表现", "Tested in this category", body) + "</section>"


def offer_section(offer: dict) -> str:
    """Section for an offer detail page; empty when neither the route nor its named models were tested."""
    same, refs = offer_results(offer)
    if not same and not refs:
        return ""
    if same:
        site_pid = EVAL_TO_SITE_PROVIDER.get(offer_eval_provider(offer), "")
        usable = sorted([m for m in same if _usable(m)], key=lambda m: (_status_of(m) != "measured", -(m.get("score") or 0)))
        cards = "".join(measured_card(m) for m in usable[:3])
        more = (
            f'<p><a href="/providers/{_e(site_pid)}/#freellm-eval">{_pair(f"查看该平台全部 {len(same)} 个实测模型（含不可用端点）", f"All {len(same)} tested models on this platform")} →</a></p>'
            if site_pid else ""
        )
        body = (
            f'<p class="lead">{_pair("我们用自己的账号直接调用该平台得到的结果（同渠道实测）。", "Results from calling this platform directly with our own key.")}</p>'
            f'{provider_summary_table(same)}<div class="fl-eval-grid">{cards}</div>{more}{unavailable_list(same)}{_method_note()}'
        )
    else:
        cards = "".join(reference_card(m) for m in refs)
        body = (
            f'<p class="lead">{_pair("本资源本身未实测；下面是它提供的同款模型在其他平台的实测能力得分，速度与成功率不能套用。", "This resource itself is untested; below are capability scores for the same models on other platforms.")}</p>'
            f'<div class="fl-eval-grid">{cards}</div>{_method_note()}'
        )
    return _section_head("FreeLLM 模型实测", "FreeLLM model test", body) + "</section>"
