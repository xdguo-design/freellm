# AdSense 审核就绪整改实施计划

> **给代理执行者：** 任务使用 `- [ ]` 勾选跟踪；按任务逐项执行并在内容策略与索引范围确定后同步用户。不要在 `main` 上直接实施。

**目标：** 提升 FreeLLM 的内容独特价值、时效可信度与索引质量，为 AdSense 重新审核做好站点准备。

**非目标（Out of Scope）：** 不向 AdSense 重新提交、不改账户设置、不部署生产、不扩展广告位、不承诺 Google 审核通过。

**架构要点：** 延续 Python 静态站点与现有数据驱动生成器。页面审计表记录 URL 级处置理由，少量索引例外由 JSON 策略驱动页面 robots 元数据和 sitemap；限时优惠以官方来源复核并更新权威 offer 数据。原创指南使用独立编辑数据输入，由 `build_seo_pages.py` 生成双语静态页并加入 sitemap。

**技术栈/运行方式：** Python 3、静态 HTML、JSON、Vercel 配置；目标检查命令为 `pytest -q`、`python scripts/build_seo_pages.py --check`、`python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-10-06-adsense审核就绪设计.md`

**执行分支：** 获得实施授权后，从已审阅的设计提交创建隔离工作区和 `codex/adsense-review-readiness` 分支。当前目录有其他未提交改动；执行时只带入本设计及本计划，不复制无关工作区文件。不得直接在 `main` 修改站点实现。

---

## 文件变更清单（先写这个再拆任务）

- 新建：
  - `docs/audits/2026-10-adsense-page-review.csv`：为 sitemap 中每个 URL 记录页面用途、独立价值、来源/时效证据、处置与理由。
  - `data/seo-index-overrides.json`：保存逐页审计确认需要 `noindex,follow` 的少数路径及其理由、复核日期。
  - `data/editorial-guides.json`：保存三篇双语原创指南的标题、正文段落、维护者、日期、方法限制和官方来源。
- 修改：
  - `scripts/build_seo_pages.py`：加载索引例外和原创指南，渲染对应 robots 元数据、sitemap、跳转和文章静态页。
  - `data/offers.json`：根据官方来源更新已结束或即将结束的限时免费条件。
  - `crawler/schema.py`：校验索引例外和编辑指南所需的字段、路径、日期、语言及来源格式。
  - `vercel.json`：为两个已合并的 LongCat 旧路由配置永久跳转。
  - `tests/test_seo_pages.py`：覆盖索引例外、文章生成、过期优惠文案与 sitemap 一致性。
  - `tests/test_model_pages.py`：确认模型页现有单记录 `noindex` 规则保留，并支持经审计的额外例外。
  - `tests/test_adsense.py`：确认新增 `noindex` 页面没有 AdSense loader，且 sitemap 不包含该 URL。
  - `tests/test_vercel_config.py`：检查 LongCat 永久跳转配置。
- 生成：
  - `guides/` 下新文章 HTML、`.seo-pages-manifest.json`、`sitemap*.xml`、受数据影响的资源页及首页静态内容。

当前已有的单记录模型页 `noindex`、薄分类页 `noindex` 和 sitemap 排除规则要保留；分类的已合并 LongCat 静态页目前只有 `noindex` 与即时 meta refresh，本计划补充真实服务器永久跳转。

## 任务列表（可勾选执行）

### 任务 1：逐 URL 审查并建立处置登记表

**涉及文件：**
- 新建：`docs/audits/2026-10-adsense-page-review.csv`
- 输入：`sitemap-pages.xml`、`sitemap-offers.xml`、`sitemap-providers.xml`、`sitemap-models.xml` 及对应公开页面

- [ ] **步骤 1：导出当前 sitemap URL 清单**

运行：

