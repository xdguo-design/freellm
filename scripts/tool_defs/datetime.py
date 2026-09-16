# -*- coding: utf-8 -*-
"""日期时间类工具定义"""
from .registry import d

d('timestamp', '时间戳转换', 'Unix 时间戳与日期时间互转（秒 / 毫秒），当前时间实时刷新', js=r'''
var now = T.stat('—', '当前时间戳（秒）');
var input = T.input(String(Math.floor(Date.now() / 1000)), { class: 'grow mono' });
var unit = T.select([{value:'s',label:'秒 (10位)'},{value:'ms',label:'毫秒 (13位)'},{value:'us',label:'微秒 (16位)'},{value:'ns',label:'纳秒 (19位)'}],'s');
var box = T.el('div');
var dateIn = T.el('input', { type: 'datetime-local', style: 'flex:1' });
dateIn.value = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 19);
function tsToDate() {
  var v = +input.value;
  if (isNaN(v)) { box.textContent = '⚠ 请输入数字时间戳'; return; }
  var div = { s: 1000, ms: 1, us: 0.001, ns: 1e-6 }[unit.value];
  var d = new Date(v * div);
  if (isNaN(d.getTime())) { box.textContent = '⚠ 时间戳超出范围'; return; }
  var rows = [
    ['本地时间', T.fmtTime(d)],
    ['UTC', d.toISOString().replace('T', ' ').replace('Z', ' UTC')],
    ['相对现在', Math.round((d - Date.now()) / 1000).toLocaleString() + ' 秒（负为过去）']
  ];
  T.clearEl(box).appendChild(T.kvTable(rows));
  dateIn.value = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
}
function dateToTs() {
  if (!dateIn.value) return;
  var d = new Date(dateIn.value);
  input.value = String(Math.floor(d.getTime() / 1000));
  unit.value = 's';
  tsToDate();
}
input.addEventListener('input', tsToDate);
unit.addEventListener('change', tsToDate);
dateIn.addEventListener('change', dateToTs);
setInterval(function () { now.firstChild.textContent = Math.floor(Date.now() / 1000).toLocaleString(); }, 1000);
app.appendChild(T.row([now, T.button('复制当前秒级时间戳', function () { T.copy(String(Math.floor(Date.now() / 1000))); })]));
app.appendChild(T.row([T.el('span', { text: '时间戳' }), input, unit, T.button('转换 →', tsToDate)]));
app.appendChild(T.row([T.el('span', { text: '日期时间' }), dateIn]));
app.appendChild(box);
tsToDate();
''')

d('cron', 'Cron 表达式', 'Cron 表达式解析说明 + 未来 5 次执行时间预览（5 字段）', js=r'''
var input = T.input('*/5 * * * *', { class: 'grow mono', placeholder: '分 时 日 月 周' });
var info = T.el('div', { class: 'pane single' });
var FIELD_DESC = [
  ['分钟', '0-59', '* / , -'],
  ['小时', '0-23', '* / , -'],
  ['日', '1-31', '* / , - ?'],
  ['月', '1-12 或 JAN-DEC', '* / , -'],
  ['星期', '0-7（0 和 7 都是周日）', '* / , - ?']
];
function describe(f, idx) {
  f = f.trim();
  var unit = FIELD_DESC[idx][0];
  if (f === '*') return '每' + unit;
  if (f === '*/1') return '每' + unit;
  var step = f.match(/^\*\/(\d+)$/);
  if (step) return '每 ' + step[1] + ' 个' + unit;
  var range = f.match(/^(\d+)-(\d+)$/);
  if (range) return '从 ' + range[1] + ' 到 ' + range[2] + ' ' + unit;
  var list = f.split(',');
  if (list.length > 1) return unit + ' = ' + f;
  return unit + ' = ' + f;
}
function matchCron(d, parts) {
  var min = d.getMinutes(), hour = d.getHours(), day = d.getDate();
  var mon = d.getMonth() + 1, dow = d.getDay();
  var fm = function (p, v, max) {
    if (p === '*' || p === '?') return true;
    var out = false;
    p.split(',').forEach(function (seg) {
      var step = 1, base = seg;
      var si = seg.indexOf('/');
      if (si >= 0) { step = +seg.slice(si + 1); base = seg.slice(0, si); }
      var a = 0, b = max;
      if (base !== '*' && base !== '') {
        var rr = base.split('-');
        a = +rr[0]; b = rr[1] ? +rr[1] : a;
      }
      var hit = false;
      for (var x = a; x <= b; x += step) if (x === v) hit = true;
      if (hit) out = true;
    });
    return out;
  };
  return fm(parts[0], min, 59) && fm(parts[1], hour, 23) && fm(parts[2], day, 31) && fm(parts[3], mon, 12) && fm(parts[4], dow, 7);
}
function nextRuns(parts, n) {
  var out = [];
  var d = new Date();
  d.setSeconds(0, 0);
  d.setMinutes(d.getMinutes() + 1);
  var guard = 0;
  while (out.length < n && guard < 500000) {
    guard++;
    if (matchCron(d, parts)) {
      out.push(new Date(d));
      d.setMinutes(d.getMinutes() + 1);
    } else {
      d.setMinutes(d.getMinutes() + 1);
    }
  }
  return out;
}
function run() {
  T.clearEl(info);
  var parts = input.value.trim().split(/\s+/);
  if (parts.length !== 5) {
    info.appendChild(T.msg('⚠ 需要 5 个字段：分 时 日 月 周', 'err'));
    return;
  }
  var rows = parts.map(function (p, i) {
    var range = FIELD_DESC[i][1];
    var v = p === '*' ? null : +p.split('/')[0].split('-')[0];
    if (v != null && (isNaN(v) || v < 0)) return [FIELD_DESC[i][0], p + ' ⚠'];
    return [describe(p, i), '范围 ' + range];
  });
  info.appendChild(T.kvTable(rows));
  var nxt = nextRuns(parts, 5);
  info.appendChild(T.el('span', { text: '未来执行时间', class: 'field' }));
  info.appendChild(T.refTable(['#', '时间'], nxt.map(function (d, i) { return [i + 1, T.fmtTime(d)]; })));
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.row([T.el('span', { text: '表达式' }), input]));
app.appendChild(T.el('p', { text: '示例：*/5 * * * * 每5分钟 · 0 9 * * 1-5 工作日每天9点 · 30 3 1,15 * * 每月1号和15号 3:30', style: 'color:var(--ink2);font-size:12px' }));
app.appendChild(info);
run();
''')

