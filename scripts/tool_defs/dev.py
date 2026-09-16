# -*- coding: utf-8 -*-
"""开发工具类工具定义"""
from .registry import d

d('mermaid', 'Mermaid 编辑器', '流程图 / 时序图 / 甘特图在线编辑渲染（本地渲染库）',
  scripts='<script src="/tools/js/vendor/mermaid.min.js"></script>',
  js=r'''
if (typeof mermaid === 'undefined') { document.getElementById('app').innerHTML = '<div class="msg err">渲染库加载失败，请刷新重试</div>'; return; }
mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });
var input = T.textarea('graph TD\n  A[开始] --> B{是否免费?}\n  B -- 是 --> C[FreeLLM]\n  B -- 否 --> D[跳过]');
input.value = 'graph TD\n  A[开始] --> B{是否免费?}\n  B -- 是 --> C[FreeLLM]\n  B -- 否 --> D[跳过]';
input.style.minHeight = '240px';
var preview = T.el('div', { class: 'output', style: 'min-height:240px;background:#fff;display:flex;justify-content:center;overflow:auto' });
var status = T.badge('—');
var serial = 0;
function render() {
  var code = input.value;
  if (!code.trim()) { preview.innerHTML = ''; return; }
  serial++;
  mermaid.render('mmd' + serial, code).then(function (res) {
    preview.innerHTML = res.svg;
    status.textContent = '✓ 渲染成功';
    status.className = 'badge ok';
  }).catch(function (e) {
    status.textContent = '⚠ 语法错误';
    status.className = 'badge warn';
  });
}
input.addEventListener('input', T.debounce(render, 400));
app.appendChild(T.pane([T.field('Mermaid 源码', input), T.el('div', { class: 'field' }, [T.el('span', { text: '预览' }), preview])]));
app.appendChild(T.row([status,
  T.button('下载 SVG', function () {
    var svg = preview.querySelector('svg');
    if (svg) T.download('diagram.svg', new XMLSerializer().serializeToString(svg), 'image/svg+xml');
  }),
  T.button('复制源码', function () { T.copy(input.value); })]));
app.appendChild(T.el('p', { text: '语法示例：graph TD 流程图 · sequenceDiagram 时序图 · gantt 甘特图 · pie 饼图 · stateDiagram-v2 状态图', style: 'color:var(--ink2);font-size:12px' }));
render();
''')

d('curl-converter', 'Curl 转代码', 'curl 命令转 Python / JS / Go / Java / PHP 代码', js=r'''
var input = T.textarea('curl -X POST https://api.example.com/users \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer token123" \\\n  -d \'{"name":"张三","age":25}\'');
input.value = 'curl -X POST https://api.example.com/users \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer token123" \\\n  -d \'{"name":"张三","age":25}\'';
var lang = T.select(['python', 'javascript', 'go', 'java', 'php'], 'python');
var output = T.out('');
function parseCurl(cmd) {
  var s = cmd.replace(/\\\n/g, ' ').replace(/\r/g, '').trim();
  if (s.startsWith('curl')) s = s.slice(4);
  var method = 'GET';
  var url = '';
  var headers = [];
  var data = '';
  var re = /(-X|--request)\s+(\w+)|(-H|--header)\s+"([^"]+)"|(-H|--header)\s+'([^']+)'|(-d|--data|--data-raw|--data-binary)\s+'([^']*)'|(-d|--data|--data-raw|--data-binary)\s+"([^"]*)"|'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)"|(https?:\/\/[^\s'"]+)/g;
  var m;
  while ((m = re.exec(s))) {
    if (m[2]) method = m[2].toUpperCase();
    else if (m[4] || m[5]) headers.push(m[4] || m[5]);
    else if (m[8] !== undefined) data = m[8];
    else if (m[9] !== undefined) data = m[9];
    else if (m[10] !== undefined) { if (!url) url = m[10]; }
    else if (m[11] !== undefined) { if (!url) url = m[11]; }
    else if (m[12] !== undefined) { if (!url) url = m[12]; }
  }
  if (data && method === 'GET') method = 'POST';
  return { method: method, url: url, headers: headers, data: data };
}
function generate(c) {
  var hs = c.headers.map(function (h) { return h; });
  var out = '';
  if (lang.value === 'python') {
    out = 'import requests\n\nurl = "' + c.url + '"\nheaders = {\n' + hs.map(function (h) {
      var i = h.indexOf(':');
      return '    "' + h.slice(0, i).trim() + '": "' + h.slice(i + 1).trim() + '",';
    }).join('\n') + '\n}\n';
    if (c.data) out += '\npayload = ' + c.data + '\n\nresponse = requests.' + c.method.toLowerCase() + '(url, headers=headers' + (c.data ? ', json=payload' : '') + ')\nprint(response.status_code, response.json())';
    else out += '\nresponse = requests.' + c.method.toLowerCase() + '(url, headers=headers)\nprint(response.status_code, response.text)';
  } else if (lang.value === 'javascript') {
    out = 'const res = await fetch("' + c.url + '", {\n  method: "' + c.method + '",\n  headers: {\n' + hs.map(function (h) {
      var i = h.indexOf(':');
      return '    "' + h.slice(0, i).trim() + '": "' + h.slice(i + 1).trim() + '",';
    }).join('\n') + '\n  }' + (c.data ? ',\n  body: JSON.stringify(' + c.data + ')' : '') + '\n});\nconsole.log(res.status, await res.text());';
  } else if (lang.value === 'go') {
    var bodyVar = 'nil';
    if (c.data) bodyVar = 'strings.NewReader(`' + c.data + '`)';
    out = 'package main\n\nimport (\n\t"fmt"\n\t"io"\n\t"net/http"\n\t"strings"\n)\n\nfunc main() {\n\treq, _ := http.NewRequest("' + c.method + '", "' + c.url + '", ' + bodyVar + ')\n';
    hs.forEach(function (h) {
      var i = h.indexOf(':');
      out += '\treq.Header.Set("' + h.slice(0, i).trim() + '", "' + h.slice(i + 1).trim() + '")\n';
    });
    out += '\tresp, _ := http.DefaultClient.Do(req)\n\tdefer resp.Body.Close()\n\tbody, _ := io.ReadAll(resp.Body)\n\tfmt.Println(resp.StatusCode, string(body))\n}';
  } else if (lang.value === 'java') {
    out = 'HttpClient client = HttpClient.newHttpClient();\nHttpRequest.Builder builder = HttpRequest.newBuilder()\n    .uri(URI.create("' + c.url + '"))\n';
    hs.forEach(function (h) {
      var i = h.indexOf(':');
      out += '    .header("' + h.slice(0, i).trim() + '", "' + h.slice(i + 1).trim() + '")\n';
    });
    out += c.data ? '    .POST(HttpRequest.BodyPublishers.ofString(String s = ' + '"""' + c.data + '"""))\n' : '    .GET();\n';
    if (c.data) out = out.replace(/String s = /, '').replace('String s = ', '');
    out += 'HttpResponse<String> resp = client.send(builder.build(), HttpResponse.BodyHandlers.ofString());\nSystem.out.println(resp.statusCode() + " " + resp.body());';
  } else {
    out = '<?php\n$ch = curl_init("' + c.url + '");\ncurl_setopt($ch, CURLOPT_CUSTOMREQUEST, "' + c.method + '");\n';
    out += 'curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);\ncurl_setopt($ch, CURLOPT_HTTPHEADER, [\n' + hs.map(function (h) { return '    "' + h + '",'; }).join('\n') + '\n]);\n';
    if (c.data) out += "curl_setopt($ch, CURLOPT_POSTFIELDS, '" + c.data + "');\n";
    out += '$resp = curl_exec($ch);\necho curl_getinfo($ch, CURLINFO_HTTP_CODE), $resp;';
  }
  return out;
}
function run() {
  try {
    var c = parseCurl(input.value);
    if (!c.url) throw new Error('未找到 URL');
    output.value = generate(c);
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, lang].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('curl 命令', input), T.field('转换结果', output)]));
app.appendChild(T.row([T.el('span', { text: '目标语言' }), lang, T.btnCopy(function () { return output.value; })]));
run();
''')

