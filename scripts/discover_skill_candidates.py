"""Discover real SKILL.md files inside verified GitHub repos.

For every repo in data/skill-sources.json whose repo exists (plus an extra
candidate pool), list the repo tree via the jsDelivr data API, find every
SKILL.md, fetch it, and parse YAML frontmatter (name / description).

Output: data/skill-candidates.json  ({repoKey: [{path, name, description, url}]})

Usage: python scripts/discover_skill_candidates.py [owner/repo ...]
"""
from __future__ import annotations

import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "data" / "skill-sources.json"
CANDIDATES_PATH = ROOT / "data" / "skill-candidates.json"

USER_AGENT = "Mozilla/5.0 (compatible; freellm-source-check/1.0)"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
EXTRA_REPOS = ["obra/superpowers"]


def _get(url: str, attempts: int = 4, timeout: int = 25) -> tuple[int, str]:
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = b""
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    body += chunk
                return response.status, body.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return error.code, ""
            status = error.code
        except (urllib.error.URLError, TimeoutError, OSError, http.client.IncompleteRead):
            status = 0
        time.sleep(1.5 * (attempt + 1))
    return status, ""


def frontmatter_field(text: str, field: str) -> str:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return ""
    entry = re.search(rf"^{field}:\s*(.+?)\s*$", match.group(1), re.MULTILINE)
    if not entry:
        return ""
    return entry.group(1).strip().strip('"').strip("'")


def list_repo_files(owner: str, repo: str, branch: str) -> list[str]:
    status, body = _get(
        f"https://data.jsdelivr.com/v1/packages/gh/{owner}/{repo}@{branch}?structure=flat", attempts=2
    )
    if status == 200:
        try:
            files = json.loads(body).get("files", [])
            return [str(item.get("name") or "").lstrip("/") for item in files if isinstance(item, dict)]
        except json.JSONDecodeError:
            return []
    status, body = _get(f"https://ungh.cc/repos/{owner}/{repo}/files/{branch}", attempts=3)
    if status != 200:
        return []
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    files = payload.get("files") if isinstance(payload, dict) else payload
    if not isinstance(files, list):
        return []
    names = []
    for item in files:
        if isinstance(item, dict):
            names.append(str(item.get("path") or "").lstrip("/"))
        elif isinstance(item, str):
            names.append(item.lstrip("/"))
    return names


def main() -> int:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    catalog: dict[str, list] = {}
    if CANDIDATES_PATH.is_file():
        try:
            catalog = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            catalog = {}
    targets: dict[str, dict] = {}
    for key, item in sources["repos"].items():
        if item.get("exists"):
            targets[key] = {"owner": item["owner"], "repo": item["repo"], "branch": item.get("defaultBranch") or "main"}
    for extra in EXTRA_REPOS:
        if extra not in targets:
            owner, repo = extra.split("/", 1)
            targets[f"{extra.lower()}"] = {"owner": owner, "repo": repo, "branch": "HEAD"}

    if len(sys.argv) > 1:
        targets = {k.lower(): v for k, v in targets.items() if k in [arg.lower() for arg in sys.argv[1:]]}

    catalog: dict[str, list] = {}
    for index, (key, item) in enumerate(sorted(targets.items()), start=1):
        owner, repo, branch = item["owner"], item["repo"], item["branch"]
        branch_ref = "main" if branch == "HEAD" else branch
        names = list_repo_files(owner, repo, branch_ref)
        if not names:
            print(f"[{index:02d}/{len(targets)}] {owner}/{repo}: listing unavailable, keeping previous", flush=True)
            continue
        skill_paths = [name for name in names if name.upper().endswith("/SKILL.MD") or name.upper() == "SKILL.MD"]
        entries = []
        for path in skill_paths:
            content_status, content = _get(f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch_ref}/{path}", attempts=4)
            if content_status != 200:
                continue
            fallback_dir = path.rsplit("/", 1)[0].rsplit("/", 1)[-1] if "/" in path.rstrip("/") else repo
            entries.append({
                "path": path,
                "name": frontmatter_field(content, "name") or fallback_dir,
                "description": frontmatter_field(content, "description"),
                "url": f"https://github.com/{owner}/{repo}/tree/{branch_ref}/{path.rsplit('/', 1)[0]}",
                "rawUrl": f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch_ref}/{path}",
            })
            time.sleep(0.1)
        previous = {entry.get("path"): entry for entry in catalog.get(key, [])}
        for entry in entries:
            previous[entry["path"]] = entry
        catalog[key] = sorted(previous.values(), key=lambda entry: entry["path"])
        print(f"[{index:02d}/{len(targets)}] {owner}/{repo}: {len(catalog[key])} skills", flush=True)

    CANDIDATES_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in catalog.values())
    print(f"total {total} candidate skills across {len(catalog)} repos", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
