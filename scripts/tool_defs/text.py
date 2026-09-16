# -*- coding: utf-8 -*-
"""文本工具类工具定义"""
from .registry import d

d('regex', '正则表达式测试', '在线正则测试：匹配高亮、捕获组、常用标志位', js=r'''
var pattern = T.input('\\b\\w+@\\w+\\.\\w+\\b', { class: 'grow mono', placeholder: '正则表达式（无需斜杠）' });
var flags = T.input('g', { class: 'mono', style: 'width:70px', placeholder: 'flags' });
var input = T.textarea('测试文本…');
input.value = '联系我们：hello@freellm.top 或 support@example.com';
var box = T.el('div', { class: 'output', style: 'min-height:110px;font-family:var(--font-sans)' });
var groupInfo = T.el('div');
function run() {
  T.clearEl(box);
  T.clearEl(groupInfo);
  var v = input.value;
  if (!pattern.value) { box.textContent = v; return; }
  var re;
  try { re = new RegExp(pattern.value, flags.value); }
  catch (e) { box.textContent = '⚠ 正则错误：' + e.message; return; }
  var last = 0, count = 0;
  if (re.global) {
    var m;
    while ((m = re.exec(v)) && count < 500) {
      if (m.index > last) box.appendChild(document.createTextNode(v.slice(last, m.index)));
      var mark = T.el('mark', { text: m[0], style: 'background:var(--accent-soft);color:var(--accent);border-radius:3px;padding:0 2px' });
      mark.title = '第 ' + (count + 1) + ' 处匹配';
      box.appendChild(mark);
      last = m.index + m[0].length;
      if (m[0] === '') re.lastIndex++;
      var groups = m.slice(1);
      if (groups.length) {
        groupInfo.appendChild(T.el('p', { text: '第 ' + (count + 1) + ' 处：' + JSON.stringify(groups), style: 'margin:2px 0;font-family:var(--font-mono);font-size:12px' }));
      }
      count++;
    }
    box.appendChild(document.createTextNode(v.slice(last)));
  } else {
    var m2 = re.exec(v);
    if (m2) {
      box.appendChild(document.createTextNode(v.slice(0, m2.index)));
      box.appendChild(T.el('mark', { text: m2[0], style: 'background:var(--accent-soft);color:var(--accent)' }));
      box.appendChild(document.createTextNode(v.slice(m2.index + m2[0].length)));
      count = 1;
    } else box.textContent = v;
  }
  if (!count) {
    var none = T.el('span', { text: '（无匹配）', style: 'color:var(--ink3)' });
    box.appendChild(none);
  }
}
[pattern, flags, input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.row([T.el('span', { text: '/ ' }), pattern, T.el('span', { text: '/ ' }), flags]));
app.appendChild(T.el('p', { text: '常用：\\d 数字 · \\w 单词字符 · \\s 空白 · + 至少一次 · * 任意次 · ? 可选 · (…) 捕获组 · g 全局 · i 忽略大小写 · m 多行', style: 'color:var(--ink2);font-size:12px' }));
app.appendChild(T.pane([T.field('测试文本', input)], true));
app.appendChild(T.el('span', { text: '匹配预览', class: 'field' }));
app.appendChild(box);
app.appendChild(groupInfo);
run();
''')

