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

## 免费模型清单对齐（同日第二遍）

主入口换成国内站后，`model` 字段里仍是国际站模型目录的旧模型族，且完全没有国内站最新一代模型。
按官方定价页（`agnes-ai.cn/zh-Hans/docs/pricing`，2026-09-19）重排：

- **现价 ¥0（列入 `freeModels`）**：`agnes-3.0-flash`、`agnes-2.5-flash`、
  `agnes-image-2.5-flash`、`agnes-image-2.1-flash`、`agnes-image-2.0-flash`、
  `agnes-video-v2.0`、`agnes-video-2.5-flash`（限时免费）。
- **付费（明确排除）**：`agnes-2.5-pro`（¥3 / ¥6 每 M Token）、
  `agnes-2.5-pro-beta`（¥0.70 / ¥2.10 每 M Token）、`agnes-video-2.5`（¥0.15–0.35 每秒）。
- **只在国际站模型目录里、国内站定价页未列出**：`agnes-1.5-flash`、`agnes-2.0-flash`，
  未列入免费清单，标为待核实。

文本模型上下文窗口 512K、`agnes-3.0-flash` 最大输出 65,536 Token 取自各模型官方文档页。
另记录一处官方文档笔误：`agnes-25-flash` 页规格表把「模型名称」写成 `agnes-2.0-flash`。

## 模型目录纳入（同日第三遍）

Agnes 此前**完全不在 `data/models.json` 里**：没有 offer 之外的模型页，也没有
`/providers/agnes-ai/`。`data/provider-catalog.json` 里那条 `agnes-ai`（5 个模型、
`lastSeenAt` 2026-09-09）是旧目录式流水线的残留，模型 ID（`agnes-1-5-flash`、
`agnes-2-0-flash`）国内站定价页已不再列出。

### 为什么没有写 Mintlify 解析器

国内站文档站确实是 Mintlify，`https://wiki.agnes-ai.cn/llms.txt` 是干净的索引，
每页也有 `.md` 变体（`/zh-Hans/docs/<slug>.md`）。但**逐页抓下来看，这些页是散文档不是目录**：

