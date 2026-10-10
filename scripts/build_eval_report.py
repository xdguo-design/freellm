#!/usr/bin/env python3
"""Render data/evaluations/latest.json into the public report page evaluations/index.html.

Editorial verdicts (one-line takeaways per model, headline findings) live in
data/evaluations/verdicts.json and are optional; everything else is computed.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.eval_integration import anchor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "evaluations" / "latest.json"
VERDICTS = ROOT / "data" / "evaluations" / "verdicts.json"
OUT = ROOT / "evaluations" / "index.html"
REPO = "https://github.com/xdguo-design/freellm"

ERROR_ZH = {
    "HTTP 401": "Key 无效或无权限",
    "HTTP 402": "需要付费/余额不足",
    "HTTP 403": "账号无权调用",
    "HTTP 404": "该账号下模型不可用（未开放或已下线）",
    "HTTP 429": "限流或免费额度用尽",
    "HTTP 400": "请求被拒绝（参数不支持）",
    "HTTP 500": "服务端错误",
    "HTTP 503": "服务暂不可用",
    "TimeoutError": "超时",
}


def e(x) -> str:
    return html.escape(str(x), quote=True)


def cell_class(v) -> str:
    if v is None:
        return "na"
    if v >= 90:
        return "s5"
    if v >= 70:
        return "s4"
    if v >= 50:
        return "s3"
    if v >= 25:
        return "s2"
    return "s1"


def short(model: str) -> str:
    return model.split("/")[-1]


def reason_zh(m: dict) -> str:
    detail = m.get("errorDetail", "")
    if "余额" in detail or "资源包" in detail:
        return "余额不足或无可用资源包（非免费）"
    if "insufficient_quota" in detail:
        return "免费额度已用尽"
    if "访问量过大" in detail or "rate-limited" in detail:
        return "上游限流（高峰期不可用）"
    errs = m.get("errors") or []
    if "HTTP 400" in errs and "no provider" in detail.lower():
        # e.g. ModelScope "… has no provider supported": the model has no serving
        # provider, it is not a parameter problem. Keep in sync with
        # eval_pages.unavailable_reason.
        return "；".join("无可用服务商" if x == "HTTP 400" else ERROR_ZH.get(x, x) for x in errs)
    return "；".join(ERROR_ZH.get(x, x) for x in errs) or "无响应"


def auto_tags(m: dict) -> tuple[list[str], list[str]]:
    d = m.get("dimensions", {})
    good, bad = [], []
    ttft, tps = m.get("p50TtftMs"), m.get("medianTokensPerSec")
    if ttft is not None and ttft < 350:
        good.append("首字极快")
    if tps is not None and tps >= 300:
        good.append("高吞吐")
    if m.get("thinksByDefault"):
        bad.append("默认长思考，响应慢")
    labels = {"coding": "代码", "tool_calling": "工具调用", "long_context": "长文本", "honesty": "不编造",
              "chinese_knowledge": "中文知识", "reasoning_math": "推理数学", "instruction_format": "格式遵循"}
    for k, lab in labels.items():
        v = d.get(k)
        if v is None:
            continue
        if v == 100:
            good.append(f"{lab}满分")
        elif v <= 34:
            bad.append({"honesty": "容易编造", "tool_calling": "工具调用弱"}.get(k, f"{lab}弱"))
    if m.get("successRate", 100) < 90:
        bad.append(f"请求成功率 {m['successRate']}%")
    return good[:5], bad[:4]


def awards(models: list[dict]) -> list[tuple[str, dict, str]]:
    ok = [m for m in models if m.get("available") and m.get("successRate", 0) >= 80]
    out = []
    if not ok:
        return out
    best = max(ok, key=lambda m: (m["score"] or 0, -(m.get("p50TtftMs") or 1e9)))
    out.append(("综合第一", best, f"{best['score']} 分"))
    fast = [m for m in ok if m.get("p50TtftMs")]
    if fast:
        f = min(fast, key=lambda m: m["p50TtftMs"])
        out.append(("首字最快", f, f"{f['p50TtftMs']} ms"))
    thr = [m for m in ok if m.get("medianTokensPerSec")]
    if thr:
        t = max(thr, key=lambda m: m["medianTokensPerSec"])
        out.append(("吞吐最高", t, f"{t['medianTokensPerSec']:.0f} tok/s"))
    for dim, title in (("coding", "代码最稳"), ("tool_calling", "工具调用最佳"), ("honesty", "最不爱编造")):
        cand = [m for m in ok if m.get("dimensions", {}).get(dim) is not None]
        if cand:
            c = max(cand, key=lambda m: (m["dimensions"][dim], m["score"] or 0, -(m.get("p50TtftMs") or 1e9)))
            out.append((title, c, f"{c['dimensions'][dim]} 分"))
    return out


def render() -> str:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    verdicts = json.loads(VERDICTS.read_text(encoding="utf-8")) if VERDICTS.exists() else {}
    vmodels = verdicts.get("models", {})
    dims: dict[str, str] = data.get("dimensions", {})
    models = data["models"]
    avail = [m for m in models if m.get("available")]
    down = [m for m in models if not m.get("available")]
    requests = sum(m.get("attempted", 0) for m in models)
    providers = sorted({m["provider"] for m in models})
    run_date = data["runAt"][:10]
    case_by_id = {c["id"]: c for c in data.get("cases", [])}

    style = "<style>\n" + (Path(__file__).with_name("eval_report.css")).read_text(encoding="utf-8") + "\n</style>"
    hero = f"""<header class="log-hero"><div class="log-hero-top"><div><div class="log-kicker">FREELLM 实测 / {e(data['suite'])}</div><h1><span lang="zh-CN">免费大模型 API 实测报告</span><span lang="en">Free LLM API test report</span></h1><p class="lead">{e(verdicts.get('lead') or '')}</p></div><div class="log-hero-meta"><div><span>测试日期</span><strong>{e(run_date)}</strong></div><div><span>测试模型 / 可用</span><strong>{len(models)} / {len(avail)}</strong></div><div><span>真实请求</span><strong>{requests}</strong></div></div></div><div class="log-hero-actions"><a href="/models/">查看精选模型</a><a href="{REPO}/blob/main/data/evaluations/latest.json">下载原始数据</a></div></header>
