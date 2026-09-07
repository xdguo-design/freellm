# Web AI 基础设施目录与使用说明设计

## 目标

将 Free AI Index 从“免费模型、IDE、Coding Plan 和开放权重目录”扩展为可直接使用的 AI 工具目录，纳入 Web Search、Fetch/Extract、Crawl/Map、Browser 和 Agent 基础设施，并为所有条目提供可执行的使用说明。

本次交付包含两条必须同时满足的主线：

1. **能力分组**：用户能够按服务能力和计费方式找到产品，单个产品可以属于多个能力组。
2. **使用闭环**：用户打开任意条目后，能够知道前置条件、开通步骤、请求方式、示例代码、额度保护和常见问题。

## 范围与边界

### 纳入范围

- Web Search API
- Fetch / Extract API
- Crawl / Map API
- Browser / Browser automation
- Agent / asynchronous web task
- 现有模型 API、免费 IDE、Coding Plan、开放权重和低价 PAYG
- 官方价格页、产品页、文档、FAQ、更新日志和官方模型仓库
- 第三方目录、GitHub 同类项目和社区内容作为发现线索，不能直接作为已核验事实

### 不纳入范围

- 不在本站代理或转发用户的 API 请求
- 不替用户注册、登录、创建 Key、充值或调用真实额度
- 不绕过验证码、地区限制、robots 或访问控制
- 不把“开源客户端 + 用户自带付费 Key”单独标成免费服务
- 不把 Search、Fetch、Browser、Agent 的不同计费单位合并成一个模糊的“免费额度”

## 推荐方案

采用“**统一 Offer 模型 + 多能力标签 + 类型化使用说明**”。保留当前 `data/offers.json` 的兼容字段；新字段用于表达 Web 基础设施和可执行用法。数据层级固定为：`Provider` 是公司或服务方，`Product` 是一个产品，`Offer` 是该产品的一种可购买/可使用方案，`capabilities` 是 Offer 的能力标签。

- 同一 Offer 可以有多个能力标签，前提是这些能力共享同一套免费规则、限制和计费方式。
- 同一 Product 需要按免费规则、计费主体或关键限制拆成多条 Offer，例如 TinyFish 至少拆成“Search/Fetch 免费 Offer”和“Agent/Browser 按量 Offer”。
- 列表总数按 Offer 去重；能力分组数量按该组包含的 Offer 计数，因此一条多能力 Offer 会在多个能力组各计一次，但不会增加总 Offer 数。
- Provider 不作为 Offer 数量的计数单位，Product 名称用于详情页归并和搜索。

不建立与现有目录平行的第二套数据格式，避免模型、IDE 和 Web API 出现两套筛选、校验、详情页和审核流程。

## 能力分类

`capabilities` 使用以下固定值：

| 能力 | 定义 | 典型使用动作 |
|---|---|---|
| `search` | 返回网页、新闻、图片或结构化搜索结果 | 提交 query，读取 URL、标题、摘要和元数据 |
| `fetch` | 获取指定 URL 的清洁文本或结构化内容 | 提交 URL，读取 Markdown、HTML 或 JSON |
| `extract` | 从网页中抽取正文、字段或结构化数据 | 指定 URL、Schema 或抽取指令 |
| `crawl` | 从起始 URL 扩展抓取多个页面 | 设置深度、页数、过滤规则并轮询任务 |
| `map` | 枚举站点链接图或可抓取页面 | 提交根 URL，获取 URL 列表 |
| `browser` | 提供远程浏览器、渲染、会话或自动化能力 | 创建会话、导航、操作、关闭会话 |
| `agent` | 执行多步骤网页任务并返回结果 | 提交目标、等待异步任务、读取结果 |
| `model_api` | 直接调用托管模型 | 设置 Base URL、模型 ID 和鉴权 |
| `free_ide` | 通过 IDE、插件或 CLI 提供免费能力 | 下载、登录、启用套餐或免费模式 |
| `open_weights` | 提供可下载模型权重 | 下载、启动本地推理并遵守许可证 |

