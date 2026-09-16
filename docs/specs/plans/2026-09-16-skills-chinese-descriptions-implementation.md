# Skills 中文展示文案实施计划

> **给代理执行者：** 本计划在当前工作树内执行。任务使用 `- [ ]` 勾选跟踪；不要触碰仓库中现有的未跟踪截图文件。

**目标：** 为 68 个 Skill 增加可校验的中文展示简介，并让 `/skills/` 的中文/英文模式分别显示对应文案。

**架构要点：** 翻译作为独立 JSON overlay 按 Skill ID 关联，不改上游 Skill 原文。静态构建器把中英文简介随页面数据输出，客户端只根据已有 `lang` 属性切换可见内容，并把两种语言都加入搜索索引。

**技术栈：** Python 构建脚本、静态 HTML/JavaScript、JSON 数据、Python unittest。

**关联设计文档：** `docs/specs/2026-09-16-skills-chinese-descriptions-design.md`

---

## 任务 1：翻译数据契约与失败测试

**涉及文件：** `data/skills-i18n.json`、`scripts/build_seo_pages.py`、`tests/test_skills_page.py`。

- [x] 增加测试：翻译映射必须覆盖每个 `skills.json` ID，所有中文简介必须为非空字符串；生成页必须同时包含中文和英文简介；搜索源码必须索引 `description_zh`。
- [x] 运行 `python -m unittest tests.test_skills_page.SkillsDataTests tests.test_skills_page.SkillsBuildTests -v`，预期因翻译文件不存在或构建器未加载中文字段而失败。

## 任务 2：实现数据加载与双语卡片渲染

**涉及文件：** `data/skills-i18n.json`、`scripts/build_seo_pages.py`。

- [x] 写入 68 个 Skill ID 的中文简介，保持 JSON UTF-8 和一一对应关系。
- [x] 新增 `load_skill_translations(data_path, skills)`，校验文件、对象类型、未知 ID、缺失 ID 和空翻译，并在 `_load_skills` 后合并 `description_zh`。
- [x] 更新 `_skill_card` 与 Skills 页面脚本：卡片简介和详情简介输出中英文双语节点；客户端卡片和弹窗按 `document.documentElement.lang` 显示对应描述；过滤器把 `skill.description_zh` 纳入搜索文本。
- [x] 更新 `validate_skills` 的字段契约，使合并后的 Skill 缺少中文简介时在构建阶段失败。

## 任务 3：逐切片 GREEN 与回归

**涉及文件：** `tests/test_skills_page.py`、`skills/index.html`。

- [x] 运行聚焦测试，确认翻译覆盖、页面双语节点、中文搜索断言全部通过。
- [x] 运行 `python scripts/build_seo_pages.py` 重新生成 SEO 页面。
- [x] 运行 `python -m unittest discover -s tests -v`，确认既有视觉预览、原文、评价、Skill Lab 和 SEO 测试通过。
- [x] 运行 `python scripts/build_seo_pages.py --check`、`git diff --check`，确认生成物与源码一致且无空白错误。

## 任务 4：发布验证

- [x] 检查 `git status --short`，确认只保留用户现有截图未跟踪状态。
- [ ] 提交翻译和渲染变更，推送 GitHub `main`。
- [ ] 发布生产站点，使用 `Invoke-WebRequest https://freellm.top/skills/` 验证 HTTP 200、中文简介和双语切换标记存在。