d('xpath', 'XPath 测试', 'XPath 表达式在线测试（对粘贴的 XML / HTML 求值）', js=r'''
var docIn = T.textarea('<bookstore><book><title>三体</title><price>45</price></book><book><title>活着</title><price>30</price></book></bookstore>', true);
docIn.value = '<bookstore><book><title>三体</title><price>45</price></book><book><title>活着</title><price>30</price></book></bookstore>';
docIn.value = '<?xml version="1.0"?>\n<bookstore>\n  <book category="sf"><title>三体</title><price>45</price></book>\n  <book category="novel"><title>活着</title><price>30</price></book>\n</bookstore>';
var expr = T.input('//book[price>35]/title/text()', { class: 'grow mono' });
var output = T.out('');
var status = T.badge('—');
function run() {
  var v = docIn.value.trim();
  if (!v || !expr.value) { output.value = ''; return; }
  try {
    var doc = new DOMParser().parseFromString(v, 'text/xml');
    if (doc.querySelector('parsererror')) throw new Error('XML 解析失败');
    var result = doc.evaluate(expr.value, doc, null, XPathResult.ANY_TYPE, null);
    var lines = [], node;
    var count = 0;
    while ((node = result.iterateNext()) && count < 100) {
      if (node.nodeType === 1) lines.push('<' + node.nodeName + '> ' + node.textContent.trim().slice(0, 200));
      else lines.push(node.textContent);
      count++;
    }
    output.value = count + ' 个结果：\n' + lines.join('\n');
    status.textContent = '✓ ' + count + ' 个结果';
    status.className = 'badge ok';
  } catch (e) {
    output.value = '⚠ ' + e.message;
    status.textContent = '出错';
    status.className = 'badge warn';
  }
}
[docIn, expr].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('XML / HTML 文档', docIn)], true));
app.appendChild(T.row([T.el('span', { text: 'XPath' }), expr, status]));
app.appendChild(T.pane([T.field('结果', output)], true));
app.appendChild(T.el('p', { text: '示例：//book/title · //book[1] · //@category · //book[price>35]/title · bookstore/book[last()]', style: 'color:var(--ink2);font-size:12px' }));
run();
''')

d('code2img', '代码转图片', '代码截图美化：生成带窗口样式的代码图片（PNG 下载）', js=r'''
var input = T.textarea('function hello() {\n  console.log("Hello, FreeLLM!");\n}');
input.value = 'function hello() {\n  console.log("Hello, FreeLLM!");\n}';
var title = T.input('hello.js', { class: 'grow mono' });
var theme = T.select([{value:'dark',label:'深色'},{value:'light',label:'浅色'}],'dark');
var pad = T.range(16, 80, 2, 40);
var canvas = T.el('canvas', { style: 'max-width:100%;border-radius:12px;border:1px solid var(--line)' });
var STYLE_D = { bg: '#1E2127', win: '#2F3440', text: '#ECEAE6', dot: ['#FF5F56', '#FFBD2E', '#27C93F'], dotbg: '#3A3F4B' };
var STYLE_L = { bg: '#F4F2EE', win: '#FFFFFF', text: '#2F3437', dot: ['#FF5F56', '#FFBD2E', '#27C93F'], dotbg: '#EAEAEA' };
function render() {
  var code = input.value || ' ';
  var lines = code.split('\n');
  var st = theme.value === 'dark' ? STYLE_D : STYLE_L;
  var fs = 14, lh = 22;
  var measure = T.el('canvas').getContext('2d');
  measure.font = fs + 'px monospace';
  var maxLen = Math.max.apply(null, lines.map(function (l) { return l.length; }));
  var winW = Math.max(420, measure.measureText('x'.repeat(Math.min(maxLen, 90))).width + 60);
  var winH = lines.length * lh + 66;
  var W = winW + pad.value * 2, H = winH + pad.value * 2;
  canvas.width = W * 2;
  canvas.height = H * 2;
  var ctx = canvas.getContext('2d');
  ctx.scale(2, 2);
  ctx.fillStyle = st.bg;
  ctx.fillRect(0, 0, W, H);
  var x = pad.value, y = pad.value;
  ctx.fillStyle = st.dotbg;
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x, y, winW, winH, 10);
  else ctx.rect(x, y, winW, winH);
  ctx.fill();
  STYLE_D.dot.forEach(function (c, i) {
    ctx.fillStyle = c;
    ctx.beginPath();
    ctx.arc(x + 20 + i * 18, y + 18, 5, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.fillStyle = 'rgba(255,255,255,.5)';
  ctx.font = '12px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(title.value, x + winW / 2, y + 22);
  ctx.textAlign = 'left';
  ctx.font = fs + 'px monospace';
  ctx.fillStyle = st.text;
  lines.forEach(function (l, i) {
    ctx.fillText(l, x + 20, y + 48 + i * lh);
  });
}
[input, title, theme, pad].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.pane([T.field('代码', input)], true));
app.appendChild(T.row([T.el('span', { text: '窗口标题' }), title, theme, T.el('span', { text: '边距' }), pad]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载 PNG（2x 高清）', function () { T.dlCanvas(canvas, title.value.replace(/\.\w+$/, '') + '.png'); }, true),
  T.button('复制到剪贴板', function () {
    canvas.toBlob(function (b) {
      navigator.clipboard.write([new ClipboardItem({ 'image/png': b })]).then(function () { T.toast('已复制图片'); }, function () { T.toast('复制失败，请使用下载'); });
    });
  })]));
render();
''')

d('ua-parser', 'UA 解析', 'User-Agent 解析：浏览器 / 引擎 / 系统 / 设备类型', js=r'''
var input = T.textarea(navigator.userAgent, true);
input.setAttribute('rows', '3');
var box = T.el('div');
function parse(ua) {
  var r = {};
  r.browser = /Edg\/([\d.]+)/.test(ua) ? 'Edge ' + RegExp.$1
    : /OPR\/([\d.]+)/.test(ua) ? 'Opera ' + RegExp.$1
    : /Firefox\/([\d.]+)/.test(ua) ? 'Firefox ' + RegExp.$1
    : /Chrome\/([\d.]+)/.test(ua) ? 'Chrome ' + RegExp.$1
    : /Version\/([\d.]+).*Safari/.test(ua) ? 'Safari ' + RegExp.$1
    : '未知';
  r.engine = /Gecko\/|Firefox/.test(ua) && !/like Gecko/.test(ua) ? 'Gecko'
    : /AppleWebKit/.test(ua) && /Chrome|Edg|OPR/.test(ua) ? 'Blink'
    : /AppleWebKit/.test(ua) ? 'WebKit'
    : /Trident/.test(ua) ? 'Trident (IE)' : '未知';
  r.os = /Windows NT 10/.test(ua) ? 'Windows 10/11'
    : /Windows NT 6\.1/.test(ua) ? 'Windows 7'
    : /Windows/.test(ua) ? 'Windows'
    : /Mac OS X ([\d_]+)/.test(ua) ? 'macOS ' + RegExp.$1.replace(/_/g, '.')
    : /Android ([\d.]+)/.test(ua) ? 'Android ' + RegExp.$1
    : /iPhone|iPad/.test(ua) ? (/OS ([\d_]+)/.test(ua) ? 'iOS ' + RegExp.$1.replace(/_/g, '.') : 'iOS')
    : /Linux/.test(ua) ? 'Linux' : '未知';
  r.device = /Mobile|Android.*Mobile|iPhone/.test(ua) ? '📱 手机'
    : /iPad|Tablet/.test(ua) ? '💻 平板' : '🖥 桌面';
  r.bot = /bot|spider|crawl|slurp|bingpreview/i.test(ua) ? '🤖 是爬虫' : '否';
  r.wechat = /MicroMessenger/.test(ua);
  return r;
}
function run() {
  var r = parse(input.value);
  var rows = [
    ['浏览器', r.browser], ['内核', r.engine], ['操作系统', r.os],
    ['设备类型', r.device], ['爬虫', r.bot]
  ];
  if (r.wechat) rows.push(['特殊', '微信内置浏览器']);
  T.clearEl(box).appendChild(T.kvTable(rows));
}
input.addEventListener('input', T.debounce(run, 200));
app.appendChild(T.pane([T.field('User-Agent', input)], true));
app.appendChild(box);
app.appendChild(T.row([T.button('复制 UA', function () { T.copy(input.value); })]));
run();
''')