`fetch` 和 `extract` 在数据层和页面中保持两个独立分组；当产品同时具备两者时可以同时打两个标签。产品展示分组与计费展示分开：能力回答“能做什么”，计费模型回答“怎么免费/怎么收费”。

## 计费与限制模型

新增字段使用结构化对象表达限制，避免只把数值写入不可查询的字符串：

```json
{
  "productType": "web_infrastructure",
  "capabilities": ["search", "fetch", "agent", "browser"],
  "pricingModel": "free_rate_limited",
  "freePolicy": {
    "type": "rate_limited",
    "amount": null,
    "unit": null,
    "period": null
  },
  "limits": {
    "requestsPerMinute": 30,
    "requestsPerHour": 500,
    "urlsPerMinute": 150,
    "urlsPerDay": 1000,
    "concurrency": 2,
    "sessionMinutes": null
  },
  "billing": {
    "walletRequired": false,
    "cardRequired": "no",
    "autoReload": "unknown",
    "overageBehavior": "stop_or_metered",
    "prices": [
      {"capability": "agent", "unit": "step", "price": "$0.016"},
      {"capability": "browser", "unit": "minute", "price": "$0.002"}
    ]
  }
}
```

上面是字段结构示意；正式 Offer 不得使用省略号或不可执行的伪代码。结构化限制的字段契约如下：

- `freePolicy` 在 `pricingModel` 为 `monthly_quota`、`daily_quota`、`weekly_quota`、`free_rate_limited`、`free_credits`、`trial` 或 `limited_time_free` 时必填。
- `freePolicy.amount` 可以为 `null`，但必须同时填写可核验的 `unit`、`period` 或限频信息；永久免费但限频的产品使用 `amount: null` 和 `limits`。
- `limits` 中每个数字字段都必须带单位；未知值使用 `null`，不使用 `0` 猜测“无限制”。
- `billing` 必须说明 `walletRequired`、`cardRequired`、`overageBehavior`；无法从官方来源确认时使用 `unknown` 并将 Offer 标为 `needs_review`。
- `pricingModel: permanent_free` 表示没有付费续费，不表示无限制；仍须记录已知的 RPM、并发、日/月额度或 `null` 的未公开限制。
- `pricingModel: payg` 或 `metered_paid` 必须有至少一个带 `capability`、`unit` 和 `price` 的 `billing.prices` 项。

### 正式字段契约

除现有 Offer 必填字段外，扩展后的 Offer 必须满足以下类型和关系：

| 字段 | 类型 | 必填条件与校验 |
|---|---|---|
| `providerId` | string | 必填；必须能在 `data/providers.json` 找到 |
| `productId` | string | 必填；同一 Product 的多个 Offer 共用此值 |
| `offerVariant` | string | 必填；与 `providerId + productId` 组成 Offer 变体唯一键 |
| `capabilities` | string[] | 必填且非空；只能使用能力分类表中的固定值 |
| `productType` | string | 必填；Web 基础设施使用 `web_infrastructure` |
| `pricingModel` | string | 必填；只能使用计费与限制模型中的固定枚举 |
| `freePolicy` | object/null | 免费或试用模型必填；`amount`、`unit`、`period` 按规则校验 |
| `limits` | object | 必填；未知限制写 `null`，已知数字字段必须带明确单位 |
| `billing` | object | 必填；包含钱包、绑卡、自动充值和超额策略 |
| `usageGuide` | object | 所有正式 Offer 必填；按能力校验使用说明矩阵 |
| `sourceUrls` | string[] | 必填且非空；每条均为官方 HTTPS URL |
| `status` | string | 必填；使用现有 `verified`、`changed`、`expired`、`unavailable`、`needs_review` |
| `lastVerifiedAt` | string | 必填；格式为 `YYYY-MM-DD` |

`providerId + productId + offerVariant` 是 Offer 的稳定唯一键。`id` 继续作为页面和历史 diff 的稳定标识，不因能力标签或说明文字变化而重建。

固定枚举：

