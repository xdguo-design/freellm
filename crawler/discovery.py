"""Discover official free/cheap AI offer candidates without publishing them."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

DISCOVERY_KEYWORDS = (
    "free",
    "trial",
    "pricing",
    "price",
    "quota",
    "credit",
    "token",
    "off-peak",
    "promotion",
    "promo",
    "免费",
    "试用",
    "额度",
    "体验金",
    "赠送",
    "价格",
    "优惠",
    "夜间",
    "非高峰",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_url(value: str) -> str:
    url, _fragment = urldefrag(value.strip())
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower()).geturl()


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def _host_allowed(url: str, domains: list[str]) -> bool:
    hostname = urlparse(url).hostname
    if not hostname:
        return False
    host = hostname.lower().rstrip(".")
    return any(host == domain.lower().lstrip(".") or host.endswith("." + domain.lower().lstrip(".")) for domain in domains)


def matched_keywords(text: str) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in DISCOVERY_KEYWORDS if keyword.lower() in lowered]


class _DiscoveryLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text)))
            self._href = None
            self._text = []


def extract_discovery_links(content: str, base_url: str, allowed_domains: list[str]) -> list[str]:
    """Extract official links whose URL or nearby anchor text signals an offer."""
    parser = _DiscoveryLinkParser()
    parser.feed(content)
    raw_links = [(href, text) for href, text in parser.links]
    raw_links.extend((url, url) for url in re.findall(r"<loc>\s*(.*?)\s*</loc>", content, flags=re.I | re.S))

    result: list[str] = []
    seen: set[str] = set()
    for raw_url, label in raw_links:
        if not raw_url:
            continue
        absolute = _canonical_url(urljoin(base_url, raw_url.strip()))
        if not _https_url(absolute) or not _host_allowed(absolute, allowed_domains):
            continue
        if not matched_keywords(f"{absolute} {label}"):
            continue
        if absolute not in seen:
            seen.add(absolute)
            result.append(absolute)
    return result


def _safe_fetch(fetcher, url: str, domains: list[str]) -> dict:
    try:
        return fetcher(url, domains)
    except Exception as error:  # one broken public page must not abort the whole run
        return {"url": url, "status": "failed", "reason": f"{type(error).__name__}: {error}"}


def scan_provider_sources(
    providers: list[dict],
    fetcher,
    max_links_per_provider: int = 20,
    max_total_pages: int = 100,
) -> list[dict]:
    """Fetch provider hubs and linked official evidence pages with per-page isolation."""
    registry_errors = validate_provider_registry(providers)
    if registry_errors:
        raise ValueError("invalid provider registry: " + "; ".join(registry_errors))

    results: list[dict] = []
    page_count = 0
    for provider in providers:
        provider_id = provider["id"]
        domains = provider["allowedDomains"]
        links: list[str] = []
        seen_links: set[str] = set()
        for hub_url in provider["discoveryUrls"]:
            if page_count >= max_total_pages:
                break
            page = _safe_fetch(fetcher, hub_url, domains)
            page_count += 1
            hub_result = {
                "providerId": provider_id,
                "url": hub_url,
                "sourceKind": "discovery",
                **page,
            }
            if hub_result.get("status") != "ok":
                hub_result["changeType"] = "source_unavailable"
            results.append(hub_result)
            if page.get("status") != "ok":
                continue
            page_links = page.get("links") or []
            if not page_links and page.get("content"):
                page_links = extract_discovery_links(str(page["content"]), hub_url, domains)
            for link in page_links:
                canonical = _canonical_url(str(link))
                if canonical not in seen_links:
                    seen_links.add(canonical)
                    links.append(canonical)
                if len(links) >= max_links_per_provider:
                    break
            if len(links) >= max_links_per_provider:
                break

        for link in links:
            if page_count >= max_total_pages:
                break
            page = _safe_fetch(fetcher, link, domains)
            page_count += 1
            candidate_result = {
                "providerId": provider_id,
                "url": link,
                "sourceKind": "candidate",
                "matchedKeywords": page.get("matchedKeywords") or matched_keywords(str(page.get("evidence", ""))),
                **page,
            }
            if candidate_result.get("status") != "ok":
                candidate_result["changeType"] = "source_unavailable"
            results.append(candidate_result)
    return results


def discover_public_sources(
    providers: list[dict],
    fetcher,
    max_links_per_provider: int = 20,
    max_total_pages: int = 100,
    now: str | None = None,
) -> list[dict]:
    """Scan public provider hubs, then turn linked evidence pages into review candidates."""
    results = scan_provider_sources(
        providers,
        fetcher=fetcher,
        max_links_per_provider=max_links_per_provider,
        max_total_pages=max_total_pages,
    )
    return build_candidates(results, now=now)


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_source_review_events(scan_results: list[dict], now: str | None = None) -> list[dict]:
    timestamp = now or _now_iso()
    events: list[dict] = []
    for result in scan_results:
        if result.get("status") == "ok":
            continue
        events.append(
            {
                "createdAt": timestamp,
                "providerId": result.get("providerId") or result.get("offerId"),
                "sourceUrl": result.get("url"),
                "changeType": "source_unavailable",
                "reason": result.get("reason", "source did not return a usable public page"),
                "needsReview": True,
                "state": "pending",
            }
        )
    return events


def build_coverage_report(
    providers: list[dict],
    scan_results: list[dict],
    candidates: list[dict],
    now: str | None = None,
    stale_after_days: int = 7,
) -> dict:
    timestamp = now or _now_iso()
    failed = [
        {
            "providerId": result.get("providerId") or result.get("offerId"),
            "sourceUrl": result.get("url"),
            "reason": result.get("reason", "unknown source failure"),
        }
        for result in scan_results
        if result.get("status") != "ok"
    ]
    seen_provider_ids = {result.get("providerId") or result.get("offerId") for result in scan_results}
    provider_ids = {provider.get("id") for provider in providers}
    cutoff = (_parse_timestamp(timestamp) or datetime.now(timezone.utc)) - timedelta(days=stale_after_days)
    stale_count = sum(
        1
        for candidate in candidates
        if (last_seen := _parse_timestamp(candidate.get("lastSeenAt"))) is not None and last_seen < cutoff
    )
    return {
        "generatedAt": timestamp,
        "providerCount": len(providers),
        "sourceCount": len(scan_results),
        "successfulSourceCount": len(scan_results) - len(failed),
        "failedSourceCount": len(failed),
        "failedSources": failed,
        "missingProviderIds": sorted(provider_ids - seen_provider_ids),
        "candidateCount": len(candidates),
        "staleCandidateCount": stale_count,
    }


def validate_provider_registry(providers: object) -> list[str]:
    if not isinstance(providers, list):
        return ["provider registry must contain a list"]

    errors: list[str] = []
    ids: set[str] = set()
    for index, provider in enumerate(providers):
        prefix = f"providers[{index}]"
        if not isinstance(provider, dict):
            errors.append(f"{prefix} must be an object")
            continue
        provider_id = provider.get("id")
        if not isinstance(provider_id, str) or not provider_id.strip():
            errors.append(f"{prefix}: id must be a non-empty string")
        elif provider_id in ids:
            errors.append(f"duplicate provider id: {provider_id}")
        ids.add(provider_id)

        domains = provider.get("allowedDomains")
        if not isinstance(domains, list) or not domains or not all(isinstance(domain, str) and domain.strip() for domain in domains):
            errors.append(f"{prefix}: allowedDomains must contain at least one domain")

        urls = provider.get("discoveryUrls")
        if not isinstance(urls, list) or not urls:
            errors.append(f"{prefix}: discoveryUrls must contain at least one HTTPS URL")
            continue
        for url in urls:
            if not _https_url(url):
                errors.append(f"{prefix}: discoveryUrls contains a non-HTTPS URL")
            elif isinstance(domains, list) and domains and not _host_allowed(url, domains):
                errors.append(f"{prefix}: discovery URL is outside allowedDomains: {url}")
    return errors


def _candidate_id(provider_id: str, source_url: str) -> str:
    key = f"{provider_id}:{_canonical_url(source_url)}".encode("utf-8")
    return "candidate-" + hashlib.sha256(key).hexdigest()[:16]


def build_candidates(scan_results: list[dict], existing: list[dict] | None = None, now: str | None = None) -> list[dict]:
    timestamp = now or _now_iso()
    candidates: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for result in scan_results:
        if result.get("status") != "ok":
            continue
        if result.get("sourceKind") == "discovery":
            continue
        provider_id = result.get("providerId") or result.get("offerId")
        source_url = result.get("url")
        evidence = str(result.get("evidence") or "").strip()
        if not isinstance(provider_id, str) or not isinstance(source_url, str) or not evidence:
            continue
        canonical_url = _canonical_url(source_url)
        key = (provider_id, canonical_url)
        if key in seen:
            continue
        keywords = result.get("matchedKeywords") or matched_keywords(evidence)
        if not keywords:
            continue
        seen.add(key)
        candidates.append(
            {
                "id": _candidate_id(provider_id, canonical_url),
                "providerId": provider_id,
                "sourceUrl": canonical_url,
                "title": result.get("title", ""),
                "evidence": evidence,
                "matchedKeywords": sorted(set(keywords)),
                "status": "needs_review",
                "firstSeenAt": timestamp,
                "lastSeenAt": timestamp,
                "seenCount": 1,
            }
        )
    return merge_candidates(existing or [], candidates, now=timestamp)


def merge_candidates(existing: list[dict], discovered: list[dict], now: str | None = None) -> list[dict]:
    timestamp = now or _now_iso()
    merged: dict[tuple[str, str], dict] = {}
    for item in existing:
        if not isinstance(item, dict) or not item.get("providerId") or not item.get("sourceUrl"):
            continue
        key = (str(item["providerId"]), _canonical_url(str(item["sourceUrl"])))
        merged[key] = {**item, "sourceUrl": key[1]}

    for item in discovered:
        key = (str(item["providerId"]), _canonical_url(str(item["sourceUrl"])))
        previous = merged.get(key)
        if previous is None:
            merged[key] = {**item, "sourceUrl": key[1]}
            continue
        keywords = sorted(set(previous.get("matchedKeywords", [])) | set(item.get("matchedKeywords", [])))
        merged[key] = {
            **previous,
            **item,
            "id": previous.get("id") or item.get("id"),
            "sourceUrl": key[1],
            "firstSeenAt": previous.get("firstSeenAt") or item.get("firstSeenAt") or timestamp,
            "lastSeenAt": timestamp,
            "seenCount": int(previous.get("seenCount", 0)) + int(item.get("seenCount", 1)),
            "matchedKeywords": keywords,
            "status": previous.get("status", "needs_review"),
        }
    return sorted(merged.values(), key=lambda item: (item.get("providerId", ""), item.get("sourceUrl", "")))
