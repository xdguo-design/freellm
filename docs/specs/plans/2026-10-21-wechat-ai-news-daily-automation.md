# 微信公众号 AI 新闻日报自动化（每日采集 → 相关性筛选 → 二级文章 → 测试发版）实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行，批次节点与用户确认。任务使用 `- [ ]` 跟踪，先写失败测试再实现。本计划横跨两个仓库：**freellm**（网站与管线主体）与 **octop-src**（平台定时任务与编排），任务标题已标注所属仓库。

**目标：** 每天定时采集微信公众号近 3 天的 AI 新闻，按 freellm.top 站点主题（免费 LLM / API 额度 / 模型发布 / AI 工具）做相关性筛选；命中的新闻自动生成一篇中文二级文章页（`/news/YYYY-MM-DD/`）并入站；经全量自动化测试门禁后提交 dev 分支，CI 全绿即发版到 main，由 Vercel 自动部署。Octop 平台提供每日定时触发、幂等补跑与日报送达。

**对"二级文章"的界定（假设，需确认）：** 二级文章 = 站点首页之外的子页面文章。本计划落地为新建 `/news/` 区块（列表页 + 每日一篇详情页），复用现有 pastel 设计系统与页面壳，而非并入 `/logs/`（那是官方来源数据日志，性质不同）。

**非目标：**
- 不全文转载公众号原文（版权风险）；文章只做摘要、观点归纳与外链，每条必须带来源（公众号名 + 原文链接 + 发布时间）
- 不修改 offers / models / providers 主数据管线（日报是独立内容层，不参与 ranking / eval）
- 不直接抓取 `mp.weixin.qq.com`、不接验证码打码（微信反爬红线）；只消费标准 RSS
- v1 不做英文版日报、不做邮件/短信推送（只走 Octop 已配置的 IM 渠道）
- v1 不自建 WeRSS / 微信读书服务（用公共 RSS 源；覆盖不足再评估）

**架构要点：**

三层分离，调度与内容生产解耦：

```
Octop 平台（octop-src）                      freellm 仓库（GitHub Actions）              线上
┌────────────────────────────┐   dispatch   ┌──────────────────────────────────┐  push   ┌─────────────┐
│ cron: freellm-news-daily   │ ───────────► │ wechat-news.yml                  │ ─────► │ Vercel      │
│  每天 08:00 Asia/Shanghai  │              │  1. wechat-scan   采集近3天RSS   │  main   │ freellm.top │
│  agent + GitHub 连接器     │ ◄─────────── │  2. relevance     相关性评分      │  自动    └─────────────┘
│  中文日报送达用户 IM        │   状态/报告   │  3. generate       LLM 写文章JSON │  部署
└────────────────────────────┘              │  4. build_news     渲染 /news/    │
        ▲ 12:00 schedule 兜底（幂等）        │  5. gates          全量测试门禁   │
        └────────────────────────────────── │  6. commit → dev → PR → main      │
                                           └──────────────────────────────────┘
```

- **数据契约**：`data/news/YYYY-MM-DD.json` 是每篇日报的唯一事实来源；页面由 `scripts/build_news_pages.py` 模板化渲染，禁止 LLM 直接产 HTML
- **幂等**：同一天重复运行检测到 `data/news/<当天>.json` 已存在即跳过；workflow 设 `concurrency` 组防重入
- **失败闭环**：任一环节失败不出文章、不提交、不发版；失败原因随日报送达用户
- **证据门禁**：每条新闻必须带公众号名、原文链接、发布时间；LLM 输出必须通过 schema 校验与来源引用检查，否则整篇放弃

**技术栈：** Python 3.11/3.12 标准库（RSS 用 `xml.etree.ElementTree`，HTTP 用 `urllib`，与现有 `crawler/` 一致）、JSON、GitHub Actions（ubuntu-latest）、现有测试体系（`python -m unittest discover -s tests -v` + `pytest` + `node --test`）。

**关联文档：** `docs/specs/2026-09-10-daily-change-log-design.md`（每日日志先例）、`.github/workflows/daily-log.yml` / `daily-check.yml` / `discovery-pr.yml`（工作流先例）、`tests/test_daily_check_workflow.py`（workflow 契约测试先例）。

---

## 关键决策（已按推荐方案写入计划，执行前请确认）

