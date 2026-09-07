# Web AI 基础设施目录与使用说明实施计划

> **给代理执行者：** 推荐在当前 `codex/github-peer-discovery-console-style` 分支上按任务逐步执行；保留工作区已有未提交修改。任务使用 `- [ ]` 勾选跟踪。

**目标：** 将 Search、Fetch、Extract、Crawl、Map、Browser、Agent 基础设施和完整“如何使用”说明纳入现有 Free AI Index，并保持现有模型、IDE、Coding Plan、开放权重和 PAYG 条目兼容。

**非目标（Out of Scope）：**

- 不代替用户注册、登录、创建 API Key、充值或调用真实额度。
- 不在本站代理第三方请求，不执行真实 Browser/Agent 任务。
- 不绕过验证码、地区限制、robots 或访问控制。
- 不把第三方文章或 GitHub README 直接发布为官方额度事实。
- 不在本批次增加排序评分、质量基准或跨供应商性能评测。

**架构要点：** Provider、Product、Offer 三层关系保持统一；Offer 用 `capabilities` 表示能力，用 `pricingModel`、`freePolicy`、`limits`、`billing` 表示商业规则，用 `usageGuide` 表示可执行用法。同一 Product 的不同免费/付费规则拆为不同 Offer；页面总数按 Offer 去重，能力组按标签计数。发现器只写候选和快照，正式 `data/offers.json` 仍需官方来源和人工审核。

**技术栈/运行方式：** Python 3.11 标准库、静态 HTML/CSS/JavaScript；测试使用 `python -m unittest discover -s tests -v`；构建检查使用 `python scripts/build_static.py --check`；浏览器验收使用仓库已有 Playwright 测试，未安装浏览器时允许按现有规则跳过。

**关联设计文档：** `docs/specs/2026-09-07-web-infrastructure-directory-design.md`

---

## 文件变更清单

- 修改：
  - `crawler/schema.py`：增加 Web Infrastructure 枚举、嵌套规则和 `usageGuide` 校验。
  - `crawler/diff.py`：比较结构化限制、计费和使用说明关键字段。
  - `crawler/discovery.py`：增加 Web 能力、限频、钱包和快速开始关键词；保留候选审核门控。
  - `crawler/cli.py`：保持 validate、discover、coverage、diff 流程兼容新字段。
  - `data/providers.json`：增加首批 8 个 Web 基础设施 Provider 和官方发现入口。
  - `data/sources.json`：增加首批 Offer 的官方价格、文档和快速开始来源。
  - `data/offers.json`：迁移现有 18 条 Offer，并加入首批 Web 基础设施 Offer 与 `usageGuide`。
  - `skills/free-ai-offer-research/references/offer-schema.md`：同步字段、能力、计费和使用说明规则。
  - `skills/free-ai-offer-research/SKILL.md`：同步检索顺序、使用说明和发布门控。
  - `design/free-china-ai-index.html`：增加能力分组、计费筛选、使用说明详情和可复制示例。
- 测试：
  - `tests/test_schema.py`：覆盖新字段、枚举、限制、计费和使用说明矩阵。
  - `tests/test_discovery.py`：覆盖新关键词和候选字段保留。
  - `tests/test_diff.py`：覆盖嵌套限制与使用说明变化。
  - `tests/test_e2e_static.py`：覆盖七个能力组、计数去重、详情用法区块和示例复制。
  - `tests/test_skill.py`：覆盖 skill 文档中的新能力和使用说明门控。

## 任务 1：扩展 Offer Schema 和使用说明校验

**涉及文件：**

- 修改：`crawler/schema.py`
- 测试：`tests/test_schema.py`

- [ ] **步骤 1：编写失败测试**

在 `tests/test_schema.py` 增加以下断言，使用现有合法 Offer 复制后覆盖新字段：

