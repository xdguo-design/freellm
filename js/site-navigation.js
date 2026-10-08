(function () {
  'use strict';

  if (window.FreeLLMNavigation) return;

  var navigationKeys = new Set(['home', 'models', 'health', 'skills', 'tools', 'workflow', 'logs', 'about']);
  var navigationPaths = new Map([
    ['/', 'home'],
    ['/models/', 'models'],
    ['/health/', 'health'],
    ['/skills/', 'skills'],
    ['/tools/', 'tools'],
    ['/workflow/', 'workflow'],
    ['/logs/', 'logs'],
    ['/about/', 'about']
  ]);
  var navigationInProgress = false;
  var requestController = null;
  var sharedNavigationCss = '/css/primary-menu.css?v=20261004-model-directory-responsive';
  var updateIndicatorReady = false;
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
        setUpdateIndicator(status.latestDate === date && status.hasCatalogChanges === true);
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

    var english = /^en(?:-|$)/i.test(document.documentElement.lang || '');
    var labels = [
      ['home', '/', '⌂', english ? 'Home' : '首页'],
      ['models', '/models/', '▣', english ? 'Models' : '模型'],
      ['skills', '/skills/', '✦', english ? 'Skills' : '技能'],
      ['tools', '/tools/', '⌘', english ? 'Tools' : '工具'],
      ['workflow', '/workflow/', '⌁', english ? 'Workflows' : '工作流'],
      ['logs', '/logs/', '◷', english ? 'Discoveries' : '今日发现'],
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

  function documentUrl(url) {
    // Vercel rewrites the public home route to this static prototype. A plain
    // local HTTP server does not apply vercel.json rewrites, so fetch the same
    // document explicitly while keeping the public URL at "/".
    return url.pathname === '/'
      ? new URL('/design/free-china-ai-index.html', url.origin)
      : url;
  }

  function event(name, detail) {
    window.dispatchEvent(new CustomEvent(name, { detail: detail }));
  }

  function isExcludedScript(script, source) {
    var type = (script.type || '').toLowerCase();
    if (type === 'application/ld+json' || type === 'application/json') return true;
    if (source) {
      return /(?:^|\/)(?:freellm-sync|site-navigation|reference-shell)(?:\.|\/|$)/i.test(source) ||
        /googletagmanager|googleadservices|adsbygoogle|\/_vercel\/insights/i.test(source);
    }
    return /googletagmanager|googleadservices|adsbygoogle|\bgtag\s*\(|\bdataLayer\b|vercelInsights|window\.va\s*=|document\.write|freellm-sync\.js|reference-shell\.js|site-navigation\.js/i.test(script.textContent || '');
  }

  function collectScripts(parsed, responseUrl) {
    return Array.from(parsed.querySelectorAll('head script, body script')).filter(function (script) {
      var source = script.getAttribute('src');
      return !isExcludedScript(script, source ? new URL(source, responseUrl).href : '');
    });
  }

  function replaceMetadata(parsed) {
    document.title = parsed.title || '';
    var names = ['description', 'keywords', 'robots', 'og:title', 'og:description', 'og:url', 'og:image', 'og:locale', 'twitter:card', 'twitter:title', 'twitter:description', 'twitter:url', 'twitter:image'];
    names.forEach(function (name) {
      var selector = name.indexOf('og:') === 0 || name.indexOf('twitter:') === 0 ? 'meta[property="' + name + '"]' : 'meta[name="' + name + '"]';
      var current = document.head.querySelector(selector);
      var next = parsed.head.querySelector(selector);
      if (current) current.remove();
      if (next) document.head.appendChild(next.cloneNode(true));
    });
    var canonical = document.head.querySelector('link[rel="canonical"]');
    if (canonical) canonical.remove();
    var nextCanonical = parsed.head.querySelector('link[rel="canonical"]');
    if (nextCanonical) document.head.appendChild(nextCanonical.cloneNode(true));
    document.head.querySelectorAll('link[rel="alternate"][hreflang]').forEach(function(node) { node.remove(); });
    parsed.head.querySelectorAll('link[rel="alternate"][hreflang]').forEach(function(node) {
      document.head.appendChild(node.cloneNode(true));
    });
    // Keep inert page data available to scripts that initialize after mount.
    document.head.querySelectorAll('script[type="application/json"][id]').forEach(function (node) { node.remove(); });
    parsed.head.querySelectorAll('script[type="application/json"][id]').forEach(function (node) {
      document.head.appendChild(node.cloneNode(true));
    });
    document.documentElement.lang = parsed.documentElement.lang || 'zh-CN';
  }

  async function replaceStyles(parsed, responseUrl) {
    var previousStyles = Array.from(document.head.querySelectorAll('link[rel="stylesheet"], style')).filter(function (node) {
      return !node.hasAttribute('data-fl-shared-navigation-styles');
    });
    var nextStyles = [];
    var styleLoads = [];
    Array.from(parsed.head.querySelectorAll('link[rel="stylesheet"], style')).forEach(function (node) {
      var copy = node.cloneNode(true);
      copy.setAttribute('data-fl-navigation-style', '');
      if (copy.tagName === 'LINK') {
        copy.href = new URL(node.getAttribute('href'), responseUrl).href;
        copy.dataset.flNavigationMedia = copy.getAttribute('media') || '';
        copy.setAttribute('media', 'not all');
      } else {
        copy.disabled = true;
      }
      if (copy.tagName === 'LINK' && new URL(copy.href, window.location.href).origin === window.location.origin && !copy.sheet) {
        styleLoads.push(new Promise(function (resolve) {
          copy.addEventListener('load', resolve, { once: true });
          copy.addEventListener('error', resolve, { once: true });
        }));
      }
      document.head.appendChild(copy);
      nextStyles.push(copy);
    });

    // Keep the current page styled until every incoming stylesheet is ready.
    // Removing the old sheets first briefly leaves the persistent sidebar
    // unstyled, which looks like the menu itself is reloading on every click.
    await Promise.all(styleLoads);

    return function commitStyles() {
      nextStyles.forEach(function (node) {
        if (node.tagName === 'LINK') {
          var media = node.dataset.flNavigationMedia;
          if (media) node.setAttribute('media', media);
          else node.removeAttribute('media');
          delete node.dataset.flNavigationMedia;
        } else {
          node.disabled = false;
        }
      });
      previousStyles.forEach(function (node) { node.remove(); });
      ensureSharedNavigationStyles();
    };
  }

  function replacePageChrome(parsed) {
    var body = document.body;
    var targetBody = parsed.body;
    var rail = body.querySelector(':scope > .fl-site-rail');
    var ribbon = body.querySelector(':scope > .fl-site-ribbon');
    var skipLink = body.querySelector(':scope > .fl-skip-link');
    if (!rail || !ribbon) return false;

    event('freellm:page-unmount', { from: currentPage(), to: targetBody.dataset.flSection || '' });
    body.className = targetBody.className;
    Array.from(body.attributes).forEach(function (attribute) {
      if (attribute.name.indexOf('data-') === 0) body.removeAttribute(attribute.name);
    });
    Array.from(targetBody.attributes).forEach(function (attribute) {
      if (attribute.name.indexOf('data-') === 0) body.setAttribute(attribute.name, attribute.value);
    });

    var pageNodes = Array.from(targetBody.childNodes).filter(function (node) {
      if (node.nodeType !== Node.ELEMENT_NODE) return true;
      if (node.matches('.fl-site-rail, .fl-site-ribbon')) return false;
      // JSON scripts are page data, not executable code. Skills needs its
      // #skill-data node before the shared page-mount handler renders cards.
      return !node.matches('script') || /^(?:application\/json|application\/ld\+json)$/i.test((node.type || '').trim());
    }).map(function (node) { return document.importNode(node, true); });
    body.replaceChildren.apply(body, (skipLink ? [skipLink] : []).concat([rail, ribbon]));
    pageNodes.forEach(function (node) { body.appendChild(node); });
    ensureSharedNavigation();
    var main = body.querySelector('main, .catalog-content, .page');
    if (main && !main.id) main.id = 'fl-main-content';
    if (skipLink && main) skipLink.href = '#' + main.id;
    return true;
  }

  function runScript(source, responseUrl) {
    return new Promise(function (resolve) {
      var script = document.createElement('script');
      Array.from(source.attributes).forEach(function (attribute) {
        if (attribute.name !== 'src' && attribute.name !== 'async' && attribute.name !== 'defer') {
          script.setAttribute(attribute.name, attribute.value);
        }
      });
      if (source.hasAttribute('src')) {
        script.async = false;
        script.src = new URL(source.getAttribute('src'), responseUrl).href;
        script.addEventListener('load', resolve, { once: true });
        script.addEventListener('error', resolve, { once: true });
      } else {
        var code = source.textContent || '';
        script.textContent = script.type === 'module' ? code : '(function(){\n' + runReadyCallbacksImmediately(code) + '\n}).call(window);';
      }
      document.body.appendChild(script);
      if (!source.hasAttribute('src')) resolve();
    });
  }

  function activateMenu(parsed) {
    var active = parsed.body.dataset.flSection || '';
    if (active === 'health') active = 'models';
    document.querySelectorAll('.fl-site-nav [data-site-nav]').forEach(function (link) {
      if (link.dataset.siteNav === active && navigationKeys.has(link.dataset.siteNav)) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
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
    activateMenu(document);
    refreshUpdateIndicator();
    activateMobileModelCards();
  });

  function findArgumentEnd(source, start) {
    var stack = [];
    var quote = '';
    var escaped = false;
    var lineComment = false;
    var blockComment = false;
    for (var index = start; index < source.length; index += 1) {
      var character = source[index];
      var next = source[index + 1];
      if (lineComment) { if (character === '\n') lineComment = false; continue; }
      if (blockComment) { if (character === '*' && next === '/') { blockComment = false; index += 1; } continue; }
      if (quote) {
        if (escaped) escaped = false;
        else if (character === '\\') escaped = true;
        else if (character === quote) quote = '';
        continue;
      }
      if (character === '/' && next === '/') { lineComment = true; index += 1; continue; }
      if (character === '/' && next === '*') { blockComment = true; index += 1; continue; }
      if (character === '\'' || character === '"' || character === '`') { quote = character; continue; }
      if (character === '(' || character === '[' || character === '{') { stack.push(character); continue; }
      if ((character === ')' || character === ',') && stack.length === 0) return index;
      if (character === ')' || character === ']' || character === '}') stack.pop();
    }
    return source.length;
  }

  function findCallEnd(source, openIndex) {
    var stack = ['('];
    var quote = '';
    var escaped = false;
    var lineComment = false;
    var blockComment = false;
    for (var index = openIndex + 1; index < source.length; index += 1) {
      var character = source[index];
      var next = source[index + 1];
      if (lineComment) { if (character === '\n') lineComment = false; continue; }
      if (blockComment) { if (character === '*' && next === '/') { blockComment = false; index += 1; } continue; }
      if (quote) {
        if (escaped) escaped = false;
        else if (character === '\\') escaped = true;
        else if (character === quote) quote = '';
        continue;
      }
      if (character === '/' && next === '/') { lineComment = true; index += 1; continue; }
      if (character === '/' && next === '*') { blockComment = true; index += 1; continue; }
      if (character === '\'' || character === '"' || character === '`') { quote = character; continue; }
      if (character === '(' || character === '[' || character === '{') { stack.push(character); continue; }
      if (character === ')' || character === ']' || character === '}') {
        stack.pop();
        if (!stack.length) return index;
      }
    }
    return -1;
  }

  function runReadyCallbacksImmediately(source) {
    var pattern = /document\.addEventListener\s*\(\s*(['"])DOMContentLoaded\1\s*,/g;
    var match;
    var output = '';
    var cursor = 0;
    while ((match = pattern.exec(source))) {
      var openIndex = source.indexOf('(', match.index);
      var callbackStart = match.index + match[0].length;
      while (/\s/.test(source[callbackStart] || '')) callbackStart += 1;
      var callbackEnd = findArgumentEnd(source, callbackStart);
      var callEnd = findCallEnd(source, openIndex);
      if (callEnd < 0 || callbackEnd > callEnd) continue;
      var callback = source.slice(callbackStart, callbackEnd).trim();
      output += source.slice(cursor, match.index) + '(' + callback + ').call(document, new Event("DOMContentLoaded"))';
      cursor = callEnd + 1;
      pattern.lastIndex = cursor;
    }
    return cursor ? output + source.slice(cursor) : source;
  }

  async function navigate(input, options) {
    var url = new URL(input, window.location.href);
    var pageUrl = documentUrl(url);
    var settings = options || {};
    var fromPage = currentPage();
    if (url.origin !== window.location.origin || !navigationPaths.has(url.pathname)) return false;
    if (url.href === window.location.href && !settings.force) return true;
    if (requestController) requestController.abort();
    requestController = new AbortController();
    navigationInProgress = true;

    try {
      var response = await fetch(pageUrl.href, {
        credentials: 'same-origin',
        headers: { Accept: 'text/html' },
        signal: requestController.signal
      });
      if (!response.ok) throw new Error('Navigation returned HTTP ' + response.status);
      var responseUrl = response.url || pageUrl.href;
      var parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
      if (!parsed.body || !parsed.body.querySelector('.fl-site-rail') || !parsed.body.querySelector('.fl-site-ribbon')) {
        throw new Error('Navigation document is missing the shared site shell');
      }
      var scripts = collectScripts(parsed, responseUrl);

      if (settings.history !== false) {
        var previousState = Object.assign({}, history.state || {}, { freellmScrollY: window.scrollY });
        history.replaceState(previousState, '', window.location.href);
        history.pushState({ freellmNavigation: true, freellmScrollY: 0 }, '', url.href);
      } else if (settings.replaceHistory) {
        history.replaceState({ freellmNavigation: true }, '', url.href);
      }

      // Reflect the selected route as soon as its document is available; the
      // shared rail stays mounted while page styles finish loading.
      activateMenu(parsed);
      replaceMetadata(parsed);
      var commitStyles = await replaceStyles(parsed, responseUrl);
      if (!replacePageChrome(parsed)) throw new Error('Current page is missing the shared site shell');
      commitStyles();
      for (var index = 0; index < scripts.length; index += 1) await runScript(scripts[index], responseUrl);
      activateMobileModelCards();
      event('freellm:page-mount', {
        from: fromPage,
        to: parsed.body.dataset.flSection || '',
        isHistoryNavigation: settings.history === false
      });
      if (settings.restoreScroll) window.scrollTo(0, Number(settings.restoreScroll) || 0);
      else if (url.hash) document.getElementById(decodeURIComponent(url.hash.slice(1)))?.scrollIntoView();
      else window.scrollTo(0, 0);
      return true;
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.warn('[FreeLLM navigation] Falling back to a full page load:', error.message);
        window.location.assign(url.href);
      }
      return false;
    } finally {
      navigationInProgress = false;
    }
  }

  window.addEventListener('click', function (clickEvent) {
    if (clickEvent.defaultPrevented || clickEvent.button !== 0 || clickEvent.metaKey || clickEvent.ctrlKey || clickEvent.shiftKey || clickEvent.altKey) return;
    var link = clickEvent.target.closest('a[data-site-nav]');
    if (!link || !navigationKeys.has(link.dataset.siteNav) || link.target || link.hasAttribute('download')) return;
    var url = new URL(link.href, window.location.href);
    if (!navigationPaths.has(url.pathname) || url.origin !== window.location.origin) return;
    clickEvent.preventDefault();
    navigate(url.href, { history: true });
  }, true);

  window.addEventListener('popstate', function (popEvent) {
    var url = new URL(window.location.href);
    if (!navigationPaths.has(url.pathname)) {
      window.location.assign(url.href);
      return;
    }
    navigate(url.href, { history: false, force: true, restoreScroll: popEvent.state && popEvent.state.freellmScrollY });
  });

  window.FreeLLMNavigation = {
    navigate: navigate,
    isNavigating: function () { return navigationInProgress; }
  };
})();
