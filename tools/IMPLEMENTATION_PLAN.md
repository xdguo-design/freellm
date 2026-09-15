# FreeLLM 工具实现计划

## 总体策略
- **分批实现**：先简单后复杂
- **完整功能**：每个工具包含输入→输出+复制/下载+历史记录+收藏
- **统一模板**：所有工具遵循统一的代码结构

## 工具分类统计

| 分类 | 数量 | 优先级 |
|------|------|--------|
| 编码加密 (encode) | 16 | 第一批 |
| 文本工具 (text) | 19 | 第一批 |
| 计算转换 (calc) | 34 | 第一批 |
| 速查参考 (ref) | 21 | 第一批 |
| 格式化 (format) | 27 | 第二批 |
| 生成器 (generate) | 17 | 第二批 |
| CSS工具 (css) | 17 | 第二批 |
| 日期时间 (datetime) | 24 | 第二批 |
| 开发工具 (dev) | 22 | 第二批 |
| 安全加密 (crypto) | 15 | 第三批 |
| 图片工具 (image) | 26 | 第三批 |
| 趣味娱乐 (fun) | 23 | 第三批 |
| 其他实用 (util) | 35 | 第三批 |

## 第一批：简单纯前端工具（60个）

### 编码加密 (16个)
1. base64 - Base64 编解码
2. url-encode - URL 编解码
3. md5 - MD5 哈希
4. sha - SHA 哈希
5. html-entity - HTML 实体编解码
6. unicode - Unicode 转换
7. caesar - 凯撒密码
8. rot13 - ROT13/ROT47
9. base32 - Base32 编码
10. base58 - Base58 编码
11. base85 - Base85 编码
12. file-hex - 文件与 Hex 互转
13. aes - AES 加解密
14. file-hash - 文件哈希
15. hmac - HMAC 哈希
16. gzip - Gzip 压缩

### 文本工具 (19个)
1. case-convert - 大小写转换
2. camel-convert - 变量名转换
3. full-half - 全角半角转换
4. word-count - 字数统计
5. text-clean - 文本清理
6. slug - URL Slug 生成
7. html-filter - HTML 标签过滤
8. bionic-reading - Bionic Reading
9. figlet - ASCII 艺术字
10. regex - 正则表达式测试
11. diff - 文本对比
12. simp-trad - 简繁体转换
13. pinyin - 汉字转拼音
14. text-similarity - 文本相似度
15. keyword-extract - 关键词提取
16. spell-check - 拼写检查
17. fanyi - 翻译助手
18. regex-visual - 正则可视化
19. markdown - Markdown 编辑器

### 计算转换 (34个)
1. radix-convert - 进制转换
2. color-convert - 颜色转换
3. unit-convert - 单位换算器
4. chmod - Chmod 计算器
5. bmi - BMI 计算器
6. storage - 存储容量换算
7. temp-converter - 温度单位换算
8. length-converter - 长度单位换算
9. weight-converter - 重量单位换算
10. area-converter - 面积单位换算
11. volume-converter - 体积单位换算
12. speed-converter - 速度单位换算
13. pressure-converter - 压力单位换算
14. energy-converter - 能量单位换算
15. power-converter - 功率单位换算
16. frequency-converter - 频率单位换算
17. angle-converter - 角度单位换算
18. density-converter - 密度单位换算
19. time-converter - 时间单位换算
20. data-transfer - 数据传输计算
21. pixel-density - 像素密度计算
22. aspect-ratio - 宽高比计算器
23. tip - 小费计算器
24. loan - 贷款计算器
25. compound - 复利计算器
26. calorie - 卡路里计算器
27. retirement - 退休年龄计算器
28. calculator - 在线计算器
29. ieee754 - IEEE 754 转换
30. endian - 大小端转换
31. color-shades - 色阶生成器
32. trig - 三角函数计算
33. bit-reverse - 二进制位操作

### 速查参考 (21个)
1. http-status - HTTP 状态码
2. ascii - ASCII 对照表
3. emoji - Emoji 大全
4. keycode - 键盘键位码
5. html-chars - HTML 特殊字符
6. http-headers - HTTP 请求头参考
7. content-type - Content-Type 大全
8. ports - 常见端口速查
9. regex-cheat - 正则大全
10. operator - 运算符优先级
11. linux-cmd - Linux 命令速查
12. symbols - 特殊符号大全
13. css-props - CSS 属性速查
14. js-api - JS API 速查
15. html-tags - HTML 标签速查
16. mysql-syntax - MySQL 语法速查
17. git-commands - Git 命令速查
18. docker-commands - Docker 命令速查
19. unicode-table - Unicode 字符表
20. color-names - 颜色名称对照
21. font-stack - 字体栈推荐

