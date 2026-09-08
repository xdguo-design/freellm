# OpenAI 与 Claude Code SEO 指南页设计

## 目标

为 `openai` 与 `claude code` 两组搜索意图提供可独立收录、可验证、不夸大免费承诺的英文 SEO 页面，并把它们接入现有 FreeLLM 目录的内部链接和 sitemap。

## 页面范围

### `/guides/free-openai-api-alternatives/`

定位为“OpenAI-compatible free API alternatives”，明确说明 OpenAI 官方 API 不承诺永久免费；内容从现有已验证条目生成，重点比较 Groq、Cerebras、LongCat、Hugging Face、SiliconFlow 等真实入口。页面包含免费条件、注册/地区限制、Base URL、OpenAI SDK 示例和官方来源链接。

### `/guides/claude-code-free-alternatives/`

定位为“Free Claude Code alternatives”，说明 Claude Code 接入需要兼容的 Anthropic 配置或专用 Coding Plan；重点链接现有 GLM Coding Plan，并列出可用于编码工具的相关 API/模型入口、限制、地区条件和官方文档。页面不声称 Claude 官方服务永久免费。

## 生成方式

- 在 `scripts/build_seo_pages.py` 中增加两个固定指南页渲染器，复用现有 `_esc`、`_absolute`、社交元数据、分析脚本和页面 CSS 模式。
- 页面使用 `Article`、`BreadcrumbList` JSON-LD；可见正文与元数据使用英文，所有免费条件和限制与已有数据一致。
- 页面通过现有 `main()` 构建流程生成，写入 `guides/.../index.html`，并自动加入 sitemap。
- 首页或现有指南页增加两个入口，形成至少一层内部链接。

## 验收标准

- 两个 URL 返回静态 HTML，含唯一 `<title>`、description、canonical、H1、英文目标关键词和官方来源链接。
- 两个 URL 均出现在 sitemap；页面没有 `noindex`。
- OpenAI 页面不把官方 OpenAI API 描述成永久免费；Claude Code 页面不把 GLM Coding Plan 描述成 Claude 官方服务。
- 生成测试覆盖页面、sitemap、内部链接和关键免责声明。
- 全量测试、静态构建检查和 SEO 构建检查通过后再部署。
