# GitHub OAuth 登录配置指南

「连接 GitHub 同步」支持两种方式，站点会自动选择：

| 方式 | 说明 | 适用 |
|------|------|------|
| GitHub 登录（OAuth） | 点击「使用 GitHub 登录」跳转 GitHub 授权，回跳后自动完成连接 | 部署在 Vercel（本站主部署） |
| Personal Access Token | 手动粘贴带 `gist` 权限的 PAT | 任何静态镜像站 / OAuth 未配置时自动回退 |

OAuth 模式下用户无需创建任何 Token，全程只授权 `gist` 一个权限。

## 原理

GitHub OAuth 必须用 client secret 换取 access token，secret 不能放进静态前端，
因此由 Vercel Serverless Function 承担换票（`api/gh-oauth.js`）：

```
浏览器 ──跳转──> github.com/login/oauth/authorize?client_id=…&scope=gist&state=…
   <──回跳──     /?code=…&state=…（state 校验防 CSRF）
浏览器 ──POST /api/gh-oauth {code}──> Vercel Function
Vercel Function ──client_id + client_secret + code──> github.com/login/oauth/access_token
   <──{token}── 返回浏览器，存入 localStorage['freellm-gh-token']（与 PAT 方式同一存储）
```

## 配置步骤

1. **创建 GitHub OAuth App**：GitHub → Settings → Developer settings →
   OAuth Apps → New OAuth App
   - Homepage URL：`https://freellm.top`
   - Authorization callback URL：`https://freellm.top/`
2. **记录** Client ID，并生成一个 Client Secret。
3. **配置 Vercel 环境变量**（Project → Settings → Environment Variables）：
   - `GH_OAUTH_CLIENT_ID`
   - `GH_OAUTH_CLIENT_SECRET`
4. **重新部署**（修改环境变量后需 Redeploy 才对 Function 生效）。

完成后所有页面右上角 GitHub 按钮的弹窗即出现「使用 GitHub 登录」。
未配置环境变量时 GET `/api/gh-oauth` 返回 `{clientId: null}`，前端自动隐藏
OAuth 按钮并回退到 PAT 模式，不会报错。

## 本地开发

GitHub 每个 OAuth App 只允许一个 callback 域名。本地调试 OAuth 需另建一个
测试用 OAuth App，callback 填 `http://localhost:3000/`，然后用 Vercel CLI：

```bash
vercel dev            # Function 在本地可用
# 终端里按提示填入 GH_OAUTH_CLIENT_ID / GH_OAUTH_CLIENT_SECRET
```

只调样式 / 同步逻辑时无需 OAuth，`python -m http.server` 下前端会自动走
PAT 回退模式。

## 安全说明

- client secret 仅存在于 Vercel 环境变量，前端与仓库均不包含。
- OAuth scope 只申请 `gist`，无法读写仓库 / 用户邮箱。
- state 参数由前端生成并在 sessionStorage 校验，防 CSRF。
- 换票接口响应 `Cache-Control: no-store`，token 不落缓存。
- token 只保存在用户本机浏览器 localStorage（与原 PAT 方案一致），
  同步直接浏览器 → GitHub API，服务器不经手用户数据。
