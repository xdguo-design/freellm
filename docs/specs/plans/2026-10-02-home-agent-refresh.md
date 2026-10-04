# 首页 Agent 热门资源与内容层级调整实施计划

> **给代理执行者：** 按任务顺序完成并逐项检查。任务使用 `- [ ]` 跟踪。

**目标：** 更新首页 Agent 精选资源、绝对日期和原创文章层级。

**架构要点：** 页面仍使用静态 HTML 和 `home-prototype-exact.css`。Agent 分类复用首页现有 `data-filter` 机制，并为上方精选卡片加局部筛选；不改动全站资源目录数据。

**技术栈：** HTML、CSS、原生 JavaScript；本任务不新增或运行测试。

**关联设计文档：** `docs/specs/2026-10-02-home-agent-refresh-design.md`

---

## 文件清单

- 修改 `design/free-china-ai-index.html`：替换精选 Agent 卡片与文章主次结构，改用固定日期，连接筛选状态。
- 修改 `css/home-prototype-exact.css`：主推文章卡片、Agent 卡片区、空状态和窄屏布局。
- 修改 `js/homepage.js` 与页面引用副本 `js/homepage.7eeed4fbb5.js`：把 `agent` token 加入实际目录类别计算。

## 任务 1：更新近期 Agent 精选和筛选

**涉及文件：** `design/free-china-ai-index.html`、`js/homepage.js`、`js/homepage.7eeed4fbb5.js`

- [ ] 将入口文本与筛选值改为“AI Agent”/`agent`。
- [ ] 用六张 Agent 卡片替换旧精选资源；加入 Meta Muse、Manus、WorkBuddy、Xiaomi MiMo Desktop、Kimi Work、WPS 灵犀。优先使用本地详情页，外链使用官方产品入口；状态与地区只展示有来源支持的信息。
- [ ] 移除旧卡片中无来源的使用量、评分和速度数字。
- [ ] 在共享分类计算器中，将资源已有的 `agent` 类型 token 加入返回分类；同步页面直接引用的字节相同脚本副本。
- [ ] 让原型精选网格随 `all`/`agent`/其他筛选切换；筛选无匹配时展示提示。

## 任务 2：将热点文章日期改为明确日期

**涉及文件：** `design/free-china-ai-index.html`

- [ ] 将更新表中的四个“今天”替换为“10 月 2 日”，将四个“2 天前”替换为“9 月 30 日”。
- [ ] 将近期文章卡标题改为“近期热点”；已知文章日期显示绝对日期，日期无法核实时不显示相对时间。

## 任务 3：建立编辑精选文章布局

**涉及文件：** `design/free-china-ai-index.html`、`css/home-prototype-exact.css`

- [ ] 将第一篇文章标为主推卡片，并把文章网格改成一张主卡搭配四张副卡。
- [ ] 通过主推卡片的封面尺寸、标题排版和网格跨度建立层级；副卡保持标题、日期、摘要、标签和原文链接。
- [ ] 在窄屏重置网格跨度并采用单列布局，避免横向溢出。
- [ ] 静态检查变更差异，确认仅触及计划中的页面和样式文件；不运行测试。