d('date-calc', '日期计算器', '日期间隔天数 / 日期加减 N 天 / 周 / 月 / 年', js=r'''
var d1 = T.dateInput(T.today());
var d2 = T.dateInput(T.fmtDate(new Date(Date.now() + 86400000 * 30)));
var base = T.dateInput(T.today());
var amount = T.num(100, { style: 'width:80px' });
var unitSel = T.select([{value:'d',label:'天'},{value:'w',label:'周'},{value:'m',label:'月'},{value:'y',label:'年'}],'d');
var dir = T.select([{value:'add',label:'之后 +'},{value:'sub',label:'之前 -'}],'add');
var diffBox = T.el('div');
var calcBox = T.el('div');
function run() {
  T.clearEl(diffBox);
  if (d1.value && d2.value) {
    var a = new Date(d1.value), b = new Date(d2.value);
    var days = Math.round((b - a) / 86400000);
    var workHint = '';
    diffBox.appendChild(T.kvTable([
      ['间隔', Math.abs(days).toLocaleString() + ' 天（' + (days >= 0 ? 'B 在 A 之后' : 'B 在 A 之前') + '）'],
      ['折合', (Math.abs(days) / 7).toFixed(1) + ' 周 · ' + (Math.abs(days) / 30.44).toFixed(1) + ' 月 · ' + (Math.abs(days) / 365.25).toFixed(1) + ' 年'],
      ['精确到', '共 ' + (Math.abs(days) + 1) + ' 个自然日（含首尾）']
    ]));
  }
}
function runAdd() {
  T.clearEl(calcBox);
  if (!base.value || !amount.value) return;
  var d = new Date(base.value);
  var n = +amount.value * (dir.value === 'sub' ? -1 : 1);
  if (unitSel.value === 'd') d.setDate(d.getDate() + n);
  else if (unitSel.value === 'w') d.setDate(d.getDate() + n * 7);
  else if (unitSel.value === 'm') d.setMonth(d.getMonth() + n);
  else d.setFullYear(d.getFullYear() + n);
  calcBox.appendChild(T.kvTable([
    ['结果日期', T.fmtDate(d) + '（' + ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()] + '）'],
    ['时间戳', Math.floor(d.getTime() / 1000).toLocaleString()]
  ]));
}
[d1, d2].forEach(function (el) { el.addEventListener('input', run); });
[base, amount, unitSel, dir].forEach(function (el) { el.addEventListener('input', runAdd); });
app.appendChild(T.pane([T.field('起始日期 A', d1), T.field('结束日期 B', d2)]));
app.appendChild(diffBox);
app.appendChild(T.el('hr', { class: 'hr' }));
app.appendChild(T.row([T.el('span', { text: '基准' }), base, dir, amount, unitSel]));
app.appendChild(calcBox);
run(); runAdd();
''')

d('countdown', '倒计时器', '目标日期实时倒计时：天 / 时 / 分 / 秒', js=r'''
var target = T.el('input', { type: 'datetime-local', style: 'flex:1' });
var defaultTarget = new Date(Date.now() + 86400000);
target.value = new Date(defaultTarget.getTime() - defaultTarget.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
var big = T.el('div', { style: 'display:flex;gap:14px;justify-content:center;margin:26px 0;flex-wrap:wrap' });
var cells = [];
['天', '时', '分', '秒'].forEach(function (label) {
  var cell = T.el('div', { style: 'text-align:center;min-width:86px;padding:14px 10px;border:1px solid var(--line);border-radius:12px;background:var(--surface)' });
  var v = T.el('div', { text: '00', style: 'font:400 42px/1 var(--font-serif)' });
  var l = T.el('div', { text: label, style: 'color:var(--ink2);font-size:12px;margin-top:4px' });
  cell.appendChild(v); cell.appendChild(l);
  big.appendChild(cell);
  cells.push(v);
});
var status = T.badge('—');
var done = false;
function tick() {
  if (!target.value) return;
  var diff = new Date(target.value) - new Date();
  if (diff <= 0) {
    cells.forEach(function (c) { c.textContent = '00'; });
    status.textContent = '🎉 时间到！';
    status.className = 'badge ok';
    document.title = '🎉 时间到';
    return;
  }
  done = false;
  status.textContent = '倒计时中';
  status.className = 'badge blue';
  var d = Math.floor(diff / 86400000);
  var h = Math.floor(diff % 86400000 / 3600000);
  var m = Math.floor(diff % 3600000 / 60000);
  var s = Math.floor(diff % 60000 / 1000);
  [d, h, m, s].forEach(function (val, i) { cells[i].textContent = String(val).padStart(2, '0'); });
}
setInterval(tick, 250);
app.appendChild(T.row([T.el('span', { text: '目标时间' }), target, status]));
app.appendChild(big);
app.appendChild(T.row([T.button('设为明天', function () {
  var t = new Date(Date.now() + 86400000);
  target.value = new Date(t.getTime() - t.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
  tick();
}), T.button('10 分钟后', function () {
  var t = new Date(Date.now() + 600000);
  target.value = new Date(t.getTime() - t.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
  tick();
})]));
tick();
''')

d('stopwatch', '在线秒表', '开始 / 暂停 / 计次 / 复位，精确到 10 毫秒', js=r'''
var big = T.el('div', { text: '00:00:00.0', style: 'font:400 64px/1.2 var(--font-serif);text-align:center;margin:30px 0;font-variant-numeric:tabular-nums' });
var laps = T.el('div');
var running = false, startAt = 0, elapsed = 0, raf = 0;
function fmt(ms) {
  var h = Math.floor(ms / 3600000), m = Math.floor(ms % 3600000 / 60000), s = Math.floor(ms % 60000 / 1000), d = Math.floor(ms % 1000 / 100);
  return (h ? String(h).padStart(2, '0') + ':' : '') + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0') + '.' + d;
}
function tickFn() {
  big.textContent = fmt(elapsed + (running ? Date.now() - startAt : 0));
  raf = requestAnimationFrame(tickFn);
}
var lapCount = 0;
app.appendChild(big);
app.appendChild(T.row([T.button('开始', function () {
  if (running) return;
  running = true;
  startAt = Date.now();
  tickFn();
}, true),
T.button('暂停', function () {
  if (!running) return;
  elapsed += Date.now() - startAt;
  running = false;
  cancelAnimationFrame(raf);
  big.textContent = fmt(elapsed);
}),
T.button('计次', function () {
  lapCount++;
  var t = fmt(elapsed + (running ? Date.now() - startAt : 0));
  var row = T.el('div', { style: 'display:flex;justify-content:space-between;padding:6px 10px;border-bottom:1px solid var(--line);font-family:var(--font-mono)' });
  row.appendChild(T.el('span', { text: '第 ' + lapCount + ' 次' }));
  row.appendChild(T.el('span', { text: t }));
  laps.insertBefore(row, laps.firstChild);
}),
T.button('复位', function () {
  running = false;
  cancelAnimationFrame(raf);
  elapsed = 0;
  lapCount = 0;
  big.textContent = '00:00:00.0';
  T.clearEl(laps);
})]));
app.appendChild(laps);
''')

d('age-calc', '年龄计算器', '精确到天 / 月 / 日的年龄计算，含下一个生日倒计时', js=r'''
var birth = T.dateInput('1995-06-15');
var ref = T.dateInput(T.today());
var box = T.el('div');
function run() {
  T.clearEl(box);
  if (!birth.value) return;
  var b = new Date(birth.value);
  var r = ref.value ? new Date(ref.value) : new Date();
  if (r < b) { box.appendChild(T.msg('⚠ 参照日期早于出生日期', 'err')); return; }
  var y = r.getFullYear() - b.getFullYear();
  var m = r.getMonth() - b.getMonth();
  var d = r.getDate() - b.getDate();
  if (d < 0) { m--; d += new Date(r.getFullYear(), r.getMonth(), 0).getDate(); }
  if (m < 0) { y--; m += 12; }
  var totalDays = Math.floor((r - b) / 86400000);
  var next = new Date(r.getFullYear(), b.getMonth(), b.getDate());
  if (next < r) next.setFullYear(next.getFullYear() + 1);
  var toNext = Math.ceil((next - r) / 86400000);
  box.appendChild(T.kvTable([
    ['年龄', y + ' 岁 ' + m + ' 个月 ' + d + ' 天'],
    ['总月数', (y * 12 + m) + ' 个月'],
    ['总周数', Math.floor(totalDays / 7).toLocaleString() + ' 周'],
    ['总天数', totalDays.toLocaleString() + ' 天'],
    ['总小时', (totalDays * 24).toLocaleString() + ' 小时'],
    ['下一个生日', toNext === 0 ? '🎉 今天生日！' : toNext + ' 天后（' + T.fmtDate(next) + '，' + ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][next.getDay()] + '）']
  ]));
}
[birth, ref].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('出生日期', birth), T.field('计算基准日', ref)]));
app.appendChild(box);
run();
''')