"""
    parts = [style, hero, '<div class="fl-eval">']

    headlines = verdicts.get("headlines") or []
    if headlines:
        parts.append('<section class="fl-eval-sec"><div class="wrap"><h2>核心结论</h2><p class="sub">基于本轮实测数据，由 FreeLLM 编辑整理</p><div class="findings">')
        parts += [f'<div class="finding">{e(h)}</div>' for h in headlines]
        parts.append("</div></div></section>")

    aw = awards(models)
    if aw:
        parts.append('<section class="fl-eval-sec"><div class="wrap"><h2>单项之最</h2><p class="sub">仅统计请求成功率 ≥ 80% 的模型</p><div class="awards">')
        for title, m, val in aw:
            parts.append(f'<div class="award"><small>{e(title)}</small><b>{e(short(m["model"]))}</b><small>{e(m["provider"])}</small> · <em>{e(val)}</em></div>')
        parts.append("</div></div></section>")

    # Leaderboard
    parts.append('<section class="fl-eval-sec"><div class="wrap"><h2>总榜</h2><p class="sub">总分 = 22 道题通过率；各维度为该维度题目通过率。首字延迟为 p50，速度为输出 token/秒中位数。</p><div class="tbl"><table><thead><tr><th>#</th><th class="l">模型</th><th>总分</th>')
    parts += [f"<th>{e(v)}</th>" for v in dims.values()]
    parts.append("<th>首字 p50</th><th>速度</th><th>成功率</th></tr></thead><tbody>")
    for i, m in enumerate(avail, 1):
        row = [f"<td>{i}</td>", f'<td class="l m">{e(short(m["model"]))}<span class="p">{e(m["provider"])}</span></td>', f'<td class="total">{m["score"]}</td>']
        for k in dims:
            v = m.get("dimensions", {}).get(k)
            row.append(f'<td class="{cell_class(v)}">{"—" if v is None else v}</td>')
        ttft = m.get("p50TtftMs")
        tps = m.get("medianTokensPerSec")
        row.append(f"<td>{'—' if ttft is None else f'{ttft:.0f} ms'}</td><td>{'—' if tps is None else f'{tps:.0f}'}</td><td>{m.get('successRate', 0)}%</td>")
        parts.append("<tr>" + "".join(row) + "</tr>")
    parts.append("</tbody></table></div></div></section>")

    # Model cards
    parts.append('<section class="fl-eval-sec"><div class="wrap"><h2>逐个模型画像</h2><p class="sub">强项、短板和适用场景；展开可看答错的题和模型原始输出</p><div class="cards">')
    for m in avail:
        v = vmodels.get(m["model"], {})
        good, bad = auto_tags(m)
        bars = "".join(
            f'<div class="bar">{e(lab)}<i><u style="width:{m["dimensions"].get(k, 0)}%"></u></i>{m["dimensions"].get(k, "—")}</div>'
            for k, lab in dims.items() if k in m.get("dimensions", {})
        )
        fails = [c for c in m.get("cases", []) if c.get("ok") and not c.get("pass")]
        errs = [c for c in m.get("cases", []) if not c.get("ok")]
        fail_html = ""
        if fails or errs:
            items = []
            for c in fails:
                prompt = case_by_id.get(c["case"], {}).get("prompt", "")
                shown = c.get("output") or ("[调用工具] " + json.dumps(c.get("toolCalls"), ensure_ascii=False) if c.get("toolCalls") else "[无正文输出]")
                items.append(f"<pre><b>{e(c['case'])}</b> {e(prompt[-120:])}\n→ {e(shown[:400])}</pre>")
            for c in errs:
                items.append(f"<pre><b>{e(c['case'])}</b> 请求失败：{e(ERROR_ZH.get(c.get('error'), c.get('error')))}</pre>")
            fail_html = f"<details><summary>答错/失败 {len(fails) + len(errs)} 题</summary>{''.join(items)}</details>"
        ttft = m.get("p50TtftMs")
        tps = m.get("medianTokensPerSec")
        parts.append(f"""<div class="card" id="{anchor(m)}"><span class="score">{m['score']}</span><h3>{e(m['model'])}</h3><div class="prov">{e(m['provider'])}{' · 默认思考模式' if m.get('thinksByDefault') else ''}</div>
