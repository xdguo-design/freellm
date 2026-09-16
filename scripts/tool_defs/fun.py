# -*- coding: utf-8 -*-
"""趣味娱乐类工具定义"""
from .registry import d

d('game2048', '2048 游戏', '经典数字合并：方向键 / 滑动合并相同数字，冲击 2048', js=r'''
var N = 4;
var grid = [];
var score = 0;
var best = +(localStorage.getItem('freellm-2048-best') || 0);
var board = T.el('div', { style: 'display:grid;grid-template-columns:repeat(4,84px);gap:8px;justify-content:center;margin:18px auto;background:var(--line);padding:8px;border-radius:10px;width:fit-content' });
var scoreEl = T.stat(0, '当前');
var bestEl = T.stat(best, '最佳');
var COLORS = { 2: '#EEE4DA', 4: '#EDE0C8', 8: '#F2B179', 16: '#F59563', 32: '#F67C5F', 64: '#F65E3B', 128: '#EDCF72', 256: '#EDCC61', 512: '#EDC850', 1024: '#EDC53F', 2048: '#EDC22E' };
function init() {
  grid = [];
  for (var i = 0; i < N * N; i++) grid.push(0);
  score = 0;
  addTile();
  addTile();
  draw();
}
function addTile() {
  var empty = [];
  grid.forEach(function (v, i) { if (!v) empty.push(i); });
  if (!empty.length) return;
  grid[empty[Math.floor(Math.random() * empty.length)]] = Math.random() < 0.9 ? 2 : 4;
}
function draw() {
  T.clearEl(board);
  grid.forEach(function (v) {
    var cell = T.el('div', { style: 'width:84px;height:84px;display:flex;align-items:center;justify-content:center;border-radius:8px;font-weight:700;font-size:' + (v > 512 ? 22 : v > 64 ? 28 : 34) + 'px;background:' + (v ? (COLORS[v] || '#3C3A32') : 'var(--surface)') + ';color:' + (v > 4 ? '#F9F6F2' : '#776E65') });
    cell.textContent = v || '';
    board.appendChild(cell);
  });
  scoreEl.firstChild.textContent = score;
  if (score > best) { best = score; localStorage.setItem('freellm-2048-best', best); bestEl.firstChild.textContent = best; }
}
function move(dir) {
  var moved = false;
  var get = function (r, c) { return grid[r * N + c]; };
  var set = function (r, c, v) { grid[r * N + c] = v; };
  for (var i = 0; i < N; i++) {
    var line = [];
    for (var j = 0; j < N; j++) {
      if (dir === 'left') line.push(get(i, j));
      else if (dir === 'right') line.push(get(i, N - 1 - j));
      else if (dir === 'up') line.push(get(j, i));
      else line.push(get(N - 1 - j, i));
    }
    var filtered = line.filter(function (v) { return v; });
    var merged = [];
    for (var k = 0; k < filtered.length; k++) {
      if (k + 1 < filtered.length && filtered[k] === filtered[k + 1]) {
        merged.push(filtered[k] * 2);
        score += filtered[k] * 2;
        k++;
      } else merged.push(filtered[k]);
    }
    while (merged.length < N) merged.push(0);
    for (var j2 = 0; j2 < N; j2++) {
      var v = merged[j2];
      if (dir === 'left') { if (get(i, j2) !== v) moved = true; set(i, j2, v); }
      else if (dir === 'right') { if (get(i, N - 1 - j2) !== v) moved = true; set(i, N - 1 - j2, v); }
      else if (dir === 'up') { if (get(j2, i) !== v) moved = true; set(j2, i, v); }
      else { if (get(N - 1 - j2, i) !== v) moved = true; set(N - 1 - j2, i, v); }
    }
  }
  if (moved) { addTile(); draw(); }
}
document.addEventListener('keydown', function (e) {
  var map = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down', a: 'left', d: 'right', w: 'up', s: 'down' };
  if (map[e.key]) { e.preventDefault(); move(map[e.key]); }
});
app.appendChild(T.row([scoreEl, bestEl, T.button('重新开始', init, true)]));
app.appendChild(T.el('p', { text: '方向键 / WASD 操作，相同数字相撞合并。', style: 'text-align:center;color:var(--ink2);font-size:12px' }));
app.appendChild(board);
init();
''')

d('snake', '贪吃蛇', '经典贪吃蛇：方向键控制，吃食物变长，撞墙即败', js=r'''
var canvas = T.el('canvas', { width: 400, height: 400, style: 'width:100%;max-width:400px;border:1px solid var(--line);border-radius:10px;display:block;margin:0 auto;background:var(--surface)' });
var scoreEl = T.stat(0, '得分');
var bestEl = T.stat(+(localStorage.getItem('freellm-snake-best') || 0), '最佳');
var ctx = canvas.getContext('2d');
var G = 20, CELL = canvas.width / G;
var snake, dir, food, score, timer = 0, speed = 130, running = false;
function init() {
  snake = [{ x: 10, y: 10 }];
  dir = { x: 1, y: 0 };
  score = 0;
  speed = 130;
  placeFood();
  scoreEl.firstChild.textContent = 0;
  if (!running) { running = true; loop(); }
}
function placeFood() {
  do {
    food = { x: Math.floor(Math.random() * G), y: Math.floor(Math.random() * G) };
  } while (snake.some(function (s) { return s.x === food.x && s.y === food.y; }));
}
function loop() {
  clearInterval(timer);
  timer = setInterval(step, speed);
}
function step() {
  if (!running) return;
  var head = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };
  if (head.x < 0 || head.y < 0 || head.x >= G || head.y >= G || snake.some(function (s) { return s.x === head.x && s.y === head.y; })) {
    running = false;
    clearInterval(timer);
    if (score > +(localStorage.getItem('freellm-snake-best') || 0)) localStorage.setItem('freellm-snake-best', score);
    bestEl.firstChild.textContent = Math.max(score, +(localStorage.getItem('freellm-snake-best') || 0));
    ctx.fillStyle = 'rgba(0,0,0,.55)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#fff';
    ctx.font = '600 26px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('游戏结束 · 得分 ' + score, canvas.width / 2, canvas.height / 2);
    ctx.font = '14px sans-serif';
    ctx.fillText('按空格或点击"重新开始"', canvas.width / 2, canvas.height / 2 + 30);
    return;
  }
  snake.unshift(head);
  if (head.x === food.x && head.y === food.y) {
    score += 10;
    scoreEl.firstChild.textContent = score;
    placeFood();
    if (speed > 65) { speed -= 4; loop(); }
  } else snake.pop();
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#E74C3C';
  ctx.beginPath();
  ctx.arc(food.x * CELL + CELL / 2, food.y * CELL + CELL / 2, CELL / 2 - 3, 0, Math.PI * 2);
  ctx.fill();
  snake.forEach(function (s, i) {
    ctx.fillStyle = i === 0 ? '#1744E8' : 'rgba(23,68,232,' + Math.max(0.35, 1 - i * 0.04) + ')';
    ctx.fillRect(s.x * CELL + 1, s.y * CELL + 1, CELL - 2, CELL - 2);
  });
}
document.addEventListener('keydown', function (e) {
  var map = { ArrowUp: { x: 0, y: -1 }, ArrowDown: { x: 0, y: 1 }, ArrowLeft: { x: -1, y: 0 }, ArrowRight: { x: 1, y: 0 }, w: { x: 0, y: -1 }, s: { x: 0, y: 1 }, a: { x: -1, y: 0 }, d: { x: 1, y: 0 } };
  if (map[e.key]) {
    e.preventDefault();
    if (map[e.key].x !== -dir.x || map[e.key].y !== -dir.y) dir = map[e.key];
  }
  if (e.key === ' ' && !running) { e.preventDefault(); init(); }
});
app.appendChild(T.row([scoreEl, bestEl, T.button('重新开始', function () { running = false; setTimeout(init, 30); }, true)]));
app.appendChild(canvas);
app.appendChild(T.el('p', { text: '方向键 / WASD 控制，空格重开。', style: 'text-align:center;color:var(--ink2);font-size:12px' }));
init();
''')

