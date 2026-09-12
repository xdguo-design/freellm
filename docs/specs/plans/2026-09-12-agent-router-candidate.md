# Agent Router 候选与今日扫描实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 注册 Agent Router 的官方与 GitHub 发现入口，生成待审核候选，并完成 2026-09-12 的公开来源扫描与每日变更日志。

**架构要点：** 官方来源注册表负责入口扫描，GitHub peer 只负责发现线索；两者都不能直接发布 `data/offers.json`。扫描产物按日期保存，候选状态固定为 `needs_review`，静态站点只从已核验 Offer 生成。

**技术栈：** Python 标准库、JSON、pytest/unittest、静态 HTML 生成器。

**关联设计文档：** `docs/specs/2026-09-12-agent-router-candidate-design.md`

---

### 任务 1：建立 Agent Router 数据契约测试

**涉及文件：**
- 新建：`tests/test_agent_router_candidate.py`
- 读取：`data/providers.json`
- 读取：`data/github-peers.json`
- 读取：`data/candidates.json`
- 读取：`data/offers.json`

- [x] **步骤 1：编写失败测试**

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def test_agent_router_is_registered_for_bounded_discovery():
    providers = _read("providers.json")
    provider = next(item for item in providers if item["id"] == "agent-router")
    assert provider["allowedDomains"] == ["agentrouter.org"]
    assert "https://agentrouter.org/" in provider["discoveryUrls"]

    peers = _read("github-peers.json")
    peer = next(item for item in peers if item["id"] == "agent-router")
    assert peer["repoUrl"] == "https://github.com/justbiar/agent-router"
    assert peer["enabled"] is True


def test_agent_router_candidate_is_review_only_and_not_a_public_offer():
    candidates = _read("candidates.json")
    candidate = next(item for item in candidates if item.get("providerId") == "agent-router")
    assert candidate["status"] == "needs_review"
    assert candidate["sourceKind"] == "github_peer"
    assert candidate["repository"] == "justbiar/agent-router"
    assert set(["claude-opus-5", "claude-opus-4-8", "gpt-5.6-sol"]).issubset(set(candidate["mentionedModels"]))

    offers = _read("offers.json")
    assert not any(item["id"] == "agent-router-free" for item in offers)
