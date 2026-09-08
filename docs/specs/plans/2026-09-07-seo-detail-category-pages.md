# SEO 详情页与分类页实施计划

> **给代理执行者：** 推荐按任务逐步执行并在每个测试批次后验证。任务使用 `- [ ]` 勾选跟踪。

**目标：** 从现有 36 条资源数据生成可被 Google 独立抓取的资源详情页、分类页和生产 sitemap。

**架构要点：** 以 `data/offers.json` 为唯一数据源；Python 标准库生成静态页面；首页继续保留现有 JavaScript 交互，但输出真实 `<a>` 内链；分类匹配规则与首页 `offerCategories` 保持一致。

**技术栈：** Python 3 标准库、静态 HTML、PowerShell；验证命令为 `pytest -q`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check`。

**关联设计文档：** `docs/specs/2026-09-07-seo-detail-category-pages-design.md`

---

## 文件变更清单

- 新建：`scripts/build_seo_pages.py`（生成详情页、分类页和 sitemap）。
- 新建：`tests/test_seo_pages.py`（验证 URL、页面元信息、分类集合和 sitemap）。
- 新建：`offers/<id>/index.html`（36 个生成资源详情页）。
- 新建：`category/<slug>/index.html`（有内容的分类页）。
- 修改：`design/free-china-ai-index.html`（为动态资源卡片加入详情页与分类页内链）。
- 修改：`sitemap.xml`（列出生产规范 URL）。
- 修改：`README.md`（增加生成与页面说明）。

## 任务 1：建立生成器契约测试

**涉及文件：**

- 新建：`tests/test_seo_pages.py`
- 新建：`scripts/build_seo_pages.py`

- [ ] **步骤 1：编写失败测试**

  测试生成器公开的 `offer_url`、`category_url`、`categorize_offer`、`build_site` 行为，断言 36 条资源有详情 URL、分类集合非空、输出 sitemap 使用 `https://freellm.top/`。

- [ ] **步骤 2：运行并确认失败**

  运行：`pytest tests/test_seo_pages.py -q`

  预期：因 `scripts.build_seo_pages` 尚不存在而失败。

- [ ] **步骤 3：最小实现**

  新建生成器，使用 `validate_offers` 校验输入；实现固定分类映射、URL slug 校验、HTML 转义、页面渲染、目录写入和 sitemap 写入。

- [ ] **步骤 4：运行并确认通过**

  运行：`pytest tests/test_seo_pages.py -q`

  预期：所有生成器契约测试通过。

## 任务 2：生成详情页、分类页和 sitemap

**涉及文件：**

- 修改：`scripts/build_seo_pages.py`
- 新建：`offers/<id>/index.html`
- 新建：`category/<slug>/index.html`
- 修改：`sitemap.xml`

- [ ] **步骤 1：编写页面输出测试**

  断言详情页含唯一标题、description、绝对 canonical、资源标题、官方链接和相关资源链接；分类页含分类标题、资源链接和首页链接；sitemap URL 数量等于首页 + 详情页 + 非空分类页。

- [ ] **步骤 2：运行并确认失败**

  运行：`pytest tests/test_seo_pages.py -q`

  预期：页面文件尚未生成，页面内容和 sitemap 断言失败。

- [ ] **步骤 3：实现页面模板与生成流程**

  详情页使用资源数据字段渲染正文；分类页使用 `categorize_offer` 结果渲染资源列表；生成器先清理自身生成的目标文件，再写入页面和 sitemap，避免过期页面残留。

- [ ] **步骤 4：运行并确认通过**

  运行：`python scripts/build_seo_pages.py`；随后运行 `pytest tests/test_seo_pages.py -q`。

  预期：输出 36 个详情页、所有非空分类页和更新后的 sitemap，测试通过。

## 任务 3：首页可爬取内链

**涉及文件：**

- 修改：`design/free-china-ai-index.html`
- 修改：`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

  断言首页动态资源卡片模板包含 `/offers/` 详情链接、分类页链接或由生成器导出的稳定路径，并保留原有详情抽屉按钮。

- [ ] **步骤 2：运行并确认失败**

  运行：`pytest tests/test_e2e_static.py -q`

  预期：新增内链断言失败。

- [ ] **步骤 3：最小实现**

  在 `rowArticleMarkup` 中给资源标题或底部操作区加入 `<a href="/offers/<id>/">`，在分类导航增加 `/category/<slug>/` 链接；不删除 `data-detail` 和抽屉交互。

- [ ] **步骤 4：运行并确认通过**

  运行：`pytest tests/test_e2e_static.py -q`。

  预期：原有首页行为和新增内链断言全部通过。

## 任务 4：文档与完整验证

**涉及文件：**

- 修改：`README.md`

- [ ] **步骤 1：更新文档**

  增加 `python scripts/build_seo_pages.py` 和 `--check` 命令，并说明生产页面 URL 结构。

- [ ] **步骤 2：运行完整验证**

  运行：`pytest -q`; `python scripts/build_static.py --check`; `python scripts/build_seo_pages.py --check`。

  预期：全部命令返回 0；测试无新增失败；生成文件与数据源一致。

- [ ] **步骤 3：检查 diff**

  运行：`git status --short`; `git diff --stat`; `git diff -- sitemap.xml README.md design/free-china-ai-index.html`。

  预期：只包含本功能相关的脚本、测试、页面、sitemap、首页内链和文档变更。
