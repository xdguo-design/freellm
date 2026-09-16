# -*- coding: utf-8 -*-
"""编码加密类工具定义"""
from .registry import d

d('base64', 'Base64 编解码', 'UTF-8 文本与 Base64 互转，支持 URL-Safe 变体与文件转 Base64', js=r'''
var input = T.textarea('输入文本或 Base64…');
var output = T.out('输出…');
var mode = T.select([{value:'enc',label:'文本 → Base64'},{value:'dec',label:'Base64 → 文本'}],'enc');
var safe = T.check('URL-Safe（-_ 替代 +/）');
var info = T.badge('—');
function run() {
  var v = input.value;
  if (!v) { output.value = ''; info.textContent = '—'; return; }
  try {
    if (mode.value === 'enc') {
      var b = T.bytesToB64(T.textToBytes(v));
      output.value = safe._input.checked ? b.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') : b;
      info.textContent = v.length + ' 字符 → ' + output.value.length + ' 字符';
    } else {
      var s = safe._input.checked ? v.replace(/-/g, '+').replace(/_/g, '/') : v;
      while (s.length % 4) s += '=';
      output.value = T.bytesToText(T.b64ToBytes(s));
      info.textContent = '解码成功';
    }
  } catch (e) { output.value = '⚠ ' + e.message; info.textContent = '出错'; }
}
[input, mode, safe._input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([T.el('span', { text: '方向' }), mode, safe, info,
  T.button('复制输出', function () { T.copy(output.value); })]));
app.appendChild(T.row([T.filePick('选择文件转 Base64', '', function (dataURL, file) {
  T.copy(dataURL.split(',')[1] || '');
  T.toast('已复制文件 Base64（' + T.fmtBytes(file.size) + '）');
}, true),
T.button('解码并下载为文件', function () {
  try { T.download('decoded.bin', T.b64ToBytes(output.value)); } catch (e) { T.toast(e.message); }
})]));
run();
''')

d('url-encode', 'URL 编解码', 'encodeURIComponent / encodeURL 全 URL 与组件级编码互转', js=r'''
var input = T.textarea('输入 URL 或文本…');
var output = T.out('输出…');
var mode = T.select([{value:'enc',label:'编码'},{value:'dec',label:'解码'}],'enc');
var comp = T.select([{value:'component',label:'组件编码 (encodeURIComponent)'},{value:'full',label:'整段 URL (encodeURI)'}],'component');
function run() {
  var v = input.value;
  try {
    if (mode.value === 'enc') {
      output.value = comp.value === 'component' ? encodeURIComponent(v) : encodeURI(v);
    } else {
      output.value = comp.value === 'component' ? decodeURIComponent(v) : decodeURI(v);
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode, comp].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([T.el('span', { text: '模式' }), mode, comp,
  T.button('复制', function () { T.copy(output.value); })]));
run();
''')

d('md5', 'MD5 哈希', '纯前端计算 MD5 摘要，支持文本与文件', js=r'''
var input = T.textarea('输入文本…');
var output = T.out('');
var upper = T.check('大写输出');
function run() {
  if (!input.value) { output.value = ''; return; }
  var h = T.bytesToHex(LC.md5(T.textToBytes(input.value)));
  output.value = upper._input.checked ? h.toUpperCase() : h;
}
input.addEventListener('input', T.debounce(run, 200));
upper._input.addEventListener('change', run);
app.appendChild(T.pane([T.field('输入', input), T.field('MD5 摘要 (128 bit / 32 hex)', output)]));
var fileBtn = T.button('计算文件 MD5', function () {
  var inp = T.el('input', { type: 'file', style: 'display:none' });
  inp.addEventListener('change', function () {
    var f = inp.files[0]; if (!f) return;
    var fr = new FileReader();
    fr.onload = function () { output.value = T.bytesToHex(LC.md5(new Uint8Array(fr.result))); T.toast('已计算 ' + f.name); };
    fr.readAsArrayBuffer(f);
  });
  document.body.appendChild(inp); inp.click();
});
app.appendChild(T.row([fileBtn, T.btnCopy(function () { return output.value; })]));
run();
''')

