# Agnes AI 国内 / 国际双入口修正

## 背景

Agnes AI 条目此前只登记了国际站入口 `https://apihub.agnes-ai.com/v1`，
但官方同时运营国内站，页面与数据里都没有出现国内地址。更矛盾的是，首页
「中国大陆可用性与注册要求」已经写着「Agnes AI…并提供中国大陆 API 加速节点」——
承诺了节点，却没有给出任何地址。`data/provider-access.json` 的备注也停留在
「大陆加速节点来自智源 BAAI 社区报道，待官方文档核验」。

## 核验结果（2026-09-19）

| 入口 | Base URL | 官方出处 | 无 Key 探测 | 大陆本机往返中位 |
|---|---|---|---|---|
| 国际站 | `https://apihub.agnes-ai.com/v1` | `agnes-ai.com/en/docs/overview` 第 5 节 Base URL | 401 Token not provided | ~1195ms（Cloudflare 104.18.x.x） |
| 国内站 | `https://api.agnes-ai.cn/v1` | `agnes-ai.cn/zh-Hans/docs/overview` 第 8 节 | 401 未提供令牌 | ~220ms（大陆 42.202.211.222） |
| 旧国内节点 | `https://apihub.agnes-ai.cn/v1` | 2026-07-29 国内节点上线公告 | 401 未提供令牌 | ~244ms（与上一行同一 IP） |

两个域名报错结构一致（`type: AgnesAI_error`），确认是同一套 API 的两个门面；
国内站为中文错误信息，国际站为英文。官方国内站 Token Plan FAQ 给出的免费 /
默认用户 RPM 与官方模型目录一致：文本 20 RPM，图片按分辨率 20/10/1/1 RPM，视频 1 RPM。

## 方案

- **主入口改为国内站**：`usageGuide.endpoint`、`command`、`examples.curl`、
  `register`、`docsUrl` 全部指向国内站，理由是本站为 China-first 目录，
  与 atria 等双入口条目的既有做法一致。
- **国际站并列保留**：新增 `accessPaths`（复用 longcat 已有的渲染路径），
  以「中国大陆入口 / 国际站入口」两行并列展示 Base URL、免费状态、访问条件与官方链接；
  国际站文档、控制台、模型目录同时留在 `links` / `sourceUrls` 里，不丢来源。
- **注册要求卡**：`registerUrl` 改为国内站控制台，`regionPolicyId` 指向新增的
  `agnes-ai-dual-endpoint` 地区策略，备注改为记录已核验的双入口事实。
- **地区策略**：新增 `agnes-ai-dual-endpoint`（`type: cloud_region`），
  用 `endpoints` 列出国内 / 国际两条入口。这属于入口与线路差异，不是按国家封锁；
  官方未发布完整国家可用性清单，CN 状态仍按 `unknown`（待核验）呈现。
- **首页文案**：把「提供中国大陆 API 加速节点」改成写明两个地址与 Key 通用。

## 数据与生成

- `data/offers.json`：改写 `agnes-ai-free` 条目，新增 `accessPaths`，
  `lastVerifiedAt` 更新为 `2026-09-19`（当天确实重新核对了两个官方文档与两个活端点）。
- `data/providers.json`：补齐 `api.agnes-ai.cn`、`apihub.agnes-ai.cn`、
  `platform.agnes-ai.cn`、`platform.agnes-ai.com`、`wiki.agnes-ai.cn` 域名与国内文档发现地址。
- `data/provider-access.json`、`data/region-policies.json`：如上。
- 端点与网络实测走官方流水线刷新（`probe_offer_endpoints.py` → `apply_endpoint_check.py`，
  `probe_offer_network.py` → `apply_network_check.py`），不手写实测字段。
- 生成器：`build_static.py` 先跑，`build_seo_pages.py` 最后跑。

## 验收标准

- `offers/agnes-ai-free/` 页面同时出现 `api.agnes-ai.cn/v1` 与 `apihub.agnes-ai.com/v1`，
  且「使用入口」表列出两条入口。
- 测试覆盖双入口：`test_agnes_ai_offer_covers_official_multimodal_models_and_free_api_access`
  断言两个 Base URL 都在数据里，新增 `test_agnes_page_renders_both_official_endpoints`。
- 四道门禁全绿：`build_static.py --check`、`build_seo_pages.py --check`、
  `site_health.py`、`pytest`。

## 已知未完成

- `model` 字段仍是旧的模型族（agnes-2.5-flash 等），国内站文档已列出
  `agnes-3.0-flash`、`agnes-image-2.5-flash`、`agnes-video-2.5`、`agnes-video-2.5-flash` 等，
  需要走官方模型目录流水线逐个对齐，本次未处理。

## 来源与时效

- https://agnes-ai.cn/zh-Hans/docs/overview
- https://agnes-ai.cn/zh-Hans/docs/tokenplan
- https://agnes-ai.com/en/docs/overview
- https://github.com/AgnesAI-Labs/AgnesAI-Models/blob/main/MODEL_CATALOG.md
- https://hub.baai.ac.cn/view/56776（国内节点上线的社区报道，仅作背景，不作为结论依据）
