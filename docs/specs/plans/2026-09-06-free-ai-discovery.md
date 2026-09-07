# 免费 AI 自动发现与防漏数据 实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 将当前固定网址扫描器升级为能够持续发现官方免费额度、试用、促销、夜间优惠和免费 IDE 的候选采集系统，并通过证据门控、来源覆盖率和过期检查避免数据缺少或误发布。

**架构要点：** 供应商注册表定义官方域名、更新日志、价格页和发现入口；发现器只访问白名单内的公开 HTTPS 页面，先生成候选队列，不直接修改公开 offers。公开目录只接受具有官方证据且通过人工审核的候选，单次抓取失败不会标记过期，连续失联和明确截止日期才会进入过期审核。

**技术栈：** Python 3.11 标准库、JSON 数据、GitHub Actions、`python -m unittest discover -s tests -v`。

**关联设计文档：** `docs/specs/2026-09-06-free-ai-index-app-and-crawler-design.md`

---

### 任务 1：供应商注册表与候选数据合同

**涉及文件：**
- 新建：`data/providers.json`
- 新建：`data/candidates.json`
- 新建：`crawler/discovery.py`
- 修改：`crawler/schema.py`
- 测试：`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

测试以下可观察行为：供应商必须有唯一 id、官方 HTTPS 域名和至少一个公开发现 URL；候选必须保留 provider、sourceUrl、发现时间、匹配关键词和 `needs_review` 状态；同一来源重复发现只能产生一个候选。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_discovery -v`

预期：因 `crawler.discovery` 不存在而失败。

- [ ] **步骤 3：最小实现**

实现：

```python
validate_provider_registry(providers) -> list[str]
build_candidates(scan_results, existing=None, now=None) -> list[dict]
merge_candidates(existing, discovered, now=None) -> list[dict]
```

候选状态只能从 `needs_review` 开始；合并时保留 `firstSeenAt`，更新 `lastSeenAt` 和 `seenCount`，以规范化 source URL 去重。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_discovery -v`

预期：全部通过。

### 任务 2：官方来源发现器

**涉及文件：**
- 修改：`crawler/fetch.py`
- 修改：`crawler/discovery.py`
- 修改：`crawler/cli.py`
- 测试：`tests/test_fetch.py`、`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

测试公开 HTML/XML 中的官方链接发现：只保留允许域名、HTTPS、包含免费/试用/额度/价格/夜间等关键词的链接；拒绝外部域名、登录页、带凭据 URL 和重复链接。测试单次来源失败只产生 `source_unavailable`，不产生 `expired`。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_fetch tests.test_discovery -v`

预期：新发现 API 和 XML 链接提取测试失败。

- [ ] **步骤 3：最小实现**

实现 `discover_public_sources(providers, fetcher=fetch_public_page, max_links_per_provider=20)`：

1. 抓取供应商注册表中的公开 discovery URL；
2. 从 sitemap、更新日志和官方活动页提取链接；
3. 用中英文关键词筛选；
4. 对候选页面提取证据摘要；
5. 输出候选，不写入 `data/offers.json`。

增加 CLI：

```text
python -m crawler.cli discover --providers data/providers.json --out data/candidates.json
```

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_fetch tests.test_discovery -v`

预期：全部通过。

### 任务 3：首批供应商覆盖与漏项保护

**涉及文件：**
- 修改：`data/providers.json`
- 修改：`data/sources.json`
- 新建：`data/coverage.json`
- 测试：`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

断言注册表至少覆盖小米 MiMo、腾讯云 TokenHub、百度千帆、阿里云百炼、商汤 SenseCore、火山方舟、智谱、LongCat、Qwen、DeepSeek、MiniMax、Kimi 和免费 AI IDE 入口；断言每个供应商至少有一个价格/免费额度来源和一个发现入口。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_discovery -v`

预期：因供应商注册表尚未存在或覆盖不足而失败。

- [ ] **步骤 3：最小实现**

录入官方域名、官方价格/活动/文档/更新日志入口和别名；生成覆盖报告字段：`providerCount`、`sourceCount`、`lastSuccessfulScanAt`、`failedSources`、`candidateCount`、`staleCandidateCount`。小米的注册赠金、夜间消耗系数、免费额度和 TTS 限免作为独立候选机制，不合并成一条模糊的“免费”。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_discovery -v`

预期：覆盖断言全部通过。

### 任务 4：发布门控与防误报/防缺失规则

**涉及文件：**
- 修改：`crawler/schema.py`
- 修改：`crawler/diff.py`
- 修改：`crawler/cli.py`
- 新建：`data/review-queue.json`
- 测试：`tests/test_diff.py`、`tests/test_schema.py`

- [ ] **步骤 1：编写失败测试**

测试以下规则：

- 候选没有官方证据时不能变成 `verified`；
- 价格、额度、有效期、自动续费或地区字段变化必须进入审核队列；
- 单次抓取失败不能变成 `expired`；
- 连续达到阈值或官方明确截止日期才产生 `possible_expiry`；
- 已人工确认的字段不能被空抓取结果覆盖；
- 过期候选保留在历史队列，不从数据中静默删除。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_schema tests.test_diff -v`

预期：新增门控测试失败。

- [ ] **步骤 3：最小实现**

增加 `publish_candidates()` 和 `classify_source_failure()`，把发现、变更、来源失败、可能过期分别记录为不同事件；公开 `offers.json` 只接受显式人工确认的候选。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_schema tests.test_diff -v`

预期：全部通过。

### 任务 5：Skill 与 GitHub Actions 自动运行

**涉及文件：**
- 修改：`skills/free-ai-offer-research/SKILL.md`
- 修改：`skills/free-ai-offer-research/README.md`
- 修改：`.github/workflows/daily-check.yml`
- 测试：`tests/test_skill.py`

- [ ] **步骤 1：编写失败测试**

断言 skill 文档明确要求运行 provider discovery、保存候选、执行来源覆盖检查、连续失败保护和人工发布门控；workflow 必须执行 `discover` 并上传候选、覆盖报告和扫描快照。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_skill -v`

预期：因文档和 workflow 尚未包含新流程而失败。

- [ ] **步骤 3：最小实现**

更新 skill：自动发现可以每日运行，但不自动把未经核验数据发布到站点；公开数据更新只能来自人工审核后的提交。更新 GitHub Actions：每日扫描供应商、生成 `data/candidates.json` 和 `data/coverage.json`，无论部分来源失败都上传 artifact，并在候选或失败来源增加时标记任务需要关注。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_skill -v`

预期：全部通过。

### 任务 6：全量验证与提交

**涉及文件：** 前述所有变更

- [ ] **步骤 1：运行全部测试**

运行：`python -m unittest discover -s tests -v`

预期：全部通过；默认浏览器不可用时只允许已有的可解释跳过。

- [ ] **步骤 2：校验数据和静态页面**

运行：

```text
python -m crawler.cli validate data/offers.json
python -m crawler.cli discover --providers data/providers.json --out data/candidates.json
python scripts/build_static.py --check
```

预期：offers 合法、discovery 生成候选或明确的来源失败记录、静态页面数据没有过期。

- [ ] **步骤 3：提交**

```text
git add data crawler skills .github docs/specs/plans tests
git commit -m "feat: add provider discovery and anti-missing data gates"
git push origin main
```

