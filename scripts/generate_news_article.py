#!/usr/bin/env python3
"""Generate the daily FreeLLM AI news article from a relevant digest.

The LLM only summarizes and links. Every item's title, source URL and publish
time are copied from the digest itself, every related link must resolve to an
existing site page, and any schema violation discards the whole article -- a
failed day produces no article rather than an unverifiable one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BEIJING = timezone(timedelta(hours=8))
SCHEMA_VERSION = 1

EXIT_NO_ARTICLE = 0
EXIT_USAGE = 1
EXIT_GENERATION_FAILED = 3

STATIC_LINK_CANDIDATES = [
    {"label": "免费模型目录", "url": "/models/"},
    {"label": "全部模型记录", "url": "/models/all/"},
    {"label": "免费额度与 Offer", "url": "/offers/"},
    {"label": "Free API 分类", "url": "/category/api/"},
    {"label": "免费额度分类", "url": "/category/free-quota/"},
    {"label": "公益 AI API 导航", "url": "/public-api/"},
    {"label": "免费 LLM 上手指南", "url": "/guides/free-llm/"},
    {"label": "每日发现日志", "url": "/logs/"},
]
CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def load_json(path: str | Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _page_exists(site_root: Path, url: str) -> bool:
    clean = url.split("?")[0].split("#")[0]
    if clean.endswith("/"):
        return (site_root / clean.strip("/") / "index.html").is_file()
    candidate = site_root / clean.strip("/")
    return candidate.is_file() or (candidate / "index.html").is_file()


def build_related_link_candidates(providers: list[dict], digest: dict, site_root: Path) -> list[dict]:
    """Offer the LLM only first-party pages that exist right now."""
    name_to_provider: dict[str, dict] = {}
    for provider in providers or []:
        keys = [str(provider.get("name") or "")]
        keys.extend(str(alias) for alias in provider.get("aliases") or [])
        for key in keys:
            if key.strip():
                name_to_provider[key.strip().casefold()] = provider

    wanted: set[str] = set()
    for item in digest.get("accepted") or []:
        for entity in item.get("matchedEntities") or []:
            provider = name_to_provider.get(str(entity).casefold())
            if provider:
                wanted.add(str(provider.get("id") or ""))

    candidates = [candidate for candidate in STATIC_LINK_CANDIDATES if _page_exists(site_root, candidate["url"])]
    for provider_id in sorted(wanted):
        url = f"/providers/{provider_id}/"
        if _page_exists(site_root, url):
            provider = name_to_provider.get(str(provider_id).casefold(), {})
            candidates.append({"label": f"{provider.get('name') or provider_id} 模型页", "url": url})
    return candidates


def published_news_ids(news_dir: str | Path) -> set[str]:
    directory = Path(news_dir)
    if not directory.is_dir():
        return set()
    ids: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        record = load_json(path)
        if not isinstance(record, dict):
            continue
        for item in record.get("items") or []:
            news_id = str(item.get("newsId") or "").strip()
            if news_id:
                ids.add(news_id)
    return ids


def build_prompt(config: dict, digest: dict, candidates: list[dict]) -> str:
    payload = [
        {
            "newsId": item.get("newsId"),
            "title": item.get("title"),
            "account": item.get("account"),
            "publishedAt": item.get("publishedAt"),
            "description": (item.get("description") or "")[:600],
        }
        for item in digest.get("accepted") or []
    ]
    template = str(config.get("promptTemplate") or "")
    return (
        template.replace("{digest_json}", json.dumps(payload, ensure_ascii=False, indent=1))
        .replace("{related_links_json}", json.dumps(candidates, ensure_ascii=False, indent=1))
        .replace("{window_days}", str(digest.get("windowDays") or 3))
    )


def strip_code_fences(text: str) -> str:
    return CODE_FENCE_RE.sub("", text or "").strip()


def default_llm_client(prompt: str, config: dict) -> str:
    """Call an OpenAI-compatible chat completions endpoint with env credentials."""
    llm = config.get("llm") or {}
    base_url = os.environ.get(str(llm.get("baseUrlEnv") or ""), "") or str(llm.get("defaultBaseUrl") or "")
    api_key = os.environ.get(str(llm.get("apiKeyEnv") or ""), "")
    model = os.environ.get(str(llm.get("modelEnv") or ""), "") or str(llm.get("defaultModel") or "")
    if not base_url or not api_key or not model:
        raise RuntimeError("LLM credentials are not configured (set NEWS_LLM_BASE_URL / NEWS_LLM_API_KEY / NEWS_LLM_MODEL)")

    body = json.dumps({
        "model": model,
        "temperature": float(llm.get("temperature") or 0.3),
        "max_tokens": int(llm.get("maxTokens") or 4096),
        "messages": [
            {"role": "system", "content": "你是严谨的中文科技编辑，只输出符合要求的 JSON。"},
            {"role": "user", "content": prompt},
        ],
    }).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "FreeLLM-News-Daily/1.0 (+https://freellm.top/)",
        },
        method="POST",
    )
    timeout = int(llm.get("timeoutSeconds") or 120)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    try:
        return str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"LLM response missing content: {error}") from error


def validate_article(payload: object, items: list[dict], candidates: list[dict], config: dict) -> list[str]:
    """Fail closed: any deviation from the contract discards the article."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["article payload must be a JSON object"]

    title = payload.get("titleZh")
    if not isinstance(title, str) or not 8 <= len(title.strip()) <= 40:
        errors.append("titleZh must be 8-40 characters")
    elif "http" in title.casefold():
        errors.append("titleZh must not contain URLs")

    summary = payload.get("summaryZh")
    if not isinstance(summary, str) or not 30 <= len(summary.strip()) <= 200:
        errors.append("summaryZh must be 30-200 characters")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        errors.append("items must be a non-empty list")
        return errors

    digest_ids = [str(item.get("newsId")) for item in items]
    seen: set[str] = set()
    candidate_urls = {str(candidate.get("url")) for candidate in candidates}
    min_items = int(config.get("minArticleItems") or 3)
    if len(raw_items) < min_items:
        errors.append(f"article needs at least {min_items} items")
    for index, entry in enumerate(raw_items):
        prefix = f"items[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        news_id = str(entry.get("newsId") or "")
        if news_id not in digest_ids:
            errors.append(f"{prefix}: newsId {news_id!r} is not in the digest")
        elif news_id in seen:
            errors.append(f"{prefix}: duplicate newsId {news_id!r}")
        else:
            seen.add(news_id)

        item_summary = entry.get("summaryZh")
        if not isinstance(item_summary, str) or not 20 <= len(item_summary.strip()) <= 400:
            errors.append(f"{prefix}: summaryZh must be 20-400 characters")

        tags = entry.get("tags")
        if not isinstance(tags, list) or not 1 <= len(tags) <= 6 or not all(isinstance(tag, str) and tag.strip() and len(tag) <= 12 for tag in tags):
            errors.append(f"{prefix}: tags must be 1-6 short strings")

        links = entry.get("relatedLinks")
        if not isinstance(links, list):
            errors.append(f"{prefix}: relatedLinks must be a list")
            continue
        for link in links:
            if not isinstance(link, dict):
                errors.append(f"{prefix}: relatedLinks entries must be objects")
                continue
            label = link.get("label")
            url = link.get("url")
            if not isinstance(label, str) or not 1 <= len(label.strip()) <= 24:
                errors.append(f"{prefix}: related link label must be 1-24 characters")
            if not isinstance(url, str) or url not in candidate_urls:
                errors.append(f"{prefix}: related link url {url!r} is not an allowed site page")

    missing = set(digest_ids) - seen
    if missing:
        errors.append(f"digest items missing from the article: {sorted(missing)}")
    return errors


