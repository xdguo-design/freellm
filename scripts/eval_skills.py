#!/usr/bin/env python3
"""FreeLLM Skill 实测 runner (suite freellm-skill-task-v1).

For every skill listed in data/skills.json:

1. take the fixed realistic task in data/skill-eval-tasks.json,
2. inject the skill's SKILL.md text (data/skill-content/<id>.md) as the system prompt,
3. call 1-2 free models through their OpenAI-compatible endpoints,
4. grade the answer with the deterministic rubric checks attached to the task,
5. write data/evaluations/skills-latest.json (summary + output excerpts) and
   data/evaluations/skills-raw.json (full trimmed outputs).

This is a *task-level* test: the model cannot run the skill's own scripts or
CLIs here, so the result says whether a free model follows the skill's
instructions on a realistic task, not whether the original repository's
tooling runs end-to-end.

Keys are read from env only, never printed, and scrubbed from stored errors.

Usage:
    python scripts/eval_skills.py --out data/evaluations              # real run
    python scripts/eval_skills.py --only obra-brainstorming --models modelscope
    python scripts/eval_skills.py --apply                              # merge reviewed results into data/skill-tests.json
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures as cf
import datetime as dt
import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TASKS_PATH = DATA / "skill-eval-tasks.json"
REVIEW_PATH = DATA / "evaluations" / "skills-review.json"
# Optional, committed only on a skill-eval/** branch: {"only": [...], "models": [...], "merge": true}
REQUEST_PATH = DATA / "skill-eval-request.json"
SUITE_VERSION = "freellm-skill-task-v1"
TIMEOUT = 180  # socket read timeout
CALL_MAX_SEC = 420  # hard wall-clock cap per streamed call
MAX_TOKENS = 16384  # reasoning models exhausted 8192 on long tasks (empty content)
DEADLINE = [float("inf")]  # set by main(); no retry is started after it
MAX_SKILL_CHARS = 120_000
EXCERPT_CHARS = 700
RAW_CHARS = 12_000
TZ = dt.timezone(dt.timedelta(hours=8))

# Free models chosen from data/evaluations/latest.json (top scorers that actually answered).
MODELS = {
    "modelscope": {
        "provider": "魔搭 ModelScope",
        "env": "MODELSCOPE_API_KEY",
        "base": "https://api-inference.modelscope.cn/v1",
        "model": "deepseek-ai/DeepSeek-V4.1-Flash",
        "concurrency": 4,
    },
    "nvidia": {
        "provider": "NVIDIA NIM",
        "env": "NVIDIA_API_KEY",
        "base": "https://integrate.api.nvidia.com/v1",
        "model": "z-ai/glm-5.3",
        "concurrency": 6,
    },
    # Follow-up models (non-default): fast free models used to retry skills where the default pair produced no answer.
    "zhipu": {
        "provider": "智谱 BigModel",
        "env": "ZHIPU_API_KEY",
        "base": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash-250414",
        "concurrency": 3,
        "max_tokens": 4095,
    },
    "nvidia_oss": {
        "provider": "NVIDIA NIM",
        "env": "NVIDIA_API_KEY",
        "base": "https://integrate.api.nvidia.com/v1",
        "model": "openai/gpt-oss-20b",
        "concurrency": 4,
    },
    "groq": {
        "provider": "Groq",
        "env": "GROQ_API_KEY",
        "base": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-120b",
        "concurrency": 1,
    },
    "openrouter": {  # ~50 free requests/day: opt-in only
        "provider": "OpenRouter",
        "env": "OPENROUTER_API_KEY",
        "base": "https://openrouter.ai/api/v1",
        "model": "cohere/north-mini-code:free",
        "concurrency": 1,
    },
}
DEFAULT_MODELS = ["modelscope", "nvidia"]
KEY_ENVS = ["SILICONFLOW_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY", "MODELSCOPE_API_KEY", "ZHIPU_API_KEY", "NVIDIA_API_KEY"]

SYSTEM_PREAMBLE = (
    "你是一个已经加载了下面这个 Agent Skill 的 AI 助手。请严格遵循 Skill 的说明来完成用户任务。\n"
    "当前环境无法执行命令、读写文件或访问网络：当 Skill 要求运行脚本/CLI/工具时，请直接给出你会执行的具体命令、代码和要验证的内容；"
    "不要声称已经执行或已经看到结果。用中文回答（代码与命令保持原样）。\n\n"
    "===== SKILL.md 开始 =====\n"
)
SYSTEM_SUFFIX = "\n===== SKILL.md 结束 ====="


# ---------------------------------------------------------------- secrets

def scrub(text: str) -> str:
    """Remove anything that looks like a credential from text we store."""
    if not text:
        return text
    for name in KEY_ENVS:
        value = os.environ.get(name)
        if value and len(value) >= 6:
            text = text.replace(value, "[REDACTED]")
    text = re.sub(r"(?i)(authorization\s*[:=]\s*)(bearer\s+)?[^\s\"'\\,}]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-]{8,}", "Bearer [REDACTED]", text)
    text = re.sub(r"\b(sk|nvapi|gsk|ms)-[A-Za-z0-9_\-]{8,}", r"\1-[REDACTED]", text)
    return text


# ---------------------------------------------------------------- loading

def load_skills() -> list[dict]:
    return json.loads((DATA / "skills.json").read_text(encoding="utf-8"))


def load_tasks(path: Path = TASKS_PATH) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))["tasks"]


def skill_text(skill_id: str) -> tuple[str, bool]:
    text = (DATA / "skill-content" / f"{skill_id}.md").read_text(encoding="utf-8")
    if len(text) > MAX_SKILL_CHARS:
        return text[:MAX_SKILL_CHARS], True
    return text, False


def build_messages(skill_id: str, task: str) -> tuple[list[dict], bool]:
    text, truncated = skill_text(skill_id)
    note = "\n（注：SKILL.md 超长，已截断到前 %d 字符）" % MAX_SKILL_CHARS if truncated else ""
    return [
        {"role": "system", "content": SYSTEM_PREAMBLE + text + note + SYSTEM_SUFFIX},
        {"role": "user", "content": task},
    ], truncated


# ---------------------------------------------------------------- grading

def strip_reasoning(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    text = re.sub(r"^.*?</think>", "", text, flags=re.S)
    return text.strip()


FENCE = re.compile(r"```([A-Za-z0-9_+\-]*)[^\n]*\n(.*?)```", re.S)
LANG_ALIASES = {
    "python": {"python", "py", "python3"},
    "javascript": {"javascript", "js", "mjs", "cjs", "node"},
    "html": {"html", "htm"},
}


def code_blocks(text: str) -> list[tuple[str, str]]:
    return [(lang.lower(), body) for lang, body in FENCE.findall(text)]


def _compiles(lang: str, code: str) -> tuple[bool, str]:
    if lang == "python":
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as exc:
            return False, f"SyntaxError line {exc.lineno}: {exc.msg}"
    if lang == "javascript":
        node = shutil.which("node")
        if not node:
            return True, "node 不可用，未检查"
        with tempfile.NamedTemporaryFile("w", suffix=".mjs" if re.search(r"^\s*(import|export)\s", code, re.M) else ".js", delete=False, encoding="utf-8") as fh:
            fh.write(code)
            path = fh.name
        try:
            proc = subprocess.run([node, "--check", path], capture_output=True, text=True, timeout=30)
            return proc.returncode == 0, (proc.stderr.strip().splitlines() or [""])[0][:200]
        finally:
            os.unlink(path)
    if lang == "html":
        ok, why = html_ok(code)
        return ok, why
    return True, ""


class _Tags(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def extract_html(text: str) -> str:
    for lang, body in code_blocks(text):
        if lang in LANG_ALIASES["html"] or re.search(r"<!doctype html|<html", body, re.I):
            return body
    m = re.search(r"(<!doctype html.*?</html>|<html.*?</html>)", text, re.S | re.I)
    return m.group(1) if m else ""


def html_ok(doc: str) -> tuple[bool, str]:
    if not re.search(r"<html", doc, re.I) or not re.search(r"</html>", doc, re.I):
        return False, "缺少 <html>…</html>"
    parser = _Tags()
    try:
        parser.feed(doc)
    except Exception as exc:  # noqa: BLE001
        return False, f"HTML 解析失败: {exc}"
    if "body" not in parser.tags:
        return False, "缺少 <body>"
    return True, ""


def run_check(check: dict, text: str) -> tuple[bool, str]:
    kind = check["type"]
    if kind == "regex":
        return bool(re.search(check["pattern"], text, re.I | re.M)), ""
    if kind == "regex_any":
        return any(re.search(p, text, re.I | re.M) for p in check["patterns"]), ""
    if kind == "not_regex":
        m = re.search(check["pattern"], text, re.I | re.M)
        return (m is None), (f"命中：{m.group(0)[:60]}" if m else "")
    if kind == "count_regex":
        n = len(re.findall(check["pattern"], text, re.I | re.M))
        ok = n >= check.get("min", 0) and ("max" not in check or n <= check["max"])
        return ok, f"计数 {n}"
    if kind == "order":
        a = re.search(check["first"], text, re.I | re.M)
        b = re.search(check["second"], text, re.I | re.M)
        return bool(a and b and a.start() < b.start()), ""
    if kind == "min_chars":
        return len(text) >= check["n"], f"{len(text)} 字符"
    if kind == "max_chars":
        return len(text) <= check["n"], f"{len(text)} 字符"
    if kind == "code_compiles":
        wanted = set().union(*(LANG_ALIASES.get(l, {l}) for l in check["langs"]))
        blocks = [(lang, body) for lang, body in code_blocks(text) if lang in wanted]
        if not blocks:
            return False, "没有找到对应语言的代码块"
        canon = {alias: name for name, aliases in LANG_ALIASES.items() for alias in aliases}
        lang, body = max(blocks, key=lambda b: len(b[1]))
        ok, why = _compiles(canon.get(lang, lang), body)
        return ok, (f"最长 {lang} 代码块：" + (why or "通过"))
    if kind == "html_doc":
        doc = extract_html(text)
        if not doc:
            return False, "没有完整 HTML 文档"
        ok, why = html_ok(doc)
        if ok and len(doc) < check.get("min_chars", 0):
            return False, f"HTML 仅 {len(doc)} 字符"
        return ok, why or f"HTML {len(doc)} 字符"
    if kind == "yaml_valid":
        blocks = [body for lang, body in code_blocks(text) if lang in {"yaml", "yml"}]
        if not blocks:
            return False, "没有 yaml 代码块"
        try:
            import yaml  # type: ignore
        except ImportError:
            return all(re.search(rf"(?m)^{k}:", blocks[0]) for k in check["keys"]), "PyYAML 不可用，仅检查顶层键"
        try:
            data = yaml.safe_load(max(blocks, key=len))
        except Exception as exc:  # noqa: BLE001
            return False, f"YAML 解析失败: {str(exc)[:120]}"
        return isinstance(data, dict) and all(k in data for k in check["keys"]), ""
    if kind == "frontmatter":
        # Any block between two consecutive `---` lines counts (Markdown rules may precede the real frontmatter).
        fences = [m.end() for m in re.finditer(r"(?m)^---\s*$", text)]
        starts = [m.start() for m in re.finditer(r"(?m)^---\s*$", text)]
        if len(fences) < 2:
            return False, "没有 frontmatter"
        for i in range(len(fences) - 1):
            block = text[fences[i]:starts[i + 1]]
            if all(re.search(rf"(?m)^{k}\s*:", block) for k in check["keys"]):
                return True, ""
        return False, "frontmatter 缺少必需键"
    raise ValueError(f"unknown check type {kind}")


def grade(task: dict, output: str) -> dict:
    text = strip_reasoning(output)
    results = []
    for check in task["checks"]:
        ok, note = run_check(check, text)
        results.append({"label": check["label"], "pass": bool(ok), **({"note": note} if note else {})})
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    ratio = passed / total if total else 0
    verdict = "通过" if passed == total else "部分通过" if ratio >= 0.6 else "未通过"
    return {"checks": results, "passedChecks": passed, "totalChecks": total,
            "score": round(10 * ratio, 1), "verdict": verdict}


# ---------------------------------------------------------------- calling

def _request(url: str, key: str, body: dict):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://freellm.top",
            "X-Title": "FreeLLM skill eval",
            "User-Agent": "freellm-skill-eval/1.0",
        },
    )
    return urllib.request.urlopen(req, timeout=TIMEOUT)


class CallTooLong(Exception):
    pass


def stream_chat(cfg: dict, key: str, messages: list[dict]) -> dict:
    body = {"model": cfg["model"], "messages": messages, "temperature": 0.2, "max_tokens": cfg.get("max_tokens", MAX_TOKENS),
            "stream": True, "stream_options": {"include_usage": True}}
    start = time.perf_counter()
    first = None
    chunks: list[str] = []
    reasoning = 0
    usage: dict = {}
    with _request(cfg["base"] + "/chat/completions", key, body) as resp:
        for raw in resp:
            if time.perf_counter() - start > CALL_MAX_SEC:
                raise CallTooLong(f"超过单次调用上限 {CALL_MAX_SEC}s 被中止")
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                evt = json.loads(data)
            except json.JSONDecodeError:
                continue
            if evt.get("usage"):
                usage = evt["usage"]
            for choice in evt.get("choices") or []:
                delta = choice.get("delta") or {}
                piece = delta.get("content") or ""
                think = delta.get("reasoning_content") or delta.get("reasoning") or ""
                reasoning += len(think)
                if (piece or think) and first is None:
                    first = time.perf_counter()
                chunks.append(piece)
    end = time.perf_counter()
    return {"output": "".join(chunks), "ttftMs": round(((first or end) - start) * 1000),
            "totalMs": round((end - start) * 1000), "usage": usage, "reasoningChars": reasoning}


def call_with_retry(cfg: dict, key: str, messages: list[dict], sleep=time.sleep) -> dict:
    last_error = ""
    for attempt in range(2):  # never loop more than twice
        try:
            return {"ok": True, **stream_chat(cfg, key, messages)}
        except urllib.error.HTTPError as exc:
            detail = scrub(exc.read().decode("utf-8", "ignore")[:300])
            last_error = f"HTTP {exc.code}: {detail}"
            if exc.code in (429, 500, 502, 503, 504) and attempt == 0 and time.time() < DEADLINE[0]:
                sleep(30 if exc.code == 429 else 8)
                continue
            break
        except CallTooLong as exc:
            last_error = str(exc)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = scrub(f"{type(exc).__name__}: {exc}")[:300]
            if attempt == 0 and time.time() < DEADLINE[0]:
                sleep(8)
                continue
    return {"ok": False, "error": last_error}


def excerpt(text: str, n: int = EXCERPT_CHARS) -> str:
    text = strip_reasoning(text)
    return text if len(text) <= n else text[:n].rstrip() + "…"


def run_one(skill: dict, task: dict, mid: str, cfg: dict, key: str, caller=call_with_retry) -> dict:
    messages, truncated = build_messages(skill["id"], task["task"])
    res = caller(cfg, key, messages)
    base = {"skillId": skill["id"], "modelId": mid, "provider": cfg["provider"], "model": cfg["model"],
            "skillTruncated": truncated, "testedAt": dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M CST")}
    if not res.get("ok"):
        return {**base, "callOk": False, "verdict": "调用失败", "score": None, "error": scrub(res.get("error", "")),
                "checks": [], "passedChecks": 0, "totalChecks": len(task["checks"]), "output": "", "excerpt": ""}
    output = strip_reasoning(res["output"])
    if not output:
        return {**base, "callOk": False, "verdict": "调用失败", "score": None,
                "error": "模型返回空内容（可能思考耗尽 max_tokens）", "checks": [], "passedChecks": 0,
                "totalChecks": len(task["checks"]), "output": "", "excerpt": "",
                "totalMs": res.get("totalMs"), "ttftMs": res.get("ttftMs"), "reasoningChars": res.get("reasoningChars", 0)}
    g = grade(task, output)
    return {**base, "callOk": True, **g, "judgedBy": "auto", "ttftMs": res["ttftMs"], "totalMs": res["totalMs"],
            "outputChars": len(output), "reasoningChars": res.get("reasoningChars", 0),
            "usage": {k: res["usage"].get(k) for k in ("prompt_tokens", "completion_tokens") if res["usage"].get(k) is not None},
            "output": output[:RAW_CHARS], "excerpt": excerpt(output)}


# ---------------------------------------------------------------- review + apply

def apply_review(runs: list[dict], review: dict) -> list[dict]:
    """Manual review overrides: {skillId: {modelId: {verdict, note}}}."""
    out = []
    for run in runs:
        item = (review.get(run["skillId"]) or {}).get(run["modelId"])
        if item and run.get("callOk"):
            run = {**run, "autoVerdict": run.get("autoVerdict", run["verdict"]), "verdict": item["verdict"],
                   "judgedBy": "manual", "reviewNote": item.get("note", "")}
        out.append(run)
    return out


def summarize(runs: list[dict], tasks: dict, skills: list[dict], started: float, run_at: str, models: list[str]) -> dict:
    by_skill: dict[str, dict] = {}
    for s in skills:
        by_skill[s["id"]] = {"id": s["id"], "name": s.get("name"), "task": tasks[s["id"]]["task"], "runs": []}
    for r in sorted(runs, key=lambda r: (r["skillId"], models.index(r["modelId"]) if r["modelId"] in models else 99)):
        slim = {k: v for k, v in r.items() if k not in ("output", "skillId")}
        by_skill[r["skillId"]]["runs"].append(slim)
    for entry in by_skill.values():
        ok = [r for r in entry["runs"] if r.get("callOk")]
        entry["bestVerdict"] = (
            "通过" if any(r["verdict"] == "通过" for r in ok) else
            "部分通过" if any(r["verdict"] == "部分通过" for r in ok) else
            "未通过" if ok else "调用失败")
    counts: dict[str, int] = {}
    for r in runs:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {
        "schemaVersion": 1,
        "suite": SUITE_VERSION,
        "runAt": run_at,
        "vantage": "GitHub Actions 托管运行器（美国）" if os.environ.get("GITHUB_ACTIONS") else "本地",
        "method": ("每个 Skill 配一个它本应处理的真实任务；把该 Skill 的 SKILL.md 全文注入 system prompt，"
                   f"通过 OpenAI 兼容接口调用免费模型各一次（temperature=0.2，max_tokens={MAX_TOKENS}（智谱 glm-4-flash 为 4095），流式计时，单次上限 {CALL_MAX_SEC}s）；"
                   "默认模型对某个 Skill 都没拿到可评分输出时，再用后备免费模型补测一轮，原失败记录保留；"
                   "按任务预设的确定性检查项自动判分（正则检查必需步骤/字段、Python 用 ast 解析、JS 用 node --check、HTML 解析、YAML 解析），"
                   "全部检查通过记为“通过”，≥60% 记为“部分通过”，否则“未通过”；接口报错或空输出记为“调用失败”。"
                   "judgedBy=manual 表示人工复核后改判，并附理由。模型不能执行 Skill 自带脚本/CLI，属于任务级测试，不等同原仓库端到端。"),
        "models": [{"id": m, "provider": MODELS[m]["provider"], "model": MODELS[m]["model"]} for m in models],
        "totals": {"skills": len(by_skill), "runs": len(runs), "verdicts": counts,
                   "wallTimeSec": round(time.time() - started, 1) if started else None},
        "skills": list(by_skill.values()),
    }


RESULTS_URL = "https://github.com/xdguo-design/freellm/blob/main/data/evaluations/skills-latest.json"
RECORD = [lambda r: None]
SITE_MODEL_LABEL = {"通过": "通过", "部分通过": "部分通过", "未通过": "未通过", "调用失败": "调用失败"}


def apply_to_site(latest: dict, tests_path: Path = DATA / "skill-tests.json") -> int:
    """Attach freeModelRun to every skill test entry; promote never-executed (待执行) entries.

    Entries with real sandbox results keep their level/score; we only add the free-model run.
    An entry that was only 待执行 becomes testLevel=task with the real best score when at least one
    call answered, otherwise stays blocked with status 调用失败.
    """
    payload = json.loads(tests_path.read_text(encoding="utf-8"))
    entries = payload["entries"]
    changed = 0
    date = (latest.get("runAt") or "")[:10]
    for skill in latest["skills"]:
        entry = entries.get(skill["id"])
        if entry is None:
            continue
        runs = []
        for r in skill["runs"]:
            runs.append({k: r.get(k) for k in ("provider", "model", "verdict", "score", "passedChecks", "totalChecks",
                                                 "totalMs", "judgedBy", "reviewNote", "error") if r.get(k) not in (None, "")})
        entry["freeModelRun"] = {"suite": latest["suite"], "runAt": latest["runAt"], "task": skill["task"],
                                 "bestVerdict": skill["bestVerdict"], "runs": runs,
                                 "resultsUrl": RESULTS_URL}
        if entry.get("status") == "待执行":
            answered = [r for r in skill["runs"] if r.get("callOk") and isinstance(r.get("score"), (int, float))]
            names = "、".join(f"{r['provider']} {r['model']}" for r in skill["runs"])
            if answered:
                best = max(answered, key=lambda r: r["score"])
                entry.update({
                    "testedAt": date, "testLevel": "task",
                    "status": f"免费模型任务级{skill['bestVerdict']}",
                    "environment": f"{latest['vantage']} · {names} · 只注入 SKILL.md，不执行原仓库脚本",
                    "task": skill["task"][:160],
                    "score": best["score"],
                    "evaluation": (f"把 SKILL.md 注入 system prompt 后由免费模型完成真实任务，最佳 {best['provider']} {best['model']} "
                                   f"{best['passedChecks']}/{best['totalChecks']} 项检查通过（{best['verdict']}）。"
                                   "属于任务级执行，不等同原仓库程序 E2E。"),
                    "evidence": [{"url": RESULTS_URL, "label": "查看免费模型实测原始结果", "note": skill["bestVerdict"]}],
                })
            else:
                entry.update({"testedAt": date, "status": "调用失败",
                              "evaluation": "免费模型调用均失败，未获得可评分输出，不计分。"})
        changed += 1
    tests_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def merge_runs(old: list[dict], new: list[dict]) -> list[dict]:
    """Pairs re-run now replace the stored pair; every other stored run is kept unchanged."""
    fresh = {(r["skillId"], r["modelId"]) for r in new}
    return [r for r in old if (r["skillId"], r["modelId"]) not in fresh] + list(new)


def not_executed(runs: list[dict], skills: list[dict], models: list[str], tasks: dict) -> list[dict]:
    """(skill, model) pairs with no stored run (job killed mid-run) are recorded as 调用失败, never dropped."""
    seen = {(r["skillId"], r["modelId"]) for r in runs}
    out = []
    for s in skills:
        for mid in models:
            if (s["id"], mid) not in seen and s["id"] in tasks and mid in MODELS:
                out.append({"skillId": s["id"], "modelId": mid, "provider": MODELS[mid]["provider"],
                            "model": MODELS[mid]["model"], "callOk": False, "verdict": "调用失败", "score": None,
                            "error": "未执行：本轮任务被中止，未获得结果", "checks": [], "passedChecks": 0,
                            "totalChecks": len(tasks[s["id"]]["checks"]), "output": "", "excerpt": "",
                            "skillTruncated": False})
    return out


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(DATA / "evaluations"))
    ap.add_argument("--models", default=os.environ.get("SKILL_EVAL_MODELS", ",".join(DEFAULT_MODELS)))
    ap.add_argument("--only", default=os.environ.get("SKILL_EVAL_ONLY", ""), help="comma-separated skill ids")
    ap.add_argument("--apply", action="store_true", help="apply review + merge skills-latest.json into data/skill-tests.json")
    ap.add_argument("--budget-min", type=float, default=float(os.environ.get("SKILL_EVAL_BUDGET_MIN", "66")),
                    help="wall-clock budget; calls not started in time are recorded as 调用失败 (未执行)")
    ap.add_argument("--merge", action="store_true",
                    help="keep stored runs in skills-raw.json and replace/add only the (skill, model) pairs run now")
    ap.add_argument("--regrade", action="store_true", help="re-grade stored raw outputs (no network) and rewrite latest")
    args = ap.parse_args(argv)
    if REQUEST_PATH.is_file() and not (args.apply or args.regrade):
        req = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        if req.get("only") and not args.only:
            args.only = ",".join(req["only"])
        if req.get("models") and "SKILL_EVAL_MODELS" not in os.environ and args.models == ",".join(DEFAULT_MODELS):
            args.models = ",".join(req["models"])
        args.merge = args.merge or bool(req.get("merge"))
        print(f"[request] {REQUEST_PATH.name}: only={len(req.get('only') or [])} models={args.models} merge={args.merge}", flush=True)
    out = Path(args.out)
    tasks = load_tasks()
    skills = load_skills()
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8")).get("reviews", {}) if REVIEW_PATH.is_file() else {}

    if args.apply:
        args.regrade = True  # always grade stored outputs with the current rubric before touching site data
    if args.apply or args.regrade:
        raw = json.loads((out / "skills-raw.json").read_text(encoding="utf-8"))
        scope = set(raw.get("skillIds") or [s["id"] for s in skills])
        skills = [s for s in skills if s["id"] in scope]
        runs = raw["runs"]
        for rnd in raw.get("rounds") or [{"models": raw["models"], "skillIds": [s["id"] for s in skills]}]:
            ids = set(rnd.get("skillIds") or [s["id"] for s in skills])
            runs = runs + not_executed(runs, [s for s in skills if s["id"] in ids], rnd.get("models") or raw["models"], tasks)
        if args.regrade:
            for r in runs:
                # Stored output is trimmed to RAW_CHARS; a trimmed output keeps the grade it got on the full text.
                if r.get("callOk") and len(r.get("output") or "") < RAW_CHARS and r.get("outputChars", 0) <= RAW_CHARS:
                    r.update(grade(tasks[r["skillId"]], r["output"]), judgedBy="auto")
                    r.pop("autoVerdict", None); r.pop("reviewNote", None)
        runs = apply_review(runs, review)
        latest = summarize(runs, tasks, skills, 0, raw["runAt"], raw["models"])
        latest["totals"]["wallTimeSec"] = raw.get("wallTimeSec")
        latest["vantage"] = raw.get("vantage", latest["vantage"])
        if raw.get("rounds"):
            latest["rounds"] = raw["rounds"]
        (out / "skills-latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.apply:
            n = apply_to_site(latest)
            print(f"applied free-model runs to {n} skill test entries")
        print(json.dumps(latest["totals"], ensure_ascii=False))
        return 0

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    for m in models:
        if m not in MODELS:
            raise SystemExit(f"unknown model id {m}")
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    todo = [s for s in skills if not only or s["id"] in only]
    missing = [s["id"] for s in todo if s["id"] not in tasks]
    if missing:
        raise SystemExit("skills without a task: " + ", ".join(missing))

    started = time.time()
    DEADLINE[0] = started + args.budget_min * 60
    run_at = dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M CST (UTC+08:00)")
    runs: list[dict] = []

    def provider_job(mid: str) -> list[dict]:
        cfg = MODELS[mid]
        key = os.environ.get(cfg["env"], "")
        if not key:
            print(f"[skip] {mid}: {cfg['env']} not set", flush=True)
            return [{"skillId": s["id"], "modelId": mid, "provider": cfg["provider"], "model": cfg["model"],
                     "callOk": False, "verdict": "调用失败", "score": None, "error": f"{cfg['env']} 未配置",
                     "checks": [], "passedChecks": 0, "totalChecks": len(tasks[s["id"]]["checks"]),
                     "output": "", "excerpt": "", "skillTruncated": False} for s in todo]
        res = []
        deadline = started + args.budget_min * 60

        def guarded(s):
            if time.time() > deadline:
                return {"skillId": s["id"], "modelId": mid, "provider": cfg["provider"], "model": cfg["model"],
                        "callOk": False, "verdict": "调用失败", "score": None, "error": "未执行：超出本轮时间预算",
                        "checks": [], "passedChecks": 0, "totalChecks": len(tasks[s["id"]]["checks"]),
                        "output": "", "excerpt": "", "skillTruncated": False}
            return run_one(s, tasks[s["id"]], mid, cfg, key)

        with cf.ThreadPoolExecutor(cfg["concurrency"]) as pool:
            futs = {pool.submit(guarded, s): s for s in todo}
            for fut in cf.as_completed(futs):
                r = fut.result()
                print(f"[{mid}] {r['skillId']}: {r['verdict']} {r.get('passedChecks')}/{r.get('totalChecks')} "
                      f"{r.get('totalMs', '-')}ms {(r.get('error') or '')[:80]}", flush=True)
                res.append(r)
                RECORD[0](r)
        return res

    out.mkdir(parents=True, exist_ok=True)
    prior_path = out / "skills-raw.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8")) if args.merge and prior_path.is_file() else None
    vantage = "GitHub Actions 托管运行器（美国）" if os.environ.get("GITHUB_ACTIONS") else "本地"

    def write_raw(items: list[dict]) -> None:
        if prior:  # never clobber stored runs with a partial checkpoint
            items = merge_runs(prior["runs"], items)
        raw = {"schemaVersion": 1, "suite": SUITE_VERSION, "runAt": run_at, "vantage": vantage, "models": models,
               "skillIds": sorted({s["id"] for s in todo} | set((prior or {}).get("skillIds") or [])),
               "wallTimeSec": round(time.time() - started, 1),
               "runs": sorted(items, key=lambda r: (r["skillId"], r["modelId"]))}
        (out / "skills-raw.json").write_text(scrub(json.dumps(raw, ensure_ascii=False, indent=1) + "\n"), encoding="utf-8")

    checkpoint = threading.Lock()
    done: list[dict] = []

    def record(r: dict) -> None:
        with checkpoint:  # partial results survive a killed job
            done.append(r)
            write_raw(done)

    RECORD[0] = record
    with cf.ThreadPoolExecutor(len(models)) as pool:
        for part in pool.map(provider_job, models):
            runs.extend(part)

    wall = round(time.time() - started, 1)
    write_raw(runs)
    scope, all_models, first_run_at = (skills if not only else todo), models, run_at
    if args.merge and prior:
        runs = merge_runs(prior["runs"], runs)
        scope_ids = set(prior.get("skillIds") or []) | {s["id"] for s in todo}
        scope = [s for s in skills if s["id"] in scope_ids]
        all_models = list(dict.fromkeys(list(prior.get("models") or []) + models))
        first_run_at = prior.get("runAt") or run_at
        rounds = list(prior.get("rounds") or [{"runAt": prior.get("runAt"), "models": prior.get("models"),
                                                   "skills": len(prior.get("skillIds") or [])}])
        rounds.append({"runAt": run_at, "models": models, "skills": len(todo), "skillIds": [s["id"] for s in todo]})
        merged = {"schemaVersion": 1, "suite": SUITE_VERSION, "runAt": first_run_at, "vantage": vantage,
                  "models": all_models, "skillIds": [s["id"] for s in scope], "rounds": rounds,
                  "wallTimeSec": round((prior.get("wallTimeSec") or 0) + wall, 1),
                  "runs": sorted(runs, key=lambda r: (r["skillId"], r["modelId"]))}
        (out / "skills-raw.json").write_text(scrub(json.dumps(merged, ensure_ascii=False, indent=1) + "\n"), encoding="utf-8")
        wall = merged["wallTimeSec"]
    latest = summarize(apply_review(runs, review), tasks, scope, started, first_run_at, all_models)
    if args.merge and prior:
        latest["rounds"] = rounds
    latest["totals"]["wallTimeSec"] = wall
    (out / "skills-latest.json").write_text(scrub(json.dumps(latest, ensure_ascii=False, indent=2)) + "\n", encoding="utf-8")
    print(json.dumps(latest["totals"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