```python
def test_web_offer_requires_capabilities_limits_billing_and_usage_guide(self):
    offer = valid_offer()
    offer.update({
        "providerId": "tinyfish",
        "productId": "tinyfish-web",
        "offerVariant": "search-fetch-free",
        "productType": "web_infrastructure",
        "capabilities": ["search", "fetch"],
        "pricingModel": "free_rate_limited",
        "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
        "limits": {"requestsPerMinute": 30, "urlsPerMinute": 150},
        "billing": {
            "walletRequired": False,
            "cardRequired": "no",
            "autoReload": "unknown",
            "overageBehavior": "stop_or_metered",
            "prices": [],
        },
        "usageGuide": {
            "summary": "搜索和抓取网页",
            "prerequisites": ["注册账号"],
            "steps": ["创建访问凭据", "发送请求"],
            "endpoint": "https://api.tinyfish.io/search",
            "method": "POST",
            "authentication": "Authorization: Bearer ${API_KEY}",
            "examples": {"curl": "curl --request POST https://api.tinyfish.io/search"},
            "docsUrl": "https://future.tinyfish.io/pricing",
        },
    })
    self.assertEqual(validate_offer(offer), [])

def test_usage_guide_rejects_ellipsis_and_missing_capability_fields(self):
    offer = valid_web_offer()
    offer["usageGuide"]["examples"] = {"curl": "curl ..."}
    errors = validate_offer(offer)
    self.assertIn("usageGuide examples must be executable", errors)

def test_paid_web_offer_requires_unit_price(self):
    offer = valid_web_offer()
    offer["pricingModel"] = "payg"
    offer["billing"]["prices"] = []
    self.assertIn("billing.prices must contain a unit price", validate_offer(offer))
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_schema -v`

预期：新测试失败，提示 `web_infrastructure`、`capabilities`、`usageGuide` 或计费校验尚未实现。

- [ ] **步骤 3：最小实现**

在 `crawler/schema.py`：

1. 将 `web_infrastructure` 加入 `PRODUCT_TYPES`。
2. 增加固定能力枚举：`search`、`fetch`、`extract`、`crawl`、`map`、`browser`、`agent`、`model_api`、`free_ide`、`open_weights`。
3. 增加 `pricingModel` 和 `overageBehavior` 枚举。
4. 校验 `providerId + productId + offerVariant` 为非空字符串，`capabilities` 为非空且无未知值。
5. 校验 `freePolicy`、`limits`、`billing` 的类型、空值和单位关系。
6. 新增 `_validate_usage_guide()`，执行公共规则和能力矩阵：API 能力要求 HTTPS `endpoint`、HTTP `method`、鉴权和至少一个 `curl`/Python/JavaScript 示例；IDE/开放权重要求安装或下载动作；示例代码拒绝 `...`、`TODO` 和疑似真实密钥。
7. 保留旧 Offer 的字段兼容；迁移完成前允许旧数据通过基础校验，但发布门控对所有正式 Offer 要求完整 `usageGuide`。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_schema -v`

预期：Schema 新增测试与现有测试全部通过。

- [ ] **步骤 5：提交检查**

运行：`git diff -- crawler/schema.py tests/test_schema.py`；确认只涉及 Schema 和测试，不覆盖工作区其他修改。

## 任务 2：扩展 Diff、发现关键词和候选字段

**涉及文件：**

- 修改：`crawler/diff.py`、`crawler/discovery.py`
- 测试：`tests/test_diff.py`、`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

增加以下行为测试：

```python
def test_compare_offers_detects_nested_limits_and_usage_guide_changes(self):
    previous = [web_offer(limits={"requestsPerMinute": 30})]
    current = [web_offer(limits={"requestsPerMinute": 20})]
    changes = compare_offers(previous, current)
    self.assertEqual(changes[0]["changeType"], "changed")
    self.assertIn("limits", changes[0]["fields"])

def test_web_keywords_find_rate_limit_and_quickstart_pages(self):
    text = "Search API quickstart, 30 RPM, wallet, auto reload, fetch URL"
    self.assertIn("quickstart", matched_keywords(text))
    self.assertIn("rate_limit", matched_keywords(text))
    self.assertIn("wallet", matched_keywords(text))
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_diff tests.test_discovery -v`

