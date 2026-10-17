"""FreeLLM evaluation blocks on secondary pages (providers/*, models/<slug>/, category/*).

Uses a fixed fixture instead of data/evaluations/latest.json so the weekly
model-eval run cannot break these contracts.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_seo_pages as seo  # noqa: E402
from scripts import eval_pages  # noqa: E402

DIMS = {k: 100 for k in eval_pages.DIM_ORDER}

FIXTURE = {
    "suite": "freellm-text-v2",
    "runAt": "Fri 2026-10-09 9:30 AM CST (UTC+08:00)",
    "vantage": "GitHub Actions 托管运行器（美国）",
    "cases": 22,
    "dimensions": {
        "chinese_knowledge": "中文知识", "reasoning_math": "推理数学", "coding": "代码", "instruction_format": "指令格式",
        "long_context": "长文本", "tool_calling": "工具调用", "honesty": "防幻觉",
    },
    "models": [
        {"providerId": "groq", "provider": "Groq", "model": "openai/gpt-oss-120b", "available": True, "score": 95,
         "answered": 22, "total": 22, "successRate": 100, "dimensions": {**DIMS, "honesty": 67},
         "p50TtftMs": 204, "p95TtftMs": 500, "medianTokensPerSec": 483.4},
        {"providerId": "groq", "provider": "Groq", "model": "allam-2-7b", "available": True, "score": 9,
         "answered": 17, "total": 22, "successRate": 77, "dimensions": {**DIMS, "coding": 0},
         "p50TtftMs": 258, "p95TtftMs": 318, "medianTokensPerSec": 1172.0, "errors": ["HTTP 400"]},
        {"providerId": "openrouter", "provider": "OpenRouter", "model": "cohere/north-mini-code:free", "available": True,
         "score": 95, "answered": 22, "total": 22, "successRate": 100, "dimensions": DIMS,
         "p50TtftMs": 4231, "p95TtftMs": 9876, "medianTokensPerSec": 46.2},
        {"providerId": "nvidia", "provider": "NVIDIA NIM", "model": "meta/codellama-70b", "available": False, "score": None,
         "successRate": 0, "errors": ["HTTP 404"],
         "errorDetail": "{\"status\":404,\"detail\":\"Function 'x': Not found for account 'SECRET-ACCOUNT-ID'\"}"},
    ],
}
VERDICTS = {"models": {"openai/gpt-oss-120b": {"tagline": "又快又准", "bestFor": "实时对话", "avoid": "冷门事实"}}}


def _visible_zh(page: str) -> str:
    page = re.sub(r'<span lang="en">.*?</span>', "", page, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))


class EvalSecondaryPagesTest(unittest.TestCase):
    def setUp(self) -> None:
        patches = [
            mock.patch.object(eval_pages, "load_results", lambda: FIXTURE),
            mock.patch.object(eval_pages, "load_verdicts", lambda: VERDICTS),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _provider_page(self, provider_id: str, name: str, models: list[dict]) -> str:
        return seo.render_provider_page({"id": provider_id, "name": name}, models, [], "https://freellm.top")

    def test_measured_provider_page_shows_score_latency_and_dimensions(self) -> None:
        models = [{"providerId": "groq", "provider": "Groq", "model": "gpt-oss-120b", "id": "groq/gpt-oss-120b"}]
        page = self._provider_page("groq", "Groq", models)
        text = _visible_zh(page)
        self.assertIn('id="freellm-eval"', page)
        self.assertIn("Groq 实测表现", text)
        self.assertIn("95", text)
        self.assertIn("204 ms / 500 ms", text)  # first-token p50 / p95
        self.assertIn("483 token/s", text)
        self.assertIn("100%", text)  # success rate
        self.assertIn("防幻觉", text)  # dimension scores
        self.assertIn("又快又准", text)  # verdict tagline
        self.assertIn("适合", text)
        self.assertIn('/evaluations/#m-groq-openai-gpt-oss-120b', page)
        self.assertIn(eval_pages.RAW_DATA_URL, page)
        # the catalog row of the same channel shows the real number too
        self.assertIn("实测 95 分", text)

    def test_rate_limited_model_leads_with_success_rate(self) -> None:
        page = self._provider_page("groq", "Groq", [])
        text = _visible_zh(page)
        self.assertIn("77%", text)
        self.assertIn("9 分受失败请求影响", text)

    def test_unavailable_endpoint_is_phrased_as_account_endpoint_issue(self) -> None:
        page = self._provider_page("nvidia-nim", "NVIDIA NIM", [])
        text = _visible_zh(page)
        self.assertIn("本账号/本端点不可用（返回 404），待复核", text)
        self.assertNotIn("SECRET-ACCOUNT-ID", page)

    def test_untested_provider_and_model_are_labelled(self) -> None:
        models = [{"providerId": "puter", "provider": "Puter.js", "model": "MiMo-V2.6-Flash", "id": "puter/mimo"}]
        page = self._provider_page("puter", "Puter.js", models)
        text = _visible_zh(page)
        self.assertIn("未实测", text)
        self.assertNotIn(" ms", _visible_zh(page.split('id="freellm-eval"', 1)[1].split("</section>", 1)[0]))
        aggregate = seo.render_model_aggregate_page("MiMo-V2.6-Flash", models, [], "https://freellm.top")
        self.assertIn("未实测", _visible_zh(aggregate))
        self.assertIn("未实测", _visible_zh(eval_pages.offer_chip({"provider": "Cursor", "model": "Cursor Auto"})))

    def test_cross_channel_reference_never_shows_other_channel_speed(self) -> None:
        models = [{"providerId": "kilo", "provider": "Kilo Gateway", "model": "Cohere: North Mini Code (free)", "id": "kilo/north"}]
        page = self._provider_page("kilo", "Kilo Gateway", models)
        text = _visible_zh(page)
        self.assertIn("同款模型经 OpenRouter 实测 95 分", text)
        self.assertIn("本渠道速度", text)
        for speed in ("4231", "9876", "46 token/s"):
            self.assertNotIn(speed, page)
        aggregate = seo.render_model_aggregate_page(
            "North Mini Code",
            models + [{"providerId": "openrouter", "provider": "OpenRouter", "model": "Cohere: North Mini Code (free)", "id": "or/north"}],
            [], "https://freellm.top",
        )
        # the OpenRouter route shows its own speed, the Kilo route only the reference
        self.assertIn("4231 ms", aggregate)
        kilo_row = re.search(r"<li><strong>Kilo Gateway</strong>(.*?)</li>", aggregate, flags=re.S).group(1)
        self.assertIn("同款模型经 OpenRouter 实测", kilo_row)
        self.assertNotIn("ms", _visible_zh(kilo_row))

    def test_category_block_separates_same_route_and_reference(self) -> None:
        offers = [
            {"id": "groq-free", "provider": "Groq", "model": "gpt-oss-120b", "title": "Groq free"},
            {"id": "kilo", "provider": "Kilo", "model": "North Mini Code", "title": "Kilo"},
            {"id": "cursor", "provider": "Cursor", "model": "Cursor Auto", "title": "Cursor"},
        ]
        block = eval_pages.category_section(offers, lambda offer: f"/offers/{offer['id']}/")
        text = _visible_zh(block)
        self.assertIn("本类实测表现", text)
        self.assertIn("同渠道实测", text)
        self.assertIn("204 ms", text)
        self.assertIn("仅同款模型参考", text)
        self.assertNotIn("4231", block)
        self.assertIn("其余 1 个未实测", text)


if __name__ == "__main__":
    unittest.main()
