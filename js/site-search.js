(() => {
  'use strict';
  const form = document.getElementById('site-search-form');
  const input = document.getElementById('site-search-input');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  const empty = document.getElementById('search-empty');
  if (!form || !input || !results) return;
  let records = [];
  let type = 'all';
  let fuse = null;
  const normal = value => String(value || '').normalize('NFKC').toLowerCase()
    .replace(/[_\/\-]+/g, ' ').replace(/\s+/g, ' ').trim();
  const escape = value => String(value || '').replace(/[&<>"']/g, ch => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[ch]));
  const read = async path => {
    const response = await fetch(path, {cache:'default'});
    if (!response.ok) throw new Error(path + ' returned ' + response.status);
    const data = await response.json();
    if (!Array.isArray(data)) throw new Error(path + ' is not a list');
    return data;
  };
  const short = (value, n=190) => String(value || '').replace(/\s+/g,' ').slice(0,n);
  const addOffer = item => ({
    type:'offer', title:item.titleZh || item.title || item.name || item.id,
    description:short([item.status === 'expired' || (item.expires_at && item.expires_at < new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()) ? '已结束' : '', item.sourceKind && item.sourceKind !== 'official' ? '第三方聚合 · 非官方' : '',item.freeSummary,item.freeMechanism,item.accessSummary].filter(Boolean).join(' · ')),
    keywords:[item.name,item.provider,item.model,item.productType,(item.type||[]).join(' '),'免费 API','API',item.freeSummary].join(' '),
    href:'/offers/'+encodeURIComponent(item.id)+'/'
  });
  const addModel = item => ({
    type:'model', title:item.model || item.id, description:short([item.provider,item.context && '上下文 '+item.context,item.rateLimit].filter(Boolean).join(' · ')),
    keywords:[item.provider,item.id,item.modality?.join(' '),item.sourceKind].join(' '),
    // The static generator publishes a detail route for every model, including
    // one-provider pages (noindex does not make the page inaccessible).
    href:'/models/'+(String(item.model || item.id).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'') || 'model')+'/'
  });
  const addSkill = item => ({
    type:'skill', title:item.name || item.id,
    description:short(item.description || item.summary || item.name),
    keywords:[item.id,item.category,item.githubUrl].filter(Boolean).join(' '),
    href:'/skills/?q='+encodeURIComponent(item.name || item.id)
  });
  const addTool = item => ({
    type:'tool', title:item.name || item.id, description:short(item.desc),
    keywords:[item.id,item.cat].join(' '),
    href:'/tools/?tool='+encodeURIComponent(item.id)
  });
  const tokens = q => normal(q).split(' ').filter(Boolean);
  const score = (item, query) => {
    const keys = tokens(query);
    const title = normal(item.title), keywords=normal(item.keywords), desc=normal(item.description);
    if (!keys.every(key => (title+' '+keywords+' '+desc).includes(key))) return -1;
    let points=0;
    for(const key of keys){if(title===key)points+=20;else if(title.includes(key))points+=10;if(keywords.includes(key))points+=4;if(desc.includes(key))points+=2;}
    return points;
  };
  const render = () => {
    const q = input.value.trim();
    const options = new URL(location.href);
    if (q) options.searchParams.set('q',q); else options.searchParams.delete('q');
    history.replaceState(null,'',options.pathname+options.search);
    const filtered = records.filter(row => type==='all' || row.type===type);
    let matches;
    if(!q)matches=filtered.slice(0,36);
    else if(fuse){
      const byRef = new Set(filtered);
      matches=fuse.search(q,{limit:300}).map(result=>result.item).filter(row=>byRef.has(row));
      // Always include exact all-token matches; Fuse can prune shorter Chinese phrases.
      const selected = new Set(matches);
      for(const row of filtered)if(score(row,q)>=0&&!selected.has(row)){matches.push(row);selected.add(row);}
      matches.sort((a,b)=>score(b,q)-score(a,q));
    }else {
      matches=filtered.map(item=>({item,score:score(item,q)}))
        .filter(row=>row.score>=0).sort((a,b)=>b.score-a.score).map(row=>row.item);
    }
    const limited=matches.slice(0,80);
    results.innerHTML=limited.map(item=>'<article class="search-result"><small>'+
      escape(({offer:'免费资源',model:'AI 模型',tool:'在线工具',skill:'Agent 技能'})[item.type])+
      '</small><h2><a href="'+escape(item.href)+'">'+escape(item.title)+'</a></h2><p>'+
      escape(item.description || '查看当前条目和使用条件')+'</p><a href="'+escape(item.href)+'">查看详情 →</a></article>').join('');
    empty.hidden=matches.length>0;
    status.textContent=q ? '找到 '+matches.length+' 条与“'+q+'”相关的结果'+(matches.length>80?'（展示前 80 条）':'') : '索引已加载，共 '+filtered.length+' 条可检索记录；输入关键词开始搜索';
  };
  const setType=next=>{
    type=next;
    document.querySelectorAll('[data-search-type]').forEach(button=>
      button.setAttribute('aria-pressed',String(button.dataset.searchType===type)));
    render();
  };
  document.querySelectorAll('[data-search-type]').forEach(button=>button.addEventListener('click',()=>setType(button.dataset.searchType)));
  document.querySelectorAll('[data-search-example]').forEach(button=>button.addEventListener('click',()=>{
    input.value=button.dataset.searchExample;render();input.focus();
  }));
  input.addEventListener('input',render);
  form.addEventListener('submit',event=>{event.preventDefault();render();});
  input.value=new URLSearchParams(location.search).get('q') || '';
  Promise.allSettled([read('/data/offers.json'),read('/data/models.json'),read('/data/skills.json')])
    .then(out=>{
      const mappers=[addOffer,addModel,addSkill];
      records=out.flatMap((result,index)=>result.status==='fulfilled'?result.value.map(mappers[index]):[]);
      if(window.Tools?.all)records.push(...window.Tools.all.map(addTool));
      if(!records.length){status.textContent='索引暂时不可用，请稍后重试。';return;}
      if(typeof window.Fuse==='function'){
        fuse=new window.Fuse(records,{keys:[{name:'title',weight:0.5},{name:'keywords',weight:0.3},{name:'description',weight:0.2}],threshold:0.35,ignoreLocation:true,includeScore:true});
      }
      render();
    }).catch(()=>{status.textContent='搜索加载失败，请稍后重试。';});
})();
