#!/usr/bin/env python3
"""Generate JSON-LD structured data (Product / SoftwareApplication / FAQPage) from data/offers.json.

Reads the verified offer catalog and emits <head>-ready JSON-LD snippets into
seo/schema/. Ratings are intentionally omitted: the catalog has no user review
data and fabricated aggregateRating values violate Google's structured-data
spam policy (and this site's own "no fabricated scores" rule).

Usage: python scripts/generate_schema.py [--out seo/schema]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OFFERS_PATH = ROOT / "data" / "offers.json"

SITE_URL = "https://freellm.top"

# pricingModel values that genuinely cost nothing up front
FREE_PRICING = {
    "permanent_free", "free_rate_limited", "free_credits",
    "monthly_quota", "daily_quota", "limited_time_free", "trial",
}

SOFTWARE_TYPES = {"free_ide", "desktop_ai_app", "open_weights"}


def build_product_node(offer: dict) -> dict:
    """Map one offer record to a schema.org Product or SoftwareApplication node."""
    offer_id = offer.get("id", "unknown")
    product_type = offer.get("productType", "api")
    is_software = product_type in SOFTWARE_TYPES

    node = {
        "@type": "SoftwareApplication" if is_software else "Product",
        "@id": f"{SITE_URL}/offers/{offer_id}#product",
        "name": offer.get("name") or offer.get("title") or offer_id,
        "description": offer.get("why") or offer.get("freeSummaryEn") or offer.get("freeSummary") or "",
        "url": offer.get("register") or (offer.get("sourceUrls") or [None])[0] or SITE_URL,
        "brand": {"@type": "Brand", "name": offer.get("provider") or offer.get("providerEn") or offer_id},
    }

    pricing = offer.get("pricingModel")
    is_free = pricing in FREE_PRICING or (pricing is None and product_type in {"api", "web_infrastructure", "free_ide"})

    offers_block = {
        "@type": "Offer",
        "url": node["url"],
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock" if offer.get("status") == "verified"
        else "https://schema.org/LimitedAvailability",
    }
    if is_free:
        offers_block["price"] = "0"
    node["offers"] = offers_block

    if offer.get("cardRequired") in {"no", "yes"}:
        node["additionalProperty"] = [{
            "@type": "PropertyValue",
            "name": "Credit card required",
            "value": offer["cardRequired"],
        }]

    return node


def build_faq_node(qa_pairs: list[tuple[str, str]]) -> dict:
    """Build a FAQPage node from (question, answer) pairs."""
    return {
        "@type": "FAQPage",
        "@id": f"{SITE_URL}/about/#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in qa_pairs
        ],
    }


def jsonld_script(nodes: list[dict]) -> str:
    """Render nodes as a single <head>-embeddable JSON-LD script block."""
    graph = {"@context": "https://schema.org", "@graph": nodes}
    body = json.dumps(graph, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{body}\n</script>\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "seo" / "schema"), help="output directory")
    args = parser.parse_args()

    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes = [build_product_node(offer) for offer in offers]

    # Site-level FAQ mirroring the Q&A page structure (seo/about-qna-structure.html)
    faq_pairs = [
        ("FreeLLM 是什么？",
         "FreeLLM (freellm.top) 是一个以官方来源为准的免费 AI 资源目录，逐条记录免费模型、免费额度、"
         "免费 IDE、API、开放权重和相关工具的平台、限制条件、地区与注册要求。"),
        ("FreeLLM 如何保证数据准确性？",
         "只用官方来源并标注核验日期；按机制区分免费额度、试用、促销、学生资格与开放权重；"
         "不伪造评分，外部信号按原始公开数据展示。"),
        ("FreeLLM 是否接受付费收录？",
         "不接受付费收录或付费排名，收录决定与商业合作无关。"),
        ("FreeLLM 如何保持更新？",
         "每天自动运行公开来源检查，新增条目经人工审核后进入目录，每日变更日志公开发布。"),
    ]

    outputs = {
        "products.schema.html": jsonld_script(nodes),
        "faq.schema.html": jsonld_script([build_faq_node(faq_pairs)]),
    }

    for filename, content in outputs.items():
        path = out_dir / filename
        path.write_text(content, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)} ({len(nodes) if 'products' in filename else len(faq_pairs)} nodes)")

    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": str(OFFERS_PATH.relative_to(ROOT)),
        "offerCount": len(offers),
        "files": list(outputs),
        "note": "aggregateRating/review omitted: no real user review data exists; fabricated ratings violate Google policy.",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
