# -*- coding: utf-8 -*-
"""生成器类工具定义"""
from .registry import d

d('uuid', 'UUID 生成器', 'UUID v4 批量生成（crypto 安全随机），可选大写 / 去连字符', js=r'''
var count = T.num(5, { min: 1, max: 500, style: 'width:90px' });
var upper = T.check('大写');
var strip = T.check('去连字符');
var braces = T.check('花括号包裹');
var output = T.out('');
function gen() {
  var n = Math.max(1, +count.value || 1);
  var lines = [];
  for (var i = 0; i < n; i++) {
    var b = crypto.getRandomValues(new Uint8Array(16));
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    var hex = T.bytesToHex(b);
    var u = hex.slice(0, 8) + '-' + hex.slice(8, 12) + '-' + hex.slice(12, 16) + '-' + hex.slice(16, 20) + '-' + hex.slice(20);
    if (upper._input.checked) u = u.toUpperCase();
    if (strip._input.checked) u = u.replace(/-/g, '');
    if (braces._input.checked) u = '{' + u + '}';
    lines.push(u);
  }
  output.value = lines.join('\n');
}
[count, upper._input, strip._input, braces._input].forEach(function (el) { el.addEventListener('input', gen); });
app.appendChild(T.pane([T.field('生成结果（每行一个）', output)], true));
app.appendChild(T.row([T.el('span', { text: '数量' }), count, upper, strip, braces,
  T.button('重新生成', gen, true), T.btnCopy(function () { return output.value; })]));
gen();
''')

d('password', '密码生成器', '安全随机密码：长度 / 字符集 / 排除易混淆字符，批量生成', js=r'''
var len = T.range(4, 64, 1, 16);
var lenLabel = T.el('b', { text: '16' });
var sets = [
  T.check('小写 a-z', true), T.check('大写 A-Z', true), T.check('数字 0-9', true),
  T.check('符号 !@#$%', true), T.check('排除易混淆 (0O1lI)', true)
];
var count = T.num(5, { min: 1, max: 100, style: 'width:80px' });
var output = T.out('');
function gen() {
  lenLabel.textContent = len.value;
  var pool = '';
  if (sets[0]._input.checked) pool += 'abcdefghijklmnopqrstuvwxyz';
  if (sets[1]._input.checked) pool += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  if (sets[2]._input.checked) pool += '0123456789';
  if (sets[3]._input.checked) pool += '!@#$%^&*()-_=+[]{};:,.<>?';
  if (sets[4]._input.checked) pool = pool.replace(/[0O1lI]/g, '');
  if (!pool) { output.value = ''; return; }
  var n = Math.max(1, +count.value || 1);
  var lines = [];
  for (var i = 0; i < n; i++) {
    var rnd = crypto.getRandomValues(new Uint32Array(+len.value));
    var pw = '';
    for (var j = 0; j < +len.value; j++) pw += pool[rnd[j] % pool.length];
    lines.push(pw);
  }
  output.value = lines.join('\n');
}
[len, count].forEach(function (el) { el.addEventListener('input', gen); });
sets.forEach(function (s) { s._input.addEventListener('change', gen); });
app.appendChild(T.pane([T.field('生成结果', output)], true));
app.appendChild(T.row([T.el('span', { text: '长度' }), len, lenLabel]));
var row2 = T.row(sets.slice(0, 3)); row2.style.marginBottom = '4px';
var row3 = T.row(sets.slice(3).concat([T.el('span', { text: '数量' }), count])); row3.style.marginBottom = '4px';
app.appendChild(row2);
app.appendChild(row3);
app.appendChild(T.row([T.button('生成', gen, true), T.btnCopy(function () { return output.value; })]));
gen();
''')

