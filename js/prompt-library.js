(function () {
  'use strict';

  var dataElement = document.getElementById('prompt-template-data');
  var grid = document.getElementById('prompt-grid');
  var search = document.getElementById('prompt-search');
  if (!dataElement || !grid || !search || grid.dataset.promptLibraryReady === 'true') return;
  grid.dataset.promptLibraryReady = 'true';

  var templates;
  try {
    templates = JSON.parse(dataElement.textContent || '[]');
  } catch (error) {
    var errorStatus = document.getElementById('prompt-count');
    if (errorStatus) errorStatus.textContent = '模板数据暂时无法加载，请手动选择下方模板正文。';
    return;
  }

  var byId = new Map(templates.map(function (template) { return [template.id, template]; }));
  var cards = Array.from(grid.querySelectorAll('[data-prompt-card]'));
  var categoryButtons = Array.from(document.querySelectorAll('[data-prompt-category]'));
  var clearButton = document.getElementById('prompt-search-clear');
  var empty = document.getElementById('prompt-empty');
  var count = document.getElementById('prompt-count');
  var activeCategory = 'all';

  function isEnglish() {
    return /^en(?:-|$)/i.test(document.documentElement.lang || '');
  }

  function updateSearchPlaceholder() {
    search.placeholder = isEnglish()
      ? 'Search titles, use cases, or prompt text'
      : '搜索标题、用途或模板内容';
  }

  function updateCount(value) {
    if (count) count.textContent = isEnglish() ? value + ' prompts' : '显示 ' + value + ' 个模板';
  }

  function filterCards() {
    var query = String(search.value || '').trim().toLocaleLowerCase();
    var visible = 0;
    cards.forEach(function (card) {
      var categoryMatches = activeCategory === 'all' || card.dataset.category === activeCategory;
      var queryMatches = !query || card.textContent.toLocaleLowerCase().indexOf(query) !== -1;
      var show = categoryMatches && queryMatches;
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (empty) empty.hidden = visible !== 0;
    if (clearButton) clearButton.hidden = !search.value && activeCategory === 'all';
    updateCount(visible);
  }

  function replaceVariables(template, card) {
    var fields = new Map();
    card.querySelectorAll('[data-prompt-variable]').forEach(function (field) {
      fields.set(field.dataset.promptVariable, field.value);
    });
    return template.prompt.replace(/\{\{([a-z][a-z0-9_]*)\}\}/g, function (marker, name) {
      return fields.has(name) ? fields.get(name) : marker;
    });
  }

  function showCopyStatus(card, message) {
    var status = card.querySelector('.prompt-copy-status');
    if (!status) return;
    status.textContent = message;
    window.clearTimeout(status._promptTimer);
    status._promptTimer = window.setTimeout(function () { status.textContent = ''; }, 1800);
  }

  function selectText(node) {
    if (!node) return;
    var range = document.createRange();
    range.selectNodeContents(node);
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }

  function copyPrompt(card, text, fallbackNode) {
    var copied = function () {
      showCopyStatus(card, isEnglish() ? 'Copied ✓' : '已复制 ✓');
    };
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      navigator.clipboard.writeText(text).then(copied).catch(function () {
        selectText(fallbackNode);
        showCopyStatus(card, isEnglish() ? 'Select the text and copy manually' : '已选中文本，请手动复制');
      });
      return;
    }
    selectText(fallbackNode);
    showCopyStatus(card, isEnglish() ? 'Select the text and copy manually' : '已选中文本，请手动复制');
  }

  cards.forEach(function (card) {
    var template = byId.get(card.dataset.promptId);
    if (!template) return;
    var original = card.querySelector('[data-prompt-original]');
    var preview = card.querySelector('[data-prompt-preview]');
    var variablePanel = card.querySelector('.prompt-variable-panel');
    var previewPanel = card.querySelector('.prompt-preview-panel');
    var actions = card.querySelector('.prompt-actions');
    if (!original || !preview || !variablePanel || !previewPanel || !actions) return;

    card.querySelectorAll('[data-prompt-variable]').forEach(function (field) {
      field.placeholder = isEnglish() ? field.dataset.placeholderEn : field.dataset.placeholderZh;
    });
    preview.textContent = template.prompt;
    variablePanel.hidden = !template.variables.length;
    previewPanel.hidden = !template.variables.length;
    actions.hidden = false;

    card.querySelectorAll('[data-prompt-variable]').forEach(function (field) {
      field.addEventListener('input', function () {
        preview.textContent = replaceVariables(template, card);
      });
    });
    var copyOriginal = card.querySelector('[data-copy-original]');
    var copyPreview = card.querySelector('[data-copy-preview]');
    if (copyOriginal) copyOriginal.addEventListener('click', function () { copyPrompt(card, template.prompt, original); });
    if (copyPreview) copyPreview.addEventListener('click', function () { copyPrompt(card, preview.textContent, preview); });
  });

  categoryButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      activeCategory = button.dataset.promptCategory || 'all';
      categoryButtons.forEach(function (item) {
        var active = item === button;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      filterCards();
    });
  });
  search.addEventListener('input', filterCards);
  if (clearButton) {
    clearButton.addEventListener('click', function () {
      search.value = '';
      activeCategory = 'all';
      categoryButtons.forEach(function (item) {
        var active = item.dataset.promptCategory === 'all';
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      filterCards();
      search.focus();
    });
  }

  updateSearchPlaceholder();
  filterCards();
})();