d('regex-visual', '正则可视化', '把正则表达式解析成嵌套结构图，帮助理解复杂表达式', js=r'''
var pattern = T.input('^(\\d{4})-(\\d{2})-(?:\\d{2})$', { class: 'grow mono' });
var box = T.el('div', { class: 'output', style: 'min-height:260px;font-family:var(--font-sans);white-space:normal' });
var COLORS = ['#1744E8', '#7BC0E5', '#B8E986', '#FFB88C', '#F48FB1', '#B39DDB'];
var depth = 0;
function esc2(s) { return T.esc(s); }
function box2(label, cls, color) {
  return '<div style="display:inline-block;border:2px solid ' + color + ';border-radius:8px;padding:2px 8px;margin:2px;vertical-align:middle;background:var(--surface)">' +
    '<div style="font-size:10px;color:' + color + ';font-weight:700;letter-spacing:.05em">' + cls + '</div>' +
    '<div style="font-family:var(--font-mono);font-size:13px">' + label + '</div></div>';
}
function render(tokens, colorIdx) {
  var out = '';
  tokens.forEach(function (tk) {
    if (tk.t === 'seq') out += box2(esc2(tk.v), '字面量', 'var(--ink3)');
    else if (tk.t === 'class') out += box2(esc2(tk.v), '字符集', COLORS[1]);
    else if (tk.t === 'group') {
      var label = tk.capture ? '捕获组 ' + tk.n : tk.named ? '命名组' : '非捕获组';
      out += '<div style="display:inline-block;border:2px solid ' + COLORS[colorIdx % COLORS.length] + ';border-radius:10px;padding:4px 10px;margin:2px;vertical-align:middle">' +
        '<div style="font-size:10px;color:' + COLORS[colorIdx % COLORS.length] + ';font-weight:700">' + label + (tk.q || '') + '</div>' +
        '<div>' + render(tk.v, colorIdx + 1) + '</div></div>';
    } else if (tk.t === 'alt') {
      out += '<div style="display:inline-block;border:2px dashed #FFB88C;border-radius:10px;padding:4px 10px;margin:2px;vertical-align:middle">' +
        '<div style="font-size:10px;color:#FFB88C;font-weight:700">或 |</div>' +
        tk.v.map(function (branch) { return '<div style="margin:2px 0">' + render(branch, colorIdx + 1) + '</div>'; }).join('') + '</div>';
    } else if (tk.t === 'anchor') out += box2(esc2(tk.v), '锚点', '#B39DDB');
    else if (tk.t === 'quant') out += box2(esc2(tk.v), '量词', '#B8E986');
    else out += box2(esc2(tk.v), '其他', 'var(--ink3)');
  });
  return out;
}
function parse(re) {
  var tokens = [], i = 0, groupN = 0;
  while (i < re.length) {
    var c = re[i];
    if (c === '\\') {
      tokens.push({ t: 'seq', v: re.substr(i, 2) });
      i += 2;
    } else if (c === '[') {
      var j = re.indexOf(']', i + 1);
      if (j < 0) j = re.length - 1;
      tokens.push({ t: 'class', v: re.slice(i, j + 1) });
      i = j + 1;
    } else if (c === '(') {
      var capture = true, named = false, skip = 1;
      if (re[i + 1] === '?') {
        if (re[i + 2] === ':') { capture = false; skip = 3; }
        else if (re[i + 2] === 'P' || re[i + 2] === '<') { named = true; skip = re[i + 2] === '<' ? 2 : 3; }
        else { capture = false; skip = 3; }
      }
      if (capture) groupN++;
      var d = 1, k = i + skip;
      while (k < re.length && d > 0) {
        if (re[k] === '(') d++;
        if (re[k] === ')') d--;
        k++;
      }
      var inner = re.slice(i + skip, k - 1);
      tokens.push({ t: 'group', v: parse(inner), capture: capture, named: named, n: groupN, q: quantOf(re, k) });
      i = k;
      if (/[+*?{]/.test(re[i] || '')) i += (re[i] === '{' ? (re.indexOf('}', i) - i + 1) : (re[i + 1] === '?' ? 2 : 1));
    } else if (c === '|') {
      var before = tokens;
      var rest = parse(re.slice(i + 1));
      var prevAlt = null;
      tokens = [{ t: 'alt', v: [before].concat(rest.length && rest[0].t === 'alt' ? rest[0].v : [rest]) }];
      i = re.length;
      tokens = [{ t: 'alt', v: [before, rest] }];
      var m2 = tokens[0];
      break;
    } else if (c === '^' || c === '$' || c === '.' || c === '\\b') {
      tokens.push({ t: c === '.' ? 'class' : 'anchor', v: c });
      i++;
    } else if ('+*?'.includes(c) || c === '{') {
      var q = c;
      if (c === '{') { var e2 = re.indexOf('}', i); q = re.slice(i, e2 + 1); i = e2 + 1; } else i++;
      if (re[i] === '?') { q += '?'; i++; }
      if (tokens.length) tokens[tokens.length - 1].q = (tokens[tokens.length - 1].q || '') + ' ' + q;
      else tokens.push({ t: 'quant', v: q });
    } else {
      var s = '';
      while (i < re.length && !'\\[(|+*?{^$.]'.includes(re[i])) { s += re[i]; i++; }
      if (!s) { s = re[i]; i++; }
      tokens.push({ t: 'seq', v: s });
    }
  }
  return tokens;
}
function quantOf(re, pos) {
  var c = re[pos];
  if (c === '+' || c === '*' || c === '?') return c;
  if (c === '{') return re.slice(pos, re.indexOf('}', pos) + 1);
  return '';
}
function run() {
  try {
    new RegExp(pattern.value);
  } catch (e) { box.innerHTML = '<span style="color:var(--err)">⚠ 正则错误：' + T.esc(e.message) + '</span>'; return; }
  depth = 0;
  box.innerHTML = render(parse(pattern.value), 0);
}
pattern.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '正则' }), pattern]));
app.appendChild(box);
app.appendChild(T.el('p', { text: '支持：字面量、字符集、捕获/非捕获/命名组、或分支、量词、锚点。嵌套越深颜色越丰富。', style: 'color:var(--ink2);font-size:12px' }));
run();
''')

