# freellm.net 第三方模型发现 实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 将 freellm.net 的模型级目录安全接入候选发现队列，并纳入每周自动发现 PR。

**架构要点：** 新适配器只解析公开 HTML 和文本，不执行第三方脚本；输出统一的 `needs_review` 候选记录。候选以 freellm.net 详情 URL 去重，官方来源核验仍由人工完成。

**技术栈：** Python 3.10+、stdlib `html.parser`、`unittest`/pytest、GitHub Actions。

**关联设计文档：** `docs/specs/2026-09-08-freellm-net-discovery-design.md`

**执行状态：** 已完成实现、测试、真实目录扫描和质量门禁；生产 `data/offers.json` 未修改。

---

### 任务 1：为模型目录解析器建立 RED 测试

**涉及文件：**
- 新建：`tests/test_freellm_net_discovery.py`
- 新建：`crawler/freellm_net_discovery.py`

- [ ] **步骤 1：编写失败测试**

在测试文件中加入三个行为测试：

```python
def test_parse_model_directory_returns_free_model_metadata():
    rows = parse_model_directory(HTML_FIXTURE, "https://freellm.net/models/")
    assert rows == [{
        "directoryProvider": "Example Provider",
        "directoryProviderSlug": "example-provider",
        "model": "Example Flash",
        "modelId": "example/example-flash",
        "modelSlug": "example-flash",
        "directoryUrl": "https://freellm.net/models/example-provider/example-flash",
        "directoryFree": True,
        "directoryNoCard": True,
        "directoryVerified": True,
        "context": "128K",
        "modality": "text,reasoning",
        "rateLimit": "10 RPM, 100 RPD",
        "status": "Online",
        "tierType": "permanent",
    }]

def test_parse_llms_links_rejects_external_and_sensitive_urls():
    links = parse_llms_links(
        "[Models](https://freellm.net/models/)\n[Bad](https://evil.example/x)\n[Key](https://freellm.net/x?api_key=secret)",
        "https://freellm.net/llms.txt",
    )
    assert links == ["https://freellm.net/models/"]

def test_source_registry_accepts_freellm_net_config():
    assert validate_source_registry([{
        "id": "freellm-net",
        "allowedDomains": ["freellm.net"],
        "urls": ["https://freellm.net/models/", "https://freellm.net/llms.txt"],
        "enabled": True,
    }]) == []
```

使用最小的 `HTML_FIXTURE`，包含一个 `tr.model-row`、模型链接、提供商链接和九个 `td`。

- [ ] **步骤 2：运行 RED 测试**

运行：`python -m pytest tests/test_freellm_net_discovery.py -q`

预期：失败，原因是 `crawler.freellm_net_discovery` 尚不存在。

### 任务 2：实现目录解析与候选扫描

**涉及文件：**
- 修改：`crawler/freellm_net_discovery.py`
- 测试：`tests/test_freellm_net_discovery.py`

- [ ] **步骤 1：最小实现**

实现 `html.parser.HTMLParser` 行解析器，读取 `data-*` 属性和模型/提供商链接；只保留 `data-free="1"` 且有安全详情 URL 的行。实现 `parse_llms_links()` 的 Markdown 链接提取和 `discover_freellm_net_sources()` 的注入式 fetcher。

扫描记录必须包含 `providerId: "freellm-net"`、`sourceKind: "third_party_directory"`、`officiality: "third_party_discovery"`、`status: "needs_review"`、模型元数据和由目录字段拼出的 evidence；失败来源记录使用 `status: "failed"`，不能中断其他来源。

- [ ] **步骤 2：运行 GREEN 测试**

运行：`python -m pytest tests/test_freellm_net_discovery.py -q`

预期：全部通过。

- [ ] **步骤 3：补充边界测试并重构**

增加重复模型、缺失模型链接、非 HTTPS URL、超过模型上限和单来源 fetcher 异常测试；运行同一测试命令，预期全部通过。

### 任务 3：接入数据配置与 CLI

