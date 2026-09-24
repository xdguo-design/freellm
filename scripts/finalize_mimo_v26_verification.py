#!/usr/bin/env python3
"""Persist the verified MiMo-V2.6-Flash live-test result and refresh copy.

This is intentionally idempotent. It records only evidence already produced by
the required GitHub Actions OpenCode CLI live gate.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFERS = ROOT / "data" / "offers.json"
WECHAT = ROOT / "docs" / "wechat" / "mimo-v2-6-flash.html"
TESTS = ROOT / "tests" / "test_mimo_v26.py"

RUN_URL = "https://github.com/xdguo-design/freellm/actions/runs/35943191315"
TESTED_AT = "2026-09-24"


def update_offer() -> None:
    rows = json.loads(OFFERS.read_text(encoding="utf-8"))
    offer = next(row for row in rows if row.get("id") == "opencode-zen-free")

    offer["lastVerifiedAt"] = TESTED_AT
    offer["checkedSummary"] = (
        "2026-09-24 / official OpenCode Zen docs + live model catalog + real OpenCode CLI generation"
    )
    offer["notes"] = (
        "不要把 OpenCode 的限时免费误写成 Xiaomi 官方 API 免费。OpenCode 说明免费期交互数据可能用于改进模型，"
        "不应提交个人、机密或敏感数据。2026-09-24 已通过官方 OpenCode CLI 对 "
        "opencode/mimo-v2.6-flash-free 完成一次真实生成并返回 MiMo OK；Zen 直连 HTTP chat completions "
        "仍需 Zen API Key。"
    )
    offer["freeLLMTest"] = {
        "testLevel": "live",
        "status": "passed",
        "testedAt": TESTED_AT,
        "actualUsageVerified": True,
        "task": (
            "核验 OpenCode Zen 是否真实公开 MiMo-V2.6-Flash Free、当前模型 ID、免费定价和调用路径，"
            "并通过官方 OpenCode CLI 对免费模型路径完成一次真实端到端生成。"
        ),
        "method": [
            "打开 OpenCode Zen 官方文档，核对 MiMo-V2.6-Flash Free、模型 ID、chat completions endpoint 与限时免费定价。",
            "访问 OpenCode Zen 公共 /zen/v1/models，确认 mimo-v2.6-flash-free 仍在实时模型目录。",
            "在 GitHub Actions 安装官方 OpenCode CLI 1.18.32，并刷新 OpenCode 模型列表。",
            "使用 opencode run --model opencode/mimo-v2.6-flash-free --format json 发送最小真实生成请求。",
            "要求真实助手输出包含 MiMo OK；无 mock、无 skip、无仓库 API Key。",
        ],
        "result": (
            "真实生成通过：2026-09-24 GitHub Actions 使用 OpenCode CLI 调用 "
            "opencode/mimo-v2.6-flash-free，模型返回 MiMo OK，记录延迟 6372 ms，"
            "actualUsageVerified=true。"
        ),
        "limitations": (
            "本次证明 OpenCode 官方 CLI 免费模型路径至少一次真实生成可用；不代表永久免费，也不代表已经验证"
            "持续限流、工具调用、多模态输入、长上下文稳定性或整体生成质量。Zen 直连 HTTP chat completions "
            "仍需要 Zen API Key。"
        ),
        "evidence": [
            {
                "label": "OpenCode Zen 官方模型与定价",
                "url": "https://opencode.ai/docs/en/zen/",
                "note": "核验模型 ID、endpoint、Free 定价与 limited-time free 说明",
            },
            {
                "label": "OpenCode Zen 实时模型目录",
                "url": "https://opencode.ai/zen/v1/models",
                "note": "公开目录返回 mimo-v2.6-flash-free",
            },
            {
                "label": "FreeLLM GitHub Actions 真实生成记录",
                "url": RUN_URL,
                "note": "OpenCode CLI 实际返回 MiMo OK；latencyMs=6372；actualUsageVerified=true",
            },
            {
                "label": "Xiaomi MiMo-V2.6-Flash 官方模型页",
                "url": "https://mimo.mi.com/models/en-US/mimo-v2.6-flash",
                "note": "核验 1M context、128K max output、100 RPM / 10M TPM 与 Xiaomi 官方付费 API 价格",
            },
        ],
    }

    OFFERS.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once_or_verify(text: str, old: str, new: str, marker: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if marker in text:
        return text
    raise RuntimeError(f"Unable to update expected block: {marker}")


def update_wechat() -> None:
    page = WECHAT.read_text(encoding="utf-8")
    page = page.replace(
        "FREELLM · MODEL NOTE · 2026-09-23",
        "FREELLM · MODEL NOTE · 2026-09-24",
        1,
    )
    old_li = (
        "      <li>核对 Hugging Face 官方模型仓库：可按官方示例用 vLLM / SGLang 自托管。</li>\n"
    )
    new_li = (
        old_li
        + "      <li><strong>真实生成已通过：</strong>2026-09-24 在 GitHub Actions 中使用官方 OpenCode CLI "
          "调用 <code>opencode/mimo-v2.6-flash-free</code>，模型实际返回 <code>MiMo OK</code>，"
          "记录延迟约 6.37 秒。</li>\n"
    )
    if "模型实际返回 <code>MiMo OK</code>" not in page:
        if old_li not in page:
            raise RuntimeError("Unable to find WeChat verification list")
        page = page.replace(old_li, new_li, 1)

    old_box = (
        '    <div style="padding:14px 16px;border-radius:12px;background:#fff3df;color:#7a581e;'
        'font-size:14px;line-height:1.7;"><strong>测试边界：</strong>本轮没有用户的 OpenCode Zen API Key，'
        '因此没有伪造“实际生成成功”。当前已完成公开模型目录、官方文档、定价和访问路径核验；'
        '真正的端到端推理请求仍需凭据后再补最后一步。</div>'
    )
    new_box = (
        '    <div style="padding:14px 16px;border-radius:12px;background:#eaf8f1;color:#25634f;'
        'font-size:14px;line-height:1.7;"><strong>真实测试结果：</strong>OpenCode 官方 CLI 的 '
        '<code>opencode/mimo-v2.6-flash-free</code> 已完成真实端到端 generation，并返回 '
        '<code>MiMo OK</code>。这证明的是 OpenCode CLI 免费模型路径当前可用；OpenCode Zen 的直连 HTTP '
        'chat completions 仍需 Zen API Key，小米官方 API 仍是付费 API，不能混为一谈。</div>'
    )
    page = replace_once_or_verify(page, old_box, new_box, "真实测试结果：")
    WECHAT.write_text(page, encoding="utf-8")


def update_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    old_offer_tail = '''    assert "Xiaomi" in offer["why"]\n    assert "paid official API" in offer["why"]\n'''
    new_offer_tail = '''    assert "Xiaomi" in offer["why"]\n    assert "paid official API" in offer["why"]\n    assert offer["freeLLMTest"]["status"] == "passed"\n    assert offer["freeLLMTest"]["testLevel"] == "live"\n    assert offer["freeLLMTest"]["actualUsageVerified"] is True\n    assert "MiMo OK" in offer["freeLLMTest"]["result"]\n'''
    if 'assert offer["freeLLMTest"]["actualUsageVerified"] is True' not in text:
        if old_offer_tail not in text:
            raise RuntimeError("Unable to update OpenCode live-test assertions")
        text = text.replace(old_offer_tail, new_offer_tail, 1)

    old_article = '    assert "端到端推理请求仍需凭据" in page\n'
    new_article = (
        '    assert "模型实际返回 <code>MiMo OK</code>" in page\n'
        '    assert "真实测试结果：" in page\n'
        '    assert "直连 HTTP" in page\n'
    )
    if 'assert "真实测试结果：" in page' not in text:
        if old_article not in text:
            raise RuntimeError("Unable to update WeChat assertions")
        text = text.replace(old_article, new_article, 1)

    TESTS.write_text(text, encoding="utf-8")


def main() -> int:
    update_offer()
    update_wechat()
    update_tests()
    print(
        json.dumps(
            {
                "status": "persisted",
                "offer": "opencode-zen-free",
                "actualUsageVerified": True,
                "testedAt": TESTED_AT,
                "evidence": RUN_URL,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
