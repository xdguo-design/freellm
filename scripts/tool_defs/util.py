# -*- coding: utf-8 -*-
"""其他实用工具类定义"""
from .registry import d

d('tts', '文字转语音', 'Web Speech API 朗读：语速 / 音调 / 音色可调', js=r'''
var input = T.textarea('你好，欢迎使用 FreeLLM 在线工具。The quick brown fox jumps over the lazy dog.', true);
input.value = '你好，欢迎使用 FreeLLM 在线工具。The quick brown fox jumps over the lazy dog.';
var voiceSel = T.select([], '');
var rate = T.range(0.5, 2, 0.1, 1);
var pitch = T.range(0.5, 2, 0.1, 1);
var status = T.badge('—');
function fillVoices() {
  var voices = speechSynthesis.getVoices();
  T.clearEl(voiceSel);
  var zh = voices.filter(function (v) { return /zh|Chinese/i.test(v.lang); });
  var others = voices.filter(function (v) { return !/zh|Chinese/i.test(v.lang); });
  zh.concat(others).slice(0, 40).forEach(function (v) {
    voiceSel.appendChild(T.el('option', { value: v.name, text: v.name + '（' + v.lang + '）' }));
  });
  if (!voices.length) status.textContent = '未检测到系统语音';
}
fillVoices();
speechSynthesis.onvoiceschanged = fillVoices;
function speak() {
  speechSynthesis.cancel();
  var u = new SpeechSynthesisUtterance(input.value);
  var voices = speechSynthesis.getVoices();
  var v = voices.find(function (x) { return x.name === voiceSel.value; });
  if (v) u.voice = v;
  u.rate = +rate.value;
  u.pitch = +pitch.value;
  u.onstart = function () { status.textContent = '朗读中…'; status.className = 'badge blue'; };
  u.onend = function () { status.textContent = '✓ 朗读完成'; status.className = 'badge ok'; };
  u.onerror = function () { status.textContent = '朗读失败'; status.className = 'badge warn'; };
  speechSynthesis.speak(u);
}
app.appendChild(T.pane([T.field('朗读文本', input)], true));
app.appendChild(T.row([T.el('span', { text: '音色' }), voiceSel]));
app.appendChild(T.row([T.el('span', { text: '语速' }), rate, T.el('span', { text: '音调' }), pitch]));
app.appendChild(T.row([T.button('▶ 朗读', speak, true),
  T.button('⏸ 暂停', function () { speechSynthesis.pause(); }),
  T.button('▶ 继续', function () { speechSynthesis.resume(); }),
  T.button('⏹ 停止', function () { speechSynthesis.cancel(); }), status]));
''')

d('whitenoise', '在线白噪音', '白噪音 / 粉噪音 / 棕噪音 + 模拟雨声，助眠专注', js=r'''
var type = T.select([
  { value: 'white', label: '白噪音（明亮）' },
  { value: 'pink', label: '粉噪音（柔和）' },
  { value: 'brown', label: '棕噪音（低沉）' },
  { value: 'rain', label: '模拟雨声' }
], 'brown');
var volume = T.range(0, 100, 1, 30);
var status = T.badge('未播放');
var ctx = null, src = null, gainNode = null, filterNode = null, lfo = null;
function start() {
  stop();
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  var bufferSize = 2 * ctx.sampleRate;
  var buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
  var data = buffer.getChannelData(0);
  var t = type.value;
  if (t === 'white') {
    for (var i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
  } else if (t === 'pink') {
    var b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (i = 0; i < bufferSize; i++) {
      var w = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + w * 0.0555179;
      b1 = 0.99332 * b1 + w * 0.0750759;
      b2 = 0.96900 * b2 + w * 0.1538520;
      b3 = 0.86650 * b3 + w * 0.3104856;
      b4 = 0.55000 * b4 + w * 0.5329522;
      b5 = -0.7616 * b5 - w * 0.0168980;
      data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362) * 0.11;
      b6 = w * 0.115926;
    }
  } else if (t === 'brown') {
    var last = 0;
    for (i = 0; i < bufferSize; i++) {
      w = Math.random() * 2 - 1;
      last = (last + 0.02 * w) / 1.02;
      data[i] = last * 3.5;
    }
  } else {
    for (i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
  }
  src = ctx.createBufferSource();
  src.buffer = buffer;
  src.loop = true;
  gainNode = ctx.createGain();
  gainNode.gain.value = volume.value / 100 * (t === 'rain' ? 0.4 : 0.25);
  if (t === 'rain') {
    filterNode = ctx.createBiquadFilter();
    filterNode.type = 'lowpass';
    filterNode.frequency.value = 1400;
    lfo = ctx.createOscillator();
    var lfoGain = ctx.createGain();
    lfo.frequency.value = 0.25;
    lfoGain.gain.value = 600;
    lfo.connect(lfoGain).connect(filterNode.frequency);
    lfo.start();
    src.connect(filterNode).connect(gainNode).connect(ctx.destination);
  } else {
    src.connect(gainNode).connect(ctx.destination);
  }
  src.start();
  status.textContent = '🔊 播放中';
  status.className = 'badge ok';
}
function stop() {
  if (src) { try { src.stop(); } catch (e) {} src = null; }
  if (lfo) { try { lfo.stop(); } catch (e) {} lfo = null; }
  if (ctx) { try { ctx.close(); } catch (e) {} ctx = null; }
  status.textContent = '已停止';
  status.className = 'badge';
}
type.addEventListener('change', function () { if (src) start(); });
volume.addEventListener('input', function () { if (gainNode) gainNode.gain.value = volume.value / 100 * 0.25; });
app.appendChild(T.row([type, T.el('span', { text: '音量' }), volume, T.button('▶ 播放', start, true), T.button('⏹ 停止', stop), status]));
app.appendChild(T.el('p', { text: '适合阅读、专注与助眠。白噪音均匀明亮，粉噪音柔和，棕噪音最适合睡眠。', style: 'color:var(--ink2);font-size:12px' }));
''')

d('metronome', '节拍器', '可调 BPM 电子节拍器：强弱拍 + 拍号设置', js=r'''
var bpm = T.range(30, 240, 1, 100);
var bpmLabel = T.el('b', { text: '100 BPM' });
var beats = T.select([{value:'2',label:'2/2'},{value:'3',label:'3/4 圆舞曲'},{value:'4',label:'4/4 常用'},{value:'6',label:'6/8'}],'4');
var status = T.badge('未开始');
var dots = T.el('div', { style: 'display:flex;gap:10px;justify-content:center;margin:20px 0' });
var ctx = null, timer = 0, beat = 0;
function drawDots() {
  T.clearEl(dots);
  for (var i = 0; i < +beats.value; i++) {
    dots.appendChild(T.el('div', { style: 'width:26px;height:26px;border-radius:50%;background:' + (i === beat % +beats.value && ctx ? (i === 0 ? 'var(--err)' : 'var(--accent)') : 'var(--line)') }));
  }
}
function click(strong) {
  var c = ctx;
  var osc = c.createOscillator();
  var gain = c.createGain();
  osc.frequency.value = strong ? 1200 : 800;
  gain.gain.setValueAtTime(strong ? 0.5 : 0.3, c.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.08);
  osc.connect(gain).connect(c.destination);
  osc.start();
  osc.stop(c.currentTime + 0.09);
}
function start() {
  stop();
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  var interval = 60000 / +bpm.value;
  beat = 0;
  function tickBeat() {
    click(beat % +beats.value === 0);
    drawDots();
    beat++;
  }
  tickBeat();
  timer = setInterval(tickBeat, interval);
  status.textContent = '节拍中';
  status.className = 'badge ok';
}
function stop() {
  if (timer) clearInterval(timer);
  timer = 0;
  if (ctx) { try { ctx.close(); } catch (e) {} ctx = null; }
  drawDots();
}
bpm.addEventListener('input', function () {
  bpmLabel.textContent = bpm.value + ' BPM';
  if (timer) start();
});
beats.addEventListener('change', function () { beat = 0; drawDots(); if (timer) start(); });
app.appendChild(T.row([T.el('span', { text: '速度' }), bpm, bpmLabel, beats, T.button('▶ 开始', function () { timer ? stop() : start(); }, true), T.button('⏹ 停止', stop), status]));
app.appendChild(dots);
drawDots();
app.appendChild(T.el('p', { text: '常用 BPM：慢板 60-76 · 行板 76-108 · 快板 108-168 · 急板 168+。红点为强拍。', style: 'color:var(--ink2);font-size:12px' }));
''')