d('sha', 'SHA 哈希', 'WebCrypto 计算 SHA-1 / SHA-256 / SHA-384 / SHA-512', js=r'''
var input = T.textarea('输入文本…');
var algo = T.select(['SHA-1', 'SHA-256', 'SHA-384', 'SHA-512'], 'SHA-256');
var upper = T.check('大写输出');
var box = T.el('div', { class: 'pane single' });
function run() {
  if (!input.value) { T.clearEl(box); return; }
  crypto.subtle.digest(algo.value, T.textToBytes(input.value)).then(function (buf) {
    var h = T.bytesToHex(buf);
    if (upper._input.checked) h = h.toUpperCase();
    T.clearEl(box).appendChild(T.field(algo.value + ' (160/256/384/512 bit)', (function () {
      var o = T.out(''); o.value = h; return o;
    })()));
  });
}
input.addEventListener('input', T.debounce(run, 250));
algo.addEventListener('change', run);
upper._input.addEventListener('change', run);
app.appendChild(T.pane([T.field('输入', input)], true));
app.appendChild(T.row([T.el('span', { text: '算法' }), algo, upper, T.el('span', { text: '所有摘要' })]));
app.appendChild(box);
app.appendChild(T.row([T.button('计算全部算法', function () {
  T.clearEl(box);
  ['SHA-1', 'SHA-256', 'SHA-384', 'SHA-512'].forEach(function (a) {
    crypto.subtle.digest(a, T.textToBytes(input.value)).then(function (buf) {
      var o = T.out(''); o.value = T.bytesToHex(buf);
      box.appendChild(T.field(a, o));
    });
  });
}, true)]));
run();
''')

d('html-entity', 'HTML 实体编解码', 'HTML 实体字符 ↔ 原始字符互转', js=r'''
var input = T.textarea('输入文本或含实体的 HTML…');
var output = T.out('输出…');
var mode = T.select([{value:'enc',label:'原始 → 实体'},{value:'dec',label:'实体 → 原始'}],'enc');
var all = T.check('编码所有非 ASCII（&#xxxx;）');
function enc(s) {
  s = s.replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  if (all._input.checked) {
    s = s.replace(/[\x80-\uFFFF]/g, function (ch) { return '&#' + ch.codePointAt(0) + ';'; });
  }
  return s;
}
function dec(s) {
  var el = T.el('textarea', { style: 'display:none' });
  el.innerHTML = s;
  return el.value;
}
function run() {
  var v = input.value;
  try {
    output.value = mode.value === 'enc' ? enc(v) : dec(v);
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode, all._input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, all, T.btnCopy(function () { return output.value; })]));
run();
''')

d('unicode', 'Unicode 转换', '文本与 Unicode 转义互转：\\\\uXXXX / \\\\u{...} / HTML 实体，含代理对', js=r'''
var input = T.textarea('输入文本或转义串…');
var output = T.out('输出…');
var style = T.select([
  { value: 'u4', label: '\\uXXXX（\\uD83D\\uDE00 代理对）' },
  { value: 'ub', label: '\\u{1F600}（ES6 码点）' },
  { value: 'hex', label: '&#x1F600;（HTML 十六进制）' },
  { value: 'dec', label: '&#128512;（HTML 十进制）' }
], 'u4');
var mode = T.select([{value:'enc',label:'文本 → 转义'},{value:'dec',label:'转义 → 文本'}],'enc');
function run() {
  var v = input.value;
  try {
    if (mode.value === 'enc') {
      output.value = Array.from(v).map(function (ch) {
        var cp = ch.codePointAt(0);
        if (cp < 128) return ch;
        if (style.value === 'u4') {
          var h = cp.toString(16).padStart(4, '0');
          return cp > 0xFFFF ? Array.from(ch).map(function (s) { return '\\u' + s.charCodeAt(0).toString(16).padStart(4, '0'); }).join('') : '\\u' + h;
        }
        if (style.value === 'ub') return '\\u{' + cp.toString(16) + '}';
        if (style.value === 'hex') return '&#x' + cp.toString(16) + ';';
        return '&#' + cp + ';';
      }).join('');
    } else {
      output.value = v
        .replace(/\\u\{([0-9a-fA-F]+)\}/g, function (m, h) { return String.fromCodePoint(parseInt(h, 16)); })
        .replace(/&#x([0-9a-fA-F]+);/gi, function (m, h) { return String.fromCodePoint(parseInt(h, 16)); })
        .replace(/&#(\d+);/g, function (m, d) { return String.fromCodePoint(+d); })
        .replace(/\\u([0-9a-fA-F]{4})/g, function (m, h) { return String.fromCharCode(parseInt(h, 16)); });
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, style, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, style, T.btnCopy(function () { return output.value; })]));
run();
''')

