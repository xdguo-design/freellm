# -*- coding: utf-8 -*-
"""CSS 工具类工具定义"""
from .registry import d

d('css-gradient', 'CSS 渐变生成器', '可视化调节线性 / 径向 / 锥形渐变，三色标实时预览', js=r'''
var type = T.select([{value:'linear',label:'线性'},{value:'radial',label:'径向'},{value:'conic',label:'锥形'}],'linear');
var angle = T.range(0, 360, 1, 135);
var c1 = T.color('#1744E8');
var c2 = T.color('#7BC0E5');
var c3 = T.color('#FFB88C');
var use3 = T.check('第三色标');
var preview = T.el('div', { style: 'height:180px;border-radius:12px;border:1px solid var(--line)' });
var output = T.out('');
function grad() {
  var stops = c1.value + ', ' + c2.value + (use3._input.checked ? ', ' + c3.value : '');
  var g;
  if (type.value === 'linear') g = 'linear-gradient(' + angle.value + 'deg, ' + stops + ')';
  else if (type.value === 'radial') g = 'radial-gradient(circle at center, ' + stops + ')';
  else g = 'conic-gradient(from ' + angle.value + 'deg, ' + stops + ')';
  preview.style.background = g;
  output.value = 'background: ' + g + ';';
}
[type, angle, c1, c2, c3, use3._input].forEach(function (el) { el.addEventListener('input', grad); });
app.appendChild(T.row([T.el('span', { text: '类型' }), type, T.el('span', { text: '角度' }), angle, use3]));
app.appendChild(T.row([T.el('span', { text: '色标 1' }), c1, T.el('span', { text: '色标 2' }), c2, T.el('span', { text: '色标 3' }), c3]));
app.appendChild(preview);
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
grad();
''')

