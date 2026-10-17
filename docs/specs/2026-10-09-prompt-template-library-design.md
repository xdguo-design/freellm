# Prompt 模板库设计

## 目标

为 FreeLLM 增加一个公开、免登录的中文 Prompt 模板库。访客可以按用途发现模板、填写变量、在本地预览并复制；页面界面支持简体中文和英文，首批 24 条模板正文使用中文。

## 已确认范围

- 首批包含 24 条经审核的中文模板。
- 页面提供分类浏览、关键词搜索、详情预览、变量填写和复制。
- 页面由现有静态构建流程生成，可被搜索引擎读取，并进入 sitemap 和站点主导航。
- 变量只在浏览器内存中替换；不登录、不保存用户填写内容、不向后端传输，也不调用模型 API。
- 模板正文按纯文本呈现；HTML/脚本样式的输入只作为文字显示，不执行。

## 用户流程

1. 用户从主导航进入 `/prompts/`，看到简介、搜索框、类别筛选和模板卡片。
2. 搜索词与类别筛选即时组合；每张卡片显示标题、用途、类别和简短摘要。
3. 用户打开模板详情，查看完整正文、变量说明、适用场景和来源/归属。
4. 用户填写模板声明的变量；预览区仅在浏览器中即时替换变量值。
5. 用户复制原始模板或填充后的预览。成功时显示短暂确认；剪贴板权限不可用时显示可选择的纯文本预览。

## 分类建议

首批 24 条均归入四类，每类约 6 条：

- 工作与效率
- 写作与表达
- 学习与研究
- 编程与创作

首发不开放用户投稿或评分，避免在缺少审核机制时把未核验内容展示为官方模板。

## 数据结构

数据源：`data/prompt-templates.json`，顶层为模板数组。必须恰好包含 24 条记录，每个固定类别恰好 6 条。每条记录包含：

```json
{
  "id": "meeting-notes",
  "title": "会议纪要整理",
  "titleEn": "Organize meeting notes",
  "category": "work",
  "summary": "从讨论记录整理决策、行动项和待确认事项。",
  "summaryEn": "Extract decisions, action items, and questions to resolve.",
  "prompt": "请将以下会议记录整理为结构化纪要。\n\n会议记录：{{meeting_notes}}",
  "variables": [
    {
      "name": "meeting_notes",
      "label": "会议记录",
      "labelEn": "Meeting notes",
      "placeholder": "粘贴需要整理的会议内容",
      "placeholderEn": "Enter meeting notes"
    }
  ],
  "scenarios": ["会后整理", "行动项追踪"],
  "scenariosEn": ["Meeting notes", "Action tracking"],
  "source": {
    "type": "original",
    "url": "",
    "note": "FreeLLM 原创模板",
    "noteEn": "Original FreeLLM template"
  },
  "updatedAt": "2026-10-09"
}
```

允许的 `category` 固定为 `work`、`writing`、`learning`、`coding`。校验器要求每类恰有 6 条、`id` 唯一且符合小写 kebab-case；`title` / `titleEn`、`summary` / `summaryEn`、`prompt` 和 `updatedAt` 为非空字符串。`variables`、`scenarios`、`scenariosEn` 为数组，中文和英文场景标签数量相同；`source` 为对象且包含非空 `type`、`note`、`noteEn` 和字符串 `url`。每个变量包含非空字符串 `name`、`label`、`labelEn`、`placeholder`、`placeholderEn`；`name` 匹配 `^[a-z][a-z0-9_]*$` 且不得重复。`updatedAt` 使用真实有效的 `YYYY-MM-DD` 日期。

`source.type` 使用 `original`、`adapted` 或 `external`。`original` 可令 `url` 为空；`adapted` 与 `external` 的 `url` 必须是绝对 HTTPS URL，且不得包含用户名或密码。`prompt` 中使用 `{{name}}` 标记变量，匹配规则为 `\{\{([a-z][a-z0-9_]*)\}\}`；每个标记必须在 `variables[].name` 中定义，每个已定义变量必须在正文中至少出现一次。格式错误、未定义标记、重复 ID、未知分类、非 HTTPS 外部来源、数量不符合 24 条及每类 6 条要求均导致构建失败。

## 页面与构建架构

