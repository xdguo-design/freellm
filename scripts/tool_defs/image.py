# -*- coding: utf-8 -*-
"""图片工具类工具定义（全部客户端 Canvas 处理）"""
from .registry import d

d('image-resize', '图片尺寸调整', '按预设 / 自定义尺寸缩放图片，保持比例可选', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var w = T.num(800, { min: 1, style: 'width:90px' });
var h = T.num(600, { min: 1, style: 'width:90px' });
var lock = T.check('锁定比例', true);
var preset = T.select([
  { value: '', label: '自定义…' }, { value: '1920x1080', label: '1920×1080 全高清' },
  { value: '1280x720', label: '1280×720' }, { value: '1080x1080', label: '1080×1080 方图' },
  { value: '1080x1920', label: '1080×1920 竖屏' }, { value: '800x600', label: '800×600' }
], '');
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var info = T.badge('—');
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function render() {
  if (!img) return;
  canvas.width = Math.max(1, +w.value);
  canvas.height = Math.max(1, +h.value);
  var ctx = canvas.getContext('2d');
  ctx.imageSmoothingQuality = 'high';
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  canvas.style.display = '';
  info.textContent = canvas.width + '×' + canvas.height;
}
function loadFile(f) {
  T.loadImage(function (i) {
    img = i;
    w.value = i.width;
    h.value = i.height;
    info.textContent = '原图 ' + i.width + '×' + i.height;
    render();
  });
  var reader = new FileReader();
  reader.onload = function () {};
}
inp.addEventListener('change', function () {
  var f = inp.files[0];
  if (!f) return;
  T.loadImage(function (i) {
    img = i;
    w.value = i.width;
    h.value = i.height;
    render();
  });
});
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
function syncWH(changed) {
  if (!lock._input.checked || !img) return;
  var ratio = img.width / img.height;
  if (changed === 'w') h.value = Math.round(+w.value / ratio);
  else w.value = Math.round(+h.value * ratio);
}
w.addEventListener('input', function () { syncWH('w'); render(); });
h.addEventListener('input', function () { syncWH('h'); render(); });
preset.addEventListener('change', function () {
  var p = preset.value.split('x');
  if (p.length === 2) { w.value = p[0]; h.value = p[1]; lock._input.checked = false; render(); }
});
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '宽' }), w, T.el('span', { text: '高' }), h, lock, preset, info]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载 PNG', function () { T.dlCanvas(canvas, 'resize-' + w.value + 'x' + h.value + '.png'); }, true),
  T.button('下载 JPEG', function () { canvas.toBlob(function (b) { T.download('resize.jpg', b); }, 'image/jpeg', 0.9); })]));
''')

d('image-crop', '图片自由裁剪', '拖拽选择裁剪区域，支持固定比例（1:1 / 16:9 等）', js=r'''
var drop = T.msg('点击或拖入图片，然后在图上拖拽选择裁剪区域', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var ratio = T.select([{value:'free',label:'自由'},{value:'1',label:'1:1'},{value:'4/3',label:'4:3'},{value:'16/9',label:'16:9'},{value:'9/16',label:'9:16'}],'free');
var canvas = T.el('canvas', { style: 'max-width:100%;cursor:crosshair;border:1px solid var(--line);border-radius:8px;display:none' });
var info = T.badge('—');
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null, sel = null, dragging = false, sx = 0, sy = 0, scale = 1;
function redraw() {
  if (!img) return;
  var ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  if (sel) {
    ctx.fillStyle = 'rgba(0,0,0,.45)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    var x = Math.min(sel.x0, sel.x1), y = Math.min(sel.y0, sel.y1);
    var w = Math.abs(sel.x1 - sel.x0), h = Math.abs(sel.y1 - sel.y0);
    ctx.clearRect(x, y, w, h);
    ctx.drawImage(img, x / scale, y / scale, w / scale, h / scale, x, y, w, h);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);
    info.textContent = '选区 ' + Math.round(w / scale) + '×' + Math.round(h / scale);
  }
}
canvas.addEventListener('pointerdown', function (e) {
  var rect = canvas.getBoundingClientRect();
  scale = img.width / rect.width;
  dragging = true;
  sx = (e.clientX - rect.left) * scale;
  sy = (e.clientY - rect.top) * scale;
  sel = { x0: sx, y0: sy, x1: sx, y1: sy };
});
canvas.addEventListener('pointermove', function (e) {
  if (!dragging) return;
  var rect = canvas.getBoundingClientRect();
  var mx = Math.max(0, Math.min(canvas.width, (e.clientX - rect.left) * scale));
  var my = Math.max(0, Math.min(canvas.height, (e.clientY - rect.top) * scale));
  var r = ratio.value;
  sel.x1 = mx;
  sel.y1 = my;
  if (r !== 'free') {
    var ar = eval(ratio.value);
    var w = Math.abs(mx - sx), h = Math.abs(my - sy);
    if (w / h > ar) sel.y1 = sy + Math.sign(my - sy || 1) * w / ar;
    else sel.x1 = sx + Math.sign(mx - sx || 1) * h * ar;
  }
  redraw();
});
window.addEventListener('pointerup', function () { dragging = false; });
inp.addEventListener('change', function () {
  T.loadImage(function (i) {
    img = i;
    var maxW = 860;
    scale = Math.min(1, maxW / i.width);
    canvas.width = Math.round(i.width * scale);
    canvas.height = Math.round(i.height * scale);
    canvas.style.display = '';
    sel = null;
    redraw();
  });
});
drop.addEventListener('click', function () { inp.click(); });
ratio.addEventListener('change', function () { sel = null; redraw(); });
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '比例' }), ratio, info]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('裁剪并下载 PNG', function () {
  if (!sel || Math.abs(sel.x1 - sel.x0) < 4) { T.toast('请先在图上拖拽选区'); return; }
  var x = Math.round(Math.min(sel.x0, sel.x1) / scale), y = Math.round(Math.min(sel.y0, sel.y1) / scale);
  var w = Math.round(Math.abs(sel.x1 - sel.x0) / scale), h = Math.round(Math.abs(sel.y1 - sel.y0) / scale);
  var out = T.el('canvas');
  out.width = w;
  out.height = h;
  out.getContext('2d').drawImage(img, x, y, w, h, 0, 0, w, h);
  T.dlCanvas(out, 'cropped-' + w + 'x' + h + '.png');
}, true)]));
''')

d('image-watermark', '图片加水印', '文字 / 平铺水印：字号 / 颜色 / 透明度 / 位置可调', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var text = T.input('© FreeLLM', { class: 'grow' });
var size = T.range(10, 120, 1, 28);
var alpha = T.range(5, 100, 1, 40);
var color = T.color('#FFFFFF');
var tile = T.check('平铺整个画面');
var pos = T.select([{value:'br',label:'右下'},{value:'bl',label:'左下'},{value:'tr',label:'右上'},{value:'tl',label:'左上'},{value:'c',label:'正中'}],'br');
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function render() {
  if (!img) return;
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
  ctx.globalAlpha = alpha.value / 100;
  ctx.fillStyle = color.value;
  ctx.font = '600 ' + size.value + 'px sans-serif';
  if (tile._input.checked) {
    ctx.rotate(-Math.PI / 12);
    var step = size.value * 8;
    for (var y = -canvas.height; y < canvas.height * 2; y += step) {
      for (var x = -canvas.width; x < canvas.width * 2; x += step * 2) {
        ctx.fillText(text.value, x, y);
      }
    }
  } else {
    var m = size.value;
    var x = pos.value[1] === 'l' ? m : pos.value === 'c' ? (canvas.width - ctx.measureText(text.value).width) / 2 : canvas.width - ctx.measureText(text.value).width - m;
    var y = pos.value[0] === 't' ? m + size.value : pos.value === 'c' ? canvas.height / 2 : canvas.height - m;
    ctx.fillText(text.value, x, y);
  }
  ctx.globalAlpha = 1;
  canvas.style.display = '';
}
inp.addEventListener('change', function () {
  T.loadImage(function (i) { img = i; render(); });
});
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
[text, size, alpha, color, tile._input, pos].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(drop);
app.appendChild(T.row([text, color]));
app.appendChild(T.row([T.el('span', { text: '字号' }), size, T.el('span', { text: '透明度' }), alpha, pos, tile]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载 PNG', function () { T.dlCanvas(canvas, 'watermarked.png'); }, true)]));
''')