```powershell
@'
from pathlib import Path
import csv
import xml.etree.ElementTree as ET

ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
root = Path(".")
urls = []
for sitemap in ("sitemap-pages.xml", "sitemap-offers.xml", "sitemap-providers.xml", "sitemap-models.xml"):
    tree = ET.parse(root / sitemap)
    for loc in tree.findall(".//s:loc", ns):
        urls.append((loc.text or "", sitemap))
assert len(urls) == 178, f"Expected 178 current URLs, found {len(urls)}"
assert len({url for url, _ in urls}) == len(urls), "Duplicate sitemap URL"
out = root / "docs/audits/2026-10-adsense-page-review.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["url", "sitemap", "page_purpose", "independent_value", "evidence_and_freshness", "required_changes", "final_disposition", "reason", "reviewed_at"])
    for url, sitemap in sorted(urls):
        writer.writerow([url, sitemap, "", "", "", "", "", "", ""])
print(f"Wrote {len(urls)} URL rows to {out}")
'@ | python -
```

预期：创建 CSV，输出 `Wrote 178 URL rows ...`；URL 唯一且每个 sitemap URL 恰有一行。

- [ ] **步骤 2：审查模型页与厂商页**

审查 `sitemap-models.xml` 的 29 个模型页和 `sitemap-providers.xml` 的 46 个厂商页。记录页面任务、独有信息、官方来源及最近核验时间。模型页重点核对外部目录数据是否有 FreeLLM 的比较或操作增量；厂商页核对是否给出平台入口、地区/注册条件或本站操作步骤。`final_disposition` 填 `keep_indexable` 或 `noindex`；`noindex` 必须说明缺少的用户价值；`required_changes` 记录补足独立价值所需的具体内容。

预期：75 行记录完成，有来源和日期证据，且无未经来源支持的结论。

- [ ] **步骤 3：审查资源页**

审查 `sitemap-offers.xml` 的 70 个资源页；核对官方来源、免费与付费边界、注册/计费条件、地区、当前期限、最后核验日和页面中的实际操作价值。明确区分长期免费方案与限时活动。

预期：70 行记录完成；所有到期或无法证实的促销都记录需要的内容更新，不再将未经确认的条件判为当前有效。

- [ ] **步骤 4：审查其他 sitemap 页面**

审查 `sitemap-pages.xml` 的 33 个 URL，覆盖首页、关于/隐私/条款、目录入口、分类和现有指南。每页写明独立访客任务和需补充/修正的内容；法律页面同时核对声明与当前站点实际配置。

预期：33 行记录完成，无纯导航页或重复表格被误写为原创指南。

- [ ] **步骤 5：完成全量处置并复核审计表**

对 `required_changes` 中的实质性问题作出明确修订范围，然后填写每行的 `final_disposition`（仅 `keep_indexable` 或 `noindex`）、`reason` 和 `reviewed_at`。`noindex` 的路径进入任务 2 策略文件；`keep_indexable` 页面按任务 3 和任务 4 完成内容补充后保留索引。

预期：178 行全部完成，无空决策、无未经来源支持的结论；每个 `noindex` 都有具体理由。

### 任务 2：让经审核的索引例外控制 robots、AdSense loader 与 sitemap

**涉及文件：**
- 新建：`data/seo-index-overrides.json`
- 修改：`scripts/build_seo_pages.py`
- 修改：`crawler/schema.py`
- 测试：`tests/test_seo_pages.py`、`tests/test_model_pages.py`、`tests/test_adsense.py`

- [ ] **步骤 1：添加索引例外契约测试**

在 `tests/test_seo_pages.py` 添加如下行为测试；fixture 中用一个有两条模型记录的 slug 作为例外项：

```python
def test_audited_noindex_override_removes_page_from_sitemap_and_adsense(tmp_path):
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    rich_slug = next(slug for slug, records in model_record_groups(models).items() if len(records) > 1)
    path = f"/models/{rich_slug}/"
    result = build_site(
        OFFERS_PATH,
        tmp_path,
        site_url="https://freellm.top",
        seo_index_overrides={
            path: {
                "reason": "Only repeats provider catalogue fields; no independent usage guidance.",
                "reviewedAt": "2026-10-06",
            }
        },
    )
    page = (tmp_path / "models" / rich_slug / "index.html").read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,follow">' in page
    assert "adsbygoogle.js" not in page
    sitemap = "".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("sitemap-*.xml"))
    assert f"https://freellm.top{path}" not in sitemap
```

测试文件已有 `json` 与 `MODELS_PATH`；从 `scripts.build_seo_pages` 增加 `model_record_groups` 导入，并使用本地目录中确实存在的多记录模型 slug，避免策略测试创建不存在的虚构路径。