d('qrcode', '二维码生成', '文本 / 网址转 QR Code，自动选择版本与最优掩码，支持 PNG / SVG 下载',
  scripts='<script src="/tools/js/qr.js"></script>',
  js=r'''
var text = T.textarea('输入文本、网址…', true);
text.value = 'https://freellm.top/';
var ecSel = T.select([{ value: 'M', label: 'M — 常用' }, { value: 'L', label: 'L — 内容多' }, { value: 'Q', label: 'Q — 较稳' }, { value: 'H', label: 'H — 最稳' }], 'M');
var darkColor = T.color('#000000');
var lightColor = T.color('#FFFFFF');
var canvas = T.el('canvas', { style: 'image-rendering:pixelated;border:1px solid var(--line);border-radius:8px;background:#fff' });
var info = T.el('span', { class: 'badge blue', text: '—' });
var render = function () {
  QR.encode(text.value, ecSel.value, function (res) {
    QR.toCanvas(canvas, res, { dark: darkColor.value, light: lightColor.value });
    info.textContent = '版本 ' + res.version + ' · ' + res.size + '×' + res.size + ' · 纠错 ' + res.ec;
    window._lastQR = res;
  });
};
var timer;
[text, ecSel].forEach(function (el) {
  el.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(render, 250); });
});
[darkColor, lightColor].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.el('div', { class: 'row' }, [
  T.el('span', { text: '纠错级别' }), ecSel,
  T.el('span', { text: '前景色' }), darkColor,
  T.el('span', { text: '背景色' }), lightColor
]));
app.appendChild(T.el('div', { class: 'pane single' }, [text]));
app.appendChild(T.el('div', { class: 'row', style: 'align-items:flex-start;gap:20px' }, [
  canvas,
  T.el('div', { class: 'field', style: 'gap:10px' }, [
    info,
    T.button('下载 PNG', function () {
      canvas.toBlob(function (b) { T.download('qrcode.png', b); });
    }, true),
    T.button('下载 SVG', function () {
      if (window._lastQR) T.download('qrcode.svg', QR.toSVG(window._lastQR, { dark: darkColor.value, light: lightColor.value }), 'image/svg+xml');
    }),
    T.button('复制 SVG 代码', function () {
      if (window._lastQR) T.copy(QR.toSVG(window._lastQR));
    })
  ])
]));
render();
''')

d('qrcode-scan', '二维码扫描', '摄像头实时扫描或上传图片识别二维码内容（jsQR 按需加载不拖慢打开）',
  head='<meta name="permissions-policy" content="camera">',
  js=r'''
var jsqrReady = null;
function ensureJsQR() {
  if (window.jsQR) return Promise.resolve();
  if (!jsqrReady) {
    jsqrReady = new Promise(function (resolve, reject) {
      status.textContent = '正在加载识别引擎…';
      var s = T.el('script', { src: '/tools/js/vendor/jsQR.js' });
      s.onload = function () { resolve(); };
      s.onerror = function () { jsqrReady = null; reject(new Error('识别引擎加载失败，请刷新重试')); };
      document.head.appendChild(s);
    });
  }
  return jsqrReady;
}
var video = T.el('video', { playsinline: '', muted: '', style: 'width:100%;max-width:360px;border-radius:8px;border:1px solid var(--line);background:#000' });
var canvas = T.el('canvas', { style: 'display:none' });
var result = T.out('扫描结果…');
var status = T.badge('未启动（点按钮时加载引擎）');
var stream = null, raf = 0;
function tick() {
  if (!stream) return;
  if (video.readyState === video.HAVE_ENOUGH_DATA) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    var img = ctx.getImageData(0, 0, canvas.width, canvas.height);
    var code = jsQR(img.data, img.width, img.height);
    if (code && code.data) {
      result.value = code.data;
      status.textContent = '✓ 已识别';
      status.className = 'badge ok';
    }
  }
  raf = requestAnimationFrame(tick);
}
app.appendChild(T.row([
  T.button('开启摄像头扫码', function () {
    ensureJsQR().then(function () {
      return navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    }).then(function (s) {
      stream = s;
      video.srcObject = s;
      video.play();
      status.textContent = '扫码中…';
      tick();
    }).catch(function (e) { T.toast((String(e.message).indexOf('引擎') >= 0 ? '' : '无法访问摄像头：') + e.message); });
  }, true),
  T.button('停止', function () {
    if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; cancelAnimationFrame(raf); status.textContent = '已停止'; }
  }),
  T.filePick('上传图片识别', 'image/*', function (dataURL) {
    ensureJsQR().then(function () {
      var img = new Image();
      img.onload = function () {
        var c = T.el('canvas');
        c.width = img.width; c.height = img.height;
        var ctx = c.getContext('2d');
        ctx.drawImage(img, 0, 0);
        var d = ctx.getImageData(0, 0, c.width, c.height);
        var code = jsQR(d.data, d.width, d.height);
        if (code && code.data) { result.value = code.data; status.textContent = '✓ 已识别'; status.className = 'badge ok'; }
        else { status.textContent = '未检测到二维码'; status.className = 'badge warn'; }
      };
      img.src = dataURL;
    }).catch(function (e) { T.toast(e.message); });
  })
]));
app.appendChild(T.el('div', { class: 'row' }, [video, status]));
app.appendChild(T.pane([T.field('识别结果', result)], true));
app.appendChild(T.row([T.btnCopy(function () { return result.value; }),
  T.button('打开链接', function () { if (/^https?:/.test(result.value)) window.open(result.value); })]));
app.appendChild(canvas);
''')

