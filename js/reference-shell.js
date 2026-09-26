
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
    topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true">⌕</span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions"><button class="ref-bell" type="button" aria-label="更新提醒">♧</button><a href="/about/">帮助</a><a class="primary" href="' + copy[2] + '">' + copy[1] + '</a></div>';
    const rail = body.querySelector(':scope > .fl-site-rail');
    if (rail) rail.insertAdjacentElement('afterend', topbar);
    else body.prepend(topbar);

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
