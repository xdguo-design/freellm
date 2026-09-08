# freellm.net 第三方模型发现设计

## 目标

把 `freellm.net` 接入 FreeLLM 的自动发现流水线，批量发现具体模型和接入路径，解决当前目录以提供商为主、模型覆盖不足的问题。

## 边界

- `freellm.net` 是第三方聚合目录，只作为发现线索，不作为免费资格、额度或官方归属的最终证据。
- 抓取结果进入现有 `data/candidates.json`，状态固定为 `needs_review`。
- 只有人工根据提供商官方定价、文档和 API 说明核验后，才允许转换为 `data/offers.json`。
- 不执行网页脚本，不抓取用户凭证，不采集带认证参数的链接。

## 数据流

```text
freellm.net/models/ + freellm.net/llms.txt
        ↓
结构化模型行解析 + 安全 URL 过滤
        ↓
按目录详情 URL 去重，生成第三方候选
        ↓
合并历史 seenCount，生成候选报告和 PR
        ↓
人工核验官方来源后才发布
```

## 模块与接口

- 新增 `crawler/freellm_net_discovery.py`：
  - `validate_source_registry(sources)` 校验第三方来源配置。
  - `parse_model_directory(html, base_url)` 解析服务端渲染的模型表格。
  - `parse_llms_links(content, base_url)` 提取安全的目录内部 Markdown 链接。
  - `discover_freellm_net_sources(sources, fetcher, max_models)` 获取来源并生成 `needs_review` 扫描记录。
- 新增 `data/third-party-discovery-sources.json`：集中维护 `freellm.net` 的模型页和 `llms.txt`。
- 扩展 `crawler.cli discover`：可选读取第三方来源配置，不改变已有官方和 GitHub 扫描参数。
- 扩展发现报告：显示目录提供商、模型、上下文、限速、状态和第三方来源警告。

## 候选字段

每个模型候选使用 `providerId: "freellm-net"`，以详情页 URL 作为稳定去重键，并保留：

- `directoryProvider`、`directoryProviderSlug`
- `model`、`modelId`、`modelSlug`
- `modality`、`context`、`rateLimit`、`status`
- `directoryFree`、`directoryNoCard`、`directoryVerified`、`tierType`
- `sourceKind: "third_party_directory"`
- `officiality: "third_party_discovery"`
- `directoryUrl` 与 `directoryReferences`

目录评分不进入站内排序，避免把第三方评分误当成官方事实。

## 错误处理与安全

- 单个来源 HTTP 失败、超限或格式错误时生成失败扫描记录，其他来源继续执行。
- 只接受 `https://freellm.net` 及其子域名；拒绝用户名、密码、控制字符和敏感查询参数。
- 模型行缺少详情 URL 或模型名时跳过，不生成不可复核候选。
- 对模型数量设置上限，避免目录扩张导致无界输出。

## 验收标准

- 固定 HTML fixture 能解析出模型、提供商、详情 URL、免费标记、上下文、限速和状态。
- `llms.txt` 只返回安全的 HTTPS 目录链接，并过滤外部链接和凭证参数。
- 相同模型重复抓取会被现有候选合并并增加 `seenCount`，不会增加重复记录。
- CLI 和 GitHub Actions 可配置执行该来源；未核验数据不会写入 `data/offers.json`。
- 原有测试、数据校验、静态构建和 SEO 构建继续通过。
