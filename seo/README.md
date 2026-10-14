# FreeLLM GEO / SEO 审核工具

这里的目标是 **真实、可审计、可重复** 的内容可见度测量，而不是“刷 AI 引用获得 Google 权重”。

## 事实边界

- Google AI Overviews / AI Mode 没有“先被别的 AI 引用即可获得权重翻倍”的机制说明。仍应优先保证可索引、内容实用、内链可发现以及页面结构清晰。官方说明：https://developers.google.com/search/docs/appearance/ai-features
- `llms.txt` 是可选目录，不是 Google AI 功能收录的技术前提。
- Reddit 发言、品牌提及、DuckDuckGo 对 AI 分享页的检索结果，都 **不能** 当作 ChatGPT / Perplexity / Gemini 对某次查询实际引用 freellm.top 的证据。
- 不编造引用、评分、免费额度，也不以 48 小时、3 天或某个排名为保证。

## 基线实验（10 查询 × 4 引擎）

`seo/geo-keywords.json` 是 5 组重点 / 5 组对照的预注册查询与对应落地页。两组均只代表观察设计，不代表已获得自然排名或曝光数据。

```bash
python seo/ai-reference-checker.py
python seo/ai-reference-checker.py --input path/to/observations.csv --output path/to/report.json
python -m unittest tests.test_geo_reference_checker -v
```

`geo-observations.example.csv` **仅有表头，没有任何虚构的基线数据**。使用前复制为本地观察记录 CSV：

| 列 | 说明 |
|---|---|
| checked_at | 带时区的 ISO8601 时间，如 `2026-10-14T08:00:00+08:00` |
| engine | `chatgpt_search`, `perplexity`, `gemini`, `google_ai_mode` |
| query | 必须匹配 `geo-keywords.json` 中的完整问题 |
| result | `cited` 表示人工看到来源链接；`not_cited` 表示人工执行查询但未看到链接 |
| cited_url | 仅 `cited` 必填；必须是指向 freellm.top 的 HTTPS 直接来源链接 |
| evidence_url | 可供核对的公开答案链接（无则留空） |
| evidence_path | 无公开答案链接时，保存截图或证据文件的本地相对路径 |
| notes | 地区、登录状态、语言、个性化设置、特殊情况等 |

- 脚本 **不会主动向 AI 服务发送查询**，不会自动核对截图真假；`cited` 代表人工观察，不能标成 API 验证结果。
- 没有记录时输出 `not_checked`（UNKNOWN），而不是 0 引用。记录未引用时才用 `not_cited`。
- 同一个引擎 + 查询只比较最新检查时间；同一时间不可同时记录正反结论。可以同一轮记录多个不同引用 URL。
- 不在 Git 中提交私人聊天记录、含身份信息的截图、令牌或 Search Console 导出。

## 与 Search Console 分开看

Search Console 数据由用户授权的真实账号导出；本脚本不连接 Search Console，不能声称抓取了 Google 排名、自然点击或“AI 权重”。流量、曝光与索引状态需要与这个人工引用观察表 **分表** 追踪。

Google 说明 AI 功能的表现主要包含在 Search Console 的网页搜索表现中，不能拿手工 ChatGPT 输出替代 GSC 统计。参见 [实验执行文档](../docs/marketing/geo-experiment-2026-10-14.md)。

## 其他存量工具

- `scripts/generate_schema.py` 生成实验用 JSON-LD 片段，**不是已自动全站注入**，不能把试用、限时优惠都宣称为永久价格 $0；上线之前逐项核对显示文本与 JSON-LD。
- `seo/about-qna-structure.html` 是可读性重构模板，FAQPage 不应当作 Google 排名捷径。
- `seo/hreflang-generator.py` 生成语言标记候选，须与站点实际独立 URL / canonical 匹配后才能接入。
