# 模型中心双 Tab 实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 新增 `/models/center/`，在同一页面提供原特色资源页和完整模型目录两个 Tab。

**架构要点：** 以现有首页模板作为共享导航、Hero、搜索和基础筛选区；旧路由继续由原构建分支生成，新页面只增加一个合并输出。Tab 只控制共享区下方的旧特色内容和完整模型目录，状态由轻量原生 JavaScript 和 URL hash 管理。

**技术栈：** Python 静态生成、原生 HTML/CSS/JavaScript、pytest；验证命令为 `python -m pytest -q`、静态检查和 SEO 检查。

**关联设计文档：** `docs/specs/2026-09-09-model-center-tabs-design.md`

---

### 任务 1：锁定路由与 Tab 行为

**涉及文件：**
- 修改：`tests/test_model_pages.py`
- 修改：`tests/test_seo_pages.py`

- [ ] **步骤 1：编写失败测试**

增加断言：`/models/center/index.html` 包含两个 Tab、`#all-models`、共享 Hero、特色资源关键词和模型目录关键词；断言 Tab 位于共享 Hero/筛选之后、原分类之前；断言旧首页与 `/models/` 仍分别存在；断言 sitemap 包含 `/models/center/`。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_model_pages.py tests/test_seo_pages.py -q`

预期：失败，因为合并页面和 sitemap 路由尚未生成。

### 任务 2：生成合并页面

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 修改：`design/free-china-ai-index.html`

- [ ] **步骤 1：最小实现**

新增 `MODEL_CENTER_PAGE_PATH = "/models/center/"` 和 `render_model_center_page()`；以原首页模板的 Hero/搜索/基础筛选作为共享区，在原分类区之前插入 Tab 和 Tab 2 的 `_model_catalog_markup(models)`，Tab 1 保持原分类及后续资源内容。为按钮绑定 `data-center-tab`，用 `window.location.hash === "#all-models"` 初始化 Tab 2，并同步 `aria-selected`、页面状态和 hash。将合并页加入 `_expected_files()` 和 sitemap；首页导航增加“模型中心”链接，不移除原有入口。

- [ ] **步骤 2：运行定向测试确认通过**

运行：`python -m pytest tests/test_model_pages.py tests/test_seo_pages.py -q`

预期：新增路由、Tab、旧页面保留和 sitemap 断言通过。

### 任务 3：构建与回归验证

**涉及文件：**
- 生成：`models/center/index.html`
- 修改：`README.md`

- [ ] **步骤 1：更新文档与生成产物**

README 增加 `/models/center/` 说明；运行 `python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top`。

- [ ] **步骤 2：运行完整质量门禁**

运行：`python -m pytest -q`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top --check`、`git diff --check`。

预期：测试通过，静态与 SEO 输出为 current，差异检查无错误。
