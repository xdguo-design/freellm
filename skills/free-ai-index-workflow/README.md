# free-ai-index-workflow

把 Free AI Index 的多个 skill 串成一条可恢复的流水线：同行发现 → 官方核验 → 外部评分/评论搬运 → 视觉原型 → TDD 实现 → 前端审查 → 发布门控。

## 安装

```text
npx skills add <owner>/<repo> --skill free-ai-index-workflow
```

## 触发示例

- `按完整工作流扫描 GitHub 同类产品并核验免费模型`
- `把官方核验、外部平台评分和页面改版串起来`
- `跑完整 Free AI Index research pipeline，但不要自动发布`

工作流会保留中间产物和人工确认点，不会自定义模型评分。
