"""Collect recent WeChat official-account articles through public RSS relays.

WeChat itself is never scraped: every source is a standard RSS/Atom feed
published by a public relay (wechat2rss.xlab.app). The collector stays polite
and bounded -- one HTTPS GET per enabled source, capped response size, and a
failing source never aborts the whole run.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import re
from xml.etree import ElementTree

from .fetch import fetch_public_text_resource

BEIJING = timezone(timedelta(hours=8))
ALLOWED_FEED_HOSTS = ("wechat2rss.xlab.app",)
MAX_FEED_BYTES = 4_000_000
DESCRIPTION_LIMIT = 800
SCHEMA_VERSION = 1

ATOM_NS = "{http://www.w3.org/2005/Atom}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def _clean_text(value: object) -> str:
    text = TAG_RE.sub(" ", str(value or ""))
    return SPACE_RE.sub(" ", text).strip()


def _is_https_feed_url(value: object) -> bool:
    from urllib.parse import urlparse

    if not isinstance(value, str) or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and parsed.hostname.lower().rstrip(".") in ALLOWED_FEED_HOSTS
        and not parsed.username
        and not parsed.password
        and bool(parsed.path.strip("/"))
    )


def validate_source_registry(sources: object) -> list[str]:
    """Validate the WeChat feed registry without network access."""
    if not isinstance(sources, list):
        return ["source registry must contain a list"]

    errors: list[str] = []
    ids: set[str] = set()
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue

        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip() or any(character.isspace() for character in source_id):
            errors.append(f"{prefix}: id must be a non-empty string without whitespace")
        elif source_id in ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            ids.add(source_id)

        account = source.get("account")
        if not isinstance(account, str) or not account.strip():
            errors.append(f"{prefix}: account must be a non-empty string")

        feed_url = source.get("feedUrl")
        if not _is_https_feed_url(feed_url):
            errors.append(f"{prefix}: feedUrl must be an HTTPS URL on an allowed relay host ({', '.join(ALLOWED_FEED_HOSTS)})")

        tags = source.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
            errors.append(f"{prefix}: tags must be a list of non-empty strings")

        if not isinstance(source.get("enabled", True), bool):
            errors.append(f"{prefix}: enabled must be a boolean")

    return errors


def parse_feed_datetime(value: object) -> datetime | None:
    """Parse RSS pubDate (RFC 2822) or Atom dates into an aware datetime."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        parsed = None
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=BEIJING)
    return parsed


def news_id(source_id: str, url: str) -> str:
    return f"{source_id}:{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}"


def _entry_text(element: ElementTree.Element, *paths: str) -> str:
    for path in paths:
        node = element.find(path)
        if node is not None:
            text = "".join(node.itertext())
            if text.strip():
                return _clean_text(text)
    return ""


def _entry_link(element: ElementTree.Element) -> str:
    link = element.find("link")
    if link is not None and (link.text or "").strip():
        return link.text.strip()
    for node in element.findall(f"{ATOM_NS}link"):
        if node.get("rel", "alternate") == "alternate" and node.get("href"):
            return node.get("href", "").strip()
    return ""


def parse_feed(xml_text: str, *, source_id: str, account: str) -> tuple[list[dict], str]:
    """Parse one feed into normalized article rows; failures return an error string."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as error:
        return [], f"malformed feed XML: {error}"

    entries: list[ElementTree.Element] = []
    channel = root.find("channel")
    if channel is not None:
        entries = list(channel.findall("item"))
    if not entries:
        entries = list(root.findall(f"{ATOM_NS}entry"))

    if not entries:
        return [], "feed contains no entries"

    items: list[dict] = []
    seen_urls: set[str] = set()
    for entry in entries:
        url = _entry_link(entry)
        title = _entry_text(entry, "title", f"{ATOM_NS}title")
        if not url or not title or url in seen_urls:
            continue
        seen_urls.add(url)
        published_at = parse_feed_datetime(
            _entry_text(entry, "pubDate", f"{ATOM_NS}updated", f"{ATOM_NS}published", f"{DC_NS}date")
        )
        description = _entry_text(
            entry,
            "description",
            f"{ATOM_NS}summary",
            f"{CONTENT_NS}encoded",
            f"{ATOM_NS}content",
        )[:DESCRIPTION_LIMIT]
        items.append({
            "newsId": news_id(source_id, url),
            "sourceId": source_id,
            "account": account,
            "title": title,
            "url": url,
            "publishedAt": published_at,
            "description": description,
        })
    if not items:
        return [], "feed entries lack a title or link"
    return items, ""


def within_window(published_at: datetime | None, now: datetime, window_days: int) -> bool:
    if published_at is None:
        return False
    cutoff = now - timedelta(days=window_days)
    return published_at.astimezone(BEIJING) >= cutoff.astimezone(BEIJING)


def collect_wechat_news(
    sources: list[dict],
    fetch=None,
    *,
    window_days: int = 3,
    now: datetime | None = None,
    timeout: int = 15,
) -> dict:
    """Fetch every enabled feed and return the raw windowed digest.

    ``fetch`` is injectable for tests; it defaults to the polite public fetcher.
    """
    fetcher = fetch or (
        lambda url: fetch_public_text_resource(
            url,
            list(ALLOWED_FEED_HOSTS),
            timeout=timeout,
            max_bytes=MAX_FEED_BYTES,
        )
    )
    now = now or datetime.now(BEIJING)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BEIJING)

    source_rows: list[dict] = []
    items: list[dict] = []
    seen: set[str] = set()
    for source in sources:
        source_id = str(source["id"])
        row = {"id": source_id, "account": source.get("account"), "status": "ok", "items": 0, "error": None}
        if not source.get("enabled", True):
            row["status"] = "disabled"
            source_rows.append(row)
            continue
        result = fetcher(str(source["feedUrl"]))
        if result.get("status") != "ok":
            row["status"] = str(result.get("status") or "failed")
            row["error"] = str(result.get("reason") or "fetch failed")
            source_rows.append(row)
            continue
        parsed, error = parse_feed(str(result.get("content") or ""), source_id=source_id, account=str(source.get("account") or source_id))
        if error:
            row["status"] = "parse_error"
            row["error"] = error
            source_rows.append(row)
            continue
        windowed = [item for item in parsed if within_window(item["publishedAt"], now, window_days)]
        row["items"] = len(windowed)
        for item in windowed:
            key = f"{item['sourceId']}:{item['url']}"
            if key in seen:
                continue
            seen.add(key)
            item["publishedAt"] = item["publishedAt"].astimezone(BEIJING).isoformat()
            items.append(item)
        source_rows.append(row)

    items.sort(key=lambda item: str(item.get("publishedAt") or ""), reverse=True)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": now.astimezone(BEIJING).replace(microsecond=0).isoformat(),
        "windowDays": window_days,
        "sources": source_rows,
        "items": items,
    }