d('barcode', '条形码生成', 'Code128（B/C 自动）条形码生成，SVG / PNG 下载', js=r'''
var text = T.input('FRELLM-2026', { class: 'grow mono', placeholder: '内容（ASCII）' });
var h = T.num(80, { min: 30, max: 200, style: 'width:80px' });
var scale = T.select([{value:'2',label:'2x'},{value:'3',label:'3x'},{value:'4',label:'4x'}],'2');
var box = T.el('div', { style: 'padding:10px;background:#fff;border:1px solid var(--line);border-radius:8px;display:inline-block' });
function render() {
  try {
    box.innerHTML = LU.code128Svg(text.value, +h.value, +scale.value);
  } catch (e) { box.innerHTML = '<span style="color:var(--err)">' + T.esc(e.message) + '</span>'; }
}
[text, h, scale].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.pane([T.field('内容', text)], true));
app.appendChild(T.row([T.el('span', { text: '高度' }), h, T.el('span', { text: '模块宽度' }), scale]));
app.appendChild(box);
app.appendChild(T.row([T.button('下载 PNG', function () {
  var svg = box.querySelector('svg');
  var img = new Image();
  img.onload = function () {
    var c = T.el('canvas');
    c.width = img.width; c.height = img.height;
    c.getContext('2d').drawImage(img, 0, 0);
    T.dlCanvas(c, 'barcode.png');
  };
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(box.innerHTML);
}), T.button('下载 SVG', function () {
  T.download('barcode.svg', box.innerHTML, 'image/svg+xml');
})]));
render();
''')

d('barcode-scan', '条形码识别', '上传图片识别 Code128 / EAN / QR 等条码内容（ZXing 按需加载不拖慢打开）',
  js=r'''
var zxingReady = null;
function ensureZXing() {
  if (window.ZXing) return Promise.resolve();
  if (!zxingReady) {
    zxingReady = new Promise(function (resolve, reject) {
      fmt.textContent = '正在加载识别引擎…';
      var s = T.el('script', { src: '/tools/js/vendor/zxing-index.min.js' });
      s.onload = function () { resolve(); };
      s.onerror = function () { zxingReady = null; reject(new Error('识别引擎加载失败，请刷新重试')); };
      document.head.appendChild(s);
    });
  }
  return zxingReady;
}
var result = T.out('识别结果…');
var fmt = T.badge('选图后自动加载引擎');
var preview = T.el('img', { style: 'max-width:100%;max-height:220px;border-radius:8px;border:1px solid var(--line)' });
function scan(dataURL) {
  ensureZXing().then(function () {
    preview.src = dataURL;
    var reader = new ZXing.BrowserMultiFormatReader();
    var img = new Image();
    img.onload = function () {
      try {
        var res = reader.decodeFromImage(img);
        if (res) {
          result.value = res.text;
          fmt.textContent = '格式：' + (res.result && res.result.getBarcodeFormat != null ? res.result.getBarcodeFormat() : '已识别');
          fmt.className = 'badge ok';
        } else { fmt.textContent = '未识别'; fmt.className = 'badge warn'; }
      } catch (e) { fmt.textContent = '未识别到条形码'; fmt.className = 'badge warn'; }
    };
    img.src = dataURL;
  }).catch(function (e) { fmt.textContent = '⚠ ' + e.message; fmt.className = 'badge warn'; });
}
app.appendChild(T.row([T.filePick('上传条形码图片', 'image/*', function (dataURL) { scan(dataURL); }, true)]));
app.appendChild(T.row([preview, fmt]));
app.appendChild(T.pane([T.field('识别结果', result)], true));
app.appendChild(T.row([T.btnCopy(function () { return result.value; })]));
''')

d('random-string', '随机字符串', '自定义字符集随机字符串批量生成', js=r'''
var len = T.num(16, { min: 1, max: 256, style: 'width:80px' });
var count = T.num(10, { min: 1, max: 500, style: 'width:80px' });
var preset = T.select([
  { value: 'alnum', label: '字母+数字' },
  { value: 'hex', label: '十六进制' },
  { value: 'digits', label: '纯数字' },
  { value: 'letters', label: '纯字母' },
  { value: 'custom', label: '自定义字符集' }
], 'alnum');
var custom = T.input('abcdef0123456789', { class: 'grow mono', placeholder: '自定义字符集' });
var output = T.out('');
function gen() {
  var pools = { alnum: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', hex: '0123456789abcdef', digits: '0123456789', letters: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' };
  var pool = preset.value === 'custom' ? custom.value : pools[preset.value];
  if (!pool) { output.value = ''; return; }
  var n = +count.value, L = +len.value;
  var rnd = crypto.getRandomValues(new Uint32Array(n * L));
  var lines = [];
  for (var i = 0; i < n; i++) {
    var s = '';
    for (var j = 0; j < L; j++) s += pool[rnd[i * L + j] % pool.length];
    lines.push(s);
  }
  output.value = lines.join('\n');
}
[len, count, custom, preset].forEach(function (el) { el.addEventListener('input', gen); });
app.appendChild(T.pane([T.field('生成结果', output)], true));
app.appendChild(T.row([T.el('span', { text: '预设' }), preset]));
app.appendChild(T.row([T.el('span', { text: '长度' }), len, T.el('span', { text: '数量' }), count]));
app.appendChild(T.row([custom, T.button('生成', gen, true), T.btnCopy(function () { return output.value; })]));
gen();
''')

