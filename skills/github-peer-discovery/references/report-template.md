# GitHub 同行发现报告模板

## 1. 结论摘要

- 扫描范围：
- 扫描模式：快速 / 标准 / 深度
- 时间和版本：
- 仓库数 / 文档数 / 成功数 / 失败数：
- 结论：只写发现线索，不写未经官方确认的免费承诺。

## 2. 仓库清单

| 仓库 | 类型 | 默认分支 | commit SHA | 查询来源 | 备注 |
|---|---|---|---|---|---|
| `owner/repo` | gateway / directory / IDE / other | `main` | `...` | query | peer discovery |

## 3. 文档索引

| 仓库 | path | bytes | status | raw URL | 发现主题 |
|---|---|---:|---|---|---|
| `owner/repo` | `README.md` |  |  |  | provider / model / quota |

## 4. 证据摘要

| 线索 | 文档 provenance | 证据摘要 | 官方核验缺口 | 状态 |
|---|---|---|---|---|
| Provider / model / plan | `repository` + `path` + `commitSha` | 不超过 600 字符 | quota / region / renewal / URL | `needs_review` |

固定字段：`sourceKind=github_peer`、`officiality=peer_discovery`、`evidenceHash`、`mentionedProviders`、`mentionedModels`、`officialLinks`。

## 5. 候选审核队列

每个候选回答：产品类型、免费机制、额度单位、有效期、续费、地区/注册条件、官方链接、证据页、未确认字段。同行文档不能单独通过发布门控。

```json
{
  "status": "needs_review",
  "sourceKind": "github_peer",
  "officiality": "peer_discovery",
  "repository": "owner/repo",
  "path": "README.md",
  "commitSha": "...",
  "reviewReasons": ["official quota page not confirmed", "region unclear"]
}
```

## 6. 网站风格参考（深度模式）

- 参考页面/仓库：
- 可迁移模式：信息架构、密度、状态表达、响应式、交互
- 本项目改写：对应页面、组件和自己的文案
- 明确不复制：品牌、Logo、原文案、专属插画、源码、未经许可资源
- 原型方向：1 / 2 / 3
- 用户选择：

## 7. 失败和下一步

| 项目 | 状态 | 原因 | 下一步 |
|---|---|---|---|
| API / branch / document | `source_unavailable` / `source_limit` |  | retry / official verification / user decision |

最后给出：需要人工核验的官方 URL、需要用户选择的视觉方向、是否可以进入 `free-ai-offer-research` 的官方核验流程。不得直接写入公开 offer。
