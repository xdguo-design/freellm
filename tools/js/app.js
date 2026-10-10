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
  var showAllButton = document.getElementById('tool-show-all');
  var categoryOverview = document.getElementById('tool-category-overview-grid');
  var popularPreview = document.getElementById('tool-popular-list');
  var historyPreview = document.getElementById('tools-history-preview');
  var favoritesPreview = document.getElementById('tools-favorites-preview');

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
  var showAll = false;
  var currentTool = null;
  var featuredOrder = ['base64','url-encode','md5','sha','html-entity','unicode','aes','file-hash','hmac','gzip','caesar','rot13','file-hex','base32','base58','base85','rsa','rsa-encrypt','ecc','hybrid-encrypt','jwt','totp','x509'];
  var categoryIcons = ['♧','⚖','✣','⚒','▤','▦','◷','▣','⌘','▧','◉','▧','⬟'];

  if (!Tools) return;
  totalEl.textContent = Tools.total;

  // Editorial use-case groups reference only actual registered local tools.
  // Keep native registry categories intact for tool metadata and static generation.
  var useCaseGroups = {
    productivity: { label: '生产力', cats: ['text', 'datetime', 'util'] },
    analytics: { label: '数据分析', ids: ['csv-json', 'csv-format', 'excel-convert', 'jsonpath', 'jmespath', 'table2csv', 'text2table', 'csv2md', 'json-schema', 'data-transfer'] },
    media: { label: '语音视频', ids: ['tts', 'audio-record', 'video2gif', 'spectrum', 'whitenoise'] },
    design: { label: '设计创作', cats: ['css', 'image'] }
  };
  function matchesCategory(tool, category) {
    if (category === 'all') return true;
    var group = useCaseGroups[category];
    if (group) return (group.cats || []).includes(tool.cat) || (group.ids || []).includes(tool.id);
    return tool.cat === category;
  }
  function useCaseCount(category) {
    return Tools.all.filter(function (tool) { return matchesCategory(tool, category); }).length;
  }

  // Allow category cards elsewhere on the site to open this page pre-filtered.
  (function selectCategoryFromQuery() {
    var requestedCategory = new URLSearchParams(location.search).get('category');
    if (requestedCategory && (
      Tools.cats.some(function (category) { return category.id === requestedCategory && category.count; }) ||
      (Object.prototype.hasOwnProperty.call(useCaseGroups, requestedCategory) && useCaseCount(requestedCategory) > 0)
    )) {
      activeCat = requestedCategory;
    }
  })();

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
    card.href = Tools.getToolUrl(t.id);
    card.setAttribute('aria-label', t.name);
    card.setAttribute('data-sync', '');
    card.setAttribute('data-sync-type', 'tool');
    card.setAttribute('data-sync-id', t.id);
    card.setAttribute('data-sync-name', t.name);
    card.setAttribute('data-sync-url', '/tools/?tool=' + t.id);
    card.setAttribute('data-sync-star', '');
    card.innerHTML =
      '<span class="tool-reference-icon" aria-hidden="true"></span>' +
      '<div class="tool-card-top">' +
        '<span class="tool-category ' + (cat ? cat.cls : '') + '">' + (cat ? cat.label : t.cat) + '</span>' +
        (t.hot ? '<span class="tool-hot">热门</span>' : '') +
      '</div>' +
      '<h2>' + t.name + '</h2>' +
      '<p>' + t.desc + '</p>' +
      '<div class="tool-card-reference-tags"><span>' + (cat ? cat.label : t.cat) + '</span><span>本地运行</span></div>';
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
    allBtn.innerHTML = '<i aria-hidden="true">⌕</i><span>全部</span><small>' + Tools.total + '</small>'; 
    allBtn.onclick = function () { setCat('all'); };
    tabsEl.appendChild(allBtn);
    Tools.cats.forEach(function (c) {
      if (!c.count) return;
      var btn = document.createElement('button');
      btn.className = 'tool-category-tab' + (activeCat === c.id ? ' is-active' : '');
      btn.type = 'button';
      btn.innerHTML = '<i aria-hidden="true">' + categoryIcons[Tools.cats.indexOf(c) % categoryIcons.length] + '</i><span>' + c.label + '</span><small>' + c.count + '</small>'; 
      btn.onclick = function () { setCat(c.id); };
      tabsEl.appendChild(btn);
    });
    Object.keys(useCaseGroups).forEach(function (id) {
      var count = useCaseCount(id);
      if (!count) return;
      var btn = document.createElement('button');
      btn.className = 'tool-category-tab' + (activeCat === id ? ' is-active' : '');
      btn.type = 'button';
      btn.innerHTML = '<span>' + useCaseGroups[id].label + '</span><small>' + count + '</small>';
      btn.onclick = function () { setCat(id); };
      tabsEl.appendChild(btn);
    });
    document.querySelectorAll('[data-use-case-cat]').forEach(function (link) {
      link.classList.toggle('is-active', link.dataset.useCaseCat === activeCat);
      if (link.dataset.useCaseCat === activeCat) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }

  function setCat(id) {
    activeCat = id;
    showAll = false;
    var params = new URLSearchParams(location.search);
    if (id === 'all') params.delete('category');
    else params.set('category', id);
    var query = params.toString();
    history.replaceState(history.state, '', location.pathname + (query ? '?' + query : '') + location.hash);
    renderTabs();
    renderGrid();
  }

  function getFiltered() {
    var q = (searchEl.value || '').trim().toLowerCase();
    return Tools.all.filter(function (t) {
      if (!matchesCategory(t, activeCat)) return false;
      if (q) {
        var hay = (t.name + ' ' + t.desc + ' ' + t.id).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    }).sort(function (a, b) {
      var ai = featuredOrder.indexOf(a.id), bi = featuredOrder.indexOf(b.id);
      return (ai < 0 ? 10000 : ai) - (bi < 0 ? 10000 : bi);
    });
  }

  function renderGrid() {
    var list = getFiltered();
    var query = (searchEl.value || '').trim();
    var hasFilter = activeCat !== 'all' || !!query;
    var visible = !hasFilter && !showAll ? list.slice(0, featuredOrder.length) : list;
    gridEl.innerHTML = '';
    if (!visible.length) {
      gridEl.innerHTML =
        '<div class="tools-empty"><p>没有匹配的工具</p>' +
        '<button id="clear-filter-btn" type="button">清空筛选</button></div>';
      document.getElementById('clear-filter-btn').onclick = clearSearch;
      countEl.textContent = '显示 0 / ' + Tools.total;
      return;
    }
    var frag = document.createDocumentFragment();
    visible.forEach(function (t) { frag.appendChild(cardEl(t)); });
    if (!hasFilter && !showAll) {
      var more = document.createElement('button');
      more.type = 'button';
      more.className = 'tool-card tool-more-card';
      more.innerHTML = '<span class="tool-more-icon" aria-hidden="true">▦</span><strong>更多工具 …</strong><span>探索更多实用工具，更多精彩工具持续上新中</span><b>浏览更多工具 →</b>';
      more.addEventListener('click', function () { showAll = true; renderGrid(); gridEl.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
      frag.appendChild(more);
    }
    gridEl.appendChild(frag);
    if (Sync) Sync.bind(gridEl); // 为动态卡片注入历史追踪 + 星标
    countEl.textContent = '显示 ' + visible.length + ' / ' + Tools.total;
    if (showAllButton) {
      showAllButton.hidden = hasFilter;
      showAllButton.setAttribute('aria-expanded', showAll && !hasFilter ? 'true' : 'false');
      showAllButton.textContent = showAll && !hasFilter ? '收起工具 ↑' : '查看全部工具 →';
    }
    var supporting = document.getElementById('tools-supporting-content');
    if (supporting) supporting.hidden = showAll && !hasFilter;
    var pageRoot = document.querySelector('.tools-page');
    if (pageRoot) pageRoot.classList.toggle('is-all-tools', showAll && !hasFilter);
  }

  function clearSearch() {
    searchEl.value = '';
    setCat('all');
  }
  searchEl.addEventListener('input', U.debounce(function () { showAll = false; renderGrid(); }, 120));
  var searchSubmit = document.getElementById('tool-search-submit');
  if (searchSubmit) searchSubmit.addEventListener('click', function () {
    searchEl.dispatchEvent(new Event('input', { bubbles: true }));
  });
  if (showAllButton) showAllButton.addEventListener('click', function () {
    showAll = !showAll;
    renderGrid();
  });

  function renderReferencePreviews() {
    if (categoryOverview) {
      var icons = categoryIcons;
      categoryOverview.innerHTML = '';
      Tools.cats.filter(function (category) { return category.count; }).forEach(function (category, index) {
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'tool-category-overview-card';
        button.innerHTML = '<i>' + icons[index % icons.length] + '</i><span><strong>' + category.label + '</strong><small>' + category.count + ' 个工具</small></span>';
        button.addEventListener('click', function () { setCat(category.id); gridEl.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
        categoryOverview.appendChild(button);
      });
      var submit = document.createElement('a');
      submit.className = 'tool-category-submit';
      submit.href = '/submit/';
      submit.innerHTML = '<i aria-hidden="true">➤</i><span><strong>提交工具</strong><small>推荐一个您喜欢的实用工具，让更多人受益</small><b>立即提交 →</b></span>';
      categoryOverview.appendChild(submit);
    }
    if (popularPreview) {
      popularPreview.innerHTML = '';
      ['base64', 'json', 'jwt', 'md5', 'aes'].map(function (id) { return Tools.get(id); }).filter(Boolean).forEach(function (tool, index) {
        var row = document.createElement('li');
        row.innerHTML = '<b>' + (index + 1) + '</b><i aria-hidden="true">' + ['♧','♨','♨','▧','⬟'][index] + '</i><span>' + tool.name + '</span>'; 
        popularPreview.appendChild(row);
      });
    }
  }

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
    if (favoritesPreview) {
      favoritesPreview.innerHTML = '';
      favs.slice(0, 5).forEach(function (favorite) {
        var row = document.createElement('div');
        row.className = 'tools-preview-row';
        row.textContent = favorite.name || favorite.id;
        favoritesPreview.appendChild(row);
      });
    }
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
    if (historyPreview) {
      historyPreview.innerHTML = '';
      items.slice(0, 5).forEach(function (item) {
        var row = document.createElement('div');
        row.className = 'tools-preview-row';
        var tool = Tools.get(item.id);
        row.textContent = tool ? tool.name : item.id;
        historyPreview.appendChild(row);
      });
    }
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
  renderReferencePreviews();
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
