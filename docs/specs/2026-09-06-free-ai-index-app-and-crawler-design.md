# Free AI Index 应用与数据抓取系统设计

日期：2026-09-06  
状态：已确认，进入实施

## 1. 目标

把当前可交互的单文件原型升级为可维护的免费 AI 目录：页面继续保持静态站点的低成本和 SEO 友好性，条目数据从 HTML 中拆出，由抓取器定期读取官方公开来源，检测变化并进入人工审核队列。

首版重点：

- 突出免费 AI IDE，尤其是 CodeBuddy、TraeCode CN、Baidu Comate、Qoder；
- 展示免费机制、额度、有效期、地区、注册要求、官方注册/下载地址；
- 让每条信息都有来源证据、核验时间和状态；
- 支持每日抓取、差异检测和人工确认，不让自动抓取直接发布不确定结论；
- 提供一个可复用的 `free-ai-offer-research` 抓取 skill。

## 2. 非目标

首版不做：统一 API 网关、用户 API Key、代注册、代理转发、绕过验证码或地区限制、实时读取账户余额、在线模型调用测试、复杂后台账号体系和多语言版本。

## 3. 推荐架构

```text
官方公开页面
      │
      ▼
Python 抓取器 ──> 原始快照 ──> 结构化解析 ──> 与上一版比较
                                      │
                                      ▼
                              review-queue.json
                                      │ 人工确认
                                      ▼
                              data/offers.json
                                      │
                                      ▼
                              静态 HTML 页面
```

### 3.1 数据层

- `data/offers.json`：当前已确认、可公开展示的条目。
- `data/sources.json`：来源 URL、来源类型、抓取策略、上次成功时间。
- `data/review-queue.json`：页面变化、解析不确定、来源失败等待人工处理项目。
- `data/snapshots/`：按日期保存规范化快照，便于审计和回滚。

### 3.2 抓取层

- Python 标准库优先，使用 `urllib`/`html.parser` 处理静态页面；需要 JavaScript 渲染的页面只标记为人工核验，不自动执行登录或高频浏览器抓取。
- 每个来源先获取原始内容，再提取有限字段：标题、免费机制、额度、有效期、续费价格、地区、注册要求、官方动作 URL、证据文本。
- 单次网络失败只记录失败，不立即把条目标记为过期；连续失败或官方明确结束时才改变状态。
- 抓取器使用请求间隔、超时、最大响应体和 User-Agent；遵守 robots.txt、服务条款和公开访问边界。

### 3.3 发布层

页面运行时读取同目录 `data/offers.json`。在直接打开 `file://` 时，如果浏览器阻止 `fetch`，保留一个构建脚本把 JSON 注入静态 HTML，确保原型和正式静态部署都能工作。

生产发布先按静态目录处理；每日任务运行抓取和测试，只有人工确认后的 JSON 变化才进入发布分支。

## 4. 数据模型

每个 offer 使用以下字段：

```json
{
  "id": "codebuddy",
  "title": "CodeBuddy · Personal trial",
  "provider": "Tencent Cloud",
  "productType": "free_ide",
  "categories": ["ide", "free"],
  "modelOrRole": "AI coding IDE",
  "originCountry": "China",
  "availability": "China account",
  "freeMechanism": "monthly_quota",
  "quota": "500 credits / month; 5,000 code completions",
  "validity": "Monthly free plan",
  "renewal": "No paid renewal for the listed personal plan",
  "phoneRequired": "unknown",
  "cardRequired": "unknown",
  "commercialUse": "check provider terms",
  "officialActionUrl": "https://www.codebuddy.cn/",
  "sourceUrls": ["https://www.codebuddy.cn/docs/ide/Account/pricing"],
  "evidence": "Official personal experience plan is priced at ¥0...",
  "setupCommand": "Download the CodeBuddy IDE from the official product page.",
  "status": "verified",
  "confidence": "high",
  "lastVerifiedAt": "2026-09-06",
  "checkedBy": "manual",
  "notes": "A free IDE plan is not an unrestricted API key."
}
```