| # | 决策点 | 推荐方案 | 备选 |
|---|---|---|---|
| D1 | 调度归属 | **双触发**：Octop cron 每天 08:00（Asia/Shanghai）`workflow_dispatch` 触发 + GH Actions 自带 12:00 `schedule` 兜底；workflow 内按日期幂等，本地 Octop 不在线时不丢任务 | A：仅 GH Actions schedule（Octop 只做日报送达，最简）；B：仅 Octop cron（本地关机即断更，不推荐） |
| D2 | 公众号源 | wechat2rss.xlab.app 免费公共源（约 400 个技术/AI 账号，收录延迟约 6 小时），Task 0 验证目标账号可订阅性后定稿清单 | 自建 WeRSS（Docker 一键，需微信扫码授权，可订任意账号，多一台服务器成本） |
| D3 | LLM 写文章 | workflow 内调 LLM API（复用仓库已有 secret：`SILICONFLOW_API_KEY` 或 `ZHIPU_API_KEY`，中文内容友好），schema 强校验 + 失败不出文章 | Octop agent 用平台 LLM 生成后经 GitHub API 提交（链路更长，且依赖本地在线） |
| D4 | 发版门槛 | dev 全量门禁绿 → 自动 PR（dev→main）→ 轮询 dev 上 daily-check 绿 → `gh pr merge --squash`；日后可开分支保护改 `--auto` | 人工确认 PR 后合并（更稳但非全自动） |
| D5 | 文章落地位置 | 新建 `/news/YYYY-MM-DD/` 详情页 + `/news/` 列表页；入口放 `/logs/` 页首（**实施时调整**：主侧栏已 8 项且导航计数测试仍在修复中，v1 不再加第 9 项，改用 `/logs/` 页首入口 + sitemap + feed） | 并入 `/guides/`（体裁是日报不是教程，不建议） |

---

## 数据契约

**`data/wechat-news-sources.json`**（源注册表，新建）：

```json
[
  {
    "id": "jiqizhixin",
    "account": "机器之心",
    "feedUrl": "https://wechat2rss.xlab.app/feed/<hash>.xml",
    "tags": ["AI", "研究"],
    "enabled": true
  }
]
```

**`data/news-digest/YYYY-MM-DD.json`**（中间产物，含评分审计，新建）：

```json
{
  "schemaVersion": 1,
  "date": "2026-10-22",
  "windowDays": 3,
  "sources": [{"id": "jiqizhixin", "status": "ok", "items": 12, "error": null}],
  "items": [
    {
      "newsId": "jiqizhixin:<url-hash>",
      "title": "原标题",
      "account": "机器之心",
      "publishedAt": "2026-10-21T20:00:00+08:00",
      "url": "https://mp.weixin.qq.com/s/...",
      "description": "RSS 摘要或全文片段",
      "score": 5,
      "matchedEntities": ["DeepSeek", "deepseek-v4"],
      "matchedKeywords": ["免费", "API"],
      "decision": "accept"
    }
  ],
  "rejected": [{"newsId": "...", "score": 1, "reason": "below_threshold"}]
}
```

**`data/news/YYYY-MM-DD.json`**（日报，唯一事实来源，新建）：

```json
{
  "schemaVersion": 1,
  "date": "2026-10-22",
  "slug": "2026-10-22",
  "titleZh": "AI 日报 · 2026-10-22：DeepSeek 新模型免费额度再扩容",
  "summaryZh": "两三句话概括今日要点",
  "items": [
    {
      "newsId": "jiqizhixin:<url-hash>",
      "title": "原标题",
      "account": "机器之心",
      "publishedAt": "2026-10-21T20:00:00+08:00",
      "url": "https://mp.weixin.qq.com/s/...",
      "summaryZh": "两到四句中文摘要（归纳，非复制）",
      "tags": ["模型发布"],
      "relatedLinks": [{"label": "DeepSeek 模型目录", "url": "/models/"}]
    }
  ],
  "digestRef": "data/news-digest/2026-10-22.json",
  "generatedBy": "siliconflow/deepseek-v3",
  "createdAt": "2026-10-22T00:05:00Z"
}
```

---

## 任务分解

### Task 0（freellm）：公众号源可用性 Spike（0.5 天）

