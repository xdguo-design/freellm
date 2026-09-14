# Skill Lab / Workflow Recipes 设计

## 目标

把 Skill 从“链接清单”升级为 FreeLLM 自己策划的工作流产品：用户先选择要完成的任务，再看到由多个 Skill 组成的可执行配方。

## 产品形态

保留原有 `/skills/` Skill 清单页，新增 `/skills/lab/` 作为 Workflow Recipes 页面。旧页继续展示完整组件目录和原有搜索/筛选能力；新页不替换旧页，110 条 Skill 作为底层组件库，首屏只展示 6 套精选 Workflow Recipe：

1. 从一句想法到可执行 PRD
2. 从会议记录到团队推进
3. 从关键词到 SEO 内容发布
4. 从商品资料到完整上新包
5. 从数据表到经营汇报
6. 从招聘 JD 到面试准备

每套配方展示目标、输入、输出、步骤链、步骤使用的 Skill、FreeLLM 的组合理由和核验提示。页面明确这是工作流建议，不承诺各仓库当前可用。

## 页面结构

- 左侧栏：Skill Lab、工作流配方、组件库、提交 Skill。
- 主区域 Hero：`从任务出发，不从 Skill 名称出发。`，显示 6 套配方、110 个组件、11 个场景。
- Recipe Bento：6 张不同权重的工作流卡片，卡片内用节点和箭头表达步骤链。
- Recipe Detail：点击配方打开详情面板，显示输入/输出、逐步说明、Skill 安装命令和“复制整套命令”。
- Component Library：默认折叠的 110 条 Skill，提供搜索与分类筛选，仅在用户主动展开时呈现。
- 页面底部：候选来源说明、待核验提示和法律链接。

## 数据

- `data/skills.json` 存放 110 条 Skill 组件，首批用户提供条目默认 `needs_review`、`user-submitted`。
- `data/skill-recipes.json` 存放 6 套由 FreeLLM 编排的配方。每套包含 `id`、`title`、`kicker`、`description`、`input`、`output`、`why`、`tags` 和有序 `steps`；每个步骤包含 `skillId`、`label`、`detail`。
- 构建器验证配方引用的 Skill 必须存在，重复 Skill ID、未知分类和缺失步骤信息都阻断构建。

## 视觉方向

复用 `design/verification/desktop-final.png` 的 Swiss index 语言：左侧固定栏、纸张底色、黑色主字、蓝色强调、黄色规则条、绿色状态块、细线网格。工作流节点使用高对比编号与连线；首屏保持留白与层级，不使用均匀的卡片墙。

## 交互与无障碍

- 点击 Recipe 卡片打开原生 `dialog`，Escape 关闭。
- 详情面板支持复制单条命令和全部安装命令；Clipboard API 失败时保留可选择文本。
- 组件库 `<details>` 默认关闭；展开后支持搜索、分类和状态筛选。
- 键盘可访问所有按钮；结果区域使用 `aria-live`；窄屏变单列，左侧栏变为可横向滚动导航。

## 验收标准

- `data/skills.json` 共 110 条，11 个场景各 10 条，无重复 ID。
- `data/skill-recipes.json` 共 6 套配方，所有步骤引用存在的 Skill。
- `/skills/` 保持原有目录页能力；`/skills/lab/` 首屏只渲染 6 套工作流配方，组件库默认折叠。
- 页面提供详情面板、单条复制、整套复制、搜索和分类筛选。
- 页面加入 canonical、hreflang、ItemList/HowTo 结构化数据和 sitemap 路径。
- 相关单元测试、静态契约测试、构建一致性检查全部通过。
