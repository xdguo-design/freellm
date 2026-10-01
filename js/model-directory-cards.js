(() => {
  const root = document.getElementById('ml-directory');
  if (!root) return;

  const pageSize = 12;
  const state = { models: [], page: 1, category: 'all', latestCutoff: '' };
  const $ = (selector) => root.querySelector(selector);
  const esc = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]));
  const contextValue = (value) => Number(String(value || '').replace(/[^0-9.]/g, '')) || 0;
  const contextLabel = (value) => {
    const amount = contextValue(value);
    if (!amount) return '上下文待核验';
    return amount >= 1000000 ? (Math.round(amount / 100000) / 10) + 'M 上下文' : Math.round(amount / 1000) + 'K 上下文';
  };
  const modalityLabel = (value) => ({ text:'文本', image:'图像', audio:'音频', video:'视频', reasoning:'推理', embedding:'向量', pdf:'PDF', code:'代码', vision:'视觉' }[value] || value);
  const matchesCategory = (model) => {
    if (state.category === 'popular') return Number(model.score || 0) >= 80;
    if (state.category === 'latest') return Boolean(model.released && model.released >= state.latestCutoff);
    if (state.category === 'free') return Boolean(model.isFree);
    if (state.category === 'limited') return model.tierType === 'limited';
    if (state.category === 'verified') return Boolean(model.verified);
    if (state.category === 'no-card') return Boolean(model.noCard);
    return true;
  };
  const matchesFilters = (model) => {
    const query = $('#ml-directory-search').value.trim().toLowerCase();
    const provider = $('#ml-directory-provider').value;
    const modality = $('#ml-directory-modality').value;
    const context = $('#ml-directory-context').value;
    const terms = [model.model, model.provider, model.description, model.bestFor, ...(model.modality || [])].join(' ').toLowerCase();
    const amount = contextValue(model.context);
    const contextMatches = !context
      || (context === 'short' && amount > 0 && amount < 32000)
      || (context === 'medium' && amount >= 32000 && amount < 128000)
      || (context === 'long' && amount >= 128000)
      || (context === 'million' && amount >= 1000000);
    return matchesCategory(model)
      && (!query || terms.includes(query))
      && (!provider || model.providerId === provider)
      && (!modality || (model.modality || []).includes(modality))
      && contextMatches;
  };
  const cardHtml = (model) => {
    const mark = String(model.provider || 'AI').trim().slice(0, 2).toUpperCase();
    const tier = model.tierType === 'limited' ? '限时免费' : model.tierType === 'trial' ? '免费试用' : model.isFree ? '免费 API' : '免费资源';
    const modalities = (model.modality || []).filter((item) => item !== 'unknown').slice(0, 3).map(modalityLabel);
    const tags = [contextLabel(model.context), ...modalities, model.noCard ? '无需信用卡' : ''].filter(Boolean).slice(0, 4);
    const facts = [
      model.score ? '<span class="ml-directory-score">指数 ' + esc(model.score) + '</span>' : '',
      model.usageActivity && model.usageActivity !== '—' ? '<span>↗ ' + esc(model.usageActivity) + '</span>' : '',
      model.rateLimit ? '<span title="速率限制">⚡ ' + esc(model.rateLimit) + '</span>' : '',
    ].filter(Boolean).join('');
    const destination = /^https:\/\//i.test(model.directoryHref || '') ? model.directoryHref : 'https://freellm.net/models/';
    return '<article class="ml-directory-card"><div class="ml-directory-card-head"><span class="ml-directory-provider-mark" aria-hidden="true">' + esc(mark) + '</span><div class="ml-directory-title"><small>' + esc(model.provider) + '</small><h3>' + esc(model.model) + '</h3></div><span class="ml-directory-badge ' + (model.tierType === 'limited' ? 'is-limited' : '') + '">' + tier + '</span></div><p>' + esc(model.description || '免费或试用模型入口，具体额度与使用条件请查看来源说明。') + '</p><div class="ml-directory-tags">' + tags.map((tag) => '<span>' + esc(tag) + '</span>').join('') + '</div><div class="ml-directory-card-footer"><span class="ml-directory-facts">' + facts + '</span><a href="' + esc(destination) + '" target="_blank" rel="noopener noreferrer">查看入口 <span aria-hidden="true">→</span></a></div></article>';
  };
  const pageItems = (page, pageCount) => {
    const candidates = new Set([1, pageCount, page - 1, page, page + 1, page <= 3 ? 2 : 0, pageCount - page < 2 ? pageCount - 1 : 0]);
    return [...candidates].filter((value) => value >= 1 && value <= pageCount).sort((a, b) => a - b);
  };
  const renderPagination = (pageCount) => {
    if (pageCount <= 1) { $('#ml-directory-pagination').innerHTML = ''; return; }
    const items = pageItems(state.page, pageCount);
    let previous = 0;
    const buttons = items.map((page) => {
      const gap = previous && page - previous > 1 ? '<span class="ml-directory-ellipsis">…</span>' : '';
      previous = page;
      return gap + '<button type="button" class="ml-directory-page' + (page === state.page ? ' is-current' : '') + '" data-directory-page="' + page + '"' + (page === state.page ? ' aria-current="page"' : '') + '>' + page + '</button>';
    }).join('');
    $('#ml-directory-pagination').innerHTML = '<button type="button" class="ml-directory-page ml-directory-page-arrow" data-directory-page="' + (state.page - 1) + '" aria-label="上一页"' + (state.page <= 1 ? ' disabled' : '') + '>‹</button>' + buttons + '<button type="button" class="ml-directory-page ml-directory-page-arrow" data-directory-page="' + (state.page + 1) + '" aria-label="下一页"' + (state.page >= pageCount ? ' disabled' : '') + '>›</button>';
  };
  const render = () => {
    const filtered = state.models.filter(matchesFilters);
    const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
    state.page = Math.min(state.page, pageCount);
    const start = (state.page - 1) * pageSize;
    const shown = filtered.slice(start, start + pageSize);
    $('#ml-directory-grid').innerHTML = shown.length ? shown.map(cardHtml).join('') : '<p class="ml-directory-empty">没有找到匹配模型，调整筛选条件再试试。</p>';
    $('#ml-directory-count').textContent = filtered.length ? '显示 ' + (start + 1) + '–' + (start + shown.length) + ' / ' + filtered.length + ' 个模型' : '0 个模型';
    $('#ml-directory-total').textContent = state.models.length;
    $('#ml-directory-page-summary').textContent = '共 ' + filtered.length + ' 个模型　跳转到第 ' + state.page + ' / ' + pageCount + ' 页';
    renderPagination(pageCount);
  };
  const reset = () => {
    $('#ml-directory-search').value = '';
    $('#ml-directory-provider').value = '';
    $('#ml-directory-modality').value = '';
    $('#ml-directory-context').value = '';
    state.category = 'all';
    state.page = 1;
    root.querySelectorAll('[data-directory-category]').forEach((button) => button.classList.toggle('is-active', button.dataset.directoryCategory === 'all'));
    render();
  };

  root.querySelectorAll('[data-directory-category]').forEach((button) => button.addEventListener('click', () => {
    state.category = button.dataset.directoryCategory;
    state.page = 1;
    root.querySelectorAll('[data-directory-category]').forEach((item) => item.classList.toggle('is-active', item === button));
    render();
  }));
  ['ml-directory-search', 'ml-directory-provider', 'ml-directory-modality', 'ml-directory-context'].forEach((id) => {
    const control = document.getElementById(id);
    control.addEventListener(id === 'ml-directory-search' ? 'input' : 'change', () => { state.page = 1; render(); });
  });
  $('#ml-directory-clear').addEventListener('click', reset);
  root.addEventListener('click', (event) => {
    const button = event.target.closest('[data-directory-page]');
    if (!button || button.disabled) return;
    state.page = Number(button.dataset.directoryPage);
    render();
    root.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  fetch('/data/freellm-net-models.json?v=20261001b')
    .then((response) => { if (!response.ok) throw new Error('model snapshot unavailable'); return response.json(); })
    .then((snapshot) => {
      if (!Array.isArray(snapshot.models) || !snapshot.models.length) throw new Error('empty model snapshot');
      state.models = snapshot.models;
      const releases = state.models.map((model) => Date.parse(model.released || '')).filter(Number.isFinite);
      const newestRelease = releases.length ? Math.max(...releases) : 0;
      state.latestCutoff = newestRelease ? new Date(newestRelease - 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10) : '';
      const providers = [...new Set(state.models.map((model) => model.providerId).filter(Boolean))]
        .map((id) => ({ id, name: state.models.find((model) => model.providerId === id).provider }))
        .sort((a, b) => a.name.localeCompare(b.name));
      $('#ml-directory-provider').innerHTML = '<option value="">厂商</option>' + providers.map((provider) => '<option value="' + esc(provider.id) + '">' + esc(provider.name) + '</option>').join('');
      render();
    })
    .catch(() => {
      $('#ml-directory-grid').innerHTML = '<p class="ml-directory-empty">本地模型快照暂时无法读取，请重新构建静态资源。</p>';
      $('#ml-directory-count').textContent = '模型目录暂不可用';
    });
})();