d('gomoku', '五子棋', '双人对战五子棋（同屏轮流），五连即胜', js=r'''
var N = 15;
var board = [];
var current = 1;
var history = [];
var canvas = T.el('canvas', { width: 480, height: 480, style: 'width:100%;max-width:480px;border:1px solid var(--line);border-radius:10px;display:block;margin:0 auto;background:#E8C88F;cursor:crosshair' });
var ctx = canvas.getContext('2d');
var turnBadge = T.badge('⚫ 黑方先行');
function init() {
  board = [];
  for (var i = 0; i < N * N; i++) board.push(0);
  history = [];
  current = 1;
  draw();
}
function draw() {
  var CELL = canvas.width / (N + 1);
  ctx.fillStyle = '#E8C88F';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'rgba(90,60,20,.55)';
  ctx.lineWidth = 1;
  for (var i = 1; i <= N; i++) {
    ctx.beginPath();
    ctx.moveTo(CELL, i * CELL);
    ctx.lineTo(canvas.width - CELL, i * CELL);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(i * CELL, CELL);
    ctx.lineTo(i * CELL, canvas.height - CELL);
    ctx.stroke();
  }
  board.forEach(function (v, idx) {
    if (!v) return;
    var x = (idx % N + 1) * CELL;
    var y = (Math.floor(idx / N) + 1) * CELL;
    ctx.beginPath();
    ctx.arc(x, y, CELL / 2 - 3, 0, Math.PI * 2);
    ctx.fillStyle = v === 1 ? '#1a1a1a' : '#fafafa';
    ctx.fill();
    if (v === 2) { ctx.strokeStyle = '#999'; ctx.stroke(); }
  });
  if (history.length) {
    var last = history[history.length - 1];
    ctx.strokeStyle = '#E74C3C';
    ctx.lineWidth = 2;
    ctx.strokeRect((last % N + 1) * CELL - CELL / 2 + 3, (Math.floor(last / N) + 1) * CELL - CELL / 2 + 3, CELL - 6, CELL - 6);
  }
  turnBadge.textContent = current === 1 ? '⚫ 黑方落子' : '⚪ 白方落子';
  turnBadge.className = 'badge ' + (current === 1 ? '' : 'blue');
}
function checkWin(idx, player) {
  var r = Math.floor(idx / N), c = idx % N;
  var dirs = [[0, 1], [1, 0], [1, 1], [1, -1]];
  for (var d = 0; d < 4; d++) {
    var count = 1;
    for (var sign = -1; sign <= 1; sign += 2) {
      var rr = r + dirs[d][0] * sign, cc = c + dirs[d][1] * sign;
      while (rr >= 0 && rr < N && cc >= 0 && cc < N && board[rr * N + cc] === player) {
        count++;
        rr += dirs[d][0] * sign;
        cc += dirs[d][1] * sign;
      }
    }
    if (count >= 5) return true;
  }
  return false;
}
canvas.addEventListener('click', function (e) {
  var rect = canvas.getBoundingClientRect();
  var CELL = canvas.width / (N + 1);
  var x = Math.round((e.clientX - rect.left) * (canvas.width / rect.width) / CELL) - 1;
  var y = Math.round((e.clientY - rect.top) * (canvas.height / rect.height) / CELL) - 1;
  if (x < 0 || y < 0 || x >= N || y >= N) return;
  var idx = y * N + x;
  if (board[idx]) return;
  board[idx] = current;
  history.push(idx);
  draw();
  if (checkWin(idx, current)) {
    setTimeout(function () { alert((current === 1 ? '⚫ 黑方' : '⚪ 白方') + ' 获胜！五连达成 🎉'); }, 50);
    return;
  }
  current = current === 1 ? 2 : 1;
  draw();
});
app.appendChild(T.row([turnBadge, T.button('悔棋', function () {
  if (!history.length) return;
  var last = history.pop();
  board[last] = 0;
  current = current === 1 ? 2 : 1;
  draw();
}), T.button('重新开局', init, true)]));
app.appendChild(canvas);
init();
''')

d('reaction', '反应速度测试', '点击测反应时间：等待变绿瞬间点击，测 5 次取平均', js=r'''
var box = T.el('div', { style: 'height:260px;border-radius:14px;display:flex;align-items:center;justify-content:center;cursor:pointer;background:var(--surface-soft);border:1px solid var(--line);user-select:none;text-align:center;padding:20px' });
var results = T.el('div', { class: 'row' });
var state = 'idle';
var startTime = 0, timeout = 0;
var times = [];
box.textContent = '点击开始测试';
box.addEventListener('click', function () {
  if (state === 'idle' || state === 'done') {
    state = 'waiting';
    box.style.background = '#C0392B';
    box.style.color = '#fff';
    box.textContent = '等待变绿…（提前点击将重置）';
    timeout = setTimeout(function () {
      state = 'ready';
      startTime = performance.now();
      box.style.background = '#27AE60';
      box.textContent = '现在点击！';
    }, 1200 + Math.random() * 2800);
  } else if (state === 'waiting') {
    clearTimeout(timeout);
    state = 'idle';
    box.style.background = '';
    box.style.color = '';
    box.textContent = '太早了！点击重新开始';
  } else if (state === 'ready') {
    var ms = Math.round(performance.now() - startTime);
    times.push(ms);
    state = 'done';
    box.style.background = '';
    box.style.color = '';
    var grade = ms < 200 ? '电光石火 ⚡' : ms < 250 ? '反应极佳' : ms < 320 ? '反应良好' : ms < 450 ? '正常水平' : '还要练练';
    box.textContent = ms + ' ms — ' + grade + (times.length < 5 ? '（再测 ' + (5 - times.length) + ' 次）' : '') + '，点击继续';
    renderResults();
  }
});
function renderResults() {
  T.clearEl(results);
  results.appendChild(T.stat(times.length ? Math.round(times.reduce(function (a, b) { return a + b; }) / times.length) : '—', '平均 ms'));
  results.appendChild(T.stat(times.length ? Math.min.apply(null, times) : '—', '最快 ms'));
  results.appendChild(T.stat(times.length, '已测次数'));
}
app.appendChild(box);
app.appendChild(results);
app.appendChild(T.row([T.button('重置成绩', function () { times = []; renderResults(); box.textContent = '点击开始测试'; }), T.el('span', { text: '人类平均反应约 250ms；电竞选手可达 150ms' })]));
renderResults();
''')

d('schulte', '舒尔特方格', '注意力训练：按 1-25 顺序点击，计时挑战', js=r'''
var N = 5;
var grid = T.el('div', { style: 'display:grid;grid-template-columns:repeat(5,64px);gap:6px;justify-content:center;margin:18px auto' });
var next = 1;
var t0 = 0, timerIv = 0;
var timeEl = T.stat('—', '用时');
var bestEl = T.stat(+(localStorage.getItem('freellm-schulte-best') || 0), '最佳(秒)');
var status = T.badge('点击开始');
function start() {
  next = 1;
  var nums = [];
  for (var i = 1; i <= N * N; i++) nums.push(i);
  nums.sort(function () { return Math.random() - 0.5; });
  T.clearEl(grid);
  nums.forEach(function (n) {
    var cell = T.el('div', { text: String(n), style: 'width:64px;height:64px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:8px;background:var(--surface);font:500 22px var(--font-serif);cursor:pointer;user-select:none' });
    cell.addEventListener('click', function () {
      if (+cell.textContent !== next) { cell.style.background = 'var(--err)'; setTimeout(function () { cell.style.background = ''; }, 200); return; }
      cell.style.visibility = 'hidden';
      next++;
      if (next === 2) {
        t0 = performance.now();
        timerIv = setInterval(function () { timeEl.firstChild.textContent = ((performance.now() - t0) / 1000).toFixed(1); }, 100);
        status.textContent = '训练中…';
      }
      if (next > N * N) {
        clearInterval(timerIv);
        var sec = (performance.now() - t0) / 1000;
        status.textContent = '🎉 完成！' + sec.toFixed(1) + ' 秒';
        status.className = 'badge ok';
        if (!+(localStorage.getItem('freellm-schulte-best') || 0) || sec < +(localStorage.getItem('freellm-schulte-best') || 0)) {
          localStorage.setItem('freellm-schulte-best', sec.toFixed(1));
          bestEl.firstChild.textContent = sec.toFixed(1);
        }
      }
    });
    grid.appendChild(cell);
  });
  status.textContent = '按 1 → 25 顺序点击';
  status.className = 'badge blue';
}
app.appendChild(T.row([timeEl, bestEl, status, T.button('重新开始', start, true)]));
app.appendChild(grid);
app.appendChild(T.el('p', { text: '成人 25 格平均 25-30 秒；坚持训练可提升视觉搜索与注意力。', style: 'text-align:center;color:var(--ink2);font-size:12px' }));
start();
''')

