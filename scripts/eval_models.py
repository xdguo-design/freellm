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

SUITE_VERSION = "freellm-text-v2"
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
        "limit": 2,  # free tier is 50 requests/day without credits
    },
    "groq": {
        "name": "Groq",
        "env": "GROQ_API_KEY",
        "base": "https://api.groq.com/openai/v1",
        "list": True,
        "limit": 4,
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
        # Official free models only (docs.bigmodel.cn/cn/guide/models/free). GLM-5.3 / 5.3-Flash are paid.
        "list": False,
        "fixed": ["glm-4.7-flash", "glm-4-flash-250414"],
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
    "merge_intervals": (
        "assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]\n"
        "assert merge_intervals([[1,4],[4,5]]) == [[1,5]]\n"
        "assert merge_intervals([]) == []\n"
        "assert merge_intervals([[5,7],[1,2]]) == [[1,2],[5,7]]\n"
    ),
    "longest_palindrome": (
        "assert longest_palindrome('babad') in ('bab','aba')\n"
        "assert longest_palindrome('cbbd') == 'bb'\n"
        "assert longest_palindrome('a') == 'a'\n"
        "assert longest_palindrome('forgeeksskeegfor') == 'geeksskeeg'\n"
    ),
    "parse_duration": (
        "assert parse_duration('1h30m15s') == 5415\n"
        "assert parse_duration('45s') == 45\n"
        "assert parse_duration('2h') == 7200\n"
        "assert parse_duration('10m5s') == 605\n"
    ),
}

TOOLS = [
    {"type": "function", "function": {"name": "get_weather", "description": "查询某城市某天的天气预报",
        "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "城市名"},
            "date": {"type": "string", "description": "日期，如 today/tomorrow 或 YYYY-MM-DD"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}}, "required": ["city"]}}},
    {"type": "function", "function": {"name": "convert_currency", "description": "按实时汇率换算货币",
        "parameters": {"type": "object", "properties": {"amount": {"type": "number"},
            "from_currency": {"type": "string", "description": "ISO 4217 代码，如 USD"},
            "to_currency": {"type": "string", "description": "ISO 4217 代码，如 CNY"}},
            "required": ["amount", "from_currency", "to_currency"]}}},
    {"type": "function", "function": {"name": "search_flights", "description": "搜索航班",
        "parameters": {"type": "object", "properties": {"origin": {"type": "string"}, "destination": {"type": "string"},
            "date": {"type": "string"}}, "required": ["origin", "destination", "date"]}}},
]


def _haystack() -> str:
    """~8k Chinese characters of deterministic filler with two planted facts."""
    topics = ["城市更新", "乡村物流", "储能电站", "智慧农业", "跨境电商", "社区养老", "数字档案", "低空经济"]
    paras = []
    for i in range(64):
        t = topics[i % len(topics)]
        paras.append(
            f"第{i + 1}段：关于{t}的调研显示，相关单位在第{(i * 7) % 12 + 1}季度完成了阶段性评估，"
            f"参与样本约{(i * 37) % 900 + 100}个，主要问题集中在协同效率、数据口径与资金到位节奏上，"
            f"报告建议后续加强跨部门联动并建立月度复盘机制，以确保各项指标按计划推进。"
        )
    paras.insert(17, "第18段补充：经董事会批准，新项目代号定为“青鸾-7”，由西北分公司牵头实施。")
    paras.insert(49, "第50段补充：“青鸾-7”项目的首期预算核定为 318 万元，资金将于明年三月拨付。")
    return "\n".join(paras)


HAY = _haystack()

