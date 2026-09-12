"""Discover public GitHub peer projects without executing repository content."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from urllib.parse import quote_plus, urlparse

from .discovery import matched_keywords


DEFAULT_GITHUB_HOSTS = {
    "github.com",
    "api.github.com",
    "raw.githubusercontent.com",
}
PEER_KINDS = {
    "gateway",
    "directory",
    "coding_agent",
    "ide",
    "model_catalog",
    "other",
}
DOCUMENT_PATH_PATTERNS = (
    "README",
    "docs/",
    "CHANGELOG",
    "RELEASE",
    "providers/",
    "models/",
    "catalog/",
    "package.json",
    "pyproject.toml",
    "docker-compose.yml",
    ".env.example",
)
KNOWN_PROVIDERS = (
    "Anthropic",
    "OpenAI",
    "AgentRouter",
    "Gemini",
    "Groq",
    "Mistral",
    "Cerebras",
    "NVIDIA",
    "Cloudflare",
    "GitHub Models",
    "Ollama",
    "Qwen",
    "DeepSeek",
    "OpenRouter",
    "OpenCode",
    "Cursor",
    "Copilot",
    "Amazon Q",
    "Antigravity",
)


def _github_https_url(value: object) -> bool:
    if not isinstance(value, str) or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and parsed.hostname.lower().rstrip(".") == "github.com"
        and not parsed.username
        and not parsed.password
        and bool(parsed.path.strip("/"))
    )


def validate_peer_registry(peers: object) -> list[str]:
    """Validate public GitHub peer configuration without network access."""
    if not isinstance(peers, list):
        return ["peer registry must contain a list"]

    errors: list[str] = []
    ids: set[str] = set()
    for index, peer in enumerate(peers):
        prefix = f"peers[{index}]"
        if not isinstance(peer, dict):
            errors.append(f"{prefix} must be an object")
            continue

        peer_id = peer.get("id")
        if not isinstance(peer_id, str) or not peer_id.strip():
            errors.append(f"{prefix}: id must be a non-empty string")
        elif peer_id in ids:
            errors.append(f"duplicate peer id: {peer_id}")
        else:
            ids.add(peer_id)

        owner = peer.get("owner")
        repo = peer.get("repo")
        for name, value in (("owner", owner), ("repo", repo)):
            if not isinstance(value, str) or not value.strip() or "/" in value or any(character.isspace() for character in value):
                errors.append(f"{prefix}: {name} must be a simple non-empty name")

        repo_url = peer.get("repoUrl")
        if not _github_https_url(repo_url):
            errors.append(f"{prefix}: repoUrl must be an HTTPS github.com URL")
        elif isinstance(owner, str) and isinstance(repo, str):
            expected_path = f"/{owner}/{repo}"
            if urlparse(repo_url).path.rstrip("/") != expected_path:
                errors.append(f"{prefix}: repoUrl must match owner and repo")

        kind = peer.get("kind")
        if kind not in PEER_KINDS:
            errors.append(f"{prefix}: kind must be one of {sorted(PEER_KINDS)}")

        queries = peer.get("discoveryQueries")
        if not isinstance(queries, list) or not queries or not all(isinstance(query, str) and query.strip() for query in queries):
            errors.append(f"{prefix}: discoveryQueries must contain a non-empty string")

        allowed_hosts = peer.get("allowedHosts")
        if (
            not isinstance(allowed_hosts, list)
            or not allowed_hosts
            or not all(isinstance(host, str) and host.strip() for host in allowed_hosts)
        ):
            errors.append(f"{prefix}: allowedHosts must contain at least one host")
        else:
            invalid_hosts = sorted(set(allowed_hosts) - DEFAULT_GITHUB_HOSTS)
            if invalid_hosts:
                errors.append(f"{prefix}: allowedHosts contains unsupported hosts: {', '.join(invalid_hosts)}")

        if not isinstance(peer.get("enabled"), bool):
            errors.append(f"{prefix}: enabled must be boolean")

    return errors


def _checked_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _github_resource_url(value: str) -> bool:
    if not isinstance(value, str) or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and parsed.hostname.lower().rstrip(".") in DEFAULT_GITHUB_HOSTS
        and not parsed.username
        and not parsed.password
    )


def fetch_github_document(
    url: str,
    fetcher=None,
    timeout: int = 8,
    max_bytes: int = 200_000,
) -> dict[str, object]:
    """Fetch one bounded public GitHub document through an injectable fetcher."""
    if not _github_resource_url(url):
        return {
            "url": url,
            "status": "rejected",
            "reason": "only public HTTPS GitHub resource URLs are supported",
            "checkedAt": _checked_at(),
        }

    if fetcher is None:
        from .fetch import fetch_public_text_resource

        fetcher = fetch_public_text_resource
    return fetcher(url, sorted(DEFAULT_GITHUB_HOSTS), timeout, max_bytes)


def fetch_github_json(
    url: str,
    timeout: int = 8,
    max_bytes: int = 2_000_000,
) -> dict:
    """Fetch one bounded public GitHub API response, including large tree indexes."""
    from .fetch import fetch_public_text_resource

    response = fetch_public_text_resource(
        url,
        sorted(DEFAULT_GITHUB_HOSTS),
        timeout=timeout,
        max_bytes=max_bytes,
    )
    if response.get("status") != "ok":
        raise RuntimeError(response.get("reason", "GitHub API response was not usable"))
    try:
        value = json.loads(str(response.get("content", "")))
    except json.JSONDecodeError as error:
        raise RuntimeError("GitHub API response was not valid JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError("GitHub API response must be a JSON object")
    return value


def _document_priority(path: str) -> tuple[int, str]:
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1].upper()
    if name.startswith("README"):
        return (0, normalized)
    if name.startswith("CHANGELOG") or name.startswith("RELEASE"):
        return (1, normalized)
    if name == ".ENV.EXAMPLE":
        return (2, normalized)
    if normalized.lower().startswith("docs/"):
        return (3, normalized)
    return (4, normalized)


def select_document_paths(paths: list[str], max_files: int = 80) -> list[str]:
    """Return deterministic, non-executable documentation paths."""
    selected: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/").lstrip("/")
        upper = normalized.upper()
        if any(pattern.upper() in upper for pattern in DOCUMENT_PATH_PATTERNS):
            selected.append(normalized)
    return sorted(set(selected), key=_document_priority)[:max_files]


def _safe_external_url(value: str) -> bool:
    if any(character.isspace() or ord(character) < 32 for character in value):
        return False
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    return not re.search(r"(?:api[_-]?key|password|secret|token)=", parsed.query, re.I)


def _redact_sensitive_lines(content: str) -> str:
    lines = []
    assignment = re.compile(r"(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]", re.I)
    for line in content.splitlines():
        if assignment.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def _extract_evidence(content: str, limit: int = 600) -> str:
    safe_content = _redact_sensitive_lines(content)
    pieces = re.split(r"(?<=[.!?。！？])\s+|\n+", safe_content)
    interesting = [piece.strip() for piece in pieces if piece.strip() and matched_keywords(piece)]
    return " ".join(interesting)[:limit] or safe_content[:limit].strip()


def extract_peer_document_evidence(
    repository: str,
    path: str,
    commit_sha: str,
    content: str,
) -> dict[str, object]:
    """Extract bounded discovery clues with repository/path/commit provenance."""
    safe_content = _redact_sensitive_lines(content)
    evidence = _extract_evidence(safe_content)
    links = []
    for raw_url in re.findall(r"https://[^\s)<>\"']+", safe_content):
        url = raw_url.rstrip(".,;:!?")
        if _safe_external_url(url) and url not in links:
            links.append(url)

    mentioned_providers = [provider for provider in KNOWN_PROVIDERS if provider.lower() in safe_content.lower()]
    mentioned_models = sorted(set(re.findall(
        r"\b(?:free-[a-z0-9-]+|(?:claude|gemini|groq|mistral|cerebras|qwen|deepseek|gpt|llama)[a-z0-9._/-]*)\b",
        safe_content,
        re.I,
    )))
    return {
        "repository": repository,
        "path": path,
        "commitSha": commit_sha,
        "sourceKind": "github_peer",
        "officiality": "peer_discovery",
        "officialLinks": links,
        "mentionedProviders": mentioned_providers,
        "mentionedModels": mentioned_models,
        "evidence": evidence,
        "evidenceHash": hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
        "status": "needs_review",
        "fetchedAt": _checked_at(),
    }


def discover_github_repositories(
    queries: list[str],
    fetch_json,
    max_repositories: int = 20,
) -> list[dict]:
    """Discover public repositories through injectable GitHub API responses."""
    repositories: list[dict] = []
    seen: set[str] = set()
    for query in dict.fromkeys(query.strip() for query in queries if isinstance(query, str) and query.strip()):
        if len(repositories) >= max_repositories:
            break
        url = "https://api.github.com/search/repositories?q=" + quote_plus(query) + "&per_page=30"
        try:
            response = fetch_json(url)
        except Exception:
            continue
        for item in response.get("items", []) if isinstance(response, dict) else []:
            if len(repositories) >= max_repositories:
                break
            full_name = item.get("full_name") if isinstance(item, dict) else None
            html_url = item.get("html_url") if isinstance(item, dict) else None
            if not isinstance(full_name, str) or not isinstance(html_url, str) or item.get("fork"):
                continue
            if full_name in seen or not _github_resource_url(html_url):
                continue
            seen.add(full_name)
            repositories.append({
                "full_name": full_name,
                "html_url": html_url,
                "default_branch": item.get("default_branch", "main"),
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "query": query,
            })
    return repositories


def discover_global_github_sources(
    queries: list[str],
    fetch_json,
    fetch_document,
    max_repositories: int = 20,
    max_files: int = 40,
) -> list[dict]:
    """Discover unknown AI offer sources from bounded public GitHub searches."""
    repositories = discover_github_repositories(
        queries,
        fetch_json=fetch_json,
        max_repositories=max_repositories,
    )
    records: list[dict] = []
    for repository in repositories:
        full_name = str(repository.get("full_name") or "")
        if full_name.count("/") != 1:
            continue
        owner, repo = full_name.split("/", 1)
        peer = {
            "id": "github-global",
            "owner": owner,
            "repo": repo,
            "enabled": True,
            "allowedHosts": sorted(DEFAULT_GITHUB_HOSTS),
        }
        peer_records = scan_github_peer(
            peer,
            fetch_json=fetch_json,
            fetch_document=fetch_document,
            max_files=max_files,
        )
        for record in peer_records:
            record.update({
                "sourceKind": "github_global",
                "query": repository.get("query", ""),
                "repositoryDescription": repository.get("description", ""),
                "repositoryStars": repository.get("stars", 0),
                "repositoryUrl": repository.get("html_url", ""),
            })
            records.append(record)
    return records


def scan_github_peer(
    peer: dict,
    fetch_json,
    fetch_document,
    max_files: int = 80,
    max_total_bytes: int = 2_000_000,
) -> list[dict]:
    """Scan bounded public documentation and return discovery records only."""
    owner = peer["owner"]
    repo = peer["repo"]
    api_root = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        metadata = fetch_json(api_root)
        branch = str(metadata.get("default_branch") or "main")
        commit_sha = str(metadata.get("sha") or "")
        if not commit_sha:
            commit = fetch_json(f"{api_root}/commits/{branch}")
            commit_sha = str(commit.get("sha") or branch)
        tree = fetch_json(f"{api_root}/git/trees/{branch}?recursive=1")
    except Exception as error:
        return [{
            "providerId": peer.get("id"),
            "repository": f"{owner}/{repo}",
            "sourceKind": "github_peer",
            "status": "source_unavailable",
            "reason": f"{type(error).__name__}: {error}",
            "checkedAt": _checked_at(),
        }]

    paths = [
        str(item["path"])
        for item in tree.get("tree", []) if isinstance(item, dict) and item.get("type") == "blob" and item.get("path")
    ] if isinstance(tree, dict) else []
    selected_paths = select_document_paths(paths, max_files=max_files)
    records: list[dict] = []
    total_bytes = 0
    for path in selected_paths:
        if total_bytes >= max_total_bytes:
            break
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_sha}/{path}"
        try:
            document = fetch_document(raw_url)
        except Exception as error:
            document = {"status": "source_unavailable", "reason": f"{type(error).__name__}: {error}"}
        status = document.get("status") if isinstance(document, dict) else "source_unavailable"
        if status != "ok":
            records.append({
                "providerId": peer.get("id"),
                "repository": f"{owner}/{repo}",
                "path": path,
                "commitSha": commit_sha,
                "url": raw_url,
                "sourceKind": "github_peer",
                "status": status or "source_unavailable",
                "reason": document.get("reason", "document did not return usable text"),
                "checkedAt": document.get("checkedAt", _checked_at()),
            })
            continue
        content = str(document.get("content", ""))
        document_bytes = int(document.get("bytes", len(content.encode("utf-8"))))
        if total_bytes + document_bytes > max_total_bytes:
            continue
        total_bytes += document_bytes
        record = extract_peer_document_evidence(f"{owner}/{repo}", path, commit_sha, content)
        record.update({
            "providerId": peer.get("id"),
            "url": raw_url,
            "bytes": document_bytes,
            "checkedAt": document.get("checkedAt", _checked_at()),
        })
        records.append(record)
    return records
