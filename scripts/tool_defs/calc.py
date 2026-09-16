# -*- coding: utf-8 -*-
"""计算转换类工具定义"""
from .registry import d
import json

CONVERTER_JS = r'''
var value = T.num(1, { style: 'width:130px' });
var from = T.select(__UNITS__, __FROM__);
var to = T.select(__UNITS__, __TO__);
var output = T.input('', { class: 'grow mono', readonly: '' });
var table = T.el('div');
var U = __DATA__;
function cv(v, f, t) {
  if (f === t) return v;
  return v * U[f] / U[t];
}
function run() {
  var v = +value.value;
  if (isNaN(v)) { output.value = ''; return; }
  output.value = +(cv(v, from.value, to.value).toPrecision(10));
  var rows = [];
  Object.keys(U).forEach(function (k) {
    rows.push([k, +(cv(v, from.value, k).toPrecision(8))]);
  });
  T.clearEl(table).appendChild(T.kvTable(rows));
}
[value, from, to].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([value, from, T.el('span', { text: '→' }), to, output]));
app.appendChild(T.el('span', { text: '换算到全部单位', class: 'field' }));
app.appendChild(table);
run();
'''

TEMP_JS = r'''
var value = T.num(25, { style: 'width:130px' });
var from = T.select([{value:'C',label:'摄氏 °C'},{value:'F',label:'华氏 °F'},{value:'K',label:'开氏 K'},{value:'R',label:'兰氏 °R'}],'C');
var table = T.el('div');
function toC(v, f) {
  if (f === 'C') return v;
  if (f === 'F') return (v - 32) * 5 / 9;
  if (f === 'K') return v - 273.15;
  return (v - 491.67) * 5 / 9;
}
function fromC(c) {
  return {
    '摄氏 °C': c,
    '华氏 °F': c * 9 / 5 + 32,
    '开氏 K': c + 273.15,
    '兰氏 °R': (c + 273.15) * 9 / 5
  };
}
function run() {
  var c = toC(+value.value, from.value);
  var rows = [];
  var ref = fromC(c);
  var names = { 'C': '摄氏 °C', 'F': '华氏 °F', 'K': '开氏 K', 'R': '兰氏 °R' };
  Object.keys(names).forEach(function (k) { rows.push([names[k], +ref[names[k]].toFixed(4)]); });
  var extra = [];
  if (c <= 0) extra.push('水的冰点及以下 ❄');
  if (c >= 100) extra.push('水的沸点及以上 ♨');
  if (c >= 36 && c <= 38) extra.push('接近人体体温');
  if (extra.length) rows.push(['备注', extra.join(' · ')]);
  T.clearEl(table).appendChild(T.kvTable(rows));
}
[value, from].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([value, from]));
app.appendChild(table);
run();
'''

CONVERTERS = {
    'speed-converter': ('速度单位换算', 'km/h ↔ mph ↔ m/s ↔ 节 等', {
        'm/s (米/秒)': 1, 'km/h (千米/时)': 3.6, 'mph (英里/时)': 1.609344,
        'knot (节)': 1.852, 'ft/s (英尺/秒)': 0.3048, 'Mach (海平面声速)': 340.29}, 'km/h (千米/时)'),
    'pressure-converter': ('压力单位换算', 'Pa / Bar / PSI / atm / mmHg 等', {
        'Pa (帕斯卡)': 1, 'kPa': 1e3, 'MPa': 1e6, 'bar': 1e5, 'mbar': 100,
        'atm (标准大气压)': 101325, 'psi (磅/英寸²)': 6894.757, 'mmHg (托)': 133.322}, 'bar'),
    'energy-converter': ('能量单位换算', 'J / kcal / kWh / BTU 等', {
        'J (焦耳)': 1, 'kJ': 1e3, 'cal (卡)': 4.184, 'kcal (大卡)': 4184,
        'Wh': 3600, 'kWh (度)': 3.6e6, 'BTU': 1055.06, 'eV': 1.602176634e-19}, 'kJ'),
    'power-converter': ('功率单位换算', 'W / kW / 马力 等', {
        'W (瓦特)': 1, 'kW': 1e3, 'MW': 1e6, 'hp (机械马力)': 745.6999,
        'hp (公制马力)': 735.4988, 'ft·lb/s': 1.35582}, 'kW'),
    'frequency-converter': ('频率单位换算', 'Hz / kHz / MHz / GHz / rpm', {
        'Hz': 1, 'kHz': 1e3, 'MHz': 1e6, 'GHz': 1e9, 'rpm (转/分)': 1 / 60}, 'MHz'),
    'angle-converter': ('角度单位换算', '度 / 弧度 / 梯度 / 圆周', {
        '度 (°)': 1, '弧度 (rad)': 57.29577951308232, '梯度 (gon)': 0.9,
        '圆周 (turn)': 360, '角分 (′)': 1 / 60, '角秒 (″)': 1 / 3600}, '度 (°)'),
    'density-converter': ('密度单位换算', 'kg/m³ ↔ g/cm³ ↔ lb/ft³', {
        'kg/m³': 1, 'g/cm³': 1000, 'g/mL': 1000, 'lb/ft³': 16.018463, 'lb/in³': 27679.905}, 'g/cm³'),
    'volume-converter': ('体积单位换算', 'L / mL / m³ / 加仑 / 杯', {
        'L (升)': 1, 'mL (毫升)': 0.001, 'm³': 1000, 'gal (美制加仑)': 3.785411784,
        'qt (夸脱)': 0.946352946, 'pt (品脱)': 0.473176473, 'cup (杯)': 0.2365882365,
        'fl oz (液盎司)': 0.0295735296, '汤匙': 0.0147868, '茶匙': 0.00492892}, 'L (升)'),
    'weight-converter': ('重量单位换算', 'g / kg / 斤 / 磅 / 盎司', {
        'g (克)': 1, 'kg (千克)': 1000, 't (吨)': 1e6, '斤': 500, '两': 50,
        'lb (磅)': 453.59237, 'oz (盎司)': 28.349523125, 'ct (克拉)': 0.2}, 'kg (千克)'),
    'length-converter': ('长度单位换算', 'mm / cm / m / inch / ft / 尺寸', {
        'm (米)': 1, 'mm (毫米)': 0.001, 'cm (厘米)': 0.01, 'km (千米)': 1000,
        'in (英寸)': 0.0254, 'ft (英尺)': 0.3048, 'yd (码)': 0.9144,
        'mi (英里)': 1609.344, 'nmi (海里)': 1852, '尺': 1 / 3, '寸': 1 / 30,
        'px (96dpi)': 0.0002645833}, 'cm (厘米)'),
    'area-converter': ('面积单位换算', 'm² / 亩 / 公顷 / 平方英尺', {
        'm² (平方米)': 1, 'km² (平方千米)': 1e6, 'cm²': 0.0001, 'ha (公顷)': 10000,
        '亩': 666.6666667, 'ft² (平方英尺)': 0.09290304, 'in² (平方英寸)': 0.00064516,
        'acre (英亩)': 4046.8564224, 'yd² (平方码)': 0.83612736}, 'm² (平方米)'),
    'time-converter': ('时间单位换算', '秒 / 分 / 时 / 天 / 周 / 年', {
        '秒 (s)': 1, '毫秒 (ms)': 0.001, '分 (min)': 60, '小时 (h)': 3600,
        '天 (d)': 86400, '周 (wk)': 604800, '月 (30天)': 2592000, '年 (365天)': 31536000}, '小时 (h)'),
    'storage': ('存储容量换算', 'Byte / KB / MB / GB / TB（二进制与十进制）', {
        'B (字节)': 1, 'KB (1000)': 1e3, 'MB (1000²)': 1e6, 'GB (1000³)': 1e9,
        'TB (1000⁴)': 1e12, 'KiB (1024)': 1024, 'MiB (1024²)': 1048576,
        'GiB (1024³)': 1073741824, 'TiB (1024⁴)': 1099511627776}, 'GB (1000³)'),
}

