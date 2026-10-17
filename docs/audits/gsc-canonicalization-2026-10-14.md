# Google Search Console 实测与规范域名修复（2026-10-14）

数据源：GSC Wizard 查询 `sc-domain:freellm.top`，Web 搜索，2026-09-14—2026-10-11（28 个已结算日，Google 使用 America/Los_Angeles 日期边界）。数据快照时间：2026-10-14。

## 确认的数据

- 3 clicks、393 impressions、CTR 0.763%、平均展示排名 7.30；上一可比 28 天点击 0、曝光 59。流量样本极少，CTR 排名波动不能外推。
- 首页 freellm.top/：1 点击、275 曝光；www 首页：1 点击、40 曝光。由于一个 Google 查询可能展示多个同站 URL，按页面聚合的曝光之和不能强制等于域名总曝光。
- /offers/agnes-ai-free/：37 曝光、0 点击、平均排名 19.54；/offers/openrouter-free/：10 曝光、0 点击、平均排名 6.2；/offers/volcengine-ark-new-user-500k/：9 曝光、0 点击、平均排名 6.78。
- sitemap-offers.xml 有 78 个 URL，其中最近 28 天 17 个获得 Search Console 曝光；**不是**只收录了 17 个。
- Search Console Sitemap 汇总曾显示 indexed 0，但 URL Inspection 实测首页、Agnes、OpenRouter、火山引擎、kimi-k3 等状态为“Submitted and indexed”，因此不能把该汇总简单表述为“全站零收录”。
- URL Inspection：freellm.top/ 与 www.freellm.top/ 都曾被 Google 分别标记为“Submitted and indexed”，并各自返回自我规范网址。www 最近抓取为 2026-09-07、主站为 2026-09-28，所以当前页面上的 canonical 与 Google 的旧快照可能不同。
- /guides/free-llm/：Google 状态“Discovered - currently not indexed”；无 last crawl / Google canonical，不能宣称它被内容质量处罚。

## 本轮部署改动

`vercel.json` 为仅 host=www.freellm.top 的请求新增永久 308 重定向至 `https://freellm.top/:path*`，其他 host 不匹配此规则；旧的路径级跳转继续保留。这是用于统一重复 URL 的强信号，具体排名和 Google 重新归一化需要等待爬虫重新抓取，不保证短期效果。

## 验收

- `tests/test_canonical_host_redirect.py` 验证跳转目标、host 限制、永久性以及规则先后位置。
- 浏览器 CI 和全仓库单元测试通过之前不得合并生产。
- 部署后通过真实 HTTP 请求验证 `https://www.freellm.top/` 和任意 `https://www.freellm.top/offers/.../` 的 308 Location，再检查 Google 后续抓取。Vercel 官方文档提示：条件 `has` 在 `vercel dev` 中不可准确本地模拟，最终以生产部署行为为准。

## 内容复核与 AdSense 的关系

下一步优先跟进未索引教程页和有曝光却无点击的详情页，依据真实搜索意图补充原创对比、接入步骤、官方来源和地区/额度限制；不要大规模批量生产薄内容。此轮 SEO 数据与规范域名修复不能推断 AdSense 未获批的真实审核原因。广告是否可展示依赖 AdSense 账号的独立审核和后台配置。

Google 官方：https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
Vercel 官方：https://vercel.com/docs/project-configuration/vercel-json