d('clipboard-view', '剪贴板查看', '读取剪贴板内容（文本），需浏览器授权', js=r'''
var output = T.out('剪贴板内容将显示在这里…');
var info = T.badge('—');
function read() {
  navigator.clipboard.readText().then(function (text) {
    output.value = text;
    info.textContent = text.length + ' 个字符';
    info.className = 'badge ok';
  }).catch(function (e) {
    info.textContent = '读取失败：' + e.message + '（需授权且页面处于前台）';
    info.className = 'badge warn';
  });
}
T.button('📋 读取剪贴板', read, true)
app.appendChild(T.row([T.button('📋 读取剪贴板', read, true), info]));
app.appendChild(T.pane([T.field('剪贴板内容', output)], true));
app.appendChild(T.row([T.button('复制内容', function () { T.copy(output.value); }),
  T.button('清空统计（写空值）', function () {
    navigator.clipboard.writeText('').then(function () { T.toast('已写入空内容'); });
  })]));
''')

d('screen-info', '屏幕信息', '当前设备屏幕参数：分辨率 / 色深 / 像素比 / 视口', js=r'''
var info = T.el('div', { class: 'pane single' });
function render() {
  var rows = [
    ['屏幕分辨率', screen.width + ' × ' + screen.height],
    ['可用区域', screen.availWidth + ' × ' + screen.availHeight + '（去除任务栏）'],
    ['色深', screen.colorDepth + ' bit'],
    ['像素深度', screen.pixelDepth + ' bit'],
    ['设备像素比 DPR', window.devicePixelRatio],
    ['物理分辨率估算', Math.round(screen.width * devicePixelRatio) + ' × ' + Math.round(screen.height * devicePixelRatio)],
    ['浏览器视口', window.innerWidth + ' × ' + window.innerHeight],
    ['窗口位置', '(' + window.screenX + ', ' + window.screenY + ')'],
    ['页面滚动位置', 'x=' + window.scrollX + ', y=' + window.scrollY],
    ['屏幕方向', (screen.orientation && screen.orientation.type) || '未知'],
    ['逻辑 CPU 数', navigator.hardwareConcurrency || '未知'],
    ['设备内存', navigator.deviceMemory ? navigator.deviceMemory + ' GB' : '未知'],
    ['语言', navigator.language],
    ['平台', navigator.platform],
    ['是否触屏', 'ontouchstart' in window ? '✓ 支持' : '✗ 不支持']
  ];
  T.clearEl(info).appendChild(T.kvTable(rows));
}
render();
window.addEventListener('resize', T.debounce(render, 200));
app.appendChild(T.el('p', { text: '窗口尺寸变化时自动刷新。', style: 'color:var(--ink2);font-size:12px' }));
app.appendChild(info);
''')

d('danmaku', '手持弹幕', '手机全屏滚动 LED 弹幕：文字 + 颜色 + 速度（演唱会应援）', js=r'''
var text = T.input('FreeLLM 加油！', { class: 'grow', placeholder: '弹幕文字' });
var speed = T.range(1, 20, 1, 6);
var color = T.color('#FF3B6B');
var bgc = T.color('#000000');
var fs = T.range(40, 200, 5, 90);
var marquee = T.el('div', { style: 'white-space:nowrap;font-weight:900;display:flex;align-items:center;height:200px;overflow:hidden;border-radius:12px;margin:16px 0' });
var inner = T.el('span', { style: 'display:inline-block;white-space:nowrap;padding-left:100%' });
marquee.appendChild(inner);
function render() {
  inner.textContent = text.value || ' ';
  inner.style.color = color.value;
  inner.style.fontSize = fs.value + 'px';
  marquee.style.background = bgc.value;
  inner.style.animation = 'none';
  void inner.offsetWidth;
  inner.style.animation = 'danmaku-scroll ' + (60 / speed.value) + 's linear infinite';
}
var style = document.createElement('style');
style.textContent = '@keyframes danmaku-scroll{from{transform:translateX(0)}to{transform:translateX(-100%)}}';
document.head.appendChild(style);
[text, speed, color, bgc, fs].forEach(function (el) { el.addEventListener('input', render); });
app.appendChild(T.pane([T.field('文字', text)], true));
app.appendChild(T.row([T.el('span', { text: '速度' }), speed, T.el('span', { text: '字号' }), fs]));
app.appendChild(T.row([T.el('span', { text: '文字色' }), color, T.el('span', { text: '背景色' }), bgc,
  T.button('⛶ 全屏播放', function () {
    if (document.fullscreenElement) { document.exitFullscreen(); return; }
    marquee.style.height = '100vh';
    document.documentElement.requestFullscreen().then(function () {}).catch(function () { T.toast('全屏被拒绝，可手动最大化窗口'); });
  })]));
app.appendChild(marquee);
render();
document.addEventListener('fullscreenchange', function () {
  marquee.style.height = document.fullscreenElement ? '100vh' : '200px';
});
''')

d('dead-pixel', '屏幕坏点检测', '全屏纯色循环检测坏点 / 亮斑（红绿蓝白黑）', js=r'''
var overlay = T.el('div', { style: 'display:none;position:fixed;inset:0;z-index:9999;cursor:pointer' });
document.body.appendChild(overlay);
var colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000'];
var idx = 0;
var iv = 0;
var auto = false;
function showColor() {
  overlay.style.background = colors[idx];
}
overlay.addEventListener('click', function () {
  idx = (idx + 1) % colors.length;
  showColor();
});
document.addEventListener('keydown', function (e) {
  if (!overlay.style.display || overlay.style.display === 'none') return;
  if (e.key === 'Escape') exitFull();
  if (e.key === ' ') { e.preventDefault(); toggleAuto(); }
  if (e.key === 'ArrowRight') { idx = (idx + 1) % colors.length; showColor(); }
});
function exitFull() {
  clearInterval(iv);
  auto = false;
  overlay.style.display = 'none';
  if (document.fullscreenElement) document.exitFullscreen();
  startBtn.firstChild.textContent = '⛶ 开始全屏检测';
}
function toggleAuto() {
  auto = !auto;
  clearInterval(iv);
  if (auto) iv = setInterval(function () { idx = (idx + 1) % colors.length; showColor(); }, 1500);
}
var startBtn = T.button('⛶ 开始全屏检测', function () {
  overlay.style.display = 'block';
  idx = 0;
  showColor();
  this.firstChild.textContent = '检测中…（点击 ESC 退出）';
  document.documentElement.requestFullscreen().catch(function () {});
});
app.appendChild(T.row([startBtn, T.button('自动循环切换', toggleAuto)]));
app.appendChild(T.el('p', { text: '检测方法：全屏后依次查看 红绿蓝白黑 五种纯色，出现不发光的黑点=坏点，异常亮点=亮斑。空格=自动循环，→ 手动切换，ESC 退出。', style: 'color:var(--ink2);font-size:12px' }));
app.appendChild(T.el('div', { style: 'display:flex;gap:6px;margin-top:10px' }, colors.map(function (c) {
  return T.el('div', { style: 'width:52px;height:32px;background:' + c + ';border:1px solid var(--line);border-radius:6px', title: c });
})));
''')

d('auto-refresh', '网页定时刷新', '按设定间隔自动刷新页面（iframe 预览或本页刷新）', js=r'''
var interval = T.num(10, { min: 1, max: 3600, style: 'width:90px' });
var unit = T.select([{value:'1',label:'秒'},{value:'60',label:'分钟'}],'1');
var mode = T.select([{value:'self',label:'刷新本页'},{value:'frame',label:'iframe 加载目标网址并定时刷新'}],'frame');
var url = T.input('https://freellm.top', { class: 'grow mono', placeholder: '目标网址（iframe 模式）' });
var frame = T.el('iframe', { sandbox: 'allow-scripts allow-same-origin allow-forms', style: 'width:100%;height:420px;border:1px solid var(--line);border-radius:10px;display:none;background:#fff' });
var status = T.badge('未启动');
var timer = 0;
function start() {
  stop();
  var ms = Math.max(1, +interval.value) * +unit.value * 1000;
  if (mode.value === 'frame') {
    frame.style.display = '';
    frame.src = url.value;
  }
  timer = setInterval(function () {
    if (mode.value === 'self') location.reload();
    else frame.src = url.value;
  }, ms);
  status.textContent = '每 ' + (unit.value === '60' ? interval.value + ' 分钟' : interval.value + ' 秒') + ' 刷新一次';
  status.className = 'badge ok';
}
function stop() {
  if (timer) clearInterval(timer);
  timer = 0;
  status.textContent = '已停止';
  status.className = 'badge';
}
app.appendChild(T.pane([T.field('刷新间隔', interval), T.field('', unit)]));
app.appendChild(T.row([mode, url]));
app.appendChild(T.row([T.button('▶ 启动', start, true), T.button('⏹ 停止', stop), status]));
app.appendChild(frame);
''')

