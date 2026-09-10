# 每日新增与下线日志 实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 为 FreeLLM 构建每日新增/下线日志数据管道、详细新增卡片页面和自动发布流程。

**架构要点：** 纯函数比较前后成功快照，日志按北京时间每天落盘；扫描失败只产生来源异常，不产生下线。SEO 生成器负责 `/logs/` 静态页面，新增记录展示完整可用性与证据字段。

**技术栈：** Python 标准库、JSON、静态 HTML、GitHub Actions、pytest/unittest。

**关联设计文档：** `docs/specs/2026-09-10-daily-change-log-design.md`

---

### 任务 1：实现变更事件和每日日志数据

**涉及文件：**
- 新建：`crawler/change_log.py`
- 修改：`crawler/cli.py`
- 测试：`tests/test_change_log.py`

- [x] 编写失败测试：覆盖首次基线不报新增、首次新模型的详细字段、资源新增、下线转换、恢复、来源失败不下线和新接入渠道。
- [x] 运行 `python -m pytest tests/test_change_log.py -q`，确认因模块或接口不存在而失败。
- [x] 实现 `build_daily_log(previous_log, current_models, current_offers, as_of, source_health)` 和 `write_daily_log`，并增加 `crawler.cli log` 子命令。
- [x] 运行同一测试，确认通过；再覆盖重复运行幂等和 JSON 输出。

### 任务 2：生成 `/logs/` 详细页面

**涉及文件：**
- 修改：`scripts/build_seo_pages.py`
- 修改：`tests/test_seo_pages.py`
- 修改：`tests/test_e2e_static.py`

- [x] 先增加页面行为测试，确认 `/logs/` 出现在 sitemap、页面包含新增详细字段、下线字段和双语导航。
- [x] 运行定向测试确认失败。
- [x] 添加日志载入、格式化、详细新增卡片、下线表格、空日期、JSON-LD/canonical/hreflang 和页面入口。
- [x] 运行定向测试确认通过。

### 任务 3：接入每日扫描与发布

**涉及文件：**
- 新建：`.github/workflows/daily-log.yml`
- 新建：`data/daily-log/.gitkeep`
- 修改：`README.md`
- 修改：`tests/test_workflow.py`

- [x] 先增加 workflow 契约测试，确认每日 schedule、北京时间说明、模型扫描、日志命令、静态生成、最小提交范围和失败保护。
- [x] 运行 workflow 测试确认失败。
- [x] 实现 workflow：抓取模型目录到日期快照，读取上一次日志作为基线，生成日志和 SEO 页面；仅有变化时提交，失败不产生离线事件。
- [x] 运行 workflow 测试确认通过。

### 任务 4：验证、审查、提交和发布

- [x] 运行 `python -m pytest -q`、`python -m unittest discover -s tests -v`、`python scripts/build_static.py --check`、`python scripts/build_seo_pages.py --check`、`git diff --check`。
- [x] 检查本次提交文件清单，确保不包含用户已有未提交改动。
- [ ] 提交 `feat: add daily discovery change log`，推送 `origin/dev`。
- [ ] 运行 Vercel production deploy，验证 `/logs/`、`/sitemap.xml`、首页和现有详情页。
