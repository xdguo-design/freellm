(function () {
  'use strict';

  var navigationKeys = new Set(['home', 'models', 'health', 'skills', 'tools', 'workflow', 'logs', 'about']);
  var sharedNavigationCss = '/css/primary-menu.css?v=20261013-overflow';
  var updateIndicatorReady = false;
  var lastUpdateDate = '';
  var readUpdateKey = 'freellm-last-read-update';
  function getLastReadUpdate() {
    try { return window.localStorage.getItem(readUpdateKey) || ''; }
    catch (error) { return ''; }
  }
  function markUpdateRead() {
    if (!lastUpdateDate) return;
    try { window.localStorage.setItem(readUpdateKey, lastUpdateDate); }
    catch (error) { /* Storage can be disabled. */ }
    setUpdateIndicator(false);
  }
  document.addEventListener('click', function (event) {
    var link = event.target && event.target.closest && event.target.closest('.fl-site-nav [data-site-nav="logs"]');
    if (link) markUpdateRead();
  });

  // Cmd/Ctrl+K works on all pages, without hijacking a focused editor.
  document.addEventListener('keydown', function(event) {
    if (!(event.metaKey || event.ctrlKey) || event.altKey || event.shiftKey || event.key.toLowerCase() !== 'k') return;
    var target = event.target;
    if (target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))) return;
    event.preventDefault();
    var search = document.getElementById('catalog-search') || document.getElementById('site-search-input');
    if (search) {
      search.focus();
      search.select();
    } else {
      window.location.assign('/search/');
    }
  });

  var englishLocalePaths = {"/":"/en/","/models/":"/en/models/","/models/all/":"/en/models/all/","/providers/":"/en/providers/","/skills/":"/en/skills/","/tools/":"/en/tools/","/workflow/":"/en/workflow/","/logs/":"/en/logs/","/about/":"/en/about/"};
  function ensureEnglishEntryLink() {
    var actions = document.querySelector('.fl-site-ribbon-actions');
    if (!actions) return;
    var path = window.location.pathname;
    var english = Object.prototype.hasOwnProperty.call(englishLocalePaths, path)
      ? englishLocalePaths[path] : '/en/';
    var link = actions.querySelector('[data-english-route]');
    if (!link) {
      link = document.createElement('a');
      link.setAttribute('data-english-route', 'true');
      link.lang = 'en';
      link.hreflang = 'en';
      link.textContent = 'English';
      actions.appendChild(link);
    }
    link.href = english;
    link.title = english === '/en/' && path !== '/'
      ? 'No English translation yet; open the English homepage'
      : 'Open the English version of this page';
  }
  // Existing language buttons should open a distinct English document.
  document.addEventListener('click', function(event) {
    var button = event.target.closest('[data-locale-switch]');
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    var path = window.location.pathname;
    window.location.assign(button.dataset.localeSwitch === 'en'
      ? (englishLocalePaths[path] || '/en/') : path);
  }, true);

  function setUpdateIndicator(visible) {
    var link = document.querySelector('.fl-site-nav [data-site-nav="logs"]');
    if (!link) return;
    if (visible) link.setAttribute('data-has-update', 'true');
    else link.removeAttribute('data-has-update');
  }

  function refreshUpdateIndicator() {
    if (updateIndicatorReady) return;
    updateIndicatorReady = true;
    fetch('/daily-update-status.json', { credentials: 'same-origin', cache: 'no-store' })
      .then(function (response) { if (!response.ok) throw new Error('status unavailable'); return response.json(); })
      .then(function (status) {
        var parts = new Intl.DateTimeFormat('en-CA', {
          timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit'
        }).formatToParts(new Date());
        var today = Object.fromEntries(parts.filter(function (part) { return part.type !== 'literal'; }).map(function (part) { return [part.type, part.value]; }));
        var date = today.year + '-' + today.month + '-' + today.day;
        lastUpdateDate = status.latestDate || '';
        var onLogPage = /^\/(?:en\/)?logs\/?$/.test(window.location.pathname);
        if (onLogPage) markUpdateRead();
        setUpdateIndicator(lastUpdateDate === date && status.hasCatalogChanges === true &&
          !onLogPage && getLastReadUpdate() !== lastUpdateDate);
      })
      .catch(function () { setUpdateIndicator(false); });
  }

  function ensureSharedNavigationStyles() {
    var link = document.head.querySelector('link[data-fl-shared-navigation-styles]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = sharedNavigationCss;
      link.dataset.flSharedNavigationStyles = '1';
      document.head.appendChild(link);
    }
    link.href = sharedNavigationCss;
    document.head.appendChild(link);
    return link;
  }

  function ensureSharedNavigation() {
    // Do not combine a saved dark preference with the light-only Aurora palette.
    // Keep the preference in storage so a future complete theme can restore it.
    if (document.body && document.body.classList.contains('fl-ui-v2')) {
      document.documentElement.removeAttribute('data-theme');
    }
    ensureSharedNavigationStyles();
    ensureEnglishEntryLink();
    var rail = document.body && document.body.querySelector('.fl-site-rail');
    if (!rail) return;

    rail.id = 'fl-shared-site-menu';
    rail.setAttribute('aria-label', 'FreeLLM 主导航');
    var english = /^en(?:-|$)/i.test(document.documentElement.lang || '');
    var discoveriesLabel = rail.querySelector('.fl-site-nav [data-site-nav="logs"] span:last-child');
    if (discoveriesLabel) discoveriesLabel.textContent = english ? 'Discoveries' : '每日发现';
    function updateCurrentItem() {
      var active = currentPage();
      if (active === 'health') active = 'models';
      rail.querySelectorAll('.fl-site-nav [data-site-nav]').forEach(function (link) {
        if (link.dataset.siteNav === active && navigationKeys.has(link.dataset.siteNav)) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      });
    }
    if (rail.dataset.flSharedNavigation === 'true') {
      updateCurrentItem();
      refreshUpdateIndicator();
      return;
    }

    var labels = [
      ['home', '/', '⌂', english ? 'Home' : '首页'],
      ['models', '/models/', '▣', english ? 'Models' : '模型'],
      ['skills', '/skills/', '✦', english ? 'Skills' : '技能'],
      ['tools', '/tools/', '⌘', english ? 'Tools' : '工具'],
      ['workflow', '/workflow/', '⌁', english ? 'Workflows' : '工作流'],
      ['logs', '/logs/', '◷', english ? 'Discoveries' : '每日发现'],
      ['about', '/about/', 'ⓘ', english ? 'About' : '关于']
    ];
    var active = currentPage();
    if (active === 'health') active = 'models';
    var links = labels.map(function (item) {
      var current = item[0] === active ? ' aria-current="page"' : '';
      return '<a href="' + item[1] + '" data-site-nav="' + item[0] + '"' + current + '><span class="fl-site-nav-icon" aria-hidden="true">' + item[2] + '</span><span>' + item[3] + '</span></a>';
    }).join('');

    rail.innerHTML =
      '<a class="fl-site-brand" href="/" aria-label="FreeLLM 首页">' +
        '<span class="fl-site-brand-mark" aria-hidden="true"></span>' +
        '<span class="fl-site-brand-copy"><strong>FreeLLM</strong><small>AI for Everyone</small></span>' +
      '</a>' +
      '<button class="fl-mobile-menu-button" type="button" aria-controls="fl-primary-links" aria-expanded="false" aria-label="展开导航菜单"><span aria-hidden="true">☰</span></button>' +
      '<nav id="fl-primary-links" class="fl-site-nav" aria-label="主导航">' + links + '</nav>' +
      '<div class="fl-site-rail-note" aria-hidden="true"></div>';

    // P1-7: an accessible drawer for narrow phones, not seven compressed icons.
    var mobileButton = rail.querySelector('.fl-mobile-menu-button');
    var mobileLinks = rail.querySelector('#fl-primary-links');
    function closeMobileMenu(restoreFocus) {
      rail.classList.remove('fl-mobile-menu-open');
      mobileButton.setAttribute('aria-expanded', 'false');
      mobileButton.setAttribute('aria-label', '展开导航菜单');
      if (restoreFocus) mobileButton.focus();
    }
    mobileButton.addEventListener('click', function () {
      var open = !rail.classList.contains('fl-mobile-menu-open');
      rail.classList.toggle('fl-mobile-menu-open', open);
      mobileButton.setAttribute('aria-expanded', String(open));
      mobileButton.setAttribute('aria-label', open ? '收起导航菜单' : '展开导航菜单');
      if (open) mobileLinks.querySelector('a')?.focus();
    });
    mobileLinks.addEventListener('click', function (event) {
      if (event.target.closest('a')) closeMobileMenu(false);
    });
    rail.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && rail.classList.contains('fl-mobile-menu-open')) {
        event.preventDefault();
        closeMobileMenu(true);
      }
    });

    // P1-5: the current page styles are light-only. Do not mount a nonworking
    // dark-mode toggle until every page surface has passed contrast review.
    rail.dataset.flSharedNavigation = 'true';
    updateCurrentItem();
    refreshUpdateIndicator();
  }

  function currentPage() {
    return document.body && document.body.dataset.flSection || '';
  }

  // The directory already has a full card renderer, localized field labels,
  // and working filters. Select it on first paint at phone widths.
  function activateMobileModelCards() {
    if (!window.matchMedia || !window.matchMedia('(max-width: 600px)').matches) return;
    var section = document.getElementById('model-directory');
    var button = section && section.querySelector('.mdir-view-btn[data-catalog-view="cards"]');
    if (button && section.dataset.catalogView !== 'cards') button.click();
  }

  document.addEventListener('DOMContentLoaded', function () {
    ensureSharedNavigation();
    refreshUpdateIndicator();
    activateMobileModelCards();
  });

})();

/* Load workflow recipe simulation on workflow pages */
(function () {
  try {
    var p = location.pathname || '';
    if (p.indexOf('/workflow') === -1 && p.indexOf('/skills/lab') === -1) return;
    if (document.querySelector('script[data-workflow-sim]')) return;
    var s = document.createElement('script');
    s.src = '/js/workflow-recipe-sim.js?v=20261012-sim';
    s.defer = true;
    s.setAttribute('data-workflow-sim', '1');
    document.head.appendChild(s);
  } catch (e) {}
})();