d('todo', '待办事项', '本地待办清单：添加 / 完成 / 删除，数据本地保存', js=r'''
var input = T.input('', { class: 'grow', placeholder: '新待办，回车添加…' });
var list = T.el('div');
var filter = T.select([{value:'all',label:'全部'},{value:'active',label:'未完成'},{value:'done',label:'已完成'}],'all');
var statEl = T.stat('0/0', '完成');
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-todos') || '[]'); } catch (e) {}
function save() { localStorage.setItem('freellm-todos', JSON.stringify(items)); }
function render() {
  T.clearEl(list);
  var show = items.filter(function (it) {
    if (filter.value === 'active') return !it.done;
    if (filter.value === 'done') return it.done;
    return true;
  });
  show.forEach(function (it) {
    var idx = items.indexOf(it);
    var row = T.el('div', { style: 'display:flex;gap:10px;align-items:center;padding:10px 6px;border-bottom:1px solid var(--line)' });
    var cb = T.el('input', { type: 'checkbox' });
    cb.checked = it.done;
    cb.addEventListener('change', function () { it.done = cb.checked; save(); render(); });
    var label = T.el('span', { text: it.text, style: 'flex:1;' + (it.done ? 'text-decoration:line-through;color:var(--ink3)' : '') });
    label.style.cursor = 'pointer';
    label.addEventListener('click', function () { it.done = !it.done; save(); render(); });
    row.appendChild(cb);
    row.appendChild(label);
    row.appendChild(T.button('✕', function () { items.splice(idx, 1); save(); render(); }));
    list.appendChild(row);
  });
  var done = items.filter(function (i) { return i.done; }).length;
  statEl.firstChild.textContent = done + '/' + items.length;
}
input.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && input.value.trim()) {
    items.unshift({ text: input.value.trim(), done: false, ts: Date.now() });
    save();
    input.value = '';
    render();
  }
});
filter.addEventListener('change', render);
app.appendChild(T.row([input, T.button('添加', function () {
  if (input.value.trim()) {
    items.unshift({ text: input.value.trim(), done: false, ts: Date.now() });
    save();
    input.value = '';
    render();
  }
}, true), filter, statEl]));
app.appendChild(list);
render();
app.appendChild(T.row([T.button('清空已完成', function () { items = items.filter(function (i) { return !i.done; }); save(); render(); }),
  T.button('清空全部', function () { if (confirm('确定清空所有待办？')) { items = []; save(); render(); } })]));
''')

d('journal', '日记本', '本地日记：按日期记录与浏览，数据保存在浏览器', js=r'''
var dateIn = T.dateInput(T.today());
var input = T.textarea('今天发生了什么…', true);
input.style.minHeight = '180px';
var list = T.el('div');
var entries = {};
try { entries = JSON.parse(localStorage.getItem('freellm-journal') || '{}'); } catch (e) {}
function save() { localStorage.setItem('freellm-journal', JSON.stringify(entries)); }
function loadDate() {
  input.value = entries[dateIn.value] || '';
}
function saveDate() {
  if (input.value.trim()) entries[dateIn.value] = input.value;
  else delete entries[dateIn.value];
  save();
  renderList();
}
function renderList() {
  T.clearEl(list);
  var keys = Object.keys(entries).sort().reverse();
  if (!keys.length) { list.appendChild(T.el('p', { text: '还没有日记。', style: 'color:var(--ink3)' })); return; }
  keys.slice(0, 20).forEach(function (k) {
    var row = T.el('div', { style: 'display:flex;gap:12px;align-items:baseline;padding:8px 4px;border-bottom:1px solid var(--line);cursor:pointer' });
    row.appendChild(T.el('b', { text: k, style: 'font-family:var(--font-mono);font-size:13px' }));
    row.appendChild(T.el('span', { text: entries[k].replace(/\n/g, ' ').slice(0, 50) + '…', style: 'flex:1;color:var(--ink2);font-size:13px;overflow:hidden;white-space:nowrap' }));
    row.addEventListener('click', function () { dateIn.value = k; loadDate(); });
    list.appendChild(row);
  });
}
dateIn.addEventListener('change', loadDate);
input.addEventListener('input', T.debounce(saveDate, 600));
app.appendChild(T.row([T.el('span', { text: '日期' }), dateIn, T.el('span', { text: Object.keys(entries).length + ' 篇' })]));
app.appendChild(input);
app.appendChild(T.el('span', { text: '历史日记（点击载入）', class: 'field' }));
app.appendChild(list);
loadDate();
renderList();
''')

d('notes', '笔记应用', '本地笔记：多笔记管理 + 搜索，数据保存在浏览器', js=r'''
var titleIn = T.input('', { class: 'grow', placeholder: '笔记标题' });
var bodyIn = T.textarea('笔记内容…', true);
bodyIn.style.minHeight = '160px';
var search = T.input('', { class: 'grow', placeholder: '搜索笔记…' });
var list = T.el('div');
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-notes') || '[]'); } catch (e) {}
var editing = -1;
function save() { localStorage.setItem('freellm-notes', JSON.stringify(items)); }
function render() {
  T.clearEl(list);
  var q = search.value.trim().toLowerCase();
  items.forEach(function (n, i) {
    if (q && !(n.title + n.body).toLowerCase().includes(q)) return;
    var card = T.el('div', { style: 'border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:8px;background:var(--surface);cursor:pointer' });
    var head = T.row([T.el('b', { text: n.title || '（无标题）' }), T.el('span', { text: new Date(n.ts).toLocaleDateString('zh-CN'), style: 'color:var(--ink3);font-size:12px' })]);
    head.style.marginBottom = '4px';
    card.appendChild(head);
    card.appendChild(T.el('div', { text: n.body.slice(0, 80) + (n.body.length > 80 ? '…' : ''), style: 'color:var(--ink2);font-size:13px' }));
    var actions = T.row([T.button('编辑', function () {
      editing = i;
      titleIn.value = n.title;
      bodyIn.value = n.body;
      saveBtn.firstChild.textContent = '更新笔记';
    }), T.button('删除', function () { items.splice(i, 1); save(); render(); })]);
    actions.style.marginTop = '8px';
    card.appendChild(actions);
    list.appendChild(card);
  });
  if (!list.children.length) list.appendChild(T.el('p', { text: q ? '无匹配笔记' : '暂无笔记', style: 'color:var(--ink3)' }));
}
var saveBtn = T.button('保存笔记', function () {
  if (!titleIn.value && !bodyIn.value.trim()) { T.toast('请填写内容'); return; }
  if (editing >= 0) {
    items[editing].title = titleIn.value;
    items[editing].body = bodyIn.value;
    editing = -1;
    saveBtn.firstChild.textContent = '保存笔记';
  } else {
    items.unshift({ title: titleIn.value, body: bodyIn.value, ts: Date.now() });
  }
  save();
  titleIn.value = '';
  bodyIn.value = '';
  render();
}, true);
search.addEventListener('input', T.debounce(render, 200));
app.appendChild(T.row([titleIn, saveBtn]));
app.appendChild(bodyIn);
app.appendChild(T.row([search]));
app.appendChild(list);
render();
''')

d('habit', '习惯追踪', '每日习惯打卡：自定义习惯 + 7 天打卡墙 + 连续天数', js=r'''
var input = T.input('', { class: 'grow', placeholder: '新习惯，如：阅读 30 分钟' });
var box = T.el('div');
var habits = [];
try { habits = JSON.parse(localStorage.getItem('freellm-habits') || '[]'); } catch (e) {}
function save() { localStorage.setItem('freellm-habits', JSON.stringify(habits)); }
function todayKey() { return T.today(); }
function last7() {
  var days = [];
  for (var i = 6; i >= 0; i--) {
    var d = new Date(Date.now() - i * 86400000);
    days.push(T.fmtDate(d));
  }
  return days;
}
function streak(checks) {
  var s = 0;
  var d = new Date();
  while (checks.includes(T.fmtDate(d))) {
    s++;
    d.setDate(d.getDate() - 1);
  }
  return s;
}
function render() {
  T.clearEl(box);
  var days = last7();
  habits.forEach(function (h, hi) {
    var card = T.el('div', { style: 'border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:10px;background:var(--surface)' });
    var head = T.row([T.el('b', { text: h.name }),
      T.badge('连续 ' + streak(h.checks) + ' 天', streak(h.checks) ? 'ok' : ''),
      T.el('span', { style: 'flex:1' }),
      T.button('✕', function () { habits.splice(hi, 1); save(); render(); })]);
    head.style.marginBottom = '10px';
    card.appendChild(head);
    var row = T.el('div', { style: 'display:flex;gap:6px' });
    days.forEach(function (d) {
      var done = h.checks.includes(d);
      var cell = T.el('div', { text: done ? '✓' : T.fmtDate(new Date(d)).slice(8), style: 'flex:1;aspect-ratio:1;display:flex;align-items:center;justify-content:center;border-radius:8px;cursor:pointer;font-weight:700;background:' + (done ? 'var(--accent)' : 'var(--surface-soft)') + ';color:' + (done ? '#fff' : 'var(--ink3)') + ';border:1px solid var(--line)', title: d });
      cell.addEventListener('click', function () {
        if (done) h.checks = h.checks.filter(function (x) { return x !== d; });
        else h.checks.push(d);
        save();
        render();
      });
      row.appendChild(cell);
    });
    card.appendChild(row);
    box.appendChild(card);
  });
  if (!habits.length) box.appendChild(T.el('p', { text: '添加第一个习惯开始打卡。', style: 'color:var(--ink3)' }));
}
input.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && input.value.trim()) {
    habits.push({ name: input.value.trim(), checks: [] });
    save();
    input.value = '';
    render();
  }
});
app.appendChild(T.row([input]));
app.appendChild(box);
app.appendChild(T.el('p', { text: '点击日期格子打卡/取消。连续天数按今天往前连续计算。', style: 'color:var(--ink2);font-size:12px' }));
render();
''')

