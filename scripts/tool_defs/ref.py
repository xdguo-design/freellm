# -*- coding: utf-8 -*-
"""速查参考类工具定义（静态表 + 搜索过滤）"""
from .registry import d

SEARCH_JS = r'''
function buildSearch(tableWrap) {
  var search = T.input('', { class: 'grow', placeholder: '搜索过滤…' });
  search.addEventListener('input', function () {
    var q = search.value.trim().toLowerCase();
    Array.from(tableWrap.querySelectorAll('tbody tr')).forEach(function (tr) {
      tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
  return search;
}
'''

d('http-status', 'HTTP 状态码', '全部 HTTP 状态码速查：1xx-5xx 分类释义', js=SEARCH_JS + r'''
var DATA = [
  ['100', 'Continue', '继续，客户端应继续请求', '1xx 信息'],
  ['101', 'Switching Protocols', '切换协议（如升级 WebSocket）', '1xx 信息'],
  ['200', 'OK', '请求成功', '2xx 成功'],
  ['201', 'Created', '已创建（POST/PUT 成功）', '2xx 成功'],
  ['202', 'Accepted', '已接受，处理中', '2xx 成功'],
  ['204', 'No Content', '成功但无返回体', '2xx 成功'],
  ['206', 'Partial Content', '范围请求成功（断点续传）', '2xx 成功'],
  ['301', 'Moved Permanently', '永久重定向', '3xx 重定向'],
  ['302', 'Found', '临时重定向', '3xx 重定向'],
  ['303', 'See Other', '用 GET 访问另一 URL', '3xx 重定向'],
  ['304', 'Not Modified', '缓存有效（协商缓存命中）', '3xx 重定向'],
  ['307', 'Temporary Redirect', '临时重定向（保持方法）', '3xx 重定向'],
  ['308', 'Permanent Redirect', '永久重定向（保持方法）', '3xx 重定向'],
  ['400', 'Bad Request', '请求语法错误', '4xx 客户端错误'],
  ['401', 'Unauthorized', '未认证（登录/Token）', '4xx 客户端错误'],
  ['402', 'Payment Required', '保留（付费）', '4xx 客户端错误'],
  ['403', 'Forbidden', '已认证但无权限', '4xx 客户端错误'],
  ['404', 'Not Found', '资源不存在', '4xx 客户端错误'],
  ['405', 'Method Not Allowed', 'HTTP 方法不允许', '4xx 客户端错误'],
  ['406', 'Not Acceptable', '无法满足 Accept 头', '4xx 客户端错误'],
  ['408', 'Request Timeout', '请求超时', '4xx 客户端错误'],
  ['409', 'Conflict', '资源冲突', '4xx 客户端错误'],
  ['410', 'Gone', '资源已永久删除', '4xx 客户端错误'],
  ['413', 'Payload Too Large', '请求体过大', '4xx 客户端错误'],
  ['415', 'Unsupported Media Type', '不支持的媒体类型', '4xx 客户端错误'],
  ['422', 'Unprocessable Entity', '语义错误（校验失败）', '4xx 客户端错误'],
  ['429', 'Too Many Requests', '请求过于频繁（限流）', '4xx 客户端错误'],
  ['451', 'Unavailable For Legal Reasons', '因法律原因不可用', '4xx 客户端错误'],
  ['500', 'Internal Server Error', '服务器内部错误', '5xx 服务器错误'],
  ['501', 'Not Implemented', '未实现', '5xx 服务器错误'],
  ['502', 'Bad Gateway', '网关收到无效响应', '5xx 服务器错误'],
  ['503', 'Service Unavailable', '服务不可用（过载/维护）', '5xx 服务器错误'],
  ['504', 'Gateway Timeout', '网关超时', '5xx 服务器错误'],
  ['505', 'HTTP Version Not Supported', 'HTTP 版本不支持', '5xx 服务器错误']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['状态码', '名称', '含义', '分类'], DATA));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('ascii', 'ASCII 对照表', '0-127 完整 ASCII 字符对照（十进制 / 十六进制 / 字符）', js=SEARCH_JS + r'''
var NAMES = { 0: 'NUL 空字符', 7: 'BEL 响铃', 8: 'BS 退格', 9: 'TAB 制表', 10: 'LF 换行', 13: 'CR 回车', 27: 'ESC 退出', 32: '空格', 127: 'DEL 删除' };
var rows = [];
for (var i = 0; i < 128; i++) {
  var ch = i < 32 || i === 127 ? '·' : String.fromCharCode(i);
  rows.push([i, '0x' + i.toString(16).toUpperCase().padStart(2, '0'), ch, NAMES[i] || (i < 32 ? '控制字符' : '')]);
}
var wrap = T.el('div');
wrap.appendChild(T.refTable(['十进制', '十六进制', '字符', '名称'], rows, function (r) { T.copy(String(r[0])); }));
app.appendChild(T.row([buildSearch(wrap), T.el('span', { text: '点击行复制十进制码' })]));
app.appendChild(wrap);
''')

d('emoji', 'Emoji 大全', '分类浏览常用 Emoji，点击复制到剪贴板', js=r'''
var DATA = {
  '笑脸': ['😀','😃','😄','😁','😆','😅','😂','🤣','😊','😇','🙂','😉','😍','🥰','😘','😜','🤪','🤨','🧐','🤓','😎','🥳','😏','😒','😞','😔','😟','😕','🙁','😣','😖','😫','😩','🥺','😢','😭','😤','😠','😡','🤬','🤯','😳','🥵','🥶','😱','😨','😰','🤗','🤔','🤭','🤫','😴','🤤','😪','😵','🤐','🥴','🤢','🤮','🤧','😷','🤒','🤕'],
  '手势': ['👍','👎','👌','✌️','🤞','🤟','🤘','🤙','👈','👉','👆','👇','☝️','✋','🤚','🖐','🖖','👋','🤝','🙏','💪','🦾','✍️','👏','🙌','🤲','🤜','🤛','✊','👊'],
  '人物': ['👶','🧒','👦','👧','🧑','👨','👩','🧓','👴','👵','👮','🕵️','💃','🕺','🧘','🏃','🚶','🧑‍💻','👨‍🏫','👩‍🔬','🦸','🦹','🧙','🧚','🧜','🧝'],
  '动物': ['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵','🐔','🐧','🐦','🐤','🦆','🦅','🦉','🦇','🐺','🐗','🐴','🦄','🐝','🐛','🦋','🐌','🐞','🐜','🦂','🐢','🐍','🦎','🐙','🦑','🦐','🦀','🐡','🐠','🐟','🐬','🐳','🐋','🦈'],
  '食物': ['🍎','🍐','🍊','🍋','🍌','🍉','🍇','🍓','🫐','🍒','🍑','🥭','🍍','🥥','🥝','🍅','🥑','🥦','🥕','🌽','🌶','🥒','🍄','🥜','🍞','🥐','🥖','🧀','🥚','🍳','🥞','🧇','🥓','🍔','🍟','🍕','🌭','🥪','🌮','🌯','🥗','🍝','🍜','🍲','🍛','🍣','🍱','🍤','🍚','🍥','🥟','🍦','🍰','🎂','🍫','🍬','🍭','🍩','🍪','☕','🍵','🥤','🧋','🍺','🍻'],
  '旅行': ['🚗','🚕','🚙','🚌','🏎','🚓','🚑','🚒','🚐','🚚','🚛','🚜','🛴','🚲','🛵','🏍','✈️','🚀','🛰','🚁','⛵','🚤','🛳','⛴','🚢','🚂','🚆','🚇','🗺','🧭','🏔','🌋','🗻','🏕','🏖','🏜','🏝','🏟','🏛','🎢','🎡','⛲','⛺'],
  '物体': ['💻','🖥','⌨️','🖱','💾','💿','📀','📱','☎️','📞','📟','📠','🔋','🔌','💡','🔦','🕯','🧯','🛢','💸','💵','💰','💳','💎','⚖️','🔧','🔨','⚙️','🧲','🔫','💊','🩹','🩺','🚪','🪑','🛏','🚿','🧼','🧹','🧺','🔔','🔑','🔒','📦','📥','📤','📫','📮','✏️','🖊','📝','📚','📖','🔖','🧾','📊','📈','📉','🗂','📋','📌','📎','🗂'],
  '符号': ['❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔','❣️','💕','💞','💓','💗','💖','💘','💝','✨','⭐','🌟','💫','⚡','🔥','🌈','☀️','🌙','⛅','☁️','❄️','💧','🌊','✅','❌','❓','❗','💯','🔔','🔕','🎵','🎶','💡','⚠️','🚫','♻️','🔒','🔓']
};
var box = T.el('div');
function render(filter) {
  T.clearEl(box);
  Object.keys(DATA).forEach(function (cat) {
    var list = DATA[cat].filter(function (e) { return !filter || cat.includes(filter); });
    if (!list.length) return;
    var sec = T.el('div', { style: 'margin-bottom:14px' });
    sec.appendChild(T.el('span', { text: cat + '（' + list.length + '）', class: 'field' }));
    var grid = T.el('div', { style: 'display:flex;flex-wrap:wrap;gap:4px' });
    list.forEach(function (e) {
      var b = T.button(e, function () { T.copy(e); });
      b.style.cssText += 'font-size:20px;padding:4px 8px;justify-content:center';
      b.title = '点击复制 ' + e;
      grid.appendChild(b);
    });
    sec.appendChild(grid);
    box.appendChild(sec);
  });
}
var search = T.input('', { class: 'grow', placeholder: '输入分类过滤（笑脸/手势/动物/食物/旅行/物体/符号）…' });
search.addEventListener('input', function () { render(search.value.trim()); });
render('');
app.appendChild(T.row([search]));
app.appendChild(box);
''')

d('keycode', '键盘键位码', '按下任意键实时显示 key / code / keyCode / which', js=r'''
var hint = T.msg('点击下方区域并按下任意按键组合（含 Ctrl/Shift/Alt），实时显示键值。', '');
var box = T.el('div', { class: 'output', style: 'min-height:120px;text-align:center;font-size:18px;padding:30px' });
box.textContent = '⌨️ 在此区域按键…';
var last = {};
box.tabIndex = 0;
box.style.cursor = 'pointer';
box.addEventListener('keydown', function (e) {
  e.preventDefault();
  last = { key: e.key, code: e.code, keyCode: e.keyCode, which: e.which, ctrl: e.ctrlKey, shift: e.shiftKey, alt: e.altKey, meta: e.metaKey };
  show();
});
box.addEventListener('click', function () { box.focus(); });
function show() {
  if (!last.key) return;
  var mods = [];
  if (last.ctrl) mods.push('Ctrl');
  if (last.shift) mods.push('Shift');
  if (last.alt) mods.push('Alt');
  if (last.meta) mods.push('Meta');
  box.innerHTML = '<div style="font:400 40px var(--font-serif)">' + T.esc(last.key) + '</div>' +
    '<div style="margin-top:10px;color:var(--ink2);font-size:13px">key: <b>' + T.esc(last.key) + '</b> · code: <b>' + T.esc(last.code) + '</b> · keyCode: <b>' + last.keyCode + '</b> · which: <b>' + last.which + '</b></div>' +
    (mods.length ? '<div style="margin-top:4px;color:var(--accent)">修饰键: ' + mods.join(' + ') + '</div>' : '');
}
app.appendChild(hint);
app.appendChild(box);
app.appendChild(T.row([T.button('复制 keyCode', function () { T.copy(String(last.keyCode || '')); })]));
''')

d('html-chars', 'HTML 特殊字符', '常用 HTML 字符实体速查：保留字符 / 符号 / 希腊字母', js=SEARCH_JS + r'''
var DATA = [
  ['&amp;', '&', 'and 符号（保留字）'], ['&lt;', '<', '小于号（保留字）'], ['&gt;', '>', '大于号（保留字）'],
  ['&quot;', '"', '双引号（保留字）'], ['&#39;', "'", '单引号（保留字）'], ['&nbsp;', ' ', '不换行空格'],
  ['&copy;', '©', '版权'], ['&reg;', '®', '注册商标'], ['&trade;', '™', '商标'],
  ['&hellip;', '…', '省略号'], ['&mdash;', '—', '长破折号'], ['&ndash;', '–', '短破折号'],
  ['&lsquo;', '\u2018', '左单引号'], ['&rsquo;', '\u2019', '右单引号'], ['&ldquo;', '\u201c', '左双引号'], ['&rdquo;', '\u201d', '右双引号'],
  ['&laquo;', '«', '左书名号'], ['&raquo;', '»', '右书名号'],
  ['&deg;', '°', '度'], ['&plusmn;', '±', '正负号'], ['&times;', '×', '乘号'], ['&divide;', '÷', '除号'],
  ['&frac12;', '½', '二分之一'], ['&frac14;', '¼', '四分之一'], ['&frac34;', '¾', '四分之三'],
  ['&micro;', 'µ', '微'], ['&para;', '¶', '段落符'], ['&sect;', '§', '章节符'], ['&dagger;', '†', '剑号'],
  ['&larr;', '←', '左箭头'], ['&uarr;', '↑', '上箭头'], ['&rarr;', '→', '右箭头'], ['&darr;', '↓', '下箭头'],
  ['&harr;', '↔', '左右箭头'], ['&spades;', '♠', '黑桃'], ['&clubs;', '♣', '梅花'], ['&hearts;', '♥', '红桃'], ['&diams;', '♦', '方块'],
  ['&alpha;', 'α', '希腊字母 alpha'], ['&beta;', 'β', 'beta'], ['&gamma;', 'γ', 'gamma'], ['&delta;', 'δ', 'delta'],
  ['&epsilon;', 'ε', 'epsilon'], ['&theta;', 'θ', 'theta'], ['&lambda;', 'λ', 'lambda'], ['&mu;', 'μ', 'mu'],
  ['&pi;', 'π', 'pi'], ['&rho;', 'ρ', 'rho'], ['&sigma;', 'σ', 'sigma'], ['&phi;', 'φ', 'phi'], ['&omega;', 'ω', 'omega'],
  ['&Alpha;', 'Α', 'Alpha 大写'], ['&Beta;', 'Β', 'Beta 大写'], ['&Delta;', 'Δ', 'Delta 大写'], ['&Omega;', 'Ω', 'Omega 大写'],
  ['&infin;', '∞', '无穷'], ['&ne;', '≠', '不等于'], ['&le;', '≤', '小于等于'], ['&ge;', '≥', '大于等于'],
  ['&sum;', '∑', '求和'], ['&radic;', '√', '根号'], ['&int;', '∫', '积分'], ['&part;', '∂', '偏导'], ['&nabla;', '∇', '梯度'],
  ['&there4;', '∴', '所以'], ['&because;', '∵', '因为'], ['&prop;', '∝', '正比'], ['&ang;', '∠', '角'], ['&perp;', '⊥', '垂直']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['实体', '显示', '说明'], DATA, function (r) { T.copy(r[0]); }));