d('lorem', 'Lorem Ipsum', '中英文占位文本生成：段落数 / 段落长度可调', js=r'''
var paras = T.num(3, { min: 1, max: 50, style: 'width:80px' });
var lang = T.select([{value:'zh',label:'中文乱数假文'},{value:'en',label:'Lorem Ipsum'}],'zh');
var output = T.out('');
var ZH = '工具开发设计数据系统网络服务用户体验内容平台管理配置安全性能优化分析处理逻辑结构模块组件接口协议缓存索引请求响应消息队列调度算法模型训练推理部署监控日志测试版本发布迭代团队协作产品需求文档评审交付质量效率流程自动化集成兼容稳定扩展维护升级迁移备份恢复容灾高可用';
var EN = 'lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure in reprehenderit voluptate velit esse cillum eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum'.split(' ');
function gen() {
  var n = +paras.value || 1;
  var out = [];
  for (var i = 0; i < n; i++) {
    if (lang.value === 'zh') {
      var s = '';
      var total = 120 + Math.floor(Math.random() * 80);
      while (s.length < total) {
        var wl = 2 + Math.floor(Math.random() * 4);
        var w = '';
        for (var j = 0; j < wl; j++) w += ZH[Math.floor(Math.random() * ZH.length)];
        s += w;
      }
      out.push(s + '。');
    } else {
      var words = [];
      var wc = 30 + Math.floor(Math.random() * 20);
      for (var k = 0; k < wc; k++) words.push(EN[Math.floor(Math.random() * EN.length)]);
      var s2 = words.join(' ');
      out.push(s2.charAt(0).toUpperCase() + s2.slice(1) + '.');
    }
  }
  output.value = out.join('\n\n');
}
app.appendChild(T.pane([T.field('占位文本', output)], true));
app.appendChild(T.row([T.el('span', { text: '段落数' }), paras, lang, T.button('生成', gen, true), T.btnCopy(function () { return output.value; })]));
gen();
''')

d('mock-data', 'Mock 数据生成', '随机中文假数据：姓名 / 手机 / 邮箱 / 身份证 / 地址，JSON 输出', js=r'''
var count = T.num(5, { min: 1, max: 200, style: 'width:80px' });
var fields = [
  T.check('姓名', true), T.check('手机号', true), T.check('邮箱', true),
  T.check('身份证', true), T.check('地址', true), T.check('公司', true)
];
var output = T.out('');
var SURNAMES = '赵钱孙李周吴郑王冯陈蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜'.split('');
var GIVEN = ['伟', '芳', '娜', '敏', '静', '磊', '军', '洋', '勇', '艳', '杰', '涛', '明', '超', '秀英', '国华', '建华', '雨欣', '子轩', '梦琪'];
var CITIES = ['北京市朝阳区', '上海市浦东新区', '广州市天河区', '深圳市南山区', '杭州市西湖区', '成都市武侯区', '武汉市洪山区', '南京市鼓楼区', '西安市雁塔区', '重庆市渝北区'];
var STREETS = ['中山路', '人民路', '解放大道', '和平街', '建设路', '科技园南区', '金融港大道', '文化街'];
var COMPANIES = ['科技', '网络', '信息', '数据', '智能', '云计算', '软件', '数字'];
function pick(a) { return a[Math.floor(Math.random() * a.length)]; }
function phone() {
  var pre = pick(['130', '135', '136', '138', '150', '155', '170', '186', '188', '199']);
  var s = pre;
  for (var i = 0; i < 8; i++) s += Math.floor(Math.random() * 10);
  return s;
}
function idcard() {
  var areas = ['110101', '310104', '440106', '440305', '330106', '510107', '420111', '320102'];
  var id = pick(areas) + (1960 + Math.floor(Math.random() * 45)) + String(1 + Math.floor(Math.random() * 12)).padStart(2, '0') + String(1 + Math.floor(Math.random() * 28)).padStart(2, '0') + String(Math.floor(Math.random() * 1000)).padStart(3, '0');
  var w = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2];
  var codes = '10X98765432';
  var sum = 0;
  for (var i = 0; i < 17; i++) sum += +id[i] * w[i];
  return id + codes[sum % 11];
}
function gen() {
  var n = +count.value || 1;
  var arr = [];
  for (var i = 0; i < n; i++) {
    var o = {};
    if (fields[0]._input.checked) o.name = pick(SURNAMES) + pick(GIVEN);
    if (fields[1]._input.checked) o.phone = phone();
    if (fields[2]._input.checked) o.email = 'user' + Math.floor(Math.random() * 9999) + '@' + pick(['qq.com', '163.com', 'gmail.com', 'outlook.com']);
    if (fields[3]._input.checked) o.idcard = idcard();
    if (fields[4]._input.checked) o.address = pick(CITIES) + pick(STREETS) + (Math.floor(Math.random() * 200) + 1) + '号';
    if (fields[5]._input.checked) o.company = pick(CITIES).slice(0, 2) + pick(COMPANIES) + pick(['有限公司', '股份公司', '集团']);
    arr.push(o);
  }
  output.value = JSON.stringify(arr, null, 2);
}
app.appendChild(T.pane([T.field('Mock 数据 (JSON)', output)], true));
app.appendChild(T.row([T.el('span', { text: '数量' }), count]));
var r1 = T.row(fields.slice(0, 3)); r1.style.marginBottom = '4px';
var r2 = T.row(fields.slice(3)); r2.style.marginBottom = '4px';
app.appendChild(r1);
app.appendChild(r2);
app.appendChild(T.row([T.button('生成', gen, true), T.btnCopy(function () { return output.value; })]));
gen();
''')

