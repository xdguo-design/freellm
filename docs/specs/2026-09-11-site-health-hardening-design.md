# freellm.top 健康检查与韧性加固设计

日期：2026-09-11

## 背景

本项目是以静态 HTML 为主、由 Python 脚本生成数据页的目录站点。基线检查显示核心路由可用，但部署响应头不完整，模型目录页体积偏大，发布产物缺少可追溯的版本信息，数据新鲜度在未知或失败时没有 fail-safe，同时首页存在若干可收敛的 DOM 写入边界和文档计数漂移。

## 目标

1. 为 Vercel 部署补齐低风险、通用的安全响应头。
2. 让构建与 CI 在数据新鲜度、HTML 体积和发布 SHA 上失败可见、可诊断。
3. 确保目录在数据源缺失、日期未知时展示明确的降级状态，不把未知状态误报为已核验。
4. 收敛前端动态文本写入，保持现有静态预览、HTTP 加载和交互行为。
5. 让 README 的关键计数由当前数据事实支撑，并通过测试防止再次漂移。

## 非目标

- 本轮不引入 CSP；当前页面有内联脚本、内联样式和第三方脚本，贸然加入 CSP 会造成行为回归。
- 本轮不重做目录 UI，不做未经测量的分页或拆页。
- 本轮不改变 offer/model 的业务定义、核验口径或公开数据。
- 不修改用户已有的 `groq-preview*.png` 未跟踪文件。

## 设计

### A. 部署安全头

在 `vercel.json` 增加 `headers` 规则，覆盖所有路径：

- `Strict-Transport-Security: max-age=63072000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `X-Frame-Options: SAMEORIGIN`

不加入 CSP，直到内联与第三方资源边界完成单独迁移和浏览器验证。

### B. 构建质量门禁

新增无副作用的 Python 校验模块，提供：

- 解析 ISO 日期并判断数据集是否在允许窗口内；非法、缺失、未来日期均视为失败。
- 对 offer/model 数据和关键 HTML 计算文件字节数，超过预算失败。
- 生成或读取发布 SHA：优先使用 `GITHUB_SHA`，否则使用本地 Git HEAD；将 SHA 写入构建报告，不改公开业务数据。

质量门禁在本地可直接运行，CI 在单元测试、构建检查后执行。阈值放在脚本参数或常量中并有测试覆盖，避免把一次性当前尺寸硬编码成不可解释的数字。

建议初始预算：单页 HTML 1 MiB，模型中心页 1 MiB，模型全量页 1 MiB；offer/model 数据新鲜度窗口 3 天。若真实数据增长触发预算，优先产出诊断并单独评估分页/拆页。

### C. 数据新鲜度 fail-safe

前端读取 `lastVerifiedAt` / `lastSeenAt` 时，日期缺失、格式非法或超出窗口显示“日期未知/需要重新核验”，并保留可见的更新时间区域；不显示“今日已核验”一类强保证。构建侧对当前数据直接失败，阻止陈旧目录发布。

### D. DOM 安全边界

保留经过 `escapeHtml` 的结构化卡片模板；对纯文本节点、时钟、错误状态和动态计数使用 `textContent`。不在本轮大规模重写含链接/标签的模板，以降低 HTML 结构回归风险。增加静态契约检查，禁止新引入未转义的用户/数据字段。

### E. 文档一致性

README 的 offer/model/provider 数量不再手工维护：新增测试以当前 JSON 事实校验 README 中展示的关键数字；同步当前真实数量和工作流说明。

## 验收标准

- 现有 Python 测试全部通过；Chromium 可用时 E2E 全部通过，不可用时保留清晰 skip。
- `build_static.py --check` 与 `build_seo_pages.py --check` 通过。
- 质量门禁在当前数据上通过，并能对过期/非法日期、超大文件、缺失 SHA 给出失败结果。
- `vercel.json` 的五个安全头有自动化契约测试。
- README 数量与 `data/offers.json`、`data/models.json`、`data/providers.json` 一致。
- 不产生截图文件改动，不改变业务数据内容。

## 风险与回滚

- 安全头可通过回退 `vercel.json` 规则撤销。
- 质量门禁仅增加检查，不自动改写数据；若真实数据超预算，回退工作流步骤即可恢复发布，同时保留诊断。
- DOM 改动限定在动态纯文本写入，发现浏览器回归时可独立回退 HTML 变更。