d('draw', '在线白板涂鸦', 'Canvas 自由绘画：调色画笔 + 橡皮 + 清空下载', js=r'''
var canvas = T.el('canvas', { width: 860, height: 460, style: 'width:100%;border:1px solid var(--line);border-radius:10px;cursor:crosshair;background:#fff;touch-action:none' });
var color = T.color('#1744E8');
var size = T.range(1, 36, 1, 6);
var sizeLabel = T.el('b', { text: '6' });
var ctx = canvas.getContext('2d');
ctx.lineCap = 'round';
var drawing = false;
canvas.addEventListener('pointerdown', function (e) {
  drawing = true;
  var rect = canvas.getBoundingClientRect();
  ctx.beginPath();
  ctx.moveTo((e.clientX - rect.left) * canvas.width / rect.width, (e.clientY - rect.top) * canvas.height / rect.height);
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', function (e) {
  if (!drawing) return;
  var rect = canvas.getBoundingClientRect();
  ctx.strokeStyle = color.value;
  ctx.lineWidth = +size.value;
  ctx.lineTo((e.clientX - rect.left) * canvas.width / rect.width, (e.clientY - rect.top) * canvas.height / rect.height);
  ctx.stroke();
});
window.addEventListener('pointerup', function () { drawing = false; });
app.appendChild(T.row([color, T.el('span', { text: '粗细' }), size, sizeLabel,
  T.button('清空', function () { ctx.clearRect(0, 0, canvas.width, canvas.height); }),
  T.button('下载画作', function () { T.dlCanvas(canvas, 'drawing.png'); }, true)]));
app.appendChild(canvas);
size.addEventListener('input', function () { sizeLabel.textContent = size.value; });
''')

d('pi-memory', 'π 记忆挑战', '圆周率记忆训练：输入小数位，挑战 100 位', js=r'''
var PI = '3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196';
var input = T.input('', { class: 'grow mono', placeholder: '输入你记住的 π（从 3 开始）…' });
var status = T.badge('开始输入，错了会提示位置');
var best = +(localStorage.getItem('freellm-pi-best') || 0);
var bestEl = T.stat(best, '最佳位数');
var display = T.el('div', { class: 'output', style: 'min-height:80px;font-size:15px;letter-spacing:2px', text: PI.slice(0, 60) + '…' });
input.addEventListener('input', function () {
  var v = input.value.replace(/[^0-9.]/g, '');
  if (!v) { status.textContent = '开始输入…'; return; }
  var ok = 0;
  for (var i = 0; i < v.length; i++) {
    if (v[i] === PI[i]) ok++;
    else {
      status.textContent = '✗ 第 ' + (i + 1) + ' 位错了（应为 ' + PI[i] + '），正确记录 ' + ok + ' 位';
      status.className = 'badge warn';
      if (ok > best) { best = ok; localStorage.setItem('freellm-pi-best', best); bestEl.firstChild.textContent = best; }
      return;
    }
  }
  status.textContent = '✓ 已正确 ' + v.length + ' 位，继续！';
  status.className = 'badge ok';
  if (v.length > best) { best = v.length; localStorage.setItem('freellm-pi-best', best); bestEl.firstChild.textContent = best; }
  if (v.length >= 40) display.textContent = PI.slice(0, 100);
});
app.appendChild(T.row([bestEl, status]));
app.appendChild(display);
app.appendChild(T.pane([T.field('你的输入', input)], true));
app.appendChild(T.row([T.button('显示前 100 位', function () { display.textContent = PI; })]));
''')

d('matrix-rain', 'Matrix 数字雨', '黑客帝国风格 Canvas 字符雨特效，截图可用', js=r'''
var canvas = T.el('canvas', { width: 860, height: 420, style: 'width:100%;border:1px solid var(--line);border-radius:10px;background:#000' });
var speed = T.range(20, 150, 5, 50);
var green = T.color('#00FF41');
var chars = 'アイウエオカキクケコサシスセソ0123456789ABCDEFｦｧｨｩｪﬀﬁﬂ'.split('');
var ctx = canvas.getContext('2d');
var cols = Math.floor(canvas.width / 16);
var drops = [];
for (var i = 0; i < cols; i++) drops[i] = Math.random() * -100;
var running = true;
function draw() {
  if (!running) return;
  ctx.fillStyle = 'rgba(0,0,0,0.08)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.font = '15px monospace';
  for (i = 0; i < cols; i++) {
    ctx.fillStyle = Math.random() > 0.975 ? '#DADADA' : green.value;
    ctx.fillText(chars[Math.floor(Math.random() * chars.length)], i * 16, drops[i] * 16);
    if (drops[i] * 16 > canvas.height && Math.random() > 0.975) drops[i] = 0;
    drops[i]++;
  }
  setTimeout(function () { requestAnimationFrame(draw); }, 155 - speed.value);
}
draw();
app.appendChild(canvas);
app.appendChild(T.row([T.el('span', { text: '速度' }), speed, T.el('span', { text: '颜色' }), green,
  T.button('暂停', function () { running = !running; this.firstChild.textContent = running ? '暂停' : '继续'; if (running) draw(); }),
  T.button('截图下载', function () { T.dlCanvas(canvas, 'matrix-rain.png'); })]));
''')

d('rubik-cube', '在线魔方', '3D CSS 三阶魔方：旋转视角 + 转动公式演示', js=r'''
var stage = T.el('div', { style: 'perspective:900px;display:flex;justify-content:center;margin:30px 0' });
var cube = T.el('div', { style: 'width:180px;height:180px;position:relative;transform-style:preserve-3d;transform:rotateX(-24deg) rotateY(-36deg);transition:transform .5s' });
var COLORS = { U: '#FFFFFF', D: '#FFD500', F: '#009B48', B: '#0046AD', L: '#FF5800', R: '#B71234' };
var faces = [
  { name: 'F', t: 'translateZ(90px)' }, { name: 'B', t: 'rotateY(180deg) translateZ(90px)' },
  { name: 'R', t: 'rotateY(90deg) translateZ(90px)' }, { name: 'L', t: 'rotateY(-90deg) translateZ(90px)' },
  { name: 'U', t: 'rotateX(90deg) translateZ(90px)' }, { name: 'D', t: 'rotateX(-90deg) translateZ(90px)' }
];
var rx = -24, ry = -36;
faces.forEach(function (f) {
  var face = T.el('div', { style: 'position:absolute;width:180px;height:180px;transform:' + f.t + ';display:grid;grid-template-columns:repeat(3,1fr);gap:3px;padding:3px;background:#111;border-radius:6px' });
  for (var i = 0; i < 9; i++) {
    face.appendChild(T.el('div', { style: 'background:' + COLORS[f.name] + ';border-radius:4px' }));
  }
  cube.appendChild(face);
});
stage.appendChild(cube);
function view(dx, dy) {
  ry += dx;
  rx = Math.max(-88, Math.min(88, rx + dy));
  cube.style.transform = 'rotateX(' + rx + 'deg) rotateY(' + ry + 'deg)';
}
app.appendChild(T.el('p', { text: '拖动下方滑块或按钮旋转视角。这是一个静态展示魔方（复原模拟器需要更完整的层旋转引擎）。', style: 'text-align:center;color:var(--ink2);font-size:12px' }));
app.appendChild(stage);
var ry2 = T.range(-180, 180, 1, -36);
var rx2 = T.range(-88, 88, 1, -24);
ry2.addEventListener('input', function () { ry = +ry2.value; cube.style.transform = 'rotateX(' + rx + 'deg) rotateY(' + ry + 'deg)'; });
rx2.addEventListener('input', function () { rx = +rx2.value; cube.style.transform = 'rotateX(' + rx + 'deg) rotateY(' + ry + 'deg)'; });
app.appendChild(T.row([T.el('span', { text: '左右' }), ry2]));
app.appendChild(T.row([T.el('span', { text: '上下' }), rx2]));
app.appendChild(T.row([
  T.button('⟲', function () { view(-30, 0); }), T.button('⟳', function () { view(30, 0); }),
  T.button('自动旋转', function () {
    var iv = setInterval(function () { view(2, 0); }, 50);
    setTimeout(function () { clearInterval(iv); }, 6000);
  }, true)
]));
''')

