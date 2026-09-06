"""Polite, public-only source fetching and small evidence extraction helpers."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "FreeAIIndexResearch/0.1 (+public-source-monitor; contact site maintainer)"
KEYWORDS = re.compile(r"free|trial|pricing|price|quota|credit|token|¥|\$|免费|试用|额度|价格", re.I)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"}:
            self._skip_depth += 1
        elif tag.lower() == "title" and not self._skip_depth:
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        self.parts.append(text)
        if self._in_title:
            self.title_parts.append(text)


def _allowed_host(url: str, allowed_domains: list[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    host = parsed.hostname.lower().rstrip(".")
    return any(host == domain.lower().lstrip(".") or host.endswith("." + domain.lower().lstrip(".")) for domain in allowed_domains)


def extract_evidence(html: str, limit: int = 600) -> dict[str, str]:
    parser = _VisibleTextParser()
    parser.feed(html)
    text = " ".join(parser.parts)
    snippets = []
    for sentence in re.split(r"(?<=[.!?。！？])\s+", text):
        if KEYWORDS.search(sentence):
            snippets.append(sentence.strip())
        if len(" ".join(snippets)) >= limit:
            break
    evidence = " ".join(snippets)[:limit] or text[:limit]
    return {"title": " ".join(parser.title_parts).strip(), "text": text[:limit], "evidence": evidence}


def fetch_public_page(url: str, allowed_domains: list[str], timeout: int = 15, max_bytes: int = 2_000_000) -> dict[str, object]:
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if not _allowed_host(url, allowed_domains):
        return {"url": url, "status": "rejected", "reason": "only HTTPS URLs on an allowed public domain are supported", "checkedAt": checked_at}

    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                return {"url": url, "status": "rejected", "reason": f"unsupported content type: {content_type}", "checkedAt": checked_at}
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                return {"url": url, "status": "rejected", "reason": "response exceeds maximum size", "checkedAt": checked_at}
            charset = response.headers.get_content_charset() or "utf-8"
            parsed = extract_evidence(body.decode(charset, errors="replace"))
            return {"url": url, "status": "ok", "checkedAt": checked_at, **parsed}
    except HTTPError as error:
        return {"url": url, "status": "failed", "reason": f"HTTP {error.code}", "checkedAt": checked_at}
    except (URLError, TimeoutError, ValueError) as error:
        return {"url": url, "status": "failed", "reason": str(error), "checkedAt": checked_at}
