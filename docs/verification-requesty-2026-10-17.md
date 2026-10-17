# Requesty 免费 API：2026-10-17 核验记录

## 核验对象与结论
- 资源：`requesty-free`，关联 13 个免费模型路由；最新正式目录已记录在 `data/offers.json` 和 `data/models.json`。
- 官方来源：[Free Models](https://docs.requesty.ai/features/free-models)，官方文档最后更新于 2026-10-12；列出 13 个免费路由。新组织共享 200 次/天、20 次/分钟，付费组织共享 1,000 次/天、60 次/分钟。
- 已核验的内容：官网来源、模型列表、公开 GET /v1/models 的可访问性、OpenAI 兼容接入地址、免费套餐的公开政策。未以 Requesty API Key 调用 Chat Completion。
- 隐私：平台条款允许部分免费模型数据被保留/训练，必须核对特定模型的 `data_used_for_training` / `data_retention` 标识，禁止把未审计的免费路由用于真实患者资料及其他敏感业务。

## 加精裁决：暂不加精
当前 `freeLLMTest.testLevel=preflight`、`actualUsageVerified=false`。网站 `scripts/mark_featured_offers.py` 要求中国大陆网络预热后 3 次往返实测中位数不高于 400ms 且额度档位达标，并把实测值写入 `endpointCheck.ms`；目录 GET 请求延迟不等于模型推理性能。因此不能因“13 个模型/200 次”就标 `featured`。

## 可复现验证
- 本地数据契约：`python -m unittest tests.test_requesty_catalog -v`
- 公开模型目录：`python scripts/probe_requesty_public.py`（不需要 Key；与站内 13 个 ID 核对，显示训练与数据留存标识；出错返回非零）
- 生成站点：`node scripts/generate_ranking.ts && python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top && python scripts/build_static.py --data data/offers.json --html design/free-china-ai-index.html`
- 真实效果评测仍需用户自行在 Requesty 控制台创建 Key 并在授权且非敏感测试环境执行；至少记录正确答复、成功率、实际额度/429、延迟及长期稳定性。不能录入模拟的速度值。

## 每日发现
`data/daily-log/2026-10-17.json` 新增 1 条 `curatedEvents`，属于 `kind=offer, eventType=new`。不把 13 条模型路由各算一条新资源。该日志由现有静态生成任务同步至 `/logs/`、首页新增口径和 Atom feed。人工事件在同日再次扫描的 `--merge` 中会被保留。
