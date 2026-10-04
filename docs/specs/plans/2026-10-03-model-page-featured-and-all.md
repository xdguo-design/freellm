# 模型页精选与全量区分实施计划

> **给代理执行者：** 在本会话中按勾选逐步执行，并在每个测试切片完成后核对输出。任务使用 `- [ ]` 勾选跟踪。

**目标：** 把 `/models/` 改为展示人工精选的加精模型，并为当前完整模型目录提供明确入口。

**架构要点：** 静态页面继续由 `scripts/build_seo_pages.py` 生成；精选数据来自 `data/models-curated.json`，全量目录继续来自 `data/models.json`。旧 `/models/center/` 路径保留为跳转别名，避免旧链接失效。

**技术栈：** Python 静态站点生成器；回归验证使用 `pytest tests/test_model_pages.py`。

**关联设计文档：** `docs/specs/2026-10-03-model-page-featured-and-all-design.md`

---

## 文件职责

- 修改 `scripts/build_seo_pages.py`：加载 curated 模型数据、生成模型精选卡片和全量入口、使旧模型中心路径跳转，并更新模型页导航口径。
- 修改 `tests/test_model_pages.py`：验证精选集合来自模型清单、卡片加精标识、全量入口保持完整以及旧路径跳转。
- 生成 `models/index.html` 与 `models/center/index.html`：发布对应静态页；构建验证期间从临时目录取出这两个目标文件，避免重写无关生成页。

### 任务 1：锁定模型页行为

**涉及文件：**
- 修改：`tests/test_model_pages.py`

- [ ] 编写回归断言：`/models/` 展示「精选模型」、加精模型卡片及带当前总数的 `/models/all/` 入口；不再展示 Offer 资源卡片。
- [ ] 为 `/models/center/` 增加跳转目标断言，并保留全量模型分页与筛选的既有断言。
- [ ] 运行 `pytest tests/test_model_pages.py -q`，确认新断言因当前页面仍是统计/Offer 入口而失败。

### 任务 2：生成精选模型入口

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`

- [ ] 从 `data/models-curated.json` 读取精选模型；页面卡片只用该集合并显示「◆ 加精」。
- [ ] 为 `/models/` 生成模型卡片首屏和跳到 `/models/all/` 的全量入口，数量取自当前模型目录。
- [ ] 保留厂家、Provider ID、免费资源的分立说明，不把 Offer 当模型。
- [ ] 将 `/models/center/` 生成为指向 `/models/` 的静态跳转页，并从索引页列表移除旧别名。
- [ ] 更新模型页导航标签：`/models/` 显示「精选模型」，`/models/all/` 显示「全部模型」。

### 任务 3：回归验证并更新目标页面

**涉及文件：**
- 修改：`tests/test_model_pages.py`
- 生成：`models/index.html`、`models/center/index.html`

- [ ] 运行 `pytest tests/test_model_pages.py -q`，预期全部通过。
- [ ] 在临时输出目录构建静态站点，核对精选模型数量、首个 curated 模型、加精标签、全量目录链接和旧路径跳转。
- [ ] 只更新仓库中的 `models/index.html`、`models/center/index.html`，确认其他预先存在的工作区改动未被重写。
