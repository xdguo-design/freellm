# FreeLLM SEO 内容扩展实施计划

> **给代理执行者：** 推荐在本会话内按勾选逐步执行；每个行为遵循 TDD 的 RED-GREEN-REFACTOR 节奏。

**目标：** 基于现有核验数据新增 6 个搜索意图入口页，并打通首页、分类页、模型页、详情页与 Sitemap 的内部链接。

**架构要点：** 继续以 `data/offers.json` 和 `data/models.json` 为唯一事实来源，由 `scripts/build_seo_pages.py` 生成静态 HTML。主题页采用集中配置和筛选规则，避免手工复制页面；所有页面共享双语、canonical、结构化数据和 AdSense 脚本模板。

**技术栈：** Python 静态生成器、HTML/CSS/原生 JavaScript、pytest、Vercel 静态部署。

**关联设计文档：** `docs/specs/2026-09-09-seo-content-expansion-design.md`

---

## 文件结构先行

- 修改：`scripts/build_seo_pages.py`——新增主题页配置、筛选、渲染、Sitemap 和内部链接。
- 修改：`tests/test_seo_pages.py`——覆盖 6 个主题页的 URL、元数据、数据映射、双语和广告脚本。
- 修改：`design/free-china-ai-index.html`——首页增加主题入口模块。
- 修改：`tests/test_e2e_static.py`——覆盖首页主题入口和生成结果一致性。
- 生成：`guides/*/index.html`、`sitemap.xml`——由生成器统一产出。
- 修改：`README.md`——确认仓库首页有指向生产站点和主题页的可发现链接。

### 任务 1：主题页公共配置与 URL 清单

**涉及文件：** `scripts/build_seo_pages.py`、`tests/test_seo_pages.py`

- [ ] **步骤 1：编写失败测试**

在测试中声明 6 个稳定 URL，并验证 `_expected_files()` 包含这 6 个 `guides/<slug>/index.html` 文件：

```python
THEME_GUIDES = {
    "free-openai-compatible-apis",
    "free-ai-coding-tools",
    "free-ai-search-apis",
    "open-weight-models",
    "model-context-windows",
    "china-free-ai-api",
}

def test_expected_files_include_theme_guides():
    files, _ = _expected_files(read_offers(), "https://freellm.top", read_models())
    generated = {path.parts[1] for path in files if path.parts[:1] == ("guides",)}
    assert THEME_GUIDES <= generated
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py::test_expected_files_include_theme_guides -v`

预期：失败，提示 6 个主题页路径尚未出现在生成文件集合中。

- [ ] **步骤 3：最小实现**

在生成器中加入集中配置，每条配置包含 `slug`、中英文标题、描述、主题筛选键和正文说明；在 `_expected_files()` 中为每条配置登记 `guides/<slug>/index.html`。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_seo_pages.py::test_expected_files_include_theme_guides -v`

预期：通过。

### 任务 2：主题页筛选和内容渲染

**涉及文件：** `scripts/build_seo_pages.py`、`tests/test_seo_pages.py`

- [ ] **步骤 1：编写失败测试**

为每个主题页验证唯一 H1、title、description、canonical、可追溯的已有资源/模型、官方链接和 AdSense 脚本；模型上下文页必须显示模型上下文参数。

```python
def test_theme_guides_render_unique_metadata_and_verified_rows(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    for slug in THEME_GUIDES:
        page = (tmp_path / "guides" / slug / "index.html").read_text(encoding="utf-8")
        assert page.count("<h1>") == 1
        assert f"https://freellm.top/guides/{slug}/" in page
        assert "<meta name=\"description\"" in page
        assert "adsbygoogle.js?client=ca-pub-2461062743308239" in page

def test_context_window_guide_exposes_model_parameters(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "guides" / "model-context-windows" / "index.html").read_text(encoding="utf-8")
    assert "Context window" in page
    assert "tokens" in page
    assert "source" in page.lower()
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py::test_theme_guides_render_unique_metadata_and_verified_rows tests/test_seo_pages.py::test_context_window_guide_exposes_model_parameters -v`

预期：失败，因为主题页尚未渲染。

- [ ] **步骤 3：最小实现**

新增 `render_theme_guide_page()`：

1. 根据主题配置从 offers/models 过滤数据。
2. 输出双语标题、说明、限制条件、资源卡片或模型参数表。
3. 资源卡片只链接现有详情页和 `register`/`sourceUrls` 官方链接。
4. 模型上下文页同时输出模型名、厂商、上下文值、单位和来源链接。
5. 输出 `CollectionPage`、BreadcrumbList、canonical、双语切换脚本、分析脚本和 AdSense 脚本。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_seo_pages.py::test_theme_guides_render_unique_metadata_and_verified_rows tests/test_seo_pages.py::test_context_window_guide_exposes_model_parameters -v`

预期：通过。

### 任务 3：首页和已有页面内链

**涉及文件：** `design/free-china-ai-index.html`、`scripts/build_seo_pages.py`、`tests/test_e2e_static.py`、`tests/test_seo_pages.py`

- [ ] **步骤 1：编写失败测试**

```python
def test_homepage_links_to_theme_guides():
    page = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
    for slug in THEME_GUIDES:
        assert f"/guides/{slug}/" in page
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_e2e_static.py::test_homepage_links_to_theme_guides -v`

预期：失败，首页尚未包含 6 个主题入口。

- [ ] **步骤 3：最小实现**

在首页现有导航/主题区域加入 6 个主题入口；在分类页、模型目录页和资源详情页的相关区域加入上下文相关链接。保持现有语言切换和视觉样式，不新增第三方脚本。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_e2e_static.py::test_homepage_links_to_theme_guides tests/test_seo_pages.py -q`

预期：本次相关测试通过；如出现已有无关失败，记录测试名称和原因，不降低断言。

### 任务 4：生成、全量验证与发布

**涉及文件：** 生成器输出文件、`README.md`、`sitemap.xml`

- [ ] **步骤 1：生成页面**

运行：`python scripts/build_seo_pages.py` 和 `python scripts/build_static.py`

预期：生成 6 个新指南页，Sitemap 包含全部新增 URL。

- [ ] **步骤 2：运行质量检查**

运行：`pytest -q`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check`、`git diff --check`

预期：静态和 SEO 检查通过；全量测试中的既有失败必须单独列出，不得用修改断言的方式绕过。

- [ ] **步骤 3：线上验证**

逐一请求 6 个生产 URL，确认 HTTP 200、canonical 正确、AdSense 脚本存在；确认 `https://freellm.top/sitemap.xml` 返回有效 XML 并包含新增 URL。

- [ ] **步骤 4：部署**

使用现有 `freellm` Vercel 项目发布当前已验证工作区，发布后再次请求首页、6 个主题页、模型页和 Sitemap。