for tid, (name, desc, units, dflt) in CONVERTERS.items():
    keys = list(units.keys())
    opts = [{'value': k, 'label': k} for k in keys]
    js = CONVERTER_JS.replace('__UNITS__', json.dumps(opts, ensure_ascii=False))
    js = js.replace('__FROM__', json.dumps(dflt, ensure_ascii=False))
    js = js.replace('__TO__', json.dumps(keys[0], ensure_ascii=False))
    js = js.replace('__DATA__', json.dumps(units, ensure_ascii=False))
    d(tid, name, desc, js=js)

d('temp-converter', '温度单位换算', '摄氏 / 华氏 / 开氏 / 兰氏互转，附常识提示', js=TEMP_JS)

d('radix-convert', '进制转换', '2 / 8 / 10 / 16 及任意 2-36 进制互转，支持小数', js=r'''
var input = T.input('255', { class: 'grow mono' });
var from = T.num(10, { min: 2, max: 36, style: 'width:70px' });
var box = T.el('div');
function run() {
  var v = input.value.trim().toLowerCase().replace(/^0[xbo]/, '');
  var b = +from.value;
  T.clearEl(box);
  if (!v) return;
  var neg = v.startsWith('-');
  if (neg) v = v.slice(1);
  var parts = v.split('.');
  var intPart = parseInt(parts[0] || '0', b);
  if (isNaN(intPart)) { box.appendChild(T.msg('⚠ ' + b + ' 进制下存在非法字符', 'err')); return; }
  var frac = 0;
  if (parts[1]) {
    parts[1].split('').forEach(function (c) {
      frac += parseInt(c, b) / b;
    });
  }
  var val = (neg ? -1 : 1) * (intPart + frac);
  var toBase = function (num, base, prec) {
    if (num === 0) return '0';
    var digits = '0123456789abcdefghijklmnopqrstuvwxyz';
    var intP = Math.floor(num);
    var fracP = num - intP;
    var s = '';
    while (intP > 0) { s = digits[intP % base] + s; intP = Math.floor(intP / base); }
    if (fracP > 0 && prec !== 0) {
      s += '.';
      var n = 0;
      while (fracP > 0 && n < 12) { fracP *= base; s += digits[Math.floor(fracP)]; fracP -= Math.floor(fracP); n++; }
    }
    return s;
  };
  var rows = [];
  [2, 8, 10, 16].forEach(function (tb) {
    rows.push([tb + ' 进制', (neg ? '-' : '') + toBase(val, tb)]);
  });
  [3, 5, 12, 20, 32, 36].forEach(function (tb) { rows.push([tb + ' 进制', (neg ? '-' : '') + toBase(val, tb)]); });
  box.appendChild(T.kvTable(rows));
}
[input, from].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '数值' }), input, T.el('span', { text: '原进制' }), from]));
app.appendChild(box);
run();
''')

d('color-convert', '颜色转换', 'HEX / RGB / HSL / HSV / CMYK 互转 + 预览与取色器', js=r'''
var input = T.input('#1744E8', { class: 'grow mono' });
var picker = T.color('#1744E8');
var box = T.el('div', { class: 'pane single' });
var swatch = T.el('div', { style: 'height:80px;border-radius:10px;border:1px solid var(--line);margin:12px 0' });
function run() {
  var v = input.value.trim();
  T.clearEl(box);
  try {
    var c = LU.Color.parse(v);
    swatch.style.background = LU.Color.hex(c);
    var hsl = LU.Color.rgbToHsl(c.r, c.g, c.b);
    var hsv = LU.Color.rgbToHsv(c.r, c.g, c.b);
    var k = 1 - Math.max(c.r, c.g, c.b) / 255;
    var cmyk = k === 1 ? [0, 0, 0, 1] : [
      (255 - c.r - k * 255) / (255 - k * 255),
      (255 - c.g - k * 255) / (255 - k * 255),
      (255 - c.b - k * 255) / (255 - k * 255),
      k
    ];
    box.appendChild(T.kvTable([
      ['HEX', LU.Color.hex(c).toUpperCase()],
      ['RGB', 'rgb(' + c.r + ', ' + c.g + ', ' + c.b + ')'],
      ['HSL', 'hsl(' + Math.round(hsl.h) + ', ' + Math.round(hsl.s * 100) + '%, ' + Math.round(hsl.l * 100) + '%)'],
      ['HSV', 'hsv(' + Math.round(hsv.h) + ', ' + Math.round(hsv.s * 100) + '%, ' + Math.round(hsv.v * 100) + '%)'],
      ['CMYK', 'cmyk(' + cmyk.map(function (x) { return Math.round(x * 100) + '%'; }).join(', ') + ')'],
      ['亮度 Luminance', LU.Color.luminance(c).toFixed(4)]
    ]));
  } catch (e) {
    box.appendChild(T.msg('⚠ ' + e.message, 'err'));
  }
}
input.addEventListener('input', run);
picker.addEventListener('input', function () { input.value = picker.value; run(); });
app.appendChild(T.row([T.el('span', { text: '颜色值' }), input, picker]));
app.appendChild(swatch);
app.appendChild(box);
run();
''')

