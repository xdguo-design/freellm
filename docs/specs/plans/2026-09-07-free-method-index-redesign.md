# Free AI Index「免费方式索引」重设计实施计划

> **给代理执行者：** 本计划基于已批准设计文档，按勾选项执行；每完成一个阶段运行对应验证命令。

**目标：** 将首页主导航和结果筛选改为 6 类“获得免费”的方式，并加入 Image2 夜间优惠视觉，同时保持现有数据、详情抽屉和 SEO 能力。

**架构要点：** 继续使用单文件静态首页 `design/free-china-ai-index.html` 和 `data/offers.json`，分类在浏览器端由纯函数从现有 offer 字段推导，不改事实数据。新增 Image2 PNG 只作为 Hero 装饰图，列表和状态信息仍由 HTML/JSON 驱动。

**技术栈：** 原生 HTML/CSS/JavaScript、Python unittest、静态构建脚本。

**关联设计文档：** `docs/specs/2026-09-07-free-method-index-redesign-design.md`

---

## 文件清单

- 修改：`design/free-china-ai-index.html` —— 重做导航、Hero、统计块、分类筛选和结果行样式；保留详情抽屉、JSON-LD、数据加载和搜索排序。
- 新建：`design/assets/free-method-night-window.png` —— Image2 生成的 Hero 装饰视觉。
- 修改：`tests/test_e2e_static.py` —— 增加首页必须包含 6 类入口、素材引用和分类逻辑关键字的静态断言。
- 新建：`docs/specs/2026-09-07-free-method-index-redesign-design.md` —— 已批准的设计规格。

### 任务 1：为 Image2 生成并落盘 Hero 素材

- [ ] 使用内置 Image2 生成横向抽象 editorial illustration：深蓝黑背景、黄色夜间时间窗 / 时钟、规整数据卡片、青绿色状态点；无品牌 Logo、无文字、无水印、无真实产品界面。
- [ ] 检查生成结果的构图、颜色和约束；若出现文字或品牌误导元素，单点迭代一次。
- [ ] 将最终 PNG 复制到 `design/assets/free-method-night-window.png`，确认文件存在且 HTML 可用相对路径访问。

### 任务 2：重做页面信息架构和样式

- [ ] 在 `design/free-china-ai-index.html` 的侧栏替换旧能力导航，保留 `all` 并新增 `free_quota`、`credits`、`ide`、`promo`、`web`、`download_lowcost` 六个入口；删除 `search`、`fetch`、`extract`、`crawl`、`map`、`browser`、`agent` 作为主入口的按钮。
- [ ] 将 Hero 改成 12 列布局：左侧标题和数据说明，右侧 `<img src="assets/free-method-night-window.png" alt="" />` 与总数统计；加入图片加载失败时的纯色背景回退。
- [ ] 将旧的 3 个 summary 块改成 5 个等宽统计块，分别显示免费额度、免费次数、免费 IDE、限时优惠、网页直用；数量由 `renderOffers` 动态写入。
- [ ] 将筛选 tabs 与侧栏共享新 `data-filter` 值；保留“可下载 / 低成本”入口，移除重复的能力 tabs。
- [ ] 调整 `.table-head` / `.offer` 为固定列：产品、免费方式、额度或价格、有效期、地区、验证状态、详情；统一 padding、line-height、截断和移动端滚动边界。
- [ ] 将黄色 notice 改为免费定义说明，并增加“夜间优惠会按浏览器时区换算”的提示；不加入未经数据支持的活动描述。

### 任务 3：实现分类推导和动态渲染

- [ ] 在 `design/free-china-ai-index.html` 的脚本区新增纯函数 `offerTokens(item)` 和 `offerCategory(item)`，按设计文档的 `freeMechanism` / `productType` / `type` / `timeWindow` 规则推导分类；分类允许重叠，优先使用明确的产品类型。
- [ ] 更新 `renderOffers`：以新分类计算统计，更新侧栏按钮 `<b>`、tabs `<em>`、Hero 总数、5 个 summary 值和“限时优惠”专题卡；能力 token 继续写入搜索字段和结果行标签。
- [ ] 更新 `rowArticleMarkup`：结果行的第二列展示主分类标签，第三列展示 `freeSummary` 或机制，保留能力小字、有效期、地区和验证状态。
- [ ] 更新 `applyFilters`：`all` 显示全部；新分类使用 `offerCategory(item)` 的结果匹配；搜索行为和清空后恢复原筛选的行为保持不变。
- [ ] 为筛选按钮设置 `aria-pressed`，并确保键盘操作、Escape 关闭详情抽屉和空结果状态继续工作。

### 任务 4：更新静态测试并构建校验

- [ ] 在 `tests/test_e2e_static.py` 增加断言：HTML 包含 6 个新 `data-filter` 值、Image2 素材路径、`offerCategory` 和 `timeWindow` 文案；HTML 不再包含旧能力导航按钮。
- [ ] 运行 `python -m unittest discover -s tests -v`，预期所有测试通过。
- [ ] 运行 `python scripts/build_static.py --check`，预期输出 `current: design/free-china-ai-index.html`。
- [ ] 启动静态服务 `python -m http.server 8000 --directory design`，用浏览器检查桌面和窄屏截图：主列对齐、分类切换、搜索、详情抽屉和素材加载均正常。
- [ ] 检查 `git diff --check`，确认无空白错误；检查 `git status --short`，确认只包含本次设计文档、素材、首页和测试变更。
