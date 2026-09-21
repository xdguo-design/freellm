/* ============================================================
   FreeLLM Tools — Tool Registry
   All tools with metadata: id, name, category, description, etc.
   Each tool is a separate HTML file in tools/tools/<id>.html
   ============================================================ */

(function (global) {
  'use strict';

  const CATS = [
    { id: 'encode', label: '编码加密', cls: 'blue' },
    { id: 'format', label: '格式化', cls: 'green' },
    { id: 'generate', label: '生成器', cls: 'yellow' },
    { id: 'css', label: 'CSS 工具', cls: 'violet' },
    { id: 'text', label: '文本工具', cls: 'blue' },
    { id: 'calc', label: '计算转换', cls: 'green' },
    { id: 'datetime', label: '日期时间', cls: 'yellow' },
    { id: 'ref', label: '速查参考', cls: 'violet' },
    { id: 'dev', label: '开发工具', cls: 'blue' },
    { id: 'image', label: '图片工具', cls: 'green' },
    { id: 'fun', label: '趣味娱乐', cls: 'yellow' },
    { id: 'util', label: '其他实用', cls: 'violet' },
    { id: 'crypto', label: '安全加密', cls: 'blue' }
  ];

  const TOOLS = [
    // ===== 编码加密 =====
    { id: 'base64', name: 'Base64 编解码', cat: 'encode', desc: 'Base64 编码与解码，含图片', hot: true },
    { id: 'url-encode', name: 'URL 编解码', cat: 'encode', desc: 'encodeURI / decodeURI 编码解码', hot: true },
    { id: 'md5', name: 'MD5 哈希', cat: 'encode', desc: 'MD5 摘要计算，纯前端实现', hot: true },
    { id: 'sha', name: 'SHA 哈希', cat: 'encode', desc: 'SHA-1/256/384/512 哈希计算', hot: true },
    { id: 'html-entity', name: 'HTML 实体编解码', cat: 'encode', desc: 'HTML 实体字符 ↔ 原始字符互转', hot: true },
    { id: 'unicode', name: 'Unicode 转换', cat: 'encode', desc: '\\uXXXX ↔ 中文/Emoji 互转' },
    { id: 'aes', name: 'AES 加解密', cat: 'encode', desc: 'AES-GCM/CBC 对称加解密' },
    { id: 'file-hash', name: '文件哈希', cat: 'encode', desc: '浏览器端计算文件 MD5/SHA 哈希' },
    { id: 'hmac', name: 'HMAC 哈希', cat: 'encode', desc: 'HMAC 消息认证码在线计算' },
    { id: 'gzip', name: 'Gzip 压缩', cat: 'encode', desc: '文本压缩/解压，显示压缩率' },
    { id: 'caesar', name: '凯撒密码', cat: 'encode', desc: '经典凯撒加密解密' },
    { id: 'rot13', name: 'ROT13/ROT47', cat: 'encode', desc: '经典 ROT 系列编码' },
    { id: 'file-hex', name: '文件与 Hex 互转', cat: 'encode', desc: '文件↔十六进制字符串' },
    { id: 'base32', name: 'Base32 编码', cat: 'encode', desc: 'Base32 编码与解码' },
    { id: 'base58', name: 'Base58 编码', cat: 'encode', desc: 'Base58 编码与解码（Bitcoin 风格）' },
    { id: 'base85', name: 'Base85 编码', cat: 'encode', desc: 'Base85 编码与解码（Ascii85）' },
    { id: 'mixed-encode', name: '混合编码', cat: 'encode', desc: '自由组合多条编码规则按顺序叠加，解密自动逆序还原' },

    // ===== 安全加密 =====
    { id: 'rsa', name: 'RSA 密钥生成', cat: 'crypto', desc: '生成 RSA-2048/4096 公私钥对' },
    { id: 'rsa-encrypt', name: 'RSA 加解密', cat: 'crypto', desc: 'RSA 公钥加密 / 私钥解密' },
    { id: 'ecc', name: 'ECC 密钥生成', cat: 'crypto', desc: '生成 ECC P-256/P-384 密钥对' },
    { id: 'hybrid-encrypt', name: '混合加密', cat: 'crypto', desc: 'RSA+AES 混合加密，安全高效' },
    { id: 'jwt', name: 'JWT 编解码', cat: 'crypto', desc: 'JWT Header/Payload 编码与解码' },
    { id: 'totp', name: '一次性密码 TOTP', cat: 'crypto', desc: '基于时间的 OTP 生成（Google Auth 兼容）' },
    { id: 'x509', name: 'X.509 证书解析', cat: 'crypto', desc: '解析 SSL/TLS 证书内容' },
    { id: 'ssh-key', name: 'SSH 密钥生成', cat: 'crypto', desc: '生成 SSH ED25519/RSA 密钥对' },
    { id: 'password-check', name: '密码强度检测', cat: 'crypto', desc: '实时检测密码强度与安全性' },
    { id: 'hash-identify', name: 'Hash 类型识别', cat: 'crypto', desc: '输入 Hash 值自动识别算法' },
    { id: 'pbkdf2', name: 'PBKDF2 派生', cat: 'crypto', desc: 'PBKDF2 密钥派生函数' },
    { id: 'scrypt', name: 'Scrypt 派生', cat: 'crypto', desc: 'Scrypt 密钥派生（抗 GPU 暴力）' },
    { id: 'ecdh', name: 'ECDH 密钥交换', cat: 'crypto', desc: '椭圆曲线 Diffie-Hellman 共享密钥' },
    { id: 'ecdsa', name: 'ECDSA 数字签名', cat: 'crypto', desc: '椭圆曲线数字签名与验证' },
    { id: 'cert-viewer', name: '证书查看器', cat: 'crypto', desc: '上传 PEM 证书查看详细信息' },

    // ===== 格式化 =====
    { id: 'json', name: 'JSON 格式化', cat: 'format', desc: 'JSON 数据美化、校验与转换', hot: true },
    { id: 'sql-formatter', name: 'SQL 格式化', cat: 'format', desc: 'SQL 语句格式化与高亮', hot: true },
    { id: 'code-formatter', name: '代码格式化', cat: 'format', desc: 'HTML/CSS/JS/SQL 代码美化', hot: true },
    { id: 'code-highlight', name: '代码着色高亮', cat: 'format', desc: '多语言代码语法高亮', hot: true },
    { id: 'csv-json', name: 'CSV ↔ JSON', cat: 'format', desc: 'CSV 与 JSON 格式互转' },
    { id: 'json-yaml', name: 'JSON ↔ YAML', cat: 'format', desc: 'JSON 与 YAML 格式互转' },
    { id: 'json-xml', name: 'JSON ↔ XML', cat: 'format', desc: 'JSON 与 XML 格式互转' },
    { id: 'html2md', name: 'HTML 转 Markdown', cat: 'format', desc: 'HTML 源码转 Markdown' },
    { id: 'md2html', name: 'Markdown 转 HTML', cat: 'format', desc: 'Markdown 源码转 HTML' },
    { id: 'minify', name: '代码压缩 Minify', cat: 'format', desc: 'HTML/CSS/JS 代码压缩' },
    { id: 'json2class', name: 'JSON 转实体类', cat: 'format', desc: '生成 Java/C#/Go/TS/Python 类' },
    { id: 'json-tree', name: 'JSON Tree 查看', cat: 'format', desc: '交互式树形结构可视化' },
    { id: 'json-merge', name: 'JSON 合并', cat: 'format', desc: '两个 JSON 对象深度合并' },
    { id: 'json-sort', name: 'JSON 排序', cat: 'format', desc: 'JSON 按 key 排序' },
    { id: 'url-parser', name: 'URL 参数解析', cat: 'format', desc: 'URL 查询字符串结构化解析' },
    { id: 'nginx-formatter', name: 'Nginx 格式化', cat: 'format', desc: 'Nginx 配置高亮美化' },
    { id: 'xml-format', name: 'XML 格式化', cat: 'format', desc: 'XML 美化/压缩/校验' },
    { id: 'yaml-format', name: 'YAML 格式化', cat: 'format', desc: 'YAML 美化/校验/压缩' },
    { id: 'csv-format', name: 'CSV 格式化', cat: 'format', desc: 'CSV 美化/转表格/压缩' },
    { id: 'md-format', name: 'Markdown 格式化', cat: 'format', desc: 'Markdown 美化/清理/压缩' },
    { id: 'excel-convert', name: 'Excel ↔ JSON/CSV', cat: 'format', desc: '上传 Excel 转换为 JSON 或 CSV' },
    { id: 'json-schema', name: 'JSON Schema 校验', cat: 'format', desc: '校验 JSON 是否符合 Schema' },
    { id: 'jsonpath', name: 'JSONPath 查询', cat: 'format', desc: '用 JSONPath 提取 JSON 数据' },
    { id: 'jmespath', name: 'JMESPath 查询', cat: 'format', desc: 'JMESPath 数据查询语言' },
    { id: 'table2csv', name: '表格转 CSV', cat: 'format', desc: '粘贴 HTML 表格 → CSV' },
    { id: 'text2table', name: '文本转表格', cat: 'format', desc: '分隔符/正则 → 表格' },
    { id: 'csv2md', name: 'CSV ↔ Markdown 表格', cat: 'format', desc: 'CSV 与 Markdown 表格互转' },

    // ===== 生成器 =====
    { id: 'uuid', name: 'UUID 生成器', cat: 'generate', desc: 'UUID/GUID 在线批量生成', hot: true },
    { id: 'password', name: '密码生成器', cat: 'generate', desc: '安全随机密码在线生成', hot: true },
    { id: 'qrcode', name: '二维码生成', cat: 'generate', desc: '在线生成 QR Code 二维码', hot: true },
    { id: 'qrcode-scan', name: '二维码扫描', cat: 'generate', desc: '摄像头/上传图片扫描二维码' },
    { id: 'barcode', name: '条形码生成', cat: 'generate', desc: '在线生成 Code128 条形码' },
    { id: 'barcode-scan', name: '条形码识别', cat: 'generate', desc: '上传图片识别条形码内容' },
    { id: 'random-string', name: '随机字符串', cat: 'generate', desc: '随机数字/字母/混合字符串生成' },
    { id: 'lorem', name: 'Lorem Ipsum', cat: 'generate', desc: '占位文本段落生成' },
    { id: 'mock-data', name: 'Mock 数据生成', cat: 'generate', desc: '随机 JSON 假数据生成' },
    { id: 'favicon-maker', name: 'Favicon 制作', cat: 'generate', desc: '图片转 favicon.ico 多尺寸' },
    { id: 'gitignore', name: '.gitignore 生成', cat: 'generate', desc: '按语言框架组合生成' },
    { id: 'og-meta', name: 'OG Meta 标签', cat: 'generate', desc: 'Open Graph 标签生成' },
    { id: 'shield', name: 'Shield Badge', cat: 'generate', desc: 'Shields.io 风格徽章' },
    { id: 'random-color', name: '随机颜色', cat: 'generate', desc: '随机颜色生成 + 调色板' },
    { id: 'random-decision', name: '随机决策', cat: 'generate', desc: '转盘随机选择/掷骰子' },
    { id: 'lorem-pixel', name: '占位图片', cat: 'generate', desc: '生成占位图片/头像' },

    // ===== CSS 工具 =====
    { id: 'css-gradient', name: 'CSS 渐变生成器', cat: 'css', desc: '可视化拖拽 CSS 渐变', hot: true },
    { id: 'css-shadow', name: 'CSS 阴影生成器', cat: 'css', desc: 'Box Shadow 可视化编辑', hot: true },
    { id: 'css-border', name: 'CSS 圆角生成器', cat: 'css', desc: 'Border Radius 可视化调节' },
    { id: 'css-animation', name: 'CSS 动画生成器', cat: 'css', desc: '关键帧动画可视化编辑' },
    { id: 'css-glass', name: 'CSS 毛玻璃', cat: 'css', desc: 'Glassmorphism 效果生成' },
    { id: 'css-loader', name: 'CSS Loading', cat: 'css', desc: 'Spinner/Loader 动画生成' },
    { id: 'css-unit', name: 'CSS 单位换算', cat: 'css', desc: 'px/rem/em/vw/vh/pt 互转' },
    { id: 'svg-shape', name: 'SVG 形状生成', cat: 'css', desc: '随机 SVG Blob/波浪生成' },
    { id: 'font-preview', name: '字体预览器', cat: 'css', desc: '上传字体在线预览' },
    { id: 'css-flexbox', name: 'CSS Flexbox 可视化', cat: 'css', desc: '拖拽调整 → 实时 CSS' },
    { id: 'css-grid', name: 'CSS Grid 可视化', cat: 'css', desc: '拖拽调整 → 实时 CSS' },
    { id: 'css-clip-path', name: 'CSS Clip-path 生成', cat: 'css', desc: '可视化裁剪路径生成' },
    { id: 'css-filter', name: 'CSS Filter 生成', cat: 'css', desc: '滤镜参数可视化调节' },
    { id: 'css-contrast', name: '对比度检查器', cat: 'css', desc: 'WCAG 2.1 对比度检测' },
    { id: 'css-variables', name: 'CSS 变量生成', cat: 'css', desc: '生成 CSS 自定义属性' },
    { id: 'css-reset', name: 'CSS Reset 生成', cat: 'css', desc: '生成 CSS Reset 样式' },
    { id: 'color-palette', name: '调色板生成器', cat: 'css', desc: '输入主色 → 自动生成配色' },

    // ===== 文本工具 =====
    { id: 'regex', name: '正则表达式测试', cat: 'text', desc: '在线正则测试与匹配高亮', hot: true },
    { id: 'regex-visual', name: '正则可视化', cat: 'text', desc: '正则表达式可视化构建器' },
    { id: 'markdown', name: 'Markdown 编辑器', cat: 'text', desc: '在线 Markdown 编辑与预览', hot: true },
    { id: 'word-count', name: '字数统计', cat: 'text', desc: '字符/单词/行/段落计数', hot: true },
    { id: 'diff', name: '文本对比', cat: 'text', desc: '快速找出两段文本之间的差异', hot: true },
    { id: 'case-convert', name: '大小写转换', cat: 'text', desc: '英文大小写/首字母大写转换', hot: true },
    { id: 'camel-convert', name: '变量名转换', cat: 'text', desc: '驼峰/下划线/短横线命名互转', hot: true },
    { id: 'pinyin', name: '汉字转拼音', cat: 'text', desc: '含声调和多音字' },
    { id: 'full-half', name: '全角半角转换', cat: 'text', desc: '全角字符与半角字符互转' },
    { id: 'simp-trad', name: '简繁体转换', cat: 'text', desc: '简体繁体中文互转' },
    { id: 'figlet', name: 'ASCII 艺术字', cat: 'text', desc: 'FIGlet 风格 ASCII 文字' },
    { id: 'slug', name: 'URL Slug 生成', cat: 'text', desc: 'SEO 友好 URL 路径' },
    { id: 'bionic-reading', name: 'Bionic Reading', cat: 'text', desc: '单词前部加粗提升阅读速度' },
    { id: 'html-filter', name: 'HTML 标签过滤', cat: 'text', desc: '保留或移除指定标签' },
    { id: 'fanyi', name: '翻译助手', cat: 'text', desc: '多语言在线翻译工具' },
    { id: 'text-clean', name: '文本清理', cat: 'text', desc: '去除多余空行/空格/特殊字符' },
    { id: 'text-similarity', name: '文本相似度', cat: 'text', desc: '两段文本相似度对比' },
    { id: 'keyword-extract', name: '关键词提取', cat: 'text', desc: '简单 TF-IDF 关键词提取' },
    { id: 'spell-check', name: '拼写检查', cat: 'text', desc: '基于词典的简单拼写检查' },

    // ===== 计算转换 =====
    { id: 'radix-convert', name: '进制转换', cat: 'calc', desc: '2/8/10/16 进制互转', hot: true },
    { id: 'color-convert', name: '颜色转换', cat: 'calc', desc: 'RGB/HEX/HSL/HSV 颜色互转', hot: true },
    { id: 'unit-convert', name: '单位换算器', cat: 'calc', desc: '长度/重量/温度/面积等换算', hot: true },
    { id: 'chmod', name: 'Chmod 计算器', cat: 'calc', desc: 'Linux 权限数字与符号互转', hot: true },
    { id: 'calculator', name: '在线计算器', cat: 'calc', desc: '科学计算器，支持多种运算' },
    { id: 'ieee754', name: 'IEEE 754 转换', cat: 'calc', desc: '浮点数 ↔ 32/64位二进制' },
    { id: 'endian', name: '大小端转换', cat: 'calc', desc: 'Big/Little Endian 字节序' },
    { id: 'color-shades', name: '色阶生成器', cat: 'calc', desc: '颜色深浅渐变序列生成' },
    { id: 'trig', name: '三角函数计算', cat: 'calc', desc: 'sin/cos/tan 角度/弧度' },
    { id: 'bit-reverse', name: '二进制位操作', cat: 'calc', desc: '按位翻转与移位操作' },
    { id: 'loan', name: '贷款计算器', cat: 'calc', desc: '等额本息/等额本金计算' },
    { id: 'bmi', name: 'BMI 计算器', cat: 'calc', desc: '身体质量指数', hot: true },
    { id: 'calorie', name: '卡路里计算器', cat: 'calc', desc: '基础代谢 + 日常消耗计算' },
    { id: 'retirement', name: '退休年龄计算器', cat: 'calc', desc: '按政策计算退休年龄与日期' },
    { id: 'compound', name: '复利计算器', cat: 'calc', desc: '复利/投资收益计算' },
    { id: 'tip', name: '小费计算器', cat: 'calc', desc: '计算小费与总账单' },
    { id: 'aspect-ratio', name: '宽高比计算器', cat: 'calc', desc: '图片/视频宽高比计算' },
    { id: 'pixel-density', name: '像素密度计算', cat: 'calc', desc: 'DPI/PPI 计算' },
    { id: 'data-transfer', name: '数据传输计算', cat: 'calc', desc: '下载时间/上传时间估算' },
    { id: 'storage', name: '存储容量换算', cat: 'calc', desc: 'Byte/KB/MB/GB/TB 互转' },
    { id: 'speed-converter', name: '速度单位换算', cat: 'calc', desc: 'km/h ↔ mph ↔ m/s 等' },
    { id: 'pressure-converter', name: '压力单位换算', cat: 'calc', desc: 'Pa/Bar/PSI/atm 等' },
    { id: 'energy-converter', name: '能量单位换算', cat: 'calc', desc: 'Joule/Kcal/kWh 等' },
    { id: 'power-converter', name: '功率单位换算', cat: 'calc', desc: 'Watt/KW/Horsepower 等' },
    { id: 'frequency-converter', name: '频率单位换算', cat: 'calc', desc: 'Hz/KHz/MHz/GHz 等' },
    { id: 'angle-converter', name: '角度单位换算', cat: 'calc', desc: '度/弧度/梯度 等' },
    { id: 'density-converter', name: '密度单位换算', cat: 'calc', desc: 'g/cm³ ↔ kg/m³ 等' },
    { id: 'volume-converter', name: '体积单位换算', cat: 'calc', desc: 'L/mL/m³ 等' },
    { id: 'weight-converter', name: '重量单位换算', cat: 'calc', desc: 'g/kg/斤/磅/盎司 等' },
    { id: 'length-converter', name: '长度单位换算', cat: 'calc', desc: 'mm/cm/m/in/ft/px 等' },
    { id: 'area-converter', name: '面积单位换算', cat: 'calc', desc: 'm²/亩/平方英尺 等' },
    { id: 'time-converter', name: '时间单位换算', cat: 'calc', desc: '秒/分/时/天/年 等' },
    { id: 'temp-converter', name: '温度单位换算', cat: 'calc', desc: '摄氏/华氏/开氏 等' },

    // ===== 日期时间 =====
    { id: 'timestamp', name: '时间戳转换', cat: 'datetime', desc: 'Unix 时间戳与日期时间互转', hot: true },
    { id: 'cron', name: 'Cron 表达式', cat: 'datetime', desc: 'Cron 表达式解析与验证', hot: true },
    { id: 'date-calc', name: '日期计算器', cat: 'datetime', desc: '日期间隔/日期加减计算', hot: true },
    { id: 'countdown', name: '倒计时器', cat: 'datetime', desc: '设定目标日期的实时倒计时' },
    { id: 'stopwatch', name: '在线秒表', cat: 'datetime', desc: '开始/暂停/计次/复位' },
    { id: 'age-calc', name: '年龄计算器', cat: 'datetime', desc: '精确到天的年龄计算' },
    { id: 'lunar-calendar', name: '公历农历转换', cat: 'datetime', desc: '公历 ↔ 农历日期互转' },
    { id: 'almanac', name: '黄历查询', cat: 'datetime', desc: '每日黄历宜忌/冲煞/吉凶' },
    { id: 'alarm', name: '在线闹钟', cat: 'datetime', desc: '设定时间到点响铃' },
    { id: 'world-time', name: '世界时间表', cat: 'datetime', desc: '全球主要城市当前时间' },
    { id: 'leap-year', name: '闰年计算器', cat: 'datetime', desc: '公历/农历闰年查询' },
    { id: 'workday', name: '工作日计算', cat: 'datetime', desc: '两个日期之间工作日天数' },
    { id: 'week-number', name: '周数查询', cat: 'datetime', desc: '任意日期是当年第几周' },
    { id: 'calendar', name: '在线万年历', cat: 'datetime', desc: '可视化月历+农历+节气' },
    { id: 'bazi', name: '八字五行', cat: 'datetime', desc: '出生时间 → 八字 + 五行分析' },
    { id: 'festival', name: '传统节日查询', cat: 'datetime', desc: '春节/元宵/端午/中秋等' },
    { id: 'solar-term', name: '二十四节气', cat: 'datetime', desc: '节气日期与说明' },
    { id: 'zodiac', name: '生肖星座', cat: 'datetime', desc: '出生年份 → 生肖 + 星座' },
    { id: 'auspicious', name: '择吉选日', cat: 'datetime', desc: '按事项选吉日' },
    { id: 'timer', name: '正计时器', cat: 'datetime', desc: '跑表模式正计时' },
    { id: 'timezone', name: '时区转换', cat: 'datetime', desc: '不同时区时间互转' },
    { id: 'meeting-time', name: '会议时间换算', cat: 'datetime', desc: '跨时区会议时间计算' },
    { id: 'quarter', name: '季度计算器', cat: 'datetime', desc: '季度/财年计算' },
    { id: 'countdown-multi', name: '多倒计时', cat: 'datetime', desc: '多个目标倒计时 + 提醒' },

    // ===== 速查参考 =====
    { id: 'http-status', name: 'HTTP 状态码', cat: 'ref', desc: '全部 HTTP 状态码速查表', hot: true },
    { id: 'ascii', name: 'ASCII 对照表', cat: 'ref', desc: '0-127 完整 ASCII 字符对照', hot: true },
    { id: 'emoji', name: 'Emoji 大全', cat: 'ref', desc: '分类浏览 Emoji，点击复制', hot: true },
    { id: 'keycode', name: '键盘键位码', cat: 'ref', desc: 'keyCode/key/which 实时查看' },
    { id: 'html-chars', name: 'HTML 特殊字符', cat: 'ref', desc: '常用 HTML 字符实体速查' },
    { id: 'http-headers', name: 'HTTP 请求头参考', cat: 'ref', desc: '常见请求头详解' },
    { id: 'content-type', name: 'Content-Type 大全', cat: 'ref', desc: 'MIME 类型速查' },
    { id: 'ports', name: '常见端口速查', cat: 'ref', desc: 'TCP/UDP 常用端口号' },
    { id: 'regex-cheat', name: '正则大全', cat: 'ref', desc: '常用正则表达式速查' },
    { id: 'operator', name: '运算符优先级', cat: 'ref', desc: '多语言运算符优先级' },
    { id: 'linux-cmd', name: 'Linux 命令速查', cat: 'ref', desc: '分类 Linux 命令参考表' },
    { id: 'symbols', name: '特殊符号大全', cat: 'ref', desc: '分类速查点击复制' },
    { id: 'css-props', name: 'CSS 属性速查', cat: 'ref', desc: 'CSS 属性参考表' },
    { id: 'js-api', name: 'JS API 速查', cat: 'ref', desc: '常用 JavaScript API 参考' },
    { id: 'html-tags', name: 'HTML 标签速查', cat: 'ref', desc: 'HTML 标签参考表' },
    { id: 'mysql-syntax', name: 'MySQL 语法速查', cat: 'ref', desc: 'MySQL 常用语法参考' },
    { id: 'git-commands', name: 'Git 命令速查', cat: 'ref', desc: 'Git 常用命令参考' },
    { id: 'docker-commands', name: 'Docker 命令大全', cat: 'ref', desc: 'Docker 命令 + Dockerfile 指令大全' },
    { id: 'unicode-table', name: 'Unicode 字符表', cat: 'ref', desc: '常用 Unicode 字符速查' },
    { id: 'color-names', name: '颜色名称对照', cat: 'ref', desc: 'CSS 颜色名称与 Hex 对照' },
    { id: 'font-stack', name: '字体栈推荐', cat: 'ref', desc: '常用字体栈组合参考' },

    // ===== 开发工具 =====
        { id: 'mermaid', name: 'Mermaid 编辑器', cat: 'dev', desc: '流程图/时序图在线编辑', hot: true },
    { id: 'curl-converter', name: 'Curl 转代码', cat: 'dev', desc: 'Curl 命令转 Python/JS/Go/Java' },
    { id: 'xpath', name: 'XPath 测试', cat: 'dev', desc: 'XPath 表达式在线测试' },
    { id: 'code2img', name: '代码转图片', cat: 'dev', desc: '代码截图美化分享' },
    { id: 'ua-parser', name: 'UA 解析', cat: 'dev', desc: 'User-Agent 浏览器信息解析' },
    { id: 'magic-bytes', name: '文件格式识别', cat: 'dev', desc: 'Magic Bytes 检测真实格式' },
    { id: 'unzip', name: 'ZIP 解压查看', cat: 'dev', desc: '在线解压查看文件列表' },
    { id: 'websocket-test', name: 'WebSocket 测试', cat: 'dev', desc: '在线 WebSocket 连接调试' },
    { id: 'csr-gen', name: 'CSR 证书生成', cat: 'dev', desc: 'SSL CSR 自签名证书' },
    { id: 'html-preview', name: 'HTML 实时预览', cat: 'dev', desc: '实时 HTML 代码预览' },
    { id: 'css-preview', name: 'CSS 实时预览', cat: 'dev', desc: '实时 CSS 代码预览' },
    { id: 'js-sandbox', name: 'JS 沙箱执行', cat: 'dev', desc: '安全的 JS 代码执行' },
    { id: 'exif-viewer', name: 'EXIF 查看器', cat: 'dev', desc: '上传图片查看元数据' },
    { id: 'image-compress', name: '图片压缩', cat: 'dev', desc: '客户端压缩图片' },
    { id: 'video2gif', name: '视频转 GIF', cat: 'dev', desc: '客户端视频转 GIF 动图' },
    { id: 'audio-record', name: '录音机', cat: 'dev', desc: '录制音频并下载' },
    { id: 'http-builder', name: 'HTTP 请求构建', cat: 'dev', desc: '构建 HTTP 请求（离线）' },
    { id: 'api-test', name: 'API 测试工具', cat: 'dev', desc: '离线 API 请求模拟' },
    { id: 'snippets', name: '代码片段管理', cat: 'dev', desc: '保存和管理代码片段' },
    { id: 'color-contrast', name: '颜色对比度', cat: 'dev', desc: 'WCAG 对比度检测工具' },
    { id: 'svg-editor', name: 'SVG 在线编辑', cat: 'dev', desc: '可视化编辑 SVG 图形' },
    { id: 'icon-font', name: '图标字体生成', cat: 'dev', desc: 'SVG → Icon Font' },
    { id: 'font-subset', name: '字体子集化', cat: 'dev', desc: '提取字体中用到的字符' },

    // ===== 图片工具 =====
    { id: 'image-resize', name: '图片尺寸调整', cat: 'image', desc: '预设尺寸裁剪调整', hot: true },
    { id: 'image-crop', name: '图片自由裁剪', cat: 'image', desc: '拖拽裁剪区域，固定比例', hot: true },
    { id: 'image-watermark', name: '图片加水印', cat: 'image', desc: '文字/Logo 水印叠加' },
    { id: 'image-filter', name: '图片滤镜', cat: 'image', desc: '亮度/对比度/饱和度调节' },
    { id: 'gif-maker', name: 'GIF 制作', cat: 'image', desc: '多张图片合成 GIF 动画' },
    { id: 'image-rotate', name: '图片旋转翻转', cat: 'image', desc: '90°/180°旋转镜像' },
    { id: 'image-grid', name: '九宫格切图', cat: 'image', desc: '图片切 9 等份发朋友圈' },
    { id: 'image-picker', name: '图片取色器', cat: 'image', desc: '上传图片点击取色' },
    { id: 'colorblind', name: '颜色盲模拟', cat: 'image', desc: '红绿色盲/蓝黄色盲视角' },
    { id: 'gif-frame', name: 'GIF 转帧', cat: 'image', desc: 'GIF 分解为逐帧图片' },
    { id: 'image2pdf', name: '图片转 PDF', cat: 'image', desc: '多张图片合并为 PDF' },
    { id: 'image-format', name: '图片格式转换', cat: 'image', desc: 'PNG↔JPEG↔WebP↔AVIF' },
    { id: 'bg-remove', name: '去背景（颜色版）', cat: 'image', desc: '基于颜色的背景去除，适合纯色背景' },
    { id: 'image-target-kb', name: '压到指定 KB', cat: 'image', desc: '按目标文件体积自动调质量' },
    { id: 'image-stitch', name: '图片拼接', cat: 'image', desc: '多图拼宫格/长图/横幅' },
    { id: 'image-poster', name: '海报制作', cat: 'image', desc: '图片+文字+图层做社媒封面' },
    { id: 'image-id-photo', name: '证件照制作', cat: 'image', desc: '换背景+常用证件照规格' },
    { id: 'image-template', name: '模板切图', cat: 'image', desc: '九宫格/长图/照片墙模板' },
    { id: 'image-mirror', name: '图片镜像翻转', cat: 'image', desc: '水平/垂直翻转图片' },
    { id: 'collage', name: '图片拼图', cat: 'image', desc: '多张图片拼接成一张' },
    { id: 'image-workspace', name: '连续处理工作台', cat: 'image', desc: '多步流水线批量处理，流程自动保存', hot: true },
    { id: 'sticker', name: '贴纸生成', cat: 'image', desc: '生成带圆角的贴纸图片' },
    { id: 'avatar-maker', name: '头像生成', cat: 'image', desc: '生成个性化头像' },
    { id: 'screenshot', name: '屏幕截图', cat: 'image', desc: '浏览器截图 + 标注' },
    { id: 'screen-record', name: '在线录屏', cat: 'image', desc: '浏览器录屏+下载 WebM' },
    { id: 'canvas-draw', name: '白板涂鸦', cat: 'image', desc: 'Canvas 自由绘画' },

    // ===== 趣味娱乐 =====
    { id: 'game2048', name: '2048 游戏', cat: 'fun', desc: '经典数字合并益智游戏', hot: true },
    { id: 'snake', name: '贪吃蛇', cat: 'fun', desc: '经典贪吃蛇游戏', hot: true },
    { id: 'gomoku', name: '五子棋', cat: 'fun', desc: '双人对战五子棋' },
    { id: 'reaction', name: '反应速度测试', cat: 'fun', desc: '点击测反应时间 ms' },
    { id: 'schulte', name: '舒尔特方格', cat: 'fun', desc: '注意力训练 5×5' },
    { id: 'draw', name: '在线白板涂鸦', cat: 'fun', desc: 'Canvas 自由绘画' },
    { id: 'pi-memory', name: 'π 记忆挑战', cat: 'fun', desc: '圆周率数字记忆测试' },
    { id: 'matrix-rain', name: 'Matrix 数字雨', cat: 'fun', desc: '黑客帝国 Canvas 特效' },
    { id: 'rubik-cube', name: '在线魔方', cat: 'fun', desc: '3D CSS 三阶魔方交互' },
    { id: 'bounce-ball', name: '弹跳小球', cat: 'fun', desc: '物理弹跳动画可拖动' },
    { id: 'sudoku', name: '数独', cat: 'fun', desc: '生成 + 求解数独' },
    { id: 'minesweeper', name: '扫雷', cat: 'fun', desc: '经典扫雷游戏' },
    { id: 'memory-cards', name: '记忆卡片', cat: 'fun', desc: '翻牌记忆游戏' },
    { id: 'dice', name: '掷骰子', cat: 'fun', desc: '3D 动画骰子' },
    { id: 'coin-flip', name: '翻硬币', cat: 'fun', desc: '随机决策' },
    { id: 'piano', name: '在线钢琴', cat: 'fun', desc: '可弹奏的钢琴键盘' },
    { id: 'tuner', name: '调音器', cat: 'fun', desc: '乐器调音工具' },
    { id: 'chord', name: '和弦生成器', cat: 'fun', desc: '音乐和弦生成' },
    { id: 'particles', name: '漂浮粒子', cat: 'fun', desc: 'Canvas 粒子动画背景' },
    { id: 'noise', name: '噪声纹理', cat: 'fun', desc: 'Canvas 噪声生成' },
    { id: 'spectrum', name: '频谱可视化', cat: 'fun', desc: '麦克风音频频谱' },
    { id: 'typing-test', name: '打字速度测试', cat: 'fun', desc: '测打字速度与准确率' },
    
    // ===== 其他实用 =====
    { id: 'pomodoro', name: '番茄钟', cat: 'util', desc: '番茄工作法计时器', hot: true },
            { id: 'tts', name: '文字转语音', cat: 'util', desc: 'Web Speech API 朗读', hot: true },
    { id: 'whitenoise', name: '在线白噪音', cat: 'util', desc: '放松背景音生成' },
    { id: 'metronome', name: '节拍器', cat: 'util', desc: '可调 BPM 电子节拍' },
    { id: 'clipboard-view', name: '剪贴板查看', cat: 'util', desc: '读取剪贴板内容' },
    { id: 'screen-info', name: '屏幕信息', cat: 'util', desc: '当前设备屏幕参数' },
    { id: 'danmaku', name: '手持弹幕', cat: 'util', desc: '手机屏幕滚动 LED 弹幕' },
    { id: 'dead-pixel', name: '屏幕坏点检测', cat: 'util', desc: '全屏纯色检测坏点' },
    { id: 'auto-refresh', name: '网页定时刷新', cat: 'util', desc: '设间隔自动刷新网页' },
    { id: 'todo', name: '待办事项', cat: 'util', desc: '本地待办清单管理' },
    { id: 'journal', name: '日记本', cat: 'util', desc: '本地日记记录' },
    { id: 'notes', name: '笔记应用', cat: 'util', desc: '本地笔记管理' },
    { id: 'habit', name: '习惯追踪', cat: 'util', desc: '每日习惯打卡追踪' },
    { id: 'expense', name: '记账本', cat: 'util', desc: '简单记账工具' },
    { id: 'mood', name: '心情追踪', cat: 'util', desc: '每日心情记录' },
    { id: 'water', name: '喝水提醒', cat: 'util', desc: '每日饮水量追踪' },
    { id: 'stand', name: '站立提醒', cat: 'util', desc: '定时站立提醒' },
    { id: 'timer-app', name: '正计时器', cat: 'util', desc: '跑表模式正计时' },
    { id: 'stopwatch-adv', name: '秒表增强', cat: 'util', desc: '分段计次 + 导出' },
    { id: 'countdown-adv', name: '倒计时增强', cat: 'util', desc: '多倒计时 + 提醒' },
    { id: 'bookmark', name: '书签管理', cat: 'util', desc: '管理常用工具书签' },
    { id: 'theme-switch', name: '主题切换', cat: 'util', desc: '亮色/暗色/自动主题' },
    { id: 'lang-switch', name: '语言切换', cat: 'util', desc: '中英文界面切换' },
    { id: 'layout-toggle', name: '布局切换', cat: 'util', desc: '网格/列表布局切换' },
    { id: 'font-switch', name: '字体切换', cat: 'util', desc: '切换界面字体' },
    { id: 'accessibility', name: '无障碍设置', cat: 'util', desc: '字体大小/对比度/减少动画' },
    { id: 'export-config', name: '配置导出', cat: 'util', desc: '导出收藏/历史/设置' },
    { id: 'import-config', name: '配置导入', cat: 'util', desc: '导入收藏/历史/设置' },
    { id: 'feedback', name: '用户反馈', cat: 'util', desc: '提交反馈与建议' },
    { id: 'changelog', name: '更新日志', cat: 'util', desc: '工具更新历史' },
    { id: 'about', name: '关于', cat: 'util', desc: '关于 FreeLLM 工具站' }
  ];

  /* ---------- Deduplicate by id ---------- */
  const seen = new Set();
  const unique = [];
  for (const t of TOOLS) {
    if (!seen.has(t.id)) {
      seen.add(t.id);
      unique.push(t);
    }
  }

  /* ---------- Build category counts ---------- */
  const catCounts = {};
  CATS.forEach(c => { catCounts[c.id] = 0; });
  unique.forEach(t => { catCounts[t.cat] = (catCounts[t.cat] || 0) + 1; });
  CATS.forEach(c => { c.count = catCounts[c.id] || 0; });

  /* ---------- Export ---------- */
  const Tools = {
    cats: CATS,
    all: unique,
    total: unique.length,

    byCat: function (cat) {
      if (cat === 'all') return this.all;
      return this.all.filter(t => t.cat === cat);
    },

    search: function (query) {
      const q = (query || '').trim().toLowerCase();
      if (!q) return this.all;
      return this.all.filter(t =>
        (t.name + ' ' + t.desc + ' ' + t.id).toLowerCase().includes(q)
      );
    },

    get: function (id) {
      return this.all.find(t => t.id === id);
    },

    getToolUrl: function (id) {
      return `/tools/tools/${id}.html`;
    }
  };

  global.Tools = Tools;
})(window);