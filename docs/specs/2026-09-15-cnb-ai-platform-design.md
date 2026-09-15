# CNB AI 平台收录设计

## 目标

将 `cnb.cool` 作为独立的 AI 代码协作平台收录，并在 2026-09-15 的每日更新中记录。

## 范围

- 新增一个 verified offer：CNB · Cloud Native Build AI。
- 记录 CNB 代码托管、Issue/PR、WebIDE 内置 CodeBuddy、CodeBuddy NPC、AI 问答、问题分析和变更分析能力。
- 新增 CNB 的操作指南，提供官方入口和 AI 功能验证步骤。
- 使用现有静态生成流程更新 offer 详情页、分类/指南索引、schema、README 和每日日志。

## 数据决策

- `productType`: `free_ide`，因为 CNB 的 AI 编程入口通过 Workspaces WebIDE 提供。
- `freeMechanism`: `permanent`，仅描述官方页面已确认的免费/内置入口，不推断额外额度。
- 独立 ID：`cnb-ai`，避免与独立 CodeBuddy 产品重复。
- 证据来源：CNB AI 助手官方文档和 CNB 官方站点。

## 验收标准

- `data/offers.json` 和 `data/operations/cnb-ai.json` 通过 schema 校验。
- 生成 `/offers/cnb-ai/` 页面，且 CNB 出现在免费 IDE/AI 编程相关索引中。
- `data/daily-log/2026-09-15.json` 记录新增 CNB 条目。
- 相关静态构建测试通过。
