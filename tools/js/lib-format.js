/* 共享库：格式处理 — MiniMD(Markdown) / MiniHL(语法高亮) / SqlF / YamlX / XmlX / CSVX / DiffX
   页面引入：<script src="/tools/js/lib-format.js"></script>*/
(function (global) {
  'use strict';
  var LF = {};

  /* ============ MiniMD：Markdown → HTML ============ */
  var esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  LF.esc = esc;

  function inlineMd(s) {
    s = esc(s);
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, '<img src="$2" alt="$1">');
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, '<a href="$2" title="$3">$1</a>');
    s = s.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    s = s.replace(/~~([^~]+)~~/g, '<del>$1</del>');
    return s;
  }

  LF.md2html = function (src) {
    var lines = src.replace(/\r\n?/g, '\n').split('\n');
    var out = [], i = 0;
    var para = [];
    function flushPara() {
      if (para.length) { out.push('<p>' + inlineMd(para.join(' ')) + '</p>'); para = []; }
    }
    while (i < lines.length) {
      var line = lines[i];
      if (/^```/.test(line)) {
        flushPara();
        var lang = line.slice(3).trim();
        var buf = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
        i++;
        out.push('<pre><code' + (lang ? ' class="language-' + esc(lang) + '"' : '') + '>' + esc(buf.join('\n')) + '</code></pre>');
        continue;
      }
      var hm = line.match(/^(#{1,6})\s+(.*)$/);
      if (hm) { flushPara(); out.push('<h' + hm[1].length + '>' + inlineMd(hm[2]) + '</h' + hm[1].length + '>'); i++; continue; }
      if (/^\s*(?:---|\*\*\*|___)\s*$/.test(line)) { flushPara(); out.push('<hr>'); i++; continue; }
      if (/^\s*[-*+]\s+/.test(line) || /^\s*\d+[.)]\s+/.test(line)) {
        flushPara();
        var ordered = /^\s*\d+[.)]\s+/.test(line);
        var re = ordered ? /^(\s*)(\d+)[.)]\s+(.*)$/ : /^(\s*)[-*+]\s+(.*)$/;
        var items = [];
        while (i < lines.length && re.test(lines[i])) {
          var m = lines[i].match(re);
          items.push({ indent: m[1].length, text: ordered ? m[3] : m[2] });
          i++;
        }
        var html = '', depth = 0;
        items.forEach(function (it) {
          var lvl = Math.min(2, Math.floor(it.indent / 2));
          while (depth < lvl) { html += ordered ? '<ol>' : '<ul>'; depth++; }
          while (depth > lvl) { html += ordered ? '</ol>' : '</ul>'; depth--; }
          html += '<li>' + inlineMd(it.text) + '</li>';
        });
        while (depth > 0) { html += ordered ? '</ol>' : '</ul>'; depth--; }
        out.push(html);
        continue;
      }
      if (/^\s*>\s?/.test(line)) {
        flushPara();
        var q = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) { q.push(lines[i].replace(/^\s*>\s?/, '')); i++; }
        out.push('<blockquote>' + LF.md2html(q.join('\n')) + '</blockquote>');
        continue;
      }
      if (line.includes('|') && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i + 1]) && /-/.test(lines[i + 1])) {
        flushPara();
        var splitRow = function (r) {
          r = r.trim(); if (r.startsWith('|')) r = r.slice(1); if (r.endsWith('|')) r = r.slice(0, -1);
          return r.split('|').map(function (c) { return c.trim(); });
        };
        var head = splitRow(lines[i]); i += 2;
        var bodyRows = [];
        while (i < lines.length && lines[i].includes('|') && lines[i].trim()) { bodyRows.push(splitRow(lines[i])); i++; }
        var t = '<table><thead><tr>' + head.map(function (h) { return '<th>' + inlineMd(h) + '</th>'; }).join('') + '</tr></thead><tbody>';
        bodyRows.forEach(function (r) {
          t += '<tr>' + r.map(function (c) { return '<td>' + inlineMd(c) + '</td>'; }).join('') + '</tr>';
        });
        out.push(t + '</tbody></table>');
        continue;
      }
      if (!line.trim()) { flushPara(); i++; continue; }
      para.push(line.trim());
      i++;
    }
    flushPara();
    return out.join('\n');
  };

  /* ============ MiniHL：语法高亮 ============ */
  var KW = {
    js: /\b(?:const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|class|extends|super|this|typeof|instanceof|try|catch|finally|throw|async|await|yield|import|export|from|default|null|undefined|true|false|of|in|delete|void|static|get|set)\b/g,
    python: /\b(?:def|return|if|elif|else|for|while|import|from|as|class|try|except|finally|with|pass|break|continue|lambda|yield|global|nonlocal|assert|raise|del|in|is|not|and|or|None|True|False|self|async|await)\b/g,
    sql: /\b(?:SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|DROP|ALTER|ADD|INDEX|VIEW|JOIN|INNER|LEFT|RIGHT|FULL|OUTER|ON|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|AS|AND|OR|NOT|NULL|IS|IN|BETWEEN|LIKE|DISTINCT|COUNT|SUM|AVG|MIN|MAX|CASE|WHEN|THEN|ELSE|END|UNION|ALL|EXISTS|PRIMARY|KEY|FOREIGN|REFERENCES|DEFAULT|CONSTRAINT|ASC|DESC)\b/gi
  };
  function hlCommon(code, lang) {
    var tokens = [];
    /* 高亮专用转义：不动引号，字符串正则可直接匹配真实引号 */
    var src = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    /* 标记索引用 A-J 字母编码，避免数字正则误吃占位符 */
    function enc(n) { return String(n).replace(/\d/g, function (d) { return 'ABCDEFGHIJ'[+d]; }); }
    function dec(s) { return s.split('').reduce(function (acc, c) { return acc * 10 + 'ABCDEFGHIJ'.indexOf(c); }, 0); }
    function stash(cls, text) {
      tokens.push('<span class="hl-' + cls + '">' + text + '</span>');
      return '\u0001' + enc(tokens.length - 1) + '\u0002';
    }
    var STR = /("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`)/g;
    if (lang === 'html' || lang === 'xml') {
      src = src.replace(/(&lt;!--[\s\S]*?--&gt;)/g, function (m) { return stash('c', m); });
      src = src.replace(/(&lt;\/?)([\w-]+)([\s\S]*?)(\/?&gt;)/g, function (m, lt, tag, attrs, gt) {
        attrs = attrs.replace(/([\w-]+)(=)("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, function (mm, a, eq, v) {
          return stash('a', a) + eq + stash('s', v);
        });
        return stash('p', lt) + stash('t', tag) + attrs + stash('p', gt);
      });
    } else {
      var lineComment = lang === 'python' ? '(?:^|[^:])\/\/[^\n]*|#[^\n]*' : '(?:^|[^:])\/\/[^\n]*';
      src = src.replace(new RegExp('(\/\\*[\\s\\S]*?\\*\/|' + lineComment + ')', 'g'), function (m) { return stash('c', m); });
      src = src.replace(STR, function (m) { return stash('s', m); });
      var kw = KW[lang === 'ts' ? 'js' : lang] || KW.js;
      src = src.replace(kw, function (m) { return stash('k', m); });
      src = src.replace(/\b(0x[0-9a-fA-F]+|\d+\.?\d*(?:e[+-]?\d+)?)\b/gi, function (m) { return stash('n', m); });
      src = src.replace(/([\w$]+)(\s*\()/g, function (m, f, p) { return stash('f', f) + p; });
    }
    src = src.replace(/\u0001([A-J]+)\u0002/g, function (m, i) { return tokens[dec(i)]; });
    return src;
  }
  LF.hl = hlCommon;

  /* ============ SqlF：SQL 格式化 ============ */
  var MAJOR = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT', 'OFFSET', 'UNION ALL', 'UNION', 'INSERT INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE FROM', 'CREATE TABLE', 'DROP TABLE', 'ALTER TABLE', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN', 'FULL JOIN', 'CROSS JOIN', 'JOIN'];
  var JTYPES = ['LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS'];
  LF.sqlFormat = function (sql) {
    var q = sql.replace(/\r\n?/g, '\n').replace(/\s+/g, ' ').trim();
    q = q.replace(/\b(".*(?!\\)"|`[^`]*`|\[[^\]]*\])\b/g, function (m) { return '\u0001' + m + '\u0002'; });
    var out = '', indent = 0;
    var tokens = q.split(/\s+/);
    var line = '';
    function newline(n) {
      if (line.trim()) out += '  '.repeat(Math.max(0, indent)) + line.trim() + '\n';
      line = '';
      if (n != null) indent = Math.max(0, indent + n);
    }
    for (var i = 0; i < tokens.length; i++) {
      var tk = tokens[i];
      var up = tk.toUpperCase().replace(/\u0001|\u0002/g, '');
      var joinExtra = JTYPES.indexOf(up) >= 0 && tokens[i + 1] && tokens[i + 1].toUpperCase() === 'JOIN';
      var matched = MAJOR.indexOf(up) >= 0 || (joinExtra);
      if (matched) {
        if (up === 'VALUES') newline();
        else newline();
        if (/^(SELECT|FROM|WHERE|SET|VALUES)$/.test(up)) {
          line = up + ' ';
          indent = up === 'SELECT' ? indent : indent;
        } else if (/BY$/.test(up) || /^(LIMIT|OFFSET)$/.test(up)) {
          line = up + ' ';
        } else if (up === 'JOIN' || JTYPES.indexOf(up) >= 0) {
          if (JTYPES.indexOf(up) >= 0) { line = up + ' JOIN '; i++; }
          else line = 'JOIN ';
        } else if (/^(UNION|UNION ALL)$/.test(up)) {
          newline(-1); line = up + '\n'; newline();
          line = '';
          indent = 0;
        } else if (up === 'INSERT INTO' || up === 'DELETE FROM' || up === 'UPDATE' || up === 'CREATE TABLE' || up === 'DROP TABLE' || up === 'ALTER TABLE') {
          line = up + ' ';
        } else {
          line = up + ' ';
        }
        continue;
      }
      if (tk === '(') { line += tk + ' '; continue; }
      if (tk === ')') { line += tk; continue; }
      if (/,$/.test(tk)) { line += tk; newline(); continue; }
      line += tk + ' ';
    }
    newline();
    return out.trim().replace(/\n{3,}/g, '\n\n');
  };

  /* ============ YamlX：YAML 子集 互转 ============ */
  var YX = {};
  function yamlScalar(s) {
    s = s.trim();
    if (!s || s === '~' || s === 'null') return null;
    if (/^-?\d+$/.test(s)) return parseInt(s, 10);
    if (/^-?\d*\.\d+$/.test(s)) return parseFloat(s);
    if (s === 'true' || s === 'True') return true;
    if (s === 'false' || s === 'False') return false;
    if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'")))
      return s.slice(1, -1).replace(/\\n/g, '\n').replace(/\\(["'\\])/g, '$1');
    if (/^[[{]/.test(s)) { try { return JSON.parse(s.replace(/([{,]\s*)(\w+)(\s*:)/g, '$1"$2"$3')); } catch (e) { return s; } }
    return s;
  }
  YX.parse = function (text) {
    var lines = [];
    text.replace(/\r\n?/g, '\n').split('\n').forEach(function (l) {
      var t = l.replace(/#.*$/, '').replace(/\s+$/, '');
      if (!t.trim()) return;
      var indent = t.match(/^\s*/)[0].length;
      lines.push({ indent: indent, text: t.trim() });
    });
    var pos = { i: 0 };
    function parseBlock(indent) {
      if (pos.i >= lines.length) return null;
      var isSeq = /^-\s/.test(lines[pos.i].text) || lines[pos.i].text === '-';
      var result = isSeq ? [] : {};
      while (pos.i < lines.length && lines[pos.i].indent >= indent) {
        var ln = lines[pos.i];
        if (ln.indent > indent) { pos.i++; continue; }
        var seqm = ln.text.match(/^-(?:\s+(.*))?$/);
        if (seqm) {
          if (!isSeq) break;
          if (seqm[1] == null) {
            pos.i++;
            result.push(parseBlock(indent + 2));
          } else if (/^[\w.-]+:\s/.test(seqm[1]) || /^[\w.-]+:$/.test(seqm[1])) {
            var kv = seqm[1].match(/^([\w.-]+):\s*(.*)$/);
            var obj = {};
            var extraIndent = ln.indent + 2;
            if (kv[2]) { obj[kv[1]] = yamlScalar(kv[2]); pos.i++; }
            else {
              obj[kv[1]] = null;
              pos.i++;
              if (pos.i < lines.length && lines[pos.i].indent > ln.indent + 1) obj[kv[1]] = parseBlock(lines[pos.i].indent);
            }
            while (pos.i < lines.length && lines[pos.i].indent === extraIndent && /^[\w.-]+:/.test(lines[pos.i].text)) {
              var k2 = lines[pos.i].text.match(/^([\w.-]+):\s*(.*)$/);
              if (k2[2]) { obj[k2[1]] = yamlScalar(k2[2]); pos.i++; }
              else {
                obj[k2[1]] = null; pos.i++;
                if (pos.i < lines.length && lines[pos.i].indent > extraIndent) obj[k2[1]] = parseBlock(lines[pos.i].indent);
              }
            }
            result.push(obj);
          } else {
            result.push(yamlScalar(seqm[1]));
            pos.i++;
          }
          continue;
        }
        var m2 = ln.text.match(/^([\w.-]+):\s*(.*)$/);
        if (!m2) { pos.i++; continue; }
        if (isSeq) break;
        if (m2[2]) { result[m2[1]] = yamlScalar(m2[2]); pos.i++; }
        else {
          pos.i++;
          if (pos.i < lines.length && lines[pos.i].indent > indent) result[m2[1]] = parseBlock(lines[pos.i].indent);
          else result[m2[1]] = null;
        }
      }
      return result;
    }
    return parseBlock(0);
  };
  function yamlStr(v, indent) {
    var pad = '  '.repeat(indent);
    if (v == null) return 'null';
    if (typeof v === 'boolean' || typeof v === 'number') return String(v);
    if (typeof v === 'string') {
      if (/[:{}\[\],&*?|>'"%@`#\-]/.test(v) || /^\s|\s$/.test(v) || /^(true|false|null|~|\d+\.?\d*)$/i.test(v) || v.includes('\n'))
        return "'" + v.replace(/\\/g, '\\\\').replace(/'/g, "''") + "'";
      return v;
    }
    if (Array.isArray(v)) {
      if (!v.length) return '[]';
      return v.map(function (item) {
        if (item && typeof item === 'object') {
          var inner = yamlStr(item, indent + 1);
          var lines = inner.split('\n');
          return pad + '- ' + lines[0].trim() + (lines.length > 1 ? '\n' + lines.slice(1).map(function (l) { return l ? '  ' + l : l; }).join('\n') : '');
        }
        return pad + '- ' + yamlStr(item, 0);
      }).join('\n');
    }
    var keys = Object.keys(v);
    if (!keys.length) return '{}';
    return keys.map(function (k) {
      var val = v[k];
      if (val && typeof val === 'object') {
        var inner = yamlStr(val, indent + 1);
        return pad + k + ':\n' + inner;
      }
      return pad + k + ': ' + yamlStr(val, 0);
    }).join('\n');
  }
  YX.stringify = function (obj) { return yamlStr(obj, 0); };
  LF.Yaml = YX;

  /* ============ XmlX：XML ↔ JS 对象 ============ */
  var XX = {};
  XX.parse = function (text) {
    var doc = new DOMParser().parseFromString(text, 'application/xml');
    if (doc.querySelector('parsererror')) throw new Error('XML 解析失败：' + doc.querySelector('parsererror').textContent.slice(0, 120));
    function nodeToObj(node) {
      var obj = {};
      if (node.attributes) {
        for (var i = 0; i < node.attributes.length; i++) {
          var a = node.attributes[i];
          obj['@' + a.name] = a.value;
        }
      }
      var kids = node.childNodes;
      var textOnly = '';
      var hasElement = false;
      for (var k = 0; k < kids.length; k++) {
        var c = kids[k];
        if (c.nodeType === 3 || c.nodeType === 4) { textOnly += c.nodeValue; continue; }
        if (c.nodeType !== 1) continue;
        hasElement = true;
        var val = nodeToObj(c);
        var name = c.nodeName;
        if (obj[name] == null) obj[name] = val;
        else if (Array.isArray(obj[name])) obj[name].push(val);
        else obj[name] = [obj[name], val];
      }
      if (!hasElement) {
        var t = textOnly.trim();
        if (!Object.keys(obj).length) return t;
        if (t) obj['#text'] = t;
      }
      return obj;
    }
    return nodeToObj(doc.documentElement);
  };
  function xmlVal(v, indent) {
    var pad = '  '.repeat(indent);
    if (v == null) return '';
    if (typeof v === 'object') return xmlObj(v, indent + 1) ? xmlObj(v, indent + 1) : '';
    return esc(String(v));
  }
  function xmlObj(obj, indent) {
    var pad = '  '.repeat(indent);
    var out = [];
    Object.keys(obj).forEach(function (k) {
      var v = obj[k];
      if (k === '#text') return;
      var attrs = '';
      var text = v;
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        attrs = Object.keys(v).filter(function (a) { return a.startsWith('@'); })
          .map(function (a) { return ' ' + a.slice(1) + '="' + esc(String(v[a])) + '"'; }).join('');
        text = v['#text'] != null ? v['#text'] : v;
      }
      var vals = Array.isArray(text) ? text : [text];
      vals.forEach(function (item) {
        if (item && typeof item === 'object' && !(item instanceof String)) {
          var inner = xmlObj(item, indent + 1) || (item['#text'] != null ? esc(String(item['#text'])) : '');
          out.push(pad + '<' + k + attrs + '>' + (inner ? '\n' + inner + '\n' + pad : '') + '</' + k + '>');
        } else {
          out.push(pad + '<' + k + attrs + '>' + (item == null ? '' : esc(String(item))) + '</' + k + '>');
        }
      });
    });
    return out.join('\n');
  }
  XX.stringify = function (obj, rootName) {
    return '<?xml version="1.0" encoding="UTF-8"?>\n<' + (rootName || 'root') + '>\n' + xmlObj(obj, 1) + '\n</' + (rootName || 'root') + '>';
  };
  LF.Xml = XX;

  /* ============ CSVX：CSV 解析/生成 ============ */
  var CX = {};
  CX.parse = function (text, delim) {
    delim = delim || ',';
    var rows = [], row = [], field = '', inQ = false;
    var src = text.replace(/\r\n?/g, '\n');
    for (var i = 0; i < src.length; i++) {
      var c = src[i];
      if (inQ) {
        if (c === '"') {
          if (src[i + 1] === '"') { field += '"'; i++; }
          else inQ = false;
        } else field += c;
      } else if (c === '"') inQ = true;
      else if (c === delim) { row.push(field); field = ''; }
      else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
      else field += c;
    }
    if (field !== '' || row.length) { row.push(field); rows.push(row); }
    return rows.filter(function (r) { return r.length > 1 || (r[0] != null && r[0] !== ''); });
  };
  CX.stringify = function (rows, delim) {
    delim = delim || ',';
    return rows.map(function (row) {
      return row.map(function (cell) {
        var s = cell == null ? '' : String(cell);
        if (s.includes('"') || s.includes(delim) || s.includes('\n')) s = '"' + s.replace(/"/g, '""') + '"';
        return s;
      }).join(delim);
    }).join('\n');
  };
  LF.Csv = CX;

  /* ============ DiffX：行级 LCS diff ============ */
  var DX = {};
  DX.diff = function (aText, bText) {
    var a = aText.replace(/\r\n?/g, '\n').split('\n');
    var b = bText.replace(/\r\n?/g, '\n').split('\n');
    var n = a.length, m = b.length;
    var MAX = 3000;
    if (n > MAX || m > MAX) {
      var minLen = Math.min(n, m);
      a = a.slice(0, MAX); b = b.slice(0, MAX);
      n = m = MAX;
    }
    var dp = [];
    for (var i = 0; i <= n; i++) { dp.push(new Uint32Array(m + 1)); }
    for (i = n - 1; i >= 0; i--)
      for (var j = m - 1; j >= 0; j--)
        dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    var ops = [];
    i = 0; j = 0;
    while (i < n && j < m) {
      if (a[i] === b[j]) { ops.push({ t: '=', a: a[i], ai: i + 1, bi: j + 1 }); i++; j++; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) { ops.push({ t: '-', a: a[i], ai: i + 1 }); i++; }
      else { ops.push({ t: '+', a: b[j], bi: j + 1 }); j++; }
    }
    while (i < n) { ops.push({ t: '-', a: a[i], ai: i + 1 }); i++; }
    while (j < m) { ops.push({ t: '+', a: b[j], bi: j + 1 }); j++; }
    return ops;
  };
  DX.similarity = function (aText, bText) {
    var a = aText.replace(/\s+/g, ' ').trim(), b = bText.replace(/\s+/g, ' ').trim();
    if (!a && !b) return 1;
    if (!a || !b) return 0;
    if (a === b) return 1;
    var grams = function (s) {
      var set = {};
      for (var i = 0; i < s.length - 1; i++) {
        var g = s.slice(i, i + 2);
        set[g] = (set[g] || 0) + 1;
      }
      return set;
    };
    var ga = grams(a), gb = grams(b);
    var inter = 0, total = 0;
    Object.keys(ga).forEach(function (g) { total += ga[g]; });
    Object.keys(gb).forEach(function (g) { total += gb[g]; if (ga[g]) inter += Math.min(ga[g], gb[g]); });
    return total ? (2 * inter / total) : 0;
  };
  LF.Diff = DX;

  global.LibFormat = LF;
})(window);
