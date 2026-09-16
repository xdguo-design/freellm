# -*- coding: utf-8 -*-
"""格式化类工具定义"""
from .registry import d

d('json', 'JSON 格式化', 'JSON 美化 / 压缩 / 校验，错误定位到行列', js=r'''
var input = T.textarea('粘贴 JSON…');
var output = T.out('');
var indent = T.select([{value:'2',label:'2 空格'},{value:'4',label:'4 空格'},{value:'tab',label:'Tab'}],'2');
var status = T.badge('—');
function fmt(v) {
  var n = +v;
  return JSON.stringify(T.parseJSON(input.value), null, v === 'tab' ? '\t' : n);
}
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; status.textContent = '—'; return; }
  try {
    var obj = JSON.parse(v);
    output.value = JSON.stringify(obj, null, indent.value === 'tab' ? '\t' : +indent.value);
    status.textContent = '✓ 合法 JSON';
    status.className = 'badge ok';
  } catch (e) {
    output.value = '';
    var m = e.message.match(/position (\d+)/);
    if (m) {
      var pos = +m[1];
      var before = v.slice(0, pos);
      var line = before.split('\n').length;
      var col = pos - before.lastIndexOf('\n');
      status.textContent = '✗ 语法错误：第 ' + line + ' 行第 ' + col + ' 列附近';
    } else status.textContent = '✗ ' + e.message;
    status.className = 'badge warn';
  }
}
input.addEventListener('input', T.debounce(run, 250));
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([T.el('span', { text: '缩进' }), indent,
  T.button('压缩为单行', function () {
    try { output.value = JSON.stringify(T.parseJSON(input.value)); status.textContent = '✓ 已压缩'; status.className = 'badge ok'; }
    catch (e) { T.toast(e.message); }
  }),
  T.button('转义为字符串', function () { T.copy(JSON.stringify(input.value)); }),
  T.btnCopy(function () { return output.value; }), status]));
run();
''')

d('sql-formatter', 'SQL 格式化', 'SQL 语句美化：关键字大写、子句换行缩进', js=r'''
var input = T.textarea('SELECT * FROM users WHERE age > 18 ORDER BY id;…');
var output = T.out('');
function run() {
  if (!input.value.trim()) { output.value = ''; return; }
  try { output.value = LF.sqlFormat(input.value); }
  catch (e) { output.value = '⚠ ' + e.message; }
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('SQL', input), T.field('格式化结果', output)]));
app.appendChild(T.row([T.btnCopy(function () { return output.value; }),
  T.el('span', { text: '支持 SELECT/INSERT/UPDATE/DELETE/JOIN/UNION 等常用子句' })]));
input.value = 'select u.id,u.name,o.total from users u left join orders o on u.id=o.user_id where o.total>100 and u.status=1 group by u.id order by o.total desc limit 20;';
run();
''')

d('code-formatter', '代码格式化', 'HTML / CSS / JS / JSON 代码缩进美化（轻量规则）', js=r'''
var input = T.textarea('粘贴代码…');
var output = T.out('');
var lang = T.select([{value:'js',label:'JavaScript'},{value:'css',label:'CSS'},{value:'html',label:'HTML'},{value:'json',label:'JSON'}],'js');
function reindent(src, openers, closers) {
  var depth = 0, out = [], line = '';
  var tokens = src.replace(/\r\n?/g, '\n');
  for (var i = 0; i < tokens.length; i++) {
    var c = tokens[i];
    if (openers.includes(c)) {
      line += c;
      out.push('  '.repeat(depth) + line.trim());
      line = '';
      depth++;
    } else if (closers.includes(c)) {
      if (line.trim()) { out.push('  '.repeat(depth) + line.trim()); line = ''; }
      depth = Math.max(0, depth - 1);
      out.push('  '.repeat(depth) + c);
    } else if (c === ';' && lang.value !== 'html') {
      line += c;
      out.push('  '.repeat(depth) + line.trim());
      line = '';
    } else if (c === '\n') {
      if (line.trim()) { out.push('  '.repeat(depth) + line.trim()); }
      line = '';
    } else line += c;
  }
  if (line.trim()) out.push('  '.repeat(depth) + line.trim());
  return out.filter(function (l, ix) { return l.trim() || (ix > 0 && out[ix - 1].trim()); }).join('\n');
}
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    if (lang.value === 'json') output.value = JSON.stringify(JSON.parse(v), null, 2);
    else if (lang.value === 'css') output.value = reindent(v, '{', '}');
    else if (lang.value === 'js') output.value = reindent(v.replace(/\s*\/\/[^\n]*/g, ''), '{[', '}]');
    else {
      var pretty = v.replace(/>\s*</g, '>\n<');
      var depth = 0;
      output.value = pretty.split('\n').map(function (l) {
        if (/^<\//.test(l.trim())) depth = Math.max(0, depth - 1);
        var res = '  '.repeat(depth) + l.trim();
        if (/^<[^/!][^>]*[^/]>$/.test(l.trim()) && !/^<(br|img|input|meta|link|hr)/i.test(l.trim())) depth++;
        return res;
      }).join('\n');
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, lang].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('代码', input), T.field('格式化结果', output)]));
app.appendChild(T.row([T.el('span', { text: '语言' }), lang, T.btnCopy(function () { return output.value; })]));
run();
''')

d('code-highlight', '代码着色高亮', '多语言语法高亮，输出带样式的 HTML', js=r'''
var input = T.textarea('粘贴代码…');
var lang = T.select([{value:'js',label:'JavaScript/TS'},{value:'css',label:'CSS'},{value:'html',label:'HTML'},{value:'sql',label:'SQL'},{value:'python',label:'Python'},{value:'json',label:'JSON'}],'js');
var preview = T.codeOut();
var htmlOut = T.out('');
var STYLE = '.hl-k{color:#c678dd}.hl-s{color:#98c379}.hl-c{color:#7f848e;font-style:italic}.hl-n{color:#d19a66}.hl-f{color:#61afef}.hl-t{color:#e06c75}.hl-a{color:#d19a66}.hl-p{color:#56b6c2}';
function run() {
  if (!input.value) { preview.textContent = ''; htmlOut.value = ''; return; }
  var html = LF.hl(input.value, lang.value);
  preview.innerHTML = html;
  htmlOut.value = '<style>' + STYLE + '</style>\n<pre style="background:#111;color:#eee;padding:14px;border-radius:8px;overflow:auto;font:12.5px/1.6 monospace">' + html + '</pre>';
}
[input, lang].forEach(function (el) { el.addEventListener('input', T.debounce(run, 250)); });
app.appendChild(T.row([T.el('span', { text: '语言' }), lang]));
app.appendChild(T.pane([T.field('代码', input)], true));
app.appendChild(T.el('span', { text: '预览', class: 'field' }));
app.appendChild(preview);
var st = document.createElement('style');
st.textContent = STYLE + ' .output.dark pre{margin:0;font:inherit;white-space:pre-wrap}';
document.head.appendChild(st);
preview.style.whiteSpace = 'pre-wrap';
preview.style.font = '12.5px/1.6 var(--font-mono)';
app.appendChild(T.row([T.button('复制 HTML', function () { T.copy(htmlOut.value); }), T.button('复制纯 HTML 片段', function () { T.copy(preview.innerHTML); })]));
run();
''')

