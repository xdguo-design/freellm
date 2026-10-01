#!/usr/bin/env python3
"""Create a local snapshot of freellm.net's free/trial model directory."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = "https://freellm.net/models/"
ROOT = Path(__file__).resolve().parents[1]


class ModelRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.row: dict | None = None
        self.cells: list[str] = []
        self.cell_parts: list[str] = []
        self.model_href = ""
        self.in_model_link = False
        self.model_link_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "tr" and "model-row" in (values.get("class") or "").split():
            self.row = values
            self.cells = []
            self.model_href = ""
            self.model_link_parts = []
        elif self.row is not None and tag == "td":
            self.cell_parts = []
        elif self.row is not None and tag == "a" and "model-link" in (values.get("class") or "").split():
            self.model_href = values.get("href") or ""
            self.in_model_link = True

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value or self.row is None:
            return
        self.cell_parts.append(value)
        if self.in_model_link:
            self.model_link_parts.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_model_link:
            self.in_model_link = False
        elif tag == "td" and self.row is not None:
            self.cells.append(" ".join(self.cell_parts).strip())
            self.cell_parts = []
        elif tag == "tr" and self.row is not None:
            self.row["_cells"] = self.cells
            self.row["_model"] = " ".join(self.model_link_parts).strip()
            self.row["_model_href"] = self.model_href
            self.rows.append(self.row)
            self.row = None


def released_date(raw: str | None) -> str:
    try:
        return datetime.fromtimestamp(int(raw or "0") / 1000, timezone.utc).date().isoformat()
    except (ValueError, OverflowError, OSError):
        return ""


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def parse_models(html: str) -> list[dict]:
    parser = ModelRowParser()
    parser.feed(html)
    models: list[dict] = []
    for row in parser.rows:
        cells = row.get("_cells", [])
        provider = row.get("data-provider") or (cells[0] if cells else "Unknown provider")
        model = row.get("data-name") or row.get("_model") or (cells[1] if len(cells) > 1 else "")
        if not model:
            continue
        provider_id = row.get("data-provider-slug") or slug(provider)
        href = row.get("_model_href") or ""
        model_slug = href.rstrip("/").split("/")[-1] if href else slug(model)
        directory_href = f"https://freellm.net{href}" if href.startswith("/") else href
        status = cells[8].strip().lower() if len(cells) > 8 else "unknown"
        try:
            score = int(row.get("data-score") or (cells[2] if len(cells) > 2 else "0"))
        except ValueError:
            score = 0
        models.append({
            "id": f"{provider_id}/{model_slug}",
            "providerId": provider_id,
            "provider": provider,
            "model": model,
            "context": row.get("data-context") or "",
            "modality": [item.strip() for item in (row.get("data-modality") or "").split(",") if item.strip()],
            "rateLimit": cells[5] if len(cells) > 5 else "",
            "released": released_date(row.get("data-released")),
            "usageActivity": cells[7] if len(cells) > 7 else "",
            "status": "online" if status == "online" else status,
            "score": score,
            "isFree": row.get("data-free") == "1",
            "noCard": row.get("data-nocard") == "1",
            "noPhone": row.get("data-nophone") == "1",
            "verified": row.get("data-verified") == "1",
            "tierType": row.get("data-tier-type") or "",
            "description": row.get("data-description") or "",
            "bestFor": row.get("data-bestfor") or "",
            "directoryHref": directory_href,
            "canonicalModelId": f"{provider_id}/{model_slug}",
            "sourceKind": "freellm.net",
        })
    return models


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/freellm-net-models.json")
    parser.add_argument("--url", default=SOURCE_URL)
    args = parser.parse_args()

    request = Request(args.url, headers={"User-Agent": "FreeLLM model catalog snapshot/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", "replace")
    models = parse_models(html)
    if len(models) < 100:
        raise SystemExit(f"Expected at least 100 model rows from {args.url}; got {len(models)}")

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": args.url,
        "fetchedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "count": len(models),
        "models": models,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(models)} model records from {args.url} to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
