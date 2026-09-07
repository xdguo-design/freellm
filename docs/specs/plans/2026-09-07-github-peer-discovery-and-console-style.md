# GitHub 同类项目扫描与 Console 风格改版实施计划

> **给代理执行者：** 任务使用 `- [ ]` 勾选跟踪；每步写清路径、命令、预期输出和验收标准。执行前应在独立 `codex/` 分支进行，并保留当前工作树中的用户修改。

**目标：** 在现有官方来源扫描基础上增加 GitHub 同类项目发现层，并将目录页面升级为自有的 Console + Editorial 视觉系统。

**非目标：** 不把第三方仓库的宣传文案、截图、Logo 或免费结论直接发布；不执行仓库代码；不把项目改造成 LLM Gateway；不在本计划内提交 AdSense 申请或部署到错误的 Vercel 地址。

**架构要点：** GitHub 扫描是发现层，官方来源扫描仍是发布证据层。仓库文档通过公开 GitHub API/raw 内容读取，经过文件、字节、请求和域名限制后生成带 commit/path provenance 的 `needs_review` 候选。页面继续由 `data/offers.json` 驱动，视觉改版先产出三个真实 HTML 初稿，用户选择后才改生产页面。

**技术栈/运行方式：** Python 3 标准库、静态 HTML/CSS/JavaScript、`unittest`、Playwright（已有端到端测试使用）。验证命令为 `python -m unittest discover -s tests -v` 和 `python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-09-07-github-peer-discovery-and-console-style-design.md`

---

## 文件变更清单

### 新建

- `data/github-peers.json`：GitHub 同类项目种子和发现关键词。
- `crawler/github_discovery.py`：GitHub 仓库发现、文档筛选、文本提取和 provenance 生成。
- `tests/test_github_discovery.py`：GitHub 注册表、抓取限制、提取、去重和安全门控测试。
- `design-demos/dark-console.html`：深色 Console 视觉初稿。
- `design-demos/console-editorial.html`：Console + Editorial 视觉初稿。
- `design-demos/docs-directory.html`：Docs Directory 视觉初稿。

### 修改

- `crawler/fetch.py`：增加允许文本/JSON/raw 文档读取的公共资源抓取能力，保持现有 HTML 抓取接口不变。
- `crawler/discovery.py`：合并 GitHub 候选的 provenance、来源等级和去重逻辑。
- `crawler/cli.py`：给 `discover` 增加可选 GitHub peer 输入，并保留旧命令行为。
- `data/providers.json`：继续维护官方 Provider，不把第三方 peer 仓库混入官方 Provider 注册表。
- `data/candidates.json`：运行扫描后追加 GitHub 候选，状态保持 `needs_review`。
- `data/coverage.json`：增加 peer 仓库统计、文档文件统计和失败分类。
- `skills/free-ai-offer-research/SKILL.md`：写入 GitHub 发现层、证据等级、安全边界和运行命令。
- `skills/free-ai-offer-research/README.md`：增加 GitHub 同类项目扫描示例。
- `skills/free-ai-offer-research/references/source-policy.md`：补充 GitHub API/raw 文档的允许范围和 provenance 要求。
- `tests/test_discovery.py`：覆盖官方候选与 GitHub 候选合并后的兼容行为。
- `tests/test_skill.py`：验证技能包含 GitHub 扫描和安全门控要求。
- `design/brand-spec.md`：用户选定视觉方向后写入最终 Console + Editorial tokens。
- `design/direction-approved.md`：记录三个初稿路径和用户选择原话。
- `design/free-china-ai-index.html`：用户选定方向后实施生产页面改版。
- `tests/test_e2e_static.py`：增加筛选、详情、复制命令和视觉入口的验收。

---

## 任务 1：建立 GitHub peer 注册表与验证契约

**涉及文件：**

- 新建：`data/github-peers.json`
- 新建：`crawler/github_discovery.py`
- 新建：`tests/test_github_discovery.py`

- [ ] **步骤 1：编写失败测试**

在 `tests/test_github_discovery.py` 中加入：

