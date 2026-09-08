# Agnes AI 目录接入设计

## 目标

将官方 Agnes AI 的免费/default API 能力纳入 FreeLLM 目录，覆盖文本、图片和视频模型，让首页、详情页、分类页和 sitemap 都能发现该资源。

## 方案

采用一个 provider-level API 条目 `agnes-ai-free`，在同一详情页列出：

- `agnes-2.5-flash`、`agnes-1.5-flash`、`agnes-2.0-flash`：文本/多模态聊天
- `agnes-image-2.0-flash`、`agnes-image-2.1-flash`：图片生成
- `agnes-video-v2.0`：视频生成

条目归类为 API + 免费，免费机制描述为 Free/default 限速访问，不宣称无限免费。详情页使用 OpenAI-compatible chat endpoint 示例；图片和视频能力链接到官方文档和模型目录。所有密钥只使用 `${AGNES_API_KEY}` 占位符。

## 数据与生成

- 在 `data/offers.json` 增加 order 37 的 Agnes 条目。
- 在 `data/providers.json` 增加 Agnes AI 的官方域名、别名和发现 URL。
- 运行现有静态页和 SEO 页生成器，更新首页嵌入数据、详情页、分类页和 sitemap。

## 验收标准

- Agnes 条目通过现有数据 schema 和新增行为测试。
- 首页嵌入数据、Agnes 详情页、API 分类页和 sitemap 都包含该条目。
- 不出现真实 API Key；全量测试、静态生成检查和 diff 检查通过。
- 提交并推送到 `origin/dev`，随后创建生产部署并验证线上 Agnes 详情页返回 200。

## 来源与时效

- https://agnes-ai.com/en/docs/overview
- https://github.com/AgnesAI-Labs/AgnesAI-Models/blob/main/MODEL_CATALOG.md

官方模型目录注明限速和可用性可能变化，因此条目使用 `confidence: medium`，并保留官方来源与复核日期。