d('favicon-maker', 'Favicon 制作', '图片转多尺寸 favicon.ico（16-256px，PNG 编码 ICO）', js=r'''
var preview = T.el('img', { style: 'max-width:128px;image-rendering:auto;border:1px solid var(--line);border-radius:8px' });
var sizesBox = T.el('div', { class: 'row' });
var SIZES = [16, 32, 48, 64, 128, 256];
var checks = SIZES.map(function (s, i) {
  return T.check(s + 'px', i === 1 || i === 2);
});
var status = T.badge('—');
var lastImg = null;
app.appendChild(T.row([T.filePick('选择图片（建议正方形 PNG）', 'image/*', function (dataURL, file) {
  lastImg = new Image();
  lastImg.onload = function () { preview.src = dataURL; status.textContent = file.name + ' · ' + lastImg.width + '×' + lastImg.height; };
  lastImg.src = dataURL;
}, true)]));
app.appendChild(T.row([preview]));
sizesBox.style.marginBottom = '10px';
checks.forEach(function (c) { sizesBox.appendChild(c); });
app.appendChild(sizesBox);
app.appendChild(T.row([
  T.button('生成并下载 favicon.ico', function () {
    if (!lastImg) { T.toast('请先选择图片'); return; }
    var items = [];
    checks.forEach(function (c, i) {
      if (!c._input.checked) return;
      var s = SIZES[i];
      var c2 = T.el('canvas', { width: s, height: s });
      var ctx = c2.getContext('2d');
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(lastImg, 0, 0, s, s);
      items.push({ size: s, blob: new Promise(function (res) { c2.toBlob(res, 'image/png'); }) });
    });
    if (!items.length) { T.toast('至少选择一个尺寸'); return; }
    LU.Ico.fromCanvases(items).then(function (blob) {
      T.download('favicon.ico', blob);
      status.textContent = '已生成 ' + items.length + ' 个尺寸';
    });
  }, true),
  T.button('下载 PNG (512px)', function () {
    if (!lastImg) { T.toast('请先选择图片'); return; }
    var c = T.el('canvas', { width: 512, height: 512 });
    c.getContext('2d').drawImage(lastImg, 0, 0, 512, 512);
    T.dlCanvas(c, 'favicon-512.png');
  }),
  status
]));
''')