d('unit-convert', '单位换算器', '综合换算：长度 / 重量 / 面积 / 体积 / 温度 / 速度 / 数据 / 压力', js=r'''
var CATS = {
  '长度': { '毫米': 0.001, '厘米': 0.01, '米': 1, '千米': 1000, '英寸': 0.0254, '英尺': 0.3048, '英里': 1609.344 },
  '重量': { '克': 1, '千克': 1000, '吨': 1e6, '斤': 500, '磅': 453.59237, '盎司': 28.34952 },
  '面积': { '平方米': 1, '公顷': 10000, '平方公里': 1e6, '亩': 666.6667, '平方英尺': 0.092903 },
  '体积': { '毫升': 0.001, '升': 1, '立方米': 1000, '加仑(美)': 3.785412 },
  '速度': { '米/秒': 1, '千米/时': 3.6, '英里/时': 1.609344, '节': 1.852 },
  '数据': { 'B': 1, 'KB': 1024, 'MB': 1048576, 'GB': 1073741824, 'TB': 1099511627776 },
  '压力': { 'Pa': 1, 'kPa': 1e3, 'bar': 1e5, 'atm': 101325, 'psi': 6894.757 }
};
var cat = T.select(Object.keys(CATS).map(function (k) { return { value: k, label: k }; }), '长度');
var value = T.num(1, { style: 'width:120px' });
var from = T.select([], '米');
var to = T.select([], '千米');
var result = T.input('', { class: 'grow mono', readonly: '' });
var tempRow = T.el('div', { class: 'row' });
var tempIn = T.num(25, { style: 'width:90px' });
var tempSel = T.select([{value:'C',label:'°C'},{value:'F',label:'°F'},{value:'K',label:'K'}],'C');
var tempOut = T.input('', { class: 'grow mono', readonly: '' });
function fill() {
  var units = Object.keys(CATS[cat.value]);
  T.clearEl(from);
  T.clearEl(to);
  units.forEach(function (u) {
    from.appendChild(T.el('option', { value: u, text: u }));
    to.appendChild(T.el('option', { value: u, text: u }));
  });
  from.value = units[2] || units[0];
  to.value = units[3] || units[0];
  run();
}
function run() {
  if (cat.value === '温度') {
    var v = +tempIn.value, f = tempSel.value;
    var c = f === 'C' ? v : f === 'F' ? (v - 32) * 5 / 9 : v - 273.15;
    tempOut.value = '°C ' + c.toFixed(2) + ' · °F ' + (c * 9 / 5 + 32).toFixed(2) + ' · K ' + (c + 273.15).toFixed(2);
    return;
  }
  var U = CATS[cat.value];
  var v2 = +value.value;
  if (!U[from.value] || isNaN(v2)) { result.value = ''; return; }
  result.value = +(v2 * U[from.value] / U[to.value]).toPrecision(10) + ' ' + to.value;
}
cat.addEventListener('change', function () {
  tempRow.hidden = cat.value !== '温度';
  document.getElementById('conv-row').hidden = cat.value === '温度';
  if (cat.value === '温度') { run(); return; }
  fill();
});
[value, from, to].forEach(function (el) { el.addEventListener('input', run); });
[tempIn, tempSel].forEach(function (el) { el.addEventListener('input', run); });
var convRow = T.row([value, from, T.el('span', { text: '→' }), to, result]);
convRow.id = 'conv-row';
app.appendChild(T.row([T.el('span', { text: '类别' }), cat]));
app.appendChild(convRow);
tempRow.appendChild(T.el('span', { text: '温度' }));
tempRow.appendChild(tempIn);
tempRow.appendChild(tempSel);
tempRow.appendChild(tempOut);
tempRow.hidden = true;
app.appendChild(tempRow);
fill();
''')

d('chmod', 'Chmod 计算器', 'Linux 文件权限：数字 ↔ 符号（rwx 三组）互转', js=r'''
var GROUPS = [['所有者 user', 'u'], ['组 group', 'g'], ['其他 others', 'o']];
var checks = {};
var wrap = T.el('div');
var octOut = T.input('644', { class: 'mono', style: 'width:90px', readonly: '' });
var symOut = T.input('', { class: 'mono grow', readonly: '' });
GROUPS.forEach(function (g) {
  var row = T.row([T.el('span', { text: g[0], style: 'width:110px' })]);
  ['r(4) 读', 'w(2) 写', 'x(1) 执行'].forEach(function (label, i) {
    var c = T.check(label);
    var key = g[1] + i;
    checks[key] = c._input;
    if ((g[1] === 'u' && [true, true, false][i]) || (g[1] === 'g' && [true, false, false][i]) || (g[1] === 'o' && [true, false, false][i])) c._input.checked = true;
    c._input.addEventListener('change', calc);
    row.appendChild(c);
  });
  wrap.appendChild(row);
});
function calcFromChecks() {
  var oct = '', sym = '';
  ['u', 'g', 'o'].forEach(function (g) {
    var n = 0;
    var s = '';
    for (var i = 0; i < 3; i++) {
      if (checks[g + i].checked) { n += [4, 2, 1][i]; s += 'rwx'[i]; }
      else s += '-';
    }
    oct += n;
    sym += s;
  });
  octOut.value = oct;
  symOut.value = '-' + sym;
}
function calcFromOct() {
  var v = octOut.value.replace(/[^0-7]/g, '').slice(0, 3).padStart(3, '0');
  ['u', 'g', 'o'].forEach(function (g, gi) {
    var n = +v[gi];
    for (var i = 0; i < 3; i++) checks[g + i].checked = !!(n & [4, 2, 1][i]);
  });
  calcFromChecks();
}
var syncing = false;
function calc() { if (syncing) return; syncing = true; calcFromChecks(); syncing = false; }
octOut.readonly = '';
octOut.addEventListener('input', function () { syncing = true; calcFromOct(); syncing = false; });
calcFromOct();
app.appendChild(wrap);
app.appendChild(T.row([T.el('span', { text: '八进制' }), octOut, T.el('span', { text: '符号' }), symOut]));
app.appendChild(T.row([T.button('复制命令 chmod ' + octOut.value, function () { T.copy('chmod ' + octOut.value + ' file'); }),
  T.el('span', { text: '常见：755 目录/脚本 · 644 普通文件 · 600 私钥 · 777 全开放（慎用）' })]));
''')

