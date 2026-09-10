# 提供商注册卡 + 模型访问卡 + 地区政策卡：数据审计与阶段 0–1 交付记录

- 日期：2026-09-09
- 范围：阶段 0（数据审计）+ 阶段 1（数据结构）+ GitHub Models 退役处理
- 结论：采用方案 A「提供商继承，模型覆盖」；296 条模型全部有访问状态，无遗留空值。

## 1. 数据盘点（2026-09-09）

| 项目 | 数量 | 数据来源 |
|---|---:|---|
| 模型记录 | 296 | `data/models.json`（由 `scripts/build_model_catalog.py` 从 freellm.net 目录生成） |
| 模型提供商 | 26 | `data/provider-catalog.json` |
| 免费资源 Offer | 37 | `data/offers.json` |
| 详细操作指南 | 9 | `data/operations/*.json` |

注意：`data/providers.json`（38 条）是另一套面向 Offer 的提供商清单（含国内云厂商、IDE、搜索 API），与这 26 个模型提供商不是同一集合，不要混用。

## 2. GitHub Models 退役（已处理）

官方文档确认 GitHub Models 已于 2026-07-30 完全退役，Playground、模型目录、Inference API、BYOK 均不可用，官方替代为 Azure AI Foundry 与 GitHub Copilot（https://docs.github.com/en/github-models）。

已执行：

- `data/model-access.json` 中 3 条 GitHub Models 记录（ai21-jamba-1-5-large、mistral-large-2411、phi-4）标记 `accessStatus: "retired"`，带替代方案、官方来源与核验日期。
- `data/provider-access.json` 中 GitHub Models 提供商卡标记 `registrationStatus: "unavailable"`。
- `scripts/build_seo_pages.py` 构建时通过 `_exclude_retired_models` 过滤退役模型：已删除 3 个模型聚合页与 `providers/github-models/` 页，模型总数、提供商总数、sitemap 同步更新（293 个可见模型、25 家厂商）。
- 退役卡是"墓碑"：即使上游目录日后移除这些模型，`generate_access_cards.py` 也会保留记录。

## 3. 新增数据结构（阶段 1）

| 文件 | 内容 |
|---|---|
| `data/provider-access.json` | 26 张提供商注册卡：注册入口、账号/邮箱/手机号/实名/信用卡/API Key 要求、许可证、额度行为、模型查找方式、地区政策引用、证据与核验状态 |
| `data/model-access.json` | 296 张模型访问卡：`registrationProfileId` 继承提供商注册卡，仅记录模型级差异（额外要求、地区覆盖、配额覆盖）与访问状态 |
| `data/region-policies.json` | 地区政策注册表：allowlist / denylist / cloud_region / model_specific / provider_model_dynamic / unknown 六类；已收录 Google Gemini 白名单、Mistral 三区域端点、GitHub Models 退役三条有官方证据的政策 |

配套代码：

- `crawler/schema.py`：新增 `validate_provider_access`、`validate_model_access`、`validate_region_policies` 及枚举。核心规则：未核验卡片不得填写 `lastVerifiedAt`；`current`/`retired` 必须有核验日期与官方来源；退役记录必须给出替代方案；国家代码必须是 ISO-3166 alpha-2。
- `scripts/generate_access_cards.py`：从模型目录 + 操作指南生成两张卡的脚本。幂等且保留人工核验字段；从 9 个操作指南的 prerequisites 提取已验证的"需要账号 / 需要 API Key"线索。
- `tests/test_access_cards.py`：schema 单测 + 数据完整性（26 卡对齐目录、296 卡对齐模型、政策引用合法、退役语义、未核验不冒充已核验）+ 构建产物不含退役模型。

## 4. 缺口报告

