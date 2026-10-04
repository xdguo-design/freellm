# 精选模型适用性与速度对比实施计划

> **给代理执行者：** 在当前会话逐项执行本计划，任务使用 `- [ ]` 跟踪，按 RED → GREEN → REFACTOR 完成每个行为。

**目标：** 在 `/models/` 精选集合中加入有证据的地区状态、方向明确的能力标签、真实速度状态、组合筛选和最多 3 个模型的对比视图。

**非目标（Out of Scope）：** 不改全部模型目录；不自动调用外部模型 API，不使用任何付费额度；不把网络探测速度当作模型生成速度；不推断没有证据的生成能力。

**架构要点：** `data/models-curated.json` 仍是精选集合唯一来源；每条模型可以携带可选的地区证据、能力证据和速度基准数据。`scripts/build_seo_pages.py` 校验并输出可读卡片与筛选属性，`js/featured-models.js` 只管理精选页上的筛选和比较交互。缺少有效证据时由页面明确展示“待核实”或“未实测”。

**技术栈/运行方式：** Python 3、pytest、静态 HTML/CSS/原生 JavaScript；运行 `pytest tests/test_model_pages.py -q` 和新建的 `pytest tests/test_featured_models.py -q`。浏览器验收使用本地静态 HTTP 服务和浏览器开发工具。

**关联设计文档：** `docs/specs/2026-10-03-featured-model-comparison-design.md`

---

## 文件变更清单

- 新建：
  - `scripts/featured_models.py`（验证地区证据、能力方向和可比较基准，并提供卡片使用的规范化数据）
  - `js/featured-models.js`（精选卡片地区/能力筛选、结果数和最多 3 项比较交互）
  - `js/featured-models.test.cjs`（Node 内置测试运行器验证纯筛选/比较函数）
  - `tests/test_featured_models.py`（纯数据规则和无效/缺失记录测试）
  - `docs/specs/plans/2026-10-04-featured-model-comparison.md`（本实施计划）
- 修改：
  - `scripts/build_seo_pages.py`（使用精选证据字段渲染标签、状态、对比数据和脚本引用）
  - `data/models-curated.json`（仅为来源已核实的条目添加 `verifiedRegions`、`verifiedCapabilities` 或 `benchmark`；当前没有真实生成基准，不能写入虚构速度值）
  - `tests/test_model_pages.py`（验证精选页面的筛选控件、状态标签和对比入口）
  - `models/index.html`（重新生成 `/models/` 静态页面）

## 数据契约

精选条目的可选证据字段：

```json
{
  "servicePath": "https://provider.example/v1/chat/completions",
  "verifiedRegions": ["domestic", "international"],
  "regionEvidenceUrl": "https://provider.example/docs/regions",
  "regionCheckedAt": "2026-10-04",
  "verifiedCapabilities": [
    {"name": "image", "direction": "input", "evidenceUrl": "https://provider.example/docs/vision", "checkedAt": "2026-10-04"},
    {"name": "video", "direction": "output", "evidenceUrl": "https://provider.example/docs/video", "checkedAt": "2026-10-04"}
  ],
  "benchmark": {
    "protocolVersion": "text-stream-v1",
    "taskId": "short-answer-zh-v1",
    "language": "zh",
    "temperature": 0,
    "maxOutputTokens": 256,
    "warmups": 1,
    "sampleCount": 3,
    "ttftMsMedian": 420,
    "outputTokensPerSecondMedian": 36.4,
    "testRegion": "domestic",
    "servicePath": "https://provider.example/v1/chat/completions",
    "testedAt": "2026-10-04",
    "rawResultRef": "data/benchmarks/example.json"
  }
}
```

The example values above are fixture-only. The production curated data must not receive invented measurements. Region values are `domestic` and `international`; a displayed “国内外均可调用” requires both values. A comparable text benchmark requires version, task ID, language, route, region, date, 1 warmup, 3 samples, and both median metrics. Benchmarks compare only when protocol version, task ID, language, and route type are compatible.

## 任务列表

### 任务 1：规范化并验证证据数据

**涉及文件：** 新建 `scripts/featured_models.py`、新建 `tests/test_featured_models.py`。

- [ ] **步骤 1：先写地区和能力证据行为测试**

