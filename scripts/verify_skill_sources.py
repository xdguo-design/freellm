"""Verify GitHub sources behind data/skills.json and fetch SKILL.md content.

github.com / raw.githubusercontent.com are unreliable from this network, so all
checks go through CDN mirrors that serve live GitHub data:

  - ungh.cc/repos/{owner}/{repo}        -> existence + stars/forks/pushedAt/defaultBranch
  - data.jsdelivr.com flat file listing  -> locate the real SKILL.md path
  - cdn.jsdelivr.net/gh/...             -> raw file content (raw.githubusercontent fallback)

Outputs:
  - data/skill-sources.json          per-repo + per-skill check results
  - data/skill-content/<id>.md       full SKILL.md content per verifiable skill
  - updates data/skills.json in place with additive fields:
      linkCheck, repoStats {stars, forks, pushedAt}, contentPath,
      contentUrl, contentFetchedAt, contentBytes

linkCheck values: ok | readme_only | skill_file_not_found | repo_not_found | network_error

Usage: python scripts/verify_skill_sources.py [--apply]
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_PATH = ROOT / "data" / "skills.json"
SOURCES_PATH = ROOT / "data" / "skill-sources.json"
CONTENT_DIR = ROOT / "data" / "skill-content"

USER_AGENT = "Mozilla/5.0 (compatible; freellm-source-check/1.0)"
GITHUB_REPO_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^/]+)((?:/[^/]+)*))?$")
CONTENT_FIELDS = ("linkCheck", "repoStats", "contentPath", "contentUrl", "contentFetchedAt", "contentBytes", "contentSource")
ATTEMPTS = 4


def _get(url: str, timeout: int = 25) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, ""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""


def _get_with_retry(url: str, attempts: int = ATTEMPTS) -> tuple[int, str]:
    status, body = 0, ""
    for attempt in range(attempts):
        status, body = _get(url)
        if status != 0:
            return status, body
        time.sleep(1.5 * (attempt + 1))
    return status, body


def parse_github_url(url: str) -> tuple[str, str, str, str] | None:
    match = GITHUB_REPO_RE.match((url or "").strip())
    if not match:
        return None
    owner, repo, branch, subpath = match.groups()
    return owner, repo, branch or "", subpath or ""


def repo_info(owner: str, repo: str) -> dict:
    status, body = _get_with_retry(f"https://ungh.cc/repos/{owner}/{repo}")
    if status == 404:
        return {"exists": False, "httpStatus": 404}
    if status != 200:
        return {"exists": None, "httpStatus": status}
    payload = json.loads(body).get("repo", {})
    return {
        "exists": True,
        "httpStatus": 200,
        "stars": payload.get("stars"),
        "forks": payload.get("forks"),
        "pushedAt": payload.get("pushedAt"),
        "description": payload.get("description"),
        "defaultBranch": payload.get("defaultBranch") or "main",
    }


def list_repo_files(owner: str, repo: str, branch: str) -> list[str]:
    status, body = _get_with_retry(
        f"https://data.jsdelivr.com/v1/packages/gh/{owner}/{repo}@{branch}?structure=flat", attempts=2
    )
    if status != 200:
        return []
    try:
        files = json.loads(body).get("files", [])
    except json.JSONDecodeError:
        return []
    return [item.get("name", "") for item in files if isinstance(item, dict)]


def pick_skill_file(files: list[str], subpath: str) -> str | None:
    prefix = subpath.strip("/") if subpath else ""
    if files:
        lowered = {name.lower(): name for name in files}
        for name in ("SKILL.md", "skill.md"):
            candidate = f"{prefix}/{name}".lower() if prefix else name.lower()
            if candidate in lowered:
                return lowered[candidate]
        if prefix:
            nested = sorted(
                name for name in files
                if name.lower().startswith(prefix.lower() + "/") and name.lower().endswith("/skill.md")
                and name.lower().count("/") == prefix.count("/") + 2
            )
            if len(nested) == 1:
                return nested[0]
        for name in ("README.md", "readme.md"):
            candidate = f"{prefix}/{name}".lower() if prefix else name.lower()
            if candidate in lowered:
                return lowered[candidate]
        return None
    return None


def fetch_raw(owner: str, repo: str, ref: str, path: str) -> tuple[int, str]:
    for url in (
        f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}",
        f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}",
    ):
        status, body = _get_with_retry(url, attempts=2)
        if status == 200 and body.strip():
            return 200, body
        if status == 404:
            continue
    return 404, ""


def main() -> int:
    apply_changes = "--apply" in sys.argv
    skills = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))

    repos: dict[str, dict] = {}
    entries: dict[str, dict] = {}
    for skill in skills:
        parsed = parse_github_url(skill.get("githubUrl", ""))
        if not parsed:
            entries[skill["id"]] = {"githubUrl": skill.get("githubUrl", ""), "linkCheck": "invalid_url"}
            continue
        owner, repo, branch, subpath = parsed
        repo_key = f"{owner}/{repo}".lower()
        repos.setdefault(repo_key, {"owner": owner, "repo": repo})
        entries[skill["id"]] = {"owner": owner, "repo": repo, "branch": branch, "subpath": subpath, "repoKey": repo_key}

    print(f"{len(skills)} skills, {len(repos)} unique repos", flush=True)
    for index, (key, item) in enumerate(sorted(repos.items()), start=1):
        info = repo_info(item["owner"], item["repo"])
        item.update(info)
        state = {True: "ok", False: "missing", None: "network_error"}[info.get("exists")]
        print(f"  [{index:02d}/{len(repos)}] {item['owner']}/{item['repo']}: {state} stars={info.get('stars')}", flush=True)
        time.sleep(0.3)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    file_cache: dict[tuple[str, str], list[str]] = {}
    for index, (skill_id, item) in enumerate(sorted(entries.items()), start=1):
        if "repoKey" not in item:
            continue
        repo_meta = repos[item["repoKey"]]
        if repo_meta.get("exists") is False:
            item["linkCheck"] = "repo_not_found"
            print(f"  [{index:02d}/{len(entries)}] {skill_id}: repo_not_found", flush=True)
            continue
        if repo_meta.get("exists") is None:
            item["linkCheck"] = "network_error"
            print(f"  [{index:02d}/{len(entries)}] {skill_id}: network_error", flush=True)
            continue
        branch = item["branch"] or repo_meta.get("defaultBranch") or "main"
        cache_key = (item["repoKey"], branch)
        if cache_key not in file_cache:
            file_cache[cache_key] = list_repo_files(item["owner"], item["repo"], branch)
        files = file_cache[cache_key]
        target = pick_skill_file(files, item["subpath"])
        if target is None and not files:
            item["linkCheck"] = "network_error"
            print(f"  [{index:02d}/{len(entries)}] {skill_id}: network_error (file listing)", flush=True)
            continue
        if target is None:
            item["linkCheck"] = "skill_file_not_found"
            print(f"  [{index:02d}/{len(entries)}] {skill_id}: skill_file_not_found", flush=True)
            continue
        status, content = fetch_raw(item["owner"], item["repo"], branch, target)
        if status != 200:
            item["linkCheck"] = "network_error" if status == 0 else "skill_file_not_found"
            print(f"  [{index:02d}/{len(entries)}] {skill_id}: {item['linkCheck']}", flush=True)
            continue
        item["linkCheck"] = "readme_only" if target.upper().endswith("README.MD") else "ok"
        item["skillFilePath"] = target
        item["content"] = content
        (CONTENT_DIR / f"{skill_id}.md").write_text(content, encoding="utf-8")
        print(f"  [{index:02d}/{len(entries)}] {skill_id}: {item['linkCheck']} ({target})", flush=True)
        time.sleep(0.2)

    sources = {
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repos": repos,
        "entries": entries,
    }
    SOURCES_PATH.write_text(
        json.dumps({**sources, "entries": {k: {kk: vv for kk, vv in v.items() if kk != "content"} for k, v in entries.items()}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if apply_changes:
        for skill in skills:
            for field in CONTENT_FIELDS:
                skill.pop(field, None)
            check = entries.get(skill["id"], {})
            skill["linkCheck"] = check.get("linkCheck", "invalid_url")
            repo_meta = repos.get(check.get("repoKey", ""), {})
            if repo_meta.get("exists"):
                skill["repoStats"] = {
                    "stars": repo_meta.get("stars"),
                    "forks": repo_meta.get("forks"),
                    "pushedAt": repo_meta.get("pushedAt"),
                }
            if check.get("linkCheck") in {"ok", "readme_only"}:
                skill["contentPath"] = f"skill-content/{skill['id']}.md"
                skill["contentSource"] = "github"
                skill["contentFetchedAt"] = sources["checkedAt"]
                skill["contentBytes"] = (CONTENT_DIR / f"{skill['id']}.md").stat().st_size
        SKILLS_PATH.write_text(json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("applied: data/skills.json updated", flush=True)

    summary: dict[str, int] = {}
    for item in entries.values():
        key = item.get("linkCheck", "invalid_url")
        summary[key] = summary.get(key, 0) + 1
    print("summary:", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
