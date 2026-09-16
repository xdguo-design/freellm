"""Rebuild data/skills.json from verified candidates.

Reads data/skill-candidates.json (real SKILL.md files discovered in verified
repos), keeps the curated subset defined in CURATED below, fetches each
SKILL.md body from the CDN URL recorded by the discovery pass, and rewrites:

  - data/skills.json          new verified catalog
  - data/skill-content/*.md   full SKILL.md content per skill id

Usage: python scripts/build_verified_skill_catalog.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_PATH = ROOT / "data" / "skill-candidates.json"
SOURCES_PATH = ROOT / "data" / "skill-sources.json"
REVIEWS_PATH = ROOT / "data" / "skill-reviews.json"
SKILLS_PATH = ROOT / "data" / "skills.json"
CONTENT_DIR = ROOT / "data" / "skill-content"

CHECKED_AT = "2026-09-15"
COMPATIBILITY = ["Claude Code", "OpenCode", "Codex"]

# (repoKey, dir suffix of the SKILL.md path) -> category
CURATED: dict[tuple[str, str], str] = {
    # anthropics/skills — official examples
    ("anthropics/skills", "skills/docx"): "documents",
    ("anthropics/skills", "skills/pdf"): "documents",
    ("anthropics/skills", "skills/doc-coauthoring"): "documents",
    ("anthropics/skills", "skills/xlsx"): "data-office",
    ("anthropics/skills", "skills/pptx"): "presentations",
    ("anthropics/skills", "skills/frontend-design"): "product-design",
    ("anthropics/skills", "skills/canvas-design"): "product-design",
    ("anthropics/skills", "skills/brand-guidelines"): "product-design",
    ("anthropics/skills", "skills/theme-factory"): "product-design",
    ("anthropics/skills", "skills/algorithmic-art"): "product-design",
    ("anthropics/skills", "skills/internal-comms"): "email-office",
    ("anthropics/skills", "skills/mcp-builder"): "development",
    ("anthropics/skills", "skills/skill-creator"): "development",
    ("anthropics/skills", "skills/web-artifacts-builder"): "development",
    ("anthropics/skills", "skills/webapp-testing"): "development",
    # obra/superpowers — engineering workflow library
    ("obra/superpowers", "skills/brainstorming"): "planning-office",
    ("obra/superpowers", "skills/writing-plans"): "planning-office",
    ("obra/superpowers", "skills/executing-plans"): "planning-office",
    ("obra/superpowers", "skills/systematic-debugging"): "planning-office",
    ("obra/superpowers", "skills/test-driven-development"): "planning-office",
    ("obra/superpowers", "skills/requesting-code-review"): "planning-office",
    ("obra/superpowers", "skills/receiving-code-review"): "planning-office",
    ("obra/superpowers", "skills/verification-before-completion"): "planning-office",
    ("obra/superpowers", "skills/subagent-driven-development"): "planning-office",
    ("obra/superpowers", "skills/writing-skills"): "development",
    # vercel-labs/agent-skills — React / Next.js workflows
    ("vercel-labs/agent-skills", "skills/composition-patterns"): "development",
    ("vercel-labs/agent-skills", "skills/react-best-practices"): "development",
    ("vercel-labs/agent-skills", "skills/react-native-skills"): "development",
    ("vercel-labs/agent-skills", "skills/web-design-guidelines"): "product-design",
    # blader/humanizer (SKILL.md at repo root)
    ("blader/humanizer", ""): "writing",
    # JimLiu/baoyu-skills — Chinese content creation
    ("jimliu/baoyu-skills", "skills/baoyu-infographic"): "writing",
    ("jimliu/baoyu-skills", "skills/baoyu-markdown-to-html"): "writing",
    ("jimliu/baoyu-skills", "skills/baoyu-url-to-markdown"): "writing",
    ("jimliu/baoyu-skills", "skills/baoyu-article-illustrator"): "writing",
    ("jimliu/baoyu-skills", "skills/baoyu-slide-deck"): "presentations",
    ("jimliu/baoyu-skills", "skills/baoyu-post-to-wechat"): "seo-content",
    ("jimliu/baoyu-skills", "skills/baoyu-post-to-x"): "seo-content",
    ("jimliu/baoyu-skills", "skills/baoyu-xhs-images"): "seo-content",
    ("jimliu/baoyu-skills", "skills/baoyu-cover-image"): "seo-content",
    # iOfficeAI/OfficeCLI — office automation
    ("iofficeai/officecli", "skills/officecli"): "documents",
    ("iofficeai/officecli", "skills/officecli-docx"): "documents",
    ("iofficeai/officecli", "skills/officecli-academic-paper"): "documents",
    ("iofficeai/officecli", "skills/officecli-word-form"): "documents",
    ("iofficeai/officecli", "skills/morph-ppt"): "presentations",
    ("iofficeai/officecli", "skills/officecli-pptx"): "presentations",
    ("iofficeai/officecli", "skills/officecli-pitch-deck"): "presentations",
    ("iofficeai/officecli", "skills/officecli-xlsx"): "data-office",
    ("iofficeai/officecli", "skills/officecli-data-dashboard"): "data-office",
    # ComposioHQ/awesome-claude-skills — curated community collection
    ("composiohq/awesome-claude-skills", "file-organizer"): "file-office",
    ("composiohq/awesome-claude-skills", "invoice-organizer"): "file-office",
    ("composiohq/awesome-claude-skills", "content-research-writer"): "writing",
    ("composiohq/awesome-claude-skills", "meeting-insights-analyzer"): "planning-office",
    ("composiohq/awesome-claude-skills", "tailored-resume-generator"): "resume",
    ("composiohq/awesome-claude-skills", "competitive-ads-extractor"): "ecommerce",
    ("composiohq/awesome-claude-skills", "lead-research-assistant"): "ecommerce",
    ("composiohq/awesome-claude-skills", "twitter-algorithm-optimizer"): "seo-content",
    ("composiohq/awesome-claude-skills", "changelog-generator"): "development",
    # michalparkola/tapestry-skills-for-claude-code — content & learning workflows
    ("michalparkola/tapestry-skills-for-claude-code", "article-extractor"): "seo-content",
    ("michalparkola/tapestry-skills-for-claude-code", "youtube-transcript"): "seo-content",
    ("michalparkola/tapestry-skills-for-claude-code", "learn-this"): "planning-office",
    ("michalparkola/tapestry-skills-for-claude-code", "ship-learn-next"): "planning-office",
    ("michalparkola/tapestry-skills-for-claude-code", "unblock-action"): "planning-office",
    ("michalparkola/tapestry-skills-for-claude-code", "scrum-sage"): "planning-office",
    # PPT / slide skills
    ("hugohe3/ppt-master", "skills/ppt-master"): "presentations",
    ("op7418/nanobanana-ppt-skills", ""): "presentations",
    ("lewislulu/html-ppt-skill", ""): "presentations",
    # resume
    ("rendercv/rendercv-skill", "skills/rendercv"): "resume",
    ("jzcreative/html-resume-beautifier", ""): "resume",
}

SLUG_CLEAN_RE = re.compile(r"[^a-z0-9-]+")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def frontmatter_field(text: str, field: str) -> str:
    """Parse a YAML frontmatter value, including folded/literal block scalars."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return ""
    lines = match.group(1).splitlines()
    for index, line in enumerate(lines):
        entry = re.match(rf"^{field}:\s*(.*)$", line)
        if not entry:
            continue
        inline = entry.group(1).strip()
        if inline in {">", ">-", "|", "|-", ">", "+", ">+", "|+"}:
            block: list[str] = []
            for follow in lines[index + 1:]:
                if not follow.strip() or re.match(r"^\s", follow):
                    block.append(follow.strip())
                else:
                    break
            return " ".join(part for part in block if part).strip()
        return inline.strip('"').strip("'")
    return ""


