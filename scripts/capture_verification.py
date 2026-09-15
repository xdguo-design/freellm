"""Capture verification screenshots of the restyled site (local only, not deployed)."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8123"
OUT = Path("gui-test-screenshots/editorial-restyle")
OUT.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("home", "/design/free-china-ai-index.html"),
    ("models", "/models/"),
    ("models-all", "/models/all/"),
    ("category-free-quota", "/category/free-quota/"),
    ("offer-groq", "/offers/groq-free/"),
    ("guide-free-llm", "/guides/free-llm/"),
    ("guide-openai-alt", "/guides/free-openai-api-alternatives/"),
    ("guide-open-weights", "/guides/open-weight-models/"),
    ("providers", "/providers/"),
    ("provider-groq", "/providers/groq/"),
    ("logs", "/logs/"),
    ("skills", "/skills/"),
    ("skills-lab", "/skills/lab/"),
    ("about", "/about/"),
    ("model-center", "/models/center/"),
]


def snap(page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


def main() -> int:
    # pick one real model-aggregate slug from the built output
    model_dirs = sorted(Path("models").glob("*/index.html"))
    agg = next((d.parent.name for d in model_dirs if "claude" in d.parent.name), None)
    pages = list(PAGES)
    if agg:
        pages.append(("model-aggregate", f"/models/{agg}/"))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        ctx = browser.new_context(viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        for name, path in pages:
            try:
                page.goto(BASE + path, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_load_state("load", timeout=15000)
            except Exception as error:  # fonts may stall load; DOM is enough
                print("load warn:", name, type(error).__name__)
            snap(page, f"desk-{name}")
        # dark mode spot checks
        for name, path in [("models", "/models/"), ("offer-groq", "/offers/groq-free/"), ("logs", "/logs/")]:
            page.goto(BASE + path, wait_until="domcontentloaded", timeout=20000)
            page.evaluate("document.documentElement.dataset.theme = 'dark'")
            snap(page, f"dark-{name}")
        # mobile spot checks
        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mpage = mobile.new_page()
        for name, path in [("home", "/design/free-china-ai-index.html"), ("models", "/models/"), ("offer-groq", "/offers/groq-free/"), ("logs", "/logs/")]:
            try:
                mpage.goto(BASE + path, wait_until="domcontentloaded", timeout=20000)
                mpage.wait_for_load_state("load", timeout=15000)
            except Exception as error:
                print("load warn:", name, type(error).__name__)
            snap(mpage, f"mob-{name}")
        # catalog table area on models/all (scrolled)
        page.goto(BASE + "/models/all/", wait_until="domcontentloaded", timeout=20000)
        page.evaluate("window.scrollTo(0, 1400)")
        snap(page, "desk-models-all-table")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
