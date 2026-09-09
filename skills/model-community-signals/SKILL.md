---
name: model-community-signals
description: "搬运 AI 模型和工具在其他公开平台上的原生评分、评论、Stars、Likes、Downloads、排名与情绪信号，并按来源展示；触发词：外部评分、平台评分、用户评论、社区反馈、评分搬运、模型口碑、Hugging Face 评分、ModelScope 下载量、GitHub Stars、Arena 排名、community signals、external ratings、review aggregation、rating import、score sync。"
---

# Model Community Signals

铁律：只搬运平台原生信号，不自评分、不自定义评分、不跨平台换算、不计算平均分；每条记录必须带 `sourcePlatform`、`sourceType`、`sourceUrl` 和 `capturedAt`。

## 工作流

- [ ] 第一步：确定对象和来源
  - 根据 `offerId`、模型 ID 或工具 ID 建立映射，确认平台上的名称、版本和实体确实对应。
  - 优先使用公开、可链接、允许引用的页面或 API；加载 `references/source-policy.md`。
  - 把评分、评论、Stars、Likes、Downloads、Rank 和 Sentiment 作为不同指标，不混用。
- [ ] 第二步：采集公开信号
  - 只读取公开 HTTPS 内容；不登录、不抓取私人内容、不绕过验证码、robots 或访问限制。
  - 使用有限请求和响应大小；动态页面无法稳定验证时记录 `needs_review`，不要猜测或补数。
  - 评论只保留短摘录、平台、原文链接、抓取时间和可公开的样本数；不复制整篇评论。
- [ ] 第三步：原样校验
  - 保留平台给出的原始值、满分、数量和标签，例如 `4.3 / 5`、`2.1K Stars`、`12.4K downloads`。
  - 只有平台明确给出评分时才使用 `sourceType=rating`；热度指标不得写成评分。
  - 过滤 token、密码、邮箱、私网地址和敏感查询参数；缺字段标记 `needs_review`，来源失败标记 `source_unavailable`。
- [ ] 第四步：合并和展示
  - 用 `offerId + modelId + sourcePlatform + sourceType + sourceUrl` 去重；`modelId` 在一个 offer 包含多个模型时使用；同一平台新快照覆盖旧快照，其他平台并列保留。
  - 页面标题使用“外部平台信号”或“社区反馈”，不使用“综合分”“本站评分”或“推荐分”。
  - 不跨平台归一化、不平均、不排序成总榜；允许用户按平台原始指标查看。
- [ ] 第五步：输出报告
  - 加载 `references/report-template.md`，列出平台、原始指标、评论摘录、抓取时间、原文链接和核验状态。
  - 无公开评分时明确写“暂无公开评分”；外部信号只能辅助官方价格、额度和可用性核验。

## 本项目集成

外部快照写入 `data/community-signals.json`，通过以下命令校验并合并：

```text
python -m crawler.cli signals --input data/community-signals.json --out data/community-signals.json
```

如果使用独立输入快照，`--input` 和 `--out` 指向不同文件。模型详情页从 `communitySignals` 读取记录，逐个平台展示原始信息。

## 反模式

- 以本站算法给模型打分，或把不同平台分数换算到同一尺度。
- 把 GitHub Stars、下载量或点赞数说成模型质量评分。
- 没有来源链接、抓取时间或样本量仍展示为最新数据。
- 把评论摘录改写成官方承诺、稳定性保证或免费额度证明。
- 登录 G2、Reddit、Product Hunt 或其他平台抓取受限内容。
- 因为某个平台没有评分而用另一个平台的分数补齐。

## 参考资源

- `references/source-policy.md` — 第二步加载，确认公开来源、引用和安全边界。
- `references/report-template.md` — 第五步加载，组织平台信号与评论报告。