MAGIC_BYTES = r'''
var SIGS = [
  { sig: [0xFF, 0xD8, 0xFF], name: 'JPEG 图片', ext: 'jpg' },
  { sig: [0x89, 0x50, 0x4E, 0x47], name: 'PNG 图片', ext: 'png' },
  { sig: [0x47, 0x49, 0x46, 0x38], name: 'GIF 图片', ext: 'gif' },
  { sig: [0x42, 0x4D], name: 'BMP 图片', ext: 'bmp' },
  { sig: [0x25, 0x50, 0x44, 0x46], name: 'PDF 文档', ext: 'pdf' },
  { sig: [0x50, 0x4B, 0x03, 0x04], name: 'ZIP / Office 文档', ext: 'zip/docx/xlsx' },
  { sig: [0x52, 0x61, 0x72, 0x21], name: 'RAR 压缩包', ext: 'rar' },
  { sig: [0x37, 0x7A, 0xBC, 0xAF], name: '7Z 压缩包', ext: '7z' },
  { sig: [0x1F, 0x8B], name: 'Gzip 压缩', ext: 'gz' },
  { sig: [0x49, 0x44, 0x33], name: 'MP3 音频', ext: 'mp3' },
  { sig: [0x66, 0x4C, 0x61, 0x43], name: 'FLAC 音频', ext: 'flac' },
  { sig: [0x00, 0x00, 0x01, 0x00], name: 'ICO 图标', ext: 'ico' },
  { sig: [0x00, 0x00, 0x02, 0x00], name: 'CUR 光标', ext: 'cur' },
  { sig: [0x77, 0x4F, 0x46, 0x32], name: 'WOFF2 字体', ext: 'woff2' },
  { sig: [0x00, 0x01, 0x00, 0x00], name: 'TTF 字体', ext: 'ttf' },
  { sig: [0x4F, 0x54, 0x54, 0x4F], name: 'OTF 字体', ext: 'otf' },
  { sig: [0x1A, 0x45, 0xDF, 0xA3], name: 'Matroska / WebM', ext: 'mkv/webm' },
  { sig: [0x52, 0x49, 0x46, 0x46], name: 'RIFF 容器 (WAV/WebP/AVI)', ext: 'wav/webp/avi' },
  { sig: [0x49, 0x49, 0x2A, 0x00], name: 'TIFF (小端)', ext: 'tif' },
  { sig: [0x4D, 0x4D, 0x00, 0x2A], name: 'TIFF (大端)', ext: 'tif' },
  { sig: [0x53, 0x51, 0x4C, 0x69], name: 'SQLite 数据库', ext: 'db' }
];
'''

d('magic-bytes', '文件格式识别', 'Magic Bytes 检测文件真实格式（不看扩展名）', js=MAGIC_BYTES + r'''
var drop = T.msg('点击选择文件或拖拽到此处', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '30px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var box = T.el('div');
var inp = T.el('input', { type: 'file', style: 'display:none' });
document.body.appendChild(inp);
function detect(u8) {
  var results = [];
  SIGS.forEach(function (s) {
    var ok = s.sig.every(function (b, i) { return u8[i] === b; });
    if (ok) results.push(s.name + '（.' + s.ext + '）');
  });
  var hex = T.bytesToHex(u8.slice(0, 16)).toUpperCase().replace(/(..)/g, '$1 ').trim();
  return { results: results, hex: hex };
}
function handle(f) {
  var fr = new FileReader();
  fr.onload = function () {
    var u8 = new Uint8Array(fr.result.slice(0, 64));
    var r = detect(u8);
    T.clearEl(box).appendChild(T.kvTable([
      ['文件名', f.name],
      ['扩展名声称', f.type || '（浏览器未知）'],
      ['大小', T.fmtBytes(f.size)],
      ['文件头 (hex)', r.hex],
      ['真实格式', r.results.length ? '✓ ' + r.results.join(' / ') : '⚠ 未知格式（纯文本或其他）']
    ]));
  };
  fr.readAsArrayBuffer(f);
}
inp.addEventListener('change', function () { if (inp.files[0]) handle(inp.files[0]); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) {
  e.preventDefault();
  if (e.dataTransfer.files[0]) handle(e.dataTransfer.files[0]);
});
app.appendChild(drop);
app.appendChild(box);
''')

d('unzip', 'ZIP 解压查看', '在线解压 ZIP：浏览文件列表、预览文本、下载单个文件', js=r'''
var pick = T.el('input', { type: 'file', accept: '.zip', style: 'display:none' });
document.body.appendChild(pick);
var info = T.badge('—');
var box = T.el('div');
pick.addEventListener('change', function () {
  var f = pick.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    try {
      var entries = LU.Zip.read(new Uint8Array(fr.result));
      render(entries);
      info.textContent = f.name + ' · ' + entries.length + ' 项';
      info.className = 'badge ok';
    } catch (e) {
      T.toast('解压失败：' + e.message);
    }
  };
  fr.readAsArrayBuffer(f);
});
function render(entries) {
  T.clearEl(box);
  var rows = entries.map(function (e, i) {
    return [i + 1, e.name, e.isDir ? '📁 目录' : T.fmtBytes(e.size), e.method === 0 ? 'store' : 'deflate', e];
  });
  var table = T.refTable(['#', '文件名', '原始大小', '压缩', ''], rows.map(function (r) {
    return [r[0], r[1], r[2], r[3], r[4]];
  }), function (r) {
    var entry = r[4];
    if (entry.isDir) return;
    entry.getData().then(function (data) {
      T.download(entry.name.split('/').pop(), data);
    }).catch(function (err) { T.toast(err.message); });
  });
  box.appendChild(table);
  box.appendChild(T.el('p', { text: '点击行下载该文件（目录除外）', style: 'color:var(--ink2);font-size:12px' }));
}
app.appendChild(T.row([T.button('选择 ZIP 文件', function () { pick.click(); }, true), info]));
app.appendChild(box);
''')

d('websocket-test', 'WebSocket 测试', '在线 WebSocket 连接调试：收发消息与事件日志', js=r'''
var url = T.input('wss://echo.websocket.org', { class: 'grow mono' });
var log = T.el('div', { class: 'output', style: 'min-height:220px;white-space:pre-wrap;font-family:var(--font-mono)' });
var status = T.badge('未连接');
var msgIn = T.input('', { class: 'grow mono', placeholder: '要发送的消息…' });
var ws = null;
function logLine(text, cls) {
  var line = T.el('div', { text: '[' + new Date().toLocaleTimeString('zh-CN') + '] ' + text, style: 'padding:1px 0;color:' + (cls === 'err' ? 'var(--err)' : cls === 'out' ? 'var(--accent)' : 'var(--ok-text)') });
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}
function connect() {
  if (ws) { ws.close(); }
  logLine('连接 ' + url.value + ' …');
  try { ws = new WebSocket(url.value); }
  catch (e) { logLine('URL 无效：' + e.message, 'err'); return; }
  ws.onopen = function () { status.textContent = '✓ 已连接'; status.className = 'badge ok'; logLine('✓ 连接已建立'); };
  ws.onmessage = function (e) { logLine('← 收到: ' + (typeof e.data === 'string' ? e.data.slice(0, 500) : '[二进制 ' + e.data.size + ' 字节]')); };
  ws.onerror = function () { logLine('⚠ 连接错误', 'err'); };
  ws.onclose = function (e) { status.textContent = '已断开 (' + e.code + ')'; status.className = 'badge warn'; logLine('连接关闭 code=' + e.code + ' ' + (e.reason || '')); };
}
function send() {
  if (!ws || ws.readyState !== 1) { T.toast('请先连接'); return; }
  ws.send(msgIn.value);
  logLine('→ 发送: ' + msgIn.value, 'out');
  msgIn.value = '';
}
app.appendChild(T.row([T.el('span', { text: '地址' }), url, T.button('连接', connect, true), status]));
app.appendChild(log);
app.appendChild(T.row([msgIn, T.button('发送', send), T.button('清空日志', function () { T.clearEl(log); }),
  T.button('断开', function () { if (ws) ws.close(); })]));
msgIn.addEventListener('keydown', function (e) { if (e.key === 'Enter') send(); });
''')

