# -*- coding: utf-8 -*-
"""批量生成 tools/tools/*.html 工具页面。
   用法: python scripts/build_tool_pages.py
   - 从 tools/js/tools.js 的 TOOLS 注册表解析全部工具 id
   - 与 scripts/tool_defs/ 中各分类模块注册的定义做双向校验
   - 缺定义/多定义直接报错，防止页面与注册表漂移
"""
import html, io, json, re, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

STATIC_TABS_START = '<!-- STATIC-TOOL-TABS:START -->'
STATIC_TABS_END = '<!-- STATIC-TOOL-TABS:END -->'
STATIC_TOOLS_START = '<!-- STATIC-TOOLS:START -->'
STATIC_TOOLS_END = '<!-- STATIC-TOOLS:END -->'

SITE_CHROME = '''<aside class="fl-site-rail" aria-label="FreeLLM 主导航">
  <a class="fl-site-brand" href="/"><span class="fl-site-brand-mark" aria-hidden="true">AI</span><span class="fl-site-brand-copy"><strong>FreeLLM</strong><small>让 AI 更自由地被使用</small></span></a>
  <nav class="fl-site-nav">
    <a href="/"><span class="fl-site-nav-icon" aria-hidden="true">⌂</span><span>首页</span></a>
    <a href="/models/"><span class="fl-site-nav-icon" aria-hidden="true">▣</span><span>模型</span></a>
    <a href="/skills/"><span class="fl-site-nav-icon" aria-hidden="true">✦</span><span>Skills</span></a>
    <a href="/tools/" aria-current="page"><span class="fl-site-nav-icon" aria-hidden="true">⌘</span><span>工具</span></a>
    <a href="/skills/lab/"><span class="fl-site-nav-icon" aria-hidden="true">⌁</span><span>工作流</span></a>
    <a href="/logs/"><span class="fl-site-nav-icon" aria-hidden="true">◷</span><span>更新</span></a>
    <a href="/about/"><span class="fl-site-nav-icon" aria-hidden="true">ⓘ</span><span>关于</span></a>
  </nav>
  <div class="fl-site-rail-note"><span>好的 AI 资源</span><br>让更多人真正受益 ♡</div>
</aside>
<div class="fl-site-ribbon">
  <span class="fl-site-ribbon-title">FREE AI INDEX / 在线工具</span>
  <span class="fl-site-ribbon-actions"><a href="/favorites/">我的收藏</a><a href="/skills/">Skills 实测 ↗</a><button id="theme-toggle" type="button" aria-label="切换深色模式">◐</button></span>
</div>'''

from tool_defs import registry  # noqa: E402
import tool_defs.encode as _e  # noqa: F401,E402
import tool_defs.crypto as _c  # noqa: F401,E402
import tool_defs.fmt as _f  # noqa: F401,E402
import tool_defs.generate as _g  # noqa: F401,E402
import tool_defs.csstools as _cs  # noqa: F401,E402
import tool_defs.text as _t  # noqa: F401,E402
import tool_defs.calc as _ca  # noqa: F401,E402
import tool_defs.datetime as _dt  # noqa: F401,E402
import tool_defs.ref as _r  # noqa: F401,E402
import tool_defs.dev as _dv  # noqa: F401,E402
import tool_defs.image as _im  # noqa: F401,E402
import tool_defs.fun as _fn  # noqa: F401,E402
import tool_defs.util as _ut  # noqa: F401,E402

