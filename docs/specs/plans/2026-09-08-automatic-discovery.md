# 自动发现 AI 免费资源 实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 为 FreeLLM 增加面向未知厂商和新模型的公开发现、候选队列、批量报告和自动 PR 流程。

**架构要点：** 复用现有 GitHub 公共 API 文档扫描器，增加可配置的宽搜索词和未知仓库扫描；所有结果先进入 `needs_review` 候选队列。GitHub Actions 每周生成一个批量 PR，生产目录仍只接受人工核验后的 Offer。

**技术栈：** Python 3.10+、stdlib `unittest`/pytest、GitHub Actions、GitHub CLI。

**关联设计文档：** `docs/specs/2026-09-08-automatic-discovery-design.md`

---

### 任务 1：配置全局发现查询

**涉及文件：**
- 新建：`data/discovery-queries.json`
- 测试：`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

增加测试，读取 `data/discovery-queries.json`，确认包含至少 8 个不同意图的查询，覆盖 free API、OpenAI-compatible、image、video、coding、rate limit 和 model catalog，并确认每项是非空字符串。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_discovery.py::DiscoveryTests::test_global_discovery_queries_cover_unknown_offer_surfaces -v`

预期：因文件不存在而失败。

- [ ] **步骤 3：最小实现**

创建 JSON 数组，使用明确的公开 GitHub 搜索词，例如 `"free AI API"`、`"OpenAI compatible free API"`、`"free image generation API"`、`"free video generation API"`、`"free coding plan AI"`、`"rate limited inference API"`、`"free multimodal API"` 和 `"AI model catalog free"`。

- [ ] **步骤 4：运行测试确认通过**

运行同一 pytest 命令，预期测试通过。

### 任务 2：实现未知 GitHub 仓库发现

**涉及文件：**
- 修改：`crawler/github_discovery.py`
- 修改：`crawler/cli.py`
- 测试：`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

增加注入式 fetcher 测试，给 `discover_global_github_sources()` 一个 GitHub 搜索结果和 README 文档，确认输出的记录包含 `sourceKind == "github_global"`、仓库、路径、commit SHA、查询词、文档证据，并且不要求该仓库预先存在于 provider registry。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_discovery.py::DiscoveryTests::test_global_github_discovery_scans_unknown_repository_docs -v`

预期：因函数不存在而失败。

- [ ] **步骤 3：最小实现**

在 `crawler/github_discovery.py` 增加 `discover_global_github_sources(queries, fetch_json, fetch_document, max_repositories=20, max_files=40)`：调用现有 `discover_github_repositories()`，为每个结果构造临时 peer，复用 `scan_github_peer()`，并给记录补充 `github_global`、查询词、仓库描述和 stars。为仓库搜索结果保留 `query` 字段，按 full name 去重。

在 `crawler/cli.py discover` 增加 `--global-queries` 和 `--global-max-repositories`，读取查询文件后合并全局扫描结果；现有 provider 和 GitHub peer 参数保持兼容。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m pytest tests/test_discovery.py::DiscoveryTests::test_global_github_discovery_scans_unknown_repository_docs -v`

预期：测试通过，且结果状态为 `needs_review`。

### 任务 3：加强候选去重和报告

**涉及文件：**
- 修改：`crawler/discovery.py`
- 新建：`scripts/build_discovery_report.py`
- 修改：`crawler/cli.py`
- 测试：`tests/test_discovery.py`

- [ ] **步骤 1：编写失败测试**

增加测试，输入同一未知仓库的两个查询结果，确认候选队列只保留一条、合并查询词和证据、增加 `seenCount`。增加报告测试，确认 Markdown 包含候选总数、来源仓库、文档路径、提及模型和 `needs_review` 提示。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_discovery.py::DiscoveryTests::test_global_candidates_merge_and_report -v`

预期：因报告入口不存在或缺少全局字段而失败。

- [ ] **步骤 3：最小实现**

让 `build_candidates()` 复制 `query`、仓库描述、stars 和 `sourceKind` 等字段，继续以 `(providerId, canonical sourceUrl)` 去重；全局结果使用稳定的 `github-global` provider ID，并以仓库/路径作为来源区分。新增报告脚本参数 `--candidates`、`--out`，输出安全、可读的候选清单，不渲染可执行内容。

在 CLI 增加 `report` 子命令，调用报告脚本使用的纯函数，便于 workflow 与本地复现。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m pytest tests/test_discovery.py::DiscoveryTests::test_global_candidates_merge_and_report -v`

预期：测试通过。

### 任务 4：接入批量候选 PR workflow

**涉及文件：**
- 新建：`.github/workflows/discovery-pr.yml`
- 修改：`tests/test_e2e_static.py` 或新增 `tests/test_workflow.py`

- [ ] **步骤 1：编写失败测试**

增加静态 workflow 测试，确认 workflow 使用 `schedule` 和 `workflow_dispatch`，权限包含 `contents: write` 与 `pull-requests: write`，执行全局查询、生成候选和报告，并且只在有变更时创建 PR。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_workflow.py -v`

预期：因 workflow 文件不存在而失败。

- [ ] **步骤 3：最小实现**

创建每周 workflow：checkout、setup Python、运行 schema/test、执行 `crawler.cli discover --global-queries data/discovery-queries.json`、执行 coverage/report、配置 bot git 身份，将 `data/candidates.json` 和 `docs/discovery-latest.md` 提交到唯一分支，并使用 `gh pr create` 创建批量候选 PR。生产 `data/offers.json` 不由该 workflow 修改。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m pytest tests/test_workflow.py -v`。

预期：workflow 静态契约测试通过。

### 任务 5：全量质量门禁和发布

**涉及文件：**
- 修改：由生成器产生的 `data/candidates.json` 或报告文件仅在本地验证时检查，不直接加入生产 Offer。

- [ ] **步骤 1：运行全量测试**

运行：`python -m pytest -q`。

预期：所有测试通过，允许已有的浏览器测试跳过。

- [ ] **步骤 2：运行数据与构建检查**

运行：`python -m crawler.cli validate data/offers.json; python scripts/build_static.py --check; python scripts/build_seo_pages.py --check; git diff --check`。

预期：schema valid、静态输出 current、SEO 输出 current、无 diff 错误。

- [ ] **步骤 3：提交**

```powershell
git add data/discovery-queries.json crawler/github_discovery.py crawler/discovery.py crawler/cli.py scripts/build_discovery_report.py .github/workflows/discovery-pr.yml tests/test_discovery.py tests/test_workflow.py docs/specs/2026-09-08-automatic-discovery-design.md docs/specs/plans/2026-09-08-automatic-discovery.md
git commit -m "feat: add automated AI offer discovery pipeline"
```

- [ ] **步骤 4：推送并验证**

运行：`git push origin dev`，随后手动触发 `discovery-pr.yml`，确认 workflow 生成候选报告；只有核验后的条目才通过普通代码变更进入 `offers.json`。