**涉及文件：**
- 新建：`data/third-party-discovery-sources.json`
- 修改：`crawler/cli.py`
- 修改：`crawler/discovery.py`
- 测试：`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试并运行 RED**

增加 CLI 测试，传入 `--third-party-sources` 和注入的扫描函数，确认输出候选包含 `third_party_directory` 字段且不修改 `data/offers.json`。运行：`python -m pytest tests/test_discovery.py -q`；预期在新参数或新模块入口处失败。

- [ ] **步骤 2：最小实现**

新增配置：

```json
[
  {
    "id": "freellm-net",
    "name": "FreeLLM Hub",
    "allowedDomains": ["freellm.net"],
    "urls": ["https://freellm.net/models/", "https://freellm.net/llms.txt"],
    "enabled": true
  }
]
```

在 `discover` 增加 `--third-party-sources` 和 `--third-party-max-models`，使用 `fetch_public_text_resource` 获取内容，再把适配器结果交给现有 `build_candidates()`/`merge_candidates()`。

- [ ] **步骤 3：运行 GREEN 测试**

运行：`python -m pytest tests/test_discovery.py tests/test_freellm_net_discovery.py -q`；预期全部通过。

### 任务 4：接入报告与 GitHub Actions

**涉及文件：**
- 修改：`scripts/build_discovery_report.py`
- 修改：`.github/workflows/discovery-pr.yml`
- 修改：`tests/test_workflow.py`

- [ ] **步骤 1：编写失败测试并运行 RED**

让报告测试要求出现目录提供商、模型和第三方核验提醒；让 workflow 契约测试要求 `data/third-party-discovery-sources.json` 和 `--third-party-sources`。运行：`python -m pytest tests/test_workflow.py tests/test_discovery.py -q`；预期失败。

- [ ] **步骤 2：最小实现**

报告中增加第三方目录候选的模型级信息和“仅作线索、必须核验官方来源”提示；workflow 在已有 GitHub 全局发现后追加第三方来源扫描。保持 workflow 不执行 `git add data/offers.json`。

- [ ] **步骤 3：运行 GREEN 测试**

运行：`python -m pytest tests/test_workflow.py tests/test_discovery.py tests/test_freellm_net_discovery.py -q`；预期全部通过。

### 任务 5：全量质量门禁与提交

**涉及文件：**
- 以上实现文件和测试文件；不修改生产 `data/offers.json`。

- [ ] **步骤 1：运行全量测试**

运行：`python -m pytest -q`；预期所有测试通过，已有浏览器测试可按项目规则跳过。

- [ ] **步骤 2：运行数据与构建检查**

运行：`python -m crawler.cli validate data/offers.json; python scripts/build_static.py --check; python scripts/build_seo_pages.py --check; git diff --check`；预期 schema、静态输出、SEO 输出均为 current，且无 diff 错误。

- [ ] **步骤 3：提交**

```powershell
git add crawler/freellm_net_discovery.py crawler/cli.py crawler/discovery.py scripts/build_discovery_report.py data/third-party-discovery-sources.json .github/workflows/discovery-pr.yml tests/test_freellm_net_discovery.py tests/test_discovery.py tests/test_workflow.py docs/specs/2026-09-08-freellm-net-discovery-design.md docs/specs/plans/2026-09-08-freellm-net-discovery.md
git commit -m "feat: discover models from freellm directory"
```

- [ ] **步骤 4：本地复现一次来源扫描**

运行：`python -m crawler.cli discover --providers data/providers.json --github-peers data/github-peers.json --global-queries data/discovery-queries.json --third-party-sources data/third-party-discovery-sources.json --out data/candidates.json --scan-out data/snapshots/discovery-third-party-scan.json --max-links 5 --max-pages 100 --global-max-repositories 40 --github-max-files 40 --third-party-max-models 305 --timeout 8`。

预期：生成模型级候选扫描记录；不改变 `data/offers.json`。`data/candidates.json` 和扫描快照属于本地发现产物，不在本次生产目录提交中加入。
