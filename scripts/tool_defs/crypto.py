# -*- coding: utf-8 -*-
"""安全加密类工具定义"""
from .registry import d

X509_JS = r'''
function _der(u8) {
  var p = 0;
  function tv() {
    if (p >= u8.length) return null;
    var tag = u8[p++];
    var len = u8[p++];
    if (len & 0x80) {
      var n = len & 0x7f; len = 0;
      for (var i = 0; i < n; i++) len = len * 256 + u8[p++];
    }
    var start = p; p += len;
    return { tag: tag, start: start, len: len, end: p };
  }
  function children(t) {
    var save = p, out = [];
    p = t.start;
    while (p < t.end) { var c = tv(); if (!c) break; out.push(c); }
    p = save;
    return out;
  }
  function oid(t) {
    var b = u8.subarray(t.start, t.end);
    var s = Math.floor(b[0] / 40) + '.' + (b[0] % 40);
    var val = 0;
    for (var i = 1; i < b.length; i++) {
      val = val * 128 + (b[i] & 0x7f);
      if (!(b[i] & 0x80)) { s += '.' + val; val = 0; }
    }
    return s;
  }
  function str(t) { return new TextDecoder().decode(u8.subarray(t.start, t.end)); }
  function int(t) {
    var b = u8.subarray(t.start, t.end), v = 0;
    for (var i = 0; i < b.length; i++) v = v * 256 + b[i];
    return v;
  }
  function time(t) {
    var s = str(t);
    if (s.endsWith('Z')) s = s.slice(0, -1);
    if (t.tag === 23) return '20' + s.slice(0, 2) + '-' + s.slice(2, 4) + '-' + s.slice(4, 6) + ' ' + s.slice(6, 8) + ':' + s.slice(8, 10) + ':' + (s.slice(10, 12) || '00');
    return s.slice(0, 4) + '-' + s.slice(4, 6) + '-' + s.slice(6, 8) + ' ' + s.slice(8, 10) + ':' + s.slice(10, 12) + ':' + (s.slice(12, 14) || '00');
  }
  function name(t) {
    var parts = [];
    var NAMES = { '2.5.4.3': 'CN', '2.5.4.6': 'C', '2.5.4.7': 'L', '2.5.4.8': 'ST', '2.5.4.10': 'O', '2.5.4.11': 'OU', '2.5.4.5': 'serialNumber', '1.2.840.113549.1.9.1': 'email' };
    children(t).forEach(function (set) {
      children(set).forEach(function (attr) {
        var f = children(attr);
        var o = oid(f[0]);
        parts.push((NAMES[o] || o) + '=' + str(f[1]));
      });
    });
    return parts.join(', ');
  }
  return { tv: tv, children: children, oid: oid, str: str, int: int, time: time, name: name };
}
function _pemToDer(pem) {
  var b64 = pem.replace(/-----(BEGIN|END)[^-]+-----/g, '').replace(/\s+/g, '');
  return T.b64ToBytes(b64);
}
function _parseX509(pem) {
  var u8 = _pemToDer(pem);
  var D = _der(u8);
  var cert = D.tv();
  var f = D.children(cert);
  var tbs = D.children(f[0]);
  var i = 0, version = 1;
  if (tbs[0].tag === 0xA0) { version = D.int(D.children(tbs[0])[0]) + 1; i = 1; }
  var serialT = tbs[i + 1];
  var serial = T.bytesToHex(u8.subarray(serialT.start, serialT.end));
  if (serial.length > 40) serial = serial.slice(0, 40) + '…';
  var ALGS = { '1.2.840.113549.1.1.5': 'SHA1 + RSA', '1.2.840.113549.1.1.11': 'SHA256 + RSA', '1.2.840.113549.1.1.12': 'SHA384 + RSA', '1.2.840.113549.1.1.13': 'SHA512 + RSA', '1.2.840.10045.4.3.2': 'SHA256 + ECDSA', '1.2.840.10045.4.3.3': 'SHA384 + ECDSA', '1.2.840.10045.4.3.4': 'SHA512 + ECDSA' };
  var sigAlg = ALGS[D.oid(tbs[i + 2])] || D.oid(tbs[i + 2]);
  var issuer = D.name(tbs[i + 3]);
  var validity = D.children(tbs[i + 4]);
  var subject = D.name(tbs[i + 5]);
  var spki = D.children(tbs[i + 6]);
  var pkAlgOid = D.oid(spki[0]);
  var pkAlg = ({ '1.2.840.113549.1.1.1': 'RSA', '1.2.840.10045.2.1': 'EC' })[pkAlgOid] || pkAlgOid;
  var keyBits = '';
  if (pkAlg === 'RSA') {
    var pk = D.children(spki[1]);
    var ints = D.children(pk[1]);
    keyBits = (ints[0].len - 1) * 8 + ' bit';
  } else if (pkAlg === 'EC') {
    var ecParams = D.children(spki[0])[1];
    var ECURVES = { '1.2.840.10045.3.1.7': 'P-256', '1.3.132.0.34': 'P-384', '1.3.132.0.35': 'P-521' };
    keyBits = ECURVES[D.oid(ecParams)] || D.str(ecParams);
  }
  var notBefore = D.time(validity[0]), notAfter = D.time(validity[1]);
  var expired = new Date(notAfter.replace(' ', 'T') + 'Z') < new Date();
  return { version: version, serial: serial, sigAlg: sigAlg, issuer: issuer, subject: subject,
    notBefore: notBefore, notAfter: notAfter, expired: expired, pkAlg: pkAlg, keyBits: keyBits };
}
'''

