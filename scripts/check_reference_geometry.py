#!/usr/bin/env python3
"""Fail CI when the seven primary pages drift outside the approved prototype geometry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "artifacts" / "visual-regression" / "report.json"

DESKTOP = {
    "home": {
        "hero.x": (202, 214), "hero.y": (58, 66), "hero.height": (284, 300),
        "primaryContent.x": (202, 214),
    },
    "models": {
        "hero.x": (178, 182), "hero.y": (-1, 1), "hero.height": (315, 325),
        "primaryContent.x": (200, 206), "primaryContent.width": (955, 990),
        "featured.x": (200, 206), "sideRail.x": (1184, 1202), "sideRail.width": (198, 206),
    },
    "skills": {
        "hero.x": (202, 214), "hero.y": (58, 66), "hero.height": (245, 265),
    },
    "tools": {
        "hero.x": (202, 214), "hero.y": (58, 66), "hero.height": (268, 284),
    },
    "workflow": {
        "hero.x": (204, 212), "hero.y": (58, 66), "hero.height": (220, 232),
        "primaryContent.x": (204, 212), "primaryContent.width": (955, 990),
        "featured.x": (204, 212), "sideRail.x": (1186, 1204), "sideRail.width": (198, 206),
    },
    "updates": {
        "hero.x": (204, 214), "hero.y": (58, 67), "hero.height": (220, 240),
    },
    "about": {
        "hero.x": (178, 182), "hero.y": (-1, 1), "hero.height": (315, 325),
        "primaryContent.x": (206, 216),
    },
}

COMMON_DESKTOP = {
    "rail.x": (-1, 1),
    "rail.width": (178, 182),
    "topbar.x": (220, 228),
    "topbar.y": (10, 16),
    "topbar.height": (36, 44),
}


def dig(item: dict, path: str):
    value = item
    for key in path.split("."):
        if value is None or key not in value:
            return None
        value = value[key]
    return value


def check_range(errors: list[str], state: str, item: dict, field: str, bounds: tuple[float, float]) -> None:
    value = dig(item, field)
    low, high = bounds
    if value is None:
        errors.append(f"{state}: missing {field}")
    elif not (low <= float(value) <= high):
        errors.append(f"{state}: {field}={value:.2f}, expected {low}..{high}")


def main() -> int:
    if not REPORT.exists():
        raise SystemExit(f"missing visual report: {REPORT}")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    errors: list[str] = []

    # No primary page may produce horizontal scroll at any acceptance viewport.
    for state, item in report.items():
        viewport = item.get("viewport") or {}
        width = float(viewport.get("width") or 0)
        scroll = float(item.get("scrollWidth") or 0)
        if width and scroll > width + 2:
            errors.append(f"{state}: horizontal overflow {scroll:.1f}px > viewport {width:.1f}px")

    # Desktop proportions are calibrated from the supplied 1448px-wide prototype boards.
    for page, rules in DESKTOP.items():
        state = f"{page}-desktop-aurora"
        item = report.get(state)
        if not item:
            errors.append(f"missing visual state {state}")
            continue
        for field, bounds in COMMON_DESKTOP.items():
            check_range(errors, state, item, field, bounds)
        for field, bounds in rules.items():
            check_range(errors, state, item, field, bounds)

    if errors:
        print("REFERENCE_GEOMETRY_GATE=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("REFERENCE_GEOMETRY_GATE=PASS")
    print("7 desktop boards + tablet/mobile horizontal-overflow checks are within tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
