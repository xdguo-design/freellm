# Groq 模型逐行展示实施计划

> **给代理执行者：** 本计划在当前会话执行；每一步完成后运行对应验证。

**目标：** 让 Groq 资源在首页和详情页逐模型展示上下文窗口、免费限制与官方来源链接。

**架构要点：** 数据源仍为 `data/offers.json`；首页由 `design/free-china-ai-index.html` 的渲染逻辑消费结构化 `freeModels` 列表；详情页由 `scripts/build_seo_pages.py` 从同一数据生成。旧资源没有结构化模型列表时继续走原有兼容渲染。

**技术栈：** Python 静态生成器、内嵌 HTML/JavaScript、pytest。

**关联设计文档：** `docs/specs/2026-09-08-groq-model-rows-design.md`

---

### 任务 1：增加 Groq 逐模型数据与数据契约测试

**涉及文件：**
- 修改：`data/offers.json`
- 修改：`tests/test_seo_pages.py`

- [ ] **步骤 1：编写断言**

为 `groq-free` 增加测试，断言模型列表非空、模型 ID 唯一、每个模型有上下文窗口和免费额度字段，并覆盖当前官方 Free Plan 表中的 13 个模型 ID。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py -q`

预期：新 Groq 逐模型断言失败，因为当前数据只有单个摘要字符串。

- [ ] **步骤 3：更新数据**

在 `groq-free` 中增加结构化 `freeModels` 条目；使用官方当前列表中的模型 ID、每模型上下文窗口、RPM/RPD/TPM/TPD 或音频限制。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_seo_pages.py -q`

预期：通过。

### 任务 2：让生成页按模型逐行渲染并显示可点击来源

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 修改：`design/free-china-ai-index.html`
- 修改：`tests/test_seo_pages.py`

- [ ] **步骤 1：增加生成器测试**

断言 Groq 详情 HTML 包含独立模型行、上下文窗口列、明确的来源链接标签，以及每个模型的上下文值。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py -q`

预期：详情页缺少上下文窗口列或来源标签，测试失败。

- [ ] **步骤 3：最小实现**

更新详情页表格渲染，增加“上下文窗口”列；更新来源渲染，优先使用 `links` 的标签并给外链设置 `target`、`rel` 和清晰文本。更新首页渲染逻辑，优先逐项渲染 `freeModels`，没有该字段时保留原字符串渲染。

- [ ] **步骤 4：重建静态产物**

运行：`python scripts/build_static.py` 和 `python scripts/build_seo_pages.py`

预期：`design/free-china-ai-index.html` 与 `offers/groq-free/index.html` 更新，Groq 模型各占一行。

- [ ] **步骤 5：运行生成器测试**

运行：`pytest tests/test_seo_pages.py tests/test_build_static.py -q`

预期：通过。

### 任务 3：回归验证

**涉及文件：**
- 修改：无

- [ ] **步骤 1：运行完整相关测试**

运行：`pytest tests/test_seo_pages.py tests/test_build_static.py tests/test_schema.py tests/test_e2e_static.py -q`

预期：通过；若浏览器依赖缺失，仅允许既有浏览器测试按项目规则跳过。

- [ ] **步骤 2：检查生成产物状态**

运行：`python scripts/build_static.py --check` 和 `python scripts/build_seo_pages.py --check`

预期：分别输出 `current`，不报告 stale。
