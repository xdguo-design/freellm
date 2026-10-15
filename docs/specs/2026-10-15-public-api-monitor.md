# 公益 API 可用性证据探针与聚合机制（2026-10-15）

## 分层证据（严格隔离）
1. DOCUMENT：官网或文档 HTTP 200 且符合内容指纹。证明文档可读，**不证明 API 可用**。
2. USER_CONFIRMED：用户主动反馈真实成功调用；本期入库 1 条 HCNSEC 反馈，实际调用日期、模型 ID、HTTP 日志和延迟未知，不能参与成功率指标。
3. AUTHENTICATED_SUCCESS：仅在拥有仓库独立秘钥 `HCNSEC_API_KEY` 的受控 CI 中，使用固定域名的 OpenAI 格式最小对话，HTTP 200 且有效 JSON 回复才算一个成功样本。
4. MEASURED_WINDOW：至少 20 个鉴权调用样本，覆盖 3 个不同 UTC 日期，最近一次不超过 72 小时，才展示该观测窗口成功率与 P50/P95；绝不当作服务 SLA 或上游真实性认证。
5. 未提供凭证时，只运行无凭证文档检查；不会替用户登录、读出密钥或绕过鉴权。

## 安全与成本
- 目标固定为 https://api.hcnsec.cn/free-api/ 和 https://api.hcnsec.cn/v1/chat/completions。禁止任意 URL，以免 SSRF / Key 外传。
- 网关的令牌只从 CI Secret `HCNSEC_API_KEY` 读取，不写入文件、日志、配置或 artifacts；重定向拒绝跟随。
- 模型固定使用站方文档的免费层 `DeepSeek-V4-Pro`，单次调用 `max_tokens=8`、非流式、合成提示词“只回复 OK”；实际是否扣额以平台当日规则为准。
- 结果只写 schema、响应状态、耗时、模型别名和有限元信息，不记录完整请求、返回内容或异常文本。
- 定时 GitHub Actions 每 6 小时一次，上传保留 90 天的脱敏结果文件。不自动更改 `main`/`dev` 或公开分数。
- 未安装 Secret 也能定期检查文档，生成 `USER_CONFIRMED` 级证据评估，**不生成伪造成功率**。
- 工作流每次输出本次证据与评估；90 天 artifact 用于后续跨批次归档，不能把单次工作流的聚合文件误认成 90 天统计。

## 本地与 CI
```bash
python -m unittest tests.test_public_api_probe -v
python scripts/probe_public_api.py --mode documentation --output .tmp/public-api/reports/docs.json
python scripts/evaluate_public_api.py --observations data/public-api-observations.json --reports-dir .tmp/public-api/reports --output .tmp/public-api/evaluation.json
node scripts/build_public_api_reviews.cjs --check
```

有授权、且明确允许真实调用时：
```bash
# 在本地安全环境中设置 HCNSEC_API_KEY，不提交密钥；本命令会产生至多一次真实 API 调用
python scripts/probe_public_api.py --mode authenticated_chat --output .tmp/public-api/reports/auth.json
```

## 待提升
- 未来从 90 天 artifact 历史合并连续样本，并建立地理节点间隔、滑动窗口与状态降级提示。
- 站点公开数据升级必须人工审核，不允许有一个成功样本就刷新“稳定可用”标记。

## 90 天运行证据留存与近况复评
- GitHub Actions 以 `public-api-evidence-<run id>` 留存 90 天产物，不写入 dev/main。最近最多 40 份 artifact 的脱敏鉴权结果通过 `scripts/restore_public_api_history.py` 读取后交由 evaluator 合并。
- GitHub REST 访问令牌只发送给 api.github.com；归档重定向会切换为无 Authorization 的独立 HTTPS 请求。归档中只提取 reports/auth.json 的白名单字段，不写原始 ZIP 和其他文件。
- 定时 workflow 仅在合并到 GitHub 仓库默认分支后自动按计划运行；目前 dev 上新配置不等于定时任务已经启用。

## 2026-10-15 AdSense / GSC 门禁修正
- 公益目录与 7 个索引内的原创评测页面挂载与现有 `ads.txt` 匹配的 AdSense loader，不填虚构广告位 ID。
- GSC 预算以根 `sitemap.xml` 实际引用的五个已发布子站点地图计算，而不是 glob 误包含 `sitemap-skills.xml`（99 个不在根 sitemap 索引中的候选快照）。
- 当前批准的总量 230（pages=58, offers=78, providers=50, models=35, english=9）。新增页面须再次审核，不能绕过预算阈值。