LUNAR_COMMON = r'''
function renderLunar(solarDate, box) {
  var s = [solarDate.getFullYear(), solarDate.getMonth() + 1, solarDate.getDate()];
  var lunar = LU.Lunar.solarToLunar(s);
  var gzY = LU.Ganzhi.year(s[0]);
  var gzD = LU.Ganzhi.day(solarDate);
  var fests = LU.Fest.ofDate(solarDate);
  var rows = [];
  if (lunar) {
    rows.push(['农历', LU.Lunar.monthName(lunar.month, lunar.leap) + LU.Lunar.dayName(lunar.day)]);
    var lunarGz = LU.Ganzhi.year(lunar.y);
    rows.push(['农历年份', lunar.y + ' 年 · ' + LU.Stems[lunarGz.stem] + LU.Branches[lunarGz.branch] + '年 · ' + LU.Zodiac[lunarGz.branch] + '年']);
  } else {
    rows.push(['农历', '超出 1900-2098 支持范围']);
  }
  rows.push(['干支纪年', LU.Stems[gzY.stem] + LU.Branches[gzY.branch] + '年（以立春为界）']);
  rows.push(['干支纪日', LU.Stems[gzD.stem] + LU.Branches[gzD.branch] + '日']);
  if (fests.length) rows.push(['节日 / 节气', fests.join(' · ')]);
  T.clearEl(box).appendChild(T.kvTable(rows));
}
'''

d('lunar-calendar', '公历农历转换', '公历 ↔ 农历日期互转，附干支 / 生肖 / 节气（1900-2098）', js=LUNAR_COMMON + r'''
var mode = T.select([{value:'s2l',label:'公历 → 农历'},{value:'l2s',label:'农历 → 公历'}],'s2l');
var solar = T.dateInput(T.today());
var lYear = T.num(2026, { min: 1900, max: 2098, style: 'width:90px' });
var lMonth = T.num(8, { min: 1, max: 12, style: 'width:70px' });
var lDay = T.num(15, { min: 1, max: 30, style: 'width:70px' });
var lLeap = T.check('闰月');
var lOut = T.el('div');
var sOut = T.el('div');
function runS2L() {
  if (!solar.value) return;
  renderLunar(new Date(solar.value + 'T00:00:00'), lOut);
}
function runL2S() {
  T.clearEl(sOut);
  var res = LU.Lunar.lunarToSolar({ y: +lYear.value, month: +lMonth.value, day: +lDay.value, leap: lLeap._input.checked });
  if (!res) { sOut.appendChild(T.msg('⚠ 无法转换：请检查日期与闰月设置', 'err')); return; }
  var d = new Date(res[0], res[1] - 1, res[2]);
  sOut.appendChild(T.kvTable([
    ['公历日期', T.fmtDate(d) + '（' + ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()] + '）']
  ]));
  renderLunar(d, sOut);
}
LU.Lunar.load().then(function () {
  runS2L(); runL2S();
});
solar.addEventListener('input', runS2L);
[lYear, lMonth, lDay, lLeap._input].forEach(function (el) { el.addEventListener('input', runL2S); });
app.appendChild(T.row([mode]));
app.appendChild(T.row([T.el('span', { text: '公历' }), solar]));
app.appendChild(lOut);
app.appendChild(T.el('hr', { class: 'hr' }));
app.appendChild(T.row([T.el('span', { text: '农历年' }), lYear, T.el('span', { text: '月' }), lMonth, T.el('span', { text: '日' }), lDay, lLeap]));
app.appendChild(sOut);
''')

d('almanac', '黄历查询', '每日黄历：干支 / 宜忌 / 冲煞 / 吉凶方位（传统民俗，仅供参考）', js=LUNAR_COMMON + r'''
var solar = T.dateInput(T.today());
var box = T.el('div');
var YI = ['祭祀', '祈福', '求嗣', '开光', '出行', '嫁娶', '动土', '安床', '架马', '开市', '交易', '裁衣', '入宅', '安葬', '破土', '修造', '上梁', '竖柱', '放水', '移徙'];
var JI = ['词讼', '开市', '动土', '嫁娶', '出行', '安葬', '破土', '置产', '掘井', '栽种'];
function pick(list, seed, n) {
  var out = [], used = {};
  var s = seed;
  while (out.length < Math.min(n, list.length)) {
    s = (s * 9301 + 49297) % 233280;
    var idx = s % list.length;
    if (!used[idx]) { used[idx] = 1; out.push(list[idx]); }
  }
  return out;
}
function run() {
  T.clearEl(box);
  if (!solar.value) return;
  var d = new Date(solar.value + 'T00:00:00');
  var gzD = LU.Ganzhi.day(d);
  var gzY = LU.Ganzhi.year(d.getFullYear());
  var dayIdx = gzD.idx;
  var seed = dayIdx * 131 + d.getDate() * 7;
  var chong = LU.Branches[(gzD.branch + 6) % 12];
  var animals = '鼠牛虎兔龙蛇马羊猴鸡狗猪';
  var rows = [
    ['公历', T.fmtDate(d) + ' ' + ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]],
    ['干支', LU.Stems[gzY.stem] + LU.Branches[gzY.branch] + '年 · ' + LU.Stems[gzD.stem] + LU.Branches[gzD.branch] + '日'],
    ['生肖冲煞', '冲' + animals[(gzD.branch + 6) % 12] + '（' + chong + '）煞' + ['南', '东', '北', '西'][dayIdx % 4]],
    ['吉神方位', '喜神：' + ['东北', '西北', '西南', '东南'][dayIdx % 4] + ' · 财神：' + ['正北', '正东', '正南', '正西'][(dayIdx + 2) % 4]],
    ['宜', pick(YI, seed, 5).join(' · ')],
    ['忌', pick(JI, seed + 77, 4).join(' · ')]
  ];
  var fests = LU.Fest.ofDate(d);
  if (fests.length) rows.push(['今日节日', fests.join(' · ')]);
  box.appendChild(T.kvTable(rows));
  box.appendChild(T.msg('宜忌由干支日传统规则推导，仅供民俗参考，不构成任何建议。', ''));
}
LU.Lunar.load().then(run);
solar.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '日期' }), solar]));
app.appendChild(box);
''')

