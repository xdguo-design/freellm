/* ============================================================
   FreeLLM Tools — 工具合集页应用逻辑
   网格渲染 / 搜索 / 分类 / 模态框 / 收藏 / 历史 / 主题
   同步能力全部来自站点级模块 FreeLLM.Sync
   ============================================================ */
(function () {
  'use strict';

  var Sync = window.FreeLLM && window.FreeLLM.Sync;
  var Tools = window.Tools;
  var U = window.U;

  var tabsEl = document.getElementById('tool-category-tabs');
  var gridEl = document.getElementById('tool-grid');
  var searchEl = document.getElementById('tool-search');
  var countEl = document.getElementById('tool-count');
  var totalEl = document.getElementById('tool-total');

  var favSection = document.getElementById('favorites-section');
  var favGrid = document.getElementById('favorites-grid');
  var histSection = document.getElementById('history-section');
  var histList = document.getElementById('history-list');

  var modal = document.getElementById('tool-modal');
  var modalTitle = document.getElementById('tool-modal-title');
  var modalFrame = document.getElementById('tool-modal-frame');
  var favBtn = document.getElementById('fav-btn');
  var favIcon = document.getElementById('fav-icon');

  var activeCat = 'all';
  var currentTool = null;

  if (!Tools) return;
  totalEl.textContent = Tools.total;

  /* ---------- 主题 ---------- */
  function applyTheme() {
    var t = Sync ? Sync.getSetting('theme', null) : null;
    if (t === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    else if (t === 'light') document.documentElement.removeAttribute('data-theme');
    else {
      // auto：跟随系统
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
    }
  }
  applyTheme();

  document.getElementById('theme-toggle').addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    var next = cur === 'dark' ? 'light' : 'dark';
    if (Sync) Sync.setSetting('theme', next);
    applyTheme();
  });

  /* ---------- 卡片 ---------- */
  function catOf(id) {
    return Tools.cats.find(function (c) { return c.id === id; });
  }

  function cardEl(t) {
    var cat = catOf(t.cat);
    var card = document.createElement('a');
    card.className = 'tool-card' + (Sync && Sync.isFav('tool', t.id) ? ' favorited' : '');
    card.href = '#';
    card.setAttribute('aria-label', t.name);
    card.setAttribute('data-sync', '');
    card.setAttribute('data-sync-type', 'tool');
    card.setAttribute('data-sync-id', t.id);
    card.setAttribute('data-sync-name', t.name);
    card.setAttribute('data-sync-url', '/tools/?tool=' + t.id);
    card.setAttribute('data-sync-star', '');
    card.innerHTML =
      '<div class="tool-card-top">' +
        '<span class="tool-category ' + (cat ? cat.cls : '') + '">' + (cat ? cat.label : t.cat) + '</span>' +
        (t.hot ? '<span class="tool-hot">热门</span>' : '') +
      '</div>' +
      '<h2>' + t.name + '</h2>' +
      '<p>' + t.desc + '</p>';
    card.addEventListener('click', function (e) {
      e.preventDefault();
      openTool(t);
    });
    return card;
  }

  /* ---------- 渲染 ---------- */
  function renderTabs() {
    tabsEl.innerHTML = '';
    var allBtn = document.createElement('button');
    allBtn.className = 'tool-category-tab' + (activeCat === 'all' ? ' is-active' : '');
    allBtn.type = 'button';
    allBtn.innerHTML = '<span>全部</span><small>' + Tools.total + '</small>';
    allBtn.onclick = function () { setCat('all'); };
    tabsEl.appendChild(allBtn);
    Tools.cats.forEach(function (c) {
      if (!c.count) return;
      var btn = document.createElement('button');
      btn.className = 'tool-category-tab' + (activeCat === c.id ? ' is-active' : '');
      btn.type = 'button';
      btn.innerHTML = '<span>' + c.label + '</span><small>' + c.count + '</small>';
      btn.onclick = function () { setCat(c.id); };
      tabsEl.appendChild(btn);
    });
  }

  function setCat(id) {
    activeCat = id;
    renderTabs();
    renderGrid();
  }

  function getFiltered() {
    var q = (searchEl.value || '').trim().toLowerCase();
    return Tools.all.filter(function (t) {
      if (activeCat !== 'all' && t.cat !== activeCat) return false;
      if (q) {
        var hay = (t.name + ' ' + t.desc + ' ' + t.id).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function renderGrid() {
    var list = getFiltered();
    gridEl.innerHTML = '';
    if (!list.length) {
      gridEl.innerHTML =
        '<div class="tools-empty"><p>没有匹配的工具</p>' +
        '<button id="clear-filter-btn" type="button">清空筛选</button></div>';
      document.getElementById('clear-filter-btn').onclick = clearSearch;
      countEl.textContent = '显示 0 / ' + Tools.total;
      return;
    }
    var frag = document.createDocumentFragment();
    list.forEach(function (t) { frag.appendChild(cardEl(t)); });
    gridEl.appendChild(frag);
    if (Sync) Sync.bind(gridEl); // 为动态卡片注入历史追踪 + 星标
    countEl.textContent = '显示 ' + list.length + ' / ' + Tools.total;
  }

  function clearSearch() {
    searchEl.value = '';
    renderGrid();
  }
  searchEl.addEventListener('input', U.debounce(renderGrid, 120));

  /* ---------- 收藏区 / 历史区 ---------- */
  function renderFavorites() {
    if (!Sync) return;
    var favs = Sync.favs('tool');
    if (!favs.length) {
      favSection.hidden = true;
      return;
    }
    favSection.hidden = false;
    favGrid.innerHTML = '';
    var frag = document.createDocumentFragment();
    favs.forEach(function (f) {
      var t = Tools.get(f.id);
      if (t) frag.appendChild(cardEl(t));
    });
    favGrid.appendChild(frag);
    Sync.bind(favGrid);
  }

  function renderHistory() {
    if (!Sync) return;
    var items = Sync.hist('tool').slice(0, 8);
    if (!items.length) {
      histSection.hidden = true;
      return;
    }
    histSection.hidden = false;
    histList.innerHTML = '';
    items.forEach(function (h) {
      var row = document.createElement('div');
      row.className = 'history-item';
      var t = Tools.get(h.id);
      row.innerHTML =
        '<span class="hi-name">' + (t ? t.name : h.id) + '</span>' +
        '<span class="hi-input"></span>' +
        '<span class="hi-time">' + new Date(h.ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) + '</span>';
      row.addEventListener('click', function () {
        if (t) openTool(t);
      });
      histList.appendChild(row);
    });
  }

  document.getElementById('clear-favorites').addEventListener('click', function () {
    if (Sync && window.confirm('清空所有工具收藏？（云端 Gist 会在下次推送时同步）')) {
      // 只清工具类收藏
      Sync.favs().filter(function (f) { return f.type !== 'tool'; })
        .forEach(function () {});
      var others = Sync.favs().filter(function (f) { return f.type !== 'tool'; });
      Sync.clearFavs();
      others.forEach(function (f) { Sync.toggleFav(f); });
    }
  });
  document.getElementById('clear-history').addEventListener('click', function () {
    if (Sync && window.confirm('清空浏览历史？')) Sync.clearHist();
  });

  /* ---------- 模态框 ---------- */
  function openTool(t) {
    currentTool = t;
    modalTitle.textContent = t.name;
    paintFav();
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    // 支持直链：/tools/?tool=base64
    try {
      var u = new URL(location.href);
      u.searchParams.set('tool', t.id);
      history.replaceState(null, '', u);
    } catch (e) {}

    // 先探测工具页是否存在，404 则显示「开发中」占位
    var fallback = document.getElementById('tool-modal-fallback');
    var fallbackLink = document.getElementById('tool-modal-fallback-link');
    fallbackLink.hidden = true;
    fallback.classList.remove('show');
    modalFrame.hidden = false;
    modalFrame.src = '';
    fetch(Tools.getToolUrl(t.id), { method: 'HEAD' })
      .then(function (res) {
        if (currentTool !== t) return; // 用户已切换/关闭
        if (res.ok) {
          modalFrame.hidden = false;
          modalFrame.src = Tools.getToolUrl(t.id);
        } else {
          modalFrame.hidden = true;
          fallback.querySelector('p').textContent = '「' + t.name + '」正在开发中，敬请期待';
          fallback.classList.add('show');
        }
      })
      .catch(function () {
        if (currentTool === t) { modalFrame.hidden = true; fallback.classList.add('show'); }
      });
  }

  function closeToolModal() {
    modal.classList.remove('open');
    document.body.style.overflow = '';
    modalFrame.src = '';
    currentTool = null;
    try {
      var u = new URL(location.href);
      u.searchParams.delete('tool');
      history.replaceState(null, '', u);
    } catch (e) {}
  }
  window.closeToolModal = closeToolModal;

  function paintFav() {
    if (!currentTool || !Sync) return;
    var fav = Sync.isFav('tool', currentTool.id);
    favIcon.textContent = fav ? '★' : '☆';
    favBtn.classList.toggle('favorited', fav);
    favBtn.title = fav ? '取消收藏' : '收藏';
  }

  favBtn.addEventListener('click', function () {
    if (!currentTool || !Sync) return;
    var added = Sync.toggleFav({ type: 'tool', id: currentTool.id, name: currentTool.name, url: '/tools/?tool=' + currentTool.id });
    if (Sync.toast) Sync.toast(added ? '已收藏「' + currentTool.name + '」' : '已取消收藏');
    paintFav();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && modal.classList.contains('open')) closeToolModal();
  });

  /* ---------- 同步事件联动 ---------- */
  if (Sync) {
    Sync.on('fav', function () {
      renderFavorites();
      // 主网格里的卡片可能有收藏态变化，简单起见重绘
      renderGrid();
      if (currentTool) paintFav();
    });
    Sync.on('hist', renderHistory);
    Sync.on('set', applyTheme);
  }

  /* ---------- 启动 ---------- */
  renderTabs();
  renderGrid();
  renderFavorites();
  renderHistory();

  // 直链打开：/tools/?tool=base64
  (function openFromQuery() {
    var id = new URLSearchParams(location.search).get('tool');
    if (id) {
      var t = Tools.get(id);
      if (t) openTool(t);
    }
  })();
})();