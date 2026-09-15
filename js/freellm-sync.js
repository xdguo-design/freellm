/* ============================================================
   FreeLLM Sync — 站点级用户配置同步模块
   ------------------------------------------------------------
   作用范围：整个 freellm.top（模型/厂家/Skills/工具/指南/日志…）
   存储策略：localStorage 即时生效 + GitHub Gist 云端同步
   接入方式（任何页面，零逻辑成本）：

     <script src="/js/freellm-sync.js"></script>

     <!-- 声明式接入卡片：自动记录浏览历史 -->
     <a href="/models/groq/" data-sync
        data-sync-type="model"
        data-sync-id="groq"
        data-sync-name="Groq"
        data-sync-url="/models/groq/">…</a>

     <!-- 加 data-sync-star 属性：自动注入 ★ 收藏按钮 -->
     <a href="/skills/pdf/" data-sync data-sync-star …>…</a>

     <!-- 认证按钮（可选，任意页面放一个空按钮即可） -->
     <button id="fl-sync-auth">GitHub</button>

   JS API：
     FreeLLM.Sync.toggleFav({type,id,name,url}) → boolean
     FreeLLM.Sync.isFav(type, id)
     FreeLLM.Sync.favs(type?) / removeFav(type,id) / clearFavs()
     FreeLLM.Sync.track({type,id,name,url})   / hist() / clearHist()
     FreeLLM.Sync.getSetting(key, def) / setSetting(key, value)
     FreeLLM.Sync.setToken(pat) / hasToken() / getUser()
     FreeLLM.Sync.pushNow() / pullNow() / on(event, fn)
   ============================================================ */
