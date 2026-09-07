---
name: free-ai-offer-research
description: "抓取、核验和比较公开的免费 AI、免费 IDE、限时试用、Coding Plan、开放权重和低价模型信息，并生成结构化 offer、证据摘要和变化审核队列。触发词：抓取 AI、抓取模型、免费模型、免费 IDE、AI 价格、免费额度、试用额度、限时优惠、Coding Plan、开放权重、数据核验、价格变化、quota check、AI offer research、web scraping、crawl pricing、scan sources。"
---

# Free AI Offer Research

铁律：只访问官方公开来源；不登录、不提交表单、不读取或保存 API Key，不绕过验证码、地区限制或访问控制；任何不确定变化进入人工审核，不直接发布。

## 工作流

- [ ] 第一步：确认任务范围
  - 判断是单个产品核验、全量来源扫描、变化比较还是新增条目。
  - 优先使用用户给出的官方页面；没有官方来源时，将结果标为 `needs_review`。
- [ ] 第二步：收集来源
  - 加载 `references/source-policy.md`。
  - 只保留官方产品页、价格页、FAQ、文档、官方 GitHub、官方 Hugging Face/ModelScope 仓库。
  - 检查 HTTPS、域名白名单和公开访问边界。
- [ ] 第三步：提取证据
  - 提取产品类型、免费机制、额度、有效期、续费价格、地区、手机号/银行卡条件、官方动作 URL。
  - 加载 `references/offer-schema.md`，不使用未定义字段或模糊的“免费”标签。
  - 每个关键结论保留来源 URL 和短证据原文摘要。
- [ ] 第四步：核验分类
  - 区分免费 IDE、免费 API、网页试用、首月促销、开放权重和低价按量付费。
  - 免费 IDE 不等同于免费 API；模型权重免费不等同于 GPU、存储和推理免费。
  - 解析失败、页面动态化、规则不完整或地区条件不明时设置 `needs_review`。
- [ ] 第五步：生成结果
  - 加载 `references/report-template.md`。
  - 输出结构化 offer、证据表、置信度、发现的问题和建议动作。
  - 如果是全量扫描，生成新增、变化、来源失败和明确过期项目。
- [ ] 第六步：发布门控
  - 加载 `references/review-checklist.md`。
  - 价格、额度、有效期、自动续费、注册条件和地区变化必须由人工确认。
  - 未经确认只能写入审核队列，不能覆盖公开 `data/offers.json`。

## 输出规则

每次输出必须回答：

1. 这个服务是什么类型？
2. 为什么能叫免费、试用、促销、开放权重或低价？
3. 免费/优惠持续多久？是否自动续费？
4. 谁可以注册？是否需要中国手机号、银行卡或特定地区？
5. 官方注册/下载/模型地址是什么？
6. 证据来自哪些页面？哪些字段仍未确认？

## 反模式

- 不把搜索结果、博客、论坛、推广文章当成唯一证据。
- 不把“有免费试用”写成“永久免费”。
- 不把首月价格写成长期价格。
- 不把免费 IDE 的内置额度写成 API 额度。
- 不为了确认额度而调用用户账户、消耗模型额度或保存密钥。
- 不因为一次超时就标记服务过期。
- 不自动覆盖人工已经确认的字段。

## 参考资源

- `references/source-policy.md` — 第二步加载，判断来源和访问边界。
- `references/offer-schema.md` — 第三步加载，规范字段和分类。
- `references/review-checklist.md` — 第六步加载，执行发布前人工核验。
- `references/report-template.md` — 第五步加载，组织最终输出。

## Automated discovery and coverage gate

For every full scan, load the provider registry from `data/providers.json` and run:

```text
python -m crawler.cli discover --providers data/providers.json --out data/candidates.json
```

Discovery may find candidates automatically, but it must not directly publish them to `data/offers.json`. Every candidate starts as `needs_review` and keeps its official source URL, evidence, matched keywords, first-seen time and last-seen time.

The daily job must also produce a coverage report. Coverage means the number of registered providers and official sources scanned, successful and failed sources, missing providers, stale candidates and pending review items. A source failure is `source_unavailable`, never `expired`; a single failed request must not delete or downgrade an existing offer.

The publication gate requires an official pricing page, FAQ, documentation page, announcement or official model repository. Promotions, new-user credits, night-rate rules and free IDE quotas are separate benefits even when they belong to the same provider. The public directory is complete only relative to the registered provider set, so the page and reports must expose coverage instead of claiming that every model on the internet was found.