- 17 个提供商有模型目录但没有操作指南：agnes-ai、aion-labs、cerebras、chutes-ai、cline、cloudflare-workers-ai、cohere、github-models（已退役，无需补）、glhf-chat、google-gemini、grok-(xai)、hugging-face、kilo-code、llm7-io、mistral-ai、ovhcloud-ai-endpoints、z-ai-zhipu-ai。
- 全部 26 张提供商卡中，邮箱 / 手机号 / 实名 / 信用卡 / 开通计费 / 单独申请模型 / 超额行为 7 个字段 100% 为 `unknown`（如实显示"待核验"，未编造）。
- 提供商卡核验状态：10 张 `partial`（9 张来自本站操作指南证据 + GitHub Models 退役证据），16 张 `unverified`。
- 模型卡状态：293 张 `needs_review`（目录发现但未向平台核验），3 张 `retired`。
- 模型 ID `grok-(xai)` 含括号，是目录 slug 的历史遗留，后续清理时需同步迁移 models.json 与两张卡。
- `data/operations/opencode-zen.json` 文件名与内部 `providerId: "opencode"` 不一致（数据正确，仅文件名易误导）。

## 5. 后续阶段入口

- 阶段 2（补齐 26 张注册卡）：按 OpenRouter → Groq → Google Gemini → ModelScope → SiliconFlow → NVIDIA NIM → Ollama Cloud → Mistral → Hugging Face → Cloudflare 顺序逐平台官方核验，更新 `provider-access.json` 的 unknown 字段并补 `registrationSteps`。
- 阶段 3–4：模型卡逐批升格 `current`；实现按国家筛选（`region-policies.json` 已含 CN/HK/MO/TW/US/SG/JP/DE/FR 优先清单）。
- 阶段 5：模型详情页渲染注册卡 + 访问卡 + 地区政策。

## 6. 范围决定与阶段 2 第一批（2026-09-09 补充）

**范围决定**：经确认，地区判断的首要用户为**中国大陆用户**。已固化进 `data/region-policies.json`（`defaultCountryCode: "CN"`，schema 校验其必须属于优先国家清单），后续页面默认筛选以此为準。

**阶段 2 第一批已完成 5 家**（`provider-access.json`，`verificationStatus: partial`，`lastVerifiedAt: 2026-09-09`）：

| 提供商 | 关键核验结论 | 官方证据 |
|---|---|---|
| SiliconFlow | 手机号+短信注册；实名仅提升额度不强制 | api-docs.siliconflow.cn quickstart |
| ModelScope | 手机号/邮箱/阿里云/GitHub 任一注册，均非强制；访问令牌 ms- 开头 | modelscope.cn API-Inference 文档与免费公告 |
| Z AI/Zhipu | 大陆入口 bigmodel.cn 手机号注册（官方确认支持海外区号）；z.ai 为海外入口 | docs.bigmodel.cn 注册登录 FAQ |
| OpenRouter | 免费模型无需信用卡、无需开通计费；Google 或邮箱任一注册 | openrouter.ai/docs/faq |
| Groq | 免费层无需信用卡；升级 Developer 层才需支付方式 | console.groq.com/docs/billing-faqs |

生成脚本重跑已验证不会覆盖上述人工核验字段（合并保护生效）。剩余 21 家待阶段 2 后续批次，优先：Google Gemini、NVIDIA NIM、Ollama Cloud、Mistral、Hugging Face、Cloudflare Workers AI。

## 7. 阶段 2 全量完成 + 大陆可用性筛选（2026-09-09 补充）

**阶段 2 状态：26/26 全部处理完毕。** 第二批 13 家取得官方或一致第三方证据并升格 `partial`，2 家如实保持 `unverified`（glhf.chat：站点 HTTP 522 不可达；grok-(xai)：搜索配额受限 + docs.x.ai 抓取超时，无新证据）。当前核验分布：24 `partial` / 2 `unverified`。

第二批关键结论（详见 `provider-access.json` 各卡 sourceUrls 与 notes）：

