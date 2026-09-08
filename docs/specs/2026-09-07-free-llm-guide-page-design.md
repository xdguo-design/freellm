# Free-LLM 中文指南页设计

日期：2026-09-07

## 目标

在 Free AI Index 中增加一个可直接访问、可被搜索引擎抓取的中文指南页，集中展示参考仓库 `nejib1/Free-LLM` 的 README.zh-CN.md 中与免费 LLM API 使用相关的内容，降低用户从首页目录进入 API 配置和本地模型工具的学习成本。

## 页面与入口

- 页面地址：`/guides/free-llm/`
- 首页顶部导航新增“使用指南”链接。
- 页面页脚返回首页，并链接到原始 README 和参考仓库。
- sitemap 增加该页面；页面生成结果纳入现有 SEO 构建与检查流程。

## 内容范围

页面保留 README 的主要阅读路径：

1. 项目定位与为什么需要免费 LLM API。
2. 三步上手：选择提供商、获取 API Key、接入代码。
3. OpenAI 兼容接口的 Python 快速示例。
4. Claude Code、Cursor、Codex CLI 的配置提示。
5. 永久免费额度、可续期额度、一次性试用额度。
6. 本地 / 自托管工具列表。
7. Base URL 与 API Key 速查表。
8. 使用指南、社区贡献和免责声明。

README 中的提供商额度属于外部资料，会在页面显著位置注明抓取/整理来源、原始仓库链接和“使用前以提供商官方页面为准”。不把参考 README 作为本站已核验 Offer 数据，也不覆盖或替代现有 `data/offers.json`。

## 实现边界

- 延续现有静态 HTML 生成器，不引入运行时网络请求或前端框架。
- 指南内容作为生成器中的结构化页面内容维护，避免线上依赖 GitHub 可用性。
- 外部链接只作为用户跳转入口，统一使用新窗口、`noopener` 和明确的官方来源提示。
- 参考仓库采用 MIT License；页面保留来源、版权和 MIT 许可声明。
- 代码示例中的 Key 仅使用占位符，不写入真实凭据。

## SEO 与验证

- 使用独立 canonical：`https://freellm.top/guides/free-llm/`。
- 使用 `Article` 或 `TechArticle` JSON-LD，声明页面名称、描述、来源和修改日期。
- 测试验证页面路径、关键章节、来源/许可证文字、首页导航链接和 sitemap 条目。
- 继续通过现有 `pytest -q` 与 `python scripts/build_static.py --check`。

## 许可与内容风险

参考 README 当前声明 MIT License。MIT 许可声明随页面展示；Provider 的额度、价格、模型名称和商标仍以各 Provider 自己的页面及条款为准。页面不复制参考项目的 Logo、截图或站点品牌，不把社区整理数据包装成本站原创核验结论。
