// GitHub OAuth 换票端点（Vercel Serverless Function）。
// 前端 freellm-sync.js 通过它完成 OAuth 登录：
//   GET  /api/gh-oauth          -> { clientId }  供前端构造授权跳转（client_id 本身是公开的）
//   POST /api/gh-oauth { code } -> { token }     用 client_secret 向 GitHub 换 access token
// secret 只存在于 Vercel 环境变量，配置步骤见 docs/github-oauth.md。

const GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token';

function json(res, status, payload) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(payload));
}

function readBody(req, limit = 4096) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > limit) {
        reject(new Error('body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

module.exports = async function handler(req, res) {
  const clientId = process.env.GH_OAUTH_CLIENT_ID;
  const clientSecret = process.env.GH_OAUTH_CLIENT_SECRET;

  if (req.method === 'GET') {
    return json(res, 200, { clientId: clientId || null });
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    return json(res, 405, { error: 'method not allowed' });
  }

  if (!clientId || !clientSecret) {
    return json(res, 500, { error: 'OAuth 未配置：缺少 GH_OAUTH_CLIENT_ID / GH_OAUTH_CLIENT_SECRET 环境变量' });
  }

  let code = '';
  try {
    const body = await readBody(req);
    code = String(JSON.parse(body || '{}').code || '').trim();
  } catch (error) {
    return json(res, 400, { error: '请求体无效' });
  }
  if (!code) {
    return json(res, 400, { error: '缺少 code 参数' });
  }

  try {
    const response = await fetch(GITHUB_TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code }),
    });
    const data = await response.json();
    if (data && data.access_token) {
      return json(res, 200, { token: data.access_token, scope: data.scope || 'gist' });
    }
    return json(res, 502, { error: (data && (data.error_description || data.error)) || 'GitHub 换票失败' });
  } catch (error) {
    return json(res, 502, { error: '请求 GitHub 失败' });
  }
};
