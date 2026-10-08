(() => {
  'use strict';
  const grid = document.getElementById('expiring-cards');
  if(!grid)return;
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const iso=()=>{
    const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
      year:'numeric',month:'2-digit',day:'2-digit',timeZone:'Asia/Shanghai'
    }).formatToParts(new Date()).filter(x=>['year','month','day'].includes(x.type)).map(x=>[x.type,x.value]));
    return parts.year+'-'+parts.month+'-'+parts.day;
  };
  fetch('/data/offers.json').then(response=>{
    if(!response.ok)throw new Error('offers unavailable');
    return response.json();
  }).then(offers=>{
    const today=iso(),dateStart=new Date(today+'T00:00:00+08:00');
    const items=offers.filter(o=>/^\d{4}-\d{2}-\d{2}$/.test(o.expires_at||''))
      .filter(o=>o.status!=='expired'&&o.expires_at>=today)
      .map(o=>({o,days:Math.round((new Date(o.expires_at+'T00:00:00+08:00')-dateStart)/86400000)}))
      .filter(x=>x.days<=30).sort((a,b)=>a.days-b.days).slice(0,6);
    grid.innerHTML=items.length?items.map(({o,days})=>'<article class="expiry-card"><strong>'+esc(o.titleZh||o.title||o.name)+'</strong><small>活动到期：'+esc(o.expires_at)+' · '+days+' 天内</small><a href="/offers/'+encodeURIComponent(o.id)+'/">查看官方条件与详情 →</a></article>').join(''):'<p>暂无已核实、30 天内到期的活动。未公布日期的活动不会假定到期日。</p>';
  }).catch(()=>{grid.textContent='活动数据暂时不可用，请前往每日更新查看核验记录。';});
})();
