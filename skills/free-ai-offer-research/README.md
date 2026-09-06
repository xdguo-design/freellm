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
python -m crawler.cli scan --sources data/sources.json --out data/snapshots/latest-scan.json
python -m crawler.cli diff --previous data/offers.json --current data/offers.json --out data/review-queue.json
```

## 安全边界

只访问公开官方页面，不登录、不读取 API Key、不绕过验证码或地区限制。页面变化先进入审核队列，再由人工确认发布。
