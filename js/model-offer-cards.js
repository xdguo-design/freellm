(() => {
  const grid = document.getElementById('ml-card-grid');
  const total = document.getElementById('ml-total');
  const status = document.getElementById('ml-results-status');
  const loadMore = document.getElementById('ml-load-more');
  const pageSize = 6;
  let entries = [];
  let shown = 0;

  if (!grid) return;

  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  };

  const freeLabel = (offer) => {
    const terms = `${offer.validitySummary || ''} ${offer.accessSummary || ''} ${offer.freeMechanism || ''}`.toLowerCase();
    if (/application|applicant|eligib|申请|审核|准入|仅限|定向/.test(terms)) return '定向免费';
    const mechanismLabels = {
      permanent: '长期免费',
      always_on: '常驻免费',
      limited_time_free: '限时免费',
      trial: '免费试用',
      daily_quota: '每日额度',
      monthly_quota: '月度额度',
      not_confirmed: '资格待核验',
    };
    if (mechanismLabels[offer.freeMechanism]) return mechanismLabels[offer.freeMechanism];
    if (/always|ongoing|常驻|长期|永久/.test(terms)) return '持续免费';
    return '限时免费';
  };

  const modelEntries = (offers) => {
    const entries = offers
      .filter((offer) => Array.isArray(offer.type) && offer.type.includes('free'))
      .filter((offer) => Array.isArray(offer.capabilities) && offer.capabilities.includes('model_api'))
      .sort((a, b) => Number(b.order || 0) - Number(a.order || 0))
      .flatMap((offer) => {
        const models = Array.isArray(offer.freeModels) && offer.freeModels.length
          ? offer.freeModels
          : [{ model: offer.model, label: offer.modelMeta, contextWindow: offer.contextWindow, quota: offer.quota }];
        return models.filter((model) => model && model.model).map((model, index) => ({ offer, model, index }));
      });
    const featuredIds = ['amd-radeon-cloud-free', 'baichuan-m3-plus-medical-free'];
    const featuredFirst = featuredIds.flatMap((id) => entries.filter((entry) => entry.offer.id === id && entry.index === 0));
    const featuredRest = entries.filter((entry) => featuredIds.includes(entry.offer.id) && entry.index !== 0);
    const otherEntries = entries.filter((entry) => !featuredIds.includes(entry.offer.id));
    return [...featuredFirst, ...featuredRest, ...otherEntries];
  };

  const renderCard = ({ offer, model }) => {
    const article = make('article', 'ml-model-card');
    const head = make('div', 'ml-card-head');
    const mark = make('span', 'ml-logo', offer.providerMark || (offer.provider || 'AI').slice(0, 2));
    mark.setAttribute('aria-hidden', 'true');
    const identity = make('div', 'ml-card-id');
    identity.append(make('small', '', offer.provider || '模型服务商'));
    identity.append(make('h3', '', model.model));
    const flag = make('span', 'ml-card-flag flag-purple', freeLabel(offer));
    head.append(mark, identity, flag);

    const access = offer.accessSummary || offer.freeSummary || (offer.usageGuide && offer.usageGuide.summary) || offer.validitySummary || '免费资格与调用限制以官方入口说明为准。';
    const description = make('p', 'ml-card-desc', access);
    const quota = model.quota || offer.quota;
    const quotaLine = quota ? make('p', 'ml-card-quota', `额度与限制：${quota}`) : null;
    const tags = make('div', 'ml-card-tags');
    [model.label, model.contextWindow, offer.originCountry].filter(Boolean).slice(0, 3).forEach((tag) => tags.append(make('span', '', tag)));
    const foot = make('div', 'ml-card-foot');
    const link = make('a', 'ml-card-cta', '查看入口详情');
    link.href = `/offers/${encodeURIComponent(offer.id)}/`;
    link.append(make('i', '', '→'));
    foot.append(link);
    article.append(head, description);
    if (quotaLine) article.append(quotaLine);
    article.append(tags, foot);
    return article;
  };

  const renderNextPage = () => {
    const fragment = document.createDocumentFragment();
    entries.slice(shown, shown + pageSize).forEach((entry) => fragment.append(renderCard(entry)));
    grid.append(fragment);
    shown = Math.min(shown + pageSize, entries.length);
    grid.setAttribute('aria-busy', 'false');
    if (total) total.textContent = `(${entries.length})`;
    if (status) status.textContent = `已收录 ${entries.length} 个免费模型入口；资格与额度详见入口详情。`;
    if (loadMore) loadMore.hidden = shown >= entries.length;
  };

  if (loadMore) loadMore.addEventListener('click', renderNextPage);
  fetch('/data/offers.json')
    .then((response) => {
      if (!response.ok) throw new Error('offer data unavailable');
      return response.json();
    })
    .then((offers) => {
      entries = modelEntries(Array.isArray(offers) ? offers : []);
      grid.replaceChildren();
      if (!entries.length) {
        grid.append(make('p', 'ml-empty-state', '暂时没有可展示的免费模型入口。'));
        grid.setAttribute('aria-busy', 'false');
        if (total) total.textContent = '(0)';
        if (status) status.textContent = '暂时没有免费模型 API 入口。';
        if (loadMore) loadMore.hidden = true;
        return;
      }
      renderNextPage();
    })
    .catch(() => {
      grid.replaceChildren(make('p', 'ml-empty-state', '模型入口暂时无法加载，请稍后重试。'));
      grid.setAttribute('aria-busy', 'false');
      if (status) status.textContent = '模型入口暂时无法加载。';
      if (loadMore) loadMore.hidden = true;
    });
})();
