# Offer 字段规则

| 字段 | 规则 |
|---|---|
| `productType` | `free_ide`、`api`、`coding_plan`、`open_weights`、`payg` |
| `freeMechanism` | `permanent`、`monthly_quota`、`daily_quota`、`weekly_quota`、`trial`、`first_month_promo`、`limited_time_free`、`open_weights`、`not_confirmed` |
| `status` | `verified`、`changed`、`expired`、`unavailable`、`needs_review` |
| `confidence` | `high`、`medium`、`low` |
| `phoneRequired` / `cardRequired` | `yes`、`no`、`unknown` |
| `officialActionUrl` / `register` | 官方注册、产品、下载或模型卡地址；必须是 HTTPS |
| `sourceUrls` | 官方价格页、FAQ、文档或模型仓库；至少一个 |
| `evidence` | 与结论直接相关的短证据摘要 |

## 分类判断

- `free_ide`：免费能力主要通过 IDE、插件、CLI 或编辑器套餐提供。
- `api`：直接调用模型的 API，不因为网页端免费而自动免费。
- `coding_plan`：Coding Plan、首月活动或按时间窗口计费的编码产品。
- `open_weights`：权重可下载，但运行资源单独计算。
- `payg`：没有免费额度，但单位价格较低，必须单独标记。