<p class="tagline">{e(v.get('tagline', ''))}</p>
<div class="tags">{''.join(f'<span class="tag g">{e(t)}</span>' for t in good)}{''.join(f'<span class="tag b">{e(t)}</span>' for t in bad)}</div>
<div class="bars">{bars}</div>
<div class="meta"><span>首字 p50 {'—' if ttft is None else f'{ttft:.0f} ms'}</span><span>p95 {'—' if m.get('p95TtftMs') is None else f"{m['p95TtftMs']:.0f} ms"}</span><span>速度 {'—' if tps is None else f'{tps:.0f} tok/s'}</span><span>成功率 {m.get('successRate', 0)}%</span></div>
{f'<div class="use"><b>适合：</b>{e(v["bestFor"])}</div>' if v.get('bestFor') else ''}{f'<div class="use"><b>不适合：</b>{e(v["avoid"])}</div>' if v.get('avoid') else ''}
{fail_html}</div>""")
    parts.append("</div></div></section>")

    if down:
        parts.append('<section class="fl-eval-sec"><div class="wrap"><h2>标称免费但本轮调不通</h2><p class="sub">同样计入报告：这些模型在本轮测试中没有返回任何有效回答</p><div class="tbl"><table><thead><tr><th class="l">模型</th><th class="l">平台</th><th class="l">原因</th></tr></thead><tbody>')
        for m in down:
            parts.append(f'<tr><td class="l m">{e(m["model"])}</td><td class="l">{e(m["provider"])}</td><td class="l">{e(reason_zh(m))}</td></tr>')
        parts.append("</tbody></table></div></div></section>")

    case_rows = "".join(f"<li><b>{e(c['id'])}</b>（{e(dims.get(c['dim'], c['dim']))}）{e(c['prompt'][:160])}</li>" for c in data.get("cases", []))
    parts.append(f"""<section class="fl-eval-sec"><div class="wrap"><h2>测试方法</h2><div class="method">
