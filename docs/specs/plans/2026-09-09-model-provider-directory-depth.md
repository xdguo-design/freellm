# 模型与厂家双目录、详细操作指南实施计划

> **给代理执行者：** 推荐按任务逐项执行；每个阶段完成后运行验证命令，并在阶段边界向用户汇报。未完成当前阶段的测试前，不进入下一阶段。

**目标：** 将当前 37 条 Offer 目录升级为可按厂家和模型浏览的模型目录，并为重点免费入口补齐可执行的独立操作指南。

**架构要点：** 模型目录、厂家目录、免费入口和操作步骤使用不同数据边界。第三方目录用于扩展发现广度，官方来源用于核验和操作说明。静态页面继续由 Python 生成，首页继续消费嵌入数据。

**技术栈：** Python 3 标准库、静态 HTML、现有 `pytest` 测试、PowerShell；验证命令为 `python -m pytest -q`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check`。

**关联设计文档：** `docs/specs/2026-09-09-model-provider-directory-depth-design.md`

---

## 阶段 0：建立基线和工作边界

**交付：** 只记录现状，不改变用户数据。

**涉及文件：**

- 读取：`data/offers.json`
- 读取：`data/providers.json`
- 读取：`data/third-party-discovery-sources.json`
- 读取：`scripts/build_seo_pages.py`
- 读取：`crawler/freellm_net_discovery.py`
- 测试：`tests/test_e2e_static.py`、`tests/test_seo_pages.py`

- [ ] 运行 `python -m pytest -q`，记录全量通过和跳过数量。
- [ ] 运行 `python scripts/build_static.py --check`，确认输出为 `current: design\\free-china-ai-index.html`。
- [ ] 运行 `python scripts/build_seo_pages.py --check`，确认输出为当前 SEO 文件数。
- [ ] 记录参考目录抓取时间、模型行数和可用字段，所有外部发现数据先标记为第三方发现。

**阶段验收：** 基线命令退出码均为 0，工作区中本阶段没有新生成或修改文件。

## 阶段 1：模型数据契约与完整发现字段

**交付：** 模型行数据能保存厂家、模型、评分、上下文、最大输出、模态、速率、发布日期、使用量、状态和来源级别。

**涉及文件：**

- 新建：`data/models.json`
- 新建：`data/provider-catalog.json`
- 修改：`crawler/freellm_net_discovery.py`
- 修改：`crawler/schema.py`
- 修改：`tests/test_freellm_net_discovery.py`
- 新建：`tests/test_model_catalog.py`

- [ ] 在 `tests/test_freellm_net_discovery.py` 中先添加包含 9 个表格字段的 fixture，并断言解析结果包含 `score`、`context`、`maxOutput`、`modality`、`rateLimit`、`released`、`usage`、`status` 和 `directoryUrl`。
- [ ] 运行 `python -m pytest -q tests/test_freellm_net_discovery.py`，预期新增字段断言失败，因为解析器当前只保留部分字段。
- [ ] 修改 `_row_value` 调用和记录映射，使缺失字段输出空字符串而不是丢弃记录；保留原有 URL、敏感查询和付费行过滤。
- [ ] 在 `tests/test_model_catalog.py` 添加以下契约断言：模型行 ID 唯一；`providerId`、`modelId` 非空；评分为非负整数或空值；所有来源 URL 为 HTTPS；`verificationStatus` 只允许 `verified`、`directory_discovered`、`stale`。
- [ ] 在 `crawler/schema.py` 增加 `validate_models`，验证模型文件是列表、字段类型正确、来源级别和新鲜度状态合法。
- [ ] 用当前参考目录数据生成 `data/models.json`；每行保存 `directoryUrl`、`directoryProvider`、`model` 和原始字段，未完成官方核验的记录使用 `directory_discovered`。
- [ ] 从现有 `data/providers.json` 生成展示用 `data/provider-catalog.json`，保持爬虫白名单文件用途不变。
- [ ] 运行 `python -m pytest -q tests/test_freellm_net_discovery.py tests/test_model_catalog.py`，预期全绿。

**阶段验收：** 模型发现字段不再丢失；第三方发现数据和官方核验状态可区分；现有 Offer schema 测试不受影响。

## 阶段 2：同步与新鲜度标记

**交付：** 能重复同步模型目录，并保留新增、消失、过期和来源变化。

**涉及文件：**

- 新建：`scripts/sync_model_catalog.py`
- 修改：`data/models.json`
- 修改：`tests/test_model_catalog.py`
- 新建：`tests/test_model_catalog_sync.py`
- 修改：`README.md`

- [ ] 在 `tests/test_model_catalog_sync.py` 添加三组 fixture：新增模型、仍存在模型、上次存在但本次消失的模型；断言输出分别为 `new`、`current`、`stale` 状态。
- [ ] 运行 `python -m pytest -q tests/test_model_catalog_sync.py`，预期同步函数不存在或断言失败。
- [ ] 新建 `scripts/sync_model_catalog.py`，输入发现结果和上次 `data/models.json`，按稳定键 `providerId + modelId + directoryUrl` 合并；不得覆盖人工核验字段；失踪记录只标记 `stale`。
- [ ] 增加 `lastSeenAt`、`lastVerifiedAt`、`freshnessStatus`、`sourceKind` 字段，并以当前日期生成状态。
- [ ] 为同步脚本增加 `--input`、`--output`、`--as-of` 参数，使测试和定期运行不依赖系统当前时间。
- [ ] 在 README 写明同步、人工核验和公开发布的边界。
- [ ] 运行 `python -m pytest -q tests/test_model_catalog.py tests/test_model_catalog_sync.py`，预期全绿。

**阶段验收：** 同步可重复执行；旧记录不会被静默删除；页面可以明确区分当前、过期、待核验。

## 阶段 3：模型大列表与模型聚合页

**交付：** `/models/` 变成简洁的大列表，同时支持按厂家和模型浏览。

**涉及文件：**

- 修改：`scripts/build_seo_pages.py`
- 修改：`models/index.html`
- 新建：`tests/test_model_pages.py`
- 修改：`tests/test_seo_pages.py`
- 修改：`design/free-china-ai-index.html`（只增加明显入口和链接，不复制模型表）

- [ ] 在 `tests/test_model_pages.py` 添加页面契约：输出包含模型表头、厂家筛选、模型搜索、评分来源、最后同步时间、`Online`/`Stale`/`Unknown` 状态和官方来源链接。
- [ ] 运行 `python -m pytest -q tests/test_model_pages.py`，预期因新页面字段不存在而失败。
- [ ] 在生成器中新增 `_render_models_page(models, providers, site_url)`，从 `data/models.json` 读取逐模型行；页面默认按在线、已核验、最近更新时间、评分排序。
- [ ] 为同一 canonical model 生成 `/models/{slug}/` 聚合页；聚合页列出所有厂家记录，并将每条记录链接到对应 Offer 或官方来源。
- [ ] 为表格增加桌面端固定表头、窄屏横向滚动和卡片化降级显示；不把全部数据硬编码进首页。
- [ ] 在首页模型导航区域增加“全部模型”和“按厂家浏览”入口，并显示目录更新时间。
- [ ] 运行 `python scripts/build_seo_pages.py` 重新生成页面和 sitemap。
- [ ] 运行 `python -m pytest -q tests/test_model_pages.py tests/test_seo_pages.py tests/test_e2e_static.py`，预期全绿；浏览器缺少 Chromium 时只允许既有浏览器用例跳过。

**阶段验收：** 用户能从一个入口搜索模型、筛选厂家、查看同一模型的多平台记录；页面首屏能看出数据是否最新。

## 阶段 4：厂家目录与厂家详情页

**交付：** `/providers/` 和 `/providers/{slug}/` 能按厂家分组浏览。

**涉及文件：**

- 修改：`scripts/build_seo_pages.py`
- 新建：`providers/index.html`
- 新建：`tests/test_provider_pages.py`
- 修改：`sitemap.xml`

- [ ] 在 `tests/test_provider_pages.py` 添加厂家数量、别名、模型数量、官方入口、更新时间和模型链接断言。
- [ ] 运行 `python -m pytest -q tests/test_provider_pages.py`，预期因厂家页面不存在而失败。
- [ ] 新增厂家目录生成器，按 `providerId` 聚合 `data/models.json`，再关联 `data/offers.json` 的可用入口。
- [ ] 生成厂家详情页，展示该厂家全部模型记录、免费入口和官方核验状态；不把厂家爬虫白名单的 `allowedDomains` 直接当作展示文案。
- [ ] 在首页、模型页、Offer 详情页之间加入双向内部链接。
- [ ] 运行 `python scripts/build_seo_pages.py`，确认 `/providers/`、厂家详情页和 sitemap 一并生成。
- [ ] 运行 `python -m pytest -q tests/test_provider_pages.py tests/test_seo_pages.py`，预期全绿。

**阶段验收：** 用户可以先按厂家找模型，也可以先按模型比较厂家；厂家页不会与 Offer 页重复承载同一段操作说明。

## 阶段 5：独立操作路径和详细步骤

**交付：** 重点厂家和模型的每条入口都有独立、可执行的操作教程。

**涉及文件：**

- 新建：`data/operations/ollama-cloud.json`
- 新建：`data/operations/openrouter.json`
- 新建：`data/operations/groq.json`
- 新建：`data/operations/nvidia-nim.json`
- 新建：`data/operations/modelscope.json`
- 新建：`data/operations/siliconflow.json`
- 新建：`data/operations/opencode-zen.json`
- 新建：`data/operations/freebuff.json`
- 新建：`data/operations/longcat.json`
- 新建：`tests/test_operation_guides.py`
- 修改：`crawler/schema.py`
- 修改：`scripts/build_seo_pages.py`
- 修改：`offers/*/index.html`

- [ ] 在 `tests/test_operation_guides.py` 先添加操作路径契约：每条路径必须有 `id`、`label`、`prerequisites`、至少 3 个步骤、至少一个官方来源、一个验证动作；API 路径还必须有 endpoint、认证方式和可复制示例。
- [ ] 运行 `python -m pytest -q tests/test_operation_guides.py`，预期因操作文件和校验函数不存在而失败。
- [ ] 在 `crawler/schema.py` 增加 `validate_operation_guides`，拒绝空步骤、占位命令、非 HTTPS 来源和带明文密钥的示例。
- [ ] 为 Ollama Cloud、OpenRouter、Groq、NVIDIA NIM、ModelScope、SiliconFlow、OpenCode Zen、Freebuff、LongCat 编写第一版操作路径；每个平台分别写注册、访问、调用、验证和限制，不共享未经核对的额度。
- [ ] 将详情页的“官方动作”“官方来源”“复制命令”“访问路径”“常见问题”改为从操作文件渲染；没有操作文件的旧 Offer 保留兼容显示并标注“基础入口”。
- [ ] 为每条重点路径添加 `lastVerifiedAt` 和 `sourceUrls`，页面上显示核验日期。
- [ ] 运行 `python scripts/build_seo_pages.py` 生成对应 Offer 详情页。
- [ ] 运行 `python -m pytest -q tests/test_operation_guides.py tests/test_schema.py tests/test_seo_pages.py`，预期全绿。

**阶段验收：** 用户打开一个模型入口后，能从注册一直走到第一次成功调用，不需要自行猜菜单、Endpoint 或模型 ID。

## 阶段 6：重点模型扩容和官方核验

**交付：** 扩大模型覆盖，同时保持数据可信度分层。

**涉及文件：**

- 修改：`data/models.json`
- 修改：`data/provider-catalog.json`
- 修改：`data/offers.json`
- 修改：`data/operations/*.json`
- 修改：`tests/test_model_catalog.py`
- 修改：`tests/test_operation_guides.py`

- [ ] 先导入参考目录当前全量模型行作为 `directory_discovered`，保留评分和目录链接，不把它们写成本站官方已验证。
- [ ] 按搜索价值和免费可用性优先核验 Ollama Cloud、Freebuff、Muse Spark 1.3、LongCat-2.0、OpenRouter、Groq、NVIDIA NIM、ModelScope、SiliconFlow、Qwen 和 DeepSeek。
- [ ] 对每个重点厂家至少补齐一个完整操作路径；对同一模型的多个厂家，分别记录上下文、限流和免费条件。
- [ ] 发现模型下线、改名或重复时，使用 canonical model 和 alias 合并，不删除历史来源；重复记录在页面上标注“同一模型的不同平台入口”。
- [ ] 运行模型、Offer 和操作路径的全量校验，确认未核验模型不会进入“已验证免费”统计。

**阶段验收：** 模型列表规模显著超过现有 37 条 Offer；增加的数量和质量状态可见，重点入口的详情深度明显高于参考目录。

## 阶段 7：页面整理、SEO 和发布验证

**交付：** 用户能从首页进入模型、厂家和操作指南；页面明确体现新鲜度和差异化。

**涉及文件：**

- 修改：`design/free-china-ai-index.html`
- 修改：`scripts/build_seo_pages.py`
- 修改：`README.md`
- 修改：`sitemap.xml`
- 修改：`tests/test_e2e_static.py`
- 修改：`tests/test_seo_pages.py`

- [ ] 首页首屏增加三个明确入口：`查模型`、`按厂家找`、`看详细操作`；不在首屏塞入完整大表。
- [ ] 模型页、厂家页和 Offer 页统一显示页面更新时间、数据来源级别和官方来源。
- [ ] 每个聚合页设置唯一 title、description、canonical、Open Graph 和 JSON-LD；sitemap 包含新增模型、厂家和重点操作页。
- [ ] 为微信、Facebook、小红书和知乎分发准备可直接分享的详情 URL、标题和摘要；不把平台文案写进模型事实数据。
- [ ] 运行 `python -m pytest -q`。
- [ ] 运行 `python scripts/build_static.py --check`。
- [ ] 运行 `python scripts/build_seo_pages.py --check`。
- [ ] 运行 `git diff --check`。

**最终验收：** 全量测试、静态构建、SEO 构建和 diff 检查通过；首页、模型页、厂家页、Offer 详情页和官方来源链接均可访问。

## 执行顺序与暂停点

按以下顺序执行，每个阶段完成后暂停一次：

`阶段 0 → 阶段 1 → 阶段 2 → 阶段 3 → 阶段 4 → 阶段 5 → 阶段 6 → 阶段 7`

第一批建议先执行阶段 0 和阶段 1。阶段 1 完成后就能看到真实模型字段和数据规模，再决定是否立即导入全部目录数据。

## 分支策略

在默认分支之外创建 `codex/model-provider-directory-depth` 分支；每个阶段使用独立的小提交，例如 `feat: add model catalog contract`、`feat: render provider directory`、`docs: add operation guides`。不覆盖工作区中已有的用户修改。