d('rsa', 'RSA 密钥生成', '生成 RSA-2048 / 4096 公私钥对，输出 PEM（SPKI / PKCS#8）', js=r'''
var bits = T.select([{value:'2048',label:'RSA-2048'},{value:'4096',label:'RSA-4096'}],'2048');
var pubOut = T.out('公钥 PEM…');
var privOut = T.out('私钥 PEM（PKCS#8）…');
function toPem(b64, label) {
  return '-----BEGIN ' + label + '-----\n' + b64.match(/.{1,64}/g).join('\n') + '\n-----END ' + label + '-----';
}
app.appendChild(T.pane([T.field('公钥 (SPKI)', pubOut), T.field('私钥 (PKCS#8)', privOut)]));
app.appendChild(T.row([T.el('span', { text: '密钥长度' }), bits,
  T.button('生成密钥对', function () {
    T.toast('生成中，' + bits.value + ' 位可能需要数秒…');
    crypto.subtle.generateKey(
      { name: 'RSA-OAEP', modulusLength: +bits.value, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
      true, ['encrypt', 'decrypt']).then(function (kp) {
      return Promise.all([
        crypto.subtle.exportKey('spki', kp.publicKey),
        crypto.subtle.exportKey('pkcs8', kp.privateKey)
      ]);
    }).then(function (keys) {
      pubOut.value = toPem(T.bytesToB64(keys[0]), 'PUBLIC KEY');
      privOut.value = toPem(T.bytesToB64(keys[1]), 'PRIVATE KEY');
      T.toast('生成完成');
    }).catch(function (e) { T.toast('生成失败：' + e.message); });
  }, true),
  T.button('复制公钥', function () { T.copy(pubOut.value); }),
  T.button('下载私钥 .pem', function () { T.download('rsa-private.pem', privOut.value); })]));
''')

d('rsa-encrypt', 'RSA 加解密', 'RSA-OAEP 公钥加密 / 私钥解密，密钥支持粘贴 PEM', js=r'''
function _pemToDer(pem) {
  var b64 = pem.replace(/-----(BEGIN|END)[^-]+-----/g, '').replace(/\s+/g, '');
  return T.b64ToBytes(b64);
}
var input = T.textarea('输入明文…');
var output = T.out('输出…');
var mode = T.select([{value:'enc',label:'公钥加密'},{value:'dec',label:'私钥解密'}],'enc');
var keyText = T.textarea('粘贴 PEM 密钥（加密用公钥，解密用私钥）…', true);
keyText.setAttribute('rows', '5');
async function run() {
  if (!input.value || !keyText.value) { output.value = ''; return; }
  try {
    if (mode.value === 'enc') {
      var pub = await crypto.subtle.importKey('spki', _pemToDer(keyText.value), { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['encrypt']);
      var ct = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, pub, T.textToBytes(input.value));
      output.value = T.bytesToB64(ct);
    } else {
      var priv = await crypto.subtle.importKey('pkcs8', _pemToDer(keyText.value), { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['decrypt']);
      var pt = await crypto.subtle.decrypt({ name: 'RSA-OAEP' }, priv, T.b64ToBytes(input.value.trim()));
      output.value = T.bytesToText(new Uint8Array(pt));
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
app.appendChild(T.pane([T.field(mode.value === 'enc' ? '明文' : '密文 (Base64)', input), T.field('结果', output)]));
app.appendChild(T.field('密钥 (PEM)', keyText));
app.appendChild(T.row([mode, T.button('执行', run, true),
  T.el('span', { text: 'RSA-OAEP + SHA-256 · 2048 位密钥最多加密 190 字节明文' })]));
''')

d('ecc', 'ECC 密钥生成', '生成 ECDSA P-256 / P-384 / P-521 椭圆曲线密钥对（PEM）', js=r'''
var curve = T.select([{value:'P-256',label:'P-256 (secp256r1)'},{value:'P-384',label:'P-384'},{value:'P-521',label:'P-521'}],'P-256');
var pubOut = T.out('公钥 PEM…');
var privOut = T.out('私钥 PEM…');
function toPem(b64, label) {
  return '-----BEGIN ' + label + '-----\n' + b64.match(/.{1,64}/g).join('\n') + '\n-----END ' + label + '-----';
}
app.appendChild(T.pane([T.field('公钥 (SPKI)', pubOut), T.field('私钥 (PKCS#8)', privOut)]));
app.appendChild(T.row([T.el('span', { text: '曲线' }), curve,
  T.button('生成密钥对', function () {
    crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: curve.value }, true, ['sign', 'verify'])
      .then(function (kp) {
        return Promise.all([
          crypto.subtle.exportKey('spki', kp.publicKey),
          crypto.subtle.exportKey('pkcs8', kp.privateKey)
        ]);
      }).then(function (keys) {
        pubOut.value = toPem(T.bytesToB64(keys[0]), 'PUBLIC KEY');
        privOut.value = toPem(T.bytesToB64(keys[1]), 'PRIVATE KEY');
        T.toast('生成完成');
      }).catch(function (e) { T.toast('失败：' + e.message); });
  }, true),
  T.button('复制公钥', function () { T.copy(pubOut.value); }),
  T.button('下载私钥 .pem', function () { T.download('ecc-private.pem', privOut.value); })]));
''')

