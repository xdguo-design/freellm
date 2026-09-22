# Vercel Deployment Storage 清理设计

## 目标

解决 `freellm` 项目 Vercel Deployment Storage 超过免费额度的问题，并防止本地测试产物继续进入后续部署包。

## 证据与范围

- 当前项目有 91 个部署：66 个 READY、22 个 BLOCKED、3 个 CANCELED。
- 当前工作树的 dry-run 部署包约 29.73MB，其中 `.tmp-*` 临时文件约 1.93MB。
- 当前生产站点仍依赖仓库中的 HTML、CSS、JS、数据和公开图片；不能用宽泛的图片或 `design/` 排除规则。
- 云端清理范围仅限不再被别名引用的旧部署；当前生产别名和活跃预览别名保留。

## 方案

1. 在 `.vercelignore` 增加 `.tmp-*` 临时文件规则；保留站点运行时需要的公开资源，包括 `logs/index.html`。
2. 使用 `vercel deploy --dry --json` 验证部署包不再包含临时产物，并运行静态站点测试。
3. 使用 Vercel CLI 的安全删除模式清理不带活跃别名的旧部署；删除后重新读取部署列表并核验生产域名。

## 验收标准

- dry-run 部署包不包含 `.tmp-*` 临时文件，且公开的 `logs/index.html` 仍在部署清单中。
- 静态站点测试通过，生产域名仍返回成功响应。
- 旧部署清理命令完成且不影响当前生产/活跃预览别名。
- Vercel Deployment Storage 告警不再由历史部署持续推高；若控制台指标有延迟，记录复查结果。