d('gitignore', '.gitignore 生成', '按语言 / 框架 / IDE 组合生成 .gitignore', js=r'''
var box = T.el('div', { class: 'row' });
var output = T.out('');
var TPL = {
  'Node': ['node_modules/', 'dist/', '.env', '.env.*', 'npm-debug.log*', 'coverage/', '.npm'],
  'Python': ['__pycache__/', '*.py[cod]', '.venv/', 'venv/', 'dist/', 'build/', '*.egg-info/', '.pytest_cache/', '.mypy_cache/'],
  'Java': ['target/', '*.class', '*.jar', '*.war', '.gradle/', 'build/', '.idea/'],
  'Go': ['bin/', 'vendor/', '*.exe', '*.test', '*.out'],
  'Rust': ['target/', 'Cargo.lock'],
  'C/C++': ['*.o', '*.obj', '*.exe', '*.dll', '*.so', '*.dylib', 'build/', 'cmake-build-*/'],
  'Vue': ['node_modules/', 'dist/', '.vuepress/dist/', '.env.local'],
  'React': ['node_modules/', 'build/', '.env', '.env.local', '.eslintcache'],
  'macOS': ['.DS_Store', '.AppleDouble', '.LSOverride', 'Icon?'],
  'Windows': ['Thumbs.db', 'Desktop.ini', '$RECYCLE.BIN/', '*.lnk'],
  'Linux': ['*~', '.directory', '.Trash-*'],
  'VS Code': ['.vscode/*', '!.vscode/settings.json', '!.vscode/extensions.json', 'history/'],
  'JetBrains': ['.idea/', '*.iml', '*.ipr', '*.iws', 'out/'],
  'Vim': ['[._]*.s[a-v][a-z]', '[._]*.sw[a-p]', '.netrwhist', 'tags'],
  'Logs': ['logs/', '*.log', 'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*'],
  'Env': ['.env', '.env.local', '.env.*.local'],
  'Docker': ['**/Dockerfile.dockerignore']
};
Object.keys(TPL).forEach(function (k) {
  box.appendChild(T.check(k, k === 'Node' || k === 'macOS' || k === 'Env'));
});
function run() {
  var lines = [];
  Array.from(box.querySelectorAll('input')).forEach(function (inp, i) {
    if (!inp.checked) return;
    var k = Object.keys(TPL)[i];
    lines.push('# === ' + k + ' ===');
    lines = lines.concat(TPL[k]);
    lines.push('');
  });
  output.value = lines.join('\n');
}
box.querySelectorAll('input').forEach ? null : null;
setTimeout(function () { Array.from(box.querySelectorAll('input')).forEach(function (inp) { inp.addEventListener('change', run); }); run(); });
app.appendChild(box);
app.appendChild(T.pane([T.field('.gitignore', output)], true));
app.appendChild(T.row([T.button('下载 .gitignore', function () { T.download('.gitignore', output.value); }, true), T.btnCopy(function () { return output.value; })]));
''')

d('og-meta', 'OG Meta 标签', 'Open Graph / Twitter Card 标签生成与预览', js=r'''
var fields = {
  title: T.input('FreeLLM - 免费 AI 资源导航', { class: 'grow' }),
  desc: T.input('精选免费 AI 资源、模型与工具', { class: 'grow' }),
  url: T.input('https://freellm.top', { class: 'grow mono' }),
  img: T.input('/freellm-01-hero.png', { class: 'grow mono' }),
  site: T.input('FreeLLM', { class: 'grow' }),
  type: T.select([{value:'website',label:'website'},{value:'article',label:'article'}],'website')
};
var output = T.out('');
function run() {
  var t = fields.title.value, d = fields.desc.value, u = fields.url.value, im = fields.img.value, s = fields.site.value, ty = fields.type.value;
  var e = T.esc;
  output.value =
    '<!-- Open Graph -->\n' +
    '<meta property="og:title" content="' + e(t) + '">\n' +
    '<meta property="og:description" content="' + e(d) + '">\n' +
    '<meta property="og:url" content="' + e(u) + '">\n' +
    '<meta property="og:image" content="' + e(im) + '">\n' +
    '<meta property="og:site_name" content="' + e(s) + '">\n' +
    '<meta property="og:type" content="' + ty + '">\n\n' +
    '<!-- Twitter Card -->\n' +
    '<meta name="twitter:card" content="summary_large_image">\n' +
    '<meta name="twitter:title" content="' + e(t) + '">\n' +
    '<meta name="twitter:description" content="' + e(d) + '">\n' +
    '<meta name="twitter:image" content="' + e(im) + '">';
  preview();
}
function preview() {
  var box = document.getElementById('og-preview');
  if (!box) return;
  box.innerHTML =
    '<div style="border:1px solid var(--line);border-radius:8px;overflow:hidden;max-width:420px;background:var(--surface)">' +
    '<div style="height:160px;background:var(--accent-soft) url(' + T.esc(fields.img.value) + ') center/cover"></div>' +
    '<div style="padding:10px 14px"><div style="color:var(--ink3);font-size:11px">' + T.esc(fields.site.value) + '</div>' +
    '<div style="font-weight:600;margin:4px 0">' + T.esc(fields.title.value) + '</div>' +
    '<div style="color:var(--ink2);font-size:12px">' + T.esc(fields.desc.value) + '</div></div></div>';
}
Object.keys(fields).forEach(function (k) { fields[k].addEventListener('input', run); });
app.appendChild(T.pane([T.field('标题', fields.title), T.field('描述', fields.desc)]));
app.appendChild(T.pane([T.field('URL', fields.url), T.field('图片 URL', fields.img)]));
app.appendChild(T.row([T.el('span', { text: '站点名' }), fields.site, T.el('span', { text: '类型' }), fields.type]));
app.appendChild(T.pane([T.field('Meta 代码', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
app.appendChild(T.el('span', { text: '卡片预览', class: 'field' }));
var pv = T.el('div', { id: 'og-preview' });
app.appendChild(pv);
run();
''')

