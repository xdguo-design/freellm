# OpenAI 与 Claude Code SEO 指南页实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 新增两个基于真实目录数据的英文 SEO 指南页，覆盖 OpenAI 兼容免费 API 替代方案与 Claude Code 免费替代方案，并接入 sitemap 和内部链接。

**架构要点：** 页面由 `scripts/build_seo_pages.py` 统一生成，数据优先复用 `data/offers.json` 中已验证条目；首页只增加入口，不复制整套内容。测试验证生成结果的可观察 SEO 行为，不绑定具体 HTML 实现细节。

**技术栈：** Python 静态生成器、原生 HTML/CSS、pytest；验证命令为 `pytest -q`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check`。

**关联设计文档：** `docs/specs/2026-09-08-openai-claude-seo-design.md`

---

### 任务 1：锁定两个指南页的生成验收行为

**涉及文件：**
- 修改：`tests/test_seo_pages.py`
- 修改：`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

添加断言：构建产物必须包含 `/guides/free-openai-api-alternatives/` 和 `/guides/claude-code-free-alternatives/`；页面分别包含目标关键词、canonical、H1、免责声明和官方来源链接；`sitemap.xml` 包含两个 URL；首页包含两个指南链接。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py tests/test_e2e_static.py -q`

预期：新增断言失败，因为两个指南页面和入口尚未生成。

### 任务 2：实现两个指南页和构建接入

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 修改：`design/free-china-ai-index.html`
- 生成：`guides/free-openai-api-alternatives/index.html`
- 生成：`guides/claude-code-free-alternatives/index.html`
- 生成：`sitemap.xml`

- [ ] **步骤 1：实现最小生成逻辑**

增加两个指南页渲染函数和构建调用；使用现有 offer 数据生成对比表，加入明确的免费承诺边界、配置示例、官方来源与面包屑；在首页现有指南/SEO 入口区域增加两个链接。

- [ ] **步骤 2：生成并运行目标测试**

运行：`python scripts/build_seo_pages.py`，然后运行 `pytest tests/test_seo_pages.py tests/test_e2e_static.py -q`。

预期：新增测试全部通过，两个页面与 sitemap 产物生成成功。

### 任务 3：全量验证

**涉及文件：** 已生成页面、测试和构建脚本。

- [ ] **步骤 1：运行全量测试**

运行：`pytest -q`。

预期：全部既有测试与新增测试通过。

- [ ] **步骤 2：运行构建检查**

运行：`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check`、`git diff --check`。

预期：静态页和 SEO 输出均显示 current/check passed；没有新增 diff 空白错误。

### 任务 4：部署与线上验收

**涉及文件：** 无新增源文件；使用不含 `.git` 的临时部署副本。

- [ ] **步骤 1：部署生产版本**

使用 Vercel production deployment，将最新构建产物发布到 `freellm.top`。

- [ ] **步骤 2：验证线上页面**

检查首页、两个新指南页、sitemap 的 HTTP 200；确认 sitemap URL 数量增加，页面 canonical、title 和目标关键词存在。

- [ ] **步骤 3：交付索引动作**

向用户提供两个 URL，建议在 Google Search Console 的网址检查中分别请求编入索引；不把提交动作误报为已收录。