d('expense', '记账本', '简单记账：收入 / 支出分类，本地保存 + 月度汇总', js=r'''
var amount = T.num(0, { min: 0, step: 0.01, style: 'width:110px' });
var type = T.select([{value:'out',label:'支出'},{value:'in',label:'收入'}],'out');
var cat = T.select(['餐饮', '交通', '购物', '居住', '娱乐', '医疗', '教育', '工资', '其他'].map(function (c) { return { value: c, label: c }; }), '餐饮');
var noteIn = T.input('', { class: 'grow', placeholder: '备注（可选）' });
var list = T.el('div');
var monthStat = T.el('div', { class: 'row' });
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-expense') || '[]'); } catch (e) {}
function save() { localStorage.setItem('freellm-expense', JSON.stringify(items)); }
function render() {
  T.clearEl(list);
  var thisMonth = T.today().slice(0, 7);
  var monthItems = items.filter(function (it) { return it.date.startsWith(thisMonth); });
  var income = 0, outcome = 0;
  monthItems.forEach(function (it) { it.type === 'in' ? income += it.amount : outcome += it.amount; });
  T.clearEl(monthStat);
  monthStat.appendChild(T.stat('¥ ' + income.toFixed(2), '本月收入'));
  monthStat.appendChild(T.stat('¥ ' + outcome.toFixed(2), '本月支出'));
  monthStat.appendChild(T.stat('¥ ' + (income - outcome).toFixed(2), '结余'));
  var byCat = {};
  monthItems.forEach(function (it) { if (it.type === 'out') byCat[it.cat] = (byCat[it.cat] || 0) + it.amount; });
  var catRows = Object.keys(byCat).map(function (k) { return [k, '¥ ' + byCat[k].toFixed(2), '█'.repeat(Math.ceil(byCat[k] / Math.max(1, outcome) * 20))]; })
    .sort(function (a, b) { return b[1].slice(2) > a[1].slice(2) ? -1 : 1; });
  if (catRows.length) {
    list.appendChild(T.el('span', { text: '本月支出分类', class: 'field' }));
    list.appendChild(T.refTable(['分类', '金额', '占比'], catRows));
  }
  list.appendChild(T.el('span', { text: '最近记录', class: 'field' }));
  items.slice(0, 20).forEach(function (it, i) {
    var row = T.el('div', { style: 'display:flex;gap:10px;align-items:center;padding:8px 4px;border-bottom:1px solid var(--line)' });
    row.appendChild(T.el('span', { text: it.date.slice(5), style: 'color:var(--ink3);font-family:var(--font-mono);font-size:12px' }));
    row.appendChild(T.el('span', { text: it.cat + (it.note ? ' · ' + it.note : ''), style: 'flex:1;font-size:13px' }));
    row.appendChild(T.el('b', { text: (it.type === 'in' ? '+' : '-') + it.amount.toFixed(2), style: 'color:' + (it.type === 'in' ? 'var(--ok-text)' : 'var(--err)') + ';font-family:var(--font-mono)' }));
    row.appendChild(T.button('✕', function () { items.splice(i, 1); save(); render(); }));
    list.appendChild(row);
  });
  if (!items.length) list.appendChild(T.el('p', { text: '添加第一笔记录。', style: 'color:var(--ink3)' }));
}
app.appendChild(monthStat);
app.appendChild(T.row([amount, type, cat, noteIn, T.button('记一笔', function () {
  if (!+amount.value) { T.toast('请输入金额'); return; }
  items.unshift({ date: T.today(), type: type.value, cat: cat.value, amount: +amount.value, note: noteIn.value });
  save();
  amount.value = 0;
  noteIn.value = '';
  render();
}, true)]));
app.appendChild(list);
render();
''')

d('mood', '心情追踪', '每日心情记录：表情打分 + 备注 + 近 14 天心情曲线', js=r'''
var MOODS = [['😞', 1], ['🙁', 2], ['😐', 3], ['🙂', 4], ['😄', 5]];
var note = T.input('', { class: 'grow', placeholder: '今天想记录一句话（可选）' });
var status = T.badge('—');
var chart = T.el('div', { style: 'display:flex;gap:4px;align-items:flex-end;height:120px;margin:18px 0' });
var list = T.el('div');
var data = {};
try { data = JSON.parse(localStorage.getItem('freellm-mood') || '{}'); } catch (e) {}
function save() { localStorage.setItem('freellm-mood', JSON.stringify(data)); }
function render() {
  T.clearEl(chart);
  var days = [];
  for (var i = 13; i >= 0; i--) days.push(T.fmtDate(new Date(Date.now() - i * 86400000)));
  days.forEach(function (d) {
    var v = data[d] ? data[d].score : 0;
    var col = T.el('div', { style: 'flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:2px', title: d + (data[d] ? '：' + MOODS[v - 1][0] + ' ' + (data[d].note || '') : '') });
    var barH = v ? v * 18 : 4;
    col.appendChild(T.el('div', { text: v ? MOODS[v - 1][0] : '·', style: 'font-size:' + (v ? 20 : 12) + 'px;opacity:' + (v ? 1 : 0.3) }));
    col.appendChild(T.el('div', { style: 'width:100%;height:' + barH + 'px;background:' + (v ? 'var(--accent)' : 'var(--line)') + ';border-radius:3px' }));
    col.appendChild(T.el('div', { text: d.slice(8), style: 'font-size:9px;color:var(--ink3)' }));
    chart.appendChild(col);
  });
  T.clearEl(list);
  var keys = Object.keys(data).sort().reverse();
  keys.slice(0, 10).forEach(function (k) {
    var row = T.el('div', { style: 'display:flex;gap:10px;align-items:center;padding:6px 4px;border-bottom:1px solid var(--line)' });
    row.appendChild(T.el('span', { text: data[k].score + ' ' + MOODS[data[k].score - 1][0] }));
    row.appendChild(T.el('b', { text: k, style: 'font-family:var(--font-mono);font-size:12px' }));
    row.appendChild(T.el('span', { text: data[k].note || '', style: 'flex:1;color:var(--ink2);font-size:13px' }));
    list.appendChild(row);
  });
}
function setMood(score) {
  data[T.today()] = { score: score, note: note.value };
  save();
  status.textContent = '已记录今天心情：' + MOODS[score - 1][0];
  status.className = 'badge ok';
  render();
}
var moodRow = T.el('div', { class: 'row', style: 'justify-content:center;gap:14px' });
MOODS.forEach(function (m) {
  var b = T.button(m[0], function () { setMood(m[1]); });
  b.style.cssText += 'font-size:30px;padding:8px 14px;justify-content:center';
  moodRow.appendChild(b);
});
app.appendChild(moodRow);
app.appendChild(T.row([note, T.button('保存备注并打分后自动带上', function () {}, true)]));
app.appendChild(T.el('span', { text: '近 14 天', class: 'field' }));
app.appendChild(chart);
app.appendChild(list);
render();
''')

