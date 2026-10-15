"""Restore recent sanitized public-API probe artifacts without touching git history.

Uses GitHub's artifact API. The token only reaches api.github.com; the archive
redirect receives a separate credential-free request. No untrusted ZIP paths are
written. Historic reports are bounded and never promoted automatically.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HOST = "api.github.com"
MAX_ZIP_BYTES = 512_000
MAX_JSON_BYTES = 65_536
MAX_ARTIFACTS = 40


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _api_opener():
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()), _NoRedirect()
    )


def _api_request(url: str, token: str, *, opener=None) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != HOST:
        raise ValueError("GitHub API target not allowed")
    opener = opener or _api_opener()
    req = urllib.request.Request(
        url,
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "User-Agent": "freellm-public-api-history/1.0"},
    )
    with opener.open(req, timeout=15) as response:
        return response.read(512_000)


def list_artifacts(repo: str, token: str, *, limit: int = MAX_ARTIFACTS, opener=None) -> list[dict]:
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ValueError("Invalid repository scope")
    limit = min(MAX_ARTIFACTS, max(0, limit))
    if not limit:
        return []
    listed: list[dict] = []
    for page in range(1, 3):
        url = f"https://{HOST}/repos/{repo}/actions/artifacts?per_page=100&page={page}"
        payload = json.loads(_api_request(url, token, opener=opener))
        rows = payload.get("artifacts", [])
        if not isinstance(rows, list):
            break
        for item in rows:
            if (
                isinstance(item, dict)
                and re.fullmatch(r"public-api-evidence-\d+", str(item.get("name", "")))
                and item.get("expired") is False
                and isinstance(item.get("id"), int)
            ):
                listed.append(item)
                if len(listed) >= limit:
                    return listed
        if len(rows) < 100:
            break
    return listed


def extract_authenticated_report(archive_bytes: bytes) -> dict | None:
    if len(archive_bytes) > MAX_ZIP_BYTES:
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            for member in archive.infolist():
                if member.filename not in ("reports/auth.json", ".tmp/public-api/reports/auth.json"):
                    continue
                if member.file_size > MAX_JSON_BYTES or member.is_dir():
                    continue
                row = json.loads(archive.read(member).decode("utf-8"))
                if (
                    isinstance(row, dict)
                    and row.get("schemaVersion") == 1
                    and row.get("providerId") == "hcnsec-gateway"
                    and row.get("probeType") == "authenticated_chat"
                    and row.get("rawPayloadStored") is False
                ):
                    return {
                        field: row.get(field)
                        for field in ("schemaVersion", "providerId", "checkedAt", "probeType", "outcome",
                                      "httpStatus", "latencyMs", "modelId", "evidenceSource", "region",
                                      "rawPayloadStored")
                    }
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, UnicodeError, KeyError):
        pass
    return None


def _fetch_archive(repo: str, token: str, artifact_id: int, *, opener=None, public_open=None) -> bytes:
    if not isinstance(artifact_id, int) or artifact_id < 1:
        raise ValueError("Invalid artifact id")
    opener = opener or _api_opener()
    url = f"https://{HOST}/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "freellm-public-api-history/1.0",
    })
    try:
        with opener.open(request, timeout=15) as response:
            raise ValueError("Expected a GitHub archive redirect")
    except urllib.error.HTTPError as error:
        if error.code not in (301, 302, 303, 307, 308):
            raise
        signed_url = error.headers.get("Location", "")
        error.close()
    target = urllib.parse.urlparse(signed_url)
    if target.scheme != "https" or not target.hostname or target.username or target.password:
        raise ValueError("Invalid signed artifact URL")
    fetch = public_open or urllib.request.urlopen
    # Crucial: no Authorization header in the request to the signed archive URL.
    with fetch(urllib.request.Request(signed_url, headers={"User-Agent": "freellm-public-api-history/1.0"}), timeout=15) as response:
        return response.read(MAX_ZIP_BYTES + 1)


def restore(repo: str, token: str, target_dir: Path, *, limit: int = MAX_ARTIFACTS) -> dict:
    target_dir.mkdir(parents=True, exist_ok=True)
    restored = 0
    skipped = 0
    for item in list_artifacts(repo, token, limit=limit):
        try:
            archive = _fetch_archive(repo, token, item["id"])
            result = extract_authenticated_report(archive)
            if not result:
                skipped += 1
                continue
            path = target_dir / f"history-auth-{item['id']}.json"
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            restored += 1
        except (OSError, ValueError, urllib.error.URLError):
            skipped += 1
    return {"restored": restored, "skipped": skipped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=".tmp/public-api/reports")
    parser.add_argument("--limit", type=int, default=MAX_ARTIFACTS)
    args = parser.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GH_TOKEN", "")
    if not repo or not token:
        print("History restore skipped: repository or CI token unavailable")
        return 0
    try:
        result = restore(repo, token, Path(args.output_dir), limit=args.limit)
    except (OSError, ValueError, urllib.error.URLError):
        print("History restore unavailable; current results remain independent")
        return 0
    print(f"Restored {result['restored']} scrubbed historical samples; {result['skipped']} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
