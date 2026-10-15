// Regression coverage for the static site's persistent sidebar navigation.
// Run with: node --test js/site-navigation.test.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, 'site-navigation.js'), 'utf8');

function createPageHarness({ failFetch = false } = {}) {
  const origin = 'https://freellm.top';
  let address = new URL('/', origin);
  let currentMain = { nodeType: 1, id: '', matches: () => false };
  let documentTitle = 'Home';
  let lastRequested = '';
  const fallbacks = [], effects = [], eventHandlers = {};
  const links = ['home', 'models', 'skills', 'tools', 'workflow', 'logs', 'about']
    .map(siteNav => ({
      dataset: { siteNav },
      setAttribute(name, value) { this[name] = value; },
      removeAttribute(name) { delete this[name]; }
    }));
  const rail = {
    dataset: { flSharedNavigation: 'true' },
    setAttribute() {},
    querySelector() { return null; },
    querySelectorAll() { return links; }
  };
  const ribbon = {};
  const sharedStyle = { dataset: {}, hasAttribute: () => true, setAttribute() {} };
  const head = {
    querySelector(selector) { return selector.includes('fl-shared-navigation-styles') ? sharedStyle : null; },
    querySelectorAll() { return []; },
    appendChild() {}
  };
  const body = {
    dataset: { flSection: 'home' }, className: 'fl-ui-v2', attributes: [],
    classList: { contains: () => false },
    querySelector(selector) {
      if (selector.includes(':scope > .fl-site-rail')) return rail;
      if (selector.includes(':scope > .fl-site-ribbon')) return ribbon;
      if (selector.includes('main,')) return currentMain;
      return null;
    },
    replaceChildren(...nodes) { this.children = nodes; },
    appendChild() {},
    setAttribute(name, value) { if (name === 'data-fl-section') this.dataset.flSection = value; },
    removeAttribute() {}
  };
  const document = {
    body, head, documentElement: { lang: 'zh-CN', removeAttribute() {} },
    get title() { return documentTitle; }, set title(value) { documentTitle = value; },
    addEventListener() {},
    querySelector() { return null; },
    querySelectorAll(selector) { return selector.includes('data-site-nav') ? links : []; },
    getElementById() { return null; },
    importNode() {
      currentMain = { nodeType: 1, id: '', matches: () => false };
      return currentMain;
    },
    createElement(tagName) {
      return { tagName: tagName.toUpperCase(), dataset: {}, setAttribute() {}, remove() {}, addEventListener() {} };
    }
  };
  const location = {
    get href() { return address.href; },
    get pathname() { return address.pathname; },
    get origin() { return address.origin; },
    assign(url) { fallbacks.push(url); }
  };
  const history = {
    state: null,
    replaceState(state, unused, url) { this.state = state; if (url) address = new URL(url, origin); },
    pushState(state, unused, url) { this.state = state; address = new URL(url, origin); }
  };
  const window = {
    location, scrollY: 0, localStorage: { getItem: () => '' },
    addEventListener(type, handler) { (eventHandlers[type] ||= []).push(handler); },
    dispatchEvent(event) { effects.push(event.type); },
    matchMedia: () => ({ matches: false }),
    scrollTo() {}
  };
  class DOMParser {
    parseFromString() {
      const section = ({ '/': 'home', '/models/': 'models', '/skills/': 'skills',
        '/tools/': 'tools', '/workflow/': 'workflow', '/logs/': 'logs',
        '/about/': 'about' })[new URL(lastRequested).pathname] || 'home';
      return {
        title: 'FreeLLM ' + section, head, documentElement: { lang: 'zh-CN' },
        querySelectorAll: () => [],
        body: {
          dataset: { flSection: section }, className: 'fl-ui-v2',
          attributes: [{ name: 'data-fl-section', value: section }],
          querySelector: () => ({}),
          childNodes: [{ nodeType: 1, matches: () => false }]
        }
      };
    }
  }
  const fetch = async url => {
    lastRequested = url;
    return { ok: !failFetch, status: failFetch ? 503 : 200,
      url, text: async () => '<html><body>page</body></html>' };
  };
  const context = {
    window, document, location, history, fetch, URL, DOMParser,
    AbortController, Event, Node: { ELEMENT_NODE: 1 },
    CustomEvent: class { constructor(type) { this.type = type; } },
    console: { warn() {} }
  };
  vm.runInNewContext(source, context, { filename: 'site-navigation.js' });
  return { window, body, rail, links, history, location, effects, fallbacks, eventHandlers };
}

test('seven menu routes preserve the same sidebar DOM and update title/history', async () => {
  const app = createPageHarness();
  for (const [route, section] of [['/models/', 'models'], ['/tools/', 'tools'], ['/about/', 'about']]) {
    assert.equal(await app.window.FreeLLMNavigation.navigate(route, { history: true }), true);
    assert.equal(app.location.pathname, route);
    assert.equal(app.body.dataset.flSection, section);
    assert.ok(app.body.children.includes(app.rail), 'same sidebar element must stay mounted');
    assert.deepEqual(app.links.filter(link => link['aria-current']).map(link => link.dataset.siteNav), [section]);
    assert.equal(app.history.state.freellmNavigation, true);
  }
  assert.deepEqual(app.effects.filter(event => event === 'freellm:page-mount').length, 3);
  assert.equal(app.fallbacks.length, 0, 'normal navigation must not trigger a full page load');
});

test('non-menu and modified clicks keep native link behavior', () => {
  const app = createPageHarness();
  let prevented = 0;
  const link = { dataset: { siteNav: 'models' }, href: 'https://freellm.top/models/',
    target: '', hasAttribute: () => false };
  const click = { button: 0, defaultPrevented: false,
    target: { closest: () => link }, preventDefault() { prevented++; } };
  app.eventHandlers.click[0]({ ...click, ctrlKey: true });
  app.eventHandlers.click[0]({ ...click, target: { closest: () => null } });
  app.eventHandlers.click[0]({ ...click, target: { closest: () => ({ ...link, href: 'https://other.example/models/' }) } });
  assert.equal(prevented, 0);
});

test('failed content requests fall back to normal navigation', async () => {
  const app = createPageHarness({ failFetch: true });
  assert.equal(await app.window.FreeLLMNavigation.navigate('/models/', { history: true }), false);
  assert.equal(app.fallbacks[0], 'https://freellm.top/models/');
});
