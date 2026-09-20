# -*- coding: utf-8 -*-
"""批量生成 tools/tools/*.html 工具页面。
   用法: python scripts/build_tool_pages.py
   - 从 tools/js/tools.js 的 TOOLS 注册表解析全部工具 id
   - 与 scripts/tool_defs/ 中各分类模块注册的定义做双向校验
   - 缺定义/多定义直接报错，防止页面与注册表漂移
"""
import io, json, re, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

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