```python
import json
import unittest
from pathlib import Path

from crawler.github_discovery import validate_peer_registry


class GitHubRegistryTests(unittest.TestCase):
    def test_seed_registry_contains_devansh_freellm(self):
        peers = json.loads(Path("data/github-peers.json").read_text(encoding="utf-8"))
        self.assertTrue(any(
            peer["owner"] == "Devansh-365" and peer["repo"] == "freellm"
            for peer in peers
        ))
        self.assertEqual(validate_peer_registry(peers), [])

    def test_registry_rejects_non_github_hosts_and_duplicate_ids(self):
        errors = validate_peer_registry([
            {
                "id": "peer-a",
                "owner": "owner",
                "repo": "repo",
                "repoUrl": "https://evil.example/repo",
                "kind": "gateway",
                "discoveryQueries": ["free llm gateway"],
                "allowedHosts": ["github.com"],
                "enabled": True,
            },
            {
                "id": "peer-a",
                "owner": "owner",
                "repo": "repo-two",
                "repoUrl": "https://github.com/owner/repo-two",
                "kind": "gateway",
                "discoveryQueries": ["llm router"],
                "allowedHosts": ["github.com"],
                "enabled": True,
            },
        ])
        self.assertIn("duplicate peer id: peer-a", errors)
        self.assertTrue(any("github.com" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_github_discovery.GitHubRegistryTests -v`

预期：因 `crawler.github_discovery` 和 `data/github-peers.json` 尚不存在而失败。

- [ ] **步骤 3：最小实现**

创建 `data/github-peers.json`，至少包含 `Devansh-365/freellm` 以及 3 个同类项目族的空之外的关键词配置。每条记录使用以下结构：

```json
{
  "id": "devansh-freellm",
  "owner": "Devansh-365",
  "repo": "freellm",
  "repoUrl": "https://github.com/Devansh-365/freellm",
  "kind": "gateway",
  "discoveryQueries": ["free llm gateway", "openai compatible free models"],
  "allowedHosts": ["github.com", "api.github.com", "raw.githubusercontent.com"],
  "enabled": true,
  "notes": "Peer discovery only; provider quotas require official verification."
}
```

在 `crawler/github_discovery.py` 定义：

```python
DEFAULT_GITHUB_HOSTS = {"github.com", "api.github.com", "raw.githubusercontent.com"}
PEER_KINDS = {"gateway", "directory", "coding_agent", "ide", "model_catalog", "other"}


def validate_peer_registry(peers: object) -> list[str]:
    """Validate public GitHub peer configuration without network access."""
```

验证唯一 `id`、非空 owner/repo、HTTPS `repoUrl`、GitHub host、合法 kind、非空查询词和允许主机集合。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_github_discovery.GitHubRegistryTests -v`

预期：2 个测试通过。

- [ ] **步骤 5：检查现有测试**

运行：`python -m unittest discover -s tests -v`

预期：现有测试和新增注册表测试全部通过；`data/providers.json` 的官方 Provider 校验结果不变。

---

## 任务 2：实现安全的 GitHub 文档抓取

**涉及文件：**

- 修改：`crawler/fetch.py`
- 修改：`crawler/github_discovery.py`
- 测试：`tests/test_github_discovery.py`

- [ ] **步骤 1：编写失败测试**

覆盖以下行为：只接受三个 GitHub 主机；拒绝 HTTP、凭据 URL、控制字符；接受 Markdown、纯文本和 JSON；响应超过 `max_bytes` 时返回 `source_limit`；fetcher 抛出异常时只返回 `source_unavailable`。

测试契约：

```python
from crawler.github_discovery import fetch_github_document


