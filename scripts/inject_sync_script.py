# -*- coding: utf-8 -*-
"""把全站同步脚本注入所有静态页面（幂等：已注入的跳过）"""
import re
import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
TAG = '<script src="/js/freellm-sync.js?v=20261012-fast-navigation"></script>'
SITE_NAVIGATION_VERSION = '20261012-fast-navigation'
SKIP_DIRS = {'.git', '.vercel', 'data', 'docs', 'node_modules', '.venv', 'tests', 'venv'}

changed = skipped = 0
for p in ROOT.rglob('*.html'):
    relative = p.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in relative.parts) or relative.parts[:2] == ('design', 'prototypes'):
        continue
    html = p.read_text(encoding='utf-8')
    html, nav_replaced = re.subn(
        r'(<script\b[^>]*\bsrc="/js/site-navigation\.js)(?:\?[^"]*)?(">)',
        rf'\g<1>?v={SITE_NAVIGATION_VERSION}\g<2>',
        html,
    )
    html, sync_replaced = re.subn(
        r'(<script\b[^>]*\bsrc="/js/freellm-sync\.js)(?:\?[^\"]*)?(")',
        r'\g<1>?v=20261012-fast-navigation\g<2>',
        html,
    )
    if nav_replaced or sync_replaced:
        p.write_text(html, encoding='utf-8')
        changed += 1
        continue
    if 'freellm-sync.js' in html:
        skipped += 1
        continue
    if '</body>' not in html:
        continue
    html = html.replace('</body>', TAG + '</body>')
    p.write_text(html, encoding='utf-8')
    changed += 1

print(f'injected: {changed}, already present: {skipped}')
