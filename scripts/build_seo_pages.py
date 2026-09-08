"""Generate crawlable offer pages, category pages, guides, and the production sitemap."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.schema import validate_offers


SITE_URL = "https://freellm.top"
SHARE_IMAGE_PATH = "/freellm-01-hero.png"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MANIFEST_NAME = ".seo-pages-manifest.json"

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


GUIDE_SOURCE_URL = "https://github.com/nejib1/Free-LLM/blob/main/README.zh-CN.md"
GUIDE_REPOSITORY_URL = "https://github.com/nejib1/Free-LLM"

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


def _list(items: list[object], empty: str = "Not specified") -> str:
    if not items:
        return f"<p>{_esc(empty)}</p>"
    return "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in items) + "</ul>"


def _source_links(offer: dict) -> str:
    urls = list(dict.fromkeys([offer.get("register"), *(offer.get("sourceUrls") or [])]))
    return "".join(
        f'<li><a href="{_esc(url)}" rel="nofollow noopener" target="_blank">{_esc(url)}</a></li>'
        for url in urls
        if url
    ) or "<li>暂无官方来源</li>"


def _related_links(offer: dict, offers: list[dict]) -> str:
    categories = set(categorize_offer(offer))
    related = [
        candidate
        for candidate in offers
        if candidate.get("id") != offer.get("id") and categories.intersection(categorize_offer(candidate))
    ][:4]
    if not related:
        return '<li><a href="/">浏览全部免费 AI 资源</a></li>'
    return "".join(
        f'<li><a href="{_esc(offer_url(candidate))}">{_esc(candidate.get("title") or candidate.get("name"))}</a></li>'
        for candidate in related
    )


def render_offer_page(offer: dict, offers: list[dict], site_url: str) -> str:
    path = offer_url(offer)
    title = offer.get("title") or offer.get("name")
    description = _description(offer)
    page_title = f"{title} · FreeLLM 免费 AI 资源索引"
    social_meta = _social_meta(site_url, path, page_title, description, "article")
    guide = offer.get("usageGuide") or {}
    categories = categorize_offer(offer)
    category_links = "".join(
        f'<a class="tag" href="{_esc(category_url(category))}">{_esc(CATEGORY_DEFINITIONS[category]["name_zh"])}</a>'
        for category in categories
    ) or '<a class="tag" href="/">免费 AI 资源索引</a>'
    examples = guide.get("examples") or {}
    example_markup = "".join(
        f'<h3>{_esc(name)}</h3><pre><code>{_esc(code)}</code></pre>' for name, code in examples.items()
    )
    context_window = offer.get("contextWindow") or {}
    context_window_markup = ""
    if context_window and offer.get("productType") in {"api", "open_weights", "coding_plan"}:
        context_summary = context_window.get("zh") or context_window.get("en") or f"{context_window.get('tokens', '—')} tokens"
        context_source = context_window.get("sourceUrl")
        source_markup = (
            f' <a href="{_esc(context_source)}" rel="nofollow noopener" target="_blank">来源 ↗</a>'
            if context_source
            else ""
        )
        context_window_markup = f'''<section>
      <h2>上下文窗口</h2>
      <p>{_esc(context_summary)}.{source_markup}</p>
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
  {social_meta}
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
    .muted {{ color: #68748a; }}
    @media (max-width: 600px) {{ body {{ padding: 14px 10px 40px; }} header, main, footer {{ padding: 18px; }} }}
  </style>
</head>
<body data-offer-id="{_esc(offer.get('id'))}">
  <header>
    <p><a href="{_esc(_absolute(site_url, '/'))}">FreeLLM 免费 AI 资源索引</a> / 资源详情</p>
    <h1>{_esc(title)}</h1>
    <p>{_esc(offer.get('providerMeta') or offer.get('provider'))}</p>
    <nav aria-label="Categories">{category_links}</nav>
  </header>
  <main>
    <section>
      <h2>这个资源提供什么</h2>
      <p>{_esc(offer.get('why'))}</p>
    </section>
    <section>
      <h2>关键信息</h2>
      <div class="facts">
        <div class="fact"><strong>免费方式</strong><span>{_esc(offer.get('freeSummary') or offer.get('mechanism'))}</span></div>
        <div class="fact"><strong>有效期</strong><span>{_esc(offer.get('validitySummary') or offer.get('validity'))}</span></div>
        <div class="fact"><strong>访问条件</strong><span>{_esc(offer.get('accessSummary') or offer.get('access'))}</span></div>
        <div class="fact"><strong>最后核验</strong><span>{_esc(offer.get('lastVerifiedAt'))}</span></div>
      </div>
    </section>
    {context_window_markup}
    <section>
      <h2>如何使用</h2>
      <p>{_esc(guide.get('summary') or offer.get('command'))}</p>
      <h3>前置条件</h3>
      {_list(guide.get('prerequisites') or [offer.get('access')], '请查看官方访问要求。')}
      <h3>步骤</h3>
      {_list(guide.get('steps') or [offer.get('command')], '请按照官方设置说明操作。')}
      {example_markup}
    </section>
    <section>
      <h2>官方来源</h2>
      <p class="muted">{_esc(offer.get('evidence'))}</p>
      <ul>{_source_links(offer)}</ul>
    </section>
    <section>
      <h2>相关资源</h2>
      <ul>{_related_links(offer, offers)}</ul>
    </section>
  </main>
  <footer>
    <p><strong>重要：</strong>免费访问可能受地区、账户类型、速率限制、有效期或提供商条款影响。依赖该资源前请核对官方来源。</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">返回 FreeLLM 免费 AI 资源索引</a></p>
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
          <h2><a href="{_esc(offer_url(offer))}">{_esc(offer.get("title") or offer.get("name"))}</a></h2>
          <p>{_esc(offer.get("freeSummary") or offer.get("mechanism"))}</p>
          <p class="muted">{_esc(offer.get("validitySummary"))} · {_esc(offer.get("accessSummary"))}</p>
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
<body>
  <header>
    <p><a href="{_esc(_absolute(site_url, '/'))}">FreeLLM 免费 AI 资源索引</a> / 分类</p>
    <h1>{_esc(definition['name'])}</h1>
    <p>{_esc(definition['description'])}</p>
    <p>{_esc(definition['description_zh'])}</p>
    <p>{len(matching)} 个经过核验的资源</p>
  </header>
  <main>
    {items}
  </main>
  <footer>
    <p>资源按免费额度、试用、优惠、学生资格、开放权重和低成本访问方式区分。使用前请核对官方条款。</p>
    <p><a href="{_esc(_absolute(site_url, '/'))}">返回 FreeLLM 免费 AI 资源索引</a></p>
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
  </main>
  <footer>
    <p><strong>免责声明：</strong>免费服务可能受地区、账户类型、速率限制、有效期和 Provider 条款影响。不要把免费试用当作生产系统的稳定推理基础设施。</p>
    <p>参考项目内容按其仓库声明的 <strong>MIT License</strong> 使用，并保留来源与许可说明。<a href="{_esc(_absolute(site_url, '/'))}">返回 Free AI Index 首页 →</a></p>
  </footer>
</body>
</html>
'''


def render_sitemap(offers: list[dict], categories: list[str], site_url: str) -> str:
    paths = ["/", guide_url()] + [offer_url(offer) for offer in offers] + [category_url(category) for category in categories]
    urls = "\n".join(f"  <url><loc>{_esc(_absolute(site_url, path))}</loc></url>" for path in paths)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
'''


def _expected_files(offers: list[dict], site_url: str) -> tuple[dict[Path, str], list[str]]:
    categories = [
        category
        for category in CATEGORY_DEFINITIONS
        if any(category in categorize_offer(offer) for offer in offers)
    ]
    files: dict[Path, str] = {
        Path("sitemap.xml"): render_sitemap(offers, categories, site_url),
        Path("guides") / "free-llm" / "index.html": render_guide_page(site_url),
    }
    for offer in offers:
        files[Path("offers") / _slug(offer["id"]) / "index.html"] = render_offer_page(offer, offers, site_url)
    for category in categories:
        files[Path("category") / category / "index.html"] = render_category_page(category, offers, site_url)
    return files, categories


def _load_data(data_path: Path) -> list[dict]:
    errors = validate_offers(data_path)
    if errors:
        raise SystemExit("Invalid offers data:\n" + "\n".join(errors))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for offer in data:
        _slug(offer["id"])
    return data


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
        if root not in path.parents or path.name != "index.html" or path.parent.name not in {"offers", "category", "free-llm"}:
            continue
        if path.is_file():
            path.unlink()
        try:
            path.parent.rmdir()
        except OSError:
            pass


def build_site(data_path: str | Path, output_root: str | Path, site_url: str = SITE_URL, check: bool = False) -> BuildResult | bool:
    offers = _load_data(Path(data_path))
    files, categories = _expected_files(offers, site_url.rstrip("/"))
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
    manifest = {"files": [path.as_posix() for path in files if path.parts and (path.parts[0] in {"offers", "category"} or path.parts[:2] == ("guides", "free-llm"))]}
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