允许值：

- `productType`: `free_ide`, `api`, `coding_plan`, `open_weights`, `payg`；
- `freeMechanism`: `permanent`, `monthly_quota`, `daily_quota`, `trial`, `first_month_promo`, `open_weights`, `not_confirmed`；
- `status`: `verified`, `changed`, `expired`, `unavailable`, `needs_review`；
- `confidence`: `high`, `medium`, `low`；
- `phoneRequired` / `cardRequired`: `yes`, `no`, `unknown`。

免费 IDE、免费 API、网页试用、开放权重和低价付费服务必须通过 `productType` 与 `freeMechanism` 分开，前端不能只依赖一个“free”布尔值。

## 5. 抓取 skill 设计

技能目录：`skills/free-ai-offer-research/`。

### 5.1 技能职责

输入可以是一个产品、一个官方来源列表或全量数据目录；输出为结构化核验报告、规范化 offer、变化 diff 或待审核队列项目。

### 5.2 工作流

1. 收集官方产品页、定价页、FAQ、文档和模型仓库 URL。
2. 判断页面是否公开可访问；不登录、不提交表单、不使用个人密钥。
3. 提取免费机制、额度、有效期、续费、地区、注册要求和官方动作链接。
4. 保存短证据和来源地址，标记证据强度。
5. 与已有记录比较，区分新增、字段变化、来源失败、明确过期和无法判断。
6. 生成 `offers.json` 候选或 `review-queue.json`，不擅自发布有歧义的变化。
7. 输出人工核验清单和下一步动作。

### 5.3 技能参考资料

- `references/source-policy.md`：官方来源优先、访问边界和禁止事项；
- `references/offer-schema.md`：字段、枚举值、证据要求；
- `references/review-checklist.md`：变化确认、价格/期限/IDE 配额核验清单；
- `references/report-template.md`：结构化输出模板。

## 6. 页面改造

- 将当前 `offers` JavaScript 常量迁移为 JSON 数据驱动；
- 保留现有搜索、筛选、排序、详情抽屉、时区提示、复制命令和直接官方动作按钮；
- `free_ide` 条目在首屏有独立高亮区块；
- 数据状态、最后核验时间、免费期限和续费价格始终可见；
- 将 JSON-LD 的 ItemList 和 FAQ 从固定内容改为根据数据生成，避免页面条目与结构化数据不一致；
- 保留 SEO metadata、`llms.txt` 和 `robots.txt`，正式域名确定后替换 canonical 和绝对 URL。

## 7. 定时任务与审核

每日任务执行顺序：

1. 校验 JSON schema 和 URL 格式；
2. 抓取来源并保存原始/规范化快照；
3. 对比上次快照；
4. 运行解析、差异和页面数据测试；
5. 有变化则写入审核队列；
6. 无变化则输出成功摘要；
7. 只有人工确认后才更新公开数据。

审核者需要确认：证据是否仍然来自官方页面、免费类型是否被误读、试用是否会自动续费、IDE 配额是否与 API 额度混淆、地区和账号条件是否发生变化。

## 8. 测试策略

- schema 测试：必填字段、枚举值、日期、URL 和唯一 ID；
- parser 测试：固定 HTML fixture 能提取预期字段；
- diff 测试：新增、变化、过期、来源失败分别生成正确状态；
- policy 测试：非官方来源、登录页、API Key、验证码流程不会进入公开结果；
- 页面测试：JSON 数据能渲染 12 条初始 offer、IDE 筛选显示 4 条、详情按钮跳转正确、无 console error；
- 运行时测试：缺少 JSON、网络失败、字段为空时页面有可理解的错误提示，不白屏。

## 9. 交付顺序

1. 建立数据 schema、初始 JSON 和抓取 skill；
2. 写本地抓取/解析/差异 CLI 和测试；
3. 让前端从 JSON 加载并保留 file 协议下的可运行体验；
4. 增加审核队列和每日任务配置；
5. 完成 SEO/GEO、构建检查和端到端验证；
6. 再考虑正式域名、部署和数据库后台。
