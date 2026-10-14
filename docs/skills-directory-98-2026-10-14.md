# FreeLLM Skills 完整中文目录（2026-10-14）

> 数据源：`skills/index.html` 内嵌 Skill 列表及中文说明；与 `data/skills.json` 对应。共 **98 个 Skill**，**12 类**。本文件只表示目录收录，不能把来源核验等同于功能验证。

> 对应页面：[`/skills/catalog/` 分类卡片总目录](https://github.com/xdguo-design/freellm/blob/dev/skills/catalog/index.html)；每条记录有独立 `/skills/<id>/` 详细页。**dev 修改未必已发布到生产站点。**

## 分类统计

| 分类 | 数量 |
| --- | ---: |
| 编程开发与代码质量 | 22 |
| SEO 与内容增长 | 16 |
| 任务规划与工程协作 | 15 |
| 产品视觉与图形设计 | 10 |
| 写作与文字表达 | 9 |
| PPT 与演示 | 8 |
| Word、PDF 与正式文档 | 7 |
| Excel 与数据看板 | 3 |
| 简历与求职材料 | 3 |
| 文件与票据管理 | 2 |
| 商业研究与客户增长 | 2 |
| 团队沟通与内部消息 | 1 |

## 编程开发与代码质量（22）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `mcp-builder` | 用于设计和构建高质量 MCP 服务，把外部服务接入 Agent；覆盖 Python FastMCP 与 TypeScript MCP SDK。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-mcp-builder/index.html) |
| `skill-creator` | 用于从零创建、修改和优化 Skill，改进触发描述，运行评测并通过基准测试检查效果。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-skill-creator/index.html) |
| `web-artifacts-builder` | 用于构建复杂的多组件 HTML 交互作品，适合需要状态管理、路由、React、Tailwind 或 shadcn/ui 的 Web Artifact。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-web-artifacts-builder/index.html) |
| `webapp-testing` | 使用 Playwright 交互测试本地 Web 应用，支持验证前端行为、排查问题、捕获截图和查看浏览器日志。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-webapp-testing/index.html) |
| `writing-skills` | 用于创建、编辑和验证 AI Agent Skill，帮助设计清晰的触发条件、工作流、参考资料和质量检查。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-writing-skills/index.html) |
| `vercel-composition-patterns` | 提供可扩展的 React 组件组合模式，帮助建立清晰、可复用且易维护的组件 API。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-composition-patterns/index.html) |
| `vercel-react-best-practices` | 提供 React 和 Next.js 的性能优化与工程实践，覆盖组件、数据获取、渲染、打包和可维护性。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-react-best-practices/index.html) |
| `vercel-react-native-skills` | 提供 React Native 与 Expo 的高性能开发实践，帮助优化移动端组件、导航、数据和渲染体验。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-react-native-skills/index.html) |
| `changelog-generator` | 分析 Git 提交记录，分类变化并生成面向用户的更新日志，把技术提交转换为清晰的发布说明。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-changelog-generator/index.html) |
| `open-code-review` | 用 ocr CLI 审查 Git 改动，输出行级问题并可按要求应用修复；需先安装 CLI 并配置受支持的模型服务。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/alibaba-open-code-review/index.html) |
| `security-audit` | 按范围侦察、漏洞排查、独立验证和报告等阶段审查代码安全；完整审计需要支持多 Agent 的运行环境、Node.js 和系统级沙箱。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/cloudflare-security-audit/index.html) |
| `claude-api` | 用于编写或调试调用 Claude API / Anthropic SDK 的代码：模型 ID、价格、参数、流式输出、工具调用、MCP、提示缓存与模型迁移；要求先查官方资料而不是凭记忆回答。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-claude-api/index.html) |
| `dispatching-parallel-agents` | 当有 2 个以上互不依赖的任务时，把它们拆给并行子 Agent 处理，并规定任务边界、上下文交接与结果汇总方式。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-dispatching-parallel-agents/index.html) |
| `using-git-worktrees` | 开始需要隔离的功能开发或执行实现计划前，先用原生工具或 git worktree 建立独立工作区，避免污染当前分支。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-using-git-worktrees/index.html) |
| `finishing-a-development-branch` | 实现完成且测试通过后，引导选择合并、开 PR 或保留分支等收尾方式，并在清理前再次验证。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-finishing-a-development-branch/index.html) |
| `vercel-react-view-transitions` | 用 React View Transition API（<ViewTransition>、addTransitionType 与 CSS 伪元素）实现页面切换、共享元素、列表重排和前进/后退方向动画，含 Next.js 集成。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-react-view-transitions/index.html) |
| `diagnosing-bugs` | 针对疑难 Bug 和性能回退的诊断流程：先建立可复现的反馈回路，再逐步提出并验证假设，最后修复并防止回归；用户说“诊断/调试”或报告报错、失败、变慢时触发。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/mattpocock-diagnosing-bugs/index.html) |
| `implement-spec` | 在 /to-spec 与 /to-tickets 产出规格和工单后，把工单当作任务图一次性实现整个 spec；需用户手动调用。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/mattpocock-implement-spec/index.html) |
| `code-review-and-quality` | 多维度代码评审：合并任何改动前使用，适用于评审自己、其他 Agent 或他人写的代码；从正确性、可读性、架构、安全与性能五个维度把关，也可直接评审粘贴的 diff 或 PR。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/addyosmani-code-review-and-quality/index.html) |
| `ponytail` | 马尾辫极简编码：先查现有代码、标准库和原生能力，再做最小完整改动；省 Token 效果因任务而异。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/dietrichgebert-ponytail/index.html) |
| `find-skills` | 按自然语言场景检索可安装 Agent Skills，并提供安装线索；发现结果必须再检查上游源码、许可与依赖，不代表自动通过审核。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-find-skills/index.html) |
| `agent-browser` | 通过 agent-browser CLI 控制浏览器，实现页面操作、表单填写、截图、网页检查及前端自动化测试；需要安装 CLI 和浏览器运行时。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-agent-browser/index.html) |

