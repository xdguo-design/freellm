# 外部信号来源策略

## 允许记录的原始信号

| sourceType | 含义 | 例子 | 不能写成 |
|---|---|---|---|
| `rating` | 平台明确评分 | `4.3 / 5` | 综合质量分 |
| `review` | 公开评论短摘录 | 一句体验反馈 | 官方承诺 |
| `stars` | GitHub Stars | `2.1K Stars` | 模型评分 |
| `likes` | Likes/收藏 | `1.2K likes` | 用户满意度总分 |
| `downloads` | 下载或使用次数 | `12.4K downloads` | 能力排名 |
| `rank` | 平台原生排名 | `#18` | 全网排名 |
| `sentiment` | 来源明确的情绪统计 | `positive 72%` | 本站判断 |

## 来源要求

- 公开 HTTPS 页面或公开 API，保存直接原文 URL。
- 平台名称、模型/产品标识和版本必须能够对应；同名模型不能凭名称猜测。
- 原始分数保留原尺度；`4.3 / 5` 不改成 `86 / 100`。
- 评论只引用必要短摘录，附平台和链接；不复制全文、作者个人资料或私信。
- 页面无法稳定读取、接口需要登录或平台规则不清楚时，停止抓取并记为 `needs_review`。
- 响应内容限量读取；不得执行脚本、安装依赖、绕过访问控制或使用用户账号。

## 最低字段

```text
offerId
sourcePlatform
sourceType
sourceUrl
rawLabel
capturedAt
status
```

评分额外保留 `value`、`scaleMax`、`sampleCount`；评论额外保留 `excerpt`。`Stars`、`Downloads` 等数量保留原平台标签，不能塞进 `rating`。
