# AdSense 验证与 IDE 数据刷新实施计划

> **给代理执行者：** 推荐配合 `subagent-driven-development（子代理驱动开发）`（每任务独立子代理 + 两阶段审查）或在本会话内按勾选逐步执行并在批次节点与用户确认。任务使用 `- [ ]` 勾选跟踪。

**目标：** 将 AdSense 验证脚本加入线上页面，并重新部署当前 8 个免费 IDE 数据版本。

**架构要点：** 页面入口由 `vercel.json` 重写到 `design/free-china-ai-index.html`；页面运行时从 `/data/offers.json` 加载数据并按 `ide` 类型动态计算 IDE 数量。验证脚本只放在 HTML `<head>`，不改变业务渲染逻辑。

**技术栈：** 静态 HTML/CSS/JavaScript、JSON、Vercel CLI、pytest。

**关联设计文档：** `docs/specs/2026-09-06-free-ai-index-app-and-crawler-design.md`

---

### 任务 1：加入 AdSense 验证脚本

**涉及文件：**
- 修改：`design/free-china-ai-index.html` 的 `<head>` 区域
- 测试：`tests/test_e2e_static.py`

- [ ] **步骤 1：编写失败测试**

在静态页面测试中断言 `<head>` 包含指定的 AdSense 脚本地址、发布者 ID 和 `crossorigin="anonymous"`。

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_e2e_static.py -q`

预期：新增 AdSense 断言失败，因为当前页面尚未包含验证脚本。

- [ ] **步骤 3：最小实现**

在 `design/free-china-ai-index.html` 的 `</head>` 前加入：

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2461062743308239"
        crossorigin="anonymous"></script>
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_e2e_static.py -q`

预期：静态页面测试通过。

### 任务 2：确认 8 个 IDE 数据并重新部署

**涉及文件：**
- 使用：`data/offers.json`
- 使用：`vercel.json`
- 测试：`tests/test_e2e_static.py`、线上页面检查

- [ ] **步骤 1：验证本地数据**

运行：`python -c "import json; d=json.load(open('data/offers.json', encoding='utf-8')); print(len(d), sum('ide' in x.get('type', []) or 'free_ide' in x.get('type', []) for x in d))"`

预期：输出 `27 8`。

- [ ] **步骤 2：运行完整相关测试**

运行：`pytest tests/test_schema.py tests/test_build_static.py tests/test_e2e_static.py -q`

预期：全部通过。

- [ ] **步骤 3：部署当前项目**

运行：`npx --yes vercel@latest --prod --yes --scope team_vxXPzKYZu8PbnXEii3JUcm97`

预期：Vercel 返回生产部署成功并给出部署 URL。

- [ ] **步骤 4：验证线上结果**

检查 `https://freellm.top/` 和 `https://www.freellm.top/`：

1. 页面按钮包含 `Browse all 8 free IDEs`；
2. 页面 HTML 包含 `ca-pub-2461062743308239`；
3. `/data/offers.json` 返回 27 条数据，其中 8 条带 `ide` 或 `free_ide` 类型；
4. 两个 HTTPS 地址返回成功响应。

- [ ] **步骤 5：记录变更**

运行：`git diff --check` 和 `git status --short`，确认没有空白错误或无关改动。
