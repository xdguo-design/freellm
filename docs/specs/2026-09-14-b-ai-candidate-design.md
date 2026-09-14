# BAI（b.ai）待审核候选设计

## 目标

将 BAI（b.ai）作为一个可追踪、可复查的免费额度线索纳入发现体系，保留"官方页面观察"与"已核验 Offer"的边界，并生成 2026-09-14 的扫描和变更记录。

## 当前证据与边界

- `https://chat.b.ai/chat?invite_code=U9ABB8` 是用户提供的邀请注册入口，页面标题为 "BAI"。邀请注册弹窗展示"邀请注册专属礼包：300,000 Credits"，登录方式含 Google。
- 站内可见模型入口：MiniMax-M3、Hunyuan Hy3（标记"限时免费"）、GLM 5.3 Flash（标记"1折"）；另有"充值即赠额外积分，最高 $100 等额奖励"的促销横幅。
- 侧边栏包含 API（/key）、用量、充值、订阅、邀请、模型排行等入口，表明其为对话 + API 网关形态，与 Agent Router 同类。
- 命令行抓取 `https://b.ai/` 与邀请页在 8 秒超时内均失败（curl 15 秒亦超时），因此官方来源扫描状态为 `failed`；候选证据来自真实浏览器打开页面的观察，仍属待核验。
- 不保存任何 API key，不执行邀请/注册流程，不把 BAI 写入已核验的 `data/offers.json`；邀请码仅作为发现证据保存在候选队列。

## 数据流

1. 在 `data/providers.json` 注册 `b-ai` 的官方域名（`b.ai`）和入口（首页 + 邀请页），供官方来源扫描。
2. 候选进入 `data/candidates.json`，`status=needs_review`、`sourceKind=official`，保留官方链接和提及模型（minimax-m3、hunyuan-hy3、glm-5.3-flash）。
3. 生成 2026-09-14 的模型快照（293 条）、发现快照（231 条来源）、覆盖报告（89/231 健康）与每日日志（3 条新增模型）。
4. 只有后续通过官方页面核验积分政策、调用限制和模型清单后，才创建正式 Offer 和静态详情页。

## 验收标准

- BAI 不出现在 `data/offers.json` 的正式 Offer 列表中。
- BAI 出现在候选队列，`status` 为 `needs_review`，来源类型为 `official`，官方来源扫描失败被如实记录为不可用来源，不升级为已核验条目。
- 今日扫描产出日期为 `2026-09-14` 的模型快照、发现快照、覆盖报告和每日日志；`data/models.json` 同步为 302 条（3 new / 290 current / 9 stale）。
- 现有 schema、单元测试（245 passed, 11 skipped）、静态构建检查（build_static / build_seo_pages --check）通过。