d('shield', 'Shield Badge', 'Shields.io 风格徽章生成：标题 / 值 / 颜色 / 样式实时预览', js=r'''
var label = T.input('build', { class: 'grow mono' });
var value = T.input('passing', { class: 'grow mono' });
var color = T.select([{value:'brightgreen',label:'brightgreen'},{value:'green',label:'green'},{value:'yellow',label:'yellow'},{value:'orange',label:'orange'},{value:'red',label:'red'},{value:'blue',label:'blue'},{value:'blueviolet',label:'blueviolet'},{value:'lightgrey',label:'lightgrey'}],'brightgreen');
var style = T.select([{value:'flat',label:'flat'},{value:'flat-square',label:'flat-square'},{value:'for-the-badge',label:'for-the-badge'},{value:'plastic',label:'plastic'}],'flat');
var logo = T.input('', { class: 'grow mono', placeholder: 'logo（simple-icons 名，如 github）' });
var preview = T.el('div', { style: 'padding:14px;background:#fff;border:1px solid var(--line);border-radius:8px;display:inline-block;min-width:200px;min-height:40px;text-align:center', title: '徽章图片来自 shields.io' });
var output = T.out('');
var winLoaded = document.readyState === 'complete';
window.addEventListener('load', function () { winLoaded = true; run(); });
function run() {
  var u = 'https://img.shields.io/badge/' + encodeURIComponent(label.value || ' ') + '-' + encodeURIComponent(value.value || ' ') + '-' + color.value + '?style=' + style.value + (logo.value ? '&logo=' + encodeURIComponent(logo.value) : '');
  output.value = u;
  if (winLoaded) preview.innerHTML = '<img src="' + T.esc(u) + '" alt="badge" onerror="this.style.opacity=.3">';
  else preview.textContent = '预览图等页面就绪后加载…';
}
[label, value, logo, color, style].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('标签', label), T.field('值', value)]));
app.appendChild(T.row([T.el('span', { text: '颜色' }), color, T.el('span', { text: '样式' }), style]));
app.appendChild(T.row([T.el('span', { text: 'Logo' }), logo]));
app.appendChild(preview);
app.appendChild(T.pane([T.field('URL', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; }),
  T.button('复制 Markdown', function () { T.copy('![badge](' + output.value + ')'); }),
  T.button('打开新标签查看', function () { window.open(output.value); })]));
run();
''')

d('random-color', '随机颜色', '随机颜色生成 + 单色多级调色板，HEX/RGB/HSL 一键复制', js=r'''
var big = T.el('div', { style: 'height:120px;border-radius:12px;border:1px solid var(--line);cursor:pointer;background:#5B8DEF' });
var labels = T.el('div', { class: 'row' });
var palette = T.el('div', { style: 'display:flex;gap:6px;height:60px;border-radius:8px;overflow:hidden;margin-top:10px' });
function run() {
  var r = Math.floor(Math.random() * 256), g = Math.floor(Math.random() * 256), b = Math.floor(Math.random() * 256);
  var hex = LU.Color.hex({ r: r, g: g, b: b });
  var hsl = LU.Color.rgbToHsl(r, g, b);
  big.style.background = hex;
  T.clearEl(labels);
  [['HEX', hex], ['RGB', 'rgb(' + r + ', ' + g + ', ' + b + ')'], ['HSL', 'hsl(' + Math.round(hsl.h) + ', ' + Math.round(hsl.s * 100) + '%, ' + Math.round(hsl.l * 100) + '%)']].forEach(function (p) {
    var b = T.button(p[0] + ' ' + p[1], function () { T.copy(p[1]); });
    b.className = 'mini';
    labels.appendChild(b);
  });
  T.clearEl(palette);
  [90, 75, 60, 45, 30, 20].forEach(function (l) {
    var c = LU.Color.hslToRgb(hsl.h / 360, hsl.s, l / 100);
    var d = T.el('div', { style: 'flex:1;background:' + LU.Color.hex(c) + ';cursor:pointer;position:relative' });
    d.title = LU.Color.hex(c);
    d.addEventListener('click', function () { T.copy(d.title); });
    palette.appendChild(d);
  });
}
big.addEventListener('click', run);
app.appendChild(big);
app.appendChild(labels);
app.appendChild(palette);
app.appendChild(T.row([T.button('随机一个', run, true), T.el('span', { text: '点击色块或按钮随机，色阶块点击复制' })]));
run();
''')