## SEO 与内容增长（16）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `baoyu-post-to-wechat` | 通过 API 或 Chrome CDP 发布微信公众号文章和图文消息，支持 HTML、Markdown、纯文本及多图内容。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-post-to-wechat/index.html) |
| `baoyu-post-to-x` | 发布 X/Twitter 帖子和长文，支持文章、图片与视频，并遵循 Codex Chrome 插件或计算机使用流程。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-post-to-x/index.html) |
| `baoyu-xhs-images` | 把主题拆成适合社交媒体传播的 1—10 张图文卡片，支持多种插画风格、布局和配色。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-xhs-images/index.html) |
| `baoyu-cover-image` | 为文章生成封面图，结合类型、色板、渲染、文字和情绪设计，支持横幅、宽屏和方形比例。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-cover-image/index.html) |
| `twitter-algorithm-optimizer` | 参考 Twitter 开源推荐算法分析和优化推文，改写内容以提升触达、互动和可见度。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-twitter-algorithm-optimizer/index.html) |
| `article-extractor` | 从网页 URL 提取干净的文章正文并保存为可读文本，去除广告、导航和页面杂乱内容。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/michalparkola-article-extractor/index.html) |
| `youtube-transcript` | 根据 YouTube URL 下载视频文字稿、字幕或转录内容。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/michalparkola-youtube-transcript/index.html) |
| `wewrite` | 公众号内容创作工作流：热点、来源核验、写作与审稿；配图、排版及推送草稿箱按需执行。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/imraywang-wewrite/index.html) |
| `aws-wechat-article-main` | 微信公众号一条龙 Skill 总控：选题、写稿、审稿、HTML 排版、配图和发布；配置模型和授权后才可运行全流程。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/aiworkskills-wechat-article-main/index.html) |
| `summarize` | 统一摘要网页、文档、YouTube 与音视频内容，支持 CLI 和结构化输出；模型能力依赖已配置的提供商或可用 CLI。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/steipete-summarize/index.html) |
| `seo-audit` | 技术 SEO 与站内 SEO 诊断：按证据核对抓取、索引、canonical、hreflang、性能和页面内容，输出按优先级排序的整改清单；不把推断当成搜索引擎实测。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-seo-audit/index.html) |
| `ai-seo` | AI 搜索可见性（GEO/AEO）：检查模型抓取与引用条件、可提取内容、品牌实体及答案结构；不能保证 ChatGPT、Google AI 或其他模型实际推荐。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-ai-seo/index.html) |
| `programmatic-seo` | 程序化 SEO 页面规划：用真实数据和模板批量组织目录/对比页面，核对每页独特价值、内链、canonical、索引和内容质量，避免薄内容批量铺页。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-programmatic-seo/index.html) |
| `site-architecture` | 站点信息架构与导航规划：设计 URL 层级、分类、面包屑和内部链接，可输出 Mermaid 站点关系图；适合梳理模型、服务商与 Skill 目录。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-site-architecture/index.html) |
| `competitors` | 竞品对比与替代页：生成来源可核对的 VS/Alternatives 页面框架，标注功能、价格和限制的证据与更新时间，禁止杜撰竞品优缺点。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-competitors/index.html) |
| `schema` | Schema.org / JSON-LD 结构化数据：根据可见页面事实生成并核查组织、网站、面包屑或列表等数据；须验证 Google 当前支持的富结果类型。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-schema/index.html) |