d('hybrid-encrypt', '混合加密', 'RSA-OAEP 包裹 AES-256-GCM 密钥，兼顾安全与大文件效率', js=r'''
function _pemToDer(pem) {
  var b64 = pem.replace(/-----(BEGIN|END)[^-]+-----/g, '').replace(/\s+/g, '');
  return T.b64ToBytes(b64);
}
var input = T.textarea('输入明文（长度不限）…');
var output = T.out('输出（JSON 包裹，含被加密的 AES 密钥）…');
var mode = T.select([{value:'enc',label:'加密（用对方公钥）'},{value:'dec',label:'解密（用自己私钥）'}],'enc');
var keyText = T.textarea('粘贴 PEM 密钥…', true);
keyText.setAttribute('rows', '5');
async function run() {
  if (!input.value || !keyText.value) { output.value = ''; return; }
  try {
    if (mode.value === 'enc') {
      var pub = await crypto.subtle.importKey('spki', _pemToDer(keyText.value), { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['encrypt']);
      var aesKey = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt']);
      var iv = crypto.getRandomValues(new Uint8Array(12));
      var ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, aesKey, T.textToBytes(input.value)));
      var rawKey = await crypto.subtle.exportKey('raw', aesKey);
      var wrapped = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, pub, rawKey);
      output.value = JSON.stringify({ v: 1, alg: 'RSA-OAEP-256 + AES-256-GCM', iv: T.bytesToB64(iv), key: T.bytesToB64(new Uint8Array(wrapped)), data: T.bytesToB64(ct) }, null, 2);
    } else {
      var bundle = T.parseJSON(input.value);
      var priv = await crypto.subtle.importKey('pkcs8', _pemToDer(keyText.value), { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['decrypt']);
      var rawKey2 = await crypto.subtle.decrypt({ name: 'RSA-OAEP' }, priv, T.b64ToBytes(bundle.key));
      var aesKey2 = await crypto.subtle.importKey('raw', rawKey2, { name: 'AES-GCM' }, false, ['decrypt']);
      var pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: T.b64ToBytes(bundle.iv) }, aesKey2, T.b64ToBytes(bundle.data));
      output.value = T.bytesToText(new Uint8Array(pt));
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
app.appendChild(T.pane([T.field(mode.value === 'enc' ? '明文' : '密文 JSON', input), T.field('结果', output)]));
app.appendChild(T.field('密钥 (PEM)', keyText));
app.appendChild(T.row([mode, T.button('执行', run, true)]));
''')

d('jwt', 'JWT 编解码', '解析 JWT Header / Payload，HS256 支持签名校验', js=r'''
var input = T.textarea('粘贴 JWT（eyJhbGciOi…）…');
var info = T.el('div', { class: 'pane single' });
var secret = T.input('', { placeholder: 'HS256 校验密钥（可选）', class: 'grow mono' });
var verdict = T.badge('—');
function b64url(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return T.bytesToText(T.b64ToBytes(s));
}
function show() {
  T.clearEl(info);
  verdict.textContent = '—';
  var parts = input.value.trim().split('.');
  if (parts.length < 2) return;
  try {
    var header = T.parseJSON(b64url(parts[0]));
    var payload = T.parseJSON(b64url(parts[1]));
    var fmt = function (obj) {
      var o = T.out(''); o.value = JSON.stringify(obj, null, 2); return o;
    };
    var payloadShow = Object.assign({}, payload);
    ['exp', 'iat', 'nbf'].forEach(function (k) {
      if (payloadShow[k]) payloadShow[k + '_readable'] = new Date(payloadShow[k] * 1000).toLocaleString('zh-CN');
    });
    if (payload.exp) {
      if (payload.exp * 1000 < Date.now()) { verdict.textContent = '⚠ Token 已过期'; verdict.className = 'badge warn'; }
      else { verdict.textContent = '✓ 未过期（至 ' + new Date(payload.exp * 1000).toLocaleString('zh-CN') + '）'; verdict.className = 'badge ok'; }
    }
    info.appendChild(T.field('Header', fmt(header)));
    info.appendChild(T.field('Payload', fmt(payloadShow)));
    if (parts[2]) info.appendChild(T.field('Signature (base64url)', fmt({ signature: parts[2] })));
  } catch (e) {
    info.appendChild(T.msg('⚠ JWT 解析失败：' + e.message, 'err'));
  }
}
input.addEventListener('input', T.debounce(show, 250));
app.appendChild(T.pane([T.field('JWT', input)], true));
app.appendChild(T.row([T.el('span', { text: 'HS256 密钥' }), secret,
  T.button('校验签名', function () {
    var parts = input.value.trim().split('.');
    if (parts.length < 3 || !secret.value) { T.toast('需要完整 JWT 与密钥'); return; }
    crypto.subtle.importKey('raw', T.textToBytes(secret.value), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
      .then(function (k) { return crypto.subtle.sign('HMAC', k, T.textToBytes(parts[0] + '.' + parts[1])); })
      .then(function (sig) {
        var expect = T.bytesToB64(sig).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
        if (expect === parts[2]) { verdict.textContent = '✓ 签名校验通过'; verdict.className = 'badge ok'; }
        else { verdict.textContent = '✗ 签名不匹配'; verdict.className = 'badge warn'; }
      });
  }), verdict]));
app.appendChild(info);
show();
''')