app.appendChild(T.row([buildSearch(wrap), T.el('span', { text: '点击行复制实体代码' })]));
app.appendChild(wrap);
''')

d('http-headers', 'HTTP 请求头参考', '常见 HTTP 请求 / 响应头详解', js=SEARCH_JS + r'''
var DATA = [
  ['Accept', '请求', '客户端可接受的响应类型，如 application/json'],
  ['Accept-Encoding', '请求', '可接受的压缩算法：gzip, deflate, br'],
  ['Authorization', '请求', '认证凭证，如 Bearer <token>、Basic <base64>'],
  ['Cache-Control', '两者', '缓存策略：no-cache / no-store / max-age=3600 / public / private'],
  ['Content-Disposition', '响应', 'body 展示方式：inline / attachment; filename="x"'],
  ['Content-Encoding', '响应', 'body 压缩算法：gzip / br / deflate'],
  ['Content-Length', '两者', 'body 字节长度'],
  ['Content-Type', '两者', 'body 的 MIME 类型：application/json 等'],
  ['Cookie', '请求', '客户端携带的 Cookie'],
  ['ETag', '响应', '资源指纹，用于协商缓存（If-None-Match）'],
  ['Expires', '响应', '缓存过期时间（HTTP/1.0 遗留）'],
  ['Host', '请求', '目标主机与端口（HTTP/1.1 必需）'],
  ['If-None-Match', '请求', '携带上次 ETag，命中则返回 304'],
  ['If-Modified-Since', '请求', '携带上次时间，命中则返回 304'],
  ['Last-Modified', '响应', '资源最后修改时间'],
  ['Location', '响应', '重定向目标 URL（3xx）'],
  ['Origin', '请求', '发起请求的源（CORS 关键）'],
  ['Referer', '请求', '来源页面 URL（拼写错误是历史遗留）'],
  ['Retry-After', '响应', '配合 503/429，建议的重试时间'],
  ['Server', '响应', '服务器软件信息（建议隐藏）'],
  ['Set-Cookie', '响应', '下发 Cookie，支持 HttpOnly/Secure/SameSite'],
  ['Strict-Transport-Security', '响应', 'HSTS：强制 HTTPS，max-age=31536000; includeSubDomains'],
  ['User-Agent', '请求', '客户端标识字符串'],
  ['X-Content-Type-Options', '响应', 'nosniff 禁止 MIME 嗅探'],
  ['X-Frame-Options', '响应', 'DENY / SAMEORIGIN 防点击劫持'],
  ['X-Forwarded-For', '请求', '代理链中的客户端真实 IP'],
  ['X-Request-Id', '两者', '请求追踪 ID（链路追踪）'],
  ['Access-Control-Allow-Origin', '响应', 'CORS：允许的源，* 或具体源'],
  ['Access-Control-Allow-Methods', '响应', 'CORS：允许的 HTTP 方法'],
  ['Access-Control-Allow-Headers', '响应', 'CORS：允许的自定义请求头']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['头部', '方向', '说明'], DATA));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('content-type', 'Content-Type 大全', '常用 MIME 类型速查：文档 / 图片 / 音视频 / 数据', js=SEARCH_JS + r'''
var DATA = [
  ['.html', 'text/html', '网页'],
  ['.css', 'text/css', '样式表'],
  ['.js / .mjs', 'text/javascript', '脚本'],
  ['.json', 'application/json', 'JSON 数据'],
  ['.xml', 'application/xml', 'XML'],
  ['.txt', 'text/plain', '纯文本'],
  ['.csv', 'text/csv', 'CSV 表格'],
  ['.pdf', 'application/pdf', 'PDF 文档'],
  ['.zip', 'application/zip', 'ZIP 压缩包'],
  ['.gz', 'application/gzip', 'Gzip 压缩包'],
  ['.7z', 'application/x-7z-compressed', '7z 压缩包'],
  ['.tar', 'application/x-tar', 'tar 归档'],
  ['.doc', 'application/msword', 'Word 97-2003'],
  ['.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 文档'],
  ['.xls', 'application/vnd.ms-excel', 'Excel 97-2003'],
  ['.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel 表格'],
  ['.pptx', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PPT'],
  ['.png', 'image/png', 'PNG 图片'],
  ['.jpg / .jpeg', 'image/jpeg', 'JPEG 图片'],
  ['.gif', 'image/gif', 'GIF 动图'],
  ['.webp', 'image/webp', 'WebP 图片'],
  ['.avif', 'image/avif', 'AVIF 图片'],
  ['.svg', 'image/svg+xml', 'SVG 矢量图'],
  ['.ico', 'image/x-icon', '网站图标'],
  ['.mp3', 'audio/mpeg', 'MP3 音频'],
  ['.wav', 'audio/wav', 'WAV 音频'],
  ['.ogg', 'audio/ogg', 'OGG 音频'],
  ['.m4a', 'audio/mp4', 'M4A 音频'],
  ['.mp4', 'video/mp4', 'MP4 视频'],
  ['.webm', 'video/webm', 'WebM 视频'],
  ['.mov', 'video/quicktime', 'QuickTime 视频'],
  ['.woff', 'font/woff', 'WOFF 字体'],
  ['.woff2', 'font/woff2', 'WOFF2 字体'],
  ['.ttf', 'font/ttf', 'TrueType 字体'],
  ['.otf', 'font/otf', 'OpenType 字体'],
  ['.wasm', 'application/wasm', 'WebAssembly'],
  ['.wasm (流式)', 'application/wasm', 'WebAssembly streaming'],
  ['表单（默认）', 'application/x-www-form-urlencoded', 'HTML 表单键值对'],
  ['表单（文件）', 'multipart/form-data', '含文件上传的表单'],
  ['事件流', 'text/event-stream', 'SSE 服务器推送'],
  ['任意二进制', 'application/octet-stream', '未知二进制流']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['扩展名 / 场景', 'MIME 类型', '说明'], DATA, function (r) { T.copy(r[1]); }));
app.appendChild(T.row([buildSearch(wrap), T.el('span', { text: '点击行复制 MIME' })]));
app.appendChild(wrap);
''')