d('markdown', 'Markdown 编辑器', '在线 Markdown 编辑与实时预览，导出 HTML', js=r'''
var input = T.textarea('#欢迎使用 FreeLLM 编辑器\n\n在左侧输入 **Markdown**，右侧实时预览。\n\n- 支持 标题/列表/表格/代码\n- 导出 HTML 文件', true);
input.value = '#欢迎使用 FreeLLM 编辑器\n\n在左侧输入 **Markdown**，右侧实时预览。\n\n- 支持 标题/列表/表格/代码\n- 导出 HTML 文件';
input.style.minHeight = '320px';
var frame = T.el('iframe', { sandbox: '', style: 'width:100%;height:356px;border:1px solid var(--line);border-radius:8px;background:#fff' });
var STYLE = 'body{font:14px/1.7 -apple-system,system-ui,sans-serif;color:#2F3437;padding:16px;max-width:760px;margin:0 auto}pre{background:#f6f6f4;padding:12px;border-radius:8px;overflow:auto}code{font-family:ui-monospace,Consolas,monospace;font-size:.9em}blockquote{margin:0;padding:2px 14px;border-left:3px solid #ddd;color:#787774}table{border-collapse:collapse}th,td{border:1px solid #e5e5e2;padding:6px 12px}h1,h2{border-bottom:1px solid #eee;padding-bottom:6px}img{max-width:100%}';
function run() {
  try { frame.srcdoc = '<style>' + STYLE + '</style>' + LF.md2html(input.value); }
  catch (e) { frame.srcdoc = '<pre>' + T.esc(e.message) + '</pre>'; }
}
input.addEventListener('input', T.debounce(run, 200));
app.appendChild(T.pane([T.field('编辑区', input), T.el('div', { class: 'field' }, [T.el('span', { text: '预览' }), frame])]));
app.appendChild(T.row([T.button('复制 HTML', function () { T.copy(LF.md2html(input.value)); }),
  T.button('下载 .html', function () { T.download('document.html', '<!doctype html><meta charset="utf-8"><style>' + STYLE + '</style>' + LF.md2html(input.value), 'text/html'); }, true),
  T.button('下载 .md', function () { T.download('document.md', input.value, 'text/markdown'); })]));
run();
''')

d('word-count', '字数统计', '字符 / 单词 / 中文字 / 行 / 段落计数，预估阅读时长', js=r'''
var input = T.textarea('在此粘贴或输入文本…');
var box = T.el('div', { class: 'row' });
var stats = T.el('div');
function run() {
  var v = input.value;
  var chars = v.length;
  var noSpace = v.replace(/\s/g, '').length;
  var cn = (v.match(/[\u4e00-\u9fff]/g) || []).length;
  var en = (v.match(/[a-zA-Z]+/g) || []).length;
  var lines = v ? v.split('\n').length : 0;
  var paras = v.trim() ? v.trim().split(/\n\s*\n/).length : 0;
  var words = en + Math.ceil(cn / 2);
  var minutes = Math.max(1, Math.round(words / 400));
  var arr = [[chars, '字符'], [noSpace, '字符(不含空格)'], [cn, '中文字符'], [en, '英文单词'], [lines, '行数'], [paras, '段落'], ['约 ' + minutes + ' 分钟', '阅读时长']];
  T.clearEl(box);
  arr.forEach(function (p) { box.appendChild(T.stat(p[0], p[1])); });
}
input.addEventListener('input', T.debounce(run, 150));
app.appendChild(T.pane([T.field('文本', input)], true));
app.appendChild(box);
run();
''')

d('diff', '文本对比', '两段文本逐行对比，差异行高亮标注', js=r'''
var aIn = T.textarea('原始文本…\n第二行');
aIn.value = '原始文本…\n第二行';
var bIn = T.textarea('修改后文本…\n第二行');
bIn.value = '修改后文本…\n第二行';
aIn.style.minHeight = '140px';
bIn.style.minHeight = '140px';
var box = T.el('div', { class: 'output', style: 'min-height:160px;font-family:var(--font-sans);white-space:pre' });
var summary = T.badge('—');
function run() {
  T.clearEl(box);
  var ops = LF.Diff.diff(aIn.value, bIn.value);
  var add = 0, del = 0, same = 0;
  ops.forEach(function (o) {
    var line;
    if (o.t === '=') { same++; line = T.el('div', { text: '  ' + o.a, style: 'padding:0 6px' }); }
    else if (o.t === '-') { del++; line = T.el('div', { text: '- ' + o.a, style: 'background:rgba(192,57,43,.12);color:var(--err);padding:0 6px' }); }
    else { add++; line = T.el('div', { text: '+ ' + o.a, style: 'background:var(--ok-bg);color:var(--ok-text);padding:0 6px' }); }
    box.appendChild(line);
  });
  summary.textContent = same + ' 相同 · ' + add + ' 新增 · ' + del + ' 删除';
  summary.className = 'badge ' + (add + del ? 'warn' : 'ok');
}
[aIn, bIn].forEach(function (el) { el.addEventListener('input', T.debounce(run, 250)); });
app.appendChild(T.pane([T.field('文本 A（原）', aIn), T.field('文本 B（改）', bIn)]));
app.appendChild(T.row([summary]));
app.appendChild(T.el('span', { text: '差异', class: 'field' }));
app.appendChild(box);
run();
''')

