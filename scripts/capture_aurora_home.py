#!/usr/bin/env python3
"""Capture Aurora homepage screenshots for phase-one visual review."""

from __future__ import annotations

import contextlib
import http.server
import json
import socket
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "aurora-home"

VIEWPORTS = {
    "desktop-1440": {"width": 1440, "height": 1000},
    "tablet-1024": {"width": 1024, "height": 900},
    "mobile-390": {"width": 390, "height": 844},
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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with serve_root() as base, sync_playwright() as p:
        browser = p.chromium.launch()
        for name, viewport in VIEWPORTS.items():
            page = browser.new_page(viewport=viewport, locale="zh-CN")
            page.goto(f"{base}/design/free-china-ai-index.html", wait_until="domcontentloaded")
            page.wait_for_selector(".catalog-hero")
            page.wait_for_selector(".today-latest")
            page.wait_for_selector("#catalog-offer-rows .offer")
            page.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
            page.wait_for_timeout(250)

            report[name] = page.evaluate(
                """() => ({
                    width: innerWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    themeClass: document.body.className,
                    hero: document.querySelector('.catalog-hero')?.getBoundingClientRect().toJSON(),
                    latest: document.querySelector('.today-latest')?.getBoundingClientRect().toJSON()
                })"""
            )
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
            page.close()
        browser.close()

    (OUT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"captured {len(report)} Aurora homepage states")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