- [ ] 列出候选 AI 公众号 10-15 个：机器之心、新智元、量子位、智东西、PaperWeekly、甲子光年、晚点 LatePost、APPSO、 Founder Park、AI 前线等
- [ ] 逐个在 wechat2rss.xlab.app 验证 RSS 可订阅，记录：feed URL、最近文章条数、时间字段格式与是否精确到发布时刻、全文/摘要模式、收录延迟
- [ ] 验证 GitHub Actions runner 可访问这些 feed（本机有代理，CI 没有，必须实测）
- [ ] 定稿 `data/wechat-news-sources.json`；不可订阅账号记入"自建评估清单"附录
- **验证：** 每个源 `curl -sI <feed>` 返回 200 且 body 为合法 XML；结论写入本计划附录

### Task 1（freellm）：RSS 采集器 + 单测

**涉及文件：** 新建 `crawler/wechat_news.py`、`data/wechat-news-sources.json`、`tests/test_wechat_news.py`；修改 `crawler/cli.py`（新增 `wechat-scan` 子命令）

- [ ] **步骤 1：编写失败测试。** 源注册表校验（id 唯一、feedUrl 必须 https、enabled 为布尔）；RSS 2.0 / Atom 均解析出 title / link / pubDate / description；近 3 天窗口过滤（时间统一归一化到 Asia/Shanghai 比较）；按 (account, link) 去重；单源超时/畸形 XML 只记录不崩溃；feed 返回 HTML 错误页时不产出假条目
- [ ] **步骤 2：运行测试确认失败。** `python -m unittest tests.test_wechat_news -v`
- [ ] **步骤 3：最小实现。** 标准库 ElementTree + urllib；复用 `crawler/fetch.py` 的 DIRECT_OPENER 思路绕开本机代理；输出 `data/news-digest/<date>-raw.json`
- [ ] **步骤 4：CLI 联通。** `python -m crawler.cli wechat-scan --sources data/wechat-news-sources.json --out data/news-digest/<date>-raw.json --window-days 3`，对真实源跑通

### Task 2（freellm）：相关性评分 + 单测

**涉及文件：** 新建 `crawler/wechat_relevance.py`、`tests/test_wechat_relevance.py`

- [ ] **步骤 1：编写失败测试。** 命中站点实体（从 `data/models.json` / `providers.json` / `offers.json` 提取厂商与模型名）加分；主题关键词（免费/额度/API/价格/发布/开源/上下文/Agent/多模态，中英）加分；黑名单（招聘/广告/软文/课程贩售）命中即拒；阈值边界（score == 阈值通过、< 阈值拒绝）；空窗期输出空 digest 不报错；每条保留 `matchedEntities` 供内链
- [ ] **步骤 2：运行测试确认失败。** `python -m unittest tests.test_wechat_relevance -v`
- [ ] **步骤 3：最小实现。** 纯函数评分（无 IO），输入 raw JSON 输出 digest JSON（含 `rejected` 审计）；CLI 子命令 `wechat-score`
- [ ] **步骤 4：初值。** 阈值暂定 score≥3 且（≥1 实体命中 或 ≥2 主题词），Task 8 用真实数据校准

### Task 3（freellm）：LLM 文章生成 + schema 校验 + 单测

**涉及文件：** 新建 `scripts/generate_news_article.py`、`data/wechat-news-config.json`、`tests/test_generate_news_article.py`

- [ ] **步骤 1：编写失败测试。** digest 为空 → 不生成、退出码 0、有明确日志；LLM 返回缺字段/类型错/items 与 digest 不对应 → 拒绝；`items[].url` 必须原文回链（防幻觉编造）；`relatedLinks` 仅允许站内路径且目标页面/文件必须存在；`summaryZh` 长度超限 → 拒绝；重试一次仍失败 → 整篇放弃、不写文件
- [ ] **步骤 2：运行测试确认失败。** `python -m unittest tests.test_generate_news_article -v`（LLM 调用打桩，不发出真实请求）
- [ ] **步骤 3：最小实现。** 读 digest → 构造中文 prompt（角色：freellm.top 编辑；要求摘要+归纳+内链建议；明令禁止大段复制原文、禁止编造链接与数字）→ 调 LLM（env `NEWS_LLM_BASE_URL` / `NEWS_LLM_API_KEY` / `NEWS_LLM_MODEL`，默认 SiliconFlow 兼容端点 + deepseek-v3 或 qwen）→ 校验 → 写 `data/news/<date>.json`
- [ ] **步骤 4：prompt 版本化。** prompt 模板与阈值、黑名单一并放入 `data/wechat-news-config.json`