## 任务规划与工程协作（15）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `brainstorming` | 在创建功能、组件或修改行为前，先澄清目标、约束和验收标准，探索方案并获得用户确认。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-brainstorming/index.html) |
| `writing-plans` | 把已确认的规格或需求拆成可执行的多步实施计划，写清文件、命令、测试和预期结果。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-writing-plans/index.html) |
| `executing-plans` | 在独立会话中执行已有实施计划，按任务推进并在关键节点进行规格符合性和代码质量审查。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-executing-plans/index.html) |
| `systematic-debugging` | 遇到错误、测试失败或异常行为时，按复现、定位、验证和回归的系统流程寻找根因并修复。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-systematic-debugging/index.html) |
| `test-driven-development` | 用测试驱动开发功能或修复问题，遵循 RED—GREEN—REFACTOR 节奏，先用失败测试锁定行为。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-test-driven-development/index.html) |
| `requesting-code-review` | 在完成重要实现、合并或发布前请求代码审查，检查需求符合性、潜在缺陷和质量风险。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-requesting-code-review/index.html) |
| `receiving-code-review` | 接收代码审查意见后，逐条核对技术依据和实际影响，再决定如何修改，而不是机械接受或拒绝。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-receiving-code-review/index.html) |
| `verification-before-completion` | 在声称完成、修复或测试通过前运行必要的验证命令，以实际证据确认结果。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-verification-before-completion/index.html) |
| `subagent-driven-development` | 把已有实施计划拆分给独立子代理执行，并在任务之间进行规格审查、质量审查和结果汇总。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/obra-subagent-driven-development/index.html) |
| `meeting-insights-analyzer` | 分析会议文字稿和录音，发现沟通模式、行为问题和可执行建议，帮助提升沟通与领导力。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-meeting-insights-analyzer/index.html) |
| `learn-this` | 统一提取内容并制定行动计划，可自动识别 YouTube、文章和 PDF，再把信息整理成可执行方案。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/michalparkola-learn-this/index.html) |
| `ship-learn-next` | 用 Ship-Learn-Next 方法把视频、文章和教程中的知识转成实施计划、练习任务和学习挑战。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/michalparkola-ship-learn-next/index.html) |
| `unblock-action` | 帮助澄清模糊或卡住的行动事项，把目标收敛到今天，并确定下一步具体动作。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/michalparkola-unblock-action/index.html) |
| `scrum-sage` | AI Scrum Master 与企业敏捷教练，支持 Scrum、迭代分析、待办细化、障碍移除、团队协作和流程优化。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/michalparkola-scrum-sage/index.html) |
| `product-marketing` | 增长技能共享产品背景：生成和维护 .agents/product-marketing.md，集中记录受众、定位、价值主张与事实/未确认事项，供 SEO 和营销技能复用。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/coreyhaines31-product-marketing/index.html) |