d('csv-json', 'CSV ↔ JSON', 'CSV 与 JSON 数组互转，支持表头与自定义分隔符', js=r'''
var input = T.textarea('name,age,city\n张三,25,北京\n李四,30,上海');
input.value = 'name,age,city\n张三,25,北京\n李四,30,上海';
var output = T.out('');
var mode = T.select([{value:'j2c',label:'JSON → CSV'},{value:'c2j',label:'CSV → JSON'}],'c2j');
var delim = T.select([{value:',',label:'逗号'},{value:'\t',label:'Tab'},{value:';',label:'分号'}],',');
var header = T.check('首行为表头', true);
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    if (mode.value === 'c2j') {
      var rows = LF.Csv.parse(v, delim.value);
      if (header._input.checked) {
        var head = rows[0];
        output.value = JSON.stringify(rows.slice(1).map(function (r) {
          var o = {};
          head.forEach(function (h, i) { o[h] = r[i] != null && r[i] !== '' && !isNaN(r[i]) && r[i].trim() !== '' ? +r[i] : r[i]; });
          return o;
        }), null, 2);
      } else output.value = JSON.stringify(rows, null, 2);
    } else {
      var arr = T.parseJSON(v);
      if (!Array.isArray(arr)) throw new Error('必须是 JSON 数组');
      if (arr.length && typeof arr[0] === 'object' && !Array.isArray(arr[0])) {
        var cols = [];
        arr.forEach(function (o) { Object.keys(o).forEach(function (k) { if (cols.indexOf(k) < 0) cols.push(k); }); });
        output.value = LF.Csv.stringify([cols].concat(arr.map(function (o) {
          return cols.map(function (c) { return o[c] == null ? '' : o[c]; });
        })), delim.value);
      } else {
        output.value = LF.Csv.stringify(arr, delim.value);
      }
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode, delim, header._input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, T.el('span', { text: '分隔符' }), delim, header, T.btnCopy(function () { return output.value; })]));
run();
''')

d('json-yaml', 'JSON ↔ YAML', 'JSON 与 YAML 子集互转（映射 / 列表 / 标量 / 行内集合）', js=r'''
var input = T.textarea('粘贴 JSON 或 YAML…');
var output = T.out('');
var mode = T.select([{value:'j2y',label:'JSON → YAML'},{value:'y2j',label:'YAML → JSON'}],'j2y');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    if (mode.value === 'j2y') output.value = LF.Yaml.stringify(T.parseJSON(v));
    else output.value = JSON.stringify(LF.Yaml.parse(v), null, 2);
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, T.btnCopy(function () { return output.value; }),
  T.el('span', { text: '支持嵌套映射/列表/标量；锚点、多行块等高级语法不支持' })]));
run();
''')

d('json-xml', 'JSON ↔ XML', 'JSON 与 XML 互转：属性用 @ 前缀，文本用 #text', js=r'''
var input = T.textarea('粘贴 JSON 或 XML…');
var output = T.out('');
var mode = T.select([{value:'j2x',label:'JSON → XML'},{value:'x2j',label:'XML → JSON'}],'j2x');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    if (mode.value === 'j2x') output.value = LF.Xml.stringify(T.parseJSON(v));
    else output.value = JSON.stringify(LF.Xml.parse(v), null, 2);
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, T.btnCopy(function () { return output.value; }),
  T.el('span', { text: '数组 → 重复元素；属性 → @attr；混合文本 → #text' })]));
run();
''')

d('html2md', 'HTML 转 Markdown', '解析 HTML 结构生成 Markdown（标题/列表/链接/表格/代码块）', js=r'''
var input = T.textarea('粘贴 HTML 源码…');
var output = T.out('');
function inline(node) {
  var s = '';
  node.childNodes.forEach(function (c) {
    if (c.nodeType === 3) { s += c.nodeValue.replace(/\s+/g, ' '); return; }
    if (c.nodeType !== 1) return;
    var tag = c.tagName.toLowerCase();
    var kids = function () { return Array.from(c.childNodes).map(inline).join(''); }();
    if (tag === 'strong' || tag === 'b') s += '**' + kids.trim() + '**';
    else if (tag === 'em' || tag === 'i') s += '*' + kids.trim() + '*';
    else if (tag === 'code') s += '`' + c.textContent + '`';
    else if (tag === 'del' || tag === 's') s += '~~' + kids.trim() + '~~';
    else if (tag === 'a') s += '[' + kids.trim() + '](' + (c.getAttribute('href') || '') + ')';
    else if (tag === 'img') s += '![' + (c.getAttribute('alt') || '') + '](' + (c.getAttribute('src') || '') + ')';
    else if (tag === 'br') s += '\n';
    else s += kids;
  });
  return s;
}
function convert(html) {
  var doc = new DOMParser().parseFromString(html, 'text/html');
  var out = [];
  function walk(node, depth) {
    Array.from(node.childNodes).forEach(function (c) {
      if (c.nodeType === 3) {
        var t = c.nodeValue.trim();
        if (t) out.push(t);
        return;
      }
      if (c.nodeType !== 1) return;
      var tag = c.tagName.toLowerCase();
      if (/^h[1-6]$/.test(tag)) out.push('#'.repeat(+tag[1]) + ' ' + inline(c).trim());
      else if (tag === 'p') { var p = inline(c).trim(); if (p) out.push(p); }
      else if (tag === 'hr') out.push('---');
      else if (tag === 'pre') out.push('```\n' + c.textContent.replace(/\n$/, '') + '\n```');
      else if (tag === 'blockquote') out.push(LF.md2html ? inline(c).trim().split('\n').map(function (l) { return '> ' + l; }).join('\n') : '> ' + inline(c).trim());
      else if (tag === 'ul' || tag === 'ol') {
        var i = 1;
        Array.from(c.children).forEach(function (li) {
          if (li.tagName !== 'LI') return;
          var marker = tag === 'ol' ? (i++) + '.' : '-';
          out.push('  '.repeat(depth) + marker + ' ' + inline(li).trim());
          if (li.querySelector('ul,ol')) walk({ childNodes: Array.from(li.children).filter(function (x) { return /^(ul|ol)$/.test(x.tagName.toLowerCase()); }) }, depth + 1);
        });
      }
      else if (tag === 'table') {
        var rows = Array.from(c.querySelectorAll('tr'));
        rows.forEach(function (tr, ri) {
          var cells = Array.from(tr.children).map(function (td) { return inline(td).trim().replace(/\|/g, '\\|'); });
          out.push('| ' + cells.join(' | ') + ' |');
          if (ri === 0) out.push('|' + cells.map(function () { return ' --- '; }).join('|') + '|');
        });
      }
      else if (tag === 'script' || tag === 'style') return;
      else walk(c, depth);
    });
  }
  walk(doc.body, 0);
  return out.join('\n\n').replace(/\n{3,}/g, '\n\n');
}
function run() {
  if (!input.value.trim()) { output.value = ''; return; }
  try { output.value = convert(input.value); }
  catch (e) { output.value = '⚠ ' + e.message; }
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('HTML', input), T.field('Markdown', output)]));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
input.value = '<h1>示例</h1><p>这是 <strong>加粗</strong> 与 <a href="https://freellm.top">链接</a>。</p><ul><li>列表项一</li><li>列表项二</li></ul>';
run();
''')

