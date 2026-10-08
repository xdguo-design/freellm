(() => {
  'use strict';
  const ready = document.readyState === 'loading'
    ? new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve, {once:true}))
    : Promise.resolve();
  const set = (node, text) => { if (node) node.textContent = String(text); };
  const onToday = date => {
    const values = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
      timeZone:'Asia/Shanghai', year:'numeric', month:'2-digit', day:'2-digit'
    }).formatToParts(new Date()).filter(part => ['year','month','day'].includes(part.type))
      .map(part => [part.type, part.value]));
    return date === [values.year,values.month,values.day].join('-');
  };
  const metric = (container, name, value, selector = 'strong') => {
    if (!container) return;
    [...container.querySelectorAll('article')].forEach(article => {
      const label = article.querySelector('small, span');
      if (label && label.textContent.trim() === name) set(article.querySelector(selector), value);
    });
  };
  const render = scan => {
    if (!scan || !/^\d{4}-\d{2}-\d{2}$/.test(scan.date)
      || !Number.isInteger(scan.models) || !Number.isInteger(scan.offers)) return;
    const current = onToday(scan.date);
    const latest = '最近扫描：' + scan.date;
    const home = document.querySelector('.prototype-stats');
    if (home) {
      const cards = home.querySelectorAll('.prototype-stat');
      const values = [scan.newCount,scan.models,scan.newOffers,scan.offers];
      const labels = current
        ? ['今日新增','模型记录','新增资源条目','已收录资源']
        : [latest,'模型记录','新增资源条目','已收录资源'];
      cards.forEach((card,i) => {
        if (i >= values.length) return;
        set(card.querySelector('small'), labels[i]);
        set(card.querySelector('strong:not(.prototype-stat-icon strong)'),values[i]);
      });
      // Top 10 is an editorial label, not a scan-derived statistic.
    }
    const hero = document.getElementById('heroCount');
    set(hero,scan.offers);
    const badge = document.getElementById('daily-log-badge');
    if (badge) {
      set(badge,current ? '新增 ' + scan.newCount + ' 项' : latest);
      badge.dataset.newCount = current ? String(scan.newCount) : '0';
      badge.dataset.changeCount = current ? String(scan.newCount) : '0';
    }
    const intel = document.querySelector('.hero-intel-head > span');
    if (intel) set(intel,current ? scan.date + ' · 最新扫描' : latest);
    if (!scan.hasHistoricalBaseline) {
      document.querySelectorAll('.mini-chart').forEach(node => node.remove());
    }
    document.querySelectorAll('.ref-update-metrics > article').forEach(article => {
      const label = article.querySelector('span')?.textContent.trim();
      const value = {今日新增:current?scan.newCount:0,模型记录:scan.models,已收录资源:scan.offers,来源核验:scan.sourceChecks + '/2',最近变更:scan.newCount}[label];
      if (value !== undefined) set(article.querySelector('strong'),value);
      if (label === '今日新增' && !current) set(article.querySelector('small'),latest);
    });
    document.querySelectorAll('.ref-update-snapshot .log-snapshot-card').forEach(card => {
      const label = card.querySelector('span')?.textContent || '';
      if (label.includes('模型')) set(card.querySelector('strong'),scan.models);
      if (label.includes('资源')) set(card.querySelector('strong'),scan.offers);
    });
    const shared = document.querySelectorAll('[data-scan-stat]');
    shared.forEach(node => set(node,scan[node.dataset.scanStat] ?? '—'));
    document.querySelectorAll('[data-scan-date]').forEach(node => set(node,current ? scan.date : latest));
  };
  ready.then(async () => {
    try {
      const response = await fetch('/data/scan-summary.json', {cache:'no-store'});
      if (!response.ok) throw new Error('scan source unavailable');
      render(await response.json());
    } catch (error) {
      document.querySelectorAll('.prototype-stats .prototype-stat strong:not(.prototype-top10), [data-scan-stat]').forEach(n => set(n,'—'));
      set(document.getElementById('daily-log-badge'),'最近扫描：暂无记录');
      document.querySelectorAll('.mini-chart').forEach(n=>n.remove());
    }
  });
})();
