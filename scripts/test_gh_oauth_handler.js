// api/gh-oauth.js 的本地单元测试（Node 直接运行，不依赖 Vercel）：
//   node scripts/test_gh_oauth_handler.js
// 覆盖：GET 返回 clientId / 未配置报错 / 正常换票 / GitHub 拒绝 / 缺 code。
'use strict';
const path = require('path');
const assert = require('assert');

const handler = require(path.join(__dirname, '..', 'api', 'gh-oauth.js'));

function mockRes() {
  return {
    statusCode: 0,
    headers: {},
    body: null,
    setHeader(k, v) { this.headers[k] = v; },
    end(payload) { this.body = payload; },
    json() { throw new Error('should not use res.json'); },
  };
}

function mockReq(method, body) {
  return {
    method,
    on(event, cb) {
      if (event === 'data' && body != null) process.nextTick(() => cb(body));
      if (event === 'end') process.nextTick(cb);
    },
    destroy() {},
  };
}

async function run(env, req, res) {
  const old = { id: process.env.GH_OAUTH_CLIENT_ID, secret: process.env.GH_OAUTH_CLIENT_SECRET };
  // process.env 只接受字符串：undefined 必须用 delete，否则会变成 "undefined"
  if (env.id === undefined) delete process.env.GH_OAUTH_CLIENT_ID; else process.env.GH_OAUTH_CLIENT_ID = env.id;
  if (env.secret === undefined) delete process.env.GH_OAUTH_CLIENT_SECRET; else process.env.GH_OAUTH_CLIENT_SECRET = env.secret;
  try {
    await handler(req, res);
  } finally {
    if (old.id === undefined) delete process.env.GH_OAUTH_CLIENT_ID; else process.env.GH_OAUTH_CLIENT_ID = old.id;
    if (old.secret === undefined) delete process.env.GH_OAUTH_CLIENT_SECRET; else process.env.GH_OAUTH_CLIENT_SECRET = old.secret;
  }
}

async function main() {
  // 1. GET：已配置 → 返回 clientId
  let res = mockRes();
  await run({ id: 'Iv1.123', secret: 'sec' }, mockReq('GET'), res);
  assert.strictEqual(res.statusCode, 200);
  assert.deepStrictEqual(JSON.parse(res.body), { clientId: 'Iv1.123' });
  console.log('✓ GET 返回 clientId');

  // 2. GET：未配置 → clientId 为 null（前端据此回退 PAT 模式）
  res = mockRes();
  await run({ id: undefined, secret: undefined }, mockReq('GET'), res);
  assert.strictEqual(res.statusCode, 200);
  assert.deepStrictEqual(JSON.parse(res.body), { clientId: null });
  console.log('✓ GET 未配置返回 null');

  // 3. POST 未配置 → 500 带错误信息
  res = mockRes();
  await run({ id: undefined, secret: undefined }, mockReq('POST', '{"code":"c"}'), res);
  assert.strictEqual(res.statusCode, 500);
  assert.ok(JSON.parse(res.body).error.includes('GH_OAUTH_CLIENT_ID'));
  console.log('✓ POST 未配置报 500');

  // 4. POST 正常换票：向 GitHub 提交 client_id/secret/code，透传 token
  let captured = null;
  global.fetch = async (url, opts) => {
    captured = { url, body: JSON.parse(opts.body), headers: opts.headers };
    return { json: async () => ({ access_token: 'gho_OK', scope: 'gist' }) };
  };
  res = mockRes();
  await run({ id: 'Iv1.123', secret: 'sec' }, mockReq('POST', '{"code":"abc"}'), res);
  assert.strictEqual(res.statusCode, 200);
  assert.deepStrictEqual(JSON.parse(res.body), { token: 'gho_OK', scope: 'gist' });
  assert.strictEqual(captured.url, 'https://github.com/login/oauth/access_token');
  assert.deepStrictEqual(captured.body, { client_id: 'Iv1.123', client_secret: 'sec', code: 'abc' });
  assert.strictEqual(captured.headers.Accept, 'application/json');
  assert.strictEqual(res.headers['Cache-Control'], 'no-store');
  console.log('✓ POST 换票成功且请求参数正确');

  // 5. GitHub 拒绝（错误码透传）
  global.fetch = async () => ({ json: async () => ({ error: 'bad_verification_code', error_description: 'The code passed is incorrect.' }) });
  res = mockRes();
  await run({ id: 'Iv1.123', secret: 'sec' }, mockReq('POST', '{"code":"bad"}'), res);
  assert.strictEqual(res.statusCode, 502);
  assert.ok(JSON.parse(res.body).error.includes('incorrect'));
  console.log('✓ GitHub 拒绝时透传错误');

  // 6. 缺 code → 400
  res = mockRes();
  await run({ id: 'Iv1.123', secret: 'sec' }, mockReq('POST', '{}'), res);
  assert.strictEqual(res.statusCode, 400);
  console.log('✓ 缺 code 返回 400');

  // 7. 不支持的 метод → 405
  res = mockRes();
  await run({ id: 'Iv1.123', secret: 'sec' }, mockReq('DELETE'), res);
  assert.strictEqual(res.statusCode, 405);
  console.log('✓ 非法方法返回 405');

  console.log('\n全部通过');
}

main().catch((e) => { console.error(e); process.exit(1); });