d('totp', '一次性密码 TOTP', 'RFC 6238 动态口令，兼容 Google Authenticator（Base32 密钥）', js=r'''
var secret = T.input('JBSWY3DPEHPK3PXP', { class: 'grow mono', spellcheck: 'false' });
var digits = T.select([{value:'6',label:'6 位'},{value:'8',label:'8 位'}],'6');
var code = T.el('span', { class: 'stat' }, [T.el('b', { text: '———' }), T.el('span', { text: '刷新倒计时' })]);
var bar = T.el('div', { style: 'height:4px;background:var(--line);border-radius:2px;overflow:hidden;flex:1' });
var fill = T.el('div', { style: 'height:100%;background:var(--accent);width:100%' });
bar.appendChild(fill);
async function totp(now) {
  var key = LC.b32decode(secret.value);
  var counter = Math.floor(now / 30000);
  var msg = new Uint8Array(8);
  for (var i = 7; i >= 0; i--) { msg[i] = counter & 255; counter = Math.floor(counter / 256); }
  var k = await crypto.subtle.importKey('raw', key, { name: 'HMAC', hash: 'SHA-1' }, false, ['sign']);
  var mac = new Uint8Array(await crypto.subtle.sign('HMAC', k, msg));
  var off = mac[mac.length - 1] & 0xf;
  var bin = ((mac[off] & 0x7f) << 24) | (mac[off + 1] << 16) | (mac[off + 2] << 8) | mac[off + 3];
  return String(bin % Math.pow(10, +digits.value)).padStart(+digits.value, '0');
}
async function tick() {
  var now = Date.now();
  if (!secret.value.trim()) return;
  try {
    var c = await totp(now);
    code.firstChild.textContent = c;
    var remain = 30 - (now / 1000) % 30;
    fill.style.width = (remain / 30 * 100) + '%';
    fill.style.background = remain < 5 ? 'var(--err)' : 'var(--accent)';
  } catch (e) { code.firstChild.textContent = '密钥格式错误'; }
}
setInterval(tick, 1000);
app.appendChild(T.row([T.el('span', { text: 'Base32 密钥' }), secret,
  T.el('span', { text: '位数' }), digits]));
app.appendChild(T.row([code]));
app.appendChild(T.row([bar]));
tick();
T.button('复制当前验证码', function () { T.copy(code.firstChild.textContent); }, true);
app.appendChild(T.row([T.button('复制当前验证码', function () { T.copy(code.firstChild.textContent); }, true),
  T.el('span', { text: 'SHA-1 · 30 秒步长 · RFC 6238' })]));
''')

d('x509', 'X.509 证书解析', '解析 SSL/TLS 证书：主体、签发者、有效期、算法、密钥长度', js=X509_JS + r'''
var input = T.textarea('粘贴 PEM 证书（-----BEGIN CERTIFICATE-----…）…', true);
input.setAttribute('rows', '6');
var info = T.el('div', { class: 'pane single' });
function show() {
  T.clearEl(info);
  if (!input.value.includes('BEGIN CERTIFICATE')) return;
  try {
    var c = _parseX509(input.value);
    info.appendChild(T.kvTable([
      ['版本', 'v' + c.version],
      ['序列号', c.serial],
      ['签名算法', c.sigAlg],
      ['主体 Subject', c.subject],
      ['签发者 Issuer', c.issuer],
      ['生效时间', c.notBefore + ' UTC'],
      ['过期时间', c.notAfter + ' UTC' + (c.expired ? '（已过期 ⚠）' : '（有效 ✓）')],
      ['公钥算法', c.pkAlg + ' · ' + c.keyBits]
    ]));
  } catch (e) {
    info.appendChild(T.msg('⚠ 证书解析失败：' + e.message, 'err'));
  }
}
input.addEventListener('input', T.debounce(show, 300));
app.appendChild(T.pane([T.field('证书 (PEM)', input)], true));
app.appendChild(info);
show();
''')

