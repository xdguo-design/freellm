# Skills 页面原型复刻实施计划

> **给代理执行者：** 在本会话按勾选逐步执行；每批完成后复核变更范围。任务使用 `- [x]` 勾选跟踪。

**目标：** 将 FreeLLM Skills 页面在 1448 CSS px 桌面宽度下复刻到用户提供的原型，同时保留真实内容和交互。

**架构要点：** `scripts/build_seo_pages.py` 是静态页面生成源，`skills/index.html` 是生成页面；`css/aurora-skills.css` 承载 Skills 作用域视觉样式。生成页面改动需与模板同步，视觉覆写限定在 Skills 页面作用域。

**技术栈：** 静态 HTML/CSS/JavaScript，Python 构建脚本；本次不增加依赖或自动化测试。视觉检查使用本地 HTTP 预览并在 1448px 宽度浏览器中查看完整页面。

**关联设计文档：** `docs/specs/2026-09-30-skills-page-prototype-replica-design.md`

---

## 文件与职责

- 修改 `css/aurora-skills.css`：校准导航、顶部栏、Hero、统计、合集、技能目录/详情栏及页面下半部的几何尺寸和视觉样式；保留 Skills 页面选择器作用域。
- 修改 `scripts/build_seo_pages.py`：将已核验的 Skill 工作流配方与 GitHub 社区热度数据传入 Skills 页生成模板，补上原型中的工具组合、社区精选、教程引导和页脚结构；保留技能数据与现有交互入口。
- 修改 `skills/index.html`：通过现有构建流程与生成模板保持一致，产出部署页面。
- 读取 `assets/reference/skills-prototype-screen.png` 和用户原型：用于裁切/定位现有素材及尺寸对照，不整页铺截图。

当前分支为 `dev`。工作区已有跨页面未提交修改；编辑前检查目标文件差异，避免重置、覆盖或提交其他改动。

## 任务 1：校准页面整体布局与主要区域

**涉及文件：**
- 修改：`css/aurora-skills.css`

- [x] 阅读 Skills 页面相关完整选择器及样式导入顺序，记录会覆盖 Skills 作用域的级联规则。
- [x] 按设计文档的 1448px 桌面基准校准侧栏、顶部栏、Hero、主栏/详情侧栏的宽度与区域间距；使尺寸和视觉属性集中在带 `data-fl-section="skills"` 的规则中。
- [x] 校准统计行、精选合集、全部技能工具栏与卡片网格的行列、卡片尺寸、圆角、边框、阴影、颜色、字号和纵向留白。
- [x] 校准详情面板、热门工具组合、社区精选、教程横幅及页脚的对齐与纵向节奏；保留窄屏既有布局能力。

## 任务 2：确认生成结构与视觉样式匹配

**涉及文件：**
- 读取/按需修改：`scripts/build_seo_pages.py`
- 生成：`skills/index.html`

- [x] 将 `render_skills_page` 扩展为接收现有 `skill-recipes.json` 配方，并在 `_expected_files` 中传入 `recipes`。
- [x] 在模板中补齐热门工具组合、社区精选、教程横幅和品牌页脚；组合从已有配方及 Skill ID 生成，社区卡片用当前 Skill 名称、描述和真实 GitHub star 数据。
- [x] 使用项目生成命令 `python scripts/build_seo_pages.py` 更新静态 Skills 页面，并确认生成结果包含新增分区、Skills 样式及当前数据/交互节点。
- [x] 若构建流程改动覆盖了并行存在的用户修改，停止并恢复仅由本轮生成导致的差异，再用最小局部方式保持模板/产物一致。

- [x] 调整 `css/aurora-skills.css` 为新增分区建立 Skills 作用域样式，匹配原型卡片布局、插画、标签、按钮、间距与页脚底图。

## 任务 3：本地预览与范围复核

**涉及文件：**
- 检查：`css/aurora-skills.css`
- 检查：`scripts/build_seo_pages.py`
- 检查：`skills/index.html`

- [x] 启动本地静态服务器：`python -m http.server 8000`。
- [x] 打开 `http://localhost:8000/skills/`，在 1448 CSS px 宽度下检查整页；按原型比对侧栏、首屏、目录和详情栏、下半部内容及页脚，发现偏差则回到任务 1 局部调整。
- [x] 检查页面搜索、分类、排序、视图切换、详情选择和收藏控件仍在 DOM 中，确保背景/装饰层未覆盖可交互内容。
- [x] 检查 `git diff --` 仅包含本任务必要改动以及本计划/设计文档；确认先前工作区未提交改动仍保留。

## 完成交付

- [x] 汇报修改文件、页面视觉校准范围、本地预览检查结果及未实证项。
- [x] 不创建提交；由用户后续决定是否提交。



