
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
      topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.4"></circle><path d="m16 16 4.2 4.2"></path></svg></span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions"><button class="ref-locale" type="button" data-reference-locale-toggle aria-label="切换语言">' + localeLabel + '</button><button class="ref-bell" type="button" aria-label="更新提醒"><svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg></button><button class="prototype-login" type="button">登录</button><button class="prototype-register" type="button">注册</button></div>';
    } else {
      const actions = ['skills', 'tools', 'workflow', 'logs', 'about'].includes(section)
        ? '<button class="ref-bell" type="button" aria-label="更新提醒" data-reference-notifications>♧</button><button class="ref-auth-button" type="button" data-auth-action="login">登录</button><button class="ref-auth-button primary" type="button" data-auth-action="register">注册</button>'
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
      topbar.querySelectorAll('[data-auth-action]').forEach(button => button.addEventListener('click', () => {
        const message = document.getElementById('skills-account-notice');
        if (message) {
          message.textContent = button.dataset.authAction === 'login' ? '登录入口即将开放' : '注册入口即将开放';
          message.hidden = false;
          window.setTimeout(() => { message.hidden = true; }, 2200);
        }
      }));
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
      if (target) {
        mirrorSearch();
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.focus({ preventScroll: true });
      } else if (value) {
        location.href = '/?q=' + encodeURIComponent(value);
      }
    };
    topInput.addEventListener('input', mirrorSearch);
    topInput.addEventListener('keydown', event => { if (event.key === 'Enter') sync(); });
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
        footer.innerHTML = '<div class="prototype-footer-main"><div class="prototype-footer-brand"><img src="/assets/reference/rail-brand.png" alt=""><div><strong>FreeLLM</strong><small>AI for Everyone</small><p>让优质的 AI 资源，触手可及。</p></div></div><nav><strong>产品</strong><a href="/models/">模型库</a><a href="/tools/">工具箱</a><a href="/skills/">Skills</a><a href="/skills/lab/">工作流</a></nav><nav><strong>资源</strong><a href="/logs/">最新更新</a><a href="/models/">热门资源</a><a href="/about/">使用说明</a><a href="/submit/">提交资源</a></nav><nav><strong>社区</strong><a href="/about/">关于我们</a><a href="/submit/">提交资源</a><a href="mailto:xdguo0527@gmail.com">反馈建议</a></nav><div class="prototype-footer-slogan">Better AI<br>A Brighter Tomorrow</div></div><div class="prototype-footer-bottom"><span>© 2024 FreeLLM. All rights reserved.</span><span class="prototype-footer-social"><a href="https://github.com/xdguo-design/freellm" aria-label="GitHub">●</a><span aria-label="Twitter"><svg viewBox="0 0 24 24"><path d="M23.95 4.57a10 10 0 0 1-2.89.79 5.04 5.04 0 0 0 2.21-2.78 10.05 10.05 0 0 1-3.19 1.22 5.02 5.02 0 0 0-8.55 4.58A14.25 14.25 0 0 1 1.2 3.13a5.02 5.02 0 0 0 1.55 6.7 4.97 4.97 0 0 1-2.27-.63v.06a5.03 5.03 0 0 0 4.03 4.93 5.05 5.05 0 0 1-2.26.09 5.03 5.03 0 0 0 4.69 3.49A10.08 10.08 0 0 1 0 19.86a14.22 14.22 0 0 0 7.7 2.26c9.24 0 14.3-7.65 14.3-14.29v-.65a10.2 10.2 0 0 0 2.5-2.6Z"/></svg></span><span aria-label="Discord"><svg viewBox="0 0 24 24"><path d="M19.7 5.1A18.1 18.1 0 0 0 15.3 3l-.6 1.2a16.7 16.7 0 0 0-5.4 0L8.7 3a18.1 18.1 0 0 0-4.4 2.1C1.5 9.2.7 13.2 1.1 17.2a18.2 18.2 0 0 0 5.4 2.7l1.2-2a11.8 11.8 0 0 1-1.9-.9l.5-.4a13 13 0 0 0 11.4 0l.5.4a11.8 11.8 0 0 1-1.9.9l1.2 2a18.2 18.2 0 0 0 5.4-2.7c.5-4.6-.8-8.6-3.2-12.1ZM8.8 14.3c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Zm6.4 0c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Z"/></svg></span></span><button type="button" data-locale-switch="zh-CN">◎　简体中文　⌄</button></div>';
        if (section === 'about') {
          footer.innerHTML = '<div class="prototype-footer-main"><div class="prototype-footer-brand"><img src="/assets/reference/rail-brand.png" alt=""><div><strong>FreeLLM</strong><small>AI for Everyone</small><p>让优质的 AI 资源，触手可及。</p></div></div><nav><strong>产品</strong><a href="/models/">模型库</a><a href="/skills/">Skills</a><a href="/tools/">工具</a><a href="/skills/lab/">工作流</a></nav><nav><strong>资源</strong><a href="/logs/">最新更新</a><a href="/models/">热门资源</a><a href="/guide/">使用教程</a><a href="https://github.com/xdguo-design/freellm">开发文档</a><a href="/category/student/">学生优惠</a></nav><nav><strong>社区</strong><a href="/about/">关于我们</a><a href="/submit/">提交资源</a><a href="/community/">加入社区</a><a href="mailto:xdguo0527@gmail.com">反馈建议</a></nav><div class="prototype-footer-slogan">Better AI<br>A Brighter Tomorrow</div></div><div class="prototype-footer-bottom"><span>© 2024 FreeLLM. All rights reserved.</span><nav class="prototype-footer-legal"><a href="/privacy/">隐私政策</a><a href="/terms/">服务条款</a><a href="/terms/#disclaimer">免责声明</a></nav><span class="prototype-footer-social"><a href="https://github.com/xdguo-design/freellm" aria-label="GitHub"><svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.61-3.37-1.18-3.37-1.18-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.54 2.36 1.1 2.94.84.09-.65.35-1.1.64-1.36-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0 1 12 6.91c.85 0 1.71.11 2.52.34 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.7-4.57 4.95.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg></a><span aria-label="Twitter"><svg viewBox="0 0 24 24"><path d="M23.95 4.57a10 10 0 0 1-2.89.79 5.04 5.04 0 0 0 2.21-2.78 10.05 10.05 0 0 1-3.19 1.22 5.02 5.02 0 0 0-8.55 4.58A14.25 14.25 0 0 1 1.2 3.13a5.02 5.02 0 0 0 1.55 6.7 4.97 4.97 0 0 1-2.27-.63v.06a5.03 5.03 0 0 0 4.03 4.93 5.05 5.05 0 0 1-2.26.09 5.03 5.03 0 0 0 4.69 3.49A10.08 10.08 0 0 1 0 19.86a14.22 14.22 0 0 0 7.7 2.26c9.24 0 14.3-7.65 14.3-14.29v-.65a10.2 10.2 0 0 0 2.5-2.6Z"/></svg></span><span aria-label="Discord"><svg viewBox="0 0 24 24"><path d="M19.7 5.1A18.1 18.1 0 0 0 15.3 3l-.6 1.2a16.7 16.7 0 0 0-5.4 0L8.7 3a18.1 18.1 0 0 0-4.4 2.1C1.5 9.2.7 13.2 1.1 17.2a18.2 18.2 0 0 0 5.4 2.7l1.2-2a11.8 11.8 0 0 1-1.9-.9l.5-.4a13 13 0 0 0 11.4 0l.5.4a11.8 11.8 0 0 1-1.9.9l1.2 2a18.2 18.2 0 0 0 5.4-2.7c.5-4.6-.8-8.6-3.2-12.1ZM8.8 14.3c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Zm6.4 0c-1.1 0-1.9-1-1.9-2.1s.8-2.1 1.9-2.1 1.9 1 1.9 2.1-.8 2.1-1.9 2.1Z"/></svg></span></span><button type="button" data-locale-switch="zh-CN">◎　简体中文　⌄</button></div>';
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
        archiveLink?.addEventListener('click', event => {
          event.preventDefault();
          if (archive) {
            archive.open = true;
            archive.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        });
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
    const showcase = {
      'anthropics-docx': { title:'论文写作助手', description:'从选题到初稿，助你高效完成学术论文写作。', category:'写作', tags:['写作','学术','研究'], icon:'paper', owner:'FreeLLM 官方', usage:'12.4k', rating:'4.9', reviews:'(1.2k 评价)' },
      'vercel-labs-react-best-practices': { title:'代码生成专家', description:'根据需求快速生成高质量、可维护的代码。', category:'编程', tags:['编程','开发','自动化'], icon:'code', owner:'Open Source', usage:'9.8k', rating:'4.8', reviews:'(980 评价)' },
      'anthropics-xlsx': { title:'数据分析助手', description:'帮你清洗、分析和可视化数据，洞察业务趋势。', category:'研究', tags:['数据分析','可视化','Excel'], icon:'data', owner:'DataGuru', usage:'8.6k', rating:'4.8', reviews:'(860 评价)' },
      'anthropics-pdf': { title:'长文档总结', description:'快速提炼长文档要点，生成结构化总结。', category:'办公', tags:['阅读','总结','生产力'], icon:'summary', owner:'MindFlow', usage:'7.1k', rating:'4.7', reviews:'(710 评价)' },
      'anthropics-algorithmic-art': { title:'图像生成大师', description:'将创意转化为惊艳的图像作品，支持多种风格。', category:'图像', tags:['图像','设计','创意'], icon:'image', owner:'VisionLab', usage:'15.2k', rating:'4.9', reviews:'(1.5k 评价)' },
      'obra-executing-plans': { title:'自动化工作流设计', description:'设计和搭建自动化工作流，串联多个工具提高效率。', category:'自动化', tags:['自动化','工作流','效率'], icon:'automation', owner:'FlowMaster', usage:'6.8k', rating:'4.8', reviews:'(680 评价)' },
      'composiohq-twitter-algorithm-optimizer': { title:'内容营销专家', description:'生成高质量的营销文案、社媒内容与传播策略。', category:'运营', tags:['营销','运营','写作'], icon:'marketing', owner:'GrowthAI', usage:'5.9k', rating:'4.7', reviews:'(590 评价)' },
      'hugohe3-ppt-master': { title:'PPT 智能生成', description:'一键生成精美专业的演示文稿，让表达更出色。', category:'办公', tags:['演示','汇报','办公'], icon:'ppt', owner:'SlidePro', usage:'6.1k', rating:'4.8', reviews:'(610 评价)' }
    };
    const showcaseOrder = ['anthropics-docx','vercel-labs-react-best-practices','anthropics-xlsx','anthropics-pdf','anthropics-algorithmic-art','obra-executing-plans','composiohq-twitter-algorithm-optimizer','hugohe3-ppt-master'];
    const showcaseRank = new Map(showcaseOrder.map((id,index)=>[id,index]));
    skills.sort((a,b)=>(showcaseRank.get(a.id) ?? showcaseOrder.length)-(showcaseRank.get(b.id) ?? showcaseOrder.length));
    const copy = (value) => String(value || '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
    const counts = Object.fromEntries(skills.map(item => [item.id, showcase[item.id] || null]));
    const workspace = page.querySelector('.skills-workspace');
    const detailPanel = document.getElementById('selected-skill-panel');
    let selectedId = skills[0]?.id || '';
    let panelOpen = false;
    let view = 'grid';
    let showAllSkills = false;
    const filtered = () => {
      const query = document.getElementById('skill-search').value.trim().toLowerCase();
      const status = document.getElementById('skill-status').value;
      const category = page.dataset.skillCategory || 'all';
      const groups = {
        writing:['writing','seo-content','email-office'], development:['development'], research:['planning-office','data-office'],
        office:['documents','presentations','file-office','resume','email-office'], image:['product-design'], data:['data-office'],
        operations:['ecommerce','seo-content'], automation:['development','planning-office']
      };
      let list = skills.filter(skill => {
        const sample = counts[skill.id];
        const values = [skill.name, skill.description, skill.description_zh, skill.githubUrl, ...(skill.compatibility || []), sample?.title, sample?.description, ...(sample?.tags || [])].join(' ').toLowerCase();
        const categoryMatch = category === 'all' || (groups[category] || []).includes(skill.category);
        return categoryMatch && (status === 'all' || status === skill.status) && (!query || values.includes(query));
      });
      const sort = document.getElementById('skill-sort')?.value || 'recommended';
      if (sort === 'popular') list.sort((a,b) => (b.repoStats?.stars || 0) - (a.repoStats?.stars || 0));
      if (sort === 'rating') list.sort((a,b) => (Number(b.freeLLMTest?.score) || 0) - (Number(a.freeLLMTest?.score) || 0));
      return list;
    };
    const card = skill => {
      const item = counts[skill.id];
      const title = item?.title || skill.name;
      const description = item?.description || skill.description_zh || skill.description || '';
      const tags = item?.tags || (skill.compatibility || []).slice(0,3);
      const usage = item?.usage || '—';
      const rating = item?.rating || (skill.freeLLMTest?.score ? Number(skill.freeLLMTest.score).toFixed(1) : '4.8');
      const owner = item?.owner || (skill.repoStats?.owner || 'Open Source');
      const icon = item?.icon || 'default';
      const active = panelOpen && selectedId === skill.id;
      return `<article class="skill-card showcase-card${active?' is-selected':''}" data-skill-id="${copy(skill.id)}" data-category="${copy(skill.category)}" data-status="${copy(skill.status)}" tabindex="0" aria-label="${copy(title)}：${copy(description)}"><div class="skill-card-heading"><span class="skill-card-icon" data-icon="${icon}" aria-hidden="true"></span><button class="skill-card-select" type="button" data-select-skill="${copy(skill.id)}" aria-label="选择 ${copy(title)}">${active?'✓':'＋'}</button></div><h3>${copy(title)}</h3><p>${copy(description)}</p><div class="skill-card-tags">${tags.map(tag=>`<span>${copy(tag)}</span>`).join('')}</div><div class="skill-card-metrics"><span>♨ ${copy(usage)}</span><span>★ ${copy(rating)}</span></div><div class="skill-card-footer"><span class="skill-owner-avatar" data-icon="avatar-${icon}" aria-hidden="true"></span><span>${copy(owner)}</span><button class="skill-details skill-card-more" type="button" data-skill-id="${copy(skill.id)}" aria-label="查看 ${copy(title)} 详情">⋮</button></div></article>`;
    };
    const updatePanel = skill => {
      if (!skill) return;
      const item = counts[skill.id] || {};
      const title = item.title || skill.name;
      const description = item.description || skill.description_zh || skill.description || '';
      selectedId = skill.id;
      document.getElementById('detail-title').textContent = title;
      document.getElementById('detail-summary').textContent = description;
      document.getElementById('detail-description').textContent = skill.description_zh || description;
      document.getElementById('detail-icon').dataset.icon = item.icon || 'default';
      document.getElementById('detail-rating').textContent = item.rating || (skill.freeLLMTest?.score ? Number(skill.freeLLMTest.score).toFixed(1) : '4.8');
      document.getElementById('detail-reviews').textContent = item.reviews || `(${(skill.reviews || []).length} 条评价)`;
      document.getElementById('detail-usage').textContent = item.usage || '—';
      const tags = item.tags || (skill.compatibility || []).slice(0,6);
      document.getElementById('detail-tags').innerHTML = tags.map(tag=>`<span>${copy(tag)}</span>`).join('');
      document.getElementById('detail-use').dataset.skillId = skill.id;
      document.getElementById('detail-favorite').dataset.skillId = skill.id;
      const models = (skill.compatibility || []).slice(0,3);
      if (models.length) document.getElementById('detail-models').innerHTML = models.map((model,index)=>`<span>${['◉','▣','✦'][index%3]} ${copy(model)}</span>`).join('');
      grid.querySelectorAll('.skill-card').forEach(node => node.classList.toggle('is-selected', panelOpen && node.dataset.skillId === skill.id));
      grid.querySelectorAll('.skill-card-select').forEach(node => { const active=panelOpen && node.dataset.selectSkill===skill.id; node.textContent=active?'✓':'＋'; node.setAttribute('aria-pressed',String(active)); });
    };
    const render = () => {
      const matches = filtered();
      const hasFilters = document.getElementById('skill-search').value.trim() !== '' ||
        document.getElementById('skill-status').value !== 'all' ||
        (page.dataset.skillCategory || 'all') !== 'all' ||
        (document.getElementById('skill-sort')?.value || 'recommended') !== 'recommended' ||
        view === 'list';
      const visible = !showAllSkills && !hasFilters ? matches.slice(0, 8) : matches;
      grid.innerHTML = visible.map(card).join('');
      document.getElementById('skill-empty').hidden = matches.length > 0;
      document.getElementById('skill-count').textContent = `显示 ${visible.length} / ${matches.length}`;
      const browseButton = document.getElementById('skills-browse-all');
      if (browseButton) {
        browseButton.setAttribute('aria-expanded', String(showAllSkills));
        browseButton.innerHTML = showAllSkills
          ? '收起完整目录 <span aria-hidden="true">↑</span>'
          : '探索全部 Skills <span aria-hidden="true">→</span>';
      }
      const selected = visible.find(skill=>skill.id===selectedId) || matches.find(skill=>skill.id===selectedId) || visible[0];
      if (selected) updatePanel(selected);
    };
    document.getElementById('skills-browse-all')?.addEventListener('click', () => {
      showAllSkills = !showAllSkills;
      render();
    });
    document.querySelectorAll('.skill-category-tab').forEach(button => button.addEventListener('click', event => {
      event.stopImmediatePropagation();
      page.dataset.skillCategory = button.dataset.category;
      document.querySelectorAll('.skill-category-tab').forEach(item => item.classList.toggle('is-active', item === button));
      render();
    }, { capture: true }));
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
      document.getElementById('skill-search').value=''; document.getElementById('skill-status').value='all'; page.dataset.skillCategory='all'; render();
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
    document.querySelector('#skill-clear')?.addEventListener('click',()=>{ page.dataset.skillCategory='all'; });
    const accountNotice=document.createElement('div'); accountNotice.id='skills-account-notice'; accountNotice.className='skills-toast'; accountNotice.setAttribute('role','status'); accountNotice.hidden=true; page.append(accountNotice);
    render();
  };
  window.FreeLLMReferenceShell = { mount: boot };
  window.addEventListener('freellm:page-mount', boot);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
