# 2026-10-12 新一期 Skills 公开来源复核

## 范围和纪律

- 线索：2026 年 10 月中文开源资讯、公开索引的公众号衍生文章和开发者官方仓库；微信 App 内非公开内容未覆盖，不能宣称已搜索全部公众号。
- 80 → 88 项：仅新增可找到官方 SKILL.md 的 8 项。全量资源库保留原条目；分类主屏最多 6 项，前三名做具体分析。
- 本次“已核验”仅证明 GitHub 项目、技能原文及公开文档可核对；**全部新增项的测试状态均为“未实测”**，不将仓库演示或明星数视为本站验收。
- 对外显示 Star 属于仓库，而非 Skill 自身。

## 已纳入的新 Skill

| Skill | 类别 | 官方 SKILL.md |
|---|---|---|
| ponytail | development | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md) |
| impeccable | product-design | [pbakaus/impeccable](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md) |
| archify | product-design | [tt-a1i/archify](https://github.com/tt-a1i/archify/blob/main/archify/SKILL.md) |
| humanizer-zh | writing | [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh/blob/main/SKILL.md) |
| humanizer-zh-next | writing | [Hyacehila/humanizer-zh-next](https://github.com/Hyacehila/humanizer-zh-next/blob/main/SKILL.md) |
| wewrite | seo-content | [imraywang/wewrite](https://github.com/imraywang/wewrite/blob/main/skills/wewrite/SKILL.md) |
| aws-wechat-article-main | seo-content | [aiworkskills/wechat-article-skills](https://github.com/aiworkskills/wechat-article-skills/blob/main/skills/aws-wechat-article-main/SKILL.md) |
| cad | product-design | [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md) |

## 重点风险

- Ponytail：是最小必要代码的开发约束，复杂需求和视觉细节要写进验收标准；省 Token 比例不得写成本站实测。
- Impeccable：主打 UI/UX 方法和设计检查；hooks、CLI 与浏览器执行未实测。
- Archify：输出架构图时应复核原代码/流程；图形可交互不等于关系真实。
- Humanizer-zh 两个实现：改善中文表达，不检测作者身份，也不保证通过 AI 检测器。
- WeWrite / aws-wechat-article-main：公众号创作工作流侧重点不同，涉及发布需账号授权，不自动发送。
- text-to-cad：CAD 技能是本地工具链，模型导出并不等于制造可行性审核合格。
- 本次不混入：REA（侧重 MCP 和逆向分析工具）、OpenMuse（独立 Agent）、Compositor 和 PhotoCraft（图像编辑软件）；应进入对应工具/Agent 目录。

## 后续工作

1. 针对首屏 6 个精选安排可重复的安装和执行用例，把“未实测”逐步替换为真实分级证据。
2. 建立每周仓库活跃度与 SKILL.md 链接审计、每月人工精选复审，信息源先发现、源码再复核。
3. 公众号文章仅用于发现线索，不凭二手营销稿抄写功能和数据。



---

## WorkBuddy 截图二次收录（2026-10-12：88 → 91）

**最终收录门禁**：`data/skills.json` 正式目录从 88 条增至 **91 条**；另外 2 个仓库只在本审计文档列为候选，没有计入正式发布目录。所有新增记录仅完成上游 SKILL.md 来源核验，测试级别均为 `unknown`（**未安装、未实测**），不计入历史免费模型通过率。

### 正式收录（3 项）

| Skill | 分类 | 源文件 | 许可与缓存 | 统计口径 |
|---|---|---|---|---|
| **find-skills** | development | [vercel-labs/skills](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) | MIT；本地原文镜像 | GitHub 33.9k Stars（网页四舍五入快照） |
| **agent-browser** | development | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) | Apache-2.0；本地原文镜像 | GitHub 43.6k Stars（网页四舍五入快照） |
| **summarize** | seo-content | [steipete/summarize](https://github.com/steipete/summarize/blob/main/.agents/skills/summarize/SKILL.md) | MIT；本地原文镜像 | GitHub 6.7k Stars（网页四舍五入快照） |

上述 Star 是来源仓库**整体**的约数，按公开 GitHub 页面显示的近似值记录（例如 33.9k 对应整数 33900）。不是技能评分，也不是精确到个位的 GitHub API 计数；元数据中已附 `starsPrecision`、`starsSource` 与 `capturedAt`。

### 候选清单（暂未进公开目录）

| 条目 | 源文件 | 暂缓原因 |
|---|---|---|
| guizang-ppt-skill | [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill/blob/main/SKILL.md) | 上游 AGPL-3.0；需确定镜像/再发布许可义务并完成 HTML 演示功能对比测试 |
| AIHOT | [infometa/workbuddyskills](https://github.com/infometa/workbuddyskills/blob/main/skills/aihot/SKILL.md) | 市场归档有二次分发版权提醒，尚无明确再分发许可；第三方资讯 API 的使用条件与准确性待核验 |

- 截图中的 **PPT Generator** 与 **PPT 演示文稿** 可能共同指向 [ggq-eng/pptx-generator](https://github.com/ggq-eng/pptx-generator/blob/main/SKILL.md) 的描述名与功能定义。不把一个技能拆成两个，且目前已有多个可编辑 PPTX 生成工具，待同一基准任务对比后择优。
- “热点话题追踪”尚未确认独立 SKILL.md 来源，暂缓；`ponytail` 已在 88 项基线中，未重复添加。

### 一致性与测试状态

- 正式目录 **91** 条：development **22**、presentations **8**、seo-content **10**，来源仓库 **30** 家；中文显示名、来源、测试状态和缓存原文数据均有记录。
- 3 条新增的 `freeLLMTest.testLevel = "unknown"`、`status = "未实测"`、`score = null`、`testedAt = ""`；这是来源审核，**不是性能/安装/端到端通过证明**。
- 数据页曾做 93 条候选静态自检，后根据远端 CI 现有正式目录门禁（每项需缓存原文与来源 Star）纠偏为 91 正式项，2 条保留候选。旧 CI 执行中出现两项失败：缺少未授权候选的缓存原文，以及新来源 Star 字段为空；已按原门禁调整目录，不修改或削弱测试断言。
- `scripts/build_seo_pages.py` 补充技能分类深链参数读取及已核验状态样式，以免静态页面重新生成时丢失修复。静态 JSON/JS 自检通过不能替代完整浏览器测试与远端 CI 成功。
- 起始 `main`、`dev` 已分叉；本次**仅在 `dev` 工作，未更新 `main`**。

### 后续验收计划

1. find-skills：隔离环境下真实执行 `npx skills find`，检查结果、路径、安装提示与失败场景。
2. agent-browser：隔离浏览器中执行 `agent-browser install` 和受控测试页操作，保存截图、页面快照与执行日志，不使用生产登录状态。
3. summarize：先检查 `summarize status`，再用本地文件/已授权测试网址执行摘要，披露模型连接依赖与费用。
4. guizang-ppt-skill：核验 AGPL-3.0 再分发义务及演示输出与现有 PPT 生成 Skill 的差异。
5. AIHOT：核验来源许可、API 服务条款、接口限流及资讯溯源，不直接转发聚合内容作为官方事实。

发布门禁：远端 CI 全绿、Skill 目录浏览器交互检查和 `main` 分叉处理完成后，再决定是否发布。