d('md2html', 'Markdown 转 HTML', 'Markdown 渲染为 HTML，实时预览 + 源码输出', js=r'''
var input = T.textarea('# 标题\n\n**加粗** *斜体* `code`\n\n- 列表项\n- 列表项二\n\n> 引用\n\n```js\nconsole.log(1);\n```');
input.value = '# 标题\n\n**加粗** *斜体* `code`\n\n- 列表项\n- 列表项二\n\n> 引用\n\n```js\nconsole.log(1);\n```';
var htmlOut = T.out('');
var frame = T.el('iframe', { sandbox: '', style: 'width:100%;height:260px;border:1px solid var(--line);border-radius:8px;background:#fff' });
var STYLE = 'body{font:14px/1.7 -apple-system,system-ui,sans-serif;color:#2F3437;max-width:760px;margin:0 auto;padding:16px}pre{background:#f6f6f4;padding:12px;border-radius:8px;overflow:auto}code{font-family:ui-monospace,Consolas,monospace;font-size:12.5px}blockquote{margin:0;padding:2px 14px;border-left:3px solid #ddd;color:#787774}table{border-collapse:collapse}th,td{border:1px solid #e5e5e2;padding:6px 12px}h1,h2{border-bottom:1px solid #eee;padding-bottom:6px}';
function run() {
  if (!input.value.trim()) { htmlOut.value = ''; frame.srcdoc = ''; return; }
  try {
    var html = LF.md2html(input.value);
    htmlOut.value = html;
    frame.srcdoc = '<style>' + STYLE + '</style>' + html;
  } catch (e) { htmlOut.value = '⚠ ' + e.message; }
}
input.addEventListener('input', T.debounce(run, 250));
app.appendChild(T.pane([T.field('Markdown', input)], true));
app.appendChild(T.el('span', { text: '预览', class: 'field' }));
app.appendChild(frame);
app.appendChild(T.pane([T.field('HTML 源码', htmlOut)], true));
app.appendChild(T.row([T.button('复制 HTML', function () { T.copy(htmlOut.value); }),
  T.button('下载 .html', function () { T.download('preview.html', '<!doctype html><meta charset="utf-8"><style>' + STYLE + '</style>' + htmlOut.value, 'text/html'); })]));
run();
''')

d('minify', '代码压缩 Minify', 'JS / CSS / JSON 轻量压缩：去注释、空白与换行', js=r'''
var input = T.textarea('粘贴代码…');
var output = T.out('');
var lang = T.select([{value:'js',label:'JavaScript'},{value:'css',label:'CSS'},{value:'json',label:'JSON'}],'js');
var info = T.badge('—');
function run() {
  var v = input.value;
  if (!v.trim()) { output.value = ''; info.textContent = '—'; return; }
  try {
    var out;
    if (lang.value === 'json') out = JSON.stringify(JSON.parse(v));
    else if (lang.value === 'css') out = v.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\s+/g, ' ').replace(/\s*([{}:;,>~+])\s*/g, '$1').replace(/;}/g, '}').trim();
    else out = v
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/(^|[^:])\/\/[^\n]*/g, '$1')
      .replace(/\n\s*/g, '\n')
      .replace(/\n+/g, '\n')
      .replace(/\s*([=+\-*/%<>!&|,;:{}()\[\]])\s*/g, '$1')
      .replace(/\n/g, '')
      .trim();
    output.value = out;
    info.textContent = T.fmtBytes(v.length) + ' → ' + T.fmtBytes(out.length) + '（-（' + (100 - out.length / v.length * 100).toFixed(1) + '%）'.slice(0, 99) + '）';
    info.textContent = v.length + ' → ' + out.length + ' 字符';
  } catch (e) { output.value = '⚠ ' + e.message; info.textContent = '出错'; }
}
[input, lang].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('代码', input), T.field('压缩结果', output)]));
app.appendChild(T.row([T.el('span', { text: '类型' }), lang, info, T.btnCopy(function () { return output.value; })]));
run();
''')

d('json2class', 'JSON 转实体类', '从 JSON 生成 Java / C# / Go / TypeScript / Python 数据类', js=r'''
var input = T.textarea('{"name":"张三","age":25,"tags":["a"],"address":{"city":"北京"}}');
input.value = '{"name":"张三","age":25,"tags":["a"],"address":{"city":"北京"}}';
var output = T.out('');
var langCls = T.select([{value:'ts',label:'TypeScript'},{value:'java',label:'Java'},{value:'cs',label:'C#'},{value:'go',label:'Go'},{value:'python',label:'Python'}],'ts');
var clsName = T.input('Root', { class: 'grow mono', placeholder: '根类名' });
function pascal(s) { return s.split(/[-_.](\w)/).map(function (w, i) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(''); }
function camel(s) { var p = pascal(s); return p.charAt(0).toLowerCase() + p.slice(1); }
function jsonType(v) {
  if (v === null) return 'null';
  if (Array.isArray(v)) return 'array';
  return typeof v;
}
function generate() {
  var root;
  try { root = T.parseJSON(input.value); } catch (e) { output.value = '⚠ ' + e.message; return; }
  var classes = [];
  var lang = langCls.value;
  function typeName(v, name) {
    var t = jsonType(v);
    if (t === 'object') { buildClass(v, pascal(name)); return pascal(name); }
    if (t === 'array') {
      if (!v.length) return lang === 'go' ? '[]interface{}' : lang === 'ts' ? 'any[]' : lang === 'java' ? 'List<Object>' : lang === 'cs' ? 'object[]' : 'list';
      var it = typeName(v[0], name);
      if (lang === 'go') return '[]' + it;
      if (lang === 'ts') return it + '[]';
      if (lang === 'java') return 'List<' + it + '>';
      if (lang === 'cs') return it + '[]';
      return 'list';
    }
    if (t === 'null') return lang === 'go' ? 'interface{}' : lang === 'ts' ? 'null' : lang === 'java' ? 'Object' : lang === 'cs' ? 'object' : 'None';
    if (t === 'number') return lang === 'go' ? (Number.isInteger(v) ? 'int' : 'float64') : lang === 'ts' ? 'number' : lang === 'java' ? (Number.isInteger(v) ? 'int' : 'double') : lang === 'cs' ? (Number.isInteger(v) ? 'int' : 'double') : 'float';
    if (t === 'boolean') return lang === 'go' ? 'bool' : lang === 'ts' ? 'boolean' : lang === 'java' ? 'boolean' : lang === 'cs' ? 'bool' : 'bool';
    return lang === 'go' ? 'string' : lang === 'ts' ? 'string' : lang === 'java' ? 'String' : lang === 'cs' ? 'string' : 'str';
  }
  function buildClass(obj, name) {
    var fields = [];
    Object.keys(obj).forEach(function (k) {
      var ft = typeName(obj[k], k);
      if (obj[k] !== null && jsonType(obj[k]) === 'array' && obj[k].length && jsonType(obj[k][0]) === 'object') buildClass(obj[k][0], pascal(k));
      fields.push({ json: k, name: /[a-z]/i.test(k) ? (lang === 'go' ? pascal(k) : camel(k)) : camel(k), type: ft, value: obj[k] });
    });
    classes.push({ name: name, fields: fields });
  }
  if (jsonType(root) !== 'object') { output.value = '⚠ 根节点必须是 JSON 对象'; return; }
  buildClass(root, pascal(clsName.value || 'Root'));
  var buf = [];
  if (lang === 'ts') {
    classes.forEach(function (c) {
      buf.push('export interface ' + c.name + ' {');
      c.fields.forEach(function (f) { buf.push('  ' + f.name + ': ' + f.type + ';'); });
      buf.push('}\n');
    });
  } else if (lang === 'java') {
    buf.push('import java.util.List;');
    classes.forEach(function (c) {
      buf.push('public class ' + c.name + ' {');
      c.fields.forEach(function (f) { buf.push('    private ' + f.type + ' ' + f.name + ';'); });
      buf.push('');
      c.fields.forEach(function (f) {
        var T2 = f.type.replace('List<', '').replace('>', '');
        buf.push('    public ' + f.type + ' get' + pascal(f.name) + '() { return this.' + f.name + '; }');
        buf.push('    public void set' + pascal(f.name) + '(' + f.type + ' ' + f.name + ') { this.' + f.name + ' = ' + f.name + '; }');
      });
      buf.push('}\n');
    });
  } else if (lang === 'cs') {
    classes.forEach(function (c) {
      buf.push('public class ' + c.name);
      buf.push('{');
      c.fields.forEach(function (f) { buf.push('    public ' + f.type + ' ' + pascal(f.name) + ' { get; set; }'); });
      buf.push('}\n');
    });
  } else if (lang === 'go') {
    classes.forEach(function (c) {
      buf.push('type ' + c.name + ' struct {');
      c.fields.forEach(function (f) { buf.push('\t' + pascal(f.json) + ' ' + f.type + ' `json:"' + f.json + '"`'); });
      buf.push('}\n');
    });
  } else {
    buf.push('from dataclasses import dataclass');
    buf.push('from typing import Any, List, Optional\n');
    classes.forEach(function (c) {
      buf.push('@dataclass');
      buf.push('class ' + c.name + ':');
      c.fields.forEach(function (f) {
        var py = f.type.replace('list', 'list').replace(/^str$/, 'str');
        buf.push('    ' + f.name + ': ' + (f.type === 'list' ? 'list' : f.type === 'None' ? 'None' : f.type));
      });
      buf.push('');
    });
  }
  output.value = buf.join('\n');
}
[input, langCls, clsName].forEach(function (el) { el.addEventListener('input', T.debounce(generate, 300)); });
app.appendChild(T.pane([T.field('JSON', input), T.field('实体类', output)]));
app.appendChild(T.row([T.el('span', { text: '语言' }), langCls, T.el('span', { text: '根类名' }), clsName, T.btnCopy(function () { return output.value; })]));
generate();
''')