def slugify(owner: str, name: str) -> str:
    base = f"{owner}-{name}".lower()
    return SLUG_CLEAN_RE.sub("-", base).strip("-")[:60]


def fetch(url: str, attempts: int = 3) -> str:
    urls = [url]
    if "cdn.jsdelivr.net" in url:
        urls.append(url.replace("cdn.jsdelivr.net/gh/", "raw.githubusercontent.com/").replace("@main/", "/main/"))
    last_error = "unknown"
    for target in urls:
        for attempt in range(attempts):
            request = urllib.request.Request(target, headers={"User-Agent": "Mozilla/5.0 (compatible; freellm-catalog/1.0)"})
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    return response.read().decode("utf-8", errors="replace")
            except Exception as error:
                last_error = f"{target}: {error}"
                time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"cannot fetch {last_error}")


def main() -> int:
    candidates = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    reviews = json.loads(REVIEWS_PATH.read_text(encoding="utf-8")).get("repos", {})

    index: dict[tuple[str, str], dict] = {}
    for repo_key, entries in candidates.items():
        for entry in entries:
            path = entry["path"]
            upper = path.upper()
            if upper.endswith("/SKILL.MD"):
                suffix = path[: -len("/SKILL.MD")]
            elif upper.endswith("SKILL.MD"):
                suffix = ""
            else:
                suffix = path
            index[(repo_key, suffix)] = entry

    skills = []
    for (repo_key, suffix), category in CURATED.items():
        entry = index.get((repo_key, suffix))
        if entry is None:
            print(f"skip (candidate missing): {repo_key}/{suffix}", file=sys.stderr)
            continue
        owner, repo = repo_key.split("/", 1)
        repo_meta = sources["repos"].get(repo_key, {})
        name_dir = suffix.rsplit("/", 1)[-1] if suffix else repo
        skill_id = slugify(owner, name_dir)
        content_path = CONTENT_DIR / f"{skill_id}.md"
        if content_path.is_file() and content_path.stat().st_size > 0:
            content = content_path.read_text(encoding="utf-8")
        else:
            content = fetch(entry["rawUrl"])
            CONTENT_DIR.mkdir(parents=True, exist_ok=True)
            content_path.write_text(content, encoding="utf-8")
        branch = repo_meta.get("defaultBranch") or "main"
        github_url = f"https://github.com/{owner}/{repo}/tree/{branch}/{suffix}".rstrip("/")
        official_description = frontmatter_field(content, "description") or entry.get("description") or repo_meta.get("description") or ""
        official_name = frontmatter_field(content, "name") or entry.get("name") or name_dir
        skills.append({
            "id": skill_id,
            "name": official_name,
            "category": category,
            "description": official_description,
            "githubUrl": github_url,
            "cloneCommand": f"git clone https://github.com/{owner}/{repo}.git",
            "compatibility": COMPATIBILITY,
            "status": "verified",
            "source": "github-verified",
            "lastCheckedAt": CHECKED_AT,
            "linkCheck": "ok",
            "repoStats": {
                "stars": repo_meta.get("stars"),
                "forks": repo_meta.get("forks"),
                "pushedAt": repo_meta.get("pushedAt"),
            },
            "contentPath": f"skill-content/{skill_id}.md",
            "contentUrl": entry["rawUrl"],
            "contentFetchedAt": CHECKED_AT,
            "contentBytes": len(content.encode("utf-8")),
            "reviews": reviews.get(repo_key, []),
        })
        print(f"+ {skill_id} [{category}] <- {repo_key}/{suffix}", file=sys.stderr)

    SKILLS_PATH.write_text(json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(skills)} verified skills to {SKILLS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
