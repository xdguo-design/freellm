"""Score collected WeChat AI news against the FreeLLM site topic.

The site serves one audience: people looking for free LLM APIs, quotas,
open-weight models and AI tools. Scoring is deliberately deterministic --
site entities (providers, models, curated brands) plus topic keywords, with a
noise blacklist -- so a bad news day produces no article instead of a thin one.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

BEIJING = timezone(timedelta(hours=8))
SCHEMA_VERSION = 1
MAX_MATCHES = 6

DEFAULT_CONFIG = {
    "minScore": 3,
    "minEntities": 1,
    "minKeywords": 2,
    "entityWeight": 3,
    "keywordWeight": 1,
    "entityScoreCap": 6,
    "keywordScoreCap": 3,
    "topicKeywords": [],
    "blacklistKeywords": [],
    "extraEntities": [],
}


def load_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("news config must be a JSON object")
    return config


def extract_site_entities(
    models: list[dict] | None = None,
    providers: list[dict] | None = None,
    extra_entities: list[str] | None = None,
) -> list[str]:
    """Collect recognizable vendor and model names from site data plus extras."""
    names: set[str] = set()
    for provider in providers or []:
        for key in ("name",):
            value = str(provider.get(key) or "").strip()
            if len(value) >= 3:
                names.add(value)
        for alias in provider.get("aliases") or []:
            value = str(alias).strip()
            if len(value) >= 3:
                names.add(value)
    for model in models or []:
        for key in ("model", "provider"):
            value = str(model.get(key) or "").strip()
            if len(value) >= 3:
                names.add(value)
        family = str(model.get("model") or "").split(" ")[0].strip()
        if len(family) >= 3:
            names.add(family)
    for value in extra_entities or []:
        value = str(value).strip()
        if len(value) >= 3:
            names.add(value)
    return sorted(name for name in names if not name.isdigit())


def score_item(item: dict, entities: list[str], config: dict) -> dict:
    """Score one collected article; blacklist hits always reject."""
    text = f"{item.get('title') or ''} {item.get('description') or ''}".casefold()
    blacklist = [str(keyword) for keyword in config.get("blacklistKeywords") or []]
    matched_blacklist = [keyword for keyword in blacklist if keyword.casefold() in text]
    if matched_blacklist:
        return {
            "score": 0,
            "matchedEntities": [],
            "matchedKeywords": [],
            "decision": "reject",
            "reason": f"blacklist:{matched_blacklist[0]}",
        }

    matched_entities = [entity for entity in entities if entity.casefold() in text][:MAX_MATCHES]
    keywords = [str(keyword) for keyword in config.get("topicKeywords") or []]
    matched_keywords = [keyword for keyword in keywords if keyword.casefold() in text][:MAX_MATCHES]

    entity_weight = int(config.get("entityWeight") or DEFAULT_CONFIG["entityWeight"])
    keyword_weight = int(config.get("keywordWeight") or DEFAULT_CONFIG["keywordWeight"])
    entity_cap = int(config.get("entityScoreCap") or DEFAULT_CONFIG["entityScoreCap"])
    keyword_cap = int(config.get("keywordScoreCap") or DEFAULT_CONFIG["keywordScoreCap"])
    score = min(len(matched_entities) * entity_weight, entity_cap) + min(
        len(matched_keywords) * keyword_weight,
        keyword_cap,
    )

    min_score = int(config.get("minScore") or DEFAULT_CONFIG["minScore"])
    min_entities = int(config.get("minEntities") or DEFAULT_CONFIG["minEntities"])
    min_keywords = int(config.get("minKeywords") or DEFAULT_CONFIG["minKeywords"])
    passes = score >= min_score and (
        len(matched_entities) >= min_entities or len(matched_keywords) >= min_keywords
    )
    return {
        "score": score,
        "matchedEntities": matched_entities,
        "matchedKeywords": matched_keywords,
        "decision": "accept" if passes else "reject",
        "reason": "" if passes else "below_threshold",
    }


def beijing_date(value: str | datetime | None) -> str:
    if value is None:
        return datetime.now(BEIJING).date().isoformat()
    if isinstance(value, datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=BEIJING)
    else:
        moment = datetime.fromisoformat(str(value))
    return moment.astimezone(BEIJING).date().isoformat()


def build_relevant_digest(raw_digest: dict, entities: list[str], config: dict) -> dict:
    """Split a raw digest into accepted and rejected items with audit fields."""
    accepted: list[dict] = []
    rejected: list[dict] = []
    for item in raw_digest.get("items") or []:
        verdict = score_item(item, entities, config)
        row = {key: item.get(key) for key in ("newsId", "sourceId", "account", "title", "url", "publishedAt", "description")}
        row.update({
            "score": verdict["score"],
            "matchedEntities": verdict["matchedEntities"],
            "matchedKeywords": verdict["matchedKeywords"],
        })
        if verdict["decision"] == "accept":
            accepted.append(row)
        else:
            rejected.append({**row, "reason": verdict["reason"]})

    accepted.sort(key=lambda row: str(row.get("publishedAt") or ""), reverse=True)
    rejected.sort(key=lambda row: str(row.get("publishedAt") or ""), reverse=True)
    max_accepted = int(config.get("maxAcceptedItems") or 0)
    if max_accepted and len(accepted) > max_accepted:
        # Keep the strongest items for the article, but preserve chronological order.
        ranked = sorted(accepted, key=lambda row: (-int(row.get("score") or 0), str(row.get("publishedAt") or "")), reverse=False)
        kept = {row["newsId"] for row in ranked[:max_accepted]}
        accepted = [row for row in accepted if row["newsId"] in kept]
    statuses = [str(row.get("status")) for row in raw_digest.get("sources") or []]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "date": beijing_date(raw_digest.get("generatedAt")),
        "windowDays": raw_digest.get("windowDays"),
        "generatedAt": raw_digest.get("generatedAt"),
        "sourceHealth": {
            "ok": statuses.count("ok"),
            "failed": sum(1 for status in statuses if status not in {"ok", "disabled"}),
            "disabled": statuses.count("disabled"),
        },
        "stats": {"collected": len(raw_digest.get("items") or []), "accepted": len(accepted), "rejected": len(rejected)},
        "accepted": accepted,
        "rejected": rejected,
    }


def digest_is_publishable(digest: dict, config: dict) -> tuple[bool, str]:
    """A day is publishable only with enough accepted items for a real article."""
    min_items = int(config.get("minArticleItems") or 3)
    accepted = len(digest.get("accepted") or [])
    if accepted == 0:
        return False, "no relevant news in window"
    if accepted < min_items:
        return False, f"only {accepted} relevant item(s), need at least {min_items}"
    return True, ""
