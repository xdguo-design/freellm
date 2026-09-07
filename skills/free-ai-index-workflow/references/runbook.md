# Free AI Index 工作流运行手册

## 研究和候选

```text
python -m crawler.cli discover --providers data/providers.json --github-peers data/github-peers.json --out data/candidates.json --scan-out data/snapshots/discovery-scan.json --max-links 5 --max-pages 100 --github-max-repositories 20 --github-max-files 80 --timeout 8
```

## 社区快照

先把公开平台原始信号整理为 `data/community-signals.json`，再运行：

```text
python -m crawler.cli signals --input data/community-signals.json --out data/community-signals.json
```

快照必须使用 `sourcePlatform`、`sourceType`、`sourceUrl`、`rawLabel` 和 `capturedAt`；评分不归一化。

## 覆盖和验证

```text
python -m crawler.cli coverage --providers data/providers.json --scan data/snapshots/latest-scan.json --scan data/snapshots/discovery-scan.json --candidates data/candidates.json --out data/coverage.json
python -m unittest discover -s tests -v
python scripts/build_static.py --check
```

## 失败处理

- 网络或平台接口失败：记录 `source_unavailable`，保留旧快照。
- 数据字段不完整：返回 1，不能覆盖旧输出。
- 页面缺社区信号：显示“暂无公开评分”，不插入占位数值。
- 浏览器依赖缺失：记录测试跳过原因；安装或部署前重新执行可用的静态契约测试。