```python
def test_unverified_region_is_unknown():
    assert normalize_region({}) == {
        "regions": [],
        "label": "待核实",
        "filterValue": "unknown",
    }

def test_both_verified_regions_are_labeled_as_both():
    assert normalize_region({"verifiedRegions": ["domestic", "international"]})["label"] == "国内外均可调用"

def test_modality_alone_does_not_claim_generation():
    labels = normalize_capabilities({"modality": ["image", "audio", "video"]})
    assert labels == ["图片·方向待核实", "音频·方向待核实", "视频·方向待核实"]

def test_verified_output_direction_is_renderable_as_generation():
    model = {"verifiedCapabilities": [{"name": "image", "direction": "output", "evidenceUrl": "https://example.com/image", "checkedAt": "2026-10-04"}]}
    assert normalize_capabilities(model) == ["图片生成"]
```

- [ ] **步骤 2：运行并确认 RED**

运行：`pytest tests/test_featured_models.py -q`  
预期：因 `scripts.featured_models` 尚未创建而失败，不能因测试语法错误失败。

- [ ] **步骤 3：实现纯函数与严格基准校验**

新增 `normalize_region(model)`、`normalize_capabilities(model)` 和 `comparable_benchmark(model)`。无证据地区返回 unknown；仅在证据 URL 和日期有效时接受地区/能力记录；基准缺任一可比较必填字段就返回 `None`。能力输入/输出映射到分开的用户标签。函数不得发网络请求或读写文件。

- [ ] **步骤 4：运行并确认 GREEN**

运行：`pytest tests/test_featured_models.py -q`  
预期：上述四个行为通过，并补测未知方向、非法地区、缺日期基准和错协议比较。

### 任务 2：渲染地区、能力与速度状态

**涉及文件：** 修改 `scripts/build_seo_pages.py`、`tests/test_model_pages.py`。

- [ ] **步骤 1：先写页面生成回归测试**

为 `tests/test_model_pages.py` 增加两项页面生成测试：

```python
def test_featured_cards_show_unknown_and_untested_states(tmp_path):
    page = build_featured_fixture_page(tmp_path)
    assert "待核实" in page
    assert "未实测" in page
    assert "图片·方向待核实" in page

def test_featured_page_includes_region_and_capability_filters(tmp_path):
    page = build_featured_fixture_page(tmp_path)
    assert 'data-filter="region"' in page
    assert 'data-filter="capability"' in page
    assert 'id="featured-model-count"' in page
```

测试 fixture 使用一个无地区/基准记录且 `modality` 为 image/audio/video 的精选模型；`build_featured_fixture_page` 调用真实的 `render_models_landing_page`，其他集合参数使用空列表。

测试辅助函数按以下方式构造数据，确保精选模型能通过 renderer 的当前目录过滤：

```python
def build_featured_fixture_page():
    from scripts.build_seo_pages import render_models_landing_page

    model = {
        "id": "fixture/model",
        "providerId": "fixture",
        "provider": "Fixture Provider",
        "model": "Fixture Model",
        "modality": ["image", "audio", "video"],
    }
    return render_models_landing_page(
        offers=[], models=[model], vendor_directory=[],
        site_url="https://freellm.top", curated_models=[model],
    )
```

- [ ] **步骤 2：运行并确认 RED**

运行：`pytest tests/test_model_pages.py::test_featured_cards_show_unknown_and_untested_states tests/test_model_pages.py::test_featured_page_includes_region_and_capability_filters -q`  
预期：页面尚无这些标签/控件，测试因目标断言失败。

- [ ] **步骤 3：最小实现卡片字段**

在 `render_models_landing_page` 的 `featured_card` 中调用 `scripts.featured_models` 规范化函数；输出 `data-region`、`data-capabilities`，显示地区验证标签、细分能力标签、有效基准速度或“未实测”。只有 `comparable_benchmark` 接受的记录才显示 TTFT、token/s、测试地区和日期。增加带 `data-filter` 的地区/能力筛选控件和结果数节点。卡片之外保持全部模型链接及现有集合口径不变。

- [ ] **步骤 4：运行相关测试**

运行：`pytest tests/test_featured_models.py tests/test_model_pages.py -q`  
预期：规范化、生成页和已有精选/全部集合测试通过。

### 任务 3：实现筛选与三模型比较

