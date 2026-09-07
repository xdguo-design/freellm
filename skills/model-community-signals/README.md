# model-community-signals

把其他公开平台已有的模型/工具评分、评论、Stars、Likes、Downloads 和排名搬运到 Free AI Index，并保留原始来源。

本 skill 不给模型评分，不跨平台换算，不计算综合分。没有公开评分就显示“暂无公开评分”。

## 安装

```text
npx skills add <owner>/<repo> --skill model-community-signals
```

## 触发示例

- `抓取这个模型在 Hugging Face 的原生评分和评论`
- `给每个模型补充 GitHub Stars、下载量和外部评价`
- `只搬运其他平台评分，不要自己打分`

输出字段包括 `sourcePlatform`、`sourceType`、`sourceUrl`、`rawLabel`、`capturedAt` 和可选评论摘录。
