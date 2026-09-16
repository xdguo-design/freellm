# -*- coding: utf-8 -*-
"""工具页自动化测试（Playwright）。

用法（先启动本地静态服务，如 python -m http.server 8901）：
  python scripts/test_tool_pages.py                     # 全量加载巡检：控制台错误 / 资源404 / 页面异常
  python scripts/test_tool_pages.py --smoke             # 追加代表性工具的功能冒烟测试
  python scripts/test_tool_pages.py --base http://127.0.0.1:8901 --report logs/tool-test-report.json

巡检项：
  1. 主文档 HTTP 状态 < 400
  2. 页面 JS 异常（pageerror）
  3. 控制台 error 级消息
  4. 子资源加载失败 / 404
  5. 骨架完整：.tool 容器存在且 h1 非空
"""
import argparse
import io
import json
import pathlib
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 功能冒烟样例：(id, 输入, 期望输出包含, 自定义动作, 断言类型)
# 自定义动作: 'click:按钮文字' 先点按钮再读输出；输入为 None 表示不填输入框
# 断言类型: 'output'(readonly 输出框) | 'canvas'(出现 canvas/svg) | 'stats'(.stat 统计卡)
#          | 'outputdiv'(.output div 文本) | 'table'(页内首个表格文本)
SMOKE = [
    ('base64', 'hello', 'aGVsbG8=', None, 'output'),
    ('url-encode', 'a b/c?', 'a%20b%2Fc%3F', None, 'output'),
    ('md5', 'abc', '900150983cd24fb0d6963f7d28e17f72', None, 'output'),
    ('caesar', 'abc', 'def', None, 'output'),
    ('mixed-encode', 'hello', 'aGVsbG8=', None, 'output'),
    ('word-count', 'hello world\n第二行', None, None, 'stats'),
    ('uuid', None, None, 'click:生成', 'output'),
    ('qrcode', 'https://freellm.top', None, None, 'canvas'),
    ('json', '{"a":1}', '"a"', None, 'output'),
    ('diff', 'abc\nxyz', None, None, 'outputdiv'),
    ('color-convert', '#1744E8', 'rgb(23, 68, 232)', None, 'table'),
]


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