## 产品视觉与图形设计（10）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `frontend-design` | 用于设计或重塑前端界面，提供有辨识度的视觉方向、字体、布局和组件建议，避免千篇一律的模板感。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-frontend-design/index.html) |
| `canvas-design` | 用于制作海报、静态艺术作品、设计图和 PDF/PNG 画布作品，强调原创视觉构图与可交付的成品质量。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-canvas-design/index.html) |
| `brand-guidelines` | 当设计需要遵循 Anthropic 的品牌色、字体或视觉规范时使用，帮助保持品牌一致性。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-brand-guidelines/index.html) |
| `theme-factory` | 为幻灯片、文档、报告和 HTML 页面应用统一主题，提供预设配色、字体和视觉风格，也支持按需定制。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-theme-factory/index.html) |
| `algorithmic-art` | 使用 p5.js 和可复现随机种子创作算法艺术、流场、粒子和生成式视觉效果。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-algorithmic-art/index.html) |
| `web-design-guidelines` | 根据 Web Interface Guidelines 审查界面，关注可访问性、交互、响应式布局、视觉一致性和用户体验。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/vercel-labs-web-design-guidelines/index.html) |
| `design-taste-frontend` | 面向落地页、作品集和界面重设计，帮助 Agent 选择视觉方向、布局、字体、留白与动效；仓库默认 v2 仍标为 experimental。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/leonxlnx-design-taste-frontend/index.html) |
| `impeccable` | 前端 UI 设计与审查 Skill：涵盖视觉层级、响应式、可访问性与 AI 模板化界面问题。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/pbakaus-impeccable/index.html) |
| `archify` | 架构图与流程可视化 Skill：将代码结构和业务关系转为可交互图示及独立 HTML。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/tt-a1i-archify/index.html) |
| `cad` | 参数化 CAD 建模 Skill：文字驱动生成与检查 STEP、STL、3MF、GLB 文件，依赖本地建模工具链。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/earthtojake-cad/index.html) |

## 写作与文字表达（9）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `humanizer` | 改写带有明显 AI 痕迹的文字，让表达更像真实作者，同时保持原意并减少套路化、夸张和空泛措辞。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/blader-humanizer/index.html) |
| `baoyu-infographic` | 把内容拆解成信息图，结合多种版式、视觉风格和配色，生成适合发布的专业可视化图稿。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-infographic/index.html) |
| `baoyu-markdown-to-html` | 把 Markdown 转成带主题的 HTML，支持代码高亮、数学公式、Mermaid、PlantUML、脚注和信息图。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-markdown-to-html/index.html) |
| `baoyu-url-to-markdown` | 抓取网页并转换为 Markdown，适用于文章、教程、YouTube、Hacker News 和需要登录等待的页面。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-url-to-markdown/index.html) |
| `baoyu-article-illustrator` | 分析文章结构，找出适合配图的位置，并按类型、风格和色板生成内容插图。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-article-illustrator/index.html) |
| `content-research-writer` | 边研究边写作，帮助补充引用、优化开头、迭代提纲并逐段反馈，把写作变成协作过程。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-content-research-writer/index.html) |
| `i-have-adhd` | 让回答优先给出下一步、将多步任务编号并减少跑题；原仓库通过 /i-have-adhd 显式启用。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/ayghri-i-have-adhd/index.html) |
| `humanizer-zh` | 中文润色 Skill：减少机械套话和重复表达，保留原文事实、限定条件和作者声音；不是 AI 检测器。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/op7418-humanizer-zh/index.html) |
| `humanizer-zh-next` | 10 月更新的中文编辑 Skill：保留原意和作者语气，可按需加载商务、学术及基金写作分支。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/hyacehila-humanizer-zh-next/index.html) |

## PPT 与演示（8）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `pptx` | 用于创建、读取、编辑和整理 PPTX 或模板，包括演示文稿、页面布局、讲稿、评论、模板和导出。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-pptx/index.html) |
| `baoyu-slide-deck` | 根据内容规划并生成专业的演示文稿页面图片，适合制作幻灯片、汇报和课程型 Deck。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jimliu-baoyu-slide-deck/index.html) |
| `morph-ppt` | 制作带 PowerPoint Morph 平滑转场的 PPTX，让形状在跨页之间连续移动、放大、缩小或旋转。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-morph-ppt/index.html) |
| `officecli-pptx` | 专门处理 PPTX 演示文稿，包括创建、解析、编辑、合并拆分、模板、讲稿和页面布局。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-pptx/index.html) |
| `officecli-pitch-deck` | 制作融资和投资人路演 Deck，适用于种子轮、A/B/C 轮、SAFE、战略融资和投资人汇报。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-pitch-deck/index.html) |
| `ppt-master` | 用 AI 生成和重构可编辑 PPTX，支持页面视觉还原、品牌/样式/布局工作区、模板填充、讲解和动画增强。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/hugohe3-ppt-master/index.html) |
| `NanoBanana-PPT-Skills` | 使用 NanoBanana 相关能力自动生成 PPT 图片和视频增强内容，支持从内容到演示页面的创作流程。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/op7418-nanobanana-ppt-skills/index.html) |
| `html-ppt` | 用模板驱动的 HTML PPT Studio 制作专业静态演示文稿，支持多种风格、布局、动画和键盘导航。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/lewislulu-html-ppt-skill/index.html) |

