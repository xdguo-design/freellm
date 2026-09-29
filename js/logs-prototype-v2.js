(() => {
  const search = document.getElementById('log-filter-search');
  const state = document.getElementById('log-filter-state');
  const count = document.getElementById('log-filter-count');
  const days = Array.from(document.querySelectorAll('.log-day'));
  const links = Array.from(document.querySelectorAll('.log-date-link'));
  const container = document.querySelector('.log-days');
  if (!search || !state || !count || !days.length) return;

  let empty = document.getElementById('log-filter-empty');
  if (!empty) {
    empty = document.createElement('div');
    empty.id = 'log-filter-empty';
    empty.className = 'log-filter-empty';
    empty.hidden = true;
    empty.textContent = '没有找到匹配的日志日期或变更记录。';
    container?.appendChild(empty);
  }

  const apply = () => {
    const q = search.value.trim().toLowerCase();
    let visible = 0;
    days.forEach(day => {
      const matchesState = state.value === 'all' || day.dataset.logState === state.value;
      const matchesQuery = !q || (day.textContent || '').toLowerCase().includes(q) || (day.dataset.logDate || '').includes(q);
      const show = matchesState && matchesQuery;
      day.hidden = !show;
      if (show) visible++;
    });
    links.forEach(link => {
      const target = document.querySelector(link.getAttribute('href'));
      link.hidden = Boolean(target?.hidden);
    });
    count.textContent = `显示 ${visible} / ${days.length} 天`;
    empty.hidden = visible !== 0;
  };

  search.addEventListener('input', apply);
  state.addEventListener('change', apply);
  links.forEach(link => link.addEventListener('click', () => {
    links.forEach(item => item.classList.toggle('is-active', item === link));
  }));
  apply();
})();