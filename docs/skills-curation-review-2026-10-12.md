# FreeLLM Skills 分类精选与差异化分析

- 日期：2026-10-12
- 分支：`dev`
- 范围：已收录 80 个 Skill、12 个有数据的业务类别；每类首屏最多 6 项，宽屏三列两排。
- 目的：为 `/skills/` 的二级分类导航提供有出处的选品与文字说明，保留全量资料库但不堆叠显示。

## 评审方法与口径

1. 优先看用途是否明确、真实场景和交付物，再看本站验证记录；关注功能与类别的差异化、中文用户的适配性。
2. 明确区分原链路 E2E、真实产物、任务级检查、部分验证和环境阻塞。**任务级模型输出通过不等于原 Skill 完整运行成功**。
3. 仓库 Star 是整个来源仓库的数据，不代表单个 Skill 的评分；同仓库多 Skill 不应被重复计算为独立人气。
4. 前三位是人工编辑顺序，不是具有统计显著性的横向基准排名；类别少于三项就少展示，不补凑数。
5. 功能介绍根据 `data/skills.json`、`data/skill-tests.json` 与页面内聚合的验收记录整理；正式使用仍需回到 SKILL.md 和上游项目核实。

## 分类与前三重点分析

### 编程与工程（收录 19 项 · 精选 6 项）

先解决真实的工程质量问题：性能、Skill 构建、根因排查；不是把所有开发提示词都摆出来。

**1. vercel-react-best-practices** — [上游来源](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)  
证据：任务级/指令级检查；本站记录评分 9.1/10。
- 特点：按优先级检查 React/Next.js 的请求瀑布、渲染与打包问题。
- 适合：实际前端性能优化与代码审查。
- 限制：任务级验证，需结合框架版本及真实性能测量。

**2. skill-creator** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/skill-creator)  
证据：任务级/指令级检查；本站记录评分 8.8/10。
- 特点：覆盖 Skill 触发条件、迭代和基准检查。
- 适合：创建可复用 Agent 技能库。
- 限制：完整评测脚本链路在当前沙箱未打通。

**3. diagnosing-bugs** — [上游来源](https://github.com/mattpocock/skills/tree/main/skills/engineering/diagnosing-bugs)  
证据：任务级/指令级检查；本站记录评分 10/10。
- 特点：先建立复现反馈，再逐个验证原因。
- 适合：疑难 Bug 和性能回退。
- 限制：任务级检查通过不等于任何仓库自动修复成功。

**本类其余入选**：open-code-review、mcp-builder、security-audit。

**二级入口**：https://freellm.top/skills/?category=development

### 任务与协作（收录 14 项 · 精选 6 项）

优先选择能让问题复现、验收可追踪的流程，而不只是通用待办清单。

**1. systematic-debugging** — [上游来源](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging)  
证据：原链路端到端验收；本站记录评分 9.3/10。
- 特点：先定位再改动，保留失败到通过的测试证据。
- 适合：有稳定复现的程序错误。
- 限制：需要能运行测试的工程环境。

**2. verification-before-completion** — [上游来源](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion)  
证据：原链路端到端验收；本站记录评分 9.4/10。
- 特点：先跑验证命令，再宣布完成。
- 适合：提交、修复和发布前的验收。
- 限制：只证明被测范围，不保证覆盖所有风险。

**3. test-driven-development** — [上游来源](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)  
证据：原链路端到端验收；本站记录评分 8.8/10。
- 特点：RED—GREEN—REFACTOR 流程已在夹具中执行。
- 适合：需求边界明确的功能与缺陷修复。
- 限制：测试设计错误仍可能带来虚假的安全感。

**本类其余入选**：writing-plans、brainstorming、executing-plans。

**二级入口**：https://freellm.top/skills/?category=planning-office

### 文档处理（收录 7 项 · 精选 6 项）

优先展示真正处理过 PDF 和文档工作流的 Skill；需外部依赖的能力明确标注阻塞。

**1. pdf** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/pdf)  
证据：原链路端到端验收；本站记录评分 8.7/10。
- 特点：真实完成 PDF 生成、拆分、旋转及渲染检查。
- 适合：表单、报告与 PDF 自动化。
- 限制：中文字体和扫描件 OCR 需额外检查。

