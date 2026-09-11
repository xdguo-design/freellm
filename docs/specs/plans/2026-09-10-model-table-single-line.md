# 模型表格单行显示实施计划

> **给代理执行者：** 当前会话按步骤执行并完成验证。

**目标：** 让厂家页和模型聚合页的长模型名保持单行省略显示。

**架构要点：** 由 `scripts/build_seo_pages.py` 统一生成 HTML；模型名称和 ID 通过专用 class 共用单行 CSS，完整文本放入 `title` 属性。

**技术栈：** Python 静态页面生成器；验证命令为 `pytest -q` 与 `python scripts/build_seo_pages.py --check`。

**关联设计文档：** `docs/specs/2026-09-10-model-table-single-line-design.md`

---

### 任务 1：调整目录表模型单元格

**涉及文件：**
- 修改：`scripts/build_seo_pages.py` 的 `_catalog_record_table`、`render_model_aggregate_page`、`render_provider_page`

- [ ] **步骤 1：修改 HTML 和 CSS**

  为模型名称链接、模型 ID 增加专用 class 和 `title`；在两处目录表样式中加入单行省略规则。

- [ ] **步骤 2：运行定向测试**

  运行：`pytest -q tests/test_model_catalog_sync.py tests/test_model_pages.py tests/test_provider_pages.py`

  预期：全部通过。

- [ ] **步骤 3：运行完整验证**

  运行：`pytest -q` 和 `python scripts/build_seo_pages.py --check`

  预期：测试通过，SEO 页面检查通过。

- [ ] **步骤 4：检查生成结果**

  检查生成的厂家页包含 `.model-name`、`.model-id` 的单行规则及完整 `title` 属性。

- [ ] **步骤 5：提交**

```bash
git add scripts/build_seo_pages.py docs/specs/2026-09-10-model-table-single-line-design.md docs/specs/plans/2026-09-10-model-table-single-line.md
git commit -m "fix: keep catalog model names on one line"
```
