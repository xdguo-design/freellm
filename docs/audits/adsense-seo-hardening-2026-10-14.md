# FreeLLM：SEO / AdSense 内容质量复审（2026-10-14）

## 证据等级

**确认**：站点公开源码已包含 ads.txt、AdSense 发布商脚本、隐私政策、关于页和联系页。它们只证明技术接入的一部分，不意味着账号获批、广告展示、Cookie 同意消息或 Auto Ads 后台配置已完成。

**可能的风险，未定因**：Google AdSense 对原创内容、页面完整度和导航有要求；站点部分目录页、模型/提供商聚合页可能出现内容模板化、独立价值不强，不能仅凭 HTML 或字数推断 Google 的拒绝理由。最终诊断必须读取 AdSense 后台“网站”中的实际问题标签。

**公众号资料借鉴**：公开可检索的中文文章如腾讯云开发者社区《公众号文章如何服务 AI 搜索获客》强调“一个问题、答案前置、H2/H3、证据与独立站互证”。但本次没有取得可靠、可核验的 mp.weixin.qq.com 原文，因此不能声称直接逐篇阅读了微信公众号文章，也不采信 GEO 权重百分比或“3 天上首页”承诺。

## 本次落地

- 新增 scripts/audit_adsense_content.py：以五份 sitemap 的 URL 为入口，解析发布版 HTML 中可见的主要文本，排除导航、JS、页脚；将过薄、缺少外部来源线索、无 main 等标记为 review，输出 JSON 报告供逐页人工检查。
- 新增 tests/test_adsense_content_audit.py：回归覆盖内容提取、薄内容提示、sitemap 缺页、真实站点遍历。
- 浏览器流水线增加站点内容盘点步骤。只有缺失 sitemap 目标文件等客观技术错误才失败，不将启发式内容质量阈值当作 Google 审核政策。
- 继续使用现有 scripts/check_adsense.py 的发布商匹配、隐私披露、无索引页禁广告、AdSense 脚本完整性检查。

## 风险修复顺序

1. 打开 AdSense 后台 Sites 与 Policy Center，记录具体拒审分类（不得公开账号凭证与完整截图）。官方会提供的常见类型包括内容不足、原创质量、导航、政策、站点连接，但不能先入为主。
2. 通过 CI 日志或者本地执行 python scripts/audit_adsense_content.py --report .tmp/adsense-editorial-inventory.json；先审查 guides、offers、providers 等主入口的 review 页面。
3. 内容增强必须有官方价格/额度/地区来源、明确核验日期、原创的选择逻辑/接入步骤和失败条件。未知额度写 UNKNOWN；对于大量内容很薄的页，应优先合并有价值的主题或者保留 noindex，不要机械扩写 800 字。
4. 保持首页与关键内容页有 AdSense 授权代码，同时核查 Auto Ads 对政策页、纯工具/登录、搜索空结果页的 URL 排除。当前代码并不能读取或修改 AdSense 后台的排除设置。
5. 确认合法隐私通知、受影响地区的认证 CMP 同意设置，然后在 AdSense 后台手动请求重新审核。未完成前不要以“广告已开通”描述网站。

## 参考

- Google AdSense 网站准备：https://support.google.com/adsense/answer/12176698
- Google AdSense 内容与体验：https://support.google.com/adsense/answer/7299563
- Google AdSense 申请未获批：https://support.google.com/adsense/answer/81904
- Google 2026 AI 搜索优化：https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- 公众号内容与 AI 搜索（腾讯云社区转载/原创）：https://cloud.tencent.cn/developer/article/2703505

发布纪律：先合并并测试 dev，检查全量 CI 与站点健康后再允许进入 main。非账号所有人无法根据网站源码直接修改 AdSense 审核状态。
