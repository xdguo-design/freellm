(() => {
  const root = document.getElementById('model-library-app');
  if (!root) return;
  const $ = (selector) => root.querySelector(selector);
  const state = { models: [], all: [], offers: [], category: '', page: 1, pageSize: 6, compare: [], recent: [] };
  const CURATED_MODELS = [
    { id:'curated/openai/gpt-4o-mini', providerId:'openai', provider:'OpenAI', model:'GPT-4o mini', context:'128000', modality:['text','image'], license:'commercial', status:'online', canonicalModelId:'curated/gpt-4o-mini', description:'强大的多模态模型，具备高性能与低延迟，适合广泛场景。', badges:['热门'], featured:true, featuredOrder:0, directoryHref:'/models/all/' },
    { id:'curated/anthropic/claude-3-5-haiku', providerId:'anthropic', provider:'Anthropic', model:'Claude 3.5 Haiku', context:'200000', modality:['text'], license:'commercial', status:'online', canonicalModelId:'curated/claude-3-5-haiku', description:'新一代高效模型，推理、创作和代码能力均衡。', badges:['热门'], featured:true, featuredOrder:1, directoryHref:'/models/all/' },
    { id:'curated/google/gemini-1-5-flash', providerId:'google', provider:'Google', model:'Gemini 1.5 Flash', context:'1000000', modality:['text','image','audio','video'], license:'commercial', status:'online', canonicalModelId:'curated/gemini-1-5-flash', description:'支持超长上下文的多模态模型，适用于复杂推理与多媒体任务。', badges:['热门'], featured:true, featuredOrder:2, directoryHref:'/models/all/' },
    { id:'curated/qwen/qwen2-5-72b', providerId:'qwen', provider:'通义千问', model:'Qwen2.5 72B', context:'128000', modality:['text'], license:'apache-2.0', status:'online', canonicalModelId:'curated/qwen2-5-72b', description:'阿里云开源的大语言模型，在中文理解与复杂任务上表现优秀。', badges:['推荐'], featured:true, featuredOrder:3, directoryHref:'/models/all/' },
    { id:'curated/deepseek/deepseek-v3', providerId:'deepseek', provider:'DeepSeek', model:'DeepSeek V3', context:'128000', modality:['text','reasoning'], license:'mit', status:'online', canonicalModelId:'curated/deepseek-v3', description:'高性能开源模型，在数学、代码和中文理解方面表现突出。', badges:['热门'], featured:true, featuredOrder:4, directoryHref:'/models/all/' },
    { id:'curated/mimo/mimo-v2-6-flash', providerId:'mimo', provider:'MiMo', model:'MiMo V2.6 Flash', context:'1000000', modality:['text','image','audio'], license:'apache-2.0', status:'online', canonicalModelId:'curated/mimo-v2-6-flash', description:'支持 1M 超长上下文的多模态模型，现有限时免费入口。', badges:['限时免费'], featured:true, featuredOrder:5, directoryHref:'/models/mimo-v2-6-flash/' }
  ];
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
  const modelKey = (value) => normalize(value).replace(/[^a-z0-9]/g, '');
  const matchingFreeOffer = (row) => {
    const name = modelKey(row.model);
    if (name.length < 5) return null;
    return state.offers.find((offer) => {
      const types = Array.isArray(offer.type) ? offer.type : [];
      const capabilities = Array.isArray(offer.capabilities) ? offer.capabilities : [];
      if (!types.includes('free') || !capabilities.includes('model_api')) return false;
      const models = Array.isArray(offer.freeModels) && offer.freeModels.length
        ? offer.freeModels.map((entry) => entry && entry.model)
        : [offer.model];
      return models.some((model) => {
        const offered = modelKey(model);
        return offered.length >= 5 && (offered === name || (offered.length > 8 && name.length > 8 && (offered.includes(name) || name.includes(offered))));
      });
    }) || null;
  };
  const hasFreeOffer = (row) => Boolean(row.isFree || ['trial','permanent','limited'].includes(row.tierType) || matchingFreeOffer(row));
  const byId = (id) => state.models.find((item) => item.key === id);
  const groupModels = (rows) => {
    const groups = new Map();
    rows.forEach((row) => {
      const key = row.canonicalModelId || normalize(row.model);
      if (!groups.has(key)) groups.set(key, { key, model: row.model, provider: row.provider, providers: [], context: row.context, modality: [], status: row.status, sourceKind: row.sourceKind, accessRegion: row.accessRegion || '', license: row.license || '', released: row.released || '', canonicalModelId: row.canonicalModelId || '', description: row.description || '', score: row.score || 0, rateLimit: row.rateLimit || '', usageActivity: row.usageActivity || '', tierType: row.tierType || '', directoryHref: row.directoryHref || '', featured: Boolean(row.featured), featuredOrder: Number.isFinite(row.featuredOrder) ? row.featuredOrder : 999, badges: row.badges || [], records: [] });
      const item = groups.get(key);
      item.records.push(row);
      if (!item.providers.includes(row.provider)) item.providers.push(row.provider);
      if (contextValue(row.context) > contextValue(item.context)) item.context = row.context;
      (row.modality || []).forEach((m) => { if (!item.modality.includes(m)) item.modality.push(m); });
      if (row.status === 'online') item.status = 'online';
      if (!item.accessRegion && row.accessRegion) item.accessRegion = row.accessRegion;
      if (row.released && (!item.released || row.released > item.released)) item.released = row.released;
      if (row.sourceKind === 'official') item.sourceKind = 'official';
      if (!item.description && row.description) item.description = row.description;
      if (!item.license && row.license) item.license = row.license;
      item.score = Math.max(item.score, Number(row.score || 0));
      if (!item.rateLimit && row.rateLimit) item.rateLimit = row.rateLimit;
      if (!item.usageActivity && row.usageActivity) item.usageActivity = row.usageActivity;
      if (row.featured) item.featured = true;
      if (Number.isFinite(row.featuredOrder)) item.featuredOrder = row.featuredOrder;
    });
    return [...groups.values()].map((item, index) => {
      item.key = String(item.key || index);
      item.hasFree = item.records.some(hasFreeOffer);
      if (!item.accessRegion) {
        const matched = item.records.map((row) => matchingFreeOffer(row)).find(Boolean);
        if (matched && matched.originCountry) item.accessRegion = /china|中国|国内/i.test(matched.originCountry) ? 'domestic' : 'international';
      }
      item.href = item.directoryHref || modelHref(item.records[0]);
      item.tierType = item.records.some((row) => row.tierType === 'trial') ? 'trial' : item.tierType;
      return item;
    });
  };
  const cardHtml = (item) => {
    const mark = (item.provider || 'AI').trim().slice(0, 2).toUpperCase();
    const licenseLabels = { commercial: '商业授权', 'apache-2.0': 'Apache 2.0', mit: 'MIT' };
    const tags = [contextLabel(item.context), modalitiesLabel(item.modality).split(' · ')[0], licenseLabels[item.license] || (item.providers.length > 1 ? item.providers.length + ' 个入口' : regionLabel(item.accessRegion))];
    const label = item.featured ? (item.badges[0] || '精选') : item.hasFree ? (item.tierType === 'trial' ? '免费试用' : '免费入口') : (item.status === 'online' ? '可查询' : '待核验');
    const description = item.description || modalitiesLabel(item.modality) + '模型，最高 ' + contextLabel(item.context) + ' 上下文。';
    const metrics = [item.score ? '<span>指数 ' + esc(item.score) + '</span>' : '', item.usageActivity ? '<span>↗ ' + esc(item.usageActivity) + '</span>' : '', item.rateLimit ? '<span>⚡ ' + esc(item.rateLimit) + '</span>' : ''].filter(Boolean).join('');
    return '<article class="ml-model-card"><div class="ml-model-card-top"><span class="ml-provider-mark" aria-hidden="true">' + esc(mark) + '</span><div class="ml-card-title"><small>' + esc(item.provider) + (item.providers.length > 1 ? ' +' + (item.providers.length - 1) : '') + '</small><h3>' + esc(item.model) + '</h3></div><span class="ml-status-badge">' + esc(label) + '</span></div><p>' + esc(description) + '</p><div class="ml-model-tags">' + tags.map((tag) => '<span>' + esc(tag) + '</span>').join('') + '</div><div class="ml-card-actions"><span class="ml-card-stats">' + metrics + '</span><a href="' + esc(item.href) + '" data-model-id="' + esc(item.key) + '">查看详情 →</a><button type="button" data-compare-id="' + esc(item.key) + '" aria-pressed="' + state.compare.includes(item.key) + '">' + (state.compare.includes(item.key) ? '✓ 已加入' : '＋ 对比') + '</button></div></article>';
  };
  const sortModels = (items) => {
    const sort = $('#ml-sort').value;
    return items.sort((a, b) => {
      if (sort === 'featured') {
        return Number(Boolean(b.featured)) - Number(Boolean(a.featured))
          || (a.featured ? a.featuredOrder - b.featuredOrder : 0)
          || Number(Boolean(b.hasFree)) - Number(Boolean(a.hasFree))
          || Number(b.status === 'online') - Number(a.status === 'online')
          || contextValue(b.context) - contextValue(a.context)
          || String(b.released).localeCompare(String(a.released))
          || a.model.localeCompare(b.model);
      }
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
    const license = $('#ml-license') ? $('#ml-license').value : '';
    const terms = normalize([item.model, item.provider, item.providers.join(' '), modalitiesLabel(item.modality), item.canonicalModelId].join(' '));
    const n = contextValue(item.context);
    const textMatch = !q || terms.includes(q);
    const providerMatch = !provider || item.providers.includes(provider);
    const modalityMatch = !modality || item.modality.includes(modality);
    const categoryMatch = !state.category || (state.category === 'multimodal' ? item.modality.filter((m) => m !== 'text').length > 0 : item.modality.includes(state.category));
    const contextMatch = !context || (context === 'short' && n > 0 && n < 32000) || (context === 'medium' && n >= 32000 && n < 128000) || (context === 'long' && n >= 128000) || (context === 'million' && n >= 1000000);
    const freeMatch = !free || (free === 'yes' ? item.hasFree : !item.hasFree);
    const regionMatch = !region || (region === 'domestic' ? item.accessRegion === 'domestic' : region === 'international' ? ['global','international'].includes(item.accessRegion) : !item.accessRegion);
    const licenseMatch = !license || (item.license || '').toLowerCase() === license;
    return textMatch && providerMatch && modalityMatch && categoryMatch && contextMatch && freeMatch && regionMatch && licenseMatch;
  };
  const renderCards = (resetPage) => {
    if (resetPage) state.page = 1;
    const items = sortModels(state.models.filter(matches));
    const shown = items.slice(0, state.page * state.pageSize);
    $('#ml-card-grid').innerHTML = shown.length ? shown.map(cardHtml).join('') : '<div class="ml-empty-state">没有找到符合条件的模型，试试清空筛选。</div>';
    $('#ml-results-status').textContent = '显示 ' + shown.length + ' / ' + items.length + ' 款精选模型';
    $('#ml-total').textContent = '(' + state.models.length + ')';
    let more = root.querySelector('#ml-load-more');
    if (!more) {
      const wrap = root.querySelector('.ml-load-more-wrap');
      wrap.innerHTML = '<button class="ml-load-more" id="ml-load-more" type="button">加载更多模型 ↓</button>';
      more = $('#ml-load-more');
    }
    more.textContent = shown >= items.length ? '已显示全部模型' : '加载更多模型 ↓';
    more.disabled = shown >= items.length;
    more.hidden = false;
    if (shown.length >= items.length) more.hidden = true;
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
    const licenseSelect = $('#ml-license');
    if (licenseSelect) {
      const licenses = [...new Set(state.models.map((item) => item.license).filter(Boolean))].sort();
      licenseSelect.innerHTML = '<option value="">全部</option>' + licenses.map((license) => '<option value="' + esc(license) + '">' + esc(license.toUpperCase()) + '</option>').join('');
    }
    ['ml-search','ml-provider','ml-modality','ml-context','ml-free','ml-region','ml-license','ml-sort'].forEach((id) => {
      const el = document.getElementById(id);
      if (el && !el.disabled) el.addEventListener(id === 'ml-search' ? 'input' : 'change', () => renderCards(true));
    });
    root.querySelectorAll('[data-category]').forEach((button) => button.addEventListener('click', () => {
      state.category = button.dataset.category;
      root.querySelectorAll('[data-category]').forEach((tab) => tab.classList.toggle('active', tab === button));
      renderCards(true);
    }));
    $('#ml-reset').addEventListener('click', () => {
      ['ml-search','ml-provider','ml-modality','ml-context','ml-free','ml-region','ml-license'].forEach((id) => {
        const control = document.getElementById(id);
        if (control) control.value = '';
      });
      state.category = '';
      root.querySelectorAll('[data-category]').forEach((tab) => tab.classList.toggle('active', !tab.dataset.category));
      renderCards(true);
    });
    $('#ml-clear-compare').addEventListener('click', () => { state.compare = []; renderCompare(); });
    $('#ml-clear-recent').addEventListener('click', () => { state.recent = []; try { localStorage.removeItem('freellm-model-library-recent'); } catch (_) {} renderRecent(); });
    $('#ml-compare-start').addEventListener('click', startCompare);
    root.addEventListener('click', (event) => {
      if (event.target.closest('#ml-load-more')) {
        state.page += 1;
        renderCards(false);
      }
    });
    document.querySelectorAll('[data-ml-theme]').forEach((button) => {
      button.addEventListener('click', () => {
        const dark = button.dataset.mlTheme === 'dark';
        if (dark) document.documentElement.dataset.theme = 'dark';
        else delete document.documentElement.dataset.theme;
        try { localStorage.setItem('freellm-theme', dark ? 'dark' : ''); } catch (_) {}
        document.querySelectorAll('[data-ml-theme]').forEach((item) => item.classList.toggle('is-active', item === button));
      });
    });
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
  const EMBEDDED_MODEL_FALLBACK = [
 {"id":"puter/mimo-v2-6-flash","providerId":"puter","provider":"Puter.js","model":"MiMo-V2.6-Flash","context":"1000000","modality":["text","image","video","audio","reasoning"],"status":"online","sourceKind":"official","canonicalModelId":"mimo-v2.6-flash","accessRegion":"global","released":"2026-09-22"},
 {"id":"opencode/mimo-v2-6-flash-free","providerId":"opencode","provider":"OpenCode Zen","model":"MiMo-V2.6-Flash Free","context":"1000000","modality":["text","image","video","audio","reasoning"],"status":"online","sourceKind":"official","canonicalModelId":"mimo-v2.6-flash","accessRegion":"international","released":"2026-09-22"},
 {"id":"siliconflow/xing4-0-29b","providerId":"siliconflow","provider":"SiliconFlow","model":"Xing4.0-29B","context":"262144","modality":["text","reasoning"],"status":"online","sourceKind":"official","canonicalModelId":"xing4-0-29b","accessRegion":"domestic","released":"2026-09-20"},
 {"id":"llm7/glm-5-3-flash","providerId":"llm7-io","provider":"LLM7","model":"GLM-5.3-Flash","context":"","modality":["unknown"],"status":"online","sourceKind":"official","canonicalModelId":"glm-5-3-flash","released":"2026-09-21"},
 {"id":"amd/deepseek-v4-flash","providerId":"amd-radeon-cloud","provider":"AMD Radeon Cloud","model":"DeepSeek-V4-Flash","context":"1048576","modality":["text","reasoning"],"status":"online","sourceKind":"official","canonicalModelId":"deepseek-v4-flash","accessRegion":"domestic","released":"2026-09-18"},
 {"id":"xiaomi/kimi-k3","providerId":"xiaomi-mimo","provider":"Xiaomi MiMo","model":"Kimi-K3","context":"262144","modality":["text","image","reasoning"],"status":"online","sourceKind":"official","canonicalModelId":"kimi-k3","accessRegion":"global","released":"2026-09-17"}
];
  const loadData = async () => {
    try {
      const modelTask = fetch('/data/freellm-net-models.json?v=20261001b').then((response) => {
        if (!response.ok) throw new Error('freellm.net model snapshot unavailable');
        return response.json();
      });
      const offerTask = fetch('/data/offers.json').then((response) => {
        if (!response.ok) throw new Error('offer JSON unavailable');
        return response.json();
      }).catch(() => []);
      const snapshot = await modelTask;
      const directoryModels = Array.isArray(snapshot.models) ? snapshot.models : [];
      const rawModels = CURATED_MODELS;
      if (!Array.isArray(snapshot.models) || !snapshot.models.length) throw new Error('freellm.net snapshot is empty');
      state.offers = await offerTask;
      state.all = rawModels;
      state.models = groupModels(rawModels);
      const modelCount = document.getElementById('ml-model-count');
      const providerCount = document.getElementById('ml-provider-count');
      if (modelCount) modelCount.textContent = directoryModels.length;
      if (providerCount) providerCount.textContent = new Set(directoryModels.map((item) => item.providerId).filter(Boolean)).size;
      if ($('#ml-offer-count') && state.offers.length) $('#ml-offer-count').textContent = state.offers.length;
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