d('bounce-ball', '弹跳小球', '物理弹跳动画：重力 / 弹性 / 摩擦可调，小球可拖拽', js=r'''
var canvas = T.el('canvas', { width: 860, height: 380, style: 'width:100%;border:1px solid var(--line);border-radius:10px;background:var(--surface);cursor:grab;touch-action:none' });
var gravity = T.range(0.1, 2, 0.05, 0.6);
var restitution = T.range(0.3, 0.99, 0.01, 0.82);
var friction = T.range(0.9, 1, 0.001, 0.995);
var balls = [];
for (var i = 0; i < 6; i++) {
  balls.push({
    x: 100 + Math.random() * 660, y: 50 + Math.random() * 150,
    vx: (Math.random() - 0.5) * 8, vy: 0,
    r: 14 + Math.random() * 16,
    color: ['#1744E8', '#7BC0E5', '#FFB88C', '#B8E986', '#F48FB1', '#B39DDB'][i]
  });
}
var ctx = canvas.getContext('2d');
var dragBall = null;
canvas.addEventListener('pointerdown', function (e) {
  var rect = canvas.getBoundingClientRect();
  var mx = (e.clientX - rect.left) * (canvas.width / rect.width);
  var my = (e.clientY - rect.top) * (canvas.height / rect.height);
  balls.forEach(function (b) {
    if (Math.hypot(b.x - mx, b.y - my) < b.r + 6) { dragBall = b; b.vx = 0; b.vy = 0; }
  });
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', function (e) {
  if (!dragBall) return;
  var rect = canvas.getBoundingClientRect();
  dragBall.x = (e.clientX - rect.left) * (canvas.width / rect.width);
  dragBall.y = (e.clientY - rect.top) * (canvas.height / rect.height);
});
window.addEventListener('pointerup', function () {
  if (dragBall) { dragBall.vx = (Math.random() - 0.5) * 10; dragBall.vy = 0; }
  dragBall = null;
});
function step() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  balls.forEach(function (b) {
    if (b !== dragBall) {
      b.vy += +gravity.value;
      b.x += b.vx;
      b.y += b.vy;
      b.vx *= +friction.value;
      if (b.y + b.r > canvas.height) { b.y = canvas.height - b.r; b.vy *= -(+restitution.value); }
      if (b.y - b.r < 0) { b.y = b.r; b.vy *= -(+restitution.value); }
      if (b.x + b.r > canvas.width) { b.x = canvas.width - b.r; b.vx *= -(+restitution.value); }
      if (b.x - b.r < 0) { b.x = b.r; b.vx *= -(+restitution.value); }
    }
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
    ctx.fillStyle = b.color;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(b.x - b.r / 3, b.y - b.r / 3, b.r / 4, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    ctx.fill();
  });
  requestAnimationFrame(step);
}
step();
app.appendChild(canvas);
app.appendChild(T.row([T.el('span', { text: '重力' }), gravity, T.el('span', { text: '弹性' }), restitution, T.el('span', { text: '摩擦' }), friction,
  T.button('重置小球', function () { location.reload ? null : null; balls.forEach(function (b, i) { b.x = 100 + i * 120; b.y = 60; b.vy = 0; b.vx = 0; }); })]));
app.appendChild(T.el('p', { text: '拖拽小球然后松手即可抛出。', style: 'color:var(--ink2);font-size:12px' }));
''')

d('sudoku', '数独', '生成 + 求解数独：随机谜题 / 校验 / 一键求解', js=r'''
var grid = T.el('div', { style: 'display:grid;grid-template-columns:repeat(9,40px);gap:0;justify-content:center;margin:16px auto;width:fit-content;border:2px solid var(--ink)' });
var cells = [];
for (var i = 0; i < 81; i++) {
  var inp = T.el('input', { maxlength: '2', style: 'width:40px;height:40px;text-align:center;font:500 18px var(--font-mono);border:.5px solid var(--line);background:var(--surface);color:var(--ink);outline:none' });
  var r = Math.floor(i / 9), c = i % 9;
  if ((Math.floor(r / 3) + Math.floor(c / 3)) % 2) inp.style.background = 'var(--surface-soft)';
  inp.addEventListener('input', function () { this.value = this.value.replace(/[^1-9]/g, '').slice(0, 1); });
  cells.push(inp);
  grid.appendChild(inp);
}
function solve(board) {
  function findEmpty() {
    for (var i = 0; i < 81; i++) if (!board[i]) return i;
    return -1;
  }
  function valid(idx, v) {
    var r = Math.floor(idx / 9), c = idx % 9;
    for (var i = 0; i < 9; i++) {
      if (board[r * 9 + i] === v || board[i * 9 + c] === v) return false;
    }
    var br = Math.floor(r / 3) * 3, bc = Math.floor(c / 3) * 3;
    for (var rr = br; rr < br + 3; rr++) for (var cc = bc; cc < bc + 3; cc++) {
      if (board[rr * 9 + cc] === v) return false;
    }
    return true;
  }
  var idx = findEmpty();
  if (idx < 0) return true;
  for (var v = 1; v <= 9; v++) {
    if (valid(idx, v)) {
      board[idx] = v;
      if (solve(board)) return true;
      board[idx] = 0;
    }
  }
  return false;
}
function generate() {
  var board = new Array(81).fill(0);
  var seeds = [1, 2, 3, 4, 5, 6, 7, 8, 9].sort(function () { return Math.random() - 0.5; });
  for (var i = 0; i < 9; i++) board[Math.floor(i / 3) * 9 + (i % 3) * 3 + i] = seeds[i];
  solve(board);
  var holes = 45 + Math.floor(Math.random() * 8);
  var idxs = [];
  for (i = 0; i < 81; i++) idxs.push(i);
  idxs.sort(function () { return Math.random() - 0.5; });
  for (i = 0; i < holes; i++) board[idxs[i]] = 0;
  cells.forEach(function (cell, i) {
    cell.readOnly = false;
    cell.style.color = '';
    if (board[i]) {
      cell.value = board[i];
      cell.readOnly = true;
      cell.style.fontWeight = '700';
    } else {
      cell.value = '';
      cell.style.fontWeight = '';
    }
  });
}
function check() {
  var board = cells.map(function (c) { return +c.value || 0; });
  var ok = true;
  var seen = function (arr) {
    var s = {};
    for (var i = 0; i < 9; i++) {
      if (!arr[i]) continue;
      if (s[arr[i]]) return false;
      s[arr[i]] = 1;
    }
    return true;
  };
  for (var r = 0; r < 9; r++) {
    var row = [];
    for (var c = 0; c < 9; c++) row.push(board[r * 9 + c]);
    if (!seen(row)) ok = false;
  }
  for (c = 0; c < 9; c++) {
    var col = [];
    for (r = 0; r < 9; r++) col.push(board[r * 9 + c]);
    if (!seen(col)) ok = false;
  }
  for (var br = 0; br < 3; br++) for (var bc = 0; bc < 3; bc++) {
    var box = [];
    for (r = 0; r < 3; r++) for (c = 0; c < 3; c++) box.push(board[(br * 3 + r) * 9 + bc * 3 + c]);
    if (!seen(box)) ok = false;
  }
  T.toast(ok && board.every(function (v) { return v; }) ? '🎉 完成！全部正确' : ok ? '目前无冲突，继续' : '⚠ 存在冲突，检查红色提示');
}
app.appendChild(grid);
app.appendChild(T.row([T.button('新谜题', generate, true), T.button('检查', check),
  T.button('显示答案', function () {
    var board = cells.map(function (c) { return +c.value || 0; });
    if (solve(board)) cells.forEach(function (c, i) {
      if (!c.value || c.readOnly) { c.value = board[i]; }
      if (!c.readOnly) c.style.color = 'var(--accent)';
    });
    else T.toast('当前局面无解');
  })]));
generate();
''')