d('image-filter', '图片滤镜', '亮度 / 对比度 / 饱和度 / 灰度 / 模糊 / 复古滤镜实时调节', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var brightness = T.range(20, 200, 1, 100);
var contrast = T.range(20, 200, 1, 100);
var saturate = T.range(0, 300, 5, 100);
var grayscale = T.range(0, 100, 1, 0);
var blur = T.range(0, 20, 0.5, 0);
var sepia = T.range(0, 100, 1, 0);
var hue = T.range(0, 360, 1, 0);
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
var PRESETS = { '原图': {}, '黑白': { grayscale: 100, contrast: 115 }, '复古': { sepia: 60, brightness: 105, saturate: 85 }, '冷色': { hue: 200, saturate: 120 }, '鲜艳': { saturate: 180, contrast: 110 }, '模糊': { blur: 4 } };
var presetRow = T.el('div', { class: 'row' });
Object.keys(PRESETS).forEach(function (name) {
  presetRow.appendChild(T.button(name, function () {
    var p = PRESETS[name];
    brightness.value = p.brightness || 100;
    contrast.value = p.contrast || 100;
    saturate.value = p.saturate || 100;
    grayscale.value = p.grayscale || 0;
    blur.value = p.blur || 0;
    sepia.value = p.sepia || 0;
    hue.value = p.hue || 0;
    render();
  }));
});
function render() {
  if (!img) return;
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext('2d');
  ctx.filter = 'brightness(' + brightness.value + '%) contrast(' + contrast.value + '%) saturate(' + saturate.value + '%) grayscale(' + grayscale.value + '%) blur(' + blur.value + 'px) sepia(' + sepia.value + '%) hue-rotate(' + hue.value + 'deg)';
  ctx.drawImage(img, 0, 0);
  ctx.filter = 'none';
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; render(); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
[brightness, contrast, saturate, grayscale, blur, sepia, hue].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(drop);
app.appendChild(presetRow);
app.appendChild(T.row([T.el('span', { text: '亮度' }), brightness, T.el('span', { text: '对比' }), contrast]));
app.appendChild(T.row([T.el('span', { text: '饱和' }), saturate, T.el('span', { text: '灰度' }), grayscale]));
app.appendChild(T.row([T.el('span', { text: '模糊' }), blur, T.el('span', { text: '复古' }), sepia, T.el('span', { text: '色相' }), hue]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载处理结果', function () { T.dlCanvas(canvas, 'filtered.png'); }, true)]));
''')

d('gif-maker', 'GIF 制作', '多张图片合成 GIF 动画：帧间隔 / 尺寸 / 色数可调', js=r'''
var frames = [];
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var list = T.el('div', { class: 'row' });
var delay = T.range(50, 2000, 50, 200);
var delayLabel = T.el('b', { text: '200ms' });
var width = T.select([{value:'320',label:'宽 320px'},{value:'480',label:'宽 480px'},{value:'640',label:'宽 640px'},{value:'原图',label:'原图宽'}],'480');
var status = T.badge('添加 ≥2 张图片');
var previewGif = T.el('img', { style: 'max-width:100%;border-radius:8px;display:none' });
var outBlob = null;
var multi = T.el('input', { type: 'file', accept: 'image/*', multiple: '', style: 'display:none' });
document.body.appendChild(multi);
multi.addEventListener('change', function () {
  var files = Array.from(multi.files);
  var loaded = 0;
  files.forEach(function (f) {
    T.loadImage(function (img) {
      frames.push(img);
      loaded++;
      if (loaded === files.length) { renderList(); play(); }
    });
  });
});
function renderList() {
  T.clearEl(list);
  frames.forEach(function (f, i) {
    var cell = T.el('div', { style: 'position:relative;border:1px solid var(--line);border-radius:8px;overflow:hidden;width:80px;height:80px' });
    var c = T.el('canvas', { width: 80, height: 80 });
    var ctx = c.getContext('2d');
    var scale = Math.max(80 / f.width, 80 / f.height);
    ctx.drawImage(f, (80 - f.width * scale) / 2, (80 - f.height * scale) / 2, f.width * scale, f.height * scale);
    cell.appendChild(c);
    var del = T.el('button', { text: '×', style: 'position:absolute;top:2px;right:2px;padding:0 6px;border:none;background:rgba(0,0,0,.5);color:#fff;border-radius:4px;cursor:pointer' });
    del.addEventListener('click', function () { frames.splice(i, 1); renderList(); });
    cell.appendChild(del);
    list.appendChild(cell);
  });
  status.textContent = frames.length + ' 帧' + (frames.length >= 2 ? '，可生成' : '');
  status.className = 'badge ' + (frames.length >= 2 ? 'ok' : '');
}
var playing = true, playIdx = 0, playTimer = 0;
function play() {
  if (!frames.length) return;
  var W = width.value === '原图' ? frames[0].width : +width.value;
  var H = Math.round(frames[0].height / frames[0].width * W);
  canvas.width = W;
  canvas.height = H;
  canvas.style.display = '';
  clearInterval(playTimer);
  playTimer = setInterval(function () {
    if (!playing || !frames.length) return;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(frames[playIdx % frames.length], 0, 0, W, H);
    playIdx++;
  }, delay.value);
}
delay.addEventListener('input', function () { delayLabel.textContent = delay.value + 'ms'; play(); });
app.appendChild(T.row([T.button('添加图片（可多选）', function () { multi.click(); }, true),
  T.button('清空', function () { frames = []; renderList(); canvas.style.display = 'none'; previewGif.style.display = 'none'; })]));
app.appendChild(list);
app.appendChild(T.row([T.el('span', { text: '帧间隔' }), delay, delayLabel, T.el('span', { text: '宽度' }), width, status]));
app.appendChild(canvas);
app.appendChild(previewGif);
app.appendChild(T.row([T.button('生成 GIF', function () {
  if (frames.length < 2) { T.toast('至少需要 2 帧'); return; }
  status.textContent = '编码中…';
  setTimeout(function () {
    var W = width.value === '原图' ? frames[0].width : +width.value;
    var H = Math.round(frames[0].height / frames[0].width * W);
    var data = frames.map(function (f) {
      var c = T.el('canvas');
      c.width = W;
      c.height = H;
      var ctx = c.getContext('2d', { willReadFrequently: true });
      ctx.drawImage(f, 0, 0, W, H);
      return { data: ctx.getImageData(0, 0, W, H).data, width: W, height: H, delay: +delay.value };
    });
    outBlob = LU.Gif.encode(data, { colors: 256 });
    previewGif.src = URL.createObjectURL(outBlob);
    previewGif.style.display = '';
    status.textContent = '✓ ' + T.fmtBytes(outBlob.size);
    status.className = 'badge ok';
  }, 50);
}, true), T.button('下载 GIF', function () { if (outBlob) T.download('animation.gif', outBlob); })]));
''')

d('image-rotate', '图片旋转翻转', '90° / 任意角度旋转 + 水平 / 垂直镜像', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var angle = T.range(-180, 180, 1, 0);
var angleLabel = T.el('b', { text: '0°' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
var flipH = false, flipV = false;
function render() {
  if (!img) return;
  angleLabel.textContent = angle.value + '°';
  var rad = angle.value * Math.PI / 180;
  var sin = Math.abs(Math.sin(rad)), cos = Math.abs(Math.cos(rad));
  canvas.width = Math.round(img.width * cos + img.height * sin);
  canvas.height = Math.round(img.width * sin + img.height * cos);
  var ctx = canvas.getContext('2d');
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(rad);
  ctx.scale(flipH ? -1 : 1, flipV ? -1 : 1);
  ctx.drawImage(img, -img.width / 2, -img.height / 2);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; render(); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
angle.addEventListener('input', render);
app.appendChild(drop);
app.appendChild(T.row([
  T.button('↺ 左转90°', function () { angle.value = (+angle.value - 90 + 360) % 360 - 180; render(); }),
  T.button('↻ 右转90°', function () { angle.value = (+angle.value + 90) % 360 > 180 ? +angle.value + 90 - 360 : +angle.value + 90; render(); }),
  T.button('⇋ 水平镜像', function () { flipH = !flipH; render(); }),
  T.button('⇵ 垂直镜像', function () { flipV = !flipV; render(); })
]));
app.appendChild(T.row([T.el('span', { text: '任意角度' }), angle, angleLabel]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载', function () { T.dlCanvas(canvas, 'rotated.png'); }, true)]));
''')

d('image-grid', '九宫格切图', '图片切 9 等份（朋友圈风格），逐格下载或整包下载', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var n = T.select([{value:'3',label:'3×3 九宫格'},{value:'2',label:'2×2 四宫格'},{value:'4',label:'4×4'}],'3');
var grid = T.el('div', { style: 'display:grid;gap:4px;margin:14px 0;max-width:480px' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var tiles = [];
function cut(img) {
  var count = +n.value;
  var size = Math.min(img.width, img.height);
  tiles = [];
  T.clearEl(grid);
  grid.style.gridTemplateColumns = 'repeat(' + count + ', 1fr)';
  var tw = Math.floor(img.width / count), th = Math.floor(img.height / count);
  for (var r = 0; r < count; r++) {
    for (var c = 0; c < count; c++) {
      var cell = T.el('canvas', { width: tw, height: th, style: 'width:100%;cursor:pointer;border-radius:4px' });
      cell.getContext('2d').drawImage(img, c * tw, r * th, tw, th, 0, 0, tw, th);
      (function (cc, rr, cnv) {
        cnv.title = '点击下载第 ' + (rr * count + cc + 1) + ' 格';
        cnv.addEventListener('click', function () { T.dlCanvas(cnv, 'grid-' + (rr + 1) + '-' + (cc + 1) + '.png'); });
      })(c, r, cell);
      grid.appendChild(cell);
      tiles.push(cell);
    }
  }
}
inp.addEventListener('change', function () { T.loadImage(cut); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
n.addEventListener('change', function () {
  T.loadImage(function () {});
  if (inp.files[0]) T.loadImage(cut);
});
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '布局' }), n]));
app.appendChild(grid);
app.appendChild(T.row([T.el('span', { text: '点击任意格子单独下载；或整体打包：' }), T.button('逐格提示下载全部', function () {
  tiles.forEach(function (t, i) {
    setTimeout(function () { T.dlCanvas(t, 'grid-' + (i + 1) + '.png'); }, i * 250);
  });
})]));
''')

d('image-picker', '图片取色器', '上传图片点击取色，HEX / RGB 一键复制', js=r'''
var drop = T.msg('点击或拖入图片，然后在图上点击取色', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var canvas = T.el('canvas', { style: 'max-width:100%;cursor:crosshair;border:1px solid var(--line);border-radius:8px;display:none' });
var picked = T.el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap;margin-top:12px' });
var current = T.badge('点击图片取色');
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var scale = 1;
inp.addEventListener('change', function () {
  T.loadImage(function (img) {
    scale = Math.min(1, 860 / img.width);
    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);
    canvas.style.display = '';
    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
  });
});
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
canvas.addEventListener('click', function (e) {
  var rect = canvas.getBoundingClientRect();
  var x = Math.round((e.clientX - rect.left) * (canvas.width / rect.width));
  var y = Math.round((e.clientY - rect.top) * (canvas.height / rect.height));
  var d = canvas.getContext('2d').getImageData(x, y, 1, 1).data;
  var hex = LU.Color.hex({ r: d[0], g: d[1], b: d[2] });
  current.textContent = hex + ' · rgb(' + d[0] + ',' + d[1] + ',' + d[2] + ')';
  current.className = 'badge blue';
  var sw = T.el('div', { style: 'width:44px;height:32px;border-radius:6px;background:' + hex + ';cursor:pointer;border:1px solid var(--line)', title: hex + '（点击复制）' });
  sw.addEventListener('click', function () { T.copy(hex); });
  picked.insertBefore(sw, picked.firstChild);
  if (picked.children.length > 12) picked.removeChild(picked.lastChild);
});
app.appendChild(drop);
app.appendChild(canvas);
app.appendChild(T.row([current, T.button('清空色板', function () { T.clearEl(picked); })]));
app.appendChild(picked);
''')

d('colorblind', '颜色盲模拟', '模拟红绿色盲 / 蓝黄色盲 / 全色盲视角查看图片', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var type = T.select([
  { value: 'protanopia', label: '红色盲 Protanopia（缺红）' },
  { value: 'deuteranopia', label: '绿色盲 Deuteranopia（缺绿）' },
  { value: 'tritanopia', label: '蓝黄色盲 Tritanopia' },
  { value: 'achromatopsia', label: '全色盲 Achromatopsia' }
], 'deuteranopia');
var before = T.el('img', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
var MATRICES = {
  protanopia: [0.567, 0.433, 0, 0.558, 0.442, 0, 0, 0.242, 0.758],
  deuteranopia: [0.625, 0.375, 0, 0.7, 0.3, 0, 0, 0.3, 0.7],
  tritanopia: [0.95, 0.05, 0, 0, 0.433, 0.567, 0, 0.475, 0.525],
  achromatopsia: [0.299, 0.587, 0.114, 0.299, 0.587, 0.114, 0.299, 0.587, 0.114]
};
function render() {
  if (!img) return;
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);
  var d = ctx.getImageData(0, 0, canvas.width, canvas.height);
  var m = MATRICES[type.value];
  for (var i = 0; i < d.data.length; i += 4) {
    var r = d.data[i], g = d.data[i + 1], b = d.data[i + 2];
    d.data[i] = r * m[0] + g * m[1] + b * m[2];
    d.data[i + 1] = r * m[3] + g * m[4] + b * m[5];
    d.data[i + 2] = r * m[6] + g * m[7] + b * m[8];
  }
  ctx.putImageData(d, 0, 0);
  canvas.style.display = '';
}
inp.addEventListener('change', function () {
  T.loadImage(function (i) {
    img = i;
    before.src = i.src;
    before.style.display = '';
    render();
  });
});
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
type.addEventListener('change', render);
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '类型' }), type]));
var cmp = T.el('div', { class: 'row', style: 'align-items:flex-start' });
cmp.appendChild(T.el('div', { class: 'field' }, [T.el('span', { text: '原图' }), before]));
cmp.appendChild(T.el('div', { class: 'field' }, [T.el('span', { text: '模拟视角' }), canvas]));
app.appendChild(cmp);
app.appendChild(T.row([T.button('下载模拟图', function () { T.dlCanvas(canvas, 'colorblind-' + type.value + '.png'); })]));
''')

d('gif-frame', 'GIF 转帧', 'GIF 分解为逐帧 PNG（使用浏览器 ImageDecoder，Chrome/Edge）', js=r'''
var pick = T.el('input', { type: 'file', accept: '.gif,image/gif', style: 'display:none' });
document.body.appendChild(pick);
var status = T.badge('—');
var box = T.el('div');
pick.addEventListener('change', function () {
  var f = pick.files[0];
  if (!f) return;
  if (!window.ImageDecoder) {
    status.textContent = '当前浏览器不支持 ImageDecoder（需 Chrome/Edge 94+）';
    status.className = 'badge warn';
    return;
  }
  status.textContent = '解码中…';
  f.arrayBuffer().then(function (buf) {
    var decoder = new ImageDecoder({ data: buf, type: 'image/gif' });
    return decoder.tracks.ready.then(function () {
      var track = decoder.tracks.selectedTrack;
      var count = Math.min(track.frameCount || 1, 60);
      var frames = [];
      var p = Promise.resolve();
      for (var i = 0; i < count; i++) {
        (function (idx) {
          p = p.then(function () {
            return decoder.decode({ frameIndex: idx }).then(function (r) {
              frames.push(r.image);
              status.textContent = '解码 ' + (idx + 1) + '/' + count;
            });
          });
        })(i);
      }
      return p.then(function () {
        T.clearEl(box);
        frames.forEach(function (img, i) {
          var c = T.el('canvas', { width: img.width, height: img.height, style: 'width:120px;border:1px solid var(--line);border-radius:6px;cursor:pointer', title: '点击下载第 ' + (i + 1) + ' 帧' });
          c.getContext('2d').drawImage(img, 0, 0);
          c.addEventListener('click', function () { T.dlCanvas(c, 'frame-' + String(i + 1).padStart(3, '0') + '.png'); });
          box.appendChild(c);
        });
        status.textContent = '✓ 共 ' + frames.length + ' 帧（点击帧下载）';
        status.className = 'badge ok';
      });
    });
  }).catch(function (e) {
    status.textContent = '解码失败：' + e.message;
    status.className = 'badge warn';
  });
});
app.appendChild(T.row([T.button('选择 GIF 文件', function () { pick.click(); }, true), status]));
app.appendChild(T.el('p', { text: '最多解码 60 帧，点击任意帧下载 PNG。', style: 'color:var(--ink2);font-size:12px' }));
app.appendChild(box);
''')

d('image2pdf', '图片转 PDF', '多张图片合并为一个 PDF（JPEG 嵌入，浏览器本地生成）', js=r'''
var pages = [];
var list = T.el('div', { class: 'row' });
var pageSize = T.select([
  { value: 'fit', label: '按图片尺寸' },
  { value: 'a4p', label: 'A4 竖版' },
  { value: 'a4l', label: 'A4 横版' }
], 'fit');
var status = T.badge('未添加图片');
var outBlob = null;
var multi = T.el('input', { type: 'file', accept: 'image/*', multiple: '', style: 'display:none' });
document.body.appendChild(multi);
multi.addEventListener('change', function () {
  var files = Array.from(multi.files);
  var loaded = 0;
  files.forEach(function (f) {
    T.loadImage(function (img) {
      pages.push(img);
      loaded++;
      if (loaded === files.length) renderList();
    });
  });
});
function renderList() {
  T.clearEl(list);
  pages.forEach(function (img, i) {
    var c = T.el('canvas', { width: 80, height: 100, style: 'border:1px solid var(--line);border-radius:6px;cursor:pointer;position:relative', title: '点击移除' });
    var ctx = c.getContext('2d');
    var scale = Math.max(80 / img.width, 100 / img.height);
    ctx.drawImage(img, (80 - img.width * scale) / 2, (100 - img.height * scale) / 2, img.width * scale, img.height * scale);
    c.addEventListener('click', function () { pages.splice(i, 1); renderList(); });
    list.appendChild(c);
  });
  status.textContent = pages.length + ' 页';
  status.className = 'badge ' + (pages.length ? 'ok' : '');
}
app.appendChild(T.row([T.button('添加图片（可多选，按顺序）', function () { multi.click(); }, true),
  T.el('span', { text: '点击缩略图可移除' }), status]));
app.appendChild(list);
app.appendChild(T.row([T.el('span', { text: '页面尺寸' }), pageSize,
  T.button('生成 PDF', function () {
    if (!pages.length) { T.toast('请先添加图片'); return; }
    status.textContent = '生成中…';
    var jobs = pages.map(function (img) {
      return new Promise(function (resolve) {
        var c = T.el('canvas');
        c.width = img.width;
        c.height = img.height;
        c.getContext('2d').drawImage(img, 0, 0);
        c.toBlob(function (b) {
          b.arrayBuffer().then(function (buf) {
            resolve({ w: img.width, h: img.height, jpeg: new Uint8Array(buf) });
          });
        }, 'image/jpeg', 0.92);
      });
    });
    Promise.all(jobs).then(function (jpegs) {
      var fit = pageSize.value === 'fit';
      var a4 = pageSize.value !== 'fit';
      var outPages = jpegs.map(function (p) {
        if (!a4) return { w: p.w, h: p.h, jpeg: p.jpeg };
        var pw = pageSize.value === 'a4p' ? 595 : 842;
        var ph = pageSize.value === 'a4p' ? 842 : 595;
        return { w: pw, h: ph, jpeg: p.jpeg, fitW: p.w, fitH: p.h };
      });
      var pdfPages = outPages.map(function (p) {
        if (!p.fitW) return p;
        var scale = Math.min((p.w - 40) / p.fitW, (p.h - 40) / p.fitH);
        return { w: p.w, h: p.h, jpeg: p.jpeg, drawW: p.fitW * scale, drawH: p.fitH * scale };
      });
      outBlob = LU.Pdf.fromJpegs(pdfPages.map(function (p) {
        return { w: p.w, h: p.h, jpeg: p.jpeg };
      }));
      status.textContent = '✓ ' + T.fmtBytes(outBlob.size);
      status.className = 'badge ok';
      T.download('images.pdf', outBlob);
    });
  }, true)]));
app.appendChild(T.msg('说明：图片以 JPEG 92% 质量嵌入 PDF；A4 模式按页面等比居中。', ''));
''')

d('image-format', '图片格式转换', 'PNG ↔ JPEG ↔ WebP 互转，透明通道自动处理', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var fmt = T.select([{value:'image/png',label:'PNG（无损/透明）'},{value:'image/jpeg',label:'JPEG（体积小）'},{value:'image/webp',label:'WebP（更小）'}],'image/webp');
var quality = T.range(0.1, 1, 0.05, 0.9);
var bg = T.color('#FFFFFF');
var info = T.badge('—');
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function render() {
  if (!img) return;
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext('2d');
  if (fmt.value !== 'image/png') {
    ctx.fillStyle = bg.value;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  ctx.drawImage(img, 0, 0);
  canvas.style.display = '';
  canvas.toBlob(function (b) {
    if (b) info.textContent = '转换后 ' + T.fmtBytes(b.size) + '（' + fmt.value.split('/')[1].toUpperCase() + '）';
  }, fmt.value, +quality.value);
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; render(); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
[fmt, quality, bg].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '目标格式' }), fmt, T.el('span', { text: '质量' }), quality, T.el('span', { text: '透明填充' }), bg, info]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载转换结果', function () {
  var ext = fmt.value.split('/')[1].replace('jpeg', 'jpg');
  canvas.toBlob(function (b) { T.download('converted.' + ext, b); }, fmt.value, +quality.value);
}, true)]));
''')

d('bg-remove', '去背景（颜色版）', '基于颜色容差的背景去除（适合纯色背景），输出透明 PNG', js=r'''
var drop = T.msg('点击或拖入图片（纯色背景效果最佳）', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var tolerance = T.range(0, 120, 1, 32);
var tolLabel = T.el('b', { text: '32' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px dashed var(--line);border-radius:8px;display:none;background:repeating-conic-gradient(#eee 0 25%, #fff 0 50%) 0 0/16px 16px' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function render() {
  if (!img) return;
  tolLabel.textContent = tolerance.value;
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);
  var d = ctx.getImageData(0, 0, canvas.width, canvas.height);
  var ref = [d.data[0], d.data[1], d.data[2]];
  var t = +tolerance.value;
  for (var i = 0; i < d.data.length; i += 4) {
    var dist = Math.abs(d.data[i] - ref[0]) + Math.abs(d.data[i + 1] - ref[1]) + Math.abs(d.data[i + 2] - ref[2]);
    if (dist < t * 3) d.data[i + 3] = 0;
    else if (dist < t * 4.5) d.data[i + 3] = Math.round((dist - t * 3) / (t * 1.5) * 255);
  }
  ctx.putImageData(d, 0, 0);
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; render(); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
tolerance.addEventListener('input', render);
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '容差（以左上角像素为背景色）' }), tolerance, tolLabel]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载透明 PNG', function () { T.dlCanvas(canvas, 'no-bg.png'); }, true),
  T.el('span', { text: '复杂背景（人像等）建议使用专业 AI 抠图服务' })]));
