
(() => {
  const boot = async () => {
    const body = document.body;
    if (!body || body.dataset.prototypeFidelityV4 === '1') return;
    body.dataset.prototypeFidelityV4 = '1';
    const section = body.dataset.flSection || '';
    const $ = (s, r = document) => r.querySelector(s);
    const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
    const clean = v => String(v || '').replace(/\s+/g, ' ').trim();
    const esc = v => clean(v).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

    if (section === 'models' && $('#model-catalog')) {
      body.classList.add('prototype-model-v4');
      const rows = $('#model-catalog .catalog-row');
      const heroNums = $('.hero-card strong').map(x => clean(x.textContent));
      let items = rows.map((row, i) => ({
        i,
        id: clean(row.dataset.modelId || $('.model-id', row)?.textContent),
        name: clean($('.model-name strong', row)?.textContent || $('.model-name', row)?.textContent || 'Model'),
        provider: clean($('.provider-filter', row)?.textContent || 'Provider'),
        providerId: clean(row.dataset.providerId),
        context: clean(row.querySelector('[data-label="上下文长度"]')?.textContent || '—'),
        rate: clean(row.querySelector('[data-label="速率限制"]')?.textContent || '—'),
        cn: clean(row.querySelector('[data-label="中国大陆可用性"]')?.textContent || '待核验'),
        modalities: clean(row.dataset.modality || '').split(',').filter(Boolean),
        href: $('.model-name[href]', row)?.getAttribute('href') || '/models/all/',
        official: $('.source-link', row)?.getAttribute('href') || '/models/all/'
      }));
      try {
        const response = await fetch('/data/daily-log/2026-09-28.json', { cache: 'no-store' });
        if (response.ok) {
          const daily = await response.json();
          const observed = Array.isArray(daily?.observed?.models) ? daily.observed.models : [];
          if (observed.length) {
            const observedIds = new Set(observed.map(x => clean(x.id)).filter(Boolean));
            items = items.filter(x => observedIds.has(x.id));
            const known = new Set(items.map(x => x.id));
            observed.forEach(model => {
              const id = clean(model.id);
              if (!id || known.has(id)) return;
              const sourceUrl = clean(model.sourceUrl) || '/models/all/';
              items.push({
                i: items.length,
                id,
                name: clean(model.model || id.split('/').pop() || 'Model'),
                provider: clean(model.provider || model.providerId || 'Provider'),
                providerId: clean(model.providerId),
                context: '待补录',
                rate: '—',
                cn: '待核验',
                modalities: [],
                href: sourceUrl,
                official: sourceUrl
              });
              known.add(id);
            });
            items.forEach((item, index) => { item.i = index; });
          }
        }
      } catch (error) {
        console.debug('FreeLLM daily model refresh skipped', error);
      }
      const total = String(items.length || Number(heroNums[0]) || rows.length);
      const providers = String(new Set(items.map(x => x.providerId || x.provider).filter(Boolean)).size || Number(heroNums[1]) || 0);
      const featured = items.find(x => /MiMo-V2\.6/i.test(x.name)) || items[0];
      const providerOptions = [...new Set(items.map(x => x.provider))].map(x => '<option>' + esc(x) + '</option>').join('');
      const recent = items.slice(0, 5).map(x => '<a class="pf-recent-item" href="' + esc(x.href) + '"><span class="pf-recent-mark">' + esc(x.provider.slice(0,2).toUpperCase()) + '</span><span><strong>' + esc(x.name) + '</strong><small>' + esc(x.provider) + '</small></span></a>').join('');

      const shell = document.createElement('div');
      shell.className = 'pf-model-shell';
      shell.innerHTML =
        '<section class="pf-model-hero"><div class="pf-model-hero-copy"><span class="pf-kicker">模型</span><h1>模型库</h1><h2>发现、比较和使用全球优质的 AI 模型</h2><p>汇聚全球顶尖的开源与商业模型，支持多维度筛选与对比，帮助你找到最适合的 AI 能力。</p><div class="pf-model-stats"><div class="pf-model-stat"><strong>' + esc(total) + '</strong><small>收录模型</small></div><div class="pf-model-stat"><strong>' + esc(providers) + '</strong><small>模型厂商</small></div><div class="pf-model-stat"><strong>2026-09-28</strong><small>最近更新</small></div></div></div><div class="pf-model-art" aria-hidden="true"><span class="pf-model-orbit"></span><span class="pf-ai-cube">AI</span><span class="pf-glass pf-g1"></span><span class="pf-glass pf-g2"></span><span class="pf-glass pf-g3"></span><span class="pf-float one">⬡ 更强大的模型<br><small>More Capabilities</small></span><span class="pf-float two">▥ 更美好的未来<br><small>A Brighter Tomorrow</small></span><span class="pf-script">Better AI<br>A Brighter Tomorrow</span></div></section>' +
        '<section class="pf-model-filter"><span class="pf-filter-icon">▽</span><label>厂商 <select data-pf-filter="provider"><option value="">全部</option>' + providerOptions + '</select></label><label>模态 <select data-pf-filter="modality"><option value="">全部</option><option value="text">文本</option><option value="image">图像</option><option value="audio">语音</option><option value="video">视频</option><option value="reasoning">推理</option></select></label><label>上下文长度 <select data-pf-filter="context"><option value="">全部</option><option value="128K">128K+</option><option value="512K">512K+</option><option value="1M">1M</option></select></label><label>是否免费 <select><option>全部</option><option>免费可用</option></select></label><label>开源协议 <select><option>全部</option><option>开源</option><option>商业</option></select></label><label>地区 <select data-pf-filter="region"><option value="">全部</option><option value="大陆">国内可用</option><option value="不可用">国外入口</option><option value="待核验">待核验</option></select></label><button class="pf-filter-reset" type="button">↻ 重置筛选</button></section>' +
        '<div class="pf-model-layout"><div><article class="pf-feature-model"><div class="pf-feature-copy"><span class="pf-feature-label">♛ 重磅推荐</span><div class="pf-feature-title"><h2>' + esc(featured?.name || 'MiMo V2.6 Flash') + '</h2><span class="pf-pill hot">限时免费</span></div><div class="pf-model-tags" style="margin-top:9px"><span>' + esc(featured?.context || '1M') + ' 上下文</span><span>多模态</span><span>高性价比</span></div><p>当前目录中的重点模型入口。保留真实上下文、模态、地区与官方来源，快速进入详情或官方使用路径。</p><div class="pf-feature-actions"><a class="primary" href="' + esc(featured?.official || '/models/all/') + '" target="_blank" rel="noopener noreferrer">立即使用　→</a><a href="' + esc(featured?.href || '/models/all/') + '">查看详情</a></div></div><div class="pf-feature-art"><span class="pf-feature-note left">' + esc(featured?.context || '1M') + ' 上下文</span><span class="pf-feature-note right">更大的世界<br>更小的距离</span><span class="pf-screen s1"></span><span class="pf-feature-logo">M</span><span class="pf-screen s2"></span></div></article><div class="pf-model-tabs"><button class="active" type="button" data-pf-tab="">全部模型 (' + esc(total) + ')</button><button type="button" data-pf-tab="text">语言模型</button><button type="button" data-pf-tab="multimodal">多模态模型</button><button type="button" data-pf-tab="image">图像模型</button><button type="button" data-pf-tab="audio">音频模型</button><button type="button" data-pf-tab="video">视频模型</button><button type="button" data-pf-tab="reasoning">推理模型</button><label class="pf-sort">排序 <select data-pf-sort><option>综合排序</option></select></label></div><section class="pf-model-grid"></section></div><aside class="pf-model-side"><section class="pf-side-card"><h3>模型对比</h3><div class="pf-compare-empty"><div><b>＋</b><span>点击下方模型卡片的对比按钮，开始对比</span></div></div><div class="pf-recent" data-pf-compare-list></div><button class="pf-side-button" type="button" disabled data-pf-compare-start>开始对比 (0/4)</button></section><section class="pf-side-card"><h3>最近浏览</h3><div class="pf-recent">' + recent + '</div></section></aside></div>';

      const anchor = $('.ref-topbar') || $('.fl-site-rail');
      anchor ? anchor.insertAdjacentElement('afterend', shell) : body.prepend(shell);
      const grid = $('.pf-model-grid', shell);
      const provider = $('[data-pf-filter="provider"]', shell);
      const modality = $('[data-pf-filter="modality"]', shell);
      const context = $('[data-pf-filter="context"]', shell);
      const region = $('[data-pf-filter="region"]', shell);
      let tab = '';
      const compare = new Set();

      const updateCompare = () => {
        const selected = [...compare].map(i => items[i]).filter(Boolean);
        $('[data-pf-compare-list]', shell).innerHTML = selected.map(x => '<div class="pf-recent-item"><span class="pf-recent-mark">' + esc(x.provider.slice(0,2).toUpperCase()) + '</span><span><strong>' + esc(x.name) + '</strong><small>' + esc(x.context) + '</small></span></div>').join('');
        const b = $('[data-pf-compare-start]', shell);
        b.textContent = '开始对比 (' + selected.length + '/4)';
        b.disabled = selected.length < 2;
        if (!b.disabled) { b.style.background = '#0868f7'; b.style.color = '#fff'; }
      };
      const render = () => {
        const list = items.filter(x => {
          if (provider.value && x.provider !== provider.value) return false;
          if (modality.value && !x.modalities.includes(modality.value)) return false;
          if (context.value && !x.context.includes(context.value)) return false;
          if (region.value && !x.cn.includes(region.value)) return false;
          if (tab === 'multimodal' && x.modalities.length < 2) return false;
          if (tab && tab !== 'multimodal' && !x.modalities.includes(tab)) return false;
          return true;
        }).slice(0, 12);
        grid.innerHTML = list.length ? list.map(x => '<article class="pf-model-card"><div class="pf-model-card-head"><span class="pf-model-mark">' + esc(x.provider.slice(0,2).toUpperCase()) + '</span><div><small>' + esc(x.provider) + '</small><h3>' + esc(x.name) + '</h3></div><span class="pf-model-badge">热门</span></div><p>' + esc(x.modalities.join(' · ') || '模型能力以官方说明为准') + ' · 上下文 ' + esc(x.context) + '</p><div class="pf-model-tags">' + x.modalities.slice(0,4).map(m => '<span>' + esc(m) + '</span>').join('') + '<span>' + esc(x.cn) + '</span></div><div class="pf-model-meta"><span>上下文 ' + esc(x.context) + '</span><span>' + esc(x.rate) + '</span></div><div class="pf-model-actions"><button type="button" data-pf-compare="' + x.i + '">' + (compare.has(x.i) ? '✓ 已加入对比' : '＋ 加入对比') + '</button><a class="primary" href="' + esc(x.href) + '">立即使用 →</a></div></article>').join('') : '<div class="pf-no-models">没有匹配模型，请调整筛选条件。</div>';
        $$('[data-pf-compare]', grid).forEach(btn => btn.addEventListener('click', () => {
          const i = Number(btn.dataset.pfCompare);
          compare.has(i) ? compare.delete(i) : compare.size < 4 && compare.add(i);
          updateCompare(); render();
        }));
      };
      [provider, modality, context, region].forEach(el => el.addEventListener('change', render));
      $$('.pf-model-tabs [data-pf-tab]', shell).forEach(btn => btn.addEventListener('click', () => {
        $$('.pf-model-tabs [data-pf-tab]', shell).forEach(x => x.classList.remove('active'));
        btn.classList.add('active'); tab = btn.dataset.pfTab || ''; render();
      }));
      $('.pf-filter-reset', shell).addEventListener('click', () => {
        provider.value = modality.value = context.value = region.value = ''; tab = '';
        $$('.pf-model-tabs [data-pf-tab]', shell).forEach((x,i) => x.classList.toggle('active', i === 0)); render();
      });
      render();
    }

    if (section === 'home' && $('#catalog-offer-rows')) {
      body.classList.add('prototype-resource-v4');
      let offers = [];
      try {
        const response = await fetch('/data/offers-ranked.json', { cache: 'no-store' });
        if (response.ok) {
          const payload = await response.json();
          offers = Array.isArray(payload) ? payload : [];
        }
      } catch (error) {
        console.debug('FreeLLM offer metadata refresh skipped', error);
      }
      const offerMeta = new Map(offers.map(item => [clean(item.id), item]));
      const getCards = () => $$('#catalog-offer-rows .offer');
      const initialCards = getCards();
      const heroCount = Number(clean($('#heroCount')?.textContent));
      const total = offers.length || heroCount || initialCards.length || 49;
      const isVerifiedOffer = item => Boolean(item && (
        item.status === 'verified' ||
        item.handsOn ||
        (item.endpointCheck && item.endpointCheck.verdict !== 'NETWORK_ERROR') ||
        (item.networkCheck && item.networkCheck.region && item.networkCheck.region !== 'none')
      ));
      const verified = offers.length
        ? offers.filter(isVerifiedOffer).length
        : initialCards.filter(card => $('.flag-endpoint,.flag-net-ok,.flag-hands-on', card)).length;
      const pending = Math.max(0, total - verified);
      const regions = new Set(offers.map(item => clean(item.originCountry || item.accessRegion || item.availability)).filter(Boolean));
      const regionCount = Math.max(regions.size, 4);

      const overview = document.createElement('section');
      overview.className = 'pf-resource-overview';
      overview.innerHTML =
        '<section class="pf-resource-hero"><span class="eyebrow">VERIFIED AI RESOURCES</span><h1>全部资源</h1><p>产品、免费方式、额度、有效期、地区和核验状态放在同一张卡片里。</p><div class="pf-resource-stats"><article class="pf-resource-stat"><i>◇</i><div><small>全部资源</small><strong>' + total + '</strong><small>个资源</small></div></article><article class="pf-resource-stat"><i>✓</i><div><small>已验证可用</small><strong>' + verified + '</strong><small>个资源</small></div></article><article class="pf-resource-stat"><i>◷</i><div><small>待验证</small><strong>' + pending + '</strong><small>个资源</small></div></article><article class="pf-resource-stat"><i>◎</i><div><small>覆盖地区/国家</small><strong>' + regionCount + '</strong><small>类地区</small></div></article></div><div class="pf-resource-hero-art"></div></section>' +
        '<section class="pf-resource-filters"><div class="pf-filter-row"><b>资源类型</b><button class="active" data-pf-kind="all">全部 (' + total + ')</button><button data-pf-kind="model">模型</button><button data-pf-kind="tool">工具</button><button data-pf-kind="platform">平台</button><button data-pf-kind="cloud">云服务</button><button data-pf-kind="development">开发框架</button><button data-pf-kind="student">学生优惠</button><button data-pf-kind="other">其他</button></div><div class="pf-filter-row"><b>特色筛选</b><button data-pf-kind="free">免费使用</button><button data-pf-kind="cn">国内可用</button><button data-pf-kind="intl">国外可用</button><button data-pf-kind="verified">已验证</button><button data-pf-kind="new">新上线</button><span class="pf-filter-spacer"></span><b>排序方式</b><button class="active" data-pf-sort-resource="default">默认排序</button><button data-pf-sort-resource="new">最新上线</button><button data-pf-sort-resource="verified">可用性优先</button><span class="pf-view-toggle"><button class="active" data-pf-view="grid">▦</button><button data-pf-view="list">☷</button></span></div><div class="pf-filter-row"><b>地区筛选</b><button class="active" data-pf-region-resource="all">全部地区</button><button data-pf-region-resource="cn">中国</button><button data-pf-region-resource="na">北美</button><button data-pf-region-resource="eu">欧洲</button><button data-pf-region-resource="asia">亚太</button><button data-pf-region-resource="other">其他</button></div></section>';
      $('.catalog-content')?.prepend(overview);

      const metadataFor = card => offerMeta.get(clean(card.dataset.detail)) || null;
      const cardText = (card, meta) => clean([
        card.textContent,
        meta?.title, meta?.titleEn, meta?.provider, meta?.productType,
        ...(meta?.type || []), ...(meta?.capabilities || []), ...(meta?.badges || []),
        meta?.freeMechanism, meta?.access, meta?.accessSummary, meta?.availability,
        meta?.originCountry, meta?.studentEligibility, meta?.studentSummary
      ].filter(Boolean).join(' ')).toLowerCase();
      const isStudent = meta => Boolean(meta && (
        meta.studentEligibility || meta.studentSummary ||
        (Array.isArray(meta.studentSourceUrls) && meta.studentSourceUrls.length)
      ));
      const matchKind = (kind, card, meta, t) => {
        if (kind === 'all') return true;
        if (kind === 'student') return isStudent(meta) || /student|学生|education/.test(t);
        if (kind === 'free') return /免费|free|¥0|quota|permanent|credits|trial/.test(t);
        if (kind === 'cn') return /中国|国内|china|beijing|cn\b/.test(t);
        if (kind === 'intl') return /global|国际|海外|国外|worldwide|international/.test(t);
        if (kind === 'verified') return isVerifiedOffer(meta) || !!$('.flag-endpoint,.flag-net-ok,.flag-hands-on', card);
        if (kind === 'new') return /新|new|2026-09-2[4-8]/.test(t) || /^2026-09-2[4-8]$/.test(clean(meta?.date));
        if (kind === 'model') return /model|模型|llm|gemini|deepseek|qwen|glm|mimo/.test(t);
        if (kind === 'tool') return /tool|ide|coding|agent|workbuddy|cursor|copilot|desktop|browser/.test(t);
        if (kind === 'development') return /api|sdk|github|code|developer|coding|编程|开发/.test(t);
        if (kind === 'cloud') return /cloud|云|aws|aliyun|阿里云|火山|huawei|nvidia/.test(t);
        if (kind === 'platform') return /studio|platform|平台|web|workspace|console/.test(t);
        if (kind === 'other') return !/(model|模型|llm|tool|ide|api|sdk|cloud|云|studio|platform|学生|student)/.test(t);
        return true;
      };
      const matchRegion = (region, t) => {
        if (region === 'all') return true;
        if (region === 'cn') return /中国|国内|china|beijing|cn\b/.test(t);
        if (region === 'na') return /north america|united states|美国|\bus\b|canada/.test(t);
        if (region === 'eu') return /europe|欧洲|\beu\b|germany|france|uk|united kingdom/.test(t);
        if (region === 'asia') return /中国|日本|新加坡|asia|国内|japan|singapore|korea/.test(t);
        if (region === 'other') return !/(中国|国内|china|beijing|north america|united states|美国|\bus\b|canada|europe|欧洲|\beu\b|germany|france|uk|united kingdom|日本|新加坡|asia|japan|singapore|korea)/.test(t);
        return true;
      };

      let kind = 'all', region = 'all';
      const apply = () => {
        getCards().forEach(card => {
          const meta = metadataFor(card);
          const t = cardText(card, meta);
          card.hidden = !(matchKind(kind, card, meta, t) && matchRegion(region, t));
        });
      };
      const sortCards = mode => {
        const grid = $('#catalog-offer-rows');
        if (!grid) return;
        const cards = getCards();
        const value = card => {
          const meta = metadataFor(card);
          if (mode === 'new') return clean(meta?.date || meta?.lastVerifiedAt || '').replace(/-/g,'');
          if (mode === 'verified') return isVerifiedOffer(meta) || !!$('.flag-endpoint,.flag-net-ok,.flag-hands-on', card) ? '1' : '0';
          return String(999999 - Number(meta?.order || 999999)).padStart(6,'0');
        };
        cards.sort((a,b) => value(b).localeCompare(value(a))).forEach(card => grid.appendChild(card));
        apply();
      };

      $$('[data-pf-kind]', overview).forEach(btn => btn.addEventListener('click', () => {
        $$('[data-pf-kind]', overview).forEach(x => x.classList.remove('active'));
        btn.classList.add('active'); kind = btn.dataset.pfKind; apply();
      }));
      $$('[data-pf-region-resource]', overview).forEach(btn => btn.addEventListener('click', () => {
        $$('[data-pf-region-resource]', overview).forEach(x => x.classList.remove('active'));
        btn.classList.add('active'); region = btn.dataset.pfRegionResource; apply();
      }));
      $$('[data-pf-sort-resource]', overview).forEach(btn => btn.addEventListener('click', () => {
        $$('[data-pf-sort-resource]', overview).forEach(x => x.classList.remove('active'));
        btn.classList.add('active'); sortCards(btn.dataset.pfSortResource);
      }));
      $$('[data-pf-view]', overview).forEach(btn => btn.addEventListener('click', () => {
        $$('[data-pf-view]', overview).forEach(x => x.classList.remove('active'));
        btn.classList.add('active');
        $('#catalog-offer-rows')?.classList.toggle('pf-resource-list-view', btn.dataset.pfView === 'list');
      }));

      const grid = $('#catalog-offer-rows');
      if (grid && 'MutationObserver' in window) {
        let scheduled = false;
        new MutationObserver(() => {
          if (scheduled) return;
          scheduled = true;
          requestAnimationFrame(() => { scheduled = false; apply(); });
        }).observe(grid, { childList: true });
      }
      const last = $('#catalog-last-checked');
      if (last) last.textContent = 'Last checked: 28 Sep 2026 · Data is subject to change';
      $('#student-offers')?.remove();
      $('.ref-student-banner')?.remove();
      apply();
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(boot, 0), { once:true });
  else setTimeout(boot, 0);
})();