d('calculator', '在线计算器', '科学计算器：四则 / 幂 / 开方 / 三角 / 对数，键盘可输入', js=r'''
var display = T.input('', { class: 'grow mono', placeholder: '输入表达式，如 (2+3)*4^2 - sqrt(16)' });
var result = T.stat('—', '');
var FN = { 'sin(': 'sin(', 'cos(': 'cos(', 'tan(': 'tan(', 'sqrt(': '√', 'log(': 'log', 'ln(': 'ln', 'abs(': 'abs(' };
var degMode = T.check('角度制（deg）', true);
var hist = [];
function calc() {
  var expr = display.value.trim();
  if (!expr) return;
  try {
    var sanitized = expr
      .replace(/×/g, '*').replace(/÷/g, '/').replace(/π/g, 'PI').replace(/√/g, 'sqrt')
      .replace(/\b(sin|cos|tan)\(/g, function (m, f) { return '_' + f + '('; })
      .replace(/\^/g, '**')
      .replace(/\b(sqrt|log10|log2|ln|abs|PI|E)\b/g, function (m) {
        return { 'ln': '(Math_log)', 'log': 'Math.log10', 'log2': 'Math.log2', 'PI': 'Math.PI', 'E': 'Math.E' }[m] || 'Math.' + m;
      })
      .replace(/Math_log/g, 'Math.log');
    if (!/^[0-9+\-*/%.()\s_Math.sqrtincoalgblPE10]*$/.test(sanitized)) throw new Error('含非法字符');
    var fn = new Function('Math', 'return ' + sanitized + ';');
    var wrapMath = Object.create(Math);
    var deg = degMode._input.checked;
    wrapMath.sin = function (x) { return Math.sin(deg ? x * Math.PI / 180 : x); };
    wrapMath.cos = function (x) { return Math.cos(deg ? x * Math.PI / 180 : x); };
    wrapMath.tan = function (x) { return Math.tan(deg ? x * Math.PI / 180 : x); };
    var val = fn(wrapMath);
    if (typeof val !== 'number' || isNaN(val)) throw new Error('无法计算');
    result.firstChild.textContent = String(+val.toPrecision(12));
    hist.unshift(expr + ' = ' + +val.toPrecision(12));
    if (hist.length > 10) hist.pop();
    histBox.value = hist.join('\n');
  } catch (e) {
    result.firstChild.textContent = '⚠ ' + e.message;
  }
}
var KEYS = [['7', '8', '9', '÷', '√'], ['4', '5', '6', '×', '^'], ['1', '2', '3', '-', 'π'], ['0', '.', '(', ')', '+']];
var pad = T.el('div', { style: 'display:grid;grid-template-columns:repeat(5,64px);gap:8px;margin:14px 0' });
KEYS.forEach(function (rowKeys) {
  rowKeys.forEach(function (k) {
    var b = T.button(k, function () { display.value += k; });
    b.style.justifyContent = 'center';
    pad.appendChild(b);
  });
});
var cRow = T.el('div', { style: 'display:grid;grid-template-columns:repeat(5,64px);gap:8px;margin-bottom:8px' });
['sin(', 'cos(', 'tan(', 'ln(', 'log('].forEach(function (k) {
  var b = T.button(k.replace('(', ''), function () { display.value += k + (k === 'sin(' || k === 'cos(' || k === 'tan(' ? '' : '('); });
  b.style.justifyContent = 'center';
  cRow.appendChild(b);
});
var histBox = T.out('计算历史…');
histBox.style.minHeight = '80px';
app.appendChild(T.row([display, T.button('计算 ⏎', calc, true), result]));
app.appendChild(T.row([degMode, T.button('清空', function () { display.value = ''; result.firstChild.textContent = '—'; }),
  T.button('退格', function () { display.value = display.value.slice(0, -1); })]));
app.appendChild(cRow);
app.appendChild(pad);
app.appendChild(histBox);
display.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); calc(); } });
display.value = '(2+3)*4^2 - sqrt(16)';
calc();
''')

d('ieee754', 'IEEE 754 转换', '浮点数 ↔ 32 / 64 位二进制表示（符号 / 指数 / 尾数）', js=r'''
var input = T.num(3.1415926, { step: 'any', style: 'width:180px' });
var bitsSel = T.select([{value:'32',label:'32 位 (float)'},{value:'64',label:'64 位 (double)'}],'64');
var box = T.el('div');
function run() {
  var v = +input.value;
  T.clearEl(box);
  if (isNaN(v)) return;
  var buf = new ArrayBuffer(8);
  var dv = new DataView(buf);
  var bits, expBits, manBits;
  if (bitsSel.value === '32') {
    dv.setFloat32(0, v);
    bits = 32; expBits = 8; manBits = 23;
  } else {
    dv.setFloat64(0, v);
    bits = 64; expBits = 11; manBits = 52;
  }
  var bin = '';
  for (var i = 0; i < bits / 8; i++) bin += dv.getUint8(i).toString(2).padStart(8, '0');
  var sign = bin[0];
  var exp = bin.slice(1, 1 + expBits);
  var man = bin.slice(1 + expBits);
  var hex = T.bytesToHex(new Uint8Array(buf).slice(0, bits / 8));
  box.appendChild(T.el('div', { class: 'output', style: 'white-space:pre' }));
  box.firstChild.textContent =
    '符号 (1 bit)   : ' + sign + (sign === '1' ? '  负' : '  正') + '\n' +
    '指数 (' + expBits + ' bits): ' + exp + '  = ' + parseInt(exp, 2) + ' (偏移 ' + (Math.pow(2, expBits - 1) - 1) + ')\n' +
    '尾数 (' + manBits + ' bits): ' + man + '\n' +
    '二进制完整     : ' + bin + '\n' +
    '十六进制       : ' + hex;
  box.appendChild(T.kvTable([
    ['十进制值', v], ['Hex', '0x' + hex.toUpperCase()],
    ['还原验证', bitsSel.value === '32' ? dv.getFloat32(0) : dv.getFloat64(0)]
  ]));
}
[input, bitsSel].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '数值' }), input, T.el('span', { text: '精度' }), bitsSel]));
app.appendChild(box);
run();
''')