''')

d('image-target-kb', '压到指定 KB', '自动调整质量把图片压到目标体积以内', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var targetKB = T.num(200, { min: 5, style: 'width:90px' });
var format = T.select([{value:'image/jpeg',label:'JPEG'},{value:'image/webp',label:'WebP'}],'image/jpeg');
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var status = T.badge('—');
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
var finalBlob = null;
function compress(quality) {
  return new Promise(function (resolve) {
    canvas.toBlob(resolve, format.value, quality);
  });
}
function run() {
  var target = +targetKB.value * 1024;
  status.textContent = '二分搜索质量中…';
  status.className = 'badge blue';
  var lo = 0.05, hi = 0.96, best = null;
  function step() {
    var mid = (lo + hi) / 2;
    compress(mid).then(function (b) {
      if (b.size <= target) { best = { blob: b, q: mid }; lo = mid; }
      else hi = mid;
      if (hi - lo < 0.02) {
        if (best) {
          finalBlob = best.blob;
          status.textContent = '✓ ' + T.fmtBytes(best.blob.size) + '（质量 ' + Math.round(best.q * 100) + '%，目标 ' + targetKB.value + 'KB）';
          status.className = 'badge ok';
        } else {
          finalBlob = b;
          status.textContent = '⚠ 最低质量仍 ' + T.fmtBytes(b.size) + '，试试缩小尺寸或换 WebP';
          status.className = 'badge warn';
        }
        return;
      }
      step();
    });
  }
  step();
}
inp.addEventListener('change', function () {
  T.loadImage(function (i) {
    img = i;
    canvas.width = i.width;
    canvas.height = i.height;
    canvas.getContext('2d').drawImage(i, 0, 0);
    canvas.style.display = '';
  });
});
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '目标体积 KB' }), targetKB, format, T.button('开始压缩', run, true), status]));
app.appendChild(canvas);
app.appendChild(T.button('下载最终结果', function () {
  var ext = format.value === 'image/webp' ? 'webp' : 'jpg';
  if (finalBlob) T.download('compressed-' + targetKB.value + 'kb.' + ext, finalBlob);
  else T.toast('请先执行压缩');
}, true));
''')