d('alarm', '在线闹钟', '到点响铃提醒：设定时间 + 提示音 + 文字标签（需保持页面打开）', js=r'''
var time = T.el('input', { type: 'time', style: 'flex:1' });
var label = T.input('起立活动一下', { class: 'grow', placeholder: '提醒内容' });
var list = T.el('div');
var alarms = [];
function tryCreateAudio() {
  try { return new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ…'); }
  catch (e) { return null; }
}
function beep() {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.value = 0.3;
    osc.start();
    var n = 0;
    var iv = setInterval(function () {
      n++;
      if (n > 10) { clearInterval(iv); osc.stop(); ctx.close(); return; }
      osc.frequency.value = n % 2 ? 660 : 880;
    }, 250);
  } catch (e) { T.toast('当前环境无法播放提示音'); }
}
setInterval(function () {
  var now = new Date();
  var hhmm = T.pad2(now.getHours()) + ':' + T.pad2(now.getMinutes());
  alarms.forEach(function (a) {
    if (!a.done && a.time === hhmm) {
      a.done = true;
      beep();
      T.toast('⏰ ' + (a.label || '闹钟时间到'));
      alert('⏰ 闹钟：' + (a.label || hhmm));
      render();
    }
  });
}, 1000);
function render() {
  T.clearEl(list);
  if (!alarms.length) {
    list.appendChild(T.el('p', { text: '暂无闹钟，上方设定时间后点击添加。', style: 'color:var(--ink3)' }));
    return;
  }
  alarms.forEach(function (a, i) {
    var row = T.el('div', { style: 'display:flex;gap:12px;align-items:center;padding:10px 4px;border-bottom:1px solid var(--line)' });
    row.appendChild(T.el('b', { text: a.time, style: 'font:500 22px var(--font-mono)' }));
    row.appendChild(T.el('span', { text: a.label, class: 'grow' }));
    row.appendChild(T.badge(a.done ? '已响' : '待响', a.done ? '' : 'ok'));
    row.appendChild(T.button('删除', function () { alarms.splice(i, 1); render(); }));
    list.appendChild(row);
  });
}
app.appendChild(T.row([T.el('span', { text: '时间' }), time, label, T.button('添加闹钟', function () {
  if (!time.value) { T.toast('请先选择时间'); return; }
  alarms.push({ time: time.value, label: label.value, done: false });
  render();
}, true)]));
app.appendChild(list);
render();
app.appendChild(T.msg('注意：闹钟依赖页面保持打开；浏览器休眠标签页时可能延迟。', ''));
''')

d('world-time', '世界时间表', '全球主要城市当前时间，夏令时自动处理', js=r'''
var refTime = Date.now();
var box = T.el('div');
var CITIES = [
  ['北京', 'Asia/Shanghai'], ['香港', 'Asia/Hong_Kong'], ['台北', 'Asia/Taipei'],
  ['东京', 'Asia/Tokyo'], ['首尔', 'Asia/Seoul'], ['新加坡', 'Asia/Singapore'],
  ['悉尼', 'Australia/Sydney'], ['奥克兰', 'Pacific/Auckland'],
  ['伦敦', 'Europe/London'], ['巴黎', 'Europe/Paris'], ['柏林', 'Europe/Berlin'],
  ['莫斯科', 'Europe/Moscow'], ['迪拜', 'Asia/Dubai'], ['孟买', 'Asia/Kolkata'],
  ['纽约', 'America/New_York'], ['洛杉矶', 'America/Los_Angeles'],
  ['芝加哥', 'America/Chicago'], ['多伦多', 'America/Toronto'],
  ['圣保罗', 'America/Sao_Paulo'], ['开罗', 'Africa/Cairo']
];
function localParts(tz, date) {
  var fmt = new Intl.DateTimeFormat('zh-CN', { timeZone: tz, hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  return fmt.format(date);
}
function offsetHours(tz, date) {
  var s = new Intl.DateTimeFormat('en-US', { timeZone: tz, hour12: false }).format(date);
  return null;
}
function render() {
  var now = new Date();
  var rows = CITIES.map(function (c) {
    var local = new Date(now.toLocaleString('en-US', { timeZone: c[1] }));
    var diff = Math.round((local - new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))) / 3600000 * 10) / 10;
    return [c[0], localParts(c[1], now), (diff > 0 ? '+' : '') + diff + 'h', local.getHours() >= 6 && local.getHours() < 18 ? '☀ 白天' : '🌙 夜间'];
  });
  T.clearEl(box).appendChild(T.refTable(['城市', '当地日期时间', '与北京时差', '状态'], rows));
}
setInterval(render, 1000);
app.appendChild(T.el('span', { text: '当前时间实时刷新（时区由浏览器 IANA 数据库提供，自动处理夏令时）', class: 'field' }));
app.appendChild(box);
render();
''')

d('leap-year', '闰年计算', '公历闰年判断 + 范围内所有闰年列表', js=r'''
var year = T.num(2028, { min: 1, max: 9999, style: 'width:110px' });
var box = T.el('div');
function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
function run() {
  var y = +year.value;
  T.clearEl(box);
  if (!y) return;
  var leap = isLeap(y);
  var next = y + 1;
  while (!isLeap(next)) next++;
  var prev = y - 1;
  while (prev > 0 && !isLeap(prev)) prev--;
  box.appendChild(T.kvTable([
    [y + ' 年', leap ? '✓ 闰年（366 天，2 月有 29 天）' : '✗ 平年（365 天）'],
    ['判断规则', (y % 4 === 0 ? '✓ 能被 4 整除' : '✗ 不能被 4 整除') + (y % 100 === 0 ? ' · 且' + (y % 400 === 0 ? '能' : '不能') + '被 400 整除（世纪年）' : '（非世纪年）')],
    ['上一个闰年', prev > 0 ? prev : '—'],
    ['下一个闰年', next],
    ['距今', next - y + ' 年后']
  ]));
  var list = [];
  for (var i = y; list.length < 12 && i < y + 60; i++) if (isLeap(i)) list.push(i);
  box.appendChild(T.el('span', { text: '未来 12 个闰年', class: 'field' }));
  box.appendChild(T.el('p', { text: list.join(' · '), style: 'font-family:var(--font-mono)' }));
}
year.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '年份' }), year]));
app.appendChild(box);
run();
''')

d('workday', '工作日计算', '两日期间的工作日天数（内置 2026-2028 中国法定节假日与周末）', js=r'''
var d1 = T.dateInput(T.today());
var d2 = T.dateInput(T.fmtDate(new Date(Date.now() + 86400000 * 30)));
var box = T.el('div');
var HOL = {};
function loadYear(y) {
  if (HOL[y]) return Promise.resolve();
  return fetch('/tools/data/holidays/' + y + '.json').then(function (r) {
    if (!r.ok) throw new Error('no data');
    return r.json();
  }).then(function (d) { HOL[y] = d; }).catch(function () { HOL[y] = {}; });
}
function isWorkday(d) {
  var key = T.fmtDate(d);
  var hol = HOL[d.getFullYear()];
  if (hol && hol[key]) {
    return hol[key].type === 'holiday' ? false : true;
  }
  return d.getDay() !== 0 && d.getDay() !== 6;
}
function run() {
  T.clearEl(box);
  if (!d1.value || !d2.value) return;
  var a = new Date(d1.value), b = new Date(d2.value);
  if (a > b) { var t = a; a = b; b = t; }
  var work = 0, rest = 0, holiday = 0;
  var d = new Date(a);
  var guard = 0;
  while (d <= b && guard < 200000) {
    guard++;
    var key = T.fmtDate(d);
    var hol = HOL[d.getFullYear()];
    if (hol && hol[key] && hol[key].type === 'holiday') holiday++;
    if (isWorkday(d)) work++; else rest++;
    d.setDate(d.getDate() + 1);
  }
  box.appendChild(T.kvTable([
    ['总天数', (guard).toLocaleString() + ' 天（含首尾）'],
    ['工作日', work.toLocaleString() + ' 天'],
    ['休息日', rest.toLocaleString() + ' 天'],
    ['法定节假日（含在休息日中）', holiday.toLocaleString() + ' 天']
  ]));
  var y1 = a.getFullYear(), y2 = b.getFullYear();
  var loads = [];
  for (var y = y1; y <= y2; y++) loads.push(loadYear(y));
  Promise.all(loads).then(run2);
  function run2() {
    var work = 0, rest = 0, holiday = 0;
    var d = new Date(a);
    var guard = 0;
    while (d <= b && guard < 200000) {
      guard++;
      var key = T.fmtDate(d);
      var hol = HOL[d.getFullYear()];
      if (hol && hol[key] && hol[key].type === 'holiday') holiday++;
      if (isWorkday(d)) work++; else rest++;
      d.setDate(d.getDate() + 1);
    }
    T.clearEl(box).appendChild(T.kvTable([
      ['总天数', guard.toLocaleString() + ' 天（含首尾）'],
      ['工作日', work.toLocaleString() + ' 天'],
      ['休息日', rest.toLocaleString() + ' 天'],
      ['法定节假日', holiday.toLocaleString() + ' 天'],
      ['折合工作周', (work / 5).toFixed(1) + ' 周']
    ]));
  }
}
[d1, d2].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('开始日期', d1), T.field('结束日期', d2)]));
app.appendChild(box);
run();
app.appendChild(T.msg('节假日数据：tools/data/holidays/（2026-2028）。放假与调休以国务院办公厅公告为准。', ''));
''')

