# SEO 技术审计与修正设计

日期：2026-10-03

## 目标

让仓库内的 SEO 质量审计对应 Vercel 实际发布的静态页面，减少本地临时文件、未发布设计稿和迁移重定向造成的误报；基于审计结果修复确实在线且可索引页面的技术元数据问题，并确认 sitemap、canonical、robots 与内链彼此一致。

## 当前情况

- `scripts/audit_seo_metadata.py` 递归检查 HTML 文件，但当前排除规则未覆盖 `.tmp-*`、本地浏览器目录等文件；第一次扫描得到 1,014 个页面并包含本地文件。
- 排除临时构建与浏览器目录后，审计得到 658 个 HTML 页面，其中 474 个显式 `noindex`。
- 当前提示包括 `/community/`、`/guide/`、`/workflow/` 标题长度较短，前两个页面描述较短；`/skills/lab/` 是旧迁移页，缺 description 且正文很短，但 `vercel.json` 已将此 URL 永久重定向到 `/workflow/`。
- `design/updates.html` 与 `/logs/` 有重复标题和描述；`.vercelignore` 已将前者排除发布，因此不应将其作为线上重复页面报告。
- `scripts/check_internal_links.py` 已检查站内链接、sitemap URL 对应文件、canonical 一致性和 sitemap 不含 `noindex` 页面；`vercel.json` 已重写首页，并配置 `/skills/lab/` 永久跳转。

## 设计

### 1. 以发布边界限定审计输入

调整 `scripts/audit_seo_metadata.py` 的页面收集规则，使其排除 Vercel 明确忽略的开发/本地目录和未发布设计稿，包括 `.tmp-*`、`.playwright-mcp/`、`.workbuddy-ai/`、缓存、截图、`design/updates.html` 和 `Temp/`。`Temp/` 当前是未跟踪的本地验证目录，含临时 HTML、日志和截图；将它加入 `.gitignore` 与 `.vercelignore`，使 Git 部署和本地 CLI 部署都不会将其误当作网站页面或输出物。保留其他公开静态页面与有意发布的 `noindex` 页面。排除规则保持明确、可读，并与 Vercel 发布边界同步。

### 2. 分开处理可索引内容页与跳转/排除页

标题、描述、正文长度和重复元数据质量门槛只用于公开且可索引的内容页。审计从 `vercel.json` 读取永久跳转源，将其归类为 `redirect_source` 并跳过内容页元数据门槛；`noindex` 页面和传统 meta-refresh 兼容页也单独分类，不将其缺少内容型元数据误报为索引页问题。中文页面的长度提醒应视作人工复核信号，避免仅凭字符数阈值强制改写准确文案。

### 3. 只修复确认在线的问题

审计确认后，优先在对应静态页面源或 `scripts/build_seo_pages.py` 生成模板中修复唯一标题与描述；生成内容通过现有构建流程更新。不要手改生成 HTML 后造成模板与产物分叉。对跳转地址保留现有永久重定向行为，并保证迁移源不会作为重复内容提交给搜索引擎。

### 4. 核对站点地图、canonical、robots 与内链

扩展 `scripts/check_internal_links.py` 的 HTML 遍历，使其覆盖全部将发布的 HTML 页面（包括当前 `SCAN_ROOTS` 遗漏的 `/workflow/`、`/community/` 和 `/guide/`），并使用与 SEO 元数据审计一致的本地/未发布排除规则。校验 sitemap 中的 URL 均可解析到页面、主机与 canonical 一致、无 `noindex` 页面进入 sitemap、公开页面无失效站内链接或 `?lang=` 链接，并确认 `robots.txt` 中的 `Sitemap:` 指向当前 sitemap index。只有发现具体不一致时才改 `robots.txt`、sitemap 生成逻辑或路由配置；当前不预设需要改这些文件。

## 范围外

- 不重写关键词策略、指南正文或营销文案。
- 不连接 Search Console、外部爬虫或第三方分析服务。
- 不调整语言 URL 方案、hreflang 策略、广告和页面视觉。
- 不批量改变现有 `noindex` 决策；发现疑似异常时记录具体 URL 和原因后再单独评估。

## 验收标准

- 元数据审计不再扫描临时工作文件、本地浏览器数据或 Vercel 排除的设计稿。
- `Temp/` 不再被 Git 或 Vercel 部署边界当作站点内容。
- `/skills/lab/` 被识别为永久重定向源，不再作为缺少描述或正文过短的索引页告警。
- 线上可索引页面的缺失或重复 title/description 等真实问题得到修复；中文长度告警不会单独触发无依据的文案改写。
- sitemap、canonical、robots 与站内链接通过既有离线校验器的一致性检查；若出现未解决问题，逐项记录并说明原因。
- 所有现存未提交改动均予以保留；生成产物只在对应生成器更新后重建。

## 验证策略

先审阅现有生成源与路由规则，再限定审计范围并修复查实的问题。完成后运行 SEO 元数据审计和现有离线内链/sitemap 校验器，审阅输出与工作区 diff，确认没有覆盖用户已有改动或引入未发布文件的误报。

## 风险与回滚

- 当前工作区已有大量未提交修改，其中包括 `scripts/build_seo_pages.py`、SEO 页面产物和 sitemap；实施必须在现有文件状态上做最小增量修改，不重置、不覆盖无关变更。
- `Temp/` 下已有未跟踪的本地检查产物；只修改 ignore 规则，不删除或移动其中任何文件。
- `.vercelignore` 与审计排除规则可能随站点发布配置演变；后续更改发布边界时应同步更新审计规则。
- 标题/描述长度是提示性规则而非排名保证；修改以页面实际主题与事实准确性为先。