d('ssh-key', 'SSH 密钥生成', '生成 RSA SSH 密钥对：OpenSSH 格式公钥 + PEM 私钥', js=r'''
var bits = T.select([{value:'2048',label:'RSA-2048'},{value:'4096',label:'RSA-4096'}],'2048');
var comment = T.input('user@host', { class: 'grow mono' });
var pubOut = T.out('OpenSSH 公钥…');
var privOut = T.out('PEM 私钥…');
function toPem(b64, label) {
  return '-----BEGIN ' + label + '-----\n' + b64.match(/.{1,64}/g).join('\n') + '\n-----END ' + label + '-----';
}
function sshString(bytes) {
  return new Uint8Array([0, 0, 0, bytes.length].concat(Array.from(bytes)));
}
function u32(n) {
  return new Uint8Array([(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255]);
}
function concat(arrs) {
  var len = arrs.reduce(function (s, a) { return s + a.length; }, 0);
  var out = new Uint8Array(len), off = 0;
  arrs.forEach(function (a) { out.set(a, off); off += a.length; });
  return out;
}
app.appendChild(T.pane([T.field('OpenSSH 公钥（authorized_keys 可直接使用）', pubOut), T.field('私钥 (PEM，保存为 id_rsa)', privOut)]));
app.appendChild(T.row([T.el('span', { text: '长度' }), bits, T.el('span', { text: '备注' }), comment,
  T.button('生成', function () {
    crypto.subtle.generateKey(
      { name: 'RSA-OAEP', modulusLength: +bits.value, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
      true, ['encrypt', 'decrypt']).then(function (kp) {
      return Promise.all([
        crypto.subtle.exportKey('spki', kp.publicKey),
        crypto.subtle.exportKey('pkcs8', kp.privateKey)
      ]);
    }).then(function (keys) {
      privOut.value = toPem(T.bytesToB64(keys[1]), 'PRIVATE KEY');
      var D = (function (u8) {
        var p = 0;
        function tv() {
          var tag = u8[p++], len = u8[p++];
          if (len & 0x80) { var n = len & 0x7f; len = 0; for (var i = 0; i < n; i++) len = len * 256 + u8[p++]; }
          var s = p; p += len;
          return { tag: tag, start: s, len: len, end: p };
        }
        function children(t) {
          var save = p, out = []; p = t.start;
          while (p < t.end) { var c = tv(); out.push(c); }
          p = save;
          return out;
        }
        function int(t) { return u8.subarray(t.start, t.end); }
        return { tv: tv, children: children, int: int };
      })(keys[0]);
      var seq = D.tv();
      var spki = D.children(seq)[1];
      var pk = D.children(spki)[1];
      var ints = D.children(pk);
      var e = ints[0], n = ints[1];
      var eBytes = e.len > 1 && keys[0][e.start] === 0 ? keys[0].subarray(e.start + 1, e.end) : keys[0].subarray(e.start, e.end);
      var nBytes = keys[0].subarray(n.start + 1, n.end);
      var wire = concat([sshString(new TextEncoder().encode('ssh-rsa')), sshString(eBytes), sshString(nBytes)]);
      pubOut.value = 'ssh-rsa ' + T.bytesToB64(wire) + ' ' + (comment.value || '');
      T.toast('生成完成，公钥可直接放入 authorized_keys');
    }).catch(function (err) { T.toast('失败：' + err.message); });
  }, true),
  T.button('下载私钥', function () { T.download('id_rsa', privOut.value); })]));
T.el('div', {});
app.appendChild(T.msg('提示：私钥请下载后保存到 ~/.ssh/id_rsa 并执行 chmod 600；OpenSSH 新版建议配合 ssh-keygen 转换为 openssh 格式。', ''));
''')

d('password-check', '密码强度检测', '实时检测密码熵值、字符覆盖与常见弱口令模式', js=r'''
var input = T.input('', { type: 'password', class: 'grow mono', placeholder: '输入要检测的密码…' });
var showPw = T.check('显示明文');
var meter = T.el('div', { style: 'height:8px;background:var(--line);border-radius:4px;overflow:hidden;flex:1' });
var fill = T.el('div', { style: 'height:100%;width:0;background:var(--err);transition:all .25s' });
meter.appendChild(fill);
var info = T.el('div', { class: 'pane single' });
var COMMON = ['123456', 'password', '12345678', 'qwerty', 'abc123', '111111', '123123', 'admin', 'letmein', 'iloveyou', '000000', '666666', '888888', 'monkey', 'dragon', 'master', 'qwertyuiop', 'superman', '1q2w3e4r', 'a123456', '123456789', '1234567890', 'password1', 'google', 'facebook'];
function entropy(pw) {
  var pool = 0;
  if (/[a-z]/.test(pw)) pool += 26;
  if (/[A-Z]/.test(pw)) pool += 26;
  if (/[0-9]/.test(pw)) pool += 10;
  if (/[^a-zA-Z0-9]/.test(pw)) pool += 33;
  return pw.length * Math.log2(pool || 1);
}
function report() {
  var pw = input.value;
  T.clearEl(info);
  if (!pw) { fill.style.width = '0'; return; }
  var issues = [];
  var bits = entropy(pw);
  if (pw.length < 8) issues.push('长度不足 8 位');
  if (!/[A-Z]/.test(pw)) issues.push('缺少大写字母');
  if (!/[0-9]/.test(pw)) issues.push('缺少数字');
  if (!/[^a-zA-Z0-9]/.test(pw)) issues.push('缺少特殊字符');
  if (COMMON.indexOf(pw.toLowerCase()) >= 0) issues.push('位于常见弱口令字典中 ⚠⚠');
  if (/^(.)\1+$/.test(pw)) issues.push('全部为同一字符');
  if (/^(?:012|123|234|345|456|567|678|789|abc|bcd|cde|def|qwe|wer|ert)+/i.test(pw)) issues.push('包含连续序列');
  var guesses = Math.pow(2, bits);
  var seconds = guesses / 1e10;
  var crack = seconds < 1 ? '瞬间' : seconds < 3600 ? Math.ceil(seconds) + ' 秒' : seconds < 86400 ? Math.ceil(seconds / 3600) + ' 小时' : seconds < 31536000 ? Math.ceil(seconds / 86400) + ' 天' : (seconds / 31536000).toExponential(2) + ' 年';
  var score = Math.max(0, Math.min(100, bits / 100 * 100));
  fill.style.width = score + '%';
  fill.style.background = score < 40 ? 'var(--err)' : score < 70 ? 'var(--warn-text)' : 'var(--ok-text)';
  var strength = score < 40 ? '弱' : score < 70 ? '中' : '强';
  var rows = [['强度', strength + '（' + Math.round(bits) + ' bit 熵）'], ['离线暴力破解（10^10 次/秒）', '约 ' + crack]];
  if (issues.length) issues.forEach(function (i2) { rows.push(['问题', i2]); });
  else rows.push(['问题', '未发现明显弱点 ✓']);
  info.appendChild(T.kvTable(rows));
}
input.addEventListener('input', report);
showPw._input.addEventListener('change', function () { input.type = showPw._input.checked ? 'text' : 'password'; });
app.appendChild(T.row([input, showPw]));
app.appendChild(T.row([meter]));
app.appendChild(info);
''')

