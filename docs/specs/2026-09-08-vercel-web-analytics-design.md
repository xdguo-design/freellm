# Vercel Web Analytics 接入设计

## 目标

为 FreeLLM 的静态 HTML 页面记录后续页面浏览量与访客数，并通过 Vercel 项目 Analytics 面板查看结果。

## 方案

- 使用 Vercel Web Analytics 官方静态 HTML 脚本。
- 首页直接加入脚本。
- 资源详情页、分类页和指南页由 `scripts/build_seo_pages.py` 统一加入脚本，避免漏页。
- 仅记录页面浏览，不增加自定义事件，不采集业务字段。
- 统计从启用并重新部署后开始，历史访问不补算。

## 验收标准

1. 首页和全部生成的 SEO 页面包含 `window.va` 初始化代码。
2. 页面引用 `/_vercel/insights/script.js`。
3. SEO 页面构建检查、全量测试通过。
4. Vercel 项目启用 Web Analytics 后重新部署，线上脚本请求不再返回 404。

## 范围外

- Google Analytics 或其他第三方分析服务。
- 自定义事件、用户画像和业务转化漏斗。
- 历史访问量恢复。
