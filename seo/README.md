# GEO 工具集

四件套：结构化数据生成、Q&A 页面重构模板、AI 引用监测、hreflang 生成。

## 1. Schema 标记（第1步）

```bash
python scripts/generate_schema.py          # 输出到 seo/schema/
python scripts/generate_schema.py --out /custom/path
```

从 `data/offers.json` 的 40 个已核验产品批量生成合规 JSON-LD：

- `products.schema.html` — 40 个节点（29 Product + 11 SoftwareApplication），含 Offer 价格、库存状态、品牌
- `faq.schema.html` — 站点级 FAQPage（4 个问答）
- `manifest.json` — 生成元信息

**接入方式**：把文件内容（`<script type="application/ld+json">...</script>`）粘到对应页面的 `<head>` 里；建议在 `scripts/build_static.py` 构建流程末尾追加注入步骤，实现全自动。

**刻意不生成 aggregateRating/review**：目录没有真实用户评分数据，编造评分违反 Google 结构化数据垃圾政策（会吃 manual action），也违背本站"不伪造评分"原则。等有真实评论数据后在 `build_product_node` 里补上即可。

## 2. Q&A 页面重构（第2步）

模板：`about-qna-structure.html`

以 about 页内容为样本，把长段落重构为 `H2问题 + <section>答案` 结构（10 个问答）。

**接入建议**：站点页面是双语结构（`lang="zh-CN"` / `lang="en"` 切换），自动改写容易破坏双语切换，因此采用手工模板方式。新页面直接按此结构写；存量页面迁移时保持 `lang` span 结构，每个 `<section>` 对应一个问答。配套的 FAQPage schema 已由第1步的 `faq.schema.html` 提供，两者内容保持一致。

## 3. AI 引用监测爬虫（第3步）

```bash
python seo/ai-reference-checker.py         # 全量关键词 × 3引擎
```

纯 `requests + BeautifulSoup`，输出 JSON 报告（每个关键词下各引擎是否引用、引用位置、引用次数）。

**实现要点**（已实测验证）：

- 检索通道用 DuckDuckGo HTML 版（`html.duckduckgo.com`）——直接爬 Google 在无 JS 环境下拿不到结果（返回降级页，0 个结果标签，已实测确认）
- DDG 对连续请求限流：脚本内置指数退避重试（最多 3 次）；实测第 3 次退避后成功
- 重定向链接自动解码（`uddg=` 参数还原真实 URL）
- 解析器已通过对照组验证：`site:perplexity.ai` 检索返回 10/10 条正确解码结果

**当前基线**：freellm.top 在三个引擎域名内引用数为 0（新站正常，先建立基线再追踪增长）。

**已知局限与升级路径**：

- `site:chatgpt.com` 等只能覆盖公开索引的分享页，ChatGPT 对话内容本身不可索引
- 更可靠的方案是官方 API：Perplexity 的 `search` 端点、OpenAI 的 web-search 工具都返回 citations 字段，需要 API key；本脚本定位为零成本批量监测
- 全量跑（7 关键词 × 3 引擎）受限于限流约需 3-5 分钟，建议 cron 夜间执行并在两次请求间保持 ≥3 秒间隔

## 4. hreflang 生成器（第4步）

```bash
python seo/hreflang-generator.py
```

输入 URL 列表（在 `main()` 里配置），输出四种产物：HTML `<head>` 标签块（含 x-default）、XHTML 格式、sitemap.xml 条目、JSON 配置。

**注意**：本站现有双语方案是单 URL + `?lang=` 查询参数 + JS 切换（见 `about/index.html`），hreflang 已在存量页面上配置。若未来迁移到独立路径方案（如 `/en/about/`），用此生成器批量产出标签。

## 文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `scripts/generate_schema.py` | Schema 批量生成（数据驱动） | ✅ 已验证 |
| `seo/schema/*.html` | 可嵌入 `<head>` 的 JSON-LD | ✅ 已生成 |
| `seo/about-qna-structure.html` | Q&A 重构模板 | ✅ 模板 |
| `seo/ai-reference-checker.py` | AI 引用监测爬虫 | ✅ 已验证 |
| `seo/hreflang-generator.py` | hreflang 批量生成 | ✅ 已验证 |
