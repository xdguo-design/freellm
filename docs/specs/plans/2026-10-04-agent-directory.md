# 精选 AI Agent 名录实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 将 `/models/` 页面 Agent 精选区扩展为 13 项独立数据驱动的精选目录。

**架构要点：** 新增 `data/featured_agents.json`，与促销 Offer 数据分离。生成器用它渲染现有视觉系统的 Agent 卡片；现有 5 个条目仍指向站内 Offer 页，新增 8 个指向官方产品入口。

**技术栈：** Python 3、JSON、pytest；验证命令为 `python -m pytest tests/test_model_pages.py -q` 和 `python scripts/build_seo_pages.py --check`。

**关联设计文档：** `docs/specs/2026-10-04-agent-directory-design.md`

---

## 文件结构与职责

- 新建 `data/featured_agents.json`：13 个精选 Agent 的双语文案、类型、标签和目标链接。
- 修改 `scripts/build_seo_pages.py`：读取、校验并渲染独立目录，统计数目与搜索属性使用该目录。
- 修改 `tests/test_model_pages.py`：验证目录格式和生成页面的 13 个条目、旧 Offer 链接、官方入口及双语/搜索属性。
- 修改 `models/index.html`：保存静态构建器生成的页面结果。
- 新建 `docs/specs/2026-10-04-agent-directory-design.md`：记录已确认的设计。
- 新建本文件：记录可执行的实施步骤。

## 任务 1：先定义数据和回归测试

**涉及文件：**
- 新建：`data/featured_agents.json`
- 修改：`tests/test_model_pages.py`

- [ ] **步骤 1：建立 13 项数据记录**

为每个条目设置 `id`、`nameZh`、`nameEn`、`provider`、`kindZh`、`kindEn`、`descriptionZh`、`descriptionEn`、`tagsZh`、`tagsEn`、`url`；前 5 项增加 `offerId`。Hermes 分类为通用 Agent；官方入口以设计文档的列表为准。不得填写未经确认的免费额度或地区承诺。

- [ ] **步骤 2：添加目录与页面行为测试**

新增测试读取目录文件，断言 ID 唯一、数量为 13、每条必填值完整且 URL scheme 为 HTTPS。扩展 `build_featured_fixture_page()` 所在测试模块中的页面构建测试，断言页面有 13 个 `.featured-agent-card`、计数文案为 13、5 个站内 Offer 链接保留、8 个官方链接存在、每张卡片含双语分类/描述和 `data-search-text`。

- [ ] **步骤 3：运行测试并确认失败**

运行：`python -m pytest tests/test_model_pages.py -q`

预期：新增测试因目录加载/页面数据尚未实现而失败；既有测试失败时应记录其具体回归后再修复。

## 任务 2：实现独立目录读取与渲染

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 新建：`data/featured_agents.json`

- [ ] **步骤 1：编写带错误上下文的目录加载器**

实现 `_load_featured_agents(data_dir)`，读取 `featured_agents.json`，验证数组类型、字段非空、HTTPS URL、ID 唯一，以及 5 个指定 `offerId` 均存在于传入的 Offer 列表中；异常信息包括数据文件和问题记录 ID。

- [ ] **步骤 2：让页面渲染使用独立目录**

在 `render_models_landing_page` 增加末尾可选参数 `featured_agents`，调用处由 `_expected_files` 传入 `_load_featured_agents(data_dir)`。在函数单测直接调用且未提供参数时，按 `ACCESS_DATA_DIR` 的仓库默认目录读取。

- [ ] **步骤 3：按记录生成卡片**

将卡片渲染改成读取目录字段：Offer 卡片链接到 `/offers/{offerId}/` 并使用现有 Offer 描述/徽标；独立目录项链接 `url` 并使用目录双语描述和标签。所有文本、URL、`data-search-text` 属性通过 `_esc` 转义；外链统一增加安全 rel 属性；品牌标识使用对应官方 hostname 和现有文字 fallback。

- [ ] **步骤 4：同步文案和计数**

页面 SEO description、精选 Agent 数、页脚模型与 Agent 数、Agent 搜索文本全部使用 `len(featured_agents)` 及目录记录，不再使用只筛 5 个 ID 的 Offer 子集。

- [ ] **步骤 5：运行模型页回归测试**

运行：`python -m pytest tests/test_model_pages.py -q`

预期：全部通过，生成页面断言显示 13 项且链接准确。

## 任务 3：生成页面并检查生产输出

**涉及文件：**
- 修改：`models/index.html`

- [ ] **步骤 1：生成静态页面**

运行：`python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top`

预期：命令成功，`models/index.html` 的精选 Agent 区输出 13 张卡片。

- [ ] **步骤 2：运行静态构建检查和相关测试**

运行：`python scripts/build_seo_pages.py --check`

运行：`python -m pytest tests/test_model_pages.py tests/test_site_visual_system.py -q`

预期：构建器检查与测试均成功。

- [ ] **步骤 3：执行浏览器验收**

在本地页面分别检查桌面宽屏与窄屏、中文与英文切换、搜索 `Grok`、`Claude Code`、`Agent.Space`，确认卡片数、目标链接和响应式网格无横向溢出。

## 任务 4：审查、提交并合并

**涉及文件：**
- 上述全部文件

- [ ] **步骤 1：查看最终差异**

运行：`git diff --check` 和 `git status --short`；逐项确认仅有设计文档、实施计划、目录数据、生成器、测试和生成页面变更，未跟踪的 `Temp/` 保持原样。

- [ ] **步骤 2：提交功能分支**

在 `codex/agent-directory` 上提交已验证变更，提交信息为 `feat: expand featured AI agent directory`。

- [ ] **步骤 3：合并至 main**

确认 `main` 未领先/偏离产生冲突后切换到 `main`，执行 `git merge --no-ff codex/agent-directory`，随后在 `main` 上重跑 `python scripts/build_seo_pages.py --check` 和 `python -m pytest tests/test_model_pages.py -q`。

- [ ] **步骤 4：确认合并结果**

运行：`git status --short --branch` 与 `git log -1 --oneline`；预期 `main` 包含合并提交，功能分支已集成，工作树只有原有未跟踪 `Temp/`。
