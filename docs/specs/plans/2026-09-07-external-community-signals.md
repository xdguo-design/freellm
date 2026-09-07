# 外部评分与评论搬运实施计划

> **给代理执行者：** 任务使用 `- [ ]` 勾选跟踪；本计划在当前 `codex/github-peer-discovery-console-style` 分支内执行，遵循 TDD 的 RED → GREEN → REFACTOR 节奏。

**目标：** 为模型/工具增加可追溯的外部平台评分、热度指标和评论摘录，并在详情页原样展示，不生成本站评分。

**非目标：** 不做综合评分、跨平台换算、本站投票、评论全文复制、登录后抓取、私人内容抓取或自动发布未经核验的免费额度。

**架构要点：** 新增纯函数模块负责记录校验、敏感信息过滤、去重和按 offer 聚合；外部 HTTP 只通过已有的公开限量抓取器；静态页面只消费已验证的数据字段。`sourcePlatform` 与 `sourceType` 始终保留，避免把热度冒充评分。

**技术栈/运行方式：** Python 3 标准库、静态 HTML/CSS/JavaScript、`unittest`；验证命令为 `python -m unittest discover -s tests -v` 和 `python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-09-07-external-community-signals-design.md`

---

## 文件变更清单

- 新建：
  - `crawler/community_signals.py`：信号记录校验、摘录过滤、去重和聚合。
  - `data/community-signals.json`：外部评分/热度/评论的公开快照容器，初始为空列表。
  - `skills/model-community-signals/SKILL.md`：只搬运外部信号的专项流程。
  - `skills/model-community-signals/README.md`：安装、触发和输出说明。
  - `skills/model-community-signals/references/source-policy.md`：来源与版权安全边界。
  - `skills/model-community-signals/references/report-template.md`：外部信号报告模板。
- 修改：
  - `crawler/cli.py`：增加 `signals` 命令，校验并合并快照。
  - `design/free-china-ai-index.html`：详情抽屉增加外部信号区块，缺失时显示明确状态。
  - `skills/free-ai-offer-research/SKILL.md`：增加外部信号阶段和“不自评分”规则。
  - `tests/test_skill.py`、`tests/test_community_signals.py`、`tests/test_e2e_static.py`：覆盖契约、CLI 和页面钩子。

## 任务 1：定义信号契约和安全过滤

**涉及文件：** `tests/test_community_signals.py`、`crawler/community_signals.py`

- [ ] 步骤 1：写失败测试，验证合法评分/热度/评论记录通过，非法平台、非 HTTPS、跨类型字段和超长摘录被拒绝；验证摘录移除 token/password/邮箱样式。
- [ ] 步骤 2：运行 `python -m unittest tests.test_community_signals.CommunitySignalValidationTests -v`；预期当前因 `crawler.community_signals` 不存在而失败。
- [ ] 步骤 3：实现 `validate_signal_record(record)`、`validate_signals(records)` 和 `redact_excerpt(text, limit=240)`，仅保留原始指标，不做数值换算。
- [ ] 步骤 4：运行同一命令；预期验证测试全部通过。

## 任务 2：实现去重和按模型聚合

**涉及文件：** `tests/test_community_signals.py`、`crawler/community_signals.py`

- [ ] 步骤 1：写失败测试，验证相同 `offerId + sourcePlatform + sourceType + sourceUrl` 的新快照覆盖旧快照，其他平台信号并列保留；验证 `rating` 不会和 `downloads` 合并。
- [ ] 步骤 2：运行 `python -m unittest tests.test_community_signals.CommunitySignalMergeTests -v`；预期因缺少 `merge_signals` 和 `group_signals_by_offer` 而失败。
- [ ] 步骤 3：实现 `merge_signals(existing, discovered, captured_at)` 和 `group_signals_by_offer(signals)`，按原始字段排序，缺失信号不补值。
- [ ] 步骤 4：运行该测试及 `python -m unittest tests.test_community_signals -v`；预期全部通过。

## 任务 3：接入快照文件与 CLI

**涉及文件：** `tests/test_community_signals.py`、`crawler/cli.py`、`data/community-signals.json`

- [ ] 步骤 1：写失败测试，调用 `python -m crawler.cli signals --input snapshot.json --out community-signals.json`，验证合法快照写出、重复记录去重、非法记录返回 1 且不覆盖旧输出。
- [ ] 步骤 2：运行 CLI 测试；预期因 CLI 不识别 `signals` 而失败。
- [ ] 步骤 3：新增 `signals` 子命令，读取 JSON 列表，调用校验和合并函数，写出 JSON；输出 `signals: <count> records, <failed> rejected`。
- [ ] 步骤 4：运行 CLI 测试与 `python -m crawler.cli signals --input data/community-signals.json --out <临时文件>`；预期返回 0，初始输出为空列表。

## 任务 4：新增专项 skill 并串入现有流程

**涉及文件：** `skills/model-community-signals/SKILL.md`、`README.md`、`references/source-policy.md`、`references/report-template.md`、`skills/free-ai-offer-research/SKILL.md`、`tests/test_skill.py`

- [ ] 步骤 1：写失败测试，要求专项 skill 包含 `sourcePlatform`、`sourceType`、`sourceUrl`、`capturedAt`、`不自评分`、`不跨平台换算`、`needs_review` 和“不登录/不抓私人内容”等规则，并保持主文件少于 500 行。
- [ ] 步骤 2：运行 `python -m unittest tests.test_skill -v`；预期新增 skill 文件不存在而失败。
- [ ] 步骤 3：创建专项 skill；工作流顺序固定为：来源范围 → 公开抓取/导入 → 原样字段校验 → 摘录过滤 → 去重合并 → 报告/页面展示。更新免费 AI skill，声明外部信号只能作为辅助信息。
- [ ] 步骤 4：运行 `python -m unittest tests.test_skill -v`；预期全部通过。

## 任务 5：接入详情抽屉

**涉及文件：** `tests/test_e2e_static.py`、`design/free-china-ai-index.html`

- [ ] 步骤 1：写页面契约测试，要求页面存在 `communitySignals` 数据读取、外部信号容器、平台名、原始分数/热度标签、抓取时间和原文链接钩子。
- [ ] 步骤 2：运行 `python -m unittest tests.test_e2e_static.StaticContractTests -v`；预期新钩子断言失败。
- [ ] 步骤 3：在详情抽屉中增加“External signals”区块，按 `sourcePlatform` 分组渲染 `rating/review/stars/downloads/likes/rank/sentiment`，缺失时显示 `No public rating found`；所有外部文本经现有 HTML 转义函数处理。
- [ ] 步骤 4：运行静态契约测试；预期通过，且不改变现有 offer 数据字段和筛选行为。

## 任务 6：全量验证和交付

- [ ] 步骤 1：运行 `python -m unittest discover -s tests -v`；预期既有测试和新增测试全部通过，只有本机缺 Chromium 时允许已有 E2E 跳过。
- [ ] 步骤 2：运行 `python scripts/build_static.py --check`；预期输出 `current: design\\free-china-ai-index.html`。
- [ ] 步骤 3：运行 `git diff --check`；预期无 whitespace error。
- [ ] 步骤 4：确认 `data/offers.json` 没有被外部信号快照自动覆盖；报告中明确说明当前哪些平台有数据、哪些没有公开评分。
