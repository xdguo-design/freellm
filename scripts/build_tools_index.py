# -*- coding: utf-8 -*-
"""Build the tools landing page with a real static first paint.

The JavaScript registry remains the single source of truth. This builder extracts
its publishable metadata and writes the total, category tabs and the first batch
of direct-link cards into tools/index.html. JavaScript may enhance/filter the
same directory after load, but the HTML source is useful without JavaScript.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_JS = ROOT / "tools" / "js" / "tools.js"
INDEX_HTML = ROOT / "tools" / "index.html"
START = "<!-- STATIC-TOOLS:START -->"
END = "<!-- STATIC-TOOLS:END -->"
TAB_START = "<!-- STATIC-TOOL-TABS:START -->"
TAB_END = "<!-- STATIC-TOOL-TABS:END -->"

CAT_RE = re.compile(
    r"\{\s*id:\s*'([^']+)'\s*,\s*label:\s*'([^']+)'\s*,\s*cls:\s*'([^']+)'"
)
TOOL_RE = re.compile(
    r"\{\s*id:\s*'([^']+)'\s*,\s*name:\s*'((?:\\.|[^'])*)'\s*,"
    r"\s*cat:\s*'([^']+)'\s*,\s*desc:\s*'((?:\\.|[^'])*)'"
    r"(?:\s*,\s*hot:\s*true)?\s*\}"
)


def _unescape_js_text(value: str) -> str:
    return (
        value.replace("\\'", "'")
        .replace("\\\\", "\\")
        .replace("\\n", "\n")
        .replace("\\r", "\r")
        .replace("\\t", "\t")
    )


def load_registry() -> tuple[list[dict], list[dict]]:
    source = TOOLS_JS.read_text(encoding="utf-8")
    cat_start = source.index("const CATS = [")
    cat_end = source.index("];", cat_start)
    tool_start = source.index("const TOOLS = [")
    tool_end = source.index("];", tool_start)
    cats = [
        {"id": match.group(1), "label": match.group(2), "cls": match.group(3)}
        for match in CAT_RE.finditer(source[cat_start:cat_end])
    ]
    tools = []
    for match in TOOL_RE.finditer(source[tool_start:tool_end]):
        raw = match.group(0)
        tools.append(
            {
                "id": match.group(1),
                "name": _unescape_js_text(match.group(2)),
                "cat": match.group(3),
                "desc": _unescape_js_text(match.group(4)),
                "hot": bool(re.search(r"hot:\s*true", raw)),
            }
        )
    if not tools:
        raise SystemExit("No tools parsed from tools/js/tools.js")
    seen: set[str] = set()
    duplicates: list[str] = []
    for tool in tools:
        tool_id = tool["id"]
        if tool_id in seen and tool_id not in duplicates:
            duplicates.append(tool_id)
        seen.add(tool_id)
    if duplicates:
        raise SystemExit("Duplicate tool ids in tools/js/tools.js: " + ", ".join(duplicates))
    counts: dict[str, int] = {}
    for tool in tools:
        counts[tool["cat"]] = counts.get(tool["cat"], 0) + 1
    for cat in cats:
        cat["count"] = counts.get(cat["id"], 0)
    return cats, tools


def render_tabs(cats: list[dict], total: int) -> str:
    chunks = [
        f'<button class="tool-category-tab is-active" type="button" data-static-tool-cat="all">'
        f'<span>全部</span><small>{total}</small></button>'
    ]
    for cat in cats:
        if not cat["count"]:
            continue
        chunks.append(
            f'<button class="tool-category-tab" type="button" data-static-tool-cat="{html.escape(cat["id"])}">'
            f'<span>{html.escape(cat["label"])}</span><small>{cat["count"]}</small></button>'
        )
    return TAB_START + "".join(chunks) + TAB_END


def render_cards(cats: list[dict], tools: list[dict], limit: int) -> str:
    cat_map = {cat["id"]: cat for cat in cats}
    cards = []
    for tool in tools[:limit]:
        cat = cat_map.get(tool["cat"], {"label": tool["cat"], "cls": ""})
        url = f'/tools/tools/{tool["id"]}.html'
        cards.append(
            f'<a class="tool-card static-tool-card" href="{html.escape(url)}" '
            f'data-tool-id="{html.escape(tool["id"])}" data-tool-cat="{html.escape(tool["cat"])}">'
            f'<div class="tool-card-top"><span class="tool-category {html.escape(cat["cls"])}">'
            f'{html.escape(cat["label"])}</span>'
            + ('<span class="tool-hot">热门</span>' if tool["hot"] else '')
            + '</div>'
            f'<h2>{html.escape(tool["name"])}</h2><p>{html.escape(tool["desc"])}</p></a>'
        )
    return START + "".join(cards) + END


def build(limit: int = 24, check: bool = False) -> bool:
    cats, tools = load_registry()
    source = INDEX_HTML.read_text(encoding="utf-8")
    updated = source
    updated = re.sub(
        r'(<strong id="tool-total">)\d+(</strong>)',
        rf'\g<1>{len(tools)}\g<2>',
        updated,
        count=1,
    )
    updated = re.sub(
        r'(<span id="tool-count" class="tools-count">).*?(</span>)',
        rf'\g<1>显示 {min(limit, len(tools))} / {len(tools)}\g<2>',
        updated,
        count=1,
        flags=re.S,
    )
    tabs = render_tabs(cats, len(tools))
    if TAB_START in updated:
        updated = re.sub(re.escape(TAB_START) + r".*?" + re.escape(TAB_END), lambda _: tabs, updated, count=1, flags=re.S)
    else:
        updated = updated.replace('<div class="tool-category-tabs" id="tool-category-tabs"></div>',
                                  f'<div class="tool-category-tabs" id="tool-category-tabs">{tabs}</div>', 1)
    cards = render_cards(cats, tools, limit)
    if START in updated:
        updated = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: cards, updated, count=1, flags=re.S)
    else:
        updated = updated.replace('<section id="tool-grid" class="tool-grid" aria-live="polite"></section>',
                                  f'<section id="tool-grid" class="tool-grid" aria-live="polite">{cards}</section>', 1)

    if check:
        if updated != source:
            print("stale: tools/index.html does not contain current static tool registry")
            return False
        print(f"current: tools/index.html ({len(tools)} tools)")
        return True

    INDEX_HTML.write_text(updated, encoding="utf-8")
    print(f"built: tools/index.html ({len(tools)} tools, {min(limit, len(tools))} first-paint cards)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return 0 if build(limit=max(1, args.limit), check=args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