def test_fetch_github_document_accepts_text_and_enforces_limit():
    result = fetch_github_document(
        "https://raw.githubusercontent.com/owner/repo/main/README.md",
        fetcher=lambda url, max_bytes: {
            "url": url,
            "status": "ok",
            "contentType": "text/markdown",
            "content": "# Free models\nProvider docs",
            "bytes": 31,
        },
        max_bytes=1024,
    )
    assert result["status"] == "ok"
    assert result["contentType"] == "text/markdown"
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_github_discovery -v`

预期：抓取函数不存在或返回结构不满足断言。

- [ ] **步骤 3：最小实现**

在 `crawler/fetch.py` 增加 `fetch_public_text_resource(url, allowed_hosts, timeout=8, max_bytes=200_000)`，复用已有 HTTPS、host、凭据和响应大小边界；允许 `text/*`、`application/json`、`application/xml`，拒绝二进制和 HTML 之外的可执行内容。

在 `crawler/github_discovery.py` 增加 `fetch_github_document()`，先验证 URL host，再调用资源抓取器。返回字段固定为：`url`、`status`、`contentType`、`content`、`bytes`、`checkedAt`、`reason`。

实现禁止执行内容：不调用 subprocess，不解析或导入仓库代码，不安装依赖，不读取本机环境变量。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_github_discovery -v`

预期：抓取格式、域名、大小限制和失败隔离测试全部通过。

- [ ] **步骤 5：回归验证**

运行：`python -m unittest tests.test_fetch tests.test_github_discovery -v`

预期：原有 HTML fetch 测试保持通过，新增文本资源测试通过。

---

## 任务 3：扫描仓库文档并提取线索

**涉及文件：**

- 修改：`crawler/github_discovery.py`
- 测试：`tests/test_github_discovery.py`

- [ ] **步骤 1：编写失败测试**

使用固定 Markdown/JSON fixture，验证读取 README、`docs/`、CHANGELOG、Provider/Model 配置和 `.env.example`；忽略 Shell、Python、JavaScript 可执行文件；抽取官方链接、Provider 名称、Model ID、免费/额度/价格关键词和短证据。

测试契约：

```python
from crawler.github_discovery import extract_peer_document_evidence


def test_extract_peer_document_evidence_keeps_provenance_and_peer_level():
    result = extract_peer_document_evidence(
        repository="Devansh-365/freellm",
        path="README.md",
        commit_sha="abc123",
        content=(
            "Gemini and Groq free tiers.\n"
            "See https://ai.google.dev/gemini-api/docs for official docs.\n"
            "Use model free-fast."
        ),
    )
    assert result["sourceKind"] == "github_peer"
    assert result["officiality"] == "peer_discovery"
    assert result["repository"] == "Devansh-365/freellm"
    assert result["path"] == "README.md"
    assert result["commitSha"] == "abc123"
    assert "ai.google.dev" in result["officialLinks"][0]
    assert "free-fast" in result["mentionedModels"]
```

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_github_discovery -v`

预期：提取函数不存在或 provenance/来源等级断言失败。

- [ ] **步骤 3：最小实现**

在 `crawler/github_discovery.py` 定义：

```python
DOCUMENT_PATH_PATTERNS = (
    "README",
    "docs/",
    "CHANGELOG",
    "RELEASE",
    "providers/",
    "models/",
    "catalog/",
    "package.json",
    "pyproject.toml",
    "docker-compose.yml",
    ".env.example",
)


def select_document_paths(paths: list[str], max_files: int = 80) -> list[str]:
    """Return deterministic, non-executable documentation paths."""


def extract_peer_document_evidence(
    repository: str,
    path: str,
    commit_sha: str,
    content: str,
) -> dict:
    """Extract bounded discovery clues with repository/path/commit provenance."""
```

对 Markdown 链接做 HTTPS 和 host 校验；只把 `github.com`、`api.github.com`、`raw.githubusercontent.com` 以及明确的官方 Provider 域名候选写入 `officialLinks`。疑似密钥、Token、密码、私有地址和个人邮箱不进入 evidence。证据摘要截断到 600 个字符，保存 SHA-256 `evidenceHash`。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_github_discovery -v`

预期：文档选择、非执行文件过滤、官方链接、模型/Provider 提取、provenance 和敏感信息过滤测试全部通过。

---

## 任务 4：增加公开 GitHub 仓库发现和固定扫描器

**涉及文件：**

- 修改：`crawler/github_discovery.py`
- 测试：`tests/test_github_discovery.py`

- [ ] **步骤 1：编写失败测试**

模拟 GitHub 搜索 API 返回结果，验证查询词去重、Fork 排除、仓库数量上限、HTTPS 过滤和 API 失败隔离。再模拟仓库文件树与内容响应，验证 `Devansh-365/freellm` 能生成至少一条 `github_peer` 结果。

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_github_discovery -v`

预期：搜索和仓库扫描函数不存在或结果数量与来源字段断言失败。

- [ ] **步骤 3：最小实现**

定义以下接口：

```python
def discover_github_repositories(
    queries: list[str],
    fetch_json,
    max_repositories: int = 20,
) -> list[dict]:
    """Discover public repositories through injectable GitHub API responses."""


def scan_github_peer(
    peer: dict,
    fetch_json,
    fetch_document,
    max_files: int = 80,
    max_total_bytes: int = 2_000_000,
) -> list[dict]:
    """Scan bounded public documentation and return discovery records only."""
```

搜索请求使用公开 GitHub API；生产运行不传 Token，不读取 `.env`。使用固定 User-Agent、低频请求、指数退避和每次运行的总请求上限。仓库文件树只选择 `DOCUMENT_PATH_PATTERNS` 命中的文件，不下载仓库压缩包，不执行文件内容。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_github_discovery -v`

预期：模拟搜索、Fork 排除、限额、失败隔离和 peer 扫描测试通过。

- [ ] **步骤 5：网络边界验证**

运行：`python -m unittest tests.test_fetch tests.test_github_discovery -v`

预期：任何 HTTP、非允许 host、带凭据 URL 和超限响应都被拒绝或记录为来源失败。

---

## 任务 5：合并候选、保留证据等级并扩展 Coverage

**涉及文件：**

- 修改：`crawler/discovery.py`
- 测试：`tests/test_discovery.py`、`tests/test_github_discovery.py`

- [ ] **步骤 1：编写失败测试**

验证 `github_peer` 候选：

- 初始状态永远是 `needs_review`。
- 保留 repository/path/commit/evidenceHash。
- 同一 `providerId + sourceUrl` 合并时保留最早发现时间。
- 同一仓库路径和 commit 不重复计算。
- 不因 `officiality=peer_discovery` 直接进入 Offer。
- Coverage 增加 peer 仓库、文件、失败和候选统计。

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_discovery tests.test_github_discovery -v`

预期：新增字段缺失、候选等级错误或 Coverage 字段不存在。

- [ ] **步骤 3：最小实现**

扩展 `build_candidates()` 和 `merge_candidates()`，识别 `sourceKind=github_peer`，将 provenance 原样保留，并强制 `status="needs_review"`。扩展 `build_coverage_report()` 返回：

```python
{
    "peerRepositoryCount": 0,
    "peerDocumentCount": 0,
    "peerSuccessfulDocumentCount": 0,
    "peerFailedDocumentCount": 0,
    "peerCandidateCount": 0,
}
```

使用 `(repository, path, commitSha)` 去重文档记录，使用现有 canonical URL 规则去重 Offer 候选。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_discovery tests.test_github_discovery -v`

预期：官方扫描回归通过，GitHub provenance、状态、去重和 Coverage 测试通过。

---

## 任务 6：接入 CLI 并保持兼容

**涉及文件：**

- 修改：`crawler/cli.py`
- 修改：`tests/test_discovery.py`
- 测试：`tests/test_github_discovery.py`

- [ ] **步骤 1：编写失败测试**

验证旧命令仍可运行：

```text
python -m crawler.cli discover --providers <providers.json> --out <candidates.json>
```

验证新命令接受：

```text
python -m crawler.cli discover --providers <providers.json> --github-peers <github-peers.json> --out <candidates.json> --scan-out <scan.json>
```

并断言第二条命令同时写入官方扫描结果和 `sourceKind=github_peer` 的结果。

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_discovery tests.test_github_discovery -v`

预期：CLI 不识别 `--github-peers` 或输出缺少 peer 结果。

- [ ] **步骤 3：最小实现**

给 `discover` 增加可选 `--github-peers`、`--github-max-repositories`、`--github-max-files` 参数。未提供 `--github-peers` 时只执行原有官方扫描。提供后依次执行官方 Provider 扫描和 peer 扫描，再通过同一个 candidates merge 流程写入审核队列。

CLI 输出保持可读：

```text
discover: <total> candidates
official sources: <official_count>
github peer documents: <peer_document_count>
```

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_discovery tests.test_github_discovery -v`

预期：旧 CLI 测试和新 CLI 测试全部通过。

- [ ] **步骤 5：端到端本地 fixture 验证**

运行：`python -m crawler.cli discover --providers data/providers.json --github-peers data/github-peers.json --out data/candidates.json --scan-out data/snapshots/discovery-scan.json --max-links 5 --max-pages 100`

预期：命令返回 0 或仅因外部来源失败返回来源失败状态；`data/candidates.json` 中新增项均为 `needs_review`，没有覆盖 `data/offers.json`。

---

## 任务 7：更新扫描 skill 和文档测试

**涉及文件：**

- 修改：`skills/free-ai-offer-research/SKILL.md`
- 修改：`skills/free-ai-offer-research/README.md`
- 修改：`skills/free-ai-offer-research/references/source-policy.md`
- 修改：`tests/test_skill.py`

- [ ] **步骤 1：编写失败测试**

在 `tests/test_skill.py` 增加断言：技能文档包含 `data/github-peers.json`、`github_peer`、`needs_review`、不执行仓库脚本、commit/path provenance 和 GitHub 扫描命令。

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_skill -v`

预期：新增文档关键词断言失败。

- [ ] **步骤 3：最小实现**

在技能工作流中增加 GitHub 发现阶段：先扫精选 peer，再按公开关键词发现仓库；只读取限定文档；所有结果进入候选队列；第三方 peer 只能发现线索；免费结论必须回到官方来源。写明不执行代码、不安装依赖、不读取 Token、不绕过限制和失败分类规则。

README 增加一条完整示例：

```text
扫描 GitHub 同类项目，发现新的免费 Provider、模型和文档入口，并回到官方页面核验。
```

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_skill -v`

预期：技能文档测试通过，技能行数仍低于测试规定的 500 行；若接近上限，将重复说明合并为一个段落而不降低安全规则。

---

## 任务 8：制作三套真实视觉初稿

**涉及文件：**

- 新建：`design-demos/dark-console.html`
- 新建：`design-demos/console-editorial.html`
- 新建：`design-demos/docs-directory.html`
- 读取：`data/offers.json`、`design/brand-spec.md`、参考站公开页面

- [ ] **步骤 1：准备真实内容和设计假设**

三版统一使用当前 `data/offers.json` 的真实 Offer，至少展示免费机制、额度、有效期、地区、官方动作、来源和最后核验时间。所有具名 Provider 使用现有文字标记或已核验官方 Logo，不编造品牌资产。

- [ ] **步骤 2：制作三版 HTML/CSS**

三版必须结构不同：

- `dark-console.html`：深色网格背景、顶部导航、模型状态表和代码面板。
- `console-editorial.html`：深色导航/代码区域、浅色目录主体、证据摘要和筛选栏；这是推荐基线。
- `docs-directory.html`：左侧 Docs/Provider 筛选栏、右侧模型目录、抽屉式详情。

共同要求：正文至少 14px、元信息至少 12px、正常对比度至少 4.5:1、移动端不横向溢出、没有装饰性虚假统计、没有复制参考站文案。

- [ ] **步骤 3：截图验证**

运行：

```text
npx playwright screenshot file:///D:/WorkSpace/freellm/design-demos/dark-console.html D:/WorkSpace/freellm/design-demos/dark-console.png --viewport-size=1440,900
npx playwright screenshot file:///D:/WorkSpace/freellm/design-demos/console-editorial.html D:/WorkSpace/freellm/design-demos/console-editorial.png --viewport-size=1440,900
npx playwright screenshot file:///D:/WorkSpace/freellm/design-demos/docs-directory.html D:/WorkSpace/freellm/design-demos/docs-directory.png --viewport-size=1440,900
```

预期：三个 HTML 和三个 PNG 均生成；页面控制台无 JavaScript 错误，桌面和移动视口都可读。

- [ ] **步骤 4：用户选择门**

同时展示三张截图，等待用户选择一个方向或组合。将选择原话、截图路径和组合规则写入 `design/direction-approved.md`。没有选择记录不得修改生产页面。

---

## 任务 9：按用户选择实施生产页面视觉改版

**涉及文件：**

- 修改：`design/brand-spec.md`
- 修改：`design/direction-approved.md`
- 修改：`design/free-china-ai-index.html`
- 测试：`tests/test_e2e_static.py`

- [ ] **步骤 1：先写页面验收测试**

在 `tests/test_e2e_static.py` 增加以下可观察断言：

- 页面标题仍包含 Free AI Index。
- 17 条以上当前 Offer 能被页面渲染。
- 搜索 `Qwen3` 只显示 Qwen 相关结果。
- 点击 Offer 能打开详情抽屉。
- 详情显示 `lastVerifiedAt`、证据来源和官方动作链接。
- 复制命令按钮不报错。
- 移动视口没有横向滚动条。

- [ ] **步骤 2：运行并确认失败**

运行：`python -m unittest tests.test_e2e_static -v`

预期：尚未改版的页面至少有新增视觉入口或交互断言失败；失败信息明确指出选择器或文本缺失。

- [ ] **步骤 3：按选定方向实现**

保留现有 Offer JSON 嵌入和运行时加载逻辑，按选择更新 tokens、导航、筛选、模型卡、详情抽屉、代码区、Docs/Compare/Quickstart 区块。所有免费机制继续使用现有字段，不把第三方 GitHub 线索渲染为已核验 Offer。

更新 `design/brand-spec.md`，记录最终背景、文字、边框、状态色、字体、间距和组件规则。更新 `design/direction-approved.md`，记录选定方向和生产页面路径。

- [ ] **步骤 4：运行并确认通过**

运行：`python -m unittest tests.test_e2e_static -v`

预期：静态页面交互测试通过，页面错误数为 0，Qwen3 搜索结果、详情、复制命令和移动布局均符合断言。

---

## 任务 10：全量构建、数据校验和发布前门禁

**涉及文件：**

- 读取：`data/offers.json`、`data/candidates.json`、`data/coverage.json`
- 修改：仅在构建过程发现页面嵌入数据过期时修改 `design/free-china-ai-index.html`
- 测试：全部现有测试和新增测试

- [ ] **步骤 1：运行 Schema、构建和全量测试**

运行：

```text
python -m crawler.cli validate data/offers.json
python scripts/build_static.py --check
python -m unittest discover -s tests -v
git diff --check
```

预期：Offer schema 通过；静态页面显示 `current`；所有测试通过；`git diff --check` 无空白错误。

- [ ] **步骤 2：审查发布门控**

确认：

- GitHub 候选全部是 `needs_review`。
- `data/offers.json` 没有由 GitHub peer 扫描自动新增的未经确认结论。
- `data/coverage.json` 能区分官方来源和 peer 文档。
- robots.txt 没有阻断公开页面和 Google 抓取器。
- 没有把 API Key、Token、密码、私人 URL 写入数据或证据。
- 当前工作树原有修改仍保留，未执行回滚或强制覆盖。

- [ ] **步骤 3：人工检查页面**

用浏览器打开生产静态页面，检查桌面和移动布局、搜索、筛选、详情、官方链接、代码复制、导航、来源说明、隐私和条款入口。确认没有把参考站名称或第三方文案显示为自己的品牌内容。

- [ ] **步骤 4：提交前输出变更摘要**

运行：`git status -sb` 和 `git diff --stat`。

预期：输出仅包含计划内文件和用户原有修改；实施者在提交前向用户报告发现的外部来源失败、待审核候选和页面差异。

---

## 质量门控

- [ ] 现有用户修改未被覆盖、回滚或重置。
- [ ] GitHub 只作为发现层，官方来源仍是公开 Offer 的证据门。
- [ ] 仓库内容从未被执行，敏感信息从未被保存。
- [ ] 所有候选保留来源 URL、仓库、路径、commit 和抓取时间。
- [ ] 单次网络失败没有被解释为过期。
- [ ] 三个视觉初稿已截图展示，并有用户选择记录。
- [ ] 用户选择记录存在后才改生产页面。
- [ ] Schema、构建、单元测试、端到端测试和 diff 检查全部通过。
- [ ] 正确的 Vercel 项目和公开地址经过单独确认后才部署。

## 执行方式决策点

计划支持两种执行方式：

1. 同会话逐步执行：按任务顺序实施，任务 1–7 完成后先同步扫描结果，再制作三套视觉初稿，用户选择后实施生产页面。
2. 子代理驱动执行：每个任务由独立执行单元完成，并在任务间做规格符合性和代码质量审查。

无论选择哪种方式，实施必须从 `codex/github-peer-discovery-console-style` 分支开始，不在 `main` 上直接修改。