d('image-stitch', '图片拼接', '多图拼长图 / 横幅 / 宫格，间距与背景可调', js=r'''
var mode = T.select([{value:'v',label:'纵向长图'},{value:'h',label:'横向横幅'},{value:'g9',label:'九宫格'}],'v');
var gap = T.range(0, 40, 1, 8);
var bg = T.color('#FFFFFF');
var width = T.num(800, { style: 'width:90px' });
var list = T.el('div', { class: 'row' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var imgs = [];
var multi = T.el('input', { type: 'file', accept: 'image/*', multiple: '', style: 'display:none' });
document.body.appendChild(multi);
multi.addEventListener('change', function () {
  var files = Array.from(multi.files);
  var loaded = 0;
  files.forEach(function (f) {
    T.loadImage(function (img) {
      imgs.push(img);
      loaded++;
      if (loaded === files.length) { renderList(); render(); }
    });
  });
});
function renderList() {
  T.clearEl(list);
  imgs.forEach(function (img, i) {
    var c = T.el('canvas', { width: 60, height: 60, style: 'border:1px solid var(--line);border-radius:6px;cursor:pointer', title: '点击移除' });
    var ctx = c.getContext('2d');
    var scale = Math.max(60 / img.width, 60 / img.height);
    ctx.drawImage(img, (60 - img.width * scale) / 2, (60 - img.height * scale) / 2, img.width * scale, img.height * scale);
    c.addEventListener('click', function () { imgs.splice(i, 1); renderList(); render(); });
    list.appendChild(c);
  });
}
function render() {
  if (!imgs.length) return;
  var W = +width.value;
  var g = +gap.value;
  var ctx;
  if (mode.value === 'v') {
    var totalH = imgs.reduce(function (s, im) { return s + Math.round(im.height / im.width * W) + g; }, -g);
    canvas.width = W;
    canvas.height = totalH;
    ctx = canvas.getContext('2d');
    ctx.fillStyle = bg.value;
    ctx.fillRect(0, 0, W, totalH);
    var y = 0;
    imgs.forEach(function (im) {
      var h = Math.round(im.height / im.width * W);
      ctx.drawImage(im, 0, y, W, h);
      y += h + g;
    });
  } else if (mode.value === 'h') {
    var scaled = imgs.map(function (im) { return { w: Math.round(im.width / im.height * 400), h: 400, im: im }; });
    var totalW = scaled.reduce(function (s, x) { return s + x.w + g; }, -g);
    canvas.width = totalW;
    canvas.height = 400;
    ctx = canvas.getContext('2d');
    ctx.fillStyle = bg.value;
    ctx.fillRect(0, 0, totalW, 400);
    var x = 0;
    scaled.forEach(function (s) {
      ctx.drawImage(s.im, x, 0, s.w, s.h);
      x += s.w + g;
    });
  } else {
    var count = Math.min(9, imgs.length);
    var cell = Math.floor((W - g * 4) / 3);
    canvas.width = W;
    canvas.height = cell * 3 + g * 2;
    ctx = canvas.getContext('2d');
    ctx.fillStyle = bg.value;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (var i = 0; i < count; i++) {
      var cx = (i % 3) * (cell + g);
      var cy = Math.floor(i / 3) * (cell + g);
      var im = imgs[i];
      var scale2 = Math.max(cell / im.width, cell / im.height);
      ctx.drawImage(im, cx + (cell - im.width * scale2) / 2, cy + (cell - im.height * scale2) / 2, im.width * scale2, im.height * scale2);
    }
  }
  canvas.style.display = '';
}
[mode, gap, bg, width].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.row([T.button('添加图片（可多选，按顺序）', function () { multi.click(); }, true), status || T.el('span', {})]));
app.appendChild(list);
app.appendChild(T.row([mode, T.el('span', { text: '间距' }), gap, T.el('span', { text: '背景' }), bg, T.el('span', { text: '宽度' }), width]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载拼接结果', function () { T.dlCanvas(canvas, 'stitched.png'); }, true)]));
''')

