#!/usr/bin/env python3
"""Fail CI when the seven primary pages drift outside the approved prototype geometry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "artifacts" / "visual-regression" / "report.json"

DESKTOP = {
    "home": {
        "rail.x": (-1, 1), "rail.width": (182, 186),
        "topbar.x": (224, 232), "topbar.y": (9, 17), "topbar.height": (36, 44),
        "hero.x": (212, 220), "hero.y": (62, 70), "hero.height": (244, 256),
        "primaryContent.x": (212, 220), "primaryContent.width": (1196, 1204),
        "featured.x": (212, 220), "featured.width": (1196, 1204),
    },
    "models": {
        "rail.x": (-1, 1), "rail.width": (180, 184),
        "topbar.x": (180, 184), "topbar.y": (-1, 1), "topbar.height": (56, 60),
        "hero.x": (180, 184), "hero.y": (56, 60), "hero.height": (312, 322),
        "primaryContent.x": (196, 204), "primaryContent.width": (1226, 1234),
        "featured.x": (196, 204), "featured.width": (996, 1006),
        "sideRail.x": (1211, 1219), "sideRail.width": (211, 219),
    },
    "skills": {
        "rail.x": (-1, 1), "rail.width": (180, 184),
        "topbar.x": (180, 184), "topbar.y": (9, 17), "topbar.height": (56, 60),
        "hero.x": (204, 212), "hero.y": (58, 66), "hero.height": (248, 258),
        "featured.x": (204, 212), "featured.width": (1208, 1216),
    },
    "tools": {
        "rail.x": (-1, 1), "rail.width": (180, 184),
        "topbar.x": (180, 184), "topbar.y": (9, 17), "topbar.height": (56, 60),
        "hero.x": (204, 212), "hero.y": (58, 66), "hero.height": (271, 281),
        "featured.x": (204, 212), "featured.width": (1208, 1216),
    },
    "workflow": {
        "rail.x": (-1, 1), "rail.width": (180, 184),
        "topbar.x": (180, 184), "topbar.y": (9, 17), "topbar.height": (56, 60),
        "hero.x": (204, 212), "hero.y": (58, 66), "hero.height": (221, 231),
        "primaryContent.x": (204, 212), "primaryContent.width": (968, 976),
        "featured.x": (204, 212), "featured.width": (968, 976),
        "sideRail.x": (1190, 1198), "sideRail.width": (198, 206),
    },
    "updates": {
        "rail.x": (-1, 1), "rail.width": (180, 184),
        "topbar.x": (180, 184), "topbar.y": (9, 17), "topbar.height": (56, 60),
        "hero.x": (205, 213), "hero.y": (59, 67), "hero.height": (224, 234),
        "featured.x": (205, 213), "featured.width": (1206, 1214),
    },
    "about": {
        "rail.x": (-1, 1), "rail.width": (180, 184),
        "topbar.x": (180, 184), "topbar.y": (9, 17), "topbar.height": (56, 60),
        "hero.x": (176, 184), "hero.y": (66, 74), "hero.height": (315, 325),
        "primaryContent.x": (206, 214), "primaryContent.width": (1182, 1190),
        "featured.x": (206, 214), "featured.width": (1182, 1190),
    },
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
        for field, bounds in rules.items():
            check_range(errors, state, item, field, bounds)

    if errors:
        print("REFERENCE_GEOMETRY_GATE=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("REFERENCE_GEOMETRY_GATE=PASS")
    print("7 v4 desktop boards + tablet/mobile horizontal-overflow checks are within tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