若现有 `build_site` 不接受策略参数，测试先通过现有签名构造输出后失败；扩展签名必须保持默认行为兼容。

- [ ] **步骤 2：运行目标测试确认失败**

运行：`pytest tests/test_seo_pages.py::test_audited_noindex_override_removes_page_from_sitemap_and_adsense -q`

预期：失败指出策略参数或相应的 noindex/sitemap 行为尚不存在。

- [ ] **步骤 3：实现策略读取与生成器集成**

在 `scripts/build_seo_pages.py` 增加读取 `data/seo-index-overrides.json` 的函数；由 `build_site` 读取并传入 `_expected_files`。将例外路径与现有分类/模型默认索引规则合并：对应页面输出 `noindex,follow`、不输出 AdSense loader、从全部子 sitemap 移除；其他页面继续使用原默认规则。`sitemap_section_paths` 过滤完整 canonical path，`render_model_aggregate_page`、`render_provider_page`、`render_offer_page` 与分类页面以同一判定函数控制 robots 和 loader。`crawler/schema.py` 校验 path 为站内绝对路径、reason 非空、reviewedAt 为 ISO 日期，拒绝重复路径和未知 disposition。将任务 1 的实际审核结果写入 JSON；只录入 disposition 为 `noindex` 的页面。

- [ ] **步骤 4：运行相关测试确认行为**

运行：

```powershell
pytest tests/test_seo_pages.py tests/test_model_pages.py tests/test_provider_pages.py tests/test_adsense.py -q
```

预期：策略例外页面无 loader 且不在 sitemap；未覆盖的索引页面仍可索引；现有单记录模型页和薄分类页规则继续通过。

### 任务 3：复核所有限时优惠并清除过期展示

**涉及文件：**
- 修改：`data/offers.json`
- 修改：`tests/test_seo_pages.py`
- 生成：相关 `offers/*/index.html` 及 `design/free-china-ai-index.html`

- [ ] **步骤 1：添加过期 Qoder 展示回归测试**

在 `tests/test_seo_pages.py` 为当前 Qoder 记录增加渲染断言：已结束的 0× Credits 活动日期和 badge 不得作为当前权益展示；正式页仍可展示经官方来源核验的基础计划条件。

```python
def test_qoder_current_offer_fields_do_not_present_expired_promotion():
    offers = read_offers()
    qoder = next(offer for offer in offers if offer["id"] == "qoder")
    current_fields = " ".join(str(qoder.get(key) or "") for key in ("badges", "freeSummary", "validitySummary", "quota", "freeModels"))
    page = render_offer_page(qoder, offers, "https://freellm.top")
    assert "2026-09-30" not in current_fields
    assert "2026-09-30" not in page
    assert "QWEN3.8 0× UNTIL SEP 30" not in page
```

- [ ] **步骤 2：运行目标测试确认失败**

运行：`pytest tests/test_seo_pages.py::test_qoder_current_offer_fields_do_not_present_expired_promotion -q`

预期：旧促销文案触发断言失败。

- [ ] **步骤 3：逐条查官方来源并修订限时数据**

检查 `data/offers.json` 中所有包含明确日期、限时、活动结束、每日领取窗口或试用期限的字段，并对照条目 `sourceUrls` 的官方页面。优先复核 Qoder 记录及 2026-10-07 到期的 GLM 活动。同步校正 `badges`、`freeSummary`、`validitySummary`、`why`、`mechanism`、`validity`、`quota`、`evidence`、`notes`、`lastVerifiedAt` 与 `freeModels`；已结束活动的日期从当前可见内容中清除，不能证实仍有效的促销从当前权益展示移除，仍有效的基础方案只按官方当前条件保留。不得把到期活动继续描述为当前可用。

- [ ] **步骤 4：重建静态首页和详情页**

运行：

```powershell
python scripts/build_static.py
python scripts/build_seo_pages.py
```

预期：Qoder 当前列表卡片和详情页不再展示已结束促销，其他已核实的免费权益仍可见；构建完成并输出生成页面数量。

- [ ] **步骤 5：运行优惠与生成器目标检查**

运行：