**2. doc-coauthoring** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring)  
证据：任务级/指令级检查；本站记录评分 8.4/10。
- 特点：通过补上下文、迭代与读者校验协作写规格。
- 适合：长文档、PRD 与技术决策记录。
- 限制：轻量文档使用时流程偏重，非程序 E2E。

**3. docx** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/docx)  
证据：环境或依赖阻塞。
- 特点：覆盖 Word 编辑、批注、修订及排版。
- 适合：正式 Word 文档工作。
- 限制：沙箱依赖安装失败，不能标成端到端通过。

**本类其余入选**：officecli-docx、officecli-academic-paper、officecli-word-form。

**二级入口**：https://freellm.top/skills/?category=documents

### 表格与数据（收录 3 项 · 精选 3 项）

区分能产出工作簿的验证记录，与尚需 Office CLI 的数据仪表盘链路。

**1. xlsx** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/xlsx)  
证据：真实产物验收（非完整 E2E）；本站记录评分 8.2/10。
- 特点：工作簿公式、结构和数据校验有真实产物。
- 适合：Excel 分析、清洗与报表。
- 限制：验证采用替代工具链，不等于原 Skill E2E。

**2. officecli-data-dashboard** — [上游来源](https://github.com/iofficeai/officecli/tree/main/skills/officecli-data-dashboard)  
证据：环境或依赖阻塞。
- 特点：面向 KPI、图表和条件格式的 Excel 仪表盘。
- 适合：需要复用模板的经营看板。
- 限制：officecli 缺失，原链路未执行。

**3. officecli-xlsx** — [上游来源](https://github.com/iofficeai/officecli/tree/main/skills/officecli-xlsx)  
证据：环境或依赖阻塞。
- 特点：强调模板、公式与透视表的办公链路。
- 适合：复杂工作簿操作。
- 限制：依赖 officecli 安装和验证。

**二级入口**：https://freellm.top/skills/?category=data-office

### PPT 与演示（收录 8 项 · 精选 6 项）

能做可编辑文件的优先，图片式演示和高级动画作为有条件的候选。

**1. pptx** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/pptx)  
证据：原链路端到端验收；本站记录评分 8.9/10。
- 特点：PPTX 生成后做了 PDF 转换与逐页渲染检查。
- 适合：可编辑演示与正式汇报。
- 限制：复杂模板和跨版本效果仍需复核。

**2. ppt-master** — [上游来源](https://github.com/hugohe3/ppt-master/tree/main/skills/ppt-master)  
证据：部分验证。
- 特点：聚焦可编辑演示、模板填充和视觉还原。
- 适合：需要强版式控制的 PPT 制作。
- 限制：当前仅部分验证，未完成原脚本全流程。

**3. baoyu-slide-deck** — [上游来源](https://github.com/jimliu/baoyu-skills/tree/main/skills/baoyu-slide-deck)  
证据：环境或依赖阻塞。
- 特点：按内容结构规划幻灯片并生成页面图像。
- 适合：讲解型和视觉型演示。
- 限制：外部生成服务未接通，不能当作已实测通过。

**本类其余入选**：officecli-pptx、officecli-pitch-deck、morph-ppt。

**二级入口**：https://freellm.top/skills/?category=presentations

### 产品与视觉设计（收录 7 项 · 精选 6 项）

分清设计创作、界面审查、静态视觉三类能力，避免只靠漂亮模板。

**1. frontend-design** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/frontend-design)  
证据：真实产物验收（非完整 E2E）；本站记录评分 8.7/10。
- 特点：强调有辨识度的视觉方向和响应式页面。
- 适合：原型设计及已有界面重塑。
- 限制：产物已验证，但浏览器交互 E2E 被环境阻塞。

**2. web-design-guidelines** — [上游来源](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)  
证据：任务级/指令级检查；本站记录评分 8.4/10。
- 特点：从可访问性、布局与交互审查 Web UI。
- 适合：上线前设计 QA。
- 限制：它是审查清单，不能替代真实用户测试。

**3. canvas-design** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/canvas-design)  
证据：真实产物验收（非完整 E2E）；本站记录评分 8.2/10。
- 特点：强调原创静态视觉构图和可交付图稿。
- 适合：海报、封面与单页视觉。
- 限制：不适合代替复杂交互产品设计。

**本类其余入选**：brand-guidelines、theme-factory、algorithmic-art。

**二级入口**：https://freellm.top/skills/?category=product-design

### 内容写作（收录 7 项 · 精选 6 项）

优先解决文字真实感与来源核验；插图生成作为依赖工具的扩展项。

**1. humanizer** — [上游来源](https://github.com/blader/humanizer/tree/main)  
证据：任务级/指令级检查；本站记录评分 8.7/10。
- 特点：减少套路化语句，保留核心事实与原意。
- 适合：已有草稿的语言打磨。
- 限制：不是客观 AI 文本检测器，需人工审稿。

**2. content-research-writer** — [上游来源](https://github.com/composiohq/awesome-claude-skills/tree/master/content-research-writer)  
证据：任务级/指令级检查；本站记录评分 8.1/10。
- 特点：把研究、提纲、引用与逐段写作串联。
- 适合：长文、报告及内容策划。
- 限制：引用和事实可靠性需要单独核验。

**3. baoyu-article-illustrator** — [上游来源](https://github.com/jimliu/baoyu-skills/tree/main/skills/baoyu-article-illustrator)  
证据：环境或依赖阻塞。
- 特点：根据文章逻辑决定插图位置和视觉风格。
- 适合：图文长文与公众号排版。
- 限制：实际生成依赖外部服务，本轮沙箱阻塞。

**本类其余入选**：baoyu-markdown-to-html、baoyu-infographic、baoyu-url-to-markdown。

**二级入口**：https://freellm.top/skills/?category=writing

### 新媒体与内容运营（收录 7 项 · 精选 6 项）

区分公众号发布、小红书图文、封面制作与增长策略，不承诺未经验证的流量收益。

**1. baoyu-post-to-wechat** — [上游来源](https://github.com/jimliu/baoyu-skills/tree/main/skills/baoyu-post-to-wechat)  
证据：环境或依赖阻塞。
- 特点：衔接 HTML/Markdown 文章到公众号发布。
- 适合：公众号内容生产流水线。
- 限制：需要账户授权与真实发布复核，沙箱未验证。

**2. baoyu-xhs-images** — [上游来源](https://github.com/jimliu/baoyu-skills/tree/main/skills/baoyu-xhs-images)  
证据：环境或依赖阻塞。
- 特点：把主题拆分成社媒图文卡片。
- 适合：小红书多图内容制作。
- 限制：外部图像能力未接通，本轮未跑通。

**3. baoyu-cover-image** — [上游来源](https://github.com/jimliu/baoyu-skills/tree/main/skills/baoyu-cover-image)  
证据：环境或依赖阻塞。
- 特点：按版式、配色和传播场景设计封面。
- 适合：文章头图及跨平台适配。
- 限制：实际图像生成链路待验收。

**本类其余入选**：twitter-algorithm-optimizer、baoyu-post-to-x、article-extractor。

**二级入口**：https://freellm.top/skills/?category=seo-content

### 简历与求职（收录 3 项 · 精选 3 项）

从岗位匹配、排版导出、可维护简历三个角度比较，绝不鼓励虚构经历。

**1. tailored-resume-generator** — [上游来源](https://github.com/composiohq/awesome-claude-skills/tree/master/tailored-resume-generator)  
证据：任务级/指令级检查；本站记录评分 8.6/10。
- 特点：把岗位要求与已有经历一一对齐。
- 适合：针对目标岗位改写简历。
- 限制：不能为匹配关键词而杜撰经历。

**2. resume-beautifier** — [上游来源](https://github.com/jzcreative/html-resume-beautifier/tree/main)  
证据：部分验证。
- 特点：用 HTML 模板排版 A4 简历，强调隐私。
- 适合：网页版与 PDF 风格统一。
- 限制：原脚本与隐私审计未完成验证。

**3. rendercv** — [上游来源](https://github.com/rendercv/rendercv-skill/tree/main/skills/rendercv)  
证据：环境或依赖阻塞。
- 特点：YAML 内容与排版分离，便于版本维护。
- 适合：技术岗位简历的持续迭代。
- 限制：RenderCV/Typst 依赖尚未安装验证。

**二级入口**：https://freellm.top/skills/?category=resume

### 文件与归档（收录 2 项 · 精选 2 项）

更看重分类是否准确、移动操作可预览，以及对发票信息的真实抽取。

**1. invoice-organizer** — [上游来源](https://github.com/composiohq/awesome-claude-skills/tree/master/invoice-organizer)  
证据：原链路端到端验收；本站记录评分 8.6/10。
- 特点：从发票抽取日期、金额和主体后归档。
- 适合：费用票据整理。
- 限制：扫描件、多币种和复杂税项需额外规则。

**2. file-organizer** — [上游来源](https://github.com/composiohq/awesome-claude-skills/tree/master/file-organizer)  
证据：原链路端到端验收；本站记录评分 8.1/10。
- 特点：查重、命名和文件夹结构梳理。
- 适合：混乱文件夹的定期整理。
- 限制：任何批量移动都应先预览和备份。

**二级入口**：https://freellm.top/skills/?category=file-office

### 商业与客户研究（收录 2 项 · 精选 2 项）

广告洞察和潜客研究用途不同，均依赖第三方网站与授权环境。

**1. lead-research-assistant** — [上游来源](https://github.com/composiohq/awesome-claude-skills/tree/master/lead-research-assistant)  
证据：环境或依赖阻塞。
- 特点：按目标客户画像寻找潜在线索。
- 适合：销售名单初筛和研究。
- 限制：需要外部数据访问，且须核实信息来源。

**2. competitive-ads-extractor** — [上游来源](https://github.com/composiohq/awesome-claude-skills/tree/master/competitive-ads-extractor)  
证据：环境或依赖阻塞。
- 特点：从公开广告素材归纳竞品表达和创意。
- 适合：市场定位与投放内容研究。
- 限制：广告库可访问性和数据新鲜度未实测。

**二级入口**：https://freellm.top/skills/?category=ecommerce

### 团队沟通（收录 1 项 · 精选 1 项）

适合内部状态同步、管理汇报与团队信息表达；目前仅有一个符合分类的条目，不补凑数。

**1. internal-comms** — [上游来源](https://github.com/anthropics/skills/tree/main/skills/internal-comms)  
证据：任务级/指令级检查；本站记录评分 7.8/10。
- 特点：提供状态报告、组织公告与领导简报结构。
- 适合：团队内部信息同步。
- 限制：与普通写作提示存在重叠，需人工核对事实。

**二级入口**：https://freellm.top/skills/?category=email-office

## 交互与发布验收

- [ ] 12 个二级分类链接可直接访问，使用浏览器前进/后退可恢复分类状态。
- [ ] 宽屏每类最多 6 卡、前三带适用/限制解析，移动端按单列重排。
- [ ] 卡片不再统一使用 default 图标；使用能力象形标识 + 条目缩写区分。
- [ ] 点击具体 Skill 可打开已有的 SKILL.md/评价/测试详情，来源链接与证据级别不丢失。
- [ ] “完整资源库”保留 80 项数据，默认折叠；搜索时允许查看未入选条目。
- [ ] 现有测试、SEO 和构建通过后才考虑合并 main，本次不触 main。
