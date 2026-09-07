# Free AI Index「免费方式索引」重设计

日期：2026-09-07

## 目标

把首页从“按 API 能力罗列”调整为“按用户获得免费资格的方式组织”，解决当前左侧分类过细、入口维度混乱、卡片高度和信息基线不齐的问题。页面需要继续保持证据优先、可核验、对开发者有用，同时通过一张 Image2 生成的抽象夜间优惠视觉提升识别度。

## 用户可见的信息架构

首页固定展示 6 个主分类：

1. **免费额度**：按日、周、月或持续额度；突出 quota、周期和是否需要绑定付款方式。
2. **积分 / 次数免费**：新人积分、一次性体验次数和 trial credits；与持续免费明确区分。
3. **免费 IDE**：可直接下载或打开的编码工具；突出补全、对话、Agent、模型范围和用量限制。
4. **时段 / 地区 / 限时优惠**：首月、夜间时段、区域价格差和汇率优惠；不把未证实的 GLM / 阿里 / 小米活动标成事实。
5. **网页直接用**：无需 API Key、打开网页即可使用的产品；豆包、通义等入口放在这里。
6. **可下载 / 低成本**：开源权重与低价 pay-as-you-go；同时提醒“权重免费不等于推理基础设施免费”。

现有 Search / Fetch / Extract / Crawl / Map / Browser / Agent 不再作为首页主导航分类，而作为结果行中的能力标签和搜索词保留，避免丢失现有数据价值。

## 页面布局

- 继续使用 Swiss index 的纸张底、黑色边框、蓝色主强调和黄色提醒，但整体切换到明确的 12 列内容网格。
- 左侧导航只放 6 个分类和数量；“验证规则”作为固定说明，不再夹杂能力分类。
- 顶部 Hero 左侧为标题、解释和更新时间，右侧为 Image2 生成的夜间优惠视觉与总数统计。
- Hero 下方放 5 个等宽统计块：免费额度、免费次数、免费 IDE、限时优惠、网页直用；第 6 类在列表入口中出现，避免首屏过拥挤。
- 主列表采用统一卡片行：`产品 / 免费方式 / 额度或价格 / 有效期 / 地区 / 验证状态 / 官方入口`。每个字段固定最小宽度、统一顶部基线和两行截断策略。
- “夜间 / 时段优惠”使用黄色专题条，展示时区转换提示；只有数据中存在 `timeWindow` 的条目才展示具体窗口。
- 保留详情抽屉、搜索、排序、空状态、JSON-LD 和移动端横向滚动能力。

## Image2 素材规范

- 用途：Hero 右侧的抽象 editorial illustration，不承担文字信息。
- 内容：深蓝黑背景、黄色夜间时间窗 / 时钟、规整数据卡片、少量青绿色状态点，表达“夜间优惠 + 可核验数据”。
- 禁止：任何品牌 Logo、真实产品界面、可误认的厂商标识、长文字、水印和人物。
- 输出：横向 PNG，放入 `design/assets/free-method-night-window.png`；HTML 使用本地相对路径并提供无图时的纯色回退。

## 数据映射

新增纯前端分类函数，不改 `data/offers.json` 的事实字段：

- `free_quota`：`freeMechanism` 为 `daily_quota`、`weekly_quota`、`monthly_quota` 或 `permanent`，且不是 IDE / 下载权重 / 低价 pay-as-you-go；Web API 可同时落入此类和 Web 工具类。
- `credits`：`freeMechanism` 为 `trial`、`limited_time_free`，或记录具有明确一次性 credits / 次数描述。
- `ide`：`productType === free_ide` 或 token 包含 `ide`。
- `promo`：`freeMechanism === first_month_promo`、存在 `timeWindow`，或 `type` 包含 `promo`。
- `web`：`productType === web_infrastructure` 或记录明确提供网页入口 / `web_use` token；UI 文案使用“网页 / Web 工具”，不把 API 误称为网页产品。
- `download_lowcost`：`productType === open_weights` 或 `productType === payg`。

分类可重叠；列表按当前筛选展示，统计使用去重后的 offer 数量。证据状态、`lastVerifiedAt`、地区和有效期始终来自原始数据，不在 UI 层推断新的免费承诺。

## 交互与无障碍

- 侧栏分类、顶部统计块和列表分类标签共享同一 `data-filter` 状态。
- 搜索时临时切换到全部结果，清空搜索后恢复原分类。
- 时段优惠详情显示访客浏览器时区；没有 `timeWindow` 时不渲染转换提示。
- 分类按钮使用真实 `button` 元素，当前项有 `aria-pressed`；详情抽屉继续支持 Escape 和背景点击关闭。
- Image2 视觉使用空 `alt`，因为它是装饰；关键信息不依赖图片。

## 验收标准

- 首页主导航只出现 6 个新分类，不出现 7 个能力分类作为主入口。
- 27 条现有 offer 均仍可搜索、排序、打开详情；分类统计和列表结果一致。
- 免费、试用、首月优惠、开源权重、低价付费在视觉标签和文案上可区分。
- 包含 `timeWindow` 的条目能看到时区提示；没有时间窗口的条目不会显示虚构的夜间活动。
- 桌面端主内容各列对齐；窄屏端无横向页面溢出，列表可局部横向滚动。
- `python -m unittest discover -s tests -v` 通过，`python scripts/build_static.py --check` 通过。
- Image2 素材存在于项目内，页面在素材加载失败时仍可读。