### Task 4（freellm）：`/news/` 页面渲染 + SEO + 单测

**涉及文件：** 新建 `scripts/build_news_pages.py`、`tests/test_news_pages.py`；生成 `news/index.html` 与 `news/YYYY-MM-DD/index.html`；修改 `js/site-navigation.js` 及页面壳模板（加"日报"导航入口）、`sitemap-pages.xml`、`feed.xml`、`scripts/check_internal_links.py`（识别新目录）、`scripts/build_static.py --check`（如需要）

- [ ] **步骤 1：编写失败测试。** 每篇日报渲染唯一 URL `/news/<date>/`；页面含 canonical / og / JSON-LD（`NewsArticle`）/ AdSense loader / 站点导航壳；条目卡片含来源名 + 原文外链（`rel="nofollow"` 或按站点外链惯例）+ 发布时间；`relatedLinks` 全部站内且目标存在；`news/index.html` 倒序列出全部日报；sitemap 与 feed 同步更新；`--check` 模式能发现被手改过的页面
- [ ] **步骤 2：运行测试确认失败。** `python -m unittest tests.test_news_pages -v`
- [ ] **步骤 3：最小实现。** 复用 guides 页壳（`css/freellm-pastel-ui.css` + `js/site-navigation.js` + Vercel insights + AdSense `ca-pub-2461062743308239`）；模板化渲染，`data/news/*.json` 驱动；单篇条目 < 3 时不出详情页（见 Task 8 空态规则）
- [ ] **步骤 4：全量校验。** `python scripts/build_news_pages.py --check`、`python scripts/check_internal_links.py` 全绿

### Task 5（freellm）：每日工作流 `wechat-news.yml`

**涉及文件：** 新建 `.github/workflows/wechat-news.yml`、`tests/test_wechat_news_workflow.py`（仿 `tests/test_daily_check_workflow.py`）

- [ ] **步骤 1：编写失败测试（YAML 契约）。** 同时含 `schedule`（兜底）与 `workflow_dispatch`（Octop 触发，带 `ref` 输入默认 dev）；`concurrency` 组存在且不 cancel 进行中的 run；steps 顺序为 scan → score → generate → render → gates → commit；checkout 恒为 `ref: dev`；存在幂等步骤（当天文章已存在则 skip 且退出 0）；任一步骤失败不 push
- [ ] **步骤 2：运行测试确认失败。** `python -m unittest tests.test_wechat_news_workflow -v`
- [ ] **步骤 3：实现。** 门禁复用现有：`python -m unittest discover -s tests -v`、`build_news_pages.py --check`、`check_internal_links.py`、`audit_all_pages.py`、`check_adsense.py`、`site_health.py`；通过后 `git push origin HEAD:dev`，commit message `content: AI 日报 YYYY-MM-DD`；随后 `gh pr create --base main --head dev`（已存在则复用），轮询 dev 上 daily-check run 结论，绿则 `gh pr merge --squash`，红则关 PR 并在日报中报告
- [ ] **步骤 4：dry-run。** `workflow_dispatch` 手动触发，用空 digest 验证"无命中零提交"路径与"有命中全链路"路径各一次

### Task 6（freellm）：发版衔接与门禁适配

- [ ] `daily-check.yml` 的 `paths` 增加：`data/news/**`、`data/wechat-news-sources.json`、`data/news-digest/**`、`news/**`、`crawler/wechat_news.py`、`crawler/wechat_relevance.py`、`scripts/build_news_pages.py`、`scripts/generate_news_article.py`、`data/wechat-news-config.json`、`.github/workflows/wechat-news.yml`
- [ ] 确认 Vercel 生产分支为 main（`vercel.json` 已设 `dev: false`，仅 main 部署）
- [ ] 与用户确认是否开启 main 分支保护（required status checks）；开启后 Task 5 的合并改 `gh pr merge --auto`
- [ ] 验证 revert 回退路径：main 出问题时可一键 revert 自动发版的提交

### Task 7（octop-src）：平台定时任务与日报送达

**涉及文件：** 无代码改动则为配置项；在 `docs/` 增加一页运行说明（cron id、agent、连接器、手动触发方式）