d('endian', '大小端转换', 'Big / Little Endian 字节序互换：16 / 32 / 64 位十六进制', js=r'''
var input = T.input('DEADBEEF', { class: 'grow mono', placeholder: '十六进制字节串' });
var width = T.select([{value:'2',label:'16 位 (2字节)'},{value:'4',label:'32 位 (4字节)'},{value:'8',label:'64 位 (8字节)'}],'4');
var box = T.el('div');
function swap(hex, w) {
  if (hex.length % (w * 2) !== 0) throw new Error('长度需为 ' + (w * 2) + ' 的倍数（当前 ' + hex.length + '）');
  var out = '';
  for (var i = 0; i < hex.length; i += w * 2) {
    var word = hex.slice(i, i + w * 2);
    for (var j = word.length; j > 0; j -= 2) out += word.slice(j - 2, j);
  }
  return out;
}
function run() {
  var v = input.value.replace(/[^0-9a-fA-F]/g, '');
  T.clearEl(box);
  if (!v) return;
  try {
    var w = +width.value;
    box.appendChild(T.kvTable([
      ['原始 (Big Endian)', v.toUpperCase()],
      ['交换后 (Little Endian)', swap(v, w).toUpperCase()],
      ['按 ' + (w * 8) + ' 位分组', v.toUpperCase().match(new RegExp('.{1,' + (w * 2) + '}', 'g')).join(' ')]
    ]));
  } catch (e) {
    box.appendChild(T.msg('⚠ ' + e.message, 'err'));
  }
}
[input, width].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: 'HEX' }), input, T.el('span', { text: '字长' }), width]));
app.appendChild(box);
run();
''')

d('color-shades', '色阶生成器', '颜色深浅渐变序列（Tints & Shades），10 级可复制', js=r'''
var color = T.color('#1744E8');
var steps = T.num(10, { min: 3, max: 20, style: 'width:70px' });
var box = T.el('div');
var strip = T.el('div', { style: 'display:flex;gap:4px;height:70px;margin:12px 0;border-radius:10px;overflow:hidden' });
function run() {
  var rgb = LU.Color.parse(color.value);
  var hsl = LU.Color.rgbToHsl(rgb.r, rgb.g, rgb.b);
  var n = +steps.value || 10;
  T.clearEl(strip);
  var rows = [];
  for (var i = 0; i < n; i++) {
    var t = i / (n - 1);
    var l = t < 0.5 ? hsl.l + (1 - hsl.l) * (0.5 - t) * 2 : hsl.l - hsl.l * (t - 0.5) * 2;
    var c = LU.Color.hex(LU.Color.hslToRgb(hsl.h / 360, hsl.s, Math.max(0, Math.min(1, l))));
    var d = T.el('div', { style: 'flex:1;background:' + c + ';cursor:pointer;position:relative', title: c + '（点击复制）' });
    var idx = Math.round(t * 100);
    d.setAttribute('data-label', idx + '%');
    d.addEventListener('click', function () { T.copy(this.title.split('（')[0]); });
    strip.appendChild(d);
    rows.push([idx + '%', c]);
  }
  T.clearEl(box).appendChild(T.refTable(['深浅', 'HEX'], rows));
}
[color, steps].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '基准色' }), color, T.el('span', { text: '级数' }), steps]));
app.appendChild(strip);
app.appendChild(box);
run();
''')

d('trig', '三角函数计算', 'sin / cos / tan / asin / acos / atan，角度弧度切换', js=r'''
var input = T.num(30, { step: 'any', style: 'width:140px' });
var mode = T.select([{value:'deg',label:'角度制 °'},{value:'rad',label:'弧度制 rad'}],'deg');
var box = T.el('div');
function toRad(v) { return mode.value === 'deg' ? v * Math.PI / 180 : v; }
function fmt(x) { return Math.abs(x) < 1e-12 ? '0' : +x.toPrecision(10); }
function run() {
  var v = +input.value;
  if (isNaN(v)) { T.clearEl(box); return; }
  var r = toRad(v);
  var rows = [
    ['sin', fmt(Math.sin(r))], ['cos', fmt(Math.cos(r))],
    ['tan', Math.abs(Math.cos(r)) < 1e-12 ? '∞ (undefined)' : fmt(Math.tan(r))],
    ['csc', fmt(1 / Math.sin(r))], ['sec', fmt(1 / Math.cos(r))],
    ['cot', Math.abs(Math.sin(r)) < 1e-12 ? '∞' : fmt(1 / Math.tan(r))]
  ];
  T.clearEl(box).appendChild(T.kvTable(rows));
  var inv = [];
  if (v >= -1 && v <= 1) {
    inv.push(['asin', fmt(mode.value === 'deg' ? Math.asin(v) * 180 / Math.PI : Math.asin(v))]);
    inv.push(['acos', fmt(mode.value === 'deg' ? Math.acos(v) * 180 / Math.PI : Math.acos(v))]);
  }
  inv.push(['atan', fmt(mode.value === 'deg' ? Math.atan(v) * 180 / Math.PI : Math.atan(v))]);
  box.appendChild(T.el('span', { text: '反三角（输入作为比值，仅当 |x|≤1 时 asin/acos 有效）', class: 'field' }));
  box.appendChild(T.kvTable(inv));
}
[input, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '输入' }), input, mode]));
app.appendChild(box);
run();
''')

