# FreeLLM 外链执行清单

更新时间：2026-09-17
配套文档：`freellm-submission-posts.md`（各渠道文案）、`backlink-forums.md`（论坛渠道）

---

## 0. 先说清楚分工

外链的**最后一步（登录、验证码、点发布）只能由你本人完成**——任何代登录、绕验证码、批量代发的做法都会导致封号，也会把站点品牌搞脏。

这份清单里：
- 🟢 = 已完成（站点侧，我已经做好）
- 🟡 = 你只需复制粘贴 + 登录发布
- 🔴 = 有硬门槛，需要先解决才能做

---

## 1. 站点侧前置（🟢 已完成）

这些是 HelloGitHub、周刊、awesome-list 的**硬门槛**，之前都缺：

| 项目 | 状态 | 说明 |
|---|---|---|
| `LICENSE` | 🟢 | MIT（代码）+ CC BY 4.0（内容与数据）。没有它，多数开源渠道直接拒收 |
| `CONTRIBUTING.md` | 🟢 | 贡献指南 + 数据字段约定 + 提交前自检命令 |
| `/links/` 友链页 | 🟢 | 含"本站信息"区块（方便他人准确引用）、友链申请要求、相关资源推荐 |
| og/twitter 分享卡片 | 🟢 | 日志页原本缺失，已补齐；offer 页原本已有 |
| sitemap 收录 `/links/` | 🟢 | 已加入 |
| 全站页脚 Links 入口 | 🟢 | 首页 + 生成页 + 静态页统一 |
| `/feed.xml` Atom 订阅源 | 🟢 | 44 条最新收录，按时间倒序；全站页面带自动发现链接（阅读器可自动识别） |
| `llms.txt` 更新 | 🟢 | 补充 `/links/` 与 `/feed.xml`，方便 AI 检索器引用 |
| 核验日期新鲜度 | 🟢 | `site_health.py` 由 `ok: false`（44 条错误）转为 `ok: true`；详见 [6.5](#65--已解决核验日期过期2026-09-17-处理完毕) |

**为什么先做这些**：站点本身"不像正经项目"时，投出去的稿子会被当成垃圾广告。补齐后，你的投稿是在陈述一个可复核的开源项目。

---

## 2. 第一优先级：中文周刊 / 月刊（🟡 转化最高）

对中文开发者受众，**一次周刊收录 > 十个英文目录站**。文案已备好，见 `freellm-submission-posts.md` 第 2.2 节。

### 2.1 阮一峰《科技爱好者周刊》

- **动作**：到 `ruanyf/weekly` 仓库按 issue 模板提交（先读一遍当前 README 的投稿说明，渠道可能变）
- **文案**：第 2.2.1 节，可直接复制
- **注意**：一周只发一期，被采纳通常要等；不要重复投同一内容
- **预期**：中文技术圈最大曝光入口之一，页面 follow 且被大量转载

### 2.2 HelloGitHub 月刊

- **动作**：官网投稿入口 / 仓库投稿说明
- **前置**：🟢 LICENSE + README + CONTRIBUTING 已就位
- **文案**：第 2.2.2 节，强调"数据管道 + 每日核验"的工程属性
- **注意**：月刊挑剔，不中不要紧，有实质更新后再投

---

## 3. 第二优先级：中文社区（🟡 需账号）

按"门槛从低到高"排序，建议这个顺序做：

| 顺序 | 渠道 | 门槛 | 落地页 | 文案位置 |
|---:|---|---|---|---|
| 1 | 小众软件论坛 | 注册开放 | `/` 或 `/category/` | backlink-forums 1.2 |
| 2 | SegmentFault / 博客园 | 注册即可，对外链最宽松 | 对应 guides 页 | backlink-forums 1.4 |
| 3 | 知乎 | 注册即可 | `/offers/student/` 等深链 | backlink-forums 1.3 |
| 4 | 掘金 | 注册即可，社区编辑更挑剔 | guides 页 | backlink-forums 1.4 |
| 5 | Linux.do | 邀请码 / 信任等级 | `/logs/` | backlink-forums 1.1 |
| 6 | V2EX | 🔴 需邀请码 | `/` | submission 第 3 节 |

**关键原则**：不要所有渠道都指首页。学生角度指 `/offers/student/`，API 角度指 `/category/api/`，每日核验故事指 `/logs/`——深链更自然也更相关。

---

## 4. 第三优先级：英文产品平台（🟡 需账号）

| 渠道 | 门槛 | 文案位置 |
|---|---|---|
| Product Hunt | 个人账号，新号需先完成 onboarding | submission 第 4 节 |
| Hacker News（Show HN） | 免费，但要求能实际试用 | submission 第 8 节 |
| Peerlist Launchpad | 个人 Maker 账号 | submission 第 6 节 |
| Uneed / MicroLaunch / Launching Next | 免费队列，排期长 | submission 第 7 节 |
| SaaSHub | 需官网邮箱验证 | submission 第 5 节 |

---

## 5. 第四优先级：awesome-list PR（🔴 当前受阻）

- **价值**：durable 外链，长期有效
- **当前阻碍**：本机网络无法直连 github.com（502），也没有 `gh` CLI
- **需要你做的**：在你自己网络环境正常的机器上操作——
  1. fork 目标 awesome-list
  2. 按对方贡献规范，在 AI resources / directory 分区加一行
  3. PR 描述用 `freellm-submission-posts.md` 第 9 节的话术
- **纪律**：**不要**用同一段推广文案同时给几十个 list 提 PR，会被批量关闭并标记

候选目标（提交前逐个确认是否接受 directory 类项目）：
- `eudk/awesome-ai-tools`
- `cheahjs/free-llm-api-resources`（同类项目，先看它的收录标准）
- 其他 AI / dev-tools 主题的 awesome list

---

## 6. 站内持续动作（🟡 长期）

1. **友链互换**：`/links/` 页已上线，现在可以去同类站点谈互换了。要求已写在页面上（内容相关、已上线、先链本站）
2. **每日更新即内容**：`/logs/` 每天自动产出——把它当"可分享的内容"而不是内部日志，社区帖子里引用它比引用首页更有说服力
3. **guides 改写分发**：`guides/` 下 9 篇指南是一稿多投的素材库，一篇改一个平台
4. **订阅源已上线**：`/feed.xml` 可被 Feedly、Inoreader 等阅读器直接订阅。投稿时把它一起给出——对周刊/月刊编辑来说，"有稳定更新的源"比"一个静态站"更值得推荐

---

## 6.5 ✅ 已解决：核验日期过期（2026-09-17 处理完毕）

**结论：`scripts/site_health.py` 现在返回 `ok: true`（错误 0 条，退出码 0）。投稿可以开始了。**

处理前的状态：`ok: false`，44 条新鲜度错误（37 条 offers 为 9–11 天、8 条 models 为 8 天）。这是 9-16 就存在的既有问题，不是当时改动引入的。

**为什么这会拖垮外链**：本站最核心的差异点是"每条都有核验日期、可复核"。当周刊编辑或社区用户点进来，看到页面上写着"核验于 2026-09-07"而当天已是 9-17，可信度会直接打折——而这恰恰是我们要投稿时最依赖的东西。

### 处理方式（全部按真实复验，没有为凑门禁改日期）

1. **逐条对照官方页面复验**了全部 37 条过期 offers，其中 **33 条确认无误**、日期刷新为 2026-09-17。
2. **查出 4 条记录与官方页面不符，已更正**——这正是复验的价值：
   - `trae`：原写 "mode-dependent quota"，官方定价页实为「每月 500 积分 / 所有功能均可免费使用 / 2 个云端任务并发」
   - `github-copilot-free`：原写 "50 chat/agent requests per month"，官方页面已不再给出该数字，现按官方口径改为 2,000 completions/月 + 经 AI Credits 计量的有限对话
   - `brave-search-free-credits`：`cardRequired` 原为 "unknown"，官方 FAQ 明确免费档**需要绑卡**（反欺诈），已改为 "yes"
   - `stepfun-limited-time-free`：原模型列表过期（`step-2x-large` 已于 2026-06-12 结束限免），现改为官方在列的 `stepaudio-3-*` 系列
   - `amazon-q-free`：删除无法证实的「25 AWS resource queries/月」，官方页面只写了 50 agentic requests/月
3. **两条顺手补全**（拿到官方原文）：`glm`（非高峰按基础积分 50% 抵扣、高峰为周一至周五 14:00–18:00 UTC+8）、`cohere-trial-key`（trial key 每月 1,000 次调用，chat 20 req/min）。
4. **1 条只做到部分复验并如实标注**：`modelscope-api-inference-free` 的"对注册用户免费"已从官方页面的服务端渲染描述重新确认，但"魔粒分档"和"阿里云实名绑定"写在纯客户端渲染的正文里，现有工具抓不到。该条 `confidence` 已下调为 `medium`，缺口写进 `notes`，**投稿前建议人工在浏览器里过一眼**。
5. **models 的 8 条**通过跑官方同步流水线（`sync_model_catalog.py` 对接当日真实抓取快照）修复，302 条 `lastSeenAt` 重新落章——没有手工改观测日期。

### 顺带确认的两件事

- `site_health.py` 的退出码**确实会失败**（复验前实测 `exit=1`，37 条错误；修复后 `exit=0`）。之前担心的"CI 形同虚设"不存在。
- 提交 `14ac8b4` 同时把 `data/offers.json` 的格式从被误改的 indent=2 还原回仓库约定的 indent=1，diff 从约 9000 行收敛到 134 行。

**仍未解决的**：`awesome-list PR` 依旧受阻（见第 5 节，本机网络到 GitHub 不通）。

---

## 7. 纪律红线（不要做的事）

- ❌ 不买链接、不做批量目录轰炸
- ❌ 不刷 Star / 刷赞 / 刷评论
- ❌ 不代登录、不绕验证码
- ❌ 不把未核验的额度写成确定事实（这会毁掉本站最核心的差异点）
- ❌ 同一篇稿不在同一天投多个平台

---

## 8. 追踪表

发布后请把 URL 回填到 `freellm-submission-posts.md` 第 13 节和 `backlink-forums.md` 第 5 节的提交记录表，避免重复投递。