- [ ] 创建专用 agent（如 `freellm-news-bot`），绑定 GitHub 连接器（PAT 仅授 `repo` + `workflow` scope，且仅对 `xdguo-design/freellm` 授权；无 GitHub MCP 时用通用 HTTP 连接器调 GitHub REST API）
- [ ] 创建 cron job（trigger 用 UTC 写法，00:00 UTC = 08:00 Asia/Shanghai；`CronCreateSpec` 当前无 timezone 字段）：

```bash
octop cron create --agent freellm-news-bot --trigger "0 0 * * *" \
  --fresh-thread --task-type agent --prompt "<任务书全文>"
```

- [ ] **任务书（自包含，写入 prompt）：**

> 你是 FreeLLM（freellm.top）的新闻日报机器人。执行每日 AI 新闻日报流程：
> 1. 调用 GitHub API 对仓库 `xdguo-design/freellm` 的 dev 分支触发 `wechat-news.yml` 的 `workflow_dispatch`；
> 2. 轮询该 run 直到结束（单次等待不超过 30 分钟，超时按失败处理）；
> 3. 读取 run 结论与 step summary：今天扫描了哪些公众号源、近 3 天命中几条、相关性阈值拦掉几条、是否生成文章、文章 URL（`https://freellm.top/news/<日期>/`）、测试门禁各项结果、dev 提交与 PR/合并状态；
> 4. 用中文写一段不超过 300 字的日报发送到当前会话：先给结论（发文/未发文及原因），再列要点（命中新闻标题 + 一句话 + 来源公众号），最后给文章链接与门禁结果；未发文时说明原因（无命中/门禁失败/LLM 失败，附关键错误）；
> 5. 任何步骤失败都要明确报告失败点，不要静默，不要编造未发生的步骤。

- [ ] `octop cron run_now <cron_id>` 手动验证一次；模拟本地关机场景，验证 12:00 schedule 兜底补跑与幂等

### Task 8（端到端与校准）

- [ ] 连续 3 天观察：源稳定性、命中率、文章质量、门禁通过率、Vercel 部署结果
- [ ] 用真实数据校准相关性阈值与黑名单（宁缺毋滥：低质量日报伤 SEO 与 AdSense）
- [ ] 确认 `check_adsense.py` 对 `/news/` 无误伤；确定空态策略：当日无命中时不生成详情页，`/news/` 列表照常，日报 IM 里说明即可
- [ ] 运营指标（扫描源数/命中数/发文数/门禁失败次数）记入本计划附录

---

## 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| wechat2rss.xlab.app 限流/宕机/下架 | 采集中断 | Task 0 实测 + 多源注册表 + 失败不发文只报警；稳定运行后评估自建 WeRSS |
| 微信侧反爬变动导致公共源失效 | 同上 | 同上；freellm 永不直接抓微信页面，源失效可整体替换 |
| LLM 幻觉/编造链接 | 内容事故 | schema 强校验 + url 必须回链 digest + relatedLinks 仅站内存量路径；失败整篇放弃 |
| 日报内容过薄触发 AdSense/SEO 惩罚 | 站点受损 | 单篇至少 3 条命中才出详情页；接现有 `check_adsense.py` 门禁；`/news/` 空态不进 sitemap |
| 版权风险 | 法务 | 只摘要+归纳+外链；prompt 明令禁止大段复制；页面声明来源与发布时间 |
| 本地 Octop 关机 | 断更 | GH Actions 12:00 schedule 兜底 + 按日期幂等 |
| 自动发版事故 | 线上事故 | 全量门禁绿才 PR；合并前轮询 dev CI；revert 即可回退 |
| 日报与官方日志 `/logs/` 混淆 | 用户困惑 | `/news/` 独立区块 + 导航"日报"入口与"更新"并列区分 |

---

## 验收标准

1. `data/wechat-news-sources.json` 注册 ≥ 8 个可订阅 AI 公众号源，全部通过 Task 0 实测
2. 手动 `workflow_dispatch`：有命中时产出 `/news/<date>/` 页面、dev 提交、PR 创建并合并；无命中时零提交、日报说明原因
3. dev 上 `daily-check.yml` 全量门禁绿（含新增单测与 workflow 契约测试）
4. main 更新后线上 `https://freellm.top/news/` 可访问，页面结构、canonical、sitemap、feed 均合规
5. Octop cron 每天 08:00 触发，用户 IM 收到中文日报；`run_now` 可手动补跑；本地关机时 12:00 兜底生效
6. 连续 3 天无人值守运行无 P0 事故

