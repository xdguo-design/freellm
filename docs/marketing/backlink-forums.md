# FreeLLM 论坛外链渠道清单

更新时间：2026-09-13

定位：补充 `freellm-submission-posts.md`（产品目录/发布平台）之外的**论坛与社区**渠道。
外链目标：freellm.top 获得更多可被抓取的引用、品牌提及和导入流量。

> 注意：整理当日网络受限，未能逐一核实各站当前注册政策与链接属性；
> 每个渠道动手前先花 2 分钟确认注册方式和版规。所有平台遵守同一底线：
> 不批量复制相同内容、不刷赞、不买链接，先参与再分享。

## 0. 优先级总览

| 优先级 | 平台 | 类型 | 链接属性（预期） | 适配角度 |
|---|---|---|---|---|
| A | Linux.do | 中文论坛（Discourse） | 高信任等级后去 nofollow | 资源荟萃/开发调优板块分享 |
| A | 小众软件论坛 meta.appinn.net | 中文论坛（Discourse） | 宽松，工具分享友好 | 发现频道分享索引站 |
| A | 知乎 | 中文问答 | nofollow，但页面自带排名 | 回答"免费 AI API/学生优惠"类问题 |
| A | 掘金 / SegmentFault / 博客园 | 中文技术社区 | 多 nofollow，文章本身可排名 | guides/ 9 篇指南改写发布 |
| A | Reddit（r/SideProject 等） | 英文论坛 | nofollow，Google 直接索引内容 | Show 项目、InternetIsBeautiful |
| A | Hacker News Show HN | 英文论坛 | 低分 nofollow，**上分后变 follow** | 已备稿（见 submission 文档第 8 节） |
| B | NodeSeek | 中文论坛 | 待核实 | 资源分享/AI 板块 |
| B | HostLoc | 中文论坛 | 待核实 | AI 讨论区资源帖 |
| B | Indie Hackers | 英文社区 | nofollow 为主 | Build in public（每日核验日志角度） |
| B | dev.to / Hashnode / HackerNoon | 英文文章平台 | 多 nofollow，平台权重高 | guides 英文版投稿 |
| B | Software Recommendations SE / Quora | 英文问答 | nofollow，搜索排名好 | 回答"free LLM API"类问题 |
| C | 即刻 / 酷安 / 电鸭 | 中文社区 | 无直接 SEO 价值，导流 | 产品动态、学生优惠角度 |
| C | 少数派 / Bilibili 专栏 | 中文内容平台 | nofollow | 深度文章、选购指南 |
| C | 友情链接互换 | 中文站传统 | follow，可控性最高 | 新增 /links/ 页面与同类站互换 |

## 1. A 级渠道详情

### 1.1 Linux.do（最优先）

- 入口：https://linux.do/
- 相关板块：开发调优、资源荟萃、福利羊毛（以站内实际版面为准）
- 门槛：邀请码/信任等级制；新账号发外链受限，Discourse 对低信任等级自动 nofollow，养到中高信任等级后链接才被抓取
- 发帖角度：复用 submission 文档第 3 节的 V2EX「分享创造」稿（去掉 V2EX 特定称呼），强调"每条记录有官方入口 + 核验日期"这个差异点
- 注意：先正常参与讨论 1–2 周再发分享帖；同一篇稿不要和 V2EX 同天发

### 1.2 小众软件论坛（meta.appinn.net）

- 入口：https://meta.appinn.net/
- 性质：Discourse 论坛，定位就是"发现、分享小众好用的工具和网站"，对资源索引站极友好
- 发帖角度：按"发现频道"格式分享：一句话定位 + 解决什么问题 + 截图；appinn 主站也有投稿/爆料入口，可双通道
- 门槛：注册开放（以站内当前政策为准）

### 1.3 知乎

- 做法：不发明新问题，搜索现有高流量问题（"有哪些免费的 AI API""学生有哪些 AI 优惠""免费 GPT/Claude 替代"），在 2–3 个问题下写结构化回答，文末自然带 freellm.top 对应栏目页（如 /offers/student/）
- 链接属性：nofollow，且未白名单域名可能加跳转；但知乎回答本身参与搜索排名，是"站外内容锚点"而不是纯外链
- 素材：guides/ 下 9 篇指南直接改写，一篇指南拆一个回答，不要一篇回答塞全部链接

### 1.4 掘金 / SegmentFault 思否 / 博客园

