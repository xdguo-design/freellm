# -*- coding: utf-8 -*-
"""生成工具站数据文件：农历表 / 拼音字典 / 繁简映射 / 节假日"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from lunardate import LunarDate
from pypinyin import pinyin as py_pinyin, Style
import zhconv

OUT = 'tools/data'

# ---------- 1. 农历压缩表 (1900-2100) ----------
# 自定义编码: data = (leapMonth << 17) | (leap30?0x10000:0) | monthBits
# monthBits bit i = 第 i+1 个农历月有 30 天; leapMonth=0 表示无闰月
def find_leap(year):
    return LunarDate.leap_month_for_year(year) or 0

def year_data(year):
    leap = find_leap(year)
    bits = (leap << 17)
    if leap:
        ld = LunarDate(year, leap, 1, is_leap_month=True)
        import calendar
        nxt = LunarDate(year, leap, 1, is_leap_month=False) if leap < 12 else LunarDate(year + 1, 1, 1)
        leap_days = (nxt.toSolarDate() - ld.toSolarDate()).days
        if leap_days == 30:
            bits |= 0x10000
    for m in range(1, 13):
        start = LunarDate(year, m, 1)
        if m < 12:
            nxtm = LunarDate(year, m + 1, 1, is_leap_month=False)
        else:
            nxtm = LunarDate(year + 1, 1, 1)
        days = (nxtm.toSolarDate() - start.toSolarDate()).days
        if days == 30:
            bits |= (1 << (m - 1))
    return bits

table = [year_data(y) for y in range(1900, 2099)]
with open(f'{OUT}/lunar-table.json', 'w', encoding='utf-8') as f:
    json.dump({'from': 1900, 'to': 2098, 'newYear': '1900-01-31', 'table': table}, f, separators=(',', ':'))
print('lunar-table.json:', len(table), 'years, first spring festival 1900-01-31')

# 校验几个已知日期
checks = {'2026-02-17': (1, 1), '2025-01-29': (1, 1), '2024-02-10': (1, 1), '2026-09-25': (8, 15)}
for solar, (lm, ld) in checks.items():
    y, m, d = map(int, solar.split('-'))
    real = LunarDate.fromSolarDate(y, m, d)
    assert (real.month, real.day) == (lm, ld), solar
print('lunar checks passed:', checks)

# ---------- 2. 节假日 (2026-2027, 以农历/公历节日为准, 调休以官方公告为准) ----------
def solar_to_lunar_str(y, m, d):
    r = LunarDate.fromSolarDate(y, m, d)
    return (r.month, r.day)

def lunar_to_solar(y, lm, ld, leap=False):
    return LunarDate(y, lm, ld, is_leap_month=leap).toSolarDate()

def qingming(y):
    c = 4.81
    day = int((y % 100) * 0.2422 + c) - int((y % 100) / 4)
    return f'{y}-04-{day:02d}'

def build_year(y):
    hd = {}
    def add(ds, name):
        hd[ds] = {'name': name, 'type': 'holiday'}
    add(f'{y}-01-01', '元旦')
    ny = lunar_to_solar(y, 1, 1)          # 春节
    cxi = lunar_to_solar(y, 1, 1)          # 除夕: 春节前一天
    from datetime import date, timedelta
    cxi = (date(ny.year, ny.month, ny.day) - timedelta(days=1))
    add(cxi.strftime('%Y-%m-%d'), '春节（除夕）')
    for i in range(0, 6):
        dd = date(ny.year, ny.month, ny.day) + timedelta(days=i)
        add(dd.strftime('%Y-%m-%d'), '春节')
    add(qingming(y), '清明节')
    add(f'{y}-05-01', '劳动节')
    add(f'{y}-05-02', '劳动节')
    add(f'{y}-05-03', '劳动节')
    dw = lunar_to_solar(y, 5, 5)
    add(dw.strftime('%Y-%m-%d'), '端午节')
    zq = lunar_to_solar(y, 7, 7)
    hd[zq.strftime('%Y-%m-%d')] = {'name': '七夕节', 'type': 'festival'}
    zqj = lunar_to_solar(y, 8, 15)
    hd[zqj.strftime('%Y-%m-%d')] = {'name': '中秋节', 'type': 'festival'}
    for i in (-1, 0, 1):
        dd = date(zqj.year, zqj.month, zqj.day) + timedelta(days=i)
        hd[dd.strftime('%Y-%m-%d')] = {'name': '中秋节', 'type': 'holiday'}
    gy = lunar_to_solar(y, 9, 9)
    hd[gy.strftime('%Y-%m-%d')] = {'name': '重阳节', 'type': 'festival'}
    for i in range(3):
        add(f'{y}-10-{i+1:02d}', '国庆节')
    hd['_note'] = '法定节假日放假与调休安排以国务院办公厅公告为准；festival 类型为传统节日（不放假）'
    return dict(sorted(hd.items()))

for y in (2026, 2027, 2028):
    with open(f'{OUT}/holidays/{y}.json', 'w', encoding='utf-8') as f:
        json.dump(build_year(y), f, ensure_ascii=False, indent=1)
print('holidays 2026-2028 generated')

# ---------- 3. 拼音字典 (常用 CJK 字) ----------
pmap = {}
for cp in range(0x4E00, 0x9FA6):
    ch = chr(cp)
    r = py_pinyin(ch, style=Style.TONE, heteronym=False, errors='ignore')
    if r and r[0] and r[0][0] and r[0][0] != ch:
        pmap[ch] = r[0][0]
with open(f'{OUT}/pinyin.json', 'w', encoding='utf-8') as f:
    json.dump(pmap, f, ensure_ascii=False, separators=(',', ':'))
print('pinyin.json:', len(pmap), 'chars')

# ---------- 4. 繁简映射 (双向, 字级) ----------
s2t, t2s = {}, {}
for cp in range(0x4E00, 0x9FA6):
    ch = chr(cp)
    t = zhconv.convert(ch, 'zh-hant')
    s = zhconv.convert(ch, 'zh-hans')
    if t != ch:
        s2t[ch] = t
    if s != ch:
        t2s[ch] = s
with open(f'{OUT}/s2t.json', 'w', encoding='utf-8') as f:
    json.dump({'s2t': s2t, 't2s': t2s}, f, ensure_ascii=False, separators=(',', ':'))
print('s2t.json:', len(s2t), 's->t,', len(t2s), 't->s')
