"""Discover model-level leads from the public freellm.net directory."""

from __future__ import annotations

from html.parser import HTMLParser
from datetime import datetime, timezone
import re
from urllib.parse import urljoin, urlparse

from .discovery import matched_keywords


SUPPORTED_SOURCE_IDS = {"freellm-net"}
SENSITIVE_QUERY = re.compile(r"(?:api[_-]?key|password|secret|token)=", re.I)


def _https_url(value: object, allowed_domains: list[str]) -> bool:
    if not isinstance(value, str) or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if SENSITIVE_QUERY.search(parsed.query):
        return False
    hostname = parsed.hostname.lower().rstrip(".")
    return any(
        hostname == domain.lower().lstrip(".")
        or hostname.endswith("." + domain.lower().lstrip("."))
        for domain in allowed_domains
    )


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def _bool_attribute(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _class_names(value: object) -> set[str]:
    return set(str(value or "").split())


class _ModelRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict] = []
        self._row: dict | None = None
        self._cell_text: list[str] | None = None
        self._link: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        lowered = tag.lower()
        if lowered == "tr" and "model-row" in _class_names(attributes.get("class")):
            self._row = {"attributes": attributes, "cells": [], "links": []}
            return
        if self._row is None:
            return
        if lowered == "td":
            self._cell_text = []
        elif lowered == "a" and self._cell_text is not None:
            self._link = {
                "href": attributes.get("href"),
                "class": attributes.get("class", ""),
                "text": [],
            }

    def handle_data(self, data: str) -> None:
        if self._row is None:
            return
        if self._link is not None:
            self._link["text"].append(data)
        if self._cell_text is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._row is None:
            return
        if lowered == "a" and self._link is not None:
            self._row["links"].append({
                "href": self._link.get("href"),
                "class": self._link.get("class", ""),
                "text": _text(" ".join(self._link.get("text", []))),
            })
            self._link = None
        elif lowered == "td" and self._cell_text is not None:
            self._row["cells"].append(_text(" ".join(self._cell_text)))
            self._cell_text = None
        elif lowered == "tr":
            self.rows.append(self._row)
            self._row = None
            self._cell_text = None
            self._link = None


def _row_value(row: dict, index: int, key: str) -> str:
    attributes = row.get("attributes", {})
    if attributes.get(key):
        return _text(attributes[key])
    cells = row.get("cells", [])
    return _text(cells[index]) if index < len(cells) else ""


def _directory_row_value(row: dict, key: str, legacy_index: int | None, current_index: int) -> str:
    """Read a directory field from data attributes, with table-layout fallbacks.

    Older snapshots omitted the Max Output column. Keeping that fallback makes
    historical discovery fixtures readable while the current table preserves
    all columns from the public directory.
    """
    attribute_keys = {
        "score": "data-score",
        "context": "data-context",
        "maxOutput": "data-max-output",
        "modality": "data-modality",
        "rateLimit": "data-rate-limit",
        "released": "data-released",
        "usageActivity": "data-usage-activity",
        "status": "data-status",
    }
    attribute_key = attribute_keys.get(key)
    if attribute_key:
        value = _text(row.get("attributes", {}).get(attribute_key))
        if value:
            if key == "released" and value.isdigit():
                if int(value) <= 0:
                    return ""
                try:
                    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                except (OverflowError, OSError, ValueError):
                    pass
            return value
    cells = row.get("cells", [])
    if len(cells) < 10 and legacy_index is None:
        return ""
    index = current_index if len(cells) >= 10 else legacy_index
    if index is None:
        return ""
    return _row_value(row, index, "")


def parse_model_directory(html: str, base_url: str) -> list[dict]:
    """Parse free model rows from freellm.net's server-rendered model table."""
    parser = _ModelRowParser()
    parser.feed(html)
    allowed_domains = [urlparse(base_url).hostname or "freellm.net"]
    models: list[dict] = []
    seen_urls: set[str] = set()
    for row in parser.rows:
        attributes = row.get("attributes", {})
        if not _bool_attribute(attributes.get("data-free")):
            continue

        links = row.get("links", [])
        model_link = next((link for link in links if "model-link" in _class_names(link.get("class"))), None)
        if model_link is None:
            model_link = next((link for link in links if "/models/" in str(link.get("href", ""))), None)
        if not isinstance(model_link, dict):
            continue
        directory_url = urljoin(base_url, str(model_link.get("href") or ""))
        if not _https_url(directory_url, allowed_domains) or directory_url in seen_urls:
            continue

        provider_link = next((link for link in links if "/providers/" in str(link.get("href", ""))), None)
        provider = _text(attributes.get("data-provider")) or _text((provider_link or {}).get("text"))
        provider_slug = _text(attributes.get("data-provider-slug"))
        if not provider_slug and isinstance(provider_link, dict):
            provider_slug = str(provider_link.get("href") or "").rstrip("/").rsplit("/", 1)[-1]
        model = _text((model_link or {}).get("text")) or _text(attributes.get("data-name"))
        if not provider or not model:
            continue

        model_id = _text(attributes.get("data-name")) or model
        model_slug = urlparse(directory_url).path.rstrip("/").rsplit("/", 1)[-1]
        record = {
            "directoryProvider": provider,
            "directoryProviderSlug": provider_slug,
            "model": model,
            "modelId": model_id,
            "modelSlug": model_slug,
            "directoryUrl": directory_url,
            "directoryFree": True,
            "directoryNoCard": _bool_attribute(attributes.get("data-nocard")),
            "directoryVerified": _bool_attribute(attributes.get("data-verified")),
            "score": _directory_row_value(row, "score", 2, 2),
            "context": _directory_row_value(row, "context", 3, 3),
            "maxOutput": _directory_row_value(row, "maxOutput", None, 4),
            "modality": _directory_row_value(row, "modality", 4, 5),
            "rateLimit": _directory_row_value(row, "rateLimit", 5, 6),
            "released": _directory_row_value(row, "released", 6, 7),
            "usageActivity": _directory_row_value(row, "usageActivity", 7, 8),
            "status": _directory_row_value(row, "status", 8, 9),
            "tierType": _text(attributes.get("data-tier-type")),
        }
        seen_urls.add(directory_url)
        models.append(record)
    return models