- `productType`: 新增 `web_infrastructure`，保留现有类型
- `pricingModel`: `permanent_free`、`monthly_quota`、`daily_quota`、`weekly_quota`、`free_rate_limited`、`free_credits`、`trial`、`limited_time_free`、`payg`、`metered_paid`、`not_confirmed`
- `overageBehavior`: `stop`、`metered`、`wallet`、`auto_reload`、`unknown`
- 数值限制的单位必须同时保存，例如 `requestsPerMinute`、`urlsPerDay`、`browserMinutes`，不允许只保存无单位数字

当一个供应商的免费能力和付费能力不同，拆成独立 Offer；不能用一个“免费”徽章掩盖 Agent 或 Browser 的付费条件。

## 使用说明模型

每一条正式 Offer 必须有 `usageGuide`。现有 `command` 字段继续保留作为兼容字段，但不能替代完整使用说明。`usageGuide` 的公共必填规则是：`summary` 非空、`prerequisites` 至少一项、`steps` 至少两步、至少一个官方 `docsUrl` 或产品入口，以及至少一个不含 `...`、`TODO` 或真实密钥的可执行示例/操作命令。

```json
{
  "usageGuide": {
    "summary": "适合需要实时网页搜索的 Agent",
    "prerequisites": [
      "注册账号",
      "创建 API Key",
      "确认免费额度或限频规则"
    ],
    "steps": [
      "打开官方注册入口",
      "在控制台创建 API Key",
      "设置环境变量",
      "发送第一次请求"
    ],
    "endpoint": "https://api.tavily.com/search",
    "method": "POST",
    "authentication": "Authorization: Bearer ${TAVILY_API_KEY}",
    "parameters": [
      {"name": "query", "required": true, "description": "搜索关键词"}
    ],
    "examples": {
      "curl": "curl --request POST \"https://api.tavily.com/search\" --header \"Content-Type: application/json\" --header \"Authorization: Bearer ${TAVILY_API_KEY}\" --data '{\"query\":\"latest AI news\",\"search_depth\":\"basic\",\"max_results\":5}'"
    },
    "quotaGuard": [
      "先关闭自动充值或设置消费上限",
      "超过 RPM 后等待下一窗口"
    ],
    "commonIssues": [
      {"problem": "请求被限频", "solution": "降低并发并按 Retry-After 重试"}
    ],
    "docsUrl": "https://docs.tavily.com/documentation/api-reference/introduction"
  }
}
```

不同能力的最低内容要求：

| 类型 | 最低使用说明 |
|---|---|
| Search | Endpoint、HTTP 方法、鉴权、query 示例、返回字段、RPM/日额度 |
| Fetch | URL 请求示例、返回格式、失败重试和成功计费单位 |
| Extract | URL/Schema 或抽取指令示例、返回字段、失败重试和成功计费单位 |
| Crawl / Map | 根 URL、深度或页数、任务状态和结果获取方式 |
| Browser | 创建/关闭会话、并发、会话时长和计费保护 |
| Agent | 目标提交、异步等待、结果读取、步骤计费和失败处理 |
| 模型 API | Base URL、模型 ID、鉴权、请求示例和停止超额设置 |
| 免费 IDE | 下载、登录、启用免费模式、额度查看和地区要求 |
| 开放权重 | 下载入口、Ollama/vLLM 或官方启动命令、硬件和许可证 |

对于非 HTTP 产品，`examples` 可使用 `shell`、`docker` 或 `action` 示例；例如 IDE 必须提供下载/安装动作和登录步骤，开放权重必须提供下载命令和本地启动命令。API 类必须提供至少一个可复制的 `curl`、Python 或 JavaScript 示例。任何示例中的 URL、字段名和命令都必须来自对应官方文档；环境变量可以使用 `$API_KEY` 一类占位符，但不得写入真实凭据。

使用说明校验矩阵：