d('image-poster', '海报制作', '图片 + 标题文字 + 副标题，生成社媒分享海报', js=r'''
var img = null;
var drop = T.msg('点击选择背景图（可选）', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '16px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var title = T.input('FreeLLM 工具合集', { class: 'grow' });
var subtitle = T.input('打开即用的 300+ 在线工具', { class: 'grow' });
var footer = T.input('freellm.top', { class: 'grow mono' });
var accent = T.color('#1744E8');
var textColor = T.color('#FFFFFF');
var canvas = T.el('canvas', { width: 1080, height: 1440, style: 'max-width:100%;border:1px solid var(--line);border-radius:12px' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
function render() {
  var W = 1080, H = 1440;
  var ctx = canvas.getContext('2d');
  var grad = ctx.createLinearGradient(0, 0, W, H);
  grad.addColorStop(0, LU.Color.hex(LU.Color.parse(accent.value)));
  var hsl = LU.Color.rgbToHsl(LU.Color.parse(accent.value).r, LU.Color.parse(accent.value).g, LU.Color.parse(accent.value).b);
  grad.addColorStop(1, LU.Color.hex(LU.Color.hslToRgb(((hsl.h + 40) % 360) / 360, hsl.s, Math.max(0.3, hsl.l - 0.1))));
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);
  if (img) {
    ctx.globalAlpha = 0.25;
    var scale = Math.max(W / img.width, H / img.height);
    ctx.drawImage(img, (W - img.width * scale) / 2, (H - img.height * scale) / 2, img.width * scale, img.height * scale);
    ctx.globalAlpha = 1;
  }
  ctx.fillStyle = textColor.value;
  ctx.textAlign = 'center';
  ctx.font = '700 92px sans-serif';
  var lines = title.value.split('\n');
  var startY = H / 2 - (lines.length - 1) * 60;
  lines.forEach(function (l, i) {
    ctx.fillText(l, W / 2, startY + i * 120);
  });
  ctx.font = '400 40px sans-serif';
  ctx.globalAlpha = 0.9;
  ctx.fillText(subtitle.value, W / 2, startY + lines.length * 120 + 20);
  ctx.globalAlpha = 1;
  ctx.font = '500 30px monospace';
  ctx.fillText(footer.value, W / 2, H - 80);
  ctx.strokeStyle = 'rgba(255,255,255,.5)';
  ctx.lineWidth = 2;
  ctx.strokeRect(60, 60, W - 120, H - 120);
}
inp.addEventListener('change', function () {
  T.loadImage(function (i) { img = i; render(); drop.textContent = '已选择背景图（点击更换）'; });
});
drop.addEventListener('click', function () { inp.click(); });
[title, subtitle, footer, accent, textColor].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(drop);
app.appendChild(T.pane([T.field('主标题（可换行）', title), T.field('副标题', subtitle)]));
app.appendChild(T.row([T.el('span', { text: '底部文字' }), footer, T.el('span', { text: '主色' }), accent, T.el('span', { text: '文字色' }), textColor]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载海报 PNG（1080×1440）', function () { T.dlCanvas(canvas, 'poster.png'); }, true)]));
render();
''')

d('image-id-photo', '证件照制作', '换背景色 + 常用证件照规格裁剪（一寸/二寸/小二寸）', js=r'''
var drop = T.msg('点击或拖入照片（纯色背景效果最佳）', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var spec = T.select([
  { value: '295x413', label: '一寸 295×413（25×35mm）' },
  { value: '413x579', label: '二寸 413×579（35×49mm）' },
  { value: '413x531', label: '小二寸 413×531' },
  { value: '600x800', label: '签证 600×800' }
], '295x413');
var bg = T.select([{value:'#438EDB',label:'蓝底'},{value:'#FFFFFF',label:'白底'},{value:'#D9001B',label:'红底'}],'#438EDB');
var tolerance = T.range(0, 120, 1, 40);
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function render() {
  if (!img) return;
  var dims = spec.value.split('x');
  var W = +dims[0], H = +dims[1];
  canvas.width = W;
  canvas.height = H;
  var ctx = canvas.getContext('2d', { willReadFrequently: true });
  var off = T.el('canvas');
  off.width = img.width;
  off.height = img.height;
  var octx = off.getContext('2d', { willReadFrequently: true });
  octx.drawImage(img, 0, 0);
  var d = octx.getImageData(0, 0, off.width, off.height);
  var ref = [d.data[0], d.data[1], d.data[2]];
  var t = +tolerance.value;
  for (var i = 0; i < d.data.length; i += 4) {
    var dist = Math.abs(d.data[i] - ref[0]) + Math.abs(d.data[i + 1] - ref[1]) + Math.abs(d.data[i + 2] - ref[2]);
    if (dist < t * 3) d.data[i + 3] = 0;
  }
  octx.putImageData(d, 0, 0);
  ctx.fillStyle = bg.value;
  ctx.fillRect(0, 0, W, H);
  var scale = Math.max(W / off.width, H / off.height * 0.75);
  scale = H / off.height * 0.82;
  var dw = off.width * scale, dh = off.height * scale;
  ctx.drawImage(off, (W - dw) / 2, H - dh, dw, dh);
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; render(); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
[spec, bg, tolerance].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '规格' }), spec, T.el('span', { text: '背景' }), bg]));
app.appendChild(T.row([T.el('span', { text: '抠图容差' }), tolerance]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载证件照', function () { T.dlCanvas(canvas, 'id-photo-' + spec.value + '.png'); }, true),
  T.el('span', { text: '基于颜色的简化抠图，人像边缘建议配合专业工具' })]));
''')