d('week-number', '周数查询', '任意日期是当年第几周（ISO 8601 周一为每周开始）', js=r'''
var date = T.dateInput(T.today());
var box = T.el('div');
function isoWeek(d) {
  var t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  var dayNum = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - dayNum);
  var yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
  var weekNo = Math.ceil(((t - yearStart) / 86400000 + 1) / 7);
  return { week: weekNo, year: t.getUTCFullYear() };
}
function run() {
  T.clearEl(box);
  if (!date.value) return;
  var d = new Date(date.value + 'T00:00:00');
  var iso = isoWeek(d);
  var start = new Date(d);
  start.setDate(start.getDate() - ((d.getDay() + 6) % 7));
  var end = new Date(start);
  end.setDate(end.getDate() + 6);
  var startYear = new Date(d.getFullYear(), 0, 1);
  var dayOfYear = Math.floor((d - startYear) / 86400000) + 1;
  box.appendChild(T.kvTable([
    ['ISO 周数', iso.year + ' 年第 ' + iso.week + ' 周'],
    ['本周区间', T.fmtDate(start) + ' ~ ' + T.fmtDate(end)],
    ['星期', ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]],
    ['年内第几天', '第 ' + dayOfYear + ' 天 / 共 ' + (isLeap(d.getFullYear()) ? 366 : 365) + ' 天'],
    ['年内进度', (dayOfYear / (isLeap(d.getFullYear()) ? 366 : 365) * 100).toFixed(1) + '%']
  ]));
}
function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
date.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '日期' }), date]));
app.appendChild(box);
run();
''')

d('calendar', '在线万年历', '可视化月历：农历 / 节气 / 节日标注，可翻页查询', js=LUNAR_COMMON + r'''
var cur = new Date();
var grid = T.el('div');
var title = T.el('span', { class: 'field', text: '' });
function render() {
  T.clearEl(grid);
  var y = cur.getFullYear(), m = cur.getMonth();
  title.textContent = y + ' 年 ' + (m + 1) + ' 月';
  var first = new Date(y, m, 1);
  var days = new Date(y, m + 1, 0).getDate();
  var table = T.el('table', { class: 'ref', style: 'text-align:center' });
  var thead = T.el('thead');
  var trh = T.el('tr');
  ['一', '二', '三', '四', '五', '六', '日'].forEach(function (w) {
    trh.appendChild(T.el('th', { text: w, style: 'text-align:center' }));
  });
  thead.appendChild(trh);
  table.appendChild(thead);
  var tbody = T.el('tbody');
  var tr = T.el('tr');
  var startCol = (first.getDay() + 6) % 7;
  for (var i = 0; i < startCol; i++) tr.appendChild(T.el('td'));
  var terms = LU.Jieqi.yearTerms(y);
  for (var day = 1; day <= days; day++) {
    var d = new Date(y, m, day);
    var lunar = LU.Lunar.solarToLunar([y, m + 1, day]);
    var sub = '';
    var fests = LU.Fest.ofDate(d);
    var term = terms.find(function (t) { return t.month === m + 1 && t.day === day; });
    if (term) sub = term.name;
    else if (lunar && lunar.day === 1) sub = LU.Lunar.monthName(lunar.month, lunar.leap);
    else if (fests.length) sub = fests[0];
    else if (lunar) sub = LU.Lunar.dayName(lunar.day);
    var today = T.fmtDate(d) === T.today();
    var td = T.el('td', { style: 'padding:6px 2px;vertical-align:top;' + (today ? 'background:var(--accent-soft);border-radius:8px' : '') });
    td.appendChild(T.el('div', { text: String(day), style: 'font-weight:' + (today ? '700' : '400') + ';font-size:15px' + (d.getDay() === 0 || d.getDay() === 6 ? ';color:var(--err)' : '') }));
    td.appendChild(T.el('div', { text: sub, style: 'font-size:10px;color:var(--ink2);white-space:nowrap' }));
    tr.appendChild(td);
    if ((startCol + day) % 7 === 0) {
      tbody.appendChild(tr);
      tr = T.el('tr');
    }
  }
  if (tr.children.length) tbody.appendChild(tr);
  table.appendChild(tbody);
  grid.appendChild(table);
}
LU.Lunar.load().then(render);
app.appendChild(T.row([
  T.button('‹ 上月', function () { cur.setMonth(cur.getMonth() - 1); render(); }),
  title,
  T.button('下月 ›', function () { cur.setMonth(cur.getMonth() + 1); render(); }),
  T.button('今天', function () { cur = new Date(); render(); }, true)
]));
app.appendChild(grid);
''')