预期：嵌套字段变化未被记录，新增关键词匹配失败。

- [ ] **步骤 3：最小实现**

在 `crawler/diff.py` 将 `limits`、`billing`、`freePolicy`、`pricingModel`、`capabilities`、`usageGuide` 纳入关键字段比较；保持 `before`/`after` 原样保存，不执行跨单位换算。

在 `crawler/discovery.py` 增加能力和使用关键词，并让候选保留 `matchedKeywords`、`sourceUrl`、`evidence`、`status=needs_review`。发现器不得从候选直接写入 `data/offers.json`。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_diff tests.test_discovery -v`

预期：新增和原有发现/Diff 测试全部通过，来源失败仍为 `source_unavailable`。

## 任务 3：登记首批 Provider 和官方来源

**涉及文件：**

- 修改：`data/providers.json`、`data/sources.json`
- 测试：`tests/test_discovery.py`、`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

增加注册表覆盖断言：

```python
def test_web_infrastructure_mvp_providers_are_registered(self):
    providers = json.loads(Path("data/providers.json").read_text(encoding="utf-8"))
    ids = {item["id"] for item in providers}
    self.assertTrue({
        "keenable", "tinyfish", "tavily", "exa",
        "you-com", "firecrawl", "brave-search", "browserbase",
    } <= ids)
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_discovery -v`

预期：当前 Provider 注册表缺少上述 Web 基础设施 ID，断言失败。

- [ ] **步骤 3：最小实现**

在 `data/providers.json` 增加 8 个 Provider，每项包含 `id`、`name`、`aliases`、`allowedDomains` 和至少一个官方 `discoveryUrls`。使用以下官方入口作为来源起点：

- Keenable：`https://keenable.ai/pricing`、`https://docs.keenable.ai/cli`
- TinyFish：`https://future.tinyfish.io/pricing`
- Tavily：`https://www.tavily.com/pricing`、`https://docs.tavily.com/documentation/api-credits`
- Exa：`https://exa.ai/pricing`
- You.com：`https://about.you.com/pricing`、`https://you.com/docs/quickstart`
- Firecrawl：`https://www.firecrawl.dev/pricing`
- Brave Search：`https://brave.com/search/api/`
- Browserbase：`https://www.browserbase.com/pricing`

在 `data/sources.json` 为每个已核验 Offer 添加价格页和快速开始/文档页，并通过现有白名单校验。Keenable 的免绑卡、免费 10 万次、Search/Fetch 入口和超额价格以官方价格页与官方文档共同核验；没有核验完的记录保持 `needs_review`。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_discovery tests.test_e2e_static -v`

预期：8 个 Provider 均有合法 HTTPS 官方来源，注册表校验通过；现有 Provider 不减少。

## 任务 4：迁移 Offer 数据并补齐“如何使用”

**涉及文件：**

- 修改：`data/offers.json`
- 修改：`skills/free-ai-offer-research/references/offer-schema.md`、`skills/free-ai-offer-research/SKILL.md`
- 测试：`tests/test_schema.py`、`tests/test_skill.py`

- [ ] **步骤 1：编写失败测试**

增加数据级验收：

```python
def test_every_public_offer_has_usage_guide_and_capabilities(self):
    offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
    for offer in offers:
        self.assertIn("usageGuide", offer)
        self.assertTrue(offer["usageGuide"]["steps"])
        self.assertTrue(offer.get("capabilities"))

