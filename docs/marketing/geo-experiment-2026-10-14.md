# SEO / GEO 可验证实验（2026-10-14）

**状态：站内工具与观测方案准备；GSC 基线和 AI 答案引用尚未实测。**

## 本轮优先利用已经发布的页面

FreeLLM 已存在相关专题，不再批量新建“AI 扩写 800 字”的薄内容页。实验登记在 `seo/geo-keywords.json`，重点组（treatment）覆盖：免费 LLM API、无需信用卡条件、免费编程工具、搜索 API、国内免费 API。对照组（control）覆盖 OpenAI 兼容替代、开放权重模型、模型大列表、Claude Code 替代与上下文窗口。

这些关键词只是**测试假设**，未获取 GSC 搜索量数据，不能声称低竞争、已排名或可提升至前三。五个重点页面与五个对照页面均已在现有站点目录中有落地路径。只有在记录 T0 后，才进入实质性内容改动；否则无法做因果比较。

## 可审计的执行顺序

1. **T0：** 在 Search Console 导出过去 28 天按页面/查询的 impressions、clicks、CTR、average position，并记录同一日期范围、国家、设备和搜索类型。若 GSC 没有指定长尾词曝光，标记 `UNKNOWN`；不要填零排名。
2. **T0：** 在 ChatGPT Search、Perplexity、Gemini、Google AI Mode 使用预注册的 10 条原始问题人工观察，每个引擎每个查询记录一次，关闭记忆或使用无历史会话（若服务支持），保留来源 URL 或截图，并注明地区、账号及模型版本；不能保证完全消除个性化。
3. **重点组：** 只更新确有官方证据、独家观测或真实使用流程的数据字段：来源、免费机制、续期方式、地区与卡要求、核验日期、API 代码、KNOWN/UNKNOWN。没有官方证据的数字不能用 AI 编造。详情页和指南必须可互相发现。
4. **对照组：** 不特意进行 GEO 文案改写；正常事实纠错、安全修复可进行，须在变更日志记录污染因素。
5. **T+7、T+14、T+28：** 重复相同问题、地区/设备和 GSC 筛选。记录源链接是否直接指向 freellm.top；品牌提及、分享页被搜索到不算引用。
6. **判定：** 分别比较 Google organic 的 clicks / impressions / average position 与手工答案的 `cited / not_cited / not_checked` 比例。样本很小，只能提供方向性信号；不能归因成“AI 认可导致 Google 排名上涨”。

## 用户可用的可核验差异点

- `/offers/` 目录：官方来源、免费条件、到期/地区、注册与核验状态（有数据才写）。
- `/logs/`：公开的发现和验证记录；需按真实扫描日期展示，不能将历史记录伪装成“今日新增”。
- `/models/all/`：模型与地区可用性标记；UNKNOWN 不能强行判为可用。
- `/feed.xml`：公开更新订阅；适合作为社区讨论时的透明来源。
- `/guides/free-openai-compatible-apis/`、`/guides/china-free-ai-api/` 等：按用户任务组织，可连接详情页。

## 不做的事

不批量向 Reddit 发带有隐蔽利益关联的回复、不抓取私人 AI 会话、不用 DuckDuckGo 的 `site:chatgpt.com` 冒充引擎引用计数、不编造“3 天冲第一”的实验结果、不把 FAQ schema 或 llms.txt 说成 Google 排名要件。

## 外部依赖和验收

- **现在完成：** 改正引用统计定义、关键词/实验组预注册、记录格式、脚本与回归测试，README 明确边界。
- **需访问真实 GSC 账号：** 查询词与着陆页基线、索引与自然流量比较；账号未授权时标记 UNKNOWN。
- **需人工或合法 API 实测：** 四个 AI 引擎的答案引用；空数据不能写 0 次引用。
- **需部署到 main 才能确认：** 公网可抓取、Search Console 收录变化与持续流量趋势。dev 不等于已上线。

参考：
- https://developers.google.com/search/docs/appearance/ai-features
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://developers.google.com/search/docs/essentials/spam-policies
