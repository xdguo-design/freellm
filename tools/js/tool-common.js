/* 工具页共享运行时 — 与 /tools/css/tool.css 配套
   用法（每个工具页）：
     <script src="/tools/js/tool-common.js"></script>
     const T = ToolCommon; T.head('工具名', '描述');
*/
(function (global) {
  'use strict';
  var T = {};

  /* ---------- 主题同步（跟随全站设置） ---------- */
  function applyTheme(t) {
    if (t === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
  }
  var theme = null;
  try { theme = JSON.parse(localStorage.getItem('freellm-settings') || '{}').theme; } catch (e) {}
  if (theme === 'dark' || theme === 'light') applyTheme(theme);
  else if (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches) applyTheme('dark');

  /* ---------- 页面骨架 ---------- */
  T.head = function (title, desc, id) {
    document.title = title + ' · FreeLLM 工具';
    var wrap = document.createElement('div');
    wrap.className = 'tool';
    wrap.innerHTML =
      '<header class="tool-topbar">' +
        '<a class="brand" href="/tools/">' +
          '<span class="brand-mark">✦</span>' +
          '<span class="brand-text"><span class="brand-name">FreeLLM</span><span class="brand-sub">Online Toolkit</span></span>' +
        '</a>' +
        '<nav class="tool-crumbs"><a href="/tools/">工具合集</a><span>/</span><span class="crumb-here"></span></nav>' +
        '<button class="theme-toggle" type="button" aria-label="切换深色模式" title="切换深色模式">' +
          '<span class="icon-moon">☾</span><span class="icon-sun">☀️</span>' +
        '</button>' +
      '</header>' +
      '<div class="tool-head"><h1></h1><span class="id"></span></div>' +
      (desc ? '<p class="tool-desc"></p>' : '');
    wrap.querySelector('h1').textContent = title;
    wrap.querySelector('.crumb-here').textContent = title;
    var idEl = wrap.querySelector('.id');
    if (id) idEl.textContent = id;
    else idEl.style.display = 'none';
    if (desc) wrap.querySelector('.tool-desc').textContent = desc;
    wrap.querySelector('.theme-toggle').addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try {
        var s = {};
        try { s = JSON.parse(localStorage.getItem('freellm-settings') || '{}'); } catch (e) {}
        s.theme = next;
        localStorage.setItem('freellm-settings', JSON.stringify(s));
        if (next === 'dark') localStorage.setItem('freellm-theme', 'dark');
        else localStorage.removeItem('freellm-theme');
      } catch (e) {}
    });
    var host = document.querySelector('.tool') || document.body;
    host.appendChild(wrap);
    return wrap;
  };

  /* ---------- 小部件构建 ---------- */
  T.el = function (tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') node.className = attrs[k];
      else if (k === 'text') node.textContent = attrs[k];
      else if (k === 'html') node.innerHTML = attrs[k];
      else if (k === 'style') node.style.cssText = attrs[k];
      else if (k.slice(0, 2) === 'on') node.addEventListener(k.slice(2), attrs[k]);
      else node.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) {
      if (c == null) return;
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return node;
  };

  T.textarea = function (placeholder, mono) {
    var ta = T.el('textarea', { placeholder: placeholder || '', rows: '9', spellcheck: 'false' });
    if (mono !== false) ta.className = 'mono';
    return ta;
  };

  T.select = function (options, value) {
    var s = T.el('select');
    options.forEach(function (o) {
      var opt = typeof o === 'string' ? { value: o, label: o } : o;
      var el = T.el('option', { value: opt.value, text: opt.label });
      if (opt.value === value) el.selected = true;
      s.appendChild(el);
    });
    return s;
  };

  T.button = function (label, onclick, primary) {
    return T.el('button', { text: label, onclick: onclick, class: primary ? 'primary' : '' });
  };

  T.copyBtn = function (getText) {
    return T.button('复制', function () {
      T.copy(typeof getText === 'function' ? getText() : getText);
    }, false);
  };

  /* ---------- 常用动作 ---------- */
  T.toast = function (msg) {
    var el = document.querySelector('.toast');
    if (!el) { el = T.el('div', { class: 'toast' }); document.body.appendChild(el); }
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.classList.remove('show'); }, 1800);
  };

  T.copy = function (text) {
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
      .then(function () { T.toast('已复制'); })
      .catch(function () {
        var ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); T.toast('已复制'); } catch (e) { T.toast('复制失败'); }
        ta.remove();
      });
  };

  T.download = function (name, data, mime) {
    var blob = data instanceof Blob ? data : new Blob([data], { type: mime || 'text/plain;charset=utf-8' });
    var a = T.el('a', { href: URL.createObjectURL(blob), download: name });
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  };

  T.readFile = function (accept, cb, asDataURL) {
    var input = T.el('input', { type: 'file', style: 'display:none' });
    if (accept) input.setAttribute('accept', accept);
    input.addEventListener('change', function () {
      var f = input.files[0];
      if (!f) return;
      var reader = new FileReader();
      reader.onload = function () { cb(reader.result, f); };
      if (asDataURL) reader.readAsDataURL(f); else reader.readAsText(f);
    });
    document.body.appendChild(input);
    input.click();
    setTimeout(function () { input.remove(); }, 60000);
  };

  /* ---------- 输入→输出 管线 ----------
     T.wire({ input, output, transform, transformOut, debounce })
     transform(inText) → outText；抛错则 output 显示错误
  ---------- */
  T.wire = function (opts) {
    var run = function () {
      var v = opts.input.value;
      try {
        var out = opts.transform(v);
        if (opts.output.tagName === 'TEXTAREA' || opts.output.tagName === 'INPUT') opts.output.value = out;
        else opts.output.textContent = out;
      } catch (e) {
        if (opts.output.tagName === 'TEXTAREA' || opts.output.tagName === 'INPUT') opts.output.value = '';
        else opts.output.textContent = '';
        opts.output.textContent = '⚠ ' + e.message;
      }
    };
    var ev = opts.event || 'input';
    if (opts.debounce) {
      var t;
      opts.input.addEventListener(ev, function () { clearTimeout(t); t = setTimeout(run, opts.debounce); });
    } else {
      opts.input.addEventListener(ev, run);
    }
    return run;
  };

  /* ---------- 深色代码输出块 ---------- */
  T.codeOut = function () {
    return T.el('div', { class: 'output dark', tabindex: '0' });
  };

  /* ---------- 参考表渲染 ---------- */
  T.refTable = function (columns, rows, onClickRow) {
    var table = T.el('table', { class: 'ref' });
    var thead = T.el('thead'); var trh = T.el('tr');
    columns.forEach(function (c) { trh.appendChild(T.el('th', { text: c })); });
    thead.appendChild(trh); table.appendChild(thead);
    var tbody = T.el('tbody');
    rows.forEach(function (r) {
      var tr = T.el('tr');
      if (onClickRow) {
        tr.className = 'clickable';
        tr.addEventListener('click', function () { onClickRow(r); });
      }
      columns.forEach(function (c, i) {
        var td = T.el('td');
        var v = Array.isArray(r) ? r[i] : r[c];
        if (i === columns.length - 1 || /[\w\-.]+/.test(String(v)) && String(v).length < 40 && /^[\x20-\x7e]+$/.test(String(v))) td.className = 'mono';
        td.textContent = v == null ? '' : v;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    return table;
  };

  /* ---------- 编解码 helpers ---------- */
  T.bytesToHex = function (buf) {
    return Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
  };
  T.hexToBytes = function (hex) {
    var clean = hex.replace(/[^0-9a-fA-F]/g, '');
    if (clean.length % 2) throw new Error('十六进制长度必须为偶数');
    var arr = new Uint8Array(clean.length / 2);
    for (var i = 0; i < arr.length; i++) arr[i] = parseInt(clean.substr(i * 2, 2), 16);
    return arr;
  };
  T.textToBytes = function (s) { return new TextEncoder().encode(s); };
  T.bytesToText = function (b) { return new TextDecoder().decode(b); };
  T.bytesToB64 = function (bytes) {
    var s = ''; var arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    for (var i = 0; i < arr.length; i++) s += String.fromCharCode(arr[i]);
    return btoa(s);
  };
  T.b64ToBytes = function (b64) {
    var s = atob(b64.replace(/\s/g, ''));
    var arr = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) arr[i] = s.charCodeAt(i);
    return arr;
  };

  /* ---------- 常用控件（第二组） ---------- */
  T.input = function (value, attrs) {
    var el = T.el('input', Object.assign({ type: 'text', value: value || '', spellcheck: 'false' }, attrs || {}));
    return el;
  };
  T.num = function (value, attrs) {
    return T.el('input', Object.assign({ type: 'number', value: value == null ? '' : value }, attrs || {}));
  };
  T.color = function (value) { return T.el('input', { type: 'color', value: value || '#000000' }); };
  T.check = function (label, checked, onchange) {
    var c = T.el('input', { type: 'checkbox' });
    c.checked = !!checked;
    if (onchange) c.addEventListener('change', onchange);
    var l = T.el('label', { class: 'grow', style: 'display:flex;gap:6px;align-items:center;cursor:pointer' }, [c, label]);
    l._input = c;
    return l;
  };
  T.range = function (min, max, step, value, oninput) {
    var r = T.el('input', { type: 'range', min: min, max: max, step: step || 1, value: value == null ? min : value, style: 'flex:1;min-width:120px' });
    if (oninput) r.addEventListener('input', oninput);
    return r;
  };
  T.field = function (label, control) {
    var f = T.el('div', { class: 'field' }, [T.el('span', { text: label }), control]);
    f._control = control;
    return f;
  };
  T.pane = function (items, single) { return T.el('div', { class: 'pane' + (single ? ' single' : '') }, items); };
  T.row = function (items) { return T.el('div', { class: 'row' }, items); };
  T.badge = function (text, cls) { return T.el('span', { class: 'badge ' + (cls || 'blue'), text: text }); };
  T.msg = function (text, cls) { return T.el('div', { class: 'msg ' + (cls || ''), text: text || '' }); };
  T.stat = function (value, label) {
    var s = T.el('span', { class: 'stat' }, [T.el('b', { text: String(value) })]);
    if (label) s.appendChild(T.el('span', { text: label }));
    return s;
  };
  T.out = function (placeholder) {
    var ta = T.textarea(placeholder || '输出…', true);
    ta.readOnly = true;
    ta.style.background = 'var(--surface-soft)';
    return ta;
  };
  T.btnCopy = function (get) {
    return T.button('复制', function () { T.copy(typeof get === 'function' ? get() : get); });
  };
  T.btnDl = function (name, get, mime, primary) {
    return T.button('下载', function () {
      var v = typeof get === 'function' ? get() : get;
      if (v instanceof Blob || v instanceof ArrayBuffer) T.download(name, v, mime);
      else T.download(name, v, mime);
    }, primary);
  };
  T.debounce = function (fn, ms) {
    var t;
    return function () { var a = arguments, s = this; clearTimeout(t); t = setTimeout(function () { fn.apply(s, a); }, ms || 200); };
  };
  T.parseJSON = function (text) {
    try { return JSON.parse(text); }
    catch (e) { throw new Error('JSON 解析失败：' + e.message); }
  };
  T.kvTable = function (pairs) {
    return T.refTable(['项目', '值'], pairs);
  };
  T.loadImage = function (cb, accept) {
    T.readFile(accept || 'image/*', function (dataURL, file) {
      var img = new Image();
      img.onload = function () { cb(img, file, dataURL); };
      img.onerror = function () { T.toast('图片解析失败'); };
      img.src = dataURL;
    }, true);
  };
  T.filePick = function (label, accept, cb, asDataURL) {
    return T.button(label, function () { T.readFile(accept, cb, asDataURL); }, true);
  };
  T.dlCanvas = function (canvas, name) {
    canvas.toBlob(function (b) { T.download(name, b); });
  };
  T.clearEl = function (el) { while (el.firstChild) el.removeChild(el.firstChild); return el; };
  T.fmtBytes = function (n) {
    if (n < 1024) return n + ' B';
    if (n < 1048576) return (n / 1024).toFixed(2) + ' KB';
    if (n < 1073741824) return (n / 1048576).toFixed(2) + ' MB';
    return (n / 1073741824).toFixed(2) + ' GB';
  };
  T.pad2 = function (n) { return String(n).padStart(2, '0'); };
  T.fmtDate = function (d) { return d.getFullYear() + '-' + T.pad2(d.getMonth() + 1) + '-' + T.pad2(d.getDate()); };
  T.fmtTime = function (d) {
    return T.fmtDate(d) + ' ' + T.pad2(d.getHours()) + ':' + T.pad2(d.getMinutes()) + ':' + T.pad2(d.getSeconds());
  };
  T.dateInput = function (value) { return T.el('input', { type: 'date', value: value || '' }); };
  T.today = function () { return T.fmtDate(new Date()); };
  T.esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  T.gcd = function (a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = b; b = a % b; a = t; } return a; };

  /* ---------- 源码查看 + 在线修改测试 ----------
     页面模板注入 <script type="application/json" id="tool-source">{id,title,desc,scripts,code}</script>
     查看源码：语法高亮展示；修改测试：编辑后在沙箱 iframe 中即时重跑 */
  T.sourcePanel = function () {
    var el = document.getElementById('tool-source');
    if (!el) return;
    var payload;
    try { payload = JSON.parse(el.textContent); } catch (e) { return; }
    var code = payload.code || '';
    var lineCount = code.split('\n').length;

    var wrap = T.el('div', { class: 'tool-source' });

    var srcBox = T.el('div', { style: 'display:none;margin-top:12px' });
    var playBox = T.el('div', { style: 'display:none;margin-top:12px' });
    var codePre = null;
    var editor = null, frame = null, playStatus = null, played = false;

    function toggle(box, btn, onOpen) {
      var open = box.style.display !== 'none';
      box.style.display = open ? 'none' : '';
      btn.firstChild.textContent = (open ? btn._label : '收起 ' + btn._label.replace(/^\S+\s/, ''));
      if (!open && onOpen) onOpen();
    }

    var srcBtn = T.button('查看源码', function () {
      toggle(srcBox, srcBtn, function () {
        if (!codePre) {
          codePre = T.el('div', { class: 'output dark', style: 'max-height:460px;white-space:pre;font-size:12px;overflow:auto' });
          codePre.innerHTML = window.LibFormat ? window.LibFormat.hl(code, 'js') : T.esc(code);
          srcBox.insertBefore(codePre, srcBox.firstChild);
        }
      });
    });
    srcBtn._label = '查看源码';

    var playBtn = T.button('在线修改测试', function () {
      toggle(playBox, playBtn, function () {
        if (!editor) {
          editor = T.el('textarea', { spellcheck: 'false' });
          editor.className = 'mono';
          editor.style.height = '300px';
          editor.value = code;
          frame = T.el('iframe', { sandbox: 'allow-scripts allow-same-origin allow-modals allow-forms' });
          frame.style.cssText = 'width:100%;height:480px;border:1px solid var(--line);border-radius:8px;background:#fff';
          playStatus = T.badge('编辑代码后点击「运行」');
          playBox.appendChild(T.el('span', { text: 'JS 源码（可自由修改）', class: 'field' }));
          playBox.appendChild(editor);
          playBox.appendChild(T.row([
            T.button('运行', runEdit, true),
            T.button('还原原始代码', function () { editor.value = code; runEdit(); }),
            T.button('新窗口打开（完整权限）', function () {
              var w = window.open('', '_blank');
              w.document.open();
              w.document.write(skeleton(editor.value));
              w.document.close();
            }),
            playStatus
          ]));
          playBox.appendChild(T.el('p', { text: '运行在沙箱 iframe 中：摄像头 / 麦克风等设备能力可能受限，需要完整权限请用「新窗口打开」。', style: 'color:var(--ink3);font-size:11.5px' }));
          playBox.appendChild(frame);
          runEdit();
        }
      });
    });
    playBtn._label = '在线修改测试';

    var head = T.row([
      T.el('span', { text: '纯前端实现 · ' + lineCount + ' 行 · 可查看源码、修改后即时运行', class: 'src-note' }),
      srcBtn, playBtn
    ]);
    head.style.marginBottom = '0';
    wrap.appendChild(head);
    wrap.appendChild(srcBox);
    wrap.appendChild(playBox);
    var host = document.querySelector('.tool') || document.body;
    host.appendChild(wrap);

    function runEdit() {
      frame.style.display = '';
      frame.srcdoc = skeleton(editor.value);
      playStatus.textContent = '✓ 已运行 ' + new Date().toLocaleTimeString('zh-CN');
      playStatus.className = 'badge ok';
    }

    function skeleton(userCode) {
      var safe = String(userCode).replace(/<\/script/gi, '<\\/script');
      return '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n' +
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n' +
        '<title>' + payload.title + ' · 在线测试</title>\n' +
        '<link rel="icon" href="data:,">\n' +
        '<link rel="stylesheet" href="/tools/css/tool.css">\n' +
        (payload.scripts || '') + '\n</head>\n<body>\n<div id="app"></div>\n' +
        '<script src="/tools/js/tool-common.js"><' + '/script>\n' +
        '<script src="/tools/js/lib-crypto.js"><' + '/script>\n' +
        '<script src="/tools/js/lib-format.js"><' + '/script>\n' +
        '<script src="/tools/js/lib-utils.js"><' + '/script>\n' +
        '<script src="/js/freellm-sync.js"><' + '/script>\n' +
        '<script>\n(function () {\n\'use strict\';\n' +
        'var T = ToolCommon, LC = window.LC, LF = window.LibFormat, LU = window.LibU;\n' +
        'var app = T.head(' + JSON.stringify(payload.title) + ', ' + JSON.stringify(payload.desc) + ', ' + JSON.stringify(payload.id) + ');\n' +
        safe + '\n})();\n<' + '/script>\n</body>\n</html>';
    }
  };

  global.ToolCommon = T;
})(window);