d('json-tree', 'JSON Tree 查看', '交互式树形结构可视化，可折叠展开', js=r'''
var input = T.textarea('{"name":"FreeLLM","tools":[{"id":"json","hot":true},{"id":"base64"}]}');
input.value = '{"name":"FreeLLM","tools":[{"id":"json","hot":true},{"id":"base64"}]}';
var box = T.el('div', { class: 'output', style: 'min-height:280px;font-family:var(--font-sans)' });
function buildTree(key, value, depth) {
  var wrap = T.el('div', { style: 'padding-left:' + (depth ? 16 : 0) + 'px' });
  var t = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
  var label = key != null ? T.el('span', {}) : null;
  var isObj = t === 'object' || t === 'array';
  var head = T.el('div', { style: 'display:flex;gap:6px;align-items:center;padding:1px 0' });
  if (isObj) {
    var entries = t === 'array' ? value.map(function (v, i) { return [i, v]; }) : Object.keys(value).map(function (k) { return [k, value[k]]; });
    var toggle = T.el('span', { text: '▾', style: 'cursor:pointer;color:var(--ink3);width:12px;display:inline-block' });
    var kids = T.el('div', {});
    entries.forEach(function (e) { kids.appendChild(buildTree(e[0], e[1], depth + 1)); });
    toggle.addEventListener('click', function () {
      var open = kids.style.display !== 'none';
      kids.style.display = open ? 'none' : '';
      toggle.textContent = open ? '▸' : '▾';
    });
    head.appendChild(toggle);
    if (label) head.appendChild(label);
    head.appendChild(T.el('span', { text: (key != null ? key + ' ' : '') + (t === 'array' ? '[] ' : '{} ') + entries.length + ' 项', style: 'color:var(--ink2)' }));
    wrap.appendChild(head);
    wrap.appendChild(kids);
  } else {
    head.appendChild(T.el('span', { style: 'width:12px;display:inline-block' }));
    if (label) head.appendChild(label);
    var color = { string: 'var(--ok-text)', number: 'var(--accent)', boolean: '#a626a4', null: 'var(--ink3)' }[t] || 'var(--ink)';
    head.appendChild(T.el('span', { text: (key != null ? key + ': ' : '') + JSON.stringify(value), style: 'color:' + color + ';font-family:var(--font-mono);font-size:12.5px' }));
    wrap.appendChild(head);
  }
  return wrap;
}
function run() {
  T.clearEl(box);
  if (!input.value.trim()) return;
  try { box.appendChild(buildTree(null, T.parseJSON(input.value), 0)); }
  catch (e) { box.textContent = '⚠ ' + e.message; }
}
input.addEventListener('input', T.debounce(run, 250));
app.appendChild(T.pane([T.field('JSON', input)], true));
app.appendChild(box);
run();
''')

d('json-merge', 'JSON 合并', '两个 JSON 对象深度合并，后者覆盖前者（数组可选替换/拼接）', js=r'''
var aIn = T.textarea('{"a":1,"b":{"x":1,"y":2},"list":[1,2]}');
aIn.value = '{"a":1,"b":{"x":1,"y":2},"list":[1,2]}';
var bIn = T.textarea('{"b":{"y":9,"z":3},"list":[3],"c":true}');
bIn.value = '{"b":{"y":9,"z":3},"list":[3],"c":true}';
var output = T.out('');
var arrMode = T.select([{value:'replace',label:'数组替换'},{value:'concat',label:'数组拼接'},{value:'union',label:'数组去重合并'}],'replace');
function deepMerge(a, b) {
  Object.keys(b).forEach(function (k) {
    if (Array.isArray(a[k]) && Array.isArray(b[k])) {
      if (arrMode.value === 'concat') a[k] = a[k].concat(b[k]);
      else if (arrMode.value === 'union') a[k] = Array.from(new Set(a[k].concat(b[k]).map(function (v) { return JSON.stringify(v); }))).map(JSON.parse);
      else a[k] = b[k];
    } else if (a[k] && b[k] && typeof a[k] === 'object' && typeof b[k] === 'object' && !Array.isArray(a[k]) && !Array.isArray(b[k])) {
      a[k] = deepMerge(a[k], b[k]);
    } else a[k] = b[k];
  });
  return a;
}
function run() {
  try {
    var a = T.parseJSON(aIn.value || '{}');
    var b = T.parseJSON(bIn.value || '{}');
    output.value = JSON.stringify(deepMerge(a, b), null, 2);
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[aIn, bIn, arrMode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('JSON A（底）', aIn), T.field('JSON B（顶，优先）', bIn)]));
app.appendChild(T.pane([T.field('合并结果', output)], true));
app.appendChild(T.row([T.el('span', { text: '数组策略' }), arrMode, T.btnCopy(function () { return output.value; })]));
run();
''')