def test_mvp_web_offers_have_independent_variants(self):
    offers = json.loads(Path("data/offers.json").read_text(encoding="utf-8"))
    web = [item for item in offers if item.get("productType") == "web_infrastructure"]
    keys = {(item["providerId"], item["productId"], item["offerVariant"]) for item in web}
    self.assertEqual(len(keys), len(web))
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_schema tests.test_skill -v`

预期：现有 18 条 Offer 尚无统一 `usageGuide` 和 `capabilities`，新断言失败。

- [ ] **步骤 3：最小实现**

迁移现有 18 条 Offer 时不删除、不改 `id`：

- `free_ide` → `capabilities: ["free_ide"]`，补下载、登录、启用套餐和额度查看步骤。
- `api`/`payg` → `capabilities: ["model_api"]`，补 Base URL、模型 ID、鉴权和最小请求示例。
- `coding_plan` → `capabilities: ["free_ide"]` 或 `model_api`，以官方使用入口为准，并明确首月/续费规则。
- `open_weights` → `capabilities: ["open_weights"]`，补下载、许可证、硬件要求和本地启动命令。

为首批 8 个 Web 产品建立稳定 `providerId`、`productId` 和 `offerVariant`。对免费与付费能力规则不同的产品拆 Offer，例如 TinyFish 至少包含 `search-fetch-free` 和 `agent-browser-metered` 两个变体。每个正式 Offer 补齐：

1. `capabilities`、`pricingModel`、`freePolicy`、`limits`、`billing`。
2. `usageGuide.summary`、`prerequisites`、`steps`、官方 `docsUrl`。
3. 对 HTTP 能力补 `endpoint`、`method`、鉴权、参数说明和可复制 `curl`/Python/JavaScript 示例。
4. 对 Browser/Agent 补会话/任务生命周期、并发、时长、计费和停止方式。
5. 对无法从官方来源确认的字段使用 `unknown`/`null` 并将状态设为 `needs_review`。

同步更新 skill 规则：所有条目必须回答“是什么、为什么免费/便宜、如何开通、如何使用、如何避免超额、官方证据是什么”；官方来源失败不能标记过期。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_schema tests.test_skill -v`

预期：所有公开 Offer 有使用说明和能力标签；文档测试确认能力分组、使用说明门控和官方来源规则存在。

## 任务 5：改造静态页面分组与使用说明详情

**涉及文件：**

- 修改：`design/free-china-ai-index.html`
- 测试：`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

增加浏览器验收：

```python
def test_web_groups_and_usage_guide_are_rendered(self):
    page = self.new_page()
    page.goto(HTML_PATH.as_uri())
    page.wait_for_function("document.body.dataset.dataSource === 'embedded'")
    for name in ("search", "fetch", "extract", "crawl", "map", "browser", "agent"):
        self.assertGreaterEqual(page.locator(f"[data-filter='{name}']").count(), 1)
    page.click(".offer[data-detail='tinyfish-search-fetch-free'] .row-arrow")
    page.wait_for_selector("#drawer.open")
    self.assertNotEqual(page.locator("#drawerUsageGuide").inner_text(), "")
    self.assertNotEqual(page.locator("#drawerExample").inner_text(), "")
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_e2e_static.BrowserPageTests.test_web_groups_and_usage_guide_are_rendered -v`

预期：当前页面没有七个能力筛选器、使用说明容器和 Web Offer，测试失败。

- [ ] **步骤 3：最小实现**

在 HTML：

1. 保留现有 Offer 表结构，增加能力徽章和计费模型徽章。
2. 动态从 `capabilities` 生成 Search、Fetch、Extract、Crawl、Map、Browser、Agent 七个分组和数量。
3. 总数按 Offer 去重，分组按能力标签计数；搜索文本包含 provider、product、model、capabilities、endpoint 和 `usageGuide`。
4. 在详情抽屉增加 `#drawerUsageGuide`、`#drawerPrerequisites`、`#drawerSteps`、`#drawerEndpoint`、`#drawerExample`、`#drawerQuotaGuard`、`#drawerCommonIssues`。
5. 示例按 `curl`、Python、JavaScript、shell/action 渲染可用语言按钮，并使用现有安全转义和复制逻辑。
6. 对 `needs_review` 显示状态，不把未核验的免费规则渲染成强推荐。
7. 更新静态 fallback、JSON-LD 和现有数量文案，避免继续硬编码 18、08、03 等旧计数。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_e2e_static -v`

预期：文件协议、HTTP 网络 JSON、fallback、搜索、详情抽屉和数据缺失错误路径全部通过；Playwright 不可用时按现有测试规则跳过浏览器用例。

## 任务 6：更新日常扫描与覆盖报告

**涉及文件：**

- 修改：`crawler/cli.py`、`.github/workflows/daily-check.yml`
- 测试：`tests/test_e2e_static.py`、`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

