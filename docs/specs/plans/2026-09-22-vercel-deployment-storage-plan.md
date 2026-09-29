# Vercel Deployment Storage 清理实施计划

> **给代理执行者：** 本计划已获用户批准。按勾选步骤执行，并在云端删除后重新验证生产站点。

**目标：** 缩小后续 Vercel 部署包并清理不再被别名引用的历史部署，解除 Deployment Storage 超额。

**架构要点：** 这是纯静态站点，部署边界由根目录 `.vercelignore` 控制；站点需要的公开 HTML/CSS/JS/数据/图片继续保留。云端清理使用 Vercel CLI 的 `--safe` 模式，跳过仍有活跃别名的部署。

**技术栈：** 静态 HTML/CSS/JavaScript；Vercel CLI 59.25.0；Python `pytest` 静态测试。

**关联设计文档：** `docs/specs/plans/2026-09-22-vercel-deployment-storage-design.md`

---

### 任务 1：收紧 Vercel 部署输入

**涉及文件：**
- 修改：`.vercelignore`

- [ ] **步骤 1：增加忽略规则**

在 `.vercelignore` 的本地验证产物区域增加：`.tmp-*`。不要排除整个 `logs/`，因为 `logs/index.html` 是公开页面；现有的 `logs/*.png` 和 `logs/*.json` 规则继续生效。保留 `design/assets/` 和根目录公开图片，因为页面/测试会引用它们。

- [ ] **步骤 2：验证部署清单**

运行：`npx --yes vercel@latest deploy --dry --json`

预期：命令成功；JSON 中 `files` 不包含 `.tmp-*` 路径，但包含 `logs/index.html`；`totalSize` 小于修改前约 29.73MB。

- [ ] **步骤 3：运行回归测试**

运行：`python -m pytest tests -q`

预期：测试通过；若仓库测试依赖外部网络导致单项失败，保留完整失败输出并单独运行静态站点相关测试确认配置没有破坏公开资源。

### 任务 2：清理历史部署并核验线上状态

**涉及对象：**
- Vercel 项目：`balabala5/freellm`
- 当前生产别名：`freellm.top`、`www.freellm.top`、`freellm-omega.vercel.app`

- [ ] **步骤 1：记录清理前状态**

运行：`npx --yes vercel@latest ls freellm --json --limit 100` 与 `npx --yes vercel@latest alias ls`

预期：保存部署总数、状态分布和活跃别名，作为清理后的对照。

- [ ] **步骤 2：安全删除无活跃别名的旧部署**

运行：`npx --yes vercel@latest remove freellm --safe --yes`

预期：命令完成；仍有活跃别名的部署被跳过，当前生产部署不被删除。

- [ ] **步骤 3：验证部署与生产域名**

运行：`npx --yes vercel@latest ls freellm --json --limit 100`；随后请求 `https://freellm.top/`、`https://www.freellm.top/` 和 `https://freellm-omega.vercel.app/` 的 HTTP 状态。

预期：生产别名仍指向 READY 部署并返回 HTTP 200；部署数量显著下降或只剩有别名/保留项。

- [ ] **步骤 4：检查工作树**

运行：`git diff --check` 与 `git status --short`

预期：没有空白错误；仅包含预期的 `.vercelignore` 变更以及本计划/设计文档。
