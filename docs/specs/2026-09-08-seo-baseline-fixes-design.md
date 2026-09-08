# SEO 基础修复设计

## 目标

让生产首页和自动生成的 SEO 页面在首次返回 HTML 时就能被搜索引擎按中文页面理解，并补齐分享卡片所需的绝对 URL 与图片信息；语言切换仍保留为前端增强功能，不新增 `/en/` 页面。

## 范围

- 修改 `design/free-china-ai-index.html` 的默认静态语言、标题、描述、canonical、Open Graph 和 Twitter 元数据。
- 将首页第二个可见 `<h1>` 降级为 `<h2>`，保留视觉层级但保证页面只有一个主标题。
- 修改 `scripts/build_seo_pages.py`，使详情页和分类页默认声明 `zh-CN`，输出中文页面标题/描述/导航文案，并补齐绝对 canonical、Open Graph、Twitter 元数据和 `og:image`。
- 重新生成 `offers/`、`category/`、`guides/`、`.seo-pages-manifest.json` 和 `sitemap.xml`。
- 增加静态元数据回归测试。

不在本次范围内：Search Console 接入、关键词内容生产、真实地区 PageSpeed 测试、英文 `/en/` 页面和 `hreflang`。

## 方案

首页使用中文作为服务器直接返回的默认内容。`?lang=en` 仍可由现有 JavaScript 改变界面文案，但不再是搜索引擎获得中文元数据的必要条件。页面的 canonical 和社交 URL 始终指向 `https://freellm.top/`，分享图片使用仓库现有的 `freellm-01-hero.png`。

生成器新增统一的页面元数据常量和小型渲染辅助函数，详情页/分类页/指南页沿用现有静态生成流程，不引入框架或运行时依赖。中文字段优先使用已有 `*_zh` 字段；资源标题和事实数据保持原始名称，避免未经证实的翻译改变语义。

## 可观察行为

- 首页初始 HTML 的 `<html lang>` 为 `zh-CN`。
- 首页初始 `<title>`、description、Open Graph 和 Twitter 描述均为中文或包含明确中文定位。
- 首页仅包含一个可见 `<h1>`。
- 首页 canonical、`og:url`、`og:image` 和 Twitter image 为生产绝对 URL。
- 生成的详情页和分类页初始语言为 `zh-CN`，页面元数据和主要导航文案为中文，并带绝对分享 URL。
- sitemap 只包含生产绝对 URL，且重新生成后数量与页面文件一致。
- 现有文件协议、HTTP 数据加载、语言切换和详情抽屉测试继续通过。

## 验证策略

先为首页与生成器元数据写失败测试并运行确认 RED；再做最小实现并分批运行测试确认 GREEN；最后运行完整 `pytest -q`、静态构建检查和 SEO 生成器检查，审阅 diff 只包含本次 SEO 范围内的文件。

## 风险与回滚

- 现有工作区有用户未提交变更，实施前不重置、不覆盖无关文件。
- SEO 页面为生成文件，模板变更后必须重新生成并用 `--check` 验证。
- 首页英文切换依赖现有脚本，静态默认中文不会移除该交互能力。
- 如测试发现旧的英文 UI 断言与新默认语言冲突，只调整测试的默认语言预期，不删除英文切换覆盖。