增加命令级断言，确认日常流程仍按顺序执行：`validate`、`scan`、`discover`、`coverage`、`snapshot`、`diff`；并确认覆盖报告包含 Web Provider。

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_e2e_static.DailyWorkflowTests -v`

预期：现有流程断言可以通过；新增 Web 覆盖断言在 Provider 数据和报告字段完成前失败。

- [ ] **步骤 3：最小实现**

保持现有命令参数兼容；只在需要时让 coverage 输出 `capabilityCounts`、`webInfrastructureProviderCount` 和 `usageGuideReviewCount`。扫描失败继续写 `source_unavailable`，不覆盖现有 Offer，不自动发布候选。

在 workflow 中继续使用 `if: always()` 上传扫描快照、候选、覆盖报告和审核队列；不增加 `git push` 或 `git commit`。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_e2e_static.DailyWorkflowTests tests.test_discovery -v`

预期：日常工作流包含新 Provider 扫描、候选审核、覆盖报告和失败隔离，且不具备自动发布权限。

## 任务 7：全量验证与质量门控

**涉及文件：**

- 验证：全部上述修改文件
- 输出：`data/coverage.json`、`data/review-queue.json`、`data/snapshots/`

- [ ] **步骤 1：运行全量单元测试**

运行：`python -m unittest discover -s tests -v`

预期：所有测试通过；无新增未处理异常。

- [ ] **步骤 2：验证 Offer 数据和静态构建**

运行：`python -m crawler.cli validate data/offers.json`；`python scripts/build_static.py --check`

预期：Offer 校验无错误；HTML 内嵌 JSON 与 `data/offers.json` 一致。

- [ ] **步骤 3：执行公开来源扫描**

运行：`python -m crawler.cli discover --providers data/providers.json --out data/candidates.json --scan-out data/snapshots/discovery-scan.json --max-links 5 --max-pages 100 --timeout 8`

预期：8 个 MVP Provider 均出现在覆盖结果；失败来源以 `source_unavailable` 记录；候选状态均为 `needs_review`，没有自动写入正式 Offer。

- [ ] **步骤 4：核对页面验收**

运行：`python -m unittest tests.test_e2e_static.BrowserPageTests -v`

预期：能力分组、Offer 去重、使用说明、代码示例、复制按钮、搜索和详情抽屉通过；缺少 Playwright 时输出现有 skip 原因。

- [ ] **步骤 5：最终差异审查**

运行：`git status --short`；`git diff --stat`；`rg -n "TODO|TBD|适当|类似|等等|curl \.\.\." crawler data design skills tests docs/specs/plans`

预期：工作区只包含本任务和原有用户修改；不出现未解决占位符、不可执行示例或真实凭据。

## 质量门控

- [ ] Provider、Product、Offer 层级和 Offer 唯一键保持稳定。
- [ ] Search、Fetch、Extract、Crawl、Map、Browser、Agent 七个能力组均可筛选和计数。
- [ ] 所有正式 Offer 都有可执行的“如何使用”说明；缺失项只能是 `needs_review`。
- [ ] 免费额度、限频、并发、钱包、自动充值、超额价格和耗尽策略不混为一个字段。
- [ ] 官方来源是最终证据；社区/GitHub 只产生候选。
- [ ] 失败来源不导致 Offer 自动过期或删除。
- [ ] 不读取、保存或输出 API Key、钱包凭据和用户账户数据。
- [ ] 现有 18 条 Offer 的 `id`、兼容加载路径和既有页面行为不回归。
- [ ] 日常 workflow 不自动提交或推送公开数据。

