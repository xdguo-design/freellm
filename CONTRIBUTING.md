# 贡献指南 / Contributing

感谢你愿意帮 FreeLLM 变得更好。这个项目最需要的是**数据纠错**，而不是代码。

Thanks for helping FreeLLM. The most valuable contribution here is **data correction**, not code.

---

## 最快的贡献方式：报告数据问题

发现下面任何情况，直接开一个 [Issue](https://github.com/xdguo-design/freellm/issues)，或发邮件到 xdguo0527@gmail.com：

- 某个免费额度已经失效、缩水或改成收费
- 注册要求写错了（比如实际需要绑卡 / 需要教育认证）
- 地区限制写错了
- 官方入口链接 404 或跳转到别的产品
- 模型已经下线、改名或被合并

**请附上官方证据链接**（厂商定价页、文档或公告）。我们只接受能用官方来源复核的修改——这是本站的核心原则。

## 提交新资源

新增一条免费资源时，请尽量提供以下信息：

| 字段 | 说明 |
|---|---|
| 官方入口 | 厂商官网 / 定价页 / 文档 URL |
| 免费机制 | 每月额度 / 一次性试用 / 限时活动 / 学生优惠 / 开放权重 |
| 具体额度 | 数字，例如 `500 credits / month`、`1M tokens / day` |
| 是否需要绑卡 | yes / no / unknown |
| 是否需要手机号 | yes / no / unknown |
| 地区限制 | 全球 / 中国大陆 / 需要特定地区 |
| 有效期 | 长期 / 截止日期 / 每月重置 |
| 核验日期 | 你确认这条信息的日期 |

**不要提交未经官方确认的额度数字。** 如果官方页面没有写明，就标 `unknown`，不要推测。

## 开发贡献

### 环境

```bash
git clone https://github.com/xdguo-design/freellm.git
cd freellm
python -m http.server 8000      # 本地预览
```

### 修改数据后必须重跑构建

数据（`data/*.json`）改动后，静态页面需要重新生成：

```bash
python scripts/build_seo_pages.py --data data/offers.json --output . --site-url https://freellm.top
python scripts/build_static.py
```

### 提交前自检

```bash
python scripts/build_static.py --check        # 首页是否最新
python scripts/build_seo_pages.py --check     # SEO 页面是否最新
python scripts/site_health.py                 # 站点健康
pytest -q                                     # 单元测试
```

四项都通过再提 PR。

### 数据字段约定

- 条目稳定键用 `id`，不要改已发布条目的 `id`（会破坏日志的历史对比）
- 新增条目必须带 `sourceUrls` 和 `lastVerifiedAt`
- `status` 只填 `verified` / `candidate` / `retired`，未核验的一律 `candidate`
- 免费机制用 `freeMechanism` 字段，不要塞进描述文案里

## 提交 PR

1. 一个 PR 只做一件事（修一个数据错误 / 加一条资源 / 修一个 bug）
2. PR 描述里写清楚**改了什么**和**证据链接**
3. 不要在同一批里混入格式化或无关重构

## 行为底线

- 不提交付费收录、付费排名或软文
- 不刷 Star、不刷 Issue、不制造虚假评价
- 引用他人数据请注明来源

---

本项目以 [MIT（代码）+ CC BY 4.0（内容与数据）](LICENSE) 授权。