d('minesweeper', '扫雷', '经典扫雷：左键翻开 / 右键插旗，三种难度', js=r'''
var diff = T.select([{value:'9x9x10',label:'初级 9×9 · 10 雷'},{value:'16x16x40',label:'中级 16×16 · 40 雷'},{value:'16x30x99',label:'高级 16×30 · 99 雷'}],'9x9x10');
var grid = T.el('div', { style: 'display:grid;gap:2px;justify-content:center;margin:14px auto;width:fit-content' });
var status = T.badge('左键翻开 · 右键插旗');
var flagEl = T.stat('0', '剩余雷数');
var board, rows, cols, mines, revealed, flags, over, started;
function init() {
  var p = diff.value.split('x');
  rows = +p[0];
  cols = +p[1];
  mines = +p[2];
  board = [];
  for (var i = 0; i < rows * cols; i++) board.push({ mine: false, open: false, flag: false, n: 0 });
  revealed = 0;
  flags = 0;
  over = false;
  started = false;
  flagEl.firstChild.textContent = mines;
  status.textContent = '左键翻开 · 右键插旗';
  status.className = 'badge';
  render();
}
function neighbors(idx) {
  var r = Math.floor(idx / cols), c = idx % cols;
  var out = [];
  for (var dr = -1; dr <= 1; dr++) for (var dc = -1; dc <= 1; dc++) {
    if (!dr && !dc) continue;
    var rr = r + dr, cc = c + dc;
    if (rr >= 0 && rr < rows && cc >= 0 && cc < cols) out.push(rr * cols + cc);
  }
  return out;
}
function place(firstIdx) {
  var banned = new Set([firstIdx].concat(neighbors(firstIdx)));
  var placed = 0;
  while (placed < mines) {
    var idx = Math.floor(Math.random() * rows * cols);
    if (board[idx].mine || banned.has(idx)) continue;
    board[idx].mine = true;
    placed++;
  }
  board.forEach(function (cell, i) {
    cell.n = neighbors(i).filter(function (j) { return board[j].mine; }).length;
  });
}
function open(idx) {
  if (over || board[idx].open || board[idx].flag) return;
  if (!started) { started = true; place(idx); }
  board[idx].open = true;
  revealed++;
  if (board[idx].mine) {
    over = true;
    status.textContent = '💥 踩雷了！点击新游戏再来';
    status.className = 'badge warn';
    board.forEach(function (c) { if (c.mine) c.open = true; });
    render();
    return;
  }
  if (board[idx].n === 0) {
    neighbors(idx).forEach(open);
  }
  if (revealed === rows * cols - mines) {
    over = true;
    status.textContent = '🎉 通关！';
    status.className = 'badge ok';
  }
  render();
}
var NC = ['', '#7BC0E5', '#346538', '#C0392B', '#6A0DAD', '#956400', '#008080', '#000', '#787774'];
function render() {
  T.clearEl(grid);
  grid.style.gridTemplateColumns = 'repeat(' + cols + ', 28px)';
  var cellSize = cols > 20 ? '26px' : '28px';
  board.forEach(function (cell, i) {
    var el = T.el('div', { style: 'width:' + cellSize + ';height:' + cellSize + ';display:flex;align-items:center;justify-content:center;font:700 13px var(--font-mono);border-radius:4px;cursor:pointer;user-select:none;background:' + (cell.open ? 'var(--surface-soft)' : 'var(--accent-soft)') + ';color:' + (cell.open && cell.n ? NC[cell.n] : 'inherit') });
    if (cell.open) {
      el.textContent = cell.mine ? '💣' : (cell.n || '');
    } else if (cell.flag) {
      el.textContent = '🚩';
    }
    el.addEventListener('click', function () { open(i); });
    el.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      if (over || cell.open) return;
      cell.flag = !cell.flag;
      flags += cell.flag ? 1 : -1;
      flagEl.firstChild.textContent = mines - flags;
      render();
    });
    grid.appendChild(el);
  });
}
diff.addEventListener('change', init);
app.appendChild(T.row([diff, flagEl, status, T.button('新游戏', init, true)]));
app.appendChild(grid);
init();
''')

d('memory-cards', '记忆卡片', '翻牌记忆配对游戏：8 对 Emoji，记步数与用时', js=r'''
var grid = T.el('div', { style: 'display:grid;grid-template-columns:repeat(4,76px);gap:8px;justify-content:center;margin:18px auto' });
var movesEl = T.stat(0, '步数');
var pairsEl = T.stat(0, '配对');
var timeEl = T.stat('0s', '用时');
var status = T.badge('点击卡片开始');
var EMOJIS = ['🎮', '🚀', '🌟', '🎧', '🍕', '🐼', '⚽', '🌈'];
var cards, flipped, matched, moves, timer, seconds, started;
function init() {
  var deck = EMOJIS.concat(EMOJIS).sort(function () { return Math.random() - 0.5; });
  cards = deck.map(function (e) { return { emoji: e, open: false, done: false }; });
  flipped = [];
  matched = 0;
  moves = 0;
  seconds = 0;
  started = false;
  clearInterval(timer);
  movesEl.firstChild.textContent = 0;
  pairsEl.firstChild.textContent = 0;
  timeEl.firstChild.textContent = '0s';
  status.textContent = '点击卡片开始';
  status.className = 'badge';
  render();
}
function render() {
  T.clearEl(grid);
  cards.forEach(function (card, i) {
    var cell = T.el('div', { text: card.open || card.done ? card.emoji : '', style: 'width:76px;height:76px;display:flex;align-items:center;justify-content:center;font-size:34px;border-radius:10px;cursor:pointer;user-select:none;transition:all .2s;background:' + (card.done ? 'var(--ok-bg)' : card.open ? 'var(--accent-soft)' : 'var(--surface)') + ';border:1px solid var(--line)' });
    cell.addEventListener('click', function () { flip(i); });
    grid.appendChild(cell);
  });
}
function flip(i) {
  var card = cards[i];
  if (card.open || card.done || flipped.length >= 2) return;
  if (!started) {
    started = true;
    timer = setInterval(function () { seconds++; timeEl.firstChild.textContent = seconds + 's'; }, 1000);
    status.textContent = '配对中…';
  }
  card.open = true;
  flipped.push(i);
  moves++;
  movesEl.firstChild.textContent = moves;
  render();
  if (flipped.length === 2) {
    var a = cards[flipped[0]], b = cards[flipped[1]];
    if (a.emoji === b.emoji) {
      a.done = b.done = true;
      matched++;
      pairsEl.firstChild.textContent = matched;
      flipped = [];
      if (matched === EMOJIS.length) {
        clearInterval(timer);
        status.textContent = '🎉 全部配对！' + moves + ' 步 · ' + seconds + ' 秒';
        status.className = 'badge ok';
      }
      render();
    } else {
      setTimeout(function () {
        a.open = b.open = false;
        flipped = [];
        render();
      }, 650);
    }
  }
}
app.appendChild(T.row([movesEl, pairsEl, timeEl, status, T.button('重新开始', init, true)]));
app.appendChild(grid);
init();
''')

d('dice', '掷骰子', '3D 动画骰子：1-6 颗可调，摇一摇出结果', js=r'''
var count = T.num(2, { min: 1, max: 6, style: 'width:70px' });
var box = T.el('div', { style: 'display:flex;gap:18px;justify-content:center;margin:34px 0;flex-wrap:wrap;min-height:110px' });
var total = T.stat('—', '总点数');
var history = T.el('div', { style: 'color:var(--ink2);font-size:12px;text-align:center;min-height:20px' });
var DOTS = { 1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8] };
function renderDice(values) {
  T.clearEl(box);
  values.forEach(function (v) {
    var die = T.el('div', { style: 'width:84px;height:84px;background:var(--surface);border:2px solid var(--ink);border-radius:14px;display:grid;grid-template-columns:repeat(3,1fr);padding:10px;gap:2px;transform:rotate(' + (Math.random() * 14 - 7) + 'deg)' });
    for (var i = 0; i < 9; i++) {
      var dot = T.el('div', { style: 'border-radius:50%;background:' + (DOTS[v].includes(i) ? 'var(--ink)' : 'transparent') + ';' });
      die.appendChild(dot);
    }
    box.appendChild(die);
  });
}
var rolling = false;
function roll() {
  if (rolling) return;
  rolling = true;
  var n = Math.max(1, +count.value || 1);
  var frames = 0;
  var iv = setInterval(function () {
    var vals = [];
    for (var i = 0; i < n; i++) vals.push(1 + Math.floor(Math.random() * 6));
    renderDice(vals);
    frames++;
    if (frames > 12) {
      clearInterval(iv);
      rolling = false;
      var sum = vals.reduce(function (a, b) { return a + b; }, 0);
      total.firstChild.textContent = sum + '（' + vals.join(' + ') + '）';
      history.textContent = '历史：' + (history.textContent.split('历史：')[1] || '') + ' [' + vals.join(',') + ']' + ' '.slice(0, 0);
      var hist = history.textContent;
      if (hist.length > 160) hist = '历史：' + hist.slice(hist.length - 150);
      history.textContent = hist;
    }
  }, 70);
}
app.appendChild(T.row([T.el('span', { text: '骰子数量' }), count, T.button('🎲 摇一摇', roll, true), total]));
app.appendChild(box);
app.appendChild(history);
roll();
setTimeout(function () { rolling = false; }, 100);
''')