```powershell
pytest tests/test_seo_pages.py tests/test_build_static.py -q
python scripts/build_static.py --check
python scripts/build_seo_pages.py --check
```

预期：目标测试通过；两个 `--check` 命令分别报告静态首页和 SEO 产物均为 current。

### 任务 4：新增有实证、可复核的原创指南

**涉及文件：**
- 新建：`data/editorial-guides.json`
- 修改：`scripts/build_seo_pages.py`
- 修改：`crawler/schema.py`
- 修改：`tests/test_seo_pages.py`
- 生成：`guides/choosing-free-ai-apis/index.html`、`guides/how-we-check-ai-api-access/index.html`、`guides/how-freellm-verifies-resources/index.html` 及 sitemap

- [ ] **步骤 1：添加编辑指南数据与渲染的失败测试**

在 `tests/test_seo_pages.py` 添加测试，加载 `data/editorial-guides.json` 并构建到 `tmp_path`；逐篇断言中英文标题和正文、维护者、发布日期、实质性复核日期、方法或适用限制、官方来源链接和 canonical 存在，并断言这三个 URL 加入 `sitemap-pages.xml`。

```python
def test_editorial_guides_render_sources_dates_and_bilingual_content(tmp_path):
    build_site(OFFERS_PATH, tmp_path, site_url="https://freellm.top")
    for slug in (
        "choosing-free-ai-apis",
        "how-we-check-ai-api-access",
        "how-freellm-verifies-resources",
    ):
        page = (tmp_path / "guides" / slug / "index.html").read_text(encoding="utf-8")
        assert 'rel="canonical"' in page
        assert 'lang="zh-CN"' in page and 'lang="en"' in page
        assert "官方来源" in page and "Official sources" in page
        assert "最近复核" in page and "Last reviewed" in page
    sitemap = (tmp_path / "sitemap-pages.xml").read_text(encoding="utf-8")
    assert "https://freellm.top/guides/choosing-free-ai-apis/" in sitemap
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_seo_pages.py::test_editorial_guides_render_sources_dates_and_bilingual_content -q`

预期：因指南数据文件及生成页面尚不存在而失败。

- [ ] **步骤 3：新增结构化编辑内容并接入静态生成**

在 `data/editorial-guides.json` 为三篇指南建立双语字段：`slug`、`title`、`description`、`maintainer`、`publishedAt`、`reviewedAt`、`method`、`limitations`、`sections`、`sources`。每个正文段落由维护者撰写，并用仓库中的可追溯实测记录或当前官方文档支持。`how-we-check-ai-api-access` 需区分 HTTP 可达性、RTT 和模型生成耗时；`choosing-free-ai-apis` 覆盖免费额度、地区、账号/计费要求和时效；`how-freellm-verifies-resources` 说明来源优先级、复核流程、过期处理和纠错渠道。不得伪造实际使用经历、未执行的测试或结论。

在 `crawler/schema.py` 验证 slug 唯一、日期格式、双语正文非空、每篇至少一个 HTTPS 来源以及必填限制说明。在 `scripts/build_seo_pages.py` 增加 `render_editorial_guide_page()`，由 `_expected_files` 读取数据、生成三个静态 HTML 文件并将固定路径并入 `sitemap_section_paths`；文章页采用现有编辑样式、静态导航和语言切换规则。

- [ ] **步骤 4：运行文章与 sitemap 目标测试**

运行：`pytest tests/test_seo_pages.py -q`

预期：三篇指南的双语内容、元数据、来源、索引规则和生成器产物断言通过。

### 任务 5：将旧 LongCat URL 配置为永久跳转并核对隐私说明

**涉及文件：**
- 修改：`vercel.json`
- 修改：`tests/test_vercel_config.py`
- 检查：`privacy/index.html`、`about/index.html`、`terms/index.html`

- [ ] **步骤 1：添加 Vercel 跳转配置失败测试**

新建 `tests/test_vercel_config.py`，检查旧路由永久跳转指向正式 LongCat 详情页：

```python
import json
from pathlib import Path

def test_merged_longcat_routes_have_permanent_redirects():
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))
    redirects = {item["source"]: item for item in config["redirects"]}
    for source in (
        "/offers/longcat-api", "/offers/longcat-api/",
        "/offers/longcat-download", "/offers/longcat-download/",
    ):
        assert redirects[source]["destination"] == "/offers/longcat-2-0/"
        assert redirects[source]["permanent"] is True
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_vercel_config.py -q`

