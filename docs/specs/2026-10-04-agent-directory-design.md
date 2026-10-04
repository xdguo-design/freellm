# 精选 AI Agent 名录设计

## 目标

将 `/models/` 页面底部的 AI Agent 区从仅展示 5 个免费 Offer 资源，扩展为独立维护的 13 项精选名录。保持现有 FreeLLM 页面风格和响应式卡片样式，使用官方入口与品牌图标回退。

## 方案

采用独立 `data/featured_agents.json` 数据源，不把非优惠型产品伪装成 Offer。继续保留现有 5 个 Offer Agent，并添加 8 个：Pi、Hermes、ChatGPT、Grok、Meta Muse、Agent.Space、Claude Code、OpenCode。Agent.Space 标注为平台；其余条目按通用助手、通用 Agent、编程 Agent、免费资源分类。

每条记录提供稳定 ID、中文和英文名称、厂商、分类、短描述、能力标签、官方 URL、可选 Offer ID。Offer 型条目继续链接站内 Offer 详情；新增目录条目链接其官方产品页面。页头计数、搜索文本和页脚统计均由目录数据生成。

## 页面行为与视觉

- 不改全站菜单、模型区、筛选、导航布局或颜色基调。
- Agent 卡片继续使用 `featured-agent-card` 样式；布局沿用现有五列网格及断点。
- 卡片展示品牌图标、名称、厂商、分类标签、描述、能力标签和“查看详情”链接。
- 对现有 Offer Agent 保留其优惠标签与站内详情链接；新增 Agent 显示通用分类标签并使用官方入口。
- 中英文切换支持新增文案。
- 全局模型搜索可匹配 Agent 名称、厂商、类别、描述和标签。

## 初始目录（13 项）

1. Manus AI（现有 Offer）
2. Xiaomi MiMo Desktop（现有 Offer）
3. CNB（现有 Offer）
4. 讯飞 AStudio（现有 Offer）
5. 腾讯 WorkBuddy（现有 Offer）
6. Pi（通用助手）
7. Hermes（通用 Agent）
8. ChatGPT（通用助手）
9. Grok（通用助手）
10. Meta Muse（通用 Agent）
11. Agent.Space（Agent 平台）
12. Claude Code（编程 Agent）
13. OpenCode（编程 Agent）

## 数据与错误处理

- 构建器校验 JSON 根节点为数组、ID 唯一、名称/类别/描述/URL 非空、URL 为 HTTPS。
- 生成 HTML 时对用户可见数据和属性值进行 HTML 转义。
- 图标请求失败时保留品牌文字回退；外链使用 `target="_blank"` 和 `rel="noopener noreferrer"`。
- 已有 Offer 若目录 ID 对应的记录不存在，页面生成应报出清楚的构建错误，避免静默漏卡。

## 官方入口核验

- Pi：`https://pi.ai/`
- Hermes：`https://hermes-agent.nousresearch.com/docs/`
- ChatGPT：`https://chatgpt.com/`
- Grok：`https://grok.com/`
- Meta Muse：`https://muse.ai/`
- Agent.Space：`https://agent.space/agents`
- Claude Code：`https://claude.ai/code`
- OpenCode：`https://opencode.ai/`

官方产品说明用于核对名称与定位；目录卡片不承诺免费额度或地区可用性，除非现有 Offer 页面已经核实并明确标注。

## 验收标准

1. `/models/` 精选 Agent 区正好显示 13 张卡片，计数和页脚同步显示 13。
2. 现有 5 个 Offer 卡片继续链接到各自站内详情；新增 8 个链接到对应官方入口。
3. 每张卡片有中文品牌回退图标；品牌 favicon 映射指向对应官方域名。
4. 页面中文、英文切换正常，模型搜索能命中新 Agent。
5. 桌面和移动布局无横向溢出，卡片遵从当前断点。
6. 静态构建检查与相关测试通过；页面生成器验证目录结构与关键输出。
