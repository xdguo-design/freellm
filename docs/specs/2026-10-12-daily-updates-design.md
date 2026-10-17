# 每日发现页面与首页摘要规则

## 目标

左侧导航 `/logs/` 叫「每日发现」（英文 Discoveries）。页面首屏让访客一眼看到近 7 天新出现的免费模型、限免活动与开发工具，用编辑写作的中文描述每一条，而不是程序变更日志；恢复、下线、来源状态保留在页面下方，作为次要信息并用平白的话说明。

## 已确认的行为（2026-10-12 用户确认）

- 导航、标题、首页摘要统一用「每日发现 / Discoveries」：`scripts/build_static.py`、`scripts/build_seo_pages.py`、`js/site-navigation.js`、`js/freellm-sync.js`、`js/scan-trust.js`、`design/free-china-ai-index.html`、`design/updates.html`。修改菜单名需同步两份导航脚本，并更新所有页面的缓存版本号（本次为 `20261012-daily-discovery`）。
- 发现的口径（`scripts/daily_discoveries.py`，/logs/、首页摘要、首页「每日发现」表和 `data/scan-summary.json` 共用）：
  - 统计 `events` 与 `curatedEvents` 中的 `new`、`new_route` 事件，同一日志内同一 id 只计一次；
  - 一个 id 只在**第一次**出现的日志日期算作发现，之后扫描器重复识别不再计入；
  - 近 7 天 = 以最新日志日期为终点的 7 个自然日，按天分组、从新到旧，并显示 7 天合计；
  - 没有日志文件的日子显示「当日未扫描」，不补写、不推算内容；有日志但没有新发现的日子如实写明。
- 每条发现由真实字段拼成一句话：标题（编辑标题直接使用；扫描器给出的裸名称前加提供方，如「Ollama 上新模型 mistral-large-4」），若 `validitySummary` / `freeSummary` 写有截止日期则补「，限时免费到 MM-DD」；第二行用 `freeSummary` 或编辑写的原因；再附提供方、类型和核验状态（已核对官方来源 / 官方列表可见，未实测 / 待核验 / 未核实）。
- 页面任何位置都不显示扫描器内部原因（如 "not present in the previous successful snapshot"），统一改写为平白中文；来源状态 `ok` 显示为「正常」。
- 首页摘要显示「每日发现」、最新日志日的首次发现数量和「查看今日发现 →」，链接到 `/logs/#discovery-day-<日期>`；没有有效日志时显示「查看每日发现 →」。
- “今日 AI 热点”已确认的四篇文章与顺序不变。

## 实现边界

首页源文件为 `design/free-china-ai-index.html`，由 `scripts/build_static.py` 注入每日摘要；`/logs/` 由 `scripts/build_seo_pages.py` 从 `data/daily-log/*.json` 生成。每日定时任务新增的日志无需改代码即可渲染；测试读取最新日志，不写死日期。

## 验收标准

1. 近 7 天视图按日期从新到旧列出首次发现，合计数与各天之和一致；没有日志文件的日期显示「当日未扫描」。
2. 同一 id 在多个日期出现时只在第一天出现（例：京东云 JoyCode 首次收录于 2026-10-11，2026-10-12 的重复新增事件已从日志删除）。
3. 页面中不出现 "previous successful snapshot" 等内部原因文字。
4. 全站菜单显示「每日发现 / Discoveries」；首页摘要显示首次发现数量与入口。
5. 390px 宽度下 /logs/ 与首页没有横向溢出。
6. 日志页分类筛选、恢复全部记录和日期排序仍能改变列表或排序状态。