d('coin-flip', '翻硬币', '抛硬币随机决策：正面 / 反面，带翻转动画与统计', js=r'''
var coin = T.el('div', { style: 'width:150px;height:150px;border-radius:50%;margin:40px auto;display:flex;align-items:center;justify-content:center;font:700 44px var(--font-serif);background:radial-gradient(circle at 35% 30%, #FFE28A, #D4A017);color:#5C4400;box-shadow:0 8px 24px rgba(0,0,0,.25);transition:transform .12s;user-select:none' });
coin.textContent = '正';
var heads = 0, tails = 0, total = 0;
var stats = T.el('div', { class: 'row', style: 'justify-content:center' });
function render() {
  T.clearEl(stats);
  stats.appendChild(T.stat(total ? Math.round(heads / total * 100) + '%' : '—', '正面'));
  stats.appendChild(T.stat(total ? Math.round(tails / total * 100) + '%' : '—', '反面'));
  stats.appendChild(T.stat(total, '总次数'));
}
var flipping = false;
function flip() {
  if (flipping) return;
  flipping = true;
  var n = 0;
  var iv = setInterval(function () {
    coin.style.transform = 'rotateY(' + (n * 90) + 'deg) scale(' + (1 + Math.sin(n) * 0.08) + ')';
    coin.textContent = n % 2 ? '反' : '正';
    n++;
    if (n > 14) {
      clearInterval(iv);
      var result = Math.random() < 0.5 ? '正' : '反';
      coin.textContent = result;
      coin.style.transform = 'rotateY(0)';
      if (result === '正') heads++;
      else tails++;
      total++;
      render();
      T.toast(result === '正' ? '正面 ✨' : '反面 🌙');
      flipping = false;
    }
  }, 90);
}
coin.addEventListener('click', flip);
app.appendChild(coin);
app.appendChild(T.row([T.button('抛硬币', flip, true), T.button('清空统计', function () { heads = tails = total = 0; render(); })]));
app.appendChild(stats);
render();
''')

d('piano', '在线钢琴', '可弹奏钢琴键盘：鼠标点击 / 键盘按键，WebAudio 合成', js=r'''
var NOTES = [
  { n: 'C4', f: 261.63, key: 'a', black: false }, { n: 'C#4', f: 277.18, key: 'w', black: true },
  { n: 'D4', f: 293.66, key: 's', black: false }, { n: 'D#4', f: 311.13, key: 'e', black: true },
  { n: 'E4', f: 329.63, key: 'd', black: false }, { n: 'F4', f: 349.23, key: 'f', black: false },
  { n: 'F#4', f: 369.99, key: 't', black: true }, { n: 'G4', f: 392.0, key: 'g', black: false },
  { n: 'G#4', f: 415.30, key: 'y', black: true }, { n: 'A4', f: 440.0, key: 'h', black: false },
  { n: 'A#4', f: 466.16, key: 'u', black: true }, { n: 'B4', f: 493.88, key: 'j', black: false },
  { n: 'C5', f: 523.25, key: 'k', black: false }, { n: 'C#5', f: 554.37, key: 'o', black: true },
  { n: 'D5', f: 587.33, key: 'l', black: false }, { n: 'D#5', f: 622.25, key: 'p', black: true },
  { n: 'E5', f: 659.25, key: ';', black: false }
];
var wave = T.select(['sine', 'triangle', 'square', 'sawtooth'], 'triangle');
var volume = T.range(0, 100, 1, 40);
var keyboard = T.el('div', { style: 'position:relative;height:190px;margin:18px 0;user-select:none' });
var keyMap = {};
var whiteIdx = 0;
NOTES.forEach(function (note) {
  var el = T.el('div', { style: 'position:absolute;top:0;bottom:' + (note.black ? 'auto' : '0') + ';height:' + (note.black ? '58%' : '100%') + ';width:' + (note.black ? '5%' : '8.6%') + ';' + (note.black ? 'left:calc(' + (whiteIdx - 0.5) * 8.6 + '% - 2.5%);' : 'left:' + whiteIdx * 8.6 + '%;') + 'background:' + (note.black ? '#222' : '#fff') + ';border:1px solid #999;border-radius:0 0 6px 6px;cursor:pointer;display:flex;align-items:flex-end;justify-content:center;padding-bottom:6px;color:' + (note.black ? '#aaa' : '#888') + ';font-size:11px;box-shadow:0 3px 0 #999;transition:all .06s', text: note.key });
  function press() {
    play(note.f);
    el.style.transform = 'translateY(3px)';
    el.style.boxShadow = 'none';
    setTimeout(function () { el.style.transform = ''; el.style.boxShadow = '0 3px 0 #999'; }, 150);
  }
  el.addEventListener('pointerdown', press);
  keyMap[note.key] = press;
  if (!note.black) whiteIdx++;
  keyboard.appendChild(el);
});
document.addEventListener('keydown', function (e) {
  if (keyMap[e.key] && !e.repeat) keyMap[e.key]();
});
function play(freq) {
  var ctx = new (window.AudioContext || window.webkitAudioContext)();
  var osc = ctx.createOscillator();
  var gain = ctx.createGain();
  osc.type = wave.value;
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(volume.value / 100 * 0.5, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
  osc.connect(gain).connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 1.3);
  osc.onended = function () { ctx.close(); };
}
app.appendChild(T.row([T.el('span', { text: '音色' }), wave, T.el('span', { text: '音量' }), volume]));
app.appendChild(keyboard);
app.appendChild(T.el('p', { text: '键盘按键 a w s e d f t g y h u j k o l p ; 对应琴键（一个半八度）。', style: 'color:var(--ink2);font-size:12px' }));
''')

d('tuner', '调音器', '麦克风实时音高检测：显示频率与最近音名，乐器调音', js=r'''
var status = T.badge('点击启动麦克风');
var freqEl = T.stat('—', 'Hz');
var noteEl = T.stat('—', '最近音');
var centsEl = T.stat('—', '偏差 (cents)');
var bar = T.el('div', { style: 'height:8px;background:var(--line);border-radius:4px;position:relative;margin:20px 0' });
var needle = T.el('div', { style: 'position:absolute;top:-6px;left:50%;width:4px;height:20px;background:var(--accent);border-radius:2px;transition:left .1s' });
bar.appendChild(needle);
var NOTES = [['C', 261.63], ['C#', 277.18], ['D', 293.66], ['D#', 311.13], ['E', 329.63], ['F', 349.23], ['F#', 369.99], ['G', 392.0], ['G#', 415.3], ['A', 440.0], ['A#', 466.16], ['B', 493.88]];
var audioCtx = null, raf = 0;
function detectPitch(buf, sampleRate) {
  var SIZE = buf.length;
  var rms = 0;
  for (var i = 0; i < SIZE; i++) rms += buf[i] * buf[i];
  rms = Math.sqrt(rms / SIZE);
  if (rms < 0.01) return -1;
  var r1 = 0, r2 = SIZE - 1;
  var thres = 0.2;
  for (i = 0; i < SIZE / 2; i++) if (Math.abs(buf[i]) < thres) { r1 = i; break; }
  for (i = 1; i < SIZE / 2; i++) if (Math.abs(buf[SIZE - i]) < thres) { r2 = SIZE - i; break; }
  var buf2 = buf.slice(r1, r2);
  var n = buf2.length;
  var c = new Array(n).fill(0);
  for (i = 0; i < n; i++) for (var j = 0; j < n - i; j++) c[i] += buf[j] * buf[j + i];
  var d = 0;
  while (c[d] > c[d + 1]) d++;
  var maxval = -1, maxpos = -1;
  for (i = d; i < n; i++) {
    if (c[i] > maxval) { maxval = c[i]; maxpos = i; }
  }
  var T0 = maxpos;
  return sampleRate / T0;
}
function tick() {
  if (!audioCtx) return;
  raf = requestAnimationFrame(tick);
}
T.button('启动麦克风', function () {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    var source = audioCtx.createMediaStreamSource(stream);
    var analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);
    var buf = new Float32Array(2048);
    status.textContent = '🎧 监听中…';
    status.className = 'badge ok';
    (function loop() {
      analyser.getFloatTimeDomainData(buf);
      var f = detectPitch(buf, audioCtx.sampleRate);
      if (f > 50 && f < 2000) {
        freqEl.firstChild.textContent = f.toFixed(1);
        var midi = 69 + 12 * Math.log2(f / 440);
        var nearest = Math.round(midi);
        var cents = Math.round((midi - nearest) * 100);
        var name = NOTES[((nearest % 12) + 12) % 12][0] + (Math.floor(nearest / 12) - 1);
        noteEl.firstChild.textContent = name;
        centsEl.firstChild.textContent = (cents > 0 ? '+' : '') + cents;
        needle.style.left = (50 + Math.max(-50, Math.min(50, cents / 2))) + '%';
        needle.style.background = Math.abs(cents) < 10 ? 'var(--ok-text)' : 'var(--err)';
      }
      requestAnimationFrame(loop);
    })();
  }).catch(function (e) { T.toast('无法访问麦克风：' + e.message); });
}, true)
''')