d('json-sort', 'JSON 排序', 'JSON 键名递归排序（字母序），可选倒序', js=r'''
var input = T.textarea('{"b":2,"a":{"d":4,"c":3}}');
input.value = '{"b":2,"a":{"d":4,"c":3}}';
var output = T.out('');
var desc = T.check('倒序（Z→A）');
function sortKeys(obj) {
  if (Array.isArray(obj)) return obj.map(sortKeys);
  if (obj && typeof obj === 'object') {
    var out = {};
    Object.keys(obj).sort(function (a, b) { return desc._input.checked ? b.localeCompare(a) : a.localeCompare(b); })
      .forEach(function (k) { out[k] = sortKeys(obj[k]); });
    return out;
  }
  return obj;
}
function run() {
  try { output.value = JSON.stringify(sortKeys(T.parseJSON(input.value)), null, 2); }
  catch (e) { output.value = '⚠ ' + e.message; }
}
[input, desc._input].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([desc, T.btnCopy(function () { return output.value; })]));
run();
''')

d('url-parser', 'URL 参数解析', 'URL 结构化解析：协议/域名/路径/哈希 + 查询参数表', js=r'''
var input = T.input('https://freellm.top/tools/?tool=base64&utm_source=nav#top', { class: 'grow mono' });
var info = T.el('div', { class: 'pane single' });
function run() {
  T.clearEl(info);
  var v = input.value.trim();
  if (!v) return;
  try {
    var u = new URL(v);
    info.appendChild(T.kvTable([
      ['协议 protocol', u.protocol], ['主机 host', u.host],
      ['端口 port', u.port || '(默认)'], ['路径 pathname', u.pathname],
      ['哈希 hash', u.hash || '(无)'], ['来源 origin', u.origin]
    ]));
    var params = [];
    u.searchParams.forEach(function (val, key) { params.push([key, decodeURIComponent(val)]); });
    if (params.length) {
      info.appendChild(T.el('span', { text: '查询参数', class: 'field' }));
      info.appendChild(T.refTable(['参数', '值'], params));
    }
  } catch (e) {
    info.appendChild(T.msg('⚠ 不是合法的绝对 URL：' + e.message, 'err'));
  }
}
input.addEventListener('input', T.debounce(run, 250));
app.appendChild(T.row([T.el('span', { text: 'URL' }), input]));
app.appendChild(info);
run();
''')

d('nginx-formatter', 'Nginx 格式化', 'Nginx 配置缩进美化，保留注释与字符串', js=r'''
var input = T.textarea('server{listen 80;server_name example.com;location /{proxy_pass http://backend;}}');
input.value = 'server{listen 80;server_name example.com;location /{proxy_pass http://backend;}}';
var output = T.out('');
function run() {
  var v = input.value.replace(/\r\n?/g, '\n');
  if (!v.trim()) { output.value = ''; return; }
  var depth = 0, out = [], line = '';
  var inComment = false, inStr = false;
  for (var i = 0; i < v.length; i++) {
    var c = v[i], next = v[i + 1];
    if (c === '#' && !inStr) inComment = true;
    if (c === '\n') inComment = false;
    if (c === '"' || c === "'") inStr = !inStr;
    if (!inStr && !inComment && c === '{') {
      line = line.trim();
      if (line) { out.push('    '.repeat(depth) + line); line = ''; }
      out.push('    '.repeat(depth) + '{');
      depth++;
      while (v[i + 1] === ' ' || v[i + 1] === '\n') i++;
      continue;
    }
    if (!inStr && !inComment && c === '}') {
      if (line.trim()) { out.push('    '.repeat(depth) + line.trim()); line = ''; }
      depth = Math.max(0, depth - 1);
      out.push('    '.repeat(depth) + '}');
      continue;
    }
    if (!inStr && !inComment && c === ';') {
      out.push('    '.repeat(depth) + (line.trim() + ';'));
      line = '';
      continue;
    }
    if (c === '\n') {
      if (line.trim()) out.push('    '.repeat(depth) + line.trim());
      line = '';
      while (v[i + 1] === ' ' || v[i + 1] === '\t') i++;
      continue;
    }
    line += c;
  }
  if (line.trim()) out.push(line.trim());
  output.value = out.join('\n');
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('Nginx 配置', input), T.field('格式化结果', output)]));
app.appendChild(T.row([T.btnCopy(function () { return output.value; })]));
run();
''')

d('xml-format', 'XML 格式化', 'XML 美化缩进 / 压缩单行 / 结构校验', js=r'''
var input = T.textarea('<root><item id="1">内容</item></root>');
input.value = '<root><item id="1">内容</item></root>';
var output = T.out('');
function parse() {
  var doc = new DOMParser().parseFromString(input.value, 'application/xml');
  var err = doc.querySelector('parsererror');
  if (err) throw new Error(err.textContent.slice(0, 140));
  return doc.documentElement;
}
function serialize(node, depth) {
  var pad = '  '.repeat(depth);
  var attrs = Array.from(node.attributes || []).map(function (a) { return ' ' + a.name + '="' + a.value.replace(/"/g, '&quot;') + '"'; }).join('');
  var kids = Array.from(node.childNodes).filter(function (c) { return c.nodeType === 1; });
  var text = Array.from(node.childNodes).filter(function (c) { return c.nodeType === 3; }).map(function (c) { return c.nodeValue.trim(); }).join('');
  if (!kids.length) return pad + '<' + node.tagName + attrs + '>' + text + '</' + node.tagName + '>';
  var inner = kids.map(function (k) { return serialize(k, depth + 1); }).join('\n');
  return pad + '<' + node.tagName + attrs + '>\n' + inner + '\n' + pad + '</' + node.tagName + '>';
}
function run(mode) {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    var root = parse();
    if (mode === 'min') output.value = v.replace(/>\s+</g, '><');
    else output.value = '<?xml version="1.0" encoding="UTF-8"?>\n' + serialize(root, 0);
    T.toast('✓ XML 结构合法');
  } catch (e) { output.value = '⚠ ' + e.message; }
}
app.appendChild(T.pane([T.field('XML', input), T.field('输出', output)]));
app.appendChild(T.row([T.button('格式化', function () { run(); }, true), T.button('压缩单行', function () { run('min'); }),
  T.btnCopy(function () { return output.value; })]));
run();
''')

d('yaml-format', 'YAML 格式化', 'YAML 校验 / 美化重排 / 压缩为单行 JSON', js=r'''
var input = T.textarea('name: freellm\nitems:\n  - id: 1\n    hot: true\n  - id: 2');
input.value = 'name: freellm\nitems:\n  - id: 1\n    hot: true\n  - id: 2';
var output = T.out('');
var status = T.badge('—');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; status.textContent = '—'; return; }
  try {
    var obj = LF.Yaml.parse(v);
    output.value = LF.Yaml.stringify(obj);
    status.textContent = '✓ YAML 合法';
    status.className = 'badge ok';
  } catch (e) {
    status.textContent = '✗ ' + e.message;
    status.className = 'badge warn';
  }
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('YAML', input), T.field('美化结果', output)]));
app.appendChild(T.row([T.button('转单行 JSON', function () {
  try { output.value = JSON.stringify(LF.Yaml.parse(input.value)); } catch (e) { T.toast(e.message); }
}), T.btnCopy(function () { return output.value; }), status]));
run();
''')

