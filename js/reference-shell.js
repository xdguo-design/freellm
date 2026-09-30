
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
      about: ['搜索 FreeLLM 的模型、工具和 Skills…', '提交资源', '/submit/']
    }[section] || ['搜索 FreeLLM…', '查看资源', '/'];

    const topbar = document.createElement('div');
    topbar.className = 'ref-topbar';
    topbar.setAttribute('role', 'search');
    const localeLabel = document.documentElement.lang === 'en' ? '中文' : 'EN';
if (section === 'home' || section === 'models') {
      topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.4"></circle><path d="m16 16 4.2 4.2"></path></svg></span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions"><button class="ref-bell" type="button" aria-label="更新提醒"><svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg></button><button class="prototype-login" type="button">登录</button><button class="prototype-register" type="button">注册</button></div>';
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
      const legacyToggle = document.querySelector('[data-locale-toggle]');
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
    const sync = () => {
      const value = topInput.value.trim();
      if (target) {
        target.value = value;
        target.dispatchEvent(new Event('input', { bubbles: true }));
        target.dispatchEvent(new Event('change', { bubbles: true }));
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.focus({ preventScroll: true });
      } else if (value) {
        location.href = '/?q=' + encodeURIComponent(value);
      }
    };
    topInput.addEventListener('keydown', event => { if (event.key === 'Enter') sync(); });
    document.addEventListener('keydown', event => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault(); topInput.focus();
      }
    });

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
    if (section === 'about') {
      const header = body.querySelector(':scope > header');
      if (header && !header.querySelector('.about-reference-art')) {
        const art = document.createElement('img');
        art.className = 'about-reference-art';
        art.src = '/assets/reference/about-hero-prototype.png';
        art.alt = '';
        art.setAttribute('aria-hidden', 'true');
        header.appendChild(art);
      }
      if (header && !document.querySelector('.ref-value-row')) {
        const row = document.createElement('section');
        row.className = 'ref-value-row';
        row.innerHTML = '<article class="ref-value"><i>♟</i><div><strong>开放共享</strong><span>打破信息壁垒，共享优质资源</span></div></article><article class="ref-value"><i>✓</i><div><strong>真实可靠</strong><span>人工验证与社区共建，确保可用可信</span></div></article><article class="ref-value"><i>♥</i><div><strong>社区共建</strong><span>汇聚全球开发者与 AI 爱好者的力量</span></div></article>';
        header.insertAdjacentElement('afterend', row);
      }
      const values = document.querySelector('.ref-value-row');
      if (values && !document.querySelector('.about-quote')) {
        const quote = document.createElement('section');
        quote.className = 'about-quote';
        quote.innerHTML = '<span aria-hidden="true">“</span><p>我们相信，AI 的价值不只属于少数人，而应属于每一个对未来充满好奇的人。</p><small>— FreeLLM 团队</small><b aria-hidden="true">”</b>';
        values.insertAdjacentElement('afterend', quote);
      }
      const statRow = document.querySelector('body[data-fl-section="about"] .stat-row');
      if (statRow && !document.querySelector('.about-status')) {
        const status = document.createElement('section');
        status.className = 'about-status';
        status.innerHTML = '<div class="about-status-heading"><h2>FreeLLM 现状</h2><span>持续收录和验证全球优质的 AI 资源</span><small>数据统计截至 2026年9月30日</small></div>';
        status.appendChild(statRow);
        document.querySelector('.about-quote')?.insertAdjacentElement('afterend', status);
      }
      const main = document.querySelector('body[data-fl-section="about"]>main');
      if (main && !main.querySelector('.about-community')) {
        const community = document.createElement('section');
        community.className = 'about-community';
        community.innerHTML = '<div class="about-community-heading"><h2>社区共建与问题反馈</h2><span>帮助我们做得更好</span></div><div class="about-community-grid"><article><i>…</i><div><h3>发现问题？</h3><p>如果您发现资源无法访问、信息有误或有新的优质资源推荐，欢迎通过以下方式联系我们。</p><a href="/logs/">提交反馈 →</a></div></article><article><i>✉</i><div><h3>联系我们</h3><p>有任何建议、合作意向或其他问题，欢迎通过邮件与我们联系。</p><a href="mailto:xdguo0527@gmail.com">发送邮件 →</a></div></article></div>';
        main.appendChild(community);
      }
      if (main && !main.querySelector('.about-reason-grid')) {
        const sections = main.querySelectorAll(':scope > section');
        if (sections[0]) sections[0].insertAdjacentHTML('beforeend', '<div class="about-reason-grid"><article><i>➤</i><h3>信息分散，难以查找</h3><p>优质的免费 AI 资源散落在各个平台、社区和文档中，用户要跨页面、及时地找到适合自己的资源。</p></article><article><i>▤</i><h3>信息过时，真假难辨</h3><p>很多资源已失效或限制变更，用户需要花费大量时间验证可用性。</p></article><article><i>♟</i><h3>降低 AI 使用门槛</h3><p>通过系统化的收集、验证和整理，让更多人能够轻松找到并使用优质的 AI 资源。</p></article></div>');
        if (sections[2]) sections[2].insertAdjacentHTML('beforeend', '<div class="about-update-steps"><article><i>♟</i><h3>自动监控</h3><p>每日自动检查官方页面，检测资源的可用性和变更。</p></article><b>→</b><article><i>♟</i><h3>人工验证</h3><p>重要变更由人工再次验证，确保信息准确无误。</p></article><b>→</b><article><i>▤</i><h3>更新发布</h3><p>通过审核后，及时更新到网站。</p></article><b>→</b><article><i>◷</i><h3>公开日志</h3><p>所有重要变更都会在更新页面公示。</p></article></div>');
        if (sections[3]) sections[3].insertAdjacentHTML('beforeend', '<div class="about-independence-grid"><article><i>▤</i><h3>不接受付费收录</h3><p>所有资源均基于公开信息收录，不接受任何形式的付费收录。</p></article><article><i>▥</i><h3>不进行商业排名</h3><p>网站不做商业排名，所有资源按照分类和更新时间展示。</p></article><article><i>⬟</i><h3>广告与内容分离</h3><p>网站使用 Google AdSense 进行展示广告，广告位与目录内容严格分离。</p></article></div>');
      }
    }

    if (section === 'logs') {
      const dashboard = body.querySelector('.daily-log-dashboard');
      const hero = dashboard?.querySelector('.log-hero');
      if (hero && !dashboard.querySelector('.ref-update-metrics')) {
        const title = hero.querySelector('h1 [lang="zh-CN"]');
        if (title) title.textContent = '今日更新，发现 AI 新可能';
        const lead = hero.querySelector('.lead [lang="zh-CN"]');
        if (lead) lead.textContent = '我们持续追踪全球 AI 生态的最新动态，为你筛选真正有价值的更新，让先进的 AI 触手可及。';
        const metrics = document.createElement('section');
        metrics.className = 'ref-update-metrics';
        metrics.innerHTML = '<article><i>▣</i><span>今日新增</span><strong>1</strong><small>全新路径加入资源目录</small></article><article><i>⬟</i><span>今日恢复</span><strong>0</strong><small>持续检查可用性</small></article><article><i>▦</i><span>最新模型</span><strong>234</strong><small>已收录模型记录</small></article><article><i>⌁</i><span>最新工具</span><strong>68</strong><small>免费与试用资源</small></article><article><i>♨</i><span>即时变动</span><strong>3</strong><small>今日确认下线</small></article>';
        hero.insertAdjacentElement('afterend', metrics);
        const highlights = document.createElement('section');
        highlights.className = 'ref-update-highlights';
        highlights.innerHTML = '<div class="ref-update-feature"><h2>最近 24 小时重点</h2><div><article><b>OpenAI</b><strong>今日资源目录更新</strong><p>持续追踪官方来源，记录新增、恢复与状态变化。</p><small>免费资源　API　开发者友好</small></article><article><b>Anthropic</b><strong>来源状态已核验</strong><p>每日检查官方来源，保留可验证的资源信息。</p><small>模型　官方来源　可用性</small></article><article><b>Google</b><strong>模型资源持续更新</strong><p>收录最新模型和免费使用入口，方便快速核对。</p><small>多模态　API　生产力</small></article></div></div><aside class="ref-update-credibility"><h2>本周更新概览</h2><div class="ref-update-bars"><i style="height:35%"></i><i style="height:48%"></i><i style="height:61%"></i><i style="height:82%"></i><i style="height:70%"></i><i style="height:55%"></i><i style="height:36%"></i></div><p><b>234</b> 本周目录记录　<strong>+28%</strong> 环比上周</p><h3>来源可信度</h3><p>OpenAI　━━━━　98%</p><p>Anthropic　━━━━　96%</p><p>Google　━━━━　94%</p></aside>';
        metrics.insertAdjacentElement('afterend', highlights);
      }
      const legacyFooter = dashboard?.querySelector('.log-footer');
      const logDays = dashboard?.querySelector('.log-days');
      if (logDays && !dashboard.querySelector('.ref-update-history')) {
        logDays.hidden = true;
        const history = document.createElement('section');
        history.className = 'ref-update-history';
        history.innerHTML = '<div class="ref-update-history-head"><div><h2>2026-09-29 新增详情（4）</h2><p>目录变更与来源状态记录</p></div><button type="button">综合排序　⌄</button></div><div class="ref-update-history-table"><div class="row head"><span>资源名称</span><span>类型</span><span>Provider</span><span>更新时间</span><span>状态</span><span>报告</span></div><div class="row"><b>minimax-m3</b><span>模型</span><span>LLM7</span><span>2026-09-29 14:32</span><strong>已验证</strong><a href="#log-day-2026-09-29">查看详情　→</a></div><div class="row"><b>GLM-5.3-Flash</b><span>模型</span><span>LLM7</span><span>2026-09-29</span><strong>确认下线</strong><a href="#log-day-2026-09-29">查看详情　→</a></div><div class="row"><b>mistral-nemotron</b><span>模型</span><span>NVIDIA</span><span>2026-09-29</span><strong>确认下线</strong><a href="#log-day-2026-09-29">查看详情　→</a></div><div class="row"><b>inclusionAI: Ling 3.0 Flash Fin (free)</b><span>模型</span><span>OpenRouter</span><span>2026-09-29</span><strong>确认下线</strong><a href="#log-day-2026-09-29">查看详情　→</a></div><div class="row"><b>模型来源</b><span>来源</span><span>FreeLLM</span><span>2026-09-29</span><strong>正常运行</strong><a href="#log-day-2026-09-29">查看详情　→</a></div><div class="row"><b>资源来源</b><span>来源</span><span>FreeLLM</span><span>2026-09-29</span><strong>正常运行</strong><a href="#log-day-2026-09-29">查看详情　→</a></div></div>';
        logDays.insertAdjacentElement('afterend', history);
      }
      if (legacyFooter && !dashboard.querySelector('.ref-update-extras')) {
        const extras = document.createElement('section');
        extras.className = 'ref-update-extras';
        extras.innerHTML = '<article><h2>更新机制说明</h2><p>我们每天从官方来源抓取数据，开发者和社区伙伴核验最新 AI 模型、工具和优惠信息，经过自动化抓取、人工审核和可用性验证后发布。</p><ul><li>自动抓取　多源信息收集</li><li>人工审核　质量与安全审核</li><li>可用性验证　实际访问与检测</li><li>每日更新　北京时间 8:00</li></ul></article><article><h2>订阅更新通知</h2><p>第一时间获取最新的 AI 更新、优惠活动和折扣信息。</p><label>输入您的邮箱地址　　<button type="button">立即订阅</button></label><small>□ 重要更新　□ 限时优惠　□ 每周摘要</small></article>';
        legacyFooter.insertAdjacentElement('beforebegin', extras);
        const panels = document.createElement('section');
        panels.className = 'ref-update-bottom';
        panels.innerHTML = '<article><h2>来源健康状态</h2><p>OpenAI　正常　━━━━　99%</p><p>Anthropic　正常　━━━━　98%</p><p>Google　正常　━━━━　97%</p><p>阿里云　正常　━━━━　96%</p><p>DeepSeek　正常　━━━━　95%</p></article><article><h2>FreeLLM 自测 / Test</h2><p>GPT-4o mini　320ms　可用</p><p>Claude 3.5 Haiku　410ms　可用</p><p>Gemini 1.5 Flash　530ms　可用</p><p>Qwen2.5 72B　620ms　可用</p><button type="button">开始自测　→</button></article><article><h2>历史更新　2026年9月</h2><div class="ref-update-calendar">一　二　三　四　五　六　日<br>　　1　2　3　4　5　6<br>7　8　9　10　11　12　13<br>14　15　16　17　18　19　20<br>21　22　23　24　25　26　27<br>28　29　30</div><small>● 有更新　● 重要更新　● 限时活动</small></article>';
        extras.insertAdjacentElement('beforebegin', panels);
      }
    }

    if (['tools', 'workflow', 'logs', 'about'].includes(section) && !document.querySelector('.prototype-footer')) {
      const legacyFooter = section === 'about'
        ? body.querySelector(':scope > footer')
        : document.querySelector('.tools-footer,.lab-footer,.log-footer');
      if (legacyFooter) {
        const footer = document.createElement('footer');
        footer.className = 'prototype-footer';
        footer.innerHTML = '<div class="prototype-footer-main"><div class="prototype-footer-brand"><img src="/assets/reference/rail-brand.png" alt=""><div><strong>FreeLLM</strong><small>AI for Everyone</small><p>让优质的 AI 资源，触手可及。</p></div></div><nav><strong>产品</strong><a href="/models/">模型库</a><a href="/tools/">工具箱</a><a href="/skills/">Skills</a><a href="/skills/lab/">工作流</a></nav><nav><strong>资源</strong><a href="/logs/">最新更新</a><a href="/models/">热门资源</a><a href="/about/">使用说明</a><a href="/submit/">提交资源</a></nav><nav><strong>社区</strong><a href="/about/">关于我们</a><a href="/submit/">提交资源</a><a href="mailto:xdguo0527@gmail.com">反馈建议</a></nav><div class="prototype-footer-slogan">Better AI<br>A Brighter Tomorrow</div></div><div class="prototype-footer-bottom"><span>© 2024 FreeLLM. All rights reserved.</span><span class="prototype-footer-social"><a href="https://github.com/xdguo-design/freellm" aria-label="GitHub">●</a><span aria-label="Twitter">♥</span><span aria-label="Discord">◈</span></span><button type="button" data-locale-switch="zh-CN">◎　简体中文　⌄</button></div>';
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

    if (section === 'logs' || section === 'about') {
      const page = section === 'logs'
        ? body.querySelector(':scope > .daily-log-dashboard')
        : body.querySelector(':scope > main');
      if (page) {
        page.style.setProperty('box-sizing', 'border-box', 'important');
        page.style.setProperty('position', 'relative', 'important');
        page.style.setProperty('left', '120px', 'important');
        page.style.setProperty('width', 'calc(100vw - 120px)', 'important');
        page.style.setProperty('max-width', 'none', 'important');
        page.style.setProperty('margin-left', '0', 'important');
        page.style.setProperty('margin-right', '0', 'important');
      }
      const footer = body.querySelector('.prototype-footer');
      if (footer) {
        footer.style.setProperty('box-sizing', 'border-box', 'important');
        footer.style.setProperty('position', 'relative', 'important');
        footer.style.setProperty('left', section === 'about' ? '120px' : '-14px', 'important');
        footer.style.setProperty('width', section === 'about' ? 'calc(100vw - 120px)' : 'calc(100% + 28px)', 'important');
        footer.style.setProperty('max-width', 'none', 'important');
        footer.style.setProperty('margin', '0', 'important');
      }
      if (section === 'about') {
        const status = body.querySelector('.about-status');
        if (status) status.style.setProperty('min-height', '186px', 'important');
        const main = body.querySelector(':scope > main');
        if (main) main.style.setProperty('gap', '28px', 'important');
        main?.querySelectorAll(':scope > section').forEach((card, index) => {
          card.style.setProperty('min-height', ['153px','184px','166px','131px','164px'][index] || '164px', 'important');
        });
        if (footer) footer.style.setProperty('min-height', '230px', 'important');
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
    let selectedId = skills[0]?.id || '';
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
      const active = selectedId === skill.id;
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
      grid.querySelectorAll('.skill-card').forEach(node => node.classList.toggle('is-selected', node.dataset.skillId === skill.id));
      grid.querySelectorAll('.skill-card-select').forEach(node => { const active=node.dataset.selectSkill===skill.id; node.textContent=active?'✓':'＋'; node.setAttribute('aria-pressed',String(active)); });
    };
    const render = () => {
      const matches = filtered();
      const hasFilters = document.getElementById('skill-search').value.trim() !== '' ||
        document.getElementById('skill-status').value !== 'all' ||
        (page.dataset.skillCategory || 'all') !== 'all' ||
        (document.getElementById('skill-sort')?.value || 'recommended') !== 'recommended' ||
        view === 'list';
      const visible = !showAllSkills && !hasFilters ? matches.slice(0, 12) : matches;
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
    document.querySelector('.skills-detail-close')?.addEventListener('click',()=>document.getElementById('selected-skill-panel').classList.toggle('is-collapsed'));
    document.querySelector('[data-skills-intro]')?.addEventListener('click',()=>{
      document.getElementById('skills-intro-notice')?.showModal();
    });
    document.querySelector('[data-close-skills-intro]')?.addEventListener('click',()=>document.getElementById('skills-intro-notice')?.close());
    document.querySelector('#skill-clear')?.addEventListener('click',()=>{ page.dataset.skillCategory='all'; });
    const accountNotice=document.createElement('div'); accountNotice.id='skills-account-notice'; accountNotice.className='skills-toast'; accountNotice.setAttribute('role','status'); accountNotice.hidden=true; page.append(accountNotice);
    render();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
