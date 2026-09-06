# Free AI Index 应用与抓取器实施计划

> **给执行者：** 任务使用 `- [ ]` 勾选跟踪；每一步都要先测试再实现，并在批次结束运行完整验证。

**目标：** 将单文件原型升级为 JSON 驱动的静态应用，并交付可审计的官方来源抓取器、差异审核队列和 `free-ai-offer-research` skill。

**非目标：** 不做用户登录、数据库后台、API Key 代理、统一网关、代注册、验证码绕过、账户余额读取和在线模型调用测试。

**架构要点：** `data/offers.json` 是公开目录的当前事实来源；页面通过 JSON 渲染列表，file 协议下使用同一份内嵌数据兜底。Python crawler 只访问公开官方页面，生成来源快照和审核队列，人工确认后才改变公开数据。

**技术栈/运行方式：** 原生 HTML/CSS/JavaScript；Python 3.11+ 标准库抓取、校验和差异；测试命令 `python -m unittest discover -s tests -v`；本地静态服务 `python -m http.server 8000`。

**关联设计文档：** `docs/specs/2026-09-06-free-ai-index-app-and-crawler-design.md`

---

## 文件变更清单

- 新建：
  - `data/offers.json`：12 条现有 offer 的规范化数据源。
  - `data/sources.json`：官方来源和允许抓取域名。
  - `data/review-queue.json`：变化与人工审核项目的持久化文件。
  - `data/snapshots/.gitkeep`：快照目录占位。
  - `crawler/__init__.py`：抓取器包入口。
  - `crawler/schema.py`：数据合同和校验函数。
  - `crawler/fetch.py`：公开页面抓取和证据提取。
  - `crawler/diff.py`：offer 快照差异和审核队列生成。
  - `crawler/cli.py`：validate、scan、diff、snapshot 命令行入口。
  - `scripts/build_static.py`：把 JSON 数据写入 HTML 的 file 协议兜底块。
  - `skills/free-ai-offer-research/SKILL.md`：抓取与核验技能主流程。
  - `skills/free-ai-offer-research/README.md`：技能安装和使用说明。
  - `skills/free-ai-offer-research/references/source-policy.md`：来源和访问边界。
  - `skills/free-ai-offer-research/references/offer-schema.md`：字段与证据规则。
  - `skills/free-ai-offer-research/references/review-checklist.md`：人工核验清单。
  - `skills/free-ai-offer-research/references/report-template.md`：技能输出模板。
  - `tests/test_schema.py`：数据合同测试。
  - `tests/test_diff.py`：差异和状态测试。
  - `.github/workflows/daily-check.yml`：每日校验和来源扫描任务。
- 修改：
  - `design/free-china-ai-index.html`：从硬编码 offer 迁移为 JSON 驱动渲染，保留现有视觉、SEO、IDE 高亮和直接跳转。

---

## 任务 1：建立数据合同和初始数据

**涉及文件：** `data/offers.json`、`data/sources.json`、`data/review-queue.json`、`crawler/schema.py`、`tests/test_schema.py`

- [ ] **步骤 1：编写失败测试**

```python
from crawler.schema import validate_offer, validate_offers

def test_all_seed_offers_have_required_fields():
    errors = validate_offers("data/offers.json")
    assert errors == []

def test_invalid_product_type_is_rejected():
    errors = validate_offer({"id": "x", "productType": "unknown"})
    assert any("productType" in error for error in errors)
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_schema -v`  
预期：因 `crawler.schema` 尚不存在而失败。

- [ ] **步骤 3：最小实现**

实现 `validate_offer()` 和 `validate_offers()`，校验：唯一 ID、必填字段、枚举值、ISO 日期、HTTPS 官方 URL、`sourceUrls` 非空、`status` 和 `confidence` 合法。

- [ ] **步骤 4：写入数据**

将原型的 12 条记录转换为统一 JSON；额外补充 `productType`、`freeMechanism`、`officialActionUrl`、`sourceUrls`、`evidence`、`confidence` 和 `lastVerifiedAt`。未知的手机号/银行卡条件写 `unknown`，不猜测。

- [ ] **步骤 5：运行并确认通过**

运行：`python -m unittest tests.test_schema -v`  
预期：所有 seed 数据合同测试通过。

---

## 任务 2：实现公开来源抓取与证据提取

**涉及文件：** `crawler/fetch.py`、`data/sources.json`、`tests/test_fetch.py`

- [ ] **步骤 1：编写失败测试**