(function (global) {
  'use strict';

  var LS = {
    fav: 'freellm-favorites',
    hist: 'freellm-history',
    set: 'freellm-settings',
    tok: 'freellm-gh-token',
    gist: 'freellm-gh-gist'
  };
  var GIST_FILE = 'freellm-config.json';
  var API = 'https://api.github.com';
  var HISTORY_MAX = 100;

  /* ---------- localStorage 基础 ---------- */
  function load(key, dflt) {
    try {
      var v = localStorage.getItem(key);
      return v == null ? dflt : JSON.parse(v);
    } catch (e) { return dflt; }
  }
  function save(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {}
  }

  var state = {
    token: load(LS.tok, null),
    gistId: load(LS.gist, null),
    user: null,
    pushTimer: null
  };

  /* ---------- 兼容迁移：旧的主题/语言键 ---------- */
  (function migrate() {
    var s = load(LS.set, {});
    var t = null;
    try { t = localStorage.getItem('freellm-theme'); } catch (e) {}
    if (t != null && s.theme == null) {
      s.theme = t === 'dark' ? 'dark' : 'light';
      save(LS.set, s);
    }
    var loc = null;
    try { loc = localStorage.getItem('free-ai-index-locale'); } catch (e) {}
    if (loc && !s.locale) { s.locale = loc; save(LS.set, s); }
  })();

  /* ---------- 核心数据 ---------- */
  function favs(type) {
    var list = load(LS.fav, []);
    return type ? list.filter(function (f) { return f.type === type; }) : list;
  }
  function hist(type) {
    var list = load(LS.hist, []);
    return type ? list.filter(function (h) { return h.type === type; }) : list;
  }
  function settingsObj() { return load(LS.set, {}); }

  function isFav(type, id) {
    return favs().some(function (f) { return f.type === type && f.id === id; });
  }

  function toggleFav(item) {
    var list = favs();
    var idx = list.findIndex(function (f) { return f.type === item.type && f.id === item.id; });
    if (idx >= 0) list.splice(idx, 1);
    else list.push({ type: item.type, id: item.id, name: item.name, url: item.url, ts: Date.now() });
    save(LS.fav, list);
    schedulePush();
    emit('fav');
    return idx < 0; // true = 已收藏
  }

  function removeFav(type, id) {
    save(LS.fav, favs().filter(function (f) { return !(f.type === type && f.id === id); }));
    schedulePush();
    emit('fav');
  }

  function clearFavs() {
    save(LS.fav, []);
    schedulePush();
    emit('fav');
  }

  function track(item) {
    var list = hist().filter(function (h) { return !(h.type === item.type && h.id === item.id); });
    list.unshift({ type: item.type, id: item.id, name: item.name, url: item.url, ts: Date.now() });
    save(LS.hist, list.slice(0, HISTORY_MAX));
    schedulePush();
    emit('hist');
  }

  function clearHist() {
    save(LS.hist, []);
    schedulePush();
    emit('hist');
  }

  function getSetting(key, dflt) {
    var s = settingsObj();
    if (key == null) return s;
    return (key in s) ? s[key] : dflt;
  }

  function setSetting(key, value) {
    var s = settingsObj();
    s[key] = value;
    save(LS.set, s);
    // 保持旧页面兼容（旧的行内脚本读 freellm-theme）
    if (key === 'theme') {
      try {
        if (value === 'dark') localStorage.setItem('freellm-theme', 'dark');
        else localStorage.removeItem('freellm-theme');
      } catch (e) {}
      applyTheme();
    }
    schedulePush();
    emit('set');
  }

  function applyTheme() {
    var t = getSetting('theme', null);
    if (t === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    else if (t === 'light') document.documentElement.removeAttribute('data-theme');
    // 'auto' 交给页面自己的 prefers-color-scheme 逻辑
  }

  /* ---------- 事件 ---------- */
  var listeners = {};
  function on(ev, fn) {
    (listeners[ev] = listeners[ev] || []).push(fn);
  }
  function emit(ev) {
    ((listeners[ev] || [])).forEach(function (fn) { try { fn(); } catch (e) {} });
    (listeners['*'] || []).forEach(function (fn) { try { fn(ev); } catch (e) {} });
  }

  /* ---------- GitHub 传输层 ---------- */
  function gh(method, path, body) {
    if (!state.token) return Promise.reject(new Error('NO_TOKEN'));
    return fetch(API + path, {
      method: method,
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + state.token,
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : undefined
    }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (j) {
          throw new Error(res.status + ' ' + (j.message || 'GitHub API error'));
        });
      }
      return res.json();
    });
  }

  function getUser() {
    if (!state.token) return Promise.resolve(null);
    if (state.user) return Promise.resolve(state.user);
    return gh('GET', '/user')
      .then(function (u) { state.user = u; return u; })
      .catch(function () { state.user = null; return null; });
  }

  function snapshot() {
    return {
      version: 2,
      updatedAt: Date.now(),
      favorites: favs(),
      history: hist(),
      settings: settingsObj()
    };
  }

  function ensureGist() {
    if (state.gistId) {
      return gh('GET', '/gists/' + state.gistId).then(function () { return state.gistId; })
        .catch(function () {
          state.gistId = null;
          return createGist();
        });
    }
    return createGist();
  }

  function createGist() {
    return gh('POST', '/gists', {
      description: 'FreeLLM config (favorites / history / settings)',
      public: false,
      files: (function () { var f = {}; f[GIST_FILE] = { content: JSON.stringify(snapshot(), null, 2) }; return f; })()
    }).then(function (gist) {
      state.gistId = gist.id;
      save(LS.gist, gist.id);
      return gist.id;
    });
  }

  function pushNow() {
    if (!state.token) return Promise.resolve(false);
    return ensureGist().then(function (id) {
      var files = {};
      files[GIST_FILE] = { content: JSON.stringify(snapshot(), null, 2) };
      return gh('PATCH', '/gists/' + id, { files: files });
    }).then(function () { return true; });
  }

  function schedulePush() {
    if (!state.token) return;
    clearTimeout(state.pushTimer);
    state.pushTimer = setTimeout(function () {
      pushNow().catch(function (err) { console.warn('[freellm-sync] push failed:', err.message); });
    }, 2000);
  }

  function pullNow() {
    if (!state.token || !state.gistId) return Promise.resolve(false);
    return gh('GET', '/gists/' + state.gistId).then(function (gist) {
      var f = gist.files && gist.files[GIST_FILE];
      if (!f || !f.content) return false;
      var remote;
      try { remote = JSON.parse(f.content); } catch (e) { return false; }

      // 收藏合并：按 type+id 并集，时间戳新者胜
      var fmap = new Map();
      favs().forEach(function (x) { fmap.set(x.type + '|' + x.id, x); });
      (remote.favorites || []).forEach(function (x) {
        if (!x || !x.type || !x.id) return;
        var k = x.type + '|' + x.id;
        var cur = fmap.get(k);
        if (!cur || (x.ts || 0) > (cur.ts || 0)) fmap.set(k, x);
      });
      save(LS.fav, Array.from(fmap.values()));

      // 历史合并：按 type+id 去重，最新在前
      var hmap = new Map();
      hist().forEach(function (x) { hmap.set(x.type + '|' + x.id, x); });
      (remote.history || []).forEach(function (x) {
        if (!x || !x.type || !x.id) return;
        var k = x.type + '|' + x.id;
        var cur = hmap.get(k);
        if (!cur || (x.ts || 0) > (cur.ts || 0)) hmap.set(k, x);
      });
      var merged = Array.from(hmap.values())
        .sort(function (a, b) { return (b.ts || 0) - (a.ts || 0); })
        .slice(0, HISTORY_MAX);
      save(LS.hist, merged);

      // 设置合并：远端按键覆盖
      var s = Object.assign(settingsObj(), remote.settings || {});
      save(LS.set, s);

      applyTheme();
      emit('fav'); emit('hist'); emit('set');
      return true;
    });
  }

  /* ---------- 认证 ---------- */
  function setToken(token) {
    state.token = token ? String(token).trim() : null;
    if (state.token) {
      save(LS.tok, state.token);
      pullNow().catch(function () {});
      schedulePush();
    } else {
      try { localStorage.removeItem(LS.tok); localStorage.removeItem(LS.gist); } catch (e) {}
      state.gistId = null;
      state.user = null;
    }
    emit('auth');
  }

  function hasToken() { return !!state.token; }

  /* ---------- UI：toast / 认证弹窗 / 收藏星标 ---------- */
  function injectStyles() {
    if (document.getElementById('freellm-sync-style')) return;
    var css = [
      '.fl-sync-star{position:absolute;top:8px;right:8px;width:24px;height:24px;display:grid;place-items:center;',
      'border:0;border-radius:6px;background:transparent;color:var(--ink-tertiary,#B4B4B0);cursor:pointer;',
      'font-size:14px;line-height:1;padding:0;z-index:5;transition:color .15s,transform .15s;}',
      '.fl-sync-star:hover{color:var(--accent,#1744E8);transform:scale(1.15);}',
      '.fl-sync-star.is-fav{color:#F5A623;}',
      '.fl-auth-mask{position:fixed;inset:0;z-index:3000;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;}',
      '.fl-auth-modal{width:min(92vw,420px);background:var(--surface,#fff);color:var(--ink,#2F3437);border-radius:12px;padding:24px;',
      'box-shadow:0 20px 60px rgba(0,0,0,.2);font-family:var(--font-sans,system-ui,sans-serif);}',
      '.fl-auth-modal h3{margin:0 0 8px;font-size:18px;}',
      '.fl-auth-modal p{margin:0 0 14px;font-size:13px;line-height:1.6;color:var(--ink-secondary,#787774);}',
      '.fl-auth-modal a{color:var(--accent,#1744E8);}',
      '.fl-auth-modal input{width:100%;padding:10px 12px;border:1px solid var(--line,#EAEAEA);border-radius:6px;',
      'font:12px/1.4 ui-monospace,monospace;margin-bottom:14px;box-sizing:border-box;background:var(--canvas,#FBFBFA);color:inherit;}',
      '.fl-auth-actions{display:flex;gap:8px;justify-content:flex-end;}',
      '.fl-auth-actions button{padding:8px 16px;border-radius:6px;border:1px solid var(--line,#EAEAEA);cursor:pointer;font-size:13px;background:var(--surface,#fff);color:inherit;}',
      '.fl-auth-actions button.primary{background:var(--accent,#1744E8);border-color:var(--accent);color:#fff;}',
      '.fl-sync-toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:3001;padding:10px 18px;border-radius:9999px;',
      'background:var(--ink,#111);color:var(--surface,#fff);font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,.2);',
      'font-family:var(--font-sans,system-ui,sans-serif);animation:flToastIn .25s ease;}',
      '@keyframes flToastIn{from{opacity:0;transform:translate(-50%,8px);}to{opacity:1;transform:translate(-50%,0);}}'
    ].join('');
    var style = document.createElement('style');
    style.id = 'freellm-sync-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function toast(msg) {
    injectStyles();
    var el = document.createElement('div');
    el.className = 'fl-sync-toast';
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(function () {
      el.style.transition = 'opacity .3s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 300);
    }, 2200);
  }

  function authModal() {
    injectStyles();
    return new Promise(function (resolve) {
      var mask = document.createElement('div');
      mask.className = 'fl-auth-mask';
      mask.innerHTML =
        '<div class="fl-auth-modal">' +
        '<h3>连接 GitHub 同步</h3>' +
        '<p>粘贴一个带 <code>gist</code> 权限的 ' +
        '<a href="https://github.com/settings/tokens/new?scopes=gist&description=FreeLLM%20sync" target="_blank" rel="noopener">Personal Access Token</a>，' +
        '收藏与历史将同步到你名下的私有 Gist。Token 仅保存在本机浏览器。</p>' +
        '<input type="password" placeholder="ghp_… 或 github_pat_…" spellcheck="false">' +
        '<div class="fl-auth-actions">' +
        '<button type="button" class="fl-cancel">取消</button>' +
        '<button type="button" class="primary fl-save">保存并同步</button>' +
        '</div></div>';
      document.body.appendChild(mask);
      var input = mask.querySelector('input');
      input.focus();
      function close(val) { mask.remove(); resolve(val); }
      mask.querySelector('.fl-cancel').addEventListener('click', function () { close(null); });
      mask.addEventListener('click', function (e) { if (e.target === mask) close(null); });
      mask.querySelector('.fl-save').addEventListener('click', function () {
        var v = input.value.trim();
        if (!v) return;
        setToken(v);
        toast('已连接 GitHub，正在同步…');
        close(v);
      });
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') mask.querySelector('.fl-save').click();
        if (e.key === 'Escape') close(null);
      });
    });
  }

  function bindAuthButton(el) {
    if (!el) return;
    el.hidden = false;
    function paint() {
      getUser().then(function (u) {
        el.classList.toggle('authenticated', !!u);
        var label = el.querySelector('.gh-login-text') || el.querySelector('.gh-label');
        if (label) label.textContent = u ? u.login : 'GitHub';
      });
    }
    el.addEventListener('click', function () {
      if (hasToken()) {
        if (window.confirm('断开 GitHub 连接？本地数据保留，云端 Gist 不删除。')) setToken(null);
      } else {
        authModal().then(paint);
      }
    });
    paint();
  }

  /* ---------- 星标按钮 ---------- */
  function starButton(item) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'fl-sync-star';
    btn.title = '收藏';
    btn.textContent = '☆';
    function paint() {
      var fav = isFav(item.type, item.id);
      btn.classList.toggle('is-fav', fav);
      btn.textContent = fav ? '★' : '☆';
    }
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var added = toggleFav(item);
      toast(added ? '已收藏「' + item.name + '」' : '已取消收藏');
    });
    on('fav', paint);
    on('auth', paint);
    paint();
    return btn;
  }

  /* ---------- 声明式绑定 ---------- */
  function bind(root) {
    injectStyles();
    (root || document).querySelectorAll('[data-sync]').forEach(function (card) {
      if (card.__flSyncBound) return;
      card.__flSyncBound = true;
      var item = {
        type: card.dataset.syncType || 'page',
        id: card.dataset.syncId || card.getAttribute('href') || location.pathname,
        name: card.dataset.syncName || (card.textContent || '').trim().slice(0, 60),
        url: card.dataset.syncUrl || card.getAttribute('href') || location.pathname
      };
      card.style.position = card.style.position || 'relative';
      card.addEventListener('click', function () { track(item); });
      if (card.hasAttribute('data-sync-star')) {
        card.appendChild(starButton(item));
      }
    });
  }

  /* ---------- 自动绑定：站点详情页链接（免逐页配置） ---------- */
  var DETAIL_RE = /^\/(models|providers|skills|guides)\/[^/]+\/?$/;
  var DETAIL_TYPE = { models: 'model', providers: 'provider', skills: 'skill', guides: 'guide' };

  function autoName(a) {
    var zh = a.querySelector('[lang="zh-CN"]');
    var t = (zh || a).textContent || '';
    return t.replace(/\s+/g, ' ').trim().slice(0, 60);
  }

  function autoBind(root) {
    (root || document).querySelectorAll('a[href^="/"]').forEach(function (a) {
      if (a.__flSyncBound) return;
      var href = a.getAttribute('href') || '';
      var m = DETAIL_RE.exec(href);
      if (!m) return;
      // 跳过导航 / 页脚 / 面包屑里的链接，只处理正文内容卡片
      if (a.closest('nav,footer,header')) return;
      a.__flSyncBound = true;
      var type = DETAIL_TYPE[m[1]];
      var item = { type: type, id: href.replace(/^\/|\/$/g, '').split('/').pop(), name: autoName(a), url: href };
      a.addEventListener('click', function () { track(item); });
      a.style.position = a.style.position || 'relative';
      a.appendChild(starButton(item));
    });
  }

  function init() {
    applyTheme();
    bind(document);
    autoBind(document);
    bindAuthButton(document.getElementById('fl-sync-auth') || document.getElementById('gh-login'));
    if (state.token) {
      pullNow().catch(function (err) { console.warn('[freellm-sync] pull failed:', err.message); });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ---------- 导出 ---------- */
  global.FreeLLM = global.FreeLLM || {};
  global.FreeLLM.Sync = {
    on: on,
    bind: bind,
    autoBind: autoBind,
    toast: toast,
    // 收藏
    favs: favs,
    isFav: isFav,
    toggleFav: toggleFav,
    removeFav: removeFav,
    clearFavs: clearFavs,
    // 历史
    hist: hist,
    track: track,
    clearHist: clearHist,
    // 设置
    getSetting: getSetting,
    setSetting: setSetting,
    // GitHub
    setToken: setToken,
    hasToken: hasToken,
    getUser: getUser,
    pushNow: pushNow,
    pullNow: pullNow,
    authModal: authModal
  };
})(window);