def generate_article(
    digest: dict,
    config: dict,
    providers: list[dict],
    site_root: Path,
    llm_client=None,
    now: datetime | None = None,
    published: set[str] | None = None,
) -> tuple[dict | None, str]:
    """Return (article, reason). The article is None whenever publishing is unsafe."""
    now = now or datetime.now(BEIJING)
    published = published or set()
    accepted = [item for item in digest.get("accepted") or [] if str(item.get("newsId")) not in published]
    skipped = len((digest.get("accepted") or [])) - len(accepted)
    if skipped:
        print(f"skipping {skipped} already published item(s)")
    if len(accepted) < int(config.get("minArticleItems") or 3):
        return None, f"only {len(accepted)} new relevant item(s) after dedupe"

    work = dict(digest, accepted=accepted)
    candidates = build_related_link_candidates(providers, work, site_root)
    prompt = build_prompt(config, work, candidates)
    client = llm_client or default_llm_client

    last_errors: list[str] = []
    for attempt in (1, 2):
        try:
            raw = strip_code_fences(client(prompt, config))
            payload = json.loads(raw)
        except Exception as error:  # noqa: BLE001 - any LLM failure must fail closed
            last_errors = [f"attempt {attempt}: unusable LLM output ({error})"]
            print(f"::warning::{last_errors[0]}")
            continue
        errors = validate_article(payload, accepted, candidates, config)
        if not errors:
            by_id = {str(item.get("newsId")): item for item in accepted}
            items = []
            for entry in payload["items"]:
                source = by_id[str(entry["newsId"])]
                items.append({
                    "newsId": source["newsId"],
                    "title": source.get("title"),
                    "account": source.get("account"),
                    "publishedAt": source.get("publishedAt"),
                    "url": source.get("url"),
                    "summaryZh": entry["summaryZh"].strip(),
                    "tags": [tag.strip() for tag in entry["tags"]],
                    "relatedLinks": entry.get("relatedLinks") or [],
                })
            llm = config.get("llm") or {}
            generated_by = os.environ.get(str(llm.get("modelEnv") or ""), "") or str(llm.get("defaultModel") or "")
            return {
                "schemaVersion": SCHEMA_VERSION,
                "date": str(digest.get("date") or now.date().isoformat()),
                "titleZh": payload["titleZh"].strip(),
                "summaryZh": payload["summaryZh"].strip(),
                "items": items,
                "digestRef": f"data/news-digest/{digest.get('date')}.json",
                "generatedBy": generated_by,
                "createdAt": now.astimezone(BEIJING).replace(microsecond=0).isoformat(),
            }, ""
        last_errors = [f"attempt {attempt}: {error}" for error in errors]
        print(f"::warning::article validation failed: {last_errors[0]}")
    return None, "; ".join(last_errors[:3])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the daily FreeLLM AI news article JSON")
    parser.add_argument("--digest", required=True, help="relevant digest JSON from wechat-score")
    parser.add_argument("--config", default="data/wechat-news-config.json")
    parser.add_argument("--providers", default="data/providers.json")
    parser.add_argument("--news-dir", default="data/news")
    parser.add_argument("--out", default=None, help="defaults to <news-dir>/<digest date>.json")
    parser.add_argument("--force", action="store_true", help="regenerate even if the article already exists")
    args = parser.parse_args(argv)

    digest = load_json(args.digest)
    if not isinstance(digest, dict):
        print(f"invalid digest: {args.digest}")
        return EXIT_USAGE
    config = load_json(args.config)
    if not isinstance(config, dict):
        print(f"invalid config: {args.config}")
        return EXIT_USAGE
    providers = load_json(args.providers, []) or []

    date = str(digest.get("date") or "")
    out_path = Path(args.out) if args.out else Path(args.news_dir) / f"{date}.json"
    if out_path.is_file() and not args.force:
        print(f"article already exists: {out_path}")
        return EXIT_NO_ARTICLE

    article, reason = generate_article(
        digest,
        config,
        providers,
        REPO_ROOT,
        published=published_news_ids(args.news_dir),
    )
    if article is None:
        print(f"no article written: {reason}")
        # "Only N new items" is a normal quiet day; anything else is a real failure
        # that must surface as a red workflow run instead of a silent skip.
        return EXIT_NO_ARTICLE if reason.startswith("only ") else EXIT_GENERATION_FAILED

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(article, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"article written: {out_path} ({len(article['items'])} items)")
    return EXIT_NO_ARTICLE


if __name__ == "__main__":
    sys.exit(main())