d('water', '喝水提醒', '每日饮水量追踪：目标杯数 + 定时提醒 + 今日进度', js=r'''
var goal = T.num(8, { min: 1, max: 30, style: 'width:70px' });
var cupMl = T.num(250, { min: 50, style: 'width:80px' });
var remindMin = T.num(60, { min: 5, style: 'width:80px' });
var status = T.badge('提醒未开启');
var today = T.today();
var data = {};
try { data = JSON.parse(localStorage.getItem('freellm-water') || '{}'); } catch (e) {}
if (data.date !== today) data = { date: today, cups: 0 };
function save() { localStorage.setItem('freellm-water', JSON.stringify(data)); }
var cups = T.el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:22px 0' });
var progress = T.stat('0', '今日杯数');
var mlEl = T.stat('0 ml', '累计');
var timer = 0;
function render() {
  T.clearEl(cups);
  var total = Math.max(goal.value, data.cups);
  for (var i = 0; i < total; i++) {
    var filled = i < data.cups;
    cups.appendChild(T.el('div', { text: filled ? '💧' : '🥛', style: 'font-size:34px;cursor:pointer;opacity:' + (filled ? 1 : 0.35) + ';transition:all .2s', title: '第 ' + (i + 1) + ' 杯' }));
  }
  progress.firstChild.textContent = data.cups + '/' + goal.value;
  mlEl.firstChild.textContent = (data.cups * +cupMl.value).toLocaleString() + ' ml';
}
function drink() {
  data.cups++;
  save();
  render();
  T.toast('💧 +1 杯，继续保持！');
  if (data.cups === +goal.value) {
    status.textContent = '🎉 今日目标达成！';
    status.className = 'badge ok';
  }
}
function toggleRemind() {
  if (timer) {
    clearInterval(timer);
    timer = 0;
    status.textContent = '提醒已关闭';
    status.className = 'badge';
    return;
  }
  timer = setInterval(function () {
    if (data.cups < +goal.value) {
      T.toast('⏰ 该喝杯水啦（今日 ' + data.cups + '/' + goal.value + ' 杯）');
      try {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator(), g = ctx.createGain();
        osc.connect(g).connect(ctx.destination);
        osc.frequency.value = 880; g.gain.value = 0.2;
        osc.start(); setTimeout(function () { osc.stop(); ctx.close(); }, 300);
      } catch (e) {}
    }
  }, +remindMin.value * 60000);
  status.textContent = '每 ' + remindMin.value + ' 分钟提醒一次';
  status.className = 'badge ok';
}
app.appendChild(T.row([T.el('span', { text: '目标(杯)' }), goal, T.el('span', { text: '每杯(ml)' }), cupMl]));
app.appendChild(cups);
app.appendChild(T.row([progress, mlEl]));
app.appendChild(T.row([T.button('💧 喝一杯', drink, true), T.button('撤销一杯', function () { if (data.cups > 0) { data.cups--; save(); render(); } }),
  T.el('span', { text: '提醒间隔(分)' }), remindMin, T.button('开启提醒', toggleRemind), status]));
goal.addEventListener('input', render);
render();
''')

d('stand', '站立提醒', '久坐提醒：定时提醒起身活动，可统计今日次数', js=r'''
var interval = T.num(45, { min: 5, max: 180, style: 'width:80px' });
var status = T.badge('未开启');
var countEl = T.stat(0, '今日已站');
var lastEl = T.el('span', { style: 'color:var(--ink2);font-size:12px' });
var timer = 0;
var today = T.today();
var data = {};
try { data = JSON.parse(localStorage.getItem('freellm-stand') || '{}'); } catch (e) {}
if (data.date !== today) data = { date: today, count: 0 };
countEl.firstChild.textContent = data.count;
function save() { localStorage.setItem('freellm-stand', JSON.stringify(data)); }
function beep() {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator(), g = ctx.createGain();
    osc.connect(g).connect(ctx.destination);
    osc.frequency.value = 660; g.gain.value = 0.3;
    osc.start();
    var n = 0;
    var iv = setInterval(function () { n++; if (n > 5) { clearInterval(iv); osc.stop(); ctx.close(); return; } osc.frequency.value = n % 2 ? 550 : 750; }, 260);
  } catch (e) {}
}
function start() {
  if (timer) clearInterval(timer);
  timer = setInterval(function () {
    beep();
    T.toast('🧍 起身活动一下！已经坐了 ' + interval.value + ' 分钟');
    alert('🧍 久坐提醒：起身活动 3-5 分钟');
  }, +interval.value * 60000);
  status.textContent = '每 ' + interval.value + ' 分钟提醒';
  status.className = 'badge ok';
  status._on = true;
  startBtn.firstChild.textContent = '⏸ 暂停提醒';
}
function stopT() {
  clearInterval(timer);
  timer = 0;
  status.textContent = '已暂停';
  status.className = 'badge';
  startBtn.firstChild.textContent = '▶ 开始提醒';
}
var startBtn = T.button('▶ 开始提醒', function () { timer ? stopT() : start(); }, true);
app.appendChild(T.row([T.el('span', { text: '间隔(分)' }), interval, startBtn, status]));
app.appendChild(T.row([countEl, T.button('✅ 我站起来了', function () {
  data.count++;
  countEl.firstChild.textContent = data.count;
  save();
  T.toast('记录成功，棒！');
  if (timer) { clearInterval(timer); start(); }
}), lastEl]));
app.appendChild(T.el('p', { text: '建议每坐 45-60 分钟起身活动 3 分钟。提醒依赖页面保持打开。', style: 'color:var(--ink2);font-size:12px' }));
''')

d('timer-app', '正计时器', '跑表模式正计时：开始 / 暂停 / 目标提醒', js=r'''
var big = T.el('div', { text: '00:00:00', style: 'font:400 76px/1.2 var(--font-serif);text-align:center;margin:28px 0;font-variant-numeric:tabular-nums' });
var goalMin = T.num(30, { min: 1, style: 'width:80px' });
var status = T.badge('未开始');
var running = false, startAt = 0, elapsed = 0, raf = 0, notified = false;
function fmt(ms) {
  var h = Math.floor(ms / 3600000), m = Math.floor(ms % 3600000 / 60000), s = Math.floor(ms % 60000 / 1000);
  return T.pad2(h) + ':' + T.pad2(m) + ':' + T.pad2(s);
}
function tickFn() {
  var ms = elapsed + (running ? Date.now() - startAt : 0);
  big.textContent = fmt(ms);
  if (!notified && ms >= (+goalMin.value || 30) * 60000) {
    notified = true;
    status.textContent = '🎯 已达目标时长';
    status.className = 'badge ok';
    T.toast('🎯 目标时长达成');
  }
  if (running) raf = requestAnimationFrame(tickFn);
}
app.appendChild(big);
app.appendChild(T.row([T.el('span', { text: '目标(分)' }), goalMin, status]));
app.appendChild(T.row([
  T.button('开始', function () { if (running) return; running = true; notified = false; startAt = Date.now(); tickFn(); }, true),
  T.button('暂停', function () { if (!running) return; elapsed += Date.now() - startAt; running = false; cancelAnimationFrame(raf); big.textContent = fmt(elapsed); }),
  T.button('清零', function () { running = false; cancelAnimationFrame(raf); elapsed = 0; notified = false; big.textContent = '00:00:00'; status.textContent = '未开始'; status.className = 'badge'; })
]));
''')

d('stopwatch-adv', '秒表增强', '分段计次秒表：单圈 / 累计时间 + 导出 CSV', js=r'''
var big = T.el('div', { text: '00:00:00.00', style: 'font:400 56px/1.3 var(--font-serif);text-align:center;margin:24px 0;font-variant-numeric:tabular-nums' });
var laps = [];
var lapList = T.el('div', { style: 'max-height:260px;overflow:auto' });
var running = false, startAt = 0, elapsed = 0, raf = 0;
function fmt(ms) {
  var h = Math.floor(ms / 3600000), m = Math.floor(ms % 3600000 / 60000), s = Math.floor(ms % 60000 / 1000), c = Math.floor(ms % 1000 / 10);
  return T.pad2(h) + ':' + T.pad2(m) + ':' + T.pad2(s) + '.' + T.pad2(c);
}
function tickFn() {
  big.textContent = fmt(elapsed + (running ? Date.now() - startAt : 0));
  if (running) raf = requestAnimationFrame(tickFn);
}
function lap() {
  var total = elapsed + (running ? Date.now() - startAt : 0);
  var prev = laps.length ? laps[laps.length - 1].total : 0;
  laps.push({ n: laps.length + 1, lap: total - prev, total: total });
  renderLaps();
}
function renderLaps() {
  T.clearEl(lapList);
  if (!laps.length) return;
  var rows = laps.slice().reverse().map(function (l) {
    return [String(l.n), fmt(l.lap), fmt(l.total)];
  });
  lapList.appendChild(T.refTable(['#', '单圈', '累计'], rows));
}
app.appendChild(big);
app.appendChild(T.row([
  T.button('开始', function () { if (running) return; running = true; startAt = Date.now(); tickFn(); }, true),
  T.button('暂停', function () { if (!running) return; elapsed += Date.now() - startAt; running = false; cancelAnimationFrame(raf); big.textContent = fmt(elapsed); }),
  T.button('计次', lap),
  T.button('复位', function () { running = false; cancelAnimationFrame(raf); elapsed = 0; laps = []; big.textContent = '00:00:00.00'; renderLaps(); }),
  T.button('导出 CSV', function () {
    if (!laps.length) { T.toast('暂无计次数据'); return; }
    var csv = '圈数,单圈时间,累计时间\n' + laps.map(function (l) { return l.n + ',' + fmt(l.lap) + ',' + fmt(l.total); }).join('\n');
    T.download('stopwatch.csv', csv, 'text/csv');
  })
]));
app.appendChild(lapList);
''')

