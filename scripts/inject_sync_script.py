# -*- coding: utf-8 -*-
"""把全站同步脚本注入所有静态页面（幂等：已注入的跳过）"""
import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
TAG = '<script src="/js/freellm-sync.js"></script>'
DIRS = ['models', 'providers', 'skills', 'guides', 'category', 'logs', 'about', 'privacy', 'terms', 'design']

changed = skipped = 0
for d in DIRS:
    for p in (ROOT / d).rglob('index.html'):
        html = p.read_text(encoding='utf-8')
        if 'freellm-sync.js' in html:
            skipped += 1
            continue
        if '</body>' not in html:
            print('skip (no </body>):', p.relative_to(ROOT))
            continue
        html = html.rreplace('</body>', TAG + '</body>', 1) if hasattr(str, 'rreplace') else html[::-1].replace('</body>'[::-1], (TAG + '</body>')[::-1], 1)[::-1]
        p.write_text(html, encoding='utf-8')
        changed += 1

print(f'injected: {changed}, already present: {skipped}')