# 原型语言路由实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 为单页原型加入英文默认、地址语言参数、浏览器语言兜底和可记忆的中英文切换。

**架构要点：** 在现有单 HTML 原型中增加小型 locale 字典和 `resolveLocale`/`applyLocale` 边界，不引入框架或外部翻译服务。URL 参数优先于路径、本地选择和浏览器语言；动态数据继续来自 `data/offers.json`。

**技术栈：** 原生 HTML/CSS/JavaScript，Python `unittest` 静态契约测试，`python -m crawler.cli validate data/offers.json`，`python scripts/build_static.py --check`。

**关联设计文档：** `docs/specs/2026-09-07-locale-routing-design.md`

---

### 任务 1：建立语言解析与翻译契约

**涉及文件：**
- 修改：`tests/test_e2e_static.py`
- 修改：`design/free-china-ai-index.html`

- [ ] **步骤 1：编写失败测试**

在 `StaticContractTests` 增加断言，要求页面包含 `SUPPORTED_LOCALES`、`resolveLocale`、`applyLocale`、`data-i18n`、`data-locale-toggle`、`free-ai-index-locale` 和 `?lang=` 处理字符串。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_e2e_static.StaticContractTests.test_page_has_locale_routing_hooks -v`

预期：失败，原因是当前 HTML 没有语言解析函数和语言切换节点。

- [ ] **步骤 3：最小实现**

在主原型 header 增加语言按钮，在固定界面节点添加 `data-i18n` 或 `data-i18n-aria-label`，在主脚本中加入 `SUPPORTED_LOCALES`、URL/path/browser/localStorage 解析和翻译字典。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_e2e_static.StaticContractTests.test_page_has_locale_routing_hooks -v`

预期：通过。

### 任务 2：接入固定界面翻译与语言切换

**涉及文件：**
- 修改：`design/free-china-ai-index.html`
- 测试：`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

增加静态断言，要求存在英文默认文案、中文文案、`document.documentElement.lang` 更新、`URLSearchParams` 更新以及保留 hash 的 `history.replaceState`。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_e2e_static.StaticContractTests.test_locale_switch_updates_url_and_document_language -v`

预期：失败，原因是现有页面只有中文固定文案且没有切换逻辑。

- [ ] **步骤 3：最小实现**

实现 `applyLocale(locale)`：批量更新 `[data-i18n]` 文本、placeholder、aria-label、`<html lang>`、语言按钮状态和固定结果提示；实现切换按钮在 `en` 与 `zh-CN` 间切换并用 `history.replaceState` 更新 `lang` 参数，保留当前 hash、搜索和筛选 DOM 状态。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_e2e_static.StaticContractTests.test_locale_switch_updates_url_and_document_language -v`

预期：通过。

### 任务 3：动态文本、浏览器验证与回归检查

**涉及文件：**
- 修改：`design/free-china-ai-index.html`
- 修改：`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

增加浏览器可执行时的行为测试，覆盖 `?lang=zh-CN`、`?lang=en`、页面默认英文和语言按钮点击后的 `lang` 属性/URL；Playwright 不可用时保持现有跳过策略。

- [ ] **步骤 2：运行测试确认失败**

运行：`python -m unittest tests.test_e2e_static.BrowserPageTests -v`

预期：在实现完成前，语言属性或 URL 断言失败；若本机没有 Playwright Chromium，则显示既有的可解释跳过信息。

- [ ] **步骤 3：最小实现**

在 `loadOffers()` 完成后调用 locale-aware 的固定结果渲染；将排序选项、空状态、详情抽屉固定标签和本地时钟前缀接入同一字典，数据卡片仍保留原始数据内容。

- [ ] **步骤 4：运行完整验证**

依次运行：

```powershell
python -m unittest discover -s tests -v
python -m crawler.cli validate data/offers.json
python scripts/build_static.py --check
git diff --check
```

预期：所有可运行测试通过，数据报告 `valid: 27 offers`，构建报告当前 HTML，diff 检查无错误。

- [ ] **步骤 5：浏览器验收**

打开以下地址并核对 `<html lang>`、导航、按钮和地址栏：

```text
http://localhost:4173/design/free-china-ai-index.html
http://localhost:4173/design/free-china-ai-index.html?lang=zh-CN
http://localhost:4173/design/free-china-ai-index.html?lang=en
```

预期：无参数为英文，`zh-CN` 为中文，`en` 为英文；点击语言按钮只更新 `lang` 参数，不丢失当前 hash、搜索和筛选状态。