d('chord', '和弦生成器', '常用和弦试听：大三 / 小三 / 七和弦，选调试听琶音与柱式', js=r'''
var root = T.select(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'], 'C');
var CHORD_TYPES = { maj: [4, 7], min: [3, 7], maj7: [4, 7, 11], min7: [3, 7, 10], dom7: [4, 7, 10], dim7: [3, 6, 9] };
var type = T.select([
  { value: 'maj', label: '大三和弦 Major' },
  { value: 'min', label: '小三和弦 Minor' },
  { value: 'maj7', label: '大七 Major7' },
  { value: 'min7', label: '小七 Minor7' },
  { value: 'dom7', label: '属七 Dominant7' },
  { value: 'dim7', label: '减七 Dim7' }
], 'maj');
function intervalsOf() { return CHORD_TYPES[type.value]; }
var base = T.select([{value:'4',label:'C4 基准（261.63Hz）'}],'4');
var status = T.badge('—');
var freqs = [];
function noteFreq(semi) {
  return 261.63 * Math.pow(2, semi / 12);
}
function intervals() {
  var roots = { 'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11 };
  var r = roots[root.value];
  var arr = [r];
  intervalsOf().forEach(function (iv) { arr.push(r + iv); });
  return arr.map(noteFreq);
}
function playChord(freqArr, stagger) {
  var ctx = new (window.AudioContext || window.webkitAudioContext)();
  freqArr.forEach(function (f, i) {
    setTimeout(function () {
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.value = f;
      gain.gain.setValueAtTime(0.18, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.6);
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 1.7);
      osc.onended = function () { if (i === freqArr.length - 1) ctx.close(); };
    }, i * (stagger || 0));
  });
}
app.appendChild(T.row([T.el('span', { text: '根音' }), root, T.el('span', { text: '类型' }), type]));
var names = root.value + ' ' + type.value;
status.textContent = '当前：' + root.value + type.value + ' · ' + intervals().map(function (f) { return f.toFixed(1) + 'Hz'; }).join(' / ');
app.appendChild(status);
app.appendChild(T.row([
  T.button('🎹 柱式（同时）', function () { playChord(intervals(), 0); }, true),
  T.button('琶音（依次）', function () { playChord(intervals(), 160); }),
  T.el('span', { text: '音符：' + (function () {
    var NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    var roots = { 'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11 };
    return [roots[root.value]].concat(intervalsOf().map(function (iv) { return roots[root.value] + iv; })).map(function (s) { return NAMES[s % 12]; }).join(' - ');
  })() })
]));
[root, type].forEach(function (el) {
  el.addEventListener('change', function () {
    status.textContent = '当前：' + root.value + type.value + ' · ' + intervals().map(function (f) { return f.toFixed(1) + 'Hz'; }).join(' / ');
  });
});
''')

d('particles', '漂浮粒子', 'Canvas 粒子动画背景：密度 / 速度 / 连线距离可调，截图可用', js=r'''
var canvas = T.el('canvas', { width: 860, height: 400, style: 'width:100%;border:1px solid var(--line);border-radius:10px;background:var(--code-bg)' });
var count = T.range(20, 200, 10, 80);
var speed = T.range(0.2, 3, 0.1, 0.8);
var linkDist = T.range(40, 200, 10, 120);
var ctx = canvas.getContext('2d');
var parts = [];
function init() {
  parts = [];
  for (var i = 0; i < +count.value; i++) {
    parts.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * +speed.value,
      vy: (Math.random() - 0.5) * +speed.value,
      r: 1 + Math.random() * 2.5
    });
  }
}
function step() {
  ctx.fillStyle = '#111111';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  parts.forEach(function (p, i) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = '#7BC0E5';
    ctx.fill();
    for (var j = i + 1; j < parts.length; j++) {
      var q = parts[j];
      var d = Math.hypot(p.x - q.x, p.y - q.y);
      if (d < +linkDist.value) {
        ctx.strokeStyle = 'rgba(123,192,229,' + (1 - d / linkDist.value) * 0.5 + ')';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.stroke();
      }
    }
  });
  requestAnimationFrame(step);
}
init();
step();
[count, speed, linkDist].forEach(function (el) { el.addEventListener('input', function () { init(); }); });
app.appendChild(canvas);
app.appendChild(T.row([T.el('span', { text: '粒子数' }), count, T.el('span', { text: '速度' }), speed, T.el('span', { text: '连线距离' }), linkDist]));
''')

d('noise', '噪声纹理', 'Canvas 噪声纹理生成：灰度 / 彩色 / 云雾（简单 Perlin 风格）', js=r'''
var mode = T.select([{value:'gray',label:'灰度噪声'},{value:'color',label:'彩色噪声'},{value:'cloud',label:'云雾（平滑）'}],'gray');
var density = T.range(0, 100, 1, 50);
var canvas = T.el('canvas', { width: 480, height: 320, style: 'width:100%;max-width:480px;border:1px solid var(--line);border-radius:10px' });
function valueNoise(w, h, scale) {
  var gw = Math.ceil(w / scale) + 2, gh = Math.ceil(h / scale) + 2;
  var g = [];
  for (var i = 0; i < gw * gh; i++) g.push(Math.random());
  var out = [];
  for (var y = 0; y < h; y++) {
    out[y] = [];
    for (var x = 0; x < w; x++) {
      var gx = x / scale, gy = y / scale;
      var x0 = Math.floor(gx), y0 = Math.floor(gy);
      var fx = gx - x0, fy = gy - y0;
      var sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
      var v = (g[y0 * gw + x0] * (1 - sx) + g[y0 * gw + x0 + 1] * sx) * (1 - sy) +
        (g[(y0 + 1) * gw + x0] * (1 - sx) + g[(y0 + 1) * gw + x0 + 1] * sx) * sy;
      out[y][x] = v;
    }
  }
  return out;
}
function render() {
  var ctx = canvas.getContext('2d');
  var d = ctx.createImageData(canvas.width, canvas.height);
  var cells = [];
  if (mode.value === 'cloud') {
    var base = valueNoise(canvas.width, canvas.height, 64);
    var mid = valueNoise(canvas.width, canvas.height, 24);
    var fine = valueNoise(canvas.width, canvas.height, 8);
    for (var y = 0; y < canvas.height; y++) for (var x = 0; x < canvas.width; x++) {
      var v = base[y][x] * 0.6 + mid[y][x] * 0.28 + fine[y][x] * 0.12;
      var c = Math.round(v * 255);
      var i = (y * canvas.width + x) * 4;
      d.data[i] = c; d.data[i + 1] = c; d.data[i + 2] = c; d.data[i + 3] = 255;
    }
  } else {
    for (y = 0; y < canvas.height; y++) for (x = 0; x < canvas.width; x++) {
      i = (y * canvas.width + x) * 4;
      if (mode.value === 'gray') {
        var g = Math.random() * 255 * (density.value / 100) + 128 * (1 - density.value / 100);
        d.data[i] = d.data[i + 1] = d.data[i + 2] = g;
      } else {
        d.data[i] = Math.random() * 255;
        d.data[i + 1] = Math.random() * 255;
        d.data[i + 2] = Math.random() * 255;
      }
      d.data[i + 3] = 255;
    }
  }
  ctx.putImageData(d, 0, 0);
}
app.appendChild(canvas);
app.appendChild(T.row([mode, T.el('span', { text: '密度（灰度）' }), density,
  T.button('重新生成', render, true),
  T.button('下载 PNG', function () { T.dlCanvas(canvas, 'noise.png'); })]));
render();
''')