- 页与页结构不统一：`agnes-25-pro` 有 `| 模型名称 | \`agnes-2.5-pro\` |` 规格表；
  `agnes-image-2.5-flash` 只在参数表里以「模型名称，使用 \`agnes-image-2.5-flash\`」出现；
  `agnes-video-25` 全文**一次都没有**「模型名称」。
- 页内会交叉引用别的模型 ID（`agnes-25-flash` 同时出现 `agnes-2.0-flash`），
  按「页里出现的反引号 ID」抽取会抽错。
- 按「标签同行取反引号值」的宽松规则抽 `最大输出`，`agnes-25-flash` / `agnes-25-pro` /
  `agnes-25-pro-beta` 三页抽到的是正文里的 `incomplete`（响应状态说明），**是错的**。

也就是说：能稳定抽出的只有模型 ID 集合与模态，上下文窗口和最大输出必须靠启发式，
会产出**错数字**。这与 `crawler/official_model_discovery.py` 自己写的第 4 条设计规则
（「Assert only what the source states」——源没说的字段留空，不许猜）直接冲突，
也与本项目的数据真实性纪律冲突。所以**不新增解析器**，改走已有的手工核验覆盖层
（`data/models-curated.json`），和 `atria-asi` / `unisound` 同一条路径。

结论留档：以后若要给别的 Mintlify 站写解析器，先确认它的页面是**目录**而不是散文档；
`llms.txt` 只是页面索引，本身不含模型元数据。

### 写入方式

- `data/models-curated.json`：新增 10 行 `agnes-ai/*`（文本 4 / 图片 3 / 视频 3），
  字段逐条取自官方国内站文档页与定价页，`sourceUrl` 指向各模型文档页，
  `canonicalModelId` 是官方「模型名称」里那个可直接当 `model` 传的字符串。
- `context` / `maxOutput` 只写官方写了值的模型：文本模型 `512K` / `1M`、最大输出 65536；
  图片与视频页没有规格表，两项**留空**而不是估。
  （`agnes-25-flash` 页写 `65.5K`，即 65536 按千进位的约数，与 `agnes-30-flash` 页的
  `65,536` 一致，故按 65536 记录。）
- `modality`：三页 `2.5-flash` / `2.5-pro` / `2.5-pro-beta` 的响应示例里有
  `"type": "reasoning"`，故记 `reasoning`；`agnes-3.0-flash` 全文没有 reasoning，不记。
  图片页「文生图、图生图、多图合成」与视频页「文生视频、图生视频」按输入文本+图像、
  输出图像/视频记为 `text,image` / `text,image,video`。
- `accessRegion: domestic` + `accessEndpoint: https://api.agnes-ai.cn/v1`，
  与「国内站为主入口」的结论一致；聚合页因此渲染出「国内入口」卡片。
- 走官方流水线合入，不手写 `models.json`：
  `build_model_catalog.py --date 2026-09-19 --models-out data/snapshots/daily-models-20260919.json`
  → `sync_model_catalog.py --input <快照> --output data/models.json --as-of 2026-09-19`。
  结果：210 → 220 条（+10 new，209 current，1 stale），provider 9 → 10 家。

### 连带必须同步的派生文件

`data/models.json` 不是孤立文件，加 10 行会同时被四道测试卡住，逐条按官方流水线补齐：

| 派生文件 | 为什么必须动 | 怎么动的 |
|---|---|---|
| `data/model-access.json` | `test_every_catalog_model_has_exactly_one_access_card` 要求每条模型记录都有一张访问卡 | 跑 `scripts/generate_access_cards.py --date 2026-09-19`：provider 卡 40→40 **零改动**，model 卡 213→223（+10，无删除、无覆盖），再把 Agnes 的 10 张从 `needs_review/unverified` 提为 `current/partial` + `lastVerifiedAt 2026-09-19` + 官方来源，与 atria / dots / unisound 三家的手工卡一致 |
| `data/endpoint-latency.json` | `test_endpoint_latency_file_is_well_formed_and_provider_complete` 要求覆盖目录里每一家 provider | 真跑 `scripts/probe_endpoint_latency.py`（只喂 Agnes 的 10 行，避免把其余 9 家 09-19 已实测的值重新抖动）：`https://api.agnes-ai.cn/v1/models` → 401 `needs_key`，中位 **229ms**（样本 290/229/194，预热 224ms） |
| `README.md` | `ReadmeFactsTests.test_readme_counts_match_current_data` 要求 README 计数与数据一致 | 中英文两处 `210 条` / `**210** third-party` → `220` |
| `about/index.html` | `test_about_and_generated_model_page_counts_match_current_data` 要求 about 页计数与数据一致 | `210+` → `220+` |
| `data/daily-log/2026-09-19.json` | 见下 | 用 `crawler.cli log` 重建 |

### 顺带修掉一个既有红门禁

`test_daily_log_dashboard_exposes_baseline_snapshot` 要求日志页最新一天的
「当日快照」模型数等于 `data/models.json` 的行数。这条**在本次改动之前就是红的**：
HEAD 的 `models.json` 是 210 行，而 `data/daily-log/2026-09-19.json` 的
`observed.models` 只有 190 行（09-18 那天是 210 = 当天 models.json，说明日志本应从
目录数据生成，09-19 这份却来自一次只抓到 190 行的扫描）。

按官方方式重建：`python -m crawler.cli log --models data/models.json --offers data/offers.json
--previous data/daily-log/2026-09-18.json --out data/daily-log/2026-09-19.json --as-of 2026-09-19 --merge`。
结果 `observed.models` 190 → 220，事件 0 → 10（7 `new` + 3 `recovered`，全部是 Agnes）。
3 条 `recovered` 是流水线的既定判定：`agnes-image-2.0-flash`、`agnes-image-2.1-flash`、
`agnes-video-v2.0` 在 09-10～09-16 的日志里是 `observed`，09-17 掉进 `known`（目录式源被移除），
今天重新观测到 —— 事件定义写的就是「previously absent or offline and observed again」。
本次没有手写任何事件，全部由流水线产出。

**遗留隐患（未修）**：GitHub Action 的 `daily-log.yml` 用 `--models data/snapshots/daily-models.json`
（一次新扫描）去 diff 上一天的日志，而日志的模型数又应对齐 `models.json`；两者一旦漂移，
就会互相产生假的 `offline` / `recovered`。09-19 的 190 行就是这么来的。这是流水线口径问题，
与 Agnes 无关，需要单独修（例如让 Action 也走 `sync_model_catalog.py`，或让日志改用同一份目录）。

### 副作用与未做

- 一次真实全量扫描会把 209 行的 `lastSeenAt` 从 2026-09-18 推到 2026-09-19，
  21 行 `freshnessStatus` 从 `new` 转 `current`。这是真实观测结果，不是伪造。
- `data/provider-catalog.json` **故意没有重生成**：它是旧目录式流水线在 2026-09-09 的残留，
  里面 14 家 provider（aion-labs、cerebras、cline、cloudflare-workers-ai、cohere、
  github-models、glhf-chat、google-gemini、grok、hugging-face、kilo-code、mistral-ai、
  ovhcloud、z-ai）的模型在 `models.json` 里已不存在，同时又缺 10 家只在 operations 里出现的
  provider。重生成会顺手删掉这 14 家，而 `scripts/generate_access_cards.py`
  会**连带删掉 `data/provider-access.json` 里这 14 家的注册卡**（`generate()` 只保留
  catalog + operations 里有的 provider）。这属于另一个话题，需单独评估后再动。
- `data/models.json` 里 `dots-api-cn` 的 `canonicalModelId`（`dots3-note-preview`）
  与官方 `/v1/models`（`dots3-note-prev`）仍不一致；该字段是跨 provider 的关联键，
  改动会影响 `tests/test_access_cards.py`，需走爬虫流水线评估，本次未改。

## 来源与时效

- https://agnes-ai.cn/zh-Hans/docs/overview
- https://agnes-ai.cn/zh-Hans/docs/pricing
- https://agnes-ai.cn/zh-Hans/docs/tokenplan
- https://agnes-ai.com/en/docs/overview
- https://github.com/AgnesAI-Labs/AgnesAI-Models/blob/main/MODEL_CATALOG.md
- https://hub.baai.ac.cn/view/56776（国内节点上线的社区报道，仅作背景，不作为结论依据）