d('aes', 'AES 加解密', 'AES-GCM / AES-CBC 对称加解密，口令经 PBKDF2 派生密钥', js=r'''
var input = T.textarea('输入明文…');
var output = T.out('输出（Base64）…');
var mode = T.select([{value:'enc',label:'加密'},{value:'dec',label:'解密'}],'enc');
var algo = T.select([{value:'AES-GCM',label:'AES-GCM（推荐）'},{value:'AES-CBC',label:'AES-CBC'}],'AES-GCM');
var pass = T.input('', { type: 'password', placeholder: '口令', class: 'grow mono' });
var ivOut = T.input('', { placeholder: 'IV（Base64，自动生成/粘贴）', class: 'grow mono' });
async function deriveKey(pwd, usages) {
  var base = await crypto.subtle.importKey('raw', T.textToBytes(pwd), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: T.textToBytes('freellm-aes-salt'), iterations: 100000, hash: 'SHA-256' },
    base, { name: algo.value, length: 256 }, false, usages);
}
async function run() {
  var v = input.value;
  if (!v || !pass.value) { output.value = ''; return; }
  try {
    if (mode.value === 'enc') {
      var iv = crypto.getRandomValues(new Uint8Array(12));
      var key = await deriveKey(pass.value, ['encrypt']);
      var ct = new Uint8Array(await crypto.subtle.encrypt({ name: algo.value, iv: iv }, key, T.textToBytes(v)));
      output.value = T.bytesToB64(ct);
      ivOut.value = T.bytesToB64(iv);
    } else {
      var iv2 = T.b64ToBytes(ivOut.value || '');
      var key2 = await deriveKey(pass.value, ['decrypt']);
      var pt = await crypto.subtle.decrypt({ name: algo.value, iv: iv2 }, key2, T.b64ToBytes(v));
      output.value = T.bytesToText(new Uint8Array(pt));
    }
  } catch (e) { output.value = '⚠ 加解密失败：口令错误或数据损坏'; }
}
[T.input, mode, algo].forEach(function () {});
input.addEventListener('change', run);
mode.addEventListener('change', function () {
  if (mode.value === 'dec') input.placeholder = '输入密文（Base64）…';
  else input.placeholder = '输入明文…';
});
app.appendChild(T.pane([T.field(mode.value === 'enc' ? '明文' : '密文 (Base64)', input), T.field('结果', output)]));
var runBtn = T.button('执行', run, true);
app.appendChild(T.row([T.el('span', { text: '方向' }), mode, T.el('span', { text: '算法' }), algo]));
app.appendChild(T.row([T.el('span', { text: '口令' }), pass, runBtn]));
app.appendChild(T.row([T.el('span', { text: 'IV' }), ivOut, T.el('span', { text: '加密后自动生成；解密需粘贴原 IV' })]));
''')

d('file-hash', '文件哈希', '浏览器本地计算文件 MD5 / SHA-1 / SHA-256 / SHA-512', js=r'''
var table = T.el('div', { class: 'pane single' });
var drop = T.msg('点击下方按钮选择文件，或拖拽到此处', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '30px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) {
  e.preventDefault();
  if (e.dataTransfer.files[0]) handle(e.dataTransfer.files[0]);
});
drop.addEventListener('click', function () { inp.click(); });
var inp = T.el('input', { type: 'file', style: 'display:none' });
inp.addEventListener('change', function () { if (inp.files[0]) handle(inp.files[0]); });
document.body.appendChild(inp);
function handle(f) {
  drop.textContent = '正在计算 ' + f.name + '（' + T.fmtBytes(f.size) + '）…';
  var fr = new FileReader();
  fr.onload = function () {
    var u8 = new Uint8Array(fr.result);
    var rows = [['文件', f.name], ['大小', T.fmtBytes(f.size)], ['MD5', T.bytesToHex(LC.md5(u8))]];
    var jobs = [['SHA-1', 'SHA-1'], ['SHA-256', 'SHA-256'], ['SHA-512', 'SHA-512']].map(function (j) {
      return crypto.subtle.digest(j[1], u8).then(function (buf) { rows.push([j[0], T.bytesToHex(buf)]); });
    });
    Promise.all(jobs).then(function () {
      T.clearEl(table).appendChild(T.kvTable(rows));
      drop.textContent = f.name + ' · ' + T.fmtBytes(f.size) + '（点击或拖入更换文件）';
    });
  };
  fr.readAsArrayBuffer(f);
}
app.appendChild(drop);
app.appendChild(table);
''')

