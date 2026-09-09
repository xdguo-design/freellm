# Groq 模型逐行展示设计

## 目标

修复 Groq 资源卡片把多个模型挤在同一行的问题。每个模型独立一行，并展示该模型自己的上下文窗口与 Free Plan 限制；“官方来源”改为带明确名称的可点击链接。

## 方案

- 在 `data/offers.json` 的 `groq-free` 中扩展结构化 `freeModels` 列表，保存模型 ID、类别、上下文窗口和免费计划限制。
- 保留 `model` 字符串作为搜索/兼容字段；首页渲染优先使用 `freeModels`，旧资源继续使用原字段。
- Groq 详情页使用已有 `freeModels` 表格扩展“上下文窗口”列，每个模型保持独立行。
- 官方来源使用 `links` 的标签和 URL 渲染为可点击链接，不展示裸 URL 作为唯一识别信息。
- 数据以 Groq 官方模型目录和 Free Plan Limits 页面为核验来源；页面保留核验日期，并提示额度与模型可能变化。

## 验收标准

1. Groq 首页卡片中模型不再以斜杠/中点拼接成一段，而是每个模型一行。
2. Groq 详情页每个模型各占一行，并有独立的上下文窗口字段；音频模型显示不适用而不是错误 token 数。
3. 官方来源区域至少有“Groq Console”“模型目录”“Free Plan Limits”“OpenAI 兼容接口”等可点击链接。
4. 现有非 Groq 资源的渲染和 schema 校验不回归。
5. `pytest tests/test_seo_pages.py tests/test_build_static.py tests/test_schema.py -q` 与静态构建检查通过。
