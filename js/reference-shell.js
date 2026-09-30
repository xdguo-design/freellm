
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
      workflow: ['搜索工作流、Skill、交付结果…', '浏览 Skills', '/skills/'],
      logs: ['搜索今天的新增、恢复或下线记录…', '查看资源', '/'],
      about: ['搜索 FreeLLM 的模型、工具和 Skills…', '提交资源', '/submit/']
    }[section] || ['搜索 FreeLLM…', '查看资源', '/'];

    const topbar = document.createElement('div');
    topbar.className = 'ref-topbar';
    topbar.setAttribute('role', 'search');
    const localeLabel = document.documentElement.lang === 'en' ? '中文' : 'EN';
if (section === 'home') {
      topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true">⌕</span><input type="search" aria-label="全站搜索" placeholder="搜索模型、工具、Skills 或任何你感兴趣的 AI 资源..."><kbd>⌘ K</kbd></label><div class="ref-top-actions"><button class="ref-bell" type="button" aria-label="更新提醒">♧</button><button class="prototype-login" type="button">登录</button><button class="prototype-register" type="button">注册</button></div>';
    } else {
      const actions = section === 'skills'
        ? '<button class="ref-bell" type="button" aria-label="更新提醒" data-reference-notifications>♧</button><button class="ref-auth-button" type="button" data-auth-action="login">登录</button><button class="ref-auth-button primary" type="button" data-auth-action="register">注册</button>'
        : '<button class="ref-locale" type="button" data-reference-locale-toggle aria-label="切换语言">' + localeLabel + '</button><button class="ref-bell" type="button" aria-label="更新提醒">♧</button><a href="/about/">帮助</a><a class="primary" href="' + copy[2] + '">' + copy[1] + '</a>';
      topbar.innerHTML = '<label class="ref-search"><span aria-hidden="true">⌕</span><input type="search" aria-label="全站搜索" placeholder="' + copy[0] + '"><kbd>⌘ K</kbd></label><div class="ref-top-actions">' + actions + '</div>';
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
      const visible = filtered();
      grid.innerHTML = visible.map(card).join('');
      document.getElementById('skill-empty').hidden = visible.length > 0;
      document.getElementById('skill-count').textContent = `显示 ${visible.length} / ${skills.length}`;
      const selected = visible.find(skill=>skill.id===selectedId) || skills.find(skill=>skill.id===selectedId) || visible[0];
      if (selected) updatePanel(selected);
    };
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