- **免费无需信用卡**：Cohere（trial key 自动生成）、Google Gemini（免费层，18+ 硬性）、Mistral（Experiment 层，但**必须短信验证**）、Cloudflare Workers AI（每日 10,000 Neurons）、NVIDIA NIM（试用积分）、Hugging Face（需邮箱验证）、OVHcloud AI Endpoints（免费限速层甚至无需账号和 Key）、llm7.io（可匿名调用）、Agnes AI（仅邮箱）、Aion Labs（第三方证据）、Cline（登录即用）、Kilo Code（已迁移 kilo.ai，免费层无卡）。
- **重要状态变化**：Chutes.ai 官方 2026-02 公告确认免费层（Early Access 200 次/天）已退役，最低 $3/月订阅或按量付费；目录中 2 个 chutes 模型的访问卡已标注付费要求（`extraRequirements`）。
- **证据冲突**：Cerebras 官方文档称赠金需绑定支付方式，第三方称有无卡免费层，`cardRequired` 保持 `unknown`。
- **勘误**：Agnes AI 注册域名实为 `agnes-ai.com`（原记录 agnes.ai 有误）；Kilo Code 品牌迁移为 kilo.ai；OVHcloud 新增 `ovhcloud-endpoints-regions`（cloud_region）地区政策卡。

**阶段 4 首个 UI：模型目录"大陆可用性"列与筛选器**（models/all 与模型中心页）：

- 每行新增 `data-cn` 属性与"大陆可用性"状态列，取值 `available / unavailable / unknown`，由提供商卡的地区政策推导（`_cn_status_for_policy`）：denylist 含 CN → 不可用；allowlist 仅在 `countriesComplete: true` 且含 CN 时 → 可用，清单不完整一律 → 待核验；cloud_region/unknown → 待核验。绝不因证据缺失判定不可用。
- 工具栏新增"大陆可用性"筛选器（默认"全部状态"）：当前数据下所有行均为"待核验"，若默认只显示"可用"会得到空列表，因此默认展示全部状态并逐行标注，待政策数据充实后再收紧默认值。
- 测试：政策推导单测（证据边界）+ 页面集成断言；全套 178 个测试通过，两个 `--check` 构建干净。

**遗留**：glhf-chat 与 grok-(xai) 两家待下次核验（搜索配额 2026-09-29 重置）；Google 白名单完整国家清单待逐项导入；提供商详情页的注册要求渲染（阶段 5）未开始。

## 8. 页面改动的 SEO 配套（2026-09-10 补充）

规则确立：**凡是页面功能改动，SEO 元素必须同步更新。** 本次围绕"大陆可用性"功能完成：

- **models/all 页**：标题追加"（含中国大陆可用性标注）· Mainland CN Availability"；meta description 重写为双语的可用性 + 注册要求卖点；JSON-LD 增加 `keywords`（免费 AI 模型、中国大陆可用、大陆可用性标注、注册要求、手机号验证、free AI API、mainland China availability 等）；lead 文案同步。
- **爬虫可见的静态内容块**（关键：筛选器是 JS 交互，爬虫看不到）：新增 `#mainland-cn-availability` 静态区块，双语列出已人工核验的注册要求结论（SiliconFlow 手机号、Mistral 短信验证、OpenRouter/Groq/Cohere/Cloudflare/NVIDIA 免费层无信用卡、Hugging Face 邮箱验证、Agnes AI 仅邮箱、llm7.io 匿名可用、Chutes 免费层退役、GitHub Models 退役公告），并内链提供商目录与国内指南页。
- **内链双向打通**：models/all ↔ `guides/china-free-ai-api`（国内指南新增 "02 / mainland CN availability" 区块链接回模型目录筛选），models/all → providers 目录。
- **模型中心页**：meta description 更新提及大陆可用性标注；工具栏五列网格 CSS 同步（页面级与 `MODEL_CENTER_STYLE` 两处）。
- **llms.txt**：新增 `## Models` 区块（模型大列表 / 模型中心 / 提供商目录 / 国内指南），描述含大陆可用性标注卖点。
- **测试**：新增 `test_models_page_seo_surfaces_cn_availability`（标题、keywords、静态区块、双向内链）；退役相关断言收紧为"目录行不出现退役模型"，但退役公告文案保持爬虫可见（`2026-07-30` 断言）。
- 验收：179 个测试通过；两个 `--check` 干净；`git diff --check` 干净（修复了条件区块留下的行尾空白）。
