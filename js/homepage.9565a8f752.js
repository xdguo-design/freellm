let offerIndex = {};
    let signalIndex = {};
    let rows = [];
    let loadedOffers = [];
    const SUPPORTED_LOCALES = Object.freeze({ en: 'en', zh: 'zh-CN' });
    const LOCALE_STORAGE_KEY = 'free-ai-index-locale';
    const LOCALE_COPY = Object.freeze({
      en: Object.freeze({
        pageTitle: 'Free AI Index — Free AI models, Qwen, Doubao, IDEs and trials',
        pageDescription: 'Compare verified free AI models, free coding IDEs, student offers, downloadable open weights and limited-time trials with official access paths.',
        brandSub: 'Verified free AI resources',
        navCatalog: 'Models', navTools: 'Developer tools', navApi: 'API services', navRank: 'Compare', submit: 'Submit a resource',
        verified: 'Verified daily · genuinely free', heroTitle: 'Find truly useful <span>free AI</span>', heroTitleAccent: 'free AI', heroCopy: 'Models, APIs, IDEs and limited trials compared in one place', searchPlaceholder: 'Search models, platforms or capabilities, e.g. DeepSeek, Qwen3', searchLabel: 'Search offers', search: 'Search', hot: 'Popular searches:', freeApi: 'Free API',
        intelTitle: 'What changed in AI today?', intelStoryCopy: 'We check official sources daily and record new, recovered, offline and source issues.', intelLogCta: "See today's changes →", newCount: 'new', changesToday: 'Changes today', noNew: 'No new entries', resourceCount: 'quality resources', checked: 'Human-checked and confirmed free to use', trend: 'vs. last week', forever: 'Free forever', longTerm: 'Long-term access', trial: 'Limited trial', grabChance: 'Use it while it lasts', openWeights: 'Downloadable weights', useFreely: 'Use freely', heroNote: 'Good AI\nshould be easier\nfor more people to use',
        method: 'Free method', capability: 'Capability', chinese: 'Chinese support', updated: 'Last checked', all: 'All', browse: 'Browse by purpose', categoryCopy: 'Categories can overlap; one resource may belong to multiple paths.', allOffers: 'All', largeModels: 'Large models', ide: 'Free IDE', credits: 'Credits / uses', promo: 'Timed / regional deal', web: 'Web tools', download_lowcost: 'Download / low cost', modelCategory: 'Model APIs', regionChipCn: 'China', regionChipIntl: 'Global', featuredChip: '◆ Featured', imageVideo: 'Image / video', apiServices: 'API services', openModels: 'Open models', more: 'More categories',
        popular: 'Popular this week', moreLink: 'See more →', permanent: 'Free forever', limitedTrial: 'Limited trial', downloadable: 'Downloadable', freeQuota: 'Free quota', freePlan: 'Free plan', supportedPlatforms: 'Supported platforms', excellent: 'Excellent', featured: 'Editor pick', seedFeatured: 'An all-purpose conversation and creation assistant with text, image, audio and video generation.', iflyFeatured: 'A Spark X2.5 desktop AI workbench that plans tasks autonomously and delivers documents, web pages and code.', mimoFeatured: 'An invitation-only desktop agent beta with free access to MiMo-X Preview models during the test.', workbuddyFeatured: 'A Tencent office AI agent that completes everyday work tasks with credits shared with CodeBuddy.', iflyQuota: '1,000 signup credits · 100 daily login credits', mimoQuota: 'Free during the invitation-only beta', mimoAccess: 'Download after invite approval', inviteMethod: 'How to join', workbuddyQuota: '500 shared credits / month', freeCredits: 'Free credits', quotaLabel: 'Free quota', monthlyTokensSeed: '5M tokens / month', chineseSupport: 'Chinese support', platforms: 'Windows / macOS', openEdition: 'Open edition available (MIT)', education: '03 / education access', studentTitle: 'Student offers, separately', studentCopy: 'Student offers are not always permanent free quota: school email or education verification is usually required. Check the eligibility, region and expiry on the official page.', studentFilter: 'Show student offers →', educationVerify: 'Requires GitHub Education verification', officialStudent: 'Official student plan · eligibility is defined by the provider', openStudent: 'Open official student page ↗', noStudent: 'No verified student offer yet', pendingStudent: 'Waiting for an official source update',
        offersEyebrow: '04 / all verified paths', offersTitle: 'Find an entrance that works now', offersCopy: 'Product, free method, quota, validity, region and verification status in one card.', showing: 'Showing', offer: 'offer', offers: 'offers', noMatch: 'No matching entrance.', resetCopy: 'Try another keyword, or clear search and filters.', reset: 'Clear search and filters', product: 'Product', amountPrice: 'Quota / price', validity: 'Validity', region: 'Region', verification: 'Verification', officialSource: 'Official source →', openDetails: 'Open details',
        cheapestEyebrow: '05 / cheapest first', cheapestTitle: 'See the cheapest entrances first', cheapestCopy: 'Start with free access, then compare first-purchase prices; region, new-user status, validity and renewal are shown together.', liveRule: 'LIVE RULE', beFirst: 'Start here', firstPurchase: 'First purchase', selfHosted: 'Self-hosted', modelWeights: 'Model weights', conclusion: 'Conclusion:', comparePriceView: 'Price view', chinaBeijing: 'China / Beijing', international: 'International', judgment: 'Verdict', startHere: 'Start here', lowPrice: 'Low price', noteBeijing: 'Beijing does not mean every product is cheaper: this section shows verified free quota, first-purchase and open-weight paths, not one blended token-price ranking. Return to the official pricing page before subscribing.', newUserRegion: 'New user · Beijing', firstPurchaseRegion: 'Volcano Ark · first purchase', fromPrice: 'From ¥9.90', selfHostedRegion: 'Download · self-hosted', weightsFree: 'Free weights', aliModels: 'Alibaba Cloud · selected models', aliModelsCopy: 'Available in the China / Beijing deployment scope; new-user access lasts 90 days and then follows official pricing.', freeQuotaRule: 'See free quota rules ↗', codingPlanTitle: 'Doubao Coding Plan Lite', firstMonthCopy: 'First-month offer; renewal is ¥40 / month. Current limits follow the official promotion.', officialPlan: 'See official plan ↗', longcatTitle: 'LongCat-2.0', weightsCopy: 'Free weights do not mean free inference; storage, GPU, traffic and deployment time are separate costs.', openSourceEntry: 'Open source entry ↗', conclusionCopy: 'If you are in Beijing and qualify as a new user, start with the ¥0 quota; otherwise compare the ¥9.9 first-month plan. Neither is an unconditional permanent monthly price.', noEquivalentQuota: 'Usually no equivalent free quota', renewalPrice: '¥9.9 / ¥40 per month', notApplicable: 'Not applicable',
        localLane: '06 / local lane', downloadLocal: 'Download locally', weightsNote: 'Weights may be free; GPU time may not be.', open: 'Open ↗', howToRead: '07 / how to read it', faqTitle: 'This is not a “everything is free” ranking', faqCopy: 'Free quota, trials, promotions, student eligibility and low-cost paths are listed separately.', recurringQuota: 'Free quota', studentDiscount: 'Student offer', openWeight: 'Open weights', officialEntry: 'Official entry', recurringQuotaCopy: 'Recurring quota can still have rate, region or payment-method limits.', studentDiscountCopy: 'Education verification is required; region, term and renewal conditions follow the provider.', openWeightCopy: 'Weights can be downloaded, but storage, GPU, inference and network egress may cost money.', officialEntryCopy: 'Every offer keeps its source, update date and a copyable usage path.', faqFree: 'What counts as free?', faqStudent: 'Are student offers permanent free?', faqNight: 'Are night discounts always available?', sortDefault: 'Overall', sortFresh: 'Recently checked', sortName: 'A–Z', footerSources: 'Official sources only · Free status separated by mechanism', footerData: 'Data is subject to change', contactLabel: 'Contact',
        localeToggle: '中文', localTime: 'Local time', detecting: 'Detecting timezone…', sourceLanguage: 'English', contextWindowLabel: 'Context window', guideNav: 'Guide', allModels: 'All models', doubaoSearch: 'Doubao', seedFeaturedTitle: 'Doubao Seed', seedFeaturedProvider: 'ByteDance', iflyFeaturedTitle: 'iFlytek AStudio', iflyFeaturedProvider: 'iFlytek', mimoFeaturedTitle: 'Xiaomi MiMo Desktop', mimoFeaturedProvider: 'Xiaomi', workbuddyFeaturedTitle: 'WorkBuddy', workbuddyFeaturedProvider: 'Tencent · Buddy AI', qwenDownloadTitle: 'Alibaba Qwen3-4B / Qwen', officialTerms: 'See official terms', dateUnknown: 'Date unavailable · review needed', dateStale: 'Needs re-check',
        keyPick: 'Key pick', featuredPick: 'Featured', featuredNote: '“Featured”: measured mainland API round trip within 400 ms (median of 3) plus a high free quota. Hover the tag for the evidence.', editionCn: 'China edition', editionIntl: 'International edition', editionDual: 'China + intl editions', alsoIntl: 'Also has intl edition', alsoCn: 'Also has China edition', netOk: 'Network verified', netBoth: 'China + global', netCn: 'China only', netIntl: 'Global only', netFail: 'Not reachable', netCnShort: 'China', netIntlShort: 'Global', netDead: 'broken link(s)', netMethod: 'measured from a mainland-China network + check-host.net nodes (US x2 / DE / SG / JP / UK)', netNote: 'network reachability and round-trip latency only, not signup requirements or model speed'
      }),
      'zh-CN': Object.freeze({
        pageTitle: 'Free AI Index — 免费 AI 模型、Qwen、豆包、IDE 和试用汇总',
        pageDescription: '一站比较经过核验的免费 AI 模型、免费编码 IDE、学生优惠、可下载权重和限时试用入口。',
        brandSub: '已核验的免费 AI 资源', navCatalog: '模型库', navTools: '开发工具', navApi: 'API 服务', navRank: '榜单', submit: '提交资源',
        verified: '官方来源 · 条件透明', heroTitle: '发现真正好用的<span>免费 AI</span>', heroTitleAccent: '免费 AI', heroCopy: '模型、API、IDE 与限时试用，一站比较', searchPlaceholder: '搜索模型、平台或功能，例如 DeepSeek、Qwen3', searchLabel: '搜索资源', search: '搜索', hot: '热门搜索：', freeApi: '免费 API',
        intelTitle: '今天的 AI 资源有什么变化？', intelStoryCopy: '我们每天检查官方来源，记录新增、恢复、下线和异常。', intelLogCta: '查看今日变化 →', newCount: '新增', changesToday: '今日有变化', noNew: '今日无新增', resourceCount: '个优质资源', checked: '显示官方条件与最近核验日期', trend: '较上周', forever: '永久免费', longTerm: '长期可用', trial: '限时试用', grabChance: '把握机会', openWeights: '开源可下载', useFreely: '自由使用', heroNote: '好的 AI\n应该被更多人\n轻松使用',
        method: '免费方式', capability: '能力', chinese: '中文支持', updated: '更新时间', all: '全部', browse: '找到适合你的 AI 工具', categoryCopy: '分类可以重叠，一条资源可能同时属于多个入口。', allOffers: '全部', largeModels: '大模型', ide: '免费 IDE', credits: '积分 / 次数', promo: '时段 / 限时优惠', web: '网页工具', download_lowcost: '下载 / 低成本', modelCategory: '单独模型', regionChipCn: '国内', regionChipIntl: '国外', featuredChip: '◆ 加精', imageVideo: '图像视频', apiServices: 'API 服务', openModels: '开源模型', more: '更多分类',
        popular: '本周热门', moreLink: '查看更多 →', permanent: '永久免费', limitedTrial: '限时试用', downloadable: '开源可下载', freeQuota: '免费额度', freePlan: '免费方案', supportedPlatforms: '支持平台', excellent: '优秀', featured: '编辑精选', seedFeatured: '全能的对话与创作助手，支持文本、图像、音视频等模态生成。', iflyFeatured: '星火 X2.5 驱动的桌面 AI 生产力工作台，自主规划任务并交付文档、网页与代码。', mimoFeatured: '邀请制桌面 Agent Beta，测试期间免费体验 MiMo-X Preview 模型。', workbuddyFeatured: '面向日常办公的 AI 智能体工作站，与 CodeBuddy 同账号积分共享，自动完成文档、表格与演示任务。', iflyQuota: '新用户 1,000 积分 · 每日登录领 100 积分', mimoQuota: '邀请制测试期间免费体验', mimoAccess: '申请邀请通过后下载', inviteMethod: '参与方式', workbuddyQuota: '每月 500 共享积分', freeCredits: '免费积分', quotaLabel: '免费额度', monthlyTokensSeed: '每月 500 万 tokens', chineseSupport: '中文支持', platforms: 'Windows / macOS', openEdition: '开源版可下载 (MIT)', education: '03 / education access', studentTitle: '学生优惠单独看', studentCopy: '学生优惠不是永久免费额度：通常需要学校邮箱或教育身份验证，资格、地区和有效期以官方页面为准。', studentFilter: '筛选学生优惠 →', educationVerify: '需要 GitHub Education 验证', officialStudent: '官方学生计划 · 资格以页面为准', openStudent: '打开官方学生页 ↗', noStudent: '暂无已核验学生优惠', pendingStudent: '等待官方来源更新',
        offersEyebrow: '04 / all verified paths', offersTitle: '找到现在能打开的入口', offersCopy: '产品、免费方式、额度、有效期、地区和核验状态放在同一张卡片里。', showing: '找到', offer: '条资源', offers: '条资源', noMatch: '没有匹配的入口。', resetCopy: '换个关键词，或清空搜索和筛选。', reset: '清空搜索和筛选', product: '产品', amountPrice: '额度 / 价格', validity: '有效期', region: '地区', verification: '核验', officialSource: '官方来源 →', openDetails: '打开详情',
        cheapestEyebrow: '05 / cheapest first', cheapestTitle: '最便宜的入口先看', cheapestCopy: '先免费，再看首购价；地区、新用户、有效期和续费同时展示。', liveRule: 'LIVE RULE', beFirst: '优先看', firstPurchase: '首购', selfHosted: '自托管', modelWeights: '模型权重', conclusion: '结论：', comparePriceView: '价格视角', chinaBeijing: '中国区 / 北京', international: '国际区', judgment: '判断', startHere: '先看', lowPrice: '低价', noteBeijing: '北京不代表所有产品都更便宜：这里展示的是已核验的“免费额度 / 首购优惠 / 开源权重”入口，不把不同模型的 token 单价混成一个总榜。订阅前请回到官方价格页。', newUserRegion: '北京区 · 新用户', firstPurchaseRegion: '火山方舟 · 首购', fromPrice: '¥9.90 起', selfHostedRegion: '下载 · 自托管', weightsFree: '权重免费', aliModels: '阿里云百炼 · 部分模型', aliModelsCopy: '仅中国（北京）部署范围可用；新用户有效期 90 天，额度用完后按官方价格计费。', freeQuotaRule: '看免费额度规则 ↗', codingPlanTitle: '豆包 Coding Plan Lite', firstMonthCopy: '首月优惠价；后续续费 ¥40 / 月，限量活动以官方页面当前状态为准。', officialPlan: '看官方方案 ↗', longcatTitle: 'LongCat-2.0', weightsCopy: '下载权重不等于推理免费；存储、GPU、流量和部署时间另算。', openSourceEntry: '打开开源入口 ↗', conclusionCopy: '如果你在北京且符合新用户条件，先用 ¥0 免费额度；不符合时，再看 ¥9.9 首月方案。¥0 和 ¥9.9 都不是无条件的长期月费。', noEquivalentQuota: '通常无同等免费额度', renewalPrice: '¥9.9 / ¥40 月', notApplicable: '不适用',
        localLane: '06 / local lane', downloadLocal: '下载到本地', weightsNote: '权重免费，GPU 时间不一定免费。', open: '打开 ↗', howToRead: '07 / how to read it', faqTitle: '这不是“全都免费”榜单', faqCopy: '我们把免费、试用、优惠、学生资格和低价入口分开写。', recurringQuota: '免费额度', studentDiscount: '学生优惠', openWeight: '开源权重', officialEntry: '官方入口', recurringQuotaCopy: '周期性额度仍可能有速率、地区或付款方式限制。', studentDiscountCopy: '需要教育身份验证，优惠期限和适用地区以官方页面为准。', openWeightCopy: '可以下载模型，但存储、GPU、推理和流量可能收费。', officialEntryCopy: '每条 offer 都保留来源、更新时间和可复制的使用路径。', faqFree: '什么才算免费？', faqStudent: '学生优惠是永久免费吗？', faqNight: '夜间优惠一定存在吗？', sortDefault: '综合排序', sortFresh: '最近核验', sortName: 'A–Z', footerSources: 'OFFICIAL SOURCES ONLY · FREE STATUS SEPARATED BY MECHANISM', footerData: '数据会变化，请以官方页面为准', contactLabel: '联系我',
        localeToggle: 'EN', localTime: '本地时间', detecting: '正在检测时区…', sourceLanguage: '简体中文', contextWindowLabel: '上下文窗口', guideNav: '使用指南', allModels: '全部模型', doubaoSearch: '豆包', seedFeaturedTitle: '豆包 Seed', seedFeaturedProvider: '字节跳动', iflyFeaturedTitle: '讯飞 AStudio', iflyFeaturedProvider: '科大讯飞', mimoFeaturedTitle: '小米 MiMo Desktop', mimoFeaturedProvider: '小米', workbuddyFeaturedTitle: '腾讯 WorkBuddy', workbuddyFeaturedProvider: '腾讯 · Buddy AI', qwenDownloadTitle: '阿里云 Qwen3-4B / 通义千问', officialTerms: '以官方条款为准', dateUnknown: '日期未知 · 需要重新核验', dateStale: '需要重新核验',
        keyPick: '重点', featuredPick: '加精', featuredNote: '「加精」= 接口实测快（大陆直连 3 次中位数 ≤ 400ms）且免费额度高。悬停标签看具体理由。', editionCn: '国内版', editionIntl: '国际版', editionDual: '国内+国际双入口', alsoIntl: '也有国际版', alsoCn: '也有国内版', netOk: '实测通过', netBoth: '国内外均可用', netCn: '仅国内可用', netIntl: '仅国外可用', netFail: '本次未连通', netCnShort: '国内', netIntlShort: '海外', netDead: '个链接解析失败', netMethod: '本机大陆网络直连 + check-host.net 海外节点（US×2 / DE / SG / JP / UK）', netNote: '仅实测网络可达性与往返延迟，不代表注册门槛或模型生成速度'
      })
    });
    let currentLocale = 'en';
    const localeText = key => LOCALE_COPY[currentLocale]?.[key] || LOCALE_COPY.en[key] || key;
    const normalizeLocale = value => {
      const text = String(value || '').toLowerCase();
      if (text === 'zh' || text.startsWith('zh-')) return SUPPORTED_LOCALES.zh;
      if (text === 'en' || text.startsWith('en-')) return SUPPORTED_LOCALES.en;
      return '';
    };
    const readStoredLocale = () => {
      try { return normalizeLocale(localStorage.getItem(LOCALE_STORAGE_KEY)); } catch (error) { return ''; }
    };
    const resolveLocale = (source = window.location) => {
      const url = new URL(source.href || source, window.location.href);
      const explicit = normalizeLocale(url.searchParams.get('lang'));
      if (explicit) return explicit;
      const pathMatch = url.pathname.match(/(?:^|\/)(zh|en)(?:\/|$)/i);
      const pathLocale = normalizeLocale(pathMatch?.[1]);
      if (pathLocale) return pathLocale;
      const pageDefault = normalizeLocale(document.documentElement.dataset.defaultLocale);
      if (pageDefault) return pageDefault;
      const stored = readStoredLocale();
      if (stored) return stored;
      const languages = navigator.languages?.length ? navigator.languages : [navigator.language];
      return languages.some(language => normalizeLocale(language) === SUPPORTED_LOCALES.zh) ? SUPPORTED_LOCALES.zh : SUPPORTED_LOCALES.en;
    };
    const setNodeText = (selector, key) => document.querySelectorAll(selector).forEach(node => { node.textContent = localeText(key); });
    const setNodeHtml = (selector, key) => document.querySelectorAll(selector).forEach(node => { node.innerHTML = localeText(key); });
    const setLeadingText = (selector, key) => document.querySelectorAll(selector).forEach(node => {
      const textNode = [...node.childNodes].find(child => child.nodeType === Node.TEXT_NODE);
      if (textNode) textNode.nodeValue = `${localeText(key)} `;
    });
    const setNodeAttribute = (selector, attribute, key) => document.querySelectorAll(selector).forEach(node => node.setAttribute(attribute, localeText(key)));
    const cleanLocaleUrl = () => {
      const url = new URL(window.location.href);
      if (!url.searchParams.has('lang')) return;
      url.searchParams.delete('lang');
      const search = url.searchParams.toString();
      history.replaceState(null, '', `${url.pathname}${search ? '?' + search : ''}${url.hash}`);
    };
    const renderClock = (clock, label, timeZone, time) => {
      clock.replaceChildren();
      clock.append(document.createTextNode(`${label} `));
      const details = document.createElement('span');
      details.append(document.createTextNode(`${timeZone} · `));
      const currentTime = document.createElement('b');
      currentTime.textContent = time;
      details.append(currentTime);
      clock.append(details);
    };
    const updateClock = () => {
      const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'local timezone';
      const time = new Intl.DateTimeFormat(currentLocale, { hour: '2-digit', minute: '2-digit' }).format(new Date());
      const clock = document.getElementById('catalog-clock');
      if (clock) renderClock(clock, localeText('localTime'), timeZone, time);
    };
    const updateLocaleMeta = () => {
      document.documentElement.lang = currentLocale;
      document.title = localeText('pageTitle');
      document.querySelector('meta[name="description"]')?.setAttribute('content', localeText('pageDescription'));
      document.querySelector('meta[property="og:locale"]')?.setAttribute('content', currentLocale === 'en' ? 'en_US' : 'zh_CN');
    };
    const applyLocale = locale => {
      currentLocale = normalizeLocale(locale) || SUPPORTED_LOCALES.en;
      updateLocaleMeta();
      document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = localeText(node.dataset.i18n); });
      setNodeText('.catalog-header .brand-sub', 'brandSub');
      setNodeText('.header-submit', 'submit');
      setNodeHtml('.hero-badge', 'verified');
      setNodeHtml('.catalog-hero h1', 'heroTitle');
      setNodeText('.catalog-hero .hero-copy', 'heroCopy');
      setNodeAttribute('#catalog-search', 'placeholder', 'searchPlaceholder');
      setNodeAttribute('#catalog-search', 'aria-label', 'searchLabel');
      setNodeText('.hero-search button', 'search');
      setNodeText('.hot-searches > span', 'hot');
      setNodeText('.hot-searches button:nth-of-type(2)', 'doubaoSearch');
      setNodeText('.hot-searches button:nth-of-type(3)', 'freeApi');
      setNodeText('.hero-intel-title-row strong', 'intelTitle');
      setNodeText('.intel-story-copy', 'intelStoryCopy');
      setNodeText('.intel-log-link', 'intelLogCta');
      const intelDate = new Intl.DateTimeFormat(currentLocale, { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date());
      document.querySelector('.hero-intel-head > span').textContent = `▣\u00a0${intelDate}`;
      const dailyBadge = document.getElementById('daily-log-badge');
      if (dailyBadge) {
        const newCount = Number(dailyBadge.dataset.newCount || 0);
        const changeCount = Number(dailyBadge.dataset.changeCount || 0);
        dailyBadge.textContent = newCount
          ? `${localeText('newCount')} ${newCount}${currentLocale === SUPPORTED_LOCALES.zh ? ' 项' : ` ${newCount === 1 ? 'entry' : 'entries'}`}`
          : (changeCount ? localeText('changesToday') : localeText('noNew'));
      }
      setNodeText('.hero-intel-main > div:first-child > strong', 'resourceCount');
      setNodeText('.hero-intel-main p', 'checked');
      setNodeHtml('.mini-chart small', 'trend');
      setNodeText('.intel-pills > div:nth-child(1) b', 'forever'); setNodeText('.intel-pills > div:nth-child(1) small', 'longTerm');
      setNodeText('.intel-pills > div:nth-child(2) b', 'trial'); setNodeText('.intel-pills > div:nth-child(2) small', 'grabChance');
      setNodeText('.intel-pills > div:nth-child(3) b', 'openWeights'); setNodeText('.intel-pills > div:nth-child(3) small', 'useFreely');
      setNodeHtml('.hero-intel-note', 'heroNote');
      ['method', 'capability', 'region', 'updated'].forEach((key, index) => setNodeText(`.catalog-filter-bar > label:nth-child(${index + 1}) b`, key));
      setNodeAttribute('#catalog-search', 'data-i18n-placeholder', 'searchPlaceholder');
      setNodeText('#catalog-sort option[value="free"]', 'sortDefault'); setNodeText('#catalog-sort option[value="fresh"]', 'sortFresh'); setNodeText('#catalog-sort option[value="name"]', 'sortName');
      setNodeText('.category-section .eyebrow', 'browse'); setNodeText('#categories-title', 'browse'); setNodeText('.category-section .section-heading > p', 'categoryCopy');
      const categoryCardLabels = { all: 'allOffers', free_quota: 'freeQuota', model: 'modelCategory', ide: 'ide', web: 'web', credits: 'credits', download_lowcost: 'download_lowcost', student: 'studentDiscount' };
      Object.entries(categoryCardLabels).forEach(([filter, key]) => setNodeText(`.category-card[data-filter="${filter}"] strong`, key));
      setNodeText('.featured-section .eyebrow', 'popular'); setNodeText('#featured-title', 'popular'); setNodeText('.featured-section .section-more', 'moreLink');
      setNodeText('.featured-card:nth-child(1) h3', 'iflyFeaturedTitle'); setNodeText('.featured-card:nth-child(1) > small', 'iflyFeaturedProvider');
      setNodeText('.featured-card:nth-child(2) h3', 'mimoFeaturedTitle'); setNodeText('.featured-card:nth-child(2) > small', 'mimoFeaturedProvider');
      setNodeText('.featured-card:nth-child(3) h3', 'workbuddyFeaturedTitle'); setNodeText('.featured-card:nth-child(3) > small', 'workbuddyFeaturedProvider');
      setNodeText('.featured-card:nth-child(4) h3', 'seedFeaturedTitle'); setNodeText('.featured-card:nth-child(4) > small', 'seedFeaturedProvider');
      setNodeText('.featured-card:nth-child(1) .resource-status', 'freeCredits'); setNodeText('.featured-card:nth-child(2) .resource-status', 'limitedTrial'); setNodeText('.featured-card:nth-child(3) .resource-status', 'freeCredits'); setNodeText('.featured-card:nth-child(4) .resource-status', 'permanent');
      setNodeText('.featured-card:nth-child(1) p', 'iflyFeatured'); setNodeText('.featured-card:nth-child(2) p', 'mimoFeatured'); setNodeText('.featured-card:nth-child(3) p', 'workbuddyFeatured'); setNodeText('.featured-card:nth-child(4) p', 'seedFeatured');
      setLeadingText('.featured-card:nth-child(1) .resource-meta span:nth-child(1)', 'quotaLabel'); setNodeText('.featured-card:nth-child(1) .resource-meta span:nth-child(1) b', 'iflyQuota'); setLeadingText('.featured-card:nth-child(1) .resource-meta span:nth-child(2)', 'supportedPlatforms'); setNodeText('.featured-card:nth-child(1) .resource-meta span:nth-child(2) b', 'platforms');
      setLeadingText('.featured-card:nth-child(2) .resource-meta span:nth-child(1)', 'quotaLabel'); setNodeText('.featured-card:nth-child(2) .resource-meta span:nth-child(1) b', 'mimoQuota'); setLeadingText('.featured-card:nth-child(2) .resource-meta span:nth-child(2)', 'inviteMethod'); setNodeText('.featured-card:nth-child(2) .resource-meta span:nth-child(2) b', 'mimoAccess');
      setLeadingText('.featured-card:nth-child(3) .resource-meta span:nth-child(1)', 'quotaLabel'); setNodeText('.featured-card:nth-child(3) .resource-meta span:nth-child(1) b', 'workbuddyQuota'); setLeadingText('.featured-card:nth-child(3) .resource-meta span:nth-child(2)', 'supportedPlatforms'); setNodeText('.featured-card:nth-child(3) .resource-meta span:nth-child(2) b', 'platforms');
      setLeadingText('.featured-card:nth-child(4) .resource-meta span:nth-child(1)', 'quotaLabel'); setNodeText('.featured-card:nth-child(4) .resource-meta span:nth-child(1) b', 'monthlyTokensSeed'); setLeadingText('.featured-card:nth-child(4) .resource-meta span:nth-child(2)', 'chineseSupport'); setNodeText('.featured-card:nth-child(4) .resource-meta span:nth-child(2) b', 'excellent');
      document.querySelector('.hero-intel')?.style.setProperty('--hero-note', currentLocale === SUPPORTED_LOCALES.en ? '"Good AI\\Ashould be easier\\Afor more people to use"' : '"好的 AI\\A应该被更多人\\A轻松使用"');
      setNodeText('.student-panel .eyebrow', 'education'); setNodeText('#student-title', 'studentTitle'); setNodeText('.student-panel-copy > p', 'studentCopy'); setNodeText('.student-button', 'studentFilter'); setNodeText('.student-item:nth-child(1) span', 'educationVerify'); setNodeText('.student-item:nth-child(2) span', 'officialStudent');
      setNodeText('.offers-section .eyebrow', 'offersEyebrow'); setNodeText('.offers-section h2', 'offersTitle'); setNodeText('.offers-heading > div > p', 'offersCopy');
      setNodeText('.table-head > div:nth-child(1)', 'product'); setNodeText('.table-head > div:nth-child(2)', 'method'); setNodeText('.table-head > div:nth-child(3)', 'amountPrice'); setNodeText('.table-head > div:nth-child(4)', 'validity'); setNodeText('.table-head > div:nth-child(5)', 'region'); setNodeText('.table-head > div:nth-child(6)', 'verification');
      const filterChipLabels = { all: 'allOffers', featured: 'featuredChip', free_quota: 'freeQuota', model: 'modelCategory', credits: 'credits', ide: 'ide', promo: 'promo', student: 'studentDiscount', web: 'web', download_lowcost: 'download_lowcost' };
      Object.entries(filterChipLabels).forEach(([filter, key]) => setLeadingText(`.filter-chip[data-filter="${filter}"]`, key));
      const regionChipLabels = { china: 'regionChipCn', global: 'regionChipIntl' };
      Object.entries(regionChipLabels).forEach(([region, key]) => setLeadingText(`[data-region-chip="${region}"]`, key));
      setNodeText('#catalog-empty-state strong', 'noMatch'); setNodeText('#catalog-empty-state p', 'resetCopy'); setNodeText('#catalog-reset-filters', 'reset');
      setNodeText('.category-seo-links a:nth-child(1)', 'freeQuota'); setNodeText('.category-seo-links a:nth-child(2)', 'ide'); setNodeText('.category-seo-links a:nth-child(3)', 'apiServices'); setNodeText('.category-seo-links a:nth-child(4)', 'promo'); setNodeText('.category-seo-links a:nth-child(5)', 'studentDiscount'); setNodeText('.category-seo-links a:nth-child(6)', 'web'); setNodeText('.category-seo-links a:nth-child(7)', 'openWeight'); setNodeText('.category-seo-links a:nth-child(10)', 'allModels');
      setNodeText('.compare-panel .eyebrow', 'cheapestEyebrow'); setNodeText('.compare-panel h2', 'cheapestTitle'); setNodeText('.compare-panel .section-heading p', 'cheapestCopy'); setNodeText('.compare-panel .badge', 'liveRule');
      setNodeText('.cheap-card:nth-child(1) .cheap-card-label span', 'newUserRegion'); setNodeText('.cheap-card:nth-child(1) .cheap-card-label b', 'beFirst'); setNodeText('.cheap-card:nth-child(1) .cheap-card-price small', 'freeQuota'); setNodeText('.cheap-card:nth-child(1) h3', 'aliModels'); setNodeText('.cheap-card:nth-child(1) p', 'aliModelsCopy'); setNodeText('.cheap-card:nth-child(1) a', 'freeQuotaRule');
      setNodeText('.cheap-card:nth-child(2) .cheap-card-label span', 'firstPurchaseRegion'); setNodeText('.cheap-card:nth-child(2) .cheap-card-label b', 'fromPrice'); setNodeText('.cheap-card:nth-child(2) .cheap-card-price small', 'firstPurchase'); setNodeText('.cheap-card:nth-child(2) h3', 'codingPlanTitle'); setNodeText('.cheap-card:nth-child(2) p', 'firstMonthCopy'); setNodeText('.cheap-card:nth-child(2) a', 'officialPlan');
      setNodeText('.cheap-card:nth-child(3) .cheap-card-label span', 'selfHostedRegion'); setNodeText('.cheap-card:nth-child(3) .cheap-card-label b', 'weightsFree'); setNodeText('.cheap-card:nth-child(3) .cheap-card-price small', 'modelWeights'); setNodeText('.cheap-card:nth-child(3) h3', 'longcatTitle'); setNodeText('.cheap-card:nth-child(3) p', 'weightsCopy'); setNodeText('.cheap-card:nth-child(3) a', 'openSourceEntry');
      setNodeHtml('.cheap-disclaimer', 'conclusionCopy');
      ['comparePriceView', 'chinaBeijing', 'international', 'judgment'].forEach((key, index) => setNodeText(`.compare-row.head > div:nth-child(${index + 1})`, key));
      setLeadingText('.compare-row:nth-child(2) > div:first-child', 'aliModels'); setNodeText('.compare-row:nth-child(2) > div:first-child small', 'freeQuota'); setNodeText('.compare-row:nth-child(2) > div:nth-child(2)', 'firstMonthCopy'); setNodeText('.compare-row:nth-child(2) > div:nth-child(3)', 'noEquivalentQuota'); setNodeText('.compare-row:nth-child(2) > div:nth-child(4)', 'startHere');
      setLeadingText('.compare-row:nth-child(3) > div:first-child', 'codingPlanTitle'); setNodeText('.compare-row:nth-child(3) > div:first-child small', 'firstPurchase'); setNodeText('.compare-row:nth-child(3) > div:nth-child(2)', 'renewalPrice'); setNodeText('.compare-row:nth-child(3) > div:nth-child(3)', 'notApplicable'); setNodeText('.compare-row:nth-child(3) > div:nth-child(4)', 'lowPrice');
      setNodeText('.compare-note', 'noteBeijing');
      setNodeText('.download-panel .eyebrow', 'localLane'); setNodeText('.download-panel h2', 'downloadLocal'); setNodeText('.download-panel .section-heading p', 'weightsNote');
      setNodeText('.download-item:nth-child(2) strong', 'qwenDownloadTitle');
      setNodeText('.catalog-faq .eyebrow', 'howToRead'); setNodeText('#catalog-faq-title', 'faqTitle'); setNodeText('.catalog-faq .section-heading p', 'faqCopy');
      ['recurringQuota', 'studentDiscount', 'openWeight', 'officialEntry'].forEach((key, index) => setNodeText(`.catalog-faq .seo-grid > div:nth-child(${index + 1}) h3`, key));
      ['recurringQuotaCopy', 'studentDiscountCopy', 'openWeightCopy', 'officialEntryCopy'].forEach((key, index) => setNodeText(`.catalog-faq .seo-grid > div:nth-child(${index + 1}) p`, key));
      ['faqFree', 'faqStudent', 'faqNight'].forEach((key, index) => setNodeText(`.catalog-faq .faq-list details:nth-child(${index + 1}) summary`, key));
      setNodeText('#drawerContextWindow strong', 'contextWindowLabel');
      setNodeText('.catalog-app .footer > span:first-child', 'footerSources'); setNodeText('.catalog-app .footer > span:last-child', 'footerData'); setNodeText('.catalog-app .footer [data-footer-contact-label]', 'contactLabel');
      const toggle = document.querySelector('[data-locale-toggle]');
      if (toggle) { toggle.textContent = localeText('localeToggle'); toggle.setAttribute('aria-label', currentLocale === 'en' ? 'Switch to Chinese' : '切换到英文'); }
      updateClock();
      if (loadedOffers.length) { renderOffers(loadedOffers); applyFilters(); }
    };
    const installLocaleToggle = () => {
      const actions = document.querySelector('.header-actions');
      if (!actions || actions.querySelector('[data-locale-toggle]')) return;
      const toggle = document.createElement('button');
      toggle.type = 'button'; toggle.className = 'locale-toggle'; toggle.dataset.localeToggle = ''; toggle.dataset.i18n = 'localeToggle';
      toggle.addEventListener('click', () => {
        const next = currentLocale === SUPPORTED_LOCALES.en ? SUPPORTED_LOCALES.zh : SUPPORTED_LOCALES.en;
        try { localStorage.setItem(LOCALE_STORAGE_KEY, next); } catch (error) { /* local storage can be unavailable */ }
        applyLocale(next);
      });
      actions.insertBefore(toggle, actions.firstChild);
    };
    installLocaleToggle();
    const resolvedLocale = resolveLocale();
    cleanLocaleUrl();
    applyLocale(resolvedLocale);
    const FREELLM_HOME_SCRIPT_URL = document.currentScript?.src || '';
    const escapeHtml = value => String(value ?? '').replace(/[&<>\"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[char]));
    const safeExternalHref = value => /^https:\/\//i.test(String(value || '')) ? String(value) : '#';
    const summaryMarkup = value => {
      const parts = String(value || '').split(' / ');
      return `${escapeHtml(parts[0])}${parts.length > 1 ? `<small>${escapeHtml(parts.slice(1).join(' / '))}</small>` : ''}`;
    };
    const localTodayIso = () => {
      const now = new Date();
      return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
    };
    const isValidIsoDate = value => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ''))) return false;
      const parsed = new Date(`${value}T00:00:00`);
      const [year, month, day] = String(value).split('-').map(Number);
      return !Number.isNaN(parsed.getTime()) && parsed.getFullYear() === year && parsed.getMonth() + 1 === month && parsed.getDate() === day;
    };
    const isFreshDate = value => {
      if (!isValidIsoDate(value)) return false;
      const age = Math.floor((new Date(`${localTodayIso()}T00:00:00`) - new Date(`${value}T00:00:00`)) / 86400000);
      return age >= 0 && age <= 7;
    };
    const checkedDateLabel = value => {
      if (!isValidIsoDate(value)) return localeText('dateUnknown');
      if (!isFreshDate(value)) return localeText('dateStale');
      return value === localTodayIso() ? (currentLocale === SUPPORTED_LOCALES.zh ? '今天' : 'Today') : formatDate(value);
    };
    const checkedMarkup = item => {
      const source = String(item.checkedSummary || '').split(' / ').slice(1).join(' / ');
      const label = checkedDateLabel(item.lastVerifiedAt || item.date);
      return `${escapeHtml(label)}${source ? `<small>${escapeHtml(localeValue(source, localeText('officialTerms')))}</small>` : ''}`;
    };
    const iconHostFromUrl = value => {
      try {
        const url = new URL(String(value || ''));
        return /^https?:$/i.test(url.protocol) ? url.hostname.toLowerCase() : '';
      } catch (error) {
        return '';
      }
    };
    const PROVIDER_ICON_HOSTS = Object.freeze({
      codebuddy: 'cloud.tencent.com',
      qoder: 'qoder.com',
      trae: 'www.trae.cn',
      comate: 'comate.baidu.com',
      doubao: 'www.volcengine.com',
      glm: 'bigmodel.cn',
      'longcat-2-0': 'www.meituan.com',
      'qwen-download': 'www.aliyun.com',
      'glm-download': 'bigmodel.cn',
      sensecore: 'www.sensetime.com',
      deepseek: 'www.deepseek.com',
      'opencode-zen-free': 'opencode.ai',
      'github-copilot-free': 'github.com',
      'cursor-hobby': 'cursor.com',
      'amazon-q-free': 'aws.amazon.com',
      'google-antigravity-free': 'google.com',
      'aliyun-qwen-free-quota': 'www.aliyun.com',
      'keenable-search-free': 'keenable.ai',
      'tinyfish-search-fetch-free': 'tinyfish.ai',
      'tinyfish-agent-browser-metered': 'tinyfish.ai',
      'tavily-web-free-credits': 'tavily.com',
      'exa-web-free-credits': 'exa.ai',
      'you-web-free-tier': 'you.com',
      'firecrawl-web-free-credits': 'firecrawl.dev',
      'brave-search-free-credits': 'brave.com',
      'browserbase-free-tier': 'browserbase.com'
    });
    const PROVIDER_ICON_ASSETS = Object.freeze({
      qwen: 'https://github.com/QwenLM.png?size=128',
      glm: 'https://github.com/zai-org.png?size=128',
      'qwen-download': 'https://github.com/QwenLM.png?size=128',
      'glm-download': 'https://github.com/zai-org.png?size=128'
    });
    const providerIconAsset = item => PROVIDER_ICON_ASSETS[item.providerId] || PROVIDER_ICON_ASSETS[item.id] || '';
    const providerIconHost = item => PROVIDER_ICON_HOSTS[item.providerId] || PROVIDER_ICON_HOSTS[item.id] || iconHostFromUrl(item.register) || iconHostFromUrl(item.sourceUrls?.[0]);
    const providerIconMarkup = item => {
      const host = providerIconHost(item);
      const asset = providerIconAsset(item);
      const fallback = `<span class="provider-mark-fallback">${escapeHtml(providerMarkText(item))}</span>`;
      if (!host && !asset) return fallback;
      const faviconService = host ? `https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=64` : '';
      const imageUrl = asset || faviconService;
      return `${fallback}<img class="provider-icon-img" src="${escapeHtml(imageUrl)}" data-icon-host="${escapeHtml(host || '')}" data-icon-asset="${escapeHtml(asset)}" alt="${escapeHtml(item.provider)} 图标" loading="lazy" decoding="async" referrerpolicy="no-referrer">`;
    };
    const hydrateProviderIcons = container => {
      container.querySelectorAll('.provider-mark .provider-icon-img').forEach(image => {
        const mark = image.closest('.provider-mark');
        image.addEventListener('load', () => mark.classList.add('has-image'), { once: true });
        image.addEventListener('error', () => {
          if (image.dataset.fallbackTried === 'true' || !image.dataset.iconHost) {
            image.remove();
            return;
          }
          image.dataset.fallbackTried = 'true';
          image.src = `https://${image.dataset.iconHost}/favicon.ico`;
        });
      });
    };
    const pad = value => String(value).padStart(2, '0');
    const rowBadgeClass = badge => {
      const text = String(badge || '');
      if (text.includes('FREE')) return 'free';
      if (text.includes('TRIAL')) return 'trial';
      if (text.includes('VERIFY')) return 'pending';
      if (text.includes('FIRST') || text.includes('OFF')) return 'promo';
      return 'open';
    };
    const categoryNames = {
      free_quota: 'freeQuota', model: 'modelCategory', credits: 'credits', ide: 'ide', promo: 'promo', student: 'studentDiscount', web: 'web', download_lowcost: 'download_lowcost'
    };
    const offerTokens = item => new Set([...(item.type || []), ...(item.capabilities || []), item.productType].filter(Boolean));
    const offerCategories = item => {
      const tokens = offerTokens(item);
      const categories = [];
      const isIde = item.productType === 'free_ide' || tokens.has('ide') || tokens.has('free_ide');
      const isWeb = item.productType === 'web_infrastructure' || tokens.has('web');
      const isDownloadOrLowCost = item.productType === 'open_weights' || item.productType === 'payg' || tokens.has('download') || tokens.has('payg');
      const isStudent = tokens.has('student') || Boolean(item.studentSummary);
      if (isStudent) categories.push('student');
      if (item.productType === 'api') categories.push('model');
      if (['daily_quota', 'weekly_quota', 'monthly_quota', 'permanent'].includes(item.freeMechanism) && !isIde && !isDownloadOrLowCost) categories.push('free_quota');
      if (['trial', 'limited_time_free'].includes(item.freeMechanism)) categories.push('credits');
      if (isIde) categories.push('ide');
      if (item.freeMechanism === 'first_month_promo' || item.timeWindow || tokens.has('promo')) categories.push('promo');
      if (isWeb) categories.push('web');
      if (isDownloadOrLowCost) categories.push('download_lowcost');
      return categories;
    };
    const primaryCategory = item => offerCategories(item)[0] || 'credits';
    const regionBucket = item => {
      const text = [item.access, item.accessSummary, item.availability].filter(Boolean).join(' ');
      if (/(china|中国|国内|beijing|北京)/i.test(text)) return 'china';
      if (/(global|international|海外|全球)/i.test(text)) return 'global';
      return 'unknown';
    };
    const renderSignalSummary = signals => {
      if (!signals?.length) return '';
      return `<div class="offer-card-signal" aria-label="External platform signals">${signals.slice(0, 3).map(signal => {
        const source = escapeHtml(localeValue(signal.sourcePlatform, 'External source'));
        const label = escapeHtml(localeValue(signal.rawLabel || `${signal.sourceType || 'signal'} · original value`, 'Original value'));
        const href = escapeHtml(safeExternalHref(signal.sourceUrl));
        return `<a href="${href}" target="_blank" rel="noreferrer noopener" title="${source}">${source}: ${label} ↗</a>`;
      }).join('')}</div>`;
    };
    const isModelOffer = item => Boolean(item?.contextWindow) && ['api', 'open_weights', 'coding_plan'].includes(item.productType);
    const modelContextText = context => context?.[currentLocale === SUPPORTED_LOCALES.zh ? 'zh' : 'en'] || context?.en || '—';
    const hasChineseText = value => /[\u3400-\u9fff]/.test(String(value || ''));
    const englishSafeText = (value, fallback = localeText('officialTerms')) => {
      const text = String(value || '').replace(/[\u3400-\u9fff]/g, ' ').replace(/\s+/g, ' ').trim();
      return text || fallback;
    };
    const localeValue = (value, fallback = localeText('officialTerms')) => currentLocale === SUPPORTED_LOCALES.en
      ? englishSafeText(value, fallback)
      : (value || fallback);
    const localizedOfferText = (item, field, fallback = localeText('officialTerms')) => {
      const value = currentLocale === SUPPORTED_LOCALES.zh ? item?.[field] : (item?.[`${field}En`] || item?.[field]);
      return localeValue(value, fallback);
    };
    const providerMarkText = item => currentLocale === SUPPORTED_LOCALES.en && hasChineseText(item?.providerMark)
      ? String(item?.id || 'ai').replace(/[^a-z0-9]+/gi, '').slice(0, 2).toUpperCase()
      : item?.providerMark;
    const renderModelContext = item => {
      const context = item?.contextWindow;
      if (!isModelOffer(item)) return '';
      return `<div class="offer-card-context">${escapeHtml(localeText('contextWindowLabel'))}: ${escapeHtml(modelContextText(context))}</div>`;
    };
    const renderOfferModels = item => {
      const models = Array.isArray(item?.freeModels) ? item.freeModels.filter(entry => entry?.model) : [];
      if (!models.length) return `<strong>${escapeHtml(localeValue(item.model || item.name, 'Listed model'))}</strong>`;
      const overLimit = models.length > 4;
      const list = `<div class="offer-card-model-list${overLimit ? ' is-clamped' : ''}">${models.map(entry => {
        const context = localeValue(entry.contextWindow, 'See model limits');
        const label = localeValue(entry.label, '');
        const quota = localeValue(entry.quota, 'See quota terms');
        const meta = [label, `${localeText('contextWindowLabel')}: ${context}`, quota].filter(Boolean).join(' · ');
        return `<div class="offer-model-row"><strong>${escapeHtml(localeValue(entry.model, 'Listed model'))}</strong><small>${escapeHtml(meta)}</small></div>`;
      }).join('')}</div>`;
      if (!overLimit) return list;
      return `${list}<button type="button" class="offer-models-toggle" aria-expanded="false"><span class="more-label">展开全部 ${models.length} 个模型 · Show all</span><span class="less-label">收起 · Collapse</span></button>`;
    };
    const renderOfferAccessPaths = item => {
      const paths = Array.isArray(item?.accessPaths) ? item.accessPaths.filter(path => path?.label) : [];
      if (!paths.length) return '';
      return `<div class="offer-access-paths">${paths.map(path => `<div class="offer-access-path"><strong>${escapeHtml(localeValue(path.label, 'Access path'))}</strong><small>${escapeHtml([path.summary, path.freeSummary, path.access].filter(Boolean).map(value => localeValue(value)).join(' · ') || localeText('officialTerms'))}</small></div>`).join('')}</div>`;
    };
    const renderOfferSource = item => {
      const source = Array.isArray(item?.links) ? item.links.find(link => Array.isArray(link) && link[1]) : null;
      const href = source?.[1] || item?.register;
      if (!href) return `<span>${escapeHtml(localeText('officialSource'))}</span>`;
      return `<a class="offer-source-link" href="${escapeHtml(href)}" rel="noreferrer noopener">${escapeHtml(localeText('officialSource'))} ↗</a>`;
    };
    const offerLinks = item => {
      const links = Array.isArray(item?.links) ? item.links.filter(link => Array.isArray(link) && link.length === 2 && link[0] && link[1]) : [];
      const modelLinks = Array.isArray(item?.freeModels)
        ? item.freeModels.filter(entry => entry?.model && entry?.sourceUrl).map(entry => [entry.model, entry.sourceUrl])
        : [];
      const pathLinks = Array.isArray(item?.accessPaths)
        ? item.accessPaths.flatMap(path => (path?.links || []).filter(link => Array.isArray(link) && link.length === 2 && link[0] && link[1]).map(([label, url]) => [`${localeValue(path.label, 'Access path')}: ${localeValue(label, 'Official link')}`, url]))
        : [];
      return [...links, ...modelLinks, ...pathLinks];
    };
    const offerEditionLabel = item => {
      const editions = Array.isArray(item.editions) ? item.editions : [];
      if (item.editionOf === 'cn') return localeText('editionCn');
      if (item.editionOf === 'intl') return localeText('editionIntl');
      if (editions.includes('cn') && editions.includes('intl')) return localeText('editionDual');
      if (editions.includes('cn')) return localeText('editionCn');
      if (editions.includes('intl')) return localeText('editionIntl');
      return '';
    };
    const offerNetworkFlags = item => {
      const check = item.networkCheck;
      if (!check || !check.region) return [];
      const regionKeys = { both: 'netBoth', cn: 'netCn', intl: 'netIntl' };
      const speedParts = [];
      if (check.cnMs) speedParts.push(`${localeText('netCnShort')} ${check.cnMs}ms`);
      if (check.intlMs) speedParts.push(`${localeText('netIntlShort')} ${check.intlMs}ms`);
      const speed = speedParts.join(' · ');
      const title = `${check.checkedAt} · ${localeText('netMethod')}${check.cnHost ? ` · ${check.cnHost}` : ''}${speed ? ` · ${speed}` : ''} · ${localeText('netNote')}`;
      const dead = Array.isArray(check.deadTargets) ? check.deadTargets : [];
      const deadChip = dead.length
        ? [`<span class="flag-chip flag-net-dead" title="${escapeHtml(dead.join(' ; '))}">⚠ ${escapeHtml(localeText('netDead'))} ${dead.length}</span>`]
        : [];
      if (check.region === 'none') {
        return [`<span class="flag-chip flag-net-fail" title="${escapeHtml(title)}">✗ ${escapeHtml(localeText('netFail'))}</span>`, ...deadChip];
      }
      if (!regionKeys[check.region]) return deadChip;
      const chips = [
        `<span class="flag-chip flag-net-ok" title="${escapeHtml(title)}">✓ ${escapeHtml(localeText('netOk'))}</span>`,
        `<span class="flag-chip flag-net-region">${escapeHtml(localeText(regionKeys[check.region]))}</span>`,
      ];
      if (speed) chips.push(`<span class="flag-chip flag-net-speed">${escapeHtml(speed)}</span>`);
      return [...chips, ...deadChip];
    };
    const offerFlagsMarkup = item => {
      const chips = [];
      if (item.featured?.reason) {
        const reason = currentLocale === SUPPORTED_LOCALES.zh ? item.featured.reason : (item.featured.reasonEn || item.featured.reason);
        const title = [reason, `${localeText('featuredPick')} ${item.featured.since}`].filter(Boolean).join(' · ');
        chips.push(`<span class="flag-chip flag-featured" title="${escapeHtml(title)}">◆ ${escapeHtml(localeText('featuredPick'))}</span>`);
      }
      if (item.key) chips.push(`<span class="flag-chip flag-key">★ ${escapeHtml(localeText('keyPick'))}</span>`);
      chips.push(...offerNetworkFlags(item));
      const editionLabel = offerEditionLabel(item);
      if (editionLabel) chips.push(`<span class="flag-chip flag-edition">${escapeHtml(editionLabel)}</span>`);
      if (item.siblingEditionId && offerIndex[item.siblingEditionId]) {
        const label = item.editionOf === 'intl' ? localeText('alsoCn') : localeText('alsoIntl');
        chips.push(`<a class="flag-chip flag-sibling" href="/offers/${encodeURIComponent(item.siblingEditionId)}/">${escapeHtml(label)} ↗</a>`);
      }
      if (item.handsOn?.testedAt) {
        const note = localeValue(item.handsOn.note, '');
        chips.push(`<span class="flag-chip flag-hands-on" title="${escapeHtml(String(item.handsOn.testedAt))}${note ? ` · ${escapeHtml(note)}` : ''}">✓ ${escapeHtml(localeText('handsOn'))}</span>`);
      } else if (item.endpointCheck?.checkedAt && item.endpointCheck.verdict !== 'NETWORK_ERROR') {
        const note = localeValue(item.endpointCheck.note, '');
        const hasEndpoint = Boolean(item.usageGuide?.endpoint);
        const label = hasEndpoint ? localeText('endpointChecked') : localeText('siteChecked');
        const latency = Number.isInteger(item.endpointCheck.ms) ? `${item.endpointCheck.ms}ms` : '';
        const title = [String(item.endpointCheck.checkedAt), note, latency].filter(Boolean).join(' · ');
        chips.push(`<span class="flag-chip flag-endpoint" title="${escapeHtml(title)}">✓ ${escapeHtml(label)}${latency ? ` · ${latency}` : ''}</span>`);
      }
      return chips.length ? `<div class="offer-card-flags">${chips.join('')}</div>` : '';
    };
    const rowArticleMarkup = item => {
      const tokens = [...offerTokens(item)];
      const categories = offerCategories(item);
      const modelSearchText = (item.freeModels || []).flatMap(entry => [entry?.model, entry?.label, entry?.contextWindow, entry?.quota, entry?.note]);
      const searchText = JSON.stringify([item.provider, item.name, item.product, item.model, item.endpoint, item.freeSummary, item.freeMechanism, item.validity, item.access, ...(item.capabilities || []), item.usageGuide?.summary, item.usageGuide?.steps?.join(' '), ...modelSearchText].filter(Boolean));
      const capabilityLabel = (item.capabilities || []).map(value => localeValue(value, 'Capability')).join(' · ');
      const primary = primaryCategory(item);
      const categoryLabel = localeText(categoryNames[primary]) || localeText('verification');
      const offerHref = `/offers/${encodeURIComponent(item.id)}/`;
      const studentMarkup = item.studentSummary ? `<div class="student-mini">${escapeHtml(localizedOfferText(item, 'studentSummary'))}</div>` : '';
      const alternateLabels = categories.slice(1).map(category => localeText(categoryNames[category])).filter(Boolean).join(' · ');
      const provider = localizedOfferText(item, 'provider', 'AI provider');
      const providerMeta = localizedOfferText(item, 'providerMeta', 'Official provider');
      const amount = localizedOfferText(item, 'freeSummary', localizedOfferText(item, 'mechanism'));
      const validity = localizedOfferText(item, 'validitySummary', localizedOfferText(item, 'validity'));
      const access = localizedOfferText(item, 'accessSummary', localizedOfferText(item, 'access'));
      const modelMeta = localeValue(item.modelMeta || alternateLabels, 'Model details');
      return `<article class=${JSON.stringify('offer')} data-type="${escapeHtml(tokens.join(' '))}" data-category="${escapeHtml(categories.join(' '))}" data-name="${escapeHtml(item.name)}" data-provider="${escapeHtml(provider)}" data-search="${escapeHtml(searchText)}" data-order="${escapeHtml(item.order)}" data-key="${item.key ? 1 : 0}" data-featured="${item.featured?.reason ? 1 : 0}" data-date="${escapeHtml(item.date)}" data-detail="${escapeHtml(item.id)}"><div class="offer-card-top"><div class="provider"><div class="provider-mark" aria-label="${escapeHtml(provider)} icon">${providerIconMarkup(item)}</div><div class="provider-name">${escapeHtml(provider)}<small>${escapeHtml(providerMeta)}</small></div></div><button type="button" class="row-arrow" aria-label="${escapeHtml(localeText('openDetails'))}: ${escapeHtml(localizedOfferText(item, 'title', provider))}">→</button></div>${offerFlagsMarkup(item)}<div class="offer-card-body">${renderSignalSummary(signalIndex[item.id])}<div class="offer-card-model">${renderOfferModels(item)}<small>${escapeHtml(modelMeta)}</small></div>${renderModelContext(item)}${renderOfferAccessPaths(item)}<div class="offer-card-metrics"><div class="offer-card-metric"><label>${escapeHtml(localeText('method'))}</label><p><span class="category-label category-${escapeHtml(primary)}">${escapeHtml(categoryLabel)}</span>${studentMarkup}</p></div><div class="offer-card-metric"><label>${escapeHtml(localeText('amountPrice'))}</label><p><span class="badge ${rowBadgeClass(item.badges?.[0])}">${escapeHtml(localeValue(item.badges?.[0], 'OPEN'))}</span><br>${escapeHtml(amount)}</p></div><div class="offer-card-metric"><label>${escapeHtml(localeText('validity'))} / ${escapeHtml(localeText('region'))}</label><p>${summaryMarkup(validity)}<small>${escapeHtml(access)}</small></p></div></div></div><button type="button" class="offer-models-toggle offer-body-toggle" hidden aria-expanded="false"><span class="more-label">展开全部 · Show more</span><span class="less-label">收起 · Collapse</span></button><div class="offer-card-footer"><small>${checkedMarkup(item)}${capabilityLabel ? ` · ${escapeHtml(capabilityLabel)}` : ''}</small>${renderOfferSource(item)}<a class="offer-detail-link" href="${offerHref}">${escapeHtml(localeText('openDetails'))} ↗</a></div></article>`;
    };
    const formatDate = iso => new Date(`${iso}T00:00:00`).toLocaleDateString(currentLocale, { day: '2-digit', month: 'short', year: 'numeric' });
    const updateStructuredData = items => {
      const node = document.getElementById('ld-dynamic');
      if (!node) return;
      const faq = [...document.querySelectorAll('.catalog-faq .faq-list details')].map(detail => ({
        '@type': 'Question',
        name: detail.querySelector('summary').textContent.trim(),
        acceptedAnswer: { '@type': 'Answer', text: detail.querySelector('p').textContent.trim() }
      }));
      node.textContent = JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': [
          { '@type': 'ItemList', name: 'Free and limited-time-free AI offers', itemListElement: items.map((item, index) => ({ '@type': 'ListItem', position: index + 1, name: item.title, url: location.origin + '/offers/' + encodeURIComponent(item.id) + '/' })) },
          { '@type': 'FAQPage', mainEntity: faq }
        ]
      }, null, 2);
    };
    const OFFER_BODY_CLAMP = 236; // keep in sync with .offer-card-body.is-clamped max-height
    const applyOfferBodyClamps = container => {
      container.querySelectorAll('.offer').forEach(card => {
        const body = card.querySelector('.offer-card-body');
        const toggle = card.querySelector('.offer-body-toggle');
        if (!body || !toggle) return;
        card.classList.remove('model-expanded');
        const overLimit = body.scrollHeight > OFFER_BODY_CLAMP + 4;
        body.classList.toggle('is-clamped', overLimit);
        toggle.hidden = !overLimit;
        toggle.setAttribute('aria-expanded', 'false');
      });
    };
    const renderOffers = items => {
      loadedOffers = items;
      offerIndex = Object.fromEntries(items.map(item => [item.id, item]));
      const container = document.getElementById('catalog-offer-rows');
      container.innerHTML = items.map(rowArticleMarkup).join('');
      container.querySelectorAll('.offer').forEach(card => {
        const item = offerIndex[card.dataset.detail];
        const detailLink = card.querySelector('.offer-detail-link');
        if (!item || !detailLink) return;
        detailLink.dataset.sync = '';
        detailLink.dataset.syncType = 'offer';
        detailLink.dataset.syncId = item.id;
        detailLink.dataset.syncName = item.title || item.name;
        detailLink.dataset.syncUrl = detailLink.getAttribute('href') || '/offers/' + encodeURIComponent(item.id) + '/';
        detailLink.dataset.syncStar = '';
        card.dataset.method = item.freeMechanism || '';
        card.dataset.capability = (item.capabilities || []).join(' ');
        card.dataset.region = regionBucket(item);
        card.dataset.date = item.lastVerifiedAt || item.date || '';
      });
      window.FreeLLM?.Sync?.bind(container);
      hydrateProviderIcons(container);
      rows = [...container.querySelectorAll('.offer')];
      applyOfferBodyClamps(container);

      const countCategory = category => items.filter(item => offerCategories(item).includes(category)).length;
      const setCount = (filter, count) => {
        document.querySelectorAll(`.catalog-app [data-filter="${filter}"] em`).forEach(node => { node.textContent = pad(count); });
        document.querySelectorAll(`.catalog-app [data-category-count="${filter}"]`).forEach(node => { node.textContent = pad(count); });
      };

      document.getElementById('heroCount').textContent = items.length;
      setCount('all', items.length);
      ['free_quota', 'model', 'credits', 'ide', 'promo', 'student', 'web', 'download_lowcost'].forEach(category => setCount(category, countCategory(category)));
      setCount('featured', items.filter(item => item.featured?.reason).length);
      const setRegionCount = (region, count) => {
        const node = document.querySelector(`[data-region-chip="${region}"] em`);
        if (node) node.textContent = pad(count);
      };
      setRegionCount('china', items.filter(item => regionBucket(item) === 'china').length);
      setRegionCount('global', items.filter(item => regionBucket(item) === 'global').length);
      const featuredQuotaCount = document.getElementById('featuredQuotaCount');
      const featuredIdeCount = document.getElementById('featuredIdeCount');
      const featuredStudentCount = document.getElementById('featuredStudentCount');
      if (featuredQuotaCount) featuredQuotaCount.textContent = pad(countCategory('free_quota'));
      if (featuredIdeCount) featuredIdeCount.textContent = pad(countCategory('ide'));
      if (featuredStudentCount) featuredStudentCount.textContent = pad(countCategory('student'));

      const studentItems = items.filter(item => offerCategories(item).includes('student'));
      document.getElementById('studentList').innerHTML = studentItems.length
        ? studentItems.map(item => `<article class="student-item"><strong>${escapeHtml(item.title || item.name)}</strong><span>${escapeHtml(item.studentEligibility || (currentLocale === SUPPORTED_LOCALES.zh ? '需要教育身份验证' : 'Education verification required'))}</span><small>${escapeHtml(item.studentSummary || (currentLocale === SUPPORTED_LOCALES.zh ? '资格和期限以官方页面为准' : 'Eligibility and expiry follow the official page'))}</small><a href="${escapeHtml(item.studentSourceUrls?.[0] || item.register)}" target="_blank" rel="noreferrer noopener">${escapeHtml(localeText('openStudent'))}</a></article>`).join('')
        : `<div class="student-item"><strong>${escapeHtml(localeText('noStudent'))}</strong><span>${escapeHtml(localeText('pendingStudent'))}</span></div>`;

      const downloadItems = items.filter(item => offerCategories(item).includes('download_lowcost'));
      document.getElementById('catalog-download-list').innerHTML = downloadItems.map(item => `<div class="download-item"><div><strong>${escapeHtml(localizedOfferText(item, 'provider', 'AI model'))}</strong><small>${escapeHtml(localeValue((item.links || []).map(link => link[0]).join(' + ') || item.modelMeta || item.model, 'Model details'))}</small></div><a href="${escapeHtml(item.register)}" target="_blank" rel="noreferrer">${escapeHtml(localizedOfferText(item, 'registerLabel', localeText('open')))}</a></div>`).join('');

      const latest = items.map(item => item.lastVerifiedAt).filter(isValidIsoDate).sort().at(-1);
      const latestLabel = latest ? (isFreshDate(latest) ? formatDate(latest) : localeText('dateStale')) : localeText('dateUnknown');
      document.getElementById('catalog-last-checked').textContent = currentLocale === SUPPORTED_LOCALES.zh ? `最后核验：${latestLabel} · ${localeText('footerData')}` : `Last checked: ${latestLabel} · ${localeText('footerData')}`;

      updateStructuredData(items);
    };
    const showDataError = () => {
      const container = document.getElementById('catalog-offer-rows');
      container.replaceChildren();
      const error = document.createElement('div');
      error.className = 'offer-error';
      error.textContent = 'Offer data unavailable. The directory could not load data/offers.json or the external data/offers.js fallback.';
      container.append(error);
      document.getElementById('catalog-last-checked').textContent = `${localeText('dateUnknown')} · ${localeText('footerData')}`;
      document.getElementById('catalog-result-count').textContent = currentLocale === SUPPORTED_LOCALES.zh ? `0 ${localeText('offer')}` : `${localeText('showing')} 0 ${localeText('offers')}`;
    };
    const loadOfferBundle = async () => {
      const current = window.FREELLM_OFFERS;
      if (Array.isArray(current) && current.length) return current;
      if (!FREELLM_HOME_SCRIPT_URL) throw new Error('homepage script URL unavailable');
      const bundleUrl = new URL('../data/offers.js', FREELLM_HOME_SCRIPT_URL).href;
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = bundleUrl;
        script.onload = resolve;
        script.onerror = () => reject(new Error('offers.js failed to load'));
        document.head.appendChild(script);
      });
      const loaded = window.FREELLM_OFFERS;
      if (!Array.isArray(loaded) || !loaded.length) throw new Error('offers.js did not expose FREELLM_OFFERS');
      return loaded;
    };
    const loadOffers = async () => {
      if (location.protocol === 'file:') {
        try {
          const data = await loadOfferBundle();
          offerDataSource = 'embedded';
          return data;
        } catch (error) {
          console.warn(`offers.js unavailable (${error.message}).`);
          return [];
        }
      }
      try {
        const response = await fetch(document.body.dataset.offersUrl || '../data/offers.json');
        if (!response.ok) throw new Error(`offers.json returned ${response.status}`);
        const data = await response.json();
        if (Array.isArray(data) && data.length) {
          offerDataSource = 'network';
          return data;
        }
      } catch (error) {
        console.warn(`offers.json unavailable (${error.message}); falling back to external data bundle.`);
        try {
          const data = await loadOfferBundle();
          offerDataSource = 'embedded-fallback';
          return data;
        } catch (bundleError) {
          console.warn(`offers.js fallback unavailable (${bundleError.message}).`);
        }
      }
      return [];
    };
    const loadCommunitySignals = async () => {
      if (location.protocol === 'file:') return [];
      try {
        const response = await fetch('../data/community-signals.json', { cache: 'no-store' });
        if (!response.ok) throw new Error(`community-signals.json returned ${response.status}`);
        const data = await response.json();
        return Array.isArray(data) ? data : [];
      } catch (error) {
        console.warn(`community-signals.json unavailable (${error.message}); showing no public rating.`);
        return [];
      }
    };
    const indexCommunitySignals = signals => signals.reduce((index, signal) => {
      if (!signal || !signal.offerId) return index;
      (index[signal.offerId] ||= []).push(signal);
      return index;
    }, {});
    const renderCommunitySignals = signals => {
      if (!signals.length) return '<div class="signal-empty">No public rating found. External platform data will appear here with its original source and capture time.</div>';
      return signals.map(signal => {
        const platform = escapeHtml(localeValue(signal.sourcePlatform, 'External platform'));
        const label = escapeHtml(localeValue(signal.rawLabel || `${signal.sourceType || 'signal'} · original value`, 'Original value'));
        const excerpt = signal.excerpt ? `<p class="signal-excerpt">${escapeHtml(localeValue(signal.excerpt, localeText('officialTerms')))}</p>` : '';
        const captured = escapeHtml(signal.capturedAt || 'capture time unavailable');
        const sourceUrl = safeExternalHref(signal.sourceUrl);
        const source = sourceUrl === '#' ? 'Source link unavailable' : `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer noopener">Open source ↗</a>`;
        return `<article class="signal-item"><div class="signal-item-top"><strong class="signal-platform">${platform}</strong><span class="signal-label">${label}</span></div>${excerpt}<div class="signal-foot"><span>${captured}</span>${source}</div></article>`;
      }).join('');
    };
    const guideListText = value => Array.isArray(value) && value.length
      ? value.map(entry => localeValue(entry)).join(' · ')
      : '—';
    const guideExampleText = guide => {
      const examples = guide?.examples || {};
      const first = Object.entries(examples)[0];
      return first ? `${localeValue(first[0], 'Example')}: ${first[1]}` : 'No executable example provided.';
    };
    const guideIssuesText = issues => Array.isArray(issues) && issues.length
      ? issues.map(issue => `${localeValue(issue.problemEn || issue.problem, 'Common issue')}: ${localeValue(issue.solutionEn || issue.solution, localeText('officialTerms'))}`).join(' · ')
      : '—';
    const drawer = document.getElementById('drawer');
    const backdrop = document.getElementById('backdrop');
    const openDrawer = (key) => {
      const item = offerIndex[key]; if (!item) return;
      const drawerBadgeClass = badge => {
        const text = String(badge || '');
        if (text.includes('FREE') || text.includes('OPEN')) return 'free';
        if (text.includes('VERIFY')) return 'pending';
        if (text.includes('FIRST') || text.includes('OFF')) return 'promo';
        return 'open';
      };
      document.getElementById('drawerKicker').textContent = localizedOfferText(item, 'kicker', 'Offer details');
      document.getElementById('drawerTitle').textContent = localizedOfferText(item, 'title', localizedOfferText(item, 'provider', 'Select an offer'));
      document.getElementById('drawerBadges').innerHTML = (item.badges || []).map((badge, index) => `<span class="badge ${index === 0 ? drawerBadgeClass(badge) : 'pending'}">${escapeHtml(badge)}</span>`).join('');
      document.getElementById('drawerWhy').textContent = localizedOfferText(item, 'why');
      document.getElementById('drawerMechanism').textContent = localizedOfferText(item, 'mechanism');
      document.getElementById('drawerValidity').textContent = localizedOfferText(item, 'validity');
      document.getElementById('drawerAccess').textContent = localizedOfferText(item, 'access');
      const contextWindowBlock = document.getElementById('drawerContextWindow');
      contextWindowBlock.hidden = !isModelOffer(item);
      document.getElementById('drawerContextValue').textContent = isModelOffer(item) ? modelContextText(item.contextWindow) : '—';
      document.getElementById('drawerLastChecked').textContent = checkedDateLabel(item.lastVerifiedAt || item.date);
      document.getElementById('drawerCommand').textContent = item.command;
      const guide = item.usageGuide || {};
      document.getElementById('drawerUsageGuide').textContent = currentLocale === SUPPORTED_LOCALES.en && hasChineseText(guide.summary) ? localeText('officialTerms') : (guide.summary || 'Usage guide pending review.');
      document.getElementById('drawerPrerequisites').textContent = guideListText(guide.prerequisites);
      document.getElementById('drawerSteps').textContent = guideListText(guide.steps);
      document.getElementById('drawerEndpoint').textContent = guide.endpoint || guide.docsUrl || 'Install/action path';
      document.getElementById('drawerCapabilities').textContent = guideListText(item.capabilities);
      const accessPaths = Array.isArray(item.accessPaths) ? item.accessPaths.filter(path => path?.label) : [];
      const accessPathsBlock = document.getElementById('drawerAccessPathsBlock');
      accessPathsBlock.hidden = !accessPaths.length;
      document.getElementById('drawerAccessPaths').innerHTML = accessPaths.map(path => `<div class="detail-value"><strong>${escapeHtml(localeValue(path.label, 'Access path'))}</strong><br>${escapeHtml([path.summary, path.freeSummary, path.access].filter(Boolean).map(value => localeValue(value)).join(' · ') || localeText('officialTerms'))}</div>`).join('');
      document.getElementById('drawerExample').textContent = guideExampleText(guide);
      document.getElementById('drawerQuotaGuard').textContent = guideListText(guide.quotaGuard);
      document.getElementById('drawerCommonIssues').textContent = guideIssuesText(guide.commonIssues);
      const register = document.getElementById('drawerRegister');
      register.href = item.register;
      register.textContent = `${localizedOfferText(item, 'registerLabel', 'Register / open official page')} ↗`;
      const timeWindowBlock = document.getElementById('timeWindowBlock');
      timeWindowBlock.hidden = !item.timeWindow;
      if (item.timeWindow) {
        const local = Intl.DateTimeFormat().resolvedOptions().timeZone || 'your timezone';
        document.getElementById('timeWindowCopy').textContent = `${item.timeWindow} Your browser timezone: ${local}. Convert the window before scheduling heavy work.`;
      }
      document.getElementById('drawerLinks').innerHTML = offerLinks(item).map(([label, url]) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer noopener">${escapeHtml(localeValue(label, 'Official link'))} ↗</a>`).join('');
      document.getElementById('drawerSignals').innerHTML = renderCommunitySignals(signalIndex[item.id] || []);
      drawer.classList.add('open'); backdrop.classList.add('open'); drawer.setAttribute('aria-hidden', 'false'); document.body.style.overflow = 'hidden';
    };
    const closeDrawer = () => { drawer.classList.remove('open'); backdrop.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true'); document.body.style.overflow = ''; };
    document.querySelector('.table-wrap').addEventListener('click', e => {
      const button = e.target.closest('.row-arrow');
      if (button) openDrawer(button.closest('.offer').dataset.detail);
    });
    document.getElementById('closeDrawer').addEventListener('click', closeDrawer);
    backdrop.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });
    const bindCopyButton = (buttonId, sourceId) => {
      document.getElementById(buttonId).addEventListener('click', async e => {
        const button = e.currentTarget;
        const text = document.getElementById(sourceId).textContent;
        try { await navigator.clipboard.writeText(text); button.textContent = 'Copied'; button.classList.add('copied'); setTimeout(() => { button.textContent = 'Copy'; button.classList.remove('copied'); }, 1300); } catch { button.textContent = 'Select manually'; }
      });
    };
    bindCopyButton('copyCommand', 'drawerCommand');
    bindCopyButton('copyExample', 'drawerExample');

    let activeFilter = 'all';
    let activeMethod = 'all';
    let activeCapability = 'all';
    const activeRegions = new Set();
    let activeFreshness = 'all';
    let filterBeforeSearch = null;
    const syncFilterUrl = () => {
      const params = new URLSearchParams(location.search);
      const query = document.getElementById('catalog-search').value.trim();
      if (query) params.set('q', query); else params.delete('q');
      if (activeFilter === 'all') params.delete('filter'); else params.set('filter', activeFilter);
      if (activeMethod === 'all') params.delete('method'); else params.set('method', activeMethod);
      if (activeCapability === 'all') params.delete('capability'); else params.set('capability', activeCapability);
      if (activeRegions.size) params.set('region', [...activeRegions].join(',')); else params.delete('region');
      if (activeFreshness === 'all') params.delete('fresh'); else params.set('fresh', activeFreshness);
      const queryString = params.toString();
      history.replaceState(null, '', location.pathname + (queryString ? '?' + queryString : '') + location.hash);
    };
    const applyFilters = () => {
      const query = document.getElementById('catalog-search').value.trim().toLowerCase();
      let visible = 0;
      rows.forEach(row => {
        const categories = row.dataset.category.split(' ').filter(Boolean);
        const matchesFilter = activeFilter === 'all'
          || (activeFilter === 'featured' ? row.dataset.featured === '1' : categories.includes(activeFilter));
        const capabilities = row.dataset.capability.split(' ').filter(Boolean);
        const matchesMethod = activeMethod === 'all' || row.dataset.method === activeMethod;
        const matchesCapability = activeCapability === 'all' || capabilities.includes(activeCapability);
        const matchesRegion = activeRegions.size === 0 || activeRegions.has(row.dataset.region);
        const fresh = isFreshDate(row.dataset.date);
        const matchesFreshness = activeFreshness === 'all' || (activeFreshness === 'fresh' ? fresh : !fresh);
        const matchesQuery = !query || row.dataset.name.toLowerCase().includes(query) || row.dataset.search.toLowerCase().includes(query) || row.textContent.toLowerCase().includes(query);
        const show = matchesFilter && matchesMethod && matchesCapability && matchesRegion && matchesFreshness && matchesQuery;
        row.classList.toggle('hidden', !show); if (show) visible++;
      });
      document.getElementById('catalog-result-count').textContent = currentLocale === SUPPORTED_LOCALES.zh
        ? `${visible} ${localeText('offer')}`
        : `${localeText('showing')} ${visible} ${visible === 1 ? localeText('offer') : localeText('offers')}`;
      document.getElementById('catalog-empty-state').hidden = visible > 0;
      const featuredNote = document.getElementById('catalog-featured-note');
      if (featuredNote) featuredNote.hidden = activeFilter !== 'featured';
      syncFilterUrl();
    };
    const setFilter = (filter) => {
      activeFilter = filter;
      document.querySelectorAll('.catalog-app [data-filter]').forEach(el => {
        const isActive = el.dataset.filter === filter;
        el.classList.toggle('active', isActive);
        if (el.tagName === 'BUTTON') el.setAttribute('aria-pressed', String(isActive));
      });
      if (filter === 'compare') document.getElementById('catalog-compare').scrollIntoView({ behavior: 'smooth', block: 'start' });
      else applyFilters();
    };
    const clearCatalogSearch = () => {
      document.getElementById('catalog-search').value = '';
      filterBeforeSearch = null;
    };
    document.querySelectorAll('.featured-resource-link').forEach(link => link.addEventListener('click', event => {
      event.preventDefault();
      clearCatalogSearch();
      setFilter(link.dataset.filter || 'all');
      document.getElementById('catalog-offers').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }));
    document.querySelectorAll('.catalog-app [data-filter]').forEach(el => el.addEventListener('click', () => {
      clearCatalogSearch();
      setFilter(el.dataset.filter);
    }));
    document.querySelectorAll('.catalog-app [data-region-chip]').forEach(el => el.addEventListener('click', () => {
      const region = el.dataset.regionChip;
      const on = !activeRegions.has(region);
      if (on) activeRegions.add(region); else activeRegions.delete(region);
      el.classList.toggle('active', on);
      el.setAttribute('aria-pressed', String(on));
      applyFilters();
      syncFilterUrl();
    }));
    [
      ['catalog-method-filter', value => { activeMethod = value; }],
      ['catalog-capability-filter', value => { activeCapability = value; }],
      ['catalog-freshness-filter', value => { activeFreshness = value; }],
    ].forEach(([id, update]) => {
      document.getElementById(id).addEventListener('change', event => {
        update(event.target.value);
        applyFilters();
      });
    });
    document.getElementById('catalog-search').addEventListener('input', () => {
      const hasQuery = Boolean(document.getElementById('catalog-search').value.trim());
      if (hasQuery) {
        if (filterBeforeSearch === null) filterBeforeSearch = activeFilter;
        setFilter('all');
      } else {
        if (filterBeforeSearch !== null) {
          const restore = filterBeforeSearch;
          filterBeforeSearch = null;
          if (restore !== 'compare' && restore !== activeFilter) { setFilter(restore); return; }
        }
        applyFilters();
      }
    });
    document.querySelectorAll('.hot-searches button').forEach(button => button.addEventListener('click', () => {
      const input = document.getElementById('catalog-search');
      input.value = button.textContent.trim();
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
      input.focus();
    }));
    document.querySelector('.hero-search button')?.addEventListener('click', () => {
      document.getElementById('catalog-offers').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    document.getElementById('catalog-reset-filters').addEventListener('click', () => {
      document.getElementById('catalog-search').value = '';
      filterBeforeSearch = null;
      setFilter('all');
    });
    const initialParams = new URLSearchParams(location.search);
    const validFilters = ['all', 'featured', 'free_quota', 'model', 'credits', 'ide', 'promo', 'student', 'web', 'download_lowcost'];
    const validMethods = ['all', 'permanent', 'monthly_quota', 'daily_quota', 'weekly_quota', 'trial', 'limited_time_free', 'first_month_promo', 'open_weights'];
    const validCapabilities = ['all', 'model_api', 'free_ide', 'coding_plan', 'search', 'fetch', 'agent', 'browser', 'open_weights', 'desktop_app'];
    const validRegions = ['china', 'global'];
    const validFreshness = ['all', 'fresh', 'stale'];
    const initialQuery = initialParams.get('q');
    if (initialQuery) document.getElementById('catalog-search').value = initialQuery;
    if (validFilters.includes(initialParams.get('filter'))) activeFilter = initialParams.get('filter');
    if (validMethods.includes(initialParams.get('method'))) activeMethod = initialParams.get('method');
    if (validCapabilities.includes(initialParams.get('capability'))) activeCapability = initialParams.get('capability');
    (initialParams.get('region') || '').split(',').forEach(region => { if (validRegions.includes(region)) activeRegions.add(region); });
    if (validFreshness.includes(initialParams.get('fresh'))) activeFreshness = initialParams.get('fresh');
    document.querySelectorAll('.catalog-app [data-region-chip]').forEach(el => {
      const on = activeRegions.has(el.dataset.regionChip);
      el.classList.toggle('active', on);
      el.setAttribute('aria-pressed', String(on));
    });
    document.getElementById('catalog-method-filter').value = activeMethod;
    document.getElementById('catalog-capability-filter').value = activeCapability;
    document.getElementById('catalog-freshness-filter').value = activeFreshness;
    document.getElementById('catalog-sort').addEventListener('change', e => {
      const byName = row => `${row.dataset.provider || row.dataset.name}\n${row.dataset.name}`;
      const sorted = [...rows].sort((a,b) => e.target.value === 'name' ? byName(a).localeCompare(byName(b), 'en', { sensitivity: 'base' }) : e.target.value === 'fresh' ? b.dataset.date.localeCompare(a.dataset.date) : a.dataset.order - b.dataset.order);
      const wrap = document.getElementById('catalog-offer-rows'); sorted.forEach(row => wrap.appendChild(row));
    });
    const clock = document.getElementById('catalog-clock');
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'local timezone';
    renderClock(clock, 'Local time', tz, new Intl.DateTimeFormat([], { hour: '2-digit', minute: '2-digit' }).format(new Date()));
    let offerDataSource = 'embedded';
    let offerHydrationPromise = null;
    document.body.dataset.hydrationState = 'static';

    const hydrateOfferData = () => {
      if (offerHydrationPromise) return offerHydrationPromise;
      document.body.dataset.hydrationState = 'loading';
      offerHydrationPromise = loadOffers().then(async items => {
        signalIndex = indexCommunitySignals(await loadCommunitySignals());
        if (Array.isArray(items) && items.length) {
          renderOffers(items);
          document.body.dataset.dataSource = offerDataSource;
          document.body.dataset.hydrationState = 'ready';
          setFilter(activeFilter);
        } else {
          document.body.dataset.hydrationState = 'error';
          showDataError();
        }
        return items;
      });
      return offerHydrationPromise;
    };

    const hasCatalogIntent = Boolean(
      initialQuery
      || activeFilter !== 'all'
      || activeMethod !== 'all'
      || activeCapability !== 'all'
      || activeRegions.size
      || activeFreshness !== 'all'
      || location.hash === '#catalog-offers'
    );
    const localPreview = location.protocol === 'file:'
      || location.hostname === 'localhost'
      || location.hostname === '127.0.0.1';

    const scheduleOfferHydration = () => {
      const start = () => { void hydrateOfferData(); };
      if (localPreview || hasCatalogIntent) {
        start();
        return;
      }

      let observer = null;
      let fallbackTimer = 0;
      const kick = () => {
        observer?.disconnect();
        if (fallbackTimer) window.clearTimeout(fallbackTimer);
        start();
      };

      const target = document.getElementById('catalog-offers');
      if ('IntersectionObserver' in window && target) {
        observer = new IntersectionObserver(entries => {
          if (entries.some(entry => entry.isIntersecting)) kick();
        }, { rootMargin: '800px 0px' });
        observer.observe(target);
      }

      const app = document.querySelector('.catalog-app');
      app?.addEventListener('pointerdown', kick, { once: true, passive: true });
      app?.addEventListener('focusin', kick, { once: true });
      app?.addEventListener('keydown', kick, { once: true });
      fallbackTimer = window.setTimeout(kick, 2500);
    };

    scheduleOfferHydration();
