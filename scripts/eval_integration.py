"""Expose FreeLLM real-evaluation results (data/evaluations/latest.json) to page builders.

Used by the models landing page (per-card "实测" block) and the homepage
leaderboard. Matching is conservative: an exact provider + model match shows the
full measured numbers; the same model measured on another provider is shown only
as a clearly labelled reference ("同款模型经 X 实测").
"""
from __future__ import annotations

import html
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "data" / "evaluations" / "latest.json"
REPORT_URL = "/evaluations/"

_PROVIDER_ALIASES = {
    "groq": ("groq",),
    "siliconflow": ("siliconflow", "硅基"),
    "modelscope": ("modelscope", "魔搭"),
    "nvidia": ("nvidia",),
    "zhipu": ("zhipu", "智谱", "bigmodel"),
    "openrouter": ("openrouter",),
}


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def model_key(name: str) -> str:
    name = str(name or "").lower()
    name = name.split("/")[-1]
    name = re.sub(r"\(free\)|:free", "", name)
    if ":" in name:  # "Vendor: Model" display names
        name = name.split(":", 1)[1]
    return re.sub(r"[^a-z0-9.]", "", name).replace(".", "")


@lru_cache(maxsize=1)
def load_results() -> dict:
    if not LATEST.exists():
        return {}
    try:
        return json.loads(LATEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _available() -> list[dict]:
    return [m for m in load_results().get("models", []) if m.get("available") and m.get("score") is not None]


def provider_matches(provider_id: str, provider_label: str) -> bool:
    label = str(provider_label or "").lower()
    return any(alias in label for alias in _PROVIDER_ALIASES.get(provider_id, (provider_id,)))


def find_result(model_name: str, provider_label: str) -> tuple[dict | None, bool]:
    """Return (result, exact_route). exact_route is False for same-model-other-provider."""
    key = model_key(model_name)
    if not key:
        return None, False
    same_model = [m for m in _available() if model_key(m["model"]) == key]
    for m in same_model:
        if provider_matches(m["providerId"], provider_label):
            return m, True
    reliable = [m for m in same_model if m.get("successRate", 0) >= 80]
    if reliable:
        return max(reliable, key=lambda m: m["score"]), False
    return None, False


def anchor(m: dict) -> str:
    return "m-" + re.sub(r"[^a-z0-9]+", "-", f"{m['providerId']}-{m['model']}".lower()).strip("-")


def card_block(model_name: str, provider_label: str, locale_pair) -> str | None:
    """HTML for a model card's measured block, or None when never measured."""
    m, exact = find_result(model_name, provider_label)
    if not m:
        return None
    run_date = str(load_results().get("runAt", ""))[:10]
    href = f"{REPORT_URL}#{anchor(m)}"
    score, rate, prov = m["score"], m.get("successRate", 100), m["provider"]
    if exact and rate < 80:
        return (
            f'<div class="featured-model-speed is-reference"><strong>{locale_pair(f"实测：频繁限流，成功率 {rate}%", f"Rate-limited: {rate}% success")}</strong>'
            f'<small>{locale_pair("FreeLLM 实测", "FreeLLM test")} · {_e(run_date)} · <a href="{_e(href)}">{locale_pair("看报告", "Report")} →</a></small></div>'
        )
    if exact:
        ttft = m.get("p50TtftMs")
        tps = m.get("medianTokensPerSec")
        parts = [f'<strong>{locale_pair(f"实测 {score} 分", f"Score {score}")}</strong>']
        if ttft:
            parts.append(f'<strong>{locale_pair(f"首 token {ttft:.0f} ms", f"TTFT {ttft:.0f} ms")}</strong>')
        if tps:
            parts.append(f'<strong>{locale_pair(f"{tps:.0f} token/s", f"{tps:.0f} tokens/s")}</strong>')
        return (
            f'<div class="featured-model-speed is-evaluated">{"".join(parts)}'
            f'<small>{locale_pair("FreeLLM 实测", "FreeLLM test")} · {_e(run_date)} · <a href="{_e(href)}">{locale_pair("看报告", "Report")} →</a></small></div>'
        )
    return (
        f'<div class="featured-model-speed is-reference"><strong>{locale_pair(f"同款模型经 {prov} 实测 {score} 分", f"Same model on {prov}: {score}")}</strong>'
        f'<small>{locale_pair("本渠道速度未实测", "This route untested")} · <a href="{_e(href)}">{locale_pair("看报告", "Report")} →</a></small></div>'
    )


def leaderboard_html(limit: int = 6, heading_tag: str = "h2") -> str:
    data = load_results()
    rows = [m for m in _available() if m.get("successRate", 0) >= 80][:limit]
    if not rows:
        return ""
    run_date = str(data.get("runAt", ""))[:10]
    total_models = len(data.get("models", []))
    items = []
    for i, m in enumerate(rows, 1):
        ttft = m.get("p50TtftMs")
        tps = m.get("medianTokensPerSec")
        items.append(
            f'<li><a href="{REPORT_URL}#{anchor(m)}"><span class="fl-evalboard-rank">{i}</span>'
            f'<span class="fl-evalboard-name"><b>{_e(m["model"].split("/")[-1])}</b><small>{_e(m["provider"])}</small></span>'
            f'<span class="fl-evalboard-score">{m["score"]}<small>分</small></span>'
            f'<span class="fl-evalboard-meta">{"" if not ttft else f"首字 {ttft:.0f} ms"}{"" if not tps else f" · {tps:.0f} tok/s"}</span></a></li>'
        )
    return (
        '<section class="fl-evalboard" id="real-evaluation" aria-labelledby="fl-evalboard-title">'
        f'<div class="fl-evalboard-head"><div><{heading_tag} id="fl-evalboard-title">免费模型实测榜</{heading_tag}>'
        f'<p>{_e(run_date)} · 真实 API 调用 · {len(data.get("cases", []))} 道题自动评分 · 共测 {total_models} 个模型</p></div>'
        f'<a href="{REPORT_URL}">完整报告 →</a></div><ol>{"".join(items)}</ol></section>'
    )


LEADERBOARD_CSS = (
    ".fl-evalboard{margin:24px 0;padding:20px 22px;border:1px solid #e3e9f4;border-radius:16px;background:#fff}"
    ".fl-evalboard-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:12px}"
    ".fl-evalboard-head h2,.fl-evalboard-head h3{font-size:20px;margin:0}.fl-evalboard-head p{margin:4px 0 0;color:#6a7896;font-size:13px}"
    ".fl-evalboard-head>a{color:#1744E8;font-weight:600;font-size:14px;white-space:nowrap}"
    ".fl-evalboard ol{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:8px}"
    ".fl-evalboard li a{display:grid;grid-template-columns:28px 1fr auto;grid-template-rows:auto auto;column-gap:10px;align-items:center;padding:10px 12px;border-radius:12px;background:#f6f9fe;color:inherit;text-decoration:none}"
    ".fl-evalboard li a:hover{background:#edf3ff}"
    ".fl-evalboard-rank{grid-row:span 2;width:28px;height:28px;border-radius:50%;background:#1744E8;color:#fff;display:grid;place-items:center;font-weight:700;font-size:13px}"
    ".fl-evalboard-name b{display:block;font-size:14px;word-break:break-all}.fl-evalboard-name small{color:#6a7896;font-size:12px}"
    ".fl-evalboard-score{grid-row:span 2;font-size:22px;font-weight:800;color:#1744E8}.fl-evalboard-score small{font-size:12px;margin-left:2px}"
    ".fl-evalboard-meta{grid-column:2;font-size:12px;color:#4a5878}"
    ".featured-model-speed.is-evaluated{background:#e7f6ee;color:#11713f}.featured-model-speed.is-evaluated a,.featured-model-speed.is-reference a{color:inherit;text-decoration:underline}"
    ".featured-model-speed.is-reference{background:#f1f4fb;color:#3a4a72}"
)