d('hmac', 'HMAC 哈希', 'HMAC-SHA 系列消息认证码在线计算', js=r'''
var msg = T.textarea('消息内容…');
var key = T.input('', { placeholder: '密钥（文本）', class: 'grow mono' });
var algo = T.select(['SHA-1', 'SHA-256', 'SHA-384', 'SHA-512'], 'SHA-256');
var output = T.out('');
function run() {
  if (!msg.value || !key.value) { output.value = ''; return; }
  crypto.subtle.importKey('raw', T.textToBytes(key.value),
    { name: 'HMAC', hash: { name: algo.value } }, false, ['sign'])
    .then(function (k) { return crypto.subtle.sign('HMAC', k, T.textToBytes(msg.value)); })
    .then(function (sig) { output.value = T.bytesToHex(sig); })
    .catch(function (e) { output.value = '⚠ ' + e.message; });
}
[msg, key, algo].forEach(function (el) { el.addEventListener('input', T.debounce(run, 250)); });
app.appendChild(T.pane([T.field('消息', msg), T.field('HMAC (hex)', output)]));
app.appendChild(T.row([T.el('span', { text: '密钥' }), key, T.el('span', { text: '算法' }), algo, T.btnCopy(function () { return output.value; })]));
run();
''')

d('gzip', 'Gzip 压缩', '文本 Gzip / Deflate 压缩解压，显示压缩率（Base64 传输）', js=r'''
var input = T.textarea('输入文本（压缩）或 Base64（解压）…');
var output = T.out('输出…');
var mode = T.select([{value:'gzip',label:'Gzip'},{value:'deflate',label:'Deflate'}],'gzip');
var dir = T.select([{value:'enc',label:'压缩'},{value:'dec',label:'解压'}],'enc');
var info = T.badge('—');
async function run() {
  var v = input.value;
  if (!v) { output.value = ''; return; }
  try {
    if (dir.value === 'enc') {
      var cs = new CompressionStream(mode.value);
      var blob = new Blob([T.textToBytes(v)]);
      var buf = await new Response(blob.stream().pipeThrough(cs)).arrayBuffer();
      var u8 = new Uint8Array(buf);
      output.value = T.bytesToB64(u8);
      info.textContent = T.fmtBytes(v.length) + ' → ' + T.fmtBytes(u8.length) + '（压缩率 ' + (100 - u8.length / v.length * 100).toFixed(1) + '%）';
    } else {
      var ds = new DecompressionStream(mode.value);
      var buf2 = await new Response(new Blob([T.b64ToBytes(v)]).stream().pipeThrough(ds)).arrayBuffer();
      output.value = T.bytesToText(new Uint8Array(buf2));
      info.textContent = '解压成功';
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([T.el('span', { text: '算法' }), mode, T.el('span', { text: '方向' }), dir, T.button('执行', run, true), info]));
''')

d('caesar', '凯撒密码', '经典凯撒移位加密解密，支持一键枚举全部移位', js=r'''
var input = T.textarea('输入文本…');
var output = T.out('输出…');
var shift = T.num(3, { min: 1, max: 25, style: 'width:80px' });
var dir = T.select([{value:'enc',label:'加密'},{value:'dec',label:'解密'}],'enc');
function caesar(s, k) {
  return s.replace(/[a-zA-Z]/g, function (c) {
    var base = c <= 'Z' ? 65 : 97;
    return String.fromCharCode((c.charCodeAt(0) - base + k + 26) % 26 + base);
  });
}
function run() {
  var k = (+shift.value || 0) * (dir.value === 'enc' ? 1 : -1);
  output.value = caesar(input.value, k);
}
[input, shift, dir].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([dir, T.el('span', { text: '移位' }), shift, T.btnCopy(function () { return output.value; })]));
var all = T.out('全部 25 种移位结果…');
all.style.minHeight = '220px';
function brute() {
  if (!input.value) { all.value = ''; return; }
  var lines = [];
  for (var k = 1; k <= 25; k++) lines.push('移位 ' + String(k).padStart(2, ' ') + '：' + caesar(input.value, -k));
  all.value = lines.join('\n');
}
input.addEventListener('input', T.debounce(brute, 300));
app.appendChild(T.el('hr', { class: 'hr' }));
app.appendChild(T.field('暴力枚举（解密方向 1-25，找可读行）', all));
run(); brute();
''')