d('countdown-adv', '倒计时增强', '多倒计时管理：创建多个目标 + 提醒音 + 本地保存', js=r'''
var nameIn = T.input('', { class: 'grow', placeholder: '倒计时名称' });
var dateIn = T.el('input', { type: 'datetime-local' });
var list = T.el('div');
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-countdown-adv') || '[]'); } catch (e) {}
items.forEach(function (it) { it.alerted = false; });
function save() { localStorage.setItem('freellm-countdown-adv', JSON.stringify(items)); }
function beep() {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator(), g = ctx.createGain();
    osc.connect(g).connect(ctx.destination);
    osc.frequency.value = 880; g.gain.value = 0.25;
    osc.start();
    var n = 0;
    var iv = setInterval(function () { n++; if (n > 8) { clearInterval(iv); osc.stop(); ctx.close(); return; } osc.frequency.value = n % 2 ? 660 : 880; }, 240);
  } catch (e) {}
}
setInterval(function () {
  items.forEach(function (it) {
    if (!it.alerted && it.target <= Date.now()) {
      it.alerted = true;
      save();
      beep();
      T.toast('⏰「' + it.name + '」时间到！');
    }
  });
}, 1000);
function render() {
  T.clearEl(list);
  if (!items.length) { list.appendChild(T.el('p', { text: '暂无倒计时。', style: 'color:var(--ink3)' })); return; }
  items.sort(function (a, b) { return a.target - b.target; });
  items.forEach(function (it, idx) {
    var diff = it.target - Date.now();
    var row = T.el('div', { style: 'display:flex;gap:12px;align-items:center;padding:12px 6px;border-bottom:1px solid var(--line);flex-wrap:wrap' });
    row.appendChild(T.el('b', { text: it.name, style: 'min-width:110px' }));
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
    row.appendChild(T.button('✕', function () { items.splice(idx, 1); save(); render(); }));
    list.appendChild(row);
  });
}
setInterval(render, 1000);
app.appendChild(T.row([nameIn, dateIn, T.button('添加', function () {
  if (!nameIn.value || !dateIn.value) { T.toast('请填写名称与时间'); return; }
  items.push({ name: nameIn.value, target: new Date(dateIn.value).getTime(), alerted: false });
  save();
  render();
}, true)]));
app.appendChild(list);
render();
''')

d('bookmark', '书签管理', '常用工具书签：本地保存 / 搜索 / 一键打开', js=r'''
var titleIn = T.input('', { class: 'grow', placeholder: '名称' });
var urlIn = T.input('', { class: 'grow mono', placeholder: 'https://…' });
var search = T.input('', { class: 'grow', placeholder: '搜索书签…' });
var list = T.el('div');
var items = [];
try { items = JSON.parse(localStorage.getItem('freellm-bookmarks') || '[]'); } catch (e) {}
items.push({ name: 'FreeLLM 工具合集', url: 'https://freellm.top/tools/', builtin: true });
function save() { localStorage.setItem('freellm-bookmarks', JSON.stringify(items.filter(function (i) { return !i.builtin; }))); }
function render() {
  T.clearEl(list);
  var q = search.value.trim().toLowerCase();
  items.forEach(function (b, i) {
    if (q && !b.name.toLowerCase().includes(q) && !b.url.toLowerCase().includes(q)) return;
    var row = T.el('div', { style: 'display:flex;gap:10px;align-items:center;padding:9px 4px;border-bottom:1px solid var(--line)' });
    row.appendChild(T.el('b', { text: b.name }));
    row.appendChild(T.el('span', { text: b.url, style: 'flex:1;color:var(--ink3);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap' }));
    row.appendChild(T.button('打开', function () { window.open(b.url, '_blank'); }, true));
    if (!b.builtin) row.appendChild(T.button('✕', function () { items.splice(i, 1); save(); render(); }));
    list.appendChild(row);
  });
  if (!list.children.length) list.appendChild(T.el('p', { text: q ? '无匹配' : '暂无书签', style: 'color:var(--ink3)' }));
}
search.addEventListener('input', T.debounce(render, 200));
app.appendChild(T.row([titleIn, urlIn, T.button('添加书签', function () {
  if (!titleIn.value || !urlIn.value) { T.toast('请填写名称与网址'); return; }
  var u = urlIn.value;
  if (!/^https?:\/\//.test(u)) u = 'https://' + u;
  items.push({ name: titleIn.value, url: u });
  save();
  titleIn.value = '';
  urlIn.value = '';
  render();
}, true)]));
app.appendChild(T.row([search]));
app.appendChild(list);
render();
''')

d('theme-switch', '主题切换', '亮色 / 暗色 / 自动跟随系统，与全站设置同步', js=r'''
var cur = 'auto';
try { cur = JSON.parse(localStorage.getItem('freellm-settings') || '{}').theme || 'auto'; } catch (e) {}
var preview = T.el('div', { style: 'height:140px;border-radius:12px;border:1px solid var(--line);margin:14px 0;display:flex;flex-direction:column;gap:8px;padding:16px' });
var apply = function (mode) {
  cur = mode;
  var settings = {};
  try { settings = JSON.parse(localStorage.getItem('freellm-settings') || '{}'); } catch (e) {}
  settings.theme = mode;
  localStorage.setItem('freellm-settings', JSON.stringify(settings));
  var dark = mode === 'dark' || (mode === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
  preview.style.background = dark ? '#181B20' : '#FFFFFF';
  preview.style.color = dark ? '#ECEAE6' : '#2F3437';
  T.clearEl(preview);
  preview.appendChild(T.el('div', { text: '标题文字 Heading', style: 'font:600 20px sans-serif' }));
  preview.appendChild(T.el('div', { text: '正文内容 Body text — 当前模式：' + (mode === 'auto' ? '自动（跟随系统 ' + (dark ? '暗' : '亮') + '）' : mode === 'dark' ? '暗色' : '亮色'), style: 'font-size:13px;opacity:.7' }));
  preview.appendChild(T.el('button', { text: '按钮 Button', style: 'padding:6px 14px;border-radius:6px;border:1px solid ' + (dark ? '#26292F' : '#EAEAEA') + ';background:' + (dark ? '#0E2533' : '#E9EEFF') + ';color:' + (dark ? '#7BC0E5' : '#1744E8') }));
  T.toast('已切换：' + (mode === 'auto' ? '自动' : mode === 'dark' ? '暗色' : '亮色'));
};
apply(cur);
var row = T.el('div', { class: 'row', style: 'justify-content:center;gap:12px' });
[['auto', '🌗 自动'], ['light', '☀️ 亮色'], ['dark', '🌙 暗色']].forEach(function (m) {
  row.appendChild(T.button(m[1] + (cur === m[0] ? ' ✓' : ''), function () { apply(m[0]); render(); }));
});
function render() {
  T.clearEl(row);
  [['auto', '🌗 自动'], ['light', '☀️ 亮色'], ['dark', '🌙 暗色']].forEach(function (m) {
    row.appendChild(T.button(m[1] + (cur === m[0] ? ' ✓' : ''), function () { apply(m[0]); render(); }));
  });
}
render();
app.appendChild(row);
app.appendChild(preview);
app.appendChild(T.msg('设置保存后，工具集线器与各工具页会读取同一配置。', ''));
''')

