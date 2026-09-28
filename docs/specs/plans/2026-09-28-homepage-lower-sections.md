# 首页下半部分原型样式实施计划

> **给执行者：** 在 `feat/model-library-reference-v2` 分支按步骤执行并勾选；保留开始前已有的未提交改动，不创建提交。

**目标：** 将首页学生优惠、低价比较、本地下载、说明卡、FAQ 和页脚改为用户截图中的浅蓝分栏卡片样式。

**架构要点：** 复用首页已有 HTML 和真实动态数据；仅在 `data-fl-section="home"` 下增加样式，不改变筛选和链接行为。中小屏逐级收窄布局，比较表可横向滚动。

**技术栈：** HTML、CSS、原生 JavaScript；按仓库要求不新增或运行测试套件。

**关联设计文档：** `docs/specs/2026-09-28-homepage-lower-sections-design.md`

---

### 任务 1：实现桌面端下半页布局

**涉及文件：**
- 修改：`css/reference-ui.css`

- [x] 在首页作用域追加样式规则，把 `.utility-grid` 排成纵向分段；将 `.student-panel`、`.compare-panel`、`.download-panel`、`.catalog-faq` 排成约 300px 标题区与剩余内容区的两栏结构。
- [x] 为学生优惠和低价入口设置白底圆角卡片；低价入口桌面三列，对比表整行展示；本地下载行显示名称、来源和链接；说明区显示四张提示卡、原生 FAQ 折叠条。
- [x] 将来源/核验信息与法律导航排成截图风格的两排页脚。

### 任务 2：适配窄屏布局

**涉及文件：**
- 修改：`css/reference-ui.css`

- [x] 在 `@media (max-width: 1000px)` 下收窄分栏标题区、减少卡片列数；在 `@media (max-width: 700px)` 下切换单列，在 `480px` 以下堆叠卡片，并允许对比表横向滚动。