d('rot13', 'ROT13/ROT47', '经典 ROT 系列编码：字母 ROT13，ASCII 可见字符 ROT47', js=r'''
var input = T.textarea('输入文本…');
var output = T.out('输出…');
var info = T.badge('ROT13 与 ROT47 均为自反变换，再执行一次即还原');
function run() {
  var v = input.value;
  var r13 = v.replace(/[a-zA-Z]/g, function (c) {
    var base = c <= 'Z' ? 65 : 97;
    return String.fromCharCode((c.charCodeAt(0) - base + 13) % 26 + base);
  });
  var r47 = v.replace(/[!-~]/g, function (c) {
    return String.fromCharCode(33 + (c.charCodeAt(0) - 33 + 47) % 94);
  });
  output.value = 'ROT13: ' + r13 + '\nROT47: ' + r47;
}
input.addEventListener('input', run);
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([info, T.btnCopy(function () { return output.value; })]));
run();
''')

d('file-hex', '文件与 Hex 互转', '任意文件 ↔ 十六进制字符串，支持拖拽与下载还原', js=r'''
var input = T.textarea('粘贴十六进制字符串，或选择文件…');
var output = T.out('输出…');
var dir = T.select([{value:'f2h',label:'文件 → Hex'},{value:'h2f',label:'Hex → 文件'}],'f2h');
var info = T.badge('—');
function run() {
  var v = input.value;
  if (!v) { output.value = ''; return; }
  try {
    if (dir.value === 'f2h') {
      var inp = T.el('input', { type: 'file', style: 'display:none' });
      inp.addEventListener('change', function () {
        var f = inp.files[0]; if (!f) return;
        var fr = new FileReader();
        fr.onload = function () {
          output.value = T.bytesToHex(new Uint8Array(fr.result));
          info.textContent = f.name + ' · ' + T.fmtBytes(f.size);
        };
        fr.readAsArrayBuffer(f);
      });
      document.body.appendChild(inp); inp.click();
    } else {
      var bytes = T.hexToBytes(v);
      output.value = '(Uint8Array ' + bytes.length + ' 字节，点击下方按钮下载)';
      info.textContent = bytes.length + ' 字节';
      window._hexBytes = bytes;
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([dir, T.button('执行', run, true), T.button('下载还原的文件', function () {
  if (window._hexBytes) T.download('restored.bin', window._hexBytes);
  else T.toast('请先执行 Hex → 文件');
}), info]));
''')

d('base32', 'Base32 编码', 'RFC 4648 Base32 编码与解码', js=r'''
var input = T.textarea('输入文本（编码）或 Base32（解码）…');
var output = T.out('输出…');
var dir = T.select([{value:'enc',label:'编码'},{value:'dec',label:'解码'}],'enc');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    output.value = dir.value === 'enc'
      ? LC.b32encode(T.textToBytes(v))
      : T.bytesToText(LC.b32decode(v));
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, dir].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([dir, T.btnCopy(function () { return output.value; })]));
run();
''')

d('base58', 'Base58 编码', 'Bitcoin 字母表 Base58 编码与解码', js=r'''
var input = T.textarea('输入文本（编码）或 Base58（解码）…');
var output = T.out('输出…');
var dir = T.select([{value:'enc',label:'编码'},{value:'dec',label:'解码'}],'enc');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    output.value = dir.value === 'enc'
      ? LC.b58encode(T.textToBytes(v))
      : T.bytesToText(LC.b58decode(v));
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, dir].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([dir, T.btnCopy(function () { return output.value; })]));
run();
''')

d('base85', 'Base85 编码', 'Ascii85 编码与解码（PDF / Git 风格）', js=r'''
var input = T.textarea('输入文本（编码）或 Ascii85（解码）…');
var output = T.out('输出…');
var dir = T.select([{value:'enc',label:'编码'},{value:'dec',label:'解码'}],'enc');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    output.value = dir.value === 'enc'
      ? LC.b85encode(T.textToBytes(v))
      : T.bytesToText(LC.b85decode(v));
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, dir].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([dir, T.btnCopy(function () { return output.value; })]));
run();
''')