d('csr-gen', 'CSR 证书生成', '生成私钥 + CSR（证书签名请求），用于 SSL 证书申请', js=r'''
var cn = T.input('www.example.com', { class: 'grow mono', placeholder: 'Common Name（域名）' });
var org = T.input('My Company', { class: 'grow mono', placeholder: '组织 O（可选）' });
var bits = T.select([{value:'2048',label:'RSA-2048'},{value:'4096',label:'RSA-4096'}],'2048');
var keyOut = T.out('私钥 PEM（务必保密）…');
keyOut.setAttribute('rows', '6');
var csrOut = T.out('CSR PEM…');
csrOut.setAttribute('rows', '6');
function encLen(n) {
  if (n < 128) return new Uint8Array([n]);
  var bytes = [];
  while (n > 0) { bytes.unshift(n & 255); n >>= 8; }
  return new Uint8Array([0x80 | bytes.length].concat(bytes));
}
function tlv(tag, content) {
  var out = new Uint8Array(1 + encLen(content.length).length + content.length);
  out[0] = tag;
  out.set(encLen(content.length), 1);
  out.set(content, 1 + encLen(content.length).length);
  return out;
}
function seq() { return tlv(0x30, concat(Array.from(arguments))); }
function set() { return tlv(0x31, concat(Array.from(arguments))); }
function int(b) { return tlv(0x02, b); }
function oid(nums) {
  var out = [nums[0] * 40 + nums[1]];
  for (var i = 2; i < nums.length; i++) {
    var v = nums[i];
    var tmp = [v & 0x7f];
    v >>= 7;
    while (v > 0) { tmp.unshift((v & 0x7f) | 0x80); v >>= 7; }
    out = out.concat(tmp);
  }
  return tlv(0x06, new Uint8Array(out));
}
function str2(tag, s) { return tlv(tag, T.textToBytes(s)); }
function nameEntry(oidArr, value) {
  return set(seq(oid(oidArr), str2(0x0c, value)));
}
function concat(arrs) {
  var len = arrs.reduce(function (s, a) { return s + a.length; }, 0);
  var out = new Uint8Array(len), off = 0;
  arrs.forEach(function (a) { out.set(a, off); off += a.length; });
  return out;
}
function toPem(u8, label) {
  return '-----BEGIN ' + label + '-----\n' + T.bytesToB64(u8).match(/.{1,64}/g).join('\n') + '\n-----END ' + label + '-----';
}
T.button('生成密钥对 + CSR', function () {
  if (!cn.value) { T.toast('请填写域名'); return; }
  T.toast('生成中…');
  crypto.subtle.generateKey(
    { name: 'RSASSA-PKCS1-v1_5', modulusLength: +bits.value, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
    true, ['sign']).then(function (kp) {
    return Promise.all([
      crypto.subtle.exportKey('pkcs8', kp.privateKey),
      crypto.subtle.exportKey('spki', kp.publicKey),
      Promise.resolve(kp)
    ]);
  }).then(function (res) {
    var pk8 = res[0], spki = res[1], kp = res[2];
    keyOut.value = toPem(new Uint8Array(pk8), 'PRIVATE KEY');
    var attrs = seq(
      nameEntry([2, 5, 4, 3], cn.value));
    if (org.value) attrs = seq(nameEntry([2, 5, 4, 3], cn.value), nameEntry([2, 5, 4, 10], org.value));
    var tbs = seq(
      int(new Uint8Array([0])),
      seq(oid([1, 2, 840, 113549, 1, 1, 11]), tlv(0x05, new Uint8Array(0))),
      attrs,
      new Uint8Array(spki));
    return crypto.subtle.sign('RSASSA-PKCS1-v1_5', kp.privateKey, tbs).then(function (sig) {
      var csr = seq(tbs, seq(oid([1, 2, 840, 113549, 1, 1, 11]), tlv(0x05, new Uint8Array(0))), tlv(0x03, concat([new Uint8Array([0]), new Uint8Array(sig)])));
      csrOut.value = toPem(new Uint8Array(csr), 'CERTIFICATE REQUEST');
      T.toast('生成完成');
    });
  }).catch(function (e) { T.toast('失败：' + e.message); });
}, true)
''')

d('html-preview', 'HTML 实时预览', '实时 HTML 代码预览（沙箱 iframe，安全隔离）', js=r'''
var input = T.textarea('<h1>Hello</h1>\n<p>在左侧修改代码，右侧实时预览。</p>\n<style>h1{color:#1744E8}</style>', true);
input.value = '<h1>Hello</h1>\n<p>在左侧修改代码，右侧实时预览。</p>\n<style>h1{color:#1744E8}</style>';
input.style.minHeight = '300px';
var frame = T.el('iframe', { sandbox: 'allow-scripts', style: 'width:100%;height:356px;border:1px solid var(--line);border-radius:8px;background:#fff' });
function run() { frame.srcdoc = input.value; }
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('HTML', input), T.el('div', { class: 'field' }, [T.el('span', { text: '预览（沙箱）' }), frame])]));
app.appendChild(T.row([T.button('打开独立标签页', function () {
  var w = window.open('', '_blank');
  w.document.write(input.value);
  w.document.close();
})]));
run();
''')

d('css-preview', 'CSS 实时预览', '实时 CSS 效果预览，自带示例 DOM', js=r'''
var input = T.textarea('.card {\n  background: linear-gradient(135deg, #1744E8, #7BC0E5);\n  border-radius: 16px;\n  padding: 24px;\n  color: #fff;\n  box-shadow: 0 10px 30px rgba(23,68,232,.3);\n  transition: transform .3s;\n}\n.card:hover { transform: translateY(-6px); }', true);
input.value = '.card {\n  background: linear-gradient(135deg, #1744E8, #7BC0E5);\n  border-radius: 16px;\n  padding: 24px;\n  color: #fff;\n  box-shadow: 0 10px 30px rgba(23,68,232,.3);\n  transition: transform .3s;\n}\n.card:hover { transform: translateY(-6px); }';
var frame = T.el('iframe', { sandbox: 'allow-scripts', style: 'width:100%;height:300px;border:1px solid var(--line);border-radius:8px;background:#fff' });
var DEMO = '<div class="card"><h2>CSS 卡片</h2><p>在左侧修改样式，右侧实时预览。</p><button>按钮</button></div><div class="card" style="margin-top:12px"><h2>第二张</h2><p>样式同时作用于两个元素。</p></div>';
function run() {
  frame.srcdoc = '<style>' + input.value + '</style><body style="font-family:system-ui;padding:16px;background:#FBFBFA">' + DEMO;
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('CSS', input), T.el('div', { class: 'field' }, [T.el('span', { text: '预览' }), frame])]));
run();
''')