def parse_llms_links(content: str, base_url: str) -> list[str]:
    """Return safe HTTPS freellm.net links from an llms.txt document."""
    raw_links = re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", content)
    raw_links.extend(re.findall(r"https://[^\s<>\"')]+", content))
    allowed_domains = [urlparse(base_url).hostname or "freellm.net"]
    links: list[str] = []
    seen: set[str] = set()
    for raw_link in raw_links:
        link = urljoin(base_url, raw_link.strip()).rstrip(".,;:!?\"")
        if _https_url(link, allowed_domains) and link not in seen:
            seen.add(link)
            links.append(link)
    return links


def validate_source_registry(sources: object) -> list[str]:
    if not isinstance(sources, list):
        return ["third-party source registry must contain a list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{prefix}: id must be a non-empty string")
        elif source_id in ids:
            errors.append(f"duplicate source id: {source_id}")
        elif source_id not in SUPPORTED_SOURCE_IDS:
            errors.append(f"{prefix}: unsupported source id: {source_id}")
        ids.add(str(source_id))
        domains = source.get("allowedDomains")
        if not isinstance(domains, list) or not domains or not all(isinstance(domain, str) and domain.strip() for domain in domains):
            errors.append(f"{prefix}: allowedDomains must contain at least one domain")
        urls = source.get("urls")
        if not isinstance(urls, list) or not urls:
            errors.append(f"{prefix}: urls must contain at least one HTTPS URL")
        elif isinstance(domains, list):
            for url in urls:
                if not _https_url(url, domains):
                    errors.append(f"{prefix}: urls contains an unsafe or out-of-domain URL: {url}")
        if not isinstance(source.get("enabled"), bool):
            errors.append(f"{prefix}: enabled must be boolean")
    return errors


def _failure(source_id: str, url: str, response: dict) -> dict:
    return {
        "providerId": source_id,
        "url": url,
        "sourceKind": "third_party_directory",
        "officiality": "third_party_discovery",
        "status": response.get("status", "failed"),
        "reason": response.get("reason", "third-party source was unavailable"),
    }


def _model_evidence(model: dict) -> str:
    fields = [
        f"{model['directoryProvider']} lists {model['model']} as free",
        f"context {model['context']}" if model.get("context") else "",
        f"rate limit {model['rateLimit']}" if model.get("rateLimit") else "",
        f"status {model['status']}" if model.get("status") else "",
        "no credit card indicated" if model.get("directoryNoCard") else "",
    ]
    return "; ".join(field for field in fields if field)


def discover_freellm_net_sources(sources: list[dict], fetcher, max_models: int = 305) -> list[dict]:
    """Fetch configured freellm.net resources and return review-only model records."""
    errors = validate_source_registry(sources)
    if errors:
        raise ValueError("invalid third-party source registry: " + "; ".join(errors))

    records: list[dict] = []
    for source in sources:
        if not source.get("enabled"):
            continue
        source_id = str(source["id"])
        domains = list(source["allowedDomains"])
        model_rows: list[dict] = []
        directory_references: list[str] = []
        for url in source["urls"]:
            try:
                response = fetcher(url, domains)
            except Exception as error:
                response = {"status": "failed", "reason": f"{type(error).__name__}: {error}"}
            if response.get("status") != "ok":
                records.append(_failure(source_id, url, response))
                continue
            content = str(response.get("content", ""))
            if urlparse(url).path.rstrip("/").endswith("models"):
                model_rows.extend(parse_model_directory(content, url))
            elif urlparse(url).path.lower().endswith(".txt"):
                directory_references.extend(parse_llms_links(content, url))

        seen_urls: set[str] = set()
        for model in model_rows:
            if len(seen_urls) >= max(0, max_models):
                break
            directory_url = model["directoryUrl"]
            if directory_url in seen_urls:
                continue
            seen_urls.add(directory_url)
            evidence = _model_evidence(model)
            records.append({
                **model,
                "providerId": source_id,
                "url": directory_url,
                "sourceKind": "third_party_directory",
                "officiality": "third_party_discovery",
                "status": "needs_review",
                "directoryStatus": model.get("status", ""),
                "title": f"{model['directoryProvider']} · {model['model']}",
                "evidence": evidence,
                "matchedKeywords": matched_keywords(evidence),
                "officialLinks": [directory_url],
                "directoryReferences": sorted(set(directory_references)),
            })
    return records