- 做法：把 guides/ 指南（free-llm、free-ai-coding-tools、china-free-ai-api 等）改写成社区文章，一文一平台首发，间隔发布，文内 1–2 条官网链接
- 顺序建议：先 SegmentFault 或博客园（对个人博客/外链最宽松），再掘金（流量大但社区编辑推荐机制更挑剔）
- 收益：这些平台域名权重高，文章页本身能排到"免费 AI API"相关关键词，间接为 freellm.top 导流

### 1.5 Reddit

- 目标版：r/SideProject（发项目首选）、r/InternetIsBeautiful（工具站尝鲜）、r/ArtificialInteligence；r/LocalLLaMA 仅在讨论开源权重话题时自然提及，先读版规
- 学生优惠角度：r/college、r/csMajors 有 self-promo 限制，只在新帖求"学生优惠"的问题下评论提及，不发主帖
- 链接属性：Reddit 出站链接 nofollow，但 Google 大量索引 Reddit 内容，曝光和点击真实存在
- 门槛：账号需要 karma 养号，新号发链接易被自动过滤

### 1.6 Hacker News（Show HN）

- 稿子已备好：submission 文档第 8 节
- 补充 SEO 价值：HN 对低分新帖加 nofollow，**帖子得分上升后会移除 nofollow**，是少数能拿到真正 follow 外链的论坛
- 时机：选北美上午发；准备好在评论区回答数据模型和核验流程问题

## 2. B 级渠道要点

- **NodeSeek**（https://www.nodeseek.com/）：VPS/资源社区，AI 与资源分享讨论活跃；注册政策需核实（历史上有邀请/开放交替）。角度：资源分享帖，附核验表格截图。
- **HostLoc**（https://hostloc.com/）：老牌主机论坛，有 AI 相关讨论区；用户偏 VPS 玩家，"免费 API + 自部署"角度契合。
- **Indie Hackers**（https://www.indiehackers.com/）：写 "I verify free AI offers daily" 的 build-in-public 帖，直接引用 logs/ 每日更新页作为内容差异化——这是别的目录站没有的故事。
- **dev.to / Hashnode / HackerNoon**：guides/ 英文化投稿；dev.to 可用 canonical 指向原站（如果将来在 freellm.top 发博客）；HackerNoon 走编辑审核，接受后链接权重尚可。
- **Software Recommendations Stack Exchange / Quora**：搜"free LLM API recommendation"类问题，按"列 3–5 个选项 + 各自限制"格式回答，freellm.top 作为汇总入口放最后。

## 3. C 级渠道要点（曝光优先，SEO 价值低）

- 即刻（"一起做产品"圈子）、酷安（效率区）、电鸭社区：发产品动态，重导流轻 SEO。
- 少数派：投稿"免费 AI 资源避坑指南"类深度稿，审核通过后曝光稳定。
- Bilibili 专栏/视频简介：适合把核验流程做成内容。
- Telegram/微信 AI 资源频道：无 SEO 价值，但"白嫖 AI"类 TG 频道投稿导流直接。

## 4. 站内配套动作（影响外链转化）

1. **新增友链页**（/links/）：中文站传统外链手段，follow 且完全可控；找同类独立工具站/导航站互换，先上线页面再去谈。
2. **每篇社区文章的落地页要对应**：不要所有渠道都指首页；学生优惠角度指 /offers/student/、API 角度指 /category/api/、每日核验故事指 /logs/——深链比首页链接更自然，也更相关。
3. **补齐 logs 页和 2 个 longcat offer 页的 og/twitter 标签**：社交渠道点开分享卡片时保持一致形象（另案处理）。

## 5. 提交记录

| 平台 | 日期 | 帖子/回答 URL | 状态 | 备注 |
|---|---|---|---|---|
| Linux.do | — | — | 未提交 | 需先注册养号 |
| meta.appinn.net | — | — | 未提交 | — |
| 知乎 | — | — | 未提交 | — |
| SegmentFault/博客园 | — | — | 未提交 | — |
| 掘金 | — | — | 未提交 | — |
| Reddit | — | — | 未提交 | 需养号 |
| Hacker News | — | — | 未提交 | 稿已备 |
| NodeSeek | — | — | 未提交 | 注册政策待核实 |
| HostLoc | — | — | 未提交 | 注册政策待核实 |
| Indie Hackers | — | — | 未提交 | — |
| dev.to | — | — | 未提交 | — |
| 友链页 | — | — | 未上线 | 站内前置任务 |
