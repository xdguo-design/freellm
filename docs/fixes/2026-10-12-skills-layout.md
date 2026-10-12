# Skills 卡片布局修复（2026-10-12）

## 1. 问题拆解

目标：恢复 `/skills/` 的卡片文字宽度、卡片高度和列表视图。
约束：保持现有静态站点与卡片结构；HTML 从生成器输出；仅修改 Skills 页面相关规则。
假设：线上采用 `origin/main` 的分类精选版本。已用线上响应、源码和浏览器截图确认。

已复现的失败场景及防护：

- 新增精选标签和解析区自动落入 46px 图标列，卡片高达约 1936px：两个块明确跨越全部列。
- 分类网格的 ID 选择器覆盖列表视图规则：为同一 ID 的列表状态声明单列。
- 手机列表的三列结构压缩正文、解析区溢出：700px 以下恢复双列标题，正文及元信息跨列。

## 2. 路径对比与选择

保留网格并补齐跨列规则：改动小，现有图标、标题与桌面列表位置保持可用。
改成纵向 Flex：需要重新实现标题图标排列和列表规则，增加影响范围。
选择第一种，不增加依赖。

## 3. 对抗性验证

浏览器实际检查 1366、889、390px × 网格/列表共六组；断言解析区宽度超过卡片的 75%、
正文超过 50%、解析区不超出卡片、精选标签不竖排、卡片高度低于 900px、列表占满容器、页面不横向溢出。
相同断言已加入 `tests/test_e2e_static.py`，用于以后检测重新出现的样式覆盖问题。

## 4. 代码与配置

- `css/aurora-skills.css`：跨列和列表断点修复，以及 SVG 图标样式。
- `js/reference-shell.js`：按具体 Skill 用途选 SVG 图形，以 Skill ID 生成稳定配色；卡片和详情共用同一图标。
- `scripts/build_seo_pages.py`：样式和脚本版本改为 `20261012-icons1`，刷新缓存。
- `skills/index.html`：通过生成器生成。
- `workflow/index.html`：通过同一生成器同步到数据源中的 15 条配方。
- `tests/test_e2e_static.py`：渲染几何回归检查。
- `tests/test_site_visual_system.py`：对应样式版本约束。

复用现有 README、静态服务、依赖、`.gitignore` 和 CI。纯 CSS 修复不需要环境变量、密钥、
新的依赖声明或 Docker 配置；数据、权限和用户输入处理没有变化。

## 5. 运行与验证

在修复工作目录运行：

```powershell
python scripts/serve_local.py --port 8902
python -m unittest tests.test_skills_page tests.test_site_visual_system -q
python -m unittest tests.test_e2e_static.BrowserPageTests.test_skills_editorial_blocks_use_card_width_in_both_views -v
python scripts/build_static.py --check
python scripts/build_seo_pages.py --check
New-Item -ItemType Directory -Force -Path '.tmp/model-audit' | Out-Null
python scripts/build_model_catalog.py --sources data/official-model-sources.json --curated data/models-curated.json --models-out .tmp/model-audit/fresh-models.json --providers-out .tmp/model-audit/fresh-providers.json --health-out .tmp/model-audit/model-source-health.json --date 2026-10-12 --timeout 20
python scripts/site_health.py --model-observation .tmp/model-audit/model-source-health.json
python scripts/check_adsense.py
python -m pytest -q --capture=no -p no:cacheprovider --junit-xml=.tmp-skills-layout-junit.xml
```

预览：`http://127.0.0.1:8902/skills/?category=development#skill-grid`。
部署沿用 README 中的 Vercel 流程，发布后核对样式与脚本 URL 为 `20261012-icons1`，重复六组渲染检查。

## 6. 已知限制

全量页面测试 663 passed、3 skipped，JUnit failures/errors 均为 0。
`build_static.py --check`、SEO 514 页一致性、AdSense 检查和 `site_health.py` 均退出成功。
站点健康结果保留 77 条旧 offer/model 新鲜度提示；模型源观测由 6 个启用源生成，0 个来源失败。
没有修改旧资源核验日期，也没有伪造模型来源证据。

## 图标重复修复补充

旧实现只用八张分类截图切片，同类的多个 Skill 使用相同图案。新增的回归检查先复现失败，再验证 SVG 替换。
曾考虑按来源仓库使用头像，但同一仓库包含多个 Skill，仍会重复，且依赖图片网络请求。
最终选择本地 SVG：编程分类分别显示羽毛、虫子、原子、魔杖、审查清单与连接器等用途图形。

防护与验证：

- 外部图片服务不可达：图标完全在本地渲染，不依赖远端图片或图标字体。
- 新 Skill 没有专用映射：使用现有用途/分类匹配作为图形回退，配色仍以 ID 为准。
- 搜索、排序或刷新改变视觉身份：配色按 ID 计算，浏览器检查刷新后保持一致。
- 详情与卡片显示不同图标：两处共用 SVG 和配色函数，回归检查图形及实际计算颜色一致。

当前 98 项目录的图形与计算颜色组合无重复；卡片与详情图形及颜色一致。
最终全量测试是在 Skills 与 Workflow 页面生成完成后运行，结果为 663 passed、3 skipped。

```powershell
node --check js/reference-shell.js
python -m unittest tests.test_e2e_static.BrowserPageTests.test_skills_have_distinct_local_icons_and_matching_detail_icon tests.test_e2e_static.BrowserPageTests.test_skills_editorial_blocks_use_card_width_in_both_views tests.test_e2e_static.BrowserPageTests.test_skills_curated_topics_and_icon_diversity tests.test_skills_page tests.test_site_visual_system -q
```