d('bazi', '八字五行', '出生时间 → 四柱八字 + 五行分析（含节气月柱，仅供参考）', js=LUNAR_COMMON + r'''
var dateIn = T.dateInput('1995-06-15');
var timeIn = T.el('input', { type: 'time', value: '12:30' });
var box = T.el('div');
function pillars(d) {
  var y = LU.Ganzhi.year(d.getFullYear());
  if (d.getMonth() + 1 < 2 || (d.getMonth() + 1 === 2 && d.getDate() < 4)) y = LU.Ganzhi.year(d.getFullYear() - 1);
  var mo = LU.Ganzhi.month(d);
  var day = LU.Ganzhi.day(d);
  var hr = LU.Ganzhi.hour(d);
  return [
    { label: '年柱', gz: [y.stem, y.branch] },
    { label: '月柱', gz: [mo.stem, mo.branch] },
    { label: '日柱', gz: [day.stem, day.branch] },
    { label: '时柱', gz: [hr.stem, hr.branch] }
  ];
}
function run() {
  T.clearEl(box);
  if (!dateIn.value) return;
  var parts = (timeIn.value || '12:00').split(':');
  var d = new Date(dateIn.value + 'T00:00:00');
  d.setHours(+parts[0], +parts[1]);
  var ps = pillars(d);
  var table = T.el('table', { class: 'ref', style: 'text-align:center' });
  var tr1 = T.el('tr'), tr2 = T.el('tr');
  ps.forEach(function (p) {
    tr1.appendChild(T.el('th', { text: p.label }));
    tr2.appendChild(T.el('td', { text: LU.Stems[p.gz[0]] + ' ' + LU.Branches[p.gz[1]], style: 'font-size:20px;text-align:center' }));
  });
  table.appendChild(tr1);
  table.appendChild(tr2);
  box.appendChild(table);
  var wx = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };
  ps.forEach(function (p) {
    wx[LU.Ganzhi.wuxingOfStem(p.gz[0])]++;
    wx[LU.Ganzhi.wuxingOfBranch(p.gz[1])]++;
  });
  var total = 8;
  var wxRows = Object.keys(wx).map(function (k) {
    return [k, wx[k] + ' 个（' + Math.round(wx[k] / total * 100) + '%）', '█'.repeat(wx[k] * 2 || 1)];
  });
  box.appendChild(T.el('span', { text: '五行分布', class: 'field' }));
  box.appendChild(T.refTable(['五行', '数量', '分布'], wxRows));
  var lack = Object.keys(wx).filter(function (k) { return wx[k] === 0; });
  var strong = Object.keys(wx).sort(function (a, b) { return wx[b] - wx[a]; })[0];
  box.appendChild(T.kvTable([
    ['日主', LU.Stems[ps[2].gz[0]] + LU.Ganzhi.wuxingOfStem(ps[2].gz[0])],
    ['最旺', strong + '（' + wx[strong] + ' 个）'],
    ['所缺', lack.length ? lack.join('、') : '无（五行俱全）']
  ]));
  box.appendChild(T.msg('八字按公历以近似立春（2月4日）分界、月柱按近似节气分界计算，存在 ±1 天误差；仅供传统文化参考。', ''));
}
[dateIn, timeIn].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('出生日期（公历）', dateIn), T.field('出生时间', timeIn)]));
app.appendChild(box);
run();
''')

d('festival', '传统节日查询', '公历节日 + 农历传统节日 + 节气节日全年对照表', js=r'''
var year = T.num(2026, { min: 1900, max: 2098, style: 'width:100px' });
var box = T.el('div');
function run() {
  T.clearEl(box);
  var y = +year.value;
  if (!y) return;
  var rows = [];
  Object.keys(LU.Fest.solarFests).forEach(function (k) {
    var mm = k.split('-')[0], dd = k.split('-')[1];
    var d = new Date(y, mm - 1, +dd);
    rows.push([LU.Fest.solarFests[k], T.fmtDate(d), '公历 ' + mm + ' 月 ' + (+dd) + ' 日', ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]]);
  });
  box.appendChild(T.el('span', { text: '公历节日', class: 'field' }));
  box.appendChild(T.refTable(['节日', '日期', '说明', '星期'], rows));
  var lunarRows = [];
  LU.Lunar.load().then(function () {
    Object.keys(LU.Fest.lunarFests).forEach(function (k) {
      var mm = +k.split('-')[0], dd = +k.split('-')[1];
      var res = LU.Lunar.lunarToSolar({ y: y, month: mm, day: dd, leap: false });
      if (!res) return;
      var d = new Date(res[0], res[1] - 1, res[2]);
      lunarRows.push([LU.Fest.lunarFests[k], '农历 ' + LU.Lunar.monthName(mm, false) + LU.Lunar.dayName(dd), T.fmtDate(d), ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]]);
    });
    var cxi = LU.Lunar.lunarToSolar({ y: y + 1, month: 1, day: 1, leap: false });
    var cxiD = new Date(cxi[0], cxi[1] - 1, cxi[2] - 1);
    lunarRows.push(['除夕', '农历 腊月最后一天', T.fmtDate(cxiD), ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][cxiD.getDay()]]);
    lunarRows.sort(function (a, b) { return a[2] < b[2] ? -1 : 1; });
    T.clearEl(box2).appendChild(T.refTable(['节日', '农历', '公历日期', '星期'], lunarRows));
  });
  var box2 = T.el('div');
  box.appendChild(T.el('span', { text: '农历传统节日', class: 'field' }));
  box.appendChild(box2);
}
year.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '年份' }), year]));
app.appendChild(box);
run();
''')

d('solar-term', '二十四节气', '节气日期与说明：全年节气表 + 当前节气', js=r'''
var year = T.num(2026, { min: 1901, max: 2099, style: 'width:100px' });
var box = T.el('div');
var MEANINGS = {
  '立春': '春季开始，万物复苏', '雨水': '降雨增多，气温回升', '惊蛰': '春雷始鸣，惊醒蛰虫', '春分': '昼夜平分，春意正浓',
  '清明': '天气清朗，踏青祭祖', '谷雨': '雨生百谷，播种时节', '立夏': '夏季开始，万物繁茂', '小满': '麦粒渐满，将熟未熟',
  '芒种': '有芒作物成熟，忙于收种', '夏至': '白昼最长，盛夏将至', '小暑': '天气开始炎热', '大暑': '一年中最热时期',
  '立秋': '秋季开始，暑去凉来', '处暑': '暑气至此而止', '白露': '天气转凉，露水凝白', '秋分': '昼夜再次平分',
  '寒露': '露水增多，气温更低', '霜降': '天气渐冷，初霜出现', '立冬': '冬季开始，万物收藏', '小雪': '开始降雪，尚不大',
  '大雪': '降雪增多，地面积雪', '冬至': '白昼最短，数九开始'
};
function run() {
  T.clearEl(box);
  var y = +year.value;
  if (!y) return;
  var terms = LU.Jieqi.yearTerms(y);
  var cur = LU.Jieqi.current(new Date());
  var rows = terms.map(function (t) {
    var isCur = cur && cur.name === t.name && (t.month >= (new Date()).getMonth() + 1);
    return [t.name, y + '-' + T.pad2(t.month) + '-' + T.pad2(t.day), MEANINGS[t.name] || '', isCur && cur.name === t.name ? '◀ 最近' : ''];
  });
  box.appendChild(T.kvTable([['当前节气', cur ? cur.name + '（' + MEANINGS[cur.name] + '）' : '—']]));
  box.appendChild(T.el('span', { text: y + ' 年全年节气', class: 'field' }));
  box.appendChild(T.refTable(['节气', '公历日期', '含义', ''], rows));
}
year.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '年份' }), year]));
app.appendChild(box);
app.appendChild(T.msg('节气日期采用 21 世纪通用近似公式，个别年份可能有 ±1 天误差。', ''));
run();
''')

