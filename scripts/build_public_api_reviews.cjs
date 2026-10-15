#!/usr/bin/env node
/* Regenerate curated editorial review pages and the directory cards from the audited JSON.
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
 const userFeedback = r.id === "hcnsec-gateway" ? '<section class="pub-feedback" aria-label="用户确认可用"><strong>1 条用户确认已调用成功</strong><p>用户提供的真实使用反馈；尚未提供模型、日志或发生日期，不计入平台自动探针成功率，也不能推导全站稳定性。</p></section>' : "";
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
${r.id === "hcnsec" ? "<section class=\"pub-detail-section pub-gateway-guide\"><p class=\"pub-kicker\">GATEWAY / FROM DIRECTORY TO API</p><h2>它的「导航」与「自营 API 网关」是两回事</h2>\n<p>导航域名 <code>link.hcnsec.cn</code> 主要用于发现其他站点；<code>api.hcnsec.cn</code> 是同一运营方对外提供的中转 API。后者的说明只能算<strong>站方自述</strong>，不能用来证明被导航收录的其他站点安全稳定。</p>\n<div class=\"pub-gateway-fields\"><div><b>文档 Base URL</b><code>https://api.hcnsec.cn/v1</code></div><div><b>实际请求路径</b><code>/v1/chat/completions</code></div><div><b>文档示例模型别名</b><code>DeepSeek-V4-Pro</code></div><div><b>文档密钥流程</b><span>控制台「密钥」→ 创建令牌 → 默认 auto 分组</span></div></div>\n<h3>出现调用错误时，先查这几项</h3><ol class=\"pub-steps\"><li>确认在自营网关创建的是 <code>sk-</code> 令牌，客户端提供正确的 Bearer 头；不要将真实密钥发给任何导航或评价网站。</li><li>检查客户端是否重复追加 <code>/v1</code> 或拼错 <code>/chat/completions</code>。</li><li>检查请求中的模型别名是否存在于<strong>该网关当前模型列表</strong>，而不是照抄其他平台的模型 ID。</li><li>如果返回 401，先看令牌；403 优先核对免费 / svip 分组权限；429 可能触发令牌或全站流控，具体以返回体为准。</li><li>即使文档宣称「1300+ 上游」或「不存储对话用于训练」，也不能据此认定其上游真实性、个人数据处理措施已经经过独立审计。</li></ol>\n<p class=\"pub-footnote\">来源：<a href=\"https://api.hcnsec.cn/free-api/tutorials/curl/\" target=\"_blank\" rel=\"noopener noreferrer\">站方 curl 文档 ↗</a> · <a href=\"https://api.hcnsec.cn/free-api/faq/\" target=\"_blank\" rel=\"noopener noreferrer\">站方 FAQ ↗</a>。以上是排查路线，不代表 FreeLLM 已取得账号、持密钥成功调用或验证网关隐私承诺。</p></section>\n" : ""}${userFeedback}
${r.id === "hcnsec-gateway" ? "<section class=\"pub-detail-section pub-gateway-guide\"><p class=\"pub-kicker\">QUICK START / 安全接入</p><h2>从注册到第一条成功响应</h2>\n<ol class=\"pub-steps\"><li>在 <a href=\"https://api.hcnsec.cn/dashboard/overview\" target=\"_blank\" rel=\"noopener noreferrer\">控制台 ↗</a> 注册，进入密钥页创建 API Key，核对 auto 分组。</li><li>确认当前模型广场标明免费层的模型别名，不要把 svip 模型误认作免费。</li><li>把令牌仅保存在自己的本地环境变量，使用最小无敏感内容请求。</li><li>HTTP 200 且 JSON 包含 choices 的有效回复，才算一次调用成功；不要仅凭网页能够打开就认定 API 可用。</li></ol>\n<h3>Python 最小调用示例</h3>\n<pre><code>import os\nfrom openai import OpenAI\n\nclient = OpenAI(\n    api_key=os.environ[\"HCNSEC_API_KEY\"],\n    base_url=\"https://api.hcnsec.cn/v1\",\n)\nresult = client.chat.completions.create(\n    model=\"DeepSeek-V4-Pro\",\n    messages=[{\"role\": \"user\", \"content\": \"只回复 OK\"}],\n    max_tokens=8,\n)\nprint(result.choices[0].message.content)</code></pre>\n<p class=\"pub-footnote\">先安装 <code>pip install openai</code> 并在本地设置 <code>HCNSEC_API_KEY</code>。示例模型为运营方文档别名，须以个人控制台当前可调用列表为准。本站不要求你上传密钥。</p>\n<h3>为什么不是稳定性五星？</h3><p>这次用户已经确认好用，是一条积极且有用的真实体验。要升级到可量化成功率，我们还需要跨时段的可复现请求记录，并记录 401/403/429、超时、余额扣减等信息。</p></section>" : ""}
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
if(registry.resources.length!==7)throw Error("Update display counts when resource count changes");
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