<p>{e(data.get('method', ''))}</p>
<ul><li>测试时间：{e(data['runAt'])}（北京时间）；测试环境：{e(data.get('vantage', ''))}。国内用户直连的延迟会不同。</li>
<li>只调用免费模型：OpenRouter 的 :free 版本、Groq 免费计划、魔搭 API-Inference、NVIDIA 免费端点、智谱官方免费模型（GLM-4.7-Flash、GLM-4-Flash-250414）、硅基流动价格表标 ¥0 的模型。</li>
<li>每题只跑一次，temperature=0。分数反映的是这套题上的表现，不等于模型的全部能力；免费额度和限流会随时间变化。</li>
<li>原始数据（含每题的完整模型输出）：<a href="{REPO}/blob/main/data/evaluations/latest.json">latest.json</a>；评测脚本：<a href="{REPO}/blob/main/scripts/eval_models.py">eval_models.py</a>。</li></ul>
<details><summary>查看全部 {len(data.get('cases', []))} 道题</summary><ul>{case_rows}</ul></details>
</div></div></section>
<p class="sub" style="margin-top:8px">每周一自动重测 · 发现数据有误？<a href="{REPO}/issues">提交 Issue</a></p></div>
""")
    return "".join(parts)


TEMPLATE = ROOT / "logs" / "index.html"
TITLE = "免费大模型 API 实测报告 · FreeLLM"


def wrap(inner: str, description: str) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    start = tpl.index('<main class="daily-log-dashboard">')
    end = tpl.rindex("</main>")
    prefix, suffix = tpl[:start], tpl[end:]
    prefix = re.sub(r"<title>.*?</title>", f"<title>{e(TITLE)}</title>", prefix, count=1, flags=re.S)
    prefix = re.sub(r'(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]*"', lambda m: m.group(1) + e(description) + '"', prefix)
    prefix = re.sub(r'(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*"', lambda m: m.group(1) + e(TITLE) + '"', prefix)
    prefix = prefix.replace("https://freellm.top/logs/", "https://freellm.top/evaluations/")
    prefix = re.sub(r'<script type="application/ld\+json">.*?</script>', "", prefix, flags=re.S)
    prefix = prefix.replace('data-fl-section="logs"', 'data-fl-section="logs" data-fl-nav="models"', 1)
    prefix = prefix.replace(' data-site-nav="logs" aria-current="page"', ' data-site-nav="logs"')
    prefix = prefix.replace('<a href="/models/" data-site-nav="models">', '<a href="/models/" data-site-nav="models" aria-current="page">', 1)
    tabs = '<nav class="model-section-tabs" aria-label="模型页面"><a href="/models/">精选模型</a><a href="/models/all/">全部模型</a><a href="/providers/">按厂家</a><a href="/category/api/">免费 API / Offer</a><a href="/evaluations/" aria-current="page">实测榜</a></nav>'
    inner = tabs + inner
    return prefix + '<main class="daily-log-dashboard">' + inner + suffix


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    desc = f"FreeLLM 用同一套 {len(data.get('cases', []))} 道固定题，对 {len(data['models'])} 个免费大模型做真实 API 调用评测：中文、推理、代码、工具调用、长文本、防幻觉、首字延迟与生成速度。原始数据公开可复现。"
    OUT.write_text(wrap(render(), desc), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