## 第二批：中等复杂度工具（70个）

### 格式化 (27个)
1. json - JSON 格式化
2. sql-formatter - SQL 格式化
3. code-formatter - 代码格式化
4. code-highlight - 代码着色高亮
5. csv-json - CSV ↔ JSON
6. json-yaml - JSON ↔ YAML
7. json-xml - JSON ↔ XML
8. html2md - HTML 转 Markdown
9. md2html - Markdown 转 HTML
10. minify - 代码压缩 Minify
11. json2class - JSON 转实体类
12. json-tree - JSON Tree 查看
13. json-merge - JSON 合并
14. json-sort - JSON 排序
15. url-parser - URL 参数解析
16. nginx-formatter - Nginx 格式化
17. xml-format - XML 格式化
18. yaml-format - YAML 格式化
19. csv-format - CSV 格式化
20. md-format - Markdown 格式化
21. excel-convert - Excel ↔ JSON/CSV
22. json-schema - JSON Schema 校验
23. jsonpath - JSONPath 查询
24. jmespath - JMESPath 查询
25. table2csv - 表格转 CSV
26. text2table - 文本转表格
27. csv2md - CSV ↔ Markdown 表格

### 生成器 (17个)
1. uuid - UUID 生成器
2. password - 密码生成器
3. random-string - 随机字符串
4. lorem - Lorem Ipsum
5. mock-data - Mock 数据生成
6. favicon-maker - Favicon 制作
7. gitignore - .gitignore 生成
8. og-meta - OG Meta 标签
9. shield - Shield Badge
10. random-color - 随机颜色
11. random-decision - 随机决策
12. lorem-pixel - 占位图片
13. qrcode-scan - 二维码扫描
14. barcode - 条形码生成
15. barcode-scan - 条形码识别

### CSS工具 (17个)
1. css-gradient - CSS 渐变生成器
2. css-shadow - CSS 阴影生成器
3. css-border - CSS 圆角生成器
4. css-animation - CSS 动画生成器
5. css-glass - CSS 毛玻璃
6. css-loader - CSS Loading
7. css-unit - CSS 单位换算
8. svg-shape - SVG 形状生成
9. font-preview - 字体预览器
10. css-flexbox - CSS Flexbox 可视化
11. css-grid - CSS Grid 可视化
12. css-clip-path - CSS Clip-path 生成
13. css-filter - CSS Filter 生成
14. css-contrast - 对比度检查器
15. css-variables - CSS 变量生成
16. css-reset - CSS Reset 生成
17. color-palette - 调色板生成器

### 日期时间 (24个)
1. timestamp - 时间戳转换
2. cron - Cron 表达式
3. date-calc - 日期计算器
4. countdown - 倒计时器
5. stopwatch - 在线秒表
6. age-calc - 年龄计算器
7. lunar-calendar - 公历农历转换
8. almanac - 黄历查询
9. alarm - 在线闹钟
10. world-time - 世界时间表
11. leap-year - 闰年计算器
12. workday - 工作日计算
13. week-number - 周数查询
14. calendar - 在线万年历
15. bazi - 八字五行
16. festival - 传统节日查询
17. solar-term - 二十四节气
18. zodiac - 生肖星座
19. auspicious - 择吉选日
20. timer - 正计时器
21. timezone - 时区转换
22. meeting-time - 会议时间换算
23. quarter - 季度计算器
24. countdown-multi - 多倒计时

### 开发工具 (22个)
1. jwt - JWT 解析
2. mermaid - Mermaid 编辑器
3. curl-converter - Curl 转代码
4. xpath - XPath 测试
5. code2img - 代码转图片
6. ua-parser - UA 解析
7. magic-bytes - 文件格式识别
8. unzip - ZIP 解压查看
9. websocket-test - WebSocket 测试
10. csr-gen - CSR 证书生成
11. html-preview - HTML 实时预览
12. css-preview - CSS 实时预览
13. js-sandbox - JS 沙箱执行
14. exif-viewer - EXIF 查看器
15. image-compress - 图片压缩
16. video2gif - 视频转 GIF
17. audio-record - 录音机
18. http-builder - HTTP 请求构建
19. api-test - API 测试工具
20. snippets - 代码片段管理
21. color-contrast - 颜色对比度
22. svg-editor - SVG 在线编辑

