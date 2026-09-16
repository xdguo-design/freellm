/* 共享库：农历/节气/干支 / 颜色转换 / ASCII字 / Code128 / ZIP / PDF / ICO / GIF 编码
   页面引入：<script src="/tools/js/lib-utils.js"></script>
   命名空间：LibU（别名 LU）*/
(function (global) {
  'use strict';
  var LU = {};

  /* ============ 农历（数据：/tools/data/lunar-table.json） ============
     编码（scripts/generate_tool_data.py）：
       data = (leapMonth << 17) | (leapMonth30天 ? 0x10000 : 0) | monthBits
       monthBits bit(m-1) = 农历第 m 个Regular月有 30 天
     基准：1900-01-31 = 农历 1900 年正月初一 */
  var STEMS = '甲乙丙丁戊己庚辛壬癸';
  var BRANCHES = '子丑寅卯辰巳午未申酉戌亥';
  var ZODIAC = '鼠牛虎兔龙蛇马羊猴鸡狗猪';
  var LUNAR_MONTHS = '正二三四五六七八九十冬腊';
  var LUNAR_DAYS = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
    '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];

  var LX = {};
  LX._table = null;
  LX._base = null;
  LX.init = function (data) {
    LX._table = data.table;
    LX._base = data.newYear.split('-').map(Number);
    LX._from = data.from;
    LX._to = data.to;
  };
  LX.load = function () {
    if (LX._table) return Promise.resolve();
    return fetch('/tools/data/lunar-table.json')
      .then(function (r) { return r.json(); })
      .then(function (d) { LX.init(d); });
  };
  LX.yearInfo = function (y) {
    var d = LX._table[y - LX._from];
    var leap = d >> 17;
    var leapDays = (d & 0x10000) ? 30 : 29;
    var months = [];
    for (var m = 1; m <= 12; m++) {
      months.push({ month: m, leap: false, days: (d >> (m - 1)) & 1 ? 30 : 29 });
      if (leap === m) months.push({ month: m, leap: true, days: leapDays });
    }
    return { leap: leap, months: months };
  };
  LX.totalDays = function (y) {
    return LX.yearInfo(y).months.reduce(function (s, m) { return s + m.days; }, 0);
  };
  LX._dateDiff = function (a, b) {
    return Math.round((Date.UTC(b[0], b[1] - 1, b[2]) - Date.UTC(a[0], a[1] - 1, a[2])) / 86400000);
  };
  LX._fromBase = function (days) {
    var d = new Date(Date.UTC(LX._base[0], LX._base[1] - 1, LX._base[2] + days));
    return [d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate()];
  };
  LX.newYearDate = function (y) {
    var days = 0;
    for (var yy = LX._from; yy < y; yy++) days += LX.totalDays(yy);
    return LX._fromBase(days);
  };
  /* solar [y,m,d] → {y, month, day, leap} 或 null（超出 1900-2098） */
  LX.solarToLunar = function (solar) {
    var days = LX._dateDiff(LX._base, solar);
    if (days < 0) return null;
    var y = LX._from;
    while (y < LX._to) {
      var yd = LX.totalDays(y);
      if (days < yd) break;
      days -= yd; y++;
    }
    if (y > LX._to) return null;
    var info = LX.yearInfo(y);
    for (var i = 0; i < info.months.length; i++) {
      var m = info.months[i];
      if (days < m.days) return { y: y, month: m.month, day: days + 1, leap: m.leap };
      days -= m.days;
    }
    return null;
  };
  /* lunar {y,month,day,leap} → solar [y,m,d] */
  LX.lunarToSolar = function (l) {
    var days = 0;
    for (var yy = LX._from; yy < l.y; yy++) days += LX.totalDays(yy);
    var info = LX.yearInfo(l.y);
    for (var i = 0; i < info.months.length; i++) {
      var m = info.months[i];
      if (m.month === l.month && m.leap === !!l.leap) {
        if (l.day > m.days) return null;
        return LX._fromBase(days + l.day - 1);
      }
      if (m.month > l.month) return null;
      days += m.days;
    }
    return null;
  };
  LX.monthName = function (m, leap) { return (leap ? '闰' : '') + LUNAR_MONTHS[m - 1] + '月'; };
  LX.dayName = function (d) { return LUNAR_DAYS[d - 1]; };
  LX.gz = function (idx) { return STEMS[idx % 10] + BRANCHES[idx % 12]; };

  /* ---- 干支 ---- */
  var GX = {};
  /* 年干支以立春为界 */
  GX.year = function (y) { return { stem: (y - 4) % 10, branch: (y - 4) % 12 }; };
  GX.day = function (date) {
    var utcDays = Math.floor(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000);
    var anchor = Math.floor(Date.UTC(1949, 9, 1) / 86400000); /* 1949-10-01 甲子日 */
    var idx = ((utcDays - anchor) % 60 + 60) % 60;
    return { stem: idx % 10, branch: idx % 12, idx: idx };
  };
  GX.hour = function (date) {
    var d = GX.day(date);
    var hBranch = Math.floor(((date.getHours() + 1) % 24) / 2);
    var hStem = (d.stem * 2 + hBranch) % 10;
    return { stem: hStem, branch: hBranch };
  };
  GX.month = function (date) {
    var y = date.getFullYear();
    var ys = GX.year(y).stem;
    var firstMonthStem = (ys % 5) * 2 + 2;
    var m = date.getMonth() + 1;
    var mBranch = (m + 1) % 12;
    var mStem = (firstMonthStem + (m - 1)) % 10;
    return { stem: mStem, branch: mBranch };
  };
  GX.wuxingOfStem = function (s) { return '木木火火土土金金水水'[s]; };
  GX.wuxingOfBranch = function (b) { return '水土木木土火火土金金土水'[b]; };
  GX.elementOf = function (wx) { return { 木: '木', 火: '火', 土: '土', 金: '金', 水: '水' }[wx] || wx; };
  LU.Ganzhi = GX;
  LU.Stems = STEMS; LU.Branches = BRANCHES; LU.Zodiac = ZODIAC;
  LU.Lunar = LX;

  /* ---- 二十四节气（21 世纪近似公式，个别年份 ±1 天） ---- */
  var JIEQI_C = [
    ['小寒', 1, 5.4055], ['大寒', 1, 20.12], ['立春', 2, 3.87], ['雨水', 2, 18.73],
    ['惊蛰', 3, 5.63], ['春分', 3, 20.646], ['清明', 4, 4.81], ['谷雨', 4, 20.1],
    ['立夏', 5, 5.52], ['小满', 5, 21.04], ['芒种', 6, 5.678], ['夏至', 6, 21.37],
    ['小暑', 7, 7.108], ['大暑', 7, 22.83], ['立秋', 8, 7.5], ['处暑', 8, 23.13],
    ['白露', 9, 7.646], ['秋分', 9, 23.042], ['寒露', 10, 8.318], ['霜降', 10, 23.438],
    ['立冬', 11, 7.438], ['小雪', 11, 22.36], ['大雪', 12, 7.18], ['冬至', 12, 21.94]];
  var JQ = {};
  JQ.yearTerms = function (year) {
    var y = year % 100;
    return JIEQI_C.map(function (t) {
      var day = Math.floor(y * 0.2422 + t[2]) - Math.floor(y / 4);
      return { name: t[0], month: t[1], day: day };
    });
  };
  JQ.current = function (date) {
    var terms = JQ.yearTerms(date.getFullYear()).concat(
      JQ.yearTerms(date.getFullYear() + 1));
    var cur = null;
    var dnum = date.getFullYear() * 10000 + (date.getMonth() + 1) * 100 + date.getDate();
    terms.forEach(function (t) {
      var tn = (t.month === 1 ? date.getFullYear() + 1 : date.getFullYear()) * 10000 + t.month * 100 + t.day;
      if (tn <= dnum) cur = t;
    });
    return cur;
  };
  LU.Jieqi = JQ;

  /* ---- 节日 ---- */
  var FEST = {};
  FEST.solarFests = { '1-1': '元旦', '2-14': '情人节', '3-8': '妇女节', '3-12': '植树节', '4-1': '愚人节', '5-1': '劳动节', '5-4': '青年节', '6-1': '儿童节', '7-1': '建党节', '8-1': '建军节', '9-10': '教师节', '10-1': '国庆节', '10-31': '万圣夜', '12-25': '圣诞节' };
  FEST.lunarFests = { '1-1': '春节', '1-15': '元宵节', '2-2': '龙抬头', '3-3': '上巳节', '5-5': '端午节', '7-7': '七夕节', '7-15': '中元节', '8-15': '中秋节', '9-9': '重阳节', '10-1': '寒衣节', '10-15': '下元节', '12-8': '腊八节', '12-23': '北方小年' };
  FEST.ofDate = function (date) {
    var names = [];
    var sk = (date.getMonth() + 1) + '-' + date.getDate();
    if (FEST.solarFests[sk]) names.push(FEST.solarFests[sk]);
    var term = JQ.yearTerms(date.getFullYear()).find(function (t) { return t.month === date.getMonth() + 1 && t.day === date.getDate(); });
    if (term) names.push(term.name);
    var lunar = LX.solarToLunar([date.getFullYear(), date.getMonth() + 1, date.getDate()]);
    if (lunar && !lunar.leap) {
      var lk = lunar.month + '-' + lunar.day;
      if (FEST.lunarFests[lk]) names.push(FEST.lunarFests[lk]);
      if (lunar.month === 12) {
        var nextDay = LX.solarToLunar([date.getFullYear(), date.getMonth() + 1, date.getDate() + 1]);
        if (nextDay && nextDay.month === 1 && nextDay.day === 1) names.push('除夕');
        else if (lunar.day === 30) names.push('除夕');
      }
    }
    return names;
  };
  LU.Fest = FEST;

  /* ============ 颜色转换 ============ */
  var CX = {};
  var NAMED = { black: '#000000', white: '#ffffff', red: '#ff0000', green: '#008000', blue: '#0000ff', yellow: '#ffff00', orange: '#ffa500', purple: '#800080', gray: '#808080', grey: '#808080', silver: '#c0c0c0', maroon: '#800000', olive: '#808000', lime: '#00ff00', aqua: '#00ffff', cyan: '#00ffff', teal: '#008080', navy: '#000080', fuchsia: '#ff00ff', magenta: '#ff00ff', pink: '#ffc0cb', brown: '#a52a2a', gold: '#ffd700' };
  CX.parse = function (str) {
    str = (str || '').trim().toLowerCase();
    if (NAMED[str]) str = NAMED[str];
    var m;
    if ((m = str.match(/^#?([0-9a-f]{3})$/))) {
      return { r: parseInt(m[1][0] + m[1][0], 16), g: parseInt(m[1][1] + m[1][1], 16), b: parseInt(m[1][2] + m[1][2], 16) };
    }
    if ((m = str.match(/^#?([0-9a-f]{6})$/))) {
      return { r: parseInt(m[1].slice(0, 2), 16), g: parseInt(m[1].slice(2, 4), 16), b: parseInt(m[1].slice(4, 6), 16) };
    }
    if ((m = str.match(/^rgba?\(([^)]+)\)$/))) {
      var p = m[1].split(/[,/\s]+/).filter(Boolean);
      return { r: +p[0], g: +p[1], b: +p[2] };
    }
    if ((m = str.match(/^hsla?\(([^)]+)\)$/))) {
      var pp = m[1].split(/[,/\s]+/).filter(Boolean);
      var h = parseFloat(pp[0]) / 360, s = parseFloat(pp[1]) / 100, l = parseFloat(pp[2]) / 100;
      return CX.hslToRgb(h, s, l);
    }
    throw new Error('无法识别的颜色：' + str);
  };
  CX.hex = function (rgb) {
    var h = function (v) { return Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0'); };
    return '#' + h(rgb.r) + h(rgb.g) + h(rgb.b);
  };
  CX.rgbToHsl = function (r, g, b) {
    r /= 255; g /= 255; b /= 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b), h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      var d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h /= 6;
    }
    return { h: h * 360, s: s, l: l };
  };
  CX.hslToRgb = function (h, s, l) {
    var f = function (n) {
      var k = (n + h * 12) % 12;
      return l - s * Math.min(l, 1 - l) * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    };
    return { r: Math.round(f(0) * 255), g: Math.round(f(8) * 255), b: Math.round(f(4) * 255) };
  };
  CX.rgbToHsv = function (r, g, b) {
    var hsl = CX.rgbToHsl(r, g, b);
    var max = Math.max(r, g, b) / 255, min = Math.min(r, g, b) / 255;
    var h = hsl.h, s = max === 0 ? 0 : (max - min) / max, v = max;
    return { h: h, s: s, v: v };
  };
  CX.luminance = function (rgb) {
    var f = function (c) { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(rgb.r) + 0.7152 * f(rgb.g) + 0.0722 * f(rgb.b);
  };
  CX.contrast = function (a, b) {
    var l1 = CX.luminance(a), l2 = CX.luminance(b);
    var hi = Math.max(l1, l2), lo = Math.min(l1, l2);
    return (hi + 0.05) / (lo + 0.05);
  };
  LU.Color = CX;

  /* ============ ASCII 艺术字（内置 5 行块状字体） ============ */
  var FIG = {
    'A': [' ### ', '#   #', '#####', '#   #', '#   #'],
    'B': ['#### ', '#   #', '#### ', '#   #', '#### '],
    'C': [' ####', '#    ', '#    ', '#    ', ' ####'],
    'D': ['#### ', '#   #', '#   #', '#   #', '#### '],
    'E': ['#####', '#    ', '#### ', '#    ', '#####'],
    'F': ['#####', '#    ', '#### ', '#    ', '#    '],
    'G': [' ####', '#    ', '#  ##', '#   #', ' ####'],
    'H': ['#   #', '#   #', '#####', '#   #', '#   #'],
    'I': ['###', ' # ', ' # ', ' # ', '###'],
    'J': ['  ###', '   # ', '   # ', '#  # ', ' ##  '],
    'K': ['#   #', '#  # ', '###  ', '#  # ', '#   #'],
    'L': ['#    ', '#    ', '#    ', '#    ', '#####'],
    'M': ['#   #', '## ##', '# # #', '#   #', '#   #'],
    'N': ['#   #', '##  #', '# # #', '#  ##', '#   #'],
    'O': [' ### ', '#   #', '#   #', '#   #', ' ### '],
    'P': ['#### ', '#   #', '#### ', '#    ', '#    '],
    'Q': [' ### ', '#   #', '# # #', '#  # ', ' ## #'],
    'R': ['#### ', '#   #', '#### ', '#  # ', '#   #'],
    'S': [' ####', '#    ', ' ### ', '    #', '#### '],
    'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  '],
    'U': ['#   #', '#   #', '#   #', '#   #', ' ### '],
    'V': ['#   #', '#   #', '#   #', ' # # ', '  #  '],
    'W': ['#   #', '#   #', '# # #', '## ##', '#   #'],
    'X': ['#   #', ' # # ', '  #  ', ' # # ', '#   #'],
    'Y': ['#   #', ' # # ', '  #  ', '  #  ', '  #  '],
    'Z': ['#####', '   # ', '  #  ', ' #   ', '#####'],
    '0': [' ### ', '#  ##', '# # #', '##  #', ' ### '],
    '1': [' #  ', '##  ', ' #  ', ' #  ', ' ###'],
    '2': ['#### ', '   # ', ' ### ', '#    ', '#####'],
    '3': ['#### ', '   # ', ' ### ', '   # ', '#### '],
    '4': ['#  # ', '#  # ', '#####', '   # ', '   # '],
    '5': ['#####', '#    ', '#### ', '   # ', '#### '],
    '6': [' ### ', '#    ', '#### ', '#   #', ' ### '],
    '7': ['#####', '   # ', '  #  ', ' #   ', ' #   '],
    '8': [' ### ', '#   #', ' ### ', '#   #', ' ### '],
    '9': [' ### ', '#   #', ' ####', '   # ', ' ### '],
    '.': ['   ', '   ', '   ', '   ', ' # '],
    ',': ['   ', '   ', '   ', ' # ', '#  '],
    '!': [' # ', ' # ', ' # ', '   ', ' # '],
    '?': [' ### ', '#   #', '  ## ', '     ', '  #  '],
    ':': ['   ', ' # ', '   ', ' # ', '   '],
    '-': ['    ', '    ', '####', '    ', '    '],
    '+': ['   ', ' # ', '###', ' # ', '   '],
    '*': [' # # ', '  #  ', '#####', '  #  ', ' # # '],
    '/': ['    #', '   # ', '  #  ', ' #   ', '#    '],
    '(': ['  # ', ' #  ', ' #  ', ' #  ', '  # '],
    ')': ['#  ', ' # ', ' # ', ' # ', '#  '],
    '@': [' ### ', '#   #', '# ###', '#    ', ' ### '],
    '#': [' # # ', '#####', ' # # ', '#####', ' # # '],
    '$': [' ### ', '# #  ', ' ### ', '  # #', ' ### '],
    '%': ['#   #', '   # ', '  #  ', ' #   ', '#   #'],
    '&': [' ##  ', '# #  ', ' ### ', '#  # ', ' ## #'],
    "'": [' # ', ' # ', '   ', '   ', '   '],
    '=': ['    ', '####', '    ', '####', '    '],
    '<': ['  #', ' # ', '#  ', ' # ', '  #'],
    '>': ['#  ', ' # ', '  #', ' # ', '#  ']
  };
  LU.figlet = function (text, ch) {
    ch = ch || '█';
    var rows = ['', '', '', '', ''];
    var unknown = [];
    String(text).toUpperCase().split('').forEach(function (c) {
      var g = FIG[c];
      if (!g) { if (c === ' ') { g = ['    ', '    ', '    ', '    ', '    ']; } else { unknown.push(c); g = FIG['?']; } }
      for (var i = 0; i < 5; i++) rows[i] += g[i].replace(/#/g, '█').replace(/ /g, ' ') + ' ';
    });
    return { art: rows.join('\n'), unknown: unknown };
  };
  LU.figletChars = Object.keys(FIG);

  /* ============ Code128 条形码 ============ */
  var C128 = ['212222', '222122', '222221', '121223', '121322', '131222', '122213', '122312', '132212', '221213', '221312', '231212', '112232', '122132', '122231', '113222', '123122', '123221', '223211', '221132', '221231', '213212', '223112', '312131', '311222', '321122', '321221', '312212', '322112', '322211', '212123', '212321', '232121', '111323', '131123', '131321', '112313', '132113', '132311', '211313', '231113', '231311', '112133', '112331', '132131', '113123', '113321', '133121', '313121', '211331', '231131', '213113', '213311', '213131', '311123', '311321', '331121', '312113', '312311', '332111', '314111', '221411', '431111', '111224', '111422', '121124', '121421', '141122', '141221', '112214', '112412', '122114', '122411', '142112', '142211', '241211', '221114', '413111', '241112', '134111', '111242', '121142', '121241', '114212', '124112', '124211', '411212', '421112', '421211', '212141', '214121', '412121', '111143', '111341', '131141', '114113', '114311', '411113', '411311', '113141', '114131', '311141', '411131', '211412', '211214', '211232', '2331112'];
  LU.code128 = function (text) {
    if (!/^[\x20-\x7e]*$/.test(text)) throw new Error('Code128 仅支持 ASCII 可见字符');
    var codes = [];
    var useC = text.length >= 2 && /^\d+$/.test(text) && text.length % 2 === 0;
    if (useC) {
      codes.push(105);
      for (var i = 0; i < text.length; i += 2) codes.push(+text.slice(i, i + 2));
    } else {
      codes.push(104);
      for (i = 0; i < text.length; i++) codes.push(text.charCodeAt(i) - 32);
    }
    var sum = codes[0];
    for (i = 1; i < codes.length; i++) sum += codes[i] * i;
    codes.push(sum % 103);
    codes.push(106);
    var modules = 0;
    var bars = codes.map(function (c) {
      var p = C128[c], arr = [];
      for (var k = 0; k < p.length; k++) arr.push(+p[k]);
      modules += arr.reduce(function (s, w) { return s + w; }, 0);
      return arr;
    });
    return { bars: bars, modules: modules };
  };
  LU.code128Svg = function (text, height, scale) {
    var r = LU.code128(text);
    scale = scale || 2; height = height || 80;
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + (r.modules * scale) + '" height="' + (height + 30) + '" viewBox="0 0 ' + r.modules * scale + ' ' + (height + 30) + '">';
    var x = 0, dark = true;
    svg += '<rect width="100%" height="100%" fill="#fff"/>';
    r.bars.forEach(function (pattern) {
      pattern.forEach(function (w) {
        if (dark) svg += '<rect x="' + x * scale + '" y="0" width="' + w * scale + '" height="' + height + '" fill="#000"/>';
        x += w; dark = !dark;
      });
    });
    svg += '<text x="' + (r.modules * scale / 2) + '" y="' + (height + 22) + '" text-anchor="middle" font-family="monospace" font-size="14">' + text.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</text></svg>';
    return svg;
  };

  /* ============ ZIP 读取（stored / deflate） ============ */
  var ZX = {};
  ZX.read = function (bytes) {
    var dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    var eocd = -1;
    for (var i = bytes.length - 22; i >= 0 && i > bytes.length - 65558; i--) {
      if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    }
    if (eocd < 0) throw new Error('未找到 ZIP 结尾记录（EOCD）');
    var count = dv.getUint16(eocd + 10, true);
    var cdOffset = dv.getUint32(eocd + 16, true);
    var td = new TextDecoder();
    var entries = [];
    var p = cdOffset;
    for (var n = 0; n < count; n++) {
      if (dv.getUint32(p, true) !== 0x02014b50) break;
      var method = dv.getUint16(p + 10, true);
      var csize = dv.getUint32(p + 20, true);
      var usize = dv.getUint32(p + 24, true);
      var nameLen = dv.getUint16(p + 28, true);
      var extraLen = dv.getUint16(p + 30, true);
      var cmtLen = dv.getUint16(p + 32, true);
      var lho = dv.getUint32(p + 42, true);
      var name = td.decode(bytes.subarray(p + 46, p + 46 + nameLen));
      var lnNameLen = dv.getUint16(lho + 26, true);
      var lnExtraLen = dv.getUint16(lho + 28, true);
      var dataStart = lho + 30 + lnNameLen + lnExtraLen;
      entries.push({
        name: name, size: usize, compressedSize: csize, method: method,
        isDir: name.endsWith('/'),
        getData: function () {
          if (this.method === 0) return Promise.resolve(bytes.slice(dataStart, dataStart + this.compressedSize));
          if (this.method === 8) {
            return new Response(bytes.slice(dataStart, dataStart + this.compressedSize).slice().buffer)
              .body.pipeThrough(new DecompressionStream('deflate-raw'))
              .getReader().read().then(function (r) { return new Uint8Array(r.value); });
          }
          return Promise.reject(new Error('不支持的压缩算法：' + this.method));
        }
      });
      p += 46 + nameLen + extraLen + cmtLen;
    }
    return entries;
  };
  LU.Zip = ZX;

  /* ============ 图片 → PDF（DCTDecode 嵌入 JPEG） ============ */
  var PX = {};
  PX.fromJpegs = function (pages) {
    /* pages: [{w, h, jpeg: Uint8Array}] */
    var out = [], offsets = [], pos = 0;
    function push(s) {
      if (typeof s === 'string') { for (var i = 0; i < s.length; i++) out.push(s.charCodeAt(i)); pos += s.length; }
      else { for (var j = 0; j < s.length; j++) out.push(s[j]); pos += s.length; }
    }
    function obj(n, body) { offsets[n] = pos; push(n + ' 0 obj\n' + body + '\nendobj\n'); }
    push('%PDF-1.4\n');
    var kids = pages.map(function (_, i) { return (3 + i * 2) + ' 0 R'; }).join(' ');
    obj(1, '<< /Type /Catalog /Pages 2 0 R >>');
    obj(2, '<< /Type /Pages /Kids [' + kids + '] /Count ' + pages.length + ' >>');
    pages.forEach(function (pg, i) {
      var pageNum = 3 + i * 2, imgNum = 4 + i * 2;
      obj(pageNum, '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + pg.w + ' ' + pg.h + '] ' +
        '/Resources << /XObject << /Im' + i + ' ' + imgNum + ' 0 R >> >> ' +
        '/Contents ' + (pages.length * 2 + 5 + i) + ' 0 R >>');
    });
    var firstStream = pages.length * 2 + 5;
    pages.forEach(function (pg, i) {
      var imgNum = 4 + i * 2;
      offsets[imgNum] = pos;
      push(imgNum + ' 0 obj\n<< /Type /XObject /Subtype /Image /Width ' + pg.w + ' /Height ' + pg.h +
        ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ' + pg.jpeg.length +
        ' >>\nstream\n');
      push(pg.jpeg);
      push('\nendstream\nendobj\n');
    });
    pages.forEach(function (pg, i) {
      var cNum = firstStream + i;
      var content = 'q ' + pg.w + ' 0 0 ' + pg.h + ' 0 0 cm /Im' + i + ' Do Q';
      obj(cNum, '<< /Length ' + content.length + ' >>\nstream\n' + content + '\nendstream');
    });
    var xrefPos = pos;
    var maxObj = firstStream + pages.length - 1;
    push('xref\n0 ' + (maxObj + 1) + '\n0000000000 65535 f \n');
    for (var k = 1; k <= maxObj; k++) {
      push(String(offsets[k] || 0).padStart(10, '0') + ' 00000 n \n');
    }
    push('trailer\n<< /Size ' + (maxObj + 1) + ' /Root 1 0 R >>\nstartxref\n' + xrefPos + '\n%%EOF');
    return new Blob([new Uint8Array(out)], { type: 'application/pdf' });
  };
  LU.Pdf = PX;

  /* ============ Canvas → ICO（PNG 编码图标） ============ */
  var IX = {};
  IX.fromCanvases = function (items) {
    /* items: [{size, blob: Promise<Blob png>}] */
    return Promise.all(items.map(function (it) { return it.blob; })).then(function (blobs) {
      return Promise.all(blobs.map(function (b) { return b.arrayBuffer(); }));
    }).then(function (bufs) {
      var total = 6 + items.length * 16;
      bufs.forEach(function (b) { total += b.byteLength; });
      var out = new Uint8Array(total);
      var dv = new DataView(out.buffer);
      dv.setUint16(0, 0, true); dv.setUint16(2, 1, true); dv.setUint16(4, items.length, true);
      var off = 6;
      bufs.forEach(function (b, i) {
        var s = items[i].size;
        out[off] = s >= 256 ? 0 : s; out[off + 1] = 0; out[off + 2] = 0; out[off + 3] = 0;
        dv.setUint16(off + 4, 1, true); dv.setUint16(off + 6, 32, true);
        dv.setUint32(off + 8, b.byteLength, true);
        dv.setUint32(off + 12, 6 + items.length * 16 + bufs.slice(0, i).reduce(function (sum, x) { return sum + x.byteLength; }, 0), true);
        off += 16;
      });
      bufs.forEach(function (b, i) { out.set(new Uint8Array(b), off); off += b.byteLength; });
      return new Blob([out], { type: 'image/x-icon' });
    });
  };
  LU.Ico = IX;

  /* ============ GIF 编码器（中位切分调色 + LZW） ============ */
  function medianCut(pixels, maxColors) {
    /* pixels: 采样后的 [[r,g,b],...] */
    var boxes = [pixels];
    while (boxes.length < maxColors) {
      var bi = -1, range = -1;
      boxes.forEach(function (box, i) {
        if (box.length < 2) return;
        for (var c = 0; c < 3; c++) {
          var min = 255, max = 0;
          box.forEach(function (p) { if (p[c] < min) min = p[c]; if (p[c] > max) max = p[c]; });
          if (max - min > range) { range = max - min; bi = i; }
        }
      });
      if (bi < 0 || range <= 0) break;
      var box = boxes[bi];
      var axis = 0, r2 = -1;
      for (var c = 0; c < 3; c++) {
        var min = 255, max = 0;
        box.forEach(function (p) { if (p[c] < min) min = p[c]; if (p[c] > max) max = p[c]; });
        if (max - min > r2) { r2 = max - min; axis = c; }
      }
      box.sort(function (a, b) { return a[axis] - b[axis]; });
      var mid = box.length >> 1;
      boxes.splice(bi, 1, box.slice(0, mid), box.slice(mid));
    }
    var palette = [];
    boxes.forEach(function (box) {
      if (!box.length) return;
      var r = 0, g = 0, b = 0;
      box.forEach(function (p) { r += p[0]; g += p[1]; b += p[2]; });
      palette.push([Math.round(r / box.length), Math.round(g / box.length), Math.round(b / box.length)]);
    });
    while (palette.length < 2) palette.push([0, 0, 0]);
    return palette;
  }
  function nearestIndex(palette, r, g, b, cache) {
    var key = (r >> 3) + ',' + (g >> 3) + ',' + (b >> 3);
    if (cache[key] != null) return cache[key];
    var best = 0, bd = Infinity;
    for (var i = 0; i < palette.length; i++) {
      var d = (palette[i][0] - r) * (palette[i][0] - r) + (palette[i][1] - g) * (palette[i][1] - g) + (palette[i][2] - b) * (palette[i][2] - b);
      if (d < bd) { bd = d; best = i; }
    }
    cache[key] = best;
    return best;
  }
  function lzwEncode(indices, minCodeSize) {
    var clear = 1 << minCodeSize, end = clear + 1;
    var dict = {}, next = end + 1, codeSize = minCodeSize + 1;
    var out = [], cur = 0, curBits = 0;
    function emit(code) {
      cur |= code << curBits; curBits += codeSize;
      while (curBits >= 8) { out.push(cur & 255); cur >>= 8; curBits -= 8; }
    }
    emit(clear);
    var prefixKey = indices[0];
    for (var i = 1; i < indices.length; i++) {
      var k = indices[i];
      var key = prefixKey + ',' + k;
      if (dict[key] != null) { prefixKey = dict[key]; continue; }
      emit(typeof prefixKey === 'number' ? prefixKey : prefixKey);
      if (typeof prefixKey !== 'number') throw new Error('lzw internal');
      dict[key] = next++;
      if (next > (1 << codeSize) && codeSize < 12) codeSize++;
      if (next >= 4096) { emit(clear); dict = {}; next = end + 2; codeSize = minCodeSize + 1; }
      prefixKey = k;
    }
    emit(typeof prefixKey === 'number' ? prefixKey : 0);
    emit(end);
    if (curBits > 0) out.push(cur & 255);
    return out;
  }
  var GW = {};
  /* frames: [{data: Uint8ClampedArray RGBA, width, height, delay(ms)}] */
  GW.encode = function (frames, opts) {
    opts = opts || {};
    var maxColors = Math.min(256, opts.colors || 256);
    var sample = [];
    frames.forEach(function (f) {
      var step = Math.max(1, Math.floor((f.width * f.height) / 5000));
      for (var i = 0; i < f.data.length; i += 4 * step) {
        if (f.data[i + 3] > 128) sample.push([f.data[i], f.data[i + 1], f.data[i + 2]]);
      }
    });
    var palette = medianCut(sample, maxColors);
    while (palette.length < 2) palette.push([0, 0, 0]);
    var paletteSize = 2;
    while (paletteSize < palette.length) paletteSize *= 2;
    var minCodeSize = 8;
    var bytes = [];
    function str(s) { for (var i = 0; i < s.length; i++) bytes.push(s.charCodeAt(i)); }
    function byte(b) { bytes.push(b & 255); }
    function short(v) { byte(v); byte(v >> 8); }
    str('GIF89a');
    var w = frames[0].width, h = frames[0].height;
    short(w); short(h);
    byte(0xF0 | (Math.log2(paletteSize) - 1)); byte(0); byte(0);
    palette.forEach(function (c) { byte(c[0]); byte(c[1]); byte(c[2]); });
    for (var pi = palette.length; pi < paletteSize; pi++) { byte(0); byte(0); byte(0); }
    if (frames.length > 1) {
      str('\x21\xFF\x0BNETSCAPE2.0\x03\x01');
      short(opts.loop === false ? 0 : 0); byte(0);
    }
    frames.forEach(function (f, fi) {
      str('\x21\xF9\x04');
      byte(0x04);
      short(Math.max(2, Math.round((f.delay || 100) / 10)));
      byte(0); byte(0);
      str('\x2C');
      short(0); short(0); short(w); short(h);
      byte(0);
      var indices = new Uint8Array(w * h);
      var cache = {};
      for (var i = 0, p = 0; i < f.data.length; i += 4, p++) {
        indices[p] = nearestIndex(palette, f.data[i], f.data[i + 1], f.data[i + 2], cache);
      }
      byte(minCodeSize);
      var lzw = lzwEncode(indices, minCodeSize);
      for (i = 0; i < lzw.length; i += 255) {
        var chunk = lzw.slice(i, i + 255);
        byte(chunk.length);
        for (var j = 0; j < chunk.length; j++) byte(chunk[j]);
      }
      byte(0);
    });
    str('\x3B');
    return new Blob([new Uint8Array(bytes)], { type: 'image/gif' });
  };
  LU.Gif = GW;

  global.LibU = LU;
})(window);