d('spectrum', '频谱可视化', '麦克风音频实时频谱（WebAudio AnalyserNode），需授权', js=r'''
var canvas = T.el('canvas', { width: 860, height: 300, style: 'width:100%;border:1px solid var(--line);border-radius:10px;background:var(--code-bg)' });
var status = T.badge('点击启动麦克风');
var mode = T.select([{value:'bar',label:'柱状频谱'},{value:'wave',label:'波形'}],'bar');
var ctx = canvas.getContext('2d');
var audioCtx = null, analyser = null, running = false;
function startMic() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    var source = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);
    status.textContent = '🎤 采集中（对麦克风说话/播放音乐）';
    status.className = 'badge ok';
    if (!running) { running = true; draw(); }
  }).catch(function (e) { T.toast('无法访问麦克风：' + e.message); });
}
function draw() {
  if (!running) return;
  requestAnimationFrame(draw);
  if (!analyser) return;
  ctx.fillStyle = '#111';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  if (mode.value === 'bar') {
    var data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    var bars = 64;
    var bw = canvas.width / bars;
    for (var i = 0; i < bars; i++) {
      var v = data[Math.floor(i * data.length / bars)] / 255;
      var h = v * canvas.height * 0.9;
      var grad = ctx.createLinearGradient(0, canvas.height - h, 0, canvas.height);
      grad.addColorStop(0, '#7BC0E5');
      grad.addColorStop(1, '#1744E8');
      ctx.fillStyle = grad;
      ctx.fillRect(i * bw + 1, canvas.height - h, bw - 2, h);
    }
  } else {
    var wave2 = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(wave2);
    ctx.strokeStyle = '#7BC0E5';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (var j = 0; j < wave2.length; j++) {
      var x = j / wave2.length * canvas.width;
      var y = canvas.height / 2 + (wave2[j] - 128) / 128 * canvas.height * 0.45;
      if (j === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}
app.appendChild(canvas);
app.appendChild(T.row([T.button('启动麦克风', startMic, true), mode, status]));
draw();
''')

d('typing-test', '打字速度测试', '测打字速度（WPM）与准确率：60 秒英文句子挑战', js=r'''
var SENTENCES = [
  'the quick brown fox jumps over the lazy dog',
  'practice makes perfect so keep typing every day',
  'a journey of a thousand miles begins with a single step',
  'actions speak louder than words in every language',
  'free tools for developers make life easier and faster',
  'the best way to predict the future is to create it'
];
var target = SENTENCES[Math.floor(Math.random() * SENTENCES.length)];
var display = T.el('div', { class: 'output', style: 'min-height:80px;font-family:var(--font-sans);font-size:17px;line-height:1.9;white-space:pre-wrap' });
var input = T.textarea('在此输入上方文字（计时从第一个字符开始）…', true);
input.setAttribute('rows', '4');
var wpmEl = T.stat('—', 'WPM');
var accEl = T.stat('—', '准确率');
var timeEl = T.stat('0s', '用时');
var status = T.badge('待开始');
var startTime = 0, timer = 0;
function render() {
  var typed = input.value;
  var html = '';
  for (var i = 0; i < target.length; i++) {
    if (i < typed.length) {
      html += typed[i] === target[i] ? '<span style="color:var(--ok-text)">' + T.esc(target[i]) + '</span>' : '<span style="color:var(--err);background:rgba(192,57,43,.15)">' + T.esc(target[i]) + '</span>';
    } else if (i === typed.length) {
      html += '<span style="background:var(--accent);color:#fff">' + T.esc(target[i]) + '</span>';
    } else html += T.esc(target[i]);
  }
  display.innerHTML = html;
}
input.addEventListener('input', function () {
  if (!startTime && input.value.length) {
    startTime = Date.now();
    timer = setInterval(function () {
      timeEl.firstChild.textContent = Math.round((Date.now() - startTime) / 1000) + 's';
    }, 500);
    status.textContent = '打字中…';
  }
  render();
  var correct = 0;
  for (var i = 0; i < input.value.length; i++) {
    if (input.value[i] === target[i]) correct++;
  }
  var acc = input.value.length ? Math.round(correct / input.value.length * 100) : 100;
  accEl.firstChild.textContent = acc + '%';
  var minutes = (Date.now() - startTime) / 60000;
  if (minutes > 0) wpmEl.firstChild.textContent = Math.round(correct / 5 / minutes);
  if (input.value.length >= target.length) {
    clearInterval(timer);
    status.textContent = acc === 100 ? '🎉 完美完成！' : '完成！准确率 ' + acc + '%';
    status.className = 'badge ok';
  }
});
app.appendChild(T.row([wpmEl, accEl, timeEl, status]));
app.appendChild(display);
app.appendChild(input);
app.appendChild(T.row([T.button('换一句 / 重来', function () {
  target = SENTENCES[Math.floor(Math.random() * SENTENCES.length)];
  input.value = '';
  startTime = 0;
  clearInterval(timer);
  wpmEl.firstChild.textContent = '—';
  accEl.firstChild.textContent = '—';
  timeEl.firstChild.textContent = '0s';
  status.textContent = '待开始';
  render();
}, true)]));
render();
''')

d('pomodoro', '番茄钟', '番茄工作法计时器：25 分钟专注 + 5 分钟休息循环', js=r'''
var workMin = T.num(25, { min: 1, max: 90, style: 'width:70px' });
var breakMin = T.num(5, { min: 1, max: 30, style: 'width:70px' });
var big = T.el('div', { text: '25:00', style: 'font:400 84px/1.2 var(--font-serif);text-align:center;margin:24px 0;font-variant-numeric:tabular-nums' });
var phaseBadge = T.badge('专注阶段');
var cyclesEl = T.stat(0, '完成番茄数');
var mode = 'work';
var remain = 25 * 60;
var timer = 0, running = false, cycles = 0;
function beep() {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 880; gain.gain.value = 0.3;
    osc.start();
    var n = 0;
    var iv = setInterval(function () { n++; if (n > 6) { clearInterval(iv); osc.stop(); ctx.close(); return; } osc.frequency.value = n % 2 ? 660 : 880; }, 220);
  } catch (e) {}
}
function tick() {
  remain--;
  if (remain <= 0) {
    beep();
    if (mode === 'work') {
      cycles++;
      cyclesEl.firstChild.textContent = cycles;
      mode = 'break';
      remain = (+breakMin.value || 5) * 60;
      phaseBadge.textContent = '☕ 休息阶段';
      phaseBadge.className = 'badge blue';
      T.toast('专注完成！休息 ' + breakMin.value + ' 分钟');
    } else {
      mode = 'work';
      remain = (+workMin.value || 25) * 60;
      phaseBadge.textContent = '专注阶段';
      phaseBadge.className = 'badge warn';
      T.toast('休息结束，开始下一个番茄');
    }
  }
  var m = Math.floor(remain / 60), s = remain % 60;
  big.textContent = T.pad2(m) + ':' + T.pad2(s);
  document.title = big.textContent + ' ' + (mode === 'work' ? '专注' : '休息');
}
app.appendChild(T.row([T.el('span', { text: '专注(分)' }), workMin, T.el('span', { text: '休息(分)' }), breakMin, cyclesEl]));
app.appendChild(phaseBadge);
app.appendChild(big);
app.appendChild(T.row([
  T.button('开始 / 暂停', function () {
    running = !running;
    if (running) timer = setInterval(tick, 1000);
    else clearInterval(timer);
  }, true),
  T.button('跳过当前', function () { remain = 1; if (!running) tick(); }),
  T.button('重置', function () {
    clearInterval(timer);
    running = false;
    mode = 'work';
    remain = (+workMin.value || 25) * 60;
    cycles = 0;
    cyclesEl.firstChild.textContent = 0;
    phaseBadge.textContent = '专注阶段';
    phaseBadge.className = 'badge warn';
    big.textContent = T.pad2(Math.floor(remain / 60)) + ':' + T.pad2(remain % 60);
  })
]));
app.appendChild(T.el('p', { text: '经典番茄工作法：25 分钟专注 + 5 分钟休息，每 4 个番茄长休 15 分钟。', style: 'text-align:center;color:var(--ink2);font-size:12px' }));
''')