d('hash-identify', 'Hash 类型识别', '根据长度与前缀特征识别可能的哈希算法', js=r'''
var input = T.input('', { class: 'grow mono', placeholder: '粘贴 hash 值…' });
var info = T.el('div');
function identify(h) {
  var out = [];
  var add = function (name, conf) { out.push([name, conf]); };
  if (/^[a-f0-9]{4}$/i.test(h)) add('CRC-16', '可能');
  if (/^[a-f0-9]{8}$/i.test(h)) { add('CRC-32', '可能'); add('Adler-32', '可能'); }
  if (/^[a-f0-9]{32}$/i.test(h)) {
    add('MD5', '很可能');
    add('MD4 / MD2 / NTLM / LM', '可能');
    add('RIPEMD-128', '可能');
    if (/^\$1\$/.test(h)) add('MD5 Crypt (Unix)', '前缀 $1$ 确认');
  }
  if (/^[a-f0-9]{40}$/i.test(h)) { add('SHA-1', '很可能'); add('RIPEMD-160', '可能'); add('MySQL5', '可能'); }
  if (/^[a-f0-9]{56}$/i.test(h)) { add('SHA-224', '很可能'); add('SHA3-224', '可能'); }
  if (/^[a-f0-9]{64}$/i.test(h)) { add('SHA-256', '很可能'); add('SHA3-256 / BLAKE2s-256', '可能'); }
  if (/^[a-f0-9]{96}$/i.test(h)) { add('SHA-384', '很可能'); add('SHA3-384', '可能'); }
  if (/^[a-f0-9]{128}$/i.test(h)) { add('SHA-512', '很可能'); add('Whirlpool / SHA3-512', '可能'); }
  if (/^\$2[aby]\$/.test(h)) add('bcrypt', '前缀 $2 确认');
  if (/^\$6\$/.test(h)) add('SHA-512 Crypt (Unix)', '前缀 $6$ 确认');
  if (/^\$5\$/.test(h)) add('SHA-256 Crypt (Unix)', '前缀 $5$ 确认');
  if (/^\$argon2(i|id)\$/.test(h)) add('Argon2', '前缀确认');
  if (/^\$scrypt\$/.test(h) || /^scrypt\$/.test(h)) add('scrypt', '前缀确认');
  if (/^[A-Za-z0-9+/]{43}=$/.test(h)) add('SHA-256（Base64）', '可能');
  if (/^[A-Fa-f0-9]{32}:[A-Fa-f0-9]{32}$/.test(h)) add('MD5 + Salt / NTLM 对', '可能');
  return out;
}
function report() {
  var h = input.value.trim();
  T.clearEl(info);
  if (!h) return;
  var res = identify(h);
  if (!res.length) {
    info.appendChild(T.msg('无法识别：长度 ' + h.length + '（' + (/^[a-f0-9]+$/i.test(h) ? '纯 hex' : '非纯 hex') + '）。若为 hex 且长度为 4 的倍数，可能为截断哈希或 HMAC。', ''));
    return;
  }
  info.appendChild(T.kvTable(res.map(function (r) { return [r[0] + '（长度 32/' + '—'.slice(0, 0) + h.length + '）', r[1]]; })));
}
input.addEventListener('input', T.debounce(report, 200));
app.appendChild(T.row([T.el('span', { text: 'Hash' }), input]));
app.appendChild(info);
''')