d('ports', '常见端口速查', 'TCP/UDP 常用端口号：Web / 邮件 / 数据库 / 远程', js=SEARCH_JS + r'''
var DATA = [
  ['20/21', 'FTP', '文件传输（数据/控制）', 'TCP'],
  ['22', 'SSH / SFTP / SCP', '安全远程登录', 'TCP'],
  ['23', 'Telnet', '明文远程登录（不安全，勿用）', 'TCP'],
  ['25', 'SMTP', '邮件发送', 'TCP'],
  ['53', 'DNS', '域名解析', 'TCP/UDP'],
  ['67/68', 'DHCP', '自动分配 IP', 'UDP'],
  ['80', 'HTTP', '网页', 'TCP'],
  ['110', 'POP3', '邮件收取', 'TCP'],
  ['143', 'IMAP', '邮件收取（同步）', 'TCP'],
  ['443', 'HTTPS', 'HTTP over TLS', 'TCP'],
  ['465', 'SMTPS', 'SMTP over SSL', 'TCP'],
  ['587', 'SMTP (提交)', '邮件提交（STARTTLS）', 'TCP'],
  ['993', 'IMAPS', 'IMAP over SSL', 'TCP'],
  ['995', 'POP3S', 'POP3 over SSL', 'TCP'],
  ['1433', 'SQL Server', '微软数据库', 'TCP'],
  ['1521', 'Oracle', '甲骨文数据库', 'TCP'],
  ['3306', 'MySQL / MariaDB', '数据库', 'TCP'],
  ['3389', 'RDP', 'Windows 远程桌面', 'TCP'],
  ['5432', 'PostgreSQL', '数据库', 'TCP'],
  ['5672', 'RabbitMQ / AMQP', '消息队列', 'TCP'],
  ['6379', 'Redis', '缓存数据库', 'TCP'],
  ['8080', 'HTTP 备用', '常见代理/开发端口', 'TCP'],
  ['8443', 'HTTPS 备用', '常见开发端口', 'TCP'],
  ['9200', 'Elasticsearch', '搜索引擎 REST', 'TCP'],
  ['27017', 'MongoDB', '文档数据库', 'TCP'],
  ['11211', 'Memcached', '缓存', 'TCP/UDP'],
  ['9092', 'Kafka', '消息队列', 'TCP'],
  ['5900', 'VNC', '远程桌面', 'TCP'],
  ['5060/5061', 'SIP', 'VoIP 信令', 'TCP/UDP'],
  ['1900', 'SSDP / UPnP', '设备发现', 'UDP']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['端口', '服务', '说明', '协议'], DATA));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('regex-cheat', '正则大全', '常用正则表达式速查：校验 / 提取 / 替换场景', js=SEARCH_JS + r'''
var DATA = [
  ['手机号（中国）', '^1[3-9]\\d{9}$', '校验 11 位手机号'],
  ['邮箱', '^[\\w.-]+@[\\w-]+(\\.[\\w-]+)+$', '标准邮箱'],
  ['身份证（18位）', '^\\d{17}[\\dXx]$', '含末位 X'],
  ['URL', '^https?://[^\\s/$.?#].[^\\s]*$', 'http/https 链接'],
  ['IPv4', '^(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3}$', '点分十进制'],
  ['IPv6（简化）', '^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$', '完整格式'],
  ['日期 (YYYY-MM-DD)', '^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$', '合法月日'],
  ['时间 (HH:mm:ss)', '^([01]\\d|2[0-3]):[0-5]\\d:[0-5]\\d$', '24 小时制'],
  ['中国邮政编码', '^[1-9]\\d{5}$', '6 位数字'],
  ['整数', '^-?\\d+$', '含负数'],
  ['正整数', '^\\d+$', '不含符号'],
  ['金额（两位小数）', '^\\d+(\\.\\d{1,2})?$', '价格'],
  ['强密码', '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[^\\w\\s]).{8,}$', '四类字符至少8位'],
  ['中文字符', '[\\u4e00-\\u9fff]+', '匹配汉字'],
  ['QQ 号', '^[1-9]\\d{4,10}$', '5-11 位'],
  ['车牌（普通）', '^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-HJ-NP-Z][A-HJ-NP-Z0-9]{4}[A-HJ-NP-Z0-9挂学警港澳]$', '民用车牌'],
  ['HTML 标签', '<(\\w+)[^>]*>.*?</\\1>|<\\w+[^>]*/>', '成对或自闭合'],
  ['十六进制颜色', '^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', '#fff 或 #ffffff'],
  ['Base64', '^[A-Za-z0-9+/]+={0,2}$', '标准 Base64'],
  ['版本号', '^\\d+\\.\\d+\\.\\d+$', '语义化版本 x.y.z'],
  ['提取中文', '[\\u4e00-\\u9fff]', '配合 g 标志'],
  ['空白字符', '\\\\s+', '匹配所有空白'],
  ['重复单词', '\\\\b(\\\\w+)\\\\s+\\\\1\\\\b', '查找连续重复（配合反向引用）'],
  ['千分位替换', '(\\d)(?=(\\d{3})+$)', '替换为 $1,（配合 g）']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['场景', '正则', '说明'], DATA, function (r) { T.copy(r[1]); }));