d('image-template', '模板切图', '按预设模板处理：九宫格 / 长图拼接 / 照片墙拼贴', js=r'''
var tpl = T.select([
  { value: 'grid3', label: '九宫格发圈（3×3 独立图）' },
  { value: 'long', label: '长图（纵向拼接）' },
  { value: 'wall', label: '照片墙（4 图 2×2 拼贴）' }
], 'long');
var gap = T.range(0, 30, 1, 10);
var multi = T.el('input', { type: 'file', accept: 'image/*', multiple: '', style: 'display:none' });
document.body.appendChild(multi);
var imgs = [];
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var tiles = T.el('div', { class: 'row' });
multi.addEventListener('change', function () {
  var files = Array.from(multi.files);
  var loaded = 0;
  files.forEach(function (f) {
    T.loadImage(function (img) {
      imgs.push(img);
      loaded++;
      if (loaded === files.length) render();
    });
  });
});
function render() {
  T.clearEl(tiles);
  if (!imgs.length) return;
  var g = +gap.value;
  var W = 900;
  if (tpl.value === 'grid3') {
    var img = imgs[0];
    if (!img) return;
    var count = 3;
    var tw = Math.floor(img.width / count), th = Math.floor(img.height / count);
    T.clearEl(tiles);
    for (var r = 0; r < count; r++) for (var c = 0; c < count; c++) {
      var cell = T.el('canvas', { width: tw, height: th, style: 'width:90px;border-radius:6px;cursor:pointer', title: '点击下载' });
      cell.getContext('2d').drawImage(img, c * tw, r * th, tw, th, 0, 0, tw, th);
      (function (cnv, name) { cnv.addEventListener('click', function () { T.dlCanvas(cnv, name); }); })(cell, 'grid-' + (r + 1) + (c + 1) + '.png');
      tiles.appendChild(cell);
    }
    canvas.style.display = 'none';
    return;
  }
  if (tpl.value === 'long') {
    var totalH = imgs.reduce(function (s, im) { return s + Math.round(im.height / im.width * W) + g; }, -g);
    canvas.width = W;
    canvas.height = totalH;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, W, totalH);
    var y = 0;
    imgs.forEach(function (im) {
      var h = Math.round(im.height / im.width * W);
      ctx.drawImage(im, 0, y, W, h);
      y += h + g;
    });
  } else {
    var cell2 = Math.floor((W - g) / 2);
    canvas.width = W;
    canvas.height = cell2 * 2 + g;
    var ctx2 = canvas.getContext('2d');
    ctx2.fillStyle = '#fff';
    ctx2.fillRect(0, 0, W, canvas.height);
    imgs.slice(0, 4).forEach(function (im, i) {
      var x = (i % 2) * (cell2 + g);
      var y2 = Math.floor(i / 2) * (cell2 + g);
      var scale = Math.max(cell2 / im.width, cell2 / im.height);
      ctx2.drawImage(im, x + (cell2 - im.width * scale) / 2, y2 + (cell2 - im.height * scale) / 2, im.width * scale, im.height * scale);
    });
  }
  canvas.style.display = '';
}
[tpl, gap].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.row([T.button('添加图片', function () { multi.click(); }, true), tpl, T.el('span', { text: '间距' }), gap]));
app.appendChild(canvas);
app.appendChild(tiles);
app.appendChild(T.row([T.button('下载结果', function () { T.dlCanvas(canvas, 'template.png'); })]));
''')

