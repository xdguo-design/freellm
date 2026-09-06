# China AI API Free Tier Directory 设计规格

日期：2026-09-05

## 1. 产品定位

面向全球开发者的英文目录，整理中国 AI 厂商及其海外区域提供的官方免费 API 额度。核心价值是让用户快速判断：哪个模型可以免费调用、在哪个地区可用、需要什么注册条件、额度何时失效。

产品只收录官方公开的免费额度、免费层和试用额度，不保存、展示或转发真实 API Key，不提供共享 token、代理调用或绕过地区/额度限制的服务。

## 2. 目标用户与成功标准

目标用户：独立开发者、学生、AI 爱好者、SaaS 创业者，以及需要低成本测试中国模型的海外开发者。

首版成功标准：

- 收录 15–30 个经官方来源核验的 API 渠道；
- 用户可按地区、额度类型、注册要求和模型能力筛选；
- 每条记录显示官方来源、最后核验时间和当前状态；
- 每日任务能够发现官方页面或结构化数据变化；
- 不因自动抓取误判政策，所有不确定变化进入待审核队列。

## 3. MVP 页面与功能

### 首页目录

以表格为主，支持搜索、筛选、排序和状态徽章。筛选条件包括 International available、No credit card、No phone verification、Permanent free、Daily quota、Trial credits、OpenAI-compatible，以及 Text、Vision、Audio、Embedding 等模型类型。

### 服务详情页

展示 Provider、Model、Region、Free quota、Quota type、Validity、Phone/Card requirements、Commercial use、API compatibility、官方注册入口、官方定价页、API 文档和 JavaScript/Python/cURL 示例。

### 变更记录页

展示新增、额度变化、地区变化、过期、服务不可用等事件，并显示变化前后摘要、来源链接和核验时间。

## 4. 数据模型

每个渠道至少包含：

- `provider`
- `model`
- `origin_country`
- `region`
- `free_quota`
- `quota_type`：permanent、daily、monthly、trial、limited
- `valid_until`
- `phone_required`
- `card_required`
- `commercial_use`
- `openai_compatible`
- `capabilities`
- `signup_url`
- `pricing_url`
- `docs_url`
- `source_evidence`
- `last_verified_at`
- `status`

免费额度、免费网页聊天和开源模型下载必须分开标注，不能混为同一类。地区、Endpoint 和 API Key 的适用范围也必须单独记录。

## 5. 监控与审核流程

推荐采用 GitHub Actions 每日定时运行，读取官方价格页、免费额度页、区域说明和 API 文档，提取可核验字段，与上一份数据快照进行比较。变化生成 diff 和审核项目；确认后更新 `data.json`，由 Cloudflare Pages 自动发布静态站点。

状态规则：

- `Verified`：官方信息已核验；
- `Changed`：页面或关键字段变化，等待人工确认；
- `Expired`：官方明确显示额度结束；
- `Unavailable`：来源连续检查失败；
- `Needs Review`：信息不完整或自动解析不可靠。

单次页面失败不立即标记失效。监控只检查公开规则和来源可用性，不尝试使用个人 API Key 读取账户余额，也不通过高频模型调用测试额度。

## 6. 技术边界

前端保持纯 HTML、CSS 和 JavaScript，数据由静态 JSON 驱动。首版不需要登录、数据库或用户账户。浏览器端只负责搜索、筛选、详情展示、复制示例和生成分享链接。

定时监控属于站点外的轻量自动化任务，可以使用 GitHub Actions；若以后需要后台审核、用户订阅提醒或历史数据查询，再引入 Serverless API 与数据库。

## 7. 风险与处理

- 免费政策变化快：每条记录显示最后核验时间，并保留变更历史；
- 页面动态渲染或结构变化：自动任务只标记变化，人工确认后发布；
- 额度信息误读：保存官方来源和证据摘要，明确区分试用、周期额度和永久免费；
- API Key 滥用风险：禁止收集真实 Key，页面仅链接到官方注册入口；
- 海外可用性差异：把注册地区、服务部署区域和 Endpoint 区域分别展示；
- 广告影响可信度：优先保证数据质量，广告不出现在筛选和核心结果上方。

## 8. 非目标

首版不做统一 API 网关、模型在线体验、用户上传 Key、自动代注册、代理转发、实时剩余额度、复杂账户体系和多语言版本。

## 9. 后续扩展

在 MVP 稳定后增加 RSS/邮件/Telegram 变更提醒、用户提交失效信息、API 可用性报告、按模型对比、赞助条目和付费数据接口。

## 10. 初步视觉方向

三张 GPT-Image2 视觉方向稿已迁移至 `design/visual-directions/`：

- [方向一：Editorial Directory](../../design/visual-directions/direction-1-editorial.png) — 暖色出版物与可信资料库感；
- [方向二：Monitoring Console](../../design/visual-directions/direction-2-monitoring-console.png) — 深色监控控制台与每日变化提醒；
- [方向三：Swiss Index](../../design/visual-directions/direction-3-swiss-index.png) — 高对比索引工具与快速筛选感。

## 11. 方向三确认后的页面升级

用户已选择方向三（Swiss Free Model Index）。首个高保真原型位于 `design/free-china-ai-index.html`，页面将首页目录扩展为五类可筛选资源：

- Free forever：长期免费但可能限速的模型或工具；
- Free IDEs：带明确免费计划或免费额度的中国编程 IDE；
- Downloadable：可从官方 GitHub、Hugging Face 或 ModelScope 获取的开放权重；
- Cheap coding：首月特价、低价 Coding Plan 和按量计费服务；
- Verify before free：官方存在 API/体验中心，但暂未找到足以证明“免费额度”的公开规则。

每行都要显示免费机制、有效期、访问地区、官方来源和最后核验时间。详情抽屉提供一条经过官方模型仓库或文档核验的下载/配置命令；本地模型区域额外标注“权重免费不等于 GPU 免费”。

比较模块以同一模型的中国端点和国际端点为基准，按每百万输入/输出 Token 对比，并明确提示账号区域、数据驻留和跨境传输约束。Coding Plan 的“半夜优惠”不写成固定的本地午夜优惠，而是保存供应商时区的峰值/非峰值规则，再换算成访问者本地时区。

## 12. 品牌定位修订

公开产品名称统一为 `Free AI Index`。产品主叙事是“免费 AI 与限时免费 AI 的可核验索引”；中国厂商是首要收录来源，但不在品牌名、Hero 标题或首页主导航中单独突出。中国信息保留在供应商、账号地区、Endpoint 和官方来源字段里，用于筛选与决策。
