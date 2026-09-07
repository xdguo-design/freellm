# Free AI Index 首页参考图风格原型实施计划

> **给代理执行者：** 本计划用于当前会话内逐步执行，先完成可视化原型，不同步远端分支。

**目标：** 将 `design/free-china-ai-index.html` 的首页视觉改造成用户提供的 Free AI Index 参考图风格，同时保留现有数据、搜索、筛选、排序和详情抽屉交互。

**架构要点：** 只改 `catalog-app` 的首页结构和样式，继续复用现有静态嵌入数据与 DOM hooks；不修改 legacy 页面和数据 schema。通过 CSS 断点让桌面端呈现信息卡片布局，移动端退化为单列卡片。

**技术栈：** 单文件 HTML/CSS/Vanilla JS；验证命令为 `python -m unittest tests.test_e2e_static` 和可用时的 Playwright E2E。

**关联设计文档：** `docs/specs/2026-09-07-free-method-index-redesign-design.md`

---

### 任务 1：重排首页展示结构

**涉及文件：**
- 修改：`design/free-china-ai-index.html` 的 `catalog-app` 首页 markup

- [ ] 顶部导航补齐“模型库 / 开发工具 / API 服务 / 榜单”、提交资源入口和账户占位。
- [ ] Hero 改为主标题、主搜索、热门搜索、今日 AI 情报卡片。
- [ ] 将分类入口、筛选条、热门资源区和编辑精选区调整为参考图的层级顺序。

### 任务 2：应用参考图视觉系统

**涉及文件：**
- 修改：`design/free-china-ai-index.html` 的 catalog CSS

- [ ] 使用暖白背景、浅蓝光晕、圆角白色卡片、深蓝文字和蓝紫渐变强调。
- [ ] 为 Hero 情报卡、资源卡、筛选器和右侧精选卡添加响应式样式。
- [ ] 保持供应商文字标识，不伪造官方 logo；保留数据证据字段。

### 任务 3：行为与视觉回归验证

**涉及文件：**
- 修改：无，除非测试暴露现有 hook 回归
- 验证：`tests/test_e2e_static.py`

- [ ] 运行静态契约测试，确认现有 DOM hooks 仍存在。
- [ ] 运行浏览器测试，确认 27 条 offer、搜索、筛选和详情抽屉正常。
- [ ] 检查桌面和窄屏不产生页面级横向滚动。
