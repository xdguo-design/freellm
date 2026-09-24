#!/usr/bin/env python3
"""Capture deterministic visual-regression screenshots for the seven primary FreeLLM pages."""

from __future__ import annotations

import contextlib
import http.server
import json
import socket
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visual-regression"

ROUTES = [
    ("home", "/design/free-china-ai-index.html", ".catalog-app"),
    ("models", "/models/", 'body[data-fl-section="models"]'),
    ("skills", "/skills/", ".skills-page"),
    ("tools", "/tools/", ".tools-page"),
    ("workflow", "/skills/lab/", ".skill-lab-page"),
    ("updates", "/logs/", ".daily-log-dashboard"),
    ("about", "/about/", 'body[data-fl-section="about"]'),
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "mobile": {"width": 390, "height": 844},
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextlib.contextmanager
def serve_root():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def measure(page, page_name: str) -> dict:
    return page.evaluate(
        """pageName => {
          const rect = sel => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {x:r.x,y:r.y,width:r.width,height:r.height};
          };
          const visible = el => {
            const s = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
          };
          const rowHeights = sel => {
            const els = Array.from(document.querySelectorAll(sel)).filter(visible).slice(0, 18);
            if (!els.length) return [];
            const items = els.map(el => {
              const r = el.getBoundingClientRect();
              return {top:r.top,height:r.height};
            });
            const firstTop = Math.min(...items.map(i => i.top));
            return items.filter(i => Math.abs(i.top-firstTop) <= 3).map(i => Math.round(i.height*10)/10);
          };
          const selectorByPage = {
            home: '#catalog-offer-rows .offer:not(.hidden)',
            models: '.models-overview-grid > article',
            skills: '#skill-grid .skill-card:not([hidden])',
            tools: '#tool-grid .tool-card:not([hidden])',
            workflow: '.workflow-grid .workflow-card',
            updates: '.log-stat-grid .log-stat-card',
            about: '.stat-row .stat'
          };
          return {
            theme: document.documentElement.dataset.theme || 'light',
            viewport: {width: innerWidth, height: innerHeight},
            scrollWidth: document.documentElement.scrollWidth,
            scrollHeight: document.documentElement.scrollHeight,
            rail: rect('.fl-site-rail'),
            hero: rect('.catalog-hero, .models-overview, .skills-hero, .tools-hero, .lab-hero, .log-hero, body[data-fl-section="about"] > header'),
            legacySkillsHeader: document.querySelector('.skills-header') ? getComputedStyle(document.querySelector('.skills-header')).display : null,
            legacyToolsHeader: document.querySelector('.tools-header') ? getComputedStyle(document.querySelector('.tools-header')).display : null,
            firstRowCardHeights: rowHeights(selectorByPage[pageName]),
            colors: {
              body: getComputedStyle(document.body).color,
              canvas: getComputedStyle(document.documentElement).getPropertyValue('--fl-canvas').trim(),
              ink: getComputedStyle(document.documentElement).getPropertyValue('--fl-ink').trim()
            }
          };
        }""",
        page_name,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with serve_root() as base, sync_playwright() as p:
        browser = p.chromium.launch()
        for viewport_name, viewport in VIEWPORTS.items():
            for theme in ("light", "dark"):
                for page_name, route, ready in ROUTES:
                    page = browser.new_page(viewport=viewport)
                    page.add_init_script("localStorage.setItem('free-ai-index-locale','zh-CN')")
                    if theme == "dark":
                        page.add_init_script("localStorage.setItem('freellm-theme','dark')")
                    else:
                        page.add_init_script("localStorage.removeItem('freellm-theme')")
                    page.goto(base + route, wait_until="domcontentloaded")
                    page.wait_for_selector(ready, timeout=15000)
                    if theme == "dark":
                        page.wait_for_function("document.documentElement.dataset.theme === 'dark'")
                    page.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
                    page.wait_for_timeout(250)
                    name = f"{page_name}-{viewport_name}-{theme}"
                    report[name] = measure(page, page_name)
                    page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
                    page.close()
        browser.close()
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"captured {len(report)} visual states to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
