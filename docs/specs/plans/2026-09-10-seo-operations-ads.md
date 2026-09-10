# SEO、重点操作文档与广告位改进实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（每任务独立子代理 + 两阶段审查）`，或在本会话内按勾选逐步执行。任务使用 `- [ ]` 勾选跟踪。

**目标：** 让 SEO 静态产物与当前数据一致，补齐推广 offer 的可执行操作文档，并接入可控的显式广告 slot。

**架构要点：** 延续现有 Python 静态生成器、JSON 数据文件和 schema 校验；SEO 元数据由生成器统一输出，操作文档由数据驱动，广告容器仅由显式 slot 配置触发。退休 URL 只通过生成器的页面集合和 sitemap 规则处理。

**技术栈：** Python 3、静态 HTML、JSON、`unittest`；验证命令为 `python -m unittest discover -s tests -v`、`python scripts/build_seo_pages.py --check`。

**关联设计文档：** `docs/specs/2026-09-10-seo-operations-ads-design.md`

---

### 任务 1：聚合页 SEO 元数据和语言替代链接

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 测试：`tests/test_seo_pages.py`

- [x] **步骤 1：编写失败测试**

为 `/models/` 和 `/models/all/` 分别断言独立 title/description，并断言页面包含 `hreflang="zh-CN"`、`hreflang="en"` 和 `x-default`。

- [x] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_seo_pages -v`

预期：新增断言因当前两个聚合页 title 重复或缺少 hreflang 而失败。

- [x] **步骤 3：最小实现**

提取共享语言替代链接渲染函数；为每个页面定义稳定的中文/英文替代 URL，并在聚合页定义中使用不同的 SEO 文案。

- [x] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_seo_pages -v`

预期：SEO 页面测试全部通过。

### 任务 2：重点 offer 操作文档覆盖

**涉及文件：**
- 修改：`data/operations/*.json`
- 修改：`crawler/schema.py`（仅在现有契约需要明确额度/常见问题字段时）
- 修改：`scripts/build_seo_pages.py`（仅在字段需要展示时）
- 测试：`tests/test_operation_guides.py`

- [x] **步骤 1：编写失败测试**

断言前六个推广 offer 及首页精选 offer 都能通过 `operation-guides` 关联到至少一条路径，并断言 API 路径包含验证、额度或限制说明、常见问题说明和官方来源。

- [x] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_operation_guides -v`

预期：当前未覆盖的推广 offer 触发覆盖率断言失败。

- [x] **步骤 3：最小实现**

在现有操作 JSON 中加入经过现有官方来源支持的路径；不凭空增加模型、额度或政策。若首页精选与前六名重复，则复用同一 offer 路径，不复制数据。

- [x] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_operation_guides -v`

预期：操作文档 schema、覆盖率和页面渲染测试全部通过。

### 任务 3：显式 AdSense slot

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 修改：`design/free-china-ai-index.html`
- 测试：`tests/test_seo_pages.py`

- [x] **步骤 1：编写失败测试**

增加一个带 slot 配置的渲染断言，要求输出 `data-ad-client`、`data-ad-slot` 和一次 `adsbygoogle.push`；同时断言无 slot 配置时不输出空 `ins` 容器。

- [x] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_seo_pages -v`

预期：当前模板没有显式 slot 渲染，因此正例失败。

- [x] **步骤 3：最小实现**

增加受控的广告 slot 配置和安全 HTML 渲染函数；保留现有 AdSense client，禁止把任何账号密钥写入数据文件。

- [x] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_seo_pages -v`

预期：广告位正反例和全部 SEO 页面测试通过。

### 任务 4：重建、全量校验和交付检查

**涉及文件：**
- 生成：`models/`、`providers/`、`offers/`、`guides/`、`category/`、`sitemap.xml`、`.seo-pages-manifest.json`

- [x] **步骤 1：重建静态页面**

运行：`python scripts/build_seo_pages.py`

预期：生成器完成且不报告 schema 错误；退休模型/provider 页面不再生成。

- [x] **步骤 2：运行全量测试**

运行：`python -m unittest discover -s tests -v`

预期：全部测试通过，允许既有环境相关 skip。

- [x] **步骤 3：运行生成一致性检查**

运行：`python scripts/build_seo_pages.py --check`

预期：输出页面集合与磁盘产物一致并返回 0。

- [x] **步骤 4：检查变更范围**

运行：`git status --short` 和 `git diff --stat`

预期：只包含本计划涉及的源文件、数据文件和生成产物；不执行部署。