d('lang-switch', '语言切换', '界面语言偏好设置（中 / 英），供支持多语言的页面读取', js=r'''
var cur = 'zh';
try { cur = JSON.parse(localStorage.getItem('freellm-settings') || '{}').lang || 'zh'; } catch (e) {}
var DICT = {
  greeting: { zh: '你好，欢迎使用 FreeLLM 工具！', en: 'Hello, welcome to FreeLLM Tools!' },
  search: { zh: '搜索工具…', en: 'Search tools…' },
  favorites: { zh: '我的收藏', en: 'My Favorites' },
  all: { zh: '全部', en: 'All' },
  copy: { zh: '复制', en: 'Copy' },
  download: { zh: '下载', en: 'Download' }
};
var preview = T.el('div', { class: 'output', style: 'min-height:140px;font-family:var(--font-sans)' });
function render() {
  var lines = Object.keys(DICT).map(function (k) {
    return k + ': ' + DICT[k][cur] + (cur === 'zh' ? '' : '');
  });
  preview.textContent = lines.join('\n') + '\n\n当前语言: ' + (cur === 'zh' ? '中文 (zh-CN)' : 'English (en)');
}
render();
var row = T.el('div', { class: 'row', style: 'justify-content:center;gap:12px' });
function renderBtns() {
  T.clearEl(row);
  [['zh', '🇨🇳 中文'], ['en', '🇺🇸 English']].forEach(function (m) {
    row.appendChild(T.button(m[1] + (cur === m[0] ? ' ✓' : ''), function () {
      cur = m[0];
      var settings = {};
      try { settings = JSON.parse(localStorage.getItem('freellm-settings') || '{}'); } catch (e) {}
      settings.lang = cur;
      localStorage.setItem('freellm-settings', JSON.stringify(settings));
      T.toast('Language: ' + (cur === 'zh' ? '中文' : 'English'));
      renderBtns();
      render();
    }));
  });
}
renderBtns();
app.appendChild(row);
app.appendChild(preview);
app.appendChild(T.msg('该设置存储在 freellm-settings.lang，供页面级双语支持读取；工具站当前主体为中文。', ''));
''')

d('layout-toggle', '布局切换', '网格 / 列表布局预览切换（偏好保存到本地）', js=r'''
var cur = 'grid';
try { cur = JSON.parse(localStorage.getItem('freellm-settings') || '{}').layout || 'grid'; } catch (e) {}
var demo = T.el('div', { style: 'margin:14px 0' });
var ITEMS = ['Base64 编解码', 'JSON 格式化', 'UUID 生成', '正则测试', '时间戳转换', '二维码生成'];
function render() {
  T.clearEl(demo);
  if (cur === 'grid') {
    demo.style.display = 'grid';
    demo.style.gridTemplateColumns = 'repeat(auto-fill, minmax(180px, 1fr))';
    demo.style.gap = '10px';
    ITEMS.forEach(function (it) {
      demo.appendChild(T.el('div', { text: it, style: 'border:1px solid var(--line);border-radius:10px;padding:20px 12px;text-align:center;background:var(--surface)' }));
    });
  } else {
    demo.style.display = '';
    ITEMS.forEach(function (it) {
      demo.appendChild(T.el('div', { text: it + '  —  工具描述占位文本', style: 'border-bottom:1px solid var(--line);padding:12px 4px;background:var(--surface)' }));
    });
  }
}
render();
var row = T.el('div', { class: 'row' });
function renderBtns() {
  T.clearEl(row);
  [['grid', '🔲 网格'], ['list', '☰ 列表']].forEach(function (m) {
    row.appendChild(T.button(m[1] + (cur === m[0] ? ' ✓' : ''), function () {
      cur = m[0];
      var settings = {};
      try { settings = JSON.parse(localStorage.getItem('freellm-settings') || '{}'); } catch (e) {}
      settings.layout = cur;
      localStorage.setItem('freellm-settings', JSON.stringify(settings));
      renderBtns();
      render();
    }));
  });
}
renderBtns();
app.appendChild(row);
app.appendChild(demo);
''')

d('font-switch', '字体切换', '切换界面字体偏好：系统 / 衬线 / 等宽 / 圆体', js=r'''
var FONTS = {
  system: { label: '系统默认（推荐）', stack: 'system-ui, -apple-system, sans-serif' },
  serif: { label: '衬线 Serif', stack: 'Georgia, "Noto Serif SC", serif' },
  mono: { label: '等宽 Mono', stack: 'ui-monospace, "JetBrains Mono", Consolas, monospace' },
  rounded: { label: '圆体 Rounded', stack: '"Yuanti SC", "PingFang SC", "Comic Sans MS", sans-serif' }
};
var cur = 'system';
try { cur = JSON.parse(localStorage.getItem('freellm-settings') || '{}').font || 'system'; } catch (e) {}
var preview = T.el('div', { class: 'output', style: 'min-height:120px;font-family:var(--font-sans);line-height:2' });
function render() {
  T.clearEl(preview);
  preview.style.fontFamily = FONTS[cur].stack;
  preview.appendChild(T.el('div', { text: '永和九年，岁在癸丑。The quick brown fox 0123456789', style: 'font-size:17px' }));
  preview.appendChild(T.el('div', { text: '当前字体：' + FONTS[cur].label, style: 'font-size:12px;color:var(--ink3)' }));
}
render();
var row = T.el('div', { class: 'row' });
function renderBtns() {
  T.clearEl(row);
  Object.keys(FONTS).forEach(function (k) {
    row.appendChild(T.button(FONTS[k].label + (cur === k ? ' ✓' : ''), function () {
      cur = k;
      var settings = {};
      try { settings = JSON.parse(localStorage.getItem('freellm-settings') || '{}'); } catch (e) {}
      settings.font = cur;
      localStorage.setItem('freellm-settings', JSON.stringify(settings));
      renderBtns();
      render();
    }));
  });
}
renderBtns();
app.appendChild(row);
app.appendChild(preview);
''')

d('accessibility', '无障碍设置', '字体大小 / 高对比度 / 减少动画等无障碍偏好', js=r'''
var settings = {};
try { settings = JSON.parse(localStorage.getItem('freellm-a11y') || '{}'); } catch (e) {}
var fontSize = T.range(80, 160, 10, settings.fontSize || 100);
var fontLabel = T.el('b', { text: (settings.fontSize || 100) + '%' });
var contrast = T.check('高对比度模式', settings.contrast);
var reduceMotion = T.check('减少动画', settings.reduceMotion);
var biggerCursor = T.check('大号光标', settings.biggerCursor);
var preview = T.el('div', { class: 'output', style: 'min-height:120px;font-family:var(--font-sans);line-height:1.9;transition:all .2s' });
function apply() {
  var fs = +fontSize.value;
  fontLabel.textContent = fs + '%';
  preview.style.fontSize = 14 * fs / 100 + 'px';
  if (contrast._input.checked) {
    preview.style.background = '#000';
    preview.style.color = '#FFF';
  } else {
    preview.style.background = '';
    preview.style.color = '';
  }
  if (reduceMotion._input.checked) preview.style.transition = 'none';
  else preview.style.transition = 'all .2s';
  preview.style.cursor = biggerCursor._input.checked ? 'url("data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2232%22 height=%2232%22><circle cx=%2210%22 cy=%2210%22 r=%228%22 fill=%22blue%22/></svg>") 4 4, auto' : '';
  preview.innerHTML = '<b>无障碍示例文本 Accessibility Sample</b><br>这是一段用于预览无障碍设置的正文。The quick brown fox jumps over the lazy dog.<br><button style="padding:6px 16px;margin-top:8px">示例按钮</button>';
}
function saveApply() {
  settings = { fontSize: +fontSize.value, contrast: contrast._input.checked, reduceMotion: reduceMotion._input.checked, biggerCursor: biggerCursor._input.checked };
  localStorage.setItem('freellm-a11y', JSON.stringify(settings));
  apply();
}
[fontSize, contrast._input, reduceMotion._input, biggerCursor._input].forEach(function (el) { el.addEventListener('input', saveApply); });
app.appendChild(T.row([T.el('span', { text: '字体大小' }), fontSize, fontLabel]));
app.appendChild(T.row([contrast, reduceMotion, biggerCursor]));
app.appendChild(preview);
app.appendChild(T.row([T.button('恢复默认', function () {
  fontSize.value = 100;
  contrast._input.checked = false;
  reduceMotion._input.checked = false;
  biggerCursor._input.checked = false;
  saveApply();
  T.toast('已恢复默认');
})]));
apply();
''')