| 条件 | 必填字段/断言 |
|---|---|
| 所有 Offer | `summary` 非空；`prerequisites` 至少 1 项；`steps` 至少 2 项；`docsUrl` 或产品入口为官方 HTTPS；至少 1 个示例，示例代码非空且不含 `...`、`TODO`、真实密钥 |
| 含 `search` | `endpoint`、`method`、`authentication`、query 参数说明、返回字段说明；示例包含 `curl`/Python/JavaScript 至少一种 |
| 含 `fetch` 或 `extract` | URL 参数说明、返回格式、成功计费单位、失败重试说明；示例必须展示 URL 输入 |
| 含 `crawl` 或 `map` | 根 URL、页数/深度参数、任务或结果获取方式；异步产品必须说明提交、查询、完成/失败状态 |
| 含 `browser` | 创建会话、导航/操作、关闭会话、并发或时长限制、停止计费方式 |
| 含 `agent` | 目标提交、异步等待、结果读取、步骤/运行计费和失败处理 |
| `free_ide` | 下载/安装入口、登录步骤、免费模式/套餐入口、额度查看方式 |
| `open_weights` | 下载地址、许可证、硬件要求、至少一个本地启动命令 |

校验器只对可判定字段做自动断言；“官方文档是否真的支持该参数”仍由人工核验，结果写入 `status` 和审核事件。

缺少 Endpoint、官方快速开始或可复制示例时，条目只能标为 `needs_review`，不能作为“可直接使用”条目发布。

## 首批供应商与分组

首期 MVP 固定核验 8 个 Web 基础设施产品，覆盖七类能力和两种免费模型：Keenable、TinyFish、Tavily、Exa、You.com、Firecrawl、Brave Search、Browserbase。首批之外的 Jina AI Reader、Browserless、ScrapingBee 先进入 provider 候选池，不阻塞 MVP 的页面和数据契约交付。

首批纳入以下候选，最终状态以官方来源核验为准：

- Search：Keenable、TinyFish、Tavily、Exa、You.com、Brave Search
- Fetch：TinyFish、Firecrawl、Tavily、You.com、Jina AI Reader、ScrapingBee
- Extract：Firecrawl、Tavily、You.com、Jina AI Reader、ScrapingBee
- Crawl / Map：Firecrawl、Tavily
- Browser：TinyFish、Browserbase、Browserless、ScrapingBee
- Agent：TinyFish、Exa、Firecrawl、Browserbase
- 现有目录：模型 API、免费 IDE、Coding Plan、开放权重和低价 PAYG 保持在对应分组

Keenable 的额度、超额价格、是否免绑卡和停止策略必须回到官方价格/文档页核验后再标 `verified`。社区描述只能生成候选。

现有 18 条 Offer 的迁移规则：不删除、不改变原有 `id`；根据现有 `productType` 补齐对应 `capabilities` 和 `usageGuide`。若官方来源不足以写出可执行说明，保留条目但降为 `needs_review`，直到补齐用法证据；页面仍显示其待核验状态，不伪装成可直接使用。

## 数据流与审核

```text
官方价格/文档/FAQ
  → provider registry
  → 公开来源扫描与关键词发现
  → 候选 Offer + 使用说明草稿
  → 字段/来源/敏感信息校验
  → 人工核验免费规则、用法与限制
  → data/offers.json
  → 静态页面分组、搜索、详情抽屉和代码示例
```

发现器需要补充能力和使用相关关键词：`search`、`fetch`、`extract`、`crawl`、`map`、`browser`、`agent`、`contents`、`API key`、`rate limit`、`RPM`、`concurrency`、`wallet`、`auto reload`、`no credit card`、`quickstart`、`curl`、`SDK` 等。

来源失败继续记为 `source_unavailable`，不能变成 `expired`。价格、额度、有效期、限频、并发、绑卡、钱包和自动充值发生变化时进入审核队列。

### 状态转换

- `needs_review`：候选或关键字段缺失，不能进入公开推荐状态。
- `verified`：官方来源、计费规则、限制和使用说明均已人工核验。
- `changed`：官方来源显示关键字段发生变化，保留旧值并等待人工确认。
- `unavailable`：官方产品或入口明确不可用或已下线。
- `expired`：官方明确声明活动或额度已结束；一次抓取失败不得使用此状态。
- `source_unavailable` 只作为扫描事件的 `changeType`，不作为 Offer 的公开状态；它会进入审核队列并保留现有 Offer。