d('csv-format', 'CSV 格式化', 'CSV 校验 / 转表格预览 / 更换分隔符 / 压缩', js=r'''
var input = T.textarea('name,age\n张三,25\n李四,30');
input.value = 'name,age\n张三,25\n李四,30';
var box = T.el('div');
var delim = T.select([{value:',',label:'逗号'},{value:'\t',label:'Tab'},{value:';',label:'分号'},{value:'|',label:'竖线'}],',');
var output = T.out('');
function run() {
  T.clearEl(box);
  var v = input.value.trim();
  if (!v) return;
  try {
    var rows = LF.Csv.parse(v, delim.value);
    if (!rows.length) return;
    var cols = Math.max.apply(null, rows.map(function (r) { return r.length; }));
    box.appendChild(T.refTable(rows[0].map(function (_, i) { return '列' + (i + 1); }), rows.slice(1)));
    box.appendChild(T.el('p', { text: rows.length + ' 行 × ' + cols + ' 列', style: 'color:var(--ink2);font-size:12px' }));
  } catch (e) { box.appendChild(T.msg(e.message, 'err')); }
}
function reformat() {
  output.value = LF.Csv.stringify(LF.Csv.parse(input.value, delim.value), delim.value);
}
[input, delim].forEach(function (el) { el.addEventListener('input', T.debounce(function () { run(); reformat(); }, 300)); });
app.appendChild(T.pane([T.field('CSV', input)], true));
app.appendChild(T.row([T.el('span', { text: '分隔符' }), delim, T.button('重新序列化', reformat), T.btnCopy(function () { return output.value; })]));
app.appendChild(box);
run();
''')

d('md-format', 'Markdown 格式化', 'Markdown 清理：规范空行 / 列表标记 / 标题空格 / 去多余空白', js=r'''
var input = T.textarea('#标题\n-   项目1\n*项目2\n\n\n\n正文  多余  空格。');
input.value = '#标题\n-   项目1\n*项目2\n\n\n\n正文  多余  空格。';
var output = T.out('');
function run() {
  var v = input.value.replace(/\r\n?/g, '\n');
  if (!v.trim()) { output.value = ''; return; }
  var lines = v.split('\n');
  var out = [];
  var inCode = false;
  lines.forEach(function (l) {
    if (/^```/.test(l.trim())) inCode = !inCode;
    if (inCode) { out.push(l); return; }
    l = l.replace(/[ \t]+$/g, '');
    l = l.replace(/^(#{1,6})([^#\s])/, '$1 $2');
    l = l.replace(/^(\s*)[-*+]\s+/, '$1- ');
    l = l.replace(/^(#{1,6})\s+/, function (m) { return m.replace(/\s+/, ' '); });
    l = l.replace(/(\S)  +(\S)/g, '$1 $2');
    out.push(l);
  });
  var res = out.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
  output.value = res;
}
input.addEventListener('input', T.debounce(run, 300));
app.appendChild(T.pane([T.field('Markdown', input), T.field('清理结果', output)]));
app.appendChild(T.row([T.el('span', { text: '规则' }), T.el('span', { text: '标题后补空格 · 列表统一 "-" · 去行尾空白 · 压缩连续空行' }), T.btnCopy(function () { return output.value; })]));
run();
''')

d('excel-convert', 'Excel ↔ JSON/CSV', '上传 xlsx / xls / csv，转换为 JSON 或 CSV（SheetJS 按需加载不拖慢打开）',
  js=r'''
var xlsxReady = null;
function ensureXLSX() {
  if (window.XLSX) return Promise.resolve();
  if (!xlsxReady) {
    xlsxReady = new Promise(function (resolve, reject) {
      var s = T.el('script', { src: '/tools/js/vendor/xlsx.full.min.js' });
      s.onload = function () { resolve(); };
      s.onerror = function () { xlsxReady = null; reject(new Error('SheetJS 加载失败，请刷新重试')); };
      document.head.appendChild(s);
    });
  }
  return xlsxReady;
}
var pick = T.el('input', { type: 'file', accept: '.xlsx,.xls,.csv', style: 'display:none' });
document.body.appendChild(pick);
var sheetSel = T.select([], '');
var box = T.el('div');
var jsonOut = T.out('');
var csvOut = T.out('');
function toAoa(wb, name) {
  return XLSX.utils.sheet_to_json(wb.Sheets[name], { header: 1, raw: false });
}
pick.addEventListener('change', function () {
  var f = pick.files[0];
  if (!f) return;
  ensureXLSX().then(function () {
    var fr = new FileReader();
    fr.onload = function () {
      try {
        var wb = XLSX.read(fr.result, { type: 'array' });
        T.clearEl(sheetSel);
        wb.SheetNames.forEach(function (n) {
          var o = T.el('option', { value: n, text: n });
          sheetSel.appendChild(o);
        });
        sheetSel.onchange = render;
        render();
        T.toast('已读取 ' + f.name + '，共 ' + wb.SheetNames.length + ' 个工作表');
      } catch (e) { T.toast('解析失败：' + e.message); }
    };
    fr.readAsArrayBuffer(f);
  }).catch(function (e) { T.toast(e.message); });
});
function render() {
  var name = sheetSel.value;
  if (!name || !window._wb) return;
  var aoa = toAoa(window._wb, name);
  T.clearEl(box);
  if (!aoa.length) return;
  box.appendChild(T.refTable(aoa[0].map(function (_, i) { return '列' + (i + 1); }), aoa.slice(1, 51)));
  if (aoa.length > 51) box.appendChild(T.el('p', { text: '预览前 50 行，共 ' + (aoa.length - 1) + ' 行数据', style: 'color:var(--ink2);font-size:12px' }));
}
app.appendChild(T.row([T.filePick('选择 Excel / CSV 文件', '.xlsx,.xls,.csv', function (buf, file) {
  ensureXLSX().then(function () {
    try {
      var wb = XLSX.read(buf, { type: 'array' });
      pick._wb = buf;
      window._wb = wb;
      T.clearEl(sheetSel);
      wb.SheetNames.forEach(function (n) { sheetSel.appendChild(T.el('option', { value: n, text: n })); });
      sheetSel.onchange = render;
      render();
    } catch (e) { T.toast('解析失败：' + e.message); }
  }).catch(function (e) { T.toast(e.message); });
}, true)]));
app.appendChild(T.row([T.el('span', { text: '工作表' }), sheetSel]));
app.appendChild(T.pane([T.field('JSON', jsonOut), T.field('CSV', csvOut)]));
app.appendChild(T.row([
  T.button('导出 JSON', function () {
    var aoa = toAoa(window._wb, sheetSel.value);
    var head = aoa[0] || [];
    var arr = aoa.slice(1).map(function (r) {
      var o = {};
      head.forEach(function (h, i) { o[h] = r[i]; });
      return o;
    });
    jsonOut.value = JSON.stringify(arr, null, 2);
  }, true),
  T.button('导出 CSV', function () {
    var aoa = toAoa(window._wb, sheetSel.value);
    csvOut.value = LF.Csv.stringify(aoa);
  }),
  T.button('下载 JSON', function () { T.download('data.json', jsonOut.value, 'application/json'); }),
  T.button('下载 CSV', function () { T.download('data.csv', csvOut.value, 'text/csv'); })
]));
app.appendChild(box);
''')