```

- [x] **步骤 2：运行测试确认失败**

运行：`python -m pytest tests/test_agent_router_candidate.py -q`

预期：失败，`StopIteration` 指向尚未注册的 Agent Router provider 或 candidate。

### 任务 2：注册发现入口并加入候选

**涉及文件：**
- 修改：`data/providers.json`
- 修改：`data/github-peers.json`
- 修改：`data/candidates.json`
- 测试：`tests/test_agent_router_candidate.py`

- [x] **步骤 1：最小实现**

在 `data/providers.json` 增加一个对象：

```json
{
  "id": "agent-router",
  "name": "Agent Router",
  "aliases": ["Agent Router", "AgentRouter"],
  "allowedDomains": ["agentrouter.org"],
  "discoveryUrls": ["https://agentrouter.org/", "https://agentrouter.org/register"]
}
```

在 `data/github-peers.json` 增加一个对象：

```json
{
  "id": "agent-router",
  "owner": "justbiar",
  "repo": "agent-router",
  "repoUrl": "https://github.com/justbiar/agent-router",
  "kind": "gateway",
  "discoveryQueries": ["agent router free ai api"],
  "allowedHosts": ["github.com", "api.github.com", "raw.githubusercontent.com"],
  "enabled": true,
  "notes": "Discovery evidence only; verify Agent Router pricing, model availability and terms on the official site."
}
```

Append the bounded GitHub README candidate returned by the scan. Keep `status` as `needs_review`, retain its `repository`, `path`, `commitSha`, `repositoryUrl`, `officialLinks`, and `mentionedModels`, and do not create a matching `data/offers.json` entry.

- [x] **步骤 2：运行测试确认通过**

运行：`python -m pytest tests/test_agent_router_candidate.py -q`

预期：2 passed。

### 任务 3：执行 2026-09-12 扫描与每日日志

**涉及文件：**
- 新建：`data/snapshots/daily-models-20260912.json`
- 新建：`data/snapshots/daily-providers-20260912.json`
- 新建：`data/snapshots/discovery-20260912.json`
- 新建：`data/snapshots/coverage-20260912.json`
- 新建：`data/daily-log/2026-09-12.json`
- 更新：`data/candidates.json`

- [x] **步骤 1：扫描模型目录**

运行：`python scripts/build_model_catalog.py --date 2026-09-12 --models-out data/snapshots/daily-models-20260912.json --providers-out data/snapshots/daily-providers-20260912.json --max-models 1000 --timeout 20`

预期：命令完成或仅报告外部来源失败；模型快照文件存在且为 JSON 数组。

- [x] **步骤 2：扫描已注册官方与 GitHub 来源**

运行：`python -m crawler.cli discover --providers data/providers.json --github-peers data/github-peers.json --out data/candidates.json --scan-out data/snapshots/discovery-20260912.json --max-links 5 --max-pages 100 --github-max-repositories 30 --github-max-files 80 --timeout 8`

预期：候选队列保留 Agent Router 线索；官方 WAF/网络失败只产生来源异常，不升级为已核验 Offer。

- [x] **步骤 3：生成覆盖报告**

运行：`python -m crawler.cli coverage --providers data/providers.json --scan data/snapshots/discovery-20260912.json --candidates data/candidates.json --out data/snapshots/coverage-20260912.json`

预期：覆盖报告记录 Agent Router 官方来源的成功或失败状态，以及 GitHub peer 的扫描统计。

- [x] **步骤 4：生成每日变更日志**

运行：`python -m crawler.cli log --models data/snapshots/daily-models-20260912.json --offers data/offers.json --previous data/daily-log/2026-09-11.json --out data/daily-log/2026-09-12.json --as-of 2026-09-12 --models-status ok --offers-status ok`

预期：日志日期为 `2026-09-12`，不因候选新增而虚构正式 Offer 新增事件。

- [x] **步骤 5：同步稳定模型目录**

运行：`python scripts/sync_model_catalog.py --input data/snapshots/daily-models-20260912.json --output data/models.json --as-of 2026-09-12`

预期：输出 299 条当前/过期合并记录，包含 2 条 `freshnessStatus=new`、288 条 `freshnessStatus=current` 和 9 条 `freshnessStatus=stale`；已有人工核验字段保持不变。

另保存官方资源扫描结果：`data/snapshots/source-scan-20260912.json`（54 个来源，40 个成功，14 个失败）。

### 任务 4：验证静态站点与全量测试

**涉及文件：**
- 检查：`data/offers.json`
- 检查：`data/models.json`
- 检查：`data/candidates.json`
- 检查：`data/daily-log/2026-09-12.json`
- 检查：`design/free-china-ai-index.html`

- [x] **步骤 1：运行验证**

运行：`python -m pytest -q`

结果：`231 passed, 11 skipped`。

运行：`python -m crawler.cli validate data/offers.json`

结果：`valid: 40 offers`。

运行：`python -c "import json; d=json.load(open('data/models.json',encoding='utf-8')); print(len(d), sum(x.get('freshnessStatus') == 'new' for x in d), sum(x.get('freshnessStatus') == 'stale' for x in d))"`

结果：`299 2 9`。

运行：`python scripts/build_static.py --check`

结果：首页构建检查通过。

运行：`python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top --check`

结果：SEO 输出 375 个文件，检查通过。

运行：`git diff --check`

结果：无空白错误。

- [x] **步骤 2：检查变更范围**

运行：`git status --short`

预期：只包含本计划列出的扫描/候选/文档/测试文件，以及用户原有的 `groq-preview-full.png` 和 `groq-preview.png`。