d('pbkdf2', 'PBKDF2 派生', 'WebCrypto PBKDF2 密钥派生：迭代次数 / 哈希 / 盐可调', js=r'''
var pass = T.input('', { type: 'password', class: 'grow mono', placeholder: '口令…' });
var salt = T.input('freellm-salt', { class: 'grow mono', placeholder: '盐（文本）…' });
var iter = T.num(100000, { min: 1000, step: 1000, style: 'width:120px' });
var algo = T.select(['SHA-256', 'SHA-384', 'SHA-512'], 'SHA-256');
var len = T.select([{value:'256',label:'256 bit'},{value:'128',label:'128 bit'},{value:'512',label:'512 bit'}],'256');
var output = T.out('');
function run() {
  if (!pass.value) { output.value = ''; return; }
  crypto.subtle.importKey('raw', T.textToBytes(pass.value), 'PBKDF2', false, ['deriveKey'])
    .then(function (base) {
      return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt: T.textToBytes(salt.value), iterations: +iter.value, hash: algo.value },
        base, { name: 'AES-GCM', length: +len.value }, true, ['encrypt']);
    })
    .then(function (key) { return crypto.subtle.exportKey('raw', key); })
    .then(function (raw) { output.value = T.bytesToHex(raw); })
    .catch(function (e) { output.value = '⚠ ' + e.message; });
}
[pass, salt, iter, algo, len].forEach(function (el) { el.addEventListener('input', T.debounce(run, 250)); });
app.appendChild(T.pane([T.field('派生密钥 (hex)', output)], true));
app.appendChild(T.row([T.el('span', { text: '口令' }), pass]));
app.appendChild(T.row([T.el('span', { text: '盐' }), salt, T.el('span', { text: '迭代' }), iter]));
app.appendChild(T.row([T.el('span', { text: '哈希' }), algo, T.el('span', { text: '长度' }), len]));
run();
''')

d('scrypt', 'Scrypt 派生', 'RFC 7914 scrypt 密钥派生（纯前端实现，抗 GPU/ASIC）', js=r'''
var pass = T.input('', { type: 'password', class: 'grow mono', placeholder: '口令…' });
var salt = T.input('freellm-salt', { class: 'grow mono', placeholder: '盐（文本）…' });
var N = T.select([{value:'1024',label:'N=1024 (r=8,p=1) 快'},{value:'4096',label:'N=4096'},{value:'16384',label:'N=16384 (128MB 内存) 慢'}],'4096');
var output = T.out('');
var status = T.badge('—');
function run() {
  if (!pass.value) { output.value = ''; return; }
  status.textContent = '计算中…';
  setTimeout(function () {
    try {
      var t0 = performance.now();
      var dk = LC.scrypt(T.textToBytes(pass.value), T.textToBytes(salt.value), +N.value, 8, 1, 32);
      output.value = T.bytesToHex(dk);
      status.textContent = '完成，耗时 ' + Math.round(performance.now() - t0) + ' ms';
    } catch (e) { output.value = '⚠ ' + e.message; status.textContent = '出错'; }
  }, 30);
}
[pass, salt, N].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('派生密钥 (hex, 32 字节)', output)], true));
app.appendChild(T.row([T.el('span', { text: '口令' }), pass]));
app.appendChild(T.row([T.el('span', { text: '盐' }), salt]));
app.appendChild(T.row([T.el('span', { text: '强度' }), N, status]));
run();
''')

d('ecdh', 'ECDH 密钥交换', '椭圆曲线 Diffie-Hellman：双方从各自密钥对推导出相同共享密钥', js=r'''
var curve = T.select([{value:'P-256',label:'P-256'},{value:'P-384',label:'P-384'}],'P-256');
var myPub = T.out('我的公钥（发给对方）…');
myPub.setAttribute('rows', '4');
var peerPub = T.textarea('粘贴对方公钥（PEM）…', true);
peerPub.setAttribute('rows', '4');
var myPriv = T.out('我的私钥（PKCS#8）…');
myPriv.setAttribute('rows', '4');
var shared = T.out('共享密钥 (hex)…');
var kp = null;
function toPem(b64) {
  return '-----BEGIN PUBLIC KEY-----\n' + b64.match(/.{1,64}/g).join('\n') + '\n-----END PUBLIC KEY-----';
}
function gen() {
  crypto.subtle.generateKey({ name: 'ECDH', namedCurve: curve.value }, true, ['deriveKey'])
    .then(function (k) {
      kp = k;
      return crypto.subtle.exportKey('spki', k.publicKey);
    })
    .then(function (spki) {
      myPub.value = toPem(T.bytesToB64(spki));
      return crypto.subtle.exportKey('pkcs8', kp.privateKey);
    })
    .then(function (pk8) {
      myPriv.value = '-----BEGIN PRIVATE KEY-----\n' + T.bytesToB64(pk8).match(/.{1,64}/g).join('\n') + '\n-----END PRIVATE KEY-----';
    });
}
function derive() {
  if (!kp || !peerPub.value) { T.toast('请先生成密钥对并粘贴对方公钥'); return; }
  crypto.subtle.importKey('spki', _peerDer(peerPub.value), { name: 'ECDH', namedCurve: curve.value }, false, [])
    .then(function (peer) {
      return crypto.subtle.deriveKey({ name: 'ECDH', public: peer }, kp.privateKey, { name: 'AES-GCM', length: 256 }, true, ['encrypt']);
    })
    .then(function (secret) { return crypto.subtle.exportKey('raw', secret); })
    .then(function (raw) { shared.value = T.bytesToHex(raw); })
    .catch(function (e) { shared.value = '⚠ ' + e.message; });
}
function _peerDer(pem) {
  var b64 = pem.replace(/-----(BEGIN|END)[^-]+-----/g, '').replace(/\s+/g, '');
  return T.b64ToBytes(b64);
}
app.appendChild(T.pane([T.field('我的公钥', myPub), T.field('对方公钥', peerPub)]));
app.appendChild(T.pane([T.field('我的私钥（妥善保管）', myPriv), T.field('共享密钥（双方一致）', shared)]));
app.appendChild(T.row([T.el('span', { text: '曲线' }), curve,
  T.button('生成我的密钥对', gen, true), T.button('推导共享密钥', derive)]));
gen();
''')

