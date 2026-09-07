# github-peer-discovery

扫描 GitHub 同类项目的公开文档，生成带 `repository/path/commitSha` provenance 的同行发现报告；也可以提取网站信息架构、组件和响应式模式，生成不复制品牌与资产的视觉参考。

## 安装

```text
npx skills add <owner>/<repo> --skill github-peer-discovery
```

在本仓库中可直接使用 `skills/github-peer-discovery/`。若项目已有扫描器，运行：

```text
python -m crawler.cli discover --providers data/providers.json --github-peers data/github-peers.json --out data/candidates.json
```

## 触发示例

- `扫描 Devansh-365/freellm 的 README、docs 和模型/provider 线索`
- `扫描 tashfeenahmed/freellmapi 的 README、docs/providers 和模型/provider 线索`
- `找 GitHub 上同类免费 LLM gateway，并生成审核队列`
- `梳理这些竞品的网站结构，给我三个不复制品牌的视觉方向`

GitHub 内容只作为 `peer_discovery` 线索；候选保持 `needs_review`，必须通过官方来源核验后才能发布。
