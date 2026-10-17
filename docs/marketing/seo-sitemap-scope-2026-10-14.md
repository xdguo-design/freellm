# Sitemap 收录范围复核 — 2026-10-14

本次 GEO 工作中现存的 `tests/test_search_console_regressions.py` 门禁指出：`222 > 220`。这不是两个相同 URL。

按 `dev` 分段 sitemap 实数统计：

| 分段 | URL |
|---|---:|
| pages | 50 |
| offers | 78 |
| providers | 50 |
| models | 35 |
| english | 9 |
| **总数** | **222** |

对 5 份 XML 的所有 `<loc>` 做了去重检查：**222 个不同 URL，0 个重复**。存量测试还要求 sitemap URL 指向存在的 HTML 页面且非 noindex。并未因为 URL 超标而随意删除 `/models/all/page/10/` 等合法分页页面，或更改 canonical/noindex。

因此明确复核后，将**仓库自设**的预算线由 220 调整到 **225**（仍为小幅限额，新增加超过 3 个 URL 会失败并要求再次审核）。此值是项目内部的防扩张阈值，**不是 Google 的 sitemap 技术上限**，也不是任何 SEO 排名因素。Google 文档提到单份 sitemap 的一般限制为 50,000 URLs / 50MB。

守住以下真实约束：确保只提交需要被搜索结果展示的规范 URL；重要网页可通过站内链接找到；内容不重复、非 noindex；以后新增页面要有用户价值、来源和维护责任。

来源：https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

复核范围：仅当前 dev 的 sitemap 文件，不等于已检查 Google 实际收录，后者需 Search Console 真实数据。