d('export-config', '配置导出', '导出收藏 / 历史 / 设置 / 待办等本地数据为 JSON 备份', js=r'''
var KEYS = ['freellm-favorites', 'freellm-history', 'freellm-settings', 'freellm-todos', 'freellm-notes', 'freellm-journal', 'freellm-habits', 'freellm-expense', 'freellm-mood', 'freellm-water', 'freellm-stand', 'freellm-countdown-adv', 'freellm-snippets', 'freellm-bookmarks', 'freellm-a11y'];
var checks = KEYS.map(function (k) {
  var has = false;
  try { has = !!(localStorage.getItem(k) && localStorage.getItem(k) !== '[]' && localStorage.getItem(k) !== '{}'); } catch (e) {}
  return T.check(k.replace('freellm-', '') + (has ? ' ✓有数据' : '（空）'), has);
});
var output = T.out('导出内容预览…');
function build() {
  var data = { _export: 'freellm-tools-backup', version: 1, date: new Date().toISOString() };
  checks.forEach(function (c, i) {
    if (!c._input.checked) return;
    try { data[KEYS[i]] = JSON.parse(localStorage.getItem(KEYS[i]) || 'null'); } catch (e) {}
  });
  output.value = JSON.stringify(data, null, 2);
  return data;
}
checks.forEach(function (c) { c._input.addEventListener('change', build); });
app.appendChild(T.el('span', { text: '选择要导出的数据', class: 'field' }));
var wrap1 = T.row(checks.slice(0, 5)); wrap1.style.marginBottom = '4px';
var wrap2 = T.row(checks.slice(5, 10)); wrap2.style.marginBottom = '4px';
var wrap3 = T.row(checks.slice(10)); wrap3.style.marginBottom = '4px';
app.appendChild(wrap1);
app.appendChild(wrap2);
app.appendChild(wrap3);
app.appendChild(T.pane([T.field('备份 JSON', output)], true));
app.appendChild(T.row([T.button('生成预览', build, true),
  T.button('下载备份文件', function () {
    var data = build();
    T.download('freellm-backup-' + T.today() + '.json', JSON.stringify(data), 'application/json');
  }, true)]));
build();
''')

d('import-config', '配置导入', '从备份 JSON 恢复本地数据（收藏 / 设置 / 笔记等）', js=r'''
var pick = T.el('input', { type: 'file', accept: '.json', style: 'display:none' });
document.body.appendChild(pick);
var input = T.textarea('粘贴备份 JSON，或点击下方按钮选择备份文件…', true);
var preview = T.el('div');
var KNOWN = ['freellm-favorites', 'freellm-history', 'freellm-settings', 'freellm-todos', 'freellm-notes', 'freellm-journal', 'freellm-habits', 'freellm-expense', 'freellm-mood', 'freellm-water', 'freellm-stand', 'freellm-countdown-adv', 'freellm-snippets', 'freellm-bookmarks', 'freellm-a11y'];
function analyze() {
  T.clearEl(preview);
  try {
    var data = T.parseJSON(input.value);
    var rows = [];
    KNOWN.forEach(function (k) {
      if (data[k] != null) {
        var size = JSON.stringify(data[k]).length;
        rows.push([k.replace('freellm-', ''), size + ' 字节', '可恢复']);
      }
    });
    if (rows.length) preview.appendChild(T.refTable(['数据项', '大小', '状态'], rows));
    else preview.appendChild(T.msg('未识别到可恢复的数据项', ''));
    window._importData = data;
  } catch (e) {
    preview.appendChild(T.msg('⚠ JSON 解析失败：' + e.message, 'err'));
  }
}
input.addEventListener('input', T.debounce(analyze, 300));
pick.addEventListener('change', function () {
  var f = pick.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () { input.value = fr.result; analyze(); };
  fr.readAsText(f);
});
app.appendChild(T.row([T.button('选择备份文件', function () { pick.click(); }), T.el('span', { text: '或直接粘贴 JSON' })]));
app.appendChild(T.pane([T.field('备份内容', input)], true));
app.appendChild(preview);
app.appendChild(T.row([T.button('⚠ 恢复所选数据（覆盖现有）', function () {
  var data = window._importData;
  if (!data) { T.toast('请先载入有效备份'); return; }
  var count = 0;
  KNOWN.forEach(function (k) {
    if (data[k] != null) {
      localStorage.setItem(k, JSON.stringify(data[k]));
      count++;
    }
  });
  T.toast('已恢复 ' + count + ' 项数据');
}, true)]));
''')

d('feedback', '用户反馈', '提交反馈与建议：生成 mailto / GitHub Issue 链接', js=r'''
var type = T.select([{value:'bug',label:'🐛 Bug 反馈'},{value:'feature',label:'💡 功能建议'},{value:'praise',label:'❤️ 好评鼓励'},{value:'other',label:'📝 其他'}],'feature');
var tool = T.input('', { class: 'grow', placeholder: '相关工具（可选），如：JSON 格式化' });
var body = T.textarea('请描述你的反馈…\n\n1. 问题描述：\n2. 复现步骤：\n3. 期望行为：', true);
body.style.minHeight = '160px';
var env = T.el('div');
function envInfo() {
  return '\n\n---\n环境：' + navigator.userAgent + ' · ' + screen.width + 'x' + screen.height;
}
function render() {
  T.clearEl(env);
  var title = '[' + type.value.toUpperCase() + '] ' + (tool.value || '工具站反馈');
  var content = body.value + envInfo();
  var gh = 'https://github.com/freellm/freellm/issues/new?title=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(content);
  var mail = 'mailto:feedback@freellm.top?subject=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(content);
  env.appendChild(T.kvTable([
    ['标题预览', title]
  ]));
  env.appendChild(T.row([T.button('通过 GitHub Issue 提交', function () { window.open(gh, '_blank'); }, true),
    T.button('通过邮件提交', function () { location.href = mail; })]));
}
[type, tool, body].forEach(function (el) { el.addEventListener('input', T.debounce(render, 300)); });
app.appendChild(T.pane([T.field('反馈类型', type), T.field('相关工具', tool)]));
app.appendChild(body);
app.appendChild(env);
render();
''')

d('changelog', '更新日志', '工具站功能更新历史', js=r'''
var LOG = [
  ['2026-09-15', 'v1.0 正式版', [
    '全部 290 个工具页面上线，覆盖 13 个分类',
    '工具集线器：搜索 / 分类 / 收藏 / 历史 / 模态框内嵌',
    '纯前端运行，不收集任何输入数据'
  ]],
  ['2026-09-14', 'v0.9 Beta', [
    '新增图片工作台（多步流水线处理）',
    '农历 / 黄历 / 八字等中国传统工具',
    '接入全站 GitHub 同步（收藏与历史漫游）'
  ]],
  ['2026-09-13', 'v0.8 Alpha', [
    '工具注册表与分类体系定型',
    '共享组件库 tool-common / lib-crypto / lib-format / lib-utils',
    '二维码生成等首批工具上线'
  ]]
];
LOG.forEach(function (entry) {
  var card = T.el('div', { style: 'border-left:3px solid var(--accent);padding:2px 0 2px 16px;margin-bottom:22px' });
  card.appendChild(T.row([T.el('b', { text: entry[1], style: 'font-size:16px' }), T.badge(entry[0])]));
  var ul = T.el('ul', { style: 'margin:8px 0 0;padding-left:18px;color:var(--ink2);font-size:13.5px' });
  entry[2].forEach(function (item) {
    ul.appendChild(T.el('li', { text: item, style: 'margin:4px 0' }));
  });
  card.appendChild(ul);
  app.appendChild(card);
});
''')

d('about', '关于', '关于 FreeLLM 工具站：理念 / 隐私 / 技术栈', js=r'''
var hero = T.el('div', { style: 'text-align:center;margin:26px 0' });
hero.appendChild(T.el('div', { text: '✦', style: 'font-size:44px;color:var(--accent)' }));
hero.appendChild(T.el('h2', { text: 'FreeLLM 工具合集', style: 'font:400 30px var(--font-serif);margin:8px 0' }));
hero.appendChild(T.el('p', { text: '打开即用的 290 个在线工具 · 全部浏览器本地运行', style: 'color:var(--ink2)' }));
app.appendChild(hero);
app.appendChild(T.kvTable([
  ['🎯 理念', '免费、无广告、无需注册；数据永不上传'],
  ['🔒 隐私', '所有工具均在浏览器端运行，输入内容不经过任何服务器'],
  ['⚡ 技术', '纯静态 HTML/CSS/JS + WebCrypto/WebAudio/Canvas，无框架无构建'],
  ['📦 收录', '编码加密 / 格式化 / 生成器 / CSS / 文本 / 计算 / 日期 / 速查 / 开发 / 图片 / 娱乐 / 实用'],
  ['🔄 同步', '收藏与历史可选 GitHub Gist 跨设备漫游'],
  ['📮 联系', 'feedback@freellm.top']
]));
app.appendChild(T.el('hr', { class: 'hr' }));
app.appendChild(T.el('p', { text: '© 2026 FreeLLM · 部分 colorblind 矩阵与农历算法基于公开资料实现。', style: 'color:var(--ink3);font-size:12px;text-align:center' }));
app.appendChild(T.row([T.button('前往工具集线器', function () { location.href = '/tools/'; }, true),
  T.button('查看每日更新', function () { location.href = '/logs/'; })]));
''')
