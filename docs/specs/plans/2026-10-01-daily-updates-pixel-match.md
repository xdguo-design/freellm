# 每日更新页原型像素复刻实施计划

> **给代理执行者：** 本计划在当前 `dev` 分支同会话逐步执行。保留工作区既有修改；每步用 `- [x]` 跟踪。

**目标：** 让每日更新原型和 `/logs/` 静态页在 898px 桌面宽度下逐区匹配 `docs/png/更新.png`，同时只呈现真实日志数据。

**架构要点：** `scripts/build_seo_pages.py` 从现有每日 JSON 生成真实页面模块，`css/prototype-pages.css` 负责参照图的紧凑布局，`design/updates.html` 继续作为同版式预览。共享导航从静态状态文件读取上海当天是否有目录变化并显示红点；扫描算法、事件分类和日志格式不变。

**技术栈：** Python 3、静态 HTML/CSS/JavaScript。按要求不运行测试套件；验收使用 Chromium 898px 视口整页预览、主要模块 DOM/链接核对。

**关联设计文档：** `docs/specs/2026-10-01-daily-updates-aurora-redesign.md`

---

## 文件结构

- 修改 `scripts/build_seo_pages.py`：新增与原型版位相同的日志模块渲染器，将真实数据接入统计、重点卡、周趋势、历史表、健康状态和日历，并输出导航状态 JSON。
- 修改 `css/prototype-pages.css`：只调整 `data-fl-section="logs"` 下的专属尺寸与视觉细节；复用已有原型卡片类。
- 修改 `design/updates.html`：让静态预览展示与目标截图相同的版式、真实日常语义和 Atom 入口。
- 修改 `js/site-navigation.js`：读取最新日志状态；仅对上海当天真实目录事件在共享导航显示红点。
- 生成 `logs/index.html` 与根目录 `daily-update-status.json`：由 SEO 构建器产出，不手工维护页面事实数据。

## 任务 1：把真实日志转成原型模块

**涉及文件：** `scripts/build_seo_pages.py`

- [x] 拆出纯渲染辅助函数，输出五项指标、筛选 chip、重点更新卡和周趋势条。计数只读取 `latest_groups`、最近 7 日日志、已发布模型/Offer 列表；事件标题、Provider、时间和状态使用 HTML 转义。
- [x] 输出“今日变化”卡、目录快照、变更流摘要、历史事件表、来源健康、月份日期格、更新机制说明和 Atom 订阅入口。来源健康只显示 `sourceHealth.status/reason`，不推导百分比；自测版位展示“此页不提供模型推理端点”，不伪造延迟或测试模型。
- [x] 用原型模块替换当前首屏双面板与大时间线的主布局；逐日可展开的完整事实详情继续作为历史/详情区域保留，且当天无变化或基线时呈现对应空状态。
- [x] 当前发布资源数量不足原型行数时仅渲染实际记录，保留卡片边框和结构，不复制示例数据。

## 任务 2：像素校准桌面版式

**涉及文件：** `css/prototype-pages.css`、`design/updates.html`

- [x] 在 898px 目标宽度下，对齐 120px 侧栏、14px 主内容边距、177px Hero、五卡统计行、筛选行、主/辅双栏、更新表、三卡底栏、说明/订阅行和 205px 页脚。
- [x] 对照 `docs/png/更新.png` 调整关键区块 top/left/width/height、圆角、边框、阴影、蓝色、字号和间距；插画固定使用 `assets/reference/updates-hero-prototype.png`。
- [x] `design/updates.html` 与正式日志页使用相同标题、区块顺序、表格列和卡片网格；内容示例改为真实可理解的空状态，不把示例模型和数字写成项目事实。
- [x] 保留现有已修改的 `--prototype-rail` 变量；不更改 About、Tools、Workflow 作用域。

## 任务 3：生成当天共享导航状态

**涉及文件：** `scripts/build_seo_pages.py`、`js/site-navigation.js`

- [x] SEO 构建器生成 `daily-update-status.json`，仅包含最新日志日期与目录事件布尔值。事件集合为 `new`、`new_route`、`recovered`、`offline`，扫描异常不计入。
- [x] `site-navigation.js` 读取该静态文件，将最新日志日期与 `Asia/Shanghai` 当天日期比较；日期不相等、文件不存在、JSON 无效或当天无目录事件时移除红点。
- [x] 仅在 `[data-site-nav="logs"]` 的标签上添加 `aria-hidden="true"` 的红色装饰点；共用导航初始化后及客户端路由切换后状态不丢失。
- [x] 更新相关静态资源 query 版本，确保本地和部署浏览器加载新 CSS/JS。

## 任务 4：生成产物并浏览器验收

**涉及文件：** `logs/index.html`、`daily-update-status.json`

- [x] 运行 `python scripts/build_seo_pages.py --data data/offers.json --output .`，预期更新 `/logs/` 并创建状态 JSON；检查终端报告构建完成。
- [x] 在 Codex 浏览器将视口宽度设为 898 CSS px，从页面顶端取得正式 `/logs/` 整页截图，与 `docs/png/更新.png` 按区块顺序和边界对照。
- [x] 核对正文中真实事件、官方来源、当日无变化/基线状态、目录数量、语言入口、Atom feed、日期定位和历史详情仍可访问；核对状态 JSON 缺失/过期/无事件时红点隐藏的代码分支。
- [x] 不运行 pytest 或其他测试套件；完成后恢复浏览器默认视口，并检查 `git diff --check` 和 `git status --short`，保留无关工作区改动。
