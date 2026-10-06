"""Helpers for resolving public assets referenced by generated homepage HTML."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit


def homepage_data_asset(html: str, public_url: str) -> str:
    """Return the same-origin path configured in the homepage body data URL."""
    body = re.search(r"<body\b[^>]*>", html, flags=re.IGNORECASE)
    if not body:
        raise ValueError("homepage HTML is missing its body element")
    source = re.search(r'\bdata-offers-url="([^"]+)"', body.group(0), flags=re.IGNORECASE)
    if not source:
        raise ValueError("homepage body is missing data-offers-url")

    resolved = urlsplit(urljoin(public_url, source.group(1)))
    expected = urlsplit(public_url)
    if resolved.scheme != expected.scheme or resolved.netloc != expected.netloc:
        raise ValueError("homepage data URL must stay on the public site origin")
    if not resolved.path.startswith("/") or ".." in resolved.path.split("/"):
        raise ValueError("homepage data URL must resolve to a safe root-relative path")
    return resolved.path.lstrip("/")
