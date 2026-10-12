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
