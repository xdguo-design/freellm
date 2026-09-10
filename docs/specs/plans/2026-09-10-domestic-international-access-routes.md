# 国内/国外模型接入路线拆分实施计划

**目标：** 将同一模型的国内与国际接入地址作为独立路线记录、核验和展示，并在模型聚合页统一归并。

**架构要点：** provider 代表具体接入平台，access route 代表该平台上的一个可调用地址；国内 Dots API 与国际 OpenRouter 不共用额度、注册条件或 Base URL。模型聚合页使用稳定的 canonical model key 归并不同路线，详情页按路线展示差异。

**技术栈：** Python、JSON 数据文件、静态 HTML 生成器、pytest。

**关联设计文档：** `docs/specs/2026-09-09-provider-access-and-region-policy-design.md`

---

### 任务 1：扩展访问路线数据结构

**涉及文件：**
- 修改：`data/models.json`
- 修改：`data/model-access.json`
- 修改：`data/provider-catalog.json`
- 修改：`data/provider-access.json`
- 修改：`data/region-policies.json`
- 测试：`tests/test_access_cards.py`

- [ ] **步骤 1：编写失败测试**

新增断言：Dots 国内路线必须使用 provider `dots-api-cn`、模型 ID `dots3-note-prev`、Base URL `https://note3-prev-api.askdiandian.com`；OpenRouter 路线必须继续使用 `dots-studio/dots-3-note-preview:free`；两条路线的注册要求和限流字段独立存在。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_access_cards.py -k dots -v`
预期：失败，因为当前目录只有 OpenRouter 路线，缺少国内 Dots API 路线。

- [ ] **步骤 3：最小数据实现**

新增国内 Dots provider/access card 和模型记录；将国内路线标记为 `region: domestic`、国际路线标记为 `region: international`，免费期限未知时使用 `unknown`，不得填 `permanent`。记录官方文档 `https://dots.ai/platform/docs` 与平台地址 `https://dots.ai/platform`。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_access_cards.py -k dots -v`
预期：所有 Dots 国内/国际路线断言通过。

### 任务 2：增加路线级 schema 与交叉引用校验

**涉及文件：**
- 修改：`crawler/schema.py`
- 修改：`scripts/build_seo_pages.py`
- 测试：`tests/test_access_cards.py`

- [ ] **步骤 1：编写失败测试**

覆盖以下断言：国内/国际路线必须有合法 region；路线的 provider、model、region policy 引用必须存在；缺少 Base URL 或把国际免费有效期写成永久时必须失败。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_access_cards.py -k route -v`
预期：失败，旧 schema 不识别路线级字段或无效路线引用。

- [ ] **步骤 3：最小实现**

在 schema 中增加路线字段集合与 `validate_access_route`；在访问上下文加载时同时执行 provider、model、policy、route 的结构校验和引用校验。错误通过 `SystemExit` 阻止静态站生成。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_access_cards.py -k route -v`
预期：合法路线通过，未知 provider、policy、model 或非法 region 均被拒绝。

### 任务 3：实现国内/国外路线的页面展示

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 测试：`tests/test_model_pages.py`
- 测试：`tests/test_provider_pages.py`

- [ ] **步骤 1：编写失败测试**

断言 Dots 模型聚合页同时出现“国内入口”和“国外入口”、两个不同 Base URL、各自模型 ID；断言国内入口不会继承 OpenRouter 的免费期限或限流。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_model_pages.py tests/test_provider_pages.py -k route -v`
预期：失败，因为详情页当前按单一 provider/access card 渲染。

- [ ] **步骤 3：最小实现**

按路线分组渲染 access route card；模型聚合页以 canonical model key 合并路线，厂家页只显示该厂家的路线。所有 URL、模型 ID、额度、地区和注册要求均通过 HTML escaping 输出。

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_model_pages.py tests/test_provider_pages.py -k route -v`
预期：页面路线分组、URL 隔离和字段隔离断言通过。

### 任务 4：重建静态站并执行质量门禁

**涉及文件：**
- 生成：`models/**/index.html`
- 生成：`providers/**/index.html`
- 生成：`models/all/index.html`
- 生成：`models/center/index.html`
- 生成：`sitemap.xml`

- [ ] **步骤 1：生成静态输出**

运行：`python scripts/build_seo_pages.py --data data/offers.json --output .`

- [ ] **步骤 2：执行专项检查**

运行：`python scripts/build_seo_pages.py --data data/offers.json --output . --check`
预期：输出 `current SEO output`。

- [ ] **步骤 3：执行全量测试与静态检查**

运行：`pytest -q; python scripts/build_static.py --check; git diff --check`
预期：pytest 全部通过，静态检查输出 `current`，diff 无 whitespace error。

- [ ] **步骤 4：人工核对 Dots 页面**

检查 `models/dots-studio-dots3-note-preview-free/index.html`、国内 Dots provider 页面和 `providers/openrouter/index.html`，确认国内、国外入口分别出现且没有交叉复用地址或免费期限。

不执行 `git commit`；完成后保留工作区改动，交由用户审阅。
