"""Generate crawlable offer pages, category pages, guides, and the production sitemap."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.schema import (
    validate_access_references,
    validate_model_access_file,
    validate_provider_access_file,
    validate_region_policies,
    validate_models,
    validate_offers,
    validate_operation_guides,
)
from scripts.generate_access_cards import _operation_hints


SITE_URL = "https://freellm.top"
ACCESS_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SHARE_IMAGE_PATH = "/freellm-01-hero.png"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MANIFEST_NAME = ".seo-pages-manifest.json"

VERCEL_ANALYTICS_SCRIPT = '''<script>
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  </script>
  <script defer src="/_vercel/insights/script.js"></script>'''

ADSENSE_SCRIPT = '''<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2461062743308239"
          crossorigin="anonymous"></script>'''

ADSENSE_SLOT = os.environ.get("FREELLM_ADSENSE_SLOT", "").strip()

STATIC_LOCALE_STYLE = '''<style id="static-locale-style">
    html[data-locale="en"] [lang="zh-CN"], html[data-locale="zh-CN"] [lang="en"] { display: none !important; }
    .static-locale-nav { display: flex; gap: 8px; align-items: center; font-size: .85rem; }
    .static-locale-nav a { text-decoration: none; }
  </style>'''

STATIC_LOCALE_SCRIPT = '''<script id="static-locale-script">
    (() => {
      const key = 'free-ai-index-locale';
      const queryLocale = new URLSearchParams(window.location.search).get('lang');
      const normalize = value => String(value || '').toLowerCase().startsWith('en') ? 'en' : 'zh-CN';
      const locale = queryLocale ? normalize(queryLocale) : normalize(localStorage.getItem(key));
      document.documentElement.lang = locale;
      document.documentElement.dataset.locale = locale;
      try { localStorage.setItem(key, locale); } catch (error) { /* storage can be unavailable */ }
      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('a[href^="/"]').forEach(link => {
          const url = new URL(link.href, window.location.href);
          url.searchParams.set('lang', locale === 'en' ? 'en' : 'zh');
          link.href = `${url.pathname}${url.search}${url.hash}`;
        });
      });
    })();
  </script>'''

CATEGORY_DEFINITIONS = {
    "free-quota": {
        "name": "Free AI quota",
        "name_zh": "免费额度",
        "description": "Verified recurring free quotas and free access paths for AI models and APIs.",
        "description_zh": "整理经过核验的 AI 模型与 API 免费额度和免费入口。",
    },
    "free-ide": {
        "name": "Free AI coding IDEs",
        "name_zh": "免费 AI IDE",
        "description": "Free coding IDEs, editor plans, and developer tools with provider-defined limits.",
        "description_zh": "整理免费 AI 编程 IDE、编辑器计划和开发工具，并标注限制条件。",
    },
    "api": {
        "name": "AI API services",
        "name_zh": "AI API 服务",
        "description": "AI API endpoints with free tiers, trials, credits, or clearly separated low-cost plans.",
        "description_zh": "整理提供免费层、试用额度、积分或低成本方案的 AI API 服务。",
    },
    "promo": {
        "name": "AI trials and promotions",
        "name_zh": "AI 试用与优惠",
        "description": "Time-limited trials, first-month deals, and regional promotions with validity notes.",
        "description_zh": "整理限时试用、首月优惠和地区活动，并注明有效期与续费条件。",
    },
    "student": {
        "name": "Student AI offers",
        "name_zh": "学生 AI 优惠",
        "description": "Student plans and education offers that require verification or eligibility checks.",
        "description_zh": "整理需要学生身份或教育资格验证的 AI 计划与优惠。",
    },
    "web": {
        "name": "Web and browser AI tools",
        "name_zh": "网页与浏览器 AI 工具",
        "description": "Search, fetch, crawl, browser, and agent web tools with free or metered access.",
        "description_zh": "整理搜索、抓取、浏览器和 Agent 网页工具，并区分免费与计费方式。",
    },
    "open-weights": {
        "name": "Open-weight AI models",
        "name_zh": "开源权重模型",
        "description": "Open-weight models with official repositories or model-card download paths.",
        "description_zh": "整理有官方仓库或模型卡下载入口的开放权重模型。",
    },
}
LEGACY_OFFER_REDIRECTS = {
    "longcat-api": "longcat-2-0",
    "longcat-download": "longcat-2-0",
}


@dataclass(frozen=True)
class BuildResult:
    offer_count: int
    category_count: int
    page_count: int


def _slug(value: object) -> str:
    text = str(value or "").strip().lower()
    if not SLUG_RE.fullmatch(text):
        raise ValueError(f"invalid SEO slug: {value!r}")
    return text


def offer_url(offer: dict) -> str:
    return f"/offers/{_slug(offer['id'])}/"


def category_url(category: str) -> str:
    return f"/category/{_slug(category)}/"


def guide_url() -> str:
    return "/guides/free-llm/"


def models_url() -> str:
    return "/models/"


def _safe_slug(value: object, fallback: str = "item") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text or fallback


def provider_url(provider: dict | str) -> str:
    provider_id = provider.get("id") if isinstance(provider, dict) else provider
    return f"/providers/{_safe_slug(provider_id, 'provider')}/"


def model_aggregate_url(model: dict | str) -> str:
    model_name = model.get("model") if isinstance(model, dict) else model
    return f"/models/{_safe_slug(model_name, 'model')}/"


MODELS_PAGE_PATH = "/models/"
ALL_MODELS_PAGE_PATH = "/models/all/"
MODEL_CENTER_PAGE_PATH = "/models/center/"
PROVIDERS_PAGE_PATH = "/providers/"
CHANGE_LOG_PAGE_PATH = "/logs/"


OPENAI_ALTERNATIVES_GUIDE_PATH = "/guides/free-openai-api-alternatives/"
CLAUDE_CODE_ALTERNATIVES_GUIDE_PATH = "/guides/claude-code-free-alternatives/"

THEME_GUIDE_DEFINITIONS = (
    {
        "slug": "free-openai-compatible-apis",
        "title_zh": "免费 OpenAI 兼容 API",
        "title_en": "Free OpenAI-Compatible APIs",
        "description_zh": "整理可用于原型和开发工具的免费或试用 OpenAI 兼容 API，并标注额度、限制和官方接入入口。",
        "description_en": "Compare free or trial OpenAI-compatible APIs for prototypes and developer tools, with quota notes and official setup links.",
        "lead_zh": "如果你的工具支持 OpenAI SDK，通常只需要替换 base URL、API key 和模型 ID。",
        "lead_en": "If your tool supports the OpenAI SDK shape, you usually only need to replace the base URL, API key and model ID.",
    },
    {
        "slug": "free-ai-coding-tools",
        "title_zh": "免费 AI 编程工具",
        "title_en": "Free AI Coding Tools",
        "description_zh": "比较免费 AI IDE、编码计划和开发工具，区分长期免费、试用和地区限制。",
        "description_en": "Compare free AI IDEs, coding plans and developer tools, separating recurring access from trials and regional limits.",
        "lead_zh": "先看免费方式和限制，再选择适合日常编码、补全或 Agent 工作流的工具。",
        "lead_en": "Check the free mechanism and limits first, then choose a tool for daily coding, completion or agent workflows.",
    },
    {
        "slug": "free-ai-search-apis",
        "title_zh": "免费 AI 搜索 API",
        "title_en": "Free AI Search APIs",
        "description_zh": "整理搜索、抓取、浏览器和 Agent 网页工具的免费额度、试用积分和使用条件。",
        "description_en": "Find free quotas, trial credits and access conditions for search, crawl, browser and agent web APIs.",
        "lead_zh": "搜索和网页工具的免费额度差异很大，重点核对请求数、地区、信用卡和过期时间。",
        "lead_en": "Free web-tool limits vary widely; check request counts, region, card requirements and expiry before building on one.",
    },
    {
        "slug": "open-weight-models",
        "title_zh": "开源权重模型",
        "title_en": "Open-Weight AI Models",
        "description_zh": "按模型和厂商浏览开放权重模型，查看上下文、模态、状态和目录来源。",
        "description_en": "Browse open-weight models by model and provider, with context, modality, status and directory sources.",
        "lead_zh": "权重免费不等于推理基础设施免费；请同时评估显存、存储、许可证和部署方式。",
        "lead_en": "Free weights do not make inference infrastructure free; also evaluate VRAM, storage, licensing and deployment.",
    },
    {
        "slug": "model-context-windows",
        "title_zh": "AI 模型上下文窗口",
        "title_en": "AI Model Context Windows",
        "description_zh": "集中查看目录中模型的上下文窗口、最大输出、模态和来源，帮助选择长文与代码模型。",
        "description_en": "Compare model context windows, maximum output, modalities and sources when choosing models for long documents or code.",
        "lead_zh": "上下文窗口是模型参数，不等于每个平台都免费，也不等于每次请求都能达到该上限。",
        "lead_en": "A context window is a model parameter; it does not mean every host is free or every request reaches the maximum.",
    },
    {
        "slug": "china-free-ai-api",
        "title_zh": "国内免费 AI API",
        "title_en": "Free AI APIs in China",
        "description_zh": "整理面向中国用户的免费或试用 AI API，标注地区、注册要求（手机号、实名、信用卡）、额度、兼容性和官方入口，模型目录逐行标注中国大陆可用性。",
        "description_en": "Compare free or trial AI APIs available to users in China, with region, signup requirements (phone, identity, credit card), quota, compatibility and official entry notes; the model directory carries per-row mainland-China availability labels.",
        "lead_zh": "国内 API 的免费条件经常和地区、实名认证、账户类型或新用户资格相关；本页只收录有官方证据的结论，未核验的如实标记待核验。",
        "lead_en": "Free access in China often depends on region, identity verification, account type or new-user eligibility; this page only states conclusions backed by official evidence, and marks everything else as unverified.",
    },
)


GUIDE_SOURCE_URL = "https://github.com/nejib1/Free-LLM/blob/main/README.zh-CN.md"
GUIDE_REPOSITORY_URL = "https://github.com/nejib1/Free-LLM"

OPENAI_ALTERNATIVE_ROWS = [
    ("groq-free", "Groq", "OpenAI-compatible API with per-model RPM, RPD and TPM limits.", "https://console.groq.com/docs/openai"),
    ("cerebras-free", "Cerebras", "$5 free credits after account creation; current terms belong to the official pricing page.", "https://inference-docs.cerebras.ai/quickstart"),
    ("hf-inference-free", "Hugging Face Inference Providers", "Free tier included; monthly credits and provider availability can change.", "https://huggingface.co/docs/inference-providers/index"),
    ("siliconflow-free-models", "SiliconFlow", "Selected models may be listed at ¥0; login, region and model limits vary.", "https://docs.siliconflow.cn/cn/userguide/quickstart"),
    ("modelscope-api-inference-free", "ModelScope", "Registered users can access API-Inference with dynamic rate limits.", "https://modelscope.cn/docs/model-service/API-Inference/intro"),
    ("longcat-2-0", "LongCat API", "OpenAI-compatible endpoint is documented; a permanent free quota is not confirmed.", "https://longcat.ai/platform/docs/zh/faq"),
]

CLAUDE_CODE_ALTERNATIVE_ROWS = [
    ("glm", "GLM Coding Plan", "Dedicated coding endpoint documented for Claude Code, Cursor and Cline; quota uses provider time windows.", "https://docs.bigmodel.cn/cn/coding-plan/faq"),
    ("longcat-2-0", "LongCat API", "OpenAI / Anthropic-compatible workflow; account access and any free quota must be checked before use.", "https://longcat.ai/platform/docs/zh/faq"),
    ("groq-free", "Groq", "OpenAI-compatible coding API with a published free rate-limit table; Claude Code requires a compatible adapter or endpoint.", "https://console.groq.com/docs/openai"),
]

GUIDE_PERMANENT_ROWS = [
    [("Google AI Studio", "https://aistudio.google.com/"), "否", "5–30 RPM（因模型而异）", "9,000 RPD（Flash）", "完全免费", "Gemini 3.1 Pro / Flash"],
    [("Mistral", "https://console.mistral.ai/"), "需手机验证", "1 request/second", "—", "Free", "Mistral 7B / Mixtral"],
    [("Hugging Face Inference", "https://huggingface.co/inference-api/serverless"), "否", "300 requests/hour", "按月度 credits", "$0.10/月路由 credits", "Llama / Qwen / Gemma"],
    [("Cohere", "https://cohere.com/"), "否", "20 requests/minute", "—", "1,000 requests/month", "Command R / R7B / A"],
    [("NVIDIA NIM", "https://build.nvidia.com/explore/discover"), "需手机验证", "40 requests/minute", "—", "—", "按模型而定"],
    [("Groq", "https://console.groq.com/"), "否", "30 RPM", "14,400 requests/day", "Free forever", "Qwen / Llama / Whisper"],
    [("Z.AI (GLM)", "https://z.ai/"), "需注册", "约 1 request/second", "约 1,000/day", "持续免费层", "GLM Flash"],
    [("Coze", "https://www.coze.com/"), "需注册", "因模型而异", "按 token 计算", "每日重置", "GPT / Gemini"],
    [("Cloudflare Workers AI", "https://dash.cloudflare.com/"), "否", "因模型而异", "10,000 neurons/day", "约 300,000 neurons/month", "Llama / Mistral / Qwen"],
    [("LLM7.io", "https://llm7.io/"), "否", "30 RPM / 120 RPM", "最多 5M tokens/day", "Free, no billing", "DeepSeek / Qwen"],
    [("OVH AI Endpoints", "https://endpoints.ai.cloud.ovh.net/"), "需注册", "2 RPM / 400 RPM", "未公布", "Beta access", "Qwen3Guard / SDXL"],
    [("Ollama Cloud", "https://ollama.com/cloud"), "否", "Light usage tier", "会话周期重置", "每周重置", "GPT-OSS / Qwen / DeepSeek"],
    [("Nous Portal", "https://portal.nousresearch.com/"), "否", "未完整公布", "未公布", "$0/month", "Hermes 4"],
    [("Hetzner Inference API", "https://experiments.hetzner.com/inference"), "否", "按 token 限制", "500M input / 5M output", "实验阶段免费", "Qwen3.6"],
    [("Pollinations.ai", "https://pollinations.ai/"), "否", "匿名约 1 request/15s", "合理使用范围", "Free", "GPT / Mistral 类模型"],
    [("SiliconFlow", "https://siliconflow.com/pricing"), "需手机验证", "按模型固定限制", "需登录确认", "免费模型", "见官方模型页"],
    [("ModelScope", "https://modelscope.cn/"), "需手机验证", "500 requests/day/model", "2,000 requests/day", "Free", "见官方模型页"],
    [("Aion Labs", "https://www.aionlabs.ai/pricing/"), "否", "未公布", "每日 token allowance", "Free", "见官方页面"],
    [("Inference.net", "https://inference.net/"), "否", "30 RPM（合理使用）", "Fair use", "Fair use", "DeepSeek / Llama"],
]

GUIDE_RENEWABLE_ROWS = [
    [("OpenRouter", "https://openrouter.ai/"), "否", "20 requests/minute", "50 requests/day（充值后更高）", "Gemini / Llama / NVIDIA"],
    [("Venice.ai", "https://venice.ai/"), "需注册", "10 RPM", "Limited daily usage", "Llama 405B / Dolphin"],
    [("Requesty", "https://requesty.ai/"), "否", "60 RPM", "200 requests/day", "Free models"],
    [("Grok (xAI)", "https://console.x.ai/"), "需注册", "视额度而定", "$25 one-time signup credit", "Grok 2"],
]

GUIDE_TRIAL_ROWS = [
    [("Together.AI", "https://together.ai/"), "需注册", "需先充值最低 $5", "—"],
    [("Replicate", "https://replicate.com/"), "需注册", "少量试用额度", "一次性"],
    [("Fireworks AI", "https://fireworks.ai/"), "需注册", "$1", "一次性"],
    [("SambaNova Cloud", "https://cloud.sambanova.ai/"), "需注册", "$5", "3 个月"],
    [("Hyperbolic", "https://app.hyperbolic.xyz/"), "需注册", "$1", "一次性"],
    [("Nebius Token Factory", "https://tokenfactory.nebius.com/"), "需注册", "$1，需银行卡", "一次性"],
    [("Cerebras", "https://cerebras.ai/inference"), "需注册", "$5", "30 天"],
    [("Novita AI", "https://novita.ai/"), "需注册", "$0.50", "一次性"],
    [("Scaleway Generative APIs", "https://console.scaleway.com/generative-api/models"), "需注册", "1M tokens", "一次性"],
    [("Qwen / Alibaba", "https://bailian.console.alibabacloud.com/"), "需注册", "每模型 1M tokens", "一次性"],
    [("AI21 Labs", "https://docs.ai21.com/"), "需注册", "$10", "3 个月"],
    [("Upstage", "https://console.upstage.ai/"), "需注册", "$10", "3 个月"],
    [("DeepSeek", "https://platform.deepseek.com/"), "需注册", "5M tokens", "30 天"],
    [("Cerebrium", "https://www.cerebrium.ai/"), "需注册", "$30", "一次性"],
    [("DeepInfra", "https://deepinfra.com/"), "需注册", "$5", "一次性，90 天过期"],
]

GUIDE_LOCAL_ROWS = [
    [("Ollama", "https://ollama.com/"), "CLI + API", "100+ 模型、GPU 加速、OpenAI 兼容"],
    [("LM Studio", "https://lmstudio.ai/"), "桌面 GUI", "GGUF 模型、模型浏览器、离线使用"],
    [("llama.cpp", "https://github.com/ggml-org/llama.cpp"), "C/C++ 引擎", "运行 GGUF，依赖少"],
    [("GPT4All", "https://gpt4all.io/"), "桌面应用", "纯 CPU 运行、开源"],
    [("Jan.ai", "https://jan.ai/"), "桌面应用", "注重隐私、100% 离线"],
    [("KoboldCpp", "https://github.com/LostRuins/koboldcpp"), "单文件应用", "创意写作、支持 GGUF"],
    [("llamafile", "https://github.com/Mozilla-Ocho/llamafile"), "跨平台", "llama.cpp + Cosmopolitan Libc"],
    [("Text Generation WebUI", "https://github.com/oobabooga/text-generation-webui"), "Gradio 界面", "高度可定制"],
    [("BentoML", "https://www.bentoml.com/"), "推理平台", "部署任意 AI/ML 模型"],
]

GUIDE_QUICKREF_ROWS = [
    [("OpenRouter", "https://openrouter.ai/"), "https://openrouter.ai/api/v1"],
    [("Google AI Studio", "https://aistudio.google.com/"), "https://generativelanguage.googleapis.com/v1beta"],
    [("Mistral", "https://console.mistral.ai/"), "https://api.mistral.ai/v1"],
    [("Hugging Face", "https://huggingface.co/inference-api/serverless"), "https://router.huggingface.co/v1"],
    [("Fireworks AI", "https://fireworks.ai/"), "https://api.fireworks.ai/inference/v1"],
    [("NVIDIA NIM", "https://build.nvidia.com/explore/discover"), "https://integrate.api.nvidia.com/v1"],
    [("Cerebras", "https://cerebras.ai/inference"), "https://api.cerebras.ai/v1"],
    [("Groq", "https://console.groq.com/"), "https://api.groq.com/openai/v1"],
    [("DeepSeek", "https://platform.deepseek.com/"), "https://api.deepseek.com/v1"],
    [("Z.AI (GLM)", "https://z.ai/"), "https://api.z.ai/api/paas/v4"],
    [("Coze", "https://www.coze.com/"), "https://api.coze.com/v1"],
    [("SiliconFlow", "https://siliconflow.com/pricing"), "https://api.siliconflow.com/v1"],
    [("ModelScope", "https://modelscope.cn/"), "https://api-inference.modelscope.cn/v1"],
    [("Ollama Cloud", "https://ollama.com/cloud"), "https://ollama.com/v1"],
]


def _tokens(offer: dict) -> set[str]:
    return {
        str(token)
        for token in [*(offer.get("type") or []), *(offer.get("capabilities") or []), offer.get("productType")]
        if token
    }


def categorize_offer(offer: dict) -> list[str]:
    """Return category slugs using the same intent as the homepage filters."""
    tokens = _tokens(offer)
    categories: list[str] = []
    is_ide = offer.get("productType") == "free_ide" or "ide" in tokens or "free_ide" in tokens
    is_web = offer.get("productType") == "web_infrastructure" or "web" in tokens
    is_open_or_low_cost = (
        offer.get("productType") in {"open_weights", "payg"}
        or "download" in tokens
        or "payg" in tokens
    )
    if "student" in tokens or offer.get("studentSummary"):
        categories.append("student")
    if (
        offer.get("freeMechanism") in {"daily_quota", "weekly_quota", "monthly_quota", "permanent"}
        and not is_ide
        and not is_open_or_low_cost
    ):
        categories.append("free-quota")
    if is_ide:
        categories.append("free-ide")
    if offer.get("productType") in {"api", "payg"} or "api" in tokens or "model_api" in tokens:
        categories.append("api")
    if (
        offer.get("freeMechanism") == "first_month_promo"
        or offer.get("timeWindow")
        or "promo" in tokens
        or offer.get("freeMechanism") in {"trial", "limited_time_free"}
    ):
        categories.append("promo")
    if is_web:
        categories.append("web")
    if offer.get("productType") == "open_weights" or "download" in tokens:
        categories.append("open-weights")
    return [category for category in categories if category in CATEGORY_DEFINITIONS]


def _esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _english_text(value: object, fallback: str = "See official terms") -> str:
    """Return readable English-safe text without leaking Han characters."""
    text = re.sub(r"[\u3400-\u9fff]", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip(" /·,;:：")
    return text or fallback


def _locale_pair(zh: object, en: object, fallback_en: str = "See official terms") -> str:
    zh_text = str(zh or en or fallback_en)
    en_text = _english_text(en or zh, fallback_en)
    return f'<span lang="zh-CN">{_esc(zh_text)}</span><span lang="en">{_esc(en_text)}</span>'


def _offer_locale_pair(offer: dict, fields: tuple[str, ...], fallback_en: str = "See official terms") -> str:
    zh = next((offer.get(field) for field in fields if offer.get(field)), None)
    en = next((offer.get(f"{field}En") for field in fields if offer.get(f"{field}En")), None)
    if not en:
        en = next((offer.get(field) for field in fields if offer.get(field) and not re.search(r"[\u3400-\u9fff]", str(offer.get(field)))), None)
    return _locale_pair(zh, en or zh, fallback_en)


def _static_locale_nav() -> str:
    return '<nav class="static-locale-nav" aria-label="Language"><a data-locale-link href="?lang=zh">中文</a><span aria-hidden="true">·</span><a data-locale-link href="?lang=en">English</a></nav>'


def _hreflang_links(site_url: str, path: str) -> str:
    """Expose the stable Chinese URL and its English locale variant to crawlers."""
    canonical = _absolute(site_url, path)
    english = f"{canonical}?lang=en"
    return "\n".join(
        (
            f'<link rel="alternate" hreflang="zh-CN" href="{_esc(canonical)}">',
            f'<link rel="alternate" hreflang="en" href="{_esc(english)}">',
            f'<link rel="alternate" hreflang="x-default" href="{_esc(canonical)}">',
        )
    )


def _inject_hreflang_links(page: str, site_url: str, path: str) -> str:
    """Normalize hreflang metadata for every generated bilingual HTML page."""
    page = re.sub(
        r'\s*<link rel="alternate" hreflang="(?:zh-CN|en|x-default)"[^>]*>',
        "",
        page,
    )
    links = _hreflang_links(site_url, path)
    return re.sub(
        r'(<link rel="canonical"[^>]*>)',
        lambda match: f"{match.group(1)}\n  {links}",
        page,
        count=1,
    )


def _adsense_slot_markup(slot: str | None = None) -> str:
    """Render an explicit AdSense unit only when a real slot is configured."""
    slot_id = str(ADSENSE_SLOT if slot is None else slot).strip()
    if not slot_id or not re.fullmatch(r"\d+", slot_id):
        return ""
    return f'''<ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-2461062743308239" data-ad-slot="{_esc(slot_id)}" data-ad-format="auto" data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>'''


def _absolute(site_url: str, path: str) -> str:
    return urljoin(site_url.rstrip("/") + "/", path.lstrip("/"))


def _description(offer: dict) -> str:
    summary = offer.get("freeSummary") or offer.get("mechanism") or offer.get("why") or "Verified AI offer"
    return f"{offer.get('provider', offer.get('name', 'AI 资源'))}：{summary}。请以官方页面为准，核对地区、有效期和使用条件。"


def _social_meta(site_url: str, page_url: str, title: str, description: str, og_type: str) -> str:
    """Render social metadata from the same absolute URLs used by canonical links."""
    absolute_url = _absolute(site_url, page_url)
    image_url = _absolute(site_url, SHARE_IMAGE_PATH)
    return "\n".join(
        (
            f'<meta property="og:type" content="{_esc(og_type)}">',
            f'<meta property="og:title" content="{_esc(title)}">',
            f'<meta property="og:description" content="{_esc(description)}">',
            f'<meta property="og:url" content="{_esc(absolute_url)}">',
            f'<meta property="og:image" content="{_esc(image_url)}">',
            f'<meta property="og:image:alt" content="{_esc(title)}">',
            f'<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{_esc(title)}">',
            f'<meta name="twitter:description" content="{_esc(description)}">',
            f'<meta name="twitter:image" content="{_esc(image_url)}">',
        )
    )


def _analytics_script() -> str:
    return VERCEL_ANALYTICS_SCRIPT


def _theme_definition(slug: str) -> dict:
    for definition in THEME_GUIDE_DEFINITIONS:
        if definition["slug"] == slug:
            return definition
    raise ValueError(f"Unknown theme guide: {slug}")


def _theme_records(slug: str, offers: list[dict], models: list[dict]) -> tuple[str, list[dict]]:
    if slug == "free-openai-compatible-apis":
        return "offer", [offer for offer in offers if offer.get("productType") in {"api", "payg"}]
    if slug == "free-ai-coding-tools":
        return "offer", [
            offer for offer in offers
            if offer.get("productType") in {"free_ide", "coding_plan"} or "coding" in _tokens(offer)
        ]
    if slug == "free-ai-search-apis":
        return "offer", [
            offer for offer in offers
            if offer.get("productType") == "web_infrastructure"
            or _tokens(offer).intersection({"search", "fetch", "browser", "agent", "crawl"})
        ]
    if slug == "open-weight-models":
        return "model", [model for model in models if model.get("directoryVerified") and model.get("sourceUrl")]
    if slug == "model-context-windows":
        return "model", [model for model in models if model.get("context") and model.get("sourceUrl")]
    if slug == "china-free-ai-api":
        return "offer", [
            offer for offer in offers
            if offer.get("originCountry") == "China"
            and offer.get("productType") in {"api", "payg"}
            and "free" in _tokens(offer)
        ]
    raise ValueError(f"Unknown theme guide: {slug}")


def _theme_offer_row(offer: dict, site_url: str) -> str:
    title = _locale_pair(
        offer.get("titleZh") or offer.get("title") or offer.get("name"),
        offer.get("title") or offer.get("name"),
        "Offer details",
    )
    source_url = offer.get("register") or next(iter(offer.get("sourceUrls") or []), "")
    source = (
        f'<a href="{_esc(source_url)}" target="_blank" rel="nofollow noopener">Official source ↗</a>'
        if source_url else _locale_pair("暂无官方来源", "No official source listed")
    )
    return f'''<tr>
      <td><a href="{_esc(offer_url(offer))}"><strong>{title}</strong></a><small>{_offer_locale_pair(offer, ("model", "name"), "Listed model")}</small></td>
      <td>{_offer_locale_pair(offer, ("freeSummary", "mechanism", "quota"), "Free terms are not listed")}</td>
      <td>{_offer_locale_pair(offer, ("accessSummary", "access"), "Check official access requirements")}</td>
      <td>{source}<br><a href="{_esc(_absolute(site_url, offer_url(offer)))}">FreeLLM record ↗</a></td>
    </tr>'''


def _theme_model_row(model: dict) -> str:
    context = str(model.get("context") or "Not listed")
    context_value = context if "token" in context.lower() else f"{context} tokens"
    source_url = model.get("sourceUrl") or "#"
    return f'''<tr>
      <td>{_esc(model.get("provider") or "Unknown provider")}</td>
      <td><strong>{_esc(model.get("model") or model.get("id") or "Unknown model")}</strong><small>{_esc(model.get("id"))}</small></td>
      <td>{_esc(context_value)}</td>
      <td>{_esc(model.get("maxOutput") or "Not listed")}</td>
      <td>{_esc(", ".join(model.get("modality") or []) or "Not listed")}</td>
      <td><a href="{_esc(source_url)}" target="_blank" rel="nofollow noopener">Source ↗</a></td>
    </tr>'''


def _render_theme_guide_page_expanded(offers: list[dict], models: list[dict], site_url: str, slug: str) -> str:
    definition = _theme_definition(slug)
    record_kind, records = _theme_records(slug, offers, models)
    path = f'/guides/{slug}/'
    page_url = _absolute(site_url, path)
    title = f'{definition["title_en"]} | {definition["title_zh"]} · FreeLLM'
    description = f'{definition["description_en"]} {definition["description_zh"]}'
    if record_kind == "offer":
        rows = "".join(_theme_offer_row(offer, site_url) for offer in records)
        table = f'''<div class="table-wrap"><table><thead><tr><th>Provider / model</th><th>Free terms</th><th>Access</th><th>Official links</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    else:
        rows = "".join(_theme_model_row(model) for model in records)
        table = f'''<div class="table-wrap"><table><thead><tr><th>Provider</th><th>Model</th><th>Context window</th><th>Max output</th><th>Modality</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    china_callout = ""
    if slug == "china-free-ai-api":
        china_callout = f'''<section>
      <div class="eyebrow">02 / mainland CN availability</div>
      <h2>{_locale_pair("模型目录的大陆可用性标注", "Mainland-CN availability labels in the model directory")}</h2>
      <p>{_locale_pair(
          f"完整模型目录（{len(models)} 个模型）逐行标注中国大陆可用状态，并提供“大陆可用性”筛选工具；每家提供商的注册要求（手机号、实名、信用卡）都有独立核验卡片与官方来源。没有官方证据的状态一律显示“待核验”。",
          f"The full catalog of {len(models)} models carries per-row mainland-China availability labels with a dedicated filter; each provider's signup requirements (phone, identity, credit card) live on its own evidence-linked card. Anything without official evidence shows as unverified.")}
          <a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair("打开模型大列表并按大陆可用性筛选 →", "Open the model directory and filter by mainland-CN availability →")}</a></p>
    </section>'''
    related_eyebrow = "03 / related pages" if china_callout else "02 / related pages"
    related = ''.join(
        f'<li><a href="{_esc(path)}">{_locale_pair(definition["title_zh"], definition["title_en"])}</a></li>'
        for path in (models_url(), guide_url(), OPENAI_ALTERNATIVES_GUIDE_PATH, CLAUDE_CODE_ALTERNATIVES_GUIDE_PATH)
        if path != f'/guides/{slug}/'
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": page_url,
        "inLanguage": ["zh-CN", "en"],
        "isPartOf": {"@type": "WebSite", "name": "FreeLLM", "url": _absolute(site_url, "/")},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(records),
            "itemListElement": [
                {"@type": "ListItem", "position": index, "name": item.get("title") or item.get("model"), "url": _absolute(site_url, offer_url(item)) if record_kind == "offer" else item.get("sourceUrl")}
                for index, item in enumerate(records, start=1)
            ],
        },
    }
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(page_url)}">
  {_social_meta(site_url, path, title, description, "website")}
  {_analytics_script()}
  {ADSENSE_SCRIPT}
  {STATIC_LOCALE_STYLE}
  {STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #68748a; --line: #dfe5ef; --soft: #f5f7fb; --blue: #1744e8; }}
    * {{ box-sizing: border-box; }}
    body {{ max-width: 1120px; margin: 0 auto; padding: 24px 18px 64px; line-height: 1.65; color: var(--ink); background: var(--soft); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    a {{ color: var(--blue); }}
    header, main, footer {{ background: white; border: 1px solid var(--line); border-radius: 16px; padding: clamp(20px, 4vw, 36px); margin-bottom: 18px; }}
    header {{ color: white; background: linear-gradient(135deg, #172033, #243f78); border-color: #172033; }}
    header a {{ color: white; }}
    h1 {{ max-width: 900px; margin: 22px 0 10px; font-size: clamp(34px, 6vw, 62px); line-height: 1.05; letter-spacing: -.05em; }}
    h2 {{ margin: 0 0 10px; font-size: clamp(24px, 4vw, 34px); }}
    p {{ max-width: 900px; }}
    .crumb, .eyebrow, th {{ font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }}
    .lead {{ max-width: 840px; color: #dbe6ff; font-size: 17px; }}
    .callout {{ margin: 22px 0 0; padding: 16px 18px; border-left: 4px solid #79e5a3; background: rgba(255,255,255,.1); }}
    section + section {{ padding-top: 28px; border-top: 1px solid var(--line); }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; margin: 16px 0 8px; }}
    table {{ width: 100%; min-width: 780px; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 12px 14px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
    th {{ color: var(--muted); background: var(--soft); }}
    tr:last-child td {{ border-bottom: 0; }}
    td small {{ display: block; margin-top: 4px; color: var(--muted); }}
    .link-list {{ padding-left: 1.3em; }}
    footer {{ color: var(--muted); font-size: 13px; }}
  </style>
</head>
<body data-static-locale="true">
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">FreeLLM Free AI Index</a> / Guides</div>
    {_static_locale_nav()}
    <h1>{_locale_pair(definition["title_zh"], definition["title_en"])}</h1>
    <p class="lead">{_locale_pair(definition["lead_zh"], definition["lead_en"])}</p>
    <div class="callout">{_locale_pair("数据来自本站已核验记录和模型目录；免费额度、地区、上下文上限和官方政策可能变化。", "Rows come from verified FreeLLM records and the model directory; free terms, regions, context limits and provider policies can change.")}</div>
  </header>
  <main>
    <section>
      <div class="eyebrow">01 / verified directory</div>
      <h2>{_locale_pair("可用入口和关键参数", "Available entries and key parameters")}</h2>
      <p>{_locale_pair(f"当前页面收录 {len(records)} 条记录。每条记录都能回到 FreeLLM 详情或目录来源。", f"This page contains {len(records)} records. Each row links back to a FreeLLM detail page or directory source.")}</p>
      {table}
    </section>
    {china_callout}<section>
      <div class="eyebrow">{related_eyebrow}</div>
      <h2>{_locale_pair("继续浏览", "Continue exploring")}</h2>
      <ul class="link-list">{related}</ul>
    </section>
  </main>
  <footer>
    <p><strong>{_locale_pair("免责声明", "Disclaimer")}：</strong>{_locale_pair("免费访问不代表无限制或适合生产环境，请在使用前核对官方来源。", "Free access does not mean unlimited or production-ready; verify the official source before use.")}</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair("返回 FreeLLM 首页 →", "Return to FreeLLM home →")}</a></p>
  </footer>
</body>
</html>
'''


def _list(items: list[object], empty: str = "Not specified") -> str:
    if not items:
        return f"<p>{_locale_pair(empty, _english_text(empty))}</p>"
    return "<ul>" + "".join(f"<li>{_locale_pair(item, item)}</li>" for item in items) + "</ul>"


def _source_links(offer: dict) -> str:
    labeled_links = []
    for link in offer.get("links") or []:
        if isinstance(link, list) and len(link) == 2 and link[0] and link[1]:
            labeled_links.append((str(link[0]), str(link[1])))
    for entry in offer.get("freeModels") or []:
        if isinstance(entry, dict) and entry.get("model") and entry.get("sourceUrl"):
            labeled_links.append((str(entry["model"]), str(entry["sourceUrl"])))
    if labeled_links:
        return "".join(
            f'<li><a href="{_esc(url)}" rel="nofollow noopener" target="_blank">{_locale_pair(label, label, "Official source")} ↗</a></li>'
            for label, url in dict(labeled_links).items()
        )

    urls = list(dict.fromkeys([offer.get("register"), *(offer.get("sourceUrls") or [])]))
    return "".join(
        f'<li><a href="{_esc(url)}" rel="nofollow noopener" target="_blank">{_esc(url)} ↗</a></li>'
        for url in urls
        if url
    ) or f"<li>{_locale_pair('暂无官方来源', 'No official source listed')}</li>"


def _access_paths_markup(offer: dict) -> str:
    paths = offer.get("accessPaths") or []
    if not paths:
        return ""
    rows = []
    for path in paths:
        if not isinstance(path, dict):
            continue
        links = " ".join(
            f'<a href="{_esc(link[1])}" rel="nofollow noopener" target="_blank">{_locale_pair(link[0], link[0], "Official link")} ↗</a>'
            for link in path.get("links") or []
            if isinstance(link, list) and len(link) == 2 and link[0] and link[1]
        )
        rows.append(
            f'''<tr><td><strong>{_locale_pair(path.get("label") or path.get("id"), path.get("label") or path.get("id"), "Access path")}</strong><br><small class="muted">{_esc(path.get("productType") or "—")}</small></td><td>{_locale_pair(path.get("summary") or "—", path.get("summary") or "—")}</td><td>{_locale_pair(path.get("freeSummary") or "—", path.get("freeSummary") or "—")}</td><td>{_locale_pair(path.get("access") or "—", path.get("access") or "—")}</td><td>{links or "—"}</td></tr>'''
        )
    if not rows:
        return ""
    return f'''<section>
      <h2>{_locale_pair("使用入口", "Access paths")}</h2>
      <div class="table-wrap"><table><thead><tr><th>{_locale_pair("入口", "Path")}</th><th>{_locale_pair("用途", "Use")}</th><th>{_locale_pair("免费状态", "Free status")}</th><th>{_locale_pair("访问条件", "Access")}</th><th>{_locale_pair("官方链接", "Official links")}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
    </section>'''


def _operation_guides_for_offer(offer: dict, operations: list[dict]) -> list[dict]:
    offer_id = str(offer.get("id") or "")
    return [guide for guide in operations if offer_id in (guide.get("offerIds") or [])]


def _operation_guides_for_provider(provider_id: str, operations: list[dict]) -> list[dict]:
    return [guide for guide in operations if guide.get("providerId") == provider_id]


def _operation_guides_markup(guides: list[dict]) -> str:
    if not guides:
        return ""
    rendered_guides = []
    command_index = 0
    for guide in guides:
        paths = []
        for path in guide.get("paths") or []:
            prerequisite_markup = _list(path.get("prerequisites") or [], "按官方要求准备账户和环境。")
            steps = []
            for step_index, step in enumerate(path.get("steps") or [], start=1):
                if isinstance(step, str):
                    steps.append(f"<li><p>{_esc(step)}</p></li>")
                    continue
                command_markup = ""
                command = step.get("command")
                if command:
                    command_index += 1
                    command_id = f"operation-command-{command_index}"
                    command_markup = f'''<div class="operation-command"><div class="operation-command-head"><span>{_locale_pair("可复制命令", "Copyable command")}</span><button type="button" class="copy-command" data-copy-target="{command_id}">{_locale_pair("复制命令", "Copy command")}</button></div><pre id="{command_id}"><code>{_esc(command)}</code></pre></div>'''
                action = step.get("action")
                action_markup = f'<p class="operation-action"><strong>{_locale_pair("操作", "Action")}：</strong>{_esc(action)}</p>' if action else ""
                expected = step.get("expected")
                expected_markup = f'<p class="operation-expected"><strong>{_locale_pair("预期结果", "Expected")}：</strong>{_esc(expected)}</p>' if expected else ""
                steps.append(f'<li><strong>{_esc(step.get("title") or f"Step {step_index}")}</strong><p>{_esc(step.get("detail") or "")}</p>{action_markup}{command_markup}{expected_markup}</li>')
            endpoint_markup = ""
            if path.get("endpoint") or path.get("auth"):
                endpoint_markup = f'''<dl class="operation-facts"><div><dt>{_locale_pair("Endpoint", "Endpoint")}</dt><dd><code>{_esc(path.get("endpoint") or "—")}</code></dd></div><div><dt>{_locale_pair("认证", "Authentication")}</dt><dd>{_esc(path.get("auth") or "—")}</dd></div></dl>'''
            limits_markup = f'<div class="operation-limits"><strong>{_locale_pair("额度与限制", "Limits")}</strong><p>{_esc(path.get("limits"))}</p></div>' if path.get("limits") else ""
            common_issues = path.get("commonIssues") or []
            if isinstance(common_issues, str):
                common_issues = [common_issues]
            issues_markup = f'<div class="operation-issues"><strong>{_locale_pair("常见问题", "Common issues")}</strong>{_list(common_issues, "以官方帮助中心为准。")}</div>' if common_issues else ""
            sources = "".join(f'<li><a href="{_esc(url)}" target="_blank" rel="nofollow noopener">{_esc(url)} ↗</a></li>' for url in path.get("sourceUrls") or [])
            paths.append(f'''<article class="operation-path"><h3>{_esc(path.get("label") or path.get("id"))}</h3><p class="operation-type">{_esc(path.get("productType") or "operation")}</p>{endpoint_markup}{limits_markup}<h4>{_locale_pair("前置条件", "Prerequisites")}</h4>{prerequisite_markup}<h4>{_locale_pair("操作步骤", "Steps")}</h4><ol class="operation-steps">{"".join(steps)}</ol><div class="operation-validation"><strong>{_locale_pair("验证动作", "Validation")}</strong><p>{_esc(path.get("validation") or "")}</p></div>{issues_markup}<h4>{_locale_pair("官方来源", "Official sources")}</h4><ul class="link-list">{sources}</ul></article>''')
        rendered_guides.append("".join(paths))
    return f'''<section id="operation-guides"><h2>{_locale_pair("详细操作步骤", "Detailed operation paths")}</h2><p class="muted">{_locale_pair("每条路径都拆成前置条件、步骤、可复制命令和验证动作；免费条件仍以官方页面实时状态为准。", "Each path includes prerequisites, steps, copyable commands and a validation action; free terms still follow the provider's live official policy.")}</p>{"".join(rendered_guides)}<script>(() => {{ document.querySelectorAll('.copy-command').forEach(button => button.addEventListener('click', async () => {{ const target = document.getElementById(button.dataset.copyTarget); if (!target) return; await navigator.clipboard.writeText(target.innerText); button.textContent = {json.dumps('已复制', ensure_ascii=False)}; setTimeout(() => button.textContent = {json.dumps('复制命令', ensure_ascii=False)}, 1400); }})); }})();</script></section>'''


def render_legacy_offer_redirect(legacy_id: str, target_id: str, site_url: str) -> str:
    target_path = f"/offers/{target_id}/"
    target_url = _absolute(site_url, target_path)
    title = "页面已合并 · FreeLLM"
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><link rel="canonical" href="{_esc(target_url)}"><meta http-equiv="refresh" content="0; url={_esc(target_url)}"></head>
<body><main><h1>页面已合并</h1><p>旧入口 <code>{_esc(legacy_id)}</code> 已合并到 LongCat-2.0 统一详情页。</p><p><a href="{_esc(target_url)}">继续查看 LongCat-2.0 详情 →</a></p></main></body></html>'''


def _related_links(offer: dict, offers: list[dict]) -> str:
    categories = set(categorize_offer(offer))
    related = [
        candidate
        for candidate in offers
        if candidate.get("id") != offer.get("id") and categories.intersection(categorize_offer(candidate))
    ]
    # Prioritize same category, then other matching pages; limit to a reasonable
    # number so off-topic pages don't dilute the signal.
    same_cat = [c for c in related if categories.intersection(categorize_offer(c))]
    other = [c for c in related if c not in same_cat]
    candidates = same_cat + other[:max(0, 6 - len(same_cat))]
    best = candidates[:6] if candidates else []
    if not best:
        related_category = next(iter(categories), "free-quota")
        related_url = category_url(related_category) if categories else "/"
        related_definition = CATEGORY_DEFINITIONS.get(related_category, {})
        related_label_zh = related_definition.get("name_zh", "全部免费 AI 资源")
        related_label_en = related_definition.get("name", "AI resources")
        return f'<li><a href="{_esc(related_url)}">{_locale_pair(f"浏览更多{related_label_zh}", f"Browse more {related_label_en}")}</a></li>'
    return "".join(
        f'<li><a href="{_esc(offer_url(candidate))}">{_locale_pair(candidate.get("titleZh") or candidate.get("provider") or candidate.get("name"), candidate.get("title") or candidate.get("provider") or candidate.get("name"), "Related resource")}</a></li>'
        for candidate in best
    )


def render_offer_page(offer: dict, offers: list[dict], site_url: str, operations: list[dict] | None = None) -> str:
    path = offer_url(offer)
    title = offer.get("title") or offer.get("name")
    description = _description(offer)
    page_title = f"{title} · FreeLLM 免费 AI 资源索引"
    social_meta = _social_meta(site_url, path, page_title, description, "article")
    guide = offer.get("usageGuide") or {}
    categories = categorize_offer(offer)
    category_links = "".join(
        f'<a class="tag" href="{_esc(category_url(category))}">{_locale_pair(CATEGORY_DEFINITIONS[category]["name_zh"], CATEGORY_DEFINITIONS[category]["name"])}</a>'
        for category in categories
    ) or f'<a class="tag" href="/">{_locale_pair("免费 AI 资源索引", "Free AI Index")}</a>'
    examples = guide.get("examples") or {}
    example_markup = "".join(
            f'<h3>{_locale_pair(name, name, "Example")}</h3><pre><code>{_esc(code)}</code></pre>' for name, code in examples.items()
    )
    context_window = offer.get("contextWindow") or {}
    context_window_markup = ""
    if context_window and offer.get("productType") in {"api", "open_weights", "coding_plan"}:
        context_summary_zh = context_window.get("zh") or context_window.get("en") or f"{context_window.get('tokens', '—')} tokens"
        context_summary_en = context_window.get("en") or context_window.get("zh") or f"{context_window.get('tokens', '—')} tokens"
        context_source = context_window.get("sourceUrl")
        source_markup = (
            f' <a href="{_esc(context_source)}" rel="nofollow noopener" target="_blank">{_locale_pair("来源", "Source")} ↗</a>'
            if context_source
            else ""
        )
        context_window_markup = f'''<section>
      <h2>{_locale_pair("上下文窗口", "Context window")}</h2>
      <p>{_locale_pair(context_summary_zh, context_summary_en)}.{source_markup}</p>
    </section>'''
    access_paths_markup = _access_paths_markup(offer)
    operation_guides_markup = _operation_guides_markup(_operation_guides_for_offer(offer, operations or []))
    free_models = offer.get("freeModels") or []
    free_models_markup = ""
    if free_models:
        rows = "".join(
            f'''<tr><td><code>{_locale_pair(entry.get("model"), entry.get("model"), "Listed model")}</code>{f'<br><small class="muted">{_locale_pair(entry["label"], entry["label"], "Model label")}</small>' if entry.get("label") else ""}</td><td>{_locale_pair(entry.get("contextWindow") or "—", entry.get("contextWindow") or "—", "See model limits")}</td><td>{_locale_pair(entry.get("quota") or "—", entry.get("quota") or "—", "See quota terms")}</td><td>{_locale_pair(entry.get("note") or "—", entry.get("note") or "—", "See official terms")}</td></tr>'''
            for entry in free_models
        )
        free_models_markup = f'''<section>
      <h2>{_locale_pair("免费模型逐个看", "Free models by entry")}</h2>
      <div class="table-wrap"><table><thead><tr><th>{_locale_pair("模型", "Model")}</th><th>{_locale_pair("上下文窗口", "Context window")}</th><th>{_locale_pair("免费额度", "Free quota")}</th><th>{_locale_pair("备注", "Notes")}</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="muted">{_locale_pair("额度以官方页面和控制台实时显示为准；公测或限免额度可能随时调整。", "Quota follows the official page and console; preview or limited free access can change.")}</p>
    </section>'''
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "name": title,
                "description": description,
                "url": _absolute(site_url, path),
                "dateModified": offer.get("lastVerifiedAt"),
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "FreeLLM 免费 AI 资源索引", "item": _absolute(site_url, "/")},
                    {"@type": "ListItem", "position": 2, "name": title, "item": _absolute(site_url, path)},
                ],
            },
        ],
    }
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(page_title)}</title>
  <meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(_absolute(site_url, path))}">
  {_hreflang_links(site_url, path)}
  {social_meta}
  {_analytics_script()}
  {ADSENSE_SCRIPT}
  {STATIC_LOCALE_STYLE}
  {STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #172033; background: #f5f7fb; }}
    body {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 64px; line-height: 1.65; }}
    a {{ color: #1744e8; }}
    header, main, footer {{ background: white; border: 1px solid #dfe5ef; border-radius: 14px; padding: 24px; margin-bottom: 18px; }}
    header {{ background: #172033; color: white; }}
    header a {{ color: white; }}
    nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .tag {{ display: inline-block; padding: 3px 9px; border-radius: 999px; background: #e9efff; text-decoration: none; font-size: .9rem; }}
    .facts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .fact {{ padding: 13px; background: #f5f7fb; border-radius: 9px; }}
    .fact strong, .fact span {{ display: block; }}
    .fact strong {{ font-size: .78rem; color: #68748a; text-transform: uppercase; letter-spacing: .04em; }}
    pre {{ overflow-x: auto; padding: 14px; background: #172033; color: #f5f7fb; border-radius: 8px; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 9px 10px; border-bottom: 1px solid #dfe5ef; text-align: left; vertical-align: top; }}
    th {{ font-size: .82rem; color: #68748a; text-transform: uppercase; letter-spacing: .04em; }}
    code {{ background: #eef2f9; padding: 2px 6px; border-radius: 5px; }}
    .muted {{ color: #68748a; }}
    .operation-path {{ margin-top: 22px; padding: 18px; border: 1px solid #dfe5ef; border-radius: 10px; background: #fbfcff; }}
    .operation-path h3 {{ margin-top: 0; }}
    .operation-path h4 {{ margin: 18px 0 6px; }}
    .operation-type {{ display: inline-block; margin: 0; padding: 2px 8px; border-radius: 999px; color: #1744e8; background: #e9efff; font-size: .78rem; }}
    .operation-steps {{ padding-left: 1.4em; }}
    .operation-steps li {{ margin: 12px 0; }}
    .operation-steps p {{ margin: 4px 0; }}
    .operation-command {{ margin: 10px 0; }}
    .operation-command-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; color: #68748a; font-size: .82rem; }}
    .copy-command {{ border: 1px solid #b9c7e8; border-radius: 6px; padding: 4px 9px; color: #1744e8; background: white; cursor: pointer; }}
    .operation-facts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin: 14px 0; }}
    .operation-facts div {{ padding: 10px; border-radius: 8px; background: #f0f4fb; }}
    .operation-facts dt {{ color: #68748a; font-size: .78rem; }}
    .operation-facts dd {{ margin: 3px 0 0; overflow-wrap: anywhere; }}
    .operation-validation {{ margin-top: 18px; padding: 12px 14px; border-left: 4px solid #1a9a5a; background: #e6f7ee; }}
    .operation-limits, .operation-issues {{ margin-top: 14px; padding: 12px 14px; border-radius: 8px; background: #f0f4fb; }}
    .operation-limits p, .operation-issues ul {{ margin: 4px 0 0; }}
    @media (max-width: 600px) {{ body {{ padding: 14px 10px 40px; }} header, main, footer {{ padding: 18px; }} }}
  </style>
</head>
<body data-offer-id="{_esc(offer.get('id'))}" data-static-locale="true">
{_adsense_slot_markup()}
  <header>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair("FreeLLM 免费 AI 资源索引", "FreeLLM Free AI Index")}</a> / {_locale_pair("资源详情", "Offer details")}</p>
    {_static_locale_nav()}
    <h1>{_locale_pair(offer.get("titleZh") or title, title, "Offer details")}</h1>
    <p>{_locale_pair(offer.get("providerMeta") or offer.get("provider"), offer.get("providerMetaEn") or offer.get("provider"), "Official provider")}</p>
    <nav aria-label="Categories">{category_links}</nav>
  </header>
  <main>
    <section>
      <h2>{_locale_pair("这个资源提供什么", "What this offer provides")}</h2>
      <p>{_offer_locale_pair(offer, ("why",), "See the official offer details")}</p>
    </section>
    <section>
      <h2>{_locale_pair("关键信息", "Key details")}</h2>
      <div class="facts">
        <div class="fact"><strong>{_locale_pair("免费方式", "Free method")}</strong><span>{_offer_locale_pair(offer, ("freeSummary", "mechanism"), "Free access details unavailable")}</span></div>
        <div class="fact"><strong>{_locale_pair("有效期", "Validity")}</strong><span>{_offer_locale_pair(offer, ("validitySummary", "validity"), "Validity follows provider terms")}</span></div>
        <div class="fact"><strong>{_locale_pair("访问条件", "Access")}</strong><span>{_offer_locale_pair(offer, ("accessSummary", "access"), "Official account required")}</span></div>
        <div class="fact"><strong>{_locale_pair("最后核验", "Last checked")}</strong><span>{_esc(offer.get('lastVerifiedAt'))}</span></div>
      </div>
    </section>
{context_window_markup}
{access_paths_markup}
{operation_guides_markup}
{free_models_markup}
    <section>
      <h2>{_locale_pair("如何使用", "How to use")}</h2>
      <p>{_locale_pair(guide.get('summary') or offer.get('command'), _english_text(guide.get('summary') or offer.get('command'), "See the official setup guide"))}</p>
      <h3>{_locale_pair("前置条件", "Prerequisites")}</h3>
      {_list(guide.get('prerequisites') or [offer.get('access')], '请查看官方访问要求。')}
      <h3>{_locale_pair("步骤", "Steps")}</h3>
      {_list(guide.get('steps') or [offer.get('command')], '请按照官方设置说明操作。')}
      {example_markup}
    </section>
    <section>
      <h2>{_locale_pair("官方来源", "Official sources")}</h2>
      <p class="muted">{_locale_pair(offer.get('evidence'), _english_text(offer.get('evidence'), "See the official source links below"))}</p>
      <ul>{_source_links(offer)}</ul>
    </section>
    <section>
      <h2>{_locale_pair("相关资源", "Related resources")}</h2>
      <ul>{_related_links(offer, offers)}</ul>
    </section>
  </main>
  <footer>
    <p><strong>{_locale_pair("重要", "Important")}：</strong>{_locale_pair("免费访问可能受地区、账户类型、速率限制、有效期或提供商条款影响。依赖该资源前请核对官方来源。", "Free access may be affected by region, account type, rate limits, validity or provider terms; verify the official source before relying on this offer.")}</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair("返回 FreeLLM 免费 AI 资源索引", "Return to FreeLLM Free AI Index")}</a></p>
  </footer>
</body>
</html>
'''


def render_category_page(category: str, offers: list[dict], site_url: str) -> str:
    definition = CATEGORY_DEFINITIONS[category]
    matching = [offer for offer in offers if category in categorize_offer(offer)]
    path = category_url(category)
    title = f"{definition['name_zh']} · FreeLLM 免费 AI 资源索引"
    description = f"{definition['description_zh']}当前有 {len(matching)} 个经过核验的资源，均提供官方入口与有效期说明。"
    social_meta = _social_meta(site_url, path, title, description, "website")
    items = "".join(
        f'''<article>
          <h2><a href="{_esc(offer_url(offer))}">{_locale_pair(offer.get("titleZh") or offer.get("title") or offer.get("name"), offer.get("title") or offer.get("name"), "Offer details")}</a></h2>
          <p>{_offer_locale_pair(offer, ("freeSummary", "mechanism"), "Free access details unavailable")}</p>
          <p class="muted">{_offer_locale_pair(offer, ("validitySummary", "validity"), "Validity follows provider terms")} · {_offer_locale_pair(offer, ("accessSummary", "access"), "Official account required")}</p>
        </article>'''
        for offer in matching
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": _absolute(site_url, path),
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(matching),
            "itemListElement": [
                {"@type": "ListItem", "position": index, "url": _absolute(site_url, offer_url(offer)), "name": offer.get("title")}
                for index, offer in enumerate(matching, start=1)
            ],
        },
    }
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(_absolute(site_url, path))}">
  {social_meta}
  {_analytics_script()}
  {ADSENSE_SCRIPT}
  {STATIC_LOCALE_STYLE}
  {STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #172033; background: #f5f7fb; }}
    body {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 64px; line-height: 1.65; }}
    a {{ color: #1744e8; }}
    header, main, footer {{ background: white; border: 1px solid #dfe5ef; border-radius: 14px; padding: 24px; margin-bottom: 18px; }}
    header {{ background: #172033; color: white; }}
    header a {{ color: white; }}
    article {{ padding: 16px 0; border-bottom: 1px solid #e6eaf1; }}
    article:last-child {{ border-bottom: 0; }}
    h1 {{ margin-bottom: 8px; }}
    .muted {{ color: #68748a; }}
  </style>
</head>
<body data-static-locale="true">
  <header>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair('FreeLLM 免费 AI 资源索引', 'FreeLLM Free AI Index')}</a> / {_locale_pair('分类', 'Category')}</p>
    {_static_locale_nav()}
    <h1>{_locale_pair(definition['name_zh'], definition['name'])}</h1>
    <p>{_locale_pair(definition['description_zh'], definition['description'])}</p>
    <p>{_locale_pair(f'{len(matching)} 个经过核验的资源', f'{len(matching)} verified resources')}</p>
  </header>
  <main>
    {items}
  </main>
  <footer>
    <p>{_locale_pair('资源按免费额度、试用、优惠、学生资格、开放权重和低成本访问方式区分。使用前请核对官方条款。', 'Resources are grouped by free quota, trials, promotions, student eligibility, open weights and low-cost access. Verify provider terms before use.')}</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair('返回 FreeLLM 免费 AI 资源索引', 'Return to FreeLLM Free AI Index')}</a> · <a href="{_esc(_absolute(site_url, MODELS_PAGE_PATH))}">{_locale_pair('全部模型一览', 'Browse all models')}</a></p>
  </footer>
</body>
</html>
'''


def _guide_cell(value: object) -> str:
    if isinstance(value, tuple) and len(value) == 2:
        label, url = value
        return f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">{_esc(label)} ↗</a>'
    return _esc(value)


def _guide_table(headers: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th>{_esc(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{_guide_cell(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_guide_page(site_url: str) -> str:
    path = guide_url()
    title = "Free-LLM — 免费 AI 与 LLM API 开放目录"
    description = "参考 Free-LLM 中文 README 整理的免费 LLM API、免费额度、本地模型和 OpenAI 兼容接入指南。"
    python_example = '''from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="GROQ_API_KEY",  # 在官方控制台获取
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)'''
    schema = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "description": description,
        "url": _absolute(site_url, path),
        "inLanguage": "zh-CN",
        "dateModified": "2026-09-07",
        "isBasedOn": GUIDE_SOURCE_URL,
        "publisher": {"@type": "Organization", "name": "Free AI Index", "url": _absolute(site_url, "/")},
    }
    permanent = _guide_table(
        ["提供商", "需要信用卡？", "速率限制", "每日限额", "月度 / 其他额度", "主要模型"],
        GUIDE_PERMANENT_ROWS,
    )
    renewable = _guide_table(["提供商", "需要信用卡？", "速率限制", "免费额度", "主要模型"], GUIDE_RENEWABLE_ROWS)
    trials = _guide_table(["提供商", "注册要求", "额度", "有效期"], GUIDE_TRIAL_ROWS)
    local = _guide_table(["工具", "类型", "亮点"], GUIDE_LOCAL_ROWS)
    quickref = _guide_table(["提供商", "Base URL"], GUIDE_QUICKREF_ROWS)
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)} · Free AI Index</title>
  <meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(_absolute(site_url, path))}">
  {_social_meta(site_url, path, f'{title} · Free AI Index', description, 'article')}
  {_analytics_script()}
  {ADSENSE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #68748a; --line: #dfe5ef; --blue: #1744e8; --soft: #f5f7fb; --green: #e6f7ee; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: var(--ink); background: var(--soft); }}
    * {{ box-sizing: border-box; }}
    body {{ max-width: 1180px; margin: 0 auto; padding: 24px 18px 64px; line-height: 1.65; }}
    a {{ color: var(--blue); }}
    header, main, footer {{ background: white; border: 1px solid var(--line); border-radius: 16px; padding: clamp(20px, 4vw, 34px); margin-bottom: 18px; }}
    header {{ color: white; background: linear-gradient(135deg, #172033, #243f78); border-color: #172033; }}
    header a {{ color: white; }}
    header h1 {{ max-width: 760px; margin: 22px 0 8px; font-size: clamp(34px, 6vw, 62px); line-height: 1.05; letter-spacing: -.06em; }}
    header p {{ max-width: 780px; margin: 8px 0; color: #dbe6ff; }}
    .crumb, .eyebrow {{ font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }}
    .source {{ display: flex; flex-wrap: wrap; gap: 10px 18px; margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,.22); font-size: 13px; }}
    main {{ display: grid; gap: 28px; }}
    section + section {{ padding-top: 26px; border-top: 1px solid var(--line); }}
    h2 {{ margin: 0 0 8px; font-size: clamp(24px, 4vw, 34px); letter-spacing: -.04em; }}
    h3 {{ margin: 22px 0 6px; font-size: 20px; }}
    p {{ max-width: 860px; }}
    .lead {{ font-size: 17px; color: #3d4b63; }}
    .steps, .link-list {{ padding-left: 1.4em; }}
    .steps li {{ margin: 8px 0; }}
    .callout {{ padding: 16px 18px; border-left: 4px solid var(--blue); background: var(--soft); }}
    .callout.green {{ border-left-color: #1a9a5a; background: var(--green); }}
    pre {{ overflow-x: auto; margin: 12px 0; padding: 18px; border-radius: 10px; background: #101827; color: #e9f0ff; font: 13px/1.65 ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; margin: 12px 0 20px; }}
    table {{ width: 100%; min-width: 760px; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 10px 12px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
    th {{ color: #53627b; background: var(--soft); font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; }}
    tr:last-child td {{ border-bottom: 0; }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    footer {{ color: var(--muted); font-size: 13px; }}
    footer strong {{ color: var(--ink); }}
    @media (max-width: 620px) {{ body {{ padding: 10px 8px 38px; }} header, main, footer {{ border-radius: 12px; padding: 18px; }} header h1 {{ font-size: 42px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / 使用指南</div>
    <h1>{_esc(title)}</h1>
    <p>来自多个提供商的免费 LLM API、试用额度和本地 / 自托管工具，帮助你几秒钟内发现、比较并开始接入。</p>
    <div class="source">
      <span>参考来源：<a href="{_esc(GUIDE_SOURCE_URL)}" target="_blank" rel="noopener noreferrer">README.zh-CN.md ↗</a></span>
      <span>仓库：<a href="{_esc(GUIDE_REPOSITORY_URL)}" target="_blank" rel="noopener noreferrer">nejib1/Free-LLM ↗</a></span>
      <span>许可证：MIT License</span>
    </div>
  </header>
  <main>
    <section>
      <div class="eyebrow">01 / why this exists</div>
      <h2>为什么需要这个项目</h2>
      <p class="lead">找一个免费 LLM API，不应该翻遍十几个更新日志，为了对比速率限制去注册五个不同平台，或者猜测哪个提供商这个月还有免费额度。</p>
      <p>这是一份参考型目录：把提供商、模型、限制条件、获取 Key 的入口和接入方式集中到一起。社区维护、信用卡透明、可复制的代码示例和并排比较，是 README 中最值得保留的使用路径。</p>
      <div class="callout green"><strong>重要：</strong>免费额度、地区、验证要求和服务条款会变化。下方内容来自参考 README 的整理快照，实际使用前请打开每行的官方链接再次确认。</div>
    </section>
    <section>
      <div class="eyebrow">02 / start here</div>
      <h2>三步上手</h2>
      <ol class="steps">
        <li><strong>选一个提供商：</strong>先看下方 Provider Directory；新手可以优先尝试 Groq、Google AI Studio 等清晰标注免费层的入口。</li>
        <li><strong>获取 API Key：</strong>打开 Quick Reference 中对应的官方控制台或密钥页面，确认是否需要邮箱、手机或银行卡。</li>
        <li><strong>接入代码：</strong>把 Base URL 与模型 ID 填入下面的 OpenAI 兼容示例，并根据官方限制控制速率和用量。</li>
      </ol>
      <p class="meta">完整提供商详情和社区备注请查看原始项目及各 Provider 官方文档。</p>
    </section>
    <section>
      <div class="eyebrow">03 / quick start</div>
      <h2>Quick Start — 30 秒接入免费 API</h2>
      <p>大多数提供商提供 OpenAI 兼容接口。接受 <code>baseURL</code> 与 <code>apiKey</code> 的工具通常只需要替换这两项。</p>
      <h3>Python（OpenAI SDK）</h3>
      <pre><code>{_esc(python_example)}</code></pre>
      <h3>编程助手</h3>
      <ul class="link-list">
        <li><strong>Claude Code：</strong>配置 <code>ANTHROPIC_BASE_URL</code> 与 <code>ANTHROPIC_AUTH_TOKEN</code>。</li>
        <li><strong>Cursor：</strong>Settings → Models → Add Model。</li>
        <li><strong>Codex CLI：</strong>配置 <code>OPENAI_BASE_URL</code> 与 <code>OPENAI_API_KEY</code>。</li>
      </ul>
    </section>
    <section>
      <div class="eyebrow">04 / provider directory</div>
      <h2>Provider Directory</h2>
      <h3>⚡ 永久免费额度</h3>
      <p>持续免费访问，通常会限速，但不以一次性试用为前提。</p>
      {permanent}
      <h3>💰 可续期额度</h3>
      <p>定期续期的免费额度，不是一次性用完即止。</p>
      {renewable}
      <h3>🎁 一次性试用额度</h3>
      <p>注册后获得一次性 credits 或金额，用完为止；部分平台可能要求注册或充值。</p>
      {trials}
    </section>
    <section>
      <div class="eyebrow">05 / local and self-hosted</div>
      <h2>本地 / 自托管</h2>
      <p>本地运行可以获得更强的隐私和可控性，但“模型权重免费”不等于 GPU、存储和推理基础设施免费。</p>
      {local}
    </section>
    <section>
      <div class="eyebrow">06 / quick reference</div>
      <h2>Quick Reference — Base URL 与 API Key 速查</h2>
      <p>下面列出 README 中的代表性入口。Base URL、模型 ID 和 Key 获取地址应以提供商官方文档为准。</p>
      {quickref}
      <p class="meta">需要更完整的列表时，请直接查看 <a href="{_esc(GUIDE_SOURCE_URL)}" target="_blank" rel="noopener noreferrer">原始中文 README ↗</a>。</p>
    </section>
    <section>
      <div class="eyebrow">07 / guides and community</div>
      <h2>使用指南与社区功能</h2>
      <ul class="link-list">
        <li>2026 年最佳免费 LLM API：主流选择横向对比。</li>
        <li>Gemini vs ChatGPT（免费版）：了解免费版的实际使用边界。</li>
        <li>如何使用 OpenRouter：附代码的配置教程。</li>
        <li>OpenRouter 替代方案、Ollama 本地模型和终极免费 LLM API 指南。</li>
        <li>社区用户可以提交新的提供商、建议编辑、投票或举报已变化的免费状态。</li>
      </ul>
      <div class="callout"><strong>来源边界：</strong>本页面借鉴并展示参考 README 的信息结构与部分目录内容；本站自己的 Offer 仍以官方证据和 `data/offers.json` 为准。</div>
    </section>
    <section>
      <div class="eyebrow">08 / free coding IDEs on Free AI Index</div>
      <h2>精选免费编程 IDE 与试用计划</h2>
      <p class="lead">想要本地开发工具而不是 API 调用，下面这些产品提供长期免费额度或一次性试用，可以直接从目录页查阅具体限制。</p>
      <ul class="link-list">
        <li><a href="{_esc(category_url('free-ide'))}">全部免费 AI 编程 IDE</a> — Cursor、Trae、GitHub Copilot、CodeBuddy 等IDE产品集合。</li>
        <li><a href="{_esc(offer_url({'id':'cursor-hobby','provider':'Cursor'}))}">Cursor Hobby 免费方案</a> — 每月恢复额度的个人免费计划。</li>
        <li><a href="{_esc(offer_url({'id':'github-copilot-free','provider':'GitHub'}))}">GitHub Copilot 免费版</a> — 学生或开源维护者的永久免费路径。</li>
        <li><a href="{_esc(offer_url({'id':'amazon-q-free','provider':'Amazon Q Developer'}))}">Amazon Q Developer 免费层</a> — 以 AWS 账户绑定的独立免费 IDE。</li>
        <li><a href="{_esc(offer_url({'id':'google-antigravity-free','provider':'Google Antigravity'}))}">Google Antigravity 个人免费版</a> — Google 出品的独立编程工具免费额度。</li>
        <li><a href="{_esc(category_url('promo'))}">AI 试用与优惠活动</a> — 限时试用、首月优惠等短期免费入口。</li>
      </ul>
    </section>
    <section>
      <div class="eyebrow">09 / open-weight downloads</div>
      <h2>开源权重模型下载</h2>
      <p class="lead">本地运行模型的前提条件不只是权重免费，还需要 GPU、显存和网络出站带宽。下面三个下载入口附有官方仓库和安装命令。</p>
      <ul class="link-list">
        <li><a href="{_esc(category_url('open-weights'))}">全部开源权重模型目录</a> — 按权重和参数规模组织的下载清单。</li>
        <li><a href="{_esc(offer_url({'id':'qwen-download','provider':'Qwen / Alibaba'}))}">Qwen3-4B 开源权重下载</a> — 阿里通义千问的中量级中文优先模型。</li>
        <li><a href="{_esc(offer_url({'id':'glm-download','provider':'Zhipu AI'}))}">GLM-4.7-Flash 开源权重下载</a> — 智谱 AI 的中量级推理模型。</li>
        <li><a href="{_esc(offer_url({'id':'longcat-2-0','provider':'LongCat'}))}">LongCat-2.0 API + 开源权重</a> — 同一模型的在线调用与本地部署入口。</li>
      </ul>
    </section>
  </main>
  <footer>
    <p><strong>免责声明：</strong>免费服务可能受地区、账户类型、速率限制、有效期和 Provider 条款影响。不要把免费试用当作生产系统的稳定推理基础设施。</p>
    <p>参考项目内容按其仓库声明的 <strong>MIT License</strong> 使用，并保留来源与许可说明。<a href="{_esc(_absolute(site_url, '/'))}">返回 Free AI Index 首页 →</a></p>
  </footer>
</body>
</html>
'''


def _offer_by_id(offers: list[dict], offer_id: str) -> dict:
    for offer in offers:
        if offer.get("id") == offer_id:
            return offer
    raise ValueError(f"SEO guide references missing offer: {offer_id}")


def _special_guide_rows(offers: list[dict], site_url: str, rows: list[tuple[str, str, str, str]]) -> str:
    rendered = []
    for offer_id, label, fit, source_url in rows:
        offer = _offer_by_id(offers, offer_id)
        detail = _absolute(site_url, offer_url(offer))
        rendered.append(
            f'''<tr>
              <td><a href="{_esc(offer_url(offer))}">{_esc(label)}</a><small>{_esc(offer.get("model") or offer.get("name"))}</small></td>
              <td>{_esc(fit)}</td>
              <td><a href="{_esc(source_url)}" target="_blank" rel="noopener noreferrer">Official source ↗</a><br><a href="{_esc(detail)}">FreeLLM record ↗</a></td>
            </tr>'''
        )
    return "".join(rendered)


def render_special_guide_page(
    offers: list[dict],
    site_url: str,
    path: str,
    title: str,
    description: str,
    eyebrow: str,
    lead: str,
    caution: str,
    rows: list[tuple[str, str, str, str]],
    setup_heading: str,
    setup_html: str,
    related_html: str,
) -> str:
    page_url = _absolute(site_url, path)
    table_rows = _special_guide_rows(offers, site_url, rows)
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": page_url,
        "inLanguage": "en",
        "dateModified": "2026-09-08",
        "isPartOf": {"@type": "WebSite", "name": "Free AI Index", "url": _absolute(site_url, "/")},
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Free AI Index", "item": _absolute(site_url, "/")},
                {"@type": "ListItem", "position": 2, "name": title, "item": page_url},
            ],
        },
    }
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(page_url)}">
  {_social_meta(site_url, path, title, description, "article")}
  {_analytics_script()}
  {ADSENSE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #68748a; --line: #dfe5ef; --soft: #f5f7fb; --blue: #1744e8; --green: #e6f7ee; }}
    * {{ box-sizing: border-box; }}
    body {{ max-width: 1080px; margin: 0 auto; padding: 24px 18px 64px; line-height: 1.65; color: var(--ink); background: var(--soft); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    a {{ color: var(--blue); }}
    header, main, footer {{ background: white; border: 1px solid var(--line); border-radius: 16px; padding: clamp(20px, 4vw, 36px); margin-bottom: 18px; }}
    header {{ color: white; background: linear-gradient(135deg, #172033, #243f78); border-color: #172033; }}
    header a {{ color: white; }}
    h1 {{ max-width: 820px; margin: 22px 0 10px; font-size: clamp(34px, 6vw, 62px); line-height: 1.05; letter-spacing: -.05em; }}
    h2 {{ margin: 0 0 10px; font-size: clamp(24px, 4vw, 34px); letter-spacing: -.03em; }}
    h3 {{ margin: 24px 0 6px; font-size: 19px; }}
    p {{ max-width: 860px; }}
    .crumb, .eyebrow, th {{ font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }}
    .lead {{ max-width: 800px; color: #dbe6ff; font-size: 17px; }}
    .callout {{ margin: 22px 0 0; padding: 16px 18px; border-left: 4px solid #79e5a3; background: rgba(255,255,255,.1); }}
    section + section {{ padding-top: 28px; border-top: 1px solid var(--line); }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; margin: 16px 0 8px; }}
    table {{ width: 100%; min-width: 760px; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 12px 14px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
    th {{ color: var(--muted); background: var(--soft); }}
    tr:last-child td {{ border-bottom: 0; }}
    td small {{ display: block; margin-top: 4px; color: var(--muted); }}
    pre {{ overflow-x: auto; padding: 18px; border-radius: 10px; background: #101827; color: #e9f0ff; font: 13px/1.65 ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .notice {{ padding: 16px 18px; border-left: 4px solid #1a9a5a; background: var(--green); }}
    .link-list {{ padding-left: 1.3em; }}
    footer {{ color: var(--muted); font-size: 13px; }}
  </style>
</head>
<body>
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / Guides</div>
    <h1>{_esc(title)}</h1>
    <p class="lead">{_esc(lead)}</p>
    <div class="callout">{_esc(caution)}</div>
  </header>
  <main>
    <section>
      <div class="eyebrow">01 / verified paths</div>
      <h2>Verified options and their limits</h2>
      <p>Each row links to a FreeLLM record and an official provider source. Quotas, regions, account requirements and prices can change, so verify the provider page before relying on an offer.</p>
      <div class="table-wrap"><table><thead><tr><th>Provider / model</th><th>What the current record says</th><th>Next step</th></tr></thead><tbody>{table_rows}</tbody></table></div>
    </section>
    <section>
      <div class="eyebrow">02 / setup</div>
      <h2>{_esc(setup_heading)}</h2>
      {setup_html}
    </section>
    <section>
      <div class="eyebrow">03 / related pages</div>
      <h2>Continue exploring</h2>
      {related_html}
    </section>
  </main>
  <footer>
    <p><strong>Last checked:</strong> 8 September 2026. Free access is always subject to provider terms, region, quota and account eligibility.</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">Return to Free AI Index →</a></p>
  </footer>
</body>
</html>
'''


def render_openai_alternatives_page(offers: list[dict], site_url: str) -> str:
    return render_special_guide_page(
        offers,
        site_url,
        "/guides/free-openai-api-alternatives/",
        "Free OpenAI API Alternatives — OpenAI-Compatible Free API Options | FreeLLM",
        "Compare verified OpenAI-compatible API alternatives with free tiers, credits, rate limits and official setup links.",
        "OpenAI-compatible API guide",
        "Compare practical OpenAI API alternatives for prototypes and developer tools, with free access conditions and limits shown next to the official source.",
        "Important: OpenAI's official API is not presented as permanently free on this page. The entries below are independent providers or OpenAI-compatible endpoints.",
        OPENAI_ALTERNATIVE_ROWS,
        "Quick start with an OpenAI-compatible SDK",
        '''<p>Most compatible providers use the OpenAI SDK shape. Replace the base URL and API key, then use the model ID listed in the provider documentation.</p>
      <pre><code>from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="YOUR_PROVIDER_KEY",
)

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": "Hello"}],
)</code></pre>
      <p>Do not copy a model ID or quota from a different provider. The official source link in each row is the authority.</p>''',
        '''<ul class="link-list">
        <li><a href="/guides/free-llm/">Free LLM and API quick-start guide</a></li>
        <li><a href="/category/api/">Browse all verified AI API services</a></li>
        <li><a href="/offers/groq-free/">Groq free plan details</a></li>
        <li><a href="/offers/hf-inference-free/">Hugging Face free inference details</a></li>
      </ul>''',
    )


def render_claude_code_alternatives_page(offers: list[dict], site_url: str) -> str:
    return render_special_guide_page(
        offers,
        site_url,
        "/guides/claude-code-free-alternatives/",
        "Free Claude Code Alternatives — Coding Models and Plans | FreeLLM",
        "Compare verified coding plans and API paths that can work with Claude Code or compatible coding tools, with region and quota notes.",
        "Claude Code compatibility guide",
        "Find coding-focused plans and API paths for Claude Code workflows, then verify the exact adapter, endpoint and quota rules in the official documentation.",
        "Important: these are third-party options and are not Claude's official free service. Claude Code compatibility, authentication and quota rules depend on the provider and the supported tool path.",
        CLAUDE_CODE_ALTERNATIVE_ROWS,
        "Configure a coding tool safely",
        '''<p>Claude Code integrations commonly use <code>ANTHROPIC_BASE_URL</code> and <code>ANTHROPIC_AUTH_TOKEN</code>, but the exact endpoint and authentication requirements are provider-specific.</p>
      <pre><code>export ANTHROPIC_BASE_URL="YOUR_PROVIDER_ENDPOINT"
export ANTHROPIC_AUTH_TOKEN="YOUR_PROVIDER_TOKEN"

# Follow the provider's official Claude Code or coding-plan quick start.
# Confirm region, quota window and supported tools before use.</code></pre>
      <p>GLM Coding Plan has a dedicated coding endpoint documented for Claude Code, Cursor and Cline. Start from its official FAQ and quick start rather than guessing an API URL.</p>''',
        '''<ul class="link-list">
        <li><a href="/offers/glm/">GLM Coding Plan details</a></li>
        <li><a href="/category/free-ide/">Browse free AI coding IDEs</a></li>
        <li><a href="/category/api/">Browse AI API services</a></li>
        <li><a href="/guides/free-openai-api-alternatives/">OpenAI-compatible API alternatives</a></li>
      </ul>''',
    )


def _models_page_sections(offers: list[dict]) -> list[tuple[tuple[str, str, str, str] | None, list[dict]]]:
    """Group offers under their first matching category; uncategorized offers land in Other."""
    grouped: dict[str, list[dict]] = {}
    for offer in sorted(offers, key=lambda item: (item.get("order", 10**9), item.get("id", ""))):
        categories = categorize_offer(offer)
        key = categories[0] if categories else "_other"
        grouped.setdefault(key, []).append(offer)
    sections: list[tuple[tuple[str, str, str, str] | None, list[dict]]] = []
    for category in CATEGORY_DEFINITIONS:
        matching = grouped.pop(category, [])
        if matching:
            definition = CATEGORY_DEFINITIONS[category]
            sections.append(((definition["name_zh"], definition["name"], definition["description_zh"], definition["description"]), matching))
    other = grouped.pop("_other", [])
    if other:
        sections.append((("其他资源", "Other resources", "尚未归入主分类的核验资源。", "Verified resources not yet grouped under a main category."), other))
    return sections


def _model_card(offer: dict) -> str:
    register_url = offer.get("register") or ""
    register_markup = (
        f'<a class="btn" href="{_esc(register_url)}" target="_blank" rel="nofollow noopener">{_locale_pair("注册领取", "Register")} ↗</a>'
        if register_url
        else ""
    )
    badges = "".join(f'<span class="badge">{_english_text(badge, "Status")}</span>' for badge in (offer.get("badges") or [])[:3])
    title = _locale_pair(
        offer.get("titleZh") or offer.get("title") or offer.get("name"),
        offer.get("title") or offer.get("name"),
        "Offer details",
    )
    provider = _locale_pair(
        offer.get("providerMeta") or offer.get("provider"),
        offer.get("providerMetaEn") or offer.get("provider"),
        "Official provider",
    )
    model = _offer_locale_pair(offer, ("model", "name"), "Listed model")
    return f'''<article class="model-card">
      <div class="card-head">
        <span class="mark">{_esc(_english_text(str(offer.get("providerMark") or offer.get("provider") or "?")[:2].upper(), "AI")[:2].upper())}</span>
        <div>
          <h3><a href="{_esc(offer_url(offer))}">{title}</a></h3>
          <p class="provider">{_locale_pair(offer.get("provider"), offer.get("provider"), "AI provider")}{(" · " + provider) if offer.get("providerMeta") or offer.get("providerMetaEn") else ""}</p>
        </div>
      </div>
      <p class="model">{model}{(" · " + _locale_pair(offer.get("modelMeta"), offer.get("modelMetaEn") or offer.get("modelMeta"), "Model details")) if offer.get("modelMeta") or offer.get("modelMetaEn") else ""}</p>
      <dl class="facts">
        <div><dt>{_locale_pair("免费额度", "Free quota")}</dt><dd>{_offer_locale_pair(offer, ("freeSummary", "mechanism"), "Free access details unavailable")}</dd></div>
        <div><dt>{_locale_pair("访问条件", "Access")}</dt><dd>{_offer_locale_pair(offer, ("accessSummary", "access"), "Official account required")}</dd></div>
        <div><dt>{_locale_pair("有效期", "Validity")}</dt><dd>{_offer_locale_pair(offer, ("validitySummary", "validity"), "Validity follows provider terms")}</dd></div>
      </dl>
      {f'<div class="badges">{badges}</div>' if badges else ''}
      <div class="actions">
        {register_markup}
        <a class="ghost" href="{_esc(offer_url(offer))}">{_locale_pair("详情", "Details")} </a>
      </div>
    </article>'''


_CN_STATUS_LABELS = {
    "available": ("大陆可用", "Available in mainland CN"),
    "unavailable": ("大陆不可用", "Unavailable in mainland CN"),
    "unknown": ("大陆待核验", "Unverified in mainland CN"),
}


def _load_access_context() -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    """Load provider access cards and region policies from the repo data directory."""
    data_dir = ACCESS_DATA_DIR
    try:
        provider_cards = json.loads((data_dir / "provider-access.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Invalid provider access data: {error}") from error
    try:
        policies_data = json.loads((data_dir / "region-policies.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Invalid region policy data: {error}") from error
    try:
        model_cards = json.loads((data_dir / "model-access.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Invalid model access data: {error}") from error
    if not isinstance(provider_cards, list):
        raise SystemExit("Invalid provider access data: expected a JSON array")
    if not isinstance(policies_data, dict) or not isinstance(policies_data.get("policies"), list):
        raise SystemExit("Invalid region policy data: expected an object with a policies array")
    if not isinstance(model_cards, list):
        raise SystemExit("Invalid model access data: expected a JSON array")
    schema_errors = [
        *validate_provider_access_file(provider_cards),
        *validate_region_policies(policies_data),
        *validate_model_access_file(model_cards),
    ]
    if schema_errors:
        raise SystemExit("Invalid access data:\n" + "\n".join(schema_errors))
    cards = {str(card.get("providerId") or ""): card for card in provider_cards if isinstance(card, dict)}
    policies = {str(policy.get("id") or ""): policy for policy in policies_data["policies"] if isinstance(policy, dict)}
    model_access = {str(card.get("modelId") or ""): card for card in model_cards if isinstance(card, dict)}
    errors = validate_access_references(provider_cards, model_cards, set(policies))
    if errors:
        raise SystemExit("Invalid access references:\n" + "\n".join(errors))
    return cards, policies, model_access


def _cn_status_for_policy(policy: dict | None) -> str:
    """Derive mainland-CN availability from one region policy; absence of evidence stays unknown."""
    if not isinstance(policy, dict):
        return "unknown"
    policy_type = policy.get("type")
    if policy_type == "denylist":
        blocked = policy.get("blockedCountries") or []
        return "unavailable" if "CN" in blocked else "unknown"
    if policy_type == "allowlist":
        allowed = policy.get("allowedCountries") or []
        if policy.get("countriesComplete") is True:
            return "available" if "CN" in allowed else "unavailable"
        return "unknown"
    return "unknown"


def _cn_region_status_map() -> dict[str, dict]:
    cards, policies, _ = _load_access_context()
    statuses: dict[str, dict] = {}
    for provider_id, card in cards.items():
        if card.get("registrationStatus") == "unavailable":
            code = "unavailable"
        else:
            code = _cn_status_for_policy(policies.get(str(card.get("regionPolicyId") or "")))
        zh, en = _CN_STATUS_LABELS[code]
        statuses[provider_id] = {"code": code, "zh": zh, "en": en}
    return statuses


def _cn_status_for_model(model: dict, provider_cards: dict[str, dict], policies: dict[str, dict], model_access: dict[str, dict]) -> str:
    provider = provider_cards.get(str(model.get("providerId") or "")) or {}
    access = model_access.get(str(model.get("id") or "")) or {}
    if access.get("accessStatus") == "retired" or provider.get("registrationStatus") == "unavailable":
        return "unavailable"
    policy_id = access.get("regionOverridePolicyId") or provider.get("regionPolicyId")
    return _cn_status_for_policy(policies.get(str(policy_id or "")))


def _model_catalog_row(model: dict, cn_statuses: dict[str, dict] | None = None) -> str:
    score = model.get("score")
    score_markup = f'<span class="score-ring" style="--score:{_esc(score)}" aria-label="Score {_esc(score)}"><strong>{_esc(score)}</strong></span>' if score is not None else '<span class="muted">—</span>'
    modalities = "".join(f'<span class="model-badge">{_esc(item)}</span>' for item in (model.get("modality") or []))
    status = str(model.get("status") or "unknown")
    status_label = _locale_pair(
        {"online": "在线", "offline": "离线", "degraded": "降级"}.get(status, "未知"),
        {"online": "Online", "offline": "Offline", "degraded": "Degraded"}.get(status, "Unknown"),
    )
    freshness = str(model.get("freshnessStatus") or "").lower()
    freshness_label = {
        "new": _locale_pair("新", "New"),
        "current": _locale_pair("当前", "Current"),
        "stale": _locale_pair("过期", "Stale"),
    }.get(freshness)
    freshness_markup = f'<small class="freshness freshness-{_esc(freshness)}">{freshness_label}</small>' if freshness_label else ""
    provider_id = str(model.get("providerId") or "")
    model_id = str(model.get("id") or "")
    cn = (cn_statuses or {}).get(model_id) or (cn_statuses or {}).get(provider_id) or {"code": "unknown", "zh": _CN_STATUS_LABELS["unknown"][0], "en": _CN_STATUS_LABELS["unknown"][1]}
    return f'''<tr class="catalog-row" data-model-id="{_esc(model_id)}" data-provider-id="{_esc(provider_id)}" data-provider="{_esc(str(model.get("provider") or "").lower())}" data-model="{_esc(str(model.get("model") or "").lower())}" data-score="{_esc(score if score is not None else -1)}" data-cn="{_esc(cn["code"])}">
      <td class="provider-cell"><button class="provider-filter" type="button" data-provider-value="{_esc(provider_id)}">{_esc(model.get("provider"))}</button><a class="provider-page-link" href="{_esc(provider_url(provider_id))}">{_locale_pair("详情", "Details")}</a></td>
      <td class="model-cell"><a class="model-name" href="{_esc(model_aggregate_url(model))}" title="{_esc(model.get("model"))}"><strong>{_esc(model.get("model"))}</strong></a><small class="model-id" title="{_esc(model_id)}">{_esc(model_id)}</small></td>
      <td>{score_markup}</td>
      <td>{_esc(model.get("context") or "—")}</td>
      <td>{_esc(model.get("maxOutput") or "—")}</td>
      <td><div class="model-badges">{modalities or '<span class="muted">—</span>'}</div></td>
      <td>{_esc(model.get("rateLimit") or "—")}</td>
      <td>{_esc(model.get("released") or "—")}</td>
      <td>{_esc(model.get("usageActivity") or "—")}</td>
      <td><span class="status status-{_esc(status)}">{status_label}</span>{freshness_markup}</td>
      <td><span class="status cn-region cn-region-{_esc(cn["code"])}"><span lang="zh-CN">{_esc(cn["zh"])}</span><span lang="en">{_esc(cn["en"])}</span></span></td>
      <td class="source-cell"><a href="{_esc(model.get("sourceUrl") or "#")}" target="_blank" rel="noopener noreferrer">{_locale_pair("目录来源", "Catalog source")} ↗</a></td>
    </tr>'''


def _model_catalog_markup(models: list[dict], include_heading: bool = True) -> str:
    if not models:
        return ""
    provider_cards, policies, model_access = _load_access_context()
    cn_statuses = {}
    for model in models:
        code = _cn_status_for_model(model, provider_cards, policies, model_access)
        cn_statuses[str(model.get("id") or "")] = {"code": code, "zh": _CN_STATUS_LABELS[code][0], "en": _CN_STATUS_LABELS[code][1]}
    providers = sorted({(str(model.get("providerId") or ""), str(model.get("provider") or "")) for model in models}, key=lambda item: item[1].lower())
    provider_options = "".join(f'<option value="{_esc(provider_id)}">{_esc(name)}</option>' for provider_id, name in providers if provider_id)
    rows = "".join(_model_catalog_row(model, cn_statuses) for model in models)
    heading_markup = f'''<div class="eyebrow">{_locale_pair("01 / 实时模型目录", "01 / Live model directory")}</div>
      <h2>{_locale_pair("模型大列表", "Model directory")} <small>{len(models)}</small></h2>
      <p class="section-desc">{_locale_pair("按模型查找可用入口，或按厂商查看完整模型家族。这里展示目录数据；具体免费额度和接入步骤进入对应资源详情。", "Search by model or browse a complete provider family. This directory shows catalog facts; open the linked access record for free-tier terms and step-by-step setup.")}</p>''' if include_heading else ""
    return f'''<section id="model-directory" class="model-directory">
      {heading_markup}
      <div class="catalog-toolbar" role="search">
        <label class="catalog-search-label" for="model-catalog-search">{_locale_pair("搜索模型或厂商", "Search models or providers")}</label>
        <input id="model-catalog-search" type="search" placeholder="搜索模型或厂商" data-placeholder-zh="搜索模型或厂商" data-placeholder-en="Search models or providers" autocomplete="off">
        <label class="catalog-provider-label" for="model-catalog-provider">{_locale_pair("厂商", "Provider")}</label>
        <select id="model-catalog-provider"><option value="" data-label-zh="全部厂商" data-label-en="All providers">全部厂商</option>{provider_options}</select>
        <label class="catalog-region-label" for="model-catalog-region">{_locale_pair("大陆可用性", "Mainland CN")}</label>
        <select id="model-catalog-region">
          <option value="" data-label-zh="全部状态" data-label-en="All statuses" selected>全部状态</option>
          <option value="available" data-label-zh="大陆可用" data-label-en="Available">大陆可用</option>
          <option value="unknown" data-label-zh="大陆待核验" data-label-en="Unverified">大陆待核验</option>
          <option value="unavailable" data-label-zh="大陆不可用" data-label-en="Unavailable">大陆不可用</option>
        </select>
        <div class="catalog-modes" aria-label="排序方式 / Group by">
          <button type="button" class="group-mode is-active" data-group-mode="score">{_locale_pair("按评分", "Score")}</button>
          <button type="button" class="group-mode" data-group-mode="provider">{_locale_pair("按厂商分组", "By provider")}</button>
          <button type="button" class="group-mode" data-group-mode="model">{_locale_pair("按模型分组", "By model")}</button>
        </div>
        <span id="model-catalog-count" class="catalog-count">{_locale_pair(f"显示 {len(models)} 条 / 共 {len(models)} 条", f"Showing {len(models)} / {len(models)}")}</span>
      </div>
      <p class="catalog-hint">{_locale_pair("这是连续长列表，不分页；可滚动查看全部记录。筛选后会显示当前匹配数量。", "This is one continuous list, not pagination; scroll to view all records. Filters show the current match count.")}</p>
      <div class="catalog-table-wrap"><table id="model-catalog" class="catalog-table"><thead><tr>
        <th>{_locale_pair("厂商", "Provider")}</th><th>{_locale_pair("模型", "Model")}</th><th>{_locale_pair("评分", "Score")}</th><th>{_locale_pair("上下文", "Context")}</th><th>{_locale_pair("最大输出", "Max output")}</th><th>{_locale_pair("模态", "Modality")}</th><th>{_locale_pair("速率限制", "Rate limit")}</th><th>{_locale_pair("发布日期", "Released")}</th><th>{_locale_pair("使用量 / 活动", "Usage / Activity")}</th><th>{_locale_pair("状态", "Status")}</th><th>{_locale_pair("大陆可用性", "Mainland CN")}</th><th>{_locale_pair("来源", "Source")}</th>
      </tr></thead><tbody>{rows}</tbody></table></div>
      <p id="model-catalog-empty" class="catalog-empty" hidden>{_locale_pair("没有匹配的模型。换个关键词或清除厂商、地区筛选。", "No models match this filter. Try another keyword or clear the provider and region filters.")}</p>
      <script>
        (() => {{
          const table = document.getElementById('model-catalog');
          const body = table?.querySelector('tbody');
          const rows = body ? Array.from(body.querySelectorAll('.catalog-row')) : [];
          const search = document.getElementById('model-catalog-search');
          const provider = document.getElementById('model-catalog-provider');
          const region = document.getElementById('model-catalog-region');
          const count = document.getElementById('model-catalog-count');
          const empty = document.getElementById('model-catalog-empty');
          const modes = Array.from(document.querySelectorAll('[data-group-mode]'));
          let mode = 'score';
          const isEnglish = () => document.documentElement.dataset.locale === 'en' || document.documentElement.lang === 'en';
          const localizeControls = () => {{
            if (search) search.placeholder = isEnglish() ? search.dataset.placeholderEn : search.dataset.placeholderZh;
            const allProviders = provider?.querySelector('option[value=""]');
            if (allProviders) allProviders.textContent = isEnglish() ? allProviders.dataset.labelEn : allProviders.dataset.labelZh;
            region?.querySelectorAll('option[data-label-zh]').forEach(option => {{
              option.textContent = isEnglish() ? option.dataset.labelEn : option.dataset.labelZh;
            }});
          }};
          const apply = () => {{
            const query = (search?.value || '').trim().toLowerCase();
            const providerId = provider?.value || '';
            const regionFilter = region?.value || '';
            const visible = rows.filter(row => {{
              const matchesText = !query || `${{row.dataset.provider || ''}} ${{row.dataset.model || ''}} ${{row.dataset.modelId || ''}}`.includes(query);
              const matchesProvider = !providerId || row.dataset.providerId === providerId;
              const matchesRegion = !regionFilter || row.dataset.cn === regionFilter;
              row.hidden = !(matchesText && matchesProvider && matchesRegion);
              return matchesText && matchesProvider && matchesRegion;
            }});
            const value = row => mode === 'provider' ? `${{row.dataset.provider || ''}} ${{row.dataset.model || ''}}` : mode === 'model' ? `${{row.dataset.model || ''}} ${{row.dataset.provider || ''}}` : String(999 - Number(row.dataset.score || -1)).padStart(3, '0');
            visible.sort((a, b) => value(a).localeCompare(value(b), undefined, {{numeric: true}}));
            body.querySelectorAll('.catalog-group-row').forEach(row => row.remove());
            let previousGroup = '';
            visible.forEach(row => {{
              if (mode !== 'score') {{
                const group = mode === 'provider' ? row.querySelector('.provider-filter')?.textContent : row.querySelector('td:nth-child(2) strong')?.textContent;
                if (group && group !== previousGroup) {{
                const groupRow = document.createElement('tr');
                groupRow.className = 'catalog-group-row';
                const cell = document.createElement('th');
                cell.colSpan = 12;
                  cell.scope = 'rowgroup';
                  cell.textContent = group;
                  groupRow.appendChild(cell);
                  body.appendChild(groupRow);
                  previousGroup = group;
                }}
              }}
              body.appendChild(row);
            }});
            if (count) count.textContent = isEnglish() ? `Showing ${{visible.length}} / ${{rows.length}}` : `显示 ${{visible.length}} 条 / 共 ${{rows.length}} 条`;
            if (empty) empty.hidden = visible.length !== 0;
          }};
          search?.addEventListener('input', apply);
          provider?.addEventListener('change', apply);
          modes.forEach(button => button.addEventListener('click', () => {{
            mode = button.dataset.groupMode || 'score';
            modes.forEach(item => item.classList.toggle('is-active', item === button));
            apply();
          }}));
          localizeControls();
          document.querySelectorAll('.provider-filter').forEach(button => button.addEventListener('click', () => {{
            if (provider) provider.value = button.dataset.providerValue || '';
            apply();
            document.getElementById('model-directory')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
          }}));
          apply();
        }})();
      </script>
    </section>'''


def _provider_catalog_from_models(models: list[dict], operations: list[dict] | None = None) -> list[dict]:
    grouped: dict[str, dict] = {}
    for model in models:
        provider_id = str(model.get("providerId") or "").strip()
        if not provider_id:
            continue
        provider = grouped.setdefault(provider_id, {
            "id": provider_id,
            "name": str(model.get("provider") or provider_id),
            "modelCount": 0,
            "modelIds": [],
            "sourceKind": "catalog",
            "lastSeenAt": model.get("lastSeenAt") or "",
        })
        provider["modelCount"] += 1
        provider["modelIds"].append(model.get("id"))
        provider["lastSeenAt"] = max(provider["lastSeenAt"], str(model.get("lastSeenAt") or ""))
    for guide in operations or []:
        provider_id = str(guide.get("providerId") or "").strip()
        if provider_id and provider_id not in grouped:
            grouped[provider_id] = {
                "id": provider_id,
                "name": str(guide.get("provider") or provider_id),
                "modelCount": 0,
                "modelIds": [],
                "sourceKind": "operation",
                "lastSeenAt": str(guide.get("lastVerifiedAt") or ""),
            }
    return sorted(grouped.values(), key=lambda item: str(item.get("name") or "").lower())


def _latest_date(items: list[dict], field: str) -> str:
    dates = {str(item.get(field) or "") for item in items if item.get(field)}
    return max(dates) if dates else "—"


def _catalog_source_label(model: dict) -> str:
    return _locale_pair(
        "目录发现" if model.get("sourceKind") == "third_party_directory" else "本站核验",
        "Directory discovered" if model.get("sourceKind") == "third_party_directory" else "FreeLLM verified",
    )


def _catalog_record_table(models: list[dict]) -> str:
    if not models:
        return '<p class="muted">暂未同步模型目录记录；请查看下方详细操作指南。 / No catalog model records are synced yet; see the detailed operation guide below.</p>'
    rows = []
    for model in models:
        status = str(model.get("status") or "unknown").lower()
        status_label = _locale_pair(
            {"online": "在线", "offline": "离线", "degraded": "降级"}.get(status, "未知"),
            {"online": "Online", "offline": "Offline", "degraded": "Degraded"}.get(status, "Unknown"),
        )
        rows.append(f'''<tr>
          <td><a href="{_esc(provider_url(str(model.get("providerId") or "provider")))}">{_esc(model.get("provider"))}</a></td>
          <td class="model-cell"><strong class="model-name" title="{_esc(model.get("model"))}">{_esc(model.get("model"))}</strong><small class="model-id" title="{_esc(model.get("id"))}">{_esc(model.get("id"))}</small></td>
          <td><strong class="score">{_esc(model.get("score") if model.get("score") is not None else "—")}</strong></td>
          <td>{_esc(model.get("context") or "—")}</td>
          <td>{_esc(model.get("rateLimit") or "—")}</td>
          <td><span class="status status-{_esc(status)}">{status_label}</span><small>{_catalog_source_label(model)}</small></td>
          <td>{_esc(model.get("lastSeenAt") or "—")}</td>
          <td><a href="{_esc(model.get("sourceUrl") or "#")}" target="_blank" rel="noopener noreferrer">{_locale_pair("目录来源", "Catalog source")} ↗</a></td>
        </tr>''')
    return '''<div class="catalog-table-wrap"><table class="catalog-table"><thead><tr>
      <th>厂商 <span lang="en">Provider</span></th><th>模型 <span lang="en">Model</span></th><th>评分 <span lang="en">Score</span></th><th>上下文 <span lang="en">Context</span></th>
      <th>速率 <span lang="en">Rate limit</span></th><th>状态 <span lang="en">Status</span></th><th>同步 <span lang="en">Synced</span></th><th>来源 <span lang="en">Source</span></th>
    </tr></thead><tbody>''' + "".join(rows) + "</tbody></table></div>"


def _provider_offer_matches(provider: dict, offer: dict) -> bool:
    provider_name = str(provider.get("name") or "").lower()
    offer_text = " ".join(str(offer.get(field) or "").lower() for field in ("provider", "providerMeta", "providerMetaEn"))
    return bool(provider_name and provider_name in offer_text)


def _model_offer_matches(model_name: str, offer: dict) -> bool:
    needle = model_name.lower().strip()
    offer_text = " ".join(str(offer.get(field) or "").lower() for field in ("title", "titleZh", "model", "modelMeta", "modelMetaEn"))
    return bool(needle and (needle in offer_text or offer_text in needle))


def _related_offer_links(offers: list[dict], predicate) -> str:
    matches = [offer for offer in offers if predicate(offer)]
    if not matches:
        return '<p class="muted">暂未关联本站详细接入资源 / No detailed FreeLLM access record linked yet.</p>'
    return "<ul class=\"related-list\">" + "".join(
        f'<li><a href="{_esc(offer_url(offer))}">{_esc(offer.get("titleZh") or offer.get("title") or offer.get("provider"))}</a></li>'
        for offer in matches
    ) + "</ul>"


def _registration_requirements_markup(provider_card: dict | None, model_card: dict | None = None) -> str:
    if not isinstance(provider_card, dict):
        return ""
    labels = {
        "accountRequired": ("需要账号", "Account"), "emailRequired": ("需要邮箱", "Email"),
        "phoneRequired": ("需要手机号", "Phone"), "identityRequired": ("需要实名", "Identity"),
        "cardRequired": ("需要信用卡", "Card"), "billingRequired": ("需要开通计费", "Billing"),
        "apiKeyRequired": ("需要 API Key", "API key"), "licenseAcceptance": ("许可证", "License"),
    }
    facts = "".join(f'<div><dt>{_locale_pair(zh, en)}</dt><dd>{_esc(str(provider_card.get(key) or "unknown"))}</dd></div>' for key, (zh, en) in labels.items())
    steps = list(provider_card.get("registrationSteps") or [])
    extras = list((model_card or {}).get("extraRequirements") or [])
    if extras:
        steps.extend(extras)
    steps_markup = "".join(f"<li>{_esc(step)}</li>" for step in steps)
    register_url = provider_card.get("registerUrl")
    register_markup = f'<a class="btn" href="{_esc(register_url)}" target="_blank" rel="noopener noreferrer">{_locale_pair("打开注册入口", "Open signup")}</a>' if register_url else ""
    return f'''<section class="registration-requirements"><h2>{_locale_pair("注册要求与模型查找", "Registration and model lookup")}</h2>
      <dl class="facts">{facts}</dl>{f"<ol>{steps_markup}</ol>" if steps_markup else f'<p class="lead">{_locale_pair("注册步骤尚未核验。", "Registration steps are not yet verified.")}</p>'}{register_markup}</section>'''


def _access_routes_markup(records: list[dict]) -> str:
    routes = [record for record in records if record.get("accessEndpoint")]
    if not routes:
        return ""
    labels = {"domestic": ("国内入口", "Mainland route"), "international": ("国外入口", "International route")}
    cards = []
    for record in routes:
        region = str(record.get("accessRegion") or "unknown")
        zh, en = labels.get(region, ("地区待核验", "Region unverified"))
        cards.append(f'''<article class="access-route"><h3>{_locale_pair(zh, en)}</h3>
          <p><strong>{_esc(record.get("provider"))}</strong> · {_esc(record.get("id"))}</p>
          <p><span class="muted">{_locale_pair("Base URL", "Base URL")}:</span> <code>{_esc(record.get("accessEndpoint"))}</code></p>
          <p><span class="muted">{_locale_pair("模型 ID", "Model ID")}:</span> <code>{_esc(record.get("modelId") or record.get("id"))}</code></p>
          <p><a href="{_esc(record.get("sourceUrl") or "#")}" target="_blank" rel="noopener noreferrer">{_locale_pair("查看官方说明", "View official documentation")} ↗</a></p>
        </article>''')
    return f'''<section class="access-routes"><h2>{_locale_pair("国内 / 国外接入地址", "Domestic / international access routes")}</h2>
      <div class="access-route-grid">{"".join(cards)}</div></section>'''


def render_model_aggregate_page(model_name: str, records: list[dict], offers: list[dict], site_url: str, provider_access: dict[str, dict] | None = None, model_access: dict[str, dict] | None = None) -> str:
    path = model_aggregate_url(model_name)
    page_url = _absolute(site_url, path)
    title = f"{model_name} 多平台入口与限制 · {model_name} Model Providers | FreeLLM"
    description = f"比较 {model_name} 在不同厂商的评分、上下文、速率、状态和目录来源，并查看 FreeLLM 已整理的详细接入资源。"
    latest = _latest_date(records, "lastSeenAt")
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": page_url,
        "inLanguage": ["zh-CN", "en"],
        "dateModified": latest if latest != "—" else "2026-09-09",
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(records),
            "itemListElement": [
                {"@type": "ListItem", "position": index, "name": f'{record.get("provider")} · {model_name}', "url": record.get("sourceUrl")}
                for index, record in enumerate(records, start=1)
            ],
        },
    }
    provider_card = (provider_access or {}).get(str(records[0].get("providerId") or "")) if records else None
    registration_markup = "".join(
        _registration_requirements_markup(
            (provider_access or {}).get(str(record.get("providerId") or "")),
            (model_access or {}).get(str(record.get("id") or "")),
        )
        for record in records
        if str(record.get("providerId") or "")
    )
    routes_markup = _access_routes_markup(records)
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title><meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "article")}
  {_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ --ink:#172033; --muted:#68748a; --line:#dfe5ef; --soft:#f5f7fb; --blue:#1744e8; }}
    * {{ box-sizing:border-box; }} body {{ max-width:1180px; margin:0 auto; padding:24px 18px 64px; color:var(--ink); background:var(--soft); font-family:Inter,ui-sans-serif,system-ui,sans-serif; line-height:1.65; }}
    a {{ color:var(--blue); }} header,main,footer {{ background:#fff; border:1px solid var(--line); border-radius:16px; padding:clamp(20px,4vw,36px); margin-bottom:18px; }}
    h1 {{ margin:10px 0; font-size:clamp(28px,5vw,48px); line-height:1.1; }} h2 {{ margin:0 0 8px; }} .lead,.muted {{ color:var(--muted); }} .stats {{ display:flex; flex-wrap:wrap; gap:8px 20px; margin-top:18px; color:var(--muted); font-size:13px; }}
    .catalog-table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; }} .catalog-table {{ width:100%; min-width:900px; border-collapse:collapse; font-size:13px; }} .catalog-table th,.catalog-table td {{ padding:11px; text-align:left; vertical-align:top; border-bottom:1px solid var(--line); }} .catalog-table th {{ color:var(--muted); background:#f8fafc; font-size:11px; white-space:nowrap; }} .catalog-table small {{ display:block; color:var(--muted); font-size:11px; }} .catalog-table .model-name,.catalog-table .model-id {{ display:block; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }} .catalog-table .model-id {{ margin-top:3px; }} .score {{ color:var(--blue); }} .status {{ display:inline-block; border-radius:999px; padding:2px 7px; font-size:11px; }} .status-online {{ color:#147a46; background:#dcfce7; }} .status-offline {{ color:#9f1239; background:#ffe4e6; }} .status-degraded,.status-unknown {{ color:#8a5a00; background:#fef3c7; }} .related-list {{ padding-left:20px; }} .eyebrow {{ font:11px ui-monospace,Consolas,monospace; letter-spacing:.08em; text-transform:uppercase; }}
    .access-route-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }} .access-route {{ padding:14px; border:1px solid var(--line); border-radius:10px; background:#f8fafc; }} .access-route h3 {{ margin:0 0 8px; }} code {{ overflow-wrap:anywhere; }}
    @media (max-width:620px) {{ body {{ padding:10px 8px 38px; }} header,main,footer {{ padding:18px; border-radius:12px; }} }}
  </style>
</head>
<body data-static-locale="true">
  <header><p><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / <a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('全部模型', 'All models')}</a></p>
    {_static_locale_nav()}<div class="eyebrow">MODEL AGGREGATION</div><h1>{_esc(model_name)}</h1>
    <p class="lead">{_locale_pair(f'同一模型在 {len(records)} 个厂家或平台的目录记录。先比较限制，再进入对应的官方或本站详细入口。', f'{len(records)} provider or platform records for the same model. Compare limits first, then open the relevant official or FreeLLM access path.')}</p>
    <div class="stats"><span>{len(records)} {_locale_pair('个平台记录', 'platform records')}</span><span>{_locale_pair('最近同步', 'Last synced')}: {latest}</span><span>{_locale_pair('来源级别', 'Source level')}: {_locale_pair('目录发现', 'Directory discovered')}</span></div>
  </header>
  <main>{routes_markup}<section><h2>{_locale_pair('平台记录对比', 'Provider records')}</h2>{_catalog_record_table(records)}</section>
     {registration_markup}<section><h2>{_locale_pair('本站详细接入资源', 'Detailed FreeLLM access records')}</h2><p class="lead">{_locale_pair('这里才放注册、Endpoint、模型 ID、调用示例和验证步骤；没有关联记录时不会虚构操作。', 'Registration, endpoints, model IDs, examples and verification steps live here; no operation path is invented when no record is linked.')}</p>{_related_offer_links(offers, lambda offer: _model_offer_matches(model_name, offer))}</section>
  </main><footer><p><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('返回模型大列表', 'Back to model directory')}</a> · <a href="{_esc(_absolute(site_url, PROVIDERS_PAGE_PATH))}">{_locale_pair('按厂家浏览', 'Browse by provider')}</a></p></footer>
</body></html>'''


def render_providers_page(providers: list[dict], models: list[dict], site_url: str) -> str:
    path = PROVIDERS_PAGE_PATH
    page_url = _absolute(site_url, path)
    title = "按厂家浏览免费 AI 模型 · AI Providers Directory | FreeLLM"
    description = f"按厂家浏览 FreeLLM 收录的 {len(providers)} 家厂商与 {len(models)} 个模型，并进入每家厂商的模型记录。"
    cards = []
    for provider in providers:
        provider_models = [model for model in models if model.get("providerId") == provider.get("id")]
        latest = _latest_date(provider_models, "lastSeenAt")
        source_label = _locale_pair("操作指南", "Operation guide") if provider.get("sourceKind") == "operation" else _locale_pair("目录发现", "Directory discovered")
        cards.append(f'''<article class="provider-card"><div class="eyebrow">{_esc(provider.get("id"))}</div><h2><a href="{_esc(provider_url(provider))}">{_esc(provider.get("name"))}</a></h2><p>{len(provider_models)} {_locale_pair('个模型', 'models')} · {source_label}</p><p class="muted">{_locale_pair('最近同步', 'Last synced')}: {latest}</p><a class="button" href="{_esc(provider_url(provider))}">{_locale_pair('查看厂家模型', 'View provider models')} →</a></article>''')
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": description, "url": page_url, "inLanguage": ["zh-CN", "en"], "mainEntity": {"@type": "ItemList", "numberOfItems": len(providers), "itemListElement": [{"@type": "ListItem", "position": index, "name": provider.get("name"), "url": _absolute(site_url, provider_url(provider))} for index, provider in enumerate(providers, start=1)]}}
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "website")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>:root {{--ink:#172033;--muted:#68748a;--line:#dfe5ef;--soft:#f5f7fb;--blue:#1744e8;}}* {{box-sizing:border-box;}}body {{max-width:1180px;margin:0 auto;padding:24px 18px 64px;color:var(--ink);background:var(--soft);font-family:Inter,ui-sans-serif,system-ui,sans-serif;line-height:1.65;}}a {{color:var(--blue);}}header,main,footer {{background:#fff;border:1px solid var(--line);border-radius:16px;padding:clamp(20px,4vw,36px);margin-bottom:18px;}}h1 {{font-size:clamp(28px,5vw,48px);line-height:1.1;}}.lead,.muted {{color:var(--muted);}}.eyebrow {{font:11px ui-monospace,Consolas,monospace;letter-spacing:.08em;text-transform:uppercase;}}.provider-grid {{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;}}.provider-card {{display:flex;flex-direction:column;min-height:220px;padding:18px;border:1px solid var(--line);border-radius:12px;background:#fff;}}.provider-card h2 {{margin:8px 0 4px;font-size:20px;}}.provider-card p {{margin:5px 0;}}.button {{margin-top:auto;display:inline-block;width:max-content;padding:8px 12px;border-radius:8px;background:var(--blue);color:#fff;text-decoration:none;font-size:13px;}}@media (max-width:620px) {{body {{padding:10px 8px 38px;}}header,main,footer {{padding:18px;border-radius:12px;}}}}</style></head>
<body data-static-locale="true"><header><p><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / {_locale_pair('按厂家浏览', 'Browse by provider')}</p>{_static_locale_nav()}<h1>{_locale_pair('按厂家浏览模型', 'Browse models by provider')}</h1><p class="lead">{_locale_pair(description, f'Explore {len(providers)} AI providers and {len(models)} catalog models.')}</p><p><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('返回模型大列表', 'Back to model directory')} →</a></p></header><main><div class="provider-grid">{"".join(cards)}</div></main><footer><p>{_locale_pair('目录数据来自第三方模型目录，具体免费条件和操作步骤进入本站详细资源页核对。', 'Catalog rows come from a third-party model directory; verify free terms and operation steps on detailed FreeLLM records.')}</p></footer></body></html>'''


def render_provider_page(provider: dict, models: list[dict], offers: list[dict], site_url: str, operations: list[dict] | None = None, provider_access: dict[str, dict] | None = None, model_access: dict[str, dict] | None = None) -> str:
    provider_models = [model for model in models if model.get("providerId") == provider.get("id")]
    path = provider_url(provider)
    page_url = _absolute(site_url, path)
    name = str(provider.get("name") or provider.get("id") or "Provider")
    title = f"{name} 模型与免费入口 · {name} Models & Access | FreeLLM"
    description = f"浏览 {name} 的 {len(provider_models)} 个模型记录，比较评分、上下文、限流、状态和来源，并查看已整理的免费入口。"
    related = _related_offer_links(offers, lambda offer: _provider_offer_matches(provider, offer))
    operation_guides_markup = _operation_guides_markup(_operation_guides_for_provider(str(provider.get("id") or ""), operations or []))
    routes_markup = _access_routes_markup(provider_models)
    registration_markup = routes_markup + _registration_requirements_markup((provider_access or {}).get(str(provider.get("id") or "")))
    source_label = _locale_pair("操作指南", "Operation guide") if provider.get("sourceKind") == "operation" else _locale_pair("目录发现", "Directory discovered")
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": description, "url": page_url, "inLanguage": ["zh-CN", "en"], "dateModified": _latest_date(provider_models, "lastSeenAt"), "mainEntity": {"@type": "ItemList", "numberOfItems": len(provider_models), "itemListElement": [{"@type": "ListItem", "position": index, "name": f'{name} · {model.get("model")}', "url": _absolute(site_url, model_aggregate_url(model))} for index, model in enumerate(provider_models, start=1)]}}
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "article")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>:root {{--ink:#172033;--muted:#68748a;--line:#dfe5ef;--soft:#f5f7fb;--blue:#1744e8;}}* {{box-sizing:border-box;}}body {{max-width:1180px;margin:0 auto;padding:24px 18px 64px;color:var(--ink);background:var(--soft);font-family:Inter,ui-sans-serif,system-ui,sans-serif;line-height:1.65;}}a {{color:var(--blue);}}header,main,footer {{background:#fff;border:1px solid var(--line);border-radius:16px;padding:clamp(20px,4vw,36px);margin-bottom:18px;}}h1 {{font-size:clamp(28px,5vw,48px);line-height:1.1;}}.lead,.muted {{color:var(--muted);}}.catalog-table-wrap {{overflow-x:auto;border:1px solid var(--line);border-radius:12px;}}.catalog-table {{width:100%;min-width:900px;border-collapse:collapse;font-size:13px;}}.catalog-table th,.catalog-table td {{padding:11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);}}.catalog-table th {{color:var(--muted);background:#f8fafc;font-size:11px;white-space:nowrap;}}.catalog-table small {{display:block;color:var(--muted);font-size:11px;}}.catalog-table .model-name,.catalog-table .model-id {{display:block;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}.catalog-table .model-id {{margin-top:3px;}}.score {{color:var(--blue);}}.status {{display:inline-block;border-radius:999px;padding:2px 7px;font-size:11px;}}.status-online {{color:#147a46;background:#dcfce7;}}.status-offline {{color:#9f1239;background:#ffe4e6;}}.status-degraded,.status-unknown {{color:#8a5a00;background:#fef3c7;}}.related-list {{padding-left:20px;}}.stats {{display:flex;flex-wrap:wrap;gap:8px 20px;color:var(--muted);font-size:13px;}}.eyebrow {{font:11px ui-monospace,Consolas,monospace;letter-spacing:.08em;text-transform:uppercase;}}@media (max-width:620px) {{body {{padding:10px 8px 38px;}}header,main,footer {{padding:18px;border-radius:12px;}}}}</style></head>
<body data-static-locale="true"><header><p><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / <a href="{_esc(_absolute(site_url, PROVIDERS_PAGE_PATH))}">{_locale_pair('按厂家浏览', 'Browse by provider')}</a></p>{_static_locale_nav()}<div class="eyebrow">PROVIDER DIRECTORY</div><h1>{_esc(name)}</h1><p class="lead">{_locale_pair(description, f'Browse {len(provider_models)} model records for {name}.')}</p><div class="stats"><span>{len(provider_models)} {_locale_pair('个模型', 'models')}</span><span>{_locale_pair('最近同步', 'Last synced')}: {_latest_date(provider_models, 'lastSeenAt')}</span><span>{_locale_pair('来源级别', 'Source level')}: {source_label}</span></div></header><main>{registration_markup}<section><h2>{_locale_pair('全部模型记录', 'All model records')}</h2>{_catalog_record_table(provider_models)}</section><section><h2>{_locale_pair('本站详细接入资源', 'Detailed FreeLLM access records')}</h2>{related}</section>{operation_guides_markup}</main><footer><p><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('返回模型大列表', 'Back to model directory')}</a> · <a href="{_esc(_absolute(site_url, PROVIDERS_PAGE_PATH))}">{_locale_pair('返回厂家目录', 'Back to providers')}</a></p></footer></body></html>'''


def render_models_page(offers: list[dict], site_url: str, models: list[dict] | None = None) -> str:
    """Bilingual (Chinese / English) directory of every verified offer with a
    registration CTA, so one shareable URL serves both language communities."""
    path = ALL_MODELS_PAGE_PATH if models is not None else MODELS_PAGE_PATH
    page_url = _absolute(site_url, path)
    total = len(offers)
    model_catalog = models or []
    model_total = len(model_catalog)
    provider_access_count = len(_load_access_context()[0]) if models is not None else 0
    if models is None:
        title = "免费 AI 资源目录：模型、API 与 IDE · Free AI Resources Directory | FreeLLM"
        description = (
            f"按免费额度、API、IDE、试用和开源权重浏览 FreeLLM 的 {total} 条可核验资源，"
            "进入每条资源页查看官方入口、限制和操作步骤。 Browse verified free AI models, APIs, IDEs and open-weight resources."
        )
    else:
        title = "全部免费 AI 模型与 API 一览（含中国大陆可用性标注）· All Free AI Models with Mainland CN Availability | FreeLLM"
        description = (
            f"FreeLLM 收录的 {model_total or total} 个模型与 {total} 个免费访问资源，逐行标注中国大陆可用性，"
            f"附 {provider_access_count} 家提供商注册要求（手机号、实名、信用卡）与官方来源。"
            f" Browse {model_total or total} catalog models and {total} verified free access records with per-row "
            f"mainland-China availability labels and per-provider signup requirements (phone, identity, credit card)."
        )
    social_meta = _social_meta(site_url, path, title, description, "website")
    checked_dates = {
        offer.get("lastVerifiedAt") for offer in offers if offer.get("lastVerifiedAt")
    }
    checked_dates.update(
        model.get("lastSeenAt") for model in model_catalog if model.get("lastSeenAt")
    )
    last_checked = max(checked_dates) if checked_dates else "2026-09-08"
    model_dates = {
        model.get("lastSeenAt") for model in model_catalog if model.get("lastSeenAt")
    }
    model_last_seen = max(model_dates) if model_dates else "—"
    offer_dates = {
        offer.get("lastVerifiedAt") for offer in offers if offer.get("lastVerifiedAt")
    }
    offer_last_checked = max(offer_dates) if offer_dates else "—"
    sections_markup = ""
    for definition, matching in _models_page_sections(offers):
        name_zh, name_en, description_zh, description_en = definition
        cards = "".join(_model_card(offer) for offer in matching)
        sections_markup += f'''<section>
      <h2>{_locale_pair(name_zh, name_en)} <small>{len(matching)}</small></h2>
      <p class="section-desc">{_locale_pair(description_zh, description_en)}</p>
      <div class="card-grid">{cards}</div>
    </section>'''
    schema_items = model_catalog if model_catalog else offers
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": page_url,
        "inLanguage": ["zh-CN", "en"],
        "keywords": "免费 AI 模型, 中国大陆可用, 大陆可用性标注, 注册要求, 手机号验证, 信用卡, 免费 LLM API, free AI models, mainland China availability, signup requirements",
        "dateModified": last_checked,
        "isPartOf": {"@type": "WebSite", "name": "Free AI Index", "url": _absolute(site_url, "/")},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(schema_items),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": (
                        f'{item.get("provider")} · {item.get("model")}'
                        if model_catalog
                        else item.get("title") or item.get("name")
                    ),
                    "url": (
                        item.get("sourceUrl")
                        if model_catalog
                        else _absolute(site_url, offer_url(item))
                    ),
                }
                for index, item in enumerate(schema_items, start=1)
            ],
        },
    }
    category_links = "".join(
        f'<a class="tag" href="{_esc(category_url(category))}">{_locale_pair(CATEGORY_DEFINITIONS[category]["name_zh"], CATEGORY_DEFINITIONS[category]["name"])}</a>'
        for category in CATEGORY_DEFINITIONS
    )
    cn_section = f'''<section id="mainland-cn-availability">
      <h2>{_locale_pair("中国大陆可用性与注册要求", "Mainland China availability and signup requirements")}</h2>
      <p class="section-desc">{_locale_pair(
        f"目录逐行标注每个模型在中国大陆的可用状态（可用 / 不可用 / 待核验），背后是 {provider_access_count} 家提供商的注册要求核验卡：是否需要手机号、实名认证或信用卡，全部以官方来源为准。没有官方证据的一律标为“待核验”，不会因为证据缺失而被判为不可用。以下要点已完成人工核验：",
        "Every catalog row carries a mainland-China availability label (available / unavailable / unverified), backed by per-provider registration cards covering phone, identity and credit-card requirements — all evidence-linked. Anything without official evidence stays “unverified” and is never marked unavailable for lack of evidence. Key verified facts:")}</p>
      <ul>
        <li>{_locale_pair("SiliconFlow：手机号 + 短信验证码注册，实名认证仅用于提升额度", "SiliconFlow: phone + SMS signup; identity verification only raises quotas")}</li>
        <li>{_locale_pair("ModelScope：手机号、邮箱、阿里云账号或 GitHub 任一即可注册", "ModelScope: register with any one of phone, email, Alibaba Cloud or GitHub")}</li>
        <li>{_locale_pair("Mistral：免费 Experiment 层需短信验证，无需信用卡", "Mistral: free Experiment tier needs SMS verification, no credit card")}</li>
        <li>{_locale_pair("OpenRouter、Groq、Cohere、Cloudflare Workers AI、NVIDIA NIM：免费层均无需信用卡", "OpenRouter, Groq, Cohere, Cloudflare Workers AI and NVIDIA NIM: no credit card on free tiers")}</li>
        <li>{_locale_pair("Hugging Face：需邮箱验证后才能创建访问令牌", "Hugging Face: email verification is required before creating access tokens")}</li>
        <li>{_locale_pair("Agnes AI：仅邮箱注册，并提供中国大陆 API 加速节点", "Agnes AI: email-only signup with a dedicated mainland-CN API endpoint")}</li>
        <li>{_locale_pair("llm7.io：可匿名调用，也可免费领取 token 提升限额", "llm7.io: anonymous access works, or claim a free token for higher limits")}</li>
        <li>{_locale_pair("Chutes.ai：免费层已于 2026 年 2 月退役，需订阅或按量付费", "Chutes.ai: free tier retired in February 2026; subscription or pay-as-you-go required")}</li>
        <li>{_locale_pair("GitHub Models：已于 2026-07-30 完全退役，替代方案为 Azure AI Foundry 与 GitHub Copilot", "GitHub Models: fully retired on July 30, 2026; use Azure AI Foundry or GitHub Copilot instead")}</li>
      </ul>
      <p><a href="{_esc(_absolute(site_url, PROVIDERS_PAGE_PATH))}">{_locale_pair("按厂家查看注册要求 →", "Browse signup requirements by provider →")}</a> · <a href="{_esc(_absolute(site_url, "/guides/china-free-ai-api/"))}">{_locale_pair("国内免费 AI API 指南 →", "Free AI APIs in China guide →")}</a></p>
    </section>'''
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}">
  <link rel="canonical" href="{_esc(page_url)}">
  {_hreflang_links(site_url, path)}
  {social_meta}
  {_analytics_script()}
  {ADSENSE_SCRIPT}
  {STATIC_LOCALE_STYLE}
  {STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #68748a; --line: #dfe5ef; --soft: #f5f7fb; --blue: #1744e8; --green: #e6f7ee; }}
    * {{ box-sizing: border-box; }}
    body {{ max-width: 1180px; margin: 0 auto; padding: 24px 18px 64px; line-height: 1.65; color: var(--ink); background: var(--soft); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    a {{ color: var(--blue); }}
    header, main, footer {{ background: white; border: 1px solid var(--line); border-radius: 16px; padding: clamp(20px, 4vw, 36px); margin-bottom: 18px; }}
    header {{ color: white; background: linear-gradient(135deg, #172033, #243f78); border-color: #172033; }}
    header a {{ color: white; }}
    h1 {{ max-width: 860px; margin: 22px 0 10px; font-size: clamp(32px, 5.5vw, 56px); line-height: 1.08; letter-spacing: -.05em; }}
    h2 {{ margin: 0 0 6px; font-size: clamp(23px, 3.5vw, 30px); letter-spacing: -.03em; }}
    h2 small {{ color: var(--muted); font-size: 15px; font-weight: 400; }}
    h2 [lang="en"] {{ color: #9db4d8; font-weight: 500; font-size: .62em; margin-left: 6px; }}
    p {{ max-width: 880px; }}
    .crumb, .eyebrow {{ font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }}
    .lead {{ max-width: 840px; color: #dbe6ff; font-size: 17px; }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 10px 22px; margin: 18px 0 0; padding-top: 16px; border-top: 1px solid rgba(255,255,255,.22); font-size: 13px; color: #dbe6ff; }}
    .callout {{ margin: 22px 0 0; padding: 16px 18px; border-left: 4px solid #79e5a3; background: rgba(255,255,255,.1); font-size: 14px; }}
    main {{ display: grid; gap: 30px; }}
    section + section {{ padding-top: 26px; border-top: 1px solid var(--line); }}
    .section-desc {{ margin: 0 0 14px; color: var(--muted); font-size: 14px; }}
    .catalog-toolbar {{ display: grid; grid-template-columns: minmax(220px, 1.5fr) minmax(150px, .8fr) minmax(140px, .75fr) auto 1fr; gap: 10px; align-items: end; margin: 18px 0 14px; padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: var(--soft); }}
    .catalog-toolbar label {{ color: var(--muted); font-size: 11px; font-weight: 700; }}
    .catalog-search-label, .catalog-provider-label, .catalog-region-label {{ display: grid; gap: 5px; }}
    .catalog-toolbar input, .catalog-toolbar select {{ min-height: 38px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; color: var(--ink); background: white; font: inherit; }}
    .catalog-modes {{ display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }}
    .group-mode, .provider-filter {{ border: 0; border-radius: 7px; padding: 7px 9px; color: var(--blue); background: transparent; cursor: pointer; font: inherit; }}
    .group-mode {{ border: 1px solid var(--line); font-size: 12px; white-space: nowrap; }}
    .group-mode.is-active {{ color: white; background: var(--blue); border-color: var(--blue); }}
    .provider-filter {{ padding: 0; color: var(--blue); text-align: left; font-size: 13px; font-weight: 600; }}
    .provider-filter:hover {{ text-decoration: underline; }}
    .provider-page-link {{ display: block; margin-top: 3px; color: var(--muted); font-size: 11px; }}
    .catalog-count {{ align-self: center; justify-self: end; color: var(--muted); font: 12px ui-monospace, SFMono-Regular, Consolas, monospace; white-space: nowrap; }}
    .catalog-table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; }}
    .catalog-table {{ width: 100%; min-width: 1120px; border-collapse: collapse; font-size: 12.5px; }}
    .catalog-table th, .catalog-table td {{ padding: 10px 11px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
    .catalog-table thead th {{ position: sticky; top: 0; z-index: 1; color: var(--muted); background: #f8fafc; font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; white-space: nowrap; }}
    .catalog-table tbody tr:last-child td {{ border-bottom: 0; }}
    .catalog-table small {{ display: block; margin-top: 3px; color: var(--muted); font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .catalog-table .model-name, .catalog-table .model-id {{ display: block; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .catalog-table .model-id {{ margin-top: 3px; }}
    .score-ring {{ display: inline-grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; background: conic-gradient(from -90deg, #3b82f6 0%, #7c3aed calc(var(--score) * .65%), #ec4899 calc(var(--score) * 1%), #e4eaf5 0); position: relative; color: var(--ink); }}
    .score-ring::after {{ content: ""; position: absolute; inset: 4px; border-radius: 50%; background: white; }}
    .score-ring strong {{ position: relative; z-index: 1; color: var(--blue); font-size: 12px; }}
    .model-badges {{ display: flex; flex-wrap: wrap; gap: 4px; min-width: 80px; }}
    .model-badge {{ border-radius: 999px; padding: 2px 6px; color: #2457b7; background: #e9efff; font-size: 11px; white-space: nowrap; }}
    .status {{ display: inline-block; border-radius: 999px; padding: 3px 7px; font-size: 11px; white-space: nowrap; }}
    .status-online {{ color: #147a46; background: #dcfce7; }}
    .status-offline {{ color: #9f1239; background: #ffe4e6; }}
    .status-degraded, .status-unknown {{ color: #8a5a00; background: #fef3c7; }}
    .catalog-group-row th {{ padding: 13px 11px 7px; color: var(--ink); background: #eef4ff; font-size: 13px; }}
    .catalog-empty {{ margin: 16px 0 0; padding: 14px; border-radius: 8px; color: #8a5a00; background: #fef3c7; }}
    .catalog-hint {{ margin: 0 0 12px; color: var(--muted); font-size: 12px; }}
    .source-cell {{ min-width: 100px; white-space: nowrap; }}
    .freshness {{ color: var(--muted); }}
    .freshness-stale {{ color: #b42318; }}
    .card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); gap: 14px; }}
    .model-card {{ display: flex; flex-direction: column; gap: 10px; border: 1px solid var(--line); border-radius: 12px; padding: 16px; background: white; }}
    .card-head {{ display: flex; gap: 10px; align-items: flex-start; }}
    .mark {{ flex: 0 0 auto; display: inline-flex; width: 34px; height: 34px; border-radius: 9px; background: #e9efff; color: var(--blue); align-items: center; justify-content: center; font-size: 13px; font-weight: 700; }}
    .card-head h3 {{ margin: 0; font-size: 16px; line-height: 1.35; }}
    .card-head a {{ color: var(--ink); text-decoration: none; }}
    .card-head a:hover {{ color: var(--blue); }}
    .provider {{ margin: 2px 0 0; color: var(--muted); font-size: 12.5px; }}
    .model {{ margin: 0; color: #3d4b63; font-size: 13px; }}
    .facts {{ margin: 0; display: grid; gap: 6px; }}
    .facts div {{ display: grid; grid-template-columns: 112px 1fr; gap: 8px; font-size: 12.5px; }}
    .facts dt {{ color: var(--muted); }}
    .facts dd {{ margin: 0; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{ border: 1px solid var(--line); border-radius: 999px; padding: 2px 9px; font-size: 11.5px; color: #3d4b63; background: var(--soft); }}
    .actions {{ margin-top: auto; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding-top: 4px; }}
    .btn {{ display: inline-block; background: var(--blue); color: white; border-radius: 9px; padding: 8px 14px; text-decoration: none; font-size: 13.5px; font-weight: 600; }}
    .btn:hover {{ background: #0f34c4; }}
    .ghost {{ font-size: 13px; color: var(--muted); }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .tag {{ display: inline-block; padding: 3px 10px; border-radius: 999px; background: #e9efff; text-decoration: none; font-size: 12.5px; }}
    footer {{ color: var(--muted); font-size: 13px; }}
    footer strong {{ color: var(--ink); }}
    @media (max-width: 820px) {{ .catalog-toolbar {{ grid-template-columns: 1fr 1fr; }} .catalog-modes {{ grid-column: 1 / -1; }} .catalog-count {{ justify-self: start; }} }}
    @media (max-width: 620px) {{ body {{ padding: 10px 8px 38px; }} header, main, footer {{ border-radius: 12px; padding: 18px; }} .facts div {{ grid-template-columns: 96px 1fr; }} .catalog-toolbar {{ grid-template-columns: 1fr; }} .catalog-modes {{ grid-column: auto; }} }}
  </style>
</head>
<body data-static-locale="true">
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / {_locale_pair('全部模型', 'All models')}</div>
    {_static_locale_nav()}
    <h1>{_locale_pair('全部免费 AI 模型与 API 一览', 'All Free AI Models & APIs')}</h1>
    <p class="lead">{_locale_pair(f'FreeLLM 收录的每一个免费 AI 模型、API、IDE 和工具都在这一页：模型目录逐行标注中国大陆可用性，接入资源直达官方，注册要求（手机号、实名、信用卡）与免费条件逐条标注。', 'Every catalog model, API and tool on FreeLLM — model rows carry mainland-China availability labels, access records link to official sites, and signup requirements (phone, identity, credit card) plus free-tier terms are listed row by row.')}</p>
    <div class="stats">
      <span><strong>{model_total or total}</strong> {_locale_pair('个模型', 'models')}</span>
      <span><strong>{total}</strong> {_locale_pair('个接入资源', 'access records')}</span>
      <span>{_locale_pair('每周人工核验', 'Verified weekly')}</span>
      <span>{_locale_pair('模型同步', 'Models synced')}: {model_last_seen}</span>
      <span>{_locale_pair('资源核验', 'Offers checked')}: {offer_last_checked}</span>
      <span>{_locale_pair('最近更新', 'Latest update')}: {last_checked}</span>
      <span>{_locale_pair('接入资源注册链接指向官方', 'Access-record links point to official sites')}</span>
    </div>
    <div class="callout">{_locale_pair('免费额度受地区、账户类型、速率限制和有效期约束，注册前请以官方页面为准。', 'Free access is always subject to region, account type, rate limits and expiry — verify the official page before signing up.')}</div>
  </header>
  <main>{_model_catalog_markup(model_catalog)}{cn_section}{sections_markup}
    <section>
      <h2>{_locale_pair('按分类浏览', 'Browse by category')}</h2>
      <p class="section-desc">{_locale_pair('每个分类有独立页面，收录同一资源的深度信息。', 'Each category has its own page with the full verified records.')}</p>
      <div class="tags">{category_links}</div>
    </section>
  </main>
  <footer>
    <p><strong>{_locale_pair('免责声明', 'Disclaimer')}：</strong>{_locale_pair('免费访问可能受地区、账户类型、速率限制、有效期或提供商条款影响。依赖任何资源前请核对官方来源。', 'Free access may be affected by region, account type, rate limits, validity or provider terms; always verify official sources before relying on an offer.')}</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair('返回 FreeLLM 免费 AI 资源索引 →', 'Return to FreeLLM Free AI Index →')}</a> · <a href="{_esc(_absolute(site_url, guide_url()))}">{_locale_pair('免费 LLM 接入指南', 'Free LLM guide')}</a></p>
  </footer>
</body>
</html>
'''


MODEL_CENTER_STYLE = '''<style id="model-center-style">
  .model-center-page { margin: 0; min-height: 100vh; background: #eef4ff; }
  .model-center-page[data-model-center-locale="en"] [lang="zh-CN"], .model-center-page[data-model-center-locale="zh-CN"] [lang="en"] { display: none !important; }
  .model-center-tabs { display: flex; justify-content: flex-start; gap: 8px; margin: 22px 0 26px; padding: 10px 0; border-bottom: 1px solid #dbe4f3; }
  .model-center-tab { border: 1px solid #cbd8ef; border-radius: 999px; padding: 8px 18px; color: #31456d; background: #fff; cursor: pointer; font: 700 13px/1.2 Inter, ui-sans-serif, system-ui, sans-serif; }
  .model-center-tab[aria-selected="true"] { border-color: #1744e8; color: #fff; background: #1744e8; }
  .model-center-tab small { margin-left: 5px; opacity: .75; font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; }
  .model-center-page[data-model-center-tab="all-models"] #categories, .model-center-page[data-model-center-tab="all-models"] #categories ~ * { display: none !important; }
  .model-center-page[data-model-center-tab="all-models"] .model-center-all-models-panel { display: block; }
  .model-center-page:not([data-model-center-tab="all-models"]) .model-center-all-models-panel { display: none; }
  .model-center-all-models-panel { max-width: 1240px; margin: 0 auto; padding: 28px 18px 64px; color: #172033; font-family: Inter, ui-sans-serif, system-ui, sans-serif; line-height: 1.65; }
  .model-center-all-models-panel .model-center-eyebrow { font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }
  .model-center-all-models-panel .model-directory { padding: clamp(20px, 4vw, 36px); border: 1px solid #dfe5ef; border-radius: 16px; background: #fff; }
  .model-center-all-models-panel .model-directory h2 { margin: 0 0 6px; font-size: clamp(23px, 3.5vw, 30px); letter-spacing: -.03em; }
  .model-center-all-models-panel .model-directory h2 small { color: #68748a; font-size: 15px; font-weight: 400; }
  .model-center-all-models-panel .section-desc { margin: 0 0 14px; color: #68748a; font-size: 14px; }
  .model-center-all-models-panel .catalog-toolbar { display: grid; grid-template-columns: minmax(220px, 1.5fr) minmax(150px, .8fr) minmax(140px, .75fr) auto 1fr; gap: 10px; align-items: end; margin: 18px 0 14px; padding: 14px; border: 1px solid #dfe5ef; border-radius: 12px; background: #f5f7fb; }
  .model-center-all-models-panel .catalog-toolbar label { color: #68748a; font-size: 11px; font-weight: 700; }
  .model-center-all-models-panel .catalog-search-label, .model-center-all-models-panel .catalog-provider-label, .model-center-all-models-panel .catalog-region-label { display: grid; gap: 5px; }
  .model-center-all-models-panel .catalog-toolbar input, .model-center-all-models-panel .catalog-toolbar select { min-height: 38px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; color: #172033; background: #fff; font: inherit; }
  .model-center-all-models-panel .catalog-modes { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
  .model-center-all-models-panel .group-mode { border: 1px solid #dfe5ef; border-radius: 7px; padding: 7px 9px; color: #1744e8; background: transparent; cursor: pointer; font: inherit; font-size: 12px; white-space: nowrap; }
  .model-center-all-models-panel .group-mode.is-active { color: #fff; background: #1744e8; border-color: #1744e8; }
  .model-center-all-models-panel .provider-filter { border: 0; padding: 0; color: #1744e8; background: transparent; cursor: pointer; text-align: left; font: inherit; font-size: 13px; font-weight: 700; }
  .model-center-all-models-panel .provider-filter:hover { text-decoration: underline; }
  .model-center-all-models-panel .provider-page-link { display: block; margin-top: 3px; color: #68748a; font-size: 11px; }
  .model-center-all-models-panel .catalog-count { align-self: center; justify-self: end; color: #68748a; font: 12px ui-monospace, SFMono-Regular, Consolas, monospace; white-space: nowrap; }
  .model-center-all-models-panel .catalog-hint { margin: 0 0 12px; color: #68748a; font-size: 12px; }
  .model-center-all-models-panel .catalog-table-wrap { overflow-x: auto; border: 1px solid #dfe5ef; border-radius: 12px; }
  .model-center-all-models-panel .catalog-table { width: 100%; min-width: 1120px; border-collapse: collapse; font-size: 12.5px; }
  .model-center-all-models-panel .catalog-table th, .model-center-all-models-panel .catalog-table td { padding: 10px 11px; text-align: left; vertical-align: top; border-bottom: 1px solid #dfe5ef; }
  .model-center-all-models-panel .catalog-table thead th { position: sticky; top: 0; z-index: 1; color: #68748a; background: #f8fafc; font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; white-space: nowrap; }
  .model-center-all-models-panel .catalog-table small { display: block; margin-top: 3px; color: #68748a; font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; }
  .model-center-all-models-panel .catalog-table .model-name, .model-center-all-models-panel .catalog-table .model-id { display: block; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .model-center-all-models-panel .catalog-table .model-id { margin-top: 3px; }
  .model-center-all-models-panel .score-ring { display: inline-grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; background: conic-gradient(from -90deg, #3b82f6 0%, #7c3aed calc(var(--score) * .65%), #ec4899 calc(var(--score) * 1%), #e4eaf5 0); position: relative; color: #172033; }
  .model-center-all-models-panel .score-ring::after { content: ""; position: absolute; inset: 4px; border-radius: 50%; background: #fff; }
  .model-center-all-models-panel .score-ring strong { position: relative; z-index: 1; color: #1744e8; font-size: 12px; }
  .model-center-all-models-panel .model-badges { display: flex; flex-wrap: wrap; gap: 4px; min-width: 80px; }
  .model-center-all-models-panel .model-badge { border-radius: 999px; padding: 2px 6px; color: #2457b7; background: #e9efff; font-size: 11px; white-space: nowrap; }
  .model-center-all-models-panel .status { display: inline-block; border-radius: 999px; padding: 3px 7px; font-size: 11px; white-space: nowrap; }
  .model-center-all-models-panel .status-online { color: #147a46; background: #dcfce7; }
  .model-center-all-models-panel .status-offline { color: #9f1239; background: #ffe4e6; }
  .model-center-all-models-panel .status-degraded, .model-center-all-models-panel .status-unknown { color: #8a5a00; background: #fef3c7; }
  .model-center-all-models-panel .catalog-group-row th { padding: 13px 11px 7px; color: #172033; background: #eef4ff; font-size: 13px; }
  .model-center-all-models-panel .catalog-empty { margin: 16px 0 0; padding: 14px; border-radius: 8px; color: #8a5a00; background: #fef3c7; }
  .model-center-all-models-panel .source-cell { min-width: 100px; white-space: nowrap; }
  .model-center-all-models-panel .freshness { color: #68748a; }
  .model-center-all-models-panel .freshness-stale { color: #b42318; }
  @media (max-width: 820px) { .model-center-all-models-panel .catalog-toolbar { grid-template-columns: 1fr 1fr; } .model-center-all-models-panel .catalog-modes { grid-column: 1 / -1; } .model-center-all-models-panel .catalog-count { justify-self: start; } }
  @media (max-width: 620px) { .model-center-tabs { justify-content: stretch; } .model-center-tab { flex: 1; padding: 8px 10px; } .model-center-all-models-panel { padding: 14px 8px 38px; } .model-center-all-models-panel .model-directory { border-radius: 12px; padding: 18px; } .model-center-all-models-panel .catalog-toolbar { grid-template-columns: 1fr; } .model-center-all-models-panel .catalog-modes { grid-column: auto; } }
</style>'''


def render_model_center_page(offers: list[dict], site_url: str, models: list[dict]) -> str:
    template_path = Path(__file__).resolve().parents[1] / "design" / "free-china-ai-index.html"
    template = template_path.read_text(encoding="utf-8")
    body_start = template.index("<body>")
    body_end = template.rindex("</body>")
    head = template[:body_start]
    body = template[body_start + len("<body>"):body_end]
    title = "模型中心 · 精选资源与全部模型 | FreeLLM"
    description = "FreeLLM 模型中心：先浏览人工核验的特色免费 AI 资源，再切换到完整模型目录，逐行查看中国大陆可用性标注、注册要求（手机号、实名、信用卡）、厂家、评分、上下文、活动和官方来源。"
    page_url = _absolute(site_url, MODEL_CENTER_PAGE_PATH)
    head = re.sub(r"<title>.*?</title>", f"<title>{_esc(title)}</title>", head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{_esc(description)}" />', head, count=1)
    head = re.sub(r'<link rel="canonical"[^>]*>', f'<link rel="canonical" href="{_esc(page_url)}" />', head, count=1)
    head = re.sub(r'(?:\s*<link rel="alternate"[^>]+>){3}', f'\n  {_hreflang_links(site_url, MODEL_CENTER_PAGE_PATH)}', head, count=1, flags=re.S)
    head = re.sub(r'(<meta property="og:url" content=")[^"]*("[^>]*>)', rf'\g<1>{_esc(page_url)}\g<2>', head, count=1)
    head = head.replace('<html lang="zh-CN">', '<html lang="zh-CN" data-default-locale="zh-CN">', 1)
    head = head.replace("</head>", f'{MODEL_CENTER_STYLE}\n</head>', 1)
    body = body.replace('class="catalog-app"', 'class="catalog-app model-center-featured-app"', 1)
    body = body.replace('href="/models/all/"', 'href="#all-models"')
    catalog_markup = _model_catalog_markup(models, include_heading=False)
    tab_markup = f'''<nav class="model-center-tabs" role="tablist" aria-label="模型中心页面切换">
  <button id="model-center-tab-featured" class="model-center-tab" type="button" role="tab" aria-controls="categories" aria-selected="true" data-center-tab="featured">{_locale_pair('精选资源', 'Featured resources')} <small>01</small></button>
  <button id="model-center-tab-all-models" class="model-center-tab" type="button" role="tab" aria-controls="model-center-all-models-panel" aria-selected="false" data-center-tab="all-models">{_locale_pair('全部模型', 'All models')} <small>{len(models)}</small></button>
</nav>'''
    tab_script = '''<script id="model-center-tabs-script">
  (() => {
    const root = document.body;
    const tabs = Array.from(document.querySelectorAll('[data-center-tab]'));
    const syncLocale = () => {
      const english = document.documentElement.lang !== 'zh-CN';
      root.dataset.modelCenterLocale = english ? 'en' : 'zh-CN';
      const search = document.getElementById('model-catalog-search');
      const provider = document.getElementById('model-catalog-provider');
      const region = document.getElementById('model-catalog-region');
      const count = document.getElementById('model-catalog-count');
      if (search) search.placeholder = english ? search.dataset.placeholderEn : search.dataset.placeholderZh;
      const allProviders = provider?.querySelector('option[value=""]');
      if (allProviders) allProviders.textContent = english ? allProviders.dataset.labelEn : allProviders.dataset.labelZh;
      document.querySelectorAll('#model-catalog-region option[data-label-zh]').forEach(option => {{
        option.textContent = english ? option.dataset.labelEn : option.dataset.labelZh;
      }});
      const rows = Array.from(document.querySelectorAll('#model-catalog .catalog-row'));
      if (count) count.textContent = english ? `Showing ${rows.filter(row => !row.hidden).length} / ${rows.length}` : `显示 ${rows.filter(row => !row.hidden).length} 条 / 共 ${rows.length} 条`;
    };
    syncLocale();
    new MutationObserver(syncLocale).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
    const activate = (name, updateHash = true) => {
      const selected = name === 'all-models' ? 'all-models' : 'featured';
      root.dataset.modelCenterTab = selected;
      tabs.forEach(tab => {
        const active = tab.dataset.centerTab === selected;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
      });
      if (updateHash) {
        const url = new URL(window.location.href);
        if (selected === 'all-models') url.hash = 'all-models';
        else url.hash = '';
        window.history.replaceState(null, '', url.href);
      }
    };
    tabs.forEach(tab => tab.addEventListener('click', () => activate(tab.dataset.centerTab)));
    tabs.forEach(tab => tab.addEventListener('keydown', event => {
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
      event.preventDefault();
      const index = tabs.indexOf(tab);
      const next = tabs[(index + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      next.focus();
      activate(next.dataset.centerTab);
    }));
    window.addEventListener('hashchange', () => activate(window.location.hash === '#all-models' ? 'all-models' : 'featured', false));
    activate(window.location.hash === '#all-models' ? 'all-models' : 'featured', false);
  })();
</script>'''
    insertion = f'''{tab_markup}
<section id="model-center-all-models-panel" class="model-center-all-models-panel" role="tabpanel" aria-labelledby="model-center-tab-all-models">
  {catalog_markup}
</section>'''
    marker = '<section id="categories"'
    if marker not in body:
        raise ValueError("feature template is missing the categories section")
    body = body.replace(marker, insertion + "\n        " + marker, 1)
    return head + f'''<body class="model-center-page" data-model-center-tab="featured">
{body}
{tab_script}
</body>
</html>
'''


def _log_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip()) or "未提供"
    if isinstance(value, dict):
        return "; ".join(f"{key}: {item}" for key, item in value.items()) or "未提供"
    return str(value or "未提供")


def _log_links(details: dict) -> str:
    urls: list[str] = []
    for key in ("sourceUrl", "register"):
        value = str(details.get(key) or "").strip()
        if value:
            urls.append(value)
    urls.extend(str(value).strip() for value in details.get("sourceUrls") or [] if str(value).strip())
    urls = list(dict.fromkeys(urls))
    if not urls:
        return '<span class="muted">未提供</span>'
    return '<ul class="log-links">' + "".join(
        f'<li><a href="{_esc(url)}" target="_blank" rel="nofollow noopener">{_esc(url)} ↗</a></li>'
        for url in urls
    ) + "</ul>"


def _log_registration_docs(details: dict) -> str:
    guide = details.get("usageGuide") if isinstance(details.get("usageGuide"), dict) else {}
    steps = [str(step).strip() for step in (details.get("registrationSteps") or guide.get("steps") or []) if str(step).strip()]
    prerequisites = [str(item).strip() for item in (guide.get("prerequisites") or []) if str(item).strip()]
    if prerequisites:
        steps = prerequisites + steps
    register_url = str(details.get("register") or details.get("registerUrl") or "").strip()
    docs_url = str(guide.get("docsUrl") or "").strip()
    links = []
    if register_url:
        links.append(("注册入口", "Open signup", register_url))
    if docs_url:
        links.append(("使用文档", "Open documentation", docs_url))
    for item in details.get("links") or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            label, url = str(item[0]).strip(), str(item[1]).strip()
            if url:
                links.append((label or "官方来源", label or "Official source", url))
    seen = set()
    link_markup = []
    for zh, en, url in links:
        if url in seen:
            continue
        seen.add(url)
        link_markup.append(f'<a class="log-registration-link" href="{_esc(url)}" target="_blank" rel="nofollow noopener">{_locale_pair(zh, en)} ↗</a>')
    steps_markup = "".join(f"<li>{_esc(step)}</li>" for step in steps)
    fallback = _locale_pair("注册步骤待核验", "Registration steps not yet verified")
    steps_block = f"<ol>{steps_markup}</ol>" if steps else f'<p class="muted">{fallback}</p>'
    links_block = f'<div class="log-registration-links">{"".join(link_markup)}</div>' if link_markup else ""
    return f'''<section class="log-registration"><h4>{_locale_pair("注册与文档", "Signup & docs")}</h4>{steps_block}{links_block}</section>'''


def _log_detail_card(event: dict) -> str:
    details = event.get("details") or {}
    detail_keys = (
        "provider", "productType", "model", "freeMechanism", "quota", "validity",
        "access", "phoneRequired", "cardRequired", "context", "maxOutput",
        "modality", "rateLimit", "status", "verificationStatus", "register",
        "evidence",
    )
    facts = "".join(
        f"<div><dt>{_esc(key)}</dt><dd>{_esc(_log_value(details.get(key)))}</dd></div>"
        for key in detail_keys
        if details.get(key) not in (None, "", [])
    )
    badge_labels = {
        "new": ("新增", "New"),
        "new_route": ("新增路径", "New route"),
        "recovered": ("恢复", "Recovered"),
        "offline": ("下线", "Offline"),
        "source_unavailable": ("来源异常", "Source issue"),
    }
    badge = _locale_pair("人工确认新增", "Curated new") if event.get("curated") else _locale_pair(*badge_labels.get(event.get("eventType"), (event.get("eventType"), event.get("eventType"))))
    return f'''<details class="log-new-card"><summary class="log-card-summary"><span class="log-badge">{badge}</span><h3>{_esc(event.get("title"))}</h3><code>{_esc(event.get("id"))}</code></summary><div class="log-card-body"><dl class="log-facts">{facts or '<div><dt>details</dt><dd>未提供</dd></div>'}</dl>{_log_registration_docs(details)}<div class="log-source"><strong>官方来源 / Official sources</strong>{_log_links(details)}</div><p class="log-reason"><strong>新增依据 / Why new:</strong> {_esc(event.get("reason"))}</p></div></details>'''


def _log_event_table(events: list[dict]) -> str:
    rows = []
    for event in events:
        details = event.get("details") or {}
        rows.append(
            f'<tr><td><strong>{_esc(event.get("title"))}</strong><small>{_esc(event.get("id"))}</small></td><td>{_esc(details.get("provider") or details.get("productType") or "未提供")}</td><td>{_esc(event.get("reason"))}</td></tr>'
        )
    if not rows:
        return f'<p class="muted">{_locale_pair("当天没有此类记录", "No records for this category.")}</p>'
    return f'<div class="table-wrap"><table><thead><tr><th>{_locale_pair("项目", "Item")}</th><th>{_locale_pair("提供商或类型", "Provider or type")}</th><th>{_locale_pair("依据", "Reason")}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _log_event_groups(events: list[dict], curated_events: list[dict] | None = None) -> dict[str, list[dict]]:
    all_events = list(events) + list(curated_events or [])
    return {
        "new": [event for event in all_events if event.get("eventType") in {"new", "new_route"}],
        "recovered": [event for event in all_events if event.get("eventType") == "recovered"],
        "offline": [event for event in all_events if event.get("eventType") == "offline"],
        "unavailable": [event for event in all_events if event.get("eventType") == "source_unavailable"],
    }


def _log_snapshot(log: dict) -> dict[str, int]:
    observed = log.get("observed") or {}
    models = [item for item in observed.get("models") or [] if isinstance(item, dict)]
    offers = [item for item in observed.get("offers") or [] if isinstance(item, dict)]
    providers = {
        str(item.get("providerId") or "").strip()
        for item in models
        if str(item.get("providerId") or "").strip()
    }
    return {"models": len(models), "providers": len(providers), "offers": len(offers)}


def _log_stat_cards(groups: dict[str, list[dict]]) -> str:
    cards = (
        ("new", "新增", "New", "发现的新资源或新路径", "Newly discovered resources or routes", "blue"),
        ("recovered", "恢复", "Recovered", "重新恢复可用的项目", "Entries available again", "green"),
        ("offline", "下线", "Offline", "确认不再可用的项目", "Confirmed unavailable entries", "red"),
        ("unavailable", "来源异常", "Source issues", "扫描失败，不等于项目下线", "Scan failure, not an offline record", "amber"),
    )
    return "".join(
        f'''<article class="log-stat-card {tone}"><div class="log-stat-label">{_locale_pair(zh, en)}</div><strong>{len(groups[key])}</strong><p>{_locale_pair(copy_zh, copy_en)}</p></article>'''
        for key, zh, en, copy_zh, copy_en, tone in cards
    )


def _log_snapshot_cards(snapshot: dict[str, int]) -> str:
    cards = (
        ("models", "模型", "Models", "当前观测到的模型记录", "Observed model records"),
        ("providers", "提供商", "Providers", "按 providerId 去重", "Deduplicated by providerId"),
        ("offers", "资源", "Offers", "当前免费与试用入口", "Current free and trial entry points"),
    )
    return "".join(
        f'''<article class="log-snapshot-card"><span>{_locale_pair(zh, en)}</span><strong>{snapshot[key]}</strong><small>{_locale_pair(copy_zh, copy_en)}</small></article>'''
        for key, zh, en, copy_zh, copy_en in cards
    )


def _log_health_cards(log: dict) -> str:
    health = log.get("sourceHealth") or {}
    cards = (("models", "模型源", "Model source"), ("offers", "资源源", "Offer source"))
    rendered = []
    for key, zh, en in cards:
        source = health.get(key) or {}
        ok = str(source.get("status") or "unknown").lower() == "ok"
        state_zh, state_en, tone = (("正常", "Healthy", "healthy") if ok else ("异常", "Issue", "issue"))
        reason = source.get("reason") or ("扫描完成" if ok else "原因未提供")
        reason_en = "Scan complete" if ok else "Reason not provided"
        rendered.append(
            f'''<article class="log-health-card {tone}"><div><span>{_locale_pair(zh, en)}</span><strong>{_locale_pair(state_zh, state_en)}</strong></div><p>{_locale_pair(reason, reason_en)}</p></article>'''
        )
    return "".join(rendered)


def _log_health_table(log: dict) -> str:
    health = log.get("sourceHealth") or {}
    rows = []
    for key, zh, en in (("models", "模型源", "Model source"), ("offers", "资源源", "Offer source")):
        source = health.get(key) or {}
        status = str(source.get("status") or "unknown")
        reason = source.get("reason") or ("扫描完成" if status == "ok" else "原因未提供")
        reason_en = "Scan complete" if status == "ok" else "Reason not provided"
        rows.append(f"<tr><td>{_locale_pair(zh, en)}</td><td><span class=\"health-pill {'healthy' if status == 'ok' else 'issue'}\">{_esc(status)}</span></td><td>{_locale_pair(reason, reason_en)}</td></tr>")
    return f'<div class="table-wrap"><table><thead><tr><th>{_locale_pair("来源", "Source")}</th><th>{_locale_pair("状态", "Status")}</th><th>{_locale_pair("说明", "Note")}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _log_empty_state(log: dict, groups: dict[str, list[dict]]) -> str:
    if not any(groups.values()):
        return f'<div class="log-empty"><strong>{_locale_pair("今日扫描完成，未发现变化", "Scan complete, no changes")}</strong><p>{_locale_pair("当前目录保持稳定。你仍可以从下面的快照进入模型和资源目录。", "The directory is stable. You can still use the snapshot below to open the model and resource directories.")}</p></div>'
    return ""


def render_daily_log_page(logs: list[dict], site_url: str) -> str:
    """Render the public daily change log as a dashboard with event details."""
    page_url = _absolute(site_url, CHANGE_LOG_PAGE_PATH)
    sorted_logs = sorted(logs, key=lambda item: str(item.get("date") or ""), reverse=True)
    dates = [str(log.get("date") or "未知日期") for log in sorted_logs]
    latest = sorted_logs[0] if sorted_logs else {}
    latest_groups = _log_event_groups(list(latest.get("events") or []), list(latest.get("curatedEvents") or []))
    latest_snapshot = _log_snapshot(latest)
    latest_has_changes = any(latest_groups.values())
    latest_status = "首次基线" if latest.get("baseline") and not latest_has_changes else ("今日有更新" if latest_has_changes else "今日扫描完成")
    latest_status_en = "Baseline" if latest.get("baseline") and not latest_has_changes else ("Changes today" if latest_has_changes else "Scan complete")
    date_nav = ""
    if len(dates) > 1:
        links = []
        for index, date in enumerate(dates):
            active = " is-active" if index == 0 else ""
            links.append(f'<a class="log-date-link{active}" href="#log-day-{_esc(date)}">{_esc(date)}</a>')
        date_nav = f'<nav class="log-date-nav" aria-label="历史日期 / History">{_locale_pair("历史日期", "History")}{"".join(links)}</nav>'
    sections = []
    for index, log in enumerate(sorted_logs):
        date = str(log.get("date") or "未知日期")
        events = list(log.get("events") or [])
        groups = _log_event_groups(events, list(log.get("curatedEvents") or []))
        snapshot = _log_snapshot(log)
        day_state = ("首次基线", "Baseline") if log.get("baseline") and not any(groups.values()) else (("有变更", "Changes") if any(groups.values()) else ("无变化", "No changes"))
        new_markup = "".join(_log_detail_card(event) for event in groups["new"]) or f'<p class="muted">{_locale_pair("当天没有新增", "No new entries.")}</p>'
        empty_state = _log_empty_state(log, groups) if index == 0 else ""
        sections.append(
            f'''<section class="log-day" id="log-day-{_esc(date)}"><div class="log-day-head"><div><span class="log-eyebrow">{_locale_pair("扫描日期", "Scan date")}</span><h2>{_esc(date)}</h2></div><div class="log-day-summary"><span>{_locale_pair(*day_state)}</span><span>{_locale_pair("新增", "New")} {len(groups["new"])}</span><span>{_locale_pair("恢复", "Recovered")} {len(groups["recovered"])}</span><span>{_locale_pair("下线", "Offline")} {len(groups["offline"])}</span><span>{_locale_pair("来源异常", "Source issues")} {len(groups["unavailable"])}</span></div></div>{empty_state}<div class="log-day-snapshot"><span>{_locale_pair("当日快照", "Daily snapshot")}</span><strong>{snapshot["models"]} {_locale_pair("模型", "models")}</strong><strong>{snapshot["providers"]} {_locale_pair("提供商", "providers")}</strong><strong>{snapshot["offers"]} {_locale_pair("资源", "offers")}</strong></div><div class="log-event-grid"><section class="log-event-panel"><h3>{_locale_pair("新增详情", "New entries")}</h3>{new_markup}</section><section class="log-event-panel"><h3>{_locale_pair("恢复", "Recovered")}</h3>{_log_event_table(groups["recovered"])}</section><section class="log-event-panel"><h3>{_locale_pair("下线", "Offline")}</h3>{_log_event_table(groups["offline"])}</section><section class="log-event-panel"><h3>{_locale_pair("来源异常", "Source issues")}</h3>{_log_event_table(groups["unavailable"])}</section></div><section class="log-event-panel log-health-panel"><h3>{_locale_pair("来源健康", "Source health")}</h3>{_log_health_table(log)}</section></section>'''
        )
    body = "".join(sections) or '<section class="log-day"><div class="log-empty"><strong>日志即将开始记录 / The daily log has not started yet.</strong></div></section>'
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "FreeLLM daily discovery log", "url": page_url, "inLanguage": ["zh-CN", "en"], "dateModified": dates[0] if dates else None}
    style = '''<style>
:root { --ink:#14213d; --muted:#66738d; --line:#dfe6f2; --paper:#f4f7fc; --panel:#fff; --blue:#285ee8; --blue-soft:#eaf0ff; --green:#0f8b68; --green-soft:#e8f8f2; --red:#c2414c; --red-soft:#fff0f1; --amber:#a66b16; --amber-soft:#fff6df; }
* { box-sizing:border-box; }
html { background:var(--paper); }
body { margin:0; color:var(--ink); background:linear-gradient(135deg,#f7f9fd 0%,#eef3fb 100%); font-family:Inter,ui-sans-serif,system-ui,sans-serif; line-height:1.55; }
a { color:var(--blue); }
.daily-log-dashboard { max-width:1240px; margin:0 auto; padding:24px 18px 64px; }
.log-hero { padding:clamp(24px,5vw,52px); border:1px solid #cbd9f2; border-radius:26px; background:linear-gradient(135deg,#fff 0%,#edf3ff 70%,#e8eeff 100%); box-shadow:0 18px 50px rgba(41,78,151,.08); }
.log-hero-top,.log-day-head { display:flex; justify-content:space-between; gap:20px; align-items:flex-start; flex-wrap:wrap; }
.log-kicker,.log-eyebrow { color:var(--blue); font:700 11px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.12em; text-transform:uppercase; }
.log-hero h1 { max-width:820px; margin:14px 0 12px; font-size:clamp(36px,6vw,72px); line-height:.98; letter-spacing:-.055em; }
.log-hero .lead { max-width:760px; margin:0; color:#52617e; font-size:16px; }
.log-hero-meta { display:grid; grid-template-columns:repeat(3,minmax(100px,1fr)); gap:10px; min-width:min(100%,360px); }
.log-hero-meta div { padding:12px; border:1px solid #d6e1f5; border-radius:14px; background:rgba(255,255,255,.72); }
.log-hero-meta span,.log-snapshot-card span { display:block; color:var(--muted); font-size:12px; }
.log-hero-meta strong { display:block; margin-top:4px; font-size:20px; }
.log-hero-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:24px; }
.log-hero-actions a { padding:9px 13px; border:1px solid #bdd0f4; border-radius:999px; background:#fff; text-decoration:none; font-weight:700; }
.log-date-nav { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin:18px 0 0; padding:10px 12px; border:1px solid var(--line); border-radius:14px; background:rgba(255,255,255,.72); color:var(--muted); font-size:12px; }
.log-date-link { padding:6px 9px; border-radius:999px; color:var(--muted); text-decoration:none; }
.log-date-link.is-active { color:#fff; background:var(--blue); }
.log-overview-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:14px; margin-top:18px; align-items:start; }
.log-panel,.log-snapshot-panel { padding:14px; border:1px solid var(--line); border-radius:16px; background:var(--panel); box-shadow:0 8px 24px rgba(41,78,151,.045); }
.log-panel h2,.log-snapshot-panel h2 { margin:0 0 10px; font-size:18px; letter-spacing:-.025em; }
.log-stat-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; align-items:start; }
.log-stat-card { min-height:92px; padding:11px; border:1px solid var(--line); border-radius:12px; background:#fbfcff; }
.log-stat-card strong { display:block; margin-top:5px; font-size:27px; line-height:1; }
.log-stat-card p { margin:5px 0 0; color:var(--muted); font-size:10px; line-height:1.3; }
.log-stat-card.blue { border-top:3px solid var(--blue); }.log-stat-card.green { border-top:3px solid var(--green); }.log-stat-card.red { border-top:3px solid var(--red); }.log-stat-card.amber { border-top:3px solid #dda12c; }
.log-stat-label { color:var(--muted); font-size:12px; font-weight:700; }
.log-snapshot-grid,.log-health-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
.log-snapshot-card { padding:10px; border:1px solid var(--line); border-radius:12px; background:#fbfcff; }.log-snapshot-card strong { display:block; margin-top:3px; font-size:24px; }.log-snapshot-card small { color:var(--muted); font-size:10px; line-height:1.3; }
.log-health-grid { grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:8px; }.log-health-card { padding:10px; border-radius:12px; background:var(--green-soft); }.log-health-card.issue { background:var(--amber-soft); }.log-health-card div { display:flex; justify-content:space-between; gap:8px; }.log-health-card span { font-size:11px; font-weight:700; }.log-health-card strong { color:var(--green); font-size:11px; }.log-health-card.issue strong { color:var(--amber); }.log-health-card p { margin:3px 0 0; color:var(--muted); font-size:10px; overflow-wrap:anywhere; }
.log-days { position:relative; margin-top:18px; padding:22px 0 30px; background:transparent; }
.log-days::before { content:""; position:absolute; left:25px; top:96px; bottom:40px; width:2px; background:linear-gradient(var(--blue),#dce5f5); }
.log-section-heading { margin:0 0 22px 70px; }.log-section-heading p { margin:8px 0 0; color:var(--muted); }
.log-day { position:relative; scroll-margin-top:18px; margin:0 0 18px 70px; padding:18px 20px 20px; border:1px solid var(--line); border-radius:18px; background:var(--panel); box-shadow:0 8px 24px rgba(41,78,151,.045); }.log-day:last-child { margin-bottom:0; }.log-day::before { content:""; position:absolute; left:-54px; top:22px; width:16px; height:16px; border:4px solid var(--paper); border-radius:50%; background:var(--blue); box-shadow:0 0 0 1px #b9c9e6; z-index:1; }.log-day-head h2 { margin:4px 0 0; font-size:30px; letter-spacing:-.035em; }.log-day-summary { display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; }.log-day-summary span { padding:5px 9px; border-radius:999px; background:var(--blue-soft); color:#3156a5; font-size:11px; font-weight:700; }
.log-empty { margin:18px 0; padding:16px 18px; border:1px dashed #b9c9e6; border-radius:15px; background:#f8faff; }.log-empty.baseline-empty { border-color:#a9bdf4; background:#eef3ff; }.log-empty strong { display:block; }.log-empty p { margin:5px 0 0; color:var(--muted); font-size:13px; }
.log-day-snapshot { display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin:18px 0; padding:11px 13px; border-radius:12px; background:#f7f9fd; color:var(--muted); font-size:12px; }.log-day-snapshot strong { color:var(--ink); }
.log-event-grid { display:grid; grid-template-columns:1fr; gap:12px; }.log-event-panel { min-width:0; padding:16px; border:1px solid var(--line); border-radius:16px; background:#fff; }.log-event-panel h3 { margin:0 0 10px; font-size:16px; }.log-health-panel { margin-top:12px; }.log-event-panel .muted { margin:8px 0; color:var(--muted); font-size:13px; }
.log-new-card { display:block; margin:10px 0 0; padding:0; border:1px solid #b8e5d7; border-left:4px solid var(--green); border-radius:14px; background:#fbfffd; overflow:hidden; }.log-new-card[open] { padding-bottom:16px; }.log-card-summary { display:flex; gap:8px; align-items:center; flex-wrap:wrap; padding:12px 16px; cursor:pointer; list-style:none; }.log-card-summary::-webkit-details-marker { display:none; }.log-card-summary::after { content:"＋"; margin-left:auto; color:var(--green); font-size:18px; line-height:1; }.log-new-card[open] > .log-card-summary::after { content:"－"; }.log-card-summary h3 { margin:0; font-size:17px; }.log-card-summary code,.log-facts dt,small { color:var(--muted); font-size:11px; }.log-badge { padding:4px 8px; border-radius:999px; color:var(--green); background:var(--green-soft); font-size:11px; font-weight:800; }.log-card-body { padding:0 16px; }.log-facts { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; margin:0 0 13px; }.log-facts div { padding:8px 9px; border:1px solid var(--line); border-radius:9px; background:#fff; }.log-facts dd { margin:3px 0 0; overflow-wrap:anywhere; font-size:12px; }.log-source { padding-top:10px; border-top:1px solid var(--line); font-size:12px; }.log-links { margin:5px 0; padding-left:17px; overflow-wrap:anywhere; }.log-reason { margin:10px 0 0; color:var(--muted); font-size:12px; }
.log-registration { margin:12px 0; padding:12px 14px; border:1px solid #cfe0f8; border-radius:12px; background:#f7faff; }.log-registration h4 { margin:0; font-size:14px; }.log-registration ol { margin:7px 0 0; padding-left:20px; }.log-registration li { margin:3px 0; font-size:12px; }.log-registration .muted { margin:7px 0 0; }.log-registration-links { display:flex; flex-wrap:wrap; gap:7px; margin-top:10px; }.log-registration-link { padding:5px 8px; border:1px solid #bcd0f2; border-radius:999px; background:#fff; font-size:11px; text-decoration:none; }
.table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:10px; }.table-wrap table { width:100%; min-width:520px; border-collapse:collapse; font-size:12px; }.table-wrap th,.table-wrap td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }.table-wrap th { color:var(--muted); font-size:10px; }.table-wrap tr:last-child td { border-bottom:0; }.table-wrap td small { display:block; margin-top:3px; }.health-pill { display:inline-block; padding:3px 7px; border-radius:999px; background:var(--green-soft); color:var(--green); font-size:11px; }.health-pill.issue { background:var(--amber-soft); color:var(--amber); }
@media (max-width:900px) { .log-overview-grid { grid-template-columns:1fr; } }
@media (max-width:720px) { .daily-log-dashboard { padding:12px 8px 42px; }.log-hero { padding:22px 18px; border-radius:20px; }.log-hero-meta { grid-template-columns:1fr; }.log-stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.log-snapshot-grid,.log-health-grid,.log-event-grid { grid-template-columns:1fr; }.log-days { padding:16px 0; }.log-days::before { left:17px; top:92px; bottom:34px; }.log-section-heading { margin-left:42px; }.log-day { margin-left:42px; padding:16px 14px; border-radius:15px; }.log-day::before { left:-34px; top:20px; width:14px; height:14px; }.log-day-summary { justify-content:flex-start; } }
</style>'''
    style += STATIC_LOCALE_SCRIPT
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>每日更新 · FreeLLM</title><meta name="description" content="FreeLLM 每日检查官方来源，记录 AI 资源的新增、恢复、下线和异常，并保留可核对的官方证据。"><link rel="canonical" href="{_esc(page_url)}">{_hreflang_links(site_url, CHANGE_LOG_PAGE_PATH)}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>{STATIC_LOCALE_STYLE}{VERCEL_ANALYTICS_SCRIPT}</head><body data-static-locale="true"><main class="daily-log-dashboard"><header class="log-hero"><div class="log-hero-top"><div><div class="log-kicker">DAILY UPDATES / 每日更新</div><h1>{_locale_pair('今天的 AI 资源有什么变化？', 'What changed in AI today?')}</h1><p class="lead">{_locale_pair('我们每天检查官方来源，记录新增、恢复、下线和异常。', 'We check official sources daily and record new, recovered, offline and source issues.')}</p></div><div class="log-hero-meta"><div><span>{_locale_pair('最新日期', 'Latest date')}</span><strong>{_esc(dates[0] if dates else '—')}</strong></div><div><span>{_locale_pair('扫描状态', 'Scan status')}</span><strong>{_locale_pair('今日扫描完成', 'Scan complete')}</strong></div><div><span>{_locale_pair('目录状态', 'Directory state')}</span><strong>{_locale_pair(latest_status, latest_status_en)}</strong></div></div></div><div class="log-hero-actions"><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair('返回首页', 'Back to FreeLLM')}</a><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('查看模型目录', 'Open model directory')}</a></div></header>{date_nav}<section class="log-overview-grid"><section class="log-panel"><h2>{_locale_pair('今日变化', "Today's changes")}</h2><div class="log-stat-grid">{_log_stat_cards(latest_groups)}</div></section><section class="log-snapshot-panel"><h2>{_locale_pair('当前目录快照', 'Current snapshot')}</h2><div class="log-snapshot-grid">{_log_snapshot_cards(latest_snapshot)}</div><div class="log-health-grid">{_log_health_cards(latest)}</div></section></section><section class="log-days"><div class="log-section-heading"><span class="log-eyebrow">CHANGE STREAM / 变更流</span><p>{_locale_pair('按日期查看变更与来源健康状态。', 'Review changes and source health by date.')}</p></div>{body}</section><footer class="log-footer"><p>{_locale_pair('下线只在来源成功时判定；来源抓取失败不会被误报为下线。', 'Offline is only recorded after a successful source snapshot; a failed fetch is never treated as offline.')}</p>{_static_locale_nav()}</footer></main>{style}</body></html>'''


def _load_daily_logs(data_path: Path) -> list[dict]:
    log_dir = data_path.parent / "daily-log"
    if not log_dir.is_dir():
        return []
    logs = []
    for path in sorted(log_dir.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            logs.append(value)
    return logs


def render_sitemap(
    offers: list[dict],
    categories: list[str],
    site_url: str,
    models: list[dict] | None = None,
    providers: list[dict] | None = None,
) -> str:
    paths = [
        "/",
        "/about/",
        "/terms/",
        "/privacy/",
        guide_url(),
        OPENAI_ALTERNATIVES_GUIDE_PATH,
        CLAUDE_CODE_ALTERNATIVES_GUIDE_PATH,
        MODELS_PAGE_PATH,
        ALL_MODELS_PAGE_PATH,
        MODEL_CENTER_PAGE_PATH,
        PROVIDERS_PAGE_PATH,
        CHANGE_LOG_PAGE_PATH,
    ] + [f'/guides/{definition["slug"]}/' for definition in THEME_GUIDE_DEFINITIONS] + [offer_url(offer) for offer in offers] + [category_url(category) for category in categories]
    paths += [model_aggregate_url(model) for model in (models or [])]
    paths += [provider_url(provider) for provider in (providers or [])]
    paths = list(dict.fromkeys(paths))
    urls = "\n".join(f"  <url><loc>{_esc(_absolute(site_url, path))}</loc></url>" for path in paths)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
'''


def _expected_files(offers: list[dict], site_url: str, models: list[dict] | None = None, operations: list[dict] | None = None, daily_logs: list[dict] | None = None) -> tuple[dict[Path, str], list[str]]:
    categories = [
        category
        for category in CATEGORY_DEFINITIONS
        if any(category in categorize_offer(offer) for offer in offers)
    ]
    model_catalog = models or []
    providers = _provider_catalog_from_models(model_catalog, operations)
    provider_access, _, model_access = _load_access_context()
    files: dict[Path, str] = {
        Path("sitemap.xml"): render_sitemap(offers, categories, site_url, model_catalog, providers),
        Path("models") / "index.html": render_models_page(offers, site_url),
        Path("models") / "all" / "index.html": render_models_page(offers, site_url, models),
        Path("models") / "center" / "index.html": render_model_center_page(offers, site_url, model_catalog),
        Path("providers") / "index.html": render_providers_page(providers, model_catalog, site_url),
        Path("logs") / "index.html": render_daily_log_page(daily_logs if daily_logs is not None else _load_daily_logs(ACCESS_DATA_DIR / "offers.json"), site_url),
        Path("guides") / "free-llm" / "index.html": render_guide_page(site_url),
        Path("guides") / "free-openai-api-alternatives" / "index.html": render_openai_alternatives_page(offers, site_url),
        Path("guides") / "claude-code-free-alternatives" / "index.html": render_claude_code_alternatives_page(offers, site_url),
    }
    for definition in THEME_GUIDE_DEFINITIONS:
        path = Path("guides") / definition["slug"] / "index.html"
        files[path] = _render_theme_guide_page_expanded(offers, model_catalog, site_url, definition["slug"])
    for offer in offers:
        files[Path("offers") / _slug(offer["id"]) / "index.html"] = render_offer_page(offer, offers, site_url, operations)
    for legacy_id, target_id in LEGACY_OFFER_REDIRECTS.items():
        files[Path("offers") / legacy_id / "index.html"] = render_legacy_offer_redirect(legacy_id, target_id, site_url)
    for category in categories:
        files[Path("category") / category / "index.html"] = render_category_page(category, offers, site_url)
    for model_name in sorted(
        {str(model.get("model") or "").strip() for model in model_catalog if model.get("model")},
        key=lambda value: (_safe_slug(value, "model"), value.lower(), value),
    ):
        records = [model for model in model_catalog if str(model.get("model") or "").strip().lower() == model_name.lower()]
        files[Path("models") / _safe_slug(model_name, "model") / "index.html"] = render_model_aggregate_page(model_name, records, offers, site_url, provider_access, model_access)
    for provider in providers:
        files[Path("providers") / _safe_slug(provider.get("id"), "provider") / "index.html"] = render_provider_page(provider, model_catalog, offers, site_url, operations, provider_access, model_access)
    for path, page in list(files.items()):
        if path.suffix != ".html":
            continue
        if path.parts[:1] == ("offers",) and len(path.parts) > 1 and path.parts[1] in LEGACY_OFFER_REDIRECTS:
            continue
        page_path = "/" + path.as_posix()
        if page_path.endswith("index.html"):
            page_path = page_path[:-len("index.html")]
        files[path] = _inject_hreflang_links(page, site_url, page_path)
    return files, categories


def _load_data(data_path: Path) -> list[dict]:
    errors = validate_offers(data_path)
    if errors:
        raise SystemExit("Invalid offers data:\n" + "\n".join(errors))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for offer in data:
        _slug(offer["id"])
    return data


def _load_models(data_path: Path) -> list[dict]:
    models_path = data_path.parent / "models.json"
    if not models_path.is_file():
        return []
    errors = validate_models(models_path)
    if errors:
        raise SystemExit("Invalid models data:\n" + "\n".join(errors))
    return json.loads(models_path.read_text(encoding="utf-8"))


def _load_model_access(data_path: Path) -> list[dict]:
    access_path = data_path.parent / "model-access.json"
    if not access_path.is_file():
        return []
    errors = validate_model_access_file(access_path)
    if errors:
        raise SystemExit("Invalid model access data:\n" + "\n".join(errors))
    return json.loads(access_path.read_text(encoding="utf-8"))


def _exclude_retired_models(models: list[dict], access_cards: list[dict]) -> list[dict]:
    """Retired models must never render as registerable free models."""
    retired = {str(card.get("modelId") or "") for card in access_cards if card.get("accessStatus") == "retired"}
    if not retired:
        return models
    return [model for model in models if str(model.get("id") or "") not in retired]


def _load_operations(data_path: Path) -> list[dict]:
    operation_dir = data_path.parent / "operations"
    if not operation_dir.is_dir():
        return []
    guides: list[dict] = []
    for path in sorted(operation_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_operation_guides(data, path.name)
        if errors:
            raise SystemExit("Invalid operation guide data:\n" + "\n".join(errors))
        guides.append(data)
    return guides


def _read_manifest(output_root: Path) -> list[str]:
    manifest_path = output_root / MANIFEST_NAME
    if not manifest_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [path for path in manifest.get("files", []) if isinstance(path, str)] if isinstance(manifest, dict) else []


def _clean_previous_pages(output_root: Path) -> None:
    for relative in _read_manifest(output_root):
        path = (output_root / relative).resolve()
        root = output_root.resolve()
        relative_path = path.relative_to(root)
        if root not in path.parents or path.name != "index.html" or len(relative_path.parts) not in {2, 3} or relative_path.parts[0] not in {"offers", "category", "guides", "models", "providers", "logs"}:
            continue
        if path.is_file():
            path.unlink()
        try:
            path.parent.rmdir()
        except OSError:
            pass


LEGAL_FOOTER_LINKS = (
    '<p><a href="/about/">{zh}关于本站{/zh}{en}About{/en}</a>'
    ' · <a href="/terms/">{zh}使用条款与免责声明{/zh}{en}Terms &amp; Disclaimer{/en}</a>'
    ' · <a href="/privacy/">{zh}隐私政策（含广告 Cookie 说明）{/zh}{en}Privacy Policy (incl. ad cookies){/en}</a></p>'
)


def _localized_legal_links() -> str:
    return (LEGAL_FOOTER_LINKS
            .replace('{zh}', '<span lang="zh-CN">').replace('{/zh}', '</span>')
            .replace('{en}', '<span lang="en">').replace('{/en}', '</span>'))


def _append_legal_links(content: str) -> str:
    """Every generated page must expose the privacy / about / terms pages for AdSense compliance."""
    if "</footer>" not in content or "href=\"/privacy/\"" in content:
        return content
    return content.replace("</footer>", _localized_legal_links() + "</footer>", 1)


def build_site(data_path: str | Path, output_root: str | Path, site_url: str = SITE_URL, check: bool = False) -> BuildResult | bool:
    data_path = Path(data_path)
    offers = _load_data(data_path)
    models = _load_models(data_path)
    models = _exclude_retired_models(models, _load_model_access(data_path))
    operations = _load_operations(data_path)
    daily_logs = _load_daily_logs(data_path)
    files, categories = _expected_files(offers, site_url.rstrip("/"), models, operations, daily_logs)
    files = {relative: _append_legal_links(content) for relative, content in files.items()}
    output_root = Path(output_root)
    if check:
        stale = []
        for relative, content in files.items():
            path = output_root / relative
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(str(relative))
        if stale:
            print("stale SEO output: " + ", ".join(stale))
            return False
        print(f"current SEO output: {len(files)} files")
        return True

    _clean_previous_pages(output_root)
    for relative, content in files.items():
        path = output_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    manifest = {"files": [path.as_posix() for path in files if path.parts and path.parts[0] in {"offers", "category", "guides", "models", "providers", "logs"}]}
    (output_root / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    result = BuildResult(offer_count=len(offers), category_count=len(categories), page_count=len(files))
    print(f"built SEO output: {result.offer_count} offers, {result.category_count} categories, {result.page_count} files")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/offers.json")
    parser.add_argument("--output", default=".")
    parser.add_argument("--site-url", default=SITE_URL)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build_site(args.data, args.output, site_url=args.site_url, check=args.check)
    return 0 if result is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
