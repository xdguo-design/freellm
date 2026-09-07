# 阶段交接契约

每个阶段输出以下结构化摘要：

| 字段 | 要求 |
|---|---|
| `stage` | 当前阶段名称 |
| `inputs` | 实际读取的文件、URL 或用户选择 |
| `outputs` | 写入的文件、记录数和关键字段 |
| `evidenceLevel` | `official_primary` / `project_primary` / `peer_discovery` / `community_signal` |
| `status` | `complete` / `needs_review` / `source_unavailable` / `blocked` |
| `failures` | 失败 URL、原因和是否可重试 |
| `nextAction` | 下一阶段的一个明确动作 |
| `userGate` | `none` / `design_approval` / `prototype_choice` / `publish_approval` |

## 交接规则

- `peer_discovery` 不得直接升级为 `official_primary`。
- `community_signal` 不得改变 offer 的 `status`、`confidence`、quota 或 validity。
- 失败源保留在失败列表，不删除既有成功记录。
- 每次数据快照都带时间；仓库文档额外带 repository、path、commitSha。
- 页面交接必须列出数据来源、空状态、键盘/移动端行为和回滚文件。
- 有用户门控时停止在门控前，不能用默认答案代替用户选择。