d('random-decision', '随机决策', '转盘随机选择 / 掷骰子 / 抛硬币，多种决策方式', js=r'''
var itemsIn = T.input('火锅, 烧烤, 面条, 汉堡, 沙拉', { class: 'grow' });
var canvas = T.el('canvas', { width: 320, height: 320, style: 'display:block;margin:0 auto' });
var result = T.badge('—');
var spinning = false;
var rotation = 0;
function drawWheel() {
  var items = itemsIn.value.split(/[,，\n]/).map(function (s) { return s.trim(); }).filter(Boolean);
  var ctx = canvas.getContext('2d');
  var cx = 160, cy = 160, r = 150;
  ctx.clearRect(0, 0, 320, 320);
  if (!items.length) return;
  var colors = ['#FF9A8B', '#FFB88C', '#FFD380', '#B8E986', '#7ED8F7', '#B39DDB', '#F48FB1', '#80CBC4'];
  items.forEach(function (item, i) {
    var a0 = (i / items.length) * Math.PI * 2 + rotation;
    var a1 = ((i + 1) / items.length) * Math.PI * 2 + rotation;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, a0, a1);
    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((a0 + a1) / 2);
    ctx.fillStyle = '#fff';
    ctx.font = '600 13px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(item.slice(0, 6), r - 10, 4);
    ctx.restore();
  });
  ctx.beginPath();
  ctx.arc(cx, cy, 24, 0, Math.PI * 2);
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(cx - 10, 6);
  ctx.lineTo(cx + 10, 6);
  ctx.lineTo(cx, 28);
  ctx.closePath();
  ctx.fillStyle = 'var(--ink)';
  ctx.fillStyle = '#2F3437';
  ctx.fill();
}
function spin() {
  var items = itemsIn.value.split(/[,，\n]/).map(function (s) { return s.trim(); }).filter(Boolean);
  if (!items.length || spinning) return;
  spinning = true;
  result.textContent = '转动中…';
  var target = rotation + Math.PI * 2 * (4 + Math.random() * 3) + Math.random() * Math.PI * 2;
  var start = rotation, t0 = performance.now(), dur = 3000;
  function anim(t) {
    var p = Math.min(1, (t - t0) / dur);
    var ease = 1 - Math.pow(1 - p, 3);
    rotation = start + (target - start) * ease;
    drawWheel();
    if (p < 1) requestAnimationFrame(anim);
    else {
      var n = items.length;
      var pointer = (Math.PI * 1.5 - rotation) % (Math.PI * 2);
      var idx = Math.floor((pointer + Math.PI * 2) % (Math.PI * 2) / (Math.PI * 2) * n) % n;
      result.textContent = '🎉 ' + items[idx];
      spinning = false;
    }
  }
  requestAnimationFrame(anim);
}
itemsIn.addEventListener('input', drawWheel);
app.appendChild(T.pane([T.field('选项（逗号分隔）', itemsIn)], true));
app.appendChild(canvas);
app.appendChild(T.row([T.button('开始转盘', spin, true), result,
  T.button('掷骰子', function () { result.textContent = '🎲 ' + (1 + Math.floor(Math.random() * 6)); }),
  T.button('抛硬币', function () { result.textContent = '🪙 ' + (Math.random() < 0.5 ? '正面' : '反面'); })]));
drawWheel();
''')

d('lorem-pixel', '占位图片', '生成自定义尺寸 / 颜色 / 文字的占位图与头像，PNG / SVG 下载', js=r'''
var w = T.num(400, { min: 1, max: 4096, style: 'width:90px' });
var h = T.num(300, { min: 1, max: 4096, style: 'width:90px' });
var bg = T.color('#5B8DEF');
var fg = T.color('#FFFFFF');
var text = T.input('FreeLLM', { class: 'grow', placeholder: '显示文字（留空显示尺寸）' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px' });
function render() {
  var W = Math.min(4096, +w.value || 400), H = Math.min(4096, +h.value || 300);
  canvas.width = W; canvas.height = H;
  var ctx = canvas.getContext('2d');
  ctx.fillStyle = bg.value;
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = fg.value;
  ctx.font = '600 ' + Math.max(12, Math.floor(Math.min(W, H) / 8)) + 'px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text.value || (W + ' × ' + H), W / 2, H / 2);
}
[w, h, bg, fg, text].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.row([T.el('span', { text: '宽' }), w, T.el('span', { text: '高' }), h,
  T.el('span', { text: '背景' }), bg, T.el('span', { text: '文字色' }), fg]));
app.appendChild(T.row([text]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载 PNG', function () { T.dlCanvas(canvas, 'placeholder-' + w.value + 'x' + h.value + '.png'); }, true),
  T.button('下载 SVG', function () {
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w.value + '" height="' + h.value + '">' +
      '<rect width="100%" height="100%" fill="' + bg.value + '"/>' +
      '<text x="50%" y="50%" fill="' + fg.value + '" font-family="sans-serif" font-size="' + Math.max(12, Math.min(+w.value, +h.value) / 8) + '" text-anchor="middle" dominant-baseline="middle">' + T.esc(text.value || w.value + ' × ' + h.value) + '</text></svg>';
    T.download('placeholder.svg', svg, 'image/svg+xml');
  })]));
render();
''')