## Word、PDF 与正式文档（7）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `docx` | 用于创建、读取、编辑和整理 Word 文档或模板；支持目录、标题、页码、信头、图片、批注、修订和格式化输出。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-docx/index.html) |
| `pdf` | 用于处理 PDF 文件，包括读取文本和表格、合并拆分、旋转、加水印、填写表单、加密解密、提取图片和扫描件 OCR。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-pdf/index.html) |
| `doc-coauthoring` | 通过结构化流程协作撰写文档、提案、技术规格和决策记录，帮助传递上下文、迭代内容并验证读者体验。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-doc-coauthoring/index.html) |
| `officecli` | 使用 officecli 创建、分析、校对和修改 docx、xlsx、pptx，支持检查格式、查找问题、添加图表和修改文档。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli/index.html) |
| `officecli-docx` | 专门处理 Word 文档，包括报告、信件、备忘录、提案、模板、修订、批注和目录。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-docx/index.html) |
| `officecli-academic-paper` | 制作带正式引用格式的学术类 Word 文档，支持论文、期刊、学位章节、公式编号、交叉引用和参考文献。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-academic-paper/index.html) |
| `officecli-word-form` | 创建可填写的 Word 表单，支持内容控件、旧版复选框、邮件合并字段和文档保护。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-word-form/index.html) |

## Excel 与数据看板（3）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `xlsx` | 当表格是主要输入或输出时使用；支持读写 xlsx、xlsm、csv、tsv，处理数据、公式、图表、格式和清洗任务。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-xlsx/index.html) |
| `officecli-xlsx` | 专门处理 Excel、工作簿、财务模型、追踪表和 CSV/TSV，支持公式、图表、透视表和模板。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-xlsx/index.html) |
| `officecli-data-dashboard` | 从 CSV 或表格数据构建多元素 Excel 仪表盘，包含 KPI 卡片、图表、迷你图和条件格式。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/iofficeai-officecli-data-dashboard/index.html) |

## 简历与求职材料（3）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `tailored-resume-generator` | 分析职位描述并生成针对性简历，突出匹配的经验、技能和成果，提高获得面试的机会。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-tailored-resume-generator/index.html) |
| `rendercv` | 使用 RenderCV 和 Typst 生成专业简历，支持 YAML 内容、主题定制、字体间距控制，并输出 PDF、PNG、HTML 和 Markdown。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/rendercv-rendercv/index.html) |
| `resume-beautifier` | 从结构化内容或现有简历生成精致且保护隐私的 A4 HTML 简历，支持样式选择、PNG/PDF 导出和隐私审计。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/jzcreative-html-resume-beautifier/index.html) |

## 文件与票据管理（2）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `file-organizer` | 理解文件上下文，查找重复内容、建议文件夹结构并自动整理电脑中的文件，减少手动清理成本。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-file-organizer/index.html) |
| `invoice-organizer` | 读取发票和收据，提取关键信息，统一命名并分类归档，帮助准备报税资料。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-invoice-organizer/index.html) |

## 商业研究与客户增长（2）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `competitive-ads-extractor` | 提取并分析 Facebook、LinkedIn 等广告库中的竞品广告，了解有效的文案、痛点和创意方向。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-competitive-ads-extractor/index.html) |
| `lead-research-assistant` | 结合业务目标搜索目标公司并筛选高质量线索，提供可执行的联系策略，适合销售和市场拓展。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/composiohq-lead-research-assistant/index.html) |

## 团队沟通与内部消息（1）

| Skill 名称 | 主要用途 | 独立详情页源码 |
| --- | --- | --- |
| `internal-comms` | 用于撰写内部沟通材料，包括状态报告、领导更新、团队简报、通讯、事件报告和项目进展。 | [打开详情](https://github.com/xdguo-design/freellm/blob/dev/skills/anthropics-internal-comms/index.html) |

## 详情页统一说明字段

每条独立详情页包括：**功能与问题、适用任务与示例、输入准备、标准流程、交付物、注意事项、FreeLLM 实测结论、上游来源与兼容环境**。实测等级分别描述端到端、任务级、产物级、部分验证、环境阻塞和未实测，不以“来源已核验”冒充运行通过。

文档更新和站点发布应通过 `dev` 测试门禁后进行，现阶段不宣称生产站已上线这 98 个页面。
