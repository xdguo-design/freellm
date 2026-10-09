# 首页 SEO 与信任信息补强实施计划

> **给代理执行者：** 按任务顺序在当前 `dev` 工作树实施，并逐项核对规格验收标准。

**目标：** 补足中文首页的静态目录说明，并让中英文首页结构化数据准确表达资源目录。

**架构要点：** 中文首页由 `design/free-china-ai-index.html` 承载，使用现有 build_static 流程更新；Vercel 将 `/` 重写到该静态文件。英文首页 `en/index.html` 是独立静态页面，直接增加 JSON-LD，不改变其现有文案和 hreflang。

**技术栈：** 静态 HTML、JSON-LD、Python 页面生成器；验证命令为 `python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-10-09-homepage-seo-trust-design.md`

---

## 文件职责

- 修改 `design/free-china-ai-index.html`：增加可抓取的目录说明，移除首页错误的 `AboutPage` 主图谱节点，保留现有 `ItemList` 和 `FAQPage`。
- 修改 `en/index.html`：增加英文 `WebSite` 与 `CollectionPage` JSON-LD。
- 生成更新后的 `design/free-china-ai-index.html`：由现有 `scripts/build_static.py` 更新；Vercel 将 `/` 重写到此文件。

## 任务 1：补充中文首页说明并修正主图谱

**涉及文件：**

- 修改：`design/free-china-ai-index.html`
- 生成：`index.html`

- [ ] 在目录首屏后增加一段简洁静态说明，涵盖收录范围、官方来源核验与信息限制，并链接到现有指南、关于/核验、社区反馈和条款页面。
- [ ] 将主 JSON-LD 图谱保留为 `WebSite`、`CollectionPage`，移除首页上的 `AboutPage` 节点；保留动态 `ItemList` 和 `FAQPage` 图谱。
- [ ] 运行 `python scripts/build_static.py`，预期输出 `built: design\free-china-ai-index.html, data\offers.js, and data\offers-ranked.json ...`，只接受预期的首页、数据生成物和资源指纹更新。

## 任务 2：为英文首页补充目录结构化数据

**涉及文件：**

- 修改：`en/index.html`

- [ ] 在 `<head>` 增加 JSON-LD，包含 `WebSite` 和 `CollectionPage`，名称、简介、URL 和 `inLanguage` 与英文首页实际内容一致。
- [ ] 保持 `https://freellm.top/en/` canonical、现有 hreflang、说明文案与站内路由不变。

## 任务 3：核对生成结果与页面契约

**涉及文件：**

- 检查：`index.html`
- 检查：`design/free-china-ai-index.html`
- 检查：`en/index.html`

- [ ] 运行 `python scripts/build_static.py --check`，预期显示 `current: design\free-china-ai-index.html`、`data\offers.js` 与 `data\offers-ranked.json`。
- [ ] 在两份首页 HTML 中核对 JSON-LD、canonical 和 hreflang；确认中文说明与英语结构化数据都位于静态 HTML。
- [ ] 核对新增中文站内链接都指向仓库现有页面，并确认中英文首页仍保留隐私与条款入口。
- [ ] 查看最终 diff，确认没有新增应用功能、路由、模型数据或未经证实的承诺。
