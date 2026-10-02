/* Model library: 精选模型 comes from the homepage offer ranking (/data/offers-ranked.json);
   category tabs browse the local freellm.net snapshot. Every number renders from real data. */
(() => {
  const root = document.getElementById('model-library-app');
  if (!root) return;
  const $ = (selector) => root.querySelector(selector);
  const state = { featured: [], models: [], all: [], offers: [], category: '', page: 1, pageSize: 6, compare: [], recent: [], offerPage: 1 };
  const OFFER_PAGE_SIZE = 12;
  const NETWORK_REGION_LABELS = { both: '国内外均可用', cn: '仅国内可用', intl: '仅国外可用' };
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
  const BRAND_TOKENS = { deepseek:'DeepSeek', glm:'GLM', kimi:'Kimi', qwen:'Qwen', mimo:'MiMo', gemma:'Gemma', gemini:'Gemini', llama:'Llama', mistral:'Mistral', llm:'LLM', api:'API', ai:'AI', tts:'TTS', ocr:'OCR', rag:'RAG', agi:'AGI', vlm:'VLM', coder:'Coder' };
  const prettifyModel = (value) => {
    const raw = String(value || '').trim();
    if (!raw) return '未命名模型';
    if (raw.includes('/') || /[\u4e00-\u9fff]/.test(raw)) return raw;
    return raw.split(/[-_\s]+/).filter(Boolean).map((token) => {
      const lower = token.toLowerCase();
      if (BRAND_TOKENS[lower]) return BRAND_TOKENS[lower];
      if (/^\d+(\.\d+)?[bkm]?$/i.test(token)) return token.toUpperCase();
      return token.charAt(0).toUpperCase() + token.slice(1);
    }).join(' ');
  };
  const markHue = (value) => {
    const text = String(value || 'ai');
    let hash = 0;
    for (let i = 0; i < text.length; i += 1) hash = (hash * 31 + text.charCodeAt(i)) % 360;
    return hash;
  };
  const logoStyle = (hue, mark) => {
    const text = String(mark || '');
    const cjk = /[\u4e00-\u9fff]/.test(text);
    const size = cjk ? 12 : (text.length >= 3 ? 11 : '');
    return 'background:linear-gradient(145deg,hsl(' + hue + ',78%,95%),hsl(' + hue + ',68%,86%));color:hsl(' + hue + ',52%,36%)' + (size ? ';--ml-logo-size:' + size + 'px' : '');
  };
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
      if (!groups.has(key)) groups.set(key, { key, model: row.model, provider: row.provider, providers: [], context: row.context, modality: [], status: row.status, sourceKind: row.sourceKind, accessRegion: row.accessRegion || '', license: row.license || '', released: row.released || '', canonicalModelId: row.canonicalModelId || '', description: row.description || '', score: row.score || 0, rateLimit: row.rateLimit || '', usageActivity: row.usageActivity || '', tierType: row.tierType || '', directoryHref: row.directoryHref || '', noCard: false, verified: false, records: [] });
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
      if (row.noCard) item.noCard = true;
      if (row.verified) item.verified = true;
      if (row.tierType === 'limited') item.tierType = 'limited';
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
  const buildFeatured = (rows) => (Array.isArray(rows) ? rows : [])
    .filter((offer) => Array.isArray(offer.capabilities) && offer.capabilities.includes('model_api')
      && Array.isArray(offer.type) && offer.type.includes('free'))
    .sort((a, b) => Number(b.rankingScore || 0) - Number(a.rankingScore || 0) || Number(a.order || 0) - Number(b.order || 0));
  const offerField = (value, fallback) => {
    const text = String(value == null ? '' : value).trim();
    return text || fallback;
  };
  const offerTitle = (offer) => offerField(offer.title, offerField(offer.name, '未命名产品')).replace(/\s+/g, ' ');
  const offerNetworkChips = (offer) => {
    const check = offer.networkCheck;
    if (!check || typeof check !== 'object') return [];
    const region = check.region;
    if (!NETWORK_REGION_LABELS[region] && region !== 'none') return [];
    if (region === 'none') return ['<span class="ml-offer-chip is-fail">✗ 本次未连通</span>'];
    const latencies = [];
    if (check.cnMs) latencies.push('国内 ' + check.cnMs + 'ms');
    if (check.intlMs) latencies.push('海外 ' + check.intlMs + 'ms');
    const title = esc('实测于 ' + offerField(check.checkedAt, '近期') + '｜仅实测网络可达性与往返延迟，不代表注册门槛或模型生成速度' + (latencies.length ? '｜' + latencies.join(' · ') : ''));
    return [
      '<span class="ml-offer-chip is-ok" title="' + title + '">✓ 实测通过</span>',
      '<span class="ml-offer-chip is-region">' + esc(NETWORK_REGION_LABELS[region]) + '</span>',
      latencies.length ? '<span class="ml-offer-chip is-speed">' + esc(latencies.join(' · ')) + '</span>' : ''
    ].filter(Boolean);
  };
  const offerFlagChips = (offer) => {
    const chips = [];
    const featured = offer.featured;
    if (featured && typeof featured === 'object' && featured.reason) {
      chips.push('<span class="ml-offer-chip is-featured" title="' + esc('加精｜' + featured.reason) + '">◆ 加精</span>');
    }
    if (offer.key) chips.push('<span class="ml-offer-chip is-key">★ 重点</span>');
    const endpoint = offer.endpointCheck;
    if (endpoint && endpoint.verdict !== 'NETWORK_ERROR') {
      const label = offer.usageGuide && offer.usageGuide.endpoint ? '接口已验证' : '官网已验证';
      const suffix = typeof endpoint.ms === 'number' ? ' · ' + endpoint.ms + 'ms' : '';
      chips.push('<span class="ml-offer-chip is-ok">' + esc('✓ ' + label + suffix) + '</span>');
    }
    return chips.concat(offerNetworkChips(offer));
  };
  const badgeHtml = (badge) => '<span class="ml-card-flag flag-' + badge.tone + '">' + esc(badge.label) + '</span>';
  const featuredCardHtml = (offer) => {
    const mark = String(offer.providerMark || offer.provider || 'AI').trim().slice(0, 4);
    const limited = (Array.isArray(offer.type) && offer.type.includes('promo')) || offer.freeMechanism === 'limited_time_free';
    const href = /^https:\/\//i.test(String(offer.register || '')) ? offer.register : '/offers/' + offer.id + '/';
    const verifiedDate = offerField(offer.lastVerifiedAt, '');
    const verified = offer.status === 'verified' && verifiedDate
      ? '<span class="ml-offer-verified">✓ 已核验 ' + esc(verifiedDate) + '</span>'
      : '<span class="ml-offer-verified is-pending">核验状态：' + esc(offerField(offer.status, 'unknown')) + '</span>';
    const metrics = [
      ['免费方式', offerField(offer.freeSummary, offerField(offer.mechanism, '见官方条款'))],
      ['额度 / 价格', offerField(offer.quota, '以官方页面为准')],
      ['有效期', offerField(offer.validitySummary, offerField(offer.validity, '见官方条款'))],
      ['地区', offerField(offer.accessSummary, offerField(offer.access, '见官方条款'))]
    ];
    return '<article class="ml-offer-card">'
      + '<div class="ml-offer-head"><span class="ml-logo" style="' + logoStyle(markHue(offer.provider || offer.id), mark) + '" aria-hidden="true">' + esc(mark) + '</span>'
      + '<div class="ml-offer-title"><strong title="' + esc(offerTitle(offer)) + '">' + esc(offerTitle(offer)) + '</strong>'
      + '<small>' + esc(offerField(offer.provider, '官方入口')) + '</small></div>'
      + badgeHtml(limited ? { label: '限时免费', tone: 'orange' } : { label: '免费 API', tone: 'green' }) + '</div>'
      + '<div class="ml-offer-flags">' + offerFlagChips(offer).join('') + '</div>'
      + '<div class="ml-offer-metrics">' + metrics.map((metric) => '<div class="ml-offer-metric"><label>' + metric[0] + '</label><p>' + esc(metric[1]) + '</p></div>').join('') + '</div>'
      + '<div class="ml-offer-foot">' + verified
      + '<span class="ml-offer-actions"><a class="ml-offer-detail" href="/offers/' + esc(offer.id) + '/">查看详情 ↗</a>'
      + '<a class="ml-card-cta" href="' + esc(href) + '"' + (/^https:\/\//i.test(href) ? ' target="_blank" rel="noopener"' : '') + '>立即使用 <i>→</i></a></span></div>'
      + '</article>';
  };
  const renderOffers = () => {
    const grid = document.getElementById('ml-offer-grid');
    if (!grid) return;
    const shown = state.featured.slice(0, state.offerPage * OFFER_PAGE_SIZE);
    grid.innerHTML = shown.length
      ? shown.map(featuredCardHtml).join('')
      : '<div class="ml-empty-state">精选入口暂时无法加载，<a href="/models/all/">打开完整模型目录 →</a></div>';
    grid.setAttribute('aria-busy', 'false');
    const count = document.getElementById('ml-offers-count');
    if (count) count.textContent = '显示 ' + shown.length + ' / ' + state.featured.length + ' 个已核验免费入口';
    const more = document.getElementById('ml-offers-more');
    if (more) {
      const exhausted = shown.length >= state.featured.length;
      more.textContent = exhausted ? '已显示全部精选入口' : '显示更多精选入口 ↓（还有 ' + (state.featured.length - shown.length) + ' 个）';
      more.disabled = exhausted;
      more.hidden = exhausted;
    }
  };
  const poolCardHtml = (item) => {
    const providerName = item.providers[0] || item.provider || 'AI';
    const mark = providerName.trim().slice(0, 2).toUpperCase();
    const licenseLabels = { commercial: '商业授权', 'apache-2.0': 'Apache 2.0', mit: 'MIT' };
    const badge = item.tierType === 'limited' ? { label: '限时免费', tone: 'orange' }
      : item.hasFree ? { label: '免费 API', tone: 'green' }
      : { label: '待核验', tone: 'gray' };
    const tags = [
      contextValue(item.context) ? contextLabel(item.context) + ' 上下文' : '上下文待核验',
      modalitiesLabel(item.modality).split(' · ')[0],
      item.license ? (licenseLabels[item.license] || item.license) : '',
      item.noCard ? '无需信用卡' : ''
    ].filter(Boolean).slice(0, 4);
    const facts = [
      item.score ? '<span class="stat-score">热度 ' + esc(item.score) + '</span>' : '',
      item.usageActivity && item.usageActivity !== '—' ? '<span>用量 ' + esc(item.usageActivity) + '</span>' : '',
      item.rateLimit ? '<span class="stat-rate">⚡ ' + esc(item.rateLimit) + '</span>' : ''
    ].join('');
    const selected = state.compare.includes(item.key);
    const displayName = prettifyModel(item.model);
    return '<article class="ml-model-card">'
      + '<div class="ml-card-head"><span class="ml-logo" style="' + logoStyle(markHue(providerName), mark) + '" aria-hidden="true">' + esc(mark) + '</span>'
      + '<div class="ml-card-id"><small>' + esc(item.provider) + (item.providers.length > 1 ? ' +' + (item.providers.length - 1) : '') + '</small><h3 title="' + esc(displayName) + '">' + esc(displayName) + '</h3></div>'
      + badgeHtml(badge) + '</div>'
      + '<p class="ml-card-desc">' + esc(item.description || modalitiesLabel(item.modality) + '模型，最高 ' + contextLabel(item.context) + ' 上下文。') + '</p>'
      + '<div class="ml-card-tags">' + tags.map((tag) => '<span>' + esc(tag) + '</span>').join('') + '</div>'
      + '<div class="ml-card-foot"><span class="ml-card-stats">' + facts + '</span>'
      + '<button class="ml-card-compare" type="button" data-compare-id="' + esc(item.key) + '" aria-pressed="' + selected + '">' + (selected ? '✓ 已加入' : '＋ 对比') + '</button>'
      + '<a class="ml-card-cta" href="' + esc(item.href) + '" target="_blank" rel="noopener" data-model-id="' + esc(item.key) + '">立即使用 <i>→</i></a></div>'
      + '</article>';
  };
  const sortModels = (items) => {
    const sort = $('#ml-sort').value;
    return items.sort((a, b) => {
      if (sort === 'featured') {
        return Number(b.hasFree) - Number(a.hasFree)
          || Number(b.status === 'online') - Number(a.status === 'online')
          || (b.score || 0) - (a.score || 0)
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
    const licenseSelect = document.getElementById('ml-license');
    const license = licenseSelect ? licenseSelect.value : '';
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
    const grid = $('#ml-card-grid');
    const items = sortModels(state.models.filter(matches));
    const shown = items.slice(0, state.page * state.pageSize);
    grid.innerHTML = shown.length ? shown.map(poolCardHtml).join('') : '<div class="ml-empty-state">没有找到符合条件的模型，试试清空筛选。</div>';
    $('#ml-results-status').textContent = '显示 ' + shown.length + ' / ' + items.length + ' 个模型';
    let more = $('#ml-load-more');
    if (!more) {
      const wrap = root.querySelector('.ml-load-more-wrap');
      wrap.innerHTML = '<button class="ml-load-more" id="ml-load-more" type="button">加载更多模型 ↓</button>';
      more = $('#ml-load-more');
    }
    const exhausted = shown.length >= items.length;
    more.textContent = exhausted ? '已显示全部模型' : '加载更多模型 ↓';
    more.disabled = exhausted;
    more.hidden = exhausted;
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
      if (event.target.closest('#ml-offers-more')) {
        state.offerPage += 1;
        renderOffers();
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
          const recent = { id: item.key, name: prettifyModel(item.model), href: item.href, mark: (item.provider || 'AI').slice(0, 1).toUpperCase(), time: '刚刚' };
          state.recent = [recent].concat(state.recent.filter((row) => row.id !== item.key)).slice(0, 5);
          try { localStorage.setItem('freellm-model-library-recent', JSON.stringify(state.recent)); } catch (_) {}
        }
      }
    });
  };
  const loadData = async () => {
    try {
      const rankedTask = fetch('/data/offers-ranked.json?v=20261002a')
        .then((response) => { if (!response.ok) throw new Error('offer ranking unavailable'); return response.json(); })
        .catch(() => []);
      const snapshotTask = fetch('/data/freellm-net-models.json?v=20261002a')
        .then((response) => { if (!response.ok) throw new Error('freellm.net model snapshot unavailable'); return response.json(); });
      const [ranked, snapshot] = await Promise.all([rankedTask, snapshotTask]);
      const directoryModels = Array.isArray(snapshot.models) ? snapshot.models : [];
      if (!directoryModels.length) throw new Error('freellm.net snapshot is empty');
      state.offers = Array.isArray(ranked) ? ranked : (ranked && Array.isArray(ranked.offers) ? ranked.offers : []);
      state.featured = buildFeatured(state.offers);
      state.all = directoryModels;
      state.models = groupModels(directoryModels);
      const modelCount = document.getElementById('ml-model-count');
      const providerCount = document.getElementById('ml-provider-count');
      if (modelCount) modelCount.textContent = state.models.length;
      if (providerCount) providerCount.textContent = new Set(directoryModels.map((item) => item.providerId).filter(Boolean)).size;
      const total = document.getElementById('ml-total');
      if (total) total.textContent = '(' + state.models.length + ')';
      renderOffers();
      let saved = [];
      try { saved = JSON.parse(localStorage.getItem('freellm-model-library-recent') || '[]'); } catch (_) {}
      state.recent = Array.isArray(saved) ? saved.map((entry) => byId(typeof entry === 'string' ? entry : entry && entry.id)).filter(Boolean).map((item) => ({ id:item.key, name:prettifyModel(item.model), href:item.href, mark:(item.provider || 'AI').slice(0,1).toUpperCase(), time:'最近浏览' })) : [];
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
