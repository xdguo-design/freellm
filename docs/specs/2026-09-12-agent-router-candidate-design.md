# Agent Router 待审核候选设计

## 目标

将 Agent Router 作为一个可追踪、可复查的免费 API 线索纳入发现体系，同时保留“第三方 README 声称”与“官方页面已核验”的边界。今天生成 2026-09-12 的扫描和变更记录。

## 当前证据与边界

- `https://agentrouter.org/` 是注册与服务入口，但当前抓取返回 WAF 页面，无法从官方页面确认奖励金额、完整模型清单和调用限制。
- `https://github.com/justbiar/agent-router` 的 README 声称存在 Claude Opus 5、Claude Opus 4.8、GPT-5.6 Sol 等模型以及注册/登录奖励；该仓库只作为 GitHub peer 发现证据，不作为官方免费政策证据。
- 不执行 README 中的代理脚本，不保存 API key，不把 Agent Router 写入已核验的 `data/offers.json`。

## 数据流

1. 在 `data/providers.json` 注册 `agent-router` 的官方域名和入口，供官方来源扫描。
2. 在 `data/github-peers.json` 注册 `justbiar/agent-router`，供受限 GitHub 文档扫描。
3. 扫描结果进入 `data/candidates.json`，状态为 `needs_review`；候选记录保留仓库、路径、commit SHA、官方链接和提及模型。
4. 生成 `data/daily-log/2026-09-12.json`，记录今天的模型扫描结果、Offer 快照变化和来源健康状态。
5. 只有后续取得官方定价/活动/文档证据后，才创建正式 Offer 和静态详情页。

## 验收标准

- Agent Router 不出现在 `data/offers.json` 的正式 Offer 列表中。
- Agent Router 出现在候选队列，`status` 为 `needs_review`，且来源类型区分为 `github_peer` 或官方来源扫描结果。
- 今日扫描产出日期为 `2026-09-12` 的模型快照、发现快照、覆盖报告和每日日志。
- 现有 schema、单元测试、静态构建检查通过；工作区保留用户已有的 Groq 截图。