```text
data/prompt-templates.json
          │
          ▼
scripts/build_seo_pages.py
  ├── 校验 24 条模板数据
  ├── 生成可索引的模板卡片和初始页面文案
  ├── 生成 /prompts/ 页面 metadata 和双语界面文案
  └── 将 /prompts/ 加入 pages sitemap
          │
          ▼
prompts/index.html + js/prompt-library.js + css/prompt-library.css

scripts/build_static.py
  └── 将 /prompts/ 入口同步到首页静态共享导航
```

页面生成沿用 `scripts/build_seo_pages.py` 的现有静态页面机制。模板记录在 HTML 输出前转义；若以 `<script type="application/json">` 承载结构化数据，序列化时须把 `<` 写为 `\u003c`，防止模板正文闭合 script 标签。构建结果提供静态卡片标题、摘要和基本内容，保证禁用 JavaScript 时仍能读取模板列表。`js/prompt-library.js` 只处理即时搜索、类别筛选、详情展开、变量替换和复制交互。

将 `prompts` 加入 `scripts/build_seo_pages.py` 的 `MANAGED_PAGE_ROOTS`、`expected_managed` 与 `managed` 受管目录白名单，确保 `--check` 检查该页且旧输出可清理。`_ensure_static_site_chrome()` 生成的静态共享菜单和 `js/site-navigation.js` 的客户端共享菜单都增加同一个双语主导航入口。`scripts/build_static.py` 也维护首页 HTML 内嵌的静态导航，并更新其导航脚本缓存版本。`_visual_section_for_path()` 识别 `/prompts/`，让未运行 JavaScript 时静态菜单也能标记正确的当前页。客户端路由键和路径列表加入 `prompts` 与末尾斜杠路径 `/prompts/`；页面输出 `data-fl-section="prompts"`，保证异步路由、页面激活态和 `aria-current` 正确。

页面可见文案按现有语言组件提供中英文；URL 共用一份内容，不伪装成独立的中英文 SEO 页面。页面 metadata 使用一个中文 title 和一段简体中文 description，canonical 为 `https://freellm.top/prompts/`，包含 `index,follow` robots 声明，并提供 Open Graph 基础信息。页面加入 `scripts/build_seo_pages.py` 的 `sitemap_section_paths()`，并在生成输出中出现在 `sitemap-pages.xml`。

## 安全、隐私与错误处理

- 模板标题、摘要、提示词和变量值一律用 `textContent` 或 DOM 文本节点显示，不使用未转义值写入 `innerHTML`。模板来源 URL 通过 schema 的 HTTPS 校验；运行时链接使用 `rel="noopener noreferrer"`。
- 变量替换采用逐项文本替换，只替换声明的变量名；未识别占位符保留为普通文本，并在开发内容校验中拒绝发布。
- 用户输入的变量值只保存在当前页面 JavaScript 内存中；关闭或离开页面后不保留。搜索词和变量内容不进入 URL、fetch/XHR 请求、自定义 analytics 事件或日志。
- 现有站点分析脚本不绑定模板搜索框、变量表单或预览内容；页面初始化及交互埋点不得读取这些输入值。
- `navigator.clipboard.writeText()` 不可用或被拒绝时，聚焦并选择纯文本预览，提示用户手动复制。
- 空数据或筛选无结果时显示双语解释和清除筛选按钮；模板数据不合法时构建失败，不生成部分页面。

## 验收标准

1. 24 条模板均通过数据校验，每类恰好 6 条，必填字段、变量标记、来源/归属信息满足本设计的数据约束。
2. 构建后存在 `/prompts/` 页面，中文 metadata、双语可见文案、canonical、静态和客户端主导航、页面路由、受管页面 manifest 及 sitemap URL 正确。
3. 搜索和分类筛选可以组合使用；无结果状态支持清空筛选。
4. 变量表单只显示该模板声明的变量；输入可即时预览，可分别复制原文和填充结果。
5. 用户输入 `<script>`、HTML 标签、引号或模板标记时只显示为文本，不执行、不破坏页面结构；嵌入 HTML 的模板 JSON 不会闭合脚本标签，来源链接只允许 HTTPS。
6. 剪贴板失败时可手动选择预览文本；关闭详情时返回列表状态不丢失筛选条件。
7. 无登录、服务端 API、账户系统、用户投稿、评分、模型调用或持久化用户输入；搜索词和变量值不会被发送到网络请求、URL、analytics 事件或日志。

## 实施边界

实现前先确认首批 24 条模板内容及其 `original` / `adapted` / `external` 来源类型；外部或改编模板需有可核验来源和归属文字。若无法确认来源的模板不进入首发清单。
