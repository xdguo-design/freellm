(() => {
  const root = document.getElementById('model-library-app');
  if (!root) return;
  const $ = (selector) => root.querySelector(selector);
  const state = { models: [], all: [], offers: [], category: '', page: 1, pageSize: 6, compare: [], recent: [] };
  const normalize = (value) => String(value || '').toLowerCase().normalize('NFKC');
  const esc = (value) => String(value == null ? '' : value).replace(/[&<>\"']/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', "'":'&#39;' }[char]));
  const contextValue = (value) => {
    const n = Number(String(value || '').replace(/[^0-9.]/g, ''));
    return Number.isFinite(n) ? n : 0;
  };
  const contextLabel = (value) => {
    const n = contextValue(value);
    if (!n) return '上下文待核验';
    return n >= 1000000 ? (Math.round(n / 100000) / 10) + 'M' : Math.round(n / 1000) + 'K';
  };
  const modalitiesLabel = (items) => {
    const map = { text: '文本', image: '图像', audio: '音频', video: '视频', reasoning: '推理', embedding: '向量' };
    return (items || []).map((item) => map[item] || item).slice(0, 3).join(' · ') || '能力待核验';
  };
  const regionLabel = (value) => ({ domestic: '国内接入', international: '国际接入', global: '全球接入' }[value] || '地区待核验');
  const modelHref = (item) => {
    if (item.directoryHref) return item.directoryHref;
    const id = item.canonicalModelId || item.id || item.model;
    const slug = String(id).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    return '/models/' + slug + '/';
  };
  const hasFreeOffer = (item) => {
    const provider = normalize(item.provider);
    const name = normalize(item.model).replace(/[^a-z0-9]/g, '');
    return state.offers.some((offer) => {
      const types = Array.isArray(offer.type) ? offer.type : [];
      if (!types.includes('free')) return false;
      const offeredModel = normalize(offer.model).replace(/[^a-z0-9]/g, '');
      const offeredProvider = normalize(offer.provider);
      return name.length > 5 && offeredModel.includes(name);
    });
  };
  const byId = (id) => state.models.find((item) => item.key === id);
  const groupModels = (rows) => {
    const groups = new Map();
    rows.forEach((row) => {
      const key = row.canonicalModelId || normalize(row.model);
      if (!groups.has(key)) groups.set(key, { key, model: row.model, provider: row.provider, providers: [], context: row.context, modality: [], status: row.status, sourceKind: row.sourceKind, accessRegion: row.accessRegion || '', released: row.released || '', canonicalModelId: row.canonicalModelId || '', records: [] });
      const item = groups.get(key);
      item.records.push(row);
      if (!item.providers.includes(row.provider)) item.providers.push(row.provider);
      if (contextValue(row.context) > contextValue(item.context)) item.context = row.context;
      (row.modality || []).forEach((m) => { if (!item.modality.includes(m)) item.modality.push(m); });
      if (row.status === 'online') item.status = 'online';
      if (!item.accessRegion && row.accessRegion) item.accessRegion = row.accessRegion;
      if (row.released && (!item.released || row.released > item.released)) item.released = row.released;
      if (row.sourceKind === 'official') item.sourceKind = 'official';
    });
    return [...groups.values()].map((item, index) => {
      item.key = String(item.key || index);
      item.hasFree = item.records.some(hasFreeOffer);
      item.href = modelHref(item.records[0]);
      return item;
    });
  };
  const cardHtml = (item) => {
    const mark = (item.provider || 'AI').trim().slice(0, 2).toUpperCase();
    const tags = [contextLabel(item.context), modalitiesLabel(item.modality).split(' · ')[0], item.providers.length > 1 ? item.providers.length + ' 个入口' : regionLabel(item.accessRegion)];
    return '<article class="ml-model-card"><div class="ml-model-card-top"><span class="ml-provider-mark" aria-hidden="true">' + esc(mark) + '</span><div class="ml-card-title"><small>' + esc(item.provider) + (item.providers.length > 1 ? ' +' + (item.providers.length - 1) : '') + '</small><h3>' + esc(item.model) + '</h3></div><span class="ml-status-badge">' + (item.hasFree ? '免费入口' : (item.status === 'online' ? '可查询' : '待核验')) + '</span></div><p>' + modalitiesLabel(item.modality) + '模型，最高 ' + contextLabel(item.context) + ' 上下文；查看接入平台、来源与限制。</p><div class="ml-model-tags">' + tags.map((tag) => '<span>' + esc(tag) + '</span>').join('') + '</div><div class="ml-card-actions"><a href="' + item.href + '" data-model-id="' + item.key + '">查看详情 →</a><button type="button" data-compare-id="' + esc(item.key) + '" aria-pressed="' + state.compare.includes(item.key) + '">' + (state.compare.includes(item.key) ? '✓ 已加入' : '＋ 对比') + '</button></div></article>';
  };
  const sortModels = (items) => {
    const sort = $('#ml-sort').value;
    return items.sort((a, b) => {
      if (sort === 'context') return contextValue(b.context) - contextValue(a.context) || a.model.localeCompare(b.model);
      if (sort === 'name') return a.model.localeCompare(b.model);
      return String(b.released).localeCompare(String(a.released)) || a.model.localeCompare(b.model);
    });
  };
  const matches = (item) => {
    const q = normalize($('#ml-search').value);
    const provider = $('#ml-provider').value;
    const modality = $('#ml-modality').value;
    const context = $('#ml-context').value;
    const free = $('#ml-free').value;
    const region = $('#ml-region').value;
    const terms = normalize([item.model, item.provider, item.providers.join(' '), modalitiesLabel(item.modality), item.canonicalModelId].join(' '));
    const n = contextValue(item.context);
    const textMatch = !q || terms.includes(q);
    const providerMatch = !provider || item.providers.includes(provider);
    const modalityMatch = !modality || item.modality.includes(modality);
    const categoryMatch = !state.category || (state.category === 'multimodal' ? item.modality.filter((m) => m !== 'text').length > 0 : item.modality.includes(state.category));
    const contextMatch = !context || (context === 'short' && n > 0 && n < 32000) || (context === 'medium' && n >= 32000 && n < 128000) || (context === 'long' && n >= 128000) || (context === 'million' && n >= 1000000);
    const freeMatch = !free || (free === 'yes' ? item.hasFree : !item.hasFree);
    const regionMatch = !region || (region === 'domestic' ? item.accessRegion === 'domestic' : region === 'international' ? ['global','international'].includes(item.accessRegion) : !item.accessRegion);
    return textMatch && providerMatch && modalityMatch && categoryMatch && contextMatch && freeMatch && regionMatch;
  };
  const renderCards = (resetPage) => {
    if (resetPage) state.page = 1;
    const items = sortModels(state.models.filter(matches));
    const shown = items.slice(0, state.page * state.pageSize);
    $('#ml-card-grid').innerHTML = shown.length ? shown.map(cardHtml).join('') : '<div class="ml-empty-state">没有找到符合条件的模型，试试清空筛选。</div>';
    $('#ml-results-status').textContent = '显示 ' + shown.length + ' / ' + items.length + ' 个模型 · 目录共 ' + state.models.length + ' 条模型记录' + (state.dataFallback ? ' · 使用目录快照' : '');
    $('#ml-total').textContent = '(' + state.models.length + ')';
    let more = root.querySelector('#ml-load-more');
    if (!more) {
      const wrap = root.querySelector('.ml-load-more-wrap');
      wrap.innerHTML = '<button class="ml-load-more" id="ml-load-more" type="button">加载更多模型 ↓</button>';
      more = $('#ml-load-more');
      more.addEventListener('click', () => { state.page += 1; renderCards(false); });
    }
    more.hidden = shown.length >= items.length;
  };
  const renderCompare = () => {
    const list = $('#ml-compare-list');
    list.innerHTML = state.compare.map((id) => {
      const item = byId(id);
      return item ? '<div class="ml-compare-chip"><span>' + esc(item.model) + '</span><button type="button" data-remove-compare="' + esc(id) + '" aria-label="移除 ' + esc(item.model) + '">×</button></div>' : '';
    }).join('');
    $('#ml-compare-empty').hidden = state.compare.length > 0;
    $('#ml-compare-count').textContent = '(' + state.compare.length + '/4)';
    $('#ml-compare-start').disabled = state.compare.length < 2;
    if (state.compare.length < 2) {
      $('#ml-compare-table').hidden = true;
      $('#ml-compare-table').innerHTML = '';
    }
    root.querySelectorAll('[data-compare-id]').forEach((button) => {
      const selected = state.compare.includes(button.dataset.compareId);
      button.setAttribute('aria-pressed', String(selected));
      button.textContent = selected ? '✓ 已加入' : '＋ 对比';
      button.disabled = !selected && state.compare.length >= 4;
    });
  };
  const renderRecent = () => {
    const wrap = $('#ml-recent-list');
    wrap.innerHTML = state.recent.length ? state.recent.slice(0, 5).map((item) => '<a class="ml-recent-item" href="' + esc(item.href) + '"><span class="ml-recent-logo">' + esc(item.mark) + '</span><span><strong>' + esc(item.name) + '</strong><small>' + esc(item.time) + '</small></span></a>').join('') : '<p class="ml-muted">打开模型详情后，会显示最近浏览记录。</p>';
  };
  const startCompare = () => {
    const items = state.compare.map(byId).filter(Boolean);
    if (items.length < 2) return;
    const rows = [['上下文', (item) => contextLabel(item.context)], ['模态能力', (item) => modalitiesLabel(item.modality)], ['接入厂家', (item) => item.providers.join('、')], ['地区', (item) => regionLabel(item.accessRegion)], ['免费入口', (item) => item.hasFree ? '有匹配的免费资源' : '需查看官方条件']];
    const table = '<table><thead><tr><th>对比项</th>' + items.map((item) => '<th>' + esc(item.model) + '</th>').join('') + '</tr></thead><tbody>' + rows.map((row) => '<tr><th>' + row[0] + '</th>' + items.map((item) => '<td>' + esc(row[1](item)) + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
    $('#ml-compare-table').innerHTML = table;
    $('#ml-compare-table').hidden = false;
  };
  const initControls = () => {
    const providers = [...new Set(state.models.flatMap((item) => item.providers))].sort((a, b) => a.localeCompare(b));
    $('#ml-provider').innerHTML = '<option value="">全部</option>' + providers.map((provider) => '<option value="' + esc(provider) + '">' + esc(provider) + '</option>').join('');
    ['ml-search','ml-provider','ml-modality','ml-context','ml-free','ml-region','ml-sort'].forEach((id) => {
      const el = document.getElementById(id);
      el.addEventListener(id === 'ml-search' ? 'input' : 'change', () => renderCards(true));
    });
    root.querySelectorAll('[data-category]').forEach((button) => button.addEventListener('click', () => {
      state.category = button.dataset.category;
      root.querySelectorAll('[data-category]').forEach((tab) => tab.classList.toggle('active', tab === button));
      renderCards(true);
    }));
    $('#ml-reset').addEventListener('click', () => {
      ['ml-search','ml-provider','ml-modality','ml-context','ml-free','ml-region'].forEach((id) => { document.getElementById(id).value = ''; });
      state.category = '';
      root.querySelectorAll('[data-category]').forEach((tab) => tab.classList.toggle('active', !tab.dataset.category));
      renderCards(true);
    });
    $('#ml-clear-compare').addEventListener('click', () => { state.compare = []; renderCompare(); });
    $('#ml-clear-recent').addEventListener('click', () => { state.recent = []; try { localStorage.removeItem('freellm-model-library-recent'); } catch (_) {} renderRecent(); });
    $('#ml-compare-start').addEventListener('click', startCompare);
    root.addEventListener('click', (event) => {
      const add = event.target.closest('[data-compare-id]');
      if (add) {
        const id = add.dataset.compareId;
        if (state.compare.includes(id)) state.compare = state.compare.filter((value) => value !== id);
        else if (state.compare.length < 4) state.compare.push(id);
        renderCompare();
        renderCards(false);
        return;
      }
      const remove = event.target.closest('[data-remove-compare]');
      if (remove) { state.compare = state.compare.filter((id) => id !== remove.dataset.removeCompare); renderCompare(); renderCards(false); }
      const link = event.target.closest('a[data-model-id]');
      if (link) {
        const item = byId(link.dataset.modelId);
        if (item) {
          const recent = { id: item.key, name: item.model, href: item.href, mark: (item.provider || 'AI').slice(0, 1).toUpperCase(), time: '刚刚' };
          state.recent = [recent].concat(state.recent.filter((row) => row.id !== item.key)).slice(0, 5);
          try { localStorage.setItem('freellm-model-library-recent', JSON.stringify(state.recent)); } catch (_) {}
        }
      }
    });
  };
  const parseDirectoryRows = (html) => {
    const parsed = new DOMParser().parseFromString(html, 'text/html');
    const rows = [...parsed.querySelectorAll('#model-catalog tbody tr.catalog-row')];
    return rows.map((row) => {
      const link = row.querySelector('.model-name');
      const name = row.querySelector('.model-name strong') || link;
      const provider = row.querySelector('.provider-filter');
      const href = link ? link.getAttribute('href') : '';
      const modelName = name ? name.textContent.trim() : 'Unknown model';
      const route = href ? href.split('/').filter(Boolean).pop() : modelName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
      const region = row.getAttribute('data-cn') || '';
      const status = row.querySelector('.status-online') ? 'online' : 'unknown';
      return {
        id: row.getAttribute('data-model-id') || route,
        providerId: row.getAttribute('data-provider-id') || '',
        provider: provider ? provider.textContent.trim() : 'Unknown provider',
        model: modelName,
        context: row.getAttribute('data-context') || '',
        modality: (row.getAttribute('data-modality') || '').split(',').filter(Boolean),
        status,
        sourceKind: 'catalog',
        canonicalModelId: route,
        directoryHref: href || '/models/all/',
        accessRegion: region === 'available' ? 'domestic' : region === 'unavailable' ? 'international' : '',
        released: row.getAttribute('data-released') || ''
      };
    });
  };
  const loadDirectorySnapshot = async () => {
    const response = await fetch('/models/all/');
    if (!response.ok) throw new Error('model directory snapshot unavailable');
    const html = await response.text();
    const routes = [...new Set([...html.matchAll(/href="(\/models\/all\/page\/\d+\/)"/g)].map((match) => match[1]))];
    const pages = await Promise.allSettled(routes.map(async (route) => {
      const page = await fetch(route);
      if (!page.ok) throw new Error('model directory page unavailable');
      return page.text();
    }));
    const pagesHtml = pages.filter((result) => result.status === 'fulfilled').map((result) => result.value);
    const rows = parseDirectoryRows(html).concat(...pagesHtml.map(parseDirectoryRows));
    if (!rows.length) throw new Error('model directory contains no rows');
    return rows;
  };
  const loadData = async () => {
    try {
      const modelTask = fetch('/data/models.json').then((response) => {
        if (!response.ok) throw new Error('model JSON unavailable');
        return response.json();
      });
      const offerTask = fetch('/data/offers.json').then((response) => {
        if (!response.ok) throw new Error('offer JSON unavailable');
        return response.json();
      }).catch(() => []);
      let rawModels;
      try {
        rawModels = await modelTask;
      } catch (_) {
        rawModels = await loadDirectorySnapshot();
        state.dataFallback = true;
      }
      state.offers = await offerTask;
      state.all = rawModels;
      state.models = groupModels(rawModels);
      $('#ml-model-count').textContent = rawModels.length;
      $('#ml-provider-count').textContent = new Set(rawModels.map((item) => item.providerId).filter(Boolean)).size;
      if (state.offers.length) $('#ml-offer-count').textContent = state.offers.length;
      let saved = [];
      try { saved = JSON.parse(localStorage.getItem('freellm-model-library-recent') || '[]'); } catch (_) {}
      state.recent = Array.isArray(saved) ? saved.map((entry) => byId(typeof entry === 'string' ? entry : entry && entry.id)).filter(Boolean).map((item) => ({ id:item.key, name:item.model, href:item.href, mark:(item.provider || 'AI').slice(0,1).toUpperCase(), time:'最近浏览' })) : [];
      initControls();
      renderRecent();
      renderCards(true);
      renderCompare();
    } catch (error) {
      $('#ml-results-status').textContent = '模型目录暂时无法加载，请进入完整模型目录继续浏览。';
      $('#ml-card-grid').innerHTML = '<div class="ml-empty-state"><a href="/models/all/">打开完整模型目录 →</a></div>';
    }
  };
  loadData();
})();