def smoke(page, base):
    results = []
    for tid, text, expect, action, assert_kind in SMOKE:
        item = {'id': tid, 'ok': True, 'detail': ''}
        try:
            page.goto('%s/tools/tools/%s.html' % (base, tid), wait_until='load', timeout=30000)
            page.wait_for_timeout(200)
            if action and action.startswith('click:'):
                label = action.split(':', 1)[1]
                page.get_by_role('button', name=label).first.click()
                page.wait_for_timeout(300)
            else:
                ta = page.locator('textarea:not([readonly])').first
                if ta.count() == 0:
                    ta = page.locator('input[type=text], input:not([type])').first
                ta.fill(text)
                page.wait_for_timeout(400)
            if assert_kind == 'canvas':
                n = page.locator('canvas, svg').count()
                item['detail'] = 'canvas/svg=%d' % n
                item['ok'] = n > 0
            elif assert_kind == 'stats':
                n = page.locator('.stat b').count()
                vals = page.locator('.stat b').all_text_contents()
                item['detail'] = 'stat=%d %s' % (n, vals[:3])
                item['ok'] = n >= 3 and any(v.strip() not in ('', '0', '—') for v in vals)
            elif assert_kind == 'outputdiv':
                val = page.locator('.output').first.text_content() or ''
                item['detail'] = val[:120]
                item['ok'] = bool(val.strip())
            elif assert_kind == 'table':
                val = page.locator('table').first.text_content() or ''
                item['detail'] = val[:120]
                item['ok'] = bool(expect and expect in val)
            else:
                out = page.locator('textarea[readonly]').first
                val = out.input_value() if out.count() else ''
                item['detail'] = (val or '')[:120]
                if expect:
                    ok = expect in val
                else:
                    ok = bool(val and val.strip() and '⚠' not in val)
                item['ok'] = bool(ok)
        except Exception as exc:  # noqa: BLE001
            item['ok'] = False
            item['detail'] = '异常: %s' % exc
        results.append(item)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://127.0.0.1:8901')
    ap.add_argument('--report', default='')
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='只测前 N 个页面（调试用）')
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    ids = registry_ids()
    if args.limit:
        ids = ids[:args.limit]
    print('待测页面: %d' % len(ids))
    t0 = time.time()
    with sync_playwright() as p:
        browser = None
        for kw in ({}, {'channel': 'msedge'}, {'channel': 'chrome'}):
            try:
                browser = p.chromium.launch(**kw)
                break
            except Exception as exc:  # noqa: BLE001
                print('启动浏览器失败(%s)，尝试下一通道' % (kw or 'default'))
                last = exc
        if browser is None:
            print('无法启动任何浏览器: %s' % last)
            sys.exit(2)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()

        # crawl_all 内部用匿名 lambda 绑定/解绑不干净，这里逐页绑定具名收集器
        failures = {}
        for tid in ids:
            collected = {'page': [], 'console': [], 'res': []}
            on_err = lambda e: collected['page'].append('pageerror: %s' % e)  # noqa: E731
            on_console = lambda m: collected['console'].append(m.text) if m.type == 'error' else None  # noqa: E731
            on_resp = lambda r: collected['res'].append('%s -> %d' % (r.url, r.status)) if r.status >= 400 else None  # noqa: E731

            def on_reqfail(r):
                # 页面切换导航会中断上一页尚未完成的外链请求（ERR_ABORTED），属巡检噪声
                if 'ERR_ABORTED' in str(r.failure) and not r.url.startswith(args.base):
                    return
                collected['res'].append('%s -> %s' % (r.url, r.failure))

            page.on('pageerror', on_err)
            page.on('console', on_console)
            page.on('response', on_resp)
            page.on('requestfailed', on_reqfail)
            try:
                resp = page.goto('%s/tools/tools/%s.html' % (args.base, tid), wait_until='load', timeout=30000)
                if resp and resp.status >= 400:
                    collected['page'].append('文档状态 %d' % resp.status)
                page.wait_for_timeout(240)
                has_tool = page.locator('.tool').count() > 0
                h1 = (page.locator('.tool h1').first.text_content() or '').strip() if has_tool else ''
                if not has_tool:
                    collected['page'].append('缺少 .tool 骨架')
                elif not h1:
                    collected['page'].append('h1 为空')
                errors = collected['page'] + \
                    ['资源异常: ' + b for b in collected['res'] if 'data:' not in b] + \
                    ['console: ' + c for c in collected['console']]
                if errors:
                    failures[tid] = errors[:10]
            except Exception as exc:  # noqa: BLE001
                failures[tid] = ['导航失败: %s' % exc]
            finally:
                page.remove_listener('pageerror', on_err)
                page.remove_listener('console', on_console)
                page.remove_listener('response', on_resp)
                page.remove_listener('requestfailed', on_reqfail)

        smoke_results = smoke(page, args.base) if args.smoke else []

        browser.close()

    dt = time.time() - t0
    print('\n===== 加载巡检 =====')
    print('通过 %d / %d，耗时 %.1fs' % (len(ids) - len(failures), len(ids), dt))
    for tid, errs in failures.items():
        print('  ✗ %s: %s' % (tid, ' | '.join(errs)))

    if args.smoke:
        print('\n===== 功能冒烟 =====')
        for r in smoke_results:
            print('  %s %s  %s' % ('✓' if r['ok'] else '✗', r['id'], r['detail'][:100]))

    if args.report:
        report = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base': args.base,
            'total': len(ids),
            'load_failures': failures,
            'smoke': smoke_results,
        }
        path = ROOT / args.report
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print('\n报告已写入 %s' % path)

    sys.exit(1 if failures or any(not r['ok'] for r in smoke_results) else 0)


if __name__ == '__main__':
    main()