app.appendChild(T.row([buildSearch(wrap), T.el('span', { text: '点击行复制正则' })]));
app.appendChild(wrap);
''')

d('operator', '运算符优先级', '多语言运算符优先级参考表（JS / Python / C）', js=SEARCH_JS + r'''
var DATA = [
  ['()', '函数调用 / 分组', '最高', 'JS/Py/C'],
  ['[] . ?. (args)', '成员访问 / 可选链', '高', 'JS'],
  ['x++ x--', '后缀自增自减', '高', 'JS/C'],
  ['! ~ +x -x ++x --x typeof await', '一元运算符', '较高', 'JS/C'],
  ['**', '幂运算', '较高（右结合）', 'JS/Py'],
  ['* / % //', '乘除取模（// 为整除）', '中高', 'JS/Py/C'],
  ['+ -', '加减 / 字符串拼接', '中', 'JS/Py/C'],
  ['<< >>', '位移', '中', 'JS/C'],
  ['< <= > >= in instanceof', '比较 / 成员判断', '中', 'JS/Py'],
  ['== != === !==', '相等判断（=== 为严格相等）', '中低', 'JS'],
  ['&', '按位与', '低', 'JS/C'],
  ['^', '按位异或', '低', 'JS/C'],
  ['|', '按位或', '低', 'JS/C'],
  ['&& and', '逻辑与', '更低', 'JS/Py'],
  ['|| or', '逻辑或', '更低', 'JS/Py'],
  ['??', '空值合并', '低（不能与 || 混用不加括号）', 'JS'],
  ['? :', '三元条件', '很低', 'JS/C'],
  ['= += -= *= /= **= ????=', '赋值（右结合）', '很低', 'JS/Py/C'],
  ['yield', '生成器产出', '最低', 'JS/Py'],
  [',', '逗号 / 序列', '最低', 'JS/C']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['运算符', '含义', '优先级', '语言'], DATA));
app.appendChild(T.row([buildSearch(wrap), T.el('span', { text: '规则：不确定时加括号；一元 ** 右结合；&& 高于 ||' })]));
app.appendChild(wrap);
''')

d('linux-cmd', 'Linux 命令速查', '分类 Linux 命令参考：文件 / 文本 / 进程 / 网络 / 磁盘', js=SEARCH_JS + r'''
var DATA = [
  ['ls -la', '文件', '列出所有文件（含隐藏）与权限'],
  ['cd -', '文件', '回到上一个目录'],
  ['pwd', '文件', '显示当前目录'],
  ['cp -r src dst', '文件', '递归复制目录'],
  ['mv old new', '文件', '移动 / 重命名'],
  ['rm -rf dir', '文件', '强制递归删除（慎用）'],
  ['mkdir -p a/b/c', '文件', '多级创建目录'],
  ['ln -s target link', '文件', '创建软链接'],
  ['find . -name "*.log"', '文件', '按名查找文件'],
  ['du -sh *', '磁盘', '统计各目录大小'],
  ['df -h', '磁盘', '查看磁盘使用率'],
  ['cat / tac', '文本', '正序 / 倒序输出文件'],
  ['less file', '文本', '分页查看（q 退出）'],
  ['head -n 20 / tail -f', '文本', '前 20 行 / 实时追踪'],
  ['grep -rn "kw" dir', '文本', '递归搜索关键词'],
  ['grep -v "x"', '文本', '反向匹配（排除）'],
  ['sed "s/old/new/g" f', '文本', '批量替换'],
  ['awk \'{print $1}\'', '文本', '按列提取'],
  ['sort -rn / uniq -c', '文本', '数值倒序排序 / 计数去重'],
  ['wc -l', '文本', '统计行数'],
  ['cut -d: -f1', '文本', '按分隔符取列'],
  ['ps aux | grep nginx', '进程', '查找进程'],
  ['top / htop', '进程', '实时资源监控'],
  ['kill -9 PID', '进程', '强杀进程'],
  ['nohup cmd &', '进程', '后台运行'],
  ['jobs / fg / bg', '进程', '任务管理'],
  ['kill -l', '进程', '列出全部信号'],
  ['ping -c 4 host', '网络', '连通性测试'],
  ['curl -I url', '网络', '查看响应头'],
  ['wget url', '网络', '下载文件'],
  ['ss -tlnp', '网络', '查看监听端口（netstat 替代）'],
  ['ssh user@host', '网络', '远程登录'],
  ['scp file host:path', '网络', '远程拷贝'],
  ['rsync -avz src dst', '网络', '增量同步'],
  ['chmod 755 f', '权限', '修改权限'],
  ['chown user:group f', '权限', '修改属主'],
  ['sudo !!', '权限', '以 sudo 重跑上一条命令'],
  ['tar -czf out.tgz dir', '压缩', '打包压缩'],
  ['tar -xzf a.tgz', '压缩', '解压 .tgz'],
  ['tar -xf a.tar.xz', '压缩', '解压（自动识别格式）'],
  ['systemctl status nginx', '系统', '服务状态'],
  ['journalctl -u nginx -f', '系统', '服务日志追踪'],
  ['crontab -e', '系统', '编辑定时任务'],
  ['uname -a / lsblsk', '系统', '内核信息 / 块设备'],
  ['lsof -i :8080', '系统', '查端口占用进程'],
  ['history | grep ssh', '系统', '历史命令搜索'],
  ['alias ll=\'ls -la\'', '系统', '设置别名'],
  ['watch -n 2 cmd', '系统', '每 2 秒重复执行']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['命令', '分类', '说明'], DATA, function (r) { T.copy(r[0]); }));