d('case-convert', '大小写转换', '全大写 / 全小写 / 首字母大写 / 句首大写 / 交换大小写', js=r'''
var input = T.textarea('hello freeLLM Tools');
input.value = 'hello freeLLM Tools';
var output = T.out('');
var MODES = [
  ['全大写 UPPER', function (s) { return s.toUpperCase(); }],
  ['全小写 lower', function (s) { return s.toLowerCase(); }],
  ['标题 Title Case', function (s) { return s.toLowerCase().replace(/(^|\s)\w/g, function (c) { return c.toUpperCase(); }); }],
  ['句首 Sentence case', function (s) { return s.toLowerCase().replace(/(^\s*\w|[.!?]\s+\w)/g, function (c) { return c.toUpperCase(); }); }],
  ['交换 SwapCASE', function (s) { return s.replace(/\w/g, function (c) { return c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase(); }); }]
];
function apply(fn) {
  output.value = fn(input.value);
  output._lastFn = fn;
}
var row = T.el('div', { class: 'row' });
MODES.forEach(function (m) {
  row.appendChild(T.button(m[0], function () { apply(m[1]); }));
});
input.addEventListener('input', function () { if (output._lastFn) apply(output._lastFn); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(row);
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
apply(MODES[0][1]);
''')

d('camel-convert', '变量名转换', 'camelCase / PascalCase / snake_case / kebab-case / CONSTANT_CASE 互转', js=r'''
var input = T.input('userProfileData', { class: 'grow mono' });
var box = T.el('div', { class: 'pane single' });
function words(s) {
  return s.replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    .split(/[\s_\-\.]+/)
    .filter(Boolean)
    .map(function (w) { return w.toLowerCase(); });
}
function run() {
  var w = words(input.value.trim());
  if (!w.length) { T.clearEl(box); return; }
  var camel = w[0] + w.slice(1).map(function (x) { return x[0].toUpperCase() + x.slice(1); }).join('');
  var pascal = w.map(function (x) { return x[0].toUpperCase() + x.slice(1); }).join('');
  var snake = w.join('_');
  var kebab = w.join('-');
  var constant = w.join('_').toUpperCase();
  T.clearEl(box).appendChild(T.kvTable([
    ['camelCase', camel], ['PascalCase', pascal], ['snake_case', snake],
    ['kebab-case', kebab], ['CONSTANT_CASE', constant]
  ]));
}
input.addEventListener('input', run);
app.appendChild(T.row([T.el('span', { text: '变量名' }), input, T.el('span', { text: '输入任意命名风格自动识别分词' })]));
app.appendChild(box);
app.appendChild(T.row([T.button('复制全部', function () {
  var rows = Array.from(box.querySelectorAll('tr')).map(function (tr) {
    var tds = tr.querySelectorAll('td');
    return tds[0].textContent + ' = ' + tds[1].textContent;
  });
  T.copy(rows.join('\n'));
})]));
run();
''')

d('pinyin', '汉字转拼音', '离线拼音字典（含声调），支持多音字取常用音、无声调数字模式', js=r'''
var input = T.textarea('免费 AI 资源导航');
input.value = '免费 AI 资源导航';
var output = T.out('');
var mode = T.select([{value:'tone',label:'带声调 (pīn yīn)'},{value:'num',label:'声调数字 (pin1 yin1)'},{value:'none',label:'无声调 (pin yin)'}],'tone');
var sep = T.select([{value:' ',label:'空格分隔'},{value:"'",label:"连字符 '"},{value:'',label:'无分隔'}],' ');
var status = T.badge('页面就绪后后台加载字典…');
var DICT = null;
function loadDict() {
  fetch('/tools/data/pinyin.json').then(function (r) { return r.json(); }).then(function (d) {
    DICT = d;
    status.textContent = '字典就绪（' + Object.keys(d).length + ' 字）';
    status.className = 'badge ok';
    run();
  });
}
if (document.readyState === 'complete') loadDict();
else window.addEventListener('load', loadDict);
function stripTone(p) {
  var map = { 'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a', 'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e', 'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i', 'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o', 'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u', 'ü': 'v', 'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ń': 'n', 'ň': 'n', 'ǹ': 'n', 'ḿ': 'm' };
  return p.replace(/[āáǎàēéěèīíǐìōóǒòūúǔùüǖǘǚǜńňǹḿ]/g, function (c) { return map[c] || c; });
}
function run() {
  if (!DICT || !input.value) { output.value = ''; return; }
  var out = [];
  Array.from(input.value).forEach(function (ch) {
    if (/[\u4e00-\u9fff]/.test(ch)) {
      var p = DICT[ch];
      if (!p) { out.push(ch); return; }
      if (mode.value === 'num') {
        var m = p.match(/[āáǎàēéěèīíǐìōóǒòūúǔùüǖǘǚǜ]/);
        var toneMap = { 'ā': 1, 'á': 2, 'ǎ': 3, 'à': 4, 'ē': 1, 'é': 2, 'ě': 3, 'è': 4, 'ī': 1, 'í': 2, 'ǐ': 3, 'ì': 4, 'ō': 1, 'ó': 2, 'ǒ': 3, 'ò': 4, 'ū': 1, 'ú': 2, 'ǔ': 3, 'ù': 4, 'ǖ': 1, 'ǘ': 2, 'ǚ': 3, 'ǜ': 4 };
        out.push(stripTone(p) + (m ? toneMap[m[0]] : ''));
      } else if (mode.value === 'none') out.push(stripTone(p));
      else out.push(p);
    } else if (/\n/.test(ch)) out.push('\n');
    else out.push(ch);
  });
  output.value = out.join(sep.value === ' ' ? ' ' : sep.value).replace(/ +/g, ' ');
}
input.addEventListener('input', T.debounce(run, 200));
[mode, sep].forEach(function (el) { el.addEventListener('change', run); });
app.appendChild(T.pane([T.field('中文文本', input), T.field('拼音', output)]));
app.appendChild(T.row([mode, sep, status, T.btnCopy(function () { return output.value; })]));
''')