d('json-schema', 'JSON Schema 校验', '校验 JSON 是否符合 Schema：类型 / 必填 / 枚举 / 数值与字符串边界', js=r'''
var schemaIn = T.textarea('{"type":"object","required":["name"],"properties":{"name":{"type":"string","minLength":1},"age":{"type":"integer","minimum":0}}}');
schemaIn.value = '{"type":"object","required":["name"],"properties":{"name":{"type":"string","minLength":1},"age":{"type":"integer","minimum":0}}}';
var dataIn = T.textarea('{"name":"张三","age":25}');
dataIn.value = '{"name":"张三","age":25}';
var output = T.out('');
function validate(data, schema, path, errors) {
  var t = schema.type;
  var actual = Array.isArray(data) ? 'array' : data === null ? 'null' : typeof data;
  if (t) {
    var types = Array.isArray(t) ? t : [t];
    var ok = types.some(function (tt) {
      if (tt === 'integer') return actual === 'number' && Number.isInteger(data);
      if (tt === 'number') return actual === 'number';
      return actual === tt;
    });
    if (!ok) { errors.push(path + ': 类型应为 ' + types.join('/') + '，实际 ' + actual); return; }
  }
  if (schema.enum && schema.enum.indexOf(data) < 0) errors.push(path + ': 值不在枚举 ' + JSON.stringify(schema.enum) + ' 中');
  if (actual === 'number') {
    if (schema.minimum != null && data < schema.minimum) errors.push(path + ': 不能小于 ' + schema.minimum);
    if (schema.maximum != null && data > schema.maximum) errors.push(path + ': 不能大于 ' + schema.maximum);
  }
  if (actual === 'string') {
    if (schema.minLength != null && data.length < schema.minLength) errors.push(path + ': 长度不足 ' + schema.minLength);
    if (schema.maxLength != null && data.length > schema.maxLength) errors.push(path + ': 长度超过 ' + schema.maxLength);
    if (schema.pattern) { try { if (!new RegExp(schema.pattern).test(data)) errors.push(path + ': 不匹配正则 ' + schema.pattern); } catch (e) {} }
  }
  if (actual === 'array' && schema.items) data.forEach(function (item, i) { validate(item, schema.items, path + '[' + i + ']', errors); });
  if (actual === 'object') {
    (schema.required || []).forEach(function (req) {
      if (!(req in data)) errors.push(path + '.' + req + ': 缺少必填字段');
    });
    if (schema.properties) Object.keys(schema.properties).forEach(function (k) {
      if (k in data) validate(data[k], schema.properties[k], path + '.' + k, errors);
    });
  }
}
function run() {
  try {
    var schema = T.parseJSON(schemaIn.value);
    var data = T.parseJSON(dataIn.value);
    var errors = [];
    validate(data, schema, '$', errors);
    output.value = errors.length ? '✗ 校验失败（' + errors.length + ' 项）：\n' + errors.map(function (e, i) { return (i + 1) + '. ' + e; }).join('\n') : '✓ 校验通过';
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[schemaIn, dataIn].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('Schema', schemaIn), T.field('数据', dataIn)]));
app.appendChild(T.pane([T.field('校验结果', output)], true));
run();
''')

d('jsonpath', 'JSONPath 查询', '用 JSONPath 表达式提取 JSON 数据（$ . [] .. * ?() 支持）', js=r'''
var dataIn = T.textarea('{"store":{"book":[{"title":"三体","price":45},{"title":"活着","price":30}],"location":"北京"}}');
dataIn.value = '{"store":{"book":[{"title":"三体","price":45},{"title":"活着","price":30}],"location":"北京"}}';
var expr = T.input('$.store.book[*].title', { class: 'grow mono' });
var output = T.out('');
function query(obj, path) {
  var results = [obj];
  var tokens = path.startsWith('$') ? path.slice(1).replace(/^\./, '').split('.') : path.split('.');
  tokens.forEach(function (tk) {
    if (!tk) return;
    var next = [];
    results.forEach(function (cur) {
      var parts = tk.match(/([\w-]+|\*)|\[(\*|\d+|'[^']*'|"[^"]*")\]|\[\?\(@?([\w.]+)([<>=!]+)([^)]+\)?)\]\]/g) || [tk];
      parts.forEach(function (p) {
        var mm;
        if ((mm = p.match(/^\[\?\(@?([\w.]+)([<>=!]=?|<[>=]?|>=?|!=)(.+?)\)\]$/))) {
          var field = mm[1], op = mm[2], val = parseFloat(mm[3]) || mm[3].replace(/^['"]|['"]$/g, '');
          cur.forEach && null;
          if (Array.isArray(cur)) {
            cur.forEach(function (item) {
              var v = field.split('.').reduce(function (o, k) { return o && o[k]; }, item);
              var cmp;
              if (typeof val === 'number') cmp = typeof v === 'number';
              if (cmp) {
                var pass = op === '<' ? v < val : op === '<=' ? v <= val : op === '>' ? v > val : op === '>=' ? v >= val : op === '==' || op === '=' ? v == val : v != val;
                if (pass) next.push(item);
              }
            });
          }
          return;
        }
        if (p === '*') {
          if (Array.isArray(cur)) next = next.concat(cur);
          else if (cur && typeof cur === 'object') Object.keys(cur).forEach(function (k) { next.push(cur[k]); });
          return;
        }
        if (cur == null) return;
        var key = p.replace(/^\['|^\["|'\]$|"\]$/g, '').replace(/^\[/, '').replace(/\]$/, '');
        if (key === 'length') { next.push((cur.length != null ? cur.length : Object.keys(cur).length)); return; }
        var idx = /^\d+$/.test(key) ? +key : key;
        if (cur[idx] !== undefined) next.push(cur[idx]);
      });
    });
    results = next;
  });
  return results;
}
function run() {
  try {
    var obj = T.parseJSON(dataIn.value);
    var res = query(obj, expr.value.trim());
    output.value = res.length + ' 个结果：\n' + res.map(function (r) { return JSON.stringify(r); }).join('\n');
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[dataIn, expr].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('数据', dataIn)], true));
app.appendChild(T.row([T.el('span', { text: '表达式' }), expr]));
app.appendChild(T.pane([T.field('结果', output)], true));
run();
''')

