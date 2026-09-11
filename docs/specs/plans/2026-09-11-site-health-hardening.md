# freellm.top 健康检查与韧性加固实施计划

设计依据：`docs/specs/2026-09-11-site-health-hardening-design.md`

## 执行顺序

### 1. 建立红测与契约

- 在现有 unittest 结构中增加 Vercel 配置测试：五个响应头、全路径匹配、保留根路由 rewrite。
- 增加质量门禁纯函数测试：有效日期、过期/未来/非法日期、字节预算、SHA 解析。
- 增加 README 数据事实测试，先让当前漂移数字失败。

完成标志：新增测试在生产代码尚未修改时按预期 RED，失败原因指向缺失能力或旧文档事实。

### 2. 实现部署头

- 修改 `vercel.json` 增加 headers 规则。
- 运行对应测试和完整 unittest。

完成标志：安全头契约测试 GREEN，rewrite 仍然通过。

### 3. 实现质量门禁与发布追踪

- 新建 `scripts/site_health.py`，只负责读取输入并返回可测试的诊断结果。
- 提供命令行入口，检查当前数据、关键 HTML、数据新鲜度和发布 SHA。
- 将门禁加入 `daily-check.yml`，输出 SHA 与诊断报告为 artifact；不自动提交或推送公共数据。

完成标志：本地命令和 CI 配置测试通过；故意构造的过期/超大/缺 SHA 输入会失败。

### 4. 收敛前端纯文本写入

- 将时钟、错误状态、动态日期与计数等纯文本 `innerHTML` 改为 `textContent`。
- 保留需要标签/链接的结构化模板，并确保数据字段继续经过 `escapeHtml`。
- 更新静态契约测试，覆盖关键边界。

完成标志：本地 HTTP/file 预览交互不回归，页面无新增控制台错误。

### 5. 同步 README 与验证

- 更新 README 中过期的 offer/model/provider 计数和相关命令说明。
- 运行 schema、构建检查、质量门禁、完整 unittest；Chromium 可用则运行 E2E。
- 进行最终 diff、敏感文件和截图变更检查，记录剩余风险。

完成标志：验收标准全部满足，工作区仅包含本轮明确修改和用户已有未跟踪文件。

## 回滚点

每个阶段保持独立提交粒度：`vercel.json`、质量门禁/CI、前端 DOM、README。任何回归可按阶段回退，不触碰数据快照和用户截图。
