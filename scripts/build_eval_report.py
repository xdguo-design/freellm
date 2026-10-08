#!/usr/bin/env python3
"""Render data/evaluations/latest.json into the public report page evaluations/index.html.

Editorial verdicts (one-line takeaways per model, headline findings) live in
data/evaluations/verdicts.json and are optional; everything else is computed.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

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

    head = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>免费大模型 API 实测报告（{e(run_date)}）｜FreeLLM</title>
<meta name="description" content="FreeLLM 用同一套 {len(data.get('cases', []))} 道固定题，对 {len(providers)} 家平台的 {len(models)} 个免费模型做真实 API 调用评测：中文、推理、代码、工具调用、长文本、防幻觉，以及首字延迟和生成速度。原始数据公开可复现。">
<link rel="canonical" href="https://freellm.top/evaluations/">
<style>
:root{{--ink:#0c1230;--t2:#4a5878;--t3:#6a7896;--line:#e3e9f4;--blue:#0b57f0;--bg:#f6fafe}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:"PingFang SC","Microsoft YaHei","Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 20px}}
header.top{{background:#0a1428;color:#e8eefc}}header.top .wrap{{display:flex;align-items:center;gap:18px;height:56px}}header.top a{{color:#e8eefc}}header.top .brand{{font-weight:700;font-size:17px}}header.top nav{{margin-left:auto;display:flex;gap:18px;font-size:14px}}
.hero{{background:radial-gradient(900px 380px at 80% -60px,rgba(147,190,247,.55),transparent 70%),linear-gradient(180deg,#eef4fe,#f6fafe);padding:44px 0 28px}}
.eyebrow{{font-size:13px;color:var(--blue);font-weight:600;letter-spacing:.04em}}h1{{font-size:34px;line-height:1.25;margin:8px 0 12px}}.lead{{font-size:16px;color:var(--t2);max-width:820px}}
.stats{{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 16px;min-width:130px}}.stat b{{display:block;font-size:24px}}.stat span{{font-size:12px;color:var(--t3)}}
section{{padding:30px 0}}h2{{font-size:22px;margin-bottom:6px}}.sub{{color:var(--t3);font-size:14px;margin-bottom:16px}}
.findings{{display:grid;gap:10px}}.finding{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:10px;padding:12px 16px;font-size:15px}}
.awards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}}.award{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}}.award small{{color:var(--t3);font-size:12px}}.award b{{display:block;font-size:15px;margin:4px 0;word-break:break-all}}.award em{{font-style:normal;color:var(--blue);font-weight:700}}
.tbl{{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:12px}}table{{border-collapse:collapse;width:100%;font-size:13.5px;white-space:nowrap}}th,td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:center}}th{{background:#f3f7fd;font-weight:600;color:var(--t2);position:sticky;top:0}}td.l,th.l{{text-align:left}}td.m{{font-weight:600}}td .p{{display:block;font-size:11.5px;color:var(--t3);font-weight:400}}
.s5{{background:#d8f3e3}}.s4{{background:#e9f7d9}}.s3{{background:#fff3d1}}.s2{{background:#ffe2cc}}.s1{{background:#fdd5d5}}.na{{color:#aab}}.total{{font-weight:700;font-size:15px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}}.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}}.card h3{{font-size:16px;word-break:break-all}}.card .prov{{font-size:12.5px;color:var(--t3)}}.card .score{{float:right;font-size:26px;font-weight:800;color:var(--blue);line-height:1}}.card .tagline{{margin:10px 0;font-size:14.5px}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}}.tag{{font-size:12px;border-radius:999px;padding:2px 9px}}.tag.g{{background:#e3f6ec;color:#11713f}}.tag.b{{background:#fde8e8;color:#a32121}}
.bars{{margin:10px 0;display:grid;gap:4px}}.bar{{display:grid;grid-template-columns:64px 1fr 34px;align-items:center;gap:8px;font-size:12px;color:var(--t2)}}.bar i{{display:block;height:7px;border-radius:4px;background:#e8eef8;overflow:hidden}}.bar i u{{display:block;height:100%;background:var(--blue)}}
.meta{{font-size:12.5px;color:var(--t2);display:flex;gap:14px;flex-wrap:wrap}}.use{{font-size:13px;margin-top:8px}}.use b{{color:var(--t2)}}
details{{margin-top:8px;font-size:12.5px}}summary{{cursor:pointer;color:var(--blue)}}details pre{{white-space:pre-wrap;word-break:break-all;background:#f6f8fc;border-radius:8px;padding:8px;margin-top:6px;max-height:200px;overflow:auto;font-size:12px}}
.method{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;font-size:14px;color:var(--t2)}}.method li{{margin-left:18px;margin-top:4px}}
footer{{padding:30px 0 50px;color:var(--t3);font-size:13px}}
@media(max-width:640px){{h1{{font-size:26px}}.cards{{grid-template-columns:1fr}}}}
</style></head><body>
<header class="top"><div class="wrap"><a class="brand" href="/">FreeLLM</a><nav><a href="/">首页</a><a href="/models/">模型</a><a href="/evaluations/">实测报告</a><a href="/about/">关于</a></nav></div></header>
"""
    hero = f"""<div class="hero"><div class="wrap">
<div class="eyebrow">FREELLM 实测 · {e(data['suite'])} · {e(run_date)}</div>
<h1>免费大模型 API 实测报告</h1>
<p class="lead">{e(verdicts.get('lead') or f'我们用自己的账号和 API Key，对 {len(providers)} 家平台上的免费模型发起真实调用：同一套题、同一参数、全部自动评分，每一个分数都能在原始数据里找到对应的模型输出。')}</p>
<div class="stats">
<div class="stat"><b>{len(models)}</b><span>测试模型</span></div>
<div class="stat"><b>{len(avail)}</b><span>实际可用</span></div>
<div class="stat"><b>{len(providers)}</b><span>平台</span></div>
<div class="stat"><b>{len(data.get('cases', []))} × {len(dims)}</b><span>题目 × 维度</span></div>
<div class="stat"><b>{requests}</b><span>真实 API 请求</span></div>
</div></div></div>
"""
    parts = [head, hero]

    headlines = verdicts.get("headlines") or []
    if headlines:
        parts.append('<section><div class="wrap"><h2>核心结论</h2><p class="sub">基于本轮实测数据，由 FreeLLM 编辑整理</p><div class="findings">')
        parts += [f'<div class="finding">{e(h)}</div>' for h in headlines]
        parts.append("</div></div></section>")

    aw = awards(models)
    if aw:
        parts.append('<section><div class="wrap"><h2>单项之最</h2><p class="sub">仅统计请求成功率 ≥ 80% 的模型</p><div class="awards">')
        for title, m, val in aw:
            parts.append(f'<div class="award"><small>{e(title)}</small><b>{e(short(m["model"]))}</b><small>{e(m["provider"])}</small> · <em>{e(val)}</em></div>')
        parts.append("</div></div></section>")

    # Leaderboard
    parts.append('<section><div class="wrap"><h2>总榜</h2><p class="sub">总分 = 22 道题通过率；各维度为该维度题目通过率。首字延迟为 p50，速度为输出 token/秒中位数。</p><div class="tbl"><table><thead><tr><th>#</th><th class="l">模型</th><th>总分</th>')
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
    parts.append('<section><div class="wrap"><h2>逐个模型画像</h2><p class="sub">强项、短板和适用场景；展开可看答错的题和模型原始输出</p><div class="cards">')
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
        parts.append(f"""<div class="card"><span class="score">{m['score']}</span><h3>{e(m['model'])}</h3><div class="prov">{e(m['provider'])}{' · 默认思考模式' if m.get('thinksByDefault') else ''}</div>
<p class="tagline">{e(v.get('tagline', ''))}</p>
<div class="tags">{''.join(f'<span class="tag g">{e(t)}</span>' for t in good)}{''.join(f'<span class="tag b">{e(t)}</span>' for t in bad)}</div>
<div class="bars">{bars}</div>
<div class="meta"><span>首字 p50 {'—' if ttft is None else f'{ttft:.0f} ms'}</span><span>p95 {'—' if m.get('p95TtftMs') is None else f"{m['p95TtftMs']:.0f} ms"}</span><span>速度 {'—' if tps is None else f'{tps:.0f} tok/s'}</span><span>成功率 {m.get('successRate', 0)}%</span></div>
{f'<div class="use"><b>适合：</b>{e(v["bestFor"])}</div>' if v.get('bestFor') else ''}{f'<div class="use"><b>不适合：</b>{e(v["avoid"])}</div>' if v.get('avoid') else ''}
{fail_html}</div>""")
    parts.append("</div></div></section>")

    if down:
        parts.append('<section><div class="wrap"><h2>标称免费但本轮调不通</h2><p class="sub">同样计入报告：这些模型在本轮测试中没有返回任何有效回答</p><div class="tbl"><table><thead><tr><th class="l">模型</th><th class="l">平台</th><th class="l">原因</th></tr></thead><tbody>')
        for m in down:
            parts.append(f'<tr><td class="l m">{e(m["model"])}</td><td class="l">{e(m["provider"])}</td><td class="l">{e(reason_zh(m))}</td></tr>')
        parts.append("</tbody></table></div></div></section>")

    case_rows = "".join(f"<li><b>{e(c['id'])}</b>（{e(dims.get(c['dim'], c['dim']))}）{e(c['prompt'][:160])}</li>" for c in data.get("cases", []))
    parts.append(f"""<section><div class="wrap"><h2>测试方法</h2><div class="method">
<p>{e(data.get('method', ''))}</p>
<ul><li>测试时间：{e(data['runAt'])}（北京时间）；测试环境：{e(data.get('vantage', ''))}。国内用户直连的延迟会不同。</li>
<li>只调用免费模型：OpenRouter 的 :free 版本、Groq 免费计划、魔搭 API-Inference、NVIDIA 免费端点、智谱官方免费模型（GLM-4.7-Flash、GLM-4-Flash-250414）、硅基流动价格表标 ¥0 的模型。</li>
<li>每题只跑一次，temperature=0。分数反映的是这套题上的表现，不等于模型的全部能力；免费额度和限流会随时间变化。</li>
<li>原始数据（含每题的完整模型输出）：<a href="{REPO}/blob/main/data/evaluations/latest.json">latest.json</a>；评测脚本：<a href="{REPO}/blob/main/scripts/eval_models.py">eval_models.py</a>。</li></ul>
<details><summary>查看全部 {len(data.get('cases', []))} 道题</summary><ul>{case_rows}</ul></details>
</div></div></section>
<footer><div class="wrap">FreeLLM · 每周一自动重测 · 发现数据有误？<a href="{REPO}/issues">提交 Issue</a></div></footer>
</body></html>
""")
    return "".join(parts)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
