# 公益与免费 API 导航 /public-api/（2026-10-15）

## 定位
- 参考 HCNSEC（https://link.hcnsec.cn/）的分类与社区发现体验，不抓取镜像、不复制未经核实的投稿内容。
- 本站已有 /links/（友链）和 /guides/getting-started/（教程），本页负责“发现 + 风险分层 + 核验标准”。
- 不是中转商、接口代理或免费额度承诺者。

## 数据事实层
- 唯一资源清单与观察候选：`data/public-api-directory.json`；页面 `public-api/index.html` 是当前的静态可访问展示快照。
- authority=official-site：对应平台官方网站；不自动等于所有套餐免费。
- authority=third-party-directory：仅候选索引，不等于收录站点已核实。
- eligibilityVerified=official_page_only：只确认官方页面展示相关选项，未做实际调用。
- apiProbe=not_performed：目前未测试 API 延迟、token 消耗、模型保真或稳定性。
- reviewedOn 为资料查看日期，不得写成 API 实测日期。

## 维护路径
1. 每次发现新站先填资源登记表或 watchlist，记录站点名称、官方域名、发现来源、采集日期、套餐信息证据。
2. 区分直接公益、免费模型、每日赠额、试用、签到、邀请奖励、需要先充值；充值与邀请返利不得伪装“无门槛免费”。
3. 至少确认 HTTPS/官方域名与服务说明，再核实免费规则、模型 ID、是否要求实名认证、手机号、绑定卡、地区限制、用量重置时间。
4. 如果尚未拿到直连网站/官方文档证据，只放观察名单，不提供不明注册链接。与此处无关的第三方评分不能作为本站评分。
5. 如有实际探针，应记录时间、地域、授权方式、响应码、延迟和请求成本；未配置探针禁止展示可用率数字。
6. 修改数据时同步更新静态页面和 6/2/4/3 的展示计数；移动端检查 360px/768px/桌面宽度、过滤、键盘焦点、无 JS 展示、外链 rel 与内部链接。
7. 如第三方来源失效，记录状态并退回观察队列；不要删除可供审计的历史线索。不要上传任何用户密钥、生产请求或敏感输入。

## 与现有构建的关系
- 本页是独立静态二级页，不参与 `data/offers.json` 的官方资源统计，不把外部导航评分灌入 FreeLLM 排名。
- 首屏主要内容服务器可见；筛选脚本只渐进增强，不依赖外部 API。
- 已加入 `sitemap-pages.xml`、首页热门入口和 /links/ 推荐内容；内部链接扫描包含 `public-api`。

- HCNSEC 同时注册进 `data/third-party-discovery-sources.json`（`enabled=false`）；现有官方模型目录抓取不应将社区投稿当成已验证模型记录。

## 后续任务（未完成）
- 通过受控人工审核单建立候选升级流程；自动采集只入审核队列，不自动公开。
- 在具备可用授权、地区节点、最小成本控制和安全审计后，加入真正的 API 探针。
- 后续英文版上线之前不设置虚假的 /en/public-api/ hreflang。

## 2026-10-15 第二轮：自主编辑评价
- 自有资料评分：公开证据 35%、免费条款 30%、接入便利 20%、隐私控制 15%，每项 0–5 整数；score = evidence×7 + terms×6 + access×4 + privacy×3。评分为编辑判断，不是 uptime、模型真实性或业务安全认证。
- 六份评测数据维护于 `data/public-api-directory.json` 的 `review` 字段。对应 `/public-api/reviews/<id>/` 可索引的静态详情页，并提供原始证据、已知事实、未知事项、验证步骤、适用场景、扣分原因。
- 2026 年 10 月 15 日核对官方价格页：OpenRouter Free 每日 50 requests（不能写成每模型 50 次）；Cloudflare Workers AI 每日 10,000 Neurons，00:00 UTC 重置，部分模型需要 Paid 或预付积分。
- ModelScope 社区 2024-12 提到每日 2000 请求，属于历史政策，不作为当前保证；SiliconFlow 当前可读入口是登录页，具体免费额度仍 UNKNOWN。
- HCNSEC 和 qiaoliang 两家导航站的编辑分仅反映可公开核对的资料质量，不能等同于被收录每家中转的可靠性。社区星级仅为外部信号，不进入 FreeLLM 分数。
- 单个用户真实密钥不能发给本站或提交到 GitHub。没有执行带密钥的 API 探针；未测数据必须保留 UNKNOWN。
- 更新数据后运行 `node scripts/build_public_api_reviews.cjs`，再运行 `node scripts/build_public_api_reviews.cjs --check`，保证卡片和详情页同步。最后跑 `python scripts/check_internal_links.py` 和 `pytest -q tests/test_public_api_directory.py`。

## 2026-10-15 二级页面治理追加
- `scripts/build_seo_pages.py` 的 `public_api_review_urls()` 从审核登记 JSON 动态获取合法 slug，防止下次 SEO build 抹去详情页的 sitemap 条目。
- `/community/` 和 `/submit/` 采用共享的 Aurora 二级页面主题，加入自主评测纠错入口、证据等级及脱敏说明。
- 静态 `sitemap-pages.xml` 已包含 6 个实际存在的详细评测页；新增资源经人工验收后运行 `node scripts/build_public_api_reviews.cjs` 和原有 sitemap 生成脚本。

## HCNSEC 自营网关故障排查
- 本站 `link.hcnsec.cn` 与运营方的 `api.hcnsec.cn` 分开描述。仅依据运营方公开文档，记录 Base URL `https://api.hcnsec.cn/v1`、POST 路径、auto 分组、模型别名以及 401/403/429 的优先排查方向。
- 网关公开宣称的上游数量、模型名称、长期免费和不用于训练等均是站方声明，不是独立审计结论。不要将用户 API Key 交给我们。

## 2026-10-15 第三轮：独立登记已实测网关
- 划分 `hcnsec` 公益导航与 `hcnsec-gateway` 真正 API 服务两个独立实体；后者属于第三方 API 中转，不能被标记为官方模型供应商。
- 用户表示自己已经真实成功调用，登记在 `data/public-api-observations.json`，时间为反馈入库日，实际调用时间与模型未提供，默认不加入成功率分母/分子。
- 自主编辑资料评分 68/100；它独立于用户确认可用。网关按站方文档提供 Python 无敏感内容示例，公开免费/SVIP 区分；任何密钥不得入仓库、记录或提交到 ChatGPT。

## 2026-10-15 发布门禁 SEO 摘要修复
- 所有公开审核详情页的 meta description 从原始评测事实构造；模板和 7 个静态页同步生成，控制在 70–170 字，不虚构实测质量。
- 同批修复 85 个此前在仓库内已经存在、且曾被 SEO 审计指出摘要过短的 Skills 详情页：保留原有用途描述，补充使用限制和核验提醒，保持页面身份不变。
- 不下调 scripts/audit_seo_metadata.py 的硬门槛。定期生成新的 Skill 详情页时仍须通过 metadata 审计。