d('js-sandbox', 'JS 沙箱执行', '安全的 JS 代码执行：捕获 console 输出与返回值', js=r'''
var input = T.textarea('// 试试：\nconst arr = [1,2,3].map(x => x * 2);\nconsole.log("数组:", arr);\nconsole.table ? null : null;\nreturn arr.reduce((a,b)=>a+b, 0);', true);
input.value = '// 试试：\nconst arr = [1,2,3].map(x => x * 2);\nconsole.log("数组:", arr);\nconsole.table ? null : null;\nreturn arr.reduce((a,b)=>a+b, 0);';
input.value = 'const arr = [1,2,3].map(x => x * 2);\nconsole.log("数组:", arr);\nreturn arr.reduce((a, b) => a + b, 0);';
input.style.minHeight = '180px';
var output = T.el('div', { class: 'output dark', style: 'min-height:180px;white-space:pre-wrap;font-family:var(--font-mono)' });
function run() {
  T.clearEl(output);
  var logs = [];
  var fakeConsole = {
    log: function () { logs.push(Array.from(arguments).map(function (a) { return typeof a === 'object' ? JSON.stringify(a) : String(a); }).join(' ')); },
    warn: function () { logs.push('⚠ ' + Array.from(arguments).join(' ')); },
    error: function () { logs.push('✗ ' + Array.from(arguments).join(' ')); },
    info: function () { this.log.apply(this, arguments); }
  };
  try {
    var fn = new Function('console', 'window', 'document', '"use strict";' + input.value);
    var result = fn(fakeConsole, undefined, undefined);
    logs.forEach(function (l) {
      output.appendChild(T.el('div', { text: l, style: 'color:var(--code-text);opacity:.9' }));
    });
    if (result !== undefined) {
      output.appendChild(T.el('div', { text: '⇒ 返回: ' + (typeof result === 'object' ? JSON.stringify(result) : String(result)), style: 'color:#98c379;margin-top:8px' }));
    }
    if (!logs.length && result === undefined) output.textContent = '(无输出)';
  } catch (e) {
    output.appendChild(T.el('div', { text: '✗ ' + e.message, style: 'color:#e74c3c' }));
  }
}
app.appendChild(T.pane([T.field('JS 代码（支持 return）', input)], true));
app.appendChild(T.row([T.button('运行 ▶', run, true), T.el('span', { text: '沙箱中 window/document 不可用，仅纯计算' })]));
app.appendChild(T.el('span', { text: '控制台输出', class: 'field' }));
app.appendChild(output);
run();
''')

EXIF_JS = r'''
function parseExif(buf) {
  var dv = new DataView(buf);
  if (dv.getUint16(0) !== 0xFFD8) return null;
  var offset = 2;
  var tiffStart = -1;
  while (offset < dv.byteLength - 4) {
    if (dv.getUint16(offset) !== 0xFFE1) {
      if (dv.getUint16(offset) === 0xFFDA) break;
      offset += 2 + dv.getUint16(offset + 2);
    } else {
      if (dv.getUint32(offset + 4) !== 0x45786966) break;
      tiffStart = offset + 10;
      break;
    }
  }
  if (tiffStart < 0) return null;
  var little = dv.getUint16(tiffStart) === 0x4949;
  function get16(off) { return dv.getUint16(off, little); }
  function get32(off) { return dv.getUint32(off, little); }
  var ifd0 = tiffStart + get32(tiffStart + 4);
  var TAGS = {
    0x010F: '制造商', 0x0110: '型号', 0x0112: '方向', 0x0132: '拍摄时间',
    0x013B: '作者', 0x8298: '版权', 0x8769: '_exifIFD', 0x8825: '_gpsIFD'
  };
  var EXIF_TAGS = {
    0x829A: '曝光时间', 0x829D: '光圈值 F', 0x8827: 'ISO', 0x9003: '拍摄时间',
    0x920A: '焦距', 0xA002: '像素宽度', 0xA003: '像素高度', 0x9209: '闪光灯', 0xA434: '镜头型号'
  };
  var ORIENT = { 1: '正常', 3: '旋转180°', 6: '需顺时针旋转90°', 8: '需逆时针旋转90°' };
  var out = {};
  function readTag(off, table) {
    var tag = get16(off);
    var type = get16(off + 2);
    var num = get32(off + 4);
    var sizes = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8 };
    var size = (sizes[type] || 1) * num;
    var valOff = size > 4 ? tiffStart + get32(off + 8) : off + 8;
    if (type === 2) {
      var s = '';
      for (var i = 0; i < num - 1; i++) s += String.fromCharCode(dv.getUint8(valOff + i));
      return s;
    }
    if (type === 3) return get16(valOff);
    if (type === 4) return get32(valOff);
    if (type === 5 || type === 10) {
      var n1 = get32(valOff), d1 = get32(valOff + 4);
      return d1 ? +(n1 / d1).toFixed(4) : null;
    }
    return get32(valOff);
  }
  var entries = get16(ifd0);
  for (var i = 0; i < entries; i++) {
    var off = ifd0 + 2 + i * 12;
    var tag = get16(off);
    var name = TAGS[tag];
    if (!name) continue;
    if (name === '_exifIFD' || name === '_gpsIFD') continue;
    var v = readTag(off);
    if (tag === 0x0112) v = ORIENT[v] || v;
    if (v != null && v !== '') out[name] = String(v);
  }
  for (i = 0; i < entries; i++) {
    off = ifd0 + 2 + i * 12;
    if (get16(off) === 0x8769) {
      var exifOff = tiffStart + get32(off + 8);
      var n2 = get16(exifOff);
      for (var j = 0; j < n2; j++) {
        var off2 = exifOff + 2 + j * 12;
        var t2 = get16(off2);
        if (EXIF_TAGS[t2]) {
          var v2 = readTag(off2);
          if (t2 === 0x829A) v2 = v2 + ' 秒';
          if (t2 === 0x829D && typeof v2 === 'number') v2 = 'F' + v2;
          if (t2 === 0x920A && typeof v2 === 'number') v2 = v2 + ' mm';
          if (v2 != null) out[EXIF_TAGS[t2]] = String(v2);
        }
      }
    }
  }
  return out;
}
'''

d('exif-viewer', 'EXIF 查看器', '上传图片查看 EXIF 元数据（相机 / 参数 / 方向 / 时间）', js=EXIF_JS + r'''
var drop = T.msg('点击选择 JPEG 图片或拖拽到此处', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '30px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var preview = T.el('img', { style: 'max-width:100%;max-height:300px;border-radius:8px;display:none' });
var box = T.el('div');
var inp = T.el('input', { type: 'file', accept: 'image/jpeg,image/*', style: 'display:none' });
document.body.appendChild(inp);
inp.addEventListener('change', function () { if (inp.files[0]) handle(inp.files[0]); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) {
  e.preventDefault();
  if (e.dataTransfer.files[0]) handle(e.dataTransfer.files[0]);
});
function handle(f) {
  var fr = new FileReader();
  fr.onload = function () {
    preview.src = fr.result;
    preview.style.display = '';
    var exif = parseExif(fr.result);
    T.clearEl(box);
    if (!exif || !Object.keys(exif).length) {
      box.appendChild(T.msg('未找到 EXIF 数据（可能已被清除，或是 PNG/WebP 等非 JPEG 格式）', ''));
      return;
    }
    box.appendChild(T.kvTable(Object.keys(exif).map(function (k) { return [k, exif[k]]; })));
  };
  fr.readAsArrayBuffer(f);
}
app.appendChild(drop);
app.appendChild(preview);
app.appendChild(box);
''')

d('image-compress', '图片压缩', '客户端图片压缩：质量 / 最大宽高可调，对比压缩前后体积', js=r'''
var quality = T.range(0.1, 0.95, 0.05, 0.7);
var qualityLabel = T.el('b', { text: '70%' });
var maxW = T.num(1920, { min: 100, step: 10, style: 'width:100px' });
var format = T.select([{value:'image/jpeg',label:'JPEG'},{value:'image/webp',label:'WebP'},{value:'image/png',label:'PNG'}],'image/jpeg');
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '26px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var before = T.el('img', { style: 'max-width:100%;border-radius:8px;border:1px solid var(--line);display:none' });
var after = T.el('img', { style: 'max-width:100%;border-radius:8px;border:1px solid var(--line);display:none' });
var compare = T.el('div', { class: 'row', style: 'align-items:flex-start' });
var result = T.badge('—');
var outBlob = null;
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
function handle(f) {
  before.src = URL.createObjectURL(f);
  before.style.display = '';
  var img = new Image();
  img.onload = function () {
    var canvas = T.el('canvas');
    var scale = Math.min(1, +maxW.value / img.width);
    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);
    var ctx = canvas.getContext('2d');
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(function (b) {
      outBlob = b;
      after.src = URL.createObjectURL(b);
      after.style.display = '';
      var saved = (1 - b.size / f.size) * 100;
      result.textContent = T.fmtBytes(f.size) + ' → ' + T.fmtBytes(b.size) + '（' + (saved >= 0 ? '省 ' : '增 ') + Math.abs(saved).toFixed(1) + '%）';
      result.className = 'badge ' + (saved >= 0 ? 'ok' : 'warn');
    }, format.value, +quality.value);
  };
  img.src = before.src;
}
inp.addEventListener('change', function () { if (inp.files[0]) handle(inp.files[0]); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) handle(e.dataTransfer.files[0]); });
[quality, maxW, format].forEach(function (el) {
  el.addEventListener('input', function () {
    qualityLabel.textContent = Math.round(quality.value * 100) + '%';
    if (inp.files[0]) handle(inp.files[0]);
  });
});
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '质量' }), quality, qualityLabel, T.el('span', { text: '最大宽' }), maxW, format]));
compare.appendChild(T.el('div', { class: 'field' }, [T.el('span', { text: '原图' }), before]));
compare.appendChild(T.el('div', { class: 'field' }, [T.el('span', { text: '压缩后' }), after]));
app.appendChild(compare);
app.appendChild(T.row([result, T.button('下载压缩图', function () {
  if (outBlob) T.download('compressed.' + (format.value === 'image/webp' ? 'webp' : format.value === 'image/png' ? 'png' : 'jpg'), outBlob);
}, true)]));
''')