测试固定 HTML fixture 能提取 `<title>`、价格关键词和一段有限证据；测试 `http://`、带凭据 URL、超过最大响应体的请求被拒绝。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_fetch -v`  
预期：因 `crawler.fetch` 尚不存在而失败。

- [ ] **步骤 3：最小实现**

实现 `fetch_public_page(url, allowed_domains, timeout=15, max_bytes=2_000_000)`：只允许 HTTPS、校验 host 在来源白名单中、使用固定 User-Agent、限制响应大小、读取后剥离 script/style，并返回 title、文本摘要、抓取时间和状态。

- [ ] **步骤 4：写入来源清单**

为每条 offer 保存至少一个官方 pricing/product/docs/model-card URL，并写入 `allowedDomains`；来源失败不得改写 offer 的 `status`。

- [ ] **步骤 5：运行并确认通过**

运行：`python -m unittest tests.test_fetch -v`  
预期：固定 fixture 测试通过，网络策略拒绝测试通过。

---

## 任务 3：实现快照差异和审核队列

**涉及文件：** `crawler/diff.py`、`crawler/cli.py`、`data/review-queue.json`、`tests/test_diff.py`

- [ ] **步骤 1：编写失败测试**

覆盖四类差异：新增 offer、额度变化、官方来源失败、明确状态变为 expired；断言每类输出 `changeType`、字段前后值和 `needsReview`。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_diff -v`  
预期：因 `crawler.diff` 尚不存在而失败。

- [ ] **步骤 3：最小实现**

实现 `compare_offers(previous, current)` 和 `build_review_queue(changes)`；任何关键字段变化默认进入人工审核，来源单次失败只产生 `source_unavailable` 事件。

- [ ] **步骤 4：实现 CLI**

提供：

```text
python -m crawler.cli validate data/offers.json
python -m crawler.cli diff --previous data/offers.json --current data/offers.json --out data/review-queue.json
python -m crawler.cli snapshot --input data/offers.json --dir data/snapshots
python -m crawler.cli scan --sources data/sources.json --out data/snapshots/latest-scan.json
```

- [ ] **步骤 5：运行并确认通过**

运行：`python -m unittest tests.test_diff -v` 和 `python -m crawler.cli validate data/offers.json`。  
预期：测试通过，CLI 输出 `valid: 12 offers`。

---

## 任务 4：将页面迁移为 JSON 驱动

**涉及文件：** `design/free-china-ai-index.html`、`scripts/build_static.py`

- [ ] **步骤 1：编写页面行为测试**

用现有 Playwright 浏览器运行页面：页面显示 12 条 offer，点击 “Browse 4 free IDEs” 显示 4 条，点击 Comate 打开官方动作 URL，搜索 `Qwen3` 只显示 1 条，控制台无错误。

- [ ] **步骤 2：运行并确认当前基线**

运行页面测试脚本，记录当前硬编码版本的行为，确保迁移没有丢失功能。

- [ ] **步骤 3：最小实现**

删除页面中的硬编码 `offers` 对象和手写 offer article，增加 `offer-data` JSON 内嵌块、`renderOffers()`、`loadOffers()` 和 `data/offers.json` 网络加载；file 协议下读取内嵌数据，HTTP 下优先读取 JSON，失败回退内嵌数据。

- [ ] **步骤 4：保持现有交互**

让搜索、筛选、排序、详情抽屉、官方动作按钮、官方链接、复制命令、GLM 时区提示、SEO ItemList 与当前数据源保持一致；IDE 高亮区块的 4 条数量由数据计算。

- [ ] **步骤 5：实现静态构建脚本**

`python scripts/build_static.py` 读取 `data/offers.json`，更新 `offer-data` 块并校验 JSON；不使用 shell 写文件。

- [ ] **步骤 6：运行并确认通过**

运行 Playwright 页面测试和 `python scripts/build_static.py --check`。  
预期：file URL 与本地 HTTP 页面均能渲染，12 条 offer、4 条免费 IDE、直达链接和 SEO 结构化数据都正常。

---

## 任务 5：创建可复用抓取 skill

**涉及文件：** `skills/free-ai-offer-research/SKILL.md`、`README.md`、`references/*.md`

- [ ] **步骤 1：编写 skill 自检**

检查主文件少于 500 行、description 含中英文触发词、工作流有确认门控、references 按需加载、输出模板可直接复制。

- [ ] **步骤 2：最小实现**

主流程包含：收集官方来源、访问边界检查、提取证据、分类免费机制、生成结构化结果、生成 diff、人工确认。明确禁止登录、Key、验证码、代理和绕过限制。

- [ ] **步骤 3：写 references**

把来源策略、数据字段、核验清单和报告模板拆开；每个 reference 只负责一个主题。

- [ ] **步骤 4：运行自检**

运行：`python -m unittest tests.test_skill -v`。  
预期：skill 结构、引用路径、触发词和禁止事项检查通过。

---

## 任务 6：每日任务与总体验收

**涉及文件：** `.github/workflows/daily-check.yml`、`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

验证 workflow 包含每日 cron、Python 版本、依赖零安装策略、schema validate、scan、diff 和 artifact 上传步骤。

- [ ] **步骤 2：最小实现**

创建每日工作流；网络扫描失败时保留失败 artifact 并让 job 失败，不直接修改公开数据。

- [ ] **步骤 3：运行总体验收**

运行：

```text
python -m unittest discover -s tests -v
python scripts/build_static.py --check
python -m crawler.cli validate data/offers.json
```

预期：所有测试通过，数据校验输出 12 条有效记录，页面验证无 console error。

- [ ] **步骤 4：交付说明**

说明本地启动命令、每日任务行为、人工审核方式、file 协议和 HTTP 访问差异，以及正式部署时需要把 `robots.txt`、`llms.txt` 和 canonical 移到站点根目录。