**涉及文件：** 新建 `js/featured-models.js`，修改 `scripts/build_seo_pages.py`、`tests/test_model_pages.py`。

- [ ] **步骤 1：先写交互挂载和限制测试**

页面生成测试增加脚本引用及比较视图断言：

```python
assert "/js/featured-models.js?v=" in page
assert 'id="featured-model-comparison"' in page
assert 'data-compare-limit="3"' in page
```

`js/featured-models.test.cjs` 使用 Node 内置测试运行器验证地区与能力组合筛选、3 项比较上限、移除选择、测速协议匹配和不调用 `localStorage` 的内存状态行为。

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { filterModels, addComparedModel, benchmarksComparable } = require("./featured-models.js");

test("region and capability filters combine with AND", () => {
  const models = [
    { id: "a", region: "domestic", capabilities: ["image"] },
    { id: "b", region: "domestic", capabilities: ["text"] },
  ];
  assert.deepEqual(filterModels(models, { region: "domestic", capability: "image" }).map(x => x.id), ["a"]);
});

test("only three model ids can be selected for comparison", () => {
  const selected = ["a", "b", "c"];
  assert.equal(addComparedModel(selected, "d").accepted, false);
});

test("benchmarks with different protocol or task are not comparable", () => {
  assert.equal(benchmarksComparable({ protocolVersion: "v1", taskId: "a", language: "zh" }, { protocolVersion: "v2", taskId: "a", language: "zh" }), false);
});
```

- [ ] **步骤 2：运行并确认 RED**

运行：`pytest tests/test_model_pages.py -q`  
预期：页面脚本引用和比较视图尚不存在，目标断言失败。

- [ ] **步骤 3：实现原生 JavaScript 交互**

在 `js/featured-models.js` 中只查询 `#featured-models` 范围内的控件和卡片。筛选按 `data-region` 与 `data-capabilities` 做 AND 组合并更新可见数。比较集合使用 `Set` 保存最多 3 个卡片 ID；上限时显示可访问的提示；比较面板提供逐项移除和清空按钮。比较表的速度字段仅在协议、任务、语言一致时并列数值，否则对相应行写“测试口径不同，不可直接比较”。

在生成页面中加入筛选结果空状态、对比状态提示和带横向滚动容器的比较表；在 HTML 末尾加载版本化脚本。脚本只依赖原生 DOM，不引入库。

- [ ] **步骤 4：运行静态交互测试**

运行：`node --test js/featured-models.test.cjs`  
预期：组合筛选、上限和基准兼容三个纯交互行为全部通过；随后运行 `pytest tests/test_featured_models.py tests/test_model_pages.py -q`，页面结构测试通过。

### 任务 4：生成静态页并做浏览器验收

**涉及文件：** 重新生成 `models/index.html`；按本计划修复前述实现问题。

- [ ] **步骤 1：运行全页相关测试**

运行：`pytest tests/test_model_pages.py tests/test_featured_models.py -q`  
预期：全部通过。

- [ ] **步骤 2：生成 `/models/` 页面**

运行：`python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top`。预期生成命令成功结束，`models/index.html` 含精选卡片、筛选/对比结构和 `/js/featured-models.js` 引用，全部模型页面保持原集合。

- [ ] **步骤 3：运行浏览器验收**

运行：`python -m http.server 8765`，打开 `http://127.0.0.1:8765/models/`。逐项验证：地区和能力筛选可组合；无结果时能清空；最多选 3 项；第 4 项出现提示；可移除一项和清空；测速缺失显示“未实测”；窄屏比较区域可以横向滚动且指标名完整；中英文标签切换正常。预期页面控制台无脚本错误、卡片没有横向溢出。

- [ ] **步骤 4：检查差异与工作区**

运行：`git diff --check`、`git status --short`。预期本次实现文件无空白错误；不暂存工作区中与本功能无关的已有改动。

## 质量门控

- [ ] 生产速度数据全部具有真实原始记录；现有网络探测速度没有进入模型基准字段。
- [ ] `data/models-curated.json` 中缺失或不完整的地区/能力/速度证据保持未核实状态。
- [ ] 所有筛选、对比和无数据状态都在 `/models/` 精选区作用，不改变 `/models/all/`。
- [ ] 在当前 `dev` 分支实施；不直接修改 `main`。