d('ecdsa', 'ECDSA 数字签名', 'P-256 椭圆曲线签名与验签', js=r'''
var msg = T.textarea('待签名消息…');
var pubOut = T.out('公钥…'); pubOut.setAttribute('rows', '4');
var privOut = T.out('私钥…'); privOut.setAttribute('rows', '4');
var sigOut = T.out('签名 (base64)…'); sigOut.setAttribute('rows', '4');
var verdict = T.badge('—');
var kp = null;
function gen() {
  crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']).then(function (k) {
    kp = k;
    return Promise.all([crypto.subtle.exportKey('spki', k.publicKey), crypto.subtle.exportKey('pkcs8', k.privateKey)]);
  }).then(function (keys) {
    var pem = function (b64, l) { return '-----BEGIN ' + l + '-----\n' + b64.match(/.{1,64}/g).join('\n') + '\n-----END ' + l + '-----'; };
    pubOut.value = pem(T.bytesToB64(keys[0]), 'PUBLIC KEY');
    privOut.value = pem(T.bytesToB64(keys[1]), 'PRIVATE KEY');
  });
}
function sign() {
  if (!kp) { T.toast('请先生成密钥对'); return; }
  crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, kp.privateKey, T.textToBytes(msg.value))
    .then(function (sig) { sigOut.value = T.bytesToB64(sig); verdict.textContent = '已签名'; });
}
function verify() {
  if (!kp) { T.toast('请先生成密钥对'); return; }
  crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, kp.publicKey, T.b64ToBytes(sigOut.value.trim()), T.textToBytes(msg.value))
    .then(function (ok) {
      verdict.textContent = ok ? '✓ 验签通过' : '✗ 验签失败（消息或签名被改动）';
      verdict.className = 'badge ' + (ok ? 'ok' : 'warn');
    });
}
app.appendChild(T.pane([T.field('消息', msg)], true));
app.appendChild(T.pane([T.field('公钥', pubOut), T.field('私钥', privOut)]));
app.appendChild(T.field('签名', sigOut));
app.appendChild(T.row([T.button('生成密钥对', gen), T.button('签名', sign, true), T.button('验签', verify), verdict]));
gen();
''')

d('cert-viewer', '证书查看器', '上传或粘贴 PEM 证书，查看完整详细信息', js=X509_JS + r'''
var info = T.el('div', { class: 'pane single' });
var drop = T.msg('点击选择 .pem/.crt/.cer 文件，或直接粘贴下方', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var input = T.textarea('或粘贴 PEM 内容…', true);
input.setAttribute('rows', '6');
var inp = T.el('input', { type: 'file', style: 'display:none', accept: '.pem,.crt,.cer,.txt' });
inp.addEventListener('change', function () {
  var f = inp.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () { input.value = fr.result; show(); };
  fr.readAsText(f);
});
document.body.appendChild(inp);
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) {
  e.preventDefault();
  if (e.dataTransfer.files[0]) {
    var fr = new FileReader();
    fr.onload = function () { input.value = fr.result; show(); };
    fr.readAsText(e.dataTransfer.files[0]);
  }
});
function show() {
  T.clearEl(info);
  if (!input.value.includes('BEGIN CERTIFICATE')) return;
  try {
    var c = _parseX509(input.value);
    info.appendChild(T.kvTable([
      ['版本', 'v' + c.version],
      ['序列号', c.serial],
      ['签名算法', c.sigAlg],
      ['主体 Subject', c.subject],
      ['签发者 Issuer', c.issuer],
      ['生效时间', c.notBefore + ' UTC'],
      ['过期时间', c.notAfter + ' UTC' + (c.expired ? '（已过期 ⚠）' : '（有效 ✓）')],
      ['公钥', c.pkAlg + ' · ' + c.keyBits]
    ]));
  } catch (e) {
    info.appendChild(T.msg('⚠ 解析失败：' + e.message, 'err'));
  }
}
input.addEventListener('input', T.debounce(show, 300));
app.appendChild(drop);
app.appendChild(T.pane([T.field('PEM 内容', input)], true));
app.appendChild(info);
''')