d('bit-reverse', '二进制位操作', '按位翻转 / 左移右移 / 位反转，8 / 16 / 32 位', js=r'''
var input = T.input('0xFF00', { class: 'grow mono', placeholder: '数值（支持 0x 前缀 / 十进制 / 0b 二进制）' });
var width = T.select([{value:'8',label:'8 位'},{value:'16',label:'16 位'},{value:'32',label:'32 位'}],'16');
var shift = T.num(4, { min: 0, max: 31, style: 'width:70px' });
var box = T.el('div');
function parseVal(s) {
  s = s.trim().toLowerCase();
  if (s.startsWith('0x')) return parseInt(s.slice(2), 16);
  if (s.startsWith('0b')) return parseInt(s.slice(2), 2);
  return parseInt(s, 10);
}
function toBin(v, w) {
  var mask = typeof v === 'bigint' ? (1n << BigInt(w)) - 1n : (w === 32 ? 0xFFFFFFFF : (1 << w) - 1);
  v = v & mask;
  var s = v.toString(2);
  while (s.length < w) s = '0' + s;
  return s;
}
function run() {
  var v = parseVal(input.value);
  T.clearEl(box);
  if (isNaN(v)) { box.appendChild(T.msg('⚠ 无法解析数值', 'err')); return; }
  var w = +width.value;
  var bin = toBin(v, w);
  var reversed = bin.split('').reverse().join('');
  var sh = +shift.value || 0;
  var mask = w === 32 ? 0xFFFFFFFF : (1 << w) - 1;
  var shl = (v << sh) & mask;
  var shr = (v >>> sh) & mask;
  box.appendChild(T.kvTable([
    ['原始', bin + '  (0x' + (v >>> 0).toString(16).toUpperCase() + ')'],
    ['按位翻转 NOT', toBin(~v, w) + '  (0x' + ((~v >>> 0) & mask).toString(16).toUpperCase() + ')'],
    ['位序反转 reverse', reversed + '  (0x' + (parseInt(reversed, 2) >>> 0).toString(16).toUpperCase() + ')'],
    ['左移 ' + sh + ' 位 <<', toBin(shl, w) + '  (0x' + (shl >>> 0).toString(16).toUpperCase() + ')'],
    ['右移 ' + sh + ' 位 >>>', toBin(shr, w) + '  (0x' + (shr >>> 0).toString(16).toUpperCase() + ')'],
    ['字节序交换', w >= 16 ? toBin(((v & 0xFF) << 8 | (v >> 8) & 0xFF) & mask, w) + (w === 32 ? '  （低16位演示）' : '') : '（8 位无字节序）']
  ]));
}
[input, width, shift].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '数值' }), input, T.el('span', { text: '位宽' }), width, T.el('span', { text: '移位' }), shift]));
app.appendChild(box);
run();
''')

d('loan', '贷款计算器', '等额本息 / 等额本金月供与总利息对比，含还款明细', js=r'''
var amount = T.num(1000000, { min: 1000, step: 10000, style: 'width:130px' });
var years = T.num(30, { min: 1, max: 50, style: 'width:80px' });
var rate = T.num(3.6, { step: 0.01, style: 'width:90px' });
var mode = T.select([{value:'bx',label:'等额本息'},{value:'bj',label:'等额本金'}],'bx');
var box = T.el('div');
function run() {
  var P = +amount.value, n = +years.value * 12, r = +rate.value / 100 / 12;
  T.clearEl(box);
  if (!P || !n) return;
  if (mode.value === 'bx') {
    var m = r === 0 ? P / n : P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
    var total = m * n;
    box.appendChild(T.kvTable([
      ['月供（固定）', m.toFixed(2) + ' 元'],
      ['还款总额', total.toFixed(2) + ' 元'],
      ['支付利息', (total - P).toFixed(2) + ' 元'],
      ['利息占比', ((total - P) / total * 100).toFixed(1) + '%']
    ]));
  } else {
    var first = P / n + P * r;
    var last = P / n + (P - P / n * (n - 1)) * r;
    var totalI = (n + 1) * P * r / 2;
    box.appendChild(T.kvTable([
      ['首月月供', first.toFixed(2) + ' 元'],
      ['末月月供', last.toFixed(2) + ' 元'],
      ['每月递减', (P * r / n).toFixed(2) + ' 元'],
      ['还款总额', (P + totalI).toFixed(2) + ' 元'],
      ['支付利息', totalI.toFixed(2) + ' 元']
    ]));
  }
}
[amount, years, rate, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('贷款总额（元）', amount), T.field('贷款年限', years)]));
app.appendChild(T.row([T.el('span', { text: '年利率 %' }), rate, mode]));
app.appendChild(box);
run();
''')

d('bmi', 'BMI 计算器', '身体质量指数：BMI 值 + 中国 / WHO 标准分级', js=r'''
var h = T.num(170, { min: 50, max: 250, style: 'width:110px' });
var w = T.num(65, { min: 10, max: 400, step: 0.1, style: 'width:110px' });
var std = T.select([{value:'cn',label:'中国标准'},{value:'who',label:'WHO 标准'}],'cn');
var big = T.stat('—', 'BMI');
var box = T.el('div');
function run() {
  var height = +h.value / 100, weight = +w.value;
  T.clearEl(box);
  if (!height || !weight) return;
  var bmi = weight / (height * height);
  big.firstChild.textContent = bmi.toFixed(1);
  var levels = std.value === 'cn'
    ? [[18.5, '偏瘦', 'ok'], [24, '正常', 'ok'], [28, '超重', 'warn'], [Infinity, '肥胖', 'warn']]
    : [[18.5, '偏瘦 Underweight', 'ok'], [25, '正常 Normal', 'ok'], [30, '超重 Overweight', 'warn'], [Infinity, '肥胖 Obese', 'warn']];
  var cur = levels[0];
  for (var i = 0; i < levels.length; i++) {
    if (bmi < levels[i][0]) { cur = levels[i]; break; }
  }
  var ideal1 = 18.5 * height * height, ideal2 = (std.value === 'cn' ? 23.9 : 24.9) * height * height;
  box.appendChild(T.kvTable([
    ['分级', cur[1]],
    ['健康体重范围', (ideal1).toFixed(1) + ' ~ ' + (ideal2).toFixed(1) + ' kg'],
    ['理想体重', ((ideal1 + ideal2) / 2).toFixed(1) + ' kg'],
    ['距离健康范围', weight < ideal1 ? '还需增重 ' + (ideal1 - weight).toFixed(1) + ' kg' : weight > ideal2 ? '还需减重 ' + (weight - ideal2).toFixed(1) + ' kg' : '✓ 处于健康区间']
  ]));
}
[h, w, std].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('身高 (cm)', h), T.field('体重 (kg)', w)]));
app.appendChild(T.row([big, std]));
app.appendChild(box);
run();
''')

