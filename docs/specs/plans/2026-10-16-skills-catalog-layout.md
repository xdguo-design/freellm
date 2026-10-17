# Skills 目录页布局实施计划

> **给代理执行者：** 在当前会话按步骤执行并逐项核对。任务使用 `- [ ]` 勾选跟踪。

**目标：** 将 FreeLLM Skills 页面改成参考图中的推荐、SkillHub、套件三视图及紧凑技能卡片。

**架构要点：** 沿用 `scripts/build_seo_pages.py` 生成页面和内嵌交互，沿用 `css/aurora-skills.css` 做页面样式。页面仍使用现有 `data/skills.json`、合集和详情数据；视图切换在当前文档内完成。

**技术栈：** Python 页面生成器、原生 JavaScript、CSS。验证命令：`python scripts/build_seo_pages.py --data data/offers.json --output D:\WorkSpace\freellm-skills-check --site-url https://freellm.top`、`python -m py_compile scripts/build_seo_pages.py`、`git diff --check`。

**关联设计文档：** `docs/specs/2026-10-16-skills-catalog-layout-design.md`

---

## 文件与职责

- 修改 `scripts/build_seo_pages.py`：输出三视图导航、数据配方卡片、精简技能卡片，并更新 Skills CSS 缓存版本。
- 修改 `js/reference-shell.js`：使用真实技能数据渲染卡片，处理视图 hash / 前进后退，不再注入演示统计。
- 修改 `js/site-navigation.js`：页内视图历史不触发全站路由重载。
- 修改 `css/aurora-skills.css`：桌面四列、平板两列、手机单列布局，以及页内导航和紧凑卡片样式。
- 生成 `skills/index.html`：从现有仓库数据刷新发布用页面。
- 保留现有搜索、分类、状态、排序和详情事件处理。

## 任务 1：页面结构和视图切换

**涉及文件：** `scripts/build_seo_pages.py`

- [x] 保留现有技能数据渲染和详情对话框，为「推荐」「SkillHub」「套件」加上有唯一 ID 的内容面板和语义化按钮。
- [x] 推荐面板复用热门推荐区，SkillHub 面板容纳分类筛选、搜索、状态、排序与完整网格，套件面板从 `recipes` 渲染真实配方卡片并链接到 `/workflow/`。
- [x] 在共享 Skills 脚本里以 `history.pushState` 写入视图 hash，处理前进 / 后退恢复；初次加载根据已知 hash 选中视图，未知 hash 回退到推荐。
- [x] 卡片主按钮显示加号并保留 `data-skill-id`，委托至已有详情弹窗；不新增安装或收藏逻辑，移除硬编码演示指标。
- [x] 更新 Skills 样式资源 URL 查询版本，确保浏览器加载新 CSS。

运行：

```powershell
python -m py_compile scripts/build_seo_pages.py
```

预期：命令成功退出且没有语法错误。

## 任务 2：响应式视觉样式

**涉及文件：** `css/aurora-skills.css`

- [x] 为视图导航、活动状态、卡片图标方块和加号按钮添加样式。
- [x] 技能网格在宽屏为四列，中等屏幕为两列，窄屏为一列；覆盖旧规则，保持列表视图可用。
- [x] 收紧卡片内边距和描述行数，在小屏保留可读的文字、状态和详情按钮。

## 任务 3：生成与验收

**涉及文件：** `skills/index.html`

- [x] 用 `python scripts/build_seo_pages.py --data data/offers.json --output D:\WorkSpace\freellm-skills-check --site-url https://freellm.top` 生成页面到独立目录，避免覆盖工作区内其他生成页。
- [x] 从生成目录复制 `skills/index.html` 到仓库，检查输出包含三个视图、资源版本和数据字段。
- [x] 运行 `git diff --check`，再本地查看页面：切换三个视图、使用分类/搜索/状态/排序、打开详情、浏览器前进后退，并检查桌面、平板和手机宽度。
- [x] 确认修改范围仅为 Skills 相关源码、生成页面和这份实施计划后，提交到 `dev`。