TEMPLATE = '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<link rel="icon" href="data:,">
<title>@TITLE@ · FreeLLM</title>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-JMK4R9519M"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-JMK4R9519M');
</script>
<link rel="stylesheet" href="/tools/css/tool.css">
<link rel="stylesheet" href="/css/freellm-pastel-ui.css">
@HEAD@
</head>
<body>
<div id="app"></div>
<script src="/tools/js/tool-common.js"></script>
<script src="/tools/js/lib-crypto.js"></script>
<script src="/tools/js/lib-format.js"></script>
<script src="/tools/js/lib-utils.js"></script>
@SCRIPTS@
<script src="/js/freellm-sync.js"></script>
<script>
(function () {
'use strict';
var T = ToolCommon, LC = window.LC, LF = window.LibFormat, LU = window.LibU;
var app = T.head('@TITLE@', '@DESC@', '@ID@');
@BODY@
})();
</script>
<script type="application/json" id="tool-source">@SOURCE@</script>
<script>ToolCommon.sourcePanel();</script>
</body>
</html>
'''


def registry_entries():
    """Parse the browser registry and apply the exact same first-id-wins rule as tools.js."""
    src = (ROOT / 'tools' / 'js' / 'tools.js').read_text(encoding='utf-8')
    start = src.index('const TOOLS = [')
    end = src.index('\n  ];', start)
    block = src[start:end]
    pattern = re.compile(
        r"\{\s*id:\s*'([^']+)',\s*name:\s*'([^']+)',\s*cat:\s*'([^']+)',\s*desc:\s*'((?:\\\\.|[^'])*)'(?:,\s*hot:\s*(true|false))?\s*\}"
    )
    entries, seen = [], set()
    for match in pattern.finditer(block):
        tool_id, name, category, desc, hot = match.groups()
        if tool_id in seen:
            continue
        seen.add(tool_id)
        entries.append({
            'id': tool_id,
            'name': name,
            'cat': category,
            'desc': desc.replace('\\\\', '\\'),
            'hot': hot == 'true',
        })
    return entries


def category_entries():
    src = (ROOT / 'tools' / 'js' / 'tools.js').read_text(encoding='utf-8')
    start = src.index('const CATS = [')
    end = src.index('];', start)
    block = src[start:end]
    return [
        {'id': match.group(1), 'label': match.group(2), 'cls': match.group(3)}
        for match in re.finditer(r"\{\s*id:\s*'([^']+)',\s*label:\s*'([^']+)',\s*cls:\s*'([^']+)'\s*\}", block)
    ]


def _static_tool_card(tool, categories):
    category = categories.get(tool['cat'], {'label': tool['cat'], 'cls': ''})
    hot = '<span class="tool-hot">热门</span>' if tool['hot'] else ''
    tool_id = html.escape(tool['id'], quote=True)
    return (
        f'<a class="tool-card static-tool-card" href="/tools/?tool={tool_id}" '
        f'aria-label="{html.escape(tool["name"], quote=True)}" data-tool-id="{tool_id}">'
        f'<div class="tool-card-top"><span class="tool-category {html.escape(category["cls"], quote=True)}">'
        f'{html.escape(category["label"])}</span>{hot}</div>'
        f'<h2>{html.escape(tool["name"])}</h2><p>{html.escape(tool["desc"])}</p></a>'
    )


def update_tools_index():
    """Persist real tool counts and cards in HTML so first paint never reports 0 tools."""
    path = ROOT / 'tools' / 'index.html'
    page = path.read_text(encoding='utf-8')
    entries = registry_entries()
    categories_list = category_entries()
    categories = {item['id']: item for item in categories_list}
    counts = {item['id']: 0 for item in categories_list}
    for tool in entries:
        counts[tool['cat']] = counts.get(tool['cat'], 0) + 1

    page = re.sub(r'<html(?![^>]*\bclass=)([^>]*)>', r'<html class="fl-pastel-ui"\1>', page, count=1, flags=re.I)
    page = re.sub(
        r'<html([^>]*\bclass=")([^"]*)(")',
        lambda match: f'<html{match.group(1)}{match.group(2)}{" " if match.group(2) else ""}fl-pastel-ui{match.group(3)}'
        if 'fl-pastel-ui' not in match.group(2).split() else match.group(0),
        page, count=1, flags=re.I,
    )
    body = re.search(r'<body([^>]*)>', page, flags=re.I)
    if body:
        attrs = body.group(1)
        if 'class="' in attrs:
            attrs = re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1)} fl-ui-v2"' if 'fl-ui-v2' not in m.group(1).split() else m.group(0), attrs, count=1)
        else:
            attrs += ' class="fl-ui-v2"'
        if 'data-fl-section=' not in attrs:
            attrs += ' data-fl-section="tools"'
        page = page[:body.start()] + f'<body{attrs}>' + page[body.end():]

    theme = '<link rel="stylesheet" href="/css/freellm-pastel-ui.css?v=20260920b">'
    if 'freellm-pastel-ui.css' not in page:
        page = page.replace('</head>', theme + '\n</head>', 1)
    else:
        page = re.sub(r'<link rel="stylesheet" href="/css/freellm-pastel-ui\.css(?:\?[^"]*)?">', theme, page, count=1)

    page = re.sub(r'\s*<header class="tools-header">.*?</header>', '\n', page, count=1, flags=re.S)
    if 'class="fl-site-rail"' not in page:
        page = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + '\n' + SITE_CHROME, page, count=1, flags=re.I)

    total = len(entries)
    page = re.sub(r'(<strong id="tool-total">)[^<]*(</strong>)', rf'\g<1>{total}\g<2>', page, count=1)
    page = re.sub(r'(<span id="tool-count" class="tools-count">)[^<]*(</span>)', rf'\g<1>显示 {total} / {total}\g<2>', page, count=1)

    tabs = [f'<button class="tool-category-tab is-active" type="button"><span>全部</span><small>{total}</small></button>']
    for item in categories_list:
        count = counts.get(item['id'], 0)
        if count:
            tabs.append(
                f'<button class="tool-category-tab" type="button" data-static-category="{html.escape(item["id"], quote=True)}">'
                f'<span>{html.escape(item["label"])}</span><small>{count}</small></button>'
            )
    tabs_markup = STATIC_TABS_START + ''.join(tabs) + STATIC_TABS_END
    cards_markup = STATIC_TOOLS_START + ''.join(_static_tool_card(tool, categories) for tool in entries) + STATIC_TOOLS_END

    tabs_pattern = re.escape(STATIC_TABS_START) + r'.*?' + re.escape(STATIC_TABS_END)
    if re.search(tabs_pattern, page, flags=re.S):
        page = re.sub(tabs_pattern, tabs_markup, page, count=1, flags=re.S)
    else:
        page = re.sub(r'<div class="tool-category-tabs" id="tool-category-tabs">.*?</div>', f'<div class="tool-category-tabs" id="tool-category-tabs">{tabs_markup}</div>', page, count=1, flags=re.S)

    cards_pattern = re.escape(STATIC_TOOLS_START) + r'.*?' + re.escape(STATIC_TOOLS_END)
    if re.search(cards_pattern, page, flags=re.S):
        page = re.sub(cards_pattern, cards_markup, page, count=1, flags=re.S)
    else:
        page = re.sub(r'<section id="tool-grid" class="tool-grid" aria-live="polite">.*?</section>', f'<section id="tool-grid" class="tool-grid" aria-live="polite">{cards_markup}</section>', page, count=1, flags=re.S)

    path.write_text(page, encoding='utf-8')
    return total


def registry_ids():
    src = (ROOT / 'tools' / 'js' / 'tools.js').read_text(encoding='utf-8')
    start = src.index('const TOOLS = [')
    end = src.index('];', start)
    ids = re.findall(r"id:\s*'([^']+)'", src[start:end])
    seen, uniq = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq


def render(defn):
    source = {
        'id': defn['id'],
        'title': defn['title'],
        'desc': defn['desc'],
        'scripts': defn['scripts'],
        'code': defn['js'].strip(),
    }
    # < 转义为 \u003c，防止 code 中出现 </script> 提前闭合载荷标签
    source_json = json.dumps(source, ensure_ascii=False).replace('<', '\\u003c')
    html = TEMPLATE
    for k, v in [
        ('@TITLE@', defn['title']),
        ('@DESC@', defn['desc'].replace("'", "\\'")),
        ('@ID@', defn['id']),
        ('@HEAD@', defn['head']),
        ('@SCRIPTS@', defn['scripts']),
        ('@SOURCE@', source_json),
        ('@BODY@', defn['js'].strip()),
    ]:
        html = html.replace(k, v)
    return html


def main():
    total = update_tools_index()
    print(f'静态工具首页: {total} 个工具')
    ids = registry_ids()
    defs = registry.DEFS
    partial = '--partial' in sys.argv
    missing = [i for i in ids if i not in defs]
    extra = [i for i in defs if i not in ids]
    if extra:
        print('注册表不存在的多余定义 (%d): %s' % (len(extra), ', '.join(extra)))
        sys.exit(1)
    if missing and not partial:
        print('缺少定义的工具 (%d): %s' % (len(missing), ', '.join(missing)))
        sys.exit(1)
    if missing:
        print('[partial] 暂缺 %d 个定义' % len(missing))

    outdir = ROOT / 'tools' / 'tools'
    outdir.mkdir(parents=True, exist_ok=True)
    stale = {p.stem for p in outdir.glob('*.html')} - set(ids)
    done = [i for i in ids if i in defs]
    for tid in done:
        (outdir / f'{tid}.html').write_text(render(defs[tid]), encoding='utf-8')
    print(f'生成 {len(done)}/{len(ids)} 个工具页 → tools/tools/')
    if stale:
        print('陈旧页面（注册表中已不存在）:', ', '.join(sorted(stale)))


if __name__ == '__main__':
    main()
