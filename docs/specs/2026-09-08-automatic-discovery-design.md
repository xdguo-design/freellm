# 自动发现 AI 免费资源设计

## 目标

让 FreeLLM 能主动发现尚未登记的 AI 厂商、模型和免费/低价入口，不再依赖用户逐个提供名称；同时避免未经核验的内容直接进入公开目录。

## 核心流程

```text
公开发现源 → 候选证据 → 去重与历史合并 → 自动生成候选 PR → 人工一次审核合并 → 生成页面并发布
```

第一版扩展现有安全的 GitHub 公共 API 扫描器：使用一组可版本化的宽泛查询，发现目录、网关、模型目录和 API 文档仓库，再只读取 README/docs/配置示例等文档文件，不执行仓库代码。现有 provider registry 继续负责已知厂商的官方来源复核。

## 状态边界

- `discovered`：刚被公开发现，证据尚不足以进入目录。
- `needs_review`：已保存来源 URL、仓库、文档路径、提交 SHA、关键词和证据摘要，等待人工核验。
- `verified`：人工确认官方来源、免费机制、模型和限制后，才转换为 `data/offers.json` 条目。

自动化只生成候选队列和 PR，不自动把候选伪装成已核验 Offer。候选扫描会继续过滤外部链接、敏感配置和不可验证的内容。

## 自动化方式

- 新增 `data/discovery-queries.json`，集中维护 GitHub 宽搜索词。
- 扩展 `crawler.github_discovery`，对未知仓库做限量、去重、文档优先扫描，并保留仓库描述、stars、查询词和提交 SHA。
- 新增候选报告脚本，输出候选数量、来源、提及的厂商/模型和下一步核验提示。
- 新增每周 GitHub Actions workflow：运行全局发现、生成 `data/candidates.json` 和报告，使用 `GITHUB_TOKEN` 创建一个批量 PR；没有候选变化时不创建 PR。
- 不修改生产 `offers.json`，不保存真实 API Key，不执行第三方仓库脚本。

## 验收标准

- 宽搜索能发现不在 `data/providers.json` 中的未知仓库，并生成 `needs_review` 候选。
- 相同仓库文档跨查询只保留一条候选，重复运行会累加 `seenCount` 而不重复增长。
- 候选记录包含来源 URL、仓库、路径、提交 SHA、证据摘要和安全过滤结果。
- 报告和 PR 仅涉及候选队列，不把未核验内容加入首页或 sitemap。
- workflow 使用最小必要 GitHub 权限，测试、schema 校验和静态构建检查继续通过。

## 风险控制

- GitHub API 使用公开接口和数量上限，避免无界抓取和速率耗尽。
- 仅允许 `https://github.com`、`api.github.com`、`raw.githubusercontent.com`，只读取文档路径。
- 自动移除疑似密钥配置行；URL 查询参数禁止包含 key/password/secret/token。
- PR 审核清单要求补齐官方域名、免费规则、地区、有效期、额度和注册入口。
