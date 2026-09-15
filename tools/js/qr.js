/* ============================================================
   QR Code 编码器 — 纯 JS 实现（字节模式，版本 1-40，四级纠错）
   GF(256) 对数表与 RS 生成多项式在运行时按 ISO/IEC 18004 推导；
   分块结构 / 矫正图形坐标为规格常量，载自 /tools/data/qr-spec.json。
   ============================================================ */
(function (global) {
  'use strict';

  /* ---------- GF(256)，本原多项式 0x11D ---------- */
  var EXP = new Uint8Array(512), LOG = new Uint8Array(256);
  (function () {
    var x = 1;
    for (var i = 0; i < 255; i++) {
      EXP[i] = x; LOG[x] = i;
      x <<= 1;
      if (x & 0x100) x ^= 0x11D;
    }
    for (var j = 255; j < 512; j++) EXP[j] = EXP[j - 255];
  })();
  function gmul(a, b) {
    if (a === 0 || b === 0) return 0;
    return EXP[LOG[a] + LOG[b]];
  }

  /* ---------- RS 生成多项式（运行时推导） ---------- */
  var genCache = {};
  function rsGen(degree) {
    if (genCache[degree]) return genCache[degree];
    var poly = [1];
    for (var i = 0; i < degree; i++) {
      var next = new Array(poly.length + 1).fill(0);
      for (var k = 0; k < poly.length; k++) {
        next[k] ^= gmul(poly[k], EXP[i]);
        next[k + 1] ^= poly[k];
      }
      poly = next;
    }
    genCache[degree] = poly.reverse(); // 高次在前
    return poly;
  }

  function rsEncode(data, ecLen) {
    var gen = rsGen(ecLen);
    var rem = data.concat(new Array(ecLen).fill(0));
    for (var i = 0; i < data.length; i++) {
      var factor = rem[i];
      if (factor === 0) continue;
      for (var j = 1; j < gen.length; j++) {
        rem[i + j] ^= gmul(gen[j], factor);
      }
    }
    return rem.slice(data.length);
  }

  /* ---------- 规格常量 ---------- */
  var SPEC = null;
  function loadSpec(done) {
    if (SPEC) return done();
    fetch('/tools/data/qr-spec.json')
      .then(function (r) { return r.json(); })
      .then(function (j) { SPEC = j; done(); });
  }

  /* ---------- 比特流 ---------- */
  function BitBuf() { this.bits = []; }
  BitBuf.prototype.push = function (val, len) {
    for (var i = len - 1; i >= 0; i--) this.bits.push((val >> i) & 1);
  };
  BitBuf.prototype.toBytes = function () {
    var bytes = [];
    for (var i = 0; i < this.bits.length; i += 8) {
      var b = 0;
      for (var j = 0; j < 8; j++) b = (b << 1) | (this.bits[i + j] || 0);
      bytes.push(b);
    }
    return bytes;
  };

  var EC_LEVELS = { L: 0, M: 1, Q: 2, H: 3 };
  var EC_FORMAT_BITS = { L: 1, M: 0, Q: 3, H: 2 }; // format info 中的纠错级别指示

  function capacity(ecIdx, version, spec) {
    var groups = spec.blocks[version - 1][ecIdx];
    var dataCW = 0;
    groups.forEach(function (g) { dataCW += g[0] * g[2]; });
    return dataCW;
  }

  function chooseVersion(len, ecName, spec) {
    var ecIdx = EC_LEVELS[ecName];
    for (var v = 1; v <= 40; v++) {
      var cap = capacity(ecIdx, v, spec);
      var ccLen = v < 10 ? 8 : 16;
      if (2 + ccLen + len <= cap) return v;
    }
    throw new Error('内容过长，无法编码为二维码');
  }

  /* ---------- 构建码字 ---------- */
  function buildCodewords(text, ecName, version, spec) {
    var ecIdx = EC_LEVELS[ecName];
    var buf = new BitBuf();
    buf.push(4, 4); // 字节模式
    var bytes = Array.from(new TextEncoder().encode(text));
    buf.push(bytes.length, version < 10 ? 8 : 16);
    bytes.forEach(function (b) { buf.push(b, 8); });

    var totalData = capacity(ecIdx, version, spec) * 8;
    // 终止符
    for (var i = 0; i < 4 && buf.bits.length < totalData; i++) buf.bits.push(0);
    // 对齐字节
    while (buf.bits.length % 8) buf.bits.push(0);
    var dataBytes = buf.toBytes();
    // 填充 0xEC 0x11
    var pad = [0xEC, 0x11], pi = 0;
    while (dataBytes.length < totalData / 8) dataBytes.push(pad[pi++ % 2]);

    // 分块 + 纠错 + 交织
    var groups = spec.blocks[version - 1][ecIdx];
    var blocks = [], ecBlocks = [], offset = 0;
    groups.forEach(function (g) {
      for (var b = 0; b < g[0]; b++) {
        var block = dataBytes.slice(offset, offset + g[2]);
        offset += g[2];
        blocks.push(block);
        ecBlocks.push(rsEncode(block, g[1] - g[2]));
      }
    });
    var maxData = Math.max.apply(null, blocks.map(function (b) { return b.length; }));
    var maxEC = Math.max.apply(null, ecBlocks.map(function (b) { return b.length; }));
    var out = [];
    for (var c = 0; c < maxData; c++)
      blocks.forEach(function (blk) { if (c < blk.length) out.push(blk[c]); });
    for (var e = 0; e < maxEC; e++)
      ecBlocks.forEach(function (blk) { if (e < blk.length) out.push(blk[e]); });
    return out;
  }

  /* ---------- BCH(format) / BCH(version) ---------- */
  function bchFormat(data5) {
    var v = data5 << 10, g = 0x537;
    for (var i = 14; i >= 10; i--)
      if ((v >> i) & 1) v ^= g << (i - 10);
    return ((data5 << 10) | v) ^ 0x5412;
  }
  function bchVersion(data6) {
    var v = data6 << 12, g = 0x1F25;
    for (var i = 17; i >= 12; i--)
      if ((v >> i) & 1) v ^= g << (i - 12);
    return (data6 << 12) | v;
  }

  /* ---------- 矩阵构建（m: null=数据待填；res: true=功能图形保留区） ---------- */
  function makeMatrix(version, spec) {
    var size = 17 + version * 4;
    var m = [], res = [];
    for (var r = 0; r < size; r++) { m.push(new Array(size).fill(null)); res.push(new Array(size).fill(false)); }
    function set(rr, cc, val) { m[rr][cc] = val; res[rr][cc] = true; }
    function finder(rr, cc) {
      for (var dr = -1; dr <= 7; dr++) for (var dc = -1; dc <= 7; dc++) {
        var r2 = rr + dr, c2 = cc + dc;
        if (r2 < 0 || c2 < 0 || r2 >= size || c2 >= size) continue;
        var dark = (dr >= 0 && dr <= 6 && (dc === 0 || dc === 6)) ||
                   (dc >= 0 && dc <= 6 && (dr === 0 || dr === 6)) ||
                   (dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4);
        set(r2, c2, dark ? 1 : 0);
      }
    }
    finder(0, 0); finder(0, size - 7); finder(size - 7, 0);
    // 时序图形
    for (var t = 8; t < size - 8; t++) { set(6, t, t % 2 ? 0 : 1); set(t, 6, t % 2 ? 0 : 1); }
    // format 信息区预留（数据摆放必须跳过；实际值在 writeFormat 写入）
    for (var f = 0; f < 15; f++) {
      if (f < 6) { set(f, 8, 0); }                      // (0..5, 8)
      else if (f < 8) { set(f + 1, 8, 0); }             // (7,8),(8,8)
      else { set(size - 15 + f, 8, 0); }                // (size-7..size-1, 8)
      if (f < 8) { set(8, size - 1 - f, 0); }           // (8, size-1..size-8)
      else if (f < 9) { set(8, 7, 0); }                 // (8, 7)
      else { set(8, 15 - f - 1, 0); }                   // (8, 5..0)
    }
    // 矫正图形
    var align = spec.align[version - 1];
    for (var ai = 0; ai < align.length; ai++) for (var aj = 0; aj < align.length; aj++) {
      var ar = align[ai], ac = align[aj];
      if (m[ar][ac] !== null) continue; // 与定位图形重叠处跳过
      for (var dr = -2; dr <= 2; dr++) for (var dc = -2; dc <= 2; dc++) {
        var dark = Math.max(Math.abs(dr), Math.abs(dc)) !== 1;
        set(ar + dr, ac + dc, dark ? 1 : 0);
      }
    }
    // 固定暗模块
    set(size - 8, 8, 1);
    // 版本信息（v≥7）
    if (version >= 7) {
      var vi = bchVersion(version);
      for (var b = 0; b < 18; b++) {
        var bit = (vi >> b) & 1;
        set(Math.floor(b / 3), b % 3 + size - 8 - 3, bit);
        set(b % 3 + size - 8 - 3, Math.floor(b / 3), bit);
      }
    }
    return { m: m, res: res };
  }

  /* ---------- 数据摆放（之字形） ---------- */
  function placeData(m, codewords) {
    var size = m.length, bitIdx = 0, totalBits = codewords.length * 8;
    var upward = true;
    for (var col = size - 1; col > 0; col -= 2) {
      if (col === 6) col--; // 跳过时序列
      for (var step = 0; step < size; step++) {
        var row = upward ? size - 1 - step : step;
        for (var c = col; c >= col - 1; c--) {
          if (m[row][c] !== null) continue;
          var bit = bitIdx < totalBits ? (codewords[bitIdx >> 3] >> (7 - (bitIdx & 7))) & 1 : 0;
          m[row][c] = bit;
          bitIdx++;
        }
      }
      upward = !upward;
    }
    return bitIdx;
  }

  /* ---------- 掩码 ---------- */
  var MASKS = [
    function (i, j) { return (i + j) % 2 === 0; },
    function (i) { return i % 2 === 0; },
    function (i, j) { return j % 3 === 0; },
    function (i, j) { return (i + j) % 3 === 0; },
    function (i, j) { return (Math.floor(i / 2) + Math.floor(j / 3)) % 2 === 0; },
    function (i, j) { return ((i * j) % 2 + (i * j) % 3) === 0; },
    function (i, j) { return (((i * j) % 2 + (i * j) % 3) % 2) === 0; },
    function (i, j) { return (((i + j) % 2 + (i * j) % 3) % 2) === 0; }
  ];

  function applyMask(m, maskIdx, res) {
    var size = m.length;
    for (var i = 0; i < size; i++) for (var j = 0; j < size; j++) {
      if (!res[i][j] && m[i][j] !== null && MASKS[maskIdx](i, j)) m[i][j] ^= 1;
    }
  }

  function writeFormat(m, ecName, maskIdx) {
    var size = m.length;
    var data = (EC_FORMAT_BITS[ecName] << 3) | maskIdx;
    var bits = bchFormat(data);
    for (var i = 0; i < 15; i++) {
      var bit = (bits >> i) & 1;
      // 纵向（col 8）
      if (i < 6) m[i][8] = bit;
      else if (i < 8) m[i + 1][8] = bit;
      else m[size - 15 + i][8] = bit;
      // 横向（row 8）
      if (i < 8) m[8][size - 1 - i] = bit;
      else if (i < 9) m[8][7] = bit;
      else m[8][15 - i - 1] = bit;
    }
    m[size - 8][8] = 1; // 固定暗模块
  }

  function penalty(m) {
    var size = m.length, score = 0;
    // 规则1：行/列连续同色
    for (var dir = 0; dir < 2; dir++) {
      for (var i = 0; i < size; i++) {
        var run = 1;
        for (var j = 1; j < size; j++) {
          var cur = dir ? m[j][i] : m[i][j], prev = dir ? m[j - 1][i] : m[i][j - 1];
          if (cur === prev) { run++; if (j === size - 1 && run >= 5) score += 3 + (run - 5); }
          else { if (run >= 5) score += 3 + (run - 5); run = 1; }
        }
      }
    }
    // 规则2：2×2 同色块
    for (var r = 0; r < size - 1; r++) for (var c = 0; c < size - 1; c++) {
      if (m[r][c] === m[r][c + 1] && m[r][c] === m[r + 1][c] && m[r][c] === m[r + 1][c + 1]) score += 3;
    }
    // 规则3：类定位图形 1011101 + 0000
    var pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], pat2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];
    for (var rr = 0; rr < size; rr++) for (var cc = 0; cc <= size - 11; cc++) {
      var rowOK1 = true, rowOK2 = true, colOK1 = true, colOK2 = true;
      for (var k = 0; k < 11; k++) {
        if (m[rr][cc + k] !== pat1[k]) rowOK1 = false;
        if (m[rr][cc + k] !== pat2[k]) rowOK2 = false;
        if (m[cc + k][rr] !== pat1[k]) colOK1 = false;
        if (m[cc + k][rr] !== pat2[k]) colOK2 = false;
      }
      if (rowOK1 || rowOK2 || colOK1 || colOK2) score += 40;
    }
    // 规则4：暗模块占比
    var dark = 0;
    for (var r2 = 0; r2 < size; r2++) for (var c2 = 0; c2 < size; c2++) dark += m[r2][c2];
    var pct = dark * 100 / (size * size);
    score += Math.floor(Math.abs(pct - 50) / 5) * 10;
    return score;
  }

  /* ---------- 对外接口 ---------- */
  function encode(text, ecName, done, forceMask) {
    loadSpec(function () {
      var bytes = new TextEncoder().encode(text);
      var version = chooseVersion(bytes.length, ecName || 'M', SPEC);
      var codewords = buildCodewords(text, ecName || 'M', version, SPEC);
      var best = null, bestScore = Infinity;
      var from = forceMask != null ? forceMask : 0;
      var to = forceMask != null ? forceMask + 1 : 8;
      for (var mask = from; mask < to; mask++) {
        var built = makeMatrix(version, SPEC);
        var m = built.m, res = built.res;
        placeData(m, codewords);
        applyMask(m, mask, res);
        writeFormat(m, ecName || 'M', mask);
        var score = penalty(m);
        if (score < bestScore) { bestScore = score; best = m; }
      }
      done({ matrix: best, version: version, ec: ecName || 'M', size: best.length, mask: forceMask != null ? forceMask : bestScore, score: bestScore });
    });
  }

  function toCanvas(canvas, result, opts) {
    opts = opts || {};
    var quiet = opts.quiet != null ? opts.quiet : 4;
    var scale = opts.scale || Math.max(2, Math.floor(320 / result.size));
    var px = (result.size + quiet * 2) * scale;
    canvas.width = px; canvas.height = px;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = opts.light || '#FFFFFF';
    ctx.fillRect(0, 0, px, px);
    ctx.fillStyle = opts.dark || '#000000';
    for (var r = 0; r < result.size; r++) for (var c = 0; c < result.size; c++) {
      if (result.matrix[r][c]) ctx.fillRect((c + quiet) * scale, (r + quiet) * scale, scale, scale);
    }
    return canvas;
  }

  function toSVG(result, opts) {
    opts = opts || {};
    var quiet = opts.quiet != null ? opts.quiet : 4;
    var size = result.size + quiet * 2;
    var parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + size + ' ' + size + '" shape-rendering="crispEdges">'];
    parts.push('<rect width="100%" height="100%" fill="' + (opts.light || '#FFFFFF') + '"/>');
    parts.push('<path fill="' + (opts.dark || '#000000') + '" d="');
    for (var r = 0; r < result.size; r++) for (var c = 0; c < result.size; c++) {
      if (result.matrix[r][c]) parts.push('M' + (c + quiet) + ' ' + (r + quiet) + 'h1v1h-1z');
    }
    parts.push('"/></svg>');
    return parts.join('');
  }

  global.QR = {
    encode: encode, toCanvas: toCanvas, toSVG: toSVG,
    _debug: function (text, ecName, version, mask, done) {
      loadSpec(function () {
        var bytes = new TextEncoder().encode(text);
        version = version || chooseVersion(bytes.length, ecName || 'M', SPEC);
        var codewords = buildCodewords(text, ecName || 'M', version, SPEC);
        var built = makeMatrix(version, SPEC);
        placeData(built.m, codewords);
        if (mask != null) applyMask(built.m, mask, built.res);
        if (mask != null) writeFormat(built.m, ecName || 'M', mask);
        done({ matrix: built.m, res: built.res, codewords: codewords, version: version, size: built.m.length });
      });
    }
  };
})(window);