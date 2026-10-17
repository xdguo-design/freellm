(() => {
      const copy = {
        en: {
          'daily-log': 'Daily updates', catalog: 'Models', resources: 'Resource directory', 'model-center': 'Model center', 'all-models': 'All models', providers: 'Providers', tools: 'Online tools', api: 'API services', rank: 'Compare', guide: 'Guide',
          freeQuota: 'Free quota', ide: 'Free IDE', apiServices: 'API services', promo: 'Timed / regional deal', studentDiscount: 'Student offer', web: 'Web tools', openWeight: 'Open weights',
          guideOpenAiAlternatives: 'OpenAI API alternatives', guideClaudeAlternatives: 'Claude Code alternatives', guideOpenAiCompatible: 'OpenAI-compatible APIs', guideCodingTools: 'Free AI coding tools', guideSearchApis: 'Free AI search APIs', guideOpenWeights: 'Open-weight models', guideContextWindows: 'Model context windows', guideChinaApi: 'Free AI APIs in China', resourceDirectory: 'Resource directory', allModelsNav: 'All models', providersDirectory: 'Browse by provider'
        },
        zh: {
          'daily-log': '每日更新', catalog: '模型库', resources: '资源目录', 'model-center': '模型中心', 'all-models': '全部模型', providers: '按厂家', tools: '在线工具', api: 'API 服务', rank: '榜单', guide: '使用指南',
          freeQuota: '免费额度', ide: '免费 AI IDE', apiServices: 'AI API 服务', promo: '试用与优惠', studentDiscount: '学生优惠', web: '网页工具', openWeight: '开源权重',
          guideOpenAiAlternatives: 'OpenAI API 替代品', guideClaudeAlternatives: 'Claude Code 替代品', guideOpenAiCompatible: '免费 OpenAI 兼容 API', guideCodingTools: '免费 AI 编程工具', guideSearchApis: '免费 AI 搜索 API', guideOpenWeights: '开源权重模型', guideContextWindows: '模型上下文窗口', guideChinaApi: '国内免费 AI API', resourceDirectory: '资源目录', allModelsNav: '全部模型', providersDirectory: '按厂家浏览'
        }
      };
      const update = () => {
        const language = document.documentElement.lang === 'zh-CN' ? 'zh' : 'en';
        const labels = copy[language];
        document.querySelectorAll('[data-nav-key]').forEach(node => {
          const key = node.dataset.navKey;
          if (labels[key]) node.textContent = labels[key];
        });
        document.querySelectorAll('.category-seo-links [data-i18n]').forEach(node => {
          const key = node.dataset.i18n;
          if (labels[key]) node.textContent = labels[key];
        });
      };
      const adaptFileNavigation = () => {
        if (window.location.protocol !== 'file:') return;
        const siteRoot = document.body.classList.contains('model-center-page') ? '../../' : '../';
        const query = window.location.search;
        document.querySelectorAll('.fl-site-nav a[href^="/"]').forEach(link => {
          const path = link.getAttribute('href').split(/[?#]/, 1)[0];
          if (!path.endsWith('/')) return;
          link.setAttribute('href', `${siteRoot}${path.slice(1)}index.html${query}`);
        });
      };
      update();
      adaptFileNavigation();
      new MutationObserver(update).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
    })();
