# FreeLLM · 免费 AI 资源索引 / Free AI Index

<div align="center">

**🌐 在线站点 / Live Site: [freellm.top](https://freellm.top/)**

一个面向中文用户的免费 AI 资源目录。
An evidence-led directory of free, trial, and low-cost AI offers.

**[中文](#中文) | [English](#english)**

</div>

---

## 中文

FreeLLM（[freellm.top](https://freellm.top/)）整理免费模型、免费额度、免费 IDE、API、开放权重和相关工具，每个条目都记录平台、限制条件、地区、注册要求和官方入口，使用前以官方页面为准。

### 在线展示

- 站点首页：[freellm.top](https://freellm.top/)
- Vercel 预览：[freellm-omega.vercel.app](https://freellm-omega.vercel.app/)
- GitHub 仓库：[xdguo-design/freellm](https://github.com/xdguo-design/freellm)

![FreeLLM 首页预览](freellm-01-hero.png)

### 当前内容

- **47 个**已整理的 AI 资源条目，另有 **220 条**第三方模型目录记录和 **40 家**厂家目录
- 原资源目录：[资源目录](https://freellm.top/models/)；模型中心：[双 Tab 页面](https://freellm.top/models/center/)（精选资源 / 全部模型）；独立模型大列表：[全部模型](https://freellm.top/models/all/)，支持搜索、按厂家筛选、按评分 / 厂家 / 模型分组；厂家入口：[按厂家浏览](https://freellm.top/providers/)
- 重点入口附有逐步操作、可复制命令、验证动作和官方来源；操作型厂家（如 Freebuff、LongCat）即使暂时没有模型目录记录，也会单独保留操作页
- **7 个**分类：[免费额度](https://freellm.top/category/free-quota/)、[学生优惠](https://freellm.top/category/student/)、[免费 IDE](https://freellm.top/category/free-ide/)、[AI API](https://freellm.top/category/api/)、[开放权重](https://freellm.top/category/open-weights/)、[试用与促销](https://freellm.top/category/promo/)、[Web 与浏览器 AI](https://freellm.top/category/web/)
- **9 个**主题指南页：[免费 LLM API 开放目录指南](https://freellm.top/guides/free-llm/)、[免费 OpenAI API 替代品](https://freellm.top/guides/free-openai-api-alternatives/)、[Claude Code 免费替代品](https://freellm.top/guides/claude-code-free-alternatives/)、[免费 OpenAI 兼容 API](https://freellm.top/guides/free-openai-compatible-apis/)、[免费 AI 编程工具](https://freellm.top/guides/free-ai-coding-tools/)、[免费 AI 搜索 API](https://freellm.top/guides/free-ai-search-apis/)、[开源权重模型](https://freellm.top/guides/open-weight-models/)、[模型上下文窗口](https://freellm.top/guides/model-context-windows/)、[国内免费 AI API](https://freellm.top/guides/china-free-ai-api/)
- 展示来自 GitHub、Hugging Face 等平台的公开外部信号（Stars、Likes、Downloads）
- 外部信号只作为原始公开数据展示，不伪造本站评分，也不把不同平台的数据强行合并成一个分数

### 自动化

| Workflow | 频率 | 作用 |
| --- | --- | --- |
| `daily-check` | 每天 01:00 UTC | 校验 offers schema，扫描公开来源；结果只写入 artifacts 和 `data/review-queue.json`，不直接改公开数据 |
| `automated-discovery-pr` | 每周一 03:00 UTC | 运行受限范围的自动发现流水线，以 Pull Request 形式提交候选条目 |

`crawler/` 目录包含数据抓取、发现、diff 与 schema 校验模块；新条目经过人工审核后才会进入正式目录。

### 静态排序引擎

首页默认顺序由无数据库的 TypeScript 排序引擎生成，原始资源数据仍保存在 `data/offers.json`。排序权重为：**新鲜度 35% + 免费可用价值 30% + 热度 20% + 用户行为 10% + 特殊优惠 5%**。

- 新收录 / 新模型 / 免费状态变化优先；时间衰减为 0–3 天 100%、4–7 天 90%、8–14 天 75%、15–30 天 55%、31–60 天 30%、61–90 天 15%、90 天后 5%。
- `contentUpdatedAt` 不参与新鲜度，避免旧条目只改文案就重新冲榜。
- 行为数据使用曝光校正 CTR；没有真实行为数据时给中性 50 分，不给新条目记 0 分。
- 仅学生身份可用的优惠会被降权；普通免费方案即使同时有学生权益，也不会被误判为“学生专属”。
- 失效/不可达、免费状态未确认、长期未核验和持续低关注会进入惩罚项。
- `data/ranked-offers.json` 保存可审计的评分结果；`data/offers-ranked.json` 是首页实际读取的完整静态数据。两者都由构建流程生成，不需要数据库。

重新生成并校验：

```bash
node scripts/generate_ranking.ts
python scripts/build_static.py
node --test tests/ranking.test.ts
node scripts/generate_ranking.ts --check
python scripts/build_static.py --check
```

排序脚本使用 Node.js 24+ 原生 TypeScript 支持，无 npm 依赖。

### 项目结构

```text
data/offers.json                 资源目录原始数据
data/ranking-config.json         排序权重、衰减、惩罚和多样性配置
data/ranking-behavior.json       可选行为输入（无数据时使用中性分）
data/ranked-offers.json          排序评分审计结果
data/offers-ranked.json          首页实际读取的排序后完整数据
data/models.json                 第三方模型目录快照（含新鲜度状态）
data/provider-catalog.json       厂家聚合目录
data/operations/*.json           重点厂家 / 模型的详细操作路径
data/providers.json              平台与提供商信息
data/community-signals.json      外部公开信号快照
data/review-queue.json           待人工审核的发现候选
data/daily-log/*.json            每日新增、恢复、下线与来源状态记录
crawler/                         抓取 / 发现 / diff / schema 模块
scripts/ranking_engine.ts         TypeScript 排序引擎
scripts/generate_ranking.ts      生成 / 校验静态排名结果
scripts/build_static.py          静态页面与排序后运行时数据构建
scripts/build_seo_pages.py       SEO 详情页 / 分类页 / 指南页生成
scripts/sync_model_catalog.py    合并模型快照并标记 new/current/stale
design/free-china-ai-index.html  网站页面
offers/<id>/index.html            资源详情页（生成文件）
category/<slug>/index.html        分类页（生成文件）
guides/*/index.html               指南页（生成文件）
logs/index.html                   每日变更日志（生成文件）
tools/index.html                  在线工具合集（精选自 leowh.com/tools）
docs/specs/                       设计与实施记录
ads.txt                          Google AdSense 授权声明
robots.txt                       搜索引擎抓取规则
sitemap.xml                      站点地图
llms.txt                         面向 AI/搜索系统的站点说明
vercel.json                      Vercel 路由配置
```

### 本地运行

```powershell
python -m http.server 8000
```

然后打开 <http://localhost:8000/design/free-china-ai-index.html>。如需本地行为与线上根路径一致，可使用 `npx vercel dev`。

### 验证与构建

```powershell
node --test tests/ranking.test.ts
node scripts/generate_ranking.ts --check
pytest -q
python scripts/build_static.py --check
python scripts/build_seo_pages.py --check
# 查看每日更新日志：/logs/
# 配置 AdSense 展示广告单元后再生成详情页（slot ID 仅填数字）
$env:FREELLM_ADSENSE_SLOT="1234567890"
python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top
# 用新的发现快照更新模型目录（不会删除消失记录）
python scripts/sync_model_catalog.py --input data/models-discovered.json --output data/models.json --as-of 2026-09-09
```

`FREELLM_ADSENSE_SLOT` 未设置或不是纯数字时，不会生成显式广告单元；设置后会写入资源详情页的 `data-ad-slot`。正式发布前请确认 AdSense 网站状态为 Ready，并确认根目录 `/ads.txt` 中的 publisher ID 与账户一致。

### 发布

生产站点部署在 Vercel，根路径指向 `design/free-china-ai-index.html`。更新页面或数据后，应先通过验证，再发布生产版本并检查首页、`/ads.txt`、`/robots.txt` 和 `/sitemap.xml`。

### 数据说明

目录内容和外部信号会随官方平台状态变化。使用前请通过条目中的官方链接再次确认额度、地区限制、服务条款和隐私政策。

---

## English

FreeLLM ([freellm.top](https://freellm.top/)) is a curated directory of free AI models, free tiers, free coding IDEs, APIs, open-weight models, and related tools. Every entry records the platform, limits, region restrictions, sign-up requirements, and the official link — always confirm details on the official page before use.

### Live

- Homepage: [freellm.top](https://freellm.top/)
- Vercel preview: [freellm-omega.vercel.app](https://freellm-omega.vercel.app/)
- GitHub repo: [xdguo-design/freellm](https://github.com/xdguo-design/freellm)

### What's inside

- **47** curated AI resource entries, plus **220** third-party model-directory records across **40** providers
- Model directory: [all models](https://freellm.top/models/) with search, provider filtering, and score / provider / model grouping; provider directory: [browse by provider](https://freellm.top/providers/)
- Priority entries include step-by-step setup, copyable commands, validation actions, and official sources; operation-only providers such as Freebuff and LongCat keep dedicated pages even without synced model rows
- **7** categories: [free quota](https://freellm.top/category/free-quota/), [student offers](https://freellm.top/category/student/), [free coding IDEs](https://freellm.top/category/free-ide/), [AI API services](https://freellm.top/category/api/), [open-weight models](https://freellm.top/category/open-weights/), [trials & promotions](https://freellm.top/category/promo/), [web & browser AI](https://freellm.top/category/web/)
- **9** topic guide pages: [Free-LLM guide](https://freellm.top/guides/free-llm/), [free OpenAI API alternatives](https://freellm.top/guides/free-openai-api-alternatives/), [free Claude Code alternatives](https://freellm.top/guides/claude-code-free-alternatives/), [free OpenAI-compatible APIs](https://freellm.top/guides/free-openai-compatible-apis/), [free AI coding tools](https://freellm.top/guides/free-ai-coding-tools/), [free AI search APIs](https://freellm.top/guides/free-ai-search-apis/), [open-weight models](https://freellm.top/guides/open-weight-models/), [model context windows](https://freellm.top/guides/model-context-windows/), [free AI APIs in China](https://freellm.top/guides/china-free-ai-api/)
- Public external signals from GitHub, Hugging Face, and similar platforms (Stars, Likes, Downloads), shown as raw public data — no fabricated site-wide scores, no merging of different platforms into one number

### Automation

| Workflow | Schedule | Purpose |
| --- | --- | --- |
| `daily-check` | Daily at 01:00 UTC | Validates the offers schema and scans public sources; results land in artifacts and `data/review-queue.json` only — public data is never edited directly |
| `automated-discovery-pr` | Mondays at 03:00 UTC | Runs a bounded discovery pipeline and submits candidates as a pull request |

The `crawler/` package contains the fetching, discovery, diff, and schema-validation modules; new entries enter the directory only after human review.

### Static ranking engine

The homepage uses a database-free TypeScript ranking engine. Raw curation stays in `data/offers.json`; generated ranking outputs are committed as static artifacts. The weights are **35% freshness, 30% free-access value, 20% popularity, 10% behavior, and 5% special offers**. Freshness decays over time, content-only edits do not create freshness, CTR is exposure-adjusted, missing behavior stays neutral, student-only offers are downgraded, and broken/stale entries receive penalties.

Run with Node.js 24+:

```bash
node scripts/generate_ranking.ts
python scripts/build_static.py
node --test tests/ranking.test.ts
node scripts/generate_ranking.ts --check
python scripts/build_static.py --check
```

### Project layout

See the [Chinese section](#中文) for the full tree. Key paths:

- `data/offers.json` — the catalog data
- `crawler/` — fetching / discovery / diff / schema modules
- `scripts/` — static build and SEO page generation
- `offers/`, `category/`, `guides/` — generated HTML pages

### Local development

```bash
python -m http.server 8000
```

Then open <http://localhost:8000/design/free-china-ai-index.html>. For root-path parity with production, use `npx vercel dev`.

### Verify & build

```bash
node --test tests/ranking.test.ts
node scripts/generate_ranking.ts --check
pytest -q
python scripts/build_static.py --check
python scripts/build_seo_pages.py --check
python scripts/site_health.py
```

To add a manual AdSense display unit to offer detail pages, set `FREELLM_ADSENSE_SLOT` to the numeric slot ID from AdSense and regenerate the static pages before deployment. Invalid or missing values intentionally render no explicit ad unit.

### Deployment

The production site is deployed on Vercel; the root path serves `design/free-china-ai-index.html`. After changing pages or data, run the checks, deploy, and verify the homepage, `/ads.txt`, `/robots.txt`, and `/sitemap.xml`.

The daily discovery workflow writes date-partitioned records under `data/daily-log/` and publishes the detailed log page at `/logs/`. Failed source scans are recorded as unavailable sources and are never treated as offline entries.

### Data disclaimer

Catalog content and external signals change as providers update their platforms. Always re-check quotas, regional restrictions, terms of service, and privacy policies via the official links in each entry.