CASES = [
    # 中文知识
    {"id": "zh-1", "dim": "chinese_knowledge", "prompt": "“落霞与孤鹜齐飞”的下一句是什么？只输出这一句。", "check": ("contains", "秋水共长天一色")},
    {"id": "zh-2", "dim": "chinese_knowledge", "prompt": "王勃《滕王阁序》中的滕王阁位于今天哪座城市？只回答城市名。", "check": ("contains", "南昌")},
    {"id": "zh-3", "dim": "chinese_knowledge", "prompt": "鲁迅和周树人之间是什么关系？用一句话回答。", "check": ("regex", r"同一(个)?人|是一个人|笔名|本名|原名")},
    # 推理与数学
    {"id": "rm-1", "dim": "reasoning_math", "prompt": "一个正整数除以 3 余 2，除以 5 余 3，除以 7 余 2。满足条件的最小正整数是多少？只输出最终数字。", "check": ("number", 23)},
    {"id": "rm-2", "dim": "reasoning_math", "prompt": "水池有甲、乙两个进水管和丙一个排水管。甲单独注满需 6 小时，乙单独注满需 9 小时，丙单独排空满池需 12 小时。三管同时打开，空池几小时注满？只输出最终数字，保留两位小数。", "check": ("approx", 36 / 7)},
    {"id": "rm-3", "dim": "reasoning_math", "prompt": "英文单词 strawberry 中一共有几个字母 r？只输出数字。", "check": ("number", 3)},
    {"id": "rm-4", "dim": "reasoning_math", "prompt": "9.11 和 9.9 哪个更大？只输出更大的那个数。", "check": ("number", 9.9)},
    {"id": "rm-5", "dim": "reasoning_math", "prompt": "A 说：“B 在说谎。” B 说：“C 在说谎。” C 说：“A 和 B 都在说谎。” 每个人要么只说真话，要么只说假话。谁说的是真话？只回答一个字母。", "check": ("letter", "B")},
    # 代码
    {"id": "code-1", "dim": "coding", "prompt": "用 Python 实现函数 merge_intervals(intervals)：输入形如 [[1,3],[2,6]] 的区间列表（可能无序、可能为空），返回合并重叠区间后按起点排序的列表，端点相接也要合并。只输出代码。", "check": ("python", "merge_intervals")},
    {"id": "code-2", "dim": "coding", "prompt": "用 Python 实现函数 longest_palindrome(s)，返回字符串 s 中最长的回文子串。只输出代码。", "check": ("python", "longest_palindrome")},
    {"id": "code-3", "dim": "coding", "prompt": "用 Python 实现函数 parse_duration(text)，把 '1h30m15s'、'45s'、'2h'、'10m5s' 这类时长字符串转换为总秒数（int）。只输出代码。", "check": ("python", "parse_duration")},
    # 指令与格式
    {"id": "fmt-1", "dim": "instruction_format", "prompt": "把下列城市及其所属省份输出为 JSON 数组，每个元素形如 {\"city\":\"…\",\"province\":\"…\"}，省份不要带“省”字，按给出顺序：杭州、成都、苏州。只输出 JSON。", "check": ("json", [{"city": "杭州", "province": "浙江"}, {"city": "成都", "province": "四川"}, {"city": "苏州", "province": "江苏"}])},
    {"id": "fmt-2", "dim": "instruction_format", "prompt": "写一首主题为秋天的五言绝句：恰好 4 句，每句恰好 5 个汉字，每句一行，不要标题、作者和任何解释。", "check": ("jueju", None)},
    {"id": "fmt-3", "dim": "instruction_format", "prompt": "用中文解释什么是 API。要求：回答必须以“结论：”开头，全文不超过 60 个字，且不能出现任何英文字母。", "check": ("constrained", None)},
    # 长文本
    {"id": "long-1", "dim": "long_context", "prompt": HAY + "\n\n问题：上文中新项目的代号是什么？首期预算是多少万元？按“代号，预算”格式回答，例如：某某-1，100。", "check": ("all", ["青鸾-7", "318"])},
    {"id": "long-2", "dim": "long_context", "prompt": HAY + "\n\n问题：上文中由哪个分公司牵头实施新项目？资金何时拨付？一句话回答。", "check": ("all", ["西北", "三月"])},
    # 工具调用
    {"id": "tool-1", "dim": "tool_calling", "prompt": "帮我查一下北京明天的天气，用摄氏度。", "tools": True, "check": ("tool", {"name": "get_weather", "args": {"city": "北京"}})},
    {"id": "tool-2", "dim": "tool_calling", "prompt": "100 美元现在能换多少人民币？", "tools": True, "check": ("tool", {"name": "convert_currency", "args": {"amount": 100, "from_currency": "USD", "to_currency": "CNY"}})},
    {"id": "tool-3", "dim": "tool_calling", "prompt": "你好！用一句话介绍一下你自己。", "tools": True, "check": ("no_tool", None)},
    # 防幻觉
    {"id": "hal-1", "dim": "honesty", "prompt": "请介绍 2025 年诺贝尔数学奖得主及其主要贡献。", "check": ("regex", r"没有诺贝尔数学奖|不设|没有设立|并没有|并不存在|不存在|并无|没有.{0,6}数学奖|未设")},
    {"id": "hal-2", "dim": "honesty", "prompt": "请总结张伟明 2019 年发表在 Nature 上的论文《基于量子蚁群算法的长江鲟鱼迁徙预测》的主要结论。", "check": ("regex", r"无法|找不到|未能找到|没有找到|不确定|无法核实|没有相关|并未|不存在|查不到|未检索到|没有.{0,6}记录|可能不存在|虚构")},
    # hal-3 must explicitly deny that chapter 121 exists (or state the book has only 120 chapters).
    # A bare "一百二十回" / "不存在" also appears in fabricated answers ("合并到第120回"), so it is not enough.
    {"id": "hal-3", "dim": "honesty", "prompt": "《红楼梦》第一百二十一回讲了什么？", "check": ("denial", r"(?:并)?没有(?:所谓的?)?[“\"「]?第?(?:一百二十一|121)\s*回|(?:第?(?:一百二十一|121)\s*回)[”\"」]?.{0,8}(?:并)?不存在|不存在[“\"「]?第?(?:一百二十一|121)\s*回|(?:只有|仅有|仅|共|共有|一共|总共)\s*(?:一百二十|120)\s*回|no chapter 121|there is no (?:such )?chapter|only (?:has |contains )?120 chapters|contains 120 chapters|has 120 chapters")},
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
    if cfg.get("fixed"):
        return list(cfg["fixed"])[: cfg["limit"]]
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
        nums = tuple(-float(x) for x in re.findall(r"\d+(?:\.\d+)?", low)[:2])
        return (pos, nums, low)

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
    text = re.sub(r"^.*?</think>", "", text, flags=re.S)  # opening tag swallowed upstream
    return text.strip()


def extract_code(text: str) -> str:
    m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.S)
    return (max(m, key=len) if m else text).strip()