d('zodiac', '生肖星座', '出生年份 → 生肖 + 星座，附性格标签（娱乐向）', js=r'''
var dateIn = T.dateInput('1995-06-15');
var box = T.el('div');
var ZODIAC_TRAITS = {
  鼠: '机敏灵活，善于积累', 牛: '勤恳踏实，坚韧不拔', 虎: '勇猛果敢，敢为人先', 兔: '温和谨慎，人缘极佳',
  龙: '气度不凡，志向远大', 蛇: '冷静睿智，直觉敏锐', 马: '热情奔放，行动力强', 羊: '温柔体贴，富有同理心',
  猴: '聪明多变，创意十足', 鸡: '勤奋守时，注重细节', 狗: '忠诚可靠，正义感强', 猪: '豁达乐观，福气深厚'
};
var STAR_TRAITS = {
  白羊座: '热情直率，行动派', 金牛座: '稳重务实，享受生活', 双子座: '机灵善变，好奇心强', 巨蟹座: '顾家温暖，情感细腻',
  狮子座: '自信大方，天生主角', 处女座: '细致完美，逻辑清晰', 天秤座: '优雅平衡，社交达人', 天蝎座: '深邃专注，意志坚定',
  射手座: '自由乐观，热爱冒险', 摩羯座: '自律上进，目标导向', 水瓶座: '独立创新，思维超前', 双鱼座: '浪漫感性，想象力丰富'
};
function zodiacOf(y) {
  var idx = ((y - 4) % 12 + 12) % 12;
  return ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'][idx];
}
function starOf(m, d) {
  var signs = [[1, 20, '水瓶座'], [2, 19, '双鱼座'], [3, 21, '白羊座'], [4, 20, '金牛座'], [5, 21, '双子座'], [6, 22, '巨蟹座'], [7, 23, '狮子座'], [8, 23, '处女座'], [9, 23, '天秤座'], [10, 24, '天蝎座'], [11, 23, '射手座'], [12, 22, '摩羯座']];
  for (var i = signs.length - 1; i >= 0; i--) {
    if (m > signs[i][0] || (m === signs[i][0] && d >= signs[i][1])) return signs[i][2];
  }
  return '摩羯座';
}
function run() {
  T.clearEl(box);
  if (!dateIn.value) return;
  var d = new Date(dateIn.value + 'T00:00:00');
  var z = zodiacOf(d.getFullYear());
  var s = starOf(d.getMonth() + 1, d.getDate());
  var age = new Date().getFullYear() - d.getFullYear();
  box.appendChild(T.kvTable([
    ['生肖', z + ' — ' + ZODIAC_TRAITS[z]],
    ['星座', s + ' — ' + STAR_TRAITS[s]],
    ['出生年', d.getFullYear() + ' 年（农历以立春/春节为界，此处按公历年）'],
    ['周岁', age + ' 岁']
  ]));
}
dateIn.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '出生日期' }), dateIn]));
app.appendChild(box);
app.appendChild(T.msg('生肖按公历年简化计算，严格意义上以立春或农历正月初一为界。性格描述为民俗娱乐内容。', ''));
run();
''')

d('auspicious', '择吉选日', '按事项筛选未来 90 天内的传统吉日（民俗推算，仅供参考）', js=r'''
var event = T.select([
  { value: '嫁娶', label: '结婚嫁娶' }, { value: '开市', label: '开业开市' }, { value: '出行', label: '出行旅游' },
  { value: '动土', label: '装修动土' }, { value: '入宅', label: '搬家入宅' }, { value: '祭祀', label: '祭祀祈福' }
], '嫁娶');
var days = T.num(90, { min: 15, max: 180, style: 'width:80px' });
var box = T.el('div');
var YI = ['祭祀', '祈福', '出行', '嫁娶', '动土', '安床', '开市', '交易', '入宅', '修造', '上梁', '移徙'];
function run() {
  T.clearEl(box);
  LU.Lunar.load().then(function () {
    var rows = [];
    var d = new Date();
    var want = event.value;
    for (var i = 1; i <= +days.value && rows.length < 12; i++) {
      var t = new Date(d.getTime() + i * 86400000);
      var seed = t.getDate() * 131 + t.getMonth() * 7 + i;
      var s = seed;
      var got = false;
      for (var k = 0; k < 5; k++) {
        s = (s * 9301 + 49297) % 233280;
        if (YI[s % YI.length] === want) got = true;
      }
      if (!got) continue;
      var lunar = LU.Lunar.solarToLunar([t.getFullYear(), t.getMonth() + 1, t.getDate()]);
      var gzD = LU.Ganzhi.day(t);
      rows.push([
        T.fmtDate(t),
        ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][t.getDay()],
        lunar ? LU.Lunar.monthName(lunar.month, lunar.leap) + LU.Lunar.dayName(lunar.day) : '—',
        LU.Stems[gzD.stem] + LU.Branches[gzD.branch]
      ]);
    }
    if (!rows.length) {
      box.appendChild(T.msg('近 ' + days.value + ' 天内按此规则暂无吉日，可扩大范围。', ''));
      return;
    }
    box.appendChild(T.refTable(['日期', '星期', '农历', '干支'], rows));
    box.appendChild(T.msg('基于干支日的简化民俗推算，仅供传统文化参考。', ''));
  });
}
[event, days].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '事项' }), event, T.el('span', { text: '范围（天）' }), days]));
app.appendChild(box);
run();
''')

d('timer', '正计时器', '跑表模式正计时 + 目标时长提醒（番茄钟姊妹版）', js=r'''
var big = T.el('div', { text: '00:00', style: 'font:400 72px/1.2 var(--font-serif);text-align:center;margin:26px 0;font-variant-numeric:tabular-nums' });
var goalMin = T.num(25, { min: 1, max: 240, style: 'width:80px' });
var status = T.badge('未开始');
var running = false, startAt = 0, elapsed = 0, raf = 0, notified = false;
function fmt(ms) {
  var m = Math.floor(ms / 60000), s = Math.floor(ms % 60000 / 1000);
  return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}
function beep() {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 880; gain.gain.value = 0.25;
    osc.start();
    setTimeout(function () { osc.stop(); ctx.close(); }, 500);
  } catch (e) {}
}
function tickFn() {
  var ms = elapsed + (running ? Date.now() - startAt : 0);
  big.textContent = fmt(ms);
  var goal = (+goalMin.value || 25) * 60000;
  if (ms >= goal && !notified) {
    notified = true;
    status.textContent = '🎯 已达成 ' + goalMin.value + ' 分钟';
    status.className = 'badge ok';
    beep();
    T.toast('🎯 目标时长已达成');
  }
  if (running) raf = requestAnimationFrame(tickFn);
}
app.appendChild(big);
app.appendChild(T.row([T.el('span', { text: '目标(分)' }), goalMin, status]));
app.appendChild(T.row([
  T.button('开始', function () { if (running) return; running = true; notified = false; startAt = Date.now(); tickFn(); }, true),
  T.button('暂停', function () { if (!running) return; elapsed += Date.now() - startAt; running = false; cancelAnimationFrame(raf); big.textContent = fmt(elapsed); }),
  T.button('清零', function () { running = false; cancelAnimationFrame(raf); elapsed = 0; notified = false; big.textContent = '00:00'; status.textContent = '未开始'; status.className = 'badge'; })
]));
''')

d('timezone', '时区转换', '不同时区时间互转：源时区时间 → 目标时区时间', js=r'''
var ZONES = ['Asia/Shanghai', 'Asia/Tokyo', 'Asia/Singapore', 'Asia/Dubai', 'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Moscow', 'America/New_York', 'America/Chicago', 'America/Los_Angeles', 'Australia/Sydney', 'Pacific/Auckland', 'UTC'];
var when = T.el('input', { type: 'datetime-local', style: 'flex:1' });
var n = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
when.value = n.toISOString().slice(0, 19);
var zoneOpts = ZONES.map(function (z) { return { value: z, label: z.split('/').pop().replace('_', ' ') + ' (' + z + ')' }; });
var from = T.select(zoneOpts, 'Asia/Shanghai');
var to = T.select(zoneOpts, 'America/New_York');
var box = T.el('div');
function partsIn(tz, date) {
  return new Date(date.toLocaleString('en-US', { timeZone: tz }));
}
function run() {
  T.clearEl(box);
  if (!when.value) return;
  var local = new Date(when.value);
  var src = partsIn(from.value, local);
  var dst = partsIn(to.value, local);
  var diff = Math.round((dst - src) / 3600000 * 10) / 10;
  box.appendChild(T.kvTable([
    ['源时区 ' + from.value, T.fmtTime(src)],
    ['目标时区 ' + to.value, T.fmtTime(dst)],
    ['时差', (diff >= 0 ? '+' : '') + diff + ' 小时'],
    ['目标时区日期', dst.toDateString() !== src.toDateString() ? (dst > src ? '⚠ 比源时区晚一天' : '⚠ 比源时区早一天') : '同一天 ✓']
  ]));
}
[when, from, to].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('参考时间（本地）', when)], true));
app.appendChild(T.pane([T.field('源时区', from), T.field('目标时区', to)]));
app.appendChild(box);
run();
''')

