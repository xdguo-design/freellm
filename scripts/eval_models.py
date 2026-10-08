#!/usr/bin/env python3
"""FreeLLM real model evaluation (suite text-api-v1, lite).

Calls free models on each provider with the API keys found in the
environment, scores a fixed versioned test set automatically, and writes
reproducible results with raw outputs.

Keys are read from env only and never printed or written to disk.
Only free models are called: OpenRouter ``:free`` variants, Groq free plan,
ModelScope API-Inference, NVIDIA free endpoints, Zhipu ``*flash*`` models and
SiliconFlow models listed at ¥0 in data/offers.json.

Usage:
    python scripts/eval_models.py --out data/evaluations
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SUITE_VERSION = "text-api-lite-v1"
TIMEOUT = 90

PROVIDERS = {
    "siliconflow": {
        "name": "硅基流动 SiliconFlow",
        "env": "SILICONFLOW_API_KEY",
        "base": "https://api.siliconflow.cn/v1",
        "list": True,
        # Only models the official price list shows at ¥0 (see data/offers.json).
        "match": ["xing4", "hunyuan-mt-7b"],
        "limit": 2,
    },
    "openrouter": {
        "name": "OpenRouter",
        "env": "OPENROUTER_API_KEY",
        "base": "https://openrouter.ai/api/v1",
        "list": True,
        "free_suffix": ":free",
        "limit": 4,  # free tier is 50 requests/day without credits
    },
    "groq": {
        "name": "Groq",
        "env": "GROQ_API_KEY",
        "base": "https://api.groq.com/openai/v1",
        "list": True,
        "limit": 3,
    },
    "modelscope": {
        "name": "魔搭 ModelScope",
        "env": "MODELSCOPE_API_KEY",
        "base": "https://api-inference.modelscope.cn/v1",
        "list": True,
        "limit": 4,
    },
    "zhipu": {
        "name": "智谱 BigModel",
        "env": "ZHIPU_API_KEY",
        "base": "https://open.bigmodel.cn/api/paas/v4",
        "list": True,
        "match": ["flash"],
        "fallback": ["glm-4.7-flash", "glm-4.5-flash", "glm-4-flash-250414", "glm-4-flash"],
        "limit": 2,
    },
    "nvidia": {
        "name": "NVIDIA NIM",
        "env": "NVIDIA_API_KEY",
        "base": "https://integrate.api.nvidia.com/v1",
        "list": True,
        "limit": 5,
    },
}

EXCLUDE = re.compile(
    r"embed|rerank|whisper|tts|speech|audio|guard|safety|moderat|ocr|vision|-vl|vl-|image|video|"
    r"detector|parse|clip|lyria|reward|kolors|flux|diffusion|cosmos|deplot|retriev|translate|sdxl|"
    r"bge|nv-|paligemma|neva|fuyu|kosmos|riva|asr|orpheus|playai|compound",
    re.I,
)
PREFER = ["deepseek", "qwen", "glm", "kimi", "gpt-oss", "minimax", "llama", "gemma", "mistral", "nemotron", "ling", "hunyuan", "xing"]

PYTHON_TESTS = {
    "is_prime": "assert is_prime(2) and is_prime(97) and not is_prime(1) and not is_prime(91) and not is_prime(0)",
    "reverse_words": "assert reverse_words('I love free AI') == 'AI free love I'\nassert reverse_words('hello') == 'hello'",
}

CASES = [
    {"id": "zh-fact-1", "dim": "chinese_factual", "prompt": "中国的首都是哪座城市？只回答城市名。", "check": ("contains", "北京")},
    {"id": "zh-fact-2", "dim": "chinese_factual", "prompt": "《红楼梦》的作者是谁？只回答姓名。", "check": ("contains", "曹雪芹")},
    {"id": "math-1", "dim": "reasoning_math", "prompt": "计算 37×43，只输出最终数字。", "check": ("number", "1591")},
    {"id": "math-2", "dim": "reasoning_math", "prompt": "一件衣服原价 200 元，先打八折，再减 30 元，最后多少元？只输出最终数字。", "check": ("number", "130")},
    {"id": "logic-1", "dim": "reasoning_math", "prompt": "小明比小红高，小红比小刚高。三个人中谁最矮？只回答名字。", "check": ("contains", "小刚")},
    {"id": "py-1", "dim": "python", "prompt": "用 Python 写一个函数 is_prime(n)，判断 n 是否为质数，返回 True 或 False。只输出代码。", "check": ("python", "is_prime")},
    {"id": "py-2", "dim": "python", "prompt": "用 Python 写一个函数 reverse_words(s)，把用空格分隔的句子中的单词顺序反转后返回字符串。只输出代码。", "check": ("python", "reverse_words")},
    {"id": "fmt-1", "dim": "instruction_format", "prompt": "输出一个 JSON 对象，包含 name（字符串）和 age（整数）两个字段，name 为“张三”，age 为 28。只输出 JSON，不要任何解释。", "check": ("json", {"name": "张三", "age": 28})},
    {"id": "fmt-2", "dim": "instruction_format", "prompt": "列出三种水果，用英文逗号分隔，只输出这三个词，不要编号和其他文字。", "check": ("list3", None)},
    {"id": "ctx-1", "dim": "context_extraction", "prompt": "阅读下面的通知，回答会议日期，只按 YYYY-MM-DD 格式输出。\n通知：经研究决定，第三届开源模型开发者大会原定于十月举行，现推迟至2026年11月3日在杭州国际博览中心召开，报名截止时间为10月25日。", "check": ("contains", "2026-11-03")},
]


def _request(url: str, key: str, body: dict | None = None, stream: bool = False):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if body is not None else "GET",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://freellm.top",
            "X-Title": "FreeLLM eval",
            "User-Agent": "freellm-eval/1.0",
        },
    )
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def list_models(cfg: dict, key: str) -> list[str]:
    ids: list[str] = []
    try:
        with _request(cfg["base"] + "/models", key) as resp:
            payload = json.loads(resp.read().decode())
        for item in payload.get("data", []):
            mid = str(item.get("id") or "")
            if not mid:
                continue
            if cfg.get("free_suffix") and not mid.endswith(cfg["free_suffix"]):
                continue
            arch = item.get("architecture") or {}
            if arch and "text" not in (arch.get("output_modalities") or ["text"]):
                continue
            ids.append(mid)
    except Exception as exc:  # noqa: BLE001 - recorded, not fatal
        print(f"  list failed for {cfg['name']}: {type(exc).__name__}", file=sys.stderr)
    if cfg.get("match"):
        ids = [m for m in ids if any(p in m.lower() for p in cfg["match"])]
    ids = [m for m in ids if not EXCLUDE.search(m)]
    if not ids and cfg.get("fallback"):
        ids = list(cfg["fallback"])

    def rank(mid: str) -> tuple:
        low = mid.lower()
        pos = next((i for i, p in enumerate(PREFER) if p in low), len(PREFER))
        return (pos, low)

    # One model per family first, so the sample is diverse.
    picked, seen = [], set()
    for mid in sorted(ids, key=rank):
        fam = next((p for p in PREFER if p in mid.lower()), mid)
        if fam in seen:
            continue
        seen.add(fam)
        picked.append(mid)
    for mid in sorted(ids, key=rank):
        if mid not in picked:
            picked.append(mid)
    return picked[: cfg["limit"]]


def strip_reasoning(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    return text.strip()


def extract_code(text: str) -> str:
    m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.S)
    return (m[0] if m else text).strip()


def score(case: dict, output: str) -> bool:
    kind, expected = case["check"]
    out = strip_reasoning(output)
    if kind == "contains":
        return expected in out
    if kind == "number":
        nums = re.findall(r"-?\d+(?:\.\d+)?", out.replace(",", ""))
        return bool(nums) and float(nums[-1]) == float(expected)
    if kind == "json":
        m = re.search(r"\{.*\}", out, flags=re.S)
        try:
            return m is not None and json.loads(m.group(0)) == expected
        except json.JSONDecodeError:
            return False
    if kind == "list3":
        line = out.strip().strip("。.")
        if "\n" in line:
            return False
        parts = [p.strip() for p in re.split(r"[,，]", line) if p.strip()]
        return len(parts) == 3 and all(len(p) <= 20 for p in parts)
    if kind == "python":
        code = extract_code(out) + "\n\n" + PYTHON_TESTS[expected] + "\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
            fh.write(code)
            path = fh.name
        try:
            proc = subprocess.run([sys.executable, path], capture_output=True, timeout=10)
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        finally:
            os.unlink(path)
    return False


def run_case(cfg: dict, key: str, model: str, case: dict) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": case["prompt"]}],
        "temperature": 0,
        "max_tokens": 1024,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    start = time.perf_counter()
    first = None
    chunks: list[str] = []
    usage = {}
    try:
        with _request(cfg["base"] + "/chat/completions", key, body) as resp:
            for raw in resp:
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
                    if (piece or delta.get("reasoning_content") or delta.get("reasoning")) and first is None:
                        first = time.perf_counter()
                    chunks.append(piece)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:200]
        return {"case": case["id"], "ok": False, "error": f"HTTP {exc.code}", "detail": detail}
    except Exception as exc:  # noqa: BLE001
        return {"case": case["id"], "ok": False, "error": type(exc).__name__}
    end = time.perf_counter()
    output = "".join(chunks)
    out_tokens = usage.get("completion_tokens") or max(1, len(output) // 2)
    gen_time = end - (first or start)
    return {
        "case": case["id"],
        "dim": case["dim"],
        "ok": True,
        "pass": score(case, output),
        "ttftMs": round(((first or end) - start) * 1000),
        "totalMs": round((end - start) * 1000),
        "outputTokens": out_tokens,
        "tokensPerSec": round(out_tokens / gen_time, 1) if gen_time > 0.05 else None,
        "output": output[:1500],
    }


def median(values: list[float]) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else round((vals[mid - 1] + vals[mid]) / 2, 1)


def eval_model(pid: str, cfg: dict, key: str, model: str) -> dict:
    results = []
    for case in CASES:
        res = run_case(cfg, key, model, case)
        results.append(res)
        if not res["ok"] and res.get("error") in {"HTTP 401", "HTTP 402", "HTTP 403", "HTTP 404"}:
            break  # model not available for free on this account; don't burn quota
        time.sleep(3.5 if pid in {"openrouter", "groq"} else 1.0)
    answered = [r for r in results if r["ok"]]
    passed = sum(1 for r in answered if r.get("pass"))
    dims: dict[str, list[bool]] = {}
    for r in answered:
        dims.setdefault(r["dim"], []).append(bool(r.get("pass")))
    errors = sorted({r["error"] for r in results if not r["ok"]})
    return {
        "providerId": pid,
        "provider": cfg["name"],
        "model": model,
        "available": bool(answered),
        "score": round(100 * passed / len(CASES)) if answered else None,
        "passed": passed,
        "answered": len(answered),
        "total": len(CASES),
        "dimensions": {d: round(100 * sum(v) / len(v)) for d, v in dims.items()},
        "medianTtftMs": median([r.get("ttftMs") for r in answered]),
        "medianTokensPerSec": median([r.get("tokensPerSec") for r in answered]),
        "errors": errors,
        "cases": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/evaluations")
    ap.add_argument("--providers", default=",".join(PROVIDERS))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    skipped = []
    for pid in args.providers.split(","):
        cfg = PROVIDERS[pid]
        key = os.environ.get(cfg["env"], "").strip()
        if not key:
            skipped.append({"providerId": pid, "reason": f"{cfg['env']} not set"})
            continue
        models = list_models(cfg, key)
        print(f"{cfg['name']}: {len(models)} model(s) selected: {models}")
        if not models:
            skipped.append({"providerId": pid, "reason": "no free text models found"})
        for model in models:
            jobs.append((pid, cfg, key, model))

    results = []
    # Providers run in parallel; models within one provider run sequentially to respect rate limits.
    by_provider: dict[str, list] = {}
    for job in jobs:
        by_provider.setdefault(job[0], []).append(job)

    def run_provider(items):
        return [eval_model(*item) for item in items]

    with cf.ThreadPoolExecutor(max_workers=len(by_provider) or 1) as pool:
        for chunk in pool.map(run_provider, by_provider.values()):
            results.extend(chunk)

    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0), r["medianTtftMs"] or 1e9))
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    report = {
        "schemaVersion": 1,
        "suite": SUITE_VERSION,
        "runAt": now.isoformat(timespec="seconds"),
        "vantage": os.environ.get("EVAL_VANTAGE", "GitHub Actions hosted runner (US)"),
        "method": "每个模型用同一组 10 道固定题（中文事实、推理数学、Python、格式遵循、长文抽取）调用一次，temperature=0，流式记录首 token 延迟与生成速度；自动评分，Python 题实际执行单元测试。",
        "cases": [{k: c[k] for k in ("id", "dim", "prompt")} for c in CASES],
        "skipped": skipped,
        "models": results,
    }
    stamp = now.strftime("%Y-%m-%d")
    for name in (f"{stamp}.json", "latest.json"):
        (out_dir / name).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("\n| 模型 | 提供方 | 得分 | 首token ms | tok/s | 错误 |")
    for r in results:
        print(f"| {r['model']} | {r['provider']} | {r['score']} | {r['medianTtftMs']} | {r['medianTokensPerSec']} | {','.join(r['errors'])} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
