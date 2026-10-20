#!/usr/bin/env python3
"""Review indexed editorial pages for possible thin-content issues.

This report does not imply Google's AdSense rejection reason.
"""
from __future__ import annotations
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from datetime import date
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {"script", "style", "noscript", "nav", "header", "footer", "aside", "svg", "button"}
VOID = {"img", "input", "link", "meta", "br", "hr", "source", "wbr", "area", "base"}


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.body = []
        self.main = []
        self.has_main = False
        self.source_hosts = set()

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.tags.append(tag)
        if tag == "main":
            self.has_main = True
        if tag == "a" and not set(self.tags).intersection(IGNORED):
            href = dict(attrs).get("href") or ""
            url = urlparse(href)
            if url.scheme == "https" and url.hostname not in {"freellm.top", "www.freellm.top"}:
                self.source_hosts.add(url.hostname)

    def handle_endtag(self, tag):
        for i in range(len(self.tags) - 1, -1, -1):
            if self.tags[i] == tag:
                del self.tags[i:]
                break

    def handle_data(self, data):
        if "body" not in self.tags or set(self.tags).intersection(IGNORED):
            return
        value = re.sub(r"\s+", " ", data).strip()
        if value:
            self.body.append(value)
            if "main" in self.tags:
                self.main.append(value)


def _date_age(value: object, today: date) -> int | None:
    try:
        return (today - date.fromisoformat(str(value)[:10])).days
    except (TypeError, ValueError):
        return None


def _audit_source_data(root: Path, indexed_paths: set[str] | None = None, today: date | None = None) -> dict:
    """Inventory source-data quality signals without treating heuristics as policy."""
    today = today or date.today()
    indexed_paths = indexed_paths or set()
    result = {
        "method": "Editorial review signals only; not Google's internal AdSense decision logic",
        "offers": {
            "total": 0,
            "statuses": {},
            "expired": [],
            "expiredSitemapLeaks": [],
            "nonIndexableSitemapLeaks": [],
            "staleVerificationReview": [],
            "missingChineseWhy": [],
            "missingChineseFreeSummary": [],
            "missingOfficialEvidence": [],
        },
        "models": {
            "total": 0,
            "statuses": {},
            "staleObservationReview": [],
            "missingOfficialSource": [],
        },
    }
    offers_path = root / "data" / "offers.json"
    if offers_path.is_file():
        try:
            offers = json.loads(offers_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            offers = []
        if isinstance(offers, list):
            result["offers"]["total"] = len(offers)
            for offer in offers:
                if not isinstance(offer, dict):
                    continue
                offer_id = str(offer.get("id") or "").strip()
                status = str(offer.get("status") or "missing")
                result["offers"]["statuses"][status] = result["offers"]["statuses"].get(status, 0) + 1
                path = f"/offers/{offer_id}/" if offer_id else ""
                if status == "expired":
                    result["offers"]["expired"].append(offer_id)
                if status in {"expired", "needs_review"} and path in indexed_paths:
                    result["offers"]["nonIndexableSitemapLeaks"].append(offer_id)
                    if status == "expired":
                        result["offers"]["expiredSitemapLeaks"].append(offer_id)
                age = _date_age(offer.get("lastVerifiedAt"), today)
                if status == "verified" and age is not None and age > 30:
                    result["offers"]["staleVerificationReview"].append({"id": offer_id, "daysSinceVerification": age})
                why = str(offer.get("why") or "")
                if why and not re.search(r"[\u3400-\u9fff]", why) and not str(offer.get("whyZh") or "").strip():
                    result["offers"]["missingChineseWhy"].append(offer_id)
                summary = str(offer.get("freeSummary") or "")
                if summary and not re.search(r"[\u3400-\u9fff]", summary) and not str(offer.get("freeSummaryZh") or "").strip():
                    result["offers"]["missingChineseFreeSummary"].append(offer_id)
                has_evidence = bool(
                    str(offer.get("evidence") or "").strip()
                    or offer.get("sourceUrls")
                    or offer.get("links")
                    or str(offer.get("register") or "").strip()
                )
                if not has_evidence:
                    result["offers"]["missingOfficialEvidence"].append(offer_id)

    models_path = root / "data" / "models.json"
    if models_path.is_file():
        try:
            models = json.loads(models_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            models = []
        if isinstance(models, list):
            result["models"]["total"] = len(models)
            for model in models:
                if not isinstance(model, dict):
                    continue
                model_id = str(model.get("id") or model.get("model") or "")
                status = str(model.get("status") or "missing")
                result["models"]["statuses"][status] = result["models"]["statuses"].get(status, 0) + 1
                age = _date_age(model.get("lastSeenAt") or model.get("lastVerifiedAt"), today)
                if age is not None and age > 30:
                    result["models"]["staleObservationReview"].append({"id": model_id, "daysSinceObservation": age})
                if not str(model.get("sourceUrl") or "").strip():
                    result["models"]["missingOfficialSource"].append(model_id)
    return result


def audit(root: Path):
    pages = []
    seen = set()
    for sitemap in sorted(root.glob("sitemap-*.xml")):
        for url in re.findall(r"<loc>\s*(https://freellm\.top/[^<]*)</loc>", sitemap.read_text(encoding="utf-8")):
            path = urlparse(url).path
            if path in seen:
                continue
            seen.add(path)
            file = root / (path.strip("/") + "/index.html") if path != "/" else root / "design/free-china-ai-index.html"
            if not file.is_file():
                pages.append({"path": path, "error": "missing_sitemap_target"})
                continue
            html = file.read_text(encoding="utf-8", errors="replace")
            parser = VisibleText()
            parser.feed(html)
            text = " ".join(parser.main if parser.has_main else parser.body)
            flags = []
            if not parser.has_main:
                flags.append("semantic_main_review")
            if len(text) < 300 and path not in {"/about/", "/contact/", "/privacy/", "/terms/", "/submit/"}:
                flags.append("thin_editorial_text_review")
            if path.startswith(("/guides/", "/offers/")) and not parser.source_hosts:
                flags.append("external_evidence_review")
            pages.append({"path": path, "editorialChars": len(text), "sourceHostCount": len(parser.source_hosts), "flags": flags})
    source_data = _audit_source_data(root, seen)
    return {
        "method": "Heuristic editorial audit, not AdSense approval evidence",
        "total": len(pages),
        "rows": pages,
        "sourceData": source_data,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=".tmp/adsense-editorial-inventory.json")
    args = ap.parse_args()
    result = audit(ROOT)
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for row in result["rows"]:
        for flag in row.get("flags", []):
            counts[flag] = counts.get(flag, 0) + 1
    print(json.dumps({"pages": result["total"], "reviewSignals": counts}, ensure_ascii=False))
    return int(any(row.get("error") for row in result["rows"]))


if __name__ == "__main__":
    raise SystemExit(main())