d('calorie', '卡路里计算器', '基础代谢 BMR（Mifflin-St Jeor）+ 活动系数 → 每日消耗 TDEE', js=r'''
var gender = T.select([{value:'m',label:'男'},{value:'f',label:'女'}],'m');
var age = T.num(28, { min: 10, max: 100, style: 'width:80px' });
var h = T.num(170, { style: 'width:90px' });
var w = T.num(65, { step: 0.1, style: 'width:90px' });
var act = T.select([
  { value: '1.2', label: '久坐不动' },
  { value: '1.375', label: '轻度活动（每周1-3次）' },
  { value: '1.55', label: '中度活动（每周3-5次）' },
  { value: '1.725', label: '高度活动（每周6-7次）' },
  { value: '1.9', label: '极高强度（体力劳动）' }
], '1.375');
var box = T.el('div');
function run() {
  var g = gender.value, a = +age.value, hh = +h.value, ww = +w.value;
  T.clearEl(box);
  if (!a || !hh || !ww) return;
  var bmr = 10 * ww + 6.25 * hh - 5 * a + (g === 'm' ? 5 : -161);
  var tdee = bmr * +act.value;
  box.appendChild(T.kvTable([
    ['基础代谢 BMR', Math.round(bmr) + ' kcal/天'],
    ['每日总消耗 TDEE', Math.round(tdee) + ' kcal/天'],
    ['减重建议摄入', Math.round(tdee - 500) + ' kcal/天（约每周减 0.45kg）'],
    ['增重建议摄入', Math.round(tdee + 300) + ' kcal/天'],
    ['维持体重', Math.round(tdee) + ' kcal/天'],
    ['蛋白质建议', Math.round(ww * 1.5) + ' ~ ' + Math.round(ww * 2) + ' g/天']
  ]));
}
[gender, age, h, w, act].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('性别', gender), T.field('年龄', age)]));
app.appendChild(T.pane([T.field('身高 (cm)', h), T.field('体重 (kg)', w)]));
app.appendChild(T.row([T.el('span', { text: '活动量' }), act]));
app.appendChild(box);
run();
''')

d('retirement', '退休年龄计算', '按渐进式延迟退休政策估算退休日期（仅供参考，以官方公告为准）', js=r'''
var birth = T.dateInput('1990-06-15');
var gender = T.select([{value:'m',label:'男职工'},{value:'f-cadre',label:'女干部（原55岁）'},{value:'f-worker',label:'女职工（原50岁）'}],'m');
var box = T.el('div');
var NOTE = '自 2025-01-01 起施行渐进式延迟：男职工与女干部每 4 个月延迟 1 个月，女职工每 2 个月延迟 1 个月；上限分别为 63 / 58 / 55 岁。';
function baseAge(g) { return g === 'm' ? 60 : g === 'f-cadre' ? 55 : 50; }
function capAge(g) { return g === 'm' ? 63 : g === 'f-cadre' ? 58 : 55; }
function stepMonths(g) { return g === 'f-worker' ? 2 : 4; }
function run() {
  T.clearEl(box);
  if (!birth.value) return;
  var b = new Date(birth.value + 'T00:00:00');
  var g = gender.value;
  var start = new Date(2025, 0, 1);
  var orig = new Date(b.getFullYear() + baseAge(g), b.getMonth(), b.getDate());
  var delay = 0;
  if (orig >= start) {
    var monthsFromStart = (orig.getFullYear() - 2025) * 12 + orig.getMonth();
    var steps = Math.floor(monthsFromStart / stepMonths(g)) + 1;
    delay = Math.min(steps, (capAge(g) - baseAge(g)) * 12);
  }
  var retire = new Date(b.getFullYear() + baseAge(g), b.getMonth() + delay, b.getDate());
  var ageY = baseAge(g) + Math.floor(delay / 12);
  var ageM = delay % 12;
  var totalDays = Math.max(0, Math.round((retire - new Date()) / 86400000));
  box.appendChild(T.kvTable([
    ['退休年龄', ageY + ' 岁 ' + (ageM ? ageM + ' 个月' : '')],
    ['法定退休日期', retire.toLocaleDateString('zh-CN') + '（' + ['日', '一', '二', '三', '四', '五', '六'][retire.getDay()] + '）'],
    ['相对原政策延迟', delay + ' 个月'],
    ['距离退休', totalDays === 0 ? '已到退休年龄' : '约 ' + (totalDays / 365.25).toFixed(1) + ' 年（' + totalDays.toLocaleString() + ' 天）']
  ]));
  box.appendChild(T.msg(NOTE, ''));
}
[birth, gender].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('出生日期', birth), T.field('类别', gender)]));
app.appendChild(box);
run();
''')

d('compound', '复利计算器', '复利 / 定投收益计算：本金 + 月投 + 年利率 + 年数', js=r'''
var principal = T.num(100000, { min: 0, step: 1000, style: 'width:120px' });
var monthly = T.num(1000, { min: 0, step: 100, style: 'width:100px' });
var rate = T.num(5, { step: 0.1, style: 'width:80px' });
var years = T.num(10, { min: 1, max: 60, style: 'width:80px' });
var box = T.el('div');
var table = T.el('div');
function run() {
  var P = +principal.value, m = +monthly.value, r = +rate.value / 100, y = +years.value;
  T.clearEl(box);
  T.clearEl(table);
  if (!y) return;
  var mr = r / 12;
  var rows = [];
  for (var yy = 1; yy <= y; yy++) {
    var months = yy * 12;
    var pv = P * Math.pow(1 + mr, months);
    var fvM = mr === 0 ? m * months : m * (Math.pow(1 + mr, months) - 1) / mr;
    var total = pv + fvM;
    var invested = P + m * months;
    rows.push([yy + ' 年', invested.toFixed(0), total.toFixed(0), '+' + (total - invested).toFixed(0)]);
  }
  var last = rows[rows.length - 1];
  box.appendChild(T.kvTable([
    ['总投入', '¥ ' + (+last[1]).toLocaleString()],
    ['期末资产', '¥ ' + (+last[2]).toLocaleString()],
    ['累计收益', '¥ ' + (+last[3].replace('+', '')).toLocaleString()],
    ['收益率', ((last[2] / last[1] - 1) * 100).toFixed(1) + '%']
  ]));
  table.appendChild(T.refTable(['年份', '总投入', '期末资产', '累计收益'], rows.map(function (r2) {
    return [r2[0], (+r2[1]).toLocaleString(), (+r2[2]).toLocaleString(), r2[3]];
  })));
}
[principal, monthly, rate, years].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('初始本金（元）', principal), T.field('每月定投（元）', monthly)]));
app.appendChild(T.pane([T.field('年利率 %', rate), T.field('投资年限', years)]));
app.appendChild(box);
app.appendChild(table);
run();
''')

