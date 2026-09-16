# Skills 目录视觉预览实施计划

> **给代理执行者：** 按任务顺序执行，每完成一个切片运行对应测试；不纳入用户已有截图文件。

**目标：** 压缩 Skills 卡片纵向高度，并在详情弹窗加入基于技能元数据的 CSS 视觉预览。

**架构要点：** `scripts/build_seo_pages.py` 继续作为唯一生成入口，输出静态 HTML、样式和内联脚本；视觉预览只消费已存在的 Skill `format` 与 `styles` 数据，不新增网络请求或外部图片依赖。

**技术栈：** Python 静态生成器、原生 HTML/CSS/JavaScript、Python unittest。

**关联设计文档：** `docs/specs/2026-09-16-skills-directory-visual-preview-design.md`

---

### 任务 1：建立卡片高度与视觉预览契约

**涉及文件：**
- 修改：`tests/test_skills_page.py`

- [ ] **步骤 1：编写失败测试**

为 Skills 页面静态输出增加以下行为断言：生成页面包含 `.skill-preview`、`id="dialog-skill-preview"`、`id="dialog-preview-format"`、`id="dialog-preview-tags"`、`id="dialog-preview-canvas"`；页面样式包含 `align-items:start`、`-webkit-line-clamp:4` 和 `.skill-preview-canvas`。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_skills_page.SkillsBuildTests.test_skills_page_exposes_compact_cards_and_visual_preview -v`

预期：失败，因为生成器尚未输出新的预览节点和卡片紧凑样式。

### 任务 2：实现紧凑卡片与视觉预览

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`

- [ ] **步骤 1：最小实现**

在 Skills 页面 CSS 中让 `.skill-grid` 使用 `align-items:start`，让 `.skill-card` 移除固定最小高度并降低内边距；卡片描述设置 4 行截断。新增 `.skill-preview`、`.skill-preview-canvas`、`.skill-preview-line`、`.skill-preview-swatch` 等 CSS 结构。

在弹窗中新增 `dialog-skill-preview` 区域，并由 `renderPreview(skill)` 写入：输出格式、样式摘要、最多 6 个样式标签，以及代表文档/代码/表格/视觉产物的 CSS 结构示意。

- [ ] **步骤 2：运行契约测试确认通过**

运行：`python -m unittest tests.test_skills_page.SkillsBuildTests.test_skills_page_exposes_compact_cards_and_visual_preview -v`

预期：通过。

### 任务 3：生成页面并做回归验证

**涉及文件：**
- 修改：`skills/index.html`
- 可能修改：`.seo-pages-manifest.json` 不纳入提交（当前由 `.gitignore` 忽略）

- [ ] **步骤 1：重新生成**

运行：`python scripts/build_seo_pages.py`

预期：输出 `built SEO output: 68 skills` 或等价的当前 Skills 数量提示，并更新 `skills/index.html`。

- [ ] **步骤 2：运行完整测试**

运行：`python -m unittest discover -s tests -v`

预期：全部测试通过；若本机没有 Chromium，仅允许已有浏览器测试跳过。

- [ ] **步骤 3：检查内联脚本和差异**

运行：`git diff --check`；并用 Node `vm.Script` 编译 `skills/index.html` 中全部可执行内联脚本。

预期：无空白错误，脚本语法通过。