d('full-half', '全角半角转换', '全角字符 ↔ 半角字符互转（字母数字标点空格）', js=r'''
var input = T.textarea('Ｈｅｌｌｏ　Ｗｏｒｌｄ！１２３');
input.value = 'Ｈｅｌｌｏ　Ｗｏｒｌｄ！１２３';
var output = T.out('');
var mode = T.select([{value:'h2f',label:'半角 → 全角'},{value:'f2h',label:'全角 → 半角'}],'f2h');
function run() {
  var v = input.value;
  if (mode.value === 'f2h') {
    output.value = v.replace(/[\uFF01-\uFF5E]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); })
      .replace(/\u3000/g, ' ');
  } else {
    output.value = v.replace(/[\x20-\x7E]/g, function (c) {
      if (c === ' ') return '\u3000';
      return String.fromCharCode(c.charCodeAt(0) + 0xFEE0);
    });
  }
}
[input, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, T.btnCopy(function () { return output.value; })]));
run();
''')

d('simp-trad', '简繁体转换', '简体 ↔ 繁体中文互转（离线字级映射，覆盖常用汉字）', js=r'''
var input = T.textarea('免费工具，在线使用，无需安装。');
input.value = '免费工具，在线使用，无需安装。';
var output = T.out('');
var mode = T.select([{value:'s2t',label:'简 → 繁'},{value:'t2s',label:'繁 → 简'}],'s2t');
var status = T.badge('页面就绪后后台加载映射…');
var MAP = null;
function loadMap() {
  fetch('/tools/data/s2t.json').then(function (r) { return r.json(); }).then(function (d) {
    MAP = d;
    status.textContent = '映射就绪（简→繁 ' + Object.keys(d.s2t).length + ' 字）';
    status.className = 'badge ok';
    run();
  });
}
if (document.readyState === 'complete') loadMap();
else window.addEventListener('load', loadMap);
function run() {
  if (!MAP || !input.value) { output.value = ''; return; }
  var map = mode.value === 's2t' ? MAP.s2t : MAP.t2s;
  output.value = Array.from(input.value).map(function (ch) { return map[ch] || ch; }).join('');
}
input.addEventListener('input', T.debounce(run, 200));
app.appendChild(T.pane([T.field('文本', input), T.field('输出', output)]));
app.appendChild(T.row([mode, status, T.btnCopy(function () { return output.value; }),
  T.el('span', { text: '字级转换，个别词汇差异（如 软件/軟體）需人工校对' })]));
''')

d('figlet', 'ASCII 艺术字', 'FIGlet 风格大字：英文与数字转 5 行块状 ASCII 字符画', js=r'''
var input = T.input('FreeLLM', { class: 'grow mono', placeholder: '输入英文 / 数字…' });
var fill = T.select(['█', '#', '@', '*', '$', '%'], '█');
var output = T.out('');
output.style.minHeight = '160px';
function run() {
  var r = LU.figlet(input.value, fill.value);
  output.value = r.art + (r.unknown.length ? '\n（未支持字符：' + r.unknown.join(' ') + '，以 ? 显示）' : '');
}
[input, fill].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('文本', input)], true));
app.appendChild(T.row([T.el('span', { text: '填充字符' }), fill, T.btnCopy(function () { return output.value; })]));
app.appendChild(output);
run();
''')

d('slug', 'URL Slug 生成', 'SEO 友好 URL 路径：中文转拼音、小写、连字符', js=r'''
var input = T.textarea('免费 AI 资源导航 Best Free Tools!');
input.value = '免费 AI 资源导航 Best Free Tools!';
var output = T.out('');
var sep = T.select([{value:'-',label:'连字符 -'},{value:'_',label:'下划线 _'}],'-');
var keepCn = T.check('中文转 URL 编码（否则移除）');
var PINYIN = null;
function loadPY() {
  fetch('/tools/data/pinyin.json').then(function (r) { return r.json(); }).then(function (d) { PINYIN = d; run(); });
}
if (document.readyState === 'complete') loadPY();
else window.addEventListener('load', loadPY);
function toSlug(s) {
  var parts = [];
  var buf = '';
  Array.from(s.toLowerCase()).forEach(function (ch) {
    if (/[a-z0-9]/.test(ch)) buf += ch;
    else if (/[\u4e00-\u9fff]/.test(ch)) {
      if (PINYIN && PINYIN[ch]) buf += PINYIN[ch].normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ü/g, 'v');
      else if (keepCn._input.checked) buf += encodeURIComponent(ch);
    }
    else {
      if (buf) { parts.push(buf); buf = ''; }
    }
  });
  if (buf) parts.push(buf);
  return parts.join(sep.value);
}
function run() {
  output.value = toSlug(input.value);
}
input.addEventListener('input', T.debounce(run, 200));
app.appendChild(T.pane([T.field('标题 / 文本', input), T.field('URL Slug', output)]));
app.appendChild(T.row([sep, keepCn, T.btnCopy(function () { return output.value; }),
  T.el('span', { text: '中文自动转拼音（无声调）' })]));
''')

