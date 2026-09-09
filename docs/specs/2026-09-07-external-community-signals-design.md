# 外部评分与评论搬运设计

## 目标

为每个模型或 AI 工具增加可追溯的外部平台评分、热度指标和公开评论短摘录，帮助用户快速判断，但不生成 Free AI Index 自己的评分。

## 规则

- 平台原生评分原样展示，不跨平台归一化、不求平均、不生成综合分。
- 评分、排名、Stars、Likes、Downloads 和评论情绪是不同指标，必须各自标注。
- 评论只保存短摘录、平台、原始链接、抓取时间和必要的样本信息，不复制整篇内容。
- 公开来源没有评分时显示“暂无公开评分”，不补造数值。
- 外部评分和评论不能替代官方额度、价格、地区、有效期和可用性核验。
- 只访问公开 HTTPS 资源；不登录、不抓取私人内容、不绕过 robots、验证码或访问限制。

## 数据流

```text
公开平台来源
  → 有限抓取 / 手工导入的来源快照
  → 字段校验 + 敏感信息过滤
  → sourcePlatform/sourceType 原样记录
  → 按 offerId 去重合并
  → 模型详情页“外部信号”区块
```

## 数据契约

每条 `communitySignals` 记录至少包含：

```json
{
  "offerId": "qwen3-4b",
  "sourcePlatform": "hugging_face",
  "sourceType": "rating",
  "sourceUrl": "https://huggingface.co/…",
  "value": 4.3,
  "scaleMax": 5,
  "sampleCount": 128,
  "rawLabel": "4.3 / 5 · 128 ratings",
  "excerpt": "短摘录，保留原意，不超过 240 字符",
  "capturedAt": "2026-09-07T00:00:00+00:00",
  "status": "observed"
}
```

当一个 offer 包含多个模型时，可选的 `modelId` 用于标明具体模型，并参与去重；不应把同一 API 入口下不同模型的信号互相覆盖。

`sourceType` 可为 `rating`、`review`、`stars`、`likes`、`downloads`、`rank` 或 `sentiment`。只有 `rating` 可以带 `value/scaleMax`；热度类指标使用 `value` 但必须用 `rawLabel` 和 `sourceType` 明确含义。数据不完整时使用 `needs_review`，来源失败使用 `source_unavailable`。

## 页面行为

- 列表卡片只显示紧凑的外部信号摘要，不显示本站分数。
- 详情抽屉显示各平台原生数据，平台之间分组展示。
- `rating` 显示原始分数和满分；`stars/downloads/likes` 显示原始数量；`review` 显示摘录和来源。
- 按平台筛选或排序属于原始字段操作；默认不按跨平台评分排序。
- 每条数据显示“来源平台、抓取时间、打开原文”以及“暂无公开评分/数据待核验”等状态。

## 工作流位置

放在 `github-peer-discovery` 和 `free-ai-offer-research` 之后：先发现同行线索，再核验官方事实，最后补充外部社区信号。视觉实现仍经过原型选择和页面测试门控。