d('video2gif', '视频转 GIF', '客户端视频转 GIF：选片段 / 帧率 / 尺寸，纯浏览器处理', js=r'''
var pick = T.el('input', { type: 'file', accept: 'video/*', style: 'display:none' });
document.body.appendChild(pick);
var video = T.el('video', { controls: '', muted: '', style: 'max-width:100%;max-height:260px;border-radius:8px;display:none' });
var fps = T.select([{value:'8',label:'8 帧/秒'},{value:'12',label:'12 帧/秒'},{value:'15',label:'15 帧/秒'}],'12');
var width = T.select([{value:'320',label:'宽 320px'},{value:'480',label:'宽 480px'},{value:'240',label:'宽 240px'}],'320');
var maxFrames = T.select([{value:'60',label:'最长 60 帧'},{value:'120',label:'最长 120 帧'},{value:'200',label:'最长 200 帧'}],'120');
var status = T.badge('—');
var bar = T.el('div', { style: 'height:5px;background:var(--line);border-radius:3px;overflow:hidden;display:none' });
var fill = T.el('div', { style: 'height:100%;width:0;background:var(--accent)' });
bar.appendChild(fill);
var outGif = T.el('img', { style: 'max-width:100%;border-radius:8px;border:1px solid var(--line);display:none' });
var gifBlob = null;
pick.addEventListener('change', function () {
  var f = pick.files[0];
  if (!f) return;
  video.src = URL.createObjectURL(f);
  video.style.display = '';
  status.textContent = '视频已加载，播放到起点后点"生成 GIF"';
  status.className = 'badge blue';
});
app.appendChild(T.row([T.button('选择视频', function () { pick.click(); }, true)]));
app.appendChild(video);
app.appendChild(T.row([T.el('span', { text: '帧率' }), fps, T.el('span', { text: '宽度' }), width, T.el('span', { text: '帧数上限' }), maxFrames,
  T.button('从当前位置生成 GIF', function () {
    if (!video.src) { T.toast('请先选择视频'); return; }
    generate();
  }, true)]));
app.appendChild(bar);
app.appendChild(outGif);
app.appendChild(T.row([status, T.button('下载 GIF', function () {
  if (gifBlob) T.download('video.gif', gifBlob);
}, true)]));
function generate() {
  var frameRate = +fps.value;
  var W = +width.value;
  var H = Math.round(video.videoHeight / video.videoWidth * W);
  var limit = +maxFrames.value;
  var frames = [];
  var canvas = T.el('canvas');
  canvas.width = W;
  canvas.height = H;
  var ctx = canvas.getContext('2d', { willReadFrequently: true });
  status.textContent = '抽帧中…';
  bar.style.display = '';
  var i = 0;
  var interval = 1000 / frameRate;
  var t0 = video.currentTime;
  function step() {
    if (i >= limit || video.currentTime >= video.duration - 0.05) {
      status.textContent = '编码 GIF 中…';
      fill.style.width = '100%';
      setTimeout(function () {
        gifBlob = LU.Gif.encode(frames, { colors: 200 });
        outGif.src = URL.createObjectURL(gifBlob);
        outGif.style.display = '';
        status.textContent = '✓ 完成：' + frames.length + ' 帧 · ' + T.fmtBytes(gifBlob.size);
        status.className = 'badge ok';
        bar.style.display = 'none';
      }, 50);
      return;
    }
    ctx.drawImage(video, 0, 0, W, H);
    frames.push({ data: ctx.getImageData(0, 0, W, H).data, width: W, height: H, delay: interval });
    i++;
    fill.style.width = (i / limit * 100) + '%';
    status.textContent = '抽帧中 ' + i + '/' + limit;
    video.currentTime = t0 + i * interval;
    video.addEventListener('seeked', function onseek() {
      video.removeEventListener('seeked', onseek);
      requestAnimationFrame(step);
    }, { once: true });
  }
  step();
}
''')

d('audio-record', '录音机', '浏览器录音（麦克风）→ WebM 音频下载，需授权', js=r'''
var status = T.badge('未开始');
var timeEl = T.stat('00:00', '时长');
var list = T.el('div');
var mediaRecorder = null, chunks = [], timer = 0, seconds = 0;
function startRec() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = function (e) { chunks.push(e.data); };
    mediaRecorder.onstop = function () {
      var blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      var url = URL.createObjectURL(blob);
      var row = T.el('div', { style: 'display:flex;gap:12px;align-items:center;padding:10px 4px;border-bottom:1px solid var(--line)' });
      var audio = T.el('audio', { controls: '', src: url, style: 'flex:1;max-width:420px' });
      row.appendChild(audio);
      row.appendChild(T.el('span', { text: T.fmtBytes(blob.size), style: 'color:var(--ink2);font-size:12px' }));
      row.appendChild(T.button('下载', function () { T.download('recording-' + Date.now() + '.webm', blob); }));
      list.insertBefore(row, list.firstChild);
      stream.getTracks().forEach(function (t) { t.stop(); });
    };
    mediaRecorder.start();
    status.textContent = '🔴 录音中';
    status.className = 'badge warn';
    seconds = 0;
    timer = setInterval(function () {
      seconds++;
      timeEl.firstChild.textContent = T.pad2(Math.floor(seconds / 60)) + ':' + T.pad2(seconds % 60);
    }, 1000);
  }).catch(function (e) { T.toast('无法访问麦克风：' + e.message); });
}
function stopRec() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    clearInterval(timer);
    status.textContent = '已停止';
    status.className = 'badge';
  }
}
app.appendChild(T.row([T.button('开始录音', startRec, true), T.button('停止', stopRec), timeEl, status]));
app.appendChild(list);
app.appendChild(T.msg('需要浏览器授权麦克风；输出为 WebM/Opus 格式（各浏览器通用）。', ''));
''')

