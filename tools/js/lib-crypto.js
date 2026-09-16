/* 共享库：纯前端加密/编码 — MD5 / SHA-256 / HMAC / PBKDF2 / Scrypt / Base32 / Base58 / Base85
   页面引入：<script src="/tools/js/lib-crypto.js"></script>
   命名空间：LibCrypto（别名 LC）*/
(function (global) {
  'use strict';
  var LC = {};

  /* ---------- MD5 ---------- */
  (function () {
    var S = [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
      5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
      4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
      6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21];
    var K = new Uint32Array(64);
    for (var i = 0; i < 64; i++) K[i] = Math.floor(Math.abs(Math.sin(i + 1)) * 4294967296);

    function rotl(x, c) { return (x << c) | (x >>> (32 - c)); }

    LC.md5 = function (bytes) {
      var msg = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
      var bitLen = msg.length * 8;
      var withPad = (((msg.length + 8) >> 6) + 1) << 6;
      var m = new Uint8Array(withPad);
      m.set(msg);
      m[msg.length] = 0x80;
      var dv = new DataView(m.buffer);
      dv.setUint32(withPad - 8, bitLen >>> 0, true);
      dv.setUint32(withPad - 4, Math.floor(bitLen / 4294967296), true);
      var a0 = 0x67452301, b0 = 0xefcdab89, c0 = 0x98badcfe, d0 = 0x10325476;
      for (var off = 0; off < withPad; off += 64) {
        var M = new Uint32Array(16);
        for (var j = 0; j < 16; j++) M[j] = dv.getUint32(off + j * 4, true);
        var A = a0, B = b0, C = c0, D = d0;
        for (var k = 0; k < 64; k++) {
          var F, g;
          if (k < 16) { F = (B & C) | (~B & D); g = k; }
          else if (k < 32) { F = (D & B) | (~D & C); g = (5 * k + 1) % 16; }
          else if (k < 48) { F = B ^ C ^ D; g = (3 * k + 5) % 16; }
          else { F = C ^ (B | ~D); g = (7 * k) % 16; }
          F = (F + A + K[k] + M[g]) >>> 0;
          A = D; D = C; C = B;
          B = (B + rotl(F, S[k])) >>> 0;
        }
        a0 = (a0 + A) >>> 0; b0 = (b0 + B) >>> 0; c0 = (c0 + C) >>> 0; d0 = (d0 + D) >>> 0;
      }
      var out = new Uint8Array(16);
      var odv = new DataView(out.buffer);
      odv.setUint32(0, a0, true); odv.setUint32(4, b0, true);
      odv.setUint32(8, c0, true); odv.setUint32(12, d0, true);
      return out;
    };
  })();

  /* ---------- SHA-256 (同步纯 JS，供 PBKDF2/Scrypt 使用) ---------- */
  var K256 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2];

  function sha256Run(msg) {
    var bitLen = msg.length * 8;
    var withPad = (((msg.length + 8) >> 6) + 1) << 6;
    var m = new Uint8Array(withPad);
    m.set(msg);
    m[msg.length] = 0x80;
    var dv = new DataView(m.buffer);
    dv.setUint32(withPad - 4, bitLen >>> 0);
    var H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    var w = new Uint32Array(64);
    function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }
    for (var off = 0; off < withPad; off += 64) {
      for (var t = 0; t < 16; t++) w[t] = dv.getUint32(off + t * 4);
      for (t = 16; t < 64; t++) {
        var s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        var s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
      }
      var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
      for (t = 0; t < 64; t++) {
        var S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (h + S1 + ch + K256[t] + w[t]) >>> 0;
        var S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        var mj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + mj) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0;
        d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b) >>> 0; H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
      H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0; H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
    }
    var out = new Uint8Array(32), odv = new DataView(out.buffer);
    for (var i = 0; i < 8; i++) odv.setUint32(i * 4, H[i]);
    return out;
  }
  LC.sha256 = sha256Run;

  /* ---------- HMAC-SHA256 ---------- */
  LC.hmacSha256 = function (key, msg) {
    if (key.length > 64) key = sha256Run(key);
    var ip = new Uint8Array(64 + msg.length), op = new Uint8Array(64 + 32);
    for (var i = 0; i < 64; i++) {
      var k = i < key.length ? key[i] : 0;
      ip[i] = k ^ 0x36; op[i] = k ^ 0x5c;
    }
    ip.set(msg, 64);
    op.set(sha256Run(ip), 64);
    return sha256Run(op);
  };

  /* ---------- PBKDF2-HMAC-SHA256 ---------- */
  LC.pbkdf2 = function (password, salt, iterations, dkLen) {
    var blocks = Math.ceil(dkLen / 32);
    var out = new Uint8Array(blocks * 32);
    for (var b = 1; b <= blocks; b++) {
      var sBytes = new Uint8Array(salt.length + 4);
      sBytes.set(salt);
      sBytes[salt.length] = (b >>> 24) & 0xff; sBytes[salt.length + 1] = (b >>> 16) & 0xff;
      sBytes[salt.length + 2] = (b >>> 8) & 0xff; sBytes[salt.length + 3] = b & 0xff;
      var u = LC.hmacSha256(password, sBytes);
      var acc = new Uint8Array(u);
      for (var it = 1; it < iterations; it++) {
        u = LC.hmacSha256(password, u);
        for (var j = 0; j < 32; j++) acc[j] ^= u[j];
      }
      out.set(acc, (b - 1) * 32);
    }
    return out.slice(0, dkLen);
  };

  /* ---------- Scrypt (RFC 7914) ---------- */
  function salsaX(tmp) {
    var x = new Uint32Array(tmp);
    function R(a, b) { return ((a << b) | (a >>> (32 - b))) >>> 0; }
    for (var i = 8; i > 0; i -= 2) {
      x[4] ^= R((x[0] + x[12]) >>> 0, 7); x[8] ^= R((x[4] + x[0]) >>> 0, 9);
      x[12] ^= R((x[8] + x[4]) >>> 0, 13); x[0] ^= R((x[12] + x[8]) >>> 0, 18);
      x[9] ^= R((x[5] + x[1]) >>> 0, 7); x[13] ^= R((x[9] + x[5]) >>> 0, 9);
      x[1] ^= R((x[13] + x[9]) >>> 0, 13); x[5] ^= R((x[1] + x[13]) >>> 0, 18);
      x[14] ^= R((x[10] + x[6]) >>> 0, 7); x[2] ^= R((x[14] + x[10]) >>> 0, 9);
      x[6] ^= R((x[2] + x[14]) >>> 0, 13); x[10] ^= R((x[6] + x[2]) >>> 0, 18);
      x[3] ^= R((x[15] + x[11]) >>> 0, 7); x[7] ^= R((x[3] + x[15]) >>> 0, 9);
      x[11] ^= R((x[7] + x[3]) >>> 0, 13); x[15] ^= R((x[11] + x[7]) >>> 0, 18);
      x[1] ^= R((x[0] + x[3]) >>> 0, 7); x[2] ^= R((x[1] + x[0]) >>> 0, 9);
      x[3] ^= R((x[2] + x[1]) >>> 0, 13); x[0] ^= R((x[3] + x[2]) >>> 0, 18);
      x[6] ^= R((x[5] + x[4]) >>> 0, 7); x[7] ^= R((x[6] + x[5]) >>> 0, 9);
      x[4] ^= R((x[7] + x[6]) >>> 0, 13); x[5] ^= R((x[4] + x[7]) >>> 0, 18);
      x[11] ^= R((x[10] + x[9]) >>> 0, 7); x[8] ^= R((x[11] + x[10]) >>> 0, 9);
      x[9] ^= R((x[8] + x[11]) >>> 0, 13); x[10] ^= R((x[9] + x[8]) >>> 0, 18);
      x[12] ^= R((x[15] + x[14]) >>> 0, 7); x[13] ^= R((x[12] + x[15]) >>> 0, 9);
      x[14] ^= R((x[13] + x[12]) >>> 0, 13); x[15] ^= R((x[14] + x[13]) >>> 0, 18);
    }
    for (i = 0; i < 16; i++) tmp[i] = (tmp[i] + x[i]) >>> 0;
  }
  function blockMixIn(B, X, r) {
    X.set(B.subarray(32 * r - 16, 32 * r));
    var Y = new Uint32Array(32 * r);
    for (var i = 0; i < r; i += 2) {
      for (var j = 0; j < 16; j++) X[j] ^= B[i * 16 + j];
      salsaX(X); Y.set(X, i * 16);
      for (j = 0; j < 16; j++) X[j] ^= B[(i + 1) * 16 + j];
      salsaX(X); Y.set(X, (i + r) * 16);
    }
    B.set(Y);
  }
  function roMix(B, r, N, V, XY) {
    for (var i = 0; i < N; i += 2) {
      V.set(B, i * 32 * r);
      blockMixIn(B, XY, r);
      var j = (B[32 * r - 16] & (N - 1)) * 32 * r;
      for (var k = 0; k < 32 * r; k++) B[k] ^= V[j + k];
      blockMixIn(B, XY, r);
    }
  }
  LC.scrypt = function (password, salt, N, r, p, dkLen) {
    if ((N & (N - 1)) !== 0) throw new Error('N 必须是 2 的幂');
    var B = LC.pbkdf2(password, salt, 1, p * 128 * r);
    var Bw = new Uint32Array(B.length / 4);
    for (var i = 0; i < Bw.length; i++) Bw[i] = B[i * 4] | (B[i * 4 + 1] << 8) | (B[i * 4 + 2] << 16) | (B[i * 4 + 3] << 24);
    var V = new Uint32Array(32 * N * r), XY = new Uint32Array(64 * r);
    for (var blk = 0; blk < p; blk++) {
      var view = Bw.subarray(blk * 32 * r, (blk + 1) * 32 * r);
      roMix(view, r, N, V, XY);
    }
    for (i = 0; i < Bw.length; i++) {
      B[i * 4] = Bw[i] & 0xff; B[i * 4 + 1] = (Bw[i] >>> 8) & 0xff;
      B[i * 4 + 2] = (Bw[i] >>> 16) & 0xff; B[i * 4 + 3] = (Bw[i] >>> 24) & 0xff;
    }
    return LC.pbkdf2(password, B, 1, dkLen);
  };

  /* ---------- Base32 (RFC 4648) ---------- */
  var B32A = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  LC.b32encode = function (bytes) {
    var out = '', bits = 0, val = 0;
    for (var i = 0; i < bytes.length; i++) {
      val = (val << 8) | bytes[i]; bits += 8;
      while (bits >= 5) { out += B32A[(val >>> (bits - 5)) & 31]; bits -= 5; }
    }
    if (bits > 0) out += B32A[(val << (5 - bits)) & 31];
    while (out.length % 8) out += '=';
    return out;
  };
  LC.b32decode = function (str) {
    var clean = str.toUpperCase().replace(/=+$/, '');
    var out = [], bits = 0, val = 0;
    for (var i = 0; i < clean.length; i++) {
      var idx = B32A.indexOf(clean[i]);
      if (idx < 0) throw new Error('非法 Base32 字符：' + clean[i]);
      val = (val << 5) | idx; bits += 5;
      if (bits >= 8) { out.push((val >>> (bits - 8)) & 255); bits -= 8; }
    }
    return new Uint8Array(out);
  };

  /* ---------- Base58 (Bitcoin 字母表) ---------- */
  var B58A = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  LC.b58encode = function (bytes) {
    if (!bytes.length) return '';
    var digits = [0], base = 58;
    for (var i = 0; i < bytes.length; i++) {
      var carry = bytes[i];
      for (var j = 0; j < digits.length; j++) {
        carry += digits[j] << 8;
        digits[j] = carry % base;
        carry = (carry / base) | 0;
      }
      while (carry > 0) { digits.push(carry % base); carry = (carry / base) | 0; }
    }
    var out = '';
    for (i = 0; i < bytes.length && bytes[i] === 0; i++) out += '1';
    for (var k = digits.length - 1; k >= 0; k--) if (k > 0 || digits[k] > 0) out += B58A[digits[k]];
    return out;
  };
  LC.b58decode = function (str) {
    if (!str.length) return new Uint8Array(0);
    var bytes = [0];
    for (var i = 0; i < str.length; i++) {
      var val = B58A.indexOf(str[i]);
      if (val < 0) throw new Error('非法 Base58 字符：' + str[i]);
      var carry = val;
      for (var j = 0; j < bytes.length; j++) {
        carry += bytes[j] * 58;
        bytes[j] = carry & 0xff;
        carry >>= 8;
      }
      while (carry > 0) { bytes.push(carry & 0xff); carry >>= 8; }
    }
    var zeros = 0;
    for (i = 0; i < str.length && str[i] === '1'; i++) zeros++;
    var out = new Uint8Array(zeros + bytes.length);
    for (var k = 0; k < bytes.length; k++) out[out.length - 1 - k] = bytes[k];
    return out;
  };

  /* ---------- Base85 / Ascii85 ---------- */
  LC.b85encode = function (bytes) {
    var out = '';
    for (var i = 0; i < bytes.length; i += 4) {
      var chunk = [bytes[i] || 0, bytes[i + 1] || 0, bytes[i + 2] || 0, bytes[i + 3] || 0];
      var n = chunk[0] * 16777216 + chunk[1] * 65536 + chunk[2] * 256 + chunk[3];
      if (n === 0 && i + 4 <= bytes.length) { out += 'z'; continue; }
      var group = '';
      for (var j = 0; j < 5; j++) { group = String.fromCharCode(33 + (n % 85)) + group; n = (n / 85) | 0; }
      out += i + 4 <= bytes.length ? group : group.slice(0, bytes.length - i + 1);
    }
    return out;
  };
  LC.b85decode = function (str) {
    str = str.replace(/\s/g, '');
    var out = [], i = 0;
    while (i < str.length) {
      if (str[i] === 'z') { out.push(0, 0, 0, 0); i++; continue; }
      var group = str.slice(i, i + 5);
      i += group.length;
      var n = 0;
      for (var j = 0; j < 5; j++) n = n * 85 + (j < group.length ? group.charCodeAt(j) - 33 : 84);
      if (n > 4294967295) throw new Error('非法 Ascii85 数据');
      var b4 = [(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255];
      var keep = group.length - 1;
      for (j = 0; j < keep; j++) out.push(b4[j]);
    }
    return new Uint8Array(out);
  };

  global.LibCrypto = LC;
  global.LC = LC;
})(window);
