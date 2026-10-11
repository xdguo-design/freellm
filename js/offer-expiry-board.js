(() => {
  'use strict';
  // Same rule as scripts/build_static.py render_expiry_board: verified offers
  // whose expires_at is within the next 14 Asia/Shanghai calendar days. The
  // server-rendered block is refreshed with the visitor's real date; with no
  // qualifying offer the whole block stays hidden (no placeholder copy).
  const board = document.getElementById('expiring-soon');
  if(!board)return;
  const WINDOW_DAYS = Number(board.dataset.expiryWindowDays) || 14;
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const iso=()=>{
    const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
      year:'numeric',month:'2-digit',day:'2-digit',timeZone:'Asia/Shanghai'
    }).formatToParts(new Date()).filter(x=>['year','month','day'].includes(x.type)).map(x=>[x.type,x.value]));
    return parts.year+'-'+parts.month+'-'+parts.day;
  };
  const loadOffers = () => fetch('/data/offers.json').then(response=>{
    if(!response.ok)throw new Error('offers unavailable');
    return response.json();
  }).then(offers=>{
    const today=iso(),dateStart=new Date(today+'T00:00:00+08:00');
    const items=offers.filter(o=>/^\d{4}-\d{2}-\d{2}$/.test(o.expires_at||''))
      .filter(o=>o.status==='verified'&&o.expires_at>=today)
      .map(o=>({o,days:Math.round((new Date(o.expires_at+'T00:00:00+08:00')-dateStart)/86400000)}))
      .filter(x=>x.days<=WINDOW_DAYS).sort((a,b)=>a.days-b.days||String(a.o.id).localeCompare(String(b.o.id))).slice(0,6);
    if(!items.length){board.hidden=true;board.replaceChildren();return;}
    board.innerHTML='<div class="weekly-scan-header"><h2 id="expiry-title">即将到期</h2><a href="/offers/">查看全部优惠 →</a></div>'+
      '<div class="expiry-card-grid" id="expiring-cards" aria-live="polite">'+
      items.map(({o,days})=>'<article class="expiry-card"><strong>'+esc(o.titleZh||o.title||o.name)+'</strong><small>活动到期：'+esc(o.expires_at)+' · '+(days===0?'今天到期':days+' 天后到期')+'</small><a href="/offers/'+encodeURIComponent(o.id)+'/">查看官方条件与详情 →</a></article>').join('')+'</div>';
    board.hidden=false;
  }).catch(()=>{/* Keep the server-rendered block as built. */});
  // The expiry board is below the resource catalogue. Do not download the
  // entire 400KB+ offers dataset on the first mobile paint for offscreen data.
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      observer.disconnect();
      loadOffers();
    }, {rootMargin: '300px'});
    observer.observe(board.hidden ? (board.previousElementSibling || board) : board);
  } else {
    window.addEventListener('load', loadOffers, {once: true});
  }
})();