d('http-builder', 'HTTP 请求构建', '构建 HTTP 请求报文：方法 / 头 / 体，生成原始报文并可实际发送', js=r'''
var method = T.select(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'], 'GET');
var url = T.input('https://httpbin.org/get', { class: 'grow mono' });
var headersIn = T.textarea('Content-Type: application/json\nX-Request-Id: freellm-001', true);
headersIn.value = 'Content-Type: application/json\nX-Request-Id: freellm-001';
headersIn.setAttribute('rows', '4');
var bodyIn = T.textarea('{"q": "freellm"}', true);
bodyIn.value = '{"q": "freellm"}';
bodyIn.setAttribute('rows', '4');
var rawOut = T.out('');
var respBox = T.el('div', { class: 'output', style: 'min-height:120px;white-space:pre-wrap' });
function build() {
  var lines = [method.value + ' ' + (function () { try { return new URL(url.value).pathname + new URL(url.value).search; } catch (e) { return '/'; } })() + ' HTTP/1.1'];
  try { lines.push('Host: ' + new URL(url.value).host); } catch (e) {}
  headersIn.value.split('\n').forEach(function (l) { if (l.trim()) lines.push(l.trim()); });
  if (bodyIn.value.trim() && method.value !== 'GET') {
    lines.push('Content-Length: ' + new Blob([bodyIn.value]).size);
    lines.push('');
    lines.push(bodyIn.value);
  }
  rawOut.value = lines.join('\n');
}
function send() {
  var headers = {};
  headersIn.value.split('\n').forEach(function (l) {
    var i = l.indexOf(':');
    if (i > 0) headers[l.slice(0, i).trim()] = l.slice(i + 1).trim();
  });
  var opts = { method: method.value, headers: headers };
  if (bodyIn.value.trim() && method.value !== 'GET') opts.body = bodyIn.value;
  var t0 = performance.now();
  respBox.textContent = '请求中…';
  fetch(url.value, opts).then(function (res) {
    return res.text().then(function (text) {
      var ms = Math.round(performance.now() - t0);
      respBox.textContent = 'HTTP ' + res.status + ' ' + res.statusText + '（' + ms + ' ms）\n\n' + text.slice(0, 4000);
    });
  }).catch(function (e) {
    respBox.textContent = '⚠ 请求失败：' + e.message + '\n（目标站点可能不允许跨域 CORS）';
  });
}
[method, url, headersIn, bodyIn].forEach(function (el) { el.addEventListener('input', build); });
app.appendChild(T.row([method, url]));
app.appendChild(T.pane([T.field('Headers（每行一个）', headersIn), T.field('Body', bodyIn)]));
app.appendChild(T.el('span', { text: '原始报文', class: 'field' }));
app.appendChild(rawOut);
app.appendChild(T.row([T.button('发送请求', send, true), T.btnCopy(function () { return rawOut.value; })]));
app.appendChild(T.el('span', { text: '响应', class: 'field' }));
app.appendChild(respBox);
build();
''')

d('api-test', 'API 测试工具', '离线 API 请求模拟：方法 / URL / 头 / 体，查看响应与耗时', js=r'''
var method = T.select(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], 'GET');
var url = T.input('https://httpbin.org/json', { class: 'grow mono' });
var headersIn = T.textarea('Accept: application/json', true);
headersIn.value = 'Accept: application/json';
headersIn.setAttribute('rows', '3');
var bodyIn = T.textarea('', true);
bodyIn.value = '';
bodyIn.setAttribute('rows', '4');
var status = T.badge('—');
var timing = T.el('span', { style: 'color:var(--ink2);font-size:12px' });
var respHeaders = T.el('div');
var respBody = T.el('div', { class: 'output', style: 'min-height:160px;white-space:pre-wrap' });
function send() {
  var headers = {};
  headersIn.value.split('\n').forEach(function (l) {
    var i = l.indexOf(':');
    if (i > 0) headers[l.slice(0, i).trim()] = l.slice(i + 1).trim();
  });
  var opts = { method: method.value, headers: headers };
  if (bodyIn.value.trim() && method.value !== 'GET') opts.body = bodyIn.value;
  status.textContent = '请求中…';
  status.className = 'badge blue';
  var t0 = performance.now();
  fetch(url.value, opts).then(function (res) {
    var ms = Math.round(performance.now() - t0);
    status.textContent = 'HTTP ' + res.status;
    status.className = 'badge ' + (res.ok ? 'ok' : 'warn');
    timing.textContent = '耗时 ' + ms + ' ms · ' + (res.headers.get('content-type') || '');
    T.clearEl(respHeaders);
    var rows = [];
    res.headers.forEach(function (v, k) { rows.push([k, v]); });
    respHeaders.appendChild(T.refTable(['响应头', '值'], rows));
    return res.text();
  }).then(function (text) {
    try { respBody.textContent = JSON.stringify(JSON.parse(text), null, 2); }
    catch (e) { respBody.textContent = text.slice(0, 5000); }
  }).catch(function (e) {
    status.textContent = '请求失败';
    status.className = 'badge warn';
    respBody.textContent = e.message + '\n\n提示：浏览器直连受 CORS 限制，目标 API 需允许跨域。';
  });
}
app.appendChild(T.row([method, url, T.button('发送', send, true)]));
app.appendChild(T.pane([T.field('请求头', headersIn), T.field('请求体', bodyIn)]));
app.appendChild(T.row([status, timing]));
app.appendChild(T.el('span', { text: '响应头', class: 'field' }));
app.appendChild(respHeaders);
app.appendChild(T.el('span', { text: '响应体', class: 'field' }));
app.appendChild(respBody);
''')

d('snippets', '代码片段管理', '保存和管理常用代码片段（浏览器本地存储）', js=r'''
var titleIn = T.input('', { class: 'grow', placeholder: '片段标题' });
var langIn = T.select(['javascript', 'python', 'css', 'html', 'sql', 'shell', 'other'], 'javascript');
var bodyIn = T.textarea('粘贴代码…', true);
bodyIn.style.minHeight = '140px';
var list = T.el('div');
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-snippets') || '[]'); } catch (e) {}
function save() { localStorage.setItem('freellm-snippets', JSON.stringify(items)); }
function render() {
  T.clearEl(list);
  if (!items.length) { list.appendChild(T.el('p', { text: '暂无片段。', style: 'color:var(--ink3)' })); return; }
  items.forEach(function (s, i) {
    var card = T.el('div', { style: 'border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:10px;background:var(--surface)' });
    var head = T.row([T.el('b', { text: s.title }), T.badge(s.lang), T.el('span', { style: 'flex:1' }),
      T.button('复制', function () { T.copy(s.code); }),
      T.button('载入', function () { titleIn.value = s.title; langIn.value = s.lang; bodyIn.value = s.code; }),
      T.button('删除', function () { items.splice(i, 1); save(); render(); })]);
    head.style.marginBottom = '8px';
    card.appendChild(head);
    var pre = T.el('div', { class: 'output', style: 'max-height:160px;white-space:pre;font-size:12px', text: s.code.slice(0, 600) });
    card.appendChild(pre);
    list.appendChild(card);
  });
}
app.appendChild(T.row([titleIn, langIn]));
app.appendChild(bodyIn);
app.appendChild(T.row([T.button('保存片段', function () {
  if (!titleIn.value || !bodyIn.value.trim()) { T.toast('请填写标题与代码'); return; }
  items.unshift({ title: titleIn.value, lang: langIn.value, code: bodyIn.value, ts: Date.now() });
  save();
  render();
  titleIn.value = '';
  bodyIn.value = '';
  T.toast('已保存');
}, true), T.el('span', { text: '片段保存在浏览器本地' })]));
app.appendChild(T.el('span', { text: '已保存片段', class: 'field' }));
app.appendChild(list);
render();
''')

d('color-contrast', '颜色对比度', 'WCAG 对比度批量检测：前景 × 多个背景一键评估', js=r'''
var fg = T.color('#2F3437');
var bgsIn = T.textarea('#FBFBFA\n#FFFFFF\n#1744E8\n#F9F9F8', true);
bgsIn.value = '#FBFBFA\n#FFFFFF\n#1744E8\n#F9F9F8';
bgsIn.setAttribute('rows', '5');
var box = T.el('div');
var sample = T.el('div', { style: 'padding:20px;border-radius:10px;border:1px solid var(--line);margin-bottom:12px' });
function run() {
  var f = LU.Color.parse(fg.value);
  sample.style.color = fg.value;
  sample.innerHTML = '示例文字 Sample Text 18px';
  var rows = [];
  bgsIn.value.split('\n').map(function (s) { return s.trim(); }).filter(Boolean).forEach(function (bgStr) {
    try {
      var b = LU.Color.parse(bgStr);
      var ratio = LU.Color.contrast(f, b);
      var grade = ratio >= 7 ? 'AAA ✓' : ratio >= 4.5 ? 'AA ✓' : ratio >= 3 ? 'AA 大字 ✓' : '✗ 不达标';
      rows.push([bgStr, ratio.toFixed(2) + ' : 1', grade]);
    } catch (e) {
      rows.push([bgStr, '—', '无法解析']);
    }
  });
  T.clearEl(box).appendChild(T.refTable(['背景色', '对比度', '评级'], rows, function (r) { T.copy(r[0]); }));
}
[fg, bgsIn].forEach(function (el) { el.addEventListener('input', T.debounce(run, 250)); });
app.appendChild(T.row([T.el('span', { text: '前景色' }), fg]));
app.appendChild(T.pane([T.field('背景色列表（每行一个）', bgsIn), T.el('div', { class: 'field' }, [T.el('span', { text: '示例' }), sample])]));
app.appendChild(box);
run();
''')

