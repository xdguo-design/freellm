# 每日更新摘要实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 首页按最新日志日显示去重后的新增数量和清晰入口，“更新”页保留最新实际日志日的完整变更列表。

**架构要点：** `scripts/build_static.py` 从最新 `data/daily-log/*.json` 读取事件并生成首页摘要；首页源模板为 `design/free-china-ai-index.html`。`scripts/build_seo_pages.py` 生成 `/logs/` 历史详情，不改变其事件数据源或过滤规则。

**技术栈：** Python 3 标准库静态站生成；`python -m unittest tests.test_build_static -v`、`python -m unittest tests.test_release_home_20261009 tests.test_ux_20261009_regressions -v`。

**关联设计文档：** `docs/specs/2026-10-12-daily-updates-design.md`

---

## 文件变更清单

- 新建：`docs/specs/2026-10-12-daily-updates-design.md`（确认后的展示规则）。
- 新建：`docs/specs/plans/2026-10-12-today-discovery.md`（本文件，实施步骤）。
- 新建：`memory.md`（记录项目长期有效的导航、日志数据源和首页更新约束）。
- 修改：`scripts/build_static.py`（首页摘要改为新增数量、日志日期和完整列表入口，并去重）。
- 修改：`design/free-china-ai-index.html`（摘要标记使用明确的语义类名和安全占位文案）。
- 修改：`css/primary-menu.css`（桌面和窄屏摘要布局）。
- 修改：`tests/test_build_static.py`（验证去重、零新增和无有效日志的展示行为）。
- 生成：`logs/index.html` 和 `design/free-china-ai-index.html`（运行现有构建器后核对，不接受无关生成差异）。

## 任务列表

### 任务 1：定义首页摘要的可观察行为

**涉及文件：** `tests/test_build_static.py`、`scripts/build_static.py`

- [x] **步骤 1：编写最小失败测试**，用临时目录构造包含两个新增、一条恢复事件和一个重复精选事件的最新日志；断言显示“新增 2 项”、正确日期锚点、完整列表链接，不显示单条资源标题。
- [x] **步骤 2：运行并确认 RED**：`python -m unittest tests.test_build_static.BuildStaticTests.test_home_discovery_shows_unique_new_count_and_all_entries_link -v`。预期：失败在缺少“新增 2 项”断言，而不是测试导入或临时文件错误。
- [x] **步骤 3：实现最小逻辑**：收集 `events` 和 `curatedEvents` 中 `new`、`new_route` 事件；以 `(eventType, id)` 去重，缺少 id 时用 `(eventType, kind, title)`；摘要输出日期锚点、计数和“查看更新详情 →”。
- [x] **步骤 4：运行并确认 GREEN**：重复运行上述单测，预期 `OK`。
- [x] **步骤 5：覆盖空数据**：增加零新增和无可读日志断言，运行 `python -m unittest tests.test_build_static -v`，预期全部通过。

### 任务 2：首页摘要响应式布局和生成结果

**涉及文件：** `design/free-china-ai-index.html`、`css/primary-menu.css`、`scripts/build_static.py`

- [x] **步骤 1：改模板占位**：在 `#home-latest-discovery` 中提供标签、计数和链接三个明确元素；使用已有动态生成入口替换内容。
- [x] **步骤 2：更新样式**：标签与计数不换行；链接可收缩；宽度不足时允许整块换行，禁止绝对定位和竖排字符；统计卡片按内容自然增高。
- [x] **步骤 3：生成首页**：运行 `python scripts/build_static.py --data data/offers.json --html design/free-china-ai-index.html`，预期首页显示最新日志日的去重新增数及日志日期链接。
- [x] **步骤 4：检查生成稳定性**：运行 `python scripts/build_static.py --check`，预期退出码为 0。

### 任务 3：保留并核验完整更新页

**涉及文件：** `scripts/build_seo_pages.py`、`logs/index.html`、`js/site-navigation.js`

- [x] **步骤 1：生成日志页面**：运行 `python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top`。
- [x] **步骤 2：核对页面**：运行 `python -m unittest tests.test_release_home_20261009 tests.test_ux_20261009_regressions -v`；断言最新日志日期下五条新增包含 `京东云 JoyCode`，导航中文为“更新”，不更改热点文章数据。
- [x] **步骤 3：检查全部静态输出**：运行 `python scripts/build_seo_pages.py --check`，预期退出码为 0。

### 任务 4：维护项目记忆并完成回归检查

**涉及文件：** `memory.md` 与以上改动文件。

- [x] **步骤 1：写入长期约束**：记录 `/logs/` 是新增记录完整列表、首页摘要仅计数并链接、热点文章固定顺序，以及生产构建必须从干净主线生成。
- [x] **步骤 2：运行相关验证**：运行 `python -m unittest tests.test_build_static tests.test_release_home_20261009 tests.test_ux_20261009_regressions -v`，预期全部通过。
- [x] **步骤 3：检查差异**：运行 `git status --short` 与 `git diff --check`；旧原型工作树与主工作区文件未改动。

### 任务 5：统一共享导航并核验交互

- [x] 同步更新 `site-navigation.js` 与 `freellm-sync.js` 的中英文菜单名称，防止异步本地化把“更新”覆盖为旧文案。
- [x] 更新全站静态页面的两份导航/本地化脚本缓存版本号，并修复首页统计卡片的日期说明溢出。
- [x] 浏览器实测日志页模型 / Offers 筛选、全部重置和日期排序。
- [x] 全量测试完成后记录结果；`python -m unittest discover -s tests -q`（377 项）和模型专项 pytest（51 项）通过；静态生成器检查通过。发布前核验部署预览。
