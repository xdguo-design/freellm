#!/usr/bin/env node
/* Regenerate six editorial review pages and the directory cards from the audited JSON.
 * Usage: node scripts/build_public_api_reviews.cjs [--check]
 * Offline: no network calls. The generated scores describe public documentation only.
 */
"use strict";
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const esc=s=>String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const score=r=>r.axes.evidence*7+r.axes.terms*6+r.axes.access*4+r.axes.privacy*3;
const link=function link(url,label){return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;};
const renderReview=function renderReview(r) {
 const v=r.review;const axes=[["公开证据",v.axes.evidence,7],["免费条款",v.axes.terms,6],["接入门槛",v.axes.access,4],["隐私与控制",v.axes.privacy,3]];
 const bullets=(arr)=>arr.map(x=>`<li>${esc(x)}</li>`).join("");
 const sources=v.sources.map((s,i)=>`<li><div><span class="pub-proof-index">0${i+1}</span><strong>${esc(s.type)}</strong>：${link(s.url,s.title)}</div><p>${esc(s.note)}</p></li>`).join("");
 const result=score(v);
 return `<!doctype html>
<html lang="zh-CN" class="fl-pastel-ui">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(r.name)} 评测与免费条件｜FreeLLM 编辑审查</title>
<meta name="description" content="${esc(r.name)} 的 FreeLLM 独立编辑资料评估：评分依据、免费条件、官方证据、注意事项和未完成的 API 实测清单。">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://freellm.top/public-api/reviews/${esc(r.id)}/">
<link rel="stylesheet" href="/css/freellm-pastel-ui.css?v=20261013-overflow">
<link rel="stylesheet" href="/css/shared-navigation.css?v=20261001b">
<link rel="stylesheet" href="/css/aurora-core.css?v=20260924a">
<link rel="stylesheet" href="/css/aurora-public-api.css?v=20261015b">
<script defer src="/js/site-navigation.js?v=20261013-overflow"></script>
</head>
<body class="fl-ui-v2 public-api-page" data-fl-section="tools" data-visual-style="aurora">
<a class="pub-skip" href="#review-content">跳到评测内容</a>
<aside class="fl-site-rail" aria-label="FreeLLM 主导航"></aside>
<div class="fl-site-ribbon"><span class="fl-site-ribbon-title">FREE AI INDEX / EDITORIAL REVIEW</span><span class="fl-site-ribbon-actions"><a href="/public-api/">返回公益目录</a><a href="/submit/">报告更新 ↗</a></span></div>
<main class="pub-layout pub-review-detail" id="review-content">
<nav class="pub-breadcrumb" aria-label="面包屑"><a href="/">首页</a><span>/</span><a href="/public-api/">公益 API</a><span>/</span><span aria-current="page">${esc(r.name)}</span></nav>
<header class="pub-detail-hero"><div class="pub-detail-head"><div><p class="pub-kicker">FREELLM / EVIDENCE-BASED REVIEW · 2026-10-15</p><h1>${esc(r.name)}</h1><p class="pub-detail-verdict">${esc(v.verdict)}</p><p class="pub-detail-kind">${r.kind==="directory"?"第三方导航发现来源":"平台官方网站"} · 证据把握程度：${esc(v.confidence)} · 尚未实测 API</p></div><div class="pub-score-panel"><strong>${result}<small>/100</small></strong><span>公开资料编辑评分</span><small>不是服务稳定性评分</small></div></div>
<p class="pub-detail-opinion">${esc(v.opinion)}</p>
<div class="pub-detail-actions">${link(r.url,"打开目标网站")}<a href="/public-api/#how-we-review">查看统一评审方法 →</a></div></header>
<section class="pub-detail-summary" aria-label="结论概况">
<div><p class="pub-kicker">适合谁</p><p>${esc(v.audience)}</p></div><div><p class="pub-kicker">不推荐场景</p><p>${esc(v.avoid)}</p></div><div><p class="pub-kicker">免费方式</p><p>${esc(r.free)}</p></div></section>
<div class="pub-detail-columns"><div>
<section class="pub-detail-section"><p class="pub-kicker">01 / EDITORIAL VIEW</p><h2>为什么给这个分数？</h2><p>${esc(v.reason)}</p><div class="pub-score-axes">${axes.map(([name,n,weight])=>`<div class="pub-axis"><div><b>${esc(name)}</b><span>${n}/5 · ${n*weight} / ${5*weight} 分</span></div><div class="pub-axis-track"><i style="width:${n*20}%"></i></div></div>`).join("")}</div><p class="pub-footnote">公式：证据×7 + 免费条款×6 + 接入门槛×4 + 隐私控制×3。维度以公开可读资料为依据；低分不意味着已证实存在安全问题。</p></section>
<section class="pub-detail-section"><p class="pub-kicker">02 / FACT CHECK</p><h2>资料证实了什么？</h2><ul class="pub-check-list">${bullets(v.known)}</ul></section>
<section class="pub-detail-section"><p class="pub-kicker">03 / OPEN QUESTIONS</p><h2>我们还不知道什么？</h2><ul class="pub-unknown-list">${bullets(v.unknown)}</ul></section>
<section class="pub-detail-section"><p class="pub-kicker">04 / PRACTICAL STEPS</p><h2>建议怎样验证？</h2><ol class="pub-steps">${bullets(v.steps)}</ol></section>
</div><aside class="pub-detail-aside"><section><p class="pub-kicker">SOURCES / EVIDENCE</p><h2>原始证据</h2><ul class="pub-sources">${sources}</ul><p class="pub-footnote">本站资料核查日期：2026-10-15。所列来源的内容可能随时更改，链接由对应网站负责。</p></section><section><p class="pub-kicker">PROBE STATUS</p><h2>API 实测门禁</h2><dl><div><dt>持密钥实测</dt><dd>未执行</dd></div><div><dt>成功率 / 延迟</dt><dd>UNKNOWN</dd></div><div><dt>模型真实性</dt><dd>UNKNOWN</dd></div><div><dt>用量扣费与配额</dt><dd>UNKNOWN</dd></div><div><dt>证据方法</dt><dd>公开网页资料审查</dd></div></dl><p class="pub-footnote">点击网页成功不能证明接口可用；不应把本文 0–100 的资料分当作在线 SLA。</p></section></aside></div>
<section class="pub-detail-next"><h2>下一步怎么选？</h2><p>如果是练习调用，优先查看有清晰官方额度说明的平台；如果是社区发现，先核验条款再做真实请求。</p><div><a href="/public-api/">返回全部资源 ←</a><a href="/submit/">提交纠错或新证据 ↗</a></div></section>
</main>
<footer class="pub-footer"><span>FreeLLM / 编辑评估 ≠ 实测结果</span><nav aria-label="相关链接"><a href="/public-api/">公益目录</a><a href="/about/">审核方法</a><a href="/privacy/">隐私</a></nav></footer>
<script src="/js/freellm-sync.js?v=20261012-daily-discovery"></script>
</body></html>
`;
};
const renderCard=function renderCard(r,i) {
 const v=r.review,kind=r.kind;return `<article class="pub-card" data-kind="${esc(kind)}" data-score="${score(v)}" data-search="${esc([r.name,r.label,r.description,r.free,v.verdict,v.opinion].join(" ").toLowerCase())}">
<div class="pub-card-head"><span class="pub-num">${String(i+1).padStart(2,"0")} / RESOURCE</span><span class="pub-status ${kind==="directory"?"pub-status-review":"pub-status-official"}">${esc(r.status)}</span></div>
<div class="pub-type">${esc(r.label)}</div><h3>${esc(r.name)}</h3>
<p class="pub-summary">${esc(r.description)}</p>
<div class="pub-editorial"><strong>${score(v)}<small>/100</small></strong><div><b>FreeLLM 编辑资料评分</b><span>${esc(v.verdict)}</span></div></div>
<dl><div><dt>免费方式</dt><dd>${esc(r.free)}</dd></div><div><dt>使用前确认</dt><dd>${esc(r.requirement)}</dd></div></dl>
<div class="pub-card-actions"><a class="pub-action" href="/public-api/reviews/${esc(r.id)}/">看我们的评测 <span aria-hidden="true">→</span></a><a class="pub-evidence" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">官方/原站 ↗</a></div>
</article>`;
};
const registry=JSON.parse(fs.readFileSync(path.join(root,"data/public-api-directory.json"),"utf8"));
const check=process.argv.includes("--check");
if(registry.resources.length!==6)throw Error("Update display counts when resource count changes");
let stale=0;
function write(rel,contents){
 const full=path.join(root,rel);
 if(check){
  if(!fs.existsSync(full)||fs.readFileSync(full,"utf8")!==contents){console.error("STALE "+rel);stale++;}
 }else{fs.mkdirSync(path.dirname(full),{recursive:true});fs.writeFileSync(full,contents);}
}
for(const r of registry.resources){
 if(!/^[-a-z0-9]+$/.test(r.id))throw Error("unsafe review id");
 if(!r.review||r.review.score!==score(r.review)||r.review.liveProbe!=="not_performed")throw Error("invalid or stale score: "+r.id);
 write("public-api/reviews/"+r.id+"/index.html",renderReview(r));
}
const directory="public-api/index.html";
const original=fs.readFileSync(path.join(root,directory),"utf8");
const first="<!-- PUBLIC_API_CARDS_START -->";
const last="<!-- PUBLIC_API_CARDS_END -->";
if(!original.includes(first)||!original.includes(last))throw Error("missing card delimiters");
const before=original.split(first)[0],after=original.split(last)[1];
const expected=before+first+"\n"+registry.resources.map(renderCard).join("\n")+"\n"+last+after;
write(directory,expected);
if(stale)process.exitCode=1;
else console.log(check?"Public API pages consistent":"Public API pages generated");