发布条件固定为：`status=verified`，至少一个官方 `sourceUrls`，`lastVerifiedAt` 非空，限制/计费字段通过校验，且 `usageGuide` 满足对应能力的最低要求。候选进入正式 Offer 时沿用稳定的 `offer.id`；同一 `providerId + productId + offerVariant` 只能有一条记录，能力标签变化通过 diff 进入审核。

状态路径固定为：

```text
候选 → needs_review → verified
verified → changed → verified
verified → expired
verified → unavailable
expired/unavailable → needs_review → verified（只有官方重新开放或新规则核验通过时）
```

每次状态或关键字段变化都写入审核事件：

```json
{
  "createdAt": "2026-09-07T00:00:00+00:00",
  "offerId": "tinyfish-search-free",
  "changeType": "changed",
  "fields": {"limits.requestsPerMinute": {"before": 30, "after": 20}},
  "sourceUrls": ["https://future.tinyfish.io/pricing"],
  "state": "pending",
  "needsReview": true
}
```

## 页面行为

- 侧边栏新增“Web Infrastructure”总组，并按 Search、Fetch、Extract、Crawl、Map、Browser、Agent 子组展示数量。
- 标签页增加“Free rate-limited”“Free credits”“Pay-as-you-go”“Browser/Agent”等计费维度。
- 一条 Offer 出现在多个能力组时只计一次总数，子组数量按能力标签计算。
- 列表行展示能力徽章、免费机制、核心额度/限频和最后核验日期。
- 详情抽屉增加“如何使用”区块，顺序为：适用场景 → 前置条件 → 开通步骤 → 请求参数 → 示例代码 → 额度保护 → 常见问题 → 官方链接。
- 示例代码按 `curl`、Python、JavaScript 切换，并提供复制按钮。
- 当用法或关键限制未确认时，页面显示 `Needs review`，不显示“免费可用”强断言。
- SEO JSON-LD 继续从统一 Offer 数据生成，不把未经核验候选写入公开 ItemList。

## 错误处理与安全

- 官方页面动态化、解析失败、限流或超时：保存来源状态和原因，保留已有 Offer，不自动降级为过期。
- 使用说明中的示例只允许官方 Endpoint、占位 API Key 和无敏感信息参数。
- 禁止把真实 Token、用户账户、充值信息或私有 URL 写入数据、日志和快照。
- 对可能触发费用的示例，必须包含消费上限、停止开关或“先确认计费”的提示；不能默认引导自动充值。
- 抓取器只访问 provider registry 白名单中的公开 HTTPS 来源。

## 测试与验收标准

### 数据与抓取

- Schema 接受合法的 Web Infrastructure Offer，并拒绝未知能力、未知计费模型和无单位限制。
- TinyFish 类多能力 Offer 能正确拆分/展示 Search、Fetch、Agent、Browser。
- 月额度、日额度、RPM、URL/日、并发和会话分钟数均能被校验和 diff。
- 搜索/使用说明关键词能够发现候选，但候选仍保持 `needs_review`，不会自动发布。
- 任何官方来源失败都生成 `source_unavailable`，不生成 `expired`。

### 页面

- 能力分组数量由 Offer 数据动态计算。
- 多标签 Offer 在多个子组可见，但总数不重复。
- 详情抽屉显示完整“如何使用”区块和至少一个可复制示例。
- 搜索可以匹配供应商、产品、能力、Endpoint、模型 ID 和使用说明文本。
- 网络 JSON、嵌入式数据和缺失数据三种加载路径均保持可用。

### 发布门控

- 正式 Offer 必须有官方来源、最后核验日期、结构化限制和完整使用说明。
- 关键字段缺失时只能进入审核队列。
- 构建检查确认 HTML 内嵌数据与 `data/offers.json` 一致。
- 现有 18 条 Offer 的原有分类、详情和测试不回归。

## 实施顺序

1. 扩展 schema 和数据结构，先写失败测试。
2. 增加首批 Web 基础设施 provider 与官方来源入口。
3. 扩展发现关键词、候选字段和覆盖报告。
4. 为首批候选补充核验后的 Offer 与使用说明。
5. 改造页面分组、计数、详情抽屉和代码示例。
6. 运行全量单元测试、静态构建检查和浏览器验收。
