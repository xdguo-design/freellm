
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
      skills: ['搜索 Skills、能力或使用场景…', 'Skill Lab', '/skills/lab/'],
      tools: ['搜索工具、功能、场景…', '提交资源', '/submit/'],
      workflow: ['搜索工作流、Skill、交付结果…', '浏览 Skills', '/skills/'],
      logs: ['搜索今天的新增、恢复或下线记录…', '查看资源', '/'],
      about: ['搜索 FreeLLM 的模型、工具和 Skills…', '提交资源', '/submit/']
    }[section] || ['搜索 FreeLLM…', '查看资源', '/'];

    const topbar = document.createElement('div');
    topbar.className = 'ref-topbar';
    topbar.setAttribute('role', 'search');
    const localeLabel = document.documentElement.lang === 'en' ? '中文' : 'EN';
    topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true">⌕</span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions"><button class="ref-locale" type="button" data-reference-locale-toggle aria-label="切换语言">' + localeLabel + '</button><button class="ref-bell" type="button" aria-label="更新提醒">♧</button><a href="/about/">帮助</a><a class="primary" href="' + copy[2] + '">' + copy[1] + '</a></div>';
    const rail = body.querySelector(':scope > .fl-site-rail');
    if (rail) rail.insertAdjacentElement('afterend', topbar);
    else body.prepend(topbar);

    const localeButton = topbar.querySelector('.ref-locale');
    localeButton?.addEventListener('click', () => {
      const legacyToggle = document.querySelector('[data-locale-toggle]');
      if (legacyToggle) legacyToggle.click();
    });

    const topInput = topbar.querySelector('input');
    const targets = ['#catalog-search','#model-library-search','#tool-search','#skill-search','#skill-library-search'].map(s => document.querySelector(s)).filter(Boolean);
    const target = targets[0];
    const sync = () => {
      const value = topInput.value.trim();
      if (target) {
        target.value = value;
        target.dispatchEvent(new Event('input', { bubbles: true }));
        target.dispatchEvent(new Event('change', { bubbles: true }));
        if (target.offsetParent !== null) {
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
          target.focus({ preventScroll: true });
        }
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
      row.innerHTML = items.map((x, i) => '<article class="ref-stat"><span class="ref-stat-icon">' + x[0] + '</span><div><strong>' + x[1] + '</strong><span>' + x[2] + '</span></div></article>').join('');
      return row;
    };

    if (section === 'tools') {
      const hero = document.querySelector('.tools-hero');
      if (hero && !document.querySelector('.ref-stat-row')) {
        const total = (document.querySelector('#tool-total')?.textContent || '291').trim();
        hero.insertAdjacentElement('afterend', makeStats([
          ['◆','10','今日推荐工具'],['✦','28','限时免费'],['◎','312','国内可用'],['↗','286','国际入口'],['✓',total,'已验证工具']
        ]));
      }
    }
    if (section === 'workflow') {
      const hero = document.querySelector('.lab-hero');
      if (hero && !document.querySelector('.ref-stat-row')) {
        hero.insertAdjacentElement('afterend', makeStats([
          ['◆','06','已发布模板'],['●','TOP 10','热门工作流'],['▣','18','今日更新'],['▱','92%','可直接复用']
        ]));
      }
    }
    if (section === 'about') {
      const header = body.querySelector(':scope > header');
      if (header && !document.querySelector('.ref-value-row')) {
        const row = document.createElement('section');
        row.className = 'ref-value-row';
        row.innerHTML = '<article class="ref-value"><i>♟</i><div><strong>开放共享</strong><span>打破信息壁垒，共享优质资源</span></div></article><article class="ref-value"><i>✓</i><div><strong>真实可靠</strong><span>人工验证与社区共建，确保可用可信</span></div></article><article class="ref-value"><i>♥</i><div><strong>社区共建</strong><span>汇聚全球开发者与 AI 爱好者的力量</span></div></article>';
        header.insertAdjacentElement('afterend', row);
      }
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();


/* Reference fidelity pass 2: page-specific structures derived from the supplied boards. */
(() => {
  const boot = () => {
    const body = document.body;
    if (!body || body.dataset.referenceFidelityV2 === '1') return;
    body.dataset.referenceFidelityV2 = '1';
    const section = body.dataset.flSection || '';
    const $ = (s, r = document) => r.querySelector(s);
    const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
    const clean = value => String(value || '').replace(/\s+/g, ' ').trim();
    const safe = value => clean(value).replace(/[<>&"]/g,'');

    if (section === 'home') {
      const hero = $('.catalog-hero'), copy = $('.catalog-hero-copy', hero || document);
      if (hero && copy) {
        const badge = $('.hero-badge', copy), title = $('h1', copy), lead = $('.hero-copy', copy);
        if (badge) badge.innerHTML = 'FreeLLM';
        if (title) title.innerHTML = '<span class="ref-kicker">FreeLLM</span>今天发现，<br>更好的 <em>AI 资源</em>';
        if (lead) lead.textContent = '汇聚全球优质的 AI 模型、工具与应用，让每个人都能轻松使用先进的 AI。';
        if (!$('.ref-home-actions', copy)) {
          const actions = document.createElement('div');
          actions.className = 'ref-home-actions';
          actions.innerHTML = '<a href="#categories">开始探索 <span aria-hidden="true">→</span></a><a href="/about/"><span aria-hidden="true">▶</span> 了解 FreeLLM</a>';
          lead?.insertAdjacentElement('afterend', actions);
        }
      }
      const latest = $('.today-latest');
      if (latest) latest.classList.add('ref-home-stats');
      const featured = $('.featured-section');
      if (featured) {
        const heading = $('#featured-title', featured), eyebrow = $('.eyebrow', featured);
        if (heading) heading.textContent = '全新资源';
        if (eyebrow) eyebrow.textContent = 'NEW RESOURCES';
      }
      if (featured && !$('.ref-home-news')) {
        const cards = $$('.featured-card').slice(0,4), offer = $('.offer-card,.resource-card');
        const pool = offer && !cards.includes(offer) ? [...cards, offer] : cards;
        const news = document.createElement('section');
        news.className = 'ref-home-news';
        news.innerHTML = '<div class="ref-home-news-head"><h2>最新动态</h2><a href="/logs/">查看全部 →</a></div><div class="ref-home-news-grid">' +
          pool.slice(0,5).map(card => '<article class="ref-home-news-card"><strong>' + safe($('h2,h3', card)?.textContent || 'AI 资源') + '</strong><p>' + safe($('p', card)?.textContent || $('small', card)?.textContent || '最近核验的 AI 资源').slice(0,58) + '</p></article>').join('') + '</div>';
        featured.insertAdjacentElement('beforebegin', news);
      }
      if (featured && !$('.ref-student-banner')) {
        const banner = document.createElement('section');
        banner.className = 'ref-student-banner';
        banner.innerHTML = '<div><strong>学生专属福利</strong><p>通过学生身份与教育优惠入口，集中查看适合学习、研究与开发的 AI 资源。</p></div><a href="#categories" data-filter="student">查看学生优惠 →</a>';
        featured.insertAdjacentElement('afterend', banner);
      }
    }

    if (section === 'tools') {
      const toolbar = $('.tools-toolbar'), grid = $('#tool-grid');
      if (toolbar && grid && !$('.ref-tool-feature')) {
        const feature = document.createElement('section');
        feature.className = 'ref-tool-feature';
        feature.innerHTML = '<div class="ref-tool-feature-head"><h2>推荐工具</h2><span>从当前工具目录中优先展示常用入口</span></div><div class="ref-tool-feature-grid"></div>';
        const target = $('.ref-tool-feature-grid', feature);
        $$('.tool-card', grid).slice(0,3).forEach(card => target.appendChild(card.cloneNode(true)));
        toolbar.insertAdjacentElement('beforebegin', feature);
      }
    }

    if (section === 'skills') {
      const hero = $('.skills-hero');
      if (hero && !$('.ref-skill-stats')) {
        const cards = $$('.skill-card'), verified = cards.filter(card => card.dataset.status === 'verified').length;
        const categories = new Set(cards.map(card => card.dataset.category).filter(Boolean)).size;
        const stats = document.createElement('section');
        stats.className = 'ref-stat-row ref-skill-stats';
        stats.innerHTML = [['◆',cards.length || 68,'已收录 Skills'],['✓',verified || 0,'已核验来源'],['▦',categories || 0,'能力分类'],['⌘','06','可复用工作流']].map(x => '<article class="ref-stat"><span class="ref-stat-icon">' + x[0] + '</span><div><strong>' + x[1] + '</strong><span>' + x[2] + '</span></div></article>').join('');
        hero.insertAdjacentElement('afterend', stats);
      }
      const toolbar = $('.skills-toolbar'), first = $('.skill-card');
      if (toolbar && first && !$('.ref-skill-feature')) {
        const compat = $$('.skill-chip', first).map(x => clean(x.textContent)).slice(0,4);
        const feature = document.createElement('section');
        feature.className = 'ref-skill-feature';
        feature.innerHTML = '<article class="ref-skill-feature-main"><span class="eyebrow">FEATURED SKILL / 重点能力</span><h2>' + safe($('h2', first)?.textContent || 'Skill') + '</h2><p>' + safe($('.skill-description-zh', first)?.textContent || $('p', first)?.textContent).slice(0,220) + '</p></article><aside class="ref-skill-feature-side"><strong>适用环境</strong>' + (compat.length ? compat : ['查看详情']).map(x => '<span>' + safe(x) + '</span>').join('') + '<span>来源与验证记录可追溯</span></aside>';
        toolbar.insertAdjacentElement('beforebegin', feature);
      }
    }

    if (section === 'workflow') {
      const grid = $('.workflow-grid'), sectionEl = grid?.closest('section'), first = $('.workflow-card', grid || document);
      if (grid && sectionEl && first && !$('.ref-workflow-feature')) {
        const feature = document.createElement('section');
        feature.className = 'ref-workflow-feature';
        feature.innerHTML = '<div class="ref-workflow-feature-main"><div class="ref-workflow-copy"><span class="badge">★ 精选工作流</span><h2>' + safe($('h2', first)?.textContent) + '</h2><p>' + safe($('p', first)?.textContent) + '</p><div class="meta"><span>' + safe($('.recipe-count', first)?.textContent || '可复用步骤') + '</span><span>模型 + 工具 + Skills</span></div><button type="button" data-open-featured-workflow>查看工作流 →</button></div><div class="ref-workflow-diagram" aria-label="工作流示意"><span class="ref-flow-node n1"><b>触发器</b>输入任务</span><span class="ref-flow-node n2"><b>内容分析</b>提取要点</span><span class="ref-flow-node n3"><b>内容改写</b>多风格生成</span><span class="ref-flow-node n4"><b>格式输出</b>适配平台</span><span class="ref-flow-node n5"><b>发布建议</b>标题 / 标签</span><i class="ref-flow-line l1"></i><i class="ref-flow-line l2"></i><i class="ref-flow-line l3"></i><i class="ref-flow-line l4"></i><i class="ref-flow-line l5"></i></div></div><aside class="ref-workflow-side"><div class="ref-workflow-side-card"><h3>推荐搭配模型</h3><span>按任务选择长上下文模型</span><span>按成本选择高性价比模型</span><span><a href="/models/">浏览模型库 →</a></span></div><div class="ref-workflow-side-card"><h3>推荐 Skills</h3><span>内容改写</span><span>图像生成</span><span>格式输出</span><span>内容审核</span></div></aside>';
        sectionEl.insertAdjacentElement('beforebegin', feature);
        const heading = $('.workflow-section-head h2', sectionEl);
        if (heading) heading.textContent = '探索工作流模板';
        $('[data-open-featured-workflow]', feature)?.addEventListener('click', () => $('.workflow-details', first)?.click());
      }
    }

    if (section === 'logs') {
      const hero = $('.log-hero'), title = $('.log-hero h1 [lang="zh-CN"]');
      if (title) title.textContent = '今日更新，发现 AI 新可能';
      if (hero && !$('.ref-log-stats')) {
        const source = [...$$('.log-stat-card').slice(0,4), ...$$('.log-snapshot-card').slice(0,1)].slice(0,5);
        const stats = document.createElement('section');
        stats.className = 'ref-stat-row ref-log-stats';
        stats.innerHTML = source.map((card,index) => '<article class="ref-stat"><span class="ref-stat-icon">' + ['＋','✓','−','!','◆'][index] + '</span><div><strong>' + safe($('strong', card)?.textContent || '—') + '</strong><span>' + safe($('.log-stat-label,span', card)?.textContent || (index === 4 ? '模型记录' : '今日变化')).slice(0,20) + '</span></div></article>').join('');
        hero.insertAdjacentElement('afterend', stats);
      }
    }

    if (section === 'about') {
      const values = $('.ref-value-row');
      if (values && !$('.ref-about-statement')) {
        const statement = document.createElement('section');
        statement.className = 'ref-about-statement';
        statement.textContent = '“我们相信，AI 的价值不只属于少数人，而应属于每一个对未来充满好奇的人。”';
        values.insertAdjacentElement('afterend', statement);
      }
      const main = $('body[data-fl-section="about"] > main'), statement = $('.ref-about-statement');
      if (main && statement && !$('.ref-about-process')) {
        const process = document.createElement('section');
        process.className = 'ref-about-process';
        process.innerHTML = '<div class="ref-about-process-head"><h2>我们在做什么</h2><span>从发现到使用，构建更好的 AI 资源生态</span></div><div class="ref-about-process-grid"><article class="ref-about-step"><b>01</b><strong>发现资源</strong><p>在全球范围内发现有价值的 AI 模型、工具和应用，关注创新与实用性。</p></article><article class="ref-about-step"><b>02</b><strong>验证可用性</strong><p>通过人工检查与来源核验，确认资源的可用性、条件与稳定性。</p></article><article class="ref-about-step"><b>03</b><strong>结构化整理</strong><p>按能力、地区与免费机制整理信息，提供清晰的导航和使用指引。</p></article><article class="ref-about-step"><b>04</b><strong>持续更新</strong><p>跟踪 AI 领域最新动态，持续收录、核验和更新优质资源。</p></article></div>';
        statement.insertAdjacentElement('afterend', process);
      }
    }

    if (section === 'models') {
      const art = $('.ml-hero-art');
      if (art && !$('.ml-hero-rings', art)) {
        const rings = document.createElement('span');
        rings.className = 'ml-hero-rings';
        rings.setAttribute('aria-hidden','true');
        rings.innerHTML = '<i class="ml-ring r1"></i><i class="ml-ring r2"></i><i class="ml-ring r3"></i>';
        art.prepend(rings);
        const person = document.createElement('span');
        person.className = 'ml-hero-person';
        person.setAttribute('aria-hidden','true');
        art.appendChild(person);
        ['g1','g2','g3','g4','g5'].forEach(name => {
          const block = document.createElement('span');
          block.className = 'ml-glass-block ' + name;
          block.setAttribute('aria-hidden','true');
          art.appendChild(block);
        });
      }
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once:true });
  else boot();
})();
