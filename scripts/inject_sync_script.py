# -*- coding: utf-8 -*-
"""Persist the shared FreeLLM design shell on standalone static pages.

The runtime sync script remains a progressive enhancement; primary navigation,
layout classes and the theme stylesheet are written into HTML at build time.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
SYNC_TAG = '<script src="/js/freellm-sync.js"></script>'
THEME_TAG = '<link rel="stylesheet" href="/css/freellm-pastel-ui.css?v=20260920b">'

TARGETS = {
    'about/index.html': 'about',
    'links/index.html': 'about',
    'privacy/index.html': 'about',
    'terms/index.html': 'about',
    'favorites/index.html': 'home',
    'submit/index.html': 'home',
}


def site_chrome(section):
    items = (
        ('/', '⌂', '首页', 'home'),
        ('/models/', '▣', '模型', 'models'),
        ('/skills/', '✦', 'Skills', 'skills'),
        ('/tools/', '⌘', '工具', 'tools'),
        ('/skills/lab/', '⌁', '工作流', 'workflow'),
        ('/logs/', '◷', '更新', 'logs'),
        ('/about/', 'ⓘ', '关于', 'about'),
    )
    links = ''.join(
        f'<a href="{href}"{" aria-current=\"page\"" if key == section else ""}>'
        f'<span class="fl-site-nav-icon" aria-hidden="true">{icon}</span><span>{label}</span></a>'
        for href, icon, label, key in items
    )
    return (
        '<aside class="fl-site-rail" aria-label="FreeLLM 主导航">'
        '<a class="fl-site-brand" href="/"><span class="fl-site-brand-mark" aria-hidden="true">AI</span>'
        '<span class="fl-site-brand-copy"><strong>FreeLLM</strong><small>让 AI 更自由地被使用</small></span></a>'
        f'<nav class="fl-site-nav">{links}</nav>'
        '<div class="fl-site-rail-note"><span>好的 AI 资源</span><br>让更多人真正受益 ♡</div></aside>'
        '<div class="fl-site-ribbon"><span class="fl-site-ribbon-title">FREE AI INDEX / 免费 AI 资源导航</span>'
        '<span class="fl-site-ribbon-actions"><a href="/favorites/">我的收藏</a><a href="/skills/">Skills 实测 ↗</a></span></div>'
    )


def stamp(page, section):
    page = re.sub(
        r'<html(?![^>]*\bclass=)([^>]*)>',
        r'<html class="fl-pastel-ui"\1>',
        page,
        count=1,
        flags=re.I,
    )
    page = re.sub(
        r'<html([^>]*\bclass=")([^"]*)(")',
        lambda m: f'<html{m.group(1)}{m.group(2)}{" " if m.group(2) else ""}fl-pastel-ui{m.group(3)}'
        if 'fl-pastel-ui' not in m.group(2).split() else m.group(0),
        page,
        count=1,
        flags=re.I,
    )
    body = re.search(r'<body([^>]*)>', page, flags=re.I)
    if body:
        attrs = body.group(1)
        if 'class="' in attrs:
            attrs = re.sub(
                r'class="([^"]*)"',
                lambda m: f'class="{m.group(1)} fl-ui-v2"' if 'fl-ui-v2' not in m.group(1).split() else m.group(0),
                attrs,
                count=1,
            )
        else:
            attrs += ' class="fl-ui-v2"'
        if 'data-fl-section=' not in attrs:
            attrs += f' data-fl-section="{section}"'
        page = page[:body.start()] + f'<body{attrs}>' + page[body.end():]

    if 'freellm-pastel-ui.css' not in page and '</head>' in page:
        page = page.replace('</head>', THEME_TAG + '\n</head>', 1)
    elif 'freellm-pastel-ui.css' in page:
        page = re.sub(
            r'<link rel="stylesheet" href="/css/freellm-pastel-ui\.css(?:\?[^"]*)?">',
            THEME_TAG,
            page,
            count=1,
        )

    if 'class="fl-site-rail"' not in page:
        page = re.sub(
            r'(<body[^>]*>)',
            lambda m: m.group(1) + '\n' + site_chrome(section),
            page,
            count=1,
            flags=re.I,
        )
    if 'freellm-sync.js' not in page and '</body>' in page:
        page = page.replace('</body>', SYNC_TAG + '</body>', 1)
    return page


changed = skipped = 0
for relative, section in TARGETS.items():
    path = ROOT / relative
    if not path.is_file():
        print('skip (missing):', relative)
        continue
    original = path.read_text(encoding='utf-8')
    updated = stamp(original, section)
    if updated == original:
        skipped += 1
        continue
    path.write_text(updated, encoding='utf-8')
    changed += 1

print(f'stamped: {changed}, current: {skipped}')
