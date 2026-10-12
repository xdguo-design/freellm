
(() => {
  const boot = () => {
    const body = document.body;
    if (!body || body.dataset.referenceShellReady === '1') return;
    body.dataset.referenceShellReady = '1';
    body.classList.add('reference-ui');

    const section = body.dataset.flSection || 'home';
    const copy = {
      home: ['搜索模型、工具、Skills 或你感兴趣的 AI 资源…', '提交资源', '/submit/'],
      models: ['搜索模型、厂商、API 或能力…', '查看资源', '/'],
      skills: ['搜索模型、工具、Skills 或任何你感兴趣的 AI 资源…', 'Skill Lab', '/skills/lab/'],
      tools: ['搜索工具、功能、场景…', '提交资源', '/submit/'],
      workflow: ['搜索模型、工具、Skills 或任何你感兴趣的 AI 资源...', '浏览 Skills', '/skills/'],
      logs: ['搜索今天的新增、恢复或下线记录…', '查看资源', '/'],
      about: ['搜索模型、工具、Skills 或任何你感兴趣的 AI 资源…', '提交资源', '/submit/']
    }[section] || ['搜索 FreeLLM…', '查看资源', '/'];

    const topbar = document.createElement('div');
    topbar.className = 'ref-topbar';
    topbar.setAttribute('role', 'search');
    const localeLabel = document.documentElement.lang === 'en' ? '中文' : 'EN';
if (section === 'home' || section === 'models') {
      topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.4"></circle><path d="m16 16 4.2 4.2"></path></svg></span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions"><button class="ref-locale" type="button" data-reference-locale-toggle aria-label="切换语言">' + localeLabel + '</button><button class="ref-bell" type="button" aria-label="更新提醒"><svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg></button><a class="ref-favorites-link" href="/favorites/">我的收藏（可 GitHub 同步）</a></div>';
    } else {
      const actions = ['skills', 'tools', 'workflow', 'logs', 'about'].includes(section)
        ? '<button class="ref-bell" type="button" aria-label="更新提醒" data-reference-notifications>♧</button><a class="ref-favorites-link" href="/favorites/">我的收藏（可 GitHub 同步）</a>'
        : '<button class="ref-locale" type="button" data-reference-locale-toggle aria-label="切换语言">' + localeLabel + '</button><button class="ref-bell" type="button" aria-label="更新提醒">♧</button><a href="/about/">帮助</a><a class="primary" href="' + copy[2] + '">' + copy[1] + '</a>';
      topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.4"></circle><path d="m16 16 4.2 4.2"></path></svg></span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions">' + actions + '</div>';
      topbar.querySelectorAll('.ref-bell').forEach(button => { button.innerHTML = '<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg>'; });
    }
    const rail = body.querySelector(':scope > .fl-site-rail');
    if (rail) rail.insertAdjacentElement('afterend', topbar);
    else body.prepend(topbar);

    const localeButton = topbar.querySelector('.ref-locale');
    localeButton?.addEventListener('click', () => {
      const legacyToggle = document.querySelector('[data-locale-toggle], [data-locale-switch]');
      if (legacyToggle) legacyToggle.click();
    });

    if (section === 'skills') {
      topbar.querySelector('[data-reference-notifications]')?.addEventListener('click', () => { location.href = '/logs/'; });
      bootSkillsShowcase();
    }

    const topInput = topbar.querySelector('input');
    const targets = ['#catalog-search','#tool-search','#skill-search','#skill-library-search'].map(s => document.querySelector(s)).filter(Boolean);
    const target = targets[0];
    const mirrorSearch = () => {
      if (!target) return;
      target.value = topInput.value.trim();
      target.dispatchEvent(new Event('input', { bubbles: true }));
      target.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const sync = () => {
      const value = topInput.value.trim();
      location.href = '/search/?q=' + encodeURIComponent(value);
    };
    topInput.addEventListener('input', mirrorSearch);
    topInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') { event.preventDefault(); sync(); }
    });
    if (!window.__freellmReferenceShortcutBound) {
      window.__freellmReferenceShortcutBound = true;
      document.addEventListener('keydown', event => {
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
          const activeSearch = document.querySelector('.ref-topbar input');
          if (activeSearch) { event.preventDefault(); activeSearch.focus(); }
        }
      });
    }

    if (section === 'home') {
      const hero = document.querySelector('.catalog-hero');
      if (hero && !document.querySelector('.ref-feature-row')) {
        const row = document.createElement('section');
        row.className = 'ref-feature-row';
        row.setAttribute('aria-label', 'FreeLLM 核心入口');
        row.innerHTML = '<article class="ref-feature"><span class="ref-feature-icon">◉</span><h3>Agent Skills</h3><p>发现和学习实用的 AI 智能体技能，从提示词到完整 Agent 实现。</p><div class="ref-feature-tags"><span>提示词技巧</span><span>智能体模板</span><span>开源项目</span></div><a href="/skills/" aria-label="打开 Agent Skills">→</a></article><article class="ref-feature workflow"><span class="ref-feature-icon">⌘</span><h3>Workflow Recipes</h3><p>把模型、工具与技能串成经过验证的 AI 工作流，一键复用。</p><div class="ref-feature-tags"><span>自动化流程</span><span>多工具协作</span><span>实战案例</span></div><a href="/skills/lab/" aria-label="打开 Workflow Recipes">→</a></article>';
        hero.insertAdjacentElement('afterend', row);
      }
    }

    const makeStats = (items) => {
      const row = document.createElement('section');
      row.className = 'ref-stat-row';
      row.innerHTML = items.map((x, i) => '<article class="ref-stat"><span class="ref-stat-icon">' + x[0] + '</span><div class="ref-stat-copy"><strong>' + x[1] + '</strong>' + (x[3] ? '<span class="ref-stat-change">' + x[3] + '</span>' : '') + '<span class="ref-stat-label">' + x[2] + '</span>' + (x[4] ? '<small>' + x[4] + '</small>' : '') + '</div></article>').join('');
      return row;
    };

    if (section === 'workflow') {
      const hero = document.querySelector('.lab-hero');
      if (hero && !document.querySelector('.ref-stat-row')) {
        hero.insertAdjacentElement('afterend', makeStats([
          ['◆','324','已发布模板','↗ +12%','来自社区的优质工作流'],['●','TOP 10','热门工作流','','最受欢迎的生产力方案'],['▣','18','今日更新','↗ +80%','新鲜灵感持续涌现'],['▱','92%','可直接复用','','一键复制，快速开始']
        ]));
      }
      const library = document.getElementById('component-library');
      const footerNav = document.querySelector('.lab-footer .static-locale-nav');
      if (library && footerNav && !footerNav.querySelector('[data-open-component-library]')) {
        library.removeAttribute('open');
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.dataset.openComponentLibrary = '';
        trigger.textContent = '组件库';
        trigger.addEventListener('click', () => {
          library.open = true;
          library.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        footerNav.append(' · ', trigger);
      }
    }
    // Render the generated daily-log archive as-is; do not replace it with demo update cards.

    if (['tools', 'workflow', 'logs', 'about'].includes(section) && !document.querySelector('.prototype-footer')) {
      const legacyFooter = section === 'about'
        ? body.querySelector(':scope > footer')
        : document.querySelector('.tools-footer,.lab-footer,.log-footer');
      if (legacyFooter) {
        const footer = document.createElement('footer');
        footer.className = 'prototype-footer';
        footer.innerHTML = '<div class="prototype-footer-main"><div class="prototype-footer-brand"><img src="/assets/reference/rail-brand.png" alt=""><div><strong>FreeLLM</strong><small>AI for Everyone</small><p>让优质的 AI 资源，触手可及。</p></div></div><nav><strong>产品</strong><a href="/models/">模型库</a><a href="/tools/">工具箱</a><a href="/skills/">Skills</a><a href="/skills/lab/">工作流</a></nav><nav><strong>资源</strong><a href="/logs/">最新更新</a><a href="/models/">热门资源</a><a href="/about/">使用说明</a><a href="/submit/">提交资源</a></nav><nav><strong>社区</strong><a href="/about/">关于我们</a><a href="/submit/">提交资源</a><a href="mailto:xdguo0527@gmail.com">反馈建议</a></nav><div class="prototype-footer-slogan">Better AI<br>A Brighter Tomorrow</div></div><div class="prototype-footer-bottom"><span>© 2026 FreeLLM. All rights reserved.</span><span class="prototype-footer-social"><a href="https://github.com/xdguo-design/freellm" aria-label="GitHub">●</a><span aria-label="Twitter"><svg viewBox="0 0 24 24"><path d="M23.95 4.57a10 10 0 0 1-2.89.79 5.04 5.04 0 0 0 2.21-2.78 10.05 10.05 0 0 1-3.19 1.22 5.02 5.02 0 0 0-8.55 4.58A14.25 14.25 0 0 1 1.2 3.13a5.02 5.02 0 0 0 1.55 6.7 4.97 4.97 0 0 1-2.27-.63v.06a5.03 5.03 0 0 0 4.03 4.93 5.05 5.05 0 0 1-2.26.09 5.03 5.03 0 0 0 4.69 3.49A10.08 10.08 0 0 1 0 19.86a14.22 14.22 0 0 0 7.7 2.26c9.24 0 14.3-7.65 14.3-14.29v-.65a10.2 10.2 0 0 0 2.5-2.6Z"/></svg></span><span aria-label="Discord"><svg viewBox="0 0 24 24"><path d="M19.7 5.1A18.1 18.1 0 0 0 15.3 3l-.6 1.2a16.7 16.7 0 0 0-5.4 0L8.7 3a18.1 18.1 0 0 0-4.4 2.1C1.5 9.2.7 13.2 1.1 17.2a18.2 18.2 0 0 0 5.4 2.7l1.2-2a11.8 11.8 0 0 1-1.9-.9l.5-.4a13 13 0 0 0 11.4 0l.5.4a11.8 11.8 0 0 1-1.9.9l1.2 2a18.2 18.2 0 0 0 5.4-2.7c.5-4.6-.8-8.6-3.2-12.1ZM8.8 14.3c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Zm6.4 0c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Z"/></svg></span></span><button type="button" data-locale-switch="zh-CN">◎　简体中文　⌄</button></div>';
        if (section === 'about') {
          footer.innerHTML = '<div class="prototype-footer-main"><div class="prototype-footer-brand"><img src="/assets/reference/rail-brand.png" alt=""><div><strong>FreeLLM</strong><small>AI for Everyone</small><p>让优质的 AI 资源，触手可及。</p></div></div><nav><strong>产品</strong><a href="/models/">模型库</a><a href="/skills/">Skills</a><a href="/tools/">工具</a><a href="/skills/lab/">工作流</a></nav><nav><strong>资源</strong><a href="/logs/">最新更新</a><a href="/models/">热门资源</a><a href="/guide/">使用教程</a><a href="https://github.com/xdguo-design/freellm">开发文档</a><a href="/category/student/">学生优惠</a></nav><nav><strong>社区</strong><a href="/about/">关于我们</a><a href="/submit/">提交资源</a><a href="/community/">加入社区</a><a href="mailto:xdguo0527@gmail.com">反馈建议</a></nav><div class="prototype-footer-slogan">Better AI<br>A Brighter Tomorrow</div></div><div class="prototype-footer-bottom"><span>© 2026 FreeLLM. All rights reserved.</span><nav class="prototype-footer-legal"><a href="/privacy/">隐私政策</a><a href="/terms/">服务条款</a><a href="/terms/#disclaimer">免责声明</a></nav><span class="prototype-footer-social"><a href="https://github.com/xdguo-design/freellm" aria-label="GitHub"><svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.61-3.37-1.18-3.37-1.18-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.54 2.36 1.1 2.94.84.09-.65.35-1.1.64-1.36-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0 1 12 6.91c.85 0 1.71.11 2.52.34 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.7-4.57 4.95.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg></a><span aria-label="Twitter"><svg viewBox="0 0 24 24"><path d="M23.95 4.57a10 10 0 0 1-2.89.79 5.04 5.04 0 0 0 2.21-2.78 10.05 10.05 0 0 1-3.19 1.22 5.02 5.02 0 0 0-8.55 4.58A14.25 14.25 0 0 1 1.2 3.13a5.02 5.02 0 0 0 1.55 6.7 4.97 4.97 0 0 1-2.27-.63v.06a5.03 5.03 0 0 0 4.03 4.93 5.05 5.05 0 0 1-2.26.09 5.03 5.03 0 0 0 4.69 3.49A10.08 10.08 0 0 1 0 19.86a14.22 14.22 0 0 0 7.7 2.26c9.24 0 14.3-7.65 14.3-14.29v-.65a10.2 10.2 0 0 0 2.5-2.6Z"/></svg></span><span aria-label="Discord"><svg viewBox="0 0 24 24"><path d="M19.7 5.1A18.1 18.1 0 0 0 15.3 3l-.6 1.2a16.7 16.7 0 0 0-5.4 0L8.7 3a18.1 18.1 0 0 0-4.4 2.1C1.5 9.2.7 13.2 1.1 17.2a18.2 18.2 0 0 0 5.4 2.7l1.2-2a11.8 11.8 0 0 1-1.9-.9l.5-.4a13 13 0 0 0 11.4 0l.5.4a11.8 11.8 0 0 1-1.9.9l1.2 2a18.2 18.2 0 0 0 5.4-2.7c.5-4.6-.8-8.6-3.2-12.1ZM8.8 14.3c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Zm6.4 0c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Z"/></svg></span></span><button type="button" data-locale-switch="zh-CN">◎　简体中文　⌄</button></div>';
        }
        legacyFooter.classList.add('prototype-legacy-footer');
        legacyFooter.insertAdjacentElement('afterend', footer);
        const locale = footer.querySelector('[data-locale-switch]');
        locale?.addEventListener('click', () => {
          const next = document.documentElement.lang === 'en' ? 'zh-CN' : 'en';
          try { localStorage.setItem('free-ai-index-locale', next); } catch (error) { /* storage can be unavailable */ }
          const url = new URL(location.href);
          url.searchParams.set('lang', next);
          location.href = url.toString();
        });
      }
    }

    if (section === 'logs' || (section === 'about' && body.dataset.aboutStatic !== 'true')) {
      const page = section === 'logs'
        ? body.querySelector(':scope > .daily-log-dashboard')
        : body.querySelector(':scope > main');
      if (page) {
        page.style.setProperty('box-sizing', 'border-box', 'important');
        page.style.setProperty('position', 'relative', 'important');
        page.style.setProperty('left', 'var(--prototype-rail)', 'important');
        page.style.setProperty('width', 'calc(100% - var(--prototype-rail))', 'important');
        page.style.setProperty('max-width', 'none', 'important');
        page.style.setProperty('margin-left', '0', 'important');
        page.style.setProperty('margin-right', '0', 'important');
      }
      const footer = body.querySelector('.prototype-footer');
      if (footer) {
        footer.style.setProperty('box-sizing', 'border-box', 'important');
        footer.style.setProperty('position', 'relative', 'important');
        footer.style.setProperty('left', section === 'about' ? 'var(--prototype-rail)' : '-22px', 'important');
        footer.style.setProperty('width', section === 'about' ? 'calc(100% - var(--prototype-rail))' : 'calc(100% + 36px)', 'important');
        footer.style.setProperty('max-width', 'none', 'important');
        footer.style.setProperty('margin', section === 'logs' ? '5px 0 0' : '0', 'important');
      }
      if (section === 'logs') {
        const archive = body.querySelector('#log-archive');
        const archiveLink = body.querySelector('.ref-update-history-head a[href="#log-archive"]');
        const history = body.querySelector('.ref-update-history');
        archiveLink?.addEventListener('click', event => {
          event.preventDefault();
          if (archive) {
            archive.open = true;
            archive.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        });
        if (history && history.dataset.historyReady !== '1') {
          history.dataset.historyReady = '1';
          const filters = [...history.querySelectorAll('[data-history-filter]')];
          const table = history.querySelector('.ref-update-history-table');
          const rows = [...history.querySelectorAll('[data-history-row]')];
          const placeholder = history.querySelector('[data-history-placeholder]');
          const empty = history.querySelector('[data-history-empty]');
          const visibleCount = history.querySelector('[data-history-visible-count]');
          const resultCount = history.querySelector('[data-history-result-count]');
          const sortButton = history.querySelector('[data-history-sort]');
          const total = rows.length;
          let activeFilter = 'all';

          const sortRows = direction => {
            const ordered = rows.slice().sort((a, b) => {
              const left = Date.parse(a.querySelector('time')?.dateTime || '') || 0;
              const right = Date.parse(b.querySelector('time')?.dateTime || '') || 0;
              return direction === 'asc' ? left - right : right - left;
            });
            ordered.forEach(row => table?.appendChild(row));
          };

          const applyFilter = () => {
            const matching = rows.filter(row => {
              const category = row.dataset.category || 'other';
              const change = row.dataset.change || '';
              const matches = activeFilter === 'all' || category === activeFilter || change === activeFilter;
              row.style.setProperty('display', matches ? '' : 'none', 'important');
              return matches;
            });
            if (placeholder) placeholder.style.setProperty('display', total === 0 && activeFilter === 'all' ? '' : 'none', 'important');
            if (visibleCount) visibleCount.textContent = String(matching.length);
            if (resultCount) resultCount.textContent = `显示${activeFilter === 'all' ? '全部' : '筛选后'} ${matching.length} / ${total} 条记录`;
            if (empty) empty.hidden = matching.length > 0 || total === 0;
          };

          filters.forEach(button => button.addEventListener('click', () => {
            activeFilter = button.dataset.historyFilter || 'all';
            filters.forEach(item => {
              const selected = item === button;
              item.classList.toggle('is-active', selected);
              item.setAttribute('aria-pressed', String(selected));
            });
            applyFilter();
          }));

          sortButton?.addEventListener('click', () => {
            const direction = sortButton.dataset.historySort === 'desc' ? 'asc' : 'desc';
            sortButton.dataset.historySort = direction;
            sortButton.setAttribute('aria-pressed', String(direction === 'asc'));
            sortButton.textContent = direction === 'asc' ? '日期：旧 → 新' : '日期：新 → 旧';
            sortRows(direction);
          });

          sortRows('desc');
          applyFilter();
        }
      }
    }
    if (section === 'about' && body.dataset.aboutStatic === 'true') {
      const page = body.querySelector(':scope > .about-page');
      if (page) {
        page.style.setProperty('box-sizing', 'border-box', 'important');
        page.style.setProperty('position', 'relative', 'important');
        page.style.setProperty('left', '0', 'important');
        const compact = window.innerWidth <= 740;
        page.style.setProperty('width', compact ? 'calc(100% - var(--prototype-rail) - 20px)' : 'calc(100% - var(--prototype-rail) - 40px)', 'important');
        page.style.setProperty('max-width', 'none', 'important');
        page.style.setProperty('margin', compact ? '5px 10px 0 calc(var(--prototype-rail) + 10px)' : '5px 18px 0 calc(var(--prototype-rail) + 22px)', 'important');
        page.style.setProperty('padding', '0 0 16px', 'important');
        page.style.setProperty('display', 'block', 'important');
        page.style.setProperty('gap', '0', 'important');
      }
    }
    if (section === 'workflow') {
      const page = body.querySelector('.skill-lab-page');
      const reviews = page?.querySelector('.workflow-reviews');
      if (!reviews && page) {
        const row = document.createElement('section');
        row.className = 'workflow-reviews';
        row.innerHTML = '<h2>用户推荐</h2><div><article><b>张同学</b><p>用这个工作流一键生成 PRD 和原型，节省了大量时间，效率提升明显！</p><strong>★★★★★</strong></article><article><b>李老师</b><p>论文整理工作流帮我快速梳理了大量文献，生成的总结很有参考价值。</p><strong>★★★★★</strong></article><article><b>王同学</b><p>代码审查工作流发现了很多潜在问题，提升了代码质量，帮助很大。</p><strong>★★★★★</strong></article></div>';
        page.querySelector('.lab-footer')?.insertAdjacentElement('beforebegin', row);
      }
      page?.querySelector('.lab-footer')?.style.setProperty('min-height', '230px', 'important');
    }
    if (section === 'tools') {
      const hero = body.querySelector('.tools-hero');
      if (hero && !hero.querySelector('.tools-reference-art')) {
        const art = document.createElement('img');
        art.className = 'tools-reference-art';
        art.src = '/assets/reference/tools-hero-prototype.png';
        art.alt = '';
        art.setAttribute('aria-hidden', 'true');
        hero.appendChild(art);
      }
    }
    if (section === 'tools' || section === 'workflow' || section === 'logs') {
      const footer = body.querySelector('.prototype-footer');
      if (footer) footer.style.setProperty('min-height', section === 'tools' ? '190px' : section === 'workflow' ? '240px' : '185px', 'important');
    }
  };

  const bootSkillsShowcase = () => {
    const page = document.querySelector('body[data-fl-section="skills"]');
    const grid = document.getElementById('skill-grid');
    const data = document.getElementById('skill-data');
    if (!page || !grid || !data || page.dataset.skillsShowcaseReady === '1') return;
    page.dataset.skillsShowcaseReady = '1';
    const skills = JSON.parse(data.textContent || '[]');
    // Only real repo data: no invented titles, owners, usage, ratings or review counts.
    const formatStars = value => typeof value === 'number' && value >= 0 ? (value >= 1000 ? `${(value / 1000).toFixed(1)}k`.replace('.0k', 'k') : String(value)) : '';
    const repoSlug = skill => { const url = String(skill.githubUrl || ''); const parts = url.includes('github.com/') ? url.split('github.com/')[1].split('/').filter(Boolean) : []; return parts.length >= 2 ? `${parts[0]}/${parts[1]}` : ''; };
    const verdictOf = skill => { const run = (skill.freeLLMTest && skill.freeLLMTest.freeModelRun) || {}; return ['通过','部分通过','未通过','调用失败'].includes(run.bestVerdict) ? run.bestVerdict : ''; };
    // FLSKILLS-CURATION-20261012: curated two-row category directory, independent deep links.
    const topicOrder = ['development','planning-office','documents','data-office','presentations','product-design','writing','seo-content','resume','file-office','ecommerce','email-office'];
    const topics = {
      'development': {title:'编程与工程',intro:'先解决真实的工程质量问题：性能、Skill 构建、根因排查；不是把所有开发提示词都摆出来。',picks:['dietrichgebert-ponytail','mattpocock-diagnosing-bugs','vercel-labs-react-best-practices','anthropics-skill-creator','alibaba-open-code-review','anthropics-mcp-builder']},
      'planning-office': {title:'任务与协作',intro:'优先选择能让问题复现、验收可追踪的流程，而不只是通用待办清单。',picks:['obra-systematic-debugging','obra-verification-before-completion','obra-test-driven-development','obra-writing-plans','obra-brainstorming','obra-executing-plans']},
      'documents': {title:'文档处理',intro:'优先展示真正处理过 PDF 和文档工作流的 Skill；需外部依赖的能力明确标注阻塞。',picks:['anthropics-pdf','anthropics-doc-coauthoring','anthropics-docx','iofficeai-officecli-docx','iofficeai-officecli-academic-paper','iofficeai-officecli-word-form']},
      'data-office': {title:'表格与数据',intro:'区分能产出工作簿的验证记录，与尚需 Office CLI 的数据仪表盘链路。',picks:['anthropics-xlsx','iofficeai-officecli-data-dashboard','iofficeai-officecli-xlsx']},
      'presentations': {title:'PPT 与演示',intro:'能做可编辑文件的优先，图片式演示和高级动画作为有条件的候选。',picks:['anthropics-pptx','hugohe3-ppt-master','jimliu-baoyu-slide-deck','iofficeai-officecli-pptx','iofficeai-officecli-pitch-deck','iofficeai-morph-ppt']},
      'product-design': {title:'产品与视觉设计',intro:'分清设计创作、界面审查、静态视觉三类能力，避免只靠漂亮模板。',picks:['pbakaus-impeccable','tt-a1i-archify','anthropics-frontend-design','earthtojake-cad','vercel-labs-web-design-guidelines','anthropics-canvas-design']},
      'writing': {title:'内容写作',intro:'优先解决文字真实感与来源核验；插图生成作为依赖工具的扩展项。',picks:['hyacehila-humanizer-zh-next','blader-humanizer','composiohq-content-research-writer','op7418-humanizer-zh','jimliu-baoyu-article-illustrator','jimliu-baoyu-markdown-to-html']},
      'seo-content': {title:'新媒体与内容运营',intro:'区分公众号发布、小红书图文、封面制作与增长策略，不承诺未经验证的流量收益。',picks:['imraywang-wewrite','jimliu-baoyu-post-to-wechat','jimliu-baoyu-xhs-images','aiworkskills-wechat-article-main','jimliu-baoyu-cover-image','jimliu-baoyu-post-to-x']},
      'resume': {title:'简历与求职',intro:'从岗位匹配、排版导出、可维护简历三个角度比较，绝不鼓励虚构经历。',picks:['composiohq-tailored-resume-generator','jzcreative-html-resume-beautifier','rendercv-rendercv']},
      'file-office': {title:'文件与归档',intro:'更看重分类是否准确、移动操作可预览，以及对发票信息的真实抽取。',picks:['composiohq-invoice-organizer','composiohq-file-organizer']},
      'ecommerce': {title:'商业与客户研究',intro:'广告洞察和潜客研究用途不同，均依赖第三方网站与授权环境。',picks:['composiohq-lead-research-assistant','composiohq-competitive-ads-extractor']},
      'email-office': {title:'团队沟通',intro:'适合内部状态同步、管理汇报与团队信息表达；目前仅有一个符合分类的条目，不补凑数。',picks:['anthropics-internal-comms']}
    };
    // These are editorial judgments tied to source descriptions and FreeLLM test notes, not user ratings.
    const insights = {
      'dietrichgebert-ponytail':["特点：编码前检查已有实现，减少不必要依赖、抽象和代码。","适合：小功能实现、重构与代码审查。","限制：高保真和复杂需求必须先列明验收范围；节省比例未经本站实测。"],
      'pbakaus-impeccable':["特点：将界面视觉规范、响应式与常见设计反模式汇成一套流程。","适合：网站改版、设计 QA 与前端交付。","限制：部分命令依赖额外工具；本站尚未运行浏览器验收。"],
      'tt-a1i-archify':["特点：从代码库或业务流程生成可分享、可交互的图表。","适合：系统架构、产品领域关系与 Agent 流程解释。","限制：图中结构须回查原始项目，不能代替事实核验。"],
      'hyacehila-humanizer-zh-next':["特点：通用中文润色加商务、学术写作专用参考。","适合：已有稿件审稿、去模板化和正式文本语气调整。","限制：不识别作者身份、不保证通过任何 AI 检测；须人工审阅。"],
      'imraywang-wewrite':["特点：先查来源再写稿，审稿后可单独加配图与排版。","适合：公众号定期更新和编辑团队。","限制：发布需额外配置并授权；本站未做真实账号验收。"],

      'vercel-labs-react-best-practices':['特点：按优先级检查 React/Next.js 的请求瀑布、渲染与打包问题。','适合：实际前端性能优化与代码审查。','限制：任务级验证，需结合框架版本及真实性能测量。'],
      'anthropics-skill-creator':['特点：覆盖 Skill 触发条件、迭代和基准检查。','适合：创建可复用 Agent 技能库。','限制：完整评测脚本链路在当前沙箱未打通。'],
      'mattpocock-diagnosing-bugs':['特点：先建立复现反馈，再逐个验证原因。','适合：疑难 Bug 和性能回退。','限制：任务级检查通过不等于任何仓库自动修复成功。'],
      'obra-systematic-debugging':['特点：先定位再改动，保留失败到通过的测试证据。','适合：有稳定复现的程序错误。','限制：需要能运行测试的工程环境。'],
      'obra-verification-before-completion':['特点：先跑验证命令，再宣布完成。','适合：提交、修复和发布前的验收。','限制：只证明被测范围，不保证覆盖所有风险。'],
      'obra-test-driven-development':['特点：RED—GREEN—REFACTOR 流程已在夹具中执行。','适合：需求边界明确的功能与缺陷修复。','限制：测试设计错误仍可能带来虚假的安全感。'],
      'anthropics-pdf':['特点：真实完成 PDF 生成、拆分、旋转及渲染检查。','适合：表单、报告与 PDF 自动化。','限制：中文字体和扫描件 OCR 需额外检查。'],
      'anthropics-doc-coauthoring':['特点：通过补上下文、迭代与读者校验协作写规格。','适合：长文档、PRD 与技术决策记录。','限制：轻量文档使用时流程偏重，非程序 E2E。'],
      'anthropics-docx':['特点：覆盖 Word 编辑、批注、修订及排版。','适合：正式 Word 文档工作。','限制：沙箱依赖安装失败，不能标成端到端通过。'],
      'anthropics-xlsx':['特点：工作簿公式、结构和数据校验有真实产物。','适合：Excel 分析、清洗与报表。','限制：验证采用替代工具链，不等于原 Skill E2E。'],
      'iofficeai-officecli-data-dashboard':['特点：面向 KPI、图表和条件格式的 Excel 仪表盘。','适合：需要复用模板的经营看板。','限制：officecli 缺失，原链路未执行。'],
      'iofficeai-officecli-xlsx':['特点：强调模板、公式与透视表的办公链路。','适合：复杂工作簿操作。','限制：依赖 officecli 安装和验证。'],
      'anthropics-pptx':['特点：PPTX 生成后做了 PDF 转换与逐页渲染检查。','适合：可编辑演示与正式汇报。','限制：复杂模板和跨版本效果仍需复核。'],
      'hugohe3-ppt-master':['特点：聚焦可编辑演示、模板填充和视觉还原。','适合：需要强版式控制的 PPT 制作。','限制：当前仅部分验证，未完成原脚本全流程。'],
      'jimliu-baoyu-slide-deck':['特点：按内容结构规划幻灯片并生成页面图像。','适合：讲解型和视觉型演示。','限制：外部生成服务未接通，不能当作已实测通过。'],
      'anthropics-frontend-design':['特点：强调有辨识度的视觉方向和响应式页面。','适合：原型设计及已有界面重塑。','限制：产物已验证，但浏览器交互 E2E 被环境阻塞。'],
      'vercel-labs-web-design-guidelines':['特点：从可访问性、布局与交互审查 Web UI。','适合：上线前设计 QA。','限制：它是审查清单，不能替代真实用户测试。'],
      'anthropics-canvas-design':['特点：强调原创静态视觉构图和可交付图稿。','适合：海报、封面与单页视觉。','限制：不适合代替复杂交互产品设计。'],
      'blader-humanizer':['特点：减少套路化语句，保留核心事实与原意。','适合：已有草稿的语言打磨。','限制：不是客观 AI 文本检测器，需人工审稿。'],
      'composiohq-content-research-writer':['特点：把研究、提纲、引用与逐段写作串联。','适合：长文、报告及内容策划。','限制：引用和事实可靠性需要单独核验。'],
      'jimliu-baoyu-article-illustrator':['特点：根据文章逻辑决定插图位置和视觉风格。','适合：图文长文与公众号排版。','限制：实际生成依赖外部服务，本轮沙箱阻塞。'],
      'jimliu-baoyu-post-to-wechat':['特点：衔接 HTML/Markdown 文章到公众号发布。','适合：公众号内容生产流水线。','限制：需要账户授权与真实发布复核，沙箱未验证。'],
      'jimliu-baoyu-xhs-images':['特点：把主题拆分成社媒图文卡片。','适合：小红书多图内容制作。','限制：外部图像能力未接通，本轮未跑通。'],
      'jimliu-baoyu-cover-image':['特点：按版式、配色和传播场景设计封面。','适合：文章头图及跨平台适配。','限制：实际图像生成链路待验收。'],
      'composiohq-tailored-resume-generator':['特点：把岗位要求与已有经历一一对齐。','适合：针对目标岗位改写简历。','限制：不能为匹配关键词而杜撰经历。'],
      'jzcreative-html-resume-beautifier':['特点：用 HTML 模板排版 A4 简历，强调隐私。','适合：网页版与 PDF 风格统一。','限制：原脚本与隐私审计未完成验证。'],
      'rendercv-rendercv':['特点：YAML 内容与排版分离，便于版本维护。','适合：技术岗位简历的持续迭代。','限制：RenderCV/Typst 依赖尚未安装验证。'],
      'composiohq-invoice-organizer':['特点：从发票抽取日期、金额和主体后归档。','适合：费用票据整理。','限制：扫描件、多币种和复杂税项需额外规则。'],
      'composiohq-file-organizer':['特点：查重、命名和文件夹结构梳理。','适合：混乱文件夹的定期整理。','限制：任何批量移动都应先预览和备份。'],
      'composiohq-lead-research-assistant':['特点：按目标客户画像寻找潜在线索。','适合：销售名单初筛和研究。','限制：需要外部数据访问，且须核实信息来源。'],
      'composiohq-competitive-ads-extractor':['特点：从公开广告素材归纳竞品表达和创意。','适合：市场定位与投放内容研究。','限制：广告库可访问性和数据新鲜度未实测。'],
      'anthropics-internal-comms':['特点：提供状态报告、组织公告与领导简报结构。','适合：团队内部信息同步。','限制：与普通写作提示存在重叠，需人工核对事实。']
    };
    const iconFor = skill => {
      const n = String(skill.name || '').toLowerCase();
      if (/ppt|slide|deck|presentation|morph/.test(n)) return 'ppt';
      if (/xlsx|excel|dashboard|data|spreadsheet/.test(n)) return 'data';
      if (/image|art|canvas|visual|brand|theme|design|impeccable|archify|cad|infographic|cover|xhs/.test(n)) return 'image';
      if (/wechat|twitter|post-to|seo|ads|lead|marketing/.test(n)) return 'marketing';
      if (/autom|agent|mcp|skill-creator|worktree|executing|parallel/.test(n)) return 'automation';
      if (/ponytail|react|code|debug|testing|test-driven|security|webapp|frontend|implement|vercel/.test(n)) return 'code';
      if (/resume|meeting|plan|brainstorm|verify|verification|research|extract|transcript/.test(n)) return 'summary';
      if (/doc|pdf|paper|write|human|content|article|file|invoice|office/.test(n)) return 'paper';
      return ({'development':'code','planning-office':'summary','documents':'paper','data-office':'data','presentations':'ppt','product-design':'image','writing':'paper','seo-content':'marketing','resume':'summary','file-office':'paper','ecommerce':'marketing','email-office':'summary'})[skill.category] || 'summary';
    };
    const urlTopic = new URLSearchParams(window.location.search).get('category');
    const initialTopic = topicOrder.includes(urlTopic) || urlTopic === 'all' ? urlTopic : 'development';
    page.dataset.skillCategory = initialTopic;
    const copy = (value) => String(value || '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
    const workspace = page.querySelector('.skills-workspace');
    const detailPanel = document.getElementById('selected-skill-panel');
    let selectedId = skills[0]?.id || '';
    let panelOpen = false;
    let view = 'grid';
    let showAllSkills = false;
    const filtered = () => {
      const query = document.getElementById('skill-search').value.trim().toLowerCase();
      const status = document.getElementById('skill-status').value;
      const category = page.dataset.skillCategory || 'development';
      const isSearch = Boolean(query);
      const chosen = category === 'all' ? skills : (isSearch
        ? skills.filter(skill => skill.category === category)
        : topics[category].picks.map(id => skills.find(skill => skill.id === id)).filter(Boolean));
      let list = chosen.filter(skill => {
        const values = [skill.name,skill.description,skill.description_zh,skill.githubUrl,...(skill.compatibility || [])].join(' ').toLowerCase();
        return (status === 'all' || status === skill.status) && (!query || values.includes(query));
      });
      const sort = document.getElementById('skill-sort')?.value || 'recommended';
      if (sort === 'popular') list = list.slice().sort((a,b) => (b.repoStats?.stars || 0) - (a.repoStats?.stars || 0));
      if (sort === 'rating') list = list.slice().sort((a,b) => (Number(b.freeLLMTest?.score) || 0) - (Number(a.freeLLMTest?.score) || 0));
      return list;
    };
    const card = skill => {
      const title = skill.name;
      const description = skill.description_zh || skill.description || '';
      const tags = (skill.compatibility || []).slice(0,3);
      const stars = formatStars(skill.repoStats?.stars);
      const verdict = verdictOf(skill);
      const owner = repoSlug(skill) || '来源仓库待补充';
      const icon = iconFor(skill);
      const letters = String(skill.name || '').replace(/[^a-z0-9]/gi,'').slice(0,2).toUpperCase() || 'SK';
      const topic = topics[page.dataset.skillCategory];
      const index = topic ? topic.picks.indexOf(skill.id) : -1;
      const featured = index >= 0 && index < 3 && (document.getElementById('skill-sort')?.value || 'recommended') === 'recommended';
      const notes = featured ? insights[skill.id] : null;
      const evidence = skill.freeLLMTest || {};
      const testLevel = evidence.testLevel || 'unknown';
      const testLabel = ({e2e:'原链路 E2E',artifact:'真实产物',task:'任务级验证',partial:'部分验证',blocked:'环境阻塞',unknown:'未实测'})[testLevel] || '未实测';
      const commentary = notes ? '<div class="skill-editorial"><strong>FreeLLM 重点解析</strong><p>'+notes.map(note => copy(note)).join('<br>')+'</p><small>证据级别：'+copy(testLabel)+'</small></div>' : '';
      const rank = featured ? '<span class="skill-pick-label">TOP 0'+(index+1)+' · 精选分析</span>' : '';
      const active = panelOpen && selectedId === skill.id;
      return '<article class="skill-card showcase-card'+(featured?' skill-featured':'')+(active?' is-selected':'')+'" data-skill-id="'+copy(skill.id)+'" data-category="'+copy(skill.category)+'" data-status="'+copy(skill.status)+'" tabindex="0" aria-label="'+copy(title)+'：'+copy(description)+'"><div class="skill-card-heading"><span class="skill-card-icon" data-icon="'+icon+'" aria-hidden="true"><small class="skill-icon-letters">'+copy(letters)+'</small></span><button class="skill-card-select" type="button" data-select-skill="'+copy(skill.id)+'" aria-label="选择 '+copy(title)+'">'+(active?'✓':'＋')+'</button></div>'+rank+'<h3>'+copy(title)+'</h3><p>'+copy(description)+'</p>'+commentary+'<div class="skill-card-tags">'+tags.map(tag=>'<span>'+copy(tag)+'</span>').join('')+'</div><div class="skill-card-metrics"><span title="来源仓库的 GitHub Star，不是单个 Skill 的评分">仓库 ★ '+copy(stars || '—')+'</span><span>'+testLabel+'</span></div><div class="skill-card-footer"><span class="skill-owner-avatar" data-icon="avatar-'+icon+'" aria-hidden="true"></span><span>'+copy(owner)+'</span><button class="skill-details skill-card-more" type="button" data-skill-id="'+copy(skill.id)+'" aria-label="查看 '+copy(title)+' 详情">⋮</button></div></article>';
    };
    const setText = (id, value) => { const node = document.getElementById(id); if (node) node.textContent = value; };
    const updatePanel = skill => {
      if (!skill) return;
      const title = skill.name;
      const description = skill.description_zh || skill.description || '';
      selectedId = skill.id;
      setText('detail-title', title);
      setText('detail-summary', description);
      setText('detail-description', description);
      const owner = document.getElementById('detail-owner');
      if (owner) owner.innerHTML = `<i aria-hidden="true">◆</i> ${copy(repoSlug(skill) || '来源仓库待补充')}`;
      document.getElementById('detail-icon').dataset.icon = iconFor(skill);
      setText('detail-rating', verdictOf(skill) || '未实测');
      setText('detail-reviews', '免费模型任务实测');
      setText('detail-usage', formatStars(skill.repoStats?.stars) || '—');
      setText('detail-usage-label', '仓库 Star（整个仓库）');
      const run = (skill.freeLLMTest && skill.freeLLMTest.freeModelRun) || {};
      setText('detail-test-task', run.task || '暂无免费模型任务实测记录。');
      const tags = (skill.compatibility || []).slice(0,6);
      document.getElementById('detail-tags').innerHTML = tags.length ? tags.map(tag=>`<span>${copy(tag)}</span>`).join('') : '<span>未标注</span>';
      document.getElementById('detail-use').dataset.skillId = skill.id;
      document.getElementById('detail-favorite').dataset.skillId = skill.id;
      const models = (skill.compatibility || []).slice(0,3);
      document.getElementById('detail-models').innerHTML = models.length ? models.map(model=>`<span>${copy(model)}</span>`).join('') : '<span>未标注</span>';
      grid.querySelectorAll('.skill-card').forEach(node => node.classList.toggle('is-selected', panelOpen && node.dataset.skillId === skill.id));
      grid.querySelectorAll('.skill-card-select').forEach(node => { const active=panelOpen && node.dataset.selectSkill===skill.id; node.textContent=active?'✓':'＋'; node.setAttribute('aria-pressed',String(active)); });
    };
    const heading = page.querySelector('.skills-directory-heading > h2');
    const headingSection = page.querySelector('.skills-directory-heading');
    const topicMenu = page.querySelector('.skills-topic-nav') || document.createElement('nav');
    topicMenu.className = 'skills-topic-nav';
    topicMenu.setAttribute('aria-label', 'Skills 分类二级导航');
    topicMenu.innerHTML = '<div class="skills-topic-heading"><strong>按技能类型探索</strong><span>每类最多两排 · 前三重点分析</span></div><div class="skills-topic-links">' +
      topicOrder.map(id => '<a data-skill-topic="'+id+'" href="/skills/?category='+encodeURIComponent(id)+'">'+copy(topics[id].title)+' <small>'+skills.filter(s=>s.category===id).length+'</small></a>').join('') +
      '<a data-skill-topic="all" class="skills-topic-archive" href="/skills/?category=all">完整资源库 <small>'+skills.length+'</small></a></div>';
    if (!topicMenu.parentNode) headingSection.before(topicMenu);
    const topicDescription = document.createElement('p');
    topicDescription.className = 'skills-topic-description';
    heading?.after(topicDescription);
    const setTopic = (id, addHistory) => {
      const next = topicOrder.includes(id) || id === 'all' ? id : 'development';
      page.dataset.skillCategory = next;
      showAllSkills = false;
      if (addHistory) {
        const url = new URL(window.location.href);
        url.searchParams.set('category', next);
        history.pushState(null, '', url.pathname + url.search + url.hash);
      }
      render();
    };
    const render = () => {
      const category = page.dataset.skillCategory || 'development';
      const matches = filtered();
      const isArchive = category === 'all';
      const searching = Boolean(document.getElementById('skill-search').value.trim());
      const visible = isArchive && showAllSkills ? matches : matches.slice(0,6);
      grid.innerHTML = visible.map(card).join('');
      document.getElementById('skill-empty').hidden = matches.length > 0;
      const categoryTotal = isArchive ? skills.length : skills.filter(s=>s.category===category).length;
      document.getElementById('skill-count').textContent = searching
        ? '搜索结果 '+visible.length+' / '+matches.length
        : (isArchive ? '显示 '+visible.length+' / '+categoryTotal : '精选 '+visible.length+' / 本类收录 '+categoryTotal);
      if (heading) heading.textContent = isArchive ? '全部 Skill 资料库' : '分类精选 · '+topics[category].title;
      topicDescription.textContent = isArchive
        ? '保留全部已收录条目；默认只展示前六项，按需展开。完整资料不等于全部推荐。'
        : topics[category].intro;
      topicMenu.querySelectorAll('[data-skill-topic]').forEach(a => {
        const active = a.dataset.skillTopic===category;
        if(active) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current');
      });
      const browseButton = document.getElementById('skills-browse-all');
      if (browseButton) {
        browseButton.setAttribute('aria-expanded',String(isArchive && showAllSkills));
        browseButton.innerHTML = isArchive
          ? (showAllSkills ? '收起完整列表 <span aria-hidden="true">↑</span>' : '展开全部 '+skills.length+' 项 <span aria-hidden="true">→</span>')
          : '查看完整资源库 <span aria-hidden="true">→</span>';
      }
      const selected = visible.find(skill=>skill.id===selectedId) || visible[0];
      if (selected) updatePanel(selected);
      const hidden = page.querySelector('.skills-hidden-filters');
      if (hidden) hidden.setAttribute('aria-hidden','false');
    };
    topicMenu.addEventListener('click', event => {
      const link = event.target.closest('a[data-skill-topic]');
      if (!link) return;
      event.preventDefault();
      setTopic(link.dataset.skillTopic, true);
    });
    window.addEventListener('popstate', () => {
      const found = new URLSearchParams(window.location.search).get('category');
      setTopic(found, false);
    });
    document.getElementById('skills-browse-all')?.addEventListener('click', event => {
      event.preventDefault();
      if (page.dataset.skillCategory !== 'all') setTopic('all', true);
      else { showAllSkills = !showAllSkills; render(); }
      document.getElementById('skill-grid')?.scrollIntoView({behavior:'smooth',block:'start'});
    });
    document.querySelectorAll('.skill-category-tab').forEach(button => button.addEventListener('click', event => {
      event.stopImmediatePropagation();
      setTopic(button.dataset.category, true);
    }, {capture:true}));
    document.getElementById('skill-search').addEventListener('input', render);
    document.getElementById('skill-status').addEventListener('change', render);
    document.getElementById('skill-sort')?.addEventListener('change', render);
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
      view = button.dataset.view;
      grid.classList.toggle('is-list-view', view === 'list');
      document.querySelectorAll('[data-view]').forEach(item => item.classList.toggle('is-active', item === button));
    }));
    grid.addEventListener('click', event => {
      const more = event.target.closest('.skill-details');
      if (more) return;
      const cardNode = event.target.closest('.skill-card');
      if (!cardNode) return;
      const skill = skills.find(item => item.id === cardNode.dataset.skillId);
      panelOpen = true;
      workspace?.classList.add('has-detail');
      detailPanel?.classList.remove('is-collapsed');
      updatePanel(skill);
      grid.querySelectorAll('.skill-card').forEach(node => node.classList.toggle('is-selected', node === cardNode));
    });
    grid.addEventListener('keydown', event => {
      if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('.skill-card')) { event.preventDefault(); updatePanel(skills.find(item=>item.id===event.target.dataset.skillId)); }
    });
    document.getElementById('skill-clear').addEventListener('click', () => {
      document.getElementById('skill-search').value=''; document.getElementById('skill-status').value='all'; setTopic('development',true);
    });
    document.getElementById('detail-use').addEventListener('click', () => {
      const skill = skills.find(item=>item.id===document.getElementById('detail-use').dataset.skillId);
      const trigger = grid.querySelector(`.skill-details[data-skill-id="${CSS.escape(skill?.id || '')}"]`);
      trigger?.click();
    });
    document.getElementById('detail-favorite').addEventListener('click', event => {
      const button=event.currentTarget; const key='freellm-skill-favorites'; let ids=[];
      try { ids=JSON.parse(localStorage.getItem(key)||'[]'); } catch {}
      const id=button.dataset.skillId; ids=ids.includes(id)?ids.filter(value=>value!==id):[...ids,id];
      try { localStorage.setItem(key,JSON.stringify(ids)); } catch {}
      button.classList.toggle('is-favorite',ids.includes(id)); button.textContent=ids.includes(id)?'♥':'♡';
    });
    document.querySelector('.skills-detail-close')?.addEventListener('click',()=>{
      panelOpen = false;
      workspace?.classList.remove('has-detail');
      detailPanel?.classList.add('is-collapsed');
      grid.querySelectorAll('.skill-card').forEach(node => node.classList.remove('is-selected'));
      grid.querySelectorAll('.skill-card-select').forEach(node => { node.textContent='＋'; node.setAttribute('aria-pressed','false'); });
    });
    document.querySelector('[data-skills-intro]')?.addEventListener('click',()=>{
      document.getElementById('skills-intro-notice')?.showModal();
    });
    document.querySelector('[data-close-skills-intro]')?.addEventListener('click',()=>document.getElementById('skills-intro-notice')?.close());
    // Topic reset is handled by the clear button above.
    const accountNotice=document.createElement('div'); accountNotice.id='skills-account-notice'; accountNotice.className='skills-toast'; accountNotice.setAttribute('role','status'); accountNotice.hidden=true; page.append(accountNotice);
    render();
  };
  window.FreeLLMReferenceShell = { mount: boot };
  window.addEventListener('freellm:page-mount', boot);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