d('jmespath', 'JMESPath 查询', 'JMESPath 数据查询：投影 / 索引 / 管道 / 内置函数', js=r'''
var dataIn = T.textarea('{"users":[{"name":"张三","age":25},{"name":"李四","age":30}],"total":2}');
dataIn.value = '{"users":[{"name":"张三","age":25},{"name":"李四","age":30}],"total":2}';
var expr = T.input('users[*].name', { class: 'grow mono' });
var output = T.out('');
function evaluate(data, exprText) {
  var segs = exprText.split('|').map(function (s) { return s.trim(); }).filter(Boolean);
  var cur = data;
  segs.forEach(function (seg) {
    var fn = seg.match(/^(length|keys|values|sum|max|min|reverse|sort|type)\((.*)\)$/);
    if (fn) {
      var inner = evaluate(cur, fn[2]);
      var arr = Array.isArray(inner) ? inner : [inner];
      switch (fn[1]) {
        case 'length': cur = arr.length; return;
        case 'keys': cur = arr.map(function (o) { return Object.keys(o); }); return;
        case 'values': cur = arr.map(function (o) { return Object.keys(o).map(function (k) { return o[k]; }); }); return;
        case 'sum': cur = arr.reduce(function (s, n) { return s + n; }, 0); return;
        case 'max': cur = Math.max.apply(null, arr); return;
        case 'min': cur = Math.min.apply(null, arr); return;
        case 'reverse': cur = arr.slice().reverse(); return;
        case 'sort': cur = arr.slice().sort(); return;
        case 'type': cur = typeof cur; return;
      }
    }
    cur = project(cur, seg);
  });
  return cur;
}
function project(cur, seg) {
  var parts = seg.match(/[\w-]+|\[\*\]|\[\d+\]|\[\d+:\d*\]|\[\?[^]]*\]|\*/g) || [seg];
  parts.forEach(function (p) {
    if (p === '[*]' || p === '*') {
      if (Array.isArray(cur)) cur = cur.slice();
      else if (cur && typeof cur === 'object') cur = Object.keys(cur).map(function (k) { return cur[k]; });
      else cur = [];
      return;
    }
    var slice = p.match(/^\[(\d+):(\d*)\]$/);
    if (slice) {
      var a = +slice[1], b = slice[2] === '' ? undefined : +slice[2];
      cur = Array.isArray(cur) ? cur.slice(a, b) : [];
      return;
    }
    var idx = p.match(/^\[(\d+)\]$/);
    if (idx) { cur = Array.isArray(cur) ? cur[+idx[1]] : undefined; return; }
    var filter = p.match(/^\[\?([\w.]+)\s*([<>=!]+)\s*'?([^'&]+)'?\]$/);
    if (filter) {
      if (Array.isArray(cur)) {
        cur = cur.filter(function (item) {
          var v = filter[1].split('.').reduce(function (o, k) { return o && o[k]; }, item);
          var target = isNaN(+filter[3]) ? filter[3].trim() : +filter[3];
          var op = filter[2];
          return op === '>' ? v > target : op === '>=' ? v >= target : op === '<' ? v < target : op === '<=' ? v <= target : (op === '==' || op === '=') ? v == target : v != target;
        });
      }
      return;
    }
    var multiselect = seg.includes('{');
    if (multiselect) return;
    if (cur == null) { cur = undefined; return; }
    cur = cur[p] === undefined ? undefined : cur[p];
  });
  return cur;
}
function run() {
  try {
    var obj = T.parseJSON(dataIn.value);
    var e = expr.value.trim();
    var res = evaluate(obj, e);
    output.value = JSON.stringify(res, null, 2);
  } catch (err) { output.value = '⚠ ' + err.message; }
}
[dataIn, expr].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('数据', dataIn)], true));
app.appendChild(T.row([T.el('span', { text: '表达式' }), expr]));
app.appendChild(T.pane([T.field('结果', output)], true));
app.appendChild(T.el('p', { text: '示例：users[*].name · users[?age>26].name · length(users) · users[*].{n: name}', style: 'color:var(--ink2);font-size:12px' }));
run();
''')

d('table2csv', '表格转 CSV', '粘贴 HTML 表格片段 → 提取为 CSV', js=r'''
var input = T.textarea('<table><tr><th>名称</th><th>价格</th></tr><tr><td>苹果</td><td>5.5</td></tr></table>');
input.value = '<table><tr><th>名称</th><th>价格</th></tr><tr><td>苹果</td><td>5.5</td></tr></table>';
var output = T.out('');
var delim = T.select([{value:',',label:'逗号'},{value:'\t',label:'Tab'}],',');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    var doc = new DOMParser().parseFromString(v, 'text/html');
    var rows = Array.from(doc.querySelectorAll('tr'));
    if (!rows.length) throw new Error('未找到 <tr> 行');
    var data = rows.map(function (tr) {
      return Array.from(tr.children).map(function (td) {
        return td.textContent.trim().replace(/\s+/g, ' ');
      });
    });
    output.value = LF.Csv.stringify(data, delim.value);
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, delim].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('HTML 表格', input), T.field('CSV', output)]));
app.appendChild(T.row([T.el('span', { text: '分隔符' }), delim, T.btnCopy(function () { return output.value; })]));
run();
''')

d('text2table', '文本转表格', '按分隔符 / 正则把文本切成表格，可导出 CSV', js=r'''
var input = T.textarea('张三|25|北京\n李四|30|上海');
input.value = '张三|25|北京\n李四|30|上海';
var output = T.out('');
var mode = T.select([{value:'str',label:'分隔符'},{value:'re',label:'正则'}],'str');
var delim = T.input('|', { class: 'mono', style: 'width:80px' });
var box = T.el('div');
function run() {
  T.clearEl(box);
  var v = input.value.trim();
  if (!v) return;
  var rows;
  try {
    var pattern = mode.value === 'str' ? delim.value : new RegExp(delim.value, 'g');
    rows = v.split('\n').map(function (l) { return l.split(pattern).map(function (c) { return c.trim(); }); });
    box.appendChild(T.refTable(rows[0].map(function (_, i) { return '列' + (i + 1); }), rows.slice(1)));
  } catch (e) { box.appendChild(T.msg('⚠ ' + e.message, 'err')); return; }
  output.value = LF.Csv.stringify(rows);
}
[input, delim, mode].forEach(function (el) { el.addEventListener('input', T.debounce(run, 300)); });
app.appendChild(T.pane([T.field('文本（每行一条记录）', input)], true));
app.appendChild(T.row([mode, T.el('span', { text: mode.value === 'str' ? '分隔符' : '正则' }), delim]));
app.appendChild(box);
app.appendChild(T.row([T.el('span', { text: 'CSV' }), T.btnCopy(function () { return output.value; })]));
app.appendChild(output);
run();
''')

d('csv2md', 'CSV ↔ Markdown 表格', 'CSV 与 Markdown 表格互转', js=r'''
var input = T.textarea('name,age\n张三,25\n李四,30');
input.value = 'name,age\n张三,25\n李四,30';
var output = T.out('');
var mode = T.select([{value:'c2m',label:'CSV → Markdown'},{value:'m2c',label:'Markdown → CSV'}],'c2m');
function run() {
  var v = input.value.trim();
  if (!v) { output.value = ''; return; }
  try {
    if (mode.value === 'c2m') {
      var rows = LF.Csv.parse(v);
      var md = '| ' + rows[0].join(' | ') + ' |\n|' + rows[0].map(function () { return ' --- |'; }).join('') + '\n';
      rows.slice(1).forEach(function (r) { md += '| ' + r.join(' | ') + ' |\n'; });
      output.value = md.trim();
    } else {
      var rows2 = v.split('\n').filter(function (l) { return l.trim() && !/^\s*\|[\s:|-]+\|\s*$/.test(l); })
        .map(function (l) { return l.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(function (c) { return c.trim(); }); });
      output.value = LF.Csv.stringify(rows2);
    }
  } catch (e) { output.value = '⚠ ' + e.message; }
}
[input, mode].forEach(function (el) { el.addEventListener('input', run); });
app.appendChild(T.pane([T.field('输入', input), T.field('输出', output)]));
app.appendChild(T.row([mode, T.btnCopy(function () { return output.value; })]));
run();
''')
