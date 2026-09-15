/* ============================================================
   FreeLLM Data — 站点级数据层
   ------------------------------------------------------------
   汇率 / 法定节假日 / 农历黄历数据
   数据文件由 GitHub Actions 定时刷新后提交到本仓库：
     /tools/data/exchange.json          汇率（每日）
     /tools/data/holidays/<year>.json   法定节假日（每年）
     /tools/data/lunar.json             农历对照（每年追加）
   前端读取同源静态文件，带 localStorage 缓存与内置兜底。
   ============================================================ */
(function (global) {
  'use strict';

  var D = {};
  var DATA_BASE = '/tools/data/';

  function cacheGet(key, ttl) {
    try {
      var raw = localStorage.getItem(key);
      if (!raw) return null;
      var obj = JSON.parse(raw);
      if (ttl && Date.now() - obj._t > ttl) return null;
      return obj.data;
    } catch (e) { return null; }
  }
  function cacheSet(key, data) {
    try { localStorage.setItem(key, JSON.stringify({ _t: Date.now(), data: data })); } catch (e) {}
  }

  /* ================= 汇率 ================= */
  D.exchange = {
    KEY: 'freellm-exchange',
    TTL: 6 * 3600 * 1000, // 6 小时

    fetch: function () {
      var cached = cacheGet(D.exchange.KEY, D.exchange.TTL);
      if (cached) return Promise.resolve(cached);

      // 1) 优先取本仓库静态文件（Actions 每日更新）
      return fetch(DATA_BASE + 'exchange.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) { cacheSet(D.exchange.KEY, data); return data; })
        .catch(function () {
          // 2) 兜底：免费公开 API 直连（无需 key）
          return fetch('https://open.er-api.com/v6/latest/USD')
            .then(function (r) { return r.json(); })
            .then(function (j) {
              var data = { base: 'USD', rates: j.rates || {}, updated: j.time_last_update_utc || '', source: 'open.er-api.com' };
              cacheSet(D.exchange.KEY, data);
              return data;
            });
        });
    },

    convert: function (data, from, to, amount) {
      if (!data || !data.rates) return null;
      var r = data.rates;
      if (!r[from] || !r[to]) return null;
      return amount / r[from] * r[to];
    }
  };

  /* ================= 法定节假日 ================= */
  D.holidays = {
    fetch: function (year) {
      var y = year || new Date().getFullYear();
      var key = 'freellm-holidays-' + y;
      var cached = cacheGet(key, 30 * 24 * 3600 * 1000);
      if (cached) return Promise.resolve(cached);
      return fetch(DATA_BASE + 'holidays/' + y + '.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) { cacheSet(key, data); return data; })
        .catch(function () { return {}; });
    },

    // 判断某日是否节假日：返回 { name, type: 'holiday'|'workday' } 或 null
    // 数据格式：{ "2026-01-01": {"name":"元旦","type":"holiday"}, "2026-01-24":{"name":"补班","type":"workday"} }
    get: function (data, dateStr) {
      return (data && data[dateStr]) || null;
    }
  };

  /* ================= 农历 / 黄历 ================= */
  D.lunar = {
    // 完整农历对照表较大，按需加载，加载一次缓存
    _p: null,
    fetch: function () {
      if (D.lunar._p) return D.lunar._p;
      D.lunar._p = fetch(DATA_BASE + 'lunar.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .catch(function () { return {}; });
      return D.lunar._p;
    },
    get: function (data, dateStr) {
      return (data && data.dates && data.dates[dateStr]) || null;
    }
  };

  global.FreeLLM = global.FreeLLM || {};
  global.FreeLLM.Data = D;
})(window);