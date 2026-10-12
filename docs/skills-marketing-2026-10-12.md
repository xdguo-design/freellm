# Marketing Skills SEO / GEO 收录核验（2026-10-12）

## 结论与收录范围

- 官方上游：[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)，MIT 许可证。GitHub API 检索时仓库 Star **54296**、Fork **8061**；**属于整个仓库，不代表单个 Skill 的评分或流量**。
- 本轮在 FreeLLM 的 `dev` 正式目录追加 **7** 条，**91 → 98**，其中 6 条 SEO/GEO/站点增长技能 + `product-marketing` 共享背景。未安装/未执行/未量化 SEO 效果，所有 FreeLLM Test 均标记 `unknown`、`score:null`。
- 安装：`npx skills add coreyhaines31/marketingskills` 为全量安装。选择性安装：`npx skills add coreyhaines31/marketingskills --skill seo-audit ai-seo programmatic-seo site-architecture competitors schema product-marketing`。官方 README 声明兼容 Claude Code、Codex、Cursor；实际 Agent 触发与运行需设备验证。
- 命名：上游 v2 后结构化数据技能名为 **`schema`**，旧版 `schema-markup` 已更名，不重复收录。竞品对比是 `competitors`，不是独立且名称相似的 `competitor-profiling`。
- 用户转述的公众号文章只作发现线索，所有正式能力以官方 SKILL.md 为准。

## 7 条来源核验表

| 核验 Skill | 页面类别 | 核心价值 | 官方源码 |
| --- | --- | --- | --- |
| `seo-audit` | `seo-content` | 技术 SEO 与站内 SEO 诊断：按证据核对抓取、索引、canonical、hreflang、性能和页面内容，输出按优先级排序的整改清单；不把推断当成搜索引擎实测。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/seo-audit/SKILL.md) |
| `ai-seo` | `seo-content` | AI 搜索可见性（GEO/AEO）：检查模型抓取与引用条件、可提取内容、品牌实体及答案结构；不能保证 ChatGPT、Google AI 或其他模型实际推荐。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/ai-seo/SKILL.md) |
| `programmatic-seo` | `seo-content` | 程序化 SEO 页面规划：用真实数据和模板批量组织目录/对比页面，核对每页独特价值、内链、canonical、索引和内容质量，避免薄内容批量铺页。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/programmatic-seo/SKILL.md) |
| `site-architecture` | `seo-content` | 站点信息架构与导航规划：设计 URL 层级、分类、面包屑和内部链接，可输出 Mermaid 站点关系图；适合梳理模型、服务商与 Skill 目录。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/site-architecture/SKILL.md) |
| `competitors` | `seo-content` | 竞品对比与替代页：生成来源可核对的 VS/Alternatives 页面框架，标注功能、价格和限制的证据与更新时间，禁止杜撰竞品优缺点。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/competitors/SKILL.md) |
| `schema` | `seo-content` | Schema.org / JSON-LD 结构化数据：根据可见页面事实生成并核查组织、网站、面包屑或列表等数据；须验证 Google 当前支持的富结果类型。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/schema/SKILL.md) |
| `product-marketing` | `planning-office` | 增长技能共享产品背景：生成和维护 .agents/product-marketing.md，集中记录受众、定位、价值主张与事实/未确认事项，供 SEO 和营销技能复用。 | [SKILL.md](https://github.com/coreyhaines31/marketingskills/blob/main/skills/product-marketing/SKILL.md) |

## 适用于 freellm.top 的场景与风险

1. **seo-audit**：检查 sitemap、索引覆盖、canonical、hreflang、站点性能；`UNKNOWN` 与实测不混用。JS 注入的 Schema 不能仅凭 `curl` 判为不存在。
2. **ai-seo**：检查 AI 搜索机器人访问、内容可提取性、实体识别与引用证据；`llms.txt`、JSON-LD 或人工撰写 40–60 字答案块不保证被 ChatGPT 等产品引用。
3. **programmatic-seo**：适用于经核验的模型免费额度 / Provider / 限时活动页面。必须每页有差异化的真实数据，阻止大量空洞的模板页进入索引；新页面要尊重原有 URL、避免和目录页重复。
4. **site-architecture**：核对 `/models/`、`/skills/`、`/logs/` 等跨栏目入口、面包屑及内部链接，优先补孤儿页，不能未做重定向就删除已索引 URL。
5. **competitors**：适合真实的 OpenRouter 等竞品体验对照；每项功能、价格与服务限制需可复查来源，时间敏感的表述加核验日期。
6. **schema**：根据页面可见数据生成 `@context`、`@type`、`ItemList` 等 JSON-LD；Google 富结果资格与 Schema.org 合法性分别校验，不能捏造用户评分。
7. **product-marketing**：上游用 `.agents/product-marketing.md` 保存产品定位，可供六种 SEO 技能共享；本轮仅**收录该 Skill**，没有擅自创建/覆盖项目的营销定位文件。

## 许可证与缓存

所有 7 份原版 `SKILL.md` 均保留文字原文、GitHub 原文地址；完整 MIT 许可证副本位于 `data/skill-content/coreyhaines31-marketingskills-LICENSE.txt`，网站缓存文件位于 `skills/content/coreyhaines31-marketingskills-LICENSE.txt`。上游某些 Skill 引用 `references/`：本站只缓存其 SKILL.md 摘要级入口，离线完整执行需要安装整个上游 Skill 包，不宣称引用文档也已收齐。

## 测试和发布门禁

- `data/skills.json`、`data/skills-i18n.json`、`data/skill-tests.json`、`data/skill-styles.json`、`data/skill-eval-tasks.json` 各含 98 个一致 ID，原文缓存共增加 7 份；测试题库新增 7 个可重复任务，但尚未运行大模型。
- 需要 CI 完整重建站点、测试计数/校验规则与关键导航，并核对 `/skills/?category=seo-content` 跳转；然后才考虑 `main` 发布。
- `dev` 与 `main` 曾分叉，合版前需确认差异，不直接推送到生产分支。
