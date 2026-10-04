(() => {
  function filterModels(models, filters = {}) {
    const region = filters.region || 'all';
    const capability = filters.capability || 'all';
    return models.filter(model => {
      const modelCapabilities = Array.isArray(model.capabilities) ? model.capabilities : [];
      const regionMatches = region === 'all' || model.region === region
        || ((region === 'domestic' || region === 'international') && model.region === 'both');
      return regionMatches
        && (capability === 'all' || modelCapabilities.includes(capability));
    });
  }

  function addComparedModel(selected, modelId, limit = 3) {
    const current = [...new Set(selected)];
    if (current.includes(modelId)) return { accepted: true, selected: current };
    if (current.length >= limit) return { accepted: false, selected: current };
    return { accepted: true, selected: [...current, modelId] };
  }

  function benchmarksComparable(first, second) {
    return Boolean(first && second
      && first.protocolVersion && first.protocolVersion === second.protocolVersion
      && first.taskId && first.taskId === second.taskId
      && first.language && first.language === second.language
      && first.samplingMode && first.samplingMode === second.samplingMode
      && String(first.temperature) === String(second.temperature)
      && first.region && first.region === second.region);
  }

  const featuredModelApi = { addComparedModel, benchmarksComparable, filterModels };
  if (typeof module !== 'undefined' && module.exports) module.exports = featuredModelApi;
  if (typeof document === 'undefined') return;

  const grid = document.getElementById('featured-model-grid');
  if (!grid) return;

  document.querySelectorAll('.brand-icon-image').forEach(image => {
    const mark = image.closest('.featured-model-mark, .featured-agent-mark');
    const showImage = () => mark?.classList.add('has-brand-image');
    image.addEventListener('load', showImage, { once: true });
    image.addEventListener('error', () => {
      if (image.dataset.directFallback !== 'true' && image.dataset.iconHost) {
        image.dataset.directFallback = 'true';
        image.src = `https://${image.dataset.iconHost}/favicon.ico`;
        return;
      }
      image.remove();
    });
    if (image.complete && image.naturalWidth > 0) showImage();
  });

  const cards = Array.from(grid.querySelectorAll('.featured-model-card'));
  const agentCards = Array.from(document.querySelectorAll('.featured-agent-card'));
  const filterButtons = Array.from(document.querySelectorAll('[data-model-filter]'));
  const search = document.getElementById('models-global-search');
  const sort = document.getElementById('models-sort');
  const moreButton = document.getElementById('models-load-more');
  const emptyState = document.querySelector('.models-empty-state');
  const regionFilter = document.getElementById('models-region-filter');
  const capabilityFilter = document.getElementById('models-capability-filter');
  const resultCount = document.getElementById('featured-model-count');
  const clearFiltersButton = document.querySelector('[data-clear-featured-filters]');
  const comparison = document.getElementById('featured-model-comparison');
  const comparisonCount = document.getElementById('featured-model-compare-count');
  const comparisonStatus = document.getElementById('featured-model-compare-status');
  const comparisonRows = comparison?.querySelector('[data-comparison-rows]');
  const selectedModelIds = new Set();
  const agentSection = document.getElementById('agent-picks');
  const agentGrid = agentSection?.querySelector('.featured-agent-grid');
  const pageSize = 8;
  const collator = new Intl.Collator(document.documentElement.lang || 'zh-CN', { sensitivity: 'base', numeric: true });
  let activeFilter = 'all';
  let visibleLimit = pageSize;

  cards.forEach((card, index) => { card.dataset.featuredIndex = String(index); });

  function update() {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    const categoryAndSearchMatches = cards.filter(card => {
      const categories = (card.dataset.modelCategories || '').split(/\s+/);
      const textMatches = !query || (card.dataset.searchText || '').toLocaleLowerCase().includes(query);
      return (activeFilter === 'all' || categories.includes(activeFilter)) && textMatches;
    });
    const matching = filterModels(categoryAndSearchMatches.map(card => ({
      id: card.dataset.modelId,
      region: card.dataset.region || 'unknown',
      capabilities: (card.dataset.capabilities || '').split(/\s+/).filter(Boolean),
      card,
    })), { region: regionFilter?.value || 'all', capability: capabilityFilter?.value || 'all' })
      .map(model => model.card);

    const ordered = [...matching];
    if (sort?.value === 'name') {
      ordered.sort((a, b) => collator.compare(a.querySelector('h3')?.textContent || '', b.querySelector('h3')?.textContent || ''));
    } else {
      ordered.sort((a, b) => Number(a.dataset.featuredIndex) - Number(b.dataset.featuredIndex));
    }

    const visibleCards = new Set(ordered.slice(0, visibleLimit));
    cards.forEach(card => {
      if (ordered.includes(card)) grid.appendChild(card);
      card.hidden = !visibleCards.has(card);
    });
    if (emptyState) emptyState.hidden = ordered.length !== 0;
    if (moreButton) {
      moreButton.hidden = ordered.length <= visibleLimit;
      moreButton.disabled = ordered.length <= visibleLimit;
    }
    if (resultCount) {
      const isEnglish = document.documentElement.lang.toLowerCase().startsWith('en');
      resultCount.textContent = isEnglish ? `Showing ${ordered.length} / ${cards.length}` : `显示 ${ordered.length} / ${cards.length}`;
    }

    let visibleAgents = 0;
    agentCards.forEach(card => {
      const matches = !query || (card.dataset.searchText || '').toLocaleLowerCase().includes(query);
      card.hidden = !matches;
      if (matches) visibleAgents += 1;
    });
    if (agentSection) agentSection.hidden = Boolean(query) && visibleAgents === 0;
    if (agentGrid) agentGrid.setAttribute('aria-label', `${visibleAgents} AI agents`);
  }

  function benchmarkFrom(card) {
    const values = card.dataset;
    if (!values.benchmarkProtocol || !values.benchmarkTask || !values.benchmarkLanguage
      || !values.benchmarkTtft || !values.benchmarkTokensPerSecond) return null;
    return {
      protocolVersion: values.benchmarkProtocol,
      taskId: values.benchmarkTask,
      language: values.benchmarkLanguage,
      samplingMode: values.benchmarkSamplingMode,
      temperature: values.benchmarkTemperature,
      ttftMs: values.benchmarkTtft,
      tokensPerSecond: values.benchmarkTokensPerSecond,
      region: values.benchmarkRegion,
      testedAt: values.benchmarkDate,
    };
  }

  function formatLimit(value) {
    if (!value) return '—';
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount <= 0) return value;
    const isEnglish = document.documentElement.lang.toLowerCase().startsWith('en');
    return `${amount.toLocaleString(isEnglish ? 'en-US' : 'zh-CN')} ${isEnglish ? 'tokens' : 'tokens'}`;
  }

  function renderComparison() {
    if (!comparison || !comparisonRows) return;
    const selected = cards.filter(card => selectedModelIds.has(card.dataset.modelId));
    comparison.hidden = selected.length === 0;
    if (comparisonCount) comparisonCount.textContent = `${selected.length} / 3`;
    comparison.querySelectorAll('[data-compare-column]').forEach((heading, index) => {
      heading.textContent = selected[index]?.dataset.modelName || '';
    });
    comparisonRows.replaceChildren();

    const labels = {
      model: ['模型', 'Model'], provider: ['服务商', 'Provider'], region: ['接入地区', 'Verified region'],
      capability: ['能力', 'Capabilities'], ttft: ['首 token 延迟', 'TTFT'],
      tokens: ['生成速度', 'Generation speed'], benchmark: ['实测地区 / 日期', 'Test region / date'],
      context: ['上下文', 'Context'], output: ['最大输出', 'Max output'], source: ['官方来源', 'Official source'],
    };
    const rows = [
      ['model', card => card.dataset.modelName || '—'],
      ['provider', card => card.dataset.provider || '—'],
      ['region', card => card.dataset.regionLabel || '待核实'],
      ['capability', card => card.querySelector('.featured-model-chips')?.innerText.trim() || '—'],
      ['ttft', (card, index) => {
        const bench = benchmarkFrom(card);
        const base = selected.length > 1 ? benchmarkFrom(selected[0]) : null;
        if (!bench) return '未实测';
        if (index > 0 && selected.length > 1 && (!base || !benchmarksComparable(base, bench))) return '不可直接比较';
        return `${bench.ttftMs} ms`;
      }],
      ['tokens', (card, index) => {
        const bench = benchmarkFrom(card);
        const base = selected.length > 1 ? benchmarkFrom(selected[0]) : null;
        if (!bench) return '未实测';
        if (index > 0 && selected.length > 1 && (!base || !benchmarksComparable(base, bench))) return '不可直接比较';
        return `${bench.tokensPerSecond} tokens/s`;
      }],
      ['benchmark', card => {
        const bench = benchmarkFrom(card);
        const isEnglish = document.documentElement.lang.toLowerCase().startsWith('en');
        return bench ? `${bench.region === 'domestic' ? (isEnglish ? 'Mainland China' : '中国大陆') : (isEnglish ? 'International' : '海外')} · ${bench.testedAt}` : (isEnglish ? 'Not tested' : '未实测');
      }],
      ['context', card => formatLimit(card.dataset.context)],
      ['output', card => formatLimit(card.dataset.maxOutput)],
      ['source', card => card.dataset.sourceUrl || '—'],
    ];
    const isEnglish = document.documentElement.lang.toLowerCase().startsWith('en');
    rows.forEach(([key, getValue]) => {
      const row = document.createElement('tr');
      const label = document.createElement('th');
      label.scope = 'row';
      label.textContent = labels[key][isEnglish ? 1 : 0];
      row.appendChild(label);
      selected.forEach((card, index) => {
        const cell = document.createElement('td');
        const value = getValue(card, index);
        if (key === 'source' && /^https?:\/\//i.test(value)) {
          const link = document.createElement('a');
          link.href = value;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = isEnglish ? 'Open source ↗' : '打开来源 ↗';
          cell.appendChild(link);
        } else {
          cell.textContent = value;
        }
        row.appendChild(cell);
      });
      comparisonRows.appendChild(row);
    });
  }

  function setCompareButtonState(button, selected) {
    button.setAttribute('aria-pressed', String(selected));
    button.querySelectorAll('[data-compare-add]').forEach(label => { label.hidden = selected; });
    button.querySelectorAll('[data-compare-remove]').forEach(label => { label.hidden = !selected; });
  }

  cards.forEach(card => {
    const button = card.querySelector('[data-compare-toggle]');
    if (!button) return;
    button.addEventListener('click', () => {
      const modelId = card.dataset.modelId;
      if (selectedModelIds.has(modelId)) {
        selectedModelIds.delete(modelId);
        setCompareButtonState(button, false);
        if (comparisonStatus) comparisonStatus.textContent = '';
      } else {
        const result = addComparedModel([...selectedModelIds], modelId, 3);
        if (!result.accepted) {
          if (comparisonStatus) comparisonStatus.textContent = document.documentElement.lang.toLowerCase().startsWith('en')
            ? 'Compare up to 3 models. Remove one before adding another.'
            : '最多比较 3 个模型，请先移除一项。';
          return;
        }
        selectedModelIds.add(modelId);
        setCompareButtonState(button, true);
        if (comparisonStatus) comparisonStatus.textContent = '';
      }
      renderComparison();
    });
  });

  comparison?.querySelector('[data-clear-comparison]')?.addEventListener('click', () => {
    selectedModelIds.clear();
    cards.forEach(card => {
      const button = card.querySelector('[data-compare-toggle]');
      if (button) setCompareButtonState(button, false);
    });
    if (comparisonStatus) comparisonStatus.textContent = '';
    renderComparison();
  });

  clearFiltersButton?.addEventListener('click', () => {
    if (regionFilter) regionFilter.value = 'all';
    if (capabilityFilter) capabilityFilter.value = 'all';
    if (search) search.value = '';
    activeFilter = 'all';
    visibleLimit = pageSize;
    filterButtons.forEach(button => {
      const active = button.dataset.modelFilter === 'all';
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    update();
  });

  filterButtons.forEach(button => button.addEventListener('click', () => {
    activeFilter = button.dataset.modelFilter || 'all';
    visibleLimit = pageSize;
    filterButtons.forEach(item => {
      const active = item === button;
      item.classList.toggle('is-active', active);
      item.setAttribute('aria-pressed', String(active));
    });
    update();
  }));

  search?.addEventListener('input', () => { visibleLimit = pageSize; update(); });
  sort?.addEventListener('change', () => { visibleLimit = pageSize; update(); });
  regionFilter?.addEventListener('change', () => { visibleLimit = pageSize; update(); });
  capabilityFilter?.addEventListener('change', () => { visibleLimit = pageSize; update(); });
  moreButton?.addEventListener('click', () => { visibleLimit += pageSize; update(); });

  document.querySelectorAll('[data-model-view]').forEach(button => button.addEventListener('click', () => {
    const list = button.dataset.modelView === 'list';
    grid.classList.toggle('is-list', list);
    document.querySelectorAll('[data-model-view]').forEach(item => {
      const active = item === button;
      item.classList.toggle('is-active', active);
      item.setAttribute('aria-pressed', String(active));
    });
  }));

  update();
})();