app.appendChild(T.row([buildSearch(wrap), T.el('span', { text: '点击行复制命令' })]));
app.appendChild(wrap);
''')

d('symbols', '特殊符号大全', '分类特殊符号：标点 / 数学 / 箭头 / 希腊 / 制表 / 货币', js=r'''
var DATA = {
  '标点符号': ['，', '。', '、', '；', '：', '？', '！', '"', '"', '\u2018', '\u2019', '（', '）', '【', '】', '《', '》', '——', '……', '～', '·'],
  '数学符号': ['＋', '－', '×', '÷', '＝', '≠', '±', '√', '≤', '≥', '≈', '∞', '∑', '∏', '∫', '∂', '∇', '∈', '∉', '⊂', '∪', '∩', '∅', '∀', '∃', '∴', '∵', '⊥', '∥', '∠', '°', '′', '″', 'π', 'α', 'β', 'γ', 'θ', 'λ', 'μ', 'σ', 'φ', 'ω', 'Δ', 'Ω'],
  '箭头符号': ['←', '↑', '→', '↓', '↔', '↕', '⇐', '⇒', '⇔', '➡', '⬅', '⬆', '⬇', '↖', '↗', '↘', '↙', '⤴', '⤵', '↺', '↻', '⇄', '⇅'],
  '货币符号': ['¥', '$', '€', '£', '¢', '₩', '₽', '₹', '₿', '¤'],
  '序号数字': ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑴', '⑵', '⒈', '⒉', 'Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', 'Ⅴ', 'Ⅵ', '½', '⅓', '¾', '№'],
  '几何图形': ['■', '□', '▲', '△', '▼', '▽', '◆', '◇', '○', '●', '◎', '☆', '★', '☀', '☁', '☂', '❄', '⚑', '⚑', '♠', '♣', '♥', '♦'],
  '制表符': ['─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '═', '║', '╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬'],
  '打勾叉号': ['✓', '✔', '✗', '✘', '☒', '☐', '☑', '×', '✚', '✖']
};
var box = T.el('div');
function render(filter) {
  T.clearEl(box);
  Object.keys(DATA).forEach(function (cat) {
    var list = DATA[cat];
    if (filter && !cat.includes(filter)) return;
    var sec = T.el('div', { style: 'margin-bottom:14px' });
    sec.appendChild(T.el('span', { text: cat + '（' + list.length + '）', class: 'field' }));
    var grid = T.el('div', { style: 'display:flex;flex-wrap:wrap;gap:4px' });
    list.forEach(function (s) {
      var b = T.button(s, function () { T.copy(s); });
      b.style.cssText += 'font-size:16px;padding:4px 10px;justify-content:center;min-width:40px';
      b.title = '点击复制';
      grid.appendChild(b);
    });
    sec.appendChild(grid);
    box.appendChild(sec);
  });
}
var search = T.input('', { class: 'grow', placeholder: '输入分类过滤（标点/数学/箭头/货币/序号/几何/制表/勾叉）…' });
search.addEventListener('input', function () { render(search.value.trim()); });
render('');
app.appendChild(T.row([search]));
app.appendChild(box);
''')

d('css-props', 'CSS 属性速查', '常用 CSS 属性参考：布局 / 盒模型 / 排版 / 视觉 / 动效', js=SEARCH_JS + r'''
var DATA = [
  ['display', '布局', 'flex / grid / block / inline-block / none'],
  ['flex-direction', '布局', 'row / column / row-reverse'],
  ['justify-content', '布局', 'flex-start / center / space-between / space-evenly'],
  ['align-items', '布局', 'stretch / center / flex-start / baseline'],
  ['grid-template-columns', '布局', 'repeat(3, 1fr) / auto-fit minmax(200px, 1fr)'],
  ['position', '布局', 'static / relative / absolute / fixed / sticky'],
  ['z-index', '布局', '层叠顺序（配合定位使用）'],
  ['overflow', '布局', 'visible / hidden / auto / scroll / clip'],
  ['margin / padding', '盒模型', '外边距 / 内边距，简写上右下左'],
  ['width / height', '盒模型', '支持 min()/max()/calc()：width: calc(100% - 20px)'],
  ['box-sizing', '盒模型', 'border-box（推荐）让宽高含边框内边距'],
  ['border / border-radius', '盒模型', '边框与圆角，radius 支持 / 椭圆语法'],
  ['box-shadow', '盒模型', 'x y blur spread color inset'],
  ['aspect-ratio', '盒模型', '宽高比：16/9、1/1'],
  ['font-family / font-size', '排版', '字体栈与字号，推荐 rem'],
  ['font-weight', '排版', '100-900 或 normal(400) / bold(700)'],
  ['line-height', '排版', '推荐无单位数值 1.5-1.8'],
  ['letter-spacing / word-spacing', '排版', '字符 / 单词间距'],
  ['text-align / text-transform', '排版', '对齐 / 大小写转换 uppercase'],
  ['text-overflow', '排版', '配合 overflow:hidden; white-space:nowrap 实现省略号'],
  ['white-space', '排版', 'nowrap 不换行 / pre 保留空白 / pre-wrap'],
  ['writing-mode', '排版', 'vertical-rl 竖排文字'],
  ['color / background', '视觉', '颜色支持 #hex / rgb() / hsl() / 颜色变量'],
  ['background-image', '视觉', 'url() / linear-gradient() / radial-gradient()'],
  ['background-size', '视觉', 'cover 铺满裁剪 / contain 完整显示'],
  ['backdrop-filter', '视觉', 'blur(10px) 毛玻璃（配合半透明背景）'],
  ['filter', '视觉', 'blur / brightness / contrast / grayscale()'],
  ['opacity', '视觉', '0-1 透明度（影响子元素，rgba 不影响）'],
  ['clip-path', '视觉', 'circle() / polygon() 裁剪形状'],
  ['transition', '动效', 'property duration easing delay'],
  ['transform', '动效', 'translate / rotate / scale / skew，GPU 加速'],
  ['animation + @keyframes', '动效', '关键帧动画：animation: name 1s infinite'],
  ['@media', '响应式', '@media (max-width: 768px) { … }'],
  ['@supports', '响应式', '特性查询：@supports (backdrop-filter: blur(1px))'],
  ['var() + 自定义属性', '变量', '--main: #1744E8; color: var(--main)'],
  ['prefers-color-scheme', '响应式', '@media (prefers-color-scheme: dark) 深色模式'],
  [':hover :focus :active', '选择器', '交互伪类'],
  ['::before / ::after', '选择器', '配合 content 属性生成内容'],
  ['scroll-behavior', '滚动', 'smooth 平滑滚动锚点'],
  ['scroll-snap-type', '滚动', 'x mandatory 轮播吸附']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['属性', '分类', '常用值 / 说明'], DATA, function (r) { T.copy(r[0]); }));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('js-api', 'JS API 速查', '常用 JavaScript Web API 参考', js=SEARCH_JS + r'''
var DATA = [
  ['querySelector / querySelectorAll', 'DOM', 'CSS 选择器查找元素'],
  ['createElement / appendChild', 'DOM', '创建并挂载节点'],
  ['classList.add/remove/toggle', 'DOM', '类名操作'],
  ['dataset', 'DOM', '读写 data-* 属性'],
  ['IntersectionObserver', 'DOM', '元素进入视口回调（懒加载/曝光埋点）'],
  ['MutationObserver', 'DOM', '监听 DOM 变更'],
  ['ResizeObserver', 'DOM', '监听元素尺寸变化'],
  ['fetch', '网络', 'async 请求；配合 AbortController 超时取消'],
  ['WebSocket', '网络', '全双工通信 ws://'],
  ['EventSource', '网络', 'SSE 服务器单向推送'],
  ['navigator.clipboard', '设备', 'readText / writeText 剪贴板'],
  ['navigator.mediaDevices', '设备', 'getUserMedia 摄像头麦克风'],
  ['navigator.geolocation', '设备', 'getCurrentPosition 定位（需授权）'],
  ['localStorage / sessionStorage', '存储', '持久 / 会话级键值存储（5MB）'],
  ['IndexedDB', '存储', '浏览器端结构化大容量数据库'],
  ['Cache API', '存储', 'caches.open 配合 SW 做离线缓存'],
  ['crypto.subtle', '安全', 'digest / sign / verify / encrypt'],
  ['crypto.getRandomValues', '安全', '密码学安全随机数'],
  ['Notification', '系统', '桌面通知（需授权）'],
  ['structuredClone', '数据', '深拷贝（含嵌套/日期）'],
  ['Array.prototype.at', '数组', 'at(-1) 取末尾元素'],
  ['Array.prototype.flatMap', '数组', 'map + flat(1)'],
  ['Object.fromEntries', '数据', '键值对数组转对象'],
  ['Intl.DateTimeFormat', '格式化', '时区/本地化日期格式'],
  ['Intl.NumberFormat', '格式化', '本地化数字/货币'],
  ['URL / URLSearchParams', '工具', 'URL 解析与查询参数'],
  ['Blob / File / FileReader', '文件', '二进制数据与文件读取'],
  ['FormData', '文件', '表单序列化（支持文件）'],
  ['CompressionStream', '文件', 'gzip / deflate 压缩流'],
  ['Web Workers', '并发', '后台线程，postMessage 通信'],
  ['requestAnimationFrame', '渲染', '下一帧回调（动画循环）'],
  ['requestIdleCallback', '渲染', '空闲时回调（低优任务）'],
  ['performance.now / mark', '性能', '高精度计时与性能标记'],
  ['matchMedia', '响应式', 'JS 查询媒体条件'],
  ['history.pushState', '路由', 'SPA 无刷新改 URL'],
  ['CustomEvent + dispatchEvent', '事件', '自定义事件'],
  ['AbortController', '事件', '取消 fetch / 事件监听'],
  ['queueMicrotask', '调度', '微任务队列'],
  ['WeakMap / WeakRef', '数据', '不阻止垃圾回收的引用'],
  ['Proxy / Reflect', '元编程', '拦截对象操作（Vue 响应式基础）']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['API', '分类', '说明'], DATA));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('html-tags', 'HTML 标签速查', 'HTML 标签参考：结构 / 文本 / 表单 / 媒体 / 语义', js=SEARCH_JS + r'''
var DATA = [
  ['<html> <head> <body>', '结构', '文档骨架'],
  ['<meta charset="utf-8">', '结构', '字符编码声明'],
  ['<meta name="viewport">', '结构', '移动端视口：width=device-width, initial-scale=1'],
  ['<title>', '结构', '标签页标题（SEO 关键）'],
  ['<link rel="stylesheet">', '结构', '引入 CSS'],
  ['<script defer/async>', '结构', 'defer 保持顺序延后执行；async 下载完即执行'],
  ['<header> <footer> <nav>', '语义', '页眉 / 页脚 / 导航'],
  ['<main> <section> <article>', '语义', '主体 / 区块 / 独立内容（利于 SEO）'],
  ['<aside> <figure> <figcaption>', '语义', '侧栏 / 插图容器 / 图注'],
  ['<h1>-<h6>', '文本', '标题层级（每页一个 h1）'],
  ['<p> <br> <hr>', '文本', '段落 / 换行 / 分隔线'],
  ['<strong> <em>', '文本', '强调（有语义，优于 b/i）'],
  ['<code> <pre> <kbd>', '文本', '行内代码 / 预格式 / 键盘输入'],
  ['<blockquote> <q> <cite>', '文本', '引用块 / 短引用 / 引用来源'],
  ['<ul> <ol> <li>', '文本', '无序 / 有序列表'],
  ['<a href target=_blank rel>', '链接', 'rel="noopener noreferrer" 安全打开新窗'],
  ['<img src alt loading=lazy>', '媒体', '图片：alt 必填，loading 懒加载'],
  ['<picture> <source>', '媒体', '响应式图片多格式'],
  ['<video controls poster muted>', '媒体', '视频播放'],
  ['<audio controls>', '媒体', '音频播放'],
  ['<iframe sandbox>', '媒体', '内嵌页面，sandbox 提升安全'],
  ['<canvas>', '媒体', '位图画布（配合 JS）'],
  ['<svg>', '媒体', '矢量图形'],
  ['<form action method>', '表单', '表单容器'],
  ['<input type=text/email/password...>', '表单', '多种输入类型'],
  ['<textarea rows>', '表单', '多行文本'],
  ['<select> <option> <optgroup>', '表单', '下拉选择'],
  ['<button type=submit/button>', '表单', '按钮（表单内默认 submit）'],
  ['<label for>', '表单', '绑定控件提升可访问性'],
  ['<fieldset> <legend>', '表单', '控件分组'],
  ['<datalist>', '表单', '输入建议列表'],
  ['<output>', '表单', '计算结果输出'],
  ['<details> <summary>', '交互', '原生折叠面板（无需 JS）'],
  ['<dialog open>', '交互', '原生对话框（showModal()）'],
  ['<progress value max>', '交互', '进度条'],
  ['<meter>', '交互', '度量值（磁盘用量等）'],
  ['<table> <thead> <tbody> <tr> <th> <td>', '表格', '数据表格，th 为表头'],
  ['<colgroup> <col>', '表格', '列样式分组'],
  ['<template>', '脚本', '不可见模板，JS 克隆使用'],
  ['<noscript>', '脚本', '禁用 JS 时的降级内容']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['标签', '分类', '说明'], DATA));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('mysql-syntax', 'MySQL 语法速查', 'MySQL 常用语法参考：CRUD / 聚合 / 连接 / 索引 / 事务', js=SEARCH_JS + r'''
var DATA = [
  ['CREATE DATABASE db CHARSET utf8mb4;', '库表', '建库（utf8mb4 支持 emoji）'],
  ['CREATE TABLE t (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(64) NOT NULL DEFAULT \'\', created DATETIME DEFAULT CURRENT_TIMESTAMP);', '库表', '建表'],
  ['SHOW TABLES; DESC t;', '库表', '查看表结构与字段'],
  ['ALTER TABLE t ADD COLUMN age INT DEFAULT 0;', '库表', '加字段'],
  ['DROP TABLE IF EXISTS t;', '库表', '删表（危险）'],
  ['INSERT INTO t (name) VALUES (\'a\'), (\'b\');', '增', '批量插入'],
  ['INSERT ... ON DUPLICATE KEY UPDATE name=VALUES(name);', '增', '存在则更新（upsert）'],
  ['REPLACE INTO t VALUES (...);', '增', '先删后插（注意自增 ID 变化）'],
  ['SELECT * FROM t WHERE id = 1 LIMIT 10 OFFSET 20;', '查', '条件 + 分页'],
  ['SELECT DISTINCT city FROM users;', '查', '去重'],
  ['SELECT COUNT(*), AVG(age) FROM users GROUP BY city HAVING AVG(age) > 20;', '聚合', '分组聚合 + HAVING'],
  ['ORDER BY age DESC, id ASC;', '查', '多字段排序'],
  ['SELECT a.*, b.name FROM orders a LEFT JOIN users b ON a.uid = b.id;', '连接', '左连接（保留左表全部）'],
  ['SELECT * FROM t WHERE name LIKE \'张%\';', '查', '前缀匹配（可走索引）'],
  ['SELECT * FROM t WHERE id IN (SELECT uid FROM vip);', '查', '子查询（大表建议改 JOIN）'],
  ['SELECT * FROM t WHERE created BETWEEN \'2026-01-01\' AND \'2026-12-31\';', '查', '范围查询'],
  ['UPDATE t SET age = age + 1 WHERE id = 1;', '改', '条件更新（无 WHERE 全表危险）'],
  ['DELETE FROM t WHERE created < \'2020-01-01\';', '删', '条件删除'],
  ['ALTER TABLE t ADD INDEX idx_name (name);', '索引', '普通索引'],
  ['ALTER TABLE t ADD UNIQUE INDEX uk_phone (phone);', '索引', '唯一索引'],
  ['EXPLAIN SELECT ...;', '优化', '执行计划（关注 type/rows/key）'],
  ['SHOW INDEX FROM t;', '索引', '查看表索引'],
  ['BEGIN; ... COMMIT; / ROLLBACK;', '事务', 'ACID 事务'],
  ['SELECT * FROM t FOR UPDATE;', '事务', '悲观锁（行锁）'],
  ['SELECT GET_LOCK(\'k\', 10);', '事务', '命名锁'],
  ['SELECT NOW(), DATE_FORMAT(NOW(), \'%Y-%m-%d %H:%i:%s\');', '函数', '时间与格式化'],
  ['SELECT DATEDIFF(d1, d2), TIMESTAMPDIFF(HOUR, t1, t2);', '函数', '日期差'],
  ['SELECT IF(age > 18, \'成年\', \'未成年\'), CASE WHEN score>=90 THEN \'A\' ELSE \'B\' END;', '函数', '条件表达式'],
  ['SELECT GROUP_CONCAT(name SEPARATOR \',\');', '函数', '分组拼接'],
  ['SHOW PROCESSLIST;', '运维', '当前连接与执行中的 SQL'],
  ['KILL <id>;', '运维', '终止查询'],
  ['mysqldump -u root -p db > backup.sql', '运维', '备份（命令行）'],
  ['SELECT @@version, @@innodb_buffer_pool_size;', '运维', '版本与配置']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['语法', '分类', '说明'], DATA, function (r) { T.copy(r[0]); }));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('git-commands', 'Git 命令速查', 'Git 常用命令：基础 / 分支 / 远程 / 撤销 / 储藏 / 排查', js=SEARCH_JS + r'''
var DATA = [
  ['git init', '基础', '初始化仓库'],
  ['git clone <url>', '基础', '克隆远程仓库'],
  ['git status -sb', '基础', '简洁状态'],
  ['git add -p', '基础', '交互式分块暂存'],
  ['git commit -m "msg"', '基础', '提交'],
  ['git commit --amend', '基础', '修正上次提交（未推送时）'],
  ['git log --oneline --graph --all', '基础', '图形化日志'],
  ['git diff / git diff --staged', '基础', '未暂存 / 已暂存的改动'],
  ['git show <commit>', '基础', '查看提交详情'],
  ['git blame <file>', '基础', '逐行追溯修改人'],
  ['git switch -c feat/x', '分支', '创建并切换分支'],
  ['git branch -d feat/x', '分支', '删除已合并分支'],
  ['git merge --no-ff feat/x', '分支', '合并（保留合并节点）'],
  ['git rebase main', '分支', '变基到 main（线性历史）'],
  ['git cherry-pick <sha>', '分支', '摘取单个提交'],
  ['git remote -v', '远程', '查看远程'],
  ['git remote add origin <url>', '远程', '添加远程'],
  ['git push -u origin main', '远程', '首次推送并关联'],
  ['git push --force-with-lease', '远程', '安全强推（先检查远端无新提交）'],
  ['git fetch --prune', '远程', '拉取并清理已删远程分支'],
  ['git pull --rebase', '远程', '变基方式拉取'],
  ['git restore <file>', '撤销', '丢弃工作区改动'],
  ['git restore --staged <file>', '撤销', '取消暂存（保留改动）'],
  ['git reset --soft HEAD~1', '撤销', '撤销提交，保留改动在暂存区'],
  ['git reset --hard HEAD~1', '撤销', '撤销提交并丢弃改动（危险）'],
  ['git revert <sha>', '撤销', '生成反向提交（已推送时用）'],
  ['git checkout <sha> -- <file>', '撤销', '从历史提交恢复单个文件'],
  ['git stash push -m "wip"', '储藏', '暂存工作现场'],
  ['git stash list / pop / drop', '储藏', '查看 / 恢复 / 删除'],
  ['git stash apply stash@{2}', '储藏', '恢复指定储藏'],
  ['git bisect start', '排查', '二分定位 bug 提交'],
  ['git reflog', '排查', '找回"丢失"的提交'],
  ['git fsck --lost-found', '排查', '查找悬空对象'],
  ['git tag -a v1.0 -m "release"', '标签', '附注标签'],
  ['git push origin --tags', '标签', '推送标签'],
  ['git worktree add ../hotfix hotfix/x', '高级', '多工作树并行'],
  ['git config alias.co checkout', '高级', '设置别名'],
  ['git shortlog -sn', '统计', '按作者统计提交数']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['命令', '分类', '说明'], DATA, function (r) { T.copy(r[0]); }));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('docker-commands', 'Docker 命令速查', 'Docker 常用命令：镜像 / 容器 / 网络 / 卷 / 编排', js=SEARCH_JS + r'''
var DATA = [
  ['docker pull nginx:alpine', '镜像', '拉取镜像（推荐 alpine 小镜像）'],
  ['docker images', '镜像', '列出本地镜像'],
  ['docker build -t app:1.0 .', '镜像', '构建镜像'],
  ['docker tag app:1.0 user/app:1.0', '镜像', '打标签'],
  ['docker push user/app:1.0', '镜像', '推送到仓库'],
  ['docker rmi <image>', '镜像', '删除镜像'],
  ['docker image prune -a', '镜像', '清理未使用镜像'],
  ['docker save/load', '镜像', '离线导出/导入镜像'],
  ['docker run -d --name web -p 8080:80 nginx', '容器', '后台运行 + 端口映射'],
  ['docker run --rm -it ubuntu bash', '容器', '交互式临时容器'],
  ['docker run -v $(pwd):/app -w /app node:20 node app.js', '容器', '挂载目录运行'],
  ['docker ps / docker ps -a', '容器', '运行中 / 全部容器'],
  ['docker exec -it web bash', '容器', '进入容器'],
  ['docker logs -f --tail 100 web', '容器', '追踪日志'],
  ['docker stop / start / restart web', '容器', '停止 / 启动 / 重启'],
  ['docker rm -f web', '容器', '删除容器'],
  ['docker stats', '容器', '实时资源占用'],
  ['docker cp web:/etc/nginx/nginx.conf .', '容器', '容器与主机拷贝文件'],
  ['docker inspect web', '容器', '查看容器详情'],
  ['docker commit web snapshot:1', '容器', '容器固化为镜像（不推荐替代 Dockerfile）'],
  ['docker network create app-net', '网络', '创建网络'],
  ['docker network connect app-net web', '网络', '容器加入网络（可用容器名互访）'],
  ['docker port web', '网络', '查看端口映射'],
  ['docker volume create data', '卷', '创建数据卷'],
  ['docker run -v data:/var/lib/mysql mysql', '卷', '挂载数据卷'],
  ['docker volume ls / prune', '卷', '列出 / 清理卷'],
  ['docker system df', '清理', '磁盘占用统计'],
  ['docker system prune -a --volumes', '清理', '深度清理（危险）'],
  ['docker compose up -d', '编排', '启动 compose 服务'],
  ['docker compose logs -f', '编排', '查看服务日志'],
  ['docker compose down -v', '编排', '停止并删除（含卷）'],
  ['docker compose build / pull', '编排', '构建 / 拉取服务镜像'],
  ['docker buildx build --platform linux/amd64,linux/arm64 -t app .', '高级', '多架构构建'],
  ['docker run --cpus=2 --memory=1g ...', '高级', '限制 CPU / 内存'],
  ['docker run --user 1000:1000 --read-only ...', '安全', '降权 + 只读根文件系统'],
  ['docker scan / sbom', '安全', '镜像漏洞扫描']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['命令', '分类', '说明'], DATA, function (r) { T.copy(r[0]); }));
app.appendChild(T.row([buildSearch(wrap)]));
app.appendChild(wrap);
''')

