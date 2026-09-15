# FreeLLM 全站用户配置同步（favorites / history / settings）

纯前端实现：localStorage 即时生效 + GitHub Gist 云端同步，无需任何后台服务。

## 架构

```
/js/freellm-sync.js     ← 站点级同步模块（唯一需要引入的文件）
/js/freellm-data.js     ← 站点级数据层（汇率/节假日/农历，Actions 定时更新）
/tools/data/*.json      ← 数据文件（GitHub Actions 每日提交刷新）
/favorites/             ← 「我的收藏」页（全站收藏 + 浏览历史汇总）
```

存储位置：

| 内容 | 本机 | 云端 |
|------|------|------|
| 收藏 | `localStorage['freellm-favorites']` | 私有 Gist `freellm-config.json` |
| 浏览历史 | `localStorage['freellm-history']`（上限 100 条） | 同上 |
| 设置（主题/语言等） | `localStorage['freellm-settings']` | 同上 |
| GitHub Token | `localStorage['freellm-gh-token']` | **绝不上传** |
| Gist ID | `localStorage['freellm-gh-gist']` | — |

数据格式（Gist 内 `freellm-config.json`）：

```json
{
  "version": 2,
  "updatedAt": 1760000000000,
  "favorites": [{ "type": "model", "id": "groq", "name": "Groq", "url": "/models/groq/", "ts": 1760000000000 }],
  "history":  [{ "type": "tool",  "id": "base64", "name": "Base64 编解码", "url": "/tools/?tool=base64", "ts": 1760000000000 }],
  "settings": { "theme": "dark", "locale": "zh-CN" }
}
```

`type` 约定：`model` / `provider` / `skill` / `tool` / `guide` / `page`（新页面可自行扩展）。

## 页面接入（零逻辑成本）

在任意页面引入一次：

```html
<script src="/js/freellm-sync.js"></script>
```

然后给卡片加 `data-` 属性即可：

```html
<!-- 只记录浏览历史 -->
<a href="/models/groq/" data-sync
   data-sync-type="model" data-sync-id="groq"
   data-sync-name="Groq" data-sync-url="/models/groq/">Groq</a>

<!-- 历史 + ★ 收藏按钮（自动注入右上角） -->
<a href="/skills/pdf/" data-sync data-sync-star
   data-sync-type="skill" data-sync-id="pdf"
   data-sync-name="PDF 处理" data-sync-url="/skills/pdf/">PDF 处理</a>

<!-- GitHub 认证按钮（可选；用户已登录时自动显示用户名） -->
<button id="fl-sync-auth" hidden>GitHub</button>
```

模块会自动：迁移旧 `freellm-theme` / `free-ai-index-locale` 设置、应用主题、绑定认证按钮、（有 Token 时）拉取云端合并。

动态渲染的卡片：渲染完成后调用一次 `FreeLLM.Sync.bind(container)`。

## JS API

```js
const S = FreeLLM.Sync;

S.toggleFav({ type:'model', id:'groq', name:'Groq', url:'/models/groq/' }) // → true=已收藏
S.isFav('model', 'groq')
S.favs() / S.favs('tool')        // 收藏列表（可按类型过滤）
S.removeFav('model','groq') / S.clearFavs()

S.track({ type:'page', id:'about', name:'关于', url:'/about/' })  // 记录历史
S.hist() / S.clearHist()

S.getSetting('theme') / S.setSetting('theme','dark')  // 写入同时兼容旧键
S.on('fav'|'hist'|'set'|'auth'|'*', fn)

S.hasToken() / S.setToken(pat) / S.getUser()
S.pushNow() / S.pullNow()          // 手动推送/拉取
S.toast('已收藏')
S.bind(rootElement)                // 绑定动态卡片
```

## 合并策略（多设备）

- **收藏**：按 `type+id` 并集，`ts` 新者胜
- **历史**：按 `type+id` 去重，最新在前，上限 100 条
- **设置**：远端按键覆盖本地
- Token 存本机 localStorage，不参与同步；Gist 为用户名下私有 Gist，站点方无法读取

## 数据自动更新（GitHub Actions）

`.github/workflows/update-tools-data.yml` 每日 UTC 00:20 拉取汇率写入 `tools/data/exchange.json` 并提交。前端读取顺序：

1. `localStorage` 缓存（汇率 6h / 节假日 30d）
2. 同源静态文件 `/tools/data/*.json`（Actions 维护）
3. 汇率直连 `open.er-api.com` 兜底

新增数据源：在 `freellm-data.js` 加 fetcher → 需要定时更新的在 workflow 里加一步生成对应 JSON。

## 安全边界

- Token 只存本机；请求直接从浏览器发往 `api.github.com`，无中间服务器
- Gist 是 **secret gist**（不公开列出，但知道 ID 者可读），勿在收藏里存敏感内容
- 若需更强隐私，可后续把存储换成用户自有私有 Repo（API 相同，改用 `/repos/.../contents` 即可）
