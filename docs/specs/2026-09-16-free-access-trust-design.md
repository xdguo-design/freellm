# FreeLLM 免费资源可信首屏与行动闭环设计

**目标**：让首页静态内容、浏览器动态内容和数据源保持一致，并把用户从筛选结果可靠地引导到 Offer 详情、官方入口、收藏或提交纠错。

**本轮范围**：

- 首页静态计数、首屏 Offer、ItemList JSON-LD 与当前 data/offers.json 一致；
- 清理首页隐藏旧应用，降低重复 HTML；
- 将分类和筛选字段改为真实可操作且语义一致；
- 首页卡片链接到已有 Offer 详情页；
- 首页加载收藏同步能力；
- 增加静态提交/纠错入口，复用现有联系渠道；
- 为构建逻辑补充行为测试。

**非目标**：在线 Playground、账号系统、付费会员、后端提交 API、广告位扩张、模型数据源重构。

## 方案

采用静态优先、渐进增强方案。scripts/build_static.py 在构建时从 Offer 数据生成计数、首屏静态行和 JSON-LD；浏览器加载后继续使用同一份嵌入 JSON 完成搜索、筛选和详情抽屉。筛选状态写入 URL，保证结果可分享。Offer 详情页仍由既有 SEO 生成器负责，首页只负责正确链接和快速入口。

统一的首页分类维度为：

- 免费方式：permanent、credits、trial、download、payg；
- 产品类型：api、ide、desktop_ai_app、free_ide、open_weights、web_infrastructure；
- 能力与地区继续从 Offer 数据中读取，未具备字段时不伪造标签。

过期核验字段本轮不修改历史数据，只把首页文案改为“官方来源检查/人工核验日期”所需的可扩展结构，并保留后续数据字段兼容性。

## 可观察行为

- 构建后首页中的资源数量等于数据数组长度；
- 构建后静态 JSON-LD 的每个 ListItem 包含对应 Offer 详情 URL；
- 构建后首页首屏包含可爬取的 Offer 链接；
- 分类名称与筛选值一致，不能把 API 显示成 credits 或把图像视频显示成 web infrastructure；
- 首页“提交资源”链接指向真实提交说明页；
- 首页 Offer 行包含同步脚本所需的 data-sync 属性和收藏按钮标识。

## 错误处理与兼容性

- 数据为空时构建失败，不生成虚假的数量；
- Offer 缺少详情页 ID 时构建失败；
- JS 加载失败时，静态首屏仍可读、可点击；
- URL 筛选参数无效时忽略该参数并回退到全部资源；
- 现有旧链接和现有详情页 URL 不改变。

## 测试策略

- Python 单元测试覆盖静态构建：计数替换、详情 URL、首屏链接、空数据/缺少 ID 错误；
- 现有静态页面测试继续验证导航、分类、Offer 数据和响应式页面；
- 运行 python -m unittest discover -s tests -v、python scripts/build_static.py --check、python scripts/build_seo_pages.py --check；
- 最后运行 python scripts/site_health.py，将剩余失败区分为代码回归和既有数据新鲜度问题。