def _nums(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))]


def _han(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def score(case: dict, output: str, tool_calls: list[dict]) -> bool:
    kind, expected = case["check"]
    out = strip_reasoning(output)
    if kind == "tool":
        if not tool_calls:
            return False
        call = tool_calls[0]
        if call.get("name") != expected["name"]:
            return False
        try:
            args = json.loads(call.get("arguments") or "{}")
        except json.JSONDecodeError:
            return False
        for k, v in expected["args"].items():
            got = args.get(k)
            if isinstance(v, (int, float)):
                try:
                    if float(got) != float(v):
                        return False
                except (TypeError, ValueError):
                    return False
            elif not isinstance(got, str) or v.lower() not in got.lower():
                return False
        return True
    if kind == "no_tool":
        return not tool_calls and bool(out)
    if tool_calls and not out:
        return False
    if kind == "contains":
        return expected in out
    if kind == "all":
        return all(x in out for x in expected)
    if kind == "regex":
        return re.search(expected, out) is not None
    if kind == "denial":
        plain = re.sub(r"[*_`#]", "", out)
        return re.search(expected, plain, flags=re.I) is not None
    if kind == "number":
        nums = _nums(out)
        return bool(nums) and abs(nums[-1] - float(expected)) < 1e-9
    if kind == "approx":
        nums = _nums(out)
        return bool(nums) and abs(nums[-1] - float(expected)) < 0.011
    if kind == "letter":
        plain = re.sub(r"[*`#\s]", "", out)
        m = re.match(r"^(?:答案[是为：:]?)?([ABC])(?![A-Za-z])", plain)
        if not m:
            hits = re.findall(r"答案[是为：:]*([ABC])|([ABC])(?:说的?是真话|说真话)", plain)
            m_letter = (hits[-1][0] or hits[-1][1]) if hits else None
        else:
            m_letter = m.group(1)
        return m_letter == expected
    if kind == "json":
        m = re.search(r"[\[{].*[\]}]", out, flags=re.S)
        try:
            return m is not None and json.loads(m.group(0)) == expected
        except json.JSONDecodeError:
            return False
    if kind == "jueju":
        lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
        return len(lines) == 4 and all(_han(l) == 5 and len(re.sub(r"[\u4e00-\u9fff，。、！？,.!?；;\s]", "", l)) == 0 for l in lines)
    if kind == "constrained":
        return out.startswith("结论：") and not re.search(r"[A-Za-z]", out) and len(re.sub(r"\s", "", out)) <= 60
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


def _stream(cfg: dict, key: str, body: dict) -> dict:
    start = time.perf_counter()
    first = None
    chunks: list[str] = []
    reasoning_chars = 0
    usage: dict = {}
    calls: dict[int, dict] = {}
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
                think = delta.get("reasoning_content") or delta.get("reasoning") or ""
                reasoning_chars += len(think)
                if (piece or think or delta.get("tool_calls")) and first is None:
                    first = time.perf_counter()
                chunks.append(piece)
                for tc in delta.get("tool_calls") or []:
                    slot = calls.setdefault(tc.get("index", 0), {"name": "", "arguments": ""})
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        slot["name"] = fn["name"]
                    if fn.get("arguments"):
                        slot["arguments"] += fn["arguments"]
    end = time.perf_counter()
    return {"start": start, "first": first, "end": end, "output": "".join(chunks),
            "reasoningChars": reasoning_chars, "usage": usage,
            "toolCalls": [calls[i] for i in sorted(calls)]}


def run_case(cfg: dict, key: str, model: str, case: dict) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": case["prompt"]}],
        "temperature": 0,
        "max_tokens": 4096,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if case.get("tools"):
        body["tools"] = TOOLS
    res = None
    for attempt in range(2):
        try:
            res = _stream(cfg, key, body)
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "ignore")[:240]
            if exc.code == 429 and attempt == 0 and "quota" not in detail and "余额" not in detail:
                time.sleep(25)
                continue
            return {"case": case["id"], "dim": case["dim"], "ok": False, "error": f"HTTP {exc.code}", "detail": detail}
        except Exception as exc:  # noqa: BLE001
            if attempt == 0:
                time.sleep(5)
                continue
            return {"case": case["id"], "dim": case["dim"], "ok": False, "error": type(exc).__name__}
    output = res["output"]
    usage = res["usage"]
    out_tokens = usage.get("completion_tokens") or max(1, (len(output) + res["reasoningChars"]) // 2)
    gen_time = res["end"] - (res["first"] or res["start"])
    return {
        "case": case["id"],
        "dim": case["dim"],
        "ok": True,
        "pass": score(case, output, res["toolCalls"]),
        "ttftMs": round(((res["first"] or res["end"]) - res["start"]) * 1000),
        "totalMs": round((res["end"] - res["start"]) * 1000),
        "outputTokens": out_tokens,
        "reasoningChars": res["reasoningChars"],
        "tokensPerSec": round(out_tokens / gen_time, 1) if gen_time > 0.2 else None,
        "toolCalls": res["toolCalls"],
        "output": output[:1200],
    }


def pct(values: list[float], q: float) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    idx = min(len(vals) - 1, max(0, round(q * (len(vals) - 1))))
    return vals[idx]


DIM_LABELS = {
    "chinese_knowledge": "中文知识",
    "reasoning_math": "推理数学",
    "coding": "代码",
    "instruction_format": "指令格式",
    "long_context": "长文本",
    "tool_calling": "工具调用",
    "honesty": "防幻觉",
}
FATAL = {"HTTP 401", "HTTP 402", "HTTP 403", "HTTP 404"}


def eval_model(pid: str, cfg: dict, key: str, model: str) -> dict:
    results = []
    for case in CASES:
        res = run_case(cfg, key, model, case)
        results.append(res)
        if not res["ok"] and (res.get("error") in FATAL or "余额" in res.get("detail", "") or "insufficient_quota" in res.get("detail", "")):
            if not any(r["ok"] for r in results):
                break  # not available for free on this account; don't burn quota
        time.sleep(3.2 if pid in {"openrouter", "groq"} else 1.0)
    answered = [r for r in results if r["ok"]]
    passed = sum(1 for r in answered if r.get("pass"))
    dims: dict[str, list[bool]] = {d: [] for d in DIM_LABELS}
    for r in results:
        dims[r["dim"]].append(bool(r.get("pass")))
    dim_scores = {d: round(100 * sum(v) / len(v)) for d, v in dims.items() if v}
    errors = sorted({r["error"] for r in results if not r["ok"]})
    ttfts = [r.get("ttftMs") for r in answered]
    tps = [r.get("tokensPerSec") for r in answered]
    reasoning = sum(1 for r in answered if r.get("reasoningChars", 0) > 50 or "</think>" in r.get("output", ""))
    return {
        "providerId": pid,
        "provider": cfg["name"],
        "model": model,
        "available": bool(answered),
        "score": round(100 * passed / len(CASES)) if answered else None,
        "passed": passed,
        "answered": len(answered),
        "attempted": len(results),
        "total": len(CASES),
        "successRate": round(100 * len(answered) / len(results)) if results else 0,
        "dimensions": dim_scores,
        "p50TtftMs": pct(ttfts, 0.5),
        "p95TtftMs": pct(ttfts, 0.95),
        "p50TotalMs": pct([r.get("totalMs") for r in answered], 0.5),
        "medianTokensPerSec": pct(tps, 0.5),
        "thinksByDefault": reasoning >= max(3, len(answered) // 2),
        "errors": errors,
        "errorDetail": next((r.get("detail", "") for r in results if not r["ok"]), ""),
        "cases": results,
    }


def rescore(out_dir: Path, case_ids: list[str]) -> int:
    """Re-grade stored outputs for the given cases after a grader fix (no API calls)."""
    path = out_dir / "latest.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in CASES}
    for m in report.get("models", []):
        results = m.get("cases") or []
        for r in results:
            if r.get("case") in case_ids and r.get("ok"):
                old = bool(r.get("pass"))
                r["pass"] = score(by_id[r["case"]], r.get("output", ""), r.get("toolCalls") or [])
                if old != r["pass"]:
                    print(f"{m['providerId']} {m['model']} {r['case']}: {old} -> {r['pass']}")
        answered = [r for r in results if r.get("ok")]
        passed = sum(1 for r in answered if r.get("pass"))
        dims: dict[str, list[bool]] = {d: [] for d in DIM_LABELS}
        for r in results:
            dims[r["dim"]].append(bool(r.get("pass")))
        m["passed"] = passed
        m["score"] = round(100 * passed / len(CASES)) if answered else None
        m["dimensions"] = {d: round(100 * sum(v) / len(v)) for d, v in dims.items() if v}
    report["models"].sort(key=lambda r: (r["score"] is None, -(r["score"] or 0), r["p50TtftMs"] or 1e9))
    text = json.dumps(report, ensure_ascii=False, indent=1) + "\n"
    path.write_text(text, encoding="utf-8")
    stamp = (report.get("runAt") or "")[:10]
    if stamp and (out_dir / f"{stamp}.json").exists():
        (out_dir / f"{stamp}.json").write_text(text, encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/evaluations")
    ap.add_argument("--providers", default=os.environ.get("EVAL_PROVIDERS") or ",".join(PROVIDERS))
    ap.add_argument("--merge", action="store_true", help="merge into existing latest.json (replace same provider)")
    ap.add_argument("--rescore", default="", help="comma-separated case ids: re-grade stored outputs in latest.json without calling any API")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.rescore:
        return rescore(out_dir, [c for c in args.rescore.split(",") if c])

    plans = []
    skipped = []
    for pid in [p for p in args.providers.split(",") if p]:
        cfg = PROVIDERS[pid]
        key = os.environ.get(cfg["env"], "").strip()
        if not key:
            skipped.append({"providerId": pid, "reason": f"{cfg['env']} not set"})
            continue
        lim = cfg["limit"]
        cfg = dict(cfg, limit=lim * 3)  # extra candidates replace models that 404 for this account
        cands = list_models(cfg, key)
        print(f"{cfg['name']}: candidates {cands}")
        if not cands:
            skipped.append({"providerId": pid, "reason": "no free text models found"})
        plans.append((pid, cfg, key, cands, lim))

    def run_provider(plan):
        pid, cfg, key, cands, lim = plan
        out, ok = [], 0
        for model in cands:
            if ok >= lim:
                break
            r = eval_model(pid, cfg, key, model)
            out.append(r)
            ok += 1 if r["available"] else 0
        return out

    results = []
    with cf.ThreadPoolExecutor(max_workers=len(plans) or 1) as pool:
        for chunk in pool.map(run_provider, plans):
            results.extend(chunk)

    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    if args.merge and (out_dir / "latest.json").exists():
        prev = json.loads((out_dir / "latest.json").read_text(encoding="utf-8"))
        if prev.get("suite") == SUITE_VERSION:
            ran = {p[0] for p in plans}
            results = [m for m in prev.get("models", []) if m["providerId"] not in ran] + results

    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0), r["p50TtftMs"] or 1e9))
    report = {
        "schemaVersion": 2,
        "suite": SUITE_VERSION,
        "runAt": now.isoformat(timespec="seconds"),
        "vantage": os.environ.get("EVAL_VANTAGE", "GitHub Actions 托管运行器（美国）"),
        "method": "每个模型用同一组 22 道固定题、7 个维度调用一次，temperature=0，max_tokens=4096，流式记录首 token 延迟与生成速度；全部自动评分：Python 题实际运行单元测试，工具调用题检查函数名与参数，长文本题在约 8000 字干扰文本中检索两处信息，防幻觉题检查模型是否拒绝编造。",
        "dimensions": DIM_LABELS,
        "cases": [{"id": c["id"], "dim": c["dim"], "prompt": (c["prompt"] if not c["id"].startswith("long") else "[约 8000 字干扰文本]\n" + c["prompt"].split("\n\n")[-1])} for c in CASES],
        "skipped": skipped,
        "models": results,
    }
    stamp = now.strftime("%Y-%m-%d")
    for name in (f"{stamp}.json", "latest.json"):
        (out_dir / name).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("\n| 模型 | 提供方 | 总分 | " + " | ".join(DIM_LABELS.values()) + " | 首token p50 | tok/s | 成功率 | 错误 |")
    for r in results:
        dims = " | ".join(str(r["dimensions"].get(d, "-")) for d in DIM_LABELS)
        print(f"| {r['model']} | {r['provider']} | {r['score']} | {dims} | {r['p50TtftMs']} | {r['medianTokensPerSec']} | {r['successRate']}% | {','.join(r['errors'])} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
