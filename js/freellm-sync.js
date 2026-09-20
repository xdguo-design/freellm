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

  /* ---------- FreeLLM 2026 site-wide visual system ---------- */
  (function installSiteVisualSystem() {
    if (document.documentElement.classList.contains('fl-pastel-ui')) return;
    document.documentElement.classList.add('fl-pastel-ui');

    var themeLink = document.createElement('link');
    themeLink.id = 'freellm-site-theme';
    themeLink.rel = 'stylesheet';
    themeLink.href = '/css/freellm-pastel-ui.css?v=20260920';
    document.head.appendChild(themeLink);

    function sectionFor(path) {
      if (path === '/' || path.indexOf('/design/free-china-ai-index') === 0) return 'home';
      if (path.indexOf('/skills/lab') === 0) return 'workflow';
      if (path.indexOf('/skills') === 0) return 'skills';
      if (path.indexOf('/tools') === 0) return 'tools';
      if (path.indexOf('/logs') === 0) return 'logs';
      if (path.indexOf('/models') === 0 || path.indexOf('/providers') === 0) return 'models';
      if (path.indexOf('/about') === 0 || path.indexOf('/links') === 0 || path.indexOf('/privacy') === 0 || path.indexOf('/terms') === 0) return 'about';
      if (path.indexOf('/offers') === 0 || path.indexOf('/category') === 0 || path.indexOf('/guides') === 0) return 'models';
      return 'home';
    }

    function railLink(href, icon, label, section, current) {
      var state = section === current ? ' aria-current="page"' : '';
      return '<a href="' + href + '"' + state + '><span class="fl-site-nav-icon" aria-hidden="true">' + icon + '</span><span>' + label + '</span></a>';
    }

    function addSiteChrome() {
      if (!document.body) return;
      /* Move the theme link to the end of <head>. On the homepage this shared
         script is loaded early, before the legacy inline CSS; moving it here
         guarantees the new design system wins the cascade everywhere. */
      if (themeLink.parentNode) document.head.appendChild(themeLink);

      document.body.classList.add('fl-ui-v2');
      var path = window.location.pathname || '/';
      var current = sectionFor(path);
      document.body.setAttribute('data-fl-section', current);

      if (!document.querySelector('.fl-site-rail')) {
        var rail = document.createElement('aside');
        rail.className = 'fl-site-rail';
        rail.setAttribute('aria-label', 'FreeLLM 主导航');
        rail.innerHTML =
          '<a class="fl-site-brand" href="/">' +
            '<span class="fl-site-brand-mark" aria-hidden="true">AI</span>' +
            '<span class="fl-site-brand-copy"><strong>FreeLLM</strong><small>让 AI 更自由地被使用</small></span>' +
          '</a>' +
          '<nav class="fl-site-nav">' +
            railLink('/', '⌂', '首页', 'home', current) +
            railLink('/models/', '▣', '模型', 'models', current) +
            railLink('/skills/', '✦', 'Skills', 'skills', current) +
            railLink('/tools/', '⌘', '工具', 'tools', current) +
            railLink('/skills/lab/', '⌁', '工作流', 'workflow', current) +
            railLink('/logs/', '◷', '更新', 'logs', current) +
            railLink('/about/', 'ⓘ', '关于', 'about', current) +
          '</nav>' +
          '<div class="fl-site-rail-note"><span>好的 AI 资源</span><br>让更多人真正受益 ♡</div>';
        document.body.insertBefore(rail, document.body.firstChild);
      }

      if (!document.querySelector('.fl-site-ribbon')) {
        var ribbon = document.createElement('div');
        ribbon.className = 'fl-site-ribbon';
        var pageTitle = (document.title || 'FreeLLM').split('·')[0].split('|')[0].trim();
        ribbon.innerHTML =
          '<span class="fl-site-ribbon-title">FREE AI INDEX / ' + escapeText(pageTitle) + '</span>' +
          '<span class="fl-site-ribbon-actions">' +
            '<a href="/favorites/">我的收藏</a>' +
            '<a href="/">资源首页 ↗</a>' +
          '</span>';
        var anchor = document.querySelector('.catalog-app, .skills-page, .skill-lab-page, .tools-page, .page, body > header, body > main');
        if (anchor && anchor.parentNode === document.body) document.body.insertBefore(ribbon, anchor);
        else document.body.insertBefore(ribbon, document.body.children[1] || null);
      }
    }

    function escapeText(value) {
      return String(value || '').replace(/[&<>"']/g, function (ch) {
        return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[ch];
      });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', addSiteChrome, { once: true });
    } else {
      addSiteChrome();
    }
  })();

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

  /* ---------- GitHub OAuth 登录（经 /api/gh-oauth 换票，见 docs/github-oauth.md） ---------- */
  var OAUTH_EP = '/api/gh-oauth';
  var OAUTH_ST = 'freellm-gh-oauth';
  var _clientId; // undefined=未查询, null=不可用, 字符串=可用
  function oauthClientId() {
    if (_clientId !== undefined) return Promise.resolve(_clientId);
    return fetch(OAUTH_EP, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { _clientId = (d && d.clientId) || null; return _clientId; })
      .catch(function () { _clientId = null; return null; });
  }

  function startOAuth() {
    return oauthClientId().then(function (cid) {
      if (!cid) {
        toast('当前站点未配置 GitHub OAuth，请使用下方 Token 方式');
        return false;
      }
      var bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      var st = Array.from(bytes).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      try {
        // 存相对路径：location.origin 在个别上下文会取到字符串 "null"，不可靠
        sessionStorage.setItem(OAUTH_ST, JSON.stringify({ state: st, back: location.pathname + location.search }));
      } catch (e) {}
      location.href = 'https://github.com/login/oauth/authorize' +
        '?client_id=' + encodeURIComponent(cid) +
        '&scope=gist' +
        '&state=' + encodeURIComponent(st) +
        '&redirect_uri=' + encodeURIComponent(location.origin + '/');
      return true;
    });
  }

  /* 授权回跳处理：/?code=…&state=… → 换票 → setToken → 清洗 URL 回原页面 */
  function handleOAuthRedirect() {
    var q;
    try { q = new URLSearchParams(location.search); } catch (e) { return; }
    var code = q.get('code');
    var st = q.get('state');
    if (!code || !st) return;
    var saved = null;
    try { saved = JSON.parse(sessionStorage.getItem(OAUTH_ST) || 'null'); } catch (e) {}
    try { sessionStorage.removeItem(OAUTH_ST); } catch (e) {}
    var back = (saved && typeof saved.back === 'string' && saved.back.charAt(0) === '/') ? saved.back : '/';
    if (!saved || saved.state !== st) {
      history.replaceState(null, '', back);
      return;
    }
    fetch(OAUTH_EP, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code })
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (res.ok && res.d && res.d.token) {
          toast('GitHub 登录成功，正在同步…');
          setToken(res.d.token);
        } else {
          toast('GitHub 登录失败：' + ((res.d && res.d.error) || '未知错误'));
        }
      })
      .catch(function () { toast('GitHub 登录失败：网络错误'); })
      .then(function () { history.replaceState(null, '', back); });
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
      '.fl-oauth{width:100%;display:inline-flex;gap:8px;align-items:center;justify-content:center;padding:10px 16px;',
      'border:1px solid var(--accent,#1744E8);border-radius:6px;background:var(--accent,#1744E8);color:#fff;cursor:pointer;',
      'font-size:13.5px;font-weight:600;font-family:inherit;margin-bottom:6px;transition:opacity .15s;}',
      '.fl-oauth:hover{opacity:.9;}',
      '.fl-auth-modal details.fl-pat{margin:0 0 14px;}',
      '.fl-auth-modal details.fl-pat summary{cursor:pointer;font-size:12.5px;color:var(--ink-secondary,#787774);padding:4px 0;}',
      '.fl-pat-hint{font-size:12px;margin:8px 0 10px;}',
      '.fl-pat input{margin-bottom:10px;}',
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
      var GH_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.765.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>';
      mask.innerHTML =
        '<div class="fl-auth-modal">' +
        '<h3>连接 GitHub 同步</h3>' +
        '<p>使用 GitHub 一键登录，收藏与浏览历史将同步到你名下的<b>私有 Gist</b>。凭据仅保存在本机浏览器。</p>' +
        '<button type="button" class="fl-oauth">' + GH_SVG + '<span>使用 GitHub 登录</span></button>' +
        '<details class="fl-pat">' +
        '<summary>或粘贴 Personal Access Token（高级）</summary>' +
        '<p class="fl-pat-hint">创建一个带 <code>gist</code> 权限的 ' +
        '<a href="https://github.com/settings/tokens/new?scopes=gist&description=FreeLLM%20sync" target="_blank" rel="noopener">Personal Access Token</a>，' +
        '适用于未部署 OAuth 服务的镜像站。</p>' +
        '<input type="password" placeholder="ghp_… 或 github_pat_…" spellcheck="false">' +
        '<div class="fl-auth-actions">' +
        '<button type="button" class="fl-cancel">取消</button>' +
        '<button type="button" class="primary fl-save">保存并同步</button>' +
        '</div>' +
        '</details>' +
        '<div class="fl-auth-actions"><button type="button" class="fl-cancel">取消</button></div>' +
        '</div>';
      document.body.appendChild(mask);
      var input = mask.querySelector('input');
      mask.querySelectorAll('.fl-cancel').forEach(function (b) {
        b.addEventListener('click', function () { close(null); });
      });
      mask.addEventListener('click', function (e) { if (e.target === mask) close(null); });
      mask.querySelector('.fl-oauth').addEventListener('click', function () {
        startOAuth().then(function (started) { if (started) close(null); });
      });
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
      // OAuth 不可用（未配置 / 镜像站）时退回纯 PAT 模式
      oauthClientId().then(function (cid) {
        if (cid) return;
        mask.querySelector('.fl-oauth').style.display = 'none';
        var det = mask.querySelector('.fl-pat');
        det.open = true;
        det.querySelector('summary').style.display = 'none';
        input.focus();
      });
      function close(val) { mask.remove(); resolve(val); }
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
    on('auth', paint);
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
  var DETAIL_RE = /^\/(models|providers|skills|guides|offers)\/[^/]+\/?$/;
  var DETAIL_TYPE = { models: 'model', providers: 'provider', skills: 'skill', guides: 'guide', offers: 'offer' };

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

  function normalizeLocaleUrls() {
    var q;
    try { q = new URLSearchParams(location.search); } catch (e) { q = null; }
    if (q && q.has('lang')) {
      q.delete('lang');
      var search = q.toString();
      history.replaceState(null, '', location.pathname + (search ? '?' + search : '') + location.hash);
    }

    document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(function (link) {
      var href = link.getAttribute('href') || '';
      if (/[?&]lang=/i.test(href)) link.remove();
    });

    document.querySelectorAll('a[href]').forEach(function (a) {
      var raw = a.getAttribute('href') || '';
      if (!raw || raw.charAt(0) === '#' || /^(?:mailto:|tel:|javascript:)/i.test(raw)) return;
      var url;
      try { url = new URL(raw, location.href); } catch (e) { return; }
      if (url.origin !== location.origin || !url.searchParams.has('lang')) return;
      url.searchParams.delete('lang');
      var search = url.searchParams.toString();
      a.setAttribute('href', url.pathname + (search ? '?' + search : '') + url.hash);
    });
  }

  function init() {
    handleOAuthRedirect();
    normalizeLocaleUrls();
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
    startOAuth: startOAuth,
    pushNow: pushNow,
    pullNow: pullNow,
    authModal: authModal
  };
})(window);