d('bionic-reading', 'Bionic Reading', '单词前部加粗，提升英文阅读速度与专注度', js=r'''
var input = T.textarea('Bionic Reading helps you read faster by guiding your eyes with bolded word beginnings.');
input.value = 'Bionic Reading helps you read faster by guiding your eyes with bolded word beginnings.';
var box = T.el('div', { class: 'output', style: 'min-height:140px;font-family:var(--font-sans);font-size:16px;line-height:1.9;white-space:pre-wrap' });
var strength = T.select([{value:'0.4',label:'40% 加粗（推荐）'},{value:'0.6',label:'60% 加粗'},{value:'0.25',label:'25% 加粗'}],'0.4');
function run() {
  var html = input.value.replace(/([A-Za-z']+)/g, function (w) {
    var n = Math.max(1, Math.round(w.length * +strength.value));
    return '<b>' + T.esc(w.slice(0, n)) + '</b>' + T.esc(w.slice(n));
  });
  box.innerHTML = html;
}
input.addEventListener('input', run);
app.appendChild(T.pane([T.field('英文文本', input)], true));
app.appendChild(T.row([T.el('span', { text: '加粗比例' }), strength]));
app.appendChild(T.el('span', { text: '预览', class: 'field' }));
app.appendChild(box);
run();
''')

d('html-filter', 'HTML 标签过滤', '保留或移除指定 HTML 标签，净化网页片段', js=r'''
var input = T.textarea('<div><p>段落 <b>加粗</b></p><span style="color:red">样式</span><a href="https://x.com">链接</a></div>', true);
input.value = '<div><p>段落 <b>加粗</b></p><span style="color:red">样式</span><a href="https://x.com">链接</a></div>';
input.value = '<div><p>段落 <b>加粗</b></p><span style="color:red">样式</span><a href="https://x.com">链接</a></div>';
var output = T.out('');
var mode = T.select([{value:'strip',label:'移除指定标签（保留内容）'},{value:'strip-all',label:'移除全部标签'},{value:'keep',label:'仅保留指定标签'}],'strip-all');
var tags = T.input('script,style', { class: 'grow mono', placeholder: '标签名，逗号分隔' });
function run() {
  var v = input.value;
  var list = tags.value.split(/[\s,]+/).filter(Boolean).map(function (t) { return t.toLowerCase(); });
  try {
    if (mode.value === 'strip-all') {
      output.value = v.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
    } else if (mode.value === 'strip') {
      list.forEach(function (t) {
        v = v.replace(new RegExp('<' + t + '(\\s[^>]*)?>[\\s\\S]*?</' + t + '>', 'gi'), '')
          .replace(new RegExp('<' + t + '(\\s[^>]*)?/?>', 'gi'), '');
      });
      output.value = v;
    } else {
      var doc = new DOMParser().parseFromString('<div>' + v + '</div>', 'text/html');
      var walk = function (node) {
        var out = '';
        Array.from(node.childNodes).forEach(function (c) {
          if (c.nodeType === 3) { out += T.esc(c.nodeValue); return; }
          if (c.nodeType !== 1) return;
          var tag = c.tagName.toLowerCase();
          if (list.includes(tag)) {
            var attrs = Array.from(c.attributes).map(function (a) { return ' ' + a.name + '="' + T.esc(a.value) + '"'; }).join('');
            out += '<' + tag + attrs + '>' + walk(c) + '</' + tag + '>';
          } else out += walk(c);
        });
        return out;
      };
      output.value = walk(doc.body.firstChild);
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode, tags].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('HTML', input), T.field('输出', output)]));
app.appendChild(T.row([mode, T.el('span', { text: '标签' }), tags, T.btnCopy(function () { return output.value; })]));
run();
''')

d('fanyi', '翻译助手', '多语言在线翻译（MyMemory 免费接口，需联网）', js=r'''
var input = T.textarea('你好，世界！');
input.value = '你好，世界！';
var output = T.out('');
var from = T.select([{value:'zh-CN',label:'中文'},{value:'en',label:'English'},{value:'ja',label:'日本語'},{value:'ko',label:'한국어'},{value:'fr',label:'Français'},{value:'de',label:'Deutsch'},{value:'es',label:'Español'},{value:'ru',label:'Русский'}],'zh-CN');
var to = T.select([{value:'en',label:'English'},{value:'zh-CN',label:'中文'},{value:'ja',label:'日本語'},{value:'ko',label:'한국어'},{value:'fr',label:'Français'},{value:'de',label:'Deutsch'},{value:'es',label:'Español'},{value:'ru',label:'Русский'}],'en');
var swap = T.button('⇄ 交换语言', function () {
  var f = from.value;
  from.value = to.value;
  to.value = f;
  var tmp = input.value;
  input.value = output.value;
  output.value = tmp;
});
var status = T.badge('—');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  status.textContent = '翻译中…';
  var pair = from.value + '|' + to.value;
  fetch('https://api.mymemory.translated.net/get?q=' + encodeURIComponent(v.slice(0, 500)) + '&langpair=' + pair)
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.responseData && d.responseData.translatedText) {
        output.value = d.responseData.translatedText;
        status.textContent = '✓ 完成';
        status.className = 'badge ok';
      } else {
        output.value = '';
        status.textContent = '翻译失败';
        status.className = 'badge warn';
      }
    })
    .catch(function () {
      status.textContent = '网络不可用（接口需联网）';
      status.className = 'badge warn';
    });
}
input.addEventListener('input', T.debounce(run, 600));
app.appendChild(T.pane([T.field('原文', input), T.field('译文', output)]));
app.appendChild(T.row([T.el('span', { text: '从' }), from, swap, T.el('span', { text: '到' }), to, T.button('翻译', run, true), T.btnCopy(function () { return output.value; })]));
app.appendChild(T.row([status, T.el('span', { text: '由 MyMemory 免费翻译接口提供，单次最长 500 字符' })]));  // 不自动请求：联网接口留给用户主动触发
''')

