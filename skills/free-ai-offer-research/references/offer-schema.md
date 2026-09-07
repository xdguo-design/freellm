# Offer 字段规则

| 字段 | 规则 |
|---|---|
| `productType` | `free_ide`、`api`、`coding_plan`、`open_weights`、`payg`、`web_infrastructure` |
| `capabilities` | `search`、`fetch`、`extract`、`crawl`、`map`、`browser`、`agent`、`model_api`、`free_ide`、`open_weights`；至少一个 |
| `pricingModel` | `permanent_free`、`monthly_quota`、`daily_quota`、`weekly_quota`、`free_rate_limited`、`free_credits`、`trial`、`limited_time_free`、`payg`、`metered_paid`、`not_confirmed` |
| `limits` | 结构化限频、额度、并发和会话时长；未知值使用 `null`，数值字段必须带单位 |
| `billing` | `walletRequired`、`cardRequired`、`autoReload`、`overageBehavior` 和单位价格列表 |
| `freeMechanism` | `permanent`、`monthly_quota`、`daily_quota`、`weekly_quota`、`trial`、`first_month_promo`、`limited_time_free`、`open_weights`、`not_confirmed` |
| `status` | `verified`、`changed`、`expired`、`unavailable`、`needs_review` |
| `confidence` | `high`、`medium`、`low` |
| `phoneRequired` / `cardRequired` | `yes`、`no`、`unknown` |
| `officialActionUrl` / `register` | 官方注册、产品、下载或模型卡地址；必须是 HTTPS |
| `sourceUrls` | 官方价格页、FAQ、文档或模型仓库；至少一个 |
| `evidence` | 与结论直接相关的短证据摘要 |
| `usageGuide` | 所有正式 Offer 必填；必须有前置条件、至少两步、官方文档链接和可执行示例/操作命令 |

## 分类判断

- `free_ide`：免费能力主要通过 IDE、插件、CLI 或编辑器套餐提供。
- `api`：直接调用模型的 API，不因为网页端免费而自动免费。
- `coding_plan`：Coding Plan、首月活动或按时间窗口计费的编码产品。
- `open_weights`：权重可下载，但运行资源单独计算。
- `payg`：没有免费额度，但单位价格较低，必须单独标记。
- `web_infrastructure`：Search、Fetch、Extract、Crawl、Map、Browser 或 Agent 等网页能力；同一产品的不同免费/付费规则拆为不同 Offer。

## 如何使用说明

所有公开条目都必须回答“如何开通、如何调用或安装、如何避免超额”。API 类至少提供一个可复制的 `curl`、Python 或 JavaScript 示例；IDE 提供下载、登录和额度查看步骤；开放权重提供下载、硬件要求和本地启动命令；Browser/Agent 提供会话或任务生命周期、计费单位和停止方式。示例不得包含省略号、TODO、真实 Token 或私有 URL。
