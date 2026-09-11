# 每日更新仪表盘实施计划

> **给代理执行者：** 本计划基于已确认的设计文档，任务使用勾选跟踪；执行时保留工作区中已有的导航修复，不覆盖无关改动。

**目标：** 将 `logs/index.html` 生成器升级为有统计、快照、健康状态和基线说明的每日更新仪表盘。

**架构要点：** 继续由 `scripts/build_seo_pages.py` 生成静态页面；在渲染层计算展示模型，不改变 `data/daily-log/*.json`。事件卡片复用现有字段，基线日通过 `baseline` 分支展示当前快照。

**技术栈：** Python 3、静态 HTML/CSS、pytest；验证命令为 `python -m pytest tests/test_seo_pages.py tests/test_e2e_static.py -q`、`python scripts/build_seo_pages.py --check`、`git diff --check`。

**关联设计文档：** `docs/specs/2026-09-10-daily-update-dashboard-design.md`

---

## 文件结构

- 修改：`scripts/build_seo_pages.py`，增加日志统计、快照、健康状态、基线状态和历史日期导航的渲染辅助函数，并替换日志页模板样式。
- 修改：`tests/test_seo_pages.py`，覆盖基线快照、来源健康、历史日期和事件详情。
- 修改：`tests/test_e2e_static.py`，覆盖生成后的日志页关键区块、统计数字和中英文壳层。
- 生成：`logs/index.html`，由 SEO 构建脚本生成，不手工编辑。

### 任务 1：先写日志仪表盘失败测试

**涉及文件：** `tests/test_seo_pages.py`

- [ ] 增加基线日志测试：输入 `baseline=true`、297 个模型、25 个 `providerId`、37 个 offer、两个健康 sourceHealth，断言输出包含 `首次基线`、`297`、`25`、`37`、四个统计卡和两个来源健康状态。
- [ ] 增加普通无变化日测试：输入 `baseline=false` 且 `events=[]`，断言输出包含“今日扫描完成，未发现变化”，且不出现“首次建立基线”。
- [ ] 扩展已有新增事件测试，断言事件卡中的官方链接、额度、注册条件和新增原因仍存在。
- [ ] 增加历史日期测试，输入两个日期日志，断言日期导航包含两个日期并标记最新日期。

运行：`python -m pytest tests/test_seo_pages.py -q`  
预期：新增断言失败，提示当前页面缺少仪表盘字段。

### 任务 2：实现数据统计和状态渲染

**涉及文件：** `scripts/build_seo_pages.py`

- [ ] 添加纯渲染辅助函数：统计四类事件、统计 `observed.models`、`observed.offers` 和去重后的 `providerId`，读取 `sourceHealth` 的 status/reason，并生成安全转义后的 HTML。
- [ ] 在 `render_daily_log_page` 中保留按日期倒序逻辑，传入当前日志对象和日期列表，生成 Hero、统计卡、目录快照、健康状态、历史日期导航和变更流。
- [ ] 将 `baseline=true` 与普通 `events=[]` 分成两个明确的空状态，不改动事件列表内容。
- [ ] 让 `observed` 缺失、`providerId` 缺失、空 sourceHealth 和旧格式日志都回退到 0/未知/暂无说明，不抛出异常。

运行：`python -m pytest tests/test_seo_pages.py -q`  
预期：任务 1 的断言全部通过，原有日志详情断言继续通过。

### 任务 3：替换日志页视觉模板

**涉及文件：** `scripts/build_seo_pages.py`

- [ ] 将日志页样式改为浅色仪表盘：页面背景、Hero 卡、统计卡、快照卡、健康状态徽章、事件卡和表格卡统一圆角、边框、间距和蓝色主色。
- [ ] 桌面端使用统计卡网格和快照双列布局；`max-width: 720px` 时改为单列，表格支持横向滚动，长 URL 可换行。
- [ ] 保留静态语言链接、canonical、hreflang、JSON-LD、首页/模型目录入口和 Vercel Analytics。
- [ ] 不修改事件数据结构、扫描逻辑或其他 SEO 页面。

运行：`python scripts/build_seo_pages.py --data data/offers.json --output .`  
预期：重新生成 `logs/index.html`，命令输出 `built SEO output`。

### 任务 4：生成并验证静态产物

**涉及文件：** `logs/index.html`

- [ ] 运行 `python scripts/build_seo_pages.py --check`，确认所有 SEO 输出 current。
- [ ] 运行 `python scripts/build_static.py --check`，确认首页未被日志模板改动破坏。
- [ ] 用 `Select-String` 或测试确认生成页包含当前基线的快照数字、基线说明和四个统计块。

### 任务 5：回归验证

- [ ] 运行 `python -m pytest tests/test_seo_pages.py tests/test_e2e_static.py -q`，预期通过。
- [ ] 运行 `python -m pytest -q`，预期全量通过，允许既有浏览器环境导致的 skip。
- [ ] 运行 `git diff --check`，预期无输出错误。
- [ ] 检查 `git status --short`，确认只包含本次日志页面、测试、生成页及本计划/设计文档的预期改动。
