/* ============================================================
   FreeLLM Tools — Shared Utilities
   Pure JS, no dependencies.
   ============================================================ */

(function (global) {
  'use strict';

  const U = {};

  /* ---------- DOM helpers ---------- */
  U.$ = function (sel, root) {
    return (root || document).querySelector(sel);
  };

  U.$$ = function (sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  };

  U.el = function (tag, props, ...children) {
    const node = document.createElement(tag);
    if (props) {
      for (const [k, v] of Object.entries(props)) {
        if (k === 'class') node.className = v;
        else if (k === 'html') node.innerHTML = v;
        else if (k === 'text') node.textContent = v;
        else if (k.startsWith('on') && typeof v === 'function') {
          node.addEventListener(k.slice(2).toLowerCase(), v);
        } else if (k === 'style' && typeof v === 'object') {
          Object.assign(node.style, v);
        } else node.setAttribute(k, v);
      }
    }
    for (const child of children) {
      if (child == null || child === false) continue;
      if (typeof child === 'string' || typeof child === 'number') {
        node.appendChild(document.createTextNode(String(child)));
      } else if (child instanceof Node) {
        node.appendChild(child);
      } else if (Array.isArray(child)) {
        child.forEach(c => node.appendChild(U.el('div', {}, c)));
      }
    }
    return node;
  };

  U.clear = function (node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  };

  /* ---------- Storage ---------- */
  U.storage = {
    get: function (key, def) {
      try {
        const v = localStorage.getItem(key);
        return v === null ? def : JSON.parse(v);
      } catch { return def; }
    },
    set: function (key, val) {
      try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
    },
    remove: function (key) {
      try { localStorage.removeItem(key); } catch {}
    }
  };

  /* ---------- Encoding / Decoding ---------- */
  U.encode = {
    base64: function (str) {
      return btoa(unescape(encodeURIComponent(str)));
    },
    decodeBase64: function (b64) {
      return decodeURIComponent(escape(atob(b64)));
    },
    urlEncode: function (str) {
      return encodeURIComponent(str);
    },
    urlDecode: function (str) {
      return decodeURIComponent(str);
    },
    htmlEncode: function (str) {
      const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
      return String(str).replace(/[&<>"']/g, m => map[m]);
    },
    htmlDecode: function (str) {
      const doc = new DOMParser().parseFromString(str, 'text/html');
      return doc.body.textContent;
    },
    unicodeToChars: function (str) {
      return str.split('').map(c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0')).join('');
    },
    charsToUnicode: function (str) {
      return str.replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
    }
  };

  /* ---------- Hashing ---------- */
  U.hash = {
    md5: async function (str) {
      const buf = await crypto.subtle.digest('MD5', new TextEncoder().encode(str));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
    },
    sha: async function (str, algo = 'SHA-256') {
      const buf = await crypto.subtle.digest(algo, new TextEncoder().encode(str));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
    },
    file: async function (file, algo = 'SHA-256') {
      const buf = await crypto.subtle.digest(algo, await file.arrayBuffer());
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
    }
  };

  /* ---------- Formatting ---------- */
  U.format = {
    json: function (val, indent = 2) {
      try {
        const obj = typeof val === 'string' ? JSON.parse(val) : val;
        return JSON.stringify(obj, null, indent);
      } catch (e) { return 'Error: ' + e.message; }
    },
    yaml: function (obj, indent = 2) {
      return U._yaml(obj, 0, indent);
    },
    _yaml: function (obj, depth, indent) {
      const pad = ' '.repeat(depth * indent);
      if (obj === null || obj === undefined) return 'null';
      if (typeof obj === 'boolean') return obj ? 'true' : 'false';
      if (typeof obj === 'number') return String(obj);
      if (typeof obj === 'string') {
        if (/[:\n#\[\]{},&*!|>'"%@`]/.test(obj) || obj.trim() !== obj) return JSON.stringify(obj);
        return obj;
      }
      if (Array.isArray(obj)) {
        if (obj.length === 0) return '[]';
        return obj.map(v => pad + '- ' + U._yaml(v, depth + 1, indent).trimStart()).join('\n');
      }
      const keys = Object.keys(obj);
      if (keys.length === 0) return '{}';
      return keys.map(k => pad + k + ': ' + U._yaml(obj[k], depth + 1, indent).trimStart()).join('\n');
    },
    xml: function (obj, root = 'root') {
      function escape(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }
      function build(o, tag) {
        if (Array.isArray(o)) {
          return o.map(v => build(v, tag)).join('\n');
        }
        if (typeof o === 'object' && o !== null) {
          const attrs = [];
          let children = '';
          for (const [k, v] of Object.entries(o)) {
            if (k === '@attrs') {
              for (const [ak, av] of Object.entries(v)) attrs.push(` ${ak}="${escape(av)}"`);
            } else if (k === '#text') {
              children += escape(v);
            } else {
              children += build(v, k);
            }
          }
          return `<${tag}${attrs.length ? attrs.join('') : ''}>${children ? '\n' + children + '\n' : ''}</${tag}>`;
        }
        return `<${tag}>${escape(o)}</${tag}>`;
      }
      return build(obj, root);
    },
    csv: function (data, sep = ',') {
      const rows = Array.isArray(data) ? data : [data];
      return rows.map(row => {
        return Array.isArray(row) ? row.map(c => {
          const s = String(c);
          return /[,"\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
        }).join(sep) : row;
      }).join('\n');
    },
    minify: {
      html: function (s) {
        return s.replace(/<!--[\s\S]*?-->/g, '')
          .replace(/\s+/g, ' ')
          .replace(/> </g, '><')
          .replace(/<\s*\/\s*>/g, '</')
          .trim();
      },
      css: function (s) {
        return s.replace(/\/\*[\s\S]*?\*\//g, '')
          .replace(/\s*([{}:;,])\s*/g, '$1')
          .replace(/;}/g, '}')
          .replace(/\s+/g, ' ')
          .trim();
      },
      js: function (s) {
        return s.replace(/\/\*[\s\S]*?\*\//g, '')
          .replace(/\/\/[^\n]*/g, '')
          .replace(/\s+/g, ' ')
          .trim();
      }
    }
  };

  /* ---------- Case conversion ---------- */
  U.case = {
    toCamel: function (s) {
      return s.replace(/[-_\s]+(.)?/g, (_, c) => c ? c.toUpperCase() : '');
    },
    toPascal: function (s) {
      const c = U.case.toCamel(s);
      return c.charAt(0).toUpperCase() + c.slice(1);
    },
    toSnake: function (s) {
      return s.replace(/([a-z0-9])([A-Z])/g, '$1_$2')
        .replace(/[-\s]+/g, '_').toLowerCase();
    },
    toKebab: function (s) {
      return s.replace(/([a-z0-9])([A-Z])/g, '$1-$2')
        .replace(/[_\s]+/g, '-').toLowerCase();
    },
    toUpper: function (s) { return s.toUpperCase(); },
    toLower: function (s) { return s.toLowerCase(); },
    toTitle: function (s) {
      return s.replace(/\w\S*/g, w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());
    }
  };

  /* ---------- Number / Math ---------- */
  U.math = {
    radix: function (val, from, to) {
      const n = parseInt(String(val), from);
      if (isNaN(n)) return 'Error: invalid number';
      if (to === 2) return n.toString(2);
      if (to === 8) return n.toString(8);
      if (to === 10) return String(n);
      if (to === 16) return n.toString(16).toUpperCase();
      return n.toString(to);
    },
    floatToBin32: function (f) {
      const buf = new ArrayBuffer(4);
      new Float32Array(buf)[0] = f;
      return Array.from(new Uint32Array(buf))[0].toString(2).padStart(32, '0');
    },
    floatToBin64: function (f) {
      const buf = new ArrayBuffer(8);
      new Float64Array(buf)[0] = f;
      return Array.from(new BigUint64Array(buf))[0].toString(2).padStart(64, '0');
    },
    bin32ToFloat: function (b) {
      const bits = b.replace(/[^01]/g, '').padStart(32, '0').slice(-32);
      const n = parseInt(bits, 2);
      const buf = new ArrayBuffer(4);
      new Uint32Array(buf)[0] = n;
      return new Float32Array(buf)[0];
    },
    bin64ToFloat: function (b) {
      const bits = b.replace(/[^01]/g, '').padStart(64, '0').slice(-64);
      const n = BigInt('0b' + bits);
      const buf = new ArrayBuffer(8);
      new BigUint64Array(buf)[0] = n;
      return new Float64Array(buf)[0];
    },
    endianSwap32: function (hex) {
      const clean = hex.replace(/^0x/, '');
      const bytes = clean.match(/.{1,2}/g) || [];
      while (bytes.length < 4) bytes.unshift('00');
      return bytes.reverse().join('');
    },
    bitReverse: function (val, bits = 8) {
      const n = parseInt(String(val));
      let rev = 0;
      for (let i = 0; i < bits; i++) {
        rev = (rev << 1) | (n & 1);
        n >>= 1;
      }
      return rev;
    },
    bitShift: function (val, dir, amount) {
      const n = parseInt(String(val));
      if (dir === 'left') return (n << amount) >>> 0;
      if (dir === 'right') return (n >> amount) >>> 0;
      if (dir === 'urshift') return n >>> amount;
      return n;
    }
  };

  /* ---------- Color ---------- */
  U.color = {
    rgbToHex: function (r, g, b) {
      return '#' + [r, g, b].map(c => Math.max(0, Math.min(255, c | 0)).toString(16).padStart(2, '0')).join('');
    },
    hexToRgb: function (hex) {
      const h = hex.replace('#', '');
      return {
        r: parseInt(h.slice(0, 2), 16),
        g: parseInt(h.slice(2, 4), 16),
        b: parseInt(h.slice(4, 6), 16)
      };
    },
    rgbToHsl: function (r, g, b) {
      r /= 255; g /= 255; b /= 255;
      const max = Math.max(r, g, b), min = Math.min(r, g, b);
      let h, s, l = (max + min) / 2;
      if (max === min) { h = s = 0; }
      else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
          case r: h = (g - b) / d + (g < b ? 6 : 0); break;
          case g: h = (b - r) / d + 2; break;
          case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
      }
      return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
    },
    hslToRgb: function (h, s, l) {
      h /= 360; s /= 100; l /= 100;
      let r, g, b;
      if (s === 0) { r = g = b = l; }
      else {
        const hue2rgb = (p, q, t) => {
          if (t < 0) t += 1;
          if (t > 1) t -= 1;
          if (t < 1/6) return p + (q - p) * 6 * t;
          if (t < 1/2) return q;
          if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
          return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
      }
      return { r: Math.round(r * 255), g: Math.round(g * 255), b: Math.round(b * 255) };
    },
    hexToHsl: function (hex) {
      const { r, g, b } = U.color.hexToRgb(hex);
      return U.color.rgbToHsl(r, g, b);
    },
    hslToHex: function (h, s, l) {
      const { r, g, b } = U.color.hslToRgb(h, s, l);
      return U.color.rgbToHex(r, g, b);
    },
    shade: function (hex, percent) {
      const { r, g, b } = U.color.hexToRgb(hex);
      const t = percent < 0 ? 0 : 255;
      const p = Math.abs(percent) / 100;
      const nr = Math.round((t - r) * p + r);
      const ng = Math.round((t - g) * p + g);
      const nb = Math.round((t - b) * p + b);
      return U.color.rgbToHex(nr, ng, nb);
    },
    mix: function (c1, c2, percent) {
      const a = U.color.hexToRgb(c1);
      const b = U.color.hexToRgb(c2);
      const p = percent / 100;
      return U.color.rgbToHex(
        Math.round(a.r + (b.r - a.r) * p),
        Math.round(a.g + (b.g - a.g) * p),
        Math.round(a.b + (b.b - a.b) * p)
      );
    }
  };

  /* ---------- UUID ---------- */
  U.uuid = {
    v4: function () {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    },
    v7: function (time) {
      const t = time || Date.now();
      const ts = t.toString(16).padStart(16, '0');
      const rand = Array.from({length: 16}, () => Math.random()*16|0).map(n => n.toString(16)).join('');
      return `${ts.slice(0,8)}-${ts.slice(8,12)}-7${ts.slice(12,16)}-${rand.slice(0,4)}-${rand.slice(4)}`;
    }
  };

  /* ---------- Password ---------- */
  U.password = {
    generate: function (opts = {}) {
      const len = opts.length || 16;
      const lower = opts.lower !== false;
      const upper = opts.upper !== false;
      const numbers = opts.numbers !== false;
      const symbols = opts.symbols || false;
      const exclude = opts.exclude || '';
      let chars = '';
      if (lower) chars += 'abcdefghijklmnopqrstuvwxyz';
      if (upper) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      if (numbers) chars += '0123456789';
      if (symbols) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';
      chars = chars.split('').filter(c => !exclude.includes(c)).join('');
      if (!chars) return '';
      const arr = new Uint32Array(len);
      crypto.getRandomValues(arr);
      let result = '';
      for (let i = 0; i < len; i++) result += chars[arr[i] % chars.length];
      return result;
    },
    strength: function (pw) {
      let score = 0;
      if (pw.length >= 8) score++;
      if (pw.length >= 12) score++;
      if (pw.length >= 16) score++;
      if (/[a-z]/.test(pw)) score++;
      if (/[A-Z]/.test(pw)) score++;
      if (/[0-9]/.test(pw)) score++;
      if (/[^a-zA-Z0-9]/.test(pw)) score++;
      const levels = ['极弱', '弱', '一般', '中等', '强', '很强', '极强'];
      return { score, level: levels[Math.min(score, levels.length - 1)] };
    }
  };

  /* ---------- Date ---------- */
  U.date = {
    format: function (d, fmt = 'YYYY-MM-DD HH:mm:ss') {
      const o = {
        'M+': d.getMonth() + 1,
        'd+': d.getDate(),
        'H+': d.getHours(),
        'm+': d.getMinutes(),
        's+': d.getSeconds(),
        'q+': Math.floor((d.getMonth() + 3) / 3),
        'S': d.getMilliseconds()
      };
      const year = String(d.getFullYear());
      let f = fmt;
      f = f.replace(/yyyy|YYYY/g, year);
      f = f.replace(/yy|YY/g, year.slice(-2));
      for (const k in o) {
        f = f.replace(new RegExp(k + '+'), m => String(o[k]).padStart(m.length, '0'));
      }
      return f;
    },
    diff: function (d1, d2) {
      const a = new Date(d1).getTime();
      const b = new Date(d2).getTime();
      const diff = Math.abs(a - b);
      return {
        days: Math.floor(diff / 86400000),
        hours: Math.floor((diff % 86400000) / 3600000),
        minutes: Math.floor((diff % 3600000) / 60000),
        seconds: Math.floor((diff % 60000) / 1000)
      };
    },
    addDays: function (d, days) {
      const r = new Date(d);
      r.setDate(r.getDate() + days);
      return r;
    },
    workdays: function (start, end) {
      const s = new Date(start).getTime();
      const e = new Date(end).getTime();
      let count = 0;
      for (let t = s; t <= e; t += 86400000) {
        const day = new Date(t).getDay();
        if (day !== 0 && day !== 6) count++;
      }
      return count;
    },
    weekNum: function (d) {
      const date = new Date(d);
      date.setHours(0, 0, 0, 0);
      date.setDate(date.getDate() + 4 - (date.getDay() || 7));
      const yearStart = new Date(date.getFullYear(), 0, 1);
      const weekNo = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
      return weekNo;
    },
    leapYear: function (y) {
      return (y % 4 === 0 && y % 100 !== 0) || (y % 400 === 0);
    }
  };

  /* ---------- Regex ---------- */
  U.regex = {
    test: function (pattern, flags, str) {
      try {
        const re = new RegExp(pattern, flags);
        const matches = [];
        let m;
        if (re.global) {
          while ((m = re.exec(str)) !== null) {
            matches.push({ match: m[0], index: m.index, groups: m.slice(1) });
            if (m.index === re.lastIndex) re.lastIndex++;
          }
        } else if ((m = re.exec(str))) {
          matches.push({ match: m[0], index: m.index, groups: m.slice(1) });
        }
        return { matches, error: null };
      } catch (e) {
        return { matches: [], error: e.message };
      }
    }
  };

  /* ---------- Diff ---------- */
  U.diff = function (a, b) {
    const aLines = a.split('\n');
    const bLines = b.split('\n');
    const n = aLines.length, m = bLines.length;
    const dp = Array.from({length: n + 1}, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) {
      for (let j = m - 1; j >= 0; j--) {
        if (aLines[i] === bLines[j]) dp[i][j] = dp[i+1][j+1] + 1;
        else dp[i][j] = Math.max(dp[i+1][j], dp[i][j+1]);
      }
    }
    const result = [];
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (aLines[i] === bLines[j]) {
        result.push({ type: 'same', text: aLines[i] });
        i++; j++;
      } else if (dp[i+1][j] >= dp[i][j+1]) {
        result.push({ type: 'del', text: aLines[i] });
        i++;
      } else {
        result.push({ type: 'add', text: bLines[j] });
        j++;
      }
    }
    while (i < n) { result.push({ type: 'del', text: aLines[i] }); i++; }
    while (j < m) { result.push({ type: 'add', text: bLines[j] }); j++; }
    return result;
  };

  /* ---------- Toast / Notification ---------- */
  U.toast = function (msg, type = 'info') {
    let container = U.$('.toast-container');
    if (!container) {
      container = U.el('div', { class: 'toast-container' });
      document.body.appendChild(container);
    }
    const toast = U.el('div', { class: 'toast toast-' + type, text: msg });
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  };

  /* ---------- Copy to clipboard ---------- */
  U.copy = async function (text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); ta.remove(); return true; }
      catch { ta.remove(); return false; }
    }
  };

  /* ---------- Debounce ---------- */
  U.debounce = function (fn, wait) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), wait);
    };
  };

  /* ---------- Export ---------- */
  global.U = U;
})(window);