/**
 * Workflow recipe step simulation
 * Enhances #workflow-dialog to show per-step outcomes when recipe.steps[].demo exists.
 */
(function () {
  'use strict';
  var FALLBACK_DEMOS = {"idea-to-plan":["✓ 澄清问题与约束\n  · 目标用户：内部产品团队\n  · 方案候选：3 个，已排除 1 个\n  → 产出：对齐后的问题定义与取舍记录","✓ 生成实施计划草案\n  · 任务 8 项 · 含验收标准与依赖\n  · 风险边界：2 条已标注\n  → 产出：可评审的计划文档","✓ 按清单推进\n  · 已完成 5/8 · 当前可验证节点已通过\n  → 产出：带进度的执行记录","✓ 验收核对完成\n  · 8/8 验收项有证据\n  · 无“大概好了”项\n  → 产出：可交付的验证清单"],"从一句想法到可执行计划":["✓ 澄清问题与约束\n  · 目标用户：内部产品团队\n  · 方案候选：3 个，已排除 1 个\n  → 产出：对齐后的问题定义与取舍记录","✓ 生成实施计划草案\n  · 任务 8 项 · 含验收标准与依赖\n  · 风险边界：2 条已标注\n  → 产出：可评审的计划文档","✓ 按清单推进\n  · 已完成 5/8 · 当前可验证节点已通过\n  → 产出：带进度的执行记录","✓ 验收核对完成\n  · 8/8 验收项有证据\n  · 无“大概好了”项\n  → 产出：可交付的验证清单"],"data-to-deck":["✓ 原始表已规范化\n  · 透视：按渠道 × 周\n  · 异常行：已标记 3 处\n  → 产出：可分析口径表","✓ 关键指标汇总\n  · GMV / 转化率 / 退款率\n  · 环比已计算\n  → 产出：指标汇总表","✓ Dashboard 已生成\n  · 4 张图 + 1 张结论表\n  → 产出：Excel 数据看板","✓ 汇报 Deck 已导出\n  · 结论 → 证据 → 下一步\n  · Q3-review.pptx（12 页）\n  → 产出：可上台的 PPTX"],"从数据表到汇报演示":["✓ 原始表已规范化\n  · 透视：按渠道 × 周\n  · 异常行：已标记 3 处\n  → 产出：可分析口径表","✓ 关键指标汇总\n  · GMV / 转化率 / 退款率\n  · 环比已计算\n  → 产出：指标汇总表","✓ Dashboard 已生成\n  · 4 张图 + 1 张结论表\n  → 产出：Excel 数据看板","✓ 汇报 Deck 已导出\n  · 结论 → 证据 → 下一步\n  · Q3-review.pptx（12 页）\n  → 产出：可上台的 PPTX"],"document-polish":["✓ 完成 4 段协同修订\n  · 语气更正式 · 补全验收表述\n  · 删除空话 2 处\n  → 产出：可排版的定稿正文","✓ 已生成正式 Word\n  · 标题层级 / 表格 / 页脚页码\n  · policy-refund-v1.docx\n  → 产出：可对外发送的 .docx","✓ 已导出定稿 PDF\n  · 3 页 · 字体已嵌入\n  · policy-refund-v1.pdf\n  → 产出：可归档的 PDF"],"从草稿到正式文档":["✓ 完成 4 段协同修订\n  · 语气更正式 · 补全验收表述\n  · 删除空话 2 处\n  → 产出：可排版的定稿正文","✓ 已生成正式 Word\n  · 标题层级 / 表格 / 页脚页码\n  · policy-refund-v1.docx\n  → 产出：可对外发送的 .docx","✓ 已导出定稿 PDF\n  · 3 页 · 字体已嵌入\n  · policy-refund-v1.pdf\n  → 产出：可归档的 PDF"],"content-to-wechat":["✓ 初稿完成\n  · 引用 5 条 · 结构：痛点→方法→案例\n  → 产出：可配图的 Markdown 正文","✓ 封面已生成\n  · 风格：编辑向 · 主色：深蓝\n  · cover-wechat-01.png\n  → 产出：文章封面图","✓ 公众号 HTML 已就绪\n  · 代码高亮 / 引用块 / 图片位\n  → 产出：可粘贴发布的排版稿","✓ 已写入公众号草稿箱\n  · 状态：待群发\n  → 产出：可群发的公众号草稿"],"从选题到公众号发布":["✓ 初稿完成\n  · 引用 5 条 · 结构：痛点→方法→案例\n  → 产出：可配图的 Markdown 正文","✓ 封面已生成\n  · 风格：编辑向 · 主色：深蓝\n  · cover-wechat-01.png\n  → 产出：文章封面图","✓ 公众号 HTML 已就绪\n  · 代码高亮 / 引用块 / 图片位\n  → 产出：可粘贴发布的排版稿","✓ 已写入公众号草稿箱\n  · 状态：待群发\n  → 产出：可群发的公众号草稿"],"resume-to-offer":["✓ 基础简历排版完成\n  · 版式：经典单栏\n  · resume-base.pdf\n  → 产出：专业排版 PDF","✓ 已按 JD 重排重点\n  · 命中关键词：React / 系统设计\n  · 弱相关经历已压缩\n  → 产出：岗位定制版正文","✓ HTML 简历美化完成\n  · A4 · 隐私字段已处理\n  → 产出：精美 HTML 简历","✓ 去 AI 腔完成\n  · 删除套话 6 处 · 保留事实密度\n  → 产出：可投递的最终简历"],"从经历到定制简历":["✓ 基础简历排版完成\n  · 版式：经典单栏\n  · resume-base.pdf\n  → 产出：专业排版 PDF","✓ 已按 JD 重排重点\n  · 命中关键词：React / 系统设计\n  · 弱相关经历已压缩\n  → 产出：岗位定制版正文","✓ HTML 简历美化完成\n  · A4 · 隐私字段已处理\n  → 产出：精美 HTML 简历","✓ 去 AI 腔完成\n  · 删除套话 6 处 · 保留事实密度\n  → 产出：可投递的最终简历"],"react-feature-delivery":["✓ 规范检查通过\n  · 数据获取 / 包体积 / 渲染路径已对齐\n  → 产出：实现约束清单","✓ 组件结构重组完成\n  · 复合组件 3 个 · props 钻取已消除\n  → 产出：可扩展组件树","✓ 交互产物已构建\n  · 本地预览通过\n  → 产出：可点的功能原型","✓ E2E 全部通过\n  · 12 passed · 0 failed\n  → 产出：可合并的测试报告"],"从需求到 React 功能交付":["✓ 规范检查通过\n  · 数据获取 / 包体积 / 渲染路径已对齐\n  → 产出：实现约束清单","✓ 组件结构重组完成\n  · 复合组件 3 个 · props 钻取已消除\n  → 产出：可扩展组件树","✓ 交互产物已构建\n  · 本地预览通过\n  → 产出：可点的功能原型","✓ E2E 全部通过\n  · 12 passed · 0 failed\n  → 产出：可合并的测试报告"]};
  if (typeof window === 'undefined') return;
  var path = (location.pathname || '');
  if (path.indexOf('/workflow') === -1 && path.indexOf('/skills/lab') === -1) return;

  var STYLE_ID = 'workflow-recipe-sim-style';
  var TIMER = null;

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement('style');
    s.id = STYLE_ID;
    s.textContent = [
      '.sim-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:6px 0 14px;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:linear-gradient(180deg,var(--surface) 0%,var(--surface-soft) 100%)}',
      '.sim-status{display:flex;align-items:center;gap:10px;min-width:0}',
      '.sim-pulse{width:8px;height:8px;border-radius:50%;background:var(--ink-tertiary);flex:0 0 auto;transition:background .2s}',
      '.sim-toolbar[data-state="running"] .sim-pulse{background:var(--accent);animation:simPulse 1.2s ease-out infinite}',
      '.sim-toolbar[data-state="done"] .sim-pulse{background:var(--pale-green-text,#346538)}',
      '@keyframes simPulse{0%{box-shadow:0 0 0 0 rgba(23,68,232,.35)}70%{box-shadow:0 0 0 8px rgba(23,68,232,0)}100%{box-shadow:0 0 0 0 rgba(23,68,232,0)}}',
      '.sim-status-text{display:flex;flex-direction:column;gap:2px;min-width:0}',
      '.sim-status-text strong{font:600 12.5px/1.2 var(--font-sans);color:var(--ink)}',
      '.sim-status-text small{color:var(--ink-tertiary);font:500 11px/1.3 var(--font-mono);letter-spacing:.02em}',
      '.sim-progress{flex:1;min-width:120px;max-width:220px;height:4px;border-radius:999px;background:var(--line);overflow:hidden}',
      '.sim-progress>i{display:block;height:100%;width:0%;border-radius:inherit;background:linear-gradient(90deg,var(--accent),#7BC0E5);transition:width .45s cubic-bezier(.22,.61,.36,1)}',
      '.sim-replay{appearance:none;border:1px solid var(--line);background:var(--surface);border-radius:8px;padding:7px 12px;cursor:pointer;color:var(--ink-secondary);font:500 12px/1 var(--font-sans)}',
      '.sim-replay:hover{color:var(--ink);border-color:var(--ink-tertiary)}',
      '.recipe-steps.sim-mode{gap:0}',
      '.recipe-steps.sim-mode .recipe-step{position:relative;display:grid;grid-template-columns:36px minmax(0,1fr);gap:12px;padding:0 0 14px;border:none;border-left:none;border-radius:0;background:transparent;opacity:0;transform:translateY(10px);transition:opacity .4s ease,transform .4s ease}',
      '.recipe-steps.sim-mode .recipe-step.is-visible{opacity:1;transform:none}',
      '.recipe-steps.sim-mode .recipe-step:last-child{padding-bottom:0}',
      '.sim-rail{position:relative;display:flex;flex-direction:column;align-items:center}',
      '.sim-rail .recipe-step-number{position:relative;z-index:1;display:grid;place-items:center;width:28px;height:28px;border-radius:50%;border:1.5px solid var(--line);background:var(--surface);color:var(--ink-tertiary);font:600 10.5px/1 var(--font-mono);transition:background .25s,border-color .25s,color .25s,box-shadow .25s}',
      '.sim-rail::after{content:"";position:absolute;top:28px;bottom:-14px;left:50%;width:1.5px;transform:translateX(-50%);background:var(--line)}',
      '.recipe-step:last-child .sim-rail::after{display:none}',
      '.recipe-step.is-running .sim-rail .recipe-step-number,.recipe-step.is-done .sim-rail .recipe-step-number{border-color:var(--accent);color:var(--accent);background:var(--accent-soft)}',
      '.recipe-step.is-done .sim-rail .recipe-step-number{background:var(--accent);color:#fff;border-color:var(--accent);box-shadow:0 0 0 4px rgba(23,68,232,.12)}',
      '.recipe-step.is-done .sim-rail::after{background:rgba(23,68,232,.35)}',
      '.sim-body{padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--surface);transition:border-color .25s,box-shadow .25s}',
      '.recipe-step.is-running .sim-body{border-color:rgba(23,68,232,.3);box-shadow:0 0 0 1px rgba(23,68,232,.08),0 8px 20px rgba(23,68,232,.06)}',
      '.sim-top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}',
      '.sim-top strong{display:block;font-size:13.5px;color:var(--ink)}',
      '.sim-top .step-detail{display:block;margin-top:4px;color:var(--ink-secondary);line-height:1.55;font-size:12.5px}',
      '.step-badge{flex:0 0 auto;padding:3px 8px;border-radius:999px;white-space:nowrap;font:500 10px/1.3 var(--font-mono);letter-spacing:.04em;color:var(--ink-tertiary);background:var(--surface-soft);border:1px solid var(--line)}',
      '.recipe-step.is-running .step-badge{color:var(--accent);background:var(--accent-soft);border-color:transparent}',
      '.recipe-step.is-done .step-badge{color:var(--pale-green-text,#346538);background:var(--pale-green-bg,#EDF3EC);border-color:transparent}',
      '.step-console{margin-top:0;padding:0 12px;border-radius:8px;background:var(--code-bg);color:var(--code-text);font:400 11px/1.55 var(--font-mono);opacity:0;max-height:0;overflow:hidden;white-space:pre-wrap;transition:opacity .3s,max-height .35s,margin .25s,padding .25s}',
      '.recipe-step.is-running .step-console,.recipe-step.is-done .step-console{opacity:1;max-height:220px;margin-top:10px;padding:10px 12px}',
      '.step-console .line-ok{color:#9BE7A5;font-weight:500}',
      '.step-console .line-out{color:#7BC0E5}',
      '.step-console .line-muted{opacity:.62}',
      '.step-console .cursor{display:inline-block;width:6px;height:12px;margin-left:2px;vertical-align:-1px;background:rgba(244,242,238,.7);animation:blink 1s steps(1) infinite}',
      '@keyframes blink{50%{opacity:0}}',
      '@media (prefers-reduced-motion:reduce){.recipe-steps.sim-mode .recipe-step{opacity:1!important;transform:none!important;transition:none!important}.sim-toolbar[data-state="running"] .sim-pulse{animation:none}.step-console .cursor{animation:none}}'
    ].join('');
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>')
      .replace(/"/g, '"');
  }

  function formatDemo(demo) {
    return String(demo || '').split('\n').map(function (line, idx) {
      var safe = esc(line);
      if (idx === 0) return '<span class="line-ok">' + safe + '</span>';
      if (line.trim().indexOf('→') === 0) return '<span class="line-out">' + safe + '</span>';
      return '<span class="line-muted">' + safe + '</span>';
    }).join('<br>');
  }

  function ensureToolbar(stepsRoot) {
    var existing = document.getElementById('sim-toolbar');
    if (existing) return existing;
    var bar = document.createElement('div');
    bar.className = 'sim-toolbar';
    bar.id = 'sim-toolbar';
    bar.dataset.state = 'idle';
    bar.innerHTML = '<div class="sim-status"><span class="sim-pulse" aria-hidden="true"></span><div class="sim-status-text"><strong id="sim-status-label">准备模拟执行</strong><small id="sim-status-sub">打开配方后将逐步演示每一步产出</small></div></div><div class="sim-progress" aria-hidden="true"><i id="sim-progress-bar"></i></div><button type="button" class="sim-replay" id="sim-replay" hidden>重新演示</button>';
    stepsRoot.parentNode.insertBefore(bar, stepsRoot);
    return bar;
  }

  function findRecipes() {
    if (window.__WORKFLOW_RECIPES__) return window.__WORKFLOW_RECIPES__;
    var scripts = document.querySelectorAll('script:not([src])');
    for (var i = 0; i < scripts.length; i++) {
      var t = scripts[i].textContent || '';
      var m = t.match(/const recipes\s*=\s*(\[[\s\S]*?\]);/);
      if (m) {
        try {
          var arr = (new Function('return ' + m[1]))();
          window.__WORKFLOW_RECIPES__ = arr;
          return arr;
        } catch (e) {}
      }
    }
    return [];
  }

  function runSim(recipe) {
    injectStyles();
    var stepsRoot = document.getElementById('recipe-steps');
    if (!stepsRoot || !recipe) return;
    var steps = recipe.steps || [];
    var key = recipe.id || recipe.title || '';
    var fb = FALLBACK_DEMOS[key];
    if (fb) {
      steps = steps.map(function (s, i) {
        if (s && !s.demo && fb[i]) {
          var copy = {};
          for (var k in s) copy[k] = s[k];
          copy.demo = fb[i];
          return copy;
        }
        return s;
      });
    }
    var hasDemo = steps.some(function (s) { return s && s.demo; });
    if (!hasDemo) return;

    if (TIMER) { clearTimeout(TIMER); TIMER = null; }

    var toolbar = ensureToolbar(stepsRoot);
    var statusLabel = document.getElementById('sim-status-label');
    var statusSub = document.getElementById('sim-status-sub');
    var progressBar = document.getElementById('sim-progress-bar');
    var replayBtn = document.getElementById('sim-replay');
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    stepsRoot.classList.add('sim-mode');
    stepsRoot.innerHTML = steps.map(function (step, index) {
      var label = step.label || step.skillId || '';
      var detail = step.detail || '';
      return '<div class="recipe-step" data-step-index="' + index + '">' +
        '<div class="sim-rail"><span class="recipe-step-number">' + String(index + 1).padStart(2, '0') + '</span></div>' +
        '<div class="sim-body"><div class="sim-top"><div><strong>' + esc(label) + '</strong>' +
        '<small class="step-detail">' + esc(detail) + '</small></div>' +
        '<span class="step-badge" data-badge>等待</span></div>' +
        '<div class="step-console" data-console><span class="line-muted">等待本阶段产出…</span></div>' +
        '</div></div>';
    }).join('');

    function finishNode(node, step) {
      node.classList.remove('is-running');
      node.classList.add('is-done');
      var badge = node.querySelector('[data-badge]');
      if (badge) badge.textContent = '完成';
      var cons = node.querySelector('[data-console]');
      if (cons) {
        var demo = String((step && step.demo) || '').trim();
        cons.innerHTML = demo ? formatDemo(demo) : '<span class="line-muted">✓ 本阶段完成</span>';
      }
    }

    function tick(nodes, i) {
      if (i > 0) finishNode(nodes[i - 1], steps[i - 1]);
      if (i >= nodes.length) {
        toolbar.dataset.state = 'done';
        if (statusLabel) statusLabel.textContent = '全部阶段已完成';
        if (statusSub) statusSub.textContent = nodes.length + ' 步已按顺序跑完';
        if (progressBar) progressBar.style.width = '100%';
        if (replayBtn) replayBtn.hidden = false;
        return;
      }
      var node = nodes[i];
      var step = steps[i] || {};
      node.classList.add('is-visible', 'is-running');
      var badge = node.querySelector('[data-badge]');
      if (badge) badge.textContent = '执行中';
      var cons = node.querySelector('[data-console]');
      var demo = String(step.demo || '').trim();
      if (cons) {
        cons.innerHTML = (demo ? formatDemo(demo) : '<span class="line-muted">正在完成本阶段…</span>') + '<span class="cursor"></span>';
      }
      if (statusSub) statusSub.textContent = '步骤 ' + (i + 1) + ' / ' + nodes.length + ' · ' + (step.label || '');
      if (progressBar) progressBar.style.width = Math.round((i / nodes.length) * 100) + '%';
      TIMER = setTimeout(function () { tick(nodes, i + 1); }, reduceMotion ? 0 : 720);
    }

    function start() {
      if (TIMER) { clearTimeout(TIMER); TIMER = null; }
      var nodes = Array.prototype.slice.call(stepsRoot.querySelectorAll('.recipe-step'));
      nodes.forEach(function (n) {
        n.classList.remove('is-visible', 'is-running', 'is-done');
        var b = n.querySelector('[data-badge]');
        if (b) b.textContent = '等待';
        var c = n.querySelector('[data-console]');
        if (c) c.innerHTML = '<span class="line-muted">等待本阶段产出…</span>';
      });
      if (progressBar) progressBar.style.width = '0%';
      if (replayBtn) replayBtn.hidden = true;
      toolbar.dataset.state = 'running';
      if (statusLabel) statusLabel.textContent = '逐步演示产出';
      if (reduceMotion) {
        nodes.forEach(function (n, idx) {
          n.classList.add('is-visible', 'is-done');
          finishNode(n, steps[idx]);
        });
        toolbar.dataset.state = 'done';
        if (statusLabel) statusLabel.textContent = '全部阶段已完成';
        if (statusSub) statusSub.textContent = nodes.length + ' 步';
        if (progressBar) progressBar.style.width = '100%';
        if (replayBtn) replayBtn.hidden = false;
      } else {
        TIMER = setTimeout(function () { tick(nodes, 0); }, 280);
      }
    }

    if (replayBtn) replayBtn.onclick = start;
    start();
  }

  function hookOpenRecipe() {
    var dialog = document.getElementById('workflow-dialog');
    if (!dialog || dialog.__simHooked) return;
    dialog.__simHooked = true;

    var observer = new MutationObserver(function () {
      if (!dialog.open) return;
      var title = (document.getElementById('workflow-dialog-title') || {}).textContent || '';
      var recipes = findRecipes();
      var recipe = null;
      for (var i = 0; i < recipes.length; i++) {
        if (recipes[i].title === title) { recipe = recipes[i]; break; }
      }
      if (!recipe) {
        var kicker = (document.getElementById('workflow-dialog-kicker') || {}).textContent || '';
        for (var j = 0; j < recipes.length; j++) {
          if (recipes[j].kicker === kicker) { recipe = recipes[j]; break; }
        }
      }
      if (recipe) setTimeout(function () { runSim(recipe); }, 30);
    });
    observer.observe(dialog, { attributes: true, attributeFilter: ['open'] });

    document.addEventListener('click', function (e) {
      var card = e.target.closest && e.target.closest('.workflow-card, .workflow-details');
      if (!card) return;
      setTimeout(function () {
        if (dialog.open) {
          var title = (document.getElementById('workflow-dialog-title') || {}).textContent || '';
          var recipes = findRecipes();
          for (var i = 0; i < recipes.length; i++) {
            if (recipes[i].title === title) { runSim(recipes[i]); break; }
          }
        }
      }, 50);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hookOpenRecipe);
  } else {
    hookOpenRecipe();
  }
})();