## 第三批：复杂工具（70个）

### 安全加密 (15个)
1. rsa - RSA 密钥生成
2. rsa-encrypt - RSA 加解密
3. ecc - ECC 密钥生成
4. hybrid-encrypt - 混合加密
5. totp - 一次性密码 TOTP
6. x509 - X.509 证书解析
7. ssh-key - SSH 密钥生成
8. password-check - 密码强度检测
9. hash-identify - Hash 类型识别
10. pbkdf2 - PBKDF2 派生
11. scrypt - Scrypt 派生
12. ecdh - ECDH 密钥交换
13. ecdsa - ECDSA 数字签名
14. cert-viewer - 证书查看器

### 图片工具 (26个)
1. image-resize - 图片尺寸调整
2. image-crop - 图片自由裁剪
3. image-watermark - 图片加水印
4. image-filter - 图片滤镜
5. gif-maker - GIF 制作
6. image-rotate - 图片旋转翻转
7. image-grid - 九宫格切图
8. image-picker - 图片取色器
9. colorblind - 颜色盲模拟
10. gif-frame - GIF 转帧
11. image2pdf - 图片转 PDF
12. image-format - 图片格式转换
13. bg-remove - 去背景（颜色版）
14. image-target-kb - 压到指定 KB
15. image-stitch - 图片拼接
16. image-poster - 海报制作
17. image-id-photo - 证件照制作
18. image-template - 模板切图
19. image-mirror - 图片镜像翻转
20. collage - 图片拼图
21. image-workspace - 连续处理工作台
22. sticker - 贴纸生成
23. avatar-maker - 头像生成
24. screenshot - 屏幕截图
25. screen-record - 在线录屏
26. canvas-draw - 白板涂鸦

### 趣味娱乐 (23个)
1. game2048 - 2048 游戏
2. snake - 贪吃蛇
3. gomoku - 五子棋
4. reaction - 反应速度测试
5. schulte - 舒尔特方格
6. draw - 在线白板涂鸦
7. pi-memory - π 记忆挑战
8. matrix-rain - Matrix 数字雨
9. rubik-cube - 在线魔方
10. bounce-ball - 弹跳小球
11. sudoku - 数独
12. minesweeper - 扫雷
13. memory-cards - 记忆卡片
14. dice - 掷骰子
15. coin-flip - 翻硬币
16. piano - 在线钢琴
17. tuner - 调音器
18. chord - 和弦生成器
19. particles - 漂浮粒子
20. noise - 噪声纹理
21. spectrum - 频谱可视化
22. typing-test - 打字速度测试
23. pomodoro - 番茄钟

### 其他实用 (35个)
1. tts - 文字转语音
2. whitenoise - 在线白噪音
3. metronome - 节拍器
4. clipboard-view - 剪贴板查看
5. screen-info - 屏幕信息
6. danmaku - 手持弹幕
7. dead-pixel - 屏幕坏点检测
8. auto-refresh - 网页定时刷新
9. todo - 待办事项
10. journal - 日记本
11. notes - 笔记应用
12. habit - 习惯追踪
13. expense - 记账本
14. mood - 心情追踪
15. water - 喝水提醒
16. stand - 站立提醒
17. timer-app - 正计时器
18. stopwatch-adv - 秒表增强
19. countdown-adv - 倒计时增强
20. bookmark - 书签管理
21. theme-switch - 主题切换
22. lang-switch - 语言切换
23. layout-toggle - 布局切换
24. font-switch - 字体切换
25. accessibility - 无障碍设置
26. export-config - 配置导出
27. import-config - 配置导入
28. feedback - 用户反馈
29. changelog - 更新日志
30. about - 关于

## 实现模板

每个工具HTML文件结构：
```html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>工具名 · FreeLLM</title>
<link rel="stylesheet" href="/tools/css/tool.css">
</head>
<body>
<div id="app"></div>
<script src="/tools/js/tool-common.js"></script>
<script src="/js/freellm-sync.js"></script>
<script>
(function () {
  var T = ToolCommon;
  var app = T.head('工具名', '工具描述', 'tool-id');
  
  // 工具实现代码
  
})();
</script>
</body>
</html>
```

## 开始实现

现在开始实现第一批工具（简单纯前端工具）。