d('text-clean', '文本清理', '去除多余空行 / 空格 / 特殊字符 / 表情符号', js=r'''
var input = T.textarea('  多余　空格　与\n\n\n\n空行…①②③ test🎉  ');
input.value = '  多余　空格　与\n\n\n\n空行…①②③ test🎉  ';
var output = T.out('');
var o1 = T.check('合并连续空白', true);
var o2 = T.check('压缩连续空行为一段', true);
var o3 = T.check('去除行首尾空白', true);
var o4 = T.check('去除全角空格', true);
var o5 = T.check('去除 Emoji/表情');
var o6 = T.check('去除中文标点间多余空格', true);
function run() {
  var v = input.value;
  if (o5._input.checked) v = v.replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, '');
  if (o1._input.checked) v = v.replace(/[ \t]{2,}/g, ' ');
  if (o4._input.checked) v = v.replace(/\u3000/g, ' ');
  if (o3._input.checked) v = v.split('\n').map(function (l) { return l.replace(/^\s+|\s+$/g, ''); }).join('\n');
  if (o2._input.checked) v = v.replace(/\n{3,}/g, '\n\n');
  if (o6._input.checked) v = v.replace(/([\u4e00-\u9fff，。！？；：、])\s+([\u4e00-\u9fff，。！？；：、])/g, '$1$2');
  output.value = v;
}
[o1._input, o2._input, o3._input, o4._input, o5._input, o6._input].forEach(function (el) { el.addEventListener('change', run); });
input.addEventListener('input', T.debounce(run, 250));
var wrap1 = T.row([o1, o2, o3]); wrap1.style.marginBottom = '4px';
var wrap2 = T.row([o4, o5, o6]); wrap2.style.marginBottom = '4px';
app.appendChild(T.pane([T.field('原文', input), T.field('清理结果', output)]));
app.appendChild(wrap1);
app.appendChild(wrap2);
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('text-similarity', '文本相似度', '两段文本相似度对比（字符二元组 Dice 系数 + 共同片段）', js=r'''
var aIn = T.textarea('FreeLLM 收录了免费的 AI 模型与工具。');
aIn.value = 'FreeLLM 收录了免费的 AI 模型与工具。';
var bIn = T.textarea('FreeLLM 收录免费 AI 模型、工具和资源。');
bIn.value = 'FreeLLM 收录免费 AI 模型、工具和资源。';
var ratio = T.badge('—');
var box = T.el('div');
function run() {
  var s = LF.Diff.similarity(aIn.value, bIn.value);
  ratio.textContent = '相似度 ' + (s * 100).toFixed(1) + '%';
  ratio.className = 'badge ' + (s > 0.8 ? 'ok' : s > 0.5 ? 'blue' : 'warn');
  T.clearEl(box);
  var ops = LF.Diff.diff(aIn.value, bIn.value);
  var lines = [];
  ops.forEach(function (o) {
    if (o.t === '=') lines.push(o.a);
    else if (o.t === '-') lines.push('【删：' + o.a + '】');
    else lines.push('【增：' + o.a + '】');
  });
  box.appendChild(T.el('div', { class: 'output', style: 'min-height:100px;font-family:var(--font-sans);white-space:pre-wrap', text: lines.join('') }));
}
[aIn, bIn].forEach(function (el) { el.addEventListener('input', T.debounce(run, 250)); });
app.appendChild(T.pane([T.field('文本 A', aIn), T.field('文本 B', bIn)]));
app.appendChild(T.row([ratio]));
app.appendChild(box);
run();
''')

d('keyword-extract', '关键词提取', '词频统计与 TF 加权关键词提取（中英文均可）', js=r'''
var input = T.textarea('免费 AI 工具是开发者的好帮手。AI 工具包含 AI 编码、AI 搜索等。免费的 AI 资源导航收录了大量免费 AI 工具。');
input.value = '免费 AI 工具是开发者的好帮手。AI 工具包含 AI 编码、AI 搜索等。免费的 AI 资源导航收录了大量免费 AI 工具。';
var topN = T.num(12, { min: 3, max: 50, style: 'width:70px' });
var box = T.el('div');
var STOP_EN = new Set('the a an and or of to in on for with is are was were be been it its this that as at by from'.split(' '));
var STOP_CN = new Set('的了和是与及在对于上下的有无需个'.split(''));
function extract(text) {
  var freq = {};
  var enWords = text.toLowerCase().match(/[a-z]{2,}/g) || [];
  enWords.forEach(function (w) {
    if (STOP_EN.has(w)) return;
    freq[w] = (freq[w] || 0) + 2;
  });
  var cnRuns = text.match(/[\u4e00-\u9fff]+/g) || [];
  cnRuns.forEach(function (run) {
    for (var n = 2; n <= 3; n++) {
      for (var i = 0; i + n <= run.length; i++) {
        var g = run.slice(i, i + n);
        if (STOP_CN.has(g[0]) || STOP_CN.has(g[g.length - 1])) continue;
        freq[g] = (freq[g] || 0) + (n === 2 ? 1.2 : 1);
      }
    }
    Array.from(run).forEach(function (ch) {
      if (!STOP_CN.has(ch)) freq[ch] = (freq[ch] || 0) + 0.3;
    });
  });
  return Object.keys(freq).map(function (k) { return [k, freq[k]]; })
    .sort(function (a, b) { return b[1] - a[1]; });
}
function run() {
  var list = extract(input.value).slice(0, +topN.value || 12);
  var max = list.length ? list[0][1] : 1;
  T.clearEl(box);
  if (!list.length) return;
  box.appendChild(T.refTable(['关键词', '权重', '强度'], list.map(function (p) {
    return [p[0], p[1].toFixed(1), '█'.repeat(Math.max(1, Math.round(p[1] / max * 20)))];
  })));
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('文本', input)], true));
app.appendChild(T.row([T.el('span', { text: 'Top N' }), topN]));
app.appendChild(box);
run();
''')

d('spell-check', '拼写检查', '英文拼写检查：浏览器原生校对 + 常见拼写错误模式 + 重复词检测', js=r'''
var input = T.textarea('Thsi is a tset of teh spell checker. I I like free tools.');
input.value = 'Thsi is a tset of teh spell checker. I I like free tools.';
var box = T.el('div');
var note = T.el('div', { class: 'msg', style: 'background:var(--accent-soft);color:var(--accent)' });
note.textContent = '下方输入框已启用浏览器原生拼写校对（红色下划线）。此外自动检测：重复单词、i 未大写、常见错拼模式。';
var checkArea = T.el('textarea', { rows: '6', spellcheck: 'true', style: 'width:100%' });
checkArea.value = input.value;
checkArea.addEventListener('input', function () { input.value = checkArea.value; run(); });
var TYPOS = { teh: 'the', recieve: 'receive', seperate: 'separate', definately: 'definitely', occured: 'occurred', untill: 'until', wich: 'which', becuase: 'because', accomodate: 'accommodate', embarass: 'embarrass', goverment: 'government', tommorow: 'tomorrow', lenght: 'length', wiht: 'with', thier: 'their', freind: 'friend', beleive: 'believe', acheive: 'achieve', calender: 'calendar', occurence: 'occurrence' };
function run() {
  T.clearEl(box);
  var v = checkArea.value;
  var issues = [];
  var tokens = v.match(/[A-Za-z']+|\s+|[^\sA-Za-z']+/g) || [];
  var prevWord = '';
  tokens.forEach(function (tk, i) {
    var low = tk.toLowerCase();
    if (TYPOS[low]) issues.push(['错拼「' + tk + '」→ 建议 ' + TYPOS[low], '…' + v.slice(Math.max(0, v.indexOf(tk) - 20), v.indexOf(tk) + 20) + '…']);
    else if (/^[a-z]+$/.test(tk) && tk === 'i') issues.push(['字母 i 应大写', '第 ' + i + ' 个词']);
    if (/^[A-Za-z]+$/.test(tk) && low === prevWord.toLowerCase()) issues.push(['重复单词「' + tk + '」', '连续出现']);
    if (/^[A-Za-z']+$/.test(tk)) prevWord = tk; else prevWord = '';
  });
  var words = (v.match(/[A-Za-z']+/g) || []);
  box.appendChild(T.el('p', { text: '共 ' + words.length + ' 个英文单词，发现 ' + issues.length + ' 个疑似问题', style: 'color:var(--ink2)' }));
  if (issues.length) {
    box.appendChild(T.refTable(['问题', '上下文'], issues));
  } else {
    box.appendChild(T.msg('✓ 未发现常见拼写问题', 'ok'));
  }
}
app.appendChild(note);
app.appendChild(T.pane([T.field('检查文本（已启用浏览器拼写校对）', checkArea)], true));
app.appendChild(box);
run();
''')
