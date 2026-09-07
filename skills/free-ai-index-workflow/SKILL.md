---
name: free-ai-index-workflow
description: "编排 Free AI Index 的完整研究、核验、外部信号、视觉设计、开发审查和发布流程；触发词：免费模型工作流、AI 目录流程、串联 skill、研究流水线、GitHub 同类扫描、官方额度核验、外部评分搬运、网站风格参考、页面改版、发布门控、workflow orchestration、research pipeline、release gate、evidence workflow。"
---

# Free AI Index Workflow

铁律：每个阶段只能消费上游明确交付的产物；GitHub 和社区内容只能提供线索，未通过官方核验的内容保持 `needs_review`，不自动发布、不自评分、不跨平台换算。

## 工作流

- [ ] 第一步：需求设计
  - 新功能、页面行为或数据规则先使用 `brainstorming`，明确目标、非目标、接口、成功标准和用户确认点。
  - 已有设计获确认后，使用 `writing-plans` 形成路径、命令、验收标准和门控；不要跳过设计直接改生产文件。
- [ ] 第二步：同行发现
  - 使用 `github-peer-discovery` 扫描指定仓库和同类项目，读取受限公开文档，产出仓库/路径/commit provenance、模型/Provider 线索和风格观察。
  - 产物只能进入发现报告或候选队列，来源标记 `sourceKind=github_peer`、`officiality=peer_discovery`。
- [ ] 第三步：官方核验
  - 使用 `free-ai-offer-research` 对每条线索寻找官方价格页、文档、FAQ、产品页或官方模型仓库。
  - 核验免费机制、额度单位、有效期、续费、地区、注册条件和官方动作 URL；失败或不完整时保持 `needs_review` / `unavailable`。
- [ ] 第四步：外部信号
  - 使用 `model-community-signals` 搬运公开平台原生评分、评论、Stars、Likes、Downloads 或排名。
  - 原样保存平台、指标类型、原始值、样本数、短摘录、原文 URL 和抓取时间；不创建本站综合分。
- [ ] 第五步：视觉设计
  - 用户要求改页面时使用 `huashu-design`，从同行观察提炼信息架构、密度、状态表达和响应式模式。
  - 生成三个独立可运行原型，展示后等待用户选择；未选择前不改正式页面。
- [ ] 第六步：实现和审查
  - 使用 `tdd-master` 按最小行为执行 RED → GREEN → REFACTOR；测试先于生产代码。
  - 页面或前端变更完成后使用 `frontend-code-review`，检查数据安全、可访问性、响应式和回归。
- [ ] 第七步：发布门控
  - 加载 `references/approval-gates.md`，确认官方证据、用户选择、测试、静态构建和目标部署地址。
  - 只有人工确认后的 offer 才能进入公开目录；外部信号只作为详情信息，不改变官方状态。

## 阶段交接

加载 `references/handoff-contract.md`，每次交接写明：输入文件、已完成动作、字段等级、失败项、下一步和是否需要用户确认。跨阶段不得通过口头隐含状态。

## 运行方式

加载 `references/runbook.md` 获取本项目命令。默认顺序是：官方扫描与 GitHub 发现 → 候选审核 → 外部信号合并 → coverage → 原型选择 → TDD 实现 → 静态构建检查。

## 反模式

- 一次调用多个 skill 却不保存中间产物和 provenance。
- 把同行 README、社区评论或平台热度写成官方事实。
- 把外部评分、Stars、下载量换算成本站综合分。
- 在用户选择视觉原型前修改正式页面。
- 把一次来源失败当成过期，或用失败数据覆盖现有 offer。
- 未确认 Vercel 项目、域名和部署范围就发布。

## 参考资源

- `references/handoff-contract.md` — 阶段交接时加载，统一输入、输出和状态字段。
- `references/approval-gates.md` — 发布或修改正式页面前加载，执行确认门控。
- `references/runbook.md` — 执行本项目 CLI、测试和构建命令时加载。