预期：缺少 LongCat 路由时，测试报告对应 source 未配置。

- [ ] **步骤 3：加永久跳转并核对隐私声明**

在 `vercel.json` 的 `redirects` 数组中沿用已有 `/skills/lab/` 配置格式，为两个 LongCat 旧路由的有斜杠和无斜杠 URL 都添加 `permanent: true`，四条规则目标均为 `/offers/longcat-2-0/`。保留 SEO 生成器的 legacy HTML 作为非 Vercel 本地预览回退，但不把它们放入 sitemap。

对照 `privacy/index.html` 实际描述与当前页面 AdSense loader、广告位配置及隐私链接。现有说明准确则保留；若存在差异，只修改相应中英文段落，并将具体差异记录在审计 CSV。

- [ ] **步骤 4：运行路由配置与 SEO 定向检查**

运行：`pytest tests/test_vercel_config.py tests/test_seo_pages.py::test_legacy_offer_redirects_are_kept_but_not_indexed -q`

预期：两条旧路由永久跳转配置通过；本地生成的回退页仍带 `noindex,follow`，并且不进入 sitemap。

### 任务 6：生成全站产物并逐项复核审核准备清单

**涉及文件：**
- 生成：`design/free-china-ai-index.html`、`offers/`、`guides/`、`models/`、`providers/`、`category/`、`.seo-pages-manifest.json`、`sitemap*.xml`
- 复核：`docs/audits/2026-10-adsense-page-review.csv`、`ads.txt`、`robots.txt`

- [ ] **步骤 1：构建 SEO 页面**

运行：`python scripts/build_seo_pages.py`

预期：生成完成、输出索引页/资源页数量、报告被清理的旧生成页数量。

- [ ] **步骤 2：检查源和生成产物是否一致**

运行：

```powershell
python scripts/build_seo_pages.py --check
python scripts/build_static.py --check
```

预期：分别输出 `current SEO output` 和静态构建产物 current；没有 stale page、missing page 或重复 sitemap URL。

- [ ] **步骤 3：运行相关与全量回归检查**

运行：

```powershell
pytest tests/test_seo_pages.py tests/test_model_pages.py tests/test_provider_pages.py tests/test_build_static.py tests/test_adsense.py tests/test_vercel_config.py -q
pytest -q
```

预期：相关测试与全量测试通过；若现有环境导致测试跳过，记录具体 skip，不通过删除或降低断言处理。

- [ ] **步骤 4：人工复核生成站点清单**

逐项核查：审计 CSV 中 178 个现有 URL 的处置与最终页面一致；新指南均有来源和维护日期；过期活动不再显示为现行权益；noindex 页无 AdSense loader 且不在 sitemap；永久跳转目标有效；核心导航、关于、隐私、条款、联系、`robots.txt`、`ads.txt` 和 AdSense 发布商代码仍可访问。

预期：审计 CSV 与实际生成页面无矛盾，重要页面可由站内导航到达，`ads.txt` publisher ID 为 `pub-2461062743308239`。

- [ ] **步骤 5：提交实施改动**

运行：

```powershell
git status --short
git diff --check
git diff --stat
```

确认范围仅包含隔离工作区内本计划列出的内容、生成产物和测试；原工作区里的 `Temp/` 与其他未提交改动保持不动。分批提交数据和生成器改动，提交信息使用 `feat: improve AdSense review readiness`；不部署、不访问 AdSense 提交审核。

## 质量门控与暂停点

- 设计文档要求的页面审查、优惠时效、原创指南、技术索引、隐私说明和最终审核清单都对应本计划任务。
- 如官方来源无法确认免费条件或地区规则，将相应优惠降为待复核并从当前权益推荐中移除；不得猜测补齐。
- 如果 CSV 判断需要永久跳转的目标不存在或语义不匹配，暂停该路径处置并向用户询问，不创建猜测性跳转。
- 实施只能在用户批准本计划与执行方式后开始；只能在新分支执行。
- 发布与 AdSense 重新提交需单独获得用户授权。
