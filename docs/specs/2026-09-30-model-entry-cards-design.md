# 模型入口卡片设计

## 目标

让模型页中部卡片展示当前可用的免费模型 API 入口，使图2的 AMD Radeon Cloud 与 Baichuan AI 数据出现在图1对应的模型区域。

## 方案

- 卡片数据从 `data/offers.json` 读取，只展示同时标记 `free` 和 `model_api` 的资源。
- 有 `freeModels` 列表的资源按模型拆卡；没有列表时使用资源的 `model` 字段。
- 厂商、模型名和限制分别取 `provider`、`freeModels[].model` / `model`、`freeModels[].quota`（缺少时回退到资源级 `quota`）；免费资格取 `freeMechanism`、有效期和准入条件取 `validitySummary` / `accessSummary`。
- 每张卡展示厂商、模型名、免费资格类型、接入条件、额度/限制，并链接到 `/offers/<id>/`。
- 首批优先展示 AMD Radeon Cloud 与 Baichuan AI 各自的一个模型入口，保证两条参考数据都进入首屏；其他记录随后按资源顺序展示，每次加载 6 条。
- 保留模型页上方推荐区、侧栏和完整目录入口。百川卡片明确显示需机构申请/审核的定向资格。
- 原型页支持每次加载 6 条；静态生成器的概览页展示首批 6 条并提供全部免费 API / Offer 入口。

## 数据流与失败处理

原型页脚本请求同源 `/data/offers.json`，筛选并构建卡片。请求失败时显示明确的加载失败提示；没有匹配记录时显示空状态。文本通过 DOM `textContent` 写入，详情地址只使用数据中的资源 ID。`build_seo_pages.py` 同样从构建参数中的资源记录生成首批静态卡片，避免定时重建后概览页丢失入口数据。

## 验收标准

- 模型卡片不再展示写死的示例模型，而是由资源数据驱动。
- 首屏可见 AMD DeepSeek-V4-Flash 与 Baichuan-M3 Plus，并链接各自资源详情页。
- Baichuan 显示定向免费标签与准入限制；AMD 卡片显示对应模型和限额。
- 其他免费模型 API 可通过“加载更多模型”逐批显示。
- 加载失败和无匹配记录时均有可读提示。