d('unicode-table', 'Unicode 字符表', '常用 Unicode 区块速览：输入十进制 / 十六进制查看字符', js=r'''
var input = T.input('4E2D', { class: 'grow mono', placeholder: '输入码点（如 4E2D / 6587 / 1F600），或粘贴字符反查' });
var box = T.el('div');
var BLOCKS = [
  ['基本拉丁', '0000-007F'], ['拉丁-1 补充', '0080-00FF'], ['希腊字母', '0370-03FF'],
  ['西里尔字母', '0400-04FF'], ['常用标点', '2000-206F'], ['货币符号', '20A0-20CF'],
  ['箭头', '2190-21FF'], ['数学运算符', '2200-22FF'], ['制表符', '2500-257F'],
  ['几何图形', '25A0-25FF'], ['杂项符号', '2600-26FF'], ['装饰符号', '2700-27BF'],
  ['CJK 部首', '2E80-2EFF'], ['CJK 符号标点', '3000-303F'], ['平假名', '3040-309F'],
  ['片假名', '30A0-30FF'], ['CJK 统一汉字', '4E00-9FFF'], ['韩文谚文', 'AC00-D7AF'],
  [' emoji 表情', '1F300-1F5FF'], ['补充符号', '1F600-1F64F'], ['交通地图', '1F680-1F6FF']
];
function showChar(cp) {
  T.clearEl(box);
  if (cp < 0 || cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF)) {
    box.appendChild(T.msg('⚠ 无效码点', 'err'));
    return;
  }
  var ch = String.fromCodePoint(cp);
  box.appendChild(T.kvTable([
    ['字符', ch],
    ['十进制', cp],
    ['十六进制', 'U+' + cp.toString(16).toUpperCase().padStart(4, '0')],
    ['HTML 实体', '&#' + cp + '; / &#x' + cp.toString(16) + ';'],
    ['JS 转义', cp > 0xFFFF ? '\\u{' + cp.toString(16) + '}' : '\\u' + cp.toString(16).padStart(4, '0')],
    ['CSS 转义', '\\\\' + cp.toString(16)],
    ['UTF-8 字节', T.bytesToHex(new TextEncoder().encode(ch)).replace(/../g, '$& ').trim()]
  ]));
  box.appendChild(T.el('div', { text: ch, style: 'font-size:80px;text-align:center;margin:16px 0' }));
}
function run() {
  var v = input.value.trim();
  T.clearEl(box);
  if (!v) return;
  if (/^[0-9]+$/.test(v)) { showChar(+v); return; }
  var hexm = v.replace(/^[Uu]\+?0*|^0[xX]/, '');
  if (/^[0-9a-fA-F]{1,6}$/.test(hexm)) { showChar(parseInt(hexm, 16)); return; }
  var ch = Array.from(v)[0];
  showChar(ch.codePointAt(0));
}
input.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '码点/字符' }), input]));
app.appendChild(box);
app.appendChild(T.el('span', { text: '常用区块', class: 'field' }));
app.appendChild(T.refTable(['区块', '码点范围'], BLOCKS.map(function (b) {
  return [b[0], 'U+' + b[1]];
})));
run();
''')

