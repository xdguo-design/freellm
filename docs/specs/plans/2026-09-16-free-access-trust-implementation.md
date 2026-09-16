# FreeLLM 可信首屏与行动闭环实施计划

> **给代理执行者：** 任务使用 - [ ] 勾选跟踪；本计划在当前工作树内执行，不触碰现有未跟踪截图文件。

**目标：** 修复首页 27/43 数据漂移，提供可爬取的 Offer 首屏和正确筛选入口，并打通详情、收藏同步与提交资源入口。

**架构要点：** 静态构建脚本从 data/offers.json 生成首页关键内容；浏览器 JS 继续渐进增强。Offer 详情 URL 使用既有 /offers/{id}/ 规则，提交入口采用静态页面和现有邮箱，不引入后端。

**技术栈：** Python 构建脚本、静态 HTML/CSS/JavaScript、Python unittest。

**关联设计文档：** docs/specs/2026-09-16-free-access-trust-design.md

---

## 文件变更清单

- 新建：docs/specs/2026-09-16-free-access-trust-design.md（设计规格）。
- 新建：docs/specs/plans/2026-09-16-free-access-trust-implementation.md（实施清单）。
- 新建：submit/index.html（提交资源与纠错说明）。
- 修改：scripts/build_static.py（生成首页统计、首屏 Offer 和带 URL 的 JSON-LD）。
- 修改：tests/test_build_static.py（静态构建行为测试）。
- 修改：design/free-china-ai-index.html（移除旧应用、接入动态入口和首页同步）。
- 修改：tests/test_e2e_static.py（更新静态首屏和分类验收）。

## 任务 1：静态构建生成真实首页内容

**涉及文件：** scripts/build_static.py、tests/test_build_static.py。

- [ ] 编写失败测试：断言构建后计数来自数据长度、JSON-LD ListItem 包含 /offers/x/、静态 Offer 链接存在。
- [ ] 运行 python -m unittest tests.test_build_static -v，预期新增断言因现有脚本没有替换 27 和静态 Offer 行而失败。
- [ ] 实现 render_static_catalog(data) 和 replace_static_catalog(html, data)，由构建脚本生成安全转义后的摘要、详情 URL、免费方式和核验日期；同时更新 JSON-LD URL。
- [ ] 运行同一测试命令，预期全部通过。
- [ ] 运行 python scripts/build_static.py，更新首页生成文件。

## 任务 2：首页真实分类、详情入口与同步接入

**涉及文件：** design/free-china-ai-index.html、tests/test_e2e_static.py。

- [ ] 先补静态断言：页面包含 /submit/、/js/freellm-sync.js、Offer 详情 URL 模板、正确分类值，并且旧隐藏 legacy-app 不存在。
- [ ] 运行 python -m unittest tests.test_e2e_static -v，预期新增断言因现有首页仍使用旧锚点、缺少同步脚本和旧应用而失败。
- [ ] 修改首页导航和精选卡片为真实链接；加载同步脚本；删除旧 legacy-app 和不再使用的旧样式；将分类卡片改为 all、api、ide、visual、open_weights、student 等与 JS 逻辑一致的值。
- [ ] 让目录行输出 data-sync="offer"、data-sync-id、data-sync-name、data-sync-url 和 data-sync-star，不改变已有详情抽屉行为。
- [ ] 运行静态测试，预期全部通过。

## 任务 3：提交资源入口

**涉及文件：** submit/index.html、design/free-china-ai-index.html。

- [ ] 编写静态页面测试，断言提交页包含官方链接、免费条件、地区限制、证据说明和联系邮箱。
- [ ] 运行对应测试，预期因页面不存在而失败。
- [ ] 新建提交页，提供字段清单、审核标准、纠错方式和 mailto:xdguo0527@gmail.com 入口；首页按钮改为 /submit/。
- [ ] 运行对应测试，预期通过。

## 任务 4：全量验证

- [ ] 运行 python -m unittest discover -s tests -v，预期既有测试与新增测试全部通过。
- [ ] 运行 python scripts/build_static.py --check，预期输出 current: design\free-china-ai-index.html。
- [ ] 运行 python scripts/build_seo_pages.py --check，预期 SEO 输出为 current。
- [ ] 运行 python scripts/site_health.py，确认页面大小和结构无新增错误；若仅剩 Offer freshness 错误，记录为数据审核待办，不通过修改阈值掩盖。
- [ ] 运行 git diff --check，预期无空白错误。
