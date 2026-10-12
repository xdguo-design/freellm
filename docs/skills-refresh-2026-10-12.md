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

## WorkBuddy 截图二次收录（2026-10-12：88 → 93）

**结论**：新增 5 个已定位源码的 Skill 记录；其中 3 个完成源码路径与许可证核对并缓存原文，2 个仅链接上游。全部 **未进行 CLI 安装或端到端运行测试**；不得在站点声称运行通过。状态 `verified` 仅代表 GitHub 上游源文件核验，`candidate` 代表仍有许可或使用条件待核实。

| 新记录 ID / 名称 | 类别 | 可信状态 | 上游 SKILL.md / 许可证 | 是否镜像原文 |
| --- | --- | --- | --- | --- |
| `vercel-labs-find-skills` / find-skills | development | 来源核验（未实测） | [源码](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) · MIT | 是 |
| `vercel-labs-agent-browser` / agent-browser | development | 来源核验（未实测） | [源码](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) · Apache-2.0 | 是 |
| `op7418-guizang-ppt-skill` / guizang-ppt-skill | presentations | 社区候选（未实测） | [源码](https://github.com/op7418/guizang-ppt-skill/blob/main/SKILL.md) · AGPL-3.0 | 否，链接原文 |
| `steipete-summarize` / summarize | seo-content | 来源核验（未实测） | [源码](https://github.com/steipete/summarize/blob/main/.agents/skills/summarize/SKILL.md) · MIT | 是 |
| `infometa-aihot` / aihot | seo-content | 社区候选（未实测） | [源码](https://github.com/infometa/workbuddyskills/blob/main/skills/aihot/SKILL.md) · LICENSE 未查明 | 否，链接原文 |

### 其余截图项目的处理

- `PPT Generator` 和 `PPT 演示文稿` 均高度吻合 [ggq-eng/pptx-generator](https://github.com/ggq-eng/pptx-generator/blob/main/SKILL.md) 的技术描述和显示名；先按**疑似同一技能/功能重叠**去重，不直接追加两个条目。现有 presentations 分类已覆盖 PPTX 生成，后续统一做质量对比，胜出者再收录。
- `热点话题追踪` 暂未定位到能明确对应截图的独立 SKILL.md；暂缓收录，不凭截图反推源仓库。
- 先前已收录的 `ponytail`（马尾辫）保留原记录，不重复计数。

### 可复核的站点静态检查

本轮对 `dev` 的 `data/skills.json`、`data/skills-i18n.json`、`data/skill-tests.json`、`data/skill-styles.json` 和 `skills/index.html` 做了交叉核查：

- 原始数据、页面内嵌数据、静态卡片、Schema.org 列表均为 **93**；ID 均不重复；旧 88 项的中文描述、评价、统计和既有测试字段已完整保留。
- 二级分类计数：development **22**、presentations **9**、seo-content **11**；总计 **32 个来源仓库**，GitHub Star 未采集者不显示伪数值。
- 5 个新条目的 FreeLLM 测试等级都是 `unknown`；网页显示“未实测”，不计入此前免费模型通过率的分母。
- 检查了 5 段页面内联 JavaScript 的**语法可编译性**、URL 分类过滤初始化、上游原文外链、3 份镜像文档与许可标签。**这不是浏览器运行截图、安装测试或生产 CI 成功证明。**
- `dev` 与 `main` 起始已分叉；为避免覆盖并行变更，**本轮只写 `dev`，不合并 `main`**。

### 后续运行验收任务

1. **find-skills**：真实执行 `npx skills find <关键词>`，比对搜索结果与官方路径；检查无请求真实密钥。
2. **agent-browser**：在隔离浏览器中完成打开测试页、读取页面快照、点击和截图，保存失败/成功证据；禁止用生产 Cookie。
3. **guizang-ppt-skill**：生成单文件 HTML，检查横屏/移动端、演讲者模式与导出条件；确认 AGPL-3.0 下的转载规范。
4. **summarize**：检查 `summarize --version` 和 `summarize status`；用受控网页和本地 PDF 执行摘要，声明模型费用/依赖。
5. **AIHOT**：先查服务条款、公开接口响应和限流，再测试中英文新闻混杂、来源归属和日期；不能把聚合摘要当成第一手事实。

正式发布门禁：CI/脚本复测通过、浏览器关键路径验收、与 `main` 先同步并解决分叉后再发布。
