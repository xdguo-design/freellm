
(() => {
  const run = () => {
    const body=document.body;
    if(!body || body.dataset.prototypeCoreV4==='1') return;
    body.dataset.prototypeCoreV4='1';
    const section=body.dataset.flSection||'';
    const $=(s,r=document)=>r.querySelector(s);
    const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
    const text=v=>String(v||'').replace(/\s+/g,' ').trim();
    const esc=v=>text(v).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

    if(section==='skills'){
      const hero=$('.skills-hero');
      const title=$('h1',hero||document);
      if(title) title.textContent='Skills';
      const lead=$('.lead',hero||document);
      if(lead) lead.textContent='发现和使用可复用的 AI 技能，让复杂任务变得简单。';

      const toolbar=$('.skills-toolbar');
      if(toolbar && !$('.pf-skill-collections')){
        const collections=document.createElement('section');
        collections.className='pf-skill-collections';
        collections.innerHTML=[
          ['✦','工作效率提升包','7 个 Skills','提升日常工作效率，从文档处理到会议总结'],
          ['⌁','学习与研究合集','6 个 Skills','论文阅读、资料检索、知识整理一套完成'],
          ['▦','办公提效合集','8 个 Skills','Word、PPT、Excel 与数据处理常用能力'],
          ['✎','内容创作合集','7 个 Skills','写作、配图、排版与多平台发布']
        ].map(x=>'<article><i>'+x[0]+'</i><div><h3>'+x[1]+'</h3><strong>'+x[2]+'</strong><p>'+x[3]+'</p></div><b>→</b></article>').join('');
        toolbar.insertAdjacentElement('beforebegin',collections);
      }

      const grid=$('#skill-grid');
      if(grid && !$('.pf-skill-layout')){
        const layout=document.createElement('div');
        layout.className='pf-skill-layout';
        grid.parentNode.insertBefore(layout,grid);
        layout.appendChild(grid);
        const first=$('.skill-card',grid);
        const aside=document.createElement('aside');
        aside.className='pf-skill-detail';
        const chips=first ? $$('.skill-chip',first).slice(0,5).map(x=>'<span>'+esc(x.textContent)+'</span>').join('') : '';
        aside.innerHTML='<div class="pf-skill-detail-icon">✦</div><span class="pf-skill-detail-kicker">技能详情</span><h2>'+esc($('h2,h3',first||document)?.textContent||'选择一个 Skill')+'</h2><p>'+esc($('.skill-description-zh,p',first||document)?.textContent||'从左侧选择 Skill 查看来源、适用场景与验证信息。')+'</p><div class="pf-skill-detail-tags">'+chips+'</div><div class="pf-skill-detail-meta"><span>来源可追溯</span><span>持续核验</span></div><a href="'+esc($('.skill-source-link,.skill-details',first||document)?.getAttribute('href')||'#skill-grid')+'">查看 Skill →</a>';
        layout.appendChild(aside);
        $$('.skill-card',grid).forEach(card=>card.addEventListener('click',()=>{
          $('h2',aside).textContent=text($('h2,h3',card)?.textContent)||'Skill';
          $('p',aside).textContent=text($('.skill-description-zh,p',card)?.textContent);
          $('.pf-skill-detail-tags',aside).innerHTML=$$('.skill-chip',card).slice(0,5).map(x=>'<span>'+esc(x.textContent)+'</span>').join('');
        }));
      }
    }

    if(section==='tools'){
      const hero=$('.tools-hero');
      const h=$('h1',hero||document);
      if(h) h.textContent='发现更好的 AI 工具';
      const lead=$('.lead',hero||document);
      if(lead) lead.textContent='精选全球优质 AI 工具，覆盖开发、设计、写作、数据与效率场景。';
      const cards=$$('#tool-grid .tool-card');
      let stats=$('.ref-stat-row');
      if(stats){
        const count=cards.length;
        const txt=c=>text(c.textContent).toLowerCase();
        const free=cards.filter(c=>/free|免费|0元|0 元/.test(txt(c))).length;
        const cn=cards.filter(c=>/国内|中国|china/.test(txt(c))).length;
        const intl=cards.filter(c=>/国际|global|海外|国外/.test(txt(c))).length;
        const vals=[Math.min(10,count),free,cn,intl,count];
        $$('.ref-stat strong',stats).forEach((el,i)=>{if(vals[i]!==undefined) el.textContent=String(vals[i]);});
      }
      const feature=$('.ref-tool-feature');
      if(feature){
        const title=$('.ref-tool-feature-head h2',feature); if(title) title.textContent='今日推荐工具';
        const target=$('.ref-tool-feature-grid',feature);
        if(target && target.children.length<5){
          const existing=new Set($$('.tool-card',target).map(c=>c.id));
          cards.filter(c=>!existing.has(c.id)).slice(0,5-target.children.length).forEach(c=>target.appendChild(c.cloneNode(true)));
        }
      }
    }

    if(section==='workflow'){
      const cards=$$('.workflow-card');
      const hero=$('.lab-hero');
      let stats=$('.ref-workflow-stats');
      if(!stats) stats=$('.ref-stat-row');
      if(stats){
        const vals=[cards.length,Math.min(10,cards.length),0,cards.length ? '100%' : '—'];
        $$('.ref-stat strong',stats).forEach((el,i)=>{if(vals[i]!==undefined) el.textContent=String(vals[i]);});
        const labels=$$('.ref-stat span:not(.ref-stat-icon)',stats);
      }
      const heading=$('.workflow-section-head h2'); if(heading) heading.textContent='探索工作流模板';
    }

    if(section==='logs'){
      const hero=$('.log-hero');
      const h=$('h1 [lang="zh-CN"],h1',hero||document); if(h) h.textContent='今日更新，发现 AI 新可能';
      const lead=$('.lead,p',hero||document); if(lead) lead.textContent='每天追踪新增、恢复与下线变化，让免费 AI 资源保持新鲜、透明、可追溯。';
      fetch('/data/daily-log/2026-09-28.json').then(r=>r.ok?r.json():null).then(data=>{
        if(!data) return;
        const models=data.observed?.models||[];
        const events=data.events||[];
        const added=events.filter(x=>/new|add/i.test(x.eventType||'')).length;
        const restored=events.filter(x=>/restore|online/i.test(x.eventType||'')).length;
        const offline=events.filter(x=>/offline|remove|down/i.test(x.eventType||'')).length;
        let stats=$('.ref-log-stats');
        if(stats){
          const vals=[added,restored,offline,events.length,models.length];
          $$('.ref-stat strong',stats).forEach((el,i)=>{if(vals[i]!==undefined) el.textContent=String(vals[i]);});
        }
        if(!$('#log-day-2026-09-28')){
          const days=$('.log-days');
          if(days){
            const block=document.createElement('section');
            block.className='log-day pf-current-log-day'; block.id='log-day-2026-09-28';
            block.innerHTML='<div class="log-day-head"><div><span class="log-eyebrow">TODAY · 2026-09-28</span><h2>9 月 28 日更新</h2></div><span class="log-badge">'+models.length+' 个模型在线</span></div><p class="log-day-summary">'+(events.length?'今日记录 '+events.length+' 项资源状态变化。':'今日扫描未发现新增、恢复或下线变化；模型与资源来源检查正常。')+'</p><div class="log-health-grid"><article class="log-health-card"><strong>'+models.length+'</strong><span>在线模型</span></article><article class="log-health-card"><strong>'+(data.sourceHealth?.models?.status==='ok'?'正常':'需检查')+'</strong><span>模型来源</span></article><article class="log-health-card"><strong>'+(data.sourceHealth?.offers?.status==='ok'?'正常':'需检查')+'</strong><span>资源来源</span></article></div>';
            days.prepend(block);
          }
          const nav=$('.log-date-nav');
          if(nav){
            const a=document.createElement('a'); a.className='log-date-link'; a.href='#log-day-2026-09-28'; a.textContent='09-28'; nav.prepend(a);
          }
        }
      }).catch(()=>{});
    }

    if(section==='about'){
      const header=$('body[data-fl-section="about"] > header');
      const h=$('h1',header||document);
      if(h) h.innerHTML='让每个人都能平等地享受<br><em>AI 带来的改变</em>';
      const lead=$('.lead',header||document);
      if(lead) lead.textContent='FreeLLM 致力于发现、验证和整理全球优质的 AI 资源，让先进的 AI 技术更容易被每一个人看见、理解和使用。';
      const eyebrow=$('.ref-about-eyebrow',header||document); if(eyebrow) eyebrow.textContent='关于 FreeLLM';
    }
  };
  const boot=()=>setTimeout(run,0);
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
})();