d('color-names', '颜色名称对照', 'CSS 颜色名称与 HEX/RGB 对照，点击复制', js=r'''
var NAMES = [
  ['black', '#000000'], ['white', '#FFFFFF'], ['red', '#FF0000'], ['lime', '#00FF00'],
  ['blue', '#0000FF'], ['yellow', '#FFFF00'], ['cyan / aqua', '#00FFFF'], ['magenta / fuchsia', '#FF00FF'],
  ['silver', '#C0C0C0'], ['gray', '#808080'], ['maroon', '#800000'], ['olive', '#808000'],
  ['green', '#008000'], ['purple', '#800080'], ['teal', '#008080'], ['navy', '#000080'],
  ['orange', '#FFA500'], ['pink', '#FFC0CB'], ['gold', '#FFD700'], ['brown', '#A52A2A'],
  ['tomato', '#FF6347'], ['coral', '#FF7F50'], ['salmon', '#FA8072'], ['crimson', '#DC143C'],
  ['firebrick', '#B22222'], ['darkred', '#8B0000'], ['hotpink', '#FF69B4'], ['deeppink', '#FF1493'],
  ['orchid', '#DA70D6'], ['violet', '#EE82EE'], ['plum', '#DDA0DD'], ['indigo', '#4B0082'],
  ['skyblue', '#87CEEB'], ['dodgerblue', '#1E90FF'], ['royalblue', '#4169E1'], ['steelblue', '#4682B4'],
  ['lightblue', '#ADD8E6'], ['turquoise', '#40E0D0'], ['aquamarine', '#7FFFD4'], ['seagreen', '#2E8B57'],
  ['limegreen', '#32CD32'], ['forestgreen', '#228B22'], ['olivedrab', '#6B8E23'], ['khaki', '#F0E68C'],
  ['goldenrod', '#DAA520'], ['chocolate', '#D2691E'], ['peru', '#CD853F'], ['sienna', '#A0522D'],
  ['beige', '#F5F5DC'], ['ivory', '#FFFFF0'], ['linen', '#FAF0E6'], ['snow', '#FFFAFA'],
  ['honeydew', '#F0FFF0'], ['mintcream', '#F5FFFA'], ['lavender', '#E6E6FA'], ['thistle', '#D8BFD8'],
  ['slateblue', '#6A5ACD'], ['mediumpurple', '#9370DB'], ['darkslategray', '#2F4F4F'], ['dimgray', '#696969'],
  ['lightgray', '#D3D3D3'], ['gainsboro', '#DCDCDC'], ['whitesmoke', '#F5F5F5'], ['ghostwhite', '#F8F8FF']
];
var wrap = T.el('div');
var rows = NAMES.map(function (n) {
  return [n[0], n[1], 'rgb(' + LU.Color.parse(n[1]).r + ', ' + LU.Color.parse(n[1]).g + ', ' + LU.Color.parse(n[1]).b + ')'];
});
wrap.appendChild(T.refTable(['名称', 'HEX', 'RGB'], rows, function (r) { T.copy(r[1]); }));
app.appendChild(T.el('p', { text: '点击行复制 HEX。', style: 'color:var(--ink2);font-size:12px' }));
app.appendChild(wrap);
var swatches = T.el('div', { style: 'display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:6px;margin-top:12px' });
NAMES.forEach(function (n) {
  var c = T.el('div', { style: 'height:54px;border-radius:8px;background:' + n[1] + ';cursor:pointer;position:relative;border:1px solid var(--line)', title: n[0] + ' ' + n[1] });
  c.addEventListener('click', function () { T.copy(n[1]); });
  swatches.appendChild(c);
});
app.appendChild(swatches);
''')