d('svg-editor', 'SVG 在线编辑', '可视化编辑 SVG 图形：改属性 / 实时预览 / 导出', js=r'''
var input = T.textarea('<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160" viewBox="0 0 240 160">\n  <rect x="10" y="10" width="100" height="60" rx="10" fill="#1744E8"/>\n  <circle cx="180" cy="80" r="50" fill="#FFB88C"/>\n  <text x="120" y="140" text-anchor="middle" font-size="16" fill="#787774">SVG 编辑器</text>\n</svg>', true);
input.value = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160" viewBox="0 0 240 160">\n  <rect x="10" y="10" width="100" height="60" rx="10" fill="#1744E8"/>\n  <circle cx="180" cy="80" r="50" fill="#FFB88C"/>\n  <text x="120" y="140" text-anchor="middle" font-size="16" fill="#787774">SVG 编辑器</text>\n</svg>';
input.style.minHeight = '220px';
var preview = T.el('div', { class: 'output', style: 'min-height:220px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:auto' });
function run() {
  try {
    preview.innerHTML = input.value;
  } catch (e) { preview.textContent = '⚠ ' + e.message; }
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('SVG 源码', input), T.el('div', { class: 'field' }, [T.el('span', { text: '预览' }), preview])]));
app.appendChild(T.row([
  T.button('下载 SVG', function () { T.download('shape.svg', input.value, 'image/svg+xml'); }, true),
  T.button('复制源码', function () { T.copy(input.value); }),
  T.button('导出 PNG', function () {
    var svg = preview.querySelector('svg');
    if (!svg) return;
    var img = new Image();
    img.onload = function () {
      var c = T.el('canvas');
      c.width = img.width || 480;
      c.height = img.height || 320;
      c.getContext('2d').drawImage(img, 0, 0);
      T.dlCanvas(c, 'shape.png');
    };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(input.value);
  })
]));
run();
''')

d('icon-font', '图标字体生成', '多 SVG 合并为 Symbol 精灵图 + CSS 类（组件级图标方案）', js=r'''
var input = T.textarea('每个 SVG 一行或空行分隔，例如：\n<svg viewBox="0 0 24 24"><path d="M12 2 L22 12 L12 22 L2 12 Z"/></svg>\n<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>', true);
var prefix = T.input('icon', { class: 'grow mono' });
var output = T.out('');
var preview = T.el('div', { style: 'display:flex;gap:16px;flex-wrap:wrap;margin-top:12px' });
function run() {
  var svgs = input.value.split(/<\/svg>\s*/).filter(function (s) { return s.includes('<svg'); }).map(function (s) {
    if (!s.includes('</svg>')) s += '</svg>';
    return s;
  });
  T.clearEl(preview);
  if (!svgs.length) { output.value = ''; return; }
  var symbols = svgs.map(function (s, i) {
    var vb = (s.match(/viewBox="([^"]+)"/) || [null, '0 0 24 24'])[1];
    var inner = s.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
    return '<symbol id="' + prefix.value + '-' + (i + 1) + '" viewBox="' + vb + '">' + inner + '</symbol>';
  }).join('\n');
  var sprite = '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n' + symbols + '\n</svg>';
  var css = '.' + prefix.value + ' {\n  display: inline-block;\n  width: 24px;\n  height: 24px;\n  fill: currentColor;\n  vertical-align: middle;\n}';
  var uses = svgs.map(function (_, i) {
    return '<svg class="' + prefix.value + '"><use href="#' + prefix.value + '-' + (i + 1) + '"/></svg>';
  }).join('\n');
  output.value = '<!-- 1. 精灵图（放在 body 开头） -->\n' + sprite + '\n\n<!-- 2. CSS -->\n<style>\n' + css + '\n</style>\n\n<!-- 3. 使用 -->\n' + uses;
  var holder = T.el('div');
  holder.innerHTML = sprite + uses;
  Array.from(holder.querySelectorAll('svg:not([style])')).forEach(function (u) {
    u.style.cssText = 'width:32px;height:32px;fill:var(--accent);border:1px dashed var(--line);padding:6px;border-radius:8px';
    preview.appendChild(u);
  });
}
[input, prefix].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('SVG 集合', input)], true));
app.appendChild(T.row([T.el('span', { text: '类名前缀' }), prefix]));
app.appendChild(preview);
app.appendChild(T.pane([T.field('生成的精灵图代码', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; }), T.button('下载 sprite.html', function () { T.download('sprite.html', output.value, 'text/html'); })]));
run();
''')

d('font-subset', '字体子集化', '提取文本用到的字符 + 生成 unicode-range 按需加载方案', js=r'''
var fontPick = T.el('input', { type: 'file', accept: '.ttf,.otf,.woff,.woff2', style: 'display:none' });
document.body.appendChild(fontPick);
var textIn = T.textarea('输入实际会用到字符的文本。例如文章标题、菜单、按钮文字。\n字体文件只会显示统计信息；子集方案用 unicode-range 按需拆分。', true);
var rangeOut = T.out('');
var info = T.badge('—');
var fontName = T.input('MyFont', { class: 'grow mono' });
var chars = [];
function analyze() {
  var unique = Array.from(new Set(Array.from(textIn.value))).filter(function (c) { return /\S/.test(c); });
  chars = unique;
  var cps = unique.map(function (c) { return c.codePointAt(0); }).sort(function (a, b) { return a - b; });
  if (!cps.length) { rangeOut.value = ''; info.textContent = '输入文本后生成'; return; }
  var ranges = [];
  var start = cps[0], prev = cps[0];
  for (var i = 1; i <= cps.length; i++) {
    if (cps[i] !== prev + 1) {
      if (start === prev) ranges.push('U+' + start.toString(16).toUpperCase().padStart(4, '0'));
      else ranges.push('U+' + start.toString(16).toUpperCase().padStart(4, '0') + '-' + prev.toString(16).toUpperCase().padStart(4, '0'));
      start = cps[i];
    }
    prev = cps[i];
  }
  var rangeStr = ranges.join(', ');
  rangeOut.value = '/* 仅加载以下字符区间，浏览器按需下载字体 */\n@font-face {\n  font-family: "' + fontName.value + '";\n  src: url("./fonts/subset.woff2") format("woff2");\n  unicode-range: ' + rangeStr + ';\n  font-display: swap;\n}';
  info.textContent = '共 ' + unique.length + ' 个唯一字符 · ' + ranges.length + ' 个区间';
  info.className = 'badge ok';
}
fontPick.addEventListener('change', function () {
  var f = fontPick.files[0];
  if (f) {
    info.textContent = f.name + '（' + T.fmtBytes(f.size) + '）· 浏览器无法直接重打包字体，请配合 pyftsubset 使用';
    info.className = 'badge blue';
  }
});
[textIn, fontName].forEach(function (el) { el.addEventListener('input', T.debounce(analyze, 300)); });
app.appendChild(T.row([T.button('选择字体文件（查看信息）', function () { fontPick.click(); }), info]));
app.appendChild(T.pane([T.field('使用的文本', textIn)], true));
app.appendChild(T.row([T.el('span', { text: '字体族名' }), fontName]));
app.appendChild(T.pane([T.field('unicode-range 按需加载 CSS', rangeOut)], true));
app.appendChild(T.row([T.btnCopy(function () { return rangeOut.value; }), T.button('下载字符清单', function () {
  T.download('subset-chars.txt', chars.join(''));
}), T.el('span', { text: '完整子集化命令：pyftsubset font.ttf --text-file=chars.txt --flavor=woff2' })]));
analyze();
''')
