# free-ai-offer-research

用于研究免费 AI、免费 IDE、限时试用、Coding Plan、开放权重和低价模型。

## 使用方式

把以下自然语言任务交给 Agent：

- `抓取并核验 CodeBuddy、Trae、Comate、Qoder 的免费 IDE 额度`
- `扫描所有来源，找出今天价格、免费额度或有效期变化的模型`
- `新增一个中国 AI 工具，判断它是否真的免费`

技能输出官方来源、证据摘要、免费机制、有效期、注册条件、置信度和人工审核建议。

## 项目 CLI

```text
python -m crawler.cli validate data/offers.json
python -m crawler.cli scan --sources data/sources.json --out data/snapshots/latest-scan.json --timeout 8
python -m crawler.cli discover --providers data/providers.json --out data/candidates.json --scan-out data/snapshots/discovery-scan.json --max-links 5 --max-pages 100 --timeout 8
python -m crawler.cli coverage --providers data/providers.json --scan data/snapshots/latest-scan.json --scan data/snapshots/discovery-scan.json --candidates data/candidates.json --out data/coverage.json
python -m crawler.cli diff --previous data/offers.json --current data/offers.json --out data/review-queue.json
```

## 安全边界

只访问公开官方页面，不登录、不读取 API Key、不绕过验证码或地区限制。`discover` 会扫描供应商注册表、更新日志、价格页、FAQ、活动页和官方模型仓库，把新发现写入 `data/candidates.json`，不会直接覆盖 `data/offers.json`。

## 防止数据缺少和误发布

- 供应商覆盖由 `data/providers.json` 管理，每个供应商必须有别名、官方域名和至少一个发现入口。
- 同一来源通过规范化 URL 去重，并记录 `firstSeenAt`、`lastSeenAt`、`seenCount`，避免重复或短暂波动造成丢失。
- 单次抓取失败只记录来源不可用，不标记过期；连续失联、明确截止日期和价格/额度变化进入人工审核。
- 每个免费额度、首月促销、夜间优惠、IDE 免费层和开放权重作为独立候选保存，避免一个供应商的多个权益相互覆盖。
- 每日生成 `data/coverage.json`，公开供应商数、来源成功数、失败数、漏扫供应商和过期候选数；目录只承诺“已注册供应商范围内的覆盖”，不声称找到互联网中的全部模型。