d('tip', '小费计算器', '账单 + 小费比例 + 人数分摊，人均应付一目了然', js=r'''
var bill = T.num(288, { min: 0, step: 1, style: 'width:120px' });
var tip = T.range(0, 30, 1, 15);
var tipLabel = T.el('b', { text: '15%' });
var people = T.num(2, { min: 1, max: 50, style: 'width:70px' });
var box = T.el('div');
function run() {
  tipLabel.textContent = tip.value + '%';
  var b = +bill.value || 0, p = Math.max(1, +people.value || 1);
  var tipAmt = b * +tip.value / 100;
  var total = b + tipAmt;
  box.appendChild(T.kvTable([
    ['小费金额', '¥ ' + tipAmt.toFixed(2)],
    ['应付总额', '¥ ' + total.toFixed(2)],
    ['人均（' + p + ' 人）', '¥ ' + (total / p).toFixed(2)],
    ['人均小费', '¥ ' + (tipAmt / p).toFixed(2)]
  ]));
}
[bill, people].forEach(function (el) { el.addEventListener('input', run); });
tip.addEventListener('input', run);
app.appendChild(T.pane([T.field('账单金额（元）', bill), T.field('人数', people)]));
app.appendChild(T.row([T.el('span', { text: '小费比例' }), tip, tipLabel]));
app.appendChild(box);
run();
''')

d('aspect-ratio', '宽高比计算', '图片 / 视频宽高比：求最简比 + 等比缩放尺寸', js=r'''
var w = T.num(1920, { min: 1, style: 'width:100px' });
var h = T.num(1080, { min: 1, style: 'width:100px' });
var newW = T.num(1280, { min: 1, style: 'width:100px' });
var box = T.el('div');
function run() {
  var W = +w.value, H = +h.value;
  T.clearEl(box);
  if (!W || !H) return;
  var g = T.gcd(W, H);
  var rw = W / g, rh = H / g;
  var nw = +newW.value || 0;
  var nh = nw ? Math.round(nw * H / W) : 0;
  box.appendChild(T.kvTable([
    ['宽高比', rw + ' : ' + rh + (rw / rh === 16 / 9 ? '  (16:9)' : rw / rh === 4 / 3 ? '  (4:3)' : rw === rh ? '  (1:1)' : '')],
    ['小数比', (W / H).toFixed(4) + ' : 1'],
    ['角度', Math.atan2(H, W) * 180 / Math.PI < 45 ? '横向 landscape' : Math.atan2(H, W) * 180 / Math.PI > 45 ? '纵向 portrait' : '正方 square'],
    nw ? ['等比缩放到宽 ' + nw, nw + ' × ' + nh] : ['填入目标宽度', '在左侧输入等比缩放的目标宽度']
  ]));
}
[w, h, newW].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('原始宽', w), T.field('原始高', h)]));
app.appendChild(T.row([T.el('span', { text: '目标宽（等比缩放）' }), newW]));
app.appendChild(box);
run();
''')

d('pixel-density', '像素密度计算', '屏幕分辨率 + 对角线英寸 → PPI / 点距 / 宽高', js=r'''
var w = T.num(2560, { min: 1, style: 'width:100px' });
var h = T.num(1440, { min: 1, style: 'width:100px' });
var diag = T.num(27, { step: 0.1, style: 'width:90px' });
var box = T.el('div');
function run() {
  var W = +w.value, H = +h.value, D = +diag.value;
  T.clearEl(box);
  if (!W || !H || !D) return;
  var dp = Math.sqrt(W * W + H * H);
  var ppi = dp / D;
  box.appendChild(T.kvTable([
    ['对角线像素', Math.round(dp).toLocaleString() + ' px'],
    ['PPI（像素/英寸）', ppi.toFixed(2)],
    ['点距 Dot Pitch', (25.4 / ppi).toFixed(4) + ' mm'],
    ['物理尺寸', (W / ppi * 2.54).toFixed(1) + ' × ' + (H / ppi * 2.54).toFixed(1) + ' cm'],
    ['总像素', (W * H / 1e6).toFixed(2) + ' MP'],
    ['Retina（≥300 PPI）', ppi >= 300 ? '✓ 达标' : '✗ 未达标（' + ppi.toFixed(0) + ' PPI）']
  ]));
}
[w, h, diag].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('宽度 px', w), T.field('高度 px', h)]));
app.appendChild(T.row([T.el('span', { text: '对角线（英寸）' }), diag]));
app.appendChild(box);
run();
''')

d('data-transfer', '数据传输计算', '文件大小 + 带宽 → 下载 / 上传时间估算', js=r'''
var size = T.num(10, { step: 'any', style: 'width:110px' });
var sizeUnit = T.select([{value:'1',label:'MB'},{value:'1024',label:'GB'},{value:'0.001',label:'KB'},{value:'1e-6',label:'B'}],'1024');
var speed = T.num(100, { step: 'any', style: 'width:110px' });
var speedUnit = T.select([{value:'1',label:'Mbps'},{value:'1000',label:'Gbps'},{value:'0.125',label:'MB/s（字节）'}],'1');
var box = T.el('div');
function fmtTime(s) {
  if (s < 1) return (s * 1000).toFixed(0) + ' 毫秒';
  if (s < 60) return s.toFixed(1) + ' 秒';
  if (s < 3600) return Math.floor(s / 60) + ' 分 ' + Math.round(s % 60) + ' 秒';
  if (s < 86400) return Math.floor(s / 3600) + ' 小时 ' + Math.round(s % 3600 / 60) + ' 分';
  return (s / 86400).toFixed(1) + ' 天';
}
function run() {
  var s = +size.value * +sizeUnit.value * 8;
  var v = +speed.value * +speedUnit.value;
  T.clearEl(box);
  if (!s || !v) return;
  var sec = s / v;
  box.appendChild(T.kvTable([
    ['文件大小', (+size.value) + ' ' + sizeUnit.selectedOptions[0].text + ' = ' + (s / 8).toFixed(2) + ' MB'],
    ['带宽', (+speed.value) + ' ' + speedUnit.selectedOptions[0].text + ' = ' + (v / 8).toFixed(2) + ' MB/s'],
    ['理论耗时', fmtTime(sec)],
    ['实际估算（80% 效率）', fmtTime(sec / 0.8)],
    ['每小时可传', ((v / 8) * 3600).toFixed(1) + ' MB ≈ ' + ((v / 8) * 3600 / 1024).toFixed(2) + ' GB']
  ]));
}
[size, sizeUnit, speed, speedUnit].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('文件大小', size), T.field('', sizeUnit)]));
app.appendChild(T.pane([T.field('带宽', speed), T.field('', speedUnit)]));
app.appendChild(box);
run();
''')