d('font-stack', '字体栈推荐', '常用 CSS font-family 字体栈组合参考', js=r'''
var DATA = [
  ['系统默认（推荐）', 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', '跟随各平台系统字体，零加载成本'],
  ['中文正文', '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif', '苹方 / 雅黑 / 思源黑体'],
  ['中文标题（衬线）', '"Noto Serif SC", "Source Han Serif SC", "SimSun", serif', '思源宋体 / 宋体'],
  ['英文无衬线经典', '"Helvetica Neue", Helvetica, Arial, sans-serif', '经典中性'],
  ['英文几何现代', '"Inter", "SF Pro Display", "Segoe UI", sans-serif', 'UI 界面现代感'],
  ['衬线阅读', 'Georgia, "Times New Roman", "Noto Serif", serif', '长文阅读舒适'],
  ['等宽代码', 'ui-monospace, "JetBrains Mono", "Fira Code", Consolas, "Courier New", monospace', '代码 / 数字对齐'],
  ['等宽终端', '"SF Mono", "Cascadia Code", "JetBrains Mono", Menlo, Consolas, monospace', '终端风格'],
  ['手写风格', '"Segoe Print", "Bradley Hand", "Comic Sans MS", cursive', '手写感（慎用正式场合）'],
  ['圆体可爱', '"Yuanti SC", "PingFang SC", "Comic Sans MS", sans-serif', '圆体 / 儿童向'],
  ['数字展示', '"DIN Alternate", "Bebas Neue", Impact, sans-serif', '海报数字'],
  ['报刊排版', '"Noto Serif SC", Georgia, "Songti SC", "SimSun", serif', '衬线中文报刊风'],
  ['UI 紧凑', '"Inter Tight", "Roboto Condensed", "Arial Narrow", sans-serif', '窄体节省空间'],
  ['老式终端', '"IBM Plex Mono", "Courier New", monospace', '复古终端感']
];
var wrap = T.el('div');
wrap.appendChild(T.refTable(['场景', '字体栈', '说明'], DATA, function (r) { T.copy(r[1]); }));
app.appendChild(T.row([T.el('span', { text: '点击行复制字体栈' })]));
app.appendChild(wrap);
var demo = T.el('div');
DATA.forEach(function (d2) {
  var row = T.el('div', { style: 'margin-bottom:10px' });
  row.appendChild(T.el('div', { text: d2[0] + ' — The quick brown fox 0123456789 永和九年', style: 'font-family:' + d2[1] + ';font-size:16px;border-bottom:1px solid var(--line);padding:6px 0' }));
  demo.appendChild(row);
});
app.appendChild(T.el('span', { text: '本机预览效果', class: 'field' }));
app.appendChild(demo);
''')
