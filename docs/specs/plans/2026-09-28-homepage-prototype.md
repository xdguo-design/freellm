# FreeLLM 首页原型对照改造实施计划

> **给执行者：** 在当前分支由本会话按清单实施；保持改动聚焦于生产首页。

**目标：** 让 FreeLLM 首页的布局和浅蓝视觉接近用户提供的原型，同时复用真实目录数据和现有交互。

**架构要点：** 在 `js/reference-shell.js` 调整首页区块装配，在 `css/reference-ui.css` 增补只作用于首页的最终样式。`design/free-china-ai-index.html` 原有搜索、筛选、排序和详情 DOM hooks 保持不变。

**技术栈：** 静态 HTML、CSS、原生 JavaScript；通过本地 HTTP 首页和桌面/窄屏浏览器视口检查。

**关联设计文档：** `docs/specs/2026-09-28-homepage-prototype-design.md`

---

### 任务 1：建立原型 Hero 与首页信息顺序

**涉及文件：**
- 修改：`js/reference-shell.js`
- 新增：`design/assets/home-hero-reference.png`
- 修改：`css/reference-ui.css`

- [x] 将用户确认的统计、动态、分类、筛选、资源和学生横幅按原型顺序放置；首页动态使用站内已存在的精选资源文案，不拼造厂商新闻。
- [x] 将原型插画保存为项目资产，并替换现有圆形空白视觉。
- [x] 只为 `data-fl-section="home"` 增补视觉规则，桌面统计/动态最多五列、资源卡三列，窄屏退化为两列和单列。
- [x] 本地打开 `/design/free-china-ai-index.html` 检查桌面布局、插画加载、搜索栏和筛选；确认“免费 IDE”由 49 条筛到 10 条。

### 任务 2：首页文案与非首页隔离

**涉及文件：**
- 修改：`js/reference-shell.js`
- 修改：`css/reference-ui.css`

- [x] 把全量真实资源区标题与原型层级对齐，保留数量、分类、地区与核验信息。
- [x] 将学生横幅放在资源列表后，继续指向现有学生分类筛选。
- [x] 在本地浏览模型库，确认首页样式选择器没有影响其他页面。
