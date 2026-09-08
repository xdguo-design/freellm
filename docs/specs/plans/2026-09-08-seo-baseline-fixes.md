# SEO 基础修复实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 修复首页及生成 SEO 页面的中文首屏元数据、标题层级和绝对分享 URL。

**架构要点：** 首页继续是静态 HTML + JavaScript 增强；详情页、分类页和指南页继续由 `scripts/build_seo_pages.py` 统一生成。所有 SEO 元数据在 HTML 生成阶段完成，不依赖客户端脚本。

**技术栈：** 静态 HTML、原生 JavaScript、Python 标准库、pytest；验证命令为 `pytest -q`、`python scripts/build_seo_pages.py --check`、`python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-09-08-seo-baseline-fixes-design.md`

---

## 文件结构

- 修改：`design/free-china-ai-index.html` —— 首页静态 SEO 元数据与标题层级。
- 修改：`scripts/build_seo_pages.py` —— 详情页、分类页、指南页模板元数据。
- 修改：`tests/test_e2e_static.py` —— 首页 SEO 静态行为测试。
- 修改：`tests/test_seo_pages.py` —— 生成页面元数据测试。
- 生成：`offers/*/index.html`、`category/*/index.html`、`guides/free-llm/index.html`、`.seo-pages-manifest.json`、`sitemap.xml`。

### 任务 1：首页 SEO 元数据 RED-GREEN

**涉及文件：**

- 修改：`tests/test_e2e_static.py`
- 修改：`design/free-china-ai-index.html`

- [ ] **步骤 1：编写失败测试**

在 `StaticFileTests` 中增加断言：原始 HTML 使用 `lang="zh-CN"`，包含中文 description、绝对首页 canonical、`og:image` 指向生产 hero 图片，并且 `<h1>` 标签出现一次。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_e2e_static.py -q`

预期：新增首页 SEO 断言失败，原因是当前首页为 `lang="en"`、description 为英文、canonical 为 `/`、没有 `og:image`，且有两个 `<h1>`。

- [ ] **步骤 3：最小实现**

修改首页 `<head>`：将默认语言改为 `zh-CN`，把 title/description/Twitter 描述改为中文定位，将 canonical、`og:url` 改为 `https://freellm.top/`，加入 `og:image`、`og:image:alt`、`twitter:image`。将第二个可见 `<h1>` 改为 `<h2>`，并保留现有 JS 的英文切换逻辑。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_e2e_static.py -q`

预期：静态断言与现有浏览器测试全部通过；如默认语言相关测试失败，只保留并验证显式 `?lang=en` 的英文切换断言。

### 任务 2：SEO 生成器元数据 RED-GREEN

**涉及文件：**

- 修改：`tests/test_seo_pages.py`
- 修改：`scripts/build_seo_pages.py`

- [ ] **步骤 1：编写失败测试**

扩展生成器测试，检查生成的详情页和分类页含 `lang="zh-CN"`、中文分类标题/描述、绝对 canonical、`og:image` 和 `twitter:image`；检查指南页保留 `zh-CN` 并补齐分享图片。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py -q`

预期：新增断言失败，原因是详情页/分类页当前模板声明 `lang="en"`，标题与描述优先使用英文，且没有分享图片。

- [ ] **步骤 3：最小实现**

在 `scripts/build_seo_pages.py` 中增加统一分享图片常量与元数据渲染辅助逻辑；详情页和分类页使用已有中文字段输出中文 title/description、中文导航和 `zh-CN`；指南页补充绝对分享图片。所有模板继续通过 `_absolute` 生成生产 URL，并对属性值转义。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_seo_pages.py -q`

预期：生成器单元测试全部通过。

### 任务 3：重新生成静态 SEO 输出

**涉及文件：**

- 生成：`offers/`、`category/`、`guides/free-llm/index.html`、`.seo-pages-manifest.json`、`sitemap.xml`

- [ ] **步骤 1：执行生成**

运行：`python scripts/build_seo_pages.py`

预期：输出当前资源、分类和页面数量，并更新生成文件。

- [ ] **步骤 2：检查生成结果**

运行：`python scripts/build_seo_pages.py --check`

预期：返回成功，所有生成文件与模板输出一致。

### 任务 4：全量验证与审查

**涉及文件：** 本次变更涉及的全部文件。

- [ ] **步骤 1：运行完整测试**

运行：`pytest -q`

预期：全部测试通过；若环境缺少 Playwright，只有项目原有的浏览器依赖测试可跳过，静态与生成器测试必须通过。

- [ ] **步骤 2：运行静态构建检查**

运行：`python scripts/build_static.py --check`

预期：静态首页构建检查通过。

- [ ] **步骤 3：审阅变更范围**

运行：`git diff --stat` 与 `git diff --check`。

预期：无空白错误；变更集中在首页、SEO 生成器、相关测试和生成输出，不包含 `.env.local` 或无关用户改动。
