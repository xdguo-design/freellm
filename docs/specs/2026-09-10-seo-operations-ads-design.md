# SEO、重点操作文档与广告位改进设计

## 目标

修复本地 SEO 产物落后于生成器的问题，消除模型聚合页的搜索意图冲突；让首页及重点推广 offer 具备可执行、可验证的操作路径；为 AdSense 提供明确且可控的广告单元入口。

## 范围

1. SEO 生成器：为 `/models/` 与 `/models/all/` 使用不同标题和描述；为中英文页面输出明确的语言替代链接；重新生成当前目录下的静态页面和 sitemap。
2. 操作文档：扩展现有 `data/operations/*.json` 结构，覆盖首页重点卡片及前六个推广 offer；每条 API 路径包含前置条件、步骤、可复制命令、验证动作、官方来源和额度/常见问题说明。
3. 广告位：在共享页面模板中提供一个不会注入真实密钥的显式 AdSense slot 配置；没有 slot 配置时不渲染空广告容器。账号审批、Auto Ads 开关和线上部署不在本次代码变更范围内。

## 方案与取舍

- 推荐：在现有 Python 生成器和 JSON 数据契约上增量修改。优点是兼容现有静态部署和校验器，回滚粒度小；代价是需要重新生成大量 HTML。
- 备选：只手工修改当前 HTML。短期快，但下次生成会丢失，且无法保证 sitemap、模板和页面一致，因此不采用。
- 备选：迁移到运行时渲染。可减少静态文件，但会改变部署方式、缓存和 SEO 风险，超出本次范围。

## 可观察行为

- `/models/` 与 `/models/all/` 有唯一且不同的 title、description、canonical、H1。
- 中英文替代链接带有 `hreflang` 和自描述 URL，且不会把查询参数当作唯一语言 SEO 信号。
- 重点 offer 通过现有 operation-guide 渲染器显示完整步骤和验证信息；非法或缺少验证的 API 文档仍被 schema 拒绝。
- 显式广告位只在配置了 `data-ad-slot` 时出现，AdSense client 仍来自现有公开配置。
- 重新生成后的 sitemap 与实际页面集合一致；已退休页面不再进入 sitemap。

## 测试策略

- 先在 `tests/test_seo_pages.py` 增加聚合页标题和 hreflang 的失败测试。
- 在 `tests/test_operation_guides.py` 增加重点 offer 覆盖率、验证字段和额度/常见问题字段测试。
- 在现有页面渲染测试中增加显式广告 slot 的正反例。
- 运行 `python -m unittest discover -s tests -v`、数据 schema 校验和 `python scripts/build_seo_pages.py --check`。

## 非目标

- 不自动登录或修改 AdSense 控制台。
- 不在没有用户另行指示时部署到 Vercel。
- 不把未经官方来源验证的新模型或免费政策写入目录。
