# -*- coding: utf-8 -*-
"""工具页定义注册表：各分类模块调用 d() 注册 {id: 定义}"""
DEFS = {}


def d(tid, title, desc, js, head='', scripts=''):
    assert tid not in DEFS, f'duplicate tool def: {tid}'
    DEFS[tid] = {'id': tid, 'title': title, 'desc': desc, 'js': js, 'head': head, 'scripts': scripts}