d('css-shadow', 'CSS 阴影生成器', 'Box Shadow 可视化调节：偏移 / 模糊 / 扩散 / 内阴影', js=r'''
var x = T.range(-40, 40, 1, 0), y = T.range(-40, 40, 1, 10);
var blur = T.range(0, 60, 1, 24), spread = T.range(-20, 40, 1, 0);
var color = T.color('#1744E8');
var alpha = T.range(0, 100, 1, 35);
var inset = T.check('内阴影 inset');
var box = T.el('div', { style: 'height:180px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:var(--surface-soft);margin-bottom:12px' });
var card = T.el('div', { style: 'width:130px;height:90px;border-radius:10px;background:var(--surface)' });
box.appendChild(card);
var output = T.out('');
function run() {
  var a = alpha.value / 100;
  var rgb = LU.Color.parse(color.value);
  var c = 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',' + a + ')';
  var v = (inset._input.checked ? 'inset ' : '') + x.value + 'px ' + y.value + 'px ' + blur.value + 'px ' + spread.value + 'px ' + c;
  card.style.boxShadow = v;
  output.value = 'box-shadow: ' + v + ';';
}
[x, y, blur, spread, color, alpha, inset._input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(box);
app.appendChild(T.row([T.el('span', { text: 'X' }), x, T.el('span', { text: 'Y' }), y]));
app.appendChild(T.row([T.el('span', { text: '模糊' }), blur, T.el('span', { text: '扩散' }), spread]));
app.appendChild(T.row([T.el('span', { text: '颜色' }), color, T.el('span', { text: '透明度' }), alpha, inset]));
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-border', 'CSS 圆角生成器', 'Border Radius 四角独立调节，胶囊 / 圆形一键预设', js=r'''
var tl = T.range(0, 150, 1, 16), tr = T.range(0, 150, 1, 16);
var br = T.range(0, 150, 1, 16), bl = T.range(0, 150, 1, 16);
var box = T.el('div', { style: 'height:200px;display:flex;align-items:center;justify-content:center;background:var(--surface-soft);border-radius:12px;margin-bottom:12px' });
var card = T.el('div', { style: 'width:150px;height:110px;background:var(--accent);opacity:.85' });
box.appendChild(card);
var output = T.out('');
function run() {
  var v = tl.value + 'px ' + tr.value + 'px ' + br.value + 'px ' + bl.value + 'px';
  card.style.borderRadius = v;
  output.value = 'border-radius: ' + v + ';';
}
[tl, tr, br, bl].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(box);
app.appendChild(T.row([T.el('span', { text: '左上' }), tl, T.el('span', { text: '右上' }), tr]));
app.appendChild(T.row([T.el('span', { text: '左下' }), bl, T.el('span', { text: '右下' }), br]));
app.appendChild(T.row([
  T.button('统一 16px', function () { [tl, tr, br, bl].forEach(function (s) { s.value = 16; }); run(); }),
  T.button('胶囊 pill', function () { [tl, tr, br, bl].forEach(function (s) { s.value = 75; }); run(); }),
  T.button('圆形', function () { [tl, tr, br, bl].forEach(function (s) { s.value = 150; }); run(); })
]));
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-animation', 'CSS 动画生成器', '关键帧动画可视化：属性 / 时长 / 缓动 / 延迟 / 循环', js=r'''
var prop = T.select([{value:'translateX',label:'位移 translateX'},{value:'rotate',label:'旋转 rotate'},{value:'scale',label:'缩放 scale'},{value:'opacity',label:'透明度 opacity'}],'translateX');
var from = T.num(0, { style: 'width:70px' }), to = T.num(120, { style: 'width:70px' });
var dur = T.range(0.2, 5, 0.1, 1.5), delay = T.range(0, 2, 0.1, 0);
var ease = T.select(['ease', 'linear', 'ease-in', 'ease-out', 'ease-in-out', 'cubic-bezier(.68,-.55,.27,1.55)'], 'ease-in-out');
var infinite = T.check('无限循环', true);
var alternate = T.check('往复 alternate', true);
var stage = T.el('div', { style: 'height:120px;display:flex;align-items:center;background:var(--surface-soft);border-radius:12px;margin-bottom:12px;padding-left:10px' });
var ball = T.el('div', { style: 'width:44px;height:44px;border-radius:50%;background:var(--accent)' });
stage.appendChild(ball);
var output = T.out('');
function unit(v) { return prop.value === 'opacity' ? String(v) : prop.value === 'rotate' ? v + 'deg' : v + 'px'; }
function run() {
  var kf = '@keyframes freellm-anim {\n  from { ' + prop.value + ': ' + unit(+from.value) + '; }\n  to { ' + prop.value + ': ' + unit(+to.value) + '; }\n}';
  var style = 'freellm-anim ' + dur.value + 's ' + ease.value + ' ' + delay.value + 's ' + (infinite._input.checked ? 'infinite ' : '1 ') + (alternate._input.checked ? 'alternate' : 'normal');
  ball.style.animation = 'none';
  void ball.offsetWidth;
  ball.style.animation = style;
  output.value = kf + '\n\n.animated {\n  animation: ' + style + ';\n}';
}
[prop, from, to, dur, delay, ease, infinite._input, alternate._input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(stage);
app.appendChild(T.row([T.el('span', { text: '属性' }), prop, T.el('span', { text: '从' }), from, T.el('span', { text: '到' }), to]));
app.appendChild(T.row([T.el('span', { text: '时长' }), dur, T.el('span', { text: '延迟' }), delay, T.el('span', { text: '缓动' }), ease]));
app.appendChild(T.row([infinite, alternate]));
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-glass', 'CSS 毛玻璃', 'Glassmorphism 效果生成：模糊 / 透明度 / 圆角 / 边框光', js=r'''
var blur = T.range(0, 30, 1, 12);
var alpha = T.range(0, 100, 1, 25);
var radius = T.range(0, 40, 1, 16);
var border = T.range(0, 4, 0.5, 1);
var saturate = T.range(100, 300, 10, 180);
var card = T.el('div', { style: 'padding:22px;color:#fff;font-weight:600;text-shadow:0 1px 3px rgba(0,0,0,.4);min-height:120px' });
card.innerHTML = '毛玻璃卡片<br><span style="font-size:12px;font-weight:400">Glassmorphism Preview</span>';
var stage = T.el('div', { style: 'height:220px;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:12px;background:linear-gradient(135deg,#1744E8,#7BC0E5 45%,#FFB88C);overflow:hidden' });
stage.appendChild(card);
var output = T.out('');
function run() {
  card.style.backdropFilter = 'blur(' + blur.value + 'px) saturate(' + saturate.value + '%)';
  card.style.webkitBackdropFilter = card.style.backdropFilter;
  card.style.background = 'rgba(255,255,255,' + (alpha.value / 100) + ')';
  card.style.borderRadius = radius.value + 'px';
  card.style.border = border.value + 'px solid rgba(255,255,255,.4)';
  output.value = '.glass {\n  background: rgba(255,255,255,' + (alpha.value / 100) + ');\n  backdrop-filter: blur(' + blur.value + 'px) saturate(' + saturate.value + '%);\n  -webkit-backdrop-filter: blur(' + blur.value + 'px) saturate(' + saturate.value + '%);\n  border-radius: ' + radius.value + 'px;\n  border: ' + border.value + 'px solid rgba(255,255,255,.4);\n}';
}
[blur, alpha, radius, border, saturate].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(stage);
app.appendChild(T.row([T.el('span', { text: '模糊' }), blur, T.el('span', { text: '背景透明' }), alpha]));
app.appendChild(T.row([T.el('span', { text: '圆角' }), radius, T.el('span', { text: '边框' }), border, T.el('span', { text: '饱和' }), saturate]));
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-loader', 'CSS Loading', 'Spinner / Loader 加载动画库：预览并复制 HTML + CSS', js=r'''
var box = T.el('div', { class: 'grid-cards' });
var LOADERS = [
  { name: '圆环', html: '', css: '.loader{width:40px;height:40px;border:4px solid #e5e5e5;border-top-color:#1744E8;border-radius:50%;animation:l-spin 1s linear infinite}@keyframes l-spin{to{transform:rotate(360deg)}}' },
  { name: '双圆环', html: '', css: '.loader{width:40px;height:40px;border:4px solid transparent;border-top-color:#1744E8;border-bottom-color:#1744E8;border-radius:50%;animation:l-spin 1s ease infinite}@keyframes l-spin{to{transform:rotate(360deg)}}' },
  { name: '三点跳动', html: '<span></span><span></span><span></span>', css: '.loader{display:flex;gap:6px}.loader span{width:10px;height:10px;border-radius:50%;background:#1744E8;animation:l-bounce .6s ease infinite alternate}.loader span:nth-child(2){animation-delay:.2s}.loader span:nth-child(3){animation-delay:.4s}@keyframes l-bounce{to{transform:translateY(-12px);opacity:.5}}' },
  { name: '脉冲', html: '', css: '.loader{width:40px;height:40px;border-radius:50%;background:#1744E8;animation:l-pulse 1.2s ease infinite}@keyframes l-pulse{0%{transform:scale(.6);opacity:1}100%{transform:scale(1.3);opacity:.2}}' },
  { name: '进度条', html: '', css: '.loader{width:120px;height:6px;border-radius:3px;background:#e5e5e5;overflow:hidden}.loader::after{content:"";display:block;width:40%;height:100%;border-radius:3px;background:#1744E8;animation:l-slide 1.2s ease infinite}@keyframes l-slide{0%{transform:translateX(-100%)}100%{transform:translateX(320%)}}' },
  { name: '方块翻转', html: '', css: '.loader{width:36px;height:36px;background:#1744E8;animation:l-flip 1.4s ease infinite}@keyframes l-flip{0%{transform:perspective(120px) rotateX(0) rotateY(0)}50%{transform:perspective(120px) rotateX(-180deg) rotateY(0)}100%{transform:perspective(120px) rotateX(-180deg) rotateY(-180deg)}}' },
  { name: '九宫格', html: '<span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span>', css: '.loader{display:grid;grid-template-columns:repeat(3,12px);gap:3px}.loader span{width:12px;height:12px;background:#1744E8;animation:l-grid 1.2s ease infinite}.loader span:nth-child(2),.loader span:nth-child(4),.loader span:nth-child(6){animation-delay:.1s}.loader span:nth-child(5){animation-delay:.2s}.loader span:nth-child(8){animation-delay:.3s}@keyframes l-grid{0%,70%,100%{opacity:1}35%{opacity:.2}}' },
  { name: '弹跳圆点', html: '', css: '.loader{width:12px;height:12px;border-radius:50%;background:#1744E8;animation:l-jump .5s ease infinite alternate;margin-top:30px}@keyframes l-jump{to{transform:translateY(-24px)}}' }
];
var styleEl = document.createElement('style');
document.head.appendChild(styleEl);
LOADERS.forEach(function (L) {
  var card = T.el('div', { style: 'border:1px solid var(--line);border-radius:10px;padding:20px 12px;display:flex;flex-direction:column;gap:14px;align-items:center;background:var(--surface)' });
  var demo = T.el('div', { style: 'height:56px;display:flex;align-items:center;justify-content:center' });
  var holder = T.el('div', { class: 'loader' });
  holder.innerHTML = L.html || '';
  demo.appendChild(holder);
  card.appendChild(demo);
  card.appendChild(T.el('span', { text: L.name, style: 'color:var(--ink2);font-size:12px' }));
  card.appendChild(T.button('复制代码', function () {
    T.copy('<div class="loader">' + (L.html || '') + '</div>\n<style>\n' + L.css + '\n</style>');
  }));
  box.appendChild(card);
});
styleEl.textContent = LOADERS.map(function (L) { return L.css; }).join('\n').replace(/\.loader/g, '.loader');
app.appendChild(box);
app.appendChild(T.el('p', { text: '颜色已在复制时替换为你站点的主题色即可；预览为固定蓝色。', style: 'color:var(--ink2);font-size:12px' }));
''')

d('css-unit', 'CSS 单位换算', 'px / rem / em / pt / vw / vh / % 互转（基准可调）', js=r'''
var value = T.num(16, { style: 'width:110px' });
var base = T.num(16, { style: 'width:70px', title: '根字号' });
var vwBase = T.num(1440, { style: 'width:80px', title: '视口宽度' });
var vhBase = T.num(900, { style: 'width:80px', title: '视口高度' });
var box = T.el('div');
function run() {
  var v = +value.value || 0, r = +base.value || 16;
  var rows = [
    ['px', v],
    ['rem', +(v / r).toFixed(4)],
    ['em（父级 16px）', +(v / 16).toFixed(4)],
    ['pt', +(v * 0.75).toFixed(2)],
    ['vw', +(v / (+vwBase.value || 1440) * 100).toFixed(3)],
    ['vh', +(v / (+vhBase.value || 900) * 100).toFixed(3)],
    ['%（1200 容器）', +(v / 1200 * 100).toFixed(3)]
  ];
  T.clearEl(box).appendChild(T.kvTable(rows));
}
[value, base, vwBase, vhBase].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: 'px 值' }), value, T.el('span', { text: '根字号' }), base]));
app.appendChild(T.row([T.el('span', { text: '视口宽' }), vwBase, T.el('span', { text: '视口高' }), vhBase]));
app.appendChild(box);
run();
''')

d('svg-shape', 'SVG 形状生成', '随机 Blob / 波浪 / 圆点阵图形，SVG 代码直接可用', js=r'''
var kind = T.select([{value:'blob',label:'Blob 斑点'},{value:'wave',label:'波浪分隔'},{value:'dots',label:'圆点阵'}],'blob');
var seedN = T.num(1, { min: 1, max: 999, style: 'width:80px' });
var color = T.color('#7BC0E5');
var box = T.el('div', { style: 'padding:16px;border:1px solid var(--line);border-radius:10px;background:#fff' });
var output = T.out('');
function rng(seed) {
  var s = seed;
  return function () { s = (s * 9301 + 49297) % 233280; return s / 233280; };
}
function gen() {
  var rnd = rng(+seedN.value * 97 + 11);
  var svg = '';
  if (kind.value === 'blob') {
    var pts = [];
    var n = 7;
    for (var i = 0; i < n; i++) {
      var a = i / n * Math.PI * 2;
      var r = 80 + rnd() * 70;
      pts.push([200 + Math.cos(a) * r, 150 + Math.sin(a) * r]);
    }
    var d = 'M' + pts[0][0] + ' ' + pts[0][1];
    for (i = 0; i < n; i++) {
      var p0 = pts[i], p1 = pts[(i + 1) % n];
      d += ' Q' + p0[0] + ' ' + p0[1] + ' ' + (p0[0] + p1[0]) / 2 + ' ' + (p0[1] + p1[1]) / 2;
    }
    d += ' Z';
    svg = '<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg" width="100%" height="220"><path d="' + d + '" fill="' + color.value + '"/></svg>';
  } else if (kind.value === 'wave') {
    var amp = 30 + Math.floor(rnd() * 40);
    svg = '<svg viewBox="0 0 400 120" xmlns="http://www.w3.org/2000/svg" width="100%" height="120"><path d="M0 60 Q100 ' + (60 - amp) + ' 200 60 T400 60 V120 H0 Z" fill="' + color.value + '"/></svg>';
  } else {
    var dots = '';
    for (var yy = 0; yy < 8; yy++) for (var xx = 0; xx < 16; xx++) {
      if (rnd() > 0.45) dots += '<circle cx="' + (20 + xx * 24) + '" cy="' + (20 + yy * 24) + '" r="' + (2 + rnd() * 6).toFixed(1) + '" fill="' + color.value + '"/>';
    }
    svg = '<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" width="100%" height="200">' + dots + '</svg>';
  }
  box.innerHTML = svg;
  output.value = svg;
}
[kind, seedN, color].forEach(function (el) { el.addEventListener('input', gen); });
app.appendChild(T.row([T.el('span', { text: '类型' }), kind, T.el('span', { text: '种子' }), seedN, T.el('span', { text: '颜色' }), color]));
app.appendChild(box);
app.appendChild(T.pane([T.field('SVG 代码', output)], true));
app.appendChild(T.row([T.button('换一个', function () { seedN.value = +seedN.value + 1; gen(); }, true), T.btnCopy(function () { return output.value; })]));
gen();
''')

d('font-preview', '字体预览器', '上传 TTF / OTF / WOFF 字体文件，实时预览任意文案', js=r'''
var pick = T.el('input', { type: 'file', accept: '.ttf,.otf,.woff,.woff2', style: 'display:none' });
document.body.appendChild(pick);
var textIn = T.textarea('FreeLLM 免费工具站\nThe quick brown fox jumps over the lazy dog.\n永和九年，岁在癸丑。0123456789', true);
textIn.value = 'FreeLLM 免费工具站\nThe quick brown fox jumps over the lazy dog.\n永和九年，岁在癸丑。0123456789';
var size = T.range(14, 72, 1, 28);
var preview = T.el('div', { class: 'output', style: 'min-height:220px;font-size:28px;line-height:1.6;white-space:pre-wrap;font-family:var(--font-sans)' });
var fname = T.badge('未选择字体');
function setFace(buf, name) {
  var font = new FontFace('UserFont', buf);
  font.load().then(function (f) {
    document.fonts.add(f);
    preview.style.fontFamily = 'UserFont';
    fname.textContent = '✓ ' + name;
    fname.className = 'badge ok';
  }).catch(function (e) { T.toast('字体解析失败：' + e.message); });
}
pick.addEventListener('change', function () {
  var f = pick.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () { setFace(fr.result, f.name); };
  fr.readAsArrayBuffer(f);
});
function render() {
  preview.style.fontSize = size.value + 'px';
  preview.textContent = textIn.value;
}
app.appendChild(T.row([T.button('选择字体文件', function () { pick.click(); }, true), fname]));
app.appendChild(T.row([T.el('span', { text: '字号' }), size]));
app.appendChild(T.pane([T.field('预览文案', textIn)], true));
app.appendChild(preview);
textIn.addEventListener('input', render);
size.addEventListener('input', render);
render();
''')

d('css-flexbox', 'CSS Flexbox 可视化', '容器属性可视化调节，实时生成 Flexbox CSS', js=r'''
var dir = T.select(['row', 'row-reverse', 'column', 'column-reverse'], 'row');
var justify = T.select(['flex-start', 'center', 'flex-end', 'space-between', 'space-around', 'space-evenly'], 'flex-start');
var align = T.select(['stretch', 'flex-start', 'center', 'flex-end', 'baseline'], 'stretch');
var wrapSel = T.select(['nowrap', 'wrap'], 'nowrap');
var gap = T.range(0, 40, 1, 10);
var stage = T.el('div', { style: 'min-height:180px;border:1px dashed var(--line);border-radius:12px;padding:10px;background:var(--surface-soft);margin-bottom:12px' });
var colors = ['#1744E8', '#7BC0E5', '#FFB88C', '#B8E986'];
for (var i = 0; i < 4; i++) {
  var it = T.el('div', { style: 'width:70px;min-height:44px;text-align:center;line-height:44px;border-radius:8px;color:#fff;font-weight:600;background:' + colors[i] });
  it.textContent = i + 1;
  stage.appendChild(it);
}
var output = T.out('');
function run() {
  stage.style.display = 'flex';
  stage.style.flexDirection = dir.value;
  stage.style.justifyContent = justify.value;
  stage.style.alignItems = align.value;
  stage.style.flexWrap = wrapSel.value;
  stage.style.gap = gap.value + 'px';
  output.value = '.container {\n  display: flex;\n  flex-direction: ' + dir.value + ';\n  justify-content: ' + justify.value + ';\n  align-items: ' + align.value + ';\n  flex-wrap: ' + wrapSel.value + ';\n  gap: ' + gap.value + 'px;\n}';
}
[dir, justify, align, wrapSel, gap].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(stage);
app.appendChild(T.pane([T.field('flex-direction', dir), T.field('justify-content', justify)]));
app.appendChild(T.pane([T.field('align-items', align), T.field('flex-wrap', wrapSel)]));
app.appendChild(T.row([T.el('span', { text: 'gap' }), gap]));
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-grid', 'CSS Grid 可视化', 'Grid 行列数 / 列宽 / 间距可视化，生成 grid-template CSS', js=r'''
var cols = T.num(3, { min: 1, max: 12, style: 'width:70px' });
var rowsN = T.num(3, { min: 1, max: 12, style: 'width:70px' });
var colFr = T.select([{value:'1fr',label:'1fr 均分'},{value:'auto',label:'auto 自适应'},{value:'80px',label:'固定 80px'}],'1fr');
var gap = T.range(0, 40, 1, 10);
var stage = T.el('div', { style: 'border:1px dashed var(--line);border-radius:12px;padding:10px;background:var(--surface-soft);margin-bottom:12px' });
var output = T.out('');
function run() {
  T.clearEl(stage);
  var c = Math.min(12, +cols.value || 1), r = Math.min(12, +rowsN.value || 1);
  var n = Math.min(24, c * r);
  for (var i = 0; i < n; i++) {
    var it = T.el('div', { style: 'min-height:44px;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600;background:' + (i % 2 ? '#7BC0E5' : '#1744E8') });
    it.textContent = i + 1;
    stage.appendChild(it);
  }
  stage.style.display = 'grid';
  stage.style.gridTemplateColumns = 'repeat(' + c + ', ' + colFr.value + ')';
  stage.style.gap = gap.value + 'px';
  output.value = '.container {\n  display: grid;\n  grid-template-columns: repeat(' + c + ', ' + colFr.value + ');\n  grid-template-rows: repeat(' + r + ', auto);\n  gap: ' + gap.value + 'px;\n}';
}
[cols, rowsN, colFr, gap].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '列数' }), cols, T.el('span', { text: '行数' }), rowsN]));
app.appendChild(T.row([T.el('span', { text: '列宽' }), colFr, T.el('span', { text: 'gap' }), gap]));
app.appendChild(stage);
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-clip-path', 'CSS Clip-path 生成', '可视化裁剪路径：圆形 / 椭圆 / 三角 / 六边形 / 星形等', js=r'''
var shape = T.select([
  { value: 'circle', label: 'circle 圆形' },
  { value: 'ellipse', label: 'ellipse 椭圆' },
  { value: 'triangle', label: '三角形' },
  { value: 'diamond', label: '菱形' },
  { value: 'hexagon', label: '六边形' },
  { value: 'arrow', label: '箭头' },
  { value: 'star', label: '星形' }
], 'circle');
var size = T.range(40, 100, 1, 70);
var box = T.el('div', { style: 'height:240px;display:flex;align-items:center;justify-content:center;background:var(--surface-soft);border-radius:12px;margin-bottom:12px' });
var img = T.el('div', { style: 'width:220px;height:180px;background:linear-gradient(135deg,#1744E8,#7BC0E5,#FFB88C);transition:all .2s' });
box.appendChild(img);
var output = T.out('');
function poly(pts) { return 'polygon(' + pts.map(function (p) { return p[0] + '% ' + p[1] + '%'; }).join(', ') + ')'; }
function run() {
  var s = +size.value;
  var v;
  if (shape.value === 'circle') v = 'circle(' + s / 2 + '% at 50% 50%)';
  else if (shape.value === 'ellipse') v = 'ellipse(' + s + '% ' + (s * 0.7) + '% at 50% 50%)';
  else if (shape.value === 'triangle') v = poly([[50, 50 - s / 2], [50 + s / 2, 50 + s / 2], [50 - s / 2, 50 + s / 2]]);
  else if (shape.value === 'diamond') v = poly([[50, 50 - s / 2], [50 + s / 2, 50], [50, 50 + s / 2], [50 - s / 2, 50]]);
  else if (shape.value === 'hexagon') v = poly([[50 - s / 2, 50], [50 - s / 4, 50 - s / 2], [50 + s / 4, 50 - s / 2], [50 + s / 2, 50], [50 + s / 4, 50 + s / 2], [50 - s / 4, 50 + s / 2]]);
  else if (shape.value === 'arrow') v = poly([[0, 30], [60, 30], [60, 10], [100, 50], [60, 90], [60, 70], [0, 70]]);
  else {
    var pts = [];
    for (var i = 0; i < 10; i++) {
      var a = -Math.PI / 2 + i * Math.PI / 5;
      var r = i % 2 ? s / 4.2 : s / 2;
      pts.push([(50 + Math.cos(a) * r).toFixed(1), (50 + Math.sin(a) * r).toFixed(1)]);
    }
    v = poly(pts);
  }
  img.style.clipPath = v;
  output.value = 'clip-path: ' + v + ';';
}
[shape, size].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(box);
app.appendChild(T.row([T.el('span', { text: '形状' }), shape, T.el('span', { text: '尺寸' }), size]));
app.appendChild(T.pane([T.field('CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-filter', 'CSS Filter 生成', '滤镜参数可视化：模糊 / 亮度 / 对比度 / 饱和 / 色相 / 灰度等', js=r'''
var blur = T.range(0, 20, 0.5, 0), brightness = T.range(20, 200, 1, 100);
var contrast = T.range(20, 200, 1, 100), saturate = T.range(0, 300, 5, 100);
var hue = T.range(0, 360, 1, 0), gray = T.range(0, 100, 1, 0);
var sepia = T.range(0, 100, 1, 0), invert = T.range(0, 100, 1, 0);
var box = T.el('div', { style: 'display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px' });
var bgc = 'linear-gradient(135deg,#1744E8,#7BC0E5,#FFB88C)';
var imgBox = T.el('div', { style: 'height:160px;border-radius:10px;background:' + bgc });
var rawBox = T.el('div', { style: 'height:160px;border-radius:10px;background:' + bgc });
box.appendChild(imgBox); box.appendChild(rawBox);
var output = T.out('');
function run() {
  var parts = [];
  if (+blur.value) parts.push('blur(' + blur.value + 'px)');
  if (+brightness.value !== 100) parts.push('brightness(' + brightness.value + '%)');
  if (+contrast.value !== 100) parts.push('contrast(' + contrast.value + '%)');
  if (+saturate.value !== 100) parts.push('saturate(' + saturate.value + '%)');
  if (+hue.value) parts.push('hue-rotate(' + hue.value + 'deg)');
  if (+gray.value) parts.push('grayscale(' + gray.value + '%)');
  if (+sepia.value) parts.push('sepia(' + sepia.value + '%)');
  if (+invert.value) parts.push('invert(' + invert.value + '%)');
  imgBox.style.filter = parts.join(' ');
  output.value = '.filtered {\n  filter: ' + (parts.join(' ') || 'none') + ';\n}';
}
[blur, brightness, contrast, saturate, hue, gray, sepia, invert].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(box);
app.appendChild(T.row([T.el('span', { text: '模糊' }), blur, T.el('span', { text: '亮度' }), brightness]));
app.appendChild(T.row([T.el('span', { text: '对比' }), contrast, T.el('span', { text: '饱和' }), saturate]));
app.appendChild(T.row([T.el('span', { text: '色相' }), hue, T.el('span', { text: '灰度' }), gray]));
app.appendChild(T.row([T.el('span', { text: '怀旧' }), sepia, T.el('span', { text: '反色' }), invert]));
app.appendChild(T.pane([T.field('CSS（左为效果，右为原图）', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('css-contrast', '对比度检查器', 'WCAG 2.1 前景 / 背景对比度检测：AA / AAA 通过情况', js=r'''
var fg = T.color('#2F3437');
var bg = T.color('#FBFBFA');
var sample = T.el('div', { style: 'padding:26px;border-radius:12px;border:1px solid var(--line);margin-bottom:12px' });
sample.innerHTML = '<div style="font-size:22px;font-weight:700">大号标题文字 (≥24px)</div><div style="margin-top:8px;font-size:16px">正文示例文字 (14-18px)</div>';
var info = T.el('div');
function run() {
  var f = LU.Color.parse(fg.value), b = LU.Color.parse(bg.value);
  var ratio = LU.Color.contrast(f, b);
  sample.style.background = bg.value;
  sample.style.color = fg.value;
  var rows = [
    ['对比度', ratio.toFixed(2) + ' : 1'],
    ['AA 正文（≥4.5）', ratio >= 4.5 ? '✓ 通过' : '✗ 不通过'],
    ['AA 大字（≥3）', ratio >= 3 ? '✓ 通过' : '✗ 不通过'],
    ['AAA 正文（≥7）', ratio >= 7 ? '✓ 通过' : '✗ 不通过'],
    ['AAA 大字（≥4.5）', ratio >= 4.5 ? '✓ 通过' : '✗ 不通过'],
    ['UI 组件（≥3）', ratio >= 3 ? '✓ 通过' : '✗ 不通过']
  ];
  T.clearEl(info).appendChild(T.kvTable(rows));
}
[fg, bg].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(sample);
app.appendChild(T.row([T.el('span', { text: '前景色' }), fg, T.el('span', { text: '背景色' }), bg]));
app.appendChild(info);
run();
''')

d('css-variables', 'CSS 变量生成', '从主色生成 CSS 自定义属性色阶系统（含暗色覆盖）', js=r'''
var primary = T.color('#1744E8');
var prefix = T.input('--brand', { class: 'grow mono' });
var dark = T.check('同时生成暗色变量');
var output = T.out('');
var previewBox = T.el('div', { style: 'display:flex;gap:6px;margin:12px 0' });
function shade(rgb, l) {
  var hsl = LU.Color.rgbToHsl(rgb.r, rgb.g, rgb.b);
  return LU.Color.hex(LU.Color.hslToRgb(hsl.h / 360, hsl.s, l));
}
function run() {
  var rgb = LU.Color.parse(primary.value);
  var hsl = LU.Color.rgbToHsl(rgb.r, rgb.g, rgb.b);
  var p = prefix.value || '--brand';
  var lines = [':root {', '  ' + p + ': ' + primary.value + ';'];
  var levels = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1];
  levels.forEach(function (l, i) {
    var name = i < 4 ? 100 + i * 100 : 500 + (i - 4) * 100;
    lines.push('  ' + p + '-' + name + ': ' + shade(rgb, l) + ';');
  });
  lines.push('  ' + p + '-rgb: ' + rgb.r + ' ' + rgb.g + ' ' + rgb.b + ';');
  lines.push('}');
  if (dark._input.checked) {
    lines.push('');
    lines.push('[data-theme="dark"] {');
    lines.push('  ' + p + ': ' + shade(rgb, Math.min(0.75, hsl.l + 0.25)) + ';');
    lines.push('}');
  }
  output.value = lines.join('\n');
  T.clearEl(previewBox);
  [0.9, 0.7, 0.5, 0.3, 0.1].forEach(function (l) {
    previewBox.appendChild(T.el('div', { style: 'flex:1;height:44px;border-radius:8px;background:' + shade(rgb, l) }));
  });
}
app.appendChild(T.row([T.el('span', { text: '主色' }), primary, dark]));
app.appendChild(T.row([T.el('span', { text: '变量前缀' }), prefix]));
app.appendChild(previewBox);
app.appendChild(T.pane([T.field('CSS 变量', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
[primary, prefix, dark._input].forEach(function (el) { el.addEventListener('input', run); });
run();
''')

d('css-reset', 'CSS Reset 生成', '按需生成 CSS Reset：盒模型 / 媒体 / 表单 / 列表 / 排版基线', js=r'''
var opts = [
  T.check('盒模型 box-sizing', true),
  T.check('外边距清零', true),
  T.check('媒体元素自适应（img/video）', true),
  T.check('表单元素继承字体', true),
  T.check('列表清除', false),
  T.check('链接样式', true),
  T.check('smooth 滚动 + 文字渲染', true),
  T.check('现代精简版（2024 风格）', true)
];
var output = T.out('');
function run() {
  var modern = opts[7]._input.checked;
  var lines = [];
  if (opts[0]._input.checked) lines.push(modern ? '*, *::before, *::after { box-sizing: border-box; }' : 'html { box-sizing: border-box; }\n*, *::before, *::after { box-sizing: inherit; }');
  if (opts[1]._input.checked) lines.push('* { margin: 0; }');
  if (opts[2]._input.checked) lines.push('img, picture, video, canvas, svg { display: block; max-width: 100%; }');
  if (opts[3]._input.checked) lines.push('input, button, textarea, select { font: inherit; }');
  if (opts[4]._input.checked) lines.push('ol, ul { list-style: none; padding: 0; }');
  if (opts[5]._input.checked) lines.push('a { color: inherit; text-decoration: none; }');
  if (opts[6]._input.checked) lines.push('html { scroll-behavior: smooth; -webkit-text-size-adjust: 100%; text-rendering: optimizeLegibility; }');
  if (modern) {
    lines.push('p, h1, h2, h3, h4, h5, h6 { overflow-wrap: break-word; }');
    if (opts[1]._input.checked) lines.push('body { min-height: 100vh; line-height: 1.5; -webkit-font-smoothing: antialiased; }');
  }
  output.value = lines.join('\n\n') + '\n';
}
opts.forEach(function (o) { o._input.addEventListener('change', run); });
var wrap = T.el('div', { class: 'row' });
opts.forEach(function (o) { wrap.appendChild(o); });
app.appendChild(wrap);
app.appendChild(T.pane([T.field('Reset CSS', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; }), T.button('下载 reset.css', function () { T.download('reset.css', output.value, 'text/css'); })]));
run();
''')

d('color-palette', '调色板生成器', '输入主色自动生成配色：类比 / 互补 / 三角 / 四角 / 单色 + 语义色', js=r'''
var primary = T.color('#1744E8');
var scheme = T.select([{value:'analogous',label:'类比色'},{value:'complementary',label:'互补色'},{value:'triadic',label:'三角配色'},{value:'tetradic',label:'四角配色'},{value:'monochrome',label:'单色系'}],'analogous');
var box = T.el('div', { style: 'display:flex;flex-direction:column;gap:8px;margin:12px 0' });
var output = T.out('');
function hexShift(hsl, dh, ds, dl) {
  return LU.Color.hex(LU.Color.hslToRgb(((((hsl.h + dh) % 360) + 360) % 360) / 360, Math.max(0, Math.min(1, hsl.s + ds)), Math.max(0, Math.min(1, hsl.l + dl))));
}
function run() {
  var rgb = LU.Color.parse(primary.value);
  var hsl = LU.Color.rgbToHsl(rgb.r, rgb.g, rgb.b);
  var colors;
  if (scheme.value === 'analogous') colors = [hexShift(hsl, -40, 0, 0), primary.value, hexShift(hsl, 40, 0, 0)];
  else if (scheme.value === 'complementary') colors = [primary.value, hexShift(hsl, 180, 0, 0)];
  else if (scheme.value === 'triadic') colors = [primary.value, hexShift(hsl, 120, 0, 0), hexShift(hsl, 240, 0, 0)];
  else if (scheme.value === 'tetradic') colors = [primary.value, hexShift(hsl, 90, 0, 0), hexShift(hsl, 180, 0, 0), hexShift(hsl, 270, 0, 0)];
  else colors = [hexShift(hsl, 0, 0, .3), hexShift(hsl, 0, 0, .15), primary.value, hexShift(hsl, 0, 0, -.15), hexShift(hsl, 0, 0, -.3)];
  var semantic = {
    'primary': primary.value,
    'primary-hover': hexShift(hsl, 0, 0, -0.08),
    'primary-light': hexShift(hsl, 0, 0, 0.85),
    'success': hexShift(hsl, 120, -0.05, 0),
    'warning': hexShift(hsl, 45, 0, 0),
    'danger': hexShift(hsl, 180, 0, 0),
    'info': hexShift(hsl, -30, 0, 0.05)
  };
  T.clearEl(box);
  var row = T.el('div', { style: 'display:flex;gap:6px;height:52px' });
  colors.forEach(function (c) {
    var d = T.el('div', { style: 'flex:1;border-radius:8px;background:' + c + ';cursor:pointer;min-width:0', title: c + '（点击复制）' });
    d.addEventListener('click', function () { T.copy(c); });
    row.appendChild(d);
  });
  box.appendChild(row);
  Object.keys(semantic).forEach(function (k) {
    var r2 = T.el('div', { style: 'display:flex;gap:10px;align-items:center' });
    var d2 = T.el('div', { style: 'width:52px;height:26px;border-radius:6px;background:' + semantic[k] + ';border:1px solid var(--line);cursor:pointer' });
    d2.addEventListener('click', function () { T.copy(semantic[k]); });
    r2.appendChild(d2);
    r2.appendChild(T.el('span', { text: k + '  ' + semantic[k], style: 'font-family:var(--font-mono);font-size:12px' }));
    box.appendChild(r2);
  });
  output.value = ':root {\n' + Object.keys(semantic).map(function (k) { return '  --' + k + ': ' + semantic[k] + ';'; }).join('\n') + '\n}';
}
app.appendChild(T.row([T.el('span', { text: '主色' }), primary, T.el('span', { text: '配色方案' }), scheme]));
app.appendChild(box);
app.appendChild(T.pane([T.field('语义色 CSS 变量', output)], true));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
[primary, scheme].forEach(function (el) { el.addEventListener('input', run); });
run();
''')
