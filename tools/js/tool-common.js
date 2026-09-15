/* 工具页共享运行时 — 与 /tools/css/tool.css 配套
   用法（每个工具页）：
     <script src="/tools/js/tool-common.js"></script>
     const T = ToolCommon; T.head('工具名', '描述');
*/
(function (global) {
  'use strict';
  var T = {};

  /* ---------- 主题同步（跟随全站设置） ---------- */
  var theme = null;
  try { theme = JSON.parse(localStorage.getItem('freellm-settings') || '{}').theme; } catch (e) {}
  if (theme === 'dark' || (!theme && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }

  /* ---------- 页面骨架 ---------- */
  T.head = function (title, desc, id) {
    document.title = title + ' · FreeLLM 工具';
    var wrap = document.createElement('div');
    wrap.className = 'tool';
    wrap.innerHTML =
      '<div class="tool-head"><h1></h1><span class="id">' + (id || '') + '</span></div>' +
      (desc ? '<p class="tool-desc"></p>' : '');
    wrap.querySelector('h1').textContent = title;
    if (desc) wrap.querySelector('.tool-desc').textContent = desc;
    document.body.appendChild(wrap);
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

  global.ToolCommon = T;
})(window);