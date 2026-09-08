# SEO 详情页与分类页设计

## 目标

把当前单页 AI 资源目录扩展为可被 Google 独立发现和收录的静态页面体系。每个资源拥有稳定详情 URL，每个主要筛选分类拥有分类 URL；首页、分类页和详情页互相链接，站点地图只列出这些规范 URL。

## 现状与边界

- 现有站点是静态 HTML + `data/offers.json`，Vercel 根路径重写到 `design/free-china-ai-index.html`。
- 当前 `offers.json` 有 36 条资源，数据已有标题、免费机制、资格、额度、来源、使用指南和核验日期。
- 不新增后台、数据库或登录系统；不自动向社交平台发帖。
- 保留现有首页筛选、详情抽屉、语言切换和数据加载行为。

## URL 设计

- 首页：`/`
- 资源详情：`/offers/<offer-id>/`
- 分类页：`/category/<slug>/`
- 详情页和分类页使用稳定的小写 slug；slug 来源于现有数据 ID 或固定分类映射，不使用中文、查询参数或随机值。
- 每个页面 canonical 指向自身的 `https://freellm.top/...` URL；预览域名不进入生产 sitemap。

## 页面内容

### 资源详情页

静态输出完整 HTML，包含唯一 `<title>`、description、canonical、Open Graph、`WebPage`/`BreadcrumbList`/`SoftwareApplication` 结构化数据（仅使用数据中可证实的字段），以及：资源概述、免费方式、额度/价格、有效期、地区与前置条件、步骤、官方来源、最后核验日期、相关资源。

### 分类页

为现有筛选分类生成 7 个页面：free quota、free IDE、API、promotion、student、web、download/open weights。页面包含分类说明、资源数量、资源卡片、详情页链接和返回首页链接。分类匹配复用首页 `offerCategories` 的业务规则，避免分类页与首页筛选结果不一致。

## 生成与发布

- 新增 `scripts/build_seo_pages.py`，从 `data/offers.json` 读取数据，使用标准库生成根目录下的 `offers/`、`category/` 页面和 `sitemap.xml`。
- 生成脚本支持默认写入和 `--check` 校验；缺少资源 ID、重复 slug、无效数据或生成结果过期时返回非零状态。
- 首页动态资源卡片增加详情页和分类页可爬取的 `<a>` 链接，同时保留原有详情抽屉按钮。
- `robots.txt` 继续允许抓取并指向生产 sitemap；README 说明生成命令和 SEO 页面结构。

## 错误与数据边界

- 生成前复用 `validate_offers`，不为缺失字段编造文案。
- HTML 文本和 URL 参数必须转义；外部官方链接继续使用数据中的 HTTPS 地址。
- 没有有效资源的分类不生成页面；sitemap 不列出空分类页。
- 资源状态变化不会删除历史 URL；详情页仍展示当前状态和官方核验信息，避免旧链接失效。

## 验收标准

1. 36 条有效资源各生成一个 `/offers/<id>/index.html`，且每页有唯一标题、canonical、资源正文和官方链接。
2. 7 个有资源的分类各生成一个 `/category/<slug>/index.html`，并列出与首页筛选相同的资源集合。
3. 首页能通过普通 `<a href>` 到达详情页和分类页；详情页能回到首页并链接相关资源。
4. sitemap 包含首页、所有生成的详情页和分类页，使用完整生产 URL，无预览 URL。
5. `pytest -q`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check` 全部通过。