d('image-mirror', '图片镜像翻转', '水平 / 垂直翻转图片，一键导出', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function draw(fx, fy) {
  if (!img) return;
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext('2d');
  ctx.translate(fx ? canvas.width : 0, fy ? canvas.height : 0);
  ctx.scale(fx ? -1 : 1, fy ? -1 : 1);
  ctx.drawImage(img, 0, 0);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; draw(false, false); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
app.appendChild(drop);
app.appendChild(T.row([T.button('⇋ 水平镜像', function () { draw(true, false); }, true),
  T.button('⇵ 垂直镜像', function () { draw(false, true); }),
  T.button('对角镜像', function () { draw(true, true); })]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载', function () { T.dlCanvas(canvas, 'mirrored.png'); })]));
''')

d('collage', '图片拼图', '多张图片拼成一张：宫格 / 自由布局，自动等分', js=r'''
var layout = T.select([
  { value: '2x1', label: '2 图横排' },
  { value: '1x2', label: '2 图竖排' },
  { value: '2x2', label: '4 图宫格' },
  { value: '3x3', label: '9 图宫格' }
], '2x2');
var gap = T.range(0, 30, 1, 8);
var bg = T.color('#FFFFFF');
var list = T.el('div', { class: 'row' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var imgs = [];
var multi = T.el('input', { type: 'file', accept: 'image/*', multiple: '', style: 'display:none' });
document.body.appendChild(multi);
multi.addEventListener('change', function () {
  var files = Array.from(multi.files);
  var loaded = 0;
  files.forEach(function (f) {
    T.loadImage(function (img) {
      imgs.push(img);
      loaded++;
      if (loaded === files.length) { renderList(); render(); }
    });
  });
});
function renderList() {
  T.clearEl(list);
  imgs.forEach(function (img, i) {
    var c = T.el('canvas', { width: 56, height: 56, style: 'border:1px solid var(--line);border-radius:6px;cursor:pointer', title: '点击移除' });
    var ctx = c.getContext('2d');
    var scale = Math.max(56 / img.width, 56 / img.height);
    ctx.drawImage(img, (56 - img.width * scale) / 2, (56 - img.height * scale) / 2, img.width * scale, img.height * scale);
    c.addEventListener('click', function () { imgs.splice(i, 1); renderList(); render(); });
    list.appendChild(c);
  });
}
function render() {
  if (!imgs.length) return;
  var parts = layout.value.split('x');
  var cols = +parts[0], rows = +parts[1];
  var need = cols * rows;
  if (imgs.length < need) { T.toast('该布局需要 ' + need + ' 张图（已有 ' + imgs.length + '）'); return; }
  var g = +gap.value;
  var cell = 400;
  canvas.width = cols * cell + (cols - 1) * g;
  canvas.height = rows * cell + (rows - 1) * g;
  var ctx = canvas.getContext('2d');
  ctx.fillStyle = bg.value;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  for (var i = 0; i < need; i++) {
    var x = (i % cols) * (cell + g);
    var y = Math.floor(i / cols) * (cell + g);
    var im = imgs[i];
    var scale = Math.max(cell / im.width, cell / im.height);
    ctx.drawImage(im, x + (cell - im.width * scale) / 2, y + (cell - im.height * scale) / 2, im.width * scale, im.height * scale);
  }
  canvas.style.display = '';
}
[layout, gap, bg].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.row([T.button('添加图片（按顺序）', function () { multi.click(); }, true), layout]));
app.appendChild(list);
app.appendChild(T.row([T.el('span', { text: '间距' }), gap, T.el('span', { text: '背景' }), bg]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载拼图', function () { T.dlCanvas(canvas, 'collage.png'); }, true)]));
''')

d('image-workspace', '连续处理工作台', '多步流水线批量处理：调整尺寸 → 滤镜 → 加水印，流程自动保存', js=r'''
var steps = [];
try { steps = JSON.parse(localStorage.getItem('freellm-workspace-steps') || '[]'); } catch (e) {}
var img = null;
var drop = T.msg('① 点击载入一张图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '20px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var pipeline = T.el('div');
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var STEP_TYPES = {
  resize: { label: '调整尺寸', params: [{ k: 'width', label: '宽度', def: 800 }, { k: 'height', label: '高度', def: 0 }] },
  grayscale: { label: '灰度', params: [] },
  brightness: { label: '亮度', params: [{ k: 'value', label: '%', def: 120 }] },
  contrast: { label: '对比度', params: [{ k: 'value', label: '%', def: 120 }] },
  saturate: { label: '饱和度', params: [{ k: 'value', label: '%', def: 140 }] },
  blur: { label: '模糊', params: [{ k: 'value', label: 'px', def: 3 }] },
  rotate: { label: '旋转', params: [{ k: 'value', label: '角度', def: 90 }] },
  watermark: { label: '文字水印', params: [{ k: 'text', label: '文字', def: '© FreeLLM' }] }
};
function saveSteps() { localStorage.setItem('freellm-workspace-steps', JSON.stringify(steps)); }
function addStep(type) {
  var st = STEP_TYPES[type];
  var step = { type: type, params: {} };
  st.params.forEach(function (p) { step.params[p.k] = p.def; });
  steps.push(step);
  saveSteps();
  renderPipeline();
}
function renderPipeline() {
  T.clearEl(pipeline);
  steps.forEach(function (step, i) {
    var st = STEP_TYPES[step.type];
    var row = T.row([T.badge((i + 1) + '. ' + st.label)]);
    st.params.forEach(function (p) {
      var inp2 = T.input(step.params[p.k], { class: 'mono', style: 'width:110px', placeholder: p.label });
      inp2.addEventListener('input', function () { step.params[p.k] = inp2.value; saveSteps(); apply(); });
      row.appendChild(T.el('span', { text: p.label }));
      row.appendChild(inp2);
    });
    row.appendChild(T.button('↑', function () {
      if (i > 0) { var t = steps[i - 1]; steps[i - 1] = steps[i]; steps[i] = t; saveSteps(); renderPipeline(); apply(); }
    }));
    row.appendChild(T.button('✕', function () { steps.splice(i, 1); saveSteps(); renderPipeline(); apply(); }));
    pipeline.appendChild(row);
  });
}
function apply() {
  if (!img) return;
  var cur = T.el('canvas');
  cur.width = img.width;
  cur.height = img.height;
  cur.getContext('2d').drawImage(img, 0, 0);
  steps.forEach(function (step) {
    var ctx = cur.getContext('2d');
    if (step.type === 'resize') {
      var nw = +step.params.width || cur.width;
      var nh = +step.params.height || Math.round(cur.height / cur.width * nw);
      var next = T.el('canvas');
      next.width = nw;
      next.height = nh;
      next.getContext('2d').drawImage(cur, 0, 0, nw, nh);
      cur = next;
    } else if (step.type === 'rotate') {
      var rad = (+step.params.value || 90) * Math.PI / 180;
      var sin = Math.abs(Math.sin(rad)), cos = Math.abs(Math.cos(rad));
      var next2 = T.el('canvas');
      next2.width = cur.width * cos + cur.height * sin;
      next2.height = cur.width * sin + cur.height * cos;
      var c2 = next2.getContext('2d');
      c2.translate(next2.width / 2, next2.height / 2);
      c2.rotate(rad);
      c2.drawImage(cur, -cur.width / 2, -cur.height / 2);
      cur = next2;
    } else if (step.type === 'watermark') {
      ctx.font = '600 ' + Math.max(14, cur.width / 30) + 'px sans-serif';
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = '#fff';
      ctx.fillText(step.params.text, 20, cur.height - 24);
      ctx.globalAlpha = 1;
    } else {
      var filters = { grayscale: 'grayscale(1)', brightness: 'brightness(' + step.params.value + '%)', contrast: 'contrast(' + step.params.value + '%)', saturate: 'saturate(' + step.params.value + '%)', blur: 'blur(' + step.params.value + 'px)' };
      var next3 = T.el('canvas');
      next3.width = cur.width;
      next3.height = cur.height;
      var c3 = next3.getContext('2d');
      c3.filter = filters[step.type];
      c3.drawImage(cur, 0, 0);
      cur = next3;
    }
  });
  canvas.width = cur.width;
  canvas.height = cur.height;
  canvas.getContext('2d').drawImage(cur, 0, 0);
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; drop.textContent = '② 已载入 ' + i.width + '×' + i.height + '，点击下方步骤加工'; apply(); }); });
drop.addEventListener('click', function () { inp.click(); });
app.appendChild(drop);
app.appendChild(T.el('span', { text: '② 添加处理步骤（顺序执行）', class: 'field' }));
var typeRow = T.el('div', { class: 'row' });
Object.keys(STEP_TYPES).forEach(function (k) {
  typeRow.appendChild(T.button(STEP_TYPES[k].label, function () { addStep(k); }));
});
app.appendChild(typeRow);
app.appendChild(pipeline);
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载结果', function () { T.dlCanvas(canvas, 'workspace.png'); }, true),
  T.button('清空流程', function () { steps = []; saveSteps(); renderPipeline(); }),
  T.el('span', { text: '流程配置自动保存在本地' })]));
renderPipeline();
''')

d('sticker', '贴纸生成', '生成带圆角 / 白边描边的贴纸风格图片（透明 PNG）', js=r'''
var drop = T.msg('点击或拖入图片', '');
drop.style.border = '1px dashed var(--line)';
drop.style.padding = '24px';
drop.style.textAlign = 'center';
drop.style.cursor = 'pointer';
var radius = T.range(0, 120, 1, 40);
var border = T.range(0, 40, 1, 12);
var borderColor = T.color('#FFFFFF');
var size = T.num(512, { min: 64, style: 'width:90px' });
var text = T.input('', { class: 'grow', placeholder: '贴纸底部文字（可选）' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px dashed var(--line);border-radius:8px;display:none;background:repeating-conic-gradient(#eee 0 25%, #fff 0 50%) 0 0/16px 16px' });
var inp = T.el('input', { type: 'file', accept: 'image/*', style: 'display:none' });
document.body.appendChild(inp);
var img = null;
function render() {
  if (!img) return;
  var S = +size.value;
  canvas.width = S;
  canvas.height = S;
  var ctx = canvas.getContext('2d');
  var pad = +border.value;
  var inner = S - pad * 2;
  ctx.fillStyle = borderColor.value;
  var r = +radius.value;
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(0, 0, S, S, r);
  else ctx.rect(0, 0, S, S);
  ctx.fill();
  ctx.save();
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(pad, pad, inner, inner, Math.max(0, r - pad));
  else ctx.rect(pad, pad, inner, inner);
  ctx.clip();
  var scale = Math.max(inner / img.width, inner / img.height);
  ctx.drawImage(img, pad + (inner - img.width * scale) / 2, pad + (inner - img.height * scale) / 2, img.width * scale, img.height * scale);
  ctx.restore();
  if (text.value) {
    ctx.font = '700 ' + Math.round(S / 14) + 'px sans-serif';
    ctx.textAlign = 'center';
    ctx.lineWidth = S / 60;
    ctx.strokeStyle = borderColor.value;
    ctx.strokeText(text.value, S / 2, S - pad / 2 - 4);
    ctx.fillStyle = '#2F3437';
    ctx.fillText(text.value, S / 2, S - pad / 2 - 4);
  }
  canvas.style.display = '';
}
inp.addEventListener('change', function () { T.loadImage(function (i) { img = i; render(); }); });
drop.addEventListener('click', function () { inp.click(); });
drop.addEventListener('dragover', function (e) { e.preventDefault(); });
drop.addEventListener('drop', function (e) { e.preventDefault(); if (e.dataTransfer.files[0]) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); } });
[radius, border, borderColor, size, text].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(drop);
app.appendChild(T.row([T.el('span', { text: '尺寸' }), size, T.el('span', { text: '圆角' }), radius, T.el('span', { text: '白边' }), border, borderColor]));
app.appendChild(T.row([text]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('下载贴纸 PNG', function () { T.dlCanvas(canvas, 'sticker.png'); }, true)]));
''')

d('avatar-maker', '头像生成', '生成个性化头像：几何图案 / 文字头像 / 随机配色', js=r'''
var style = T.select([{value:'geo',label:'几何图案（自动生成）'},{value:'text',label:'文字头像'},{value:'identicon',label:'Identicon 风格'}],'geo');
var text = T.input('FL', { class: 'grow', placeholder: '文字头像内容（1-2 字）' });
var color = T.color('#1744E8');
var size = T.select([{value:'256',label:'256px'},{value:'512',label:'512px'}],'512');
var canvas = T.el('canvas', { style: 'width:280px;height:280px;border-radius:16px;border:1px solid var(--line)' });
function render() {
  var S = +size.value;
  canvas.width = S;
  canvas.height = S;
  var ctx = canvas.getContext('2d');
  var seedRand = function () { var x = Math.sin(Date.now() / 10000) * 10000; return x - Math.floor(x); };
  var c = LU.Color.parse(color.value);
  var hsl = LU.Color.rgbToHsl(c.r, c.g, c.b);
  if (style.value === 'text') {
    ctx.fillStyle = color.value;
    ctx.fillRect(0, 0, S, S);
    ctx.fillStyle = '#fff';
    ctx.font = '600 ' + S / 2.2 + 'px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText((text.value || 'A').slice(0, 2), S / 2, S / 2 + S / 40);
  } else if (style.value === 'identicon') {
    ctx.fillStyle = '#F0F0EE';
    ctx.fillRect(0, 0, S, S);
    ctx.fillStyle = color.value;
    var cells = 5;
    var cs = S / cells;
    var rnd = function () { return Math.random(); };
    for (var col = 0; col < Math.ceil(cells / 2); col++) {
      for (var row = 0; row < cells; row++) {
        if (rnd() > 0.5) {
          ctx.fillRect(col * cs, row * cs, cs, cs);
          ctx.fillRect((cells - 1 - col) * cs, row * cs, cs, cs);
        }
      }
    }
  } else {
    var grad = ctx.createLinearGradient(0, 0, S, S);
    grad.addColorStop(0, color.value);
    grad.addColorStop(1, LU.Color.hex(LU.Color.hslToRgb(((hsl.h + 60) % 360) / 360, hsl.s, hsl.l)));
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(S / 2, S / 2, S / 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.85)';
    var shapes = 5;
    for (var i = 0; i < shapes; i++) {
      var cx = S * (0.2 + Math.random() * 0.6);
      var cy = S * (0.2 + Math.random() * 0.6);
      var rr = S * (0.06 + Math.random() * 0.14);
      ctx.beginPath();
      if (Math.random() > 0.5) ctx.arc(cx, cy, rr, 0, Math.PI * 2);
      else ctx.rect(cx - rr, cy - rr, rr * 2, rr * 2);
      ctx.fill();
    }
  }
}
[color, text, style].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.row([style, T.el('span', { text: '主色' }), color]));
app.appendChild(T.row([text]));
app.appendChild(canvas);
app.appendChild(T.row([T.button('换一批图案', function () { render(); }, true),
  T.button('下载头像', function () { T.dlCanvas(canvas, 'avatar-' + size.value + '.png'); })]));
render();
''')

d('screenshot', '屏幕截图', '浏览器截图（屏幕 / 窗口 / 标签页）+ 标注，需授权', js=r'''
var btn = T.button('开始截图（选择屏幕/窗口/标签页）', null, true);
var video = T.el('video', { autoplay: '', muted: '', style: 'max-width:100%;border-radius:8px;border:1px solid var(--line);display:none' });
var canvas = T.el('canvas', { style: 'max-width:100%;border:1px solid var(--line);border-radius:8px;display:none;cursor:crosshair' });
var color = T.color('#FF3B30');
var width = T.range(2, 20, 1, 6);
var status = T.badge('未开始');
var stream = null;
var drawing = false, ctx2 = null;
btn.onclick = function () {
  navigator.mediaDevices.getDisplayMedia({ video: true }).then(function (s) {
    stream = s;
    video.srcObject = s;
    video.style.display = '';
    status.textContent = '共享中：点击"捕捉当前画面"定格标注';
    s.getVideoTracks()[0].addEventListener('ended', function () {
      status.textContent = '共享已结束';
    });
  }).catch(function (e) { T.toast('未授权或取消：' + e.message); });
};
function capture() {
  if (!video.videoWidth) { T.toast('请先开始共享'); return; }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx2 = canvas.getContext('2d');
  ctx2.drawImage(video, 0, 0);
  canvas.style.display = '';
  status.textContent = '已捕捉，可在图上拖拽画笔标注';
}
function undo() {
  if (!ctx2) return;
  if (video.videoWidth) {
    ctx2.drawImage(video, 0, 0);
    T.toast('已重绘（标注清除）');
  }
}
canvas.addEventListener('pointerdown', function (e) {
  drawing = true;
  var rect = canvas.getBoundingClientRect();
  var sx = (e.clientX - rect.left) * (canvas.width / rect.width);
  var sy = (e.clientY - rect.top) * (canvas.height / rect.height);
  ctx2.strokeStyle = color.value;
  ctx2.lineWidth = +width.value;
  ctx2.lineCap = 'round';
  ctx2.beginPath();
  ctx2.moveTo(sx, sy);
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', function (e) {
  if (!drawing) return;
  var rect = canvas.getBoundingClientRect();
  ctx2.lineTo((e.clientX - rect.left) * (canvas.width / rect.width), (e.clientY - rect.top) * (canvas.height / rect.height));
  ctx2.stroke();
});
window.addEventListener('pointerup', function () { drawing = false; });
app.appendChild(T.row([btn, T.button('捕捉当前画面', capture), status]));
app.appendChild(video);
app.appendChild(T.row([T.el('span', { text: '画笔颜色' }), color, T.el('span', { text: '粗细' }), width,
  T.button('清除标注', undo), T.button('下载截图', function () { T.dlCanvas(canvas, 'screenshot.png'); }, true)]));
app.appendChild(canvas);
''')

d('screen-record', '在线录屏', '浏览器录屏（屏幕/窗口/标签页）+ 下载 WebM，需授权', js=r'''
var btn = T.button('开始录屏', null, true);
var status = T.badge('未开始');
var timeEl = T.stat('00:00', '时长');
var preview = T.el('video', { autoplay: '', muted: '', style: 'max-width:100%;border-radius:8px;border:1px solid var(--line);display:none' });
var stream = null, recorder = null, chunks = [], timer = 0, seconds = 0;
var lastBlob = null;
btn.onclick = function () {
  if (stream) { stop(); return; }
  navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 }, audio: false }).then(function (s) {
    stream = s;
    preview.srcObject = s;
    preview.style.display = '';
    chunks = [];
    recorder = new MediaRecorder(s, { mimeType: MediaRecorder.isTypeSupported('video/webm;codecs=vp9') ? 'video/webm;codecs=vp9' : 'video/webm' });
    recorder.ondataavailable = function (e) { chunks.push(e.data); };
    recorder.onstop = function () {
      lastBlob = new Blob(chunks, { type: 'video/webm' });
      T.toast('录制完成：' + T.fmtBytes(lastBlob.size));
    };
    recorder.start(1000);
    seconds = 0;
    timer = setInterval(function () {
      seconds++;
      timeEl.firstChild.textContent = T.pad2(Math.floor(seconds / 60)) + ':' + T.pad2(seconds % 60);
    }, 1000);
    status.textContent = '🔴 录制中（再次点击按钮停止）';
    status.className = 'badge warn';
    btn.firstChild.textContent = '停止录制';
    s.getVideoTracks()[0].addEventListener('ended', stop);
  }).catch(function (e) { T.toast('未授权或取消'); });
};
function stop() {
  if (recorder && recorder.state !== 'inactive') recorder.stop();
  if (stream) stream.getTracks().forEach(function (t) { t.stop(); });
  clearInterval(timer);
  stream = null;
  preview.style.display = 'none';
  status.textContent = '已停止';
  status.className = 'badge';
  btn.firstChild.textContent = '开始录屏';
}
app.appendChild(T.row([btn, timeEl, status]));
app.appendChild(preview);
app.appendChild(T.row([T.button('下载录像 WebM', function () {
  if (lastBlob) T.download('screen-' + Date.now() + '.webm', lastBlob);
  else T.toast('还没有录制内容');
})]));
app.appendChild(T.msg('录制内容仅在本地处理，不上传。系统音频录制视浏览器支持而定。', ''));
''')

d('canvas-draw', '白板涂鸦', 'Canvas 自由绘画：画笔 / 橡皮 / 颜色 / 粗细，导出 PNG', js=r'''
var canvas = T.el('canvas', { width: 860, height: 480, style: 'width:100%;border:1px solid var(--line);border-radius:10px;cursor:crosshair;background:#fff;touch-action:none' });
var color = T.color('#2F3437');
var size = T.range(1, 40, 1, 4);
var sizeLabel = T.el('b', { text: '4' });
var eraser = false;
var drawing = false, ctx = canvas.getContext('2d');
ctx.lineCap = 'round';
ctx.lineJoin = 'round';
canvas.addEventListener('pointerdown', function (e) {
  drawing = true;
  var rect = canvas.getBoundingClientRect();
  var x = (e.clientX - rect.left) * (canvas.width / rect.width);
  var y = (e.clientY - rect.top) * (canvas.height / rect.height);
  ctx.beginPath();
  ctx.moveTo(x, y);
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', function (e) {
  if (!drawing) return;
  var rect = canvas.getBoundingClientRect();
  var x = (e.clientX - rect.left) * (canvas.width / rect.width);
  var y = (e.clientY - rect.top) * (canvas.height / rect.height);
  ctx.strokeStyle = eraser ? '#FFFFFF' : color.value;
  ctx.lineWidth = eraser ? +size.value * 3 : +size.value;
  ctx.lineTo(x, y);
  ctx.stroke();
});
window.addEventListener('pointerup', function () { drawing = false; });
app.appendChild(T.row([color, T.el('span', { text: '粗细' }), size, sizeLabel,
  T.button(eraser ? '✏️ 画笔' : '🧽 橡皮', function () {
    eraser = !eraser;
    this.firstChild.textContent = eraser ? '✏️ 画笔' : '🧽 橡皮';
  }),
  T.button('清空', function () { ctx.clearRect(0, 0, canvas.width, canvas.height); }),
  T.button('下载 PNG', function () { T.dlCanvas(canvas, 'drawing.png'); }, true)]));
app.appendChild(canvas);
size.addEventListener('input', function () { sizeLabel.textContent = size.value; });
''')