## 里程碑

| 里程碑 | 内容 | 产出 |
|---|---|---|
| M0（0.5 天） | Task 0 spike + 决策 D1-D5 确认 | 源清单定稿、决策记录 |
| M1（2 天） | Task 1-4 采集/评分/生成/渲染 | 单测全绿，本地可跑通全链路 |
| M2（1 天） | Task 5-6 工作流与发版 | dry-run 通过，PR 链路打通 |
| M3（0.5 天） | Task 7 Octop cron + agent + 连接器 | 首次真实触发并收到日报 |
| M4（3 天） | Task 8 端到端校准 | 阈值/黑名单定版，转入日常运营 |

---

## 附录 A：源可用性实测记录（Task 0，2026-10-21 完成）

wechat2rss.xlab.app 列表页（`/list/all`）共 395 个公众号，其中 AI 相关 10 个已收录进 `data/wechat-news-sources.json`，全部实测可拉取（近 3 天窗口内共 46 条）：

| 公众号 | feed 可用 | 近 3 天条数 | 备注 |
|---|---|---|---|
| 机器之心 | 是 | 5 | 模型发布 / 产业 |
| 新智元 | 是 | 6 | 模型发布 / 论文 |
| 量子位 | 是 | 16 | 产品 / 产业 |
| 夕小瑶科技说 | 是 | 2 | 模型 / 开源 |
| PaperWeekly | 是 | 4 | 论文 / 开源 |
| Datawhale | 是 | 3 | 开源 / 教程 |
| 集智俱乐部 | 是 | 4 | 研究 / 复杂系统 |
| 机器学习初学者 | 是 | 0 | 更新频率低，保留观察 |
| 我爱计算机视觉 | 是 | 4 | CV / 论文 |
| 腾讯技术工程 | 是 | 2 | 工程 / 云 |

源格式：RSS 2.0 + `content:encoded` 全文、`pubDate` 为 RFC 2822（+0800，精确到分钟）、每源约 20 条、单源约 700 KB。抓取上限 4 MB / 源，15s 超时。

同一份 46 条的实测评分结果：接受 15 条、拒绝 31 条（黑名单命中 1 条：大会征集；其余为车企/财经/与站点无关的论文），阈值（score ≥ 3 且 ≥1 实体或 ≥2 关键词）与 `maxAcceptedItems = 15` 保持。

## 附录 B：实施状态（2026-10-21）

已完成并本地验证：

- Task 1 采集器 `crawler/wechat_news.py`（15 单测）
- Task 2 相关性评分 `crawler/wechat_relevance.py`（13 单测，真实数据校准过）
- Task 3 文章生成 `scripts/generate_news_article.py`（18 单测，LLM 打桩）
- Task 4 页面渲染接入 `scripts/build_seo_pages.py`（`/news/` 列表 + 详情 + `sitemap-news.xml` + feed + `--check`，15 单测；空态 noindex 且不带广告）
- Task 5 工作流 `.github/workflows/wechat-news.yml`（9 契约测试）+ daily-check paths 扩展
- Task 6 发版：workflow 提交目标 = 触发分支；schedule 落在默认分支、Octop dispatch 落在 dev

待办：

- Task 7 平台侧 cron：需要先给 Octop 配一个能调 GitHub 的连接器（GitHub PAT），步骤见 `octop-src/docs/freellm-wechat-news-cron.md`
- Task 8 端到端观察 3 天（阈值/黑名单校准、AdSense 表现）

已知遗留（**非本功能引入**，dev 分支既有）：

- `prompts/` 页面未提交（提示词库是未上线 WIP），但导航与 sitemap 已引用它 → `check_internal_links.py`、`check_adsense.py` 在 dev 上为红
- `test_p0_convergence.test_primary_navigation_has_exactly_seven_items` 与 `test_e2e_static.test_mobile_navigation_keeps_core_directory_entries_visible` 断言侧栏 7 项，实际生成 8 项（提示词入口）→ dev 上已失败
- 因此日报工作流的门禁按 news 范围设计（单元测试 + `--check` + news 页 audit + sitemap 解析），站点级门禁等 `prompts/` 落地后恢复