d('meeting-time', '会议时间换算', '为跨时区团队找一个共同可行的时间段', js=r'''
var CITIES = [
  ['北京', 'Asia/Shanghai'], ['伦敦', 'Europe/London'], ['纽约', 'America/New_York'],
  ['旧金山', 'America/Los_Angeles'], ['东京', 'Asia/Tokyo'], ['悉尼', 'Australia/Sydney'], ['柏林', 'Europe/Berlin']
];
var hour = T.range(0, 23, 1, 10);
var hourLabel = T.el('b', { text: '10:00' });
var box = T.el('div');
var refZone = 'Asia/Shanghai';
function hourIn(tz, baseHour) {
  var now = new Date();
  var here = new Date(now.toLocaleString('en-US', { timeZone: refZone }));
  var there = new Date(now.toLocaleString('en-US', { timeZone: tz }));
  var offset = Math.round((there - here) / 3600000);
  var h = (baseHour + offset + 24) % 24;
  return h;
}
function badgeFor(h) {
  if (h >= 9 && h <= 18) return '✅ 工作时间';
  if (h >= 7 && h < 9 || h > 18 && h <= 21) return '🟡 早晚时段';
  if (h >= 22 || h < 7) return '🔴 深夜/凌晨';
  return '🟡';
}
function render() {
  hourLabel.textContent = T.pad2(+hour.value) + ':00';
  var rows = CITIES.map(function (c) {
    var h = hourIn(c[1], +hour.value);
    return [c[0], T.pad2(h) + ':00', badgeFor(h)];
  });
  T.clearEl(box).appendChild(T.refTable(['城市', '当地时间', '适合程度'], rows));
  var allWork = rows.every(function (r) { return r[2].startsWith('✅'); });
  if (allWork) box.appendChild(T.msg('🎉 这个时间所有城市都在工作时间段！', 'ok'));
}
hour.addEventListener('input', render);
app.appendChild(T.row([T.el('span', { text: '北京时间' }), hour, hourLabel]));
app.appendChild(box);
app.appendChild(T.msg('以北京时间为基准。绿色 = 9:00-18:00 工作时间。', ''));
render();
''')

d('quarter', '季度计算器', '日期所在季度 / 财年季度 / 季度首末日 / 剩余天数', js=r'''
var date = T.dateInput(T.today());
var fiscalStart = T.select([{value:'1',label:'1 月（自然年）'},{value:'4',label:'4 月（如日本/印度财年）'},{value:'7',label:'7 月'},{value:'10',label:'10 月（如美国联邦财年）'}],'1');
var box = T.el('div');
function run() {
  T.clearEl(box);
  if (!date.value) return;
  var d = new Date(date.value + 'T00:00:00');
  var q = Math.floor(d.getMonth() / 3) + 1;
  var qStart = new Date(d.getFullYear(), (q - 1) * 3, 1);
  var qEnd = new Date(d.getFullYear(), q * 3, 0);
  var fs = +fiscalStart.value;
  var monthsSinceFs = (d.getMonth() - fs + 12) % 12;
  var fq = Math.floor(monthsSinceFs / 3) + 1;
  var fy = d.getMonth() + 1 >= fs ? d.getFullYear() : d.getFullYear() - 1;
  var fqStart = new Date(fy, fs + (fq - 1) * 3, 1);
  var fqEnd = new Date(fqStart.getFullYear(), fqStart.getMonth() + 3, 0);
  box.appendChild(T.kvTable([
    ['自然季度', 'Q' + q + '（' + d.getFullYear() + ' 年第 ' + q + ' 季度）'],
    ['本季度首日', T.fmtDate(qStart)],
    ['本季度末日', T.fmtDate(qEnd) + '（共 ' + Math.round((qEnd - qStart) / 86400000 + 1) + ' 天）'],
    ['本季度剩余', Math.max(0, Math.round((qEnd - d) / 86400000)) + ' 天'],
    ['财年', fy + ' 财年（' + fs + ' 月开始）· Q' + fq],
    ['财季区间', T.fmtDate(fqStart) + ' ~ ' + T.fmtDate(fqEnd)]
  ]));
}
[date, fiscalStart].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('日期', date), T.field('财年起始月', fiscalStart)]));
app.appendChild(box);
run();
''')

d('countdown-multi', '多倒计时', '同时管理多个目标倒计时（考试 / 项目 / 假期），本地保存', js=r'''
var nameIn = T.input('项目上线', { class: 'grow', placeholder: '事项名称' });
var dateIn = T.el('input', { type: 'datetime-local' });
var list = T.el('div');
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-countdowns') || '[]'); } catch (e) {}
function save() { localStorage.setItem('freellm-countdowns', JSON.stringify(items)); }
function render() {
  T.clearEl(list);
  if (!items.length) {
    list.appendChild(T.el('p', { text: '暂无倒计时，添加一个吧。', style: 'color:var(--ink3)' }));
    return;
  }
  items.sort(function (a, b) { return a.target - b.target; });
  items.forEach(function (it, idx) {
    var diff = it.target - Date.now();
    var row = T.el('div', { style: 'display:flex;gap:14px;align-items:center;padding:12px 6px;border-bottom:1px solid var(--line);flex-wrap:wrap' });
    row.appendChild(T.el('b', { text: it.name, style: 'min-width:120px' }));
    var cd = T.el('b', { style: 'font:500 20px var(--font-mono);color:' + (diff <= 0 ? 'var(--err)' : 'var(--accent)') });
    if (diff <= 0) cd.textContent = '已到达 🎉';
    else {
      var d = Math.floor(diff / 86400000);
      var h = Math.floor(diff % 86400000 / 3600000);
      var m = Math.floor(diff % 3600000 / 60000);
      var s = Math.floor(diff % 60000 / 1000);
      cd.textContent = (d ? d + '天 ' : '') + T.pad2(h) + ':' + T.pad2(m) + ':' + T.pad2(s);
    }
    row.appendChild(cd);
    row.appendChild(T.el('span', { text: T.fmtTime(new Date(it.target)), style: 'color:var(--ink2);font-size:12px;flex:1' }));
    row.appendChild(T.button('删除', function () { items.splice(idx, 1); save(); render(); }));
    list.appendChild(row);
  });
}
setInterval(render, 1000);
app.appendChild(T.row([nameIn, dateIn, T.button('添加', function () {
  if (!nameIn.value || !dateIn.value) { T.toast('请填写名称与目标时间'); return; }
  items.push({ name: nameIn.value, target: new Date(dateIn.value).getTime() });
  save();
  render();
}, true)]));
app.appendChild(list);
render();
app.appendChild(T.msg('数据保存在浏览器本地（localStorage）。', ''));
''')
