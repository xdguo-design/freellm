# Free-LLM 中文指南页实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 新增 `/guides/free-llm/` 中文静态指南页，展示参考 README 的主要内容，并接入首页导航、SEO sitemap 与测试。

**架构要点：** 复用 `scripts/build_seo_pages.py` 的静态页面生成流程；指南内容以生成器内的结构化常量维护，和 `data/offers.json` 的已核验数据保持边界。生成器同步输出页面、sitemap 和 manifest，避免线上依赖 GitHub。

**技术栈：** Python 标准库、静态 HTML/CSS、pytest/unittest；验证命令为 `pytest -q`、`python scripts/build_seo_pages.py --check`、`python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-09-07-free-llm-guide-page-design.md`

---

### 任务 1：锁定指南页公共行为

**涉及文件：**
- 修改：`tests/test_seo_pages.py`
- 修改：`tests/test_e2e_static.py`

- [x] **步骤 1：编写失败测试**

在 `tests/test_seo_pages.py` 中新增 `guide_url()` 导入及断言：

```python
from scripts.build_seo_pages import guide_url


def test_guide_url_is_stable():
    assert guide_url() == "/guides/free-llm/"
```

扩展构建测试，断言临时输出包含 `guides/free-llm/index.html`、README 关键章节、原始仓库链接、MIT License，并把 sitemap 的 URL 数量期望改为首页 + Offer + 分类 + 指南。

在 `tests/test_e2e_static.py` 中断言首页含有 `/guides/free-llm/`，并断言生成后的静态页面存在。

- [x] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py tests/test_e2e_static.py -q`

预期：失败，原因是 `guide_url` 尚未定义，且当前生成器没有指南页和 sitemap 条目。

### 任务 2：生成指南页与 sitemap

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 修改：`design/free-china-ai-index.html`

- [x] **步骤 1：最小实现**

在 `scripts/build_seo_pages.py` 中增加：

```python
def guide_url() -> str:
    return "/guides/free-llm/"
```

新增 `render_guide_page(site_url)`，输出带 canonical、JSON-LD、响应式样式和以下可见区块的 HTML：项目定位、三步上手、Python 示例、编程助手、三类免费额度、本地/自托管、Base URL 速查、使用指南、社区与许可免责声明。表格中的链接经过 HTML 转义并设置 `target="_blank" rel="noopener noreferrer"`。

将 `guide_url()` 加入 `render_sitemap()` 的 paths；将 `guides/free-llm/index.html` 加入 `_expected_files()`；将 manifest 清理逻辑扩展到 `guides` 目录，并把指南文件纳入 manifest。

在首页顶部导航中新增：

```html
<a href="/guides/free-llm/">使用指南</a>
```

- [x] **步骤 2：运行测试确认通过**

运行：`pytest tests/test_seo_pages.py tests/test_e2e_static.py -q`

预期：新增指南页测试和既有静态页面测试全部通过。

### 任务 3：文档与生成结果同步

**涉及文件：**
- 修改：`README.md`
- 生成：`guides/free-llm/index.html`
- 生成：`sitemap.xml`
- 生成：`.seo-pages-manifest.json`

- [x] **步骤 1：更新项目说明**

在 README 的 SEO 页面和项目结构中加入 `/guides/free-llm/` 与 `guides/free-llm/index.html`，说明页面参考 `nejib1/Free-LLM` 的中文 README，并保留官方来源复核提示。

- [x] **步骤 2：生成静态产物**

运行：`python scripts/build_seo_pages.py`

预期：输出包含 1 个指南页，生成 `guides/free-llm/index.html`，并让 sitemap 包含 `https://freellm.top/guides/free-llm/`。

### 任务 4：全量验证

**涉及文件：**
- 无新增代码文件；检查任务 1–3 的所有修改。

- [x] **步骤 1：运行完整测试**

运行：`pytest -q`

预期：全量测试通过；若浏览器测试依赖不可用，只允许出现项目既有的跳过结果。

- [x] **步骤 2：检查生成结果无漂移**

运行：`python scripts/build_seo_pages.py --check` 和 `python scripts/build_static.py --check`

预期：分别输出当前 SEO 输出和当前静态页面数据，退出码为 0。

- [x] **步骤 3：检查工作区变更**

运行：`git status --short`

预期：只出现本功能涉及的指南、生成器、首页导航、README、测试和生成产物变化；保留用户原有未提交改动，不执行 reset、checkout 或清理操作。
