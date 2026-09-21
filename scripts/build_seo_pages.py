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
SHARE_IMAGE_PATH = "/freellm-06-faq.png"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MANIFEST_NAME = ".seo-pages-manifest.json"

VERCEL_ANALYTICS_SCRIPT = '''<script>
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  </script>
  <script defer src="/_vercel/insights/script.js"></script>'''

GA4_MEASUREMENT_ID = "G-JMK4R9519M"

GA4_SCRIPT = f'''<!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA4_MEASUREMENT_ID}');
  </script>'''

ADSENSE_SCRIPT = '''<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2461062743308239"
          crossorigin="anonymous"></script>'''

ADSENSE_SLOT = os.environ.get("FREELLM_ADSENSE_SLOT", "").strip()

STATIC_LOCALE_STYLE = '''<style id="static-locale-style">
    html[data-locale="en"] [lang="zh-CN"], html[data-locale="zh-CN"] [lang="en"] { display: none !important; }
    .static-locale-nav { display: flex; gap: 8px; align-items: center; font-size: .85rem; }
    .static-locale-nav button { border: 0; padding: 0; background: none; color: var(--accent, currentColor); font: inherit; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }
  </style>'''

STATIC_LOCALE_SCRIPT = '''<script id="static-locale-script">
    (() => {
      const key = 'free-ai-index-locale';
      const query = new URLSearchParams(window.location.search);
      const queryLocale = query.get('lang');
      const normalize = value => String(value || '').toLowerCase().startsWith('en') ? 'en' : 'zh-CN';
      let storedLocale = '';
      try { storedLocale = localStorage.getItem(key) || ''; } catch (error) { /* storage can be unavailable */ }
      const locale = queryLocale ? normalize(queryLocale) : normalize(storedLocale);
      document.documentElement.lang = locale;
      document.documentElement.dataset.locale = locale;
      try { localStorage.setItem(key, locale); } catch (error) { /* storage can be unavailable */ }

      if (queryLocale) {
        query.delete('lang');
        const search = query.toString();
        history.replaceState(null, '', `${window.location.pathname}${search ? '?' + search : ''}${window.location.hash}`);
      }

      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-locale-switch]').forEach(button => {
          button.addEventListener('click', () => {
            const next = normalize(button.dataset.localeSwitch);
            try { localStorage.setItem(key, next); } catch (error) { /* storage can be unavailable */ }
            window.location.reload();
          });
        });
      });
    })();
  </script>'''

# Editorial design assets shared by the Agent Skills pages: webfonts + dark-mode bootstrap.
SKILLS_THEME_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
                      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                      '<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1'
                      '&family=JetBrains+Mono:wght@400;500&family=Manrope:wght@400;500;600;700'
                      '&family=Noto+Serif+SC:wght@400;600&display=swap" rel="stylesheet">')

SKILLS_THEME_SCRIPT = '''<script id="skills-theme-script">
    (() => {
      let theme = '';
      try {
        theme = localStorage.getItem('freellm-theme')
          || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : '');
      } catch (error) { /* storage can be unavailable */ }
      if (theme === 'dark') document.documentElement.dataset.theme = 'dark';
      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.theme-toggle').forEach(button => {
          button.addEventListener('click', () => {
            const next = document.documentElement.dataset.theme === 'dark' ? '' : 'dark';
            if (next === 'dark') document.documentElement.dataset.theme = 'dark';
            else delete document.documentElement.dataset.theme;
            try { localStorage.setItem('freellm-theme', next); } catch (error) { /* ignore */ }
          });
        });
      });
    })();
  </script>'''

SKILLS_THEME_ASSETS = SKILLS_THEME_FONTS + SKILLS_THEME_SCRIPT

# Editorial design tokens (data-platform-editorial): warm paper canvas, Instrument Serif
# display type, Manrope body, JetBrains Mono metadata, hairline borders, pastel semantics.
# Shared by every content page; legacy token names (--muted/--soft/--blue) are aliased so
# page-specific rules written against the old palette keep resolving.
EDITORIAL_TOKENS_CSS = ''':root { color-scheme: light; --canvas:#FBFBFA; --canvas-warm:#F7F6F3; --surface:#FFFFFF; --surface-soft:#F9F9F8; --ink:#2F3437; --ink-secondary:#787774; --ink-tertiary:#B4B4B0; --line:#EAEAEA; --line-soft:rgba(0,0,0,.04); --ink-solid:#111111; --ink-solid-hover:#333333; --ink-solid-contrast:#FFFFFF; --accent:#1744E8; --accent-soft:#E9EEFF; --pale-red-bg:#FDEBEC; --pale-red-text:#9F2F2D; --pale-green-bg:#EDF3EC; --pale-green-text:#346538; --pale-yellow-bg:#FBF3DB; --pale-yellow-text:#956400; --pale-stone-bg:#F0EFEC; --pale-stone-text:#5A5854; --code-bg:#111111; --code-text:#F4F2EE; --card-shadow:0 2px 8px rgba(0,0,0,.04); --font-serif:'Instrument Serif','Noto Serif SC',Georgia,'Songti SC','SimSun',serif; --font-sans:'Manrope','PingFang SC','Hiragino Sans GB','Microsoft YaHei',ui-sans-serif,system-ui,sans-serif; --font-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace; --muted:#787774; --soft:#F7F6F3; --blue:#1744E8; }
:root[data-theme="dark"] { color-scheme: dark; --canvas:#0E0F11; --canvas-warm:#14161A; --surface:#181B20; --surface-soft:#1E2127; --ink:#ECEAE6; --ink-secondary:#A7A5A0; --ink-tertiary:#6E6C68; --line:#26292F; --line-soft:rgba(255,255,255,.04); --ink-solid:#F4F2EE; --ink-solid-hover:#D8D6D2; --ink-solid-contrast:#111111; --accent:#7BC0E5; --accent-soft:#0E2533; --pale-red-bg:#2A1416; --pale-red-text:#E98A86; --pale-green-bg:#112218; --pale-green-text:#86C098; --pale-yellow-bg:#2B2010; --pale-yellow-text:#D9A85F; --pale-stone-bg:#232220; --pale-stone-text:#B4B1AB; --code-bg:#1E2127; --code-text:#ECEAE6; --card-shadow:0 2px 8px rgba(0,0,0,.3); --muted:#A7A5A0; --soft:#1E2127; --blue:#7BC0E5; }'''

EDITORIAL_BASE_CSS = EDITORIAL_TOKENS_CSS + '''
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body { margin:0 auto; max-width:1180px; padding:24px 20px 64px; background:var(--canvas); color:var(--ink); font:400 15px/1.65 var(--font-sans); -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }
::selection { background:var(--accent-soft); }
a { color:var(--accent); }
button, input, select { font:inherit; }
h1, h2, h3, h4 { font-family:var(--font-serif); font-weight:400; color:var(--ink); }
header, main, footer { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:clamp(22px,4vw,36px); margin-bottom:16px; position:relative; }
header a { color:var(--accent); }
h1 { margin:18px 0 10px; line-height:1.08; letter-spacing:-.02em; }
h2 { margin:0 0 8px; line-height:1.2; letter-spacing:-.015em; }
h3 { margin:22px 0 6px; }
p { max-width:880px; }
.lead { max-width:840px; color:var(--ink-secondary); font-size:16px; line-height:1.7; }
.muted { color:var(--ink-secondary); }
.crumb, .eyebrow { font:500 11px/1.5 var(--font-mono); letter-spacing:.1em; text-transform:uppercase; }
.crumb { color:var(--ink-secondary); }
.crumb a { color:var(--ink-secondary); text-decoration:none; }
.crumb a:hover { color:var(--ink); }
header > p:first-child { margin:0; color:var(--ink-secondary); font:500 12px/1.7 var(--font-mono); }
header > p:first-child a { color:var(--ink-secondary); }
.eyebrow { color:var(--accent); }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { padding:11px 12px; text-align:left; vertical-align:top; border-bottom:1px solid var(--line-soft); }
th { color:var(--ink-tertiary); background:var(--surface-soft); font:500 11px/1.5 var(--font-mono); letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; }
tr:last-child td { border-bottom:0; }
.table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:8px; margin:14px 0 18px; background:var(--surface); }
.table-wrap table { min-width:640px; }
td small { display:block; margin-top:4px; color:var(--ink-secondary); }
code { padding:2px 6px; border-radius:5px; background:var(--surface-soft); color:var(--ink); font:400 .88em var(--font-mono); overflow-wrap:anywhere; }
pre { overflow-x:auto; margin:12px 0; padding:16px 18px; border-radius:8px; background:var(--code-bg); color:var(--code-text); font:400 13px/1.65 var(--font-mono); }
pre code { padding:0; background:none; color:inherit; }
.link-list, .steps { padding-left:1.35em; }
.steps li { margin:8px 0; }
.callout { margin:20px 0 0; padding:14px 18px; border-left:3px solid var(--ink); border-radius:0 6px 6px 0; background:var(--canvas-warm); color:var(--ink); font-size:14px; }
.callout.green { border-left-color:var(--pale-green-text); background:var(--pale-green-bg); color:var(--pale-green-text); }
.notice { padding:14px 18px; border-left:3px solid var(--pale-green-text); border-radius:0 6px 6px 0; background:var(--pale-green-bg); color:var(--pale-green-text); }
.button, .btn { display:inline-block; width:max-content; padding:9px 16px; border:1px solid var(--ink-solid); border-radius:6px; background:var(--ink-solid); color:var(--ink-solid-contrast); text-decoration:none; font-size:13px; font-weight:600; transition:background .15s, border-color .15s; }
.button:hover, .btn:hover { background:var(--ink-solid-hover); border-color:var(--ink-solid-hover); color:var(--ink-solid-contrast); }
.ghost { font-size:13px; color:var(--ink-secondary); }
.stats { display:flex; flex-wrap:wrap; gap:8px 22px; margin:18px 0 0; padding-top:16px; border-top:1px solid var(--line); color:var(--ink-secondary); font-size:13px; }
.stats strong { font-family:var(--font-serif); font-size:19px; font-weight:400; color:var(--ink); }
.tag { display:inline-block; padding:3px 11px; border-radius:9999px; background:var(--accent-soft); color:var(--accent); text-decoration:none; font:500 11px/1.7 var(--font-mono); letter-spacing:.04em; }
.flag-featured { display:inline-flex; align-items:center; gap:4px; padding:3px 9px; border-radius:9999px; border:1px solid var(--pale-yellow-text); background:var(--pale-yellow-text); color:var(--pale-yellow-bg); font:700 11px/1.7 var(--font-mono); letter-spacing:.06em; text-decoration:none; white-space:nowrap; }
.status { display:inline-block; border-radius:9999px; padding:3px 8px; font:500 11px/1.5 var(--font-mono); white-space:nowrap; }
.status-online { color:var(--pale-green-text); background:var(--pale-green-bg); }
.status-offline { color:var(--pale-red-text); background:var(--pale-red-bg); }
.status-degraded, .status-unknown { color:var(--pale-yellow-text); background:var(--pale-yellow-bg); }
.facts { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }
.fact { padding:13px 14px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); }
.fact strong, .fact span { display:block; }
.fact strong { color:var(--ink-tertiary); font:500 10.5px/1.6 var(--font-mono); text-transform:uppercase; letter-spacing:.08em; }
.provider-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:14px; }
.provider-card { display:flex; flex-direction:column; min-height:200px; padding:20px; border:1px solid var(--line); border-radius:8px; background:var(--surface); transition:box-shadow .2s; }
.provider-card:hover { box-shadow:var(--card-shadow); }
.provider-card h2 { margin:8px 0 4px; font-size:22px; }
.provider-card h2 a { color:var(--ink); text-decoration:none; }
.provider-card h2 a:hover { color:var(--accent); }
.provider-card p { margin:5px 0; color:var(--ink-secondary); font-size:13.5px; }
.provider-card .eyebrow { color:var(--ink-tertiary); }
.catalog-table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:8px; }
.catalog-table { width:100%; min-width:900px; border-collapse:collapse; font-size:13px; }
.catalog-table th, .catalog-table td { padding:10px 11px; text-align:left; vertical-align:top; border-bottom:1px solid var(--line-soft); }
.catalog-table thead th { position:sticky; top:0; z-index:1; color:var(--ink-tertiary); background:var(--surface-soft); font:500 11px/1.5 var(--font-mono); letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; }
.catalog-table tbody tr:last-child td { border-bottom:0; }
.catalog-table small { display:block; margin-top:3px; color:var(--ink-secondary); font:400 11px/1.5 var(--font-mono); }
.catalog-table .model-name, .catalog-table .model-id { display:block; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.catalog-table .model-id { margin-top:3px; color:var(--ink-tertiary); }
.model-badges { display:flex; flex-wrap:wrap; gap:4px; min-width:80px; }
.model-badge { border-radius:9999px; padding:2px 8px; color:var(--accent); background:var(--accent-soft); font:500 11px/1.6 var(--font-mono); white-space:nowrap; }
.catalog-group-row th { padding:13px 11px 7px; color:var(--ink); background:var(--canvas-warm); font-size:13px; letter-spacing:0; text-transform:none; font-family:var(--font-sans); }
.catalog-empty { margin:16px 0 0; padding:13px 16px; border-radius:6px; color:var(--pale-yellow-text); background:var(--pale-yellow-bg); }
.source-cell { min-width:100px; white-space:nowrap; }
.freshness { color:var(--ink-secondary); }
.freshness-stale { color:var(--pale-red-text); }
.catalog-table .latency-cell { white-space:nowrap; }
.catalog-table .latency-value { font:500 12.5px/1.5 var(--font-mono); color:var(--ink); }
.catalog-table .latency-unknown { color:var(--ink-tertiary); }
.catalog-latency-note { margin:-4px 0 12px; color:var(--ink-tertiary); font:400 12px/1.7 var(--font-sans); }
.access-route-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }
.access-route { padding:14px 16px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); }
.access-route h3 { margin:0 0 8px; font-size:18px; }
.access-route code { overflow-wrap:anywhere; }
.theme-toggle { position:absolute; top:16px; right:16px; z-index:5; width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); cursor:pointer; transition:all .2s; font-size:14px; line-height:1; padding:0; }
.theme-toggle:hover { background:var(--line-soft); border-color:var(--ink-tertiary); }
.theme-toggle .icon-sun { display:none; }
.theme-toggle .icon-moon { display:inline; }
:root[data-theme="dark"] .theme-toggle .icon-sun { display:inline; }
:root[data-theme="dark"] .theme-toggle .icon-moon { display:none; }
@media (max-width:640px) { body { padding:14px 10px 40px; } header, main, footer { padding:18px; border-radius:8px; } }'''

# Compact token-only bundle for pages that keep bespoke layout CSS but need the palette
# (model center reuses the homepage document, so it must not inherit the full base styles).
EDITORIAL_TOKEN_STYLE = f'<style id="editorial-tokens">{EDITORIAL_TOKENS_CSS}</style>'

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

SKILL_CATEGORY_DEFINITIONS = {
    "product-design": {"name_zh": "产品设计", "name_en": "Product design", "accent": "blue"},
    "ecommerce": {"name_zh": "电商运营", "name_en": "E-commerce", "accent": "yellow"},
    "seo-content": {"name_zh": "SEO & 内容流量", "name_en": "SEO & content", "accent": "green"},
    "email-office": {"name_zh": "邮件与消息", "name_en": "Email & messaging", "accent": "violet"},
    "planning-office": {"name_zh": "任务与会议", "name_en": "Planning & meetings", "accent": "blue"},
    "data-office": {"name_zh": "报表与数据", "name_en": "Reports & data", "accent": "green"},
    "file-office": {"name_zh": "文件与资源", "name_en": "Files & resources", "accent": "yellow"},
    "documents": {"name_zh": "办公文档", "name_en": "Documents", "accent": "blue"},
    "presentations": {"name_zh": "PPT 幻灯片", "name_en": "Presentations", "accent": "violet"},
    "resume": {"name_zh": "简历与求职", "name_en": "Resume & jobs", "accent": "yellow"},
    "writing": {"name_zh": "写作与文案", "name_en": "Writing & copy", "accent": "green"},
    "development": {"name_zh": "开发工作流", "name_en": "Development", "accent": "blue"},
}
SKILL_REQUIRED_FIELDS = (
    "id", "name", "category", "description", "githubUrl", "cloneCommand",
    "compatibility", "status", "source", "lastCheckedAt",
)
SKILL_STATUS_LABELS = {
    "candidate": ("社区候选", "Community candidate"),
    "needs_review": ("待核验", "Needs review"),
    "verified": ("已核验", "Verified"),
}
SKILL_LINK_CHECK_VALUES = {
    "ok", "readme_only", "skill_file_not_found", "repo_not_found", "network_error", "invalid_url",
}
SKILL_RECIPE_REQUIRED_FIELDS = (
    "id", "title", "description", "input", "output", "steps",
)
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


# A single-record aggregate page adds nothing over the row already shown in
# /models/all/, so it is kept for humans but kept out of Google's index.
MIN_RECORDS_FOR_INDEXABLE_MODEL_PAGE = 2


def model_record_groups(models: list[dict]) -> dict[str, list[dict]]:
    """Group catalog rows by aggregate-page slug so one URL always equals one page.

    Provider catalogues spell the same model differently ("GLM-5.3-Flash" vs
    "glm-5.3-flash", "gpt-oss:20b" vs "gpt-oss-20b"); the slug decides the URL,
    so it must decide the grouping too, or several groups fight over one file.
    """
    groups: dict[str, list[dict]] = {}
    for model in models:
        name = str(model.get("model") or "").strip()
        if name:
            groups.setdefault(_safe_slug(name, "model"), []).append(model)
    return groups


def indexable_model_slugs(models: list[dict]) -> set[str]:
    """Aggregate-page slugs with enough provider records to earn an indexable page."""
    return {
        slug
        for slug, records in model_record_groups(models).items()
        if len(records) >= MIN_RECORDS_FOR_INDEXABLE_MODEL_PAGE
    }


MODELS_PAGE_PATH = "/models/"
ALL_MODELS_PAGE_PATH = "/models/all/"
MODEL_CENTER_PAGE_PATH = "/models/center/"
PROVIDERS_PAGE_PATH = "/providers/"
CHANGE_LOG_PAGE_PATH = "/logs/"
SKILLS_PAGE_PATH = "/skills/"
SKILL_LAB_PAGE_PATH = "/skills/lab/"

# Server-side pagination: each catalog page carries at most this many rows.
# Keeps individual HTML files small enough for fast parse/DOM build on mobile.
MODELS_PER_PAGE = 45

_MODALITY_LABELS = {"text": "文本", "reasoning": "推理", "image": "图像", "audio": "语音", "video": "视频"}


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


# 分类页是「列表落地页」，条目太少就撑不起独立的搜索意图 —— 页面上只剩一句导语、
# 两三张卡片和页脚样板文字，Google 会当成薄内容，而薄内容页再挂广告就是 AdSense
# 最忌讳的组合。2026-09-19 实测：7 个分类里健康的 5 个有 9–19 条（中文正文 1174–3021 字），
# 最薄的两个只有 2–3 条（438/455 字），中间有明显断层，所以阈值取在断层里。
# 低于阈值的分类页降级为 noindex,follow（仍可跟随链接、仍可访问），并同步移出 sitemap、
# 不再挂广告代码 —— 与模型聚合页用的是同一条规则。
MIN_OFFERS_FOR_INDEXABLE_CATEGORY = 5


def category_offer_counts(offers: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for offer in offers:
        for category in categorize_offer(offer):
            counts[category] = counts.get(category, 0) + 1
    return counts


def indexable_category_slugs(offers: list[dict]) -> set[str]:
    """Category slugs with enough verified offers to earn an indexable landing page."""
    counts = category_offer_counts(offers)
    return {
        slug
        for slug in CATEGORY_DEFINITIONS
        if counts.get(slug, 0) >= MIN_OFFERS_FOR_INDEXABLE_CATEGORY
    }


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
    return '<nav class="static-locale-nav" aria-label="Language"><button type="button" data-locale-switch="zh-CN">中文</button><span aria-hidden="true">·</span><button type="button" data-locale-switch="en">English</button></nav>'


def _hreflang_links(site_url: str, path: str) -> str:
    """Expose only non-locale alternates until languages have distinct crawlable URLs."""
    feed = _absolute(site_url, "/" + FEED_PATH)
    return f'<link rel="alternate" type="application/atom+xml" title="FreeLLM 免费 AI 资源新增" href="{_esc(feed)}">'


def _inject_hreflang_links(page: str, site_url: str, path: str) -> str:
    """Normalize hreflang metadata for every generated bilingual HTML page."""
    page = re.sub(
        r'\s*<link rel="alternate" hreflang="(?:zh-CN|en|x-default)"[^>]*>',
        "",
        page,
    )
    page = re.sub(
        r'\s*<link rel="alternate" type="application/atom\+xml" title="FreeLLM 免费 AI 资源新增"[^>]*>',
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


SEO_TITLE_MIN = 24
SEO_TITLE_MAX = 60
SEO_DESCRIPTION_MIN = 100
SEO_DESCRIPTION_MAX = 160


def _compact_seo_title(title: str) -> str:
    """Keep titles descriptive while avoiding crawler truncation warnings."""
    value = re.sub(r"\s+", " ", str(title or "")).strip()
    if len(value) > SEO_TITLE_MAX:
        primary = re.split(r"\s+[·|]\s+", value, maxsplit=1)[0].strip()
        suffix = " · FreeLLM"
        room = SEO_TITLE_MAX - len(suffix)
        if len(primary) > room:
            primary = primary[: max(1, room - 1)].rstrip(" ·|—-:：()（）") + "…"
        value = primary + suffix
    if len(value) < SEO_TITLE_MIN:
        suffix = " · 免费 AI 资源 · FreeLLM"
        if suffix not in value:
            value = value.rstrip(" ·|") + suffix
    return value[:SEO_TITLE_MAX].rstrip()


def _compact_seo_description(description: str) -> str:
    """Normalize descriptions to a useful crawl/snippet length without keyword stuffing."""
    value = re.sub(r"\s+", " ", str(description or "")).strip()
    if len(value) < SEO_DESCRIPTION_MIN:
        if re.search(r"[\u3400-\u9fff]", value):
            extra = " FreeLLM 同时标注官方来源、免费条件、地区限制、最近核验日期与可用入口，便于在使用前核对当前规则。"
        else:
            extra = " FreeLLM also records official sources, access limits, region notes and verification dates so you can confirm the current terms before relying on it."
        value = (value + extra).strip()
    if len(value) > SEO_DESCRIPTION_MAX:
        value = value[: SEO_DESCRIPTION_MAX - 1].rstrip(" ,，.;；:：|·—-") + "…"
    return value


def _normalize_seo_metadata(page: str) -> str:
    """Apply the same title/description guardrails to every generated HTML page."""
    title_match = re.search(r"<title>(.*?)</title>", page, flags=re.S | re.I)
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', page, flags=re.I)
    if title_match:
        original = html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip())
        title = _compact_seo_title(original)
        page = re.sub(r"<title>.*?</title>", f"<title>{_esc(title)}</title>", page, count=1, flags=re.S | re.I)
        page = re.sub(r'(<meta\s+property="og:title"\s+content=")[^"]*(")', lambda m: m.group(1) + _esc(title) + m.group(2), page, flags=re.I)
        page = re.sub(r'(<meta\s+name="twitter:title"\s+content=")[^"]*(")', lambda m: m.group(1) + _esc(title) + m.group(2), page, flags=re.I)
    if desc_match:
        original = html.unescape(desc_match.group(1))
        description = _compact_seo_description(original)
        page = re.sub(r'(<meta\s+name="description"\s+content=")[^"]*(")', lambda m: m.group(1) + _esc(description) + m.group(2), page, count=1, flags=re.I)
        page = re.sub(r'(<meta\s+property="og:description"\s+content=")[^"]*(")', lambda m: m.group(1) + _esc(description) + m.group(2), page, flags=re.I)
        page = re.sub(r'(<meta\s+name="twitter:description"\s+content=")[^"]*(")', lambda m: m.group(1) + _esc(description) + m.group(2), page, flags=re.I)
    return page


def _description(offer: dict) -> str:
    summary = offer.get("freeSummary") or offer.get("mechanism") or offer.get("why") or "Verified AI offer"
    return f"{offer.get('provider', offer.get('name', 'AI 资源'))}：{summary}。请以官方页面为准，核对地区、有效期和使用条件。"


def _social_meta(site_url: str, page_url: str, title: str, description: str, og_type: str, indexable: bool = True) -> str:
    """Render social metadata from the same absolute URLs used by canonical links."""
    absolute_url = _absolute(site_url, page_url)
    image_url = _absolute(site_url, SHARE_IMAGE_PATH)
    robots = "index,follow,max-image-preview:large" if indexable else "noindex,follow"
    return "\n".join(
        (
            f'<meta name="robots" content="{robots}">',
            f'<meta property="og:type" content="{_esc(og_type)}">',
            f'<meta property="og:title" content="{_esc(title)}">',
            f'<meta property="og:description" content="{_esc(description)}">',
            f'<meta property="og:url" content="{_esc(absolute_url)}">',
            f'<meta property="og:image" content="{_esc(image_url)}">',
            f'<meta property="og:image:alt" content="{_esc(title)}">',
            f'<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{_esc(title)}">',
            f'<meta name="twitter:description" content="{_esc(description)}">',
            f'<meta name="twitter:url" content="{_esc(absolute_url)}">',
            f'<meta name="twitter:image" content="{_esc(image_url)}">',
        )
    )


def _analytics_script() -> str:
    return VERCEL_ANALYTICS_SCRIPT + GA4_SCRIPT


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
        # Previously this selected models on a third-party directory's
        # "verified" flag, which asserted open-weight status we had no source
        # for. Open weights is now stated only where we classified the offer
        # ourselves, so the guide lists offers rather than catalog rows.
        return "offer", [offer for offer in offers if offer.get("productType") == "open_weights"]
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
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    body {{ max-width: 1120px; }}
    h1 {{ max-width: 900px; margin: 22px 0 10px; font-size: clamp(34px, 6vw, 58px); }}
    section + section {{ padding-top: 28px; border-top: 1px solid var(--line); }}
    footer {{ color: var(--ink-secondary); font-size: 13px; }}
  </style>
</head>
<body data-static-locale="true">
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">FreeLLM Free AI Index</a> / Guides</div>
    {_static_locale_nav()}
    <button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button>
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


def _quick_start_markup(offer: dict) -> str:
    """Render the one-stop quick-start block: register → get API key → call model.

    Each offer already carries ``register`` (signup/console URL), ``usageGuide.docsUrl``
    (docs / API-key page) and ``usageGuide.examples.curl`` (invocation example) in
    ``data/offers.json``; this surfaces them as the first thing a visitor sees instead
    of burying them inside the official-sources list.
    """
    guide = offer.get("usageGuide") or {}
    register_url = offer.get("register")
    register_label = offer.get("registerLabel") or _locale_pair("注册账号", "Sign up")
    docs_url = guide.get("docsUrl")
    curl = ((guide.get("examples") or {}).get("curl") or offer.get("command"))

    def step(number: int, title_zh: str, title_en: str, desc_zh: str, desc_en: str, body: str, wide: bool = False) -> str:
        wide_class = " qs-step-wide" if wide else ""
        return (
            f'<div class="qs-step{wide_class}">'
            f'<span class="qs-num">{number}</span>'
            f'<h3>{_locale_pair(title_zh, title_en)}</h3>'
            f'<p class="qs-desc">{_locale_pair(desc_zh, desc_en)}</p>'
            f'{body}'
            f'</div>'
        )

    # ① 注册账号
    if register_url:
        body1 = (
            f'<a class="qs-link" href="{_esc(register_url)}" target="_blank" '
            f'rel="noopener noreferrer">{_esc(register_label)} ↗</a>'
        )
    else:
        body1 = f'<p class="muted">{_locale_pair("见官方来源", "See official sources")}</p>'

    # ② 获取 API Key
    key_url = docs_url or register_url
    if key_url:
        key_label = (
            _locale_pair("查看文档 / 控制台", "Docs / console")
            if docs_url
            else _locale_pair("在同一控制台创建", "Create in the same console")
        )
        body2 = (
            f'<a class="qs-link" href="{_esc(key_url)}" target="_blank" '
            f'rel="noopener noreferrer">{key_label} ↗</a>'
        )
    else:
        body2 = f'<p class="muted">{_locale_pair("见官方来源", "See official sources")}</p>'

    # ③ 调用模型：全宽代码块 + 复制按钮
    if curl:
        body3 = (
            '<div class="qs-code">'
            f'<div class="operation-command-head"><span>{_locale_pair("可复制命令", "Copyable command")}</span>'
            f'<button type="button" class="copy-command" data-copy-target="qs-command-1">{_locale_pair("复制命令", "Copy command")}</button>'
            '</div>'
            f'<pre id="qs-command-1"><code>{_esc(curl)}</code></pre>'
            '</div>'
        )
    else:
        body3 = f'<p class="muted">{_locale_pair("见下方操作步骤", "See the operation steps below")}</p>'

    steps = "".join(
        (
            step(1, "注册账号", "Sign up", "打开官方平台完成注册；部分平台需要手机号或邮箱验证。", "Create an account on the official platform; phone or email verification may apply.", body1),
            step(2, "获取 API Key", "Get API key", "在控制台的 API Keys 页面创建密钥并妥善保存。", "Create a key on the console's API keys page and store it safely.", body2),
            step(3, "调用模型", "Call model", "把命令中的环境变量换成你的 Key，即可发送第一条请求。", "Swap in your key via the environment variable and send the first request.", body3, wide=True),
        )
    )

    qs_desc_zh = "注册 → 拿 Key → 调用模型，三步放在最前面；免费条件仍以官方页面实时状态为准。"
    qs_desc_en = "Register, get your API key, then call the model; free terms still follow the provider's live official policy."
    copy_script = (
        "<script>(() => { document.querySelectorAll('.quick-start .copy-command')"
        ".forEach(button => button.addEventListener('click', async () => {"
        " const target = document.getElementById(button.dataset.copyTarget);"
        " if (!target) return;"
        " await navigator.clipboard.writeText(target.innerText);"
        f" button.textContent = {json.dumps('已复制', ensure_ascii=False)};"
        f" setTimeout(() => button.textContent = {json.dumps('复制命令', ensure_ascii=False)}, 1400);"
        " })); })();</script>"
    )
    return (
        '<section class="quick-start">\n'
        '      <h2>' + _locale_pair("快速上手", "Quick start") + '</h2>\n'
        '      <p class="muted">' + _locale_pair(qs_desc_zh, qs_desc_en) + '</p>\n'
        '      <div class="qs-grid">' + steps + '</div>\n'
        '      ' + copy_script + '\n'
        '    </section>'
    )


def _source_links(offer: dict) -> str:
    labeled_links = []
    for link in offer.get("links") or []:
        if isinstance(link, list) and len(link) == 2 and link[0] and link[1]:
            labeled_links.append((str(link[0]), str(link[1])))
    for entry in offer.get("freeModels") or []:
        if isinstance(entry, dict) and entry.get("model") and entry.get("sourceUrl"):
            labeled_links.append((str(entry["model"]), str(entry["sourceUrl"])))
    if labeled_links:
        by_url: dict[str, str] = {}
        for label, url in labeled_links:
            by_url.setdefault(url, label)
        return "".join(
            f'<li><a href="{_esc(url)}" rel="nofollow noopener" target="_blank">{_locale_pair(label, label, "Official source")} ↗</a></li>'
            for url, label in by_url.items()
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


def _repeats_reference_command(command: str, reference_command: str) -> bool:
    """True when a step command merely restates the quick-start command (same endpoint)."""
    if not reference_command:
        return False
    match = re.search(r"https?://[^\s'\"]+", str(reference_command))
    if not match:
        return False
    return match.group(0) in str(command)


def _operation_guides_markup(guides: list[dict], reference_command: str = "") -> str:
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
                if command and _repeats_reference_command(command, reference_command):
                    # 快速上手已展示同一 endpoint 的可复制命令，这里只留指引避免整页重复。
                    command_markup = f'<p class="muted">{_locale_pair("命令已在上方「快速上手」给出。", "The copyable command already appears in Quick start above.")}</p>'
                elif command:
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
    return f'''<section id="operation-guides"><h2>{_locale_pair("详细操作步骤", "Detailed operation paths")}</h2><p class="muted">{_locale_pair("每条路径都拆成前置条件、步骤、可复制命令和验证动作；免费条件仍以官方页面实时状态为准。", "Each path includes prerequisites, steps, copyable commands and a validation action; free terms still follow the provider's live official policy.")}</p>{"".join(rendered_guides)}<script>(() => {{ document.querySelectorAll('.operation-path .copy-command').forEach(button => button.addEventListener('click', async () => {{ const target = document.getElementById(button.dataset.copyTarget); if (!target) return; await navigator.clipboard.writeText(target.innerText); button.textContent = {json.dumps('已复制', ensure_ascii=False)}; setTimeout(() => button.textContent = {json.dumps('复制命令', ensure_ascii=False)}, 1400); }})); }})();</script></section>'''


def render_legacy_offer_redirect(legacy_id: str, target_id: str, site_url: str) -> str:
    target_path = f"/offers/{target_id}/"
    target_url = _absolute(site_url, target_path)
    title = "页面已合并 · FreeLLM"
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><link rel="canonical" href="{_esc(target_url)}"><meta http-equiv="refresh" content="0; url={_esc(target_url)}"></head>
<body><main><h1>页面已合并</h1><p>旧入口 <code>{_esc(legacy_id)}</code> 已合并到 LongCat-2.0 统一详情页。</p><p><a href="{_esc(target_url)}">继续查看 LongCat-2.0 详情 →</a></p></main></body></html>'''
    page = page.replace(
        '<link rel="canonical" href="' + _esc(target_url) + '">',
        '<meta name="robots" content="noindex,follow"><link rel="canonical" href="' + _esc(target_url) + '">',
        1,
    )
    return page


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


EDITION_LABELS = {"cn": ("国内版", "China edition"), "intl": ("国际版", "International edition")}


def _edition_chip(offer: dict) -> str:
    """Which edition this entry is; products serving both entries through one page say so."""
    edition_of = offer.get("editionOf")
    if edition_of in EDITION_LABELS:
        zh, en = EDITION_LABELS[edition_of]
        return zh, en, f'<span class="flag-chip flag-edition">{_locale_pair(zh, en)}</span>'
    editions = offer.get("editions") or []
    if "cn" in editions and "intl" in editions:
        return "国内+国际双入口", "China + intl editions", '<span class="flag-chip flag-edition">{}</span>'.format(_locale_pair("国内+国际双入口", "China + intl editions"))
    if "cn" in editions:
        zh, en = EDITION_LABELS["cn"]
        return zh, en, f'<span class="flag-chip flag-edition">{_locale_pair(zh, en)}</span>'
    if "intl" in editions:
        zh, en = EDITION_LABELS["intl"]
        return zh, en, f'<span class="flag-chip flag-edition">{_locale_pair(zh, en)}</span>'
    return "", "", ""


NETWORK_REGION_LABELS = {
    "both": ("国内外均可用", "China + global"),
    "cn": ("仅国内可用", "China only"),
    "intl": ("仅国外可用", "Global only"),
}
NETWORK_METHOD = "本机大陆网络直连 + check-host.net 海外节点（US×2 / DE / SG / JP / UK）"
NETWORK_NOTE = "仅实测网络可达性与往返延迟，不代表注册门槛或模型生成速度"


def _network_chips(offer: dict) -> str:
    """绿色实测标签：网络可达性 + 国内/国外分类 + 往返延迟。

    数据来自 scripts/probe_offer_network.py 的双视角实测（大陆直连 +
    check-host.net 海外节点）。只描述网络层，不描述注册门槛或模型生成速度。
    """
    check = offer.get("networkCheck")
    if not isinstance(check, dict):
        return ""
    region = check.get("region")
    dead = [str(url) for url in (check.get("deadTargets") or [])]
    dead_chip = (
        f'<span class="flag-chip flag-net-dead" title="{_esc(" ; ".join(dead))}">'
        f'{_locale_pair(f"⚠ {len(dead)} 个链接解析失败", f"⚠ {len(dead)} broken link(s)")}</span>'
        if dead else ""
    )
    if region == "none":
        return f'<span class="flag-chip flag-net-fail">{_locale_pair("✗ 本次未连通", "✗ Not reachable")}</span>' + dead_chip
    if region not in NETWORK_REGION_LABELS:
        return dead_chip
    zh, en = NETWORK_REGION_LABELS[region]
    speed = ""
    if check.get("cnMs") or check.get("intlMs"):
        cn_ms = f"{check['cnMs']}ms" if check.get("cnMs") else "—"
        intl_ms = f"{check['intlMs']}ms" if check.get("intlMs") else "—"
        speed = _locale_pair(f"国内 {cn_ms} · 海外 {intl_ms}", f"China {cn_ms} · Global {intl_ms}")
    title = " · ".join(
        part for part in (
            str(check.get("checkedAt") or ""),
            NETWORK_METHOD,
            check.get("cnHost") or "",
            NETWORK_NOTE,
        ) if part
    )
    chips = [
        f'<span class="flag-chip flag-net-ok" title="{_esc(title)}">{_locale_pair("✓ 实测通过", "✓ Network verified")}</span>',
        f'<span class="flag-chip flag-net-region">{_locale_pair(zh, en)}</span>',
    ]
    if speed:
        chips.append(f'<span class="flag-chip flag-net-speed">{speed}</span>')
    if dead_chip:
        chips.append(dead_chip)
    return "".join(chips)


FEATURED_CHIP_LABEL = ("◆ 加精", "◆ Featured")
FEATURED_NOTE = (
    "「加精」= 接口实测速度达标（大陆直连中位数 ≤ 400ms）且免费额度高（官方长期免费，或有大额免费额度）。"
    "把鼠标停在标签上可以看到这一条的具体理由和实测数字。",
    "“Featured” means the measured API round trip from mainland China is within 400 ms and the free quota is high "
    "(permanently free, or a large stated allowance). Hover the tag to see the exact evidence.",
)


def _featured_chip(offer: dict) -> str:
    """加精标签：速度与额度两条证据都由 scripts/mark_featured_offers.py 从实测数据算出。"""
    featured = offer.get("featured")
    if not isinstance(featured, dict):
        return ""
    reason = str(featured.get("reason") or "").strip()
    reason_en = str(featured.get("reasonEn") or "").strip()
    if not reason and not reason_en:
        return ""
    title = "｜".join(part for part in (f"加精于 {featured.get('since')}", reason, reason_en) if part)
    return (
        f'<span class="flag-chip flag-featured" title="{_esc(title)}">'
        f'{_locale_pair(*FEATURED_CHIP_LABEL)}</span>'
    )


def _offer_freellm_test_markup(offer: dict) -> str:
    test = offer.get("freeLLMTest")
    if not isinstance(test, dict):
        return ""
    level = str(test.get("testLevel") or "")
    status = str(test.get("status") or "")
    actual = test.get("actualUsageVerified") is True
    if actual and status == "passed":
        state_zh, state_en, state_class = "登录态实测通过", "Hands-on test passed", "verified"
    elif level == "preflight" and status in {"passed", "partial"}:
        state_zh, state_en, state_class = "预检通过 · 登录态实测待补", "Preflight passed · signed-in test pending", "partial"
    elif status == "blocked":
        state_zh, state_en, state_class = "测试受阻", "Test blocked", "blocked"
    else:
        state_zh, state_en, state_class = "部分验证", "Partially verified", "partial"

    methods = "".join(f"<li>{_esc(item)}</li>" for item in (test.get("method") or []))
    evidence = "".join(
        f'<li><a href="{_esc(item.get("url"))}" target="_blank" rel="nofollow noopener">{_esc(item.get("label"))} ↗</a>'
        + (f'<small>{_esc(item.get("note"))}</small>' if item.get("note") else "") + "</li>"
        for item in (test.get("evidence") or []) if isinstance(item, dict) and item.get("url")
    )
    return f'''<section class="freellm-offer-test">
      <div class="freellm-offer-test-head"><div><span class="eyebrow">FreeLLM TEST</span><h2>{_locale_pair("FreeLLM 自测", "FreeLLM test")}</h2></div><span class="freellm-test-state {state_class}">{_locale_pair(state_zh, state_en)}</span></div>
      <div class="facts">
        <div class="fact"><strong>{_locale_pair("测试时间", "Tested at")}</strong><span>{_esc(test.get("testedAt"))}</span></div>
        <div class="fact"><strong>{_locale_pair("测试级别", "Test level")}</strong><span>{_esc(level)}</span></div>
        <div class="fact"><strong>{_locale_pair("真实登录使用", "Signed-in usage")}</strong><span>{_locale_pair("已验证" if actual else "未验证", "Verified" if actual else "Not verified")}</span></div>
      </div>
      <h3>{_locale_pair("我们测了什么", "What we tested")}</h3>
      <p>{_esc(test.get("task"))}</p>
      <ol class="steps">{methods}</ol>
      <h3>{_locale_pair("测试结果", "Result")}</h3>
      <p>{_esc(test.get("result"))}</p>
      <div class="callout"><strong>{_locale_pair("未验证 / 限制：", "Not verified / limits:")}</strong> {_esc(test.get("limitations"))}</div>
      {f'<h3>{_locale_pair("测试证据", "Test evidence")}</h3><ul class="link-list">{evidence}</ul>' if evidence else ""}
    </section>'''


def _offer_freellm_test_chip(offer: dict) -> str:
    test = offer.get("freeLLMTest")
    if not isinstance(test, dict) or not test.get("testedAt"):
        return ""
    if test.get("actualUsageVerified") is True and test.get("status") == "passed":
        label = _locale_pair("✓ FreeLLM 实测", "✓ FreeLLM hands-on")
        cls = "flag-hands-on"
    elif test.get("testLevel") == "preflight":
        label = _locale_pair("△ FreeLLM 预检", "△ FreeLLM preflight")
        cls = "flag-test-preflight"
    else:
        label = _locale_pair("△ FreeLLM 部分验证", "△ FreeLLM partial")
        cls = "flag-test-preflight"
    return f'<span class="flag-chip {cls}" title="{_esc(str(test.get("testedAt")))}">{label}</span>'


def _offer_version_line(offer: dict, offers: list[dict]) -> str:
    """版本标记行：加精 / 重点 / 网络实测 / 国内或国际版本 / 双版本互链 / 实测好用。"""
    chips = []
    featured_chip = _featured_chip(offer)
    if featured_chip:
        chips.append(featured_chip)
    if offer.get("key"):
        chips.append(f'<span class="flag-chip flag-key">{_locale_pair("★ 重点", "★ Key pick")}</span>')
    freellm_test_chip = _offer_freellm_test_chip(offer)
    if freellm_test_chip:
        chips.append(freellm_test_chip)
    network_chip = _network_chips(offer)
    if network_chip:
        chips.append(network_chip)
    _, _, edition_chip = _edition_chip(offer)
    if edition_chip:
        chips.append(edition_chip)
    sibling_id = offer.get("siblingEditionId")
    if sibling_id:
        sibling = next((candidate for candidate in offers if candidate.get("id") == sibling_id), None)
        if sibling is not None:
            sibling_title = sibling.get("titleZh") or sibling.get("title") or sibling.get("name")
            label = _locale_pair(
                f"同产品另一版本：{sibling_title}",
                f"Other edition: {sibling.get('title') or sibling.get('name')}",
            )
            chips.append(f'<a class="flag-chip flag-sibling" href="{_esc(offer_url(sibling))}">{label} ↗</a>')
    hands_on = offer.get("handsOn")
    if isinstance(hands_on, dict) and hands_on.get("testedAt"):
        note = str(hands_on.get("note") or "").strip()
        title_markup = f' title="{_esc(hands_on["testedAt"] + (" · " + note if note else ""))}"' if note else ""
        chips.append(
            f'<span class="flag-chip flag-hands-on"{title_markup}>{_locale_pair("✓ 实测好用", "✓ Hands-on verified")}</span>'
        )
    else:
        endpoint_check = offer.get("endpointCheck")
        if isinstance(endpoint_check, dict) and endpoint_check.get("checkedAt") and endpoint_check.get("verdict") != "NETWORK_ERROR":
            note = str(endpoint_check.get("note") or "").strip()
            ms = endpoint_check.get("ms")
            latency = f"{int(ms)}ms" if isinstance(ms, int) else ""
            endpoint = str((offer.get("usageGuide") or {}).get("endpoint") or "").strip()
            method = str((offer.get("usageGuide") or {}).get("method") or "GET").strip().upper() or "GET"
            title = " · ".join(
                part for part in (
                    str(endpoint_check["checkedAt"]),
                    note,
                    f"{method} {endpoint}" if endpoint else "",
                    f"调用耗时 {latency}（本机大陆实测，3 次中位数）" if latency else "",
                ) if part
            )
            label_zh, label_en = ("接口已验证", "Endpoint verified") if offer.get("usageGuide", {}).get("endpoint") else ("官网已验证", "Site verified")
            suffix = f" · {latency}" if latency else ""
            chips.append(
                f'<span class="flag-chip flag-endpoint" title="{_esc(title)}">'
                f'{_locale_pair(f"✓ {label_zh}{suffix}", f"✓ {label_en}{suffix}")}</span>'
            )
    if not chips:
        return ""
    return '<div class="offer-version-line">' + "".join(chips) + "</div>"


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
    cta_parts = []
    if offer.get("register"):
        reg_small = f'<small>{_esc(offer.get("registerLabel"))}</small>' if offer.get("registerLabel") else ""
        cta_parts.append(
            f'<a class="button" href="{_esc(offer.get("register"))}" target="_blank" rel="nofollow noopener">'
            f'<span>{_locale_pair("立即开始", "Get started")} ↗</span>{reg_small}</a>'
        )
    if guide.get("docsUrl"):
        cta_parts.append(
            f'<a class="button button--ghost" href="{_esc(guide.get("docsUrl"))}" target="_blank" rel="nofollow noopener">'
            f'<span>{_locale_pair("官方文档", "Documentation")} ↗</span></a>'
        )
    header_cta_markup = (
        '<nav class="header-cta" aria-label="Official links">' + "".join(cta_parts) + "</nav>"
    ) if cta_parts else ""
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
    version_line = _offer_version_line(offer, offers)
    freellm_test_markup = _offer_freellm_test_markup(offer)
    featured = offer.get("featured")
    if isinstance(featured, dict) and featured.get("reason"):
        featured_reason_zh = f"◆ 加精理由：{featured['reason']}"
        featured_reason_en = f"◆ Why featured: {featured.get('reasonEn') or featured['reason']}"
        featured_note_markup = f'<p class="featured-note">{_locale_pair(featured_reason_zh, featured_reason_en)}</p>'
    else:
        featured_note_markup = ""
    operation_guides_markup = _operation_guides_markup(
        _operation_guides_for_offer(offer, operations or []),
        reference_command=((guide.get("examples") or {}).get("curl") or offer.get("command") or ""),
    )
    if operation_guides_markup:
        # 操作路径已覆盖前置条件/步骤/命令，再渲染"如何使用"只会重复内容。
        how_to_section = ""
    else:
        how_to_section = f'''<section>
      <h2>{_locale_pair("如何使用", "How to use")}</h2>
      <p>{_locale_pair(guide.get('summary') or offer.get('command'), _english_text(guide.get('summary') or offer.get('command'), "See the official setup guide"))}</p>
      <h3>{_locale_pair("前置条件", "Prerequisites")}</h3>
      {_list(guide.get('prerequisites') or [offer.get('access')], '请查看官方访问要求。')}
      <h3>{_locale_pair("步骤", "Steps")}</h3>
      {_list(guide.get('steps') or [offer.get('command')], '请按照官方设置说明操作。')}
    </section>'''
    free_models = offer.get("freeModels") or []
    free_models_markup = ""
    if free_models:
        show_context = any(entry.get("contextWindow") for entry in free_models)

        def _model_row(entry: dict) -> str:
            name_cell = (
                f'<td><code>{_locale_pair(entry.get("model"), entry.get("model"), "Listed model")}</code>'
                + (
                    f'<br><small class="muted">{_locale_pair(entry["label"], entry["label"], "Model label")}</small>'
                    if entry.get("label")
                    else ""
                )
                + "</td>"
            )
            context_cell = (
                f'<td>{_locale_pair(entry.get("contextWindow") or "—", entry.get("contextWindow") or "—", "See model limits")}</td>'
                if show_context
                else ""
            )
            quota_cell = f'<td>{_locale_pair(entry.get("quota") or "—", entry.get("quota") or "—", "See quota terms")}</td>'
            note_cell = f'<td>{_locale_pair(entry.get("note") or "—", entry.get("note") or "—", "See official terms")}</td>'
            return f"<tr>{name_cell}{context_cell}{quota_cell}{note_cell}</tr>"

        head_cells = f'<th>{_locale_pair("模型", "Model")}</th>'
        if show_context:
            head_cells += f'<th>{_locale_pair("上下文窗口", "Context window")}</th>'
        head_cells += f'<th>{_locale_pair("免费额度", "Free quota")}</th><th>{_locale_pair("备注", "Notes")}</th>'
        rows = "".join(_model_row(entry) for entry in free_models)
        free_models_markup = f'''<section>
      <h2>{_locale_pair("免费模型逐个看", "Free models by entry")}</h2>
      <div class="table-wrap"><table><thead><tr>{head_cells}</tr></thead><tbody>{rows}</tbody></table></div>
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
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    body {{ max-width: 980px; }}
    h1 {{ font-size: clamp(30px, 5vw, 44px); }}
    header {{ padding-bottom: 26px; }}
    header nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    main section + section {{ margin-top: 26px; padding-top: 24px; border-top: 1px solid var(--line); }}
    main h2 {{ font-size: clamp(22px, 3.4vw, 30px); }}
    main h3 {{ font-size: 18px; }}
    .operation-path {{ margin-top: 24px; padding: 20px 22px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); }}
    .operation-path h3 {{ margin-top: 0; }}
    .operation-path h4 {{ margin: 18px 0 6px; }}
    .operation-type {{ display: inline-block; margin: 0; padding: 3px 10px; border-radius: 9999px; color: var(--accent); background: var(--accent-soft); font: 500 11px/1.6 var(--font-mono); letter-spacing: .04em; }}
    .operation-steps {{ padding-left: 1.4em; }}
    .operation-steps li {{ margin: 12px 0; }}
    .operation-steps p {{ margin: 4px 0; }}
    .operation-command {{ margin: 10px 0; }}
    .operation-command-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; color: var(--ink-secondary); font: 500 11px/1.6 var(--font-mono); letter-spacing: .05em; }}
    .copy-command {{ border: 1px solid var(--line); border-radius: 6px; padding: 5px 11px; color: var(--accent); background: var(--surface); cursor: pointer; font-size: 12px; transition: all .15s; }}
    .copy-command:hover {{ border-color: var(--accent); }}
    .operation-facts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin: 14px 0; }}
    .operation-facts div {{ padding: 11px 13px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }}
    .operation-facts dt {{ color: var(--ink-tertiary); font: 500 10.5px/1.6 var(--font-mono); text-transform: uppercase; letter-spacing: .07em; }}
    .operation-facts dd {{ margin: 3px 0 0; overflow-wrap: anywhere; font-size: 13.5px; }}
    .operation-validation {{ margin-top: 18px; padding: 12px 16px; border-left: 3px solid var(--pale-green-text); border-radius: 0 6px 6px 0; background: var(--pale-green-bg); color: var(--pale-green-text); }}
.operation-limits, .operation-issues {{ margin-top: 14px; padding: 12px 16px; border-radius: 8px; background: var(--surface-soft); }}
        .operation-limits p, .operation-issues ul {{ margin: 4px 0 0; }}
    .quick-start {{ margin: 26px 0 0; }}
    .qs-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .qs-step {{ display: flex; flex-direction: column; gap: 8px; padding: 18px 20px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }}
    .qs-step-wide {{ grid-column: 1 / -1; }}
    .qs-num {{ display: inline-block; width: 26px; height: 26px; line-height: 26px; text-align: center; border-radius: 50%; color: var(--ink-solid-contrast); background: var(--ink-solid); font: 500 12px/1 var(--font-mono); flex-shrink: 0; }}
    .qs-step h3 {{ margin: 0; font-size: 18px; }}
    .qs-desc {{ margin: 0; color: var(--ink-secondary); font-size: 13.5px; }}
    .qs-link {{ display: inline-block; color: var(--accent); text-decoration: none; font-weight: 500; word-break: break-all; }}
    .qs-link:hover {{ text-decoration: underline; }}
    .qs-code {{ display: flex; flex-direction: column; gap: 6px; margin-top: 2px; }}
    .qs-step pre {{ margin: 0; padding: 12px 14px; border-radius: 6px; background: var(--code-bg); color: var(--code-text); font: 400 12px/1.55 var(--font-mono); overflow-x: auto; max-width: 100%; }}
    .header-cta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .offer-version-line {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    .flag-chip {{ display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 9999px; font: 500 11px/1.6 var(--font-mono); letter-spacing: .04em; text-decoration: none; }}
    .flag-key {{ color: var(--ink); background: var(--surface-soft); border: 1px solid var(--line); }}
    .featured-note {{ margin: 10px 0 0; padding: 10px 14px; border-left: 3px solid var(--pale-yellow-text); border-radius: 0 6px 6px 0; background: var(--pale-yellow-bg); color: var(--pale-yellow-text); font-size: 13.5px; }}
    .flag-edition {{ color: var(--accent); background: var(--accent-soft); }}
    .flag-sibling {{ color: var(--accent); background: var(--surface); border: 1px solid var(--line); }}
    .flag-sibling:hover {{ border-color: var(--accent); }}
    .flag-hands-on {{ color: var(--pale-green-text); background: var(--pale-green-bg); }}
    .flag-test-preflight {{ color: var(--pale-yellow-text); background: var(--pale-yellow-bg); border: 1px solid var(--pale-yellow-text); }}
    .freellm-offer-test {{ border-top: 3px solid var(--accent) !important; }}
    .freellm-offer-test-head {{ display:flex; gap:16px; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; }}
    .freellm-offer-test-head h2 {{ margin-top:4px; }}
    .freellm-test-state {{ display:inline-flex; padding:5px 10px; border-radius:9999px; font:500 11px/1.5 var(--font-mono); }}
    .freellm-test-state.verified {{ color:var(--pale-green-text); background:var(--pale-green-bg); }}
    .freellm-test-state.partial {{ color:var(--pale-yellow-text); background:var(--pale-yellow-bg); }}
    .freellm-test-state.blocked {{ color:var(--pale-red-text); background:var(--pale-red-bg); }}
    .flag-endpoint {{ color: var(--pale-green-text); background: var(--surface); border: 1px solid var(--pale-green-text); }}
    .flag-net-ok {{ color: var(--pale-green-text); background: var(--pale-green-bg); border: 1px solid var(--pale-green-text); }}
    .flag-net-region {{ color: var(--pale-green-text); background: var(--pale-green-bg); }}
    .flag-net-speed {{ color: var(--ink-secondary); background: var(--surface); border: 1px solid var(--line); }}
    .flag-net-fail {{ color: var(--pale-red-text); background: var(--pale-red-bg); }}
    .flag-net-dead {{ color: var(--pale-yellow-text); background: var(--pale-yellow-bg); }}
    .header-cta .button {{ display: inline-flex; flex-direction: column; align-items: flex-start; gap: 2px; padding: 10px 16px; }}
    .header-cta .button small {{ font-weight: 400; opacity: .75; font-size: 11px; }}
    .header-cta .button--ghost {{ background: transparent; color: var(--ink); border-color: var(--line); }}
    .header-cta .button--ghost:hover {{ background: var(--surface-soft); border-color: var(--ink-tertiary); color: var(--ink); }}
    @media (max-width: 680px) {{ .qs-grid {{ grid-template-columns: 1fr; }} }}
        footer {{ color: var(--ink-secondary); font-size: 13.5px; }}
  </style>
</head>
<body data-offer-id="{_esc(offer.get('id'))}" data-static-locale="true">
{_adsense_slot_markup()}
  <header>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair("FreeLLM 免费 AI 资源索引", "FreeLLM Free AI Index")}</a> / {_locale_pair("资源详情", "Offer details")}</p>
    {_static_locale_nav()}
    <button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button>
    <h1>{_locale_pair(offer.get("titleZh") or title, title, "Offer details")}</h1>
    <p>{_locale_pair(offer.get("providerMeta") or offer.get("provider"), offer.get("providerMetaEn") or offer.get("provider"), "Official provider")}</p>
    {version_line}
    {featured_note_markup}
    <nav aria-label="Categories">{category_links}</nav>
    {header_cta_markup}
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
{_quick_start_markup(offer)}
{context_window_markup}
{access_paths_markup}
{operation_guides_markup}
{free_models_markup}
{how_to_section}
{freellm_test_markup}
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
    # 条目不足的分类页是薄页：既然主动 noindex，就不再挂广告代码（同模型聚合页的规则）。
    indexable = len(matching) >= MIN_OFFERS_FOR_INDEXABLE_CATEGORY
    social_meta = _social_meta(site_url, path, title, description, "website", indexable=indexable)
    items = "".join(
        f'''<article>
          <h2><a href="{_esc(offer_url(offer))}">{_locale_pair(offer.get("titleZh") or offer.get("title") or offer.get("name"), offer.get("title") or offer.get("name"), "Offer details")}</a>{_featured_chip(offer)}</h2>
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
  {ADSENSE_SCRIPT if indexable else ""}
  {STATIC_LOCALE_STYLE}
  {STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    body {{ max-width: 980px; }}
    h1 {{ font-size: clamp(30px, 5vw, 44px); }}
    main {{ padding-top: 6px; }}
    article {{ padding: 18px 0; border-bottom: 1px solid var(--line-soft); }}
    article:last-child {{ border-bottom: 0; padding-bottom: 6px; }}
    article h2 {{ margin: 0 0 6px; font-size: 21px; }}
    article h2 .flag-featured {{ margin-left: 8px; vertical-align: middle; font-size: 11px; }}
    article h2 a {{ color: var(--ink); text-decoration: none; }}
    article h2 a:hover {{ color: var(--accent); }}
    article p {{ margin: 0 0 4px; font-size: 14px; color: var(--ink-secondary); }}
    footer {{ color: var(--ink-secondary); font-size: 13.5px; }}
  </style>
</head>
<body data-static-locale="true">
  <header>
    <p><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair('FreeLLM 免费 AI 资源索引', 'FreeLLM Free AI Index')}</a> / {_locale_pair('分类', 'Category')}</p>
    {_static_locale_nav()}
    <button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button>
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
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    h1 {{ max-width: 760px; margin: 22px 0 8px; font-size: clamp(34px, 6vw, 58px); }}
    header p {{ max-width: 780px; margin: 8px 0; }}
    .source {{ display: flex; flex-wrap: wrap; gap: 10px 18px; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line); font-size: 13px; color: var(--ink-secondary); }}
    main {{ display: grid; gap: 28px; }}
    section + section {{ padding-top: 26px; border-top: 1px solid var(--line); }}
    h2 {{ font-size: clamp(24px, 4vw, 32px); }}
    h3 {{ font-size: 20px; }}
    .meta {{ color: var(--ink-secondary); font-size: 13px; }}
    footer {{ color: var(--ink-secondary); font-size: 13px; }}
    footer strong {{ color: var(--ink); }}
    @media (max-width: 620px) {{ h1 {{ font-size: 40px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / 使用指南</div>
    <button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button>
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
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    h1 {{ max-width: 820px; margin: 22px 0 10px; font-size: clamp(34px, 6vw, 58px); }}
    section + section {{ padding-top: 28px; border-top: 1px solid var(--line); }}
    h2 {{ font-size: clamp(24px, 4vw, 32px); }}
    h3 {{ font-size: 19px; }}
    footer {{ color: var(--ink-secondary); font-size: 13px; }}
  </style>
</head>
<body>
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / Guides</div>
    <button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button>
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


ENDPOINT_LATENCY_FILE = "endpoint-latency.json"
LATENCY_COLUMN_LABEL = ("接口速度 (API RTT)", "API latency")
LATENCY_NOTE = (
    "「接口速度」为本机大陆直连实测的服务商 API 网关往返延迟（3 次中位数），只反映接口调用快慢，不代表模型生成速度。",
    "API latency is the mainland-China round trip to each provider's API gateway (median of 3 keyless probes). It measures the interface, not model generation speed.",
)


def _load_endpoint_latency() -> tuple[dict[str, dict], dict]:
    """Per-provider API-gateway latency measured by scripts/probe_endpoint_latency.py.

    The file is written by a real probe run, never by hand: every entry carries
    its own check date, endpoint and samples so the column can be audited.
    """
    path = ACCESS_DATA_DIR / ENDPOINT_LATENCY_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Invalid endpoint latency data ({path}): {error}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("providers"), list):
        raise SystemExit(f"Invalid endpoint latency data ({path}): expected an object with a providers array")
    entries: dict[str, dict] = {}
    for entry in payload["providers"]:
        if not isinstance(entry, dict) or not entry.get("providerId"):
            raise SystemExit(f"Invalid endpoint latency entry in {path}: {entry!r}")
        entries[str(entry["providerId"])] = entry
    meta = {
        "checkedAt": str(payload.get("checkedAt") or ""),
        "vantage": str(payload.get("vantage") or ""),
        "method": str(payload.get("method") or ""),
    }
    return entries, meta


def _latency_cell(model: dict, latencies: dict[str, dict], meta: dict) -> tuple[str, str]:
    """Markup plus the sortable value for one model row's API-latency cell."""
    entry = latencies.get(str(model.get("providerId") or "")) or {}
    ms = entry.get("ms")
    title_parts = [
        f"实测于 {entry['checkedAt']}" if entry.get("checkedAt") else "",
        f"GET {entry['endpoint']}" if entry.get("endpoint") else "",
        "3 次成功请求的中位数" if ms is not None else "",
        meta.get("vantage") or "",
        str(entry.get("note") or ""),
    ]
    title = _esc(" · ".join(part for part in title_parts if part))
    if ms is None:
        return f'<td class="latency-cell latency-unknown" data-label="接口速度" title="{title}">—</td>', ""
    return (
        f'<td class="latency-cell" data-label="接口速度" title="{title}"><span class="latency-value">{int(ms)}ms</span></td>',
        str(int(ms)),
    )


def _format_context_window(value: object) -> str:
    """Render raw token counts like 256000 as 256K / 1M; pass through anything else."""
    raw = str(value or "").strip()
    if not raw.isdigit():
        return raw or "—"
    count = int(raw)
    if count >= 1_000_000:
        return f"{count / 1_000_000:g}M"
    if count >= 1_000:
        return f"{round(count / 1_000):g}K"
    return raw


def _model_catalog_row(
    model: dict,
    cn_statuses: dict[str, dict] | None = None,
    row_number: int = 0,
    latencies: dict[str, dict] | None = None,
    latency_meta: dict | None = None,
    linkable_model_slugs: set[str] | None = None,
) -> str:
    modalities = "".join(
        f'<span class="model-badge">{_esc(item)}</span>'
        for item in (model.get("modality") or [])
        if str(item).lower() != "unknown"
    )
    modality_key = ",".join(sorted(str(item) for item in (model.get("modality") or [])))
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
    provider_name = str(model.get("provider") or "")
    model_id = str(model.get("id") or "")
    model_name = str(model.get("model") or "")
    context_text = _format_context_window(model.get("context"))
    cn = (cn_statuses or {}).get(model_id) or (cn_statuses or {}).get(provider_id) or {"code": "unknown", "zh": _CN_STATUS_LABELS["unknown"][0], "en": _CN_STATUS_LABELS["unknown"][1]}
    latency_cell, latency_ms = _latency_cell(model, latencies or {}, latency_meta or {})
    linkable = linkable_model_slugs is None or _safe_slug(model_name, "model") in linkable_model_slugs
    model_name_markup = (
        f'<a class="model-name" href="{_esc(model_aggregate_url(model))}" title="{_esc(model_name)}"><strong>{_esc(model_name)}</strong></a>'
        if linkable else
        f'<span class="model-name model-name-static" title="{_esc(model_name)}"><strong>{_esc(model_name)}</strong></span>'
    )
    card_model_markup = (
        f'<a href="{_esc(model_aggregate_url(model))}">{_esc(model_name)}</a>'
        if linkable else
        f'<span>{_esc(model_name)}</span>'
    )
    card_facts = "".join(
        f'<span class="model-card-fact"><small>{label}</small>{value}</span>'
        for label, value in (
            (_locale_pair("上下文", "Context"), _esc(context_text)),
            (_locale_pair("速率", "Rate"), _esc(model.get("rateLimit") or "—")),
            (_locale_pair("接口", "API"), f"{_esc(latency_ms)}ms" if latency_ms else "—"),
            (_locale_pair("发布", "Released"), _esc(model.get("released") or "—")),
        )
    )
    return f'''<tr class="catalog-row" data-model-id="{_esc(model_id)}" data-provider-id="{_esc(provider_id)}" data-cn="{_esc(cn["code"])}" data-modality="{_esc(modality_key)}" data-context="{_esc(str(model.get("context") or ""))}" data-released="{_esc(str(model.get("released") or ""))}" data-ms="{_esc(latency_ms)}" data-score="{_esc(str(model.get("score") or ""))}">
      <td class="row-index" data-label="#">{row_number or "—"}</td>
      <td class="model-cell" data-label="模型">{model_name_markup}<small class="model-id" title="{_esc(model_id)}">{_esc(model_id)}</small></td>
      <td class="provider-cell" data-label="服务商"><button class="provider-filter" type="button" data-provider-value="{_esc(provider_id)}">{_esc(provider_name)}</button><a class="provider-page-link" href="{_esc(provider_url(provider_id))}">{_locale_pair("详情", "Details")}</a></td>
      <td data-label="上下文长度" title="{_esc(str(model.get("context") or ""))}">{_esc(context_text)}</td>
      <td data-label="最大输出">{_esc(_format_context_window(model.get("maxOutput")) if str(model.get("maxOutput") or "").isdigit() else (model.get("maxOutput") or "—"))}</td>
      <td data-label="支持模态"><div class="model-badges">{modalities or '<span class="muted">—</span>'}</div></td>
      <td data-label="速率限制">{_esc(model.get("rateLimit") or "—")}</td>
      {latency_cell}
      <td data-label="发布时间">{_esc(model.get("released") or "—")}</td>
      <td data-label="在线状态"><span class="status-dot status-dot-{_esc(status)}"></span><span class="status status-{_esc(status)}">{status_label}</span>{freshness_markup}</td>
      <td data-label="中国大陆可用性"><span class="status cn-region cn-region-{_esc(cn["code"])}"><span lang="zh-CN">{_esc(cn["zh"])}</span><span lang="en">{_esc(cn["en"])}</span></span></td>
      <td class="source-cell" data-label="操作"><a class="source-link" href="{_esc(model.get("sourceUrl") or "#")}" target="_blank" rel="noopener noreferrer">{_locale_pair("目录来源", "Catalog source")} ↗</a></td>
    </tr>
    <tr class="catalog-card-row" hidden><td colspan="12"><div class="catalog-card"><h3>{card_model_markup}</h3><small class="model-id">{_esc(model_id)}</small><div class="model-badges">{modalities or ""}</div><div class="catalog-card-facts">{card_facts}</div><div class="catalog-card-meta"><span class="status cn-region cn-region-{_esc(cn["code"])}"><span lang="zh-CN">{_esc(cn["zh"])}</span><span lang="en">{_esc(cn["en"])}</span></span><a class="source-link" href="{_esc(model.get("sourceUrl") or "#")}" target="_blank" rel="noopener noreferrer">{_locale_pair("目录来源", "Catalog source")} ↗</a></div></div></td></tr>'''


def _model_catalog_markup(models: list[dict], include_heading: bool = True, page_num: int = 1, total_pages: int = 1, total_models: int = 0, linkable_model_slugs: set[str] | None = None) -> str:
    if not models:
        return ""
    provider_cards, policies, model_access = _load_access_context()
    cn_statuses = {}
    for model in models:
        code = _cn_status_for_model(model, provider_cards, policies, model_access)
        cn_statuses[str(model.get("id") or "")] = {"code": code, "zh": _CN_STATUS_LABELS[code][0], "en": _CN_STATUS_LABELS[code][1]}
    providers = sorted({(str(model.get("providerId") or ""), str(model.get("provider") or "")) for model in models}, key=lambda item: item[1].lower())
    provider_options = "".join(f'<option value="{_esc(provider_id)}">{_esc(name)}</option>' for provider_id, name in providers if provider_id)
    latencies, latency_meta = _load_endpoint_latency()
    start_index = (page_num - 1) * MODELS_PER_PAGE if total_pages > 1 else 0
    rows = "".join(
        _model_catalog_row(model, cn_statuses, row_number=start_index + offset, latencies=latencies, latency_meta=latency_meta, linkable_model_slugs=linkable_model_slugs)
        for offset, model in enumerate(models, start=1)
    )
    modalities_present = sorted({str(item) for model in models for item in (model.get("modality") or [])} - {"unknown"})
    modality_options = "".join(
        f'<option value="{_esc(item)}" data-label-zh="{_esc(_MODALITY_LABELS.get(item, item))}" data-label-en="{_esc(item.capitalize())}">{_esc(_MODALITY_LABELS.get(item, item))}</option>'
        for item in modalities_present
    )
    heading_markup = f'''<div class="mdir-heading">
        <div>
          <div class="mdir-heading-title"><span class="mdir-heading-num">01</span><span class="mdir-heading-slash">/</span><h2>{_locale_pair("实时模型目录", "Live model directory")}</h2></div>
          <p class="section-desc">{_locale_pair(f"按模型或厂商筛选目录数据，共 {total_models or len(models)} 条记录，每周人工核验更新；免费额度与接入步骤见对应资源详情页。", f"Filter catalog facts by model or provider — {total_models or len(models)} records, re-verified weekly; open each access record for free-tier terms and setup steps.")}</p>
        </div>
        <a class="mdir-heading-link" href="#mainland-cn-availability">{_locale_pair("数据说明", "Data notes")}</a>
      </div>''' if include_heading else f'''<div class="mdir-heading">
        <div>
          <div class="mdir-heading-title"><span class="mdir-heading-num">01</span><span class="mdir-heading-slash">/</span><h2>{_locale_pair("实时模型目录", "Live model directory")}</h2></div>
          <p class="section-desc">{_locale_pair("按模型或厂商筛选目录数据；免费额度与接入步骤见对应资源详情页。", "Filter catalog facts by model or provider; open each access record for free-tier terms and setup steps.")}</p>
        </div>
      </div>'''
    # Build pagination navigation
    if total_pages > 1:
        def _page_link(p: int, label: str, aria_label: str) -> str:
            if p == page_num:
                return f'<span class="catalog-page-current" aria-current="page">{label}</span>'
            href = "/models/all/" if p == 1 else f"/models/all/page/{p}/"
            return f'<a class="catalog-page-link" href="{href}" aria-label="{aria_label}">{label}</a>'
        prev_link = _page_link(page_num - 1, "‹ " + _locale_pair("上一页", "Previous"), "上一页 / Previous page") if page_num > 1 else ""
        next_link = _page_link(page_num + 1, _locale_pair("下一页", "Next") + " ‹", "下一页 / Next page") if page_num < total_pages else ""
        page_links = ""
        for p in range(1, total_pages + 1):
            if p == page_num:
                page_links += f'<span class="catalog-page-current" aria-current="page">{p}</span>'
            else:
                href = "/models/all/" if p == 1 else f"/models/all/page/{p}/"
                page_links += f'<a class="catalog-page-link" href="{href}" aria-label="第 {p} 页 / Page {p}">{p}</a>'
        pagination_markup = f'''<nav class="catalog-pagination" aria-label="分页导航 / Pagination">
        {prev_link}
        {page_links}
        {next_link}
      </nav>'''
        hint_text = _locale_pair(
            f"第 {page_num} / {total_pages} 页，共 {total_models} 条。可滚动查看当前页；筛选仅作用于当前页。",
            f"Page {page_num} of {total_pages}, {total_models} total records. Filters apply to the current page only.",
        )
    else:
        pagination_markup = ""
        hint_text = _locale_pair(
            f"共 {len(models)} 条，可滚动查看全部记录。筛选后会显示当前匹配数量。",
            f"{len(models)} records, scroll to view all. Filters show the current match count.",
        )
    return f'''<section id="model-directory" class="model-directory" data-catalog-view="table">
      {heading_markup}
      <div class="mdir-toolbar" role="search">
        <label class="mdir-search" for="model-catalog-search">
          <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m13.5 13.5 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input id="model-catalog-search" type="search" placeholder="搜索模型名称、服务商或关键词…" data-placeholder-zh="搜索模型名称、服务商或关键词…" data-placeholder-en="Search models, providers or keywords…" autocomplete="off">
          <kbd>Ctrl K</kbd>
        </label>
        <label class="mdir-field" for="model-catalog-provider"><select id="model-catalog-provider"><option value="" data-label-zh="全部服务商" data-label-en="All providers">全部服务商</option>{provider_options}</select></label>
        <label class="mdir-field" for="model-catalog-region"><select id="model-catalog-region">
          <option value="" data-label-zh="中国大陆可用性" data-label-en="Mainland CN">中国大陆可用性</option>
          <option value="available" data-label-zh="大陆可用" data-label-en="Available">大陆可用</option>
          <option value="unknown" data-label-zh="大陆待核验" data-label-en="Unverified">大陆待核验</option>
          <option value="unavailable" data-label-zh="大陆不可用" data-label-en="Unavailable">大陆不可用</option>
        </select></label>
        <label class="mdir-field" for="model-catalog-modality"><select id="model-catalog-modality"><option value="" data-label-zh="全部模态" data-label-en="All modalities">全部模态</option>{modality_options}</select></label>
        <label class="mdir-field" for="model-catalog-sort"><select id="model-catalog-sort">
          <option value="group" data-label-zh="综合排序" data-label-en="Smart sort">综合排序</option>
          <option value="latency" data-label-zh="接口最快优先" data-label-en="Fastest API first">接口最快优先</option>
          <option value="context" data-label-zh="上下文长度优先" data-label-en="Largest context">上下文长度优先</option>
          <option value="released" data-label-zh="最新发布优先" data-label-en="Newest releases">最新发布优先</option>
          <option value="score" data-label-zh="综合评分优先" data-label-en="Score">综合评分优先</option>
        </select></label>
        <div class="mdir-view" role="group" aria-label="视图切换 / View switch">
          <button type="button" class="mdir-view-btn is-active" data-catalog-view="table" aria-pressed="true">
            <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 3h13M1.5 8h13M1.5 13h13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            {_locale_pair("表格", "Table")}</button>
          <button type="button" class="mdir-view-btn" data-catalog-view="cards" aria-pressed="false">
            <svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="1.5" width="5.5" height="5.5" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="9" y="1.5" width="5.5" height="5.5" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="1.5" y="9" width="5.5" height="5.5" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="9" y="9" width="5.5" height="5.5" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>
            {_locale_pair("卡片", "Cards")}</button>
        </div>
      </div>
      <div class="mdir-chips" role="group" aria-label="热门筛选 / Quick filters">
        <span class="mdir-chips-label">{_locale_pair("热门筛选", "Quick filters")}</span>
        <button type="button" class="mdir-chip" data-chip-region="available">{_locale_pair("中国大陆可用", "Mainland CN available")}</button>
        <button type="button" class="mdir-chip" data-chip-region="unknown">{_locale_pair("待核验", "Unverified")}</button>
        <button type="button" class="mdir-chip" data-chip-modality="text">{_locale_pair("文本生成", "Text")}</button>
        <button type="button" class="mdir-chip" data-chip-modality="reasoning">{_locale_pair("推理模型", "Reasoning")}</button>
        <button type="button" class="mdir-chip" data-chip-modality="image">{_locale_pair("图像", "Image")}</button>
        <button type="button" class="mdir-chip" data-chip-modality="audio">{_locale_pair("语音", "Audio")}</button>
        <span class="mdir-chips-spacer"></span>
        <span id="model-catalog-count" class="catalog-count"></span>
        <span class="catalog-modes" aria-label="分组方式 / Group by">
          <button type="button" class="group-mode is-active" data-group-mode="provider">{_locale_pair("按厂商分组", "By provider")}</button>
          <button type="button" class="group-mode" data-group-mode="model">{_locale_pair("按模型分组", "By model")}</button>
        </span>
        <button type="button" id="model-catalog-clear" class="mdir-clear">✕ {_locale_pair("清除筛选", "Clear filters")}</button>
      </div>
      <p class="catalog-hint">{hint_text}</p>
      <p class="catalog-latency-note">{_locale_pair(*LATENCY_NOTE)}</p>
      <div class="catalog-table-wrap"><table id="model-catalog" class="catalog-table"><thead><tr>
        <th class="row-index">#</th><th>{_locale_pair("模型名称 (Model)", "Model")}</th><th>{_locale_pair("服务商 (Provider)", "Provider")}</th><th>{_locale_pair("上下文长度", "Context")}</th><th>{_locale_pair("最大输出", "Max output")}</th><th>{_locale_pair("支持模态", "Modality")}</th><th>{_locale_pair("速率限制 (Rate Limit)", "Rate limit")}</th><th>{_locale_pair(*LATENCY_COLUMN_LABEL)}</th><th>{_locale_pair("发布时间", "Released")}</th><th>{_locale_pair("在线状态", "Status")}</th><th>{_locale_pair("中国大陆可用性", "Mainland CN")}</th><th>{_locale_pair("操作", "Actions")}</th>
      </tr></thead><tbody>{rows}</tbody></table></div>
      <p id="model-catalog-empty" class="catalog-empty" hidden>{_locale_pair("没有匹配的模型。换个关键词或清除筛选条件。", "No models match this filter. Try another keyword or clear the filters.")}</p>
      {pagination_markup}
      <script>
        (() => {{
          const section = document.getElementById('model-directory');
          const table = document.getElementById('model-catalog');
          const body = table?.querySelector('tbody');
          const dataRows = body ? Array.from(body.querySelectorAll('.catalog-row')) : [];
          const cardRows = body ? Array.from(body.querySelectorAll('.catalog-card-row')) : [];
          const pairs = dataRows.map((row, index) => ({{ row, card: cardRows[index] || null }}));
          const search = document.getElementById('model-catalog-search');
          const provider = document.getElementById('model-catalog-provider');
          const region = document.getElementById('model-catalog-region');
          const modality = document.getElementById('model-catalog-modality');
          const sortSelect = document.getElementById('model-catalog-sort');
          const count = document.getElementById('model-catalog-count');
          const empty = document.getElementById('model-catalog-empty');
          const clear = document.getElementById('model-catalog-clear');
          const modes = Array.from(document.querySelectorAll('[data-group-mode]'));
          const viewButtons = Array.from(document.querySelectorAll('[data-catalog-view].mdir-view-btn'));
          const chips = Array.from(document.querySelectorAll('.mdir-chip'));
          let mode = 'provider';
          let sortMode = 'group';
          const isEnglish = () => document.documentElement.dataset.locale === 'en' || document.documentElement.lang === 'en';
          const localizeControls = () => {{
            if (search) search.placeholder = isEnglish() ? search.dataset.placeholderEn : search.dataset.placeholderZh;
            document.querySelectorAll('option[data-label-zh]').forEach(option => {{
              option.textContent = isEnglish() ? option.dataset.labelEn : option.dataset.labelZh;
            }});
          }};
          const textOf = row => (row.textContent || '').toLowerCase();
          const matches = pair => {{
            const row = pair.row;
            const query = (search?.value || '').trim().toLowerCase();
            const providerId = provider?.value || '';
            const regionFilter = region?.value || '';
            const modalityFilter = modality?.value || '';
            const modalities = (row.dataset.modality || '').split(',').filter(Boolean);
            return (!query || textOf(row).includes(query))
              && (!providerId || row.dataset.providerId === providerId)
              && (!regionFilter || row.dataset.cn === regionFilter)
              && (!modalityFilter || modalities.includes(modalityFilter));
          }};
          const sortedPairs = () => {{
            const list = pairs.filter(matches);
            if (sortMode === 'latency') {{
              const value = pair => {{
                const ms = parseInt(pair.row.dataset.ms, 10);
                return Number.isFinite(ms) ? ms : Number.POSITIVE_INFINITY;
              }};
              list.sort((a, b) => value(a) - value(b));
            }} else if (sortMode === 'context') {{
              list.sort((a, b) => (parseInt(b.row.dataset.context, 10) || 0) - (parseInt(a.row.dataset.context, 10) || 0));
            }} else if (sortMode === 'released') {{
              list.sort((a, b) => (b.row.dataset.released || '').localeCompare(a.row.dataset.released || ''));
            }} else if (sortMode === 'score') {{
              list.sort((a, b) => (parseFloat(b.row.dataset.score) || 0) - (parseFloat(a.row.dataset.score) || 0));
            }} else {{
              const value = pair => {{
                const cell = mode === 'model' ? pair.row.querySelector('.model-cell strong') : pair.row.querySelector('.provider-filter');
                return cell ? cell.textContent.trim().toLowerCase() : '';
              }};
              list.sort((a, b) => value(a).localeCompare(value(b), undefined, {{numeric: true}}));
            }}
            return list;
          }};
          const applyView = () => {{
            const cards = section?.dataset.catalogView === 'cards';
            viewButtons.forEach(button => {{
              const active = (button.dataset.catalogView === 'cards') === cards;
              button.classList.toggle('is-active', active);
              button.setAttribute('aria-pressed', String(active));
            }});
          }};
          const apply = () => {{
            const cards = section?.dataset.catalogView === 'cards';
            const visible = sortedPairs();
            body.querySelectorAll('.catalog-group-row').forEach(row => row.remove());
            let previousGroup = '';
            visible.forEach((pair, index) => {{
              const indexCell = pair.row.querySelector('.row-index');
              if (indexCell) indexCell.textContent = String(index + 1);
              pair.row.hidden = cards;
              if (pair.card) pair.card.hidden = !cards;
              if (!cards && sortMode === 'group') {{
                const groupCell = mode === 'provider' ? pair.row.querySelector('.provider-filter') : pair.row.querySelector('.model-cell strong');
                const group = groupCell ? groupCell.textContent.trim() : '';
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
              body.appendChild(pair.row);
              if (pair.card) body.appendChild(pair.card);
            }});
            if (count) count.textContent = isEnglish() ? `Showing ${{visible.length}} / ${{pairs.length}}` : `显示 ${{visible.length}} 条 / 共 ${{pairs.length}} 条`;
            if (empty) empty.hidden = visible.length !== 0;
            chips.forEach(chip => {{
              const chipRegion = chip.dataset.chipRegion;
              const chipModality = chip.dataset.chipModality;
              const active = (chipRegion && region?.value === chipRegion) || (chipModality && modality?.value === chipModality);
              chip.classList.toggle('is-active', Boolean(active));
            }});
          }};
          search?.addEventListener('input', apply);
          provider?.addEventListener('change', apply);
          region?.addEventListener('change', apply);
          modality?.addEventListener('change', apply);
          sortSelect?.addEventListener('change', () => {{
            sortMode = sortSelect.value || 'group';
            apply();
          }});
          modes.forEach(button => button.addEventListener('click', () => {{
            mode = button.dataset.groupMode || 'provider';
            modes.forEach(item => item.classList.toggle('is-active', item === button));
            apply();
          }}));
          viewButtons.forEach(button => button.addEventListener('click', () => {{
            if (section) section.dataset.catalogView = button.dataset.catalogView || 'table';
            applyView();
            apply();
          }}));
          chips.forEach(chip => chip.addEventListener('click', () => {{
            if (chip.dataset.chipRegion && region) region.value = region.value === chip.dataset.chipRegion ? '' : chip.dataset.chipRegion;
            if (chip.dataset.chipModality && modality) modality.value = modality.value === chip.dataset.chipModality ? '' : chip.dataset.chipModality;
            apply();
          }}));
          clear?.addEventListener('click', () => {{
            if (search) search.value = '';
            if (provider) provider.value = '';
            if (region) region.value = '';
            if (modality) modality.value = '';
            if (sortSelect) sortSelect.value = 'group';
            sortMode = 'group';
            apply();
          }});
          document.addEventListener('keydown', event => {{
            if ((event.ctrlKey || event.metaKey) && (event.key === 'k' || event.key === 'K')) {{
              event.preventDefault();
              search?.focus();
              search?.select();
            }}
          }});
          document.querySelectorAll('.provider-filter').forEach(button => button.addEventListener('click', () => {{
            if (provider) provider.value = button.dataset.providerValue || '';
            apply();
            document.getElementById('model-directory')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
          }}));
          localizeControls();
          applyView();
          apply();
        }})();
      </script>
      <style>
        .model-directory .mdir-heading {{ display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: flex-start; justify-content: space-between; margin: 0 0 14px; }}
        .model-directory .mdir-heading-title {{ display: flex; gap: 12px; align-items: baseline; }}
        .model-directory .mdir-heading-num {{ color: var(--accent); font: 700 30px/1 var(--font-serif), Georgia, serif; letter-spacing: .02em; }}
        .model-directory .mdir-heading-slash {{ color: var(--ink-tertiary); font: 400 24px/1 var(--font-serif), Georgia, serif; }}
        .model-directory .mdir-heading-title h2 {{ margin: 0; }}
        .model-directory .mdir-heading-link {{ flex: 0 0 auto; align-self: center; display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 9999px; padding: 7px 14px; color: var(--accent); background: var(--surface); font: 500 12.5px/1.2 var(--font-sans); text-decoration: none; transition: all .15s; }}
        .model-directory .mdir-heading-link:hover {{ border-color: var(--accent); }}
        .model-directory .mdir-toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 0 0 10px; padding: 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }}
        .model-directory .mdir-search {{ position: relative; flex: 1 1 260px; display: flex; align-items: center; }}
        .model-directory .mdir-search svg {{ position: absolute; left: 11px; width: 15px; height: 15px; color: var(--ink-tertiary); pointer-events: none; }}
        .model-directory .mdir-search input {{ width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 8px; padding: 8px 62px 8px 34px; color: var(--ink); background: var(--surface-soft); font: inherit; font-size: 13.5px; outline: none; transition: border-color .15s, box-shadow .15s; }}
        .model-directory .mdir-search input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft, var(--soft)); background: var(--surface); }}
        .model-directory .mdir-search kbd {{ position: absolute; right: 10px; border: 1px solid var(--line); border-radius: 5px; padding: 2px 6px; color: var(--ink-tertiary); background: var(--surface); font: 500 10.5px/1.4 var(--font-mono); pointer-events: none; }}
        .model-directory .mdir-field select {{ min-height: 38px; max-width: 200px; border: 1px solid var(--line); border-radius: 8px; padding: 8px 28px 8px 10px; color: var(--ink); background: var(--surface-soft); font: inherit; font-size: 13px; outline: none; cursor: pointer; transition: border-color .15s; }}
        .model-directory .mdir-field select:focus {{ border-color: var(--accent); }}
        .model-directory .mdir-view {{ display: inline-flex; gap: 0; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }}
        .model-directory .mdir-view-btn {{ display: inline-flex; gap: 6px; align-items: center; border: 0; padding: 9px 14px; color: var(--ink-secondary); background: var(--surface); cursor: pointer; font: 500 12.5px/1 var(--font-sans); transition: all .15s; }}
        .model-directory .mdir-view-btn + .mdir-view-btn {{ border-left: 1px solid var(--line); }}
        .model-directory .mdir-view-btn svg {{ width: 13px; height: 13px; }}
        .model-directory .mdir-view-btn.is-active {{ color: #fff; background: var(--accent); }}
        .model-directory .mdir-chips {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0 0 12px; }}
        .model-directory .mdir-chips-label {{ color: var(--ink-tertiary); font: 500 12px/1.6 var(--font-sans); }}
        .model-directory .mdir-chip {{ border: 1px solid var(--line); border-radius: 7px; padding: 6px 12px; color: var(--ink-secondary); background: var(--surface); cursor: pointer; font: 400 12.5px/1.4 var(--font-sans); transition: all .15s; }}
        .model-directory .mdir-chip:hover {{ border-color: var(--accent); color: var(--accent); }}
        .model-directory .mdir-chip.is-active {{ color: var(--accent); border-color: var(--accent); background: var(--accent-soft, var(--soft)); }}
        .model-directory .mdir-chips-spacer {{ flex: 1 1 auto; }}
        .model-directory .mdir-clear {{ border: 0; padding: 6px 8px; color: var(--ink-tertiary); background: transparent; cursor: pointer; font: 400 12.5px/1.4 var(--font-sans); }}
        .model-directory .mdir-clear:hover {{ color: var(--accent); }}
        .model-directory .catalog-table {{ min-width: 1260px; }}
        .model-directory .catalog-table td, .model-directory .catalog-table tbody th {{ padding: 11px 12px; vertical-align: middle; }}
        .model-directory .catalog-table .row-index {{ color: var(--ink-tertiary); font: 500 12px/1.5 var(--font-mono); width: 34px; }}
        .model-directory .catalog-table .model-cell strong {{ font: 600 13px/1.5 var(--font-mono); }}
        .model-directory .catalog-table .source-link {{ display: inline-flex; align-items: center; gap: 4px; border: 1px solid var(--line); border-radius: 7px; padding: 6px 11px; color: var(--accent); background: var(--surface); font: 500 12px/1.3 var(--font-sans); text-decoration: none; white-space: nowrap; transition: all .15s; }}
        .model-directory .catalog-table .source-link:hover {{ border-color: var(--accent); background: var(--accent-soft, var(--soft)); }}
        .model-directory .status-dot {{ display: inline-block; width: 7px; height: 7px; margin-right: 6px; border-radius: 9999px; background: var(--ink-tertiary); vertical-align: 1px; }}
        .model-directory .status-dot-online {{ background: #16a34a; box-shadow: 0 0 0 3px rgba(22, 163, 74, .14); }}
        .model-directory .status-dot-offline {{ background: #dc2626; }}
        .model-directory .status-dot-degraded {{ background: #d97706; }}
        .model-directory .catalog-table .freshness {{ margin-left: 6px; }}
        .model-directory .catalog-table .latency-cell {{ white-space: nowrap; }}
        .model-directory .catalog-table .latency-value {{ font: 500 12.5px/1.5 var(--font-mono); color: var(--ink); }}
        .model-directory .catalog-table .latency-unknown {{ color: var(--ink-tertiary); }}
        .model-directory .catalog-latency-note {{ margin: -4px 0 12px; color: var(--ink-tertiary); font: 400 12px/1.7 var(--font-sans); }}
        .model-directory .catalog-card-row > td {{ padding: 0; border-bottom: 0; background: transparent; }}
        .model-directory .catalog-card {{ display: grid; gap: 10px; margin: 6px 0; padding: 16px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }}
        .model-directory .catalog-card h3 {{ margin: 0; font: 600 15px/1.4 var(--font-mono); }}
        .model-directory .catalog-card h3 a {{ color: var(--ink); text-decoration: none; }}
        .model-directory .catalog-card h3 a:hover {{ color: var(--accent); }}
        .model-directory .catalog-card-facts {{ display: flex; flex-wrap: wrap; gap: 8px 18px; }}
        .model-directory .catalog-card-fact {{ display: grid; gap: 1px; font: 500 12.5px/1.5 var(--font-sans); color: var(--ink); }}
        .model-directory .catalog-card-fact small {{ color: var(--ink-tertiary); font: 500 10.5px/1.4 var(--font-mono); text-transform: uppercase; letter-spacing: .06em; }}
        .model-directory .catalog-card-meta {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; }}
        .model-directory[data-catalog-view="cards"] .catalog-table thead {{ display: none; }}
        .model-directory[data-catalog-view="cards"] .catalog-row {{ display: none; }}
        .model-directory[data-catalog-view="cards"] .catalog-group-row {{ display: none; }}
        .model-directory[data-catalog-view="cards"] .catalog-card-row {{ display: table-row; }}
        @media (max-width: 720px) {{
          .model-directory .mdir-heading-link {{ display: none; }}
          .model-directory .mdir-field, .model-directory .mdir-field select {{ flex: 1 1 45%; max-width: none; }}
        }}
        .catalog-pagination {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; justify-content: center; margin: 20px 0 0; padding: 16px; }}
        .catalog-page-link, .catalog-page-current {{ display: inline-flex; align-items: center; justify-content: center; min-width: 36px; height: 36px; padding: 0 12px; border: 1px solid var(--line); border-radius: 8px; color: var(--accent); background: var(--surface); text-decoration: none; font: 600 13px/1 var(--font-sans), ui-sans-serif, system-ui, sans-serif; transition: all .15s; }}
        .catalog-page-link:hover {{ border-color: var(--accent); color: var(--accent); }}
        .catalog-page-current {{ color: #fff; background: var(--accent); border-color: var(--accent); }}
      </style>
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
    """Label a row by the kind of source it was read from.

    ``official`` means the provider's own catalogue. ``public_api`` means a
    public model API used as a supplement, which is a weaker claim about the
    upstream lab and has to be visible as such.
    """
    kind = str(model.get("sourceKind") or "")
    if kind == "official":
        return _locale_pair("厂商官方来源", "Provider official source")
    if kind == "public_api":
        return _locale_pair("公开 API", "Public API")
    return _locale_pair("来源待核验", "Source unverified")


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
          <td>{_esc(model.get("context") or "—")}</td>
          <td>{_esc(model.get("rateLimit") or "—")}</td>
          <td><span class="status status-{_esc(status)}">{status_label}</span><small>{_catalog_source_label(model)}</small></td>
          <td>{_esc(model.get("lastSeenAt") or "—")}</td>
          <td><a href="{_esc(model.get("sourceUrl") or "#")}" target="_blank" rel="noopener noreferrer">{_locale_pair("目录来源", "Catalog source")} ↗</a></td>
        </tr>''')
    return '''<div class="catalog-table-wrap"><table class="catalog-table"><thead><tr>
      <th>厂商 <span lang="en">Provider</span></th><th>模型 <span lang="en">Model</span></th><th>上下文 <span lang="en">Context</span></th>
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
    description = f"比较 {model_name} 在不同厂商的上下文、速率、状态和来源，并查看 FreeLLM 已整理的详细接入资源。"
    # 记录数不足阈值的聚合页本身就是薄页，已经主动 noindex；既然不让搜索引擎收录，
    # 就不该同时挂广告代码 —— 薄页广告属于低价值库存，是 AdSense 审核和账号风险的高发面。
    # 广告与收录用同一个判定，避免两套标准各走各的。
    indexable = len(records) >= MIN_RECORDS_FOR_INDEXABLE_MODEL_PAGE
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
  <link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "article", indexable=indexable)}
  {_analytics_script()}{ADSENSE_SCRIPT if indexable else ""}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    h1 {{ margin: 10px 0; font-size: clamp(30px, 5vw, 48px); }}
    main section h2 {{ font-size: clamp(22px, 3.4vw, 30px); }}
    .related-list {{ padding-left: 20px; }}
    footer {{ color: var(--ink-secondary); font-size: 13px; }}
  </style>
</head>
<body data-static-locale="true">
  <header><p><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / <a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('全部模型', 'All models')}</a></p>
    {_static_locale_nav()}<button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button><div class="eyebrow">MODEL AGGREGATION</div><h1>{_esc(model_name)}</h1>
    <p class="lead">{_locale_pair(f'同一模型在 {len(records)} 个厂家或平台的目录记录。先比较限制，再进入对应的官方或本站详细入口。', f'{len(records)} provider or platform records for the same model. Compare limits first, then open the relevant official or FreeLLM access path.')}</p>
    <div class="stats"><span>{len(records)} {_locale_pair('个平台记录', 'platform records')}</span><span>{_locale_pair('最近同步', 'Last synced')}: {latest}</span><span>{_locale_pair('来源级别', 'Source level')}: {_locale_pair('厂商官方目录', 'Provider catalogues')}</span></div>
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
        source_label = _locale_pair("操作指南", "Operation guide") if provider.get("sourceKind") == "operation" else _locale_pair("厂商来源", "Provider source")
        cards.append(f'''<article class="provider-card"><div class="eyebrow">{_esc(provider.get("id"))}</div><h2><a href="{_esc(provider_url(provider))}">{_esc(provider.get("name"))}</a></h2><p>{len(provider_models)} {_locale_pair('个模型', 'models')} · {source_label}</p><p class="muted">{_locale_pair('最近同步', 'Last synced')}: {latest}</p><a class="button" href="{_esc(provider_url(provider))}">{_locale_pair('查看厂家模型', 'View provider models')} →</a></article>''')
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": description, "url": page_url, "inLanguage": ["zh-CN", "en"], "mainEntity": {"@type": "ItemList", "numberOfItems": len(providers), "itemListElement": [{"@type": "ListItem", "position": index, "name": provider.get("name"), "url": _absolute(site_url, provider_url(provider))} for index, provider in enumerate(providers, start=1)]}}
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "website")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>{SKILLS_THEME_ASSETS}
<style>{EDITORIAL_BASE_CSS}</style>
<style>body {{max-width:1180px;}}h1 {{font-size:clamp(30px,5vw,48px);}}.provider-card .button {{margin-top:auto;}}footer {{color:var(--ink-secondary);font-size:13px;}}</style></head>
<body data-static-locale="true"><header><p><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / {_locale_pair('按厂家浏览', 'Browse by provider')}</p>{_static_locale_nav()}<button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button><h1>{_locale_pair('按厂家浏览模型', 'Browse models by provider')}</h1><p class="lead">{_locale_pair(description, f'Explore {len(providers)} AI providers and {len(models)} catalog models.')}</p><p><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('返回模型大列表', 'Back to model directory')} →</a></p></header><main><div class="provider-grid">{"".join(cards)}</div></main><footer><p>{_locale_pair('目录数据来自各厂商自己公开的模型目录；公开 API 来源已单独标注，具体免费条件和操作步骤进入本站详细资源页核对。', 'Catalog rows come from the model catalogues each provider publishes, with public-API sources labelled separately; verify free terms and operation steps on detailed FreeLLM records.')}</p></footer></body></html>'''


def render_provider_page(provider: dict, models: list[dict], offers: list[dict], site_url: str, operations: list[dict] | None = None, provider_access: dict[str, dict] | None = None, model_access: dict[str, dict] | None = None) -> str:
    provider_models = [model for model in models if model.get("providerId") == provider.get("id")]
    path = provider_url(provider)
    page_url = _absolute(site_url, path)
    name = str(provider.get("name") or provider.get("id") or "Provider")
    title = f"{name} 模型与免费入口 · {name} Models & Access | FreeLLM"
    description = f"浏览 {name} 的 {len(provider_models)} 个模型记录，比较上下文、限流、状态和来源，并查看已整理的免费入口。"
    related = _related_offer_links(offers, lambda offer: _provider_offer_matches(provider, offer))
    operation_guides_markup = _operation_guides_markup(_operation_guides_for_provider(str(provider.get("id") or ""), operations or []))
    routes_markup = _access_routes_markup(provider_models)
    registration_markup = routes_markup + _registration_requirements_markup((provider_access or {}).get(str(provider.get("id") or "")))
    source_label = _locale_pair("操作指南", "Operation guide") if provider.get("sourceKind") == "operation" else _locale_pair("厂商来源", "Provider source")
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": description, "url": page_url, "inLanguage": ["zh-CN", "en"], "dateModified": _latest_date(provider_models, "lastSeenAt"), "mainEntity": {"@type": "ItemList", "numberOfItems": len(provider_models), "itemListElement": [{"@type": "ListItem", "position": index, "name": f'{name} · {model.get("model")}', "url": (_absolute(site_url, model_aggregate_url(model)) if _safe_slug(model.get("model"), "model") in indexable_model_slugs(models) else (model.get("sourceUrl") or page_url))} for index, model in enumerate(provider_models, start=1)]}}
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "article")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>{SKILLS_THEME_ASSETS}
<style>{EDITORIAL_BASE_CSS}</style>
<style>h1 {{margin:10px 0;font-size:clamp(30px,5vw,48px);}}main section h2 {{font-size:clamp(22px,3.4vw,30px);}}.related-list {{padding-left:20px;}}footer {{color:var(--ink-secondary);font-size:13px;}}</style></head>
<body data-static-locale="true"><header><p><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / <a href="{_esc(_absolute(site_url, PROVIDERS_PAGE_PATH))}">{_locale_pair('按厂家浏览', 'Browse by provider')}</a></p>{_static_locale_nav()}<button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button><div class="eyebrow">PROVIDER DIRECTORY</div><h1>{_esc(name)}</h1><p class="lead">{_locale_pair(description, f'Browse {len(provider_models)} model records for {name}.')}</p><div class="stats"><span>{len(provider_models)} {_locale_pair('个模型', 'models')}</span><span>{_locale_pair('最近同步', 'Last synced')}: {_latest_date(provider_models, 'lastSeenAt')}</span><span>{_locale_pair('来源级别', 'Source level')}: {source_label}</span></div></header><main>{registration_markup}<section><h2>{_locale_pair('全部模型记录', 'All model records')}</h2>{_catalog_record_table(provider_models)}</section><section><h2>{_locale_pair('本站详细接入资源', 'Detailed FreeLLM access records')}</h2>{related}</section>{operation_guides_markup}</main><footer><p><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('返回模型大列表', 'Back to model directory')}</a> · <a href="{_esc(_absolute(site_url, PROVIDERS_PAGE_PATH))}">{_locale_pair('返回厂家目录', 'Back to providers')}</a></p></footer></body></html>'''


def render_models_landing_page(offers: list[dict], models: list[dict], vendor_directory: list[dict], site_url: str) -> str:
    path = MODELS_PAGE_PATH
    page_url = _absolute(site_url, path)
    offer_count = len(offers)
    model_record_count = len(models)
    vendor_directory_count = len(vendor_directory)
    active_provider_id_count = len({str(item.get("providerId") or "").strip() for item in models if item.get("providerId")})
    title = "AI 模型概览：模型记录、厂家目录与免费资源 · FreeLLM"
    description = (
        f"FreeLLM 当前整理 {model_record_count} 条模型记录、{vendor_directory_count} 个厂家目录、"
        f"{active_provider_id_count} 个当前模型数据 Provider ID 与 {offer_count} 条免费资源。四种口径分开统计，避免把 Offer 当成模型。"
    )
    schema = {
        "@context": "https://schema.org", "@type": "CollectionPage", "name": title,
        "description": description, "url": page_url, "inLanguage": ["zh-CN", "en"],
    }
    tabs = f'''<nav class="model-section-tabs" aria-label="模型页面">
      <a href="{MODELS_PAGE_PATH}" aria-current="page">概览</a>
      <a href="{ALL_MODELS_PAGE_PATH}">全部模型</a>
      <a href="{PROVIDERS_PAGE_PATH}">按厂家</a>
      <a href="/category/api/">免费 API / Offer</a>
    </nav>'''
    stats = f'''<div class="fl-stat-grid" aria-label="模型目录统计">
      <div class="fl-stat-card"><strong>{model_record_count}</strong><span>模型记录 / model records</span></div>
      <div class="fl-stat-card"><strong>{vendor_directory_count}</strong><span>厂家目录 / vendor directory</span></div>
      <div class="fl-stat-card"><strong>{active_provider_id_count}</strong><span>当前数据 Provider ID</span></div>
      <div class="fl-stat-card"><strong>{offer_count}</strong><span>免费资源 / verified offers</span></div>
    </div>'''
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">
{_social_meta(site_url, path, title, description, "website")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>{SKILLS_THEME_ASSETS}
<style>{EDITORIAL_BASE_CSS}</style><style>
.models-overview h1{{font-size:clamp(34px,6vw,58px);max-width:900px}}.models-overview .lead{{max-width:860px}}
.models-overview-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
.models-overview-grid article{{padding:20px;border:1px solid var(--line);border-radius:12px;background:var(--surface)}}
.models-overview-grid h2{{margin:0 0 8px;font-size:22px}}@media(max-width:700px){{.models-overview-grid{{grid-template-columns:1fr}}}}
</style></head><body data-static-locale="true"><header class="models-overview">
<div class="eyebrow">MODEL DIRECTORY / 数据口径已拆分</div><h1>模型、厂家、Provider 和免费资源，不再混成一个数字</h1>
<p class="lead">“模型记录”“厂家目录”“当前模型数据 Provider ID”“免费资源 / Offer”是四种不同实体。这里分别统计，再进入对应目录继续浏览。</p>
{tabs}{stats}</header><main><section class="models-overview-grid">
<article><h2>全部模型</h2><p>查看模型名称、厂家、上下文、状态和来源。</p><a class="button" href="{ALL_MODELS_PAGE_PATH}">打开完整模型目录 →</a></article>
<article><h2>按厂家</h2><p>浏览厂家目录；厂家目录总数不等于当前模型快照里的 providerId 数。</p><a class="button" href="{PROVIDERS_PAGE_PATH}">查看厂家目录 →</a></article>
<article><h2>免费 API / Offer</h2><p>这是可注册、可试用或可下载的资源入口，不拿它冒充模型数量。</p><a class="button" href="/category/api/">查看免费 API / Offer →</a></article>
<article><h2>模型中心</h2><p>先看精选资源，再进入模型目录与接入信息。</p><a class="button" href="{MODEL_CENTER_PAGE_PATH}">进入模型中心 →</a></article>
</section></main><footer><p>统计由 data/offers.json、data/models.json 与 data/provider-catalog.json 构建生成。</p></footer></body></html>'''


def render_models_page(offers: list[dict], site_url: str, models: list[dict] | None = None, page_num: int = 1, total_pages: int = 1) -> str:
    """Bilingual (Chinese / English) directory of every verified offer with a
    registration CTA, so one shareable URL serves both language communities."""
    if models is not None and total_pages > 1:
        path = f"{ALL_MODELS_PAGE_PATH}page/{page_num}/" if page_num > 1 else ALL_MODELS_PAGE_PATH
    else:
        path = ALL_MODELS_PAGE_PATH if models is not None else MODELS_PAGE_PATH
    page_url = _absolute(site_url, path)
    total = len(offers)
    model_catalog = models or []
    model_total = len(model_catalog)
    provider_total = len({str(model.get("providerId") or "") for model in model_catalog if model.get("providerId")})
    if models is not None and total_pages > 1:
        start = (page_num - 1) * MODELS_PER_PAGE
        end = start + MODELS_PER_PAGE
        page_models = model_catalog[start:end]
    else:
        page_models = model_catalog
    provider_access_count = len(_load_access_context()[0]) if models is not None else 0
    if models is None:
        title = "免费 AI 资源目录：模型、API 与 IDE · Free AI Resources Directory | FreeLLM"
        description = (
            f"按免费额度、API、IDE、试用和开源权重浏览 FreeLLM 的 {total} 条可核验资源，"
            "进入每条资源页查看官方入口、限制和操作步骤。 Browse verified free AI models, APIs, IDEs and open-weight resources."
        )
    else:
        if page_num > 1:
            title = f"全部免费 AI 模型与 API 一览（第 {page_num} 页）· All Free AI Models with Mainland CN Availability | FreeLLM"
            description = (
                f"FreeLLM 收录的 {model_total or total} 个模型与 {total} 个免费访问资源，逐行标注中国大陆可用性，"
                f"第 {page_num}/{total_pages} 页。附 {provider_access_count} 家提供商注册要求（手机号、实名、信用卡）与官方来源。"
                f" Browse {model_total or total} catalog models and {total} verified free access records with per-row "
                f"mainland-China availability labels and per-provider signup requirements (phone, identity, credit card)."
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
        <li>{_locale_pair("Agnes AI：仅邮箱注册；国内站 api.agnes-ai.cn 与国际站 apihub.agnes-ai.com 为两套官方入口，API Key 通用", "Agnes AI: email-only signup; the mainland-CN host api.agnes-ai.cn and the global host apihub.agnes-ai.com are separate official endpoints sharing one API key")}</li>
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
  {SKILLS_THEME_ASSETS}
  <style>
    {EDITORIAL_BASE_CSS}
  </style>
  <style>
    h1 {{ max-width: 860px; margin: 22px 0 10px; font-size: clamp(32px, 5.5vw, 52px); }}
    h2 {{ font-size: clamp(23px, 3.5vw, 30px); }}
    h2 small {{ color: var(--ink-secondary); font-size: 15px; font-weight: 400; }}
    h2 [lang="en"] {{ color: var(--ink-tertiary); font-weight: 500; font-size: .62em; margin-left: 6px; }}
    main {{ display: grid; gap: 30px; }}
    .hero-grid {{ display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(300px, 1fr); gap: 26px; align-items: start; }}
    .hero-eyebrow {{ margin: 26px 0 0; color: var(--accent); font: 600 11px/1.5 var(--font-mono); letter-spacing: .22em; }}
    .hero-grid h1 {{ max-width: none; margin: 10px 0 4px; }}
    .hero-sub {{ margin: 0 0 6px; color: var(--ink-secondary); font: 400 clamp(17px, 2.6vw, 24px)/1.4 var(--font-serif), Georgia, serif; }}
    .hero-cards {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 26px; }}
    .hero-card {{ display: flex; gap: 12px; align-items: center; padding: 16px 15px; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); box-shadow: 0 1px 2px rgba(15, 23, 42, .04); }}
    .hero-card-icon {{ flex: 0 0 auto; display: inline-flex; width: 38px; height: 38px; border-radius: 10px; color: var(--accent); background: var(--accent-soft, var(--soft)); align-items: center; justify-content: center; }}
    .hero-card-icon svg {{ width: 19px; height: 19px; }}
    .hero-card div {{ display: grid; gap: 1px; min-width: 0; }}
    .hero-card strong {{ font: 600 16px/1.3 var(--font-sans); color: var(--ink); letter-spacing: -.01em; }}
    .hero-card span {{ color: var(--ink-tertiary); font: 400 11px/1.5 var(--font-sans); }}
    @media (max-width: 900px) {{ .hero-grid {{ grid-template-columns: 1fr; }} .hero-cards {{ margin-top: 0; }} .hero-eyebrow {{ margin-top: 18px; }} }}
    section + section {{ padding-top: 26px; border-top: 1px solid var(--line); }}
    .section-desc {{ margin: 0 0 14px; color: var(--ink-secondary); font-size: 14px; }}
    .catalog-toolbar {{ display: grid; grid-template-columns: minmax(220px, 1.5fr) minmax(150px, .8fr) minmax(140px, .75fr) auto 1fr; gap: 10px; align-items: end; margin: 18px 0 14px; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); }}
    .catalog-toolbar label {{ color: var(--ink-secondary); font: 500 11px/1.6 var(--font-mono); text-transform: uppercase; letter-spacing: .07em; }}
    .catalog-search-label, .catalog-provider-label, .catalog-region-label {{ display: grid; gap: 5px; }}
    .catalog-toolbar input, .catalog-toolbar select {{ min-height: 38px; border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; color: var(--ink); background: var(--surface); font: inherit; outline: none; transition: border-color .15s, box-shadow .15s; }}
    .catalog-toolbar input:focus, .catalog-toolbar select:focus {{ border-color: var(--ink); box-shadow: 0 0 0 3px var(--line-soft); }}
    .catalog-modes {{ display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }}
    .group-mode, .provider-filter {{ border: 0; border-radius: 6px; padding: 7px 10px; color: var(--accent); background: transparent; cursor: pointer; font: inherit; }}
    .group-mode {{ border: 1px solid var(--line); font-size: 12px; white-space: nowrap; transition: all .15s; }}
    .group-mode:hover {{ border-color: var(--ink-tertiary); }}
    .group-mode.is-active {{ color: var(--ink-solid-contrast); background: var(--ink-solid); border-color: var(--ink-solid); }}
    .provider-filter {{ padding: 0; text-align: left; font-size: 13px; font-weight: 600; }}
    .provider-filter:hover {{ text-decoration: underline; }}
    .provider-page-link {{ display: block; margin-top: 3px; color: var(--ink-secondary); font-size: 11px; }}
    .catalog-count {{ align-self: center; justify-self: end; color: var(--ink-tertiary); font: 500 11px var(--font-mono); letter-spacing: .05em; white-space: nowrap; }}
    .catalog-table {{ min-width: 1220px; }}
    .catalog-table .latency-cell {{ white-space: nowrap; }}
    .catalog-table .latency-value {{ font: 500 12.5px/1.5 var(--font-mono); color: var(--ink); }}
    .catalog-table .latency-unknown {{ color: var(--ink-tertiary); }}
    .catalog-hint {{ margin: 0 0 12px; color: var(--ink-secondary); font-size: 12px; }}
    .catalog-latency-note {{ margin: -4px 0 12px; color: var(--ink-tertiary); font-size: 12px; }}
    .card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); gap: 14px; }}
    .model-card {{ display: flex; flex-direction: column; gap: 10px; border: 1px solid var(--line); border-radius: 8px; padding: 18px; background: var(--surface); transition: box-shadow .2s; }}
    .model-card:hover {{ box-shadow: var(--card-shadow); }}
    .card-head {{ display: flex; gap: 10px; align-items: flex-start; }}
    .mark {{ flex: 0 0 auto; display: inline-flex; width: 34px; height: 34px; border-radius: 8px; background: var(--accent-soft); color: var(--accent); align-items: center; justify-content: center; font: 700 13px var(--font-mono); }}
    .card-head h3 {{ margin: 0; font-size: 19px; line-height: 1.35; }}
    .card-head a {{ color: var(--ink); text-decoration: none; }}
    .card-head a:hover {{ color: var(--accent); }}
    .provider {{ margin: 2px 0 0; color: var(--ink-secondary); font-size: 12.5px; }}
    .model {{ margin: 0; color: var(--ink-secondary); font: 400 12px/1.6 var(--font-mono); }}
    .facts {{ margin: 0; display: grid; gap: 6px; }}
    .facts div {{ display: grid; grid-template-columns: 112px 1fr; gap: 8px; font-size: 12.5px; }}
    .facts dt {{ color: var(--ink-tertiary); }}
    .facts dd {{ margin: 0; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{ border: 1px solid var(--line); border-radius: 9999px; padding: 2px 9px; font: 400 11px/1.7 var(--font-mono); color: var(--ink-secondary); background: var(--surface-soft); }}
    .actions {{ margin-top: auto; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding-top: 4px; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    footer {{ color: var(--ink-secondary); font-size: 13px; }}
    footer strong {{ color: var(--ink); }}
    @media (max-width: 820px) {{ .catalog-toolbar {{ grid-template-columns: 1fr 1fr; }} .catalog-modes {{ grid-column: 1 / -1; }} .catalog-count {{ justify-self: start; }} }}
    @media (max-width: 620px) {{ .facts div {{ grid-template-columns: 96px 1fr; }} .catalog-toolbar {{ grid-template-columns: 1fr; }} .catalog-modes {{ grid-column: auto; }} }}
  </style>
</head>
<body data-static-locale="true">
  <header>
    <div class="crumb"><a href="{_esc(_absolute(site_url, '/'))}">Free AI Index</a> / {_locale_pair('全部模型', 'All models')}</div>
    {_static_locale_nav()}
    <button class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button>
    <div class="hero-grid">
      <div class="hero-copy">
        <p class="hero-eyebrow">FREE MODELS. MORE POSSIBILITIES.</p>
        <h1>{_locale_pair('全部免费 AI 模型与 API 一览', 'All Free AI Models & APIs')}</h1>
        <p class="hero-sub">{_locale_pair('含中国大陆可用性标注', 'with Mainland CN Availability')}</p>
        <p class="lead">{_locale_pair(f'FreeLLM 收录的每一个免费 AI 模型、API、IDE 和工具都在这一页：模型目录逐行标注中国大陆可用性，接入资源直达官方，注册要求（手机号、实名、信用卡）与免费条件逐条标注。', 'Every catalog model, API and tool on FreeLLM — model rows carry mainland-China availability labels, access records link to official sites, and signup requirements (phone, identity, credit card) plus free-tier terms are listed row by row.')}</p>
      </div>
      <div class="hero-cards" aria-label="目录统计 / Catalog stats">
        <div class="hero-card">
          <span class="hero-card-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M10 2 3 5.5v9L10 18l7-3.5v-9L10 2Zm0 2.2 4.6 2.3L10 8.8 5.4 6.5 10 4.2ZM5 8.3l4 2v5l-4-2v-5Zm6 7v-5l4-2v5l-4 2Z" fill="currentColor"/></svg></span>
          <div><strong>{model_total or total}</strong><span>{_locale_pair('免费模型与 API', 'Total Models & APIs')}</span></div>
        </div>
        <div class="hero-card">
          <span class="hero-card-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M10 2a4 4 0 1 1 0 8 4 4 0 0 1 0-8Zm-7 8.5V16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5.5a7.97 7.97 0 0 1-7 0 7.97 7.97 0 0 1-7 0Z" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="6" cy="6" r="2.6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></span>
          <div><strong>{provider_total}</strong><span>{_locale_pair('厂商 / 访问记录', 'Providers')}</span></div>
        </div>
        <div class="hero-card">
          <span class="hero-card-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="7.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 5.5V10l3 2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></span>
          <div><strong>{_locale_pair('每周核验', 'Verified Weekly')}</strong><span>{_locale_pair('持续更新', 'Continuously updated')}</span></div>
        </div>
        <div class="hero-card">
          <span class="hero-card-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><rect x="3" y="4.5" width="14" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 8.5h14M7 2.5v4M13 2.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></span>
          <div><strong>{last_checked}</strong><span>{_locale_pair('最近更新', 'Last Updated')}</span></div>
        </div>
      </div>
    </div>
    <div class="stats">
      <span><strong>{model_total or total}</strong> {_locale_pair('个模型', 'models')}</span>
      <span><strong>{total}</strong> {_locale_pair('个接入资源', 'access records')}</span>
      <span>{_locale_pair('模型同步', 'Models synced')}: {model_last_seen}</span>
      <span>{_locale_pair('资源核验', 'Offers checked')}: {offer_last_checked}</span>
      <span>{_locale_pair('接入资源注册链接指向官方', 'Access-record links point to official sites')}</span>
    </div>
    <div class="callout">{_locale_pair('免费额度受地区、账户类型、速率限制和有效期约束，注册前请以官方页面为准。', 'Free access is always subject to region, account type, rate limits and expiry — verify the official page before signing up.')}</div>
  </header>
  <main>{_model_catalog_markup(page_models, page_num=page_num, total_pages=total_pages, total_models=model_total, linkable_model_slugs=indexable_model_slugs(model_catalog))}{cn_section}{sections_markup}
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
''' + EDITORIAL_TOKENS_CSS + '''
  .model-center-page { margin: 0; min-height: 100vh; background: var(--canvas); }
  .model-center-page[data-model-center-locale="en"] [lang="zh-CN"], .model-center-page[data-model-center-locale="zh-CN"] [lang="en"] { display: none !important; }
  .model-center-tabs { display: flex; justify-content: flex-start; gap: 8px; margin: 22px 0 26px; padding: 10px 0; border-bottom: 1px solid var(--line); }
  .model-center-tab { border: 1px solid var(--line); border-radius: 9999px; padding: 8px 18px; color: var(--ink-secondary); background: var(--surface); cursor: pointer; font: 600 13px/1.2 var(--font-sans); transition: all .18s; }
  .model-center-tab:hover { border-color: var(--ink-tertiary); color: var(--ink); }
  .model-center-tab[aria-selected="true"] { border-color: var(--ink-solid); color: var(--ink-solid-contrast); background: var(--ink-solid); }
  .model-center-tab small { margin-left: 5px; opacity: .7; font: 500 11px/1.2 var(--font-mono); }
  .model-center-page[data-model-center-tab="all-models"] #categories, .model-center-page[data-model-center-tab="all-models"] #categories ~ * { display: none !important; }
  .model-center-page[data-model-center-tab="all-models"] .model-center-all-models-panel { display: block; }
  .model-center-page:not([data-model-center-tab="all-models"]) .model-center-all-models-panel { display: none; }
  .model-center-all-models-panel { max-width: 1240px; margin: 0 auto; padding: 28px 18px 64px; color: var(--ink); font-family: var(--font-sans); line-height: 1.65; }
  .model-center-all-models-panel .model-center-eyebrow { color: var(--accent); font: 500 11px/1.5 var(--font-mono); letter-spacing: .1em; text-transform: uppercase; }
  .model-center-all-models-panel .model-directory { padding: clamp(20px, 4vw, 36px); border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
  .model-center-all-models-panel .model-directory h2 { margin: 0 0 6px; font-family: var(--font-serif); font-weight: 400; font-size: clamp(23px, 3.5vw, 30px); letter-spacing: -.015em; }
  .model-center-all-models-panel .model-directory h2 small { color: var(--ink-secondary); font-size: 15px; font-weight: 400; }
  .model-center-all-models-panel .section-desc { margin: 0 0 14px; color: var(--ink-secondary); font-size: 14px; }
  .model-center-all-models-panel .catalog-toolbar { display: grid; grid-template-columns: minmax(220px, 1.5fr) minmax(150px, .8fr) minmax(140px, .75fr) auto 1fr; gap: 10px; align-items: end; margin: 18px 0 14px; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); }
  .model-center-all-models-panel .catalog-toolbar label { color: var(--ink-secondary); font: 500 11px/1.6 var(--font-mono); text-transform: uppercase; letter-spacing: .07em; }
  .model-center-all-models-panel .catalog-search-label, .model-center-all-models-panel .catalog-provider-label, .model-center-all-models-panel .catalog-region-label { display: grid; gap: 5px; }
  .model-center-all-models-panel .catalog-toolbar input, .model-center-all-models-panel .catalog-toolbar select { min-height: 38px; border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; color: var(--ink); background: var(--surface); font: inherit; }
  .model-center-all-models-panel .catalog-modes { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
  .model-center-all-models-panel .group-mode { border: 1px solid var(--line); border-radius: 6px; padding: 7px 10px; color: var(--accent); background: transparent; cursor: pointer; font: inherit; font-size: 12px; white-space: nowrap; }
  .model-center-all-models-panel .group-mode.is-active { color: #FFF; background: var(--ink-solid); border-color: var(--ink-solid); }
  .model-center-all-models-panel .provider-filter { border: 0; padding: 0; color: var(--accent); background: transparent; cursor: pointer; text-align: left; font: inherit; font-size: 13px; font-weight: 600; }
  .model-center-all-models-panel .provider-filter:hover { text-decoration: underline; }
  .model-center-all-models-panel .provider-page-link { display: block; margin-top: 3px; color: var(--ink-secondary); font-size: 11px; }
  .model-center-all-models-panel .catalog-count { align-self: center; justify-self: end; color: var(--ink-tertiary); font: 500 11px var(--font-mono); letter-spacing: .05em; white-space: nowrap; }
  .model-center-all-models-panel .catalog-hint { margin: 0 0 12px; color: var(--ink-secondary); font-size: 12px; }
  .model-center-all-models-panel .catalog-table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }
  .model-center-all-models-panel .catalog-table { width: 100%; min-width: 1120px; border-collapse: collapse; font-size: 13px; }
  .model-center-all-models-panel .catalog-table th, .model-center-all-models-panel .catalog-table td { padding: 10px 11px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line-soft); }
  .model-center-all-models-panel .catalog-table thead th { position: sticky; top: 0; z-index: 1; color: var(--ink-tertiary); background: var(--surface-soft); font: 500 11px/1.5 var(--font-mono); letter-spacing: .08em; text-transform: uppercase; white-space: nowrap; }
  .model-center-all-models-panel .catalog-table tbody tr:last-child td { border-bottom: 0; }
  .model-center-all-models-panel .catalog-table small { display: block; margin-top: 3px; color: var(--ink-secondary); font: 400 11px/1.5 var(--font-mono); }
  .model-center-all-models-panel .catalog-table .model-name, .model-center-all-models-panel .catalog-table .model-id { display: block; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .model-center-all-models-panel .catalog-table .model-id { margin-top: 3px; color: var(--ink-tertiary); }
  .model-center-all-models-panel .model-badges { display: flex; flex-wrap: wrap; gap: 4px; min-width: 80px; }
  .model-center-all-models-panel .model-badge { border-radius: 9999px; padding: 2px 8px; color: var(--accent); background: var(--accent-soft); font: 500 11px/1.6 var(--font-mono); white-space: nowrap; }
  .model-center-all-models-panel .status { display: inline-block; border-radius: 9999px; padding: 3px 8px; font: 500 11px/1.5 var(--font-mono); white-space: nowrap; }
  .model-center-all-models-panel .status-online { color: var(--pale-green-text); background: var(--pale-green-bg); }
  .model-center-all-models-panel .status-offline { color: var(--pale-red-text); background: var(--pale-red-bg); }
  .model-center-all-models-panel .status-degraded, .model-center-all-models-panel .status-unknown { color: var(--pale-yellow-text); background: var(--pale-yellow-bg); }
  .model-center-all-models-panel .catalog-group-row th { padding: 13px 11px 7px; color: var(--ink); background: var(--canvas-warm); font-family: var(--font-sans); font-size: 13px; letter-spacing: 0; text-transform: none; }
  .model-center-all-models-panel .catalog-empty { margin: 16px 0 0; padding: 13px 16px; border-radius: 6px; color: var(--pale-yellow-text); background: var(--pale-yellow-bg); }
  .model-center-full-directory { display:flex; align-items:center; justify-content:space-between; gap:18px; margin-top:16px; padding:16px 18px; border:1px solid var(--line); border-radius:14px; background:var(--surface-soft); }
  .model-center-full-directory p { margin:0; color:var(--ink-secondary); font-size:13px; }
  .model-center-full-directory .button { flex:0 0 auto; }
  .model-center-all-models-panel .source-cell { min-width: 100px; white-space: nowrap; }
  .model-center-all-models-panel .freshness { color: var(--ink-secondary); }
  .model-center-all-models-panel .freshness-stale { color: var(--pale-red-text); }
  @media (max-width: 820px) { .model-center-all-models-panel .catalog-toolbar { grid-template-columns: 1fr 1fr; } .model-center-all-models-panel .catalog-modes { grid-column: 1 / -1; } .model-center-all-models-panel .catalog-count { justify-self: start; } }
  @media (max-width: 620px) { .model-center-tabs { justify-content: stretch; } .model-center-tab { flex: 1; padding: 8px 10px; } .model-center-all-models-panel { padding: 14px 8px 38px; } .model-center-all-models-panel .model-directory { border-radius: 8px; padding: 18px; } .model-center-all-models-panel .catalog-toolbar { grid-template-columns: 1fr; } .model-center-all-models-panel .catalog-modes { grid-column: auto; } }
</style>'''


def render_model_center_page(offers: list[dict], site_url: str, models: list[dict]) -> str:
    template_path = Path(__file__).resolve().parents[1] / "design" / "free-china-ai-index.html"
    template = template_path.read_text(encoding="utf-8")
    body_match = re.search(r"<body[^>]*>", template, flags=re.I)
    if not body_match:
        raise ValueError("feature template is missing the body element")
    body_start = body_match.start()
    body_end = template.rindex("</body>")
    head = template[:body_start]
    body = template[body_match.end():body_end]
    title = "模型中心 · 精选资源与全部模型 | FreeLLM"
    description = "FreeLLM 模型中心：先浏览人工核验的特色免费 AI 资源，再切换到完整模型目录，逐行查看中国大陆可用性标注、注册要求（手机号、实名、信用卡）、厂家、上下文、活动和官方来源。"
    page_url = _absolute(site_url, MODEL_CENTER_PAGE_PATH)
    head = re.sub(r"<title>.*?</title>", f"<title>{_esc(title)}</title>", head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{_esc(description)}" />', head, count=1)
    head = re.sub(r'<link rel="canonical"[^>]*>', f'<link rel="canonical" href="{_esc(page_url)}" />', head, count=1)
    head = re.sub(r'<meta name="robots"[^>]*>', '<meta name="robots" content="index,follow,max-image-preview:large" />', head, count=1)
    head = re.sub(r'(?:\s*<link rel="alternate"[^>]+>){3}', f'\n  {_hreflang_links(site_url, MODEL_CENTER_PAGE_PATH)}', head, count=1, flags=re.S)
    head = re.sub(r'(<meta property="og:url" content=")[^"]*("[^>]*>)', rf'\g<1>{_esc(page_url)}\g<2>', head, count=1)
    head = re.sub(r'(<meta name="twitter:url" content=")[^"]*("[^>]*>)', rf'\g<1>{_esc(page_url)}\g<2>', head, count=1)
    head = re.sub(
        r'<html([^>]*)>',
        lambda m: '<html' + (m.group(1) if 'data-default-locale=' in m.group(1) else m.group(1) + ' data-default-locale="zh-CN"') + '>',
        head,
        count=1,
        flags=re.I,
    )
    head = head.replace('href="../css/freellm-pastel-ui.css"', 'href="/css/freellm-pastel-ui.css"')
    head = head.replace("</head>", f'{MODEL_CENTER_STYLE}\n</head>', 1)
    body = body.replace('class="catalog-app"', 'class="catalog-app model-center-featured-app"', 1)
    body = body.replace('href="/models/all/"', 'href="#all-models"')
    preview_models = models[:24]
    catalog_markup = _model_catalog_markup(
        preview_models,
        include_heading=False,
        total_models=len(models),
        linkable_model_slugs=indexable_model_slugs(models),
    )
    catalog_markup += f'''<div class="model-center-full-directory">
      <p>{_locale_pair(
          f"这里先展示 24 条模型作为快速预览；完整 {len(models)} 条目录使用独立分页，避免模型中心重复下载整份大表。",
          f"This tab previews 24 models. Open the paginated directory for all {len(models)} records without downloading the full table twice."
      )}</p>
      <a class="button" href="{ALL_MODELS_PAGE_PATH}">{_locale_pair("打开完整模型目录", "Open full model directory")} →</a>
    </div>'''
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


def _log_model_key(value: object) -> str:
    """Normalize ids so scan keys like "Atria-Dawn-Preview" match offer keys like "Atria Dawn Preview"."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _log_offer_lookup(offers: list[dict] | None) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for offer in offers or []:
        if not isinstance(offer, dict):
            continue
        for field in ("id", "model"):
            key = _log_model_key(offer.get(field))
            if key:
                lookup.setdefault(key, offer)
    return lookup


def _log_event_model_keys(event: dict) -> list[str]:
    details = event.get("details") or {}
    candidates = (
        details.get("canonicalModelId"),
        details.get("model"),
        event.get("id"),
        str(event.get("id") or "").rsplit("/", 1)[-1],
    )
    keys = [_log_model_key(item) for item in candidates]
    return [key for key in dict.fromkeys(keys) if key]


def _log_detail_card(event: dict, offer_lookup: dict[str, dict] | None = None) -> str:
    details = dict(event.get("details") or {})
    if offer_lookup and not details.get("usageGuide") and not details.get("registrationSteps"):
        for key in _log_event_model_keys(event):
            offer = offer_lookup.get(key)
            if offer:
                for field in ("usageGuide", "registrationSteps", "register", "registerLabel", "sourceUrls", "links", "freeLLMTest"):
                    if offer.get(field) not in (None, "", []) and field not in details:
                        details[field] = offer[field]
                break
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
    test_markup = _offer_freellm_test_markup(details)
    return f'''<details class="log-new-card"><summary class="log-card-summary"><span class="log-badge">{badge}</span><h3>{_esc(event.get("title"))}</h3><code>{_esc(event.get("id"))}</code></summary><div class="log-card-body"><dl class="log-facts">{facts or '<div><dt>details</dt><dd>未提供</dd></div>'}</dl>{_log_registration_docs(details)}{test_markup}<div class="log-source"><strong>官方来源 / Official sources</strong>{_log_links(details)}</div><p class="log-reason"><strong>新增依据 / Why new:</strong> {_esc(event.get("reason"))}</p></div></details>'''


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


def _log_event_panel(title_zh: str, title_en: str, content: str, events: list[dict]) -> str:
    if not events:
        return ""
    return f'<section class="log-event-panel"><h3>{_locale_pair(title_zh, title_en)}</h3>{content}</section>'


def _log_event_has_context(event: dict) -> bool:
    details = event.get("details") or {}
    return any(str(details.get(key) or "").strip() for key in ("provider", "productType"))


def _log_event_groups(events: list[dict], curated_events: list[dict] | None = None) -> dict[str, list[dict]]:
    all_events = list(events) + list(curated_events or [])
    return {
        "new": [event for event in all_events if event.get("eventType") in {"new", "new_route"}],
        "recovered": [event for event in all_events if event.get("eventType") == "recovered"],
        "offline": [event for event in all_events if event.get("eventType") == "offline"],
        "unavailable": [
            event
            for event in all_events
            if event.get("eventType") == "source_unavailable" and _log_event_has_context(event)
        ],
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


def render_daily_log_page(logs: list[dict], site_url: str, offers: list[dict] | None = None) -> str:
    """Render the public daily change log as a dashboard with event details."""
    offer_lookup = _log_offer_lookup(offers)
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
        new_markup = "".join(_log_detail_card(event, offer_lookup) for event in groups["new"])
        event_panels = "".join((
            _log_event_panel("新增详情", "New entries", new_markup, groups["new"]),
            _log_event_panel("恢复", "Recovered", _log_event_table(groups["recovered"]), groups["recovered"]),
            _log_event_panel("下线", "Offline", _log_event_table(groups["offline"]), groups["offline"]),
            _log_event_panel("来源异常", "Source issues", _log_event_table(groups["unavailable"]), groups["unavailable"]),
        ))
        empty_state = _log_empty_state(log, groups) if index == 0 else ""
        sections.append(
            f'''<section class="log-day" id="log-day-{_esc(date)}"><div class="log-day-head"><div><span class="log-eyebrow">{_locale_pair("扫描日期", "Scan date")}</span><h2>{_esc(date)}</h2></div><div class="log-day-summary"><span>{_locale_pair(*day_state)}</span><span>{_locale_pair("新增", "New")} {len(groups["new"])}</span><span>{_locale_pair("恢复", "Recovered")} {len(groups["recovered"])}</span><span>{_locale_pair("下线", "Offline")} {len(groups["offline"])}</span><span>{_locale_pair("来源异常", "Source issues")} {len(groups["unavailable"])}</span></div></div>{empty_state}<div class="log-day-snapshot"><span>{_locale_pair("当日快照", "Daily snapshot")}</span><strong>{snapshot["models"]} {_locale_pair("模型", "models")}</strong><strong>{snapshot["providers"]} {_locale_pair("提供商", "providers")}</strong><strong>{snapshot["offers"]} {_locale_pair("资源", "offers")}</strong></div><div class="log-event-grid">{event_panels}</div><section class="log-event-panel log-health-panel"><h3>{_locale_pair("来源健康", "Source health")}</h3>{_log_health_table(log)}</section></section>'''
        )
    body = "".join(sections) or '<section class="log-day"><div class="log-empty"><strong>日志即将开始记录 / The daily log has not started yet.</strong></div></section>'
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "FreeLLM daily discovery log", "url": page_url, "inLanguage": ["zh-CN", "en"], "dateModified": dates[0] if dates else None}
    style = '''<style>
''' + EDITORIAL_TOKENS_CSS + '''
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body { margin:0; color:var(--ink); background:var(--canvas); font:400 15px/1.6 var(--font-sans); -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }
a { color:var(--accent); }
h1,h2,h3,h4 { font-family:var(--font-serif); font-weight:400; color:var(--ink); }
.daily-log-dashboard { max-width:1240px; margin:0 auto; padding:24px 18px 64px; }
.log-hero { padding:clamp(24px,5vw,52px); border:1px solid var(--line); border-radius:8px; background:var(--surface); }
.log-hero-top,.log-day-head { display:flex; justify-content:space-between; gap:20px; align-items:flex-start; flex-wrap:wrap; }
.log-kicker,.log-eyebrow { color:var(--accent); font:500 11px/1.4 var(--font-mono); letter-spacing:.12em; text-transform:uppercase; }
.log-hero h1 { max-width:820px; margin:14px 0 12px; font-size:clamp(36px,6vw,64px); line-height:1.05; letter-spacing:-.02em; }
.log-hero .lead { max-width:760px; margin:0; color:var(--ink-secondary); font-size:16px; line-height:1.7; }
.log-hero-meta { display:grid; grid-template-columns:repeat(3,minmax(100px,1fr)); gap:10px; min-width:min(100%,360px); }
.log-hero-meta div { padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); }
.log-hero-meta span,.log-snapshot-card span { display:block; color:var(--ink-tertiary); font:500 10.5px/1.5 var(--font-mono); letter-spacing:.07em; text-transform:uppercase; }
.log-hero-meta strong { display:block; margin-top:5px; font-family:var(--font-serif); font-weight:400; font-size:21px; letter-spacing:-.01em; }
.log-hero-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:24px; }
.log-hero-actions a { padding:9px 15px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); text-decoration:none; font-size:13px; font-weight:600; transition:all .15s; }
.log-hero-actions a:first-child { background:var(--ink-solid); border-color:var(--ink-solid); color:var(--ink-solid-contrast); }
.log-hero-actions a:hover { border-color:var(--ink-tertiary); }
.log-hero-actions a:first-child:hover { background:var(--ink-solid-hover); border-color:var(--ink-solid-hover); color:var(--ink-solid-contrast); }
.log-date-nav { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin:18px 0 0; padding:10px 12px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); color:var(--ink-secondary); font:400 12px var(--font-mono); }
.log-date-link { padding:5px 10px; border-radius:9999px; color:var(--ink-secondary); text-decoration:none; font-size:11.5px; transition:all .15s; }
.log-date-link:hover { color:var(--ink); background:var(--line-soft); }
.log-date-link.is-active { color:var(--ink-solid-contrast); background:var(--ink-solid); }
.log-overview-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:14px; margin-top:18px; align-items:start; }
.log-panel,.log-snapshot-panel { padding:18px; border:1px solid var(--line); border-radius:8px; background:var(--surface); }
.log-panel h2,.log-snapshot-panel h2 { margin:0 0 12px; font-size:22px; letter-spacing:-.015em; }
.log-stat-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; align-items:start; }
.log-stat-card { min-height:92px; padding:12px 13px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); }
.log-stat-card strong { display:block; margin-top:5px; font-family:var(--font-serif); font-weight:400; font-size:30px; line-height:1; letter-spacing:-.02em; }
.log-stat-card p { margin:5px 0 0; color:var(--ink-secondary); font-size:10.5px; line-height:1.4; }
.log-stat-card.blue { border-top:2px solid var(--accent); }.log-stat-card.green { border-top:2px solid var(--pale-green-text); }.log-stat-card.red { border-top:2px solid var(--pale-red-text); }.log-stat-card.amber { border-top:2px solid var(--pale-yellow-text); }
.log-stat-label { color:var(--ink-secondary); font:500 11px/1.5 var(--font-mono); letter-spacing:.05em; }
.log-snapshot-grid,.log-health-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
.log-snapshot-card { padding:11px 12px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); }.log-snapshot-card strong { display:block; margin-top:3px; font-family:var(--font-serif); font-weight:400; font-size:25px; letter-spacing:-.02em; }.log-snapshot-card small { color:var(--ink-secondary); font-size:10.5px; line-height:1.4; }
.log-health-grid { grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:8px; }.log-health-card { padding:11px 12px; border-radius:8px; background:var(--pale-green-bg); }.log-health-card.issue { background:var(--pale-yellow-bg); }.log-health-card div { display:flex; justify-content:space-between; gap:8px; }.log-health-card span { font-size:11px; font-weight:600; }.log-health-card strong { color:var(--pale-green-text); font:500 11px var(--font-mono); }.log-health-card.issue strong { color:var(--pale-yellow-text); }.log-health-card p { margin:3px 0 0; color:var(--ink-secondary); font-size:10.5px; overflow-wrap:anywhere; }
.log-days { position:relative; margin-top:18px; padding:22px 0 30px; background:transparent; }
.log-days::before { content:""; position:absolute; left:25px; top:96px; bottom:40px; width:1px; background:var(--line); }
.log-section-heading { margin:0 0 22px 70px; }.log-section-heading p { margin:8px 0 0; color:var(--ink-secondary); }
.log-day { position:relative; scroll-margin-top:18px; margin:0 0 18px 70px; padding:18px 20px 20px; border:1px solid var(--line); border-radius:8px; background:var(--surface); }.log-day:last-child { margin-bottom:0; }.log-day::before { content:""; position:absolute; left:-54px; top:22px; width:11px; height:11px; border:3px solid var(--canvas); border-radius:50%; background:var(--accent); z-index:1; }.log-day-head h2 { margin:4px 0 0; font-size:30px; letter-spacing:-.02em; }.log-day-summary { display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; }.log-day-summary span { padding:4px 10px; border-radius:9999px; background:var(--accent-soft); color:var(--accent); font:500 11px/1.6 var(--font-mono); }
.log-empty { margin:18px 0; padding:16px 18px; border:1px dashed var(--line); border-radius:8px; background:var(--surface-soft); }.log-empty.baseline-empty { border-color:var(--ink-tertiary); background:var(--canvas-warm); }.log-empty strong { display:block; }.log-empty p { margin:5px 0 0; color:var(--ink-secondary); font-size:13px; }
.log-day-snapshot { display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin:18px 0; padding:11px 13px; border-radius:8px; background:var(--surface-soft); color:var(--ink-secondary); font:400 12px var(--font-mono); }.log-day-snapshot strong { color:var(--ink); }
.log-event-grid { display:grid; grid-template-columns:1fr; gap:12px; }.log-event-panel { min-width:0; padding:16px 18px; border:1px solid var(--line); border-radius:8px; background:var(--surface); }.log-event-panel h3 { margin:0 0 10px; font-size:18px; }.log-health-panel { margin-top:12px; }.log-event-panel .muted { margin:8px 0; color:var(--ink-secondary); font-size:13px; }
.log-new-card { display:block; margin:10px 0 0; padding:0; border:1px solid var(--line); border-left:3px solid var(--pale-green-text); border-radius:8px; background:var(--surface); overflow:hidden; }.log-new-card[open] { padding-bottom:16px; }.log-card-summary { display:flex; gap:8px; align-items:center; flex-wrap:wrap; padding:12px 16px; cursor:pointer; list-style:none; }.log-card-summary::-webkit-details-marker { display:none; }.log-card-summary::after { content:"＋"; margin-left:auto; color:var(--pale-green-text); font-size:18px; line-height:1; }.log-new-card[open] > .log-card-summary::after { content:"－"; }.log-card-summary h3 { margin:0; font-size:17px; }.log-card-summary code,.log-facts dt,small { color:var(--ink-secondary); font:400 11px/1.6 var(--font-mono); }.log-badge { padding:3px 9px; border-radius:9999px; color:var(--pale-green-text); background:var(--pale-green-bg); font:600 10.5px/1.6 var(--font-mono); }.log-card-body { padding:0 16px; }.log-facts { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; margin:0 0 13px; }.log-facts div { padding:8px 10px; border:1px solid var(--line); border-radius:6px; background:var(--surface-soft); }.log-facts dd { margin:3px 0 0; overflow-wrap:anywhere; font-size:12px; }.log-source { padding-top:10px; border-top:1px solid var(--line-soft); font-size:12px; }.log-links { margin:5px 0; padding-left:17px; overflow-wrap:anywhere; }.log-reason { margin:10px 0 0; color:var(--ink-secondary); font-size:12px; }
.log-registration { margin:12px 0; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--canvas-warm); }.log-registration h4 { margin:0; font-size:15px; }.log-registration ol { margin:7px 0 0; padding-left:20px; }.log-registration li { margin:3px 0; font-size:12px; }.log-registration .muted { margin:7px 0 0; }.log-registration-links { display:flex; flex-wrap:wrap; gap:7px; margin-top:10px; }.log-registration-link { padding:5px 10px; border:1px solid var(--line); border-radius:9999px; background:var(--surface); color:var(--accent); font-size:11px; text-decoration:none; }.log-registration-link:hover { border-color:var(--accent); }
.table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:8px; background:var(--surface); }.table-wrap table { width:100%; min-width:520px; border-collapse:collapse; font-size:12.5px; }.table-wrap th,.table-wrap td { padding:9px 11px; border-bottom:1px solid var(--line-soft); text-align:left; vertical-align:top; }.table-wrap th { color:var(--ink-tertiary); background:var(--surface-soft); font:500 10.5px/1.5 var(--font-mono); letter-spacing:.07em; text-transform:uppercase; }.table-wrap tr:last-child td { border-bottom:0; }.table-wrap td small { display:block; margin-top:3px; }.health-pill { display:inline-block; padding:3px 9px; border-radius:9999px; background:var(--pale-green-bg); color:var(--pale-green-text); font:500 11px/1.6 var(--font-mono); }.health-pill.issue { background:var(--pale-yellow-bg); color:var(--pale-yellow-text); }
.log-footer { margin-top:36px; padding-top:20px; border-top:1px solid var(--line); color:var(--ink-secondary); font-size:12.5px; line-height:1.7; }
@media (max-width:900px) { .log-overview-grid { grid-template-columns:1fr; } }
@media (max-width:720px) { .daily-log-dashboard { padding:12px 8px 42px; }.log-hero { padding:22px 18px; }.log-hero-meta { grid-template-columns:1fr; }.log-stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.log-snapshot-grid,.log-health-grid,.log-event-grid { grid-template-columns:1fr; }.log-days { padding:16px 0; }.log-days::before { left:17px; top:92px; bottom:34px; }.log-section-heading { margin-left:42px; }.log-day { margin-left:42px; padding:16px 14px; }.log-day::before { left:-34px; top:20px; width:10px; height:10px; }.log-day-summary { justify-content:flex-start; } }
</style>'''
    style += STATIC_LOCALE_SCRIPT
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>每日更新 · FreeLLM</title><meta name="description" content="FreeLLM 每日检查官方来源，记录 AI 资源的新增、恢复、下线和异常，并保留可核对的官方证据。"><link rel="canonical" href="{_esc(page_url)}">{_hreflang_links(site_url, CHANGE_LOG_PAGE_PATH)}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>{ADSENSE_SCRIPT}{VERCEL_ANALYTICS_SCRIPT}{GA4_SCRIPT}{STATIC_LOCALE_STYLE}</head><body data-static-locale="true"><main class="daily-log-dashboard"><header class="log-hero"><div class="log-hero-top"><div><div class="log-kicker">DAILY UPDATES / 每日更新</div><h1>{_locale_pair('今天的 AI 资源有什么变化？', 'What changed in AI today?')}</h1><p class="lead">{_locale_pair('我们每天检查官方来源，记录新增、恢复、下线和异常。', 'We check official sources daily and record new, recovered, offline and source issues.')}</p></div><div class="log-hero-meta"><div><span>{_locale_pair('最新日期', 'Latest date')}</span><strong>{_esc(dates[0] if dates else '—')}</strong></div><div><span>{_locale_pair('扫描状态', 'Scan status')}</span><strong>{_locale_pair('今日扫描完成', 'Scan complete')}</strong></div><div><span>{_locale_pair('目录状态', 'Directory state')}</span><strong>{_locale_pair(latest_status, latest_status_en)}</strong></div></div></div><div class="log-hero-actions"><a href="{_esc(_absolute(site_url, '/'))}">{_locale_pair('返回首页', 'Back to FreeLLM')}</a><a href="{_esc(_absolute(site_url, ALL_MODELS_PAGE_PATH))}">{_locale_pair('查看模型目录', 'Open model directory')}</a></div></header>{date_nav}<section class="log-overview-grid"><section class="log-panel"><h2>{_locale_pair('今日变化', "Today's changes")}</h2><div class="log-stat-grid">{_log_stat_cards(latest_groups)}</div></section><section class="log-snapshot-panel"><h2>{_locale_pair('当前目录快照', 'Current snapshot')}</h2><div class="log-snapshot-grid">{_log_snapshot_cards(latest_snapshot)}</div><div class="log-health-grid">{_log_health_cards(latest)}</div></section></section><section class="log-days"><div class="log-section-heading"><span class="log-eyebrow">CHANGE STREAM / 变更流</span><p>{_locale_pair('按日期查看变更与来源健康状态。', 'Review changes and source health by date.')}</p></div>{body}</section><footer class="log-footer"><p>{_locale_pair('下线只在来源成功时判定；来源抓取失败不会被误报为下线。', 'Offline is only recorded after a successful source snapshot; a failed fetch is never treated as offline.')}</p>{_static_locale_nav()}</footer></main>{style}</body></html>'''


    canonical = f'<link rel="canonical" href="{_esc(page_url)}">'
    share_title = "每日更新 · FreeLLM"
    share_description = "FreeLLM 每日检查官方来源，记录 AI 资源的新增、恢复、下线和异常，并保留可核对的官方证据。"
    share_image = _absolute(site_url, SHARE_IMAGE_PATH)
    social = (
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        '<meta property="og:type" content="website">'
        f'<meta property="og:title" content="{_esc(share_title)}">'
        f'<meta property="og:description" content="{_esc(share_description)}">'
        f'<meta property="og:url" content="{_esc(page_url)}">'
        f'<meta property="og:image" content="{_esc(share_image)}">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:url" content="{_esc(page_url)}">'
        f'<meta name="twitter:title" content="{_esc(share_title)}">'
        f'<meta name="twitter:description" content="{_esc(share_description)}">'
        f'<meta name="twitter:image" content="{_esc(share_image)}">'
    )
    return page.replace(canonical, canonical + social, 1)


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


def _format_star_count(value) -> str:
    if not isinstance(value, int) or value < 0:
        return ""
    return f"{value / 1000:.1f}k".replace(".0k", "k") if value >= 1000 else str(value)


def _skill_link_chip(skill: dict) -> str:
    check = skill.get("linkCheck")
    if check in {"ok", "readme_only"} and skill.get("contentPath"):
        return '<span class="skill-link-chip ok"><span lang="zh-CN">原文已收录</span><span lang="en">Source indexed</span></span>'
    if check == "repo_not_found":
        return '<span class="skill-link-chip warn"><span lang="zh-CN">仓库无法访问</span><span lang="en">Repo unreachable</span></span>'
    if check in {"skill_file_not_found", "invalid_url"}:
        return '<span class="skill-link-chip warn"><span lang="zh-CN">SKILL.md 待定位</span><span lang="en">SKILL.md not located</span></span>'
    return ""


def _style_preview(entry: dict) -> str:
    """One-line summary of a skill's presentation styles, e.g. "36 套主题 · tokyo-night / … +33"."""
    summary = str(entry.get("summary") or "").strip()
    items = [str(item).strip() for item in entry.get("items") or [] if str(item).strip()]
    if not items:
        return summary
    total = entry.get("total")
    count = total if isinstance(total, int) and not isinstance(total, bool) and total >= len(items) else len(items)
    preview = " / ".join(items[:3])
    extra = count - 3
    if extra > 0:
        preview += f" +{extra}"
    return f"{summary} · {preview}" if summary else preview


def _skill_style_line(skill: dict) -> str:
    entry = skill.get("styles")
    if not isinstance(entry, dict) or not entry.get("hasStyles"):
        return ""
    text = _style_preview(entry)
    if not text:
        return ""
    return f'<div class="skill-style"><span class="skill-style-label">样式</span><span class="skill-style-text">{_esc(text)}</span></div>'


def _skill_test_markup(skill: dict) -> str:
    test = skill.get("freeLLMTest") or {}
    if not test:
        return ""
    status = str(test.get("status") or "待测试")
    level = str(test.get("testLevel") or "")
    tested_at = str(test.get("testedAt") or "")
    environment = str(test.get("environment") or "")
    task = str(test.get("task") or "")
    evaluation = str(test.get("evaluation") or "")
    score = test.get("score")

    if level == "blocked":
        lead, state_class = "BLOCKED", "blocked"
    elif level == "partial":
        lead, state_class = "PARTIAL", "partial"
    elif level == "task":
        lead = f"{score:g}/10" if isinstance(score, (int, float)) else "TASK"
        state_class = "task"
    elif level == "artifact":
        lead = f"{score:g}/10" if isinstance(score, (int, float)) else "ARTIFACT"
        state_class = "partial" if "部分" in status else "tested"
    elif level == "e2e":
        lead = f"{score:g}/10" if isinstance(score, (int, float)) else "E2E"
        state_class = "tested"
    else:
        lead = f"{score:g}/10" if isinstance(score, (int, float)) else "TEST"
        state_class = "pending"

    label = f"FreeLLM 真测 · {status}"
    evidence_links = []
    for index, evidence in enumerate(test.get("evidence") or [], start=1):
        if isinstance(evidence, str):
            url, name = evidence, f"证据 {index}"
        elif isinstance(evidence, dict):
            url = str(evidence.get("url") or "")
            name = str(evidence.get("label") or evidence.get("title") or f"证据 {index}")
        else:
            continue
        if url:
            evidence_links.append(f'<a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(name)} ↗</a>')
    evidence_markup = '<div class="freellm-test-evidence">' + "".join(evidence_links) + "</div>" if evidence_links else ""
    environment_markup = f'<p><strong>环境：</strong>{_esc(environment)}</p>' if environment else ""
    detail = (
        '<details class="freellm-test-inline"><summary>查看真实测试任务、限制与评价</summary>'
        '<div class="freellm-test-inline-body">'
        f'<p><strong>测试任务：</strong>{_esc(task)}</p>'
        f'<p><strong>评价：</strong>{_esc(evaluation)}</p>'
        f'{environment_markup}'
        f'<p><strong>测试时间：</strong>{_esc(tested_at)} · {_esc(level)}</p>'
        f'{evidence_markup}</div></details>'
    )
    return (
        f'<div class="freellm-test-strip {state_class}"><strong>{_esc(lead)}</strong>'
        f'<span>{_esc(label)}</span><small>{_esc(level)}</small></div>' + detail
    )

def _skill_card(skill: dict) -> str:
    category = SKILL_CATEGORY_DEFINITIONS.get(skill.get("category"), {})
    status_zh, status_en = SKILL_STATUS_LABELS.get(skill.get("status"), ("待核验", "Needs review"))
    compatibility = "".join(f'<span class="skill-chip">{_esc(item)}</span>' for item in skill.get("compatibility") or [])
    github = str(skill.get("githubUrl") or "").strip()
    source = (
        f'<a class="skill-source-link" href="{_esc(github)}" target="_blank" rel="nofollow noopener">打开 GitHub ↗</a>'
        if github else '<span class="skill-source-missing">来源链接待补充</span>'
    )
    status_class = "verified" if skill.get("status") == "verified" else "review"
    stars = _format_star_count((skill.get("repoStats") or {}).get("stars"))
    review_count = len(skill.get("reviews") or [])
    meta = '<div class="skill-card-meta">'
    meta += f'<span class="skill-stat">★ {_esc(stars)}</span>' if stars else '<span class="skill-stat is-muted">★ —</span>'
    if review_count:
        meta += f'<span class="skill-stat">{review_count} <span lang="zh-CN">条社区评价</span><span lang="en">community reviews</span></span>'
    meta += _skill_link_chip(skill) + "</div>"
    description_zh = skill.get("description_zh") or skill.get("description") or ""
    description_en = skill.get("description") or ""
    test_markup = _skill_test_markup(skill)
    return f'''<article class="skill-card" data-skill-id="{_esc(skill.get('id'))}" data-category="{_esc(skill.get('category'))}" data-status="{_esc(skill.get('status'))}">
      <div class="skill-card-top"><span class="skill-category {category.get('accent', 'blue')}">{_esc(category.get('name_zh', 'Skill'))}</span><span class="skill-status {status_class}"><span lang="zh-CN">{_esc(status_zh)}</span><span lang="en">{_esc(status_en)}</span></span></div>
      <h2>{_esc(skill.get('name'))}</h2>{test_markup}<p><span class="skill-description-zh" lang="zh-CN">{_esc(description_zh)}</span><span class="skill-description-en" lang="en">{_esc(description_en)}</span></p>{_skill_style_line(skill)}<div class="skill-chips">{compatibility}</div>{meta}
      <div class="skill-card-bottom"><button class="skill-details" type="button" data-skill-id="{_esc(skill.get('id'))}"><span lang="zh-CN">查看 SKILL.md 与社区参考 →</span><span lang="en">Source &amp; community reference →</span></button>{source}</div>
    </article>'''
def _legacy_render_skills_page(skills: list[dict], site_url: str) -> str:
    path = SKILLS_PAGE_PATH
    title = "Agent Skills 市集 · FreeLLM"
    description = "FreeLLM 对 Agent Skill 做固定任务实测：记录任务、环境、结果、阻塞点、实际产物和自己的评价；GitHub 与社区数据仅作为参考。"
    page_url = _absolute(site_url, path)
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": page_url,
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "FreeLLM 免费 AI 资源索引", "item": _absolute(site_url, "/")},
                {"@type": "ListItem", "position": 2, "name": title, "item": page_url},
            ],
        },
        "mainEntity": {"@type": "ItemList", "numberOfItems": len(skills), "itemListElement": [
            {"@type": "ListItem", "position": index, "name": skill.get("name"), "url": page_url}
            for index, skill in enumerate(skills, start=1)
        ]},
    }
    serialized = json.dumps(skills, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    cards = "".join(_skill_card(skill) for skill in skills)
    category_buttons = "".join(
        f'<button class="skill-category-tab" type="button" data-category="{_esc(key)}"><span>{_esc(value["name_zh"])}</span><small>{sum(item.get("category") == key for item in skills):02d}</small></button>'
        for key, value in SKILL_CATEGORY_DEFINITIONS.items()
        if any(item.get("category") == key for item in skills)
    )
    style = r'''
    :root { color-scheme: light; --canvas:#FBFBFA; --canvas-warm:#F7F6F3; --surface:#FFFFFF; --surface-soft:#F9F9F8; --ink:#2F3437; --ink-secondary:#787774; --ink-tertiary:#B4B4B0; --line:#EAEAEA; --line-soft:rgba(0,0,0,.04); --ink-solid:#111111; --accent:#1744E8; --accent-soft:#E9EEFF; --pale-green-bg:#EDF3EC; --pale-green-text:#346538; --pale-yellow-bg:#FBF3DB; --pale-yellow-text:#956400; --pale-stone-bg:#F0EFEC; --pale-stone-text:#5A5854; --code-bg:#111111; --code-text:#F4F2EE; --card-shadow:0 2px 8px rgba(0,0,0,.04); --modal-shadow:0 20px 60px rgba(0,0,0,.12); --font-serif:'Instrument Serif','Noto Serif SC',Georgia,'Songti SC','SimSun',serif; --font-sans:'Manrope','PingFang SC','Hiragino Sans GB','Microsoft YaHei',ui-sans-serif,system-ui,sans-serif; --font-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace; }
    :root[data-theme="dark"] { color-scheme: dark; --canvas:#0E0F11; --canvas-warm:#14161A; --surface:#181B20; --surface-soft:#1E2127; --ink:#ECEAE6; --ink-secondary:#A7A5A0; --ink-tertiary:#6E6C68; --line:#26292F; --line-soft:rgba(255,255,255,.04); --ink-solid:#F4F2EE; --accent:#7BC0E5; --accent-soft:#0E2533; --pale-green-bg:#112218; --pale-green-text:#86C098; --pale-yellow-bg:#2B2010; --pale-yellow-text:#D9A85F; --pale-stone-bg:#232220; --pale-stone-text:#B4B1AB; --code-bg:#1E2127; --code-text:#ECEAE6; --card-shadow:0 2px 8px rgba(0,0,0,.3); --modal-shadow:0 20px 60px rgba(0,0,0,.5); }
    * { box-sizing:border-box; } html { scroll-behavior:smooth; } body { margin:0; min-width:320px; background:var(--canvas); color:var(--ink); font:400 15px/1.6 var(--font-sans); -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; } a { color:inherit; } button,input,select { font:inherit; } h1,h2,h3 { font-family:var(--font-serif); font-weight:400; }
    ::selection { background:var(--accent-soft); }
    .skills-page { max-width:1240px; margin:0 auto; padding:20px 32px 72px; }
    .skills-header { display:flex; gap:20px; align-items:center; justify-content:space-between; padding:10px 0 24px; border-bottom:1px solid var(--line); }
    .brand { display:flex; gap:11px; align-items:center; text-decoration:none; } .brand-mark { display:grid; place-items:center; width:34px; height:34px; border-radius:8px; color:#fff; background:var(--accent); font-size:19px; } .brand-name { display:block; font-family:var(--font-serif); font-size:21px; letter-spacing:-.02em; line-height:1.1; } .brand-sub { display:block; color:var(--ink-tertiary); font:500 10px/1.4 var(--font-mono); letter-spacing:.1em; text-transform:uppercase; margin-top:3px; }
    .header-right { display:flex; gap:16px; align-items:center; } .top-nav { display:flex; gap:18px; align-items:center; overflow-x:auto; white-space:nowrap; font-size:13px; scrollbar-width:none; } .top-nav::-webkit-scrollbar { display:none; } .top-nav a { text-decoration:none; color:var(--ink-secondary); transition:color .15s; } .top-nav a:hover { color:var(--ink); } .top-nav a[aria-current="page"] { color:var(--ink); font-weight:600; }
    .theme-toggle { width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); cursor:pointer; transition:all .2s; font-size:14px; line-height:1; padding:0; flex-shrink:0; } .theme-toggle:hover { background:var(--line-soft); border-color:var(--ink-tertiary); } .theme-toggle .icon-sun { display:none; } .theme-toggle .icon-moon { display:inline; } :root[data-theme="dark"] .theme-toggle .icon-sun { display:inline; } :root[data-theme="dark"] .theme-toggle .icon-moon { display:none; }
    .skills-hero { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(280px,.7fr); gap:40px; align-items:end; padding:60px 0 36px; } .eyebrow { color:var(--accent); font:500 11px/1.3 var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .skills-hero h1 { max-width:640px; margin:14px 0 16px; font-size:clamp(40px,4.6vw,58px); line-height:1.12; letter-spacing:-.02em; } .hero-copy { max-width:560px; margin:0; color:var(--ink-secondary); font-size:16px; line-height:1.7; }
    .hero-note { padding:26px 26px 24px; border:1px solid var(--line); border-radius:8px; background:var(--surface); } .hero-note-label { display:block; color:var(--ink-tertiary); font:500 10px/1 var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .hero-note-value { display:flex; gap:10px; align-items:baseline; margin:12px 0 10px; } .hero-note-value strong { font-family:var(--font-serif); font-size:56px; font-weight:400; line-height:.9; letter-spacing:-.03em; color:var(--ink); } .hero-note-value span { color:var(--ink-secondary); font-size:14px; } .hero-note p { margin:0; color:var(--ink-secondary); font-size:13px; line-height:1.65; }
    .skills-toolbar { display:flex; gap:12px; align-items:center; flex-wrap:wrap; padding:16px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); } .skills-search { flex:1 1 300px; min-width:220px; padding:10px 14px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); outline:none; transition:border-color .15s, box-shadow .15s; } .skills-search:focus { border-color:var(--ink); box-shadow:0 0 0 3px var(--line-soft); } .skills-search::placeholder { color:var(--ink-tertiary); } .skills-status-filter { padding:10px 12px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); cursor:pointer; } .skills-count { margin-left:auto; color:var(--ink-tertiary); font:500 11px var(--font-mono); letter-spacing:.05em; }
    .skill-category-tabs { display:flex; gap:8px; overflow-x:auto; padding:20px 0 16px; scrollbar-width:none; } .skill-category-tabs::-webkit-scrollbar { display:none; } .skill-category-tab { display:flex; gap:12px; align-items:center; padding:8px 14px; border:1px solid var(--line); border-radius:9999px; background:var(--surface); color:var(--ink-secondary); cursor:pointer; font-size:13px; white-space:nowrap; transition:all .18s; } .skill-category-tab:hover { color:var(--ink); border-color:var(--ink-tertiary); } .skill-category-tab.is-active { border-color:var(--accent); background:var(--accent-soft); color:var(--accent); font-weight:600; } .skill-category-tab small { color:var(--ink-tertiary); font:500 10px var(--font-mono); } .skill-category-tab.is-active small { color:var(--accent); }
    .skill-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; align-items:start; } .skill-card { min-width:0; display:flex; flex-direction:column; min-height:0; align-self:start; padding:18px; border:1px solid var(--line); border-radius:8px; background:var(--surface); transition:box-shadow .2s, transform .2s; } .skill-card:hover { box-shadow:var(--card-shadow); transform:translateY(-1px); }
    .skill-card-top,.skill-card-bottom { display:flex; gap:8px; align-items:center; justify-content:space-between; } .skill-category,.skill-status { display:inline-flex; align-items:center; padding:3px 10px; border-radius:9999px; font:500 10px/1.8 var(--font-mono); letter-spacing:.05em; white-space:nowrap; } .skill-category.blue { background:var(--accent-soft); color:var(--accent); } .skill-category.yellow { background:var(--pale-yellow-bg); color:var(--pale-yellow-text); } .skill-category.green { background:var(--pale-green-bg); color:var(--pale-green-text); } .skill-category.violet { background:var(--pale-stone-bg); color:var(--pale-stone-text); } .skill-status.review { background:var(--pale-stone-bg); color:var(--pale-stone-text); } .skill-status.verified { background:var(--pale-green-bg); color:var(--pale-green-text); }
    .skill-card h2 { margin:14px 0 7px; font:500 16px/1.4 var(--font-mono); letter-spacing:-.01em; color:var(--ink); overflow-wrap:anywhere; } .skill-card p { display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:4; overflow:hidden; min-height:0; margin:0; color:var(--ink-secondary); font-size:13.5px; line-height:1.65; } .skill-chips { display:flex; flex-wrap:wrap; gap:6px; margin:12px 0 0; } .skill-chip { padding:3px 9px; border:1px solid var(--line); border-radius:9999px; color:var(--ink-secondary); font:400 10.5px/1.7 var(--font-mono); } .skill-card-bottom { gap:10px; justify-content:flex-start; margin-top:14px; padding-top:14px; border-top:1px solid var(--line-soft); } .skill-details,.skill-source-link { color:var(--accent); font-size:12.5px; font-weight:500; text-decoration:none; transition:opacity .15s; } .skill-details { padding:0; border:0; background:none; cursor:pointer; } .skill-details:hover,.skill-source-link:hover { opacity:.72; } .skill-source-link { margin-left:auto; } .skill-source-missing { margin-left:auto; color:var(--ink-tertiary); font-size:11px; }
    .skills-empty { padding:60px 18px; text-align:center; color:var(--ink-tertiary); border:1px dashed var(--line); border-radius:8px; background:var(--surface); } .skills-empty button { margin-top:10px; padding:8px 16px; border:1px solid var(--line); border-radius:6px; color:var(--accent); background:var(--surface); cursor:pointer; font-weight:500; transition:all .15s; } .skills-empty button:hover { border-color:var(--accent); }
    dialog { width:min(760px,calc(100% - 28px)); max-height:calc(100% - 40px); padding:0; border:1px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink); box-shadow:var(--modal-shadow); } dialog::backdrop { background:rgba(0,0,0,.4); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); } .skill-dialog-body { padding:28px; } .skill-dialog-close { float:right; display:grid; place-items:center; width:30px; height:30px; border:0; border-radius:50%; background:none; color:var(--ink-secondary); font-size:20px; cursor:pointer; transition:all .15s; } .skill-dialog-close:hover { background:var(--line-soft); color:var(--ink); } .skill-dialog-body h2 { margin:0 40px 10px 0; font-family:var(--font-mono); font-size:21px; font-weight:500; letter-spacing:-.01em; overflow-wrap:anywhere; } .skill-dialog-body p { color:var(--ink-secondary); line-height:1.7; } .command-box { display:flex; gap:10px; align-items:center; margin:20px 0; padding:14px; border-radius:8px; background:var(--code-bg); color:var(--code-text); } .command-box code { flex:1; overflow:auto; font:400 12px/1.6 var(--font-mono); white-space:pre-wrap; } .copy-command { padding:7px 12px; border:1px solid rgba(255,255,255,.28); border-radius:6px; color:var(--code-text); background:transparent; cursor:pointer; white-space:nowrap; font-size:12px; transition:all .15s; } .copy-command:hover { background:rgba(255,255,255,.08); } .dialog-actions { display:flex; gap:12px; align-items:center; } .dialog-actions a { color:var(--accent); font-size:13px; font-weight:500; text-decoration:none; } .dialog-actions a:hover { opacity:.72; } .muted { color:var(--ink-tertiary); font-size:12px; }
    .skill-dialog-stats { display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 0; } .skill-dialog-stats .stat-chip { padding:4px 10px; border:1px solid var(--line); border-radius:9999px; font:500 11px var(--font-mono); color:var(--ink-secondary); }
    .skill-dialog-section { margin-top:22px; padding-top:16px; border-top:1px solid var(--line); } .skill-dialog-section h3 { margin:0 0 10px; font:500 11px/1.4 var(--font-mono); letter-spacing:.12em; text-transform:uppercase; color:var(--ink-tertiary); }
    .skill-content-meta { margin:0 0 8px; color:var(--ink-tertiary); font-size:11.5px; } .skill-content-meta a { color:var(--accent); text-decoration:none; } .skill-content-meta a:hover { opacity:.72; }
    .skill-content { max-height:300px; overflow:auto; margin:0; padding:14px; border-radius:8px; background:var(--code-bg); color:var(--code-text); font:400 11.5px/1.65 var(--font-mono); white-space:pre-wrap; overflow-wrap:anywhere; } .skill-content.is-error { background:var(--pale-yellow-bg); color:var(--pale-yellow-text); }
    .skill-review-list { list-style:none; margin:0; padding:0; display:grid; gap:10px; } .skill-review-item { padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); } .skill-review-item blockquote { margin:0 0 8px; font-size:13px; line-height:1.7; color:var(--ink); } .skill-review-item .review-meta { display:flex; flex-wrap:wrap; gap:8px; align-items:center; font:500 11px var(--font-mono); color:var(--ink-tertiary); } .skill-review-item .review-meta a { color:var(--accent); text-decoration:none; } .skill-review-item.is-empty { color:var(--ink-tertiary); font-size:12.5px; }
    .skill-sentiment { padding:2px 8px; border-radius:9999px; font:500 10px/1.8 var(--font-mono); text-transform:uppercase; letter-spacing:.05em; } .skill-sentiment.positive { background:var(--pale-green-bg); color:var(--pale-green-text); } .skill-sentiment.mixed { background:var(--pale-yellow-bg); color:var(--pale-yellow-text); } .skill-sentiment.negative { background:var(--pale-yellow-bg); color:var(--pale-yellow-text); } .skill-sentiment.neutral { background:var(--pale-stone-bg); color:var(--pale-stone-text); }
    .skill-card-meta { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:14px 0 0; } .skill-stat { font:500 11px var(--font-mono); color:var(--ink-secondary); } .skill-stat.is-muted { color:var(--ink-tertiary); } .skill-link-chip { padding:3px 9px; border-radius:9999px; font:500 10px/1.8 var(--font-mono); } .skill-link-chip.ok { background:var(--pale-green-bg); color:var(--pale-green-text); } .skill-link-chip.warn { background:var(--pale-yellow-bg); color:var(--pale-yellow-text); } .skill-dialog-body { max-height:calc(100vh - 42px); overflow:auto; }
    .skills-footer { display:flex; gap:16px; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-top:36px; padding-top:20px; border-top:1px solid var(--line); color:var(--ink-tertiary); font-size:12.5px; line-height:1.7; } .skills-footer p { max-width:760px; margin:0; }
    @media (max-width:900px) { .skills-hero { grid-template-columns:1fr; gap:24px; padding-top:40px; } .hero-note { max-width:440px; } .skill-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
    .skill-style { display:flex; gap:8px; align-items:baseline; margin:10px 0 0; padding:8px 10px; background:var(--surface-soft); border:1px solid var(--line); border-radius:6px; } .skill-style-label { flex:none; color:var(--accent); font:500 10px/1.6 var(--font-mono); letter-spacing:.1em; text-transform:uppercase; } .skill-style-text { min-width:0; color:var(--ink-secondary); font-size:12.5px; line-height:1.55; }
    .skill-style-chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; } .skill-style-chips:empty { margin:0; } .style-chip { padding:3px 9px; border:1px solid var(--line); border-radius:999px; background:var(--surface); font:400 11.5px/1.5 var(--font-mono); color:var(--ink-secondary); } .style-more { align-self:center; color:var(--ink-tertiary); font:500 11px/1.5 var(--font-mono); }
    .skill-preview-layout { display:grid; grid-template-columns:minmax(0,.85fr) minmax(250px,1.15fr); gap:16px; align-items:stretch; } .skill-preview-copy { display:flex; min-width:0; flex-direction:column; justify-content:center; } .skill-preview-label { color:var(--ink-tertiary); font:500 10px/1.4 var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .skill-preview-format { margin:8px 0 0; color:var(--ink); font:500 15px/1.45 var(--font-mono); overflow-wrap:anywhere; } .skill-preview-summary { margin:8px 0 0; color:var(--ink-secondary); font-size:12.5px; line-height:1.6; } .skill-preview-tags { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; } .skill-preview-tag { padding:3px 8px; border:1px solid var(--line); border-radius:999px; color:var(--accent); background:var(--accent-soft); font:500 10.5px/1.5 var(--font-mono); }
    .skill-preview-canvas { min-height:168px; padding:12px; border:1px solid var(--line); border-radius:8px; background:linear-gradient(135deg,var(--accent-soft),var(--surface-soft)); overflow:hidden; } .skill-preview-window { height:100%; min-height:144px; overflow:hidden; border:1px solid var(--line); border-radius:6px; background:var(--surface); box-shadow:0 8px 24px rgba(30,40,60,.08); } .skill-preview-window-bar { display:flex; gap:5px; align-items:center; height:25px; padding:0 9px; border-bottom:1px solid var(--line); background:var(--surface-soft); } .skill-preview-window-bar i { width:6px; height:6px; border-radius:50%; background:var(--line); } .skill-preview-window-bar i:first-child { background:var(--accent); } .skill-preview-window-bar span { margin-left:5px; overflow:hidden; color:var(--ink-tertiary); font:500 9px/1 var(--font-mono); text-overflow:ellipsis; white-space:nowrap; } .skill-preview-window-main { display:grid; gap:8px; padding:14px; } .skill-preview-kicker { width:32%; height:6px; border-radius:4px; background:var(--accent); opacity:.65; } .skill-preview-title-line { width:74%; height:13px; border-radius:4px; background:var(--ink); opacity:.82; } .skill-preview-copy-line { width:92%; height:6px; border-radius:4px; background:var(--line); } .skill-preview-copy-line.short { width:66%; } .skill-preview-blocks { display:grid; grid-template-columns:repeat(3,1fr); gap:7px; margin-top:5px; } .skill-preview-block { height:45px; border:1px solid var(--line); border-radius:5px; background:linear-gradient(160deg,var(--surface),var(--surface-soft)); } .skill-preview-block::before { display:block; width:42%; height:6px; margin:9px 8px 7px; border-radius:4px; background:var(--accent); content:""; opacity:.48; } .skill-preview-block::after { display:block; width:64%; height:5px; margin-left:8px; border-radius:4px; background:var(--line); content:""; box-shadow:0 9px 0 var(--line); } .skill-preview-canvas.code { background:linear-gradient(135deg,#17202b,#30465c); } .skill-preview-canvas.code .skill-preview-window { border-color:#53687b; background:#111820; } .skill-preview-canvas.code .skill-preview-window-bar { border-color:#293743; background:#1c2732; } .skill-preview-canvas.code .skill-preview-copy-line,.skill-preview-canvas.code .skill-preview-block { border-color:#293743; background:#1b2731; } .skill-preview-canvas.code .skill-preview-title-line { background:#e5f2ff; } .skill-preview-canvas.visual { background:linear-gradient(135deg,#e9e1ff,#ffe7d4); } .skill-preview-canvas.visual .skill-preview-kicker { background:#7c4dff; } .skill-preview-canvas.data { background:linear-gradient(135deg,#dff4e8,#e1ecff); } .skill-preview-canvas.data .skill-preview-blocks { grid-template-columns:1.3fr .8fr .8fr; } .skill-preview-canvas.document { background:linear-gradient(135deg,#f4efdf,#e7edf8); } .skill-preview-canvas.document .skill-preview-blocks { grid-template-columns:1fr 1fr; } .skill-preview-canvas.document .skill-preview-block:last-child { display:none; }
    #dialog-style-section .skill-style-format { margin:0; } #dialog-style-section .skill-style-format code { font:500 12px/1.5 var(--font-mono); color:var(--ink); background:var(--surface-soft); border:1px solid var(--line); border-radius:4px; padding:2px 8px; } #dialog-style-summary { margin:10px 0 0; color:var(--ink-secondary); font-size:13.5px; line-height:1.65; }
    @media (max-width:800px) { .skills-page { padding:12px 18px 48px; } .skills-header { align-items:flex-start; flex-direction:column; } .header-right { width:100%; justify-content:space-between; } .skills-count { margin-left:0; } .skill-preview-layout { grid-template-columns:1fr; } } @media (max-width:560px) { .skills-hero h1 { font-size:36px; } .skill-grid { grid-template-columns:1fr; } .skill-card p { -webkit-line-clamp:5; } .skill-preview-canvas { min-height:150px; } }
    '''
    script = r'''
    (() => {
      const skills = JSON.parse(document.getElementById('skill-data').textContent); const grid = document.getElementById('skill-grid'); const search = document.getElementById('skill-search'); const status = document.getElementById('skill-status'); const count = document.getElementById('skill-count'); const empty = document.getElementById('skill-empty'); const dialog = document.getElementById('skill-dialog'); let category = 'all'; let current = null;
      const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, character => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[character])); const statusLabel = value => value === 'verified' ? '已核验' : value === 'candidate' ? '社区候选' : '待核验'; const categoryLabel = value => CATEGORY_MAP[value] || 'Skill'; const isEn = () => document.documentElement.lang === 'en';
      const formatCount = value => typeof value === 'number' && value >= 0 ? (value >= 1000 ? `${(value / 1000).toFixed(1)}k`.replace('.0k', 'k') : String(value)) : null; const reviewsOf = skill => Array.isArray(skill.reviews) ? skill.reviews : [];
      const linkChip = skill => { const check = skill.linkCheck; if ((check === 'ok' || check === 'readme_only') && skill.contentPath) return `<span class="skill-link-chip ok"><span lang="zh-CN">原文已收录</span><span lang="en">Source indexed</span></span>`; if (check === 'repo_not_found') return `<span class="skill-link-chip warn"><span lang="zh-CN">仓库无法访问</span><span lang="en">Repo unreachable</span></span>`; if (check === 'skill_file_not_found' || check === 'invalid_url') return `<span class="skill-link-chip warn"><span lang="zh-CN">SKILL.md 待定位</span><span lang="en">SKILL.md not located</span></span>`; return ''; };
      const metaHtml = skill => { const stars = formatCount(skill.repoStats && skill.repoStats.stars); const reviews = reviewsOf(skill).length; return `<div class="skill-card-meta">${stars ? `<span class="skill-stat">★ ${stars}</span>` : '<span class="skill-stat is-muted">★ —</span>'}${reviews ? `<span class="skill-stat">${reviews} <span lang="zh-CN">条评价</span><span lang="en">reviews</span></span>` : ''}${linkChip(skill)}</div>`; };
      const styleEntry = skill => (skill.styles && typeof skill.styles === 'object') ? skill.styles : null; const styleItems = entry => Array.isArray(entry.items) ? entry.items : []; const stylePreview = entry => { const items = styleItems(entry); const total = typeof entry.total === 'number' && entry.total >= items.length ? entry.total : items.length; let text = entry.summary || ''; if (items.length) { text += (text ? ' · ' : '') + items.slice(0, 3).join(' / ') + (total > 3 ? ` +${total - 3}` : ''); } return text; };
      const styleLine = skill => { const entry = styleEntry(skill); if (!entry || !entry.hasStyles) return ''; const text = stylePreview(entry); return text ? `<div class="skill-style"><span class="skill-style-label">样式</span><span class="skill-style-text">${escapeHtml(text)}</span></div>` : ''; };
       const filtered = () => { const keyword = search.value.trim().toLowerCase(); return skills.filter(skill => (category === 'all' || skill.category === category) && (status.value === 'all' || skill.status === status.value) && (!keyword || [skill.name, skill.description_zh, skill.description, skill.githubUrl, ...(skill.compatibility || []), ...reviewsOf(skill).map(review => `${review.source || ''} ${review.quote || ''}`), ...(entry => entry ? [entry.format || '', entry.summary || '', ...styleItems(entry)] : [])(styleEntry(skill))].join(' ').toLowerCase().includes(keyword))); };
       const card = skill => `<article class="skill-card"><div class="skill-card-top"><span class="skill-category blue">${escapeHtml(categoryLabel(skill.category))}</span><span class="skill-status review">${escapeHtml(statusLabel(skill.status))}</span></div><h2>${escapeHtml(skill.name)}</h2><p><span class="skill-description-zh" lang="zh-CN">${escapeHtml(skill.description_zh)}</span><span class="skill-description-en" lang="en">${escapeHtml(skill.description)}</span></p>${styleLine(skill)}<div class="skill-chips">${(skill.compatibility || []).map(item => `<span class="skill-chip">${escapeHtml(item)}</span>`).join('')}</div>${metaHtml(skill)}<div class="skill-card-bottom"><button class="skill-details" type="button" data-skill-id="${escapeHtml(skill.id)}"><span lang="zh-CN">查看内容与评价 →</span><span lang="en">Content &amp; reviews →</span></button>${skill.githubUrl ? `<a class="skill-source-link" href="${escapeHtml(skill.githubUrl)}" target="_blank" rel="nofollow noopener">打开 GitHub ↗</a>` : '<span class="skill-source-missing">来源链接待补充</span>'}</div></article>`;
      const render = () => { const visible = filtered(); grid.innerHTML = visible.map(card).join(''); empty.hidden = visible.length > 0; count.textContent = `显示 ${visible.length} / ${skills.length}`; };
      document.querySelectorAll('.skill-category-tab').forEach(button => button.addEventListener('click', () => { category = button.dataset.category; document.querySelectorAll('.skill-category-tab').forEach(item => item.classList.toggle('is-active', item === button)); render(); })); search.addEventListener('input', render); status.addEventListener('change', render);
      document.getElementById('skill-clear').addEventListener('click', () => { search.value = ''; status.value = 'all'; category = 'all'; document.querySelectorAll('.skill-category-tab').forEach(item => item.classList.toggle('is-active', item.dataset.category === 'all')); render(); });
      const sentimentLabel = value => ({ positive: ['正面', 'positive'], mixed: ['有褒有贬', 'mixed'], negative: ['负面', 'negative'], neutral: ['中性', 'neutral'] }[value] || null);
      const renderStats = skill => { const stats = skill.repoStats || {}; const chips = []; const stars = formatCount(stats.stars); if (stars) chips.push(`★ ${stars}`); const forks = formatCount(stats.forks); if (forks) chips.push(`${isEn() ? 'forks ' : 'fork '}${forks}`); if (stats.pushedAt) chips.push(`${isEn() ? 'pushed ' : '最近推送 '}${String(stats.pushedAt).slice(0, 10)}`); document.getElementById('dialog-skill-stats').innerHTML = chips.map(chip => `<span class="stat-chip">${escapeHtml(chip)}</span>`).join(''); };
      const renderReviews = skill => { const items = reviewsOf(skill); const list = document.getElementById('dialog-skill-reviews'); if (!items.length) { list.innerHTML = `<li class="skill-review-item is-empty"><span lang="zh-CN">暂未收录针对该 Skill 的第三方评价；上方 star / fork 数据可作为社区热度参考。</span><span lang="en">No third-party review collected yet; the star / fork counts above serve as a popularity signal.</span></li>`; return; } list.innerHTML = items.map(review => { const sentiment = sentimentLabel(review.sentiment); return `<li class="skill-review-item"><blockquote>“${escapeHtml(review.quote)}”</blockquote><div class="review-meta">${sentiment ? `<span class="skill-sentiment ${sentiment[1]}"><span lang="zh-CN">${sentiment[0]}</span><span lang="en">${sentiment[1]}</span></span>` : ''}${review.date ? `<span>${escapeHtml(review.date)}</span>` : ''}<a href="${escapeHtml(review.url)}" target="_blank" rel="nofollow noopener">${escapeHtml(review.source)} ↗</a></div></li>`; }).join(''); };
      const contentCache = {};
      const renderContent = skill => { const pre = document.getElementById('dialog-skill-content'); const meta = document.getElementById('dialog-content-meta'); pre.classList.remove('is-error'); if (!skill.contentPath) { pre.classList.add('is-error'); meta.innerHTML = ''; pre.textContent = isEn() ? 'No SKILL.md could be verified for this entry. Open the GitHub link to inspect the source yourself.' : '该条目未能核验到 SKILL.md 原文（来源链接缺失或不可达），请打开 GitHub 自行核对。'; return; } const show = doc => { pre.textContent = doc.content; meta.innerHTML = `${escapeHtml(String(doc.bytes || ''))} bytes · ${isEn() ? 'fetched ' : '抓取于 '}${escapeHtml(String(doc.fetchedAt || '').slice(0, 10))} · <a href="${escapeHtml(doc.contentUrl || skill.githubUrl || '#')}" target="_blank" rel="nofollow noopener">raw ↗</a>`; }; if (contentCache[skill.id]) { show(contentCache[skill.id]); return; } pre.textContent = isEn() ? 'Loading SKILL.md…' : '正在加载 SKILL.md 原文…'; meta.innerHTML = ''; fetch(`content/${encodeURIComponent(skill.id)}.json`).then(response => { if (!response.ok) throw new Error('http ' + response.status); return response.json(); }).then(doc => { contentCache[skill.id] = doc; if (current && current.id === skill.id) show(doc); }).catch(() => { if (current && current.id === skill.id) { pre.classList.add('is-error'); pre.textContent = isEn() ? 'Failed to load the content. Open GitHub to read the source.' : '原文加载失败，请打开 GitHub 查看源文件。'; } }); };
      const ensurePreview = () => { let section = document.getElementById('dialog-skill-preview'); if (section) return section; section = document.createElement('section'); section.id = 'dialog-skill-preview'; section.className = 'skill-dialog-section skill-preview'; section.innerHTML = '<h3><span lang="zh-CN">视觉预览</span><span lang="en">Visual preview</span></h3><div class="skill-preview-layout"><div class="skill-preview-copy"><span class="skill-preview-label">OUTPUT FORMAT / 输出形式</span><strong id="dialog-preview-format" class="skill-preview-format"></strong><p id="dialog-preview-summary" class="skill-preview-summary"></p><div id="dialog-preview-tags" class="skill-preview-tags"></div></div><div id="dialog-preview-canvas" class="skill-preview-canvas" role="img" aria-label="Skill output structure preview"></div></div>'; document.getElementById('dialog-skill-stats').after(section); return section; };
      const previewKind = skill => { const text = `${skill.name || ''} ${(skill.styles && skill.styles.format) || ''} ${skill.description || ''}`.toLowerCase(); if (/ppt|slide|幻灯片|png|image|infographic|插画|视觉|canvas/.test(text)) return 'visual'; if (/xlsx|excel|table|表格|data|dashboard|报表/.test(text)) return 'data'; if (/docx|word|文档|markdown|resume|简历|writing|文案|pdf/.test(text)) return 'document'; return 'code'; };
      const renderPreview = skill => { ensurePreview(); const entry = styleEntry(skill) || {}; const kind = previewKind(skill); const format = entry.format || 'Agent workflow output'; const summary = entry.hasStyles ? '根据该 Skill 的样式元数据生成结构预览；具体内容由 Skill 执行时产生。' : '该 Skill 没有预设视觉主题，这里展示它的输出结构示意。'; const items = styleItems(entry).slice(0, 6); document.getElementById('dialog-preview-format').textContent = format; document.getElementById('dialog-preview-summary').textContent = summary; document.getElementById('dialog-preview-tags').innerHTML = (items.length ? items : ['结构示意']).map(item => `<span class="skill-preview-tag">${escapeHtml(item)}</span>`).join(''); const canvas = document.getElementById('dialog-preview-canvas'); canvas.className = `skill-preview-canvas ${kind}`; canvas.innerHTML = `<div class="skill-preview-window"><div class="skill-preview-window-bar"><i></i><i></i><i></i><span>${escapeHtml(format)}</span></div><div class="skill-preview-window-main"><span class="skill-preview-kicker"></span><span class="skill-preview-title-line"></span><span class="skill-preview-copy-line"></span><span class="skill-preview-copy-line short"></span><div class="skill-preview-blocks"><i class="skill-preview-block"></i><i class="skill-preview-block"></i><i class="skill-preview-block"></i></div></div></div>`; };
      const renderStyles = skill => { const section = document.getElementById('dialog-style-section'); const entry = styleEntry(skill); if (!entry) { section.hidden = true; return; } section.hidden = false; document.getElementById('dialog-style-format').textContent = entry.format || ''; document.getElementById('dialog-style-summary').textContent = entry.summary || ''; const items = styleItems(entry); const total = typeof entry.total === 'number' && entry.total >= items.length ? entry.total : items.length; document.getElementById('dialog-style-chips').innerHTML = items.map(item => `<code class="style-chip">${escapeHtml(item)}</code>`).join('') + (total > items.length ? `<span class="style-more">+${total - items.length}</span>` : ''); };
      grid.addEventListener('click', event => { const trigger = event.target.closest('.skill-details'); if (!trigger) return; const skill = skills.find(item => item.id === trigger.dataset.skillId); if (!skill) return; current = skill; document.getElementById('dialog-skill-name').textContent = skill.name; document.getElementById('dialog-skill-description-zh').textContent = skill.description_zh; document.getElementById('dialog-skill-description-en').textContent = skill.description; document.getElementById('dialog-command').textContent = skill.cloneCommand; const link = document.getElementById('dialog-github'); link.href = skill.githubUrl || '#'; link.hidden = !skill.githubUrl; renderStats(skill); renderReviews(skill); renderPreview(skill); renderStyles(skill); renderContent(skill); dialog.showModal(); });
      document.querySelector('.skill-dialog-close').addEventListener('click', () => dialog.close()); document.getElementById('copy-command').addEventListener('click', async event => { const button = event.currentTarget; const command = document.getElementById('dialog-command').textContent; try { await navigator.clipboard.writeText(command); button.textContent = '已复制'; } catch { const range = document.createRange(); range.selectNodeContents(document.getElementById('dialog-command')); const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range); button.textContent = '请手动复制'; } setTimeout(() => { button.textContent = '复制命令'; }, 1600); });
      const adaptFileNavigation = () => { if (window.location.protocol !== 'file:') return; document.querySelectorAll('.top-nav a[href^="/"]').forEach(link => { const path = link.getAttribute('href').split(/[?#]/, 1)[0]; if (!path.endsWith('/')) return; link.setAttribute('href', `../${path.slice(1)}index.html${window.location.search}`); }); };
      adaptFileNavigation(); render();
    })();
    '''
    script = (
        "const CATEGORY_MAP = "
        + json.dumps({key: value["name_zh"] for key, value in SKILL_CATEGORY_DEFINITIONS.items()}, ensure_ascii=False)
        + ";"
        + script
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "website")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script><script type="application/json" id="skill-data">{serialized}</script>{SKILLS_THEME_ASSETS}<style>{style}</style></head><body data-static-locale="true"><main class="skills-page"><header class="skills-header"><a class="brand" href="/"><span class="brand-mark">✦</span><span><span class="brand-name">FreeLLM</span><span class="brand-sub">免费 AI 资源导航</span></span></a><div class="header-right"><nav class="top-nav" aria-label="Page sections"><a href="/logs/">每日更新</a><a href="/models/">资源目录</a><a href="/models/center/">模型中心</a><a href="/providers/">按厂家</a><a href="/skills/" aria-current="page">Skills</a></nav><button id="theme-toggle" class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button></div></header><section class="skills-hero"><div><div class="eyebrow">AGENT SKILLS / WORKFLOWS</div><h1>这些 Skill，能跑的真跑；跑不了的明确写阻塞</h1><p class="hero-copy">不再把“生成了一个 Demo”当成通过。页面区分原链路 E2E、真实产物、任务级执行、部分验证和环境阻塞；每项都能追到本轮验收记录。</p></div><aside class="hero-note"><span class="hero-note-label">VERIFIED SKILLS / 已核验组件</span><div class="hero-note-value"><strong>{len(skills)}</strong><span>个可下载 Skill</span></div><p>每个条目均核验过 GitHub 来源，页面内直接展示 SKILL.md 原文与社区评价；star / fork 数据随核验快照更新。</p></aside></section><section class="real-test-banner" aria-label="FreeLLM sandbox acceptance"><div><strong>2026-09-20 沙箱真实验收已重跑</strong><p>68 个 Skill 全部重新分级：原链路能跑就跑；任务型明确标“任务级”；网络、账号、CLI 或浏览器策略阻塞的直接标 BLOCKED。仅有 Demo 不再算通过。</p></div><a href="/skills/test-artifacts/sandbox-2026-09-20/">查看 68 项完整验收记录 →</a></section><section class="skills-toolbar" aria-label="Skill filters"><input id="skill-search" class="skills-search" type="search" placeholder="搜索名称、用途、框架或 GitHub 地址" aria-label="搜索 Skill"><select id="skill-status" class="skills-status-filter" aria-label="按状态筛选"><option value="all">全部状态</option><option value="needs_review">待核验</option><option value="candidate">社区候选</option><option value="verified">已核验</option></select><span id="skill-count" class="skills-count">显示 0 / {len(skills)}</span></section><div class="skill-category-tabs"><button class="skill-category-tab is-active" type="button" data-category="all"><span>全部</span><small>{len(skills):02d}</small></button>{category_buttons}</div><section id="skill-grid" class="skill-grid" aria-live="polite">{cards}</section><section id="skill-empty" class="skills-empty" hidden><p>没有找到匹配的 Skill。</p><button id="skill-clear" type="button">清除筛选</button></section><footer class="skills-footer"><p>提示：Skill 通常需要放入对应 Agent 工具的 skills 目录；不同工具的目录结构和触发方式可能不同。所有条目的来源仓库与 SKILL.md 均经过自动核验， star / fork 为核验当日快照。</p>{_static_locale_nav()}</footer></main><dialog id="skill-dialog"><div class="skill-dialog-body"><button class="skill-dialog-close" type="button" aria-label="关闭">×</button><div class="eyebrow">SKILL DETAIL / 条目详情</div><h2 id="dialog-skill-name"></h2><p id="dialog-skill-description"><span id="dialog-skill-description-zh" class="skill-description-zh" lang="zh-CN"></span><span id="dialog-skill-description-en" class="skill-description-en" lang="en"></span></p><div id="dialog-skill-stats" class="skill-dialog-stats"></div><section class="skill-dialog-section"><h3><span lang="zh-CN">安装方式</span><span lang="en">Install</span></h3><div class="command-box"><code id="dialog-command"></code><button id="copy-command" class="copy-command" type="button">复制命令</button></div><div class="dialog-actions"><a id="dialog-github" href="#" target="_blank" rel="nofollow noopener">打开 GitHub ↗</a><span class="muted"><span lang="zh-CN">使用前请自行核对仓库状态</span><span lang="en">Verify the repo before use</span></span></div></section><section class="skill-dialog-section" id="dialog-style-section" hidden><h3><span lang="zh-CN">呈现样式</span><span lang="en">Output styles</span></h3><p class="skill-style-format"><code id="dialog-style-format"></code></p><p id="dialog-style-summary"></p><div id="dialog-style-chips" class="skill-style-chips"></div></section><section class="skill-dialog-section"><h3><span lang="zh-CN">Skill 原文</span><span lang="en">Skill source</span></h3><p class="skill-content-meta" id="dialog-content-meta"></p><pre class="skill-content" id="dialog-skill-content" tabindex="0"></pre></section><section class="skill-dialog-section"><h3><span lang="zh-CN">社区评价</span><span lang="en">Community signals</span></h3><ol class="skill-review-list" id="dialog-skill-reviews"></ol></section></div></dialog><script>{script}</script></body></html>'''


def render_skills_page(skills: list[dict], site_url: str) -> str:
    page = _legacy_render_skills_page(skills, site_url)
    return page.replace(
        '<a href="/skills/" aria-current="page">Skills</a></nav>',
        '<a href="/skills/" aria-current="page">Skills</a><a href="/skills/lab/">Skill Lab</a></nav>',
    )


def _render_skill_lab_page(skills: list[dict], recipes: list[dict], site_url: str) -> str:
    """Render curated workflow recipes first; keep the full catalog behind a collapsed library."""
    if site_url is None:
        site_url = str(recipes)
        recipes = []
    recipes = recipes if isinstance(recipes, list) else []
    path = SKILL_LAB_PAGE_PATH
    title = "Skill Lab · FreeLLM"
    description = "用 FreeLLM 的 Workflow Recipes 把 Agent Skill 组合成可执行的产品、办公、电商、SEO 和求职工作流。"
    page_url = _absolute(site_url, path)
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": title, "description": description, "url": page_url},
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "FreeLLM 免费 AI 资源索引", "item": _absolute(site_url, "/")},
                    {"@type": "ListItem", "position": 2, "name": "Agent Skills", "item": _absolute(site_url, SKILLS_PAGE_PATH)},
                    {"@type": "ListItem", "position": 3, "name": title, "item": page_url},
                ],
            },
            {
                "@type": "ItemList",
                "name": "FreeLLM Workflow Recipes",
                "numberOfItems": len(recipes),
                "itemListElement": [
                    {"@type": "ListItem", "position": index, "name": recipe.get("title"), "url": page_url}
                    for index, recipe in enumerate(recipes, start=1)
                ],
            },
            *[
                {
                    "@type": "HowTo",
                    "name": recipe.get("title"),
                    "description": recipe.get("description"),
                    "step": [
                        {"@type": "HowToStep", "position": index, "name": step.get("label"), "text": step.get("detail")}
                        for index, step in enumerate(recipe.get("steps") or [], start=1)
                    ],
                }
                for recipe in recipes
            ],
        ],
    }
    serialized_skills = json.dumps(skills, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    serialized_recipes = json.dumps(recipes, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    recipe_cards = []
    for recipe in recipes:
        flow = "".join(
            f'<span class="flow-node">{index:02d}</span><span class="flow-line" aria-hidden="true"></span>'
            for index, _ in enumerate(recipe.get("steps") or [], start=1)
        )
        recipe_cards.append(
            f'''<article class="workflow-card" data-recipe-id="{_esc(recipe.get("id"))}">
              <div class="workflow-card-head"><span class="recipe-kicker">{_esc(recipe.get("kicker", "WORKFLOW"))}</span><span class="recipe-count">{len(recipe.get("steps") or []):02d} STEPS</span></div>
              <h2>{_esc(recipe.get("title"))}</h2><p>{_esc(recipe.get("description"))}</p>
              <div class="workflow-flow">{flow}</div>
              <div class="workflow-card-foot"><span>{_esc(" · ".join(recipe.get("tags") or []))}</span><button class="workflow-details" type="button" data-recipe-id="{_esc(recipe.get("id"))}">展开配方 ↗</button></div>
            </article>'''
        )
    category_options = "".join(
        f'<option value="{_esc(key)}" data-category="{_esc(key)}">{_esc(value["name_zh"])} / {_esc(value["name_en"])}</option>'
        for key, value in SKILL_CATEGORY_DEFINITIONS.items()
        if any(item.get("category") == key for item in skills)
    )
    category_map = json.dumps(
        {key: value["name_zh"] for key, value in SKILL_CATEGORY_DEFINITIONS.items()},
        ensure_ascii=False,
    )
    style = r'''
    :root { color-scheme:light; --canvas:#FBFBFA; --canvas-warm:#F7F6F3; --surface:#FFFFFF; --surface-soft:#F9F9F8; --ink:#2F3437; --ink-secondary:#787774; --ink-tertiary:#B4B4B0; --line:#EAEAEA; --line-soft:rgba(0,0,0,.04); --ink-solid:#111111; --accent:#1744E8; --accent-soft:#E9EEFF; --pale-green-bg:#EDF3EC; --pale-green-text:#346538; --pale-yellow-bg:#FBF3DB; --pale-yellow-text:#956400; --pale-stone-bg:#F0EFEC; --pale-stone-text:#5A5854; --code-bg:#111111; --code-text:#F4F2EE; --card-shadow:0 2px 8px rgba(0,0,0,.04); --modal-shadow:0 20px 60px rgba(0,0,0,.12); --sidebar:236px; --font-serif:'Instrument Serif','Noto Serif SC',Georgia,'Songti SC','SimSun',serif; --font-sans:'Manrope','PingFang SC','Hiragino Sans GB','Microsoft YaHei',ui-sans-serif,system-ui,sans-serif; --font-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace; }
    :root[data-theme="dark"] { color-scheme:dark; --canvas:#0E0F11; --canvas-warm:#14161A; --surface:#181B20; --surface-soft:#1E2127; --ink:#ECEAE6; --ink-secondary:#A7A5A0; --ink-tertiary:#6E6C68; --line:#26292F; --line-soft:rgba(255,255,255,.04); --ink-solid:#F4F2EE; --accent:#7BC0E5; --accent-soft:#0E2533; --pale-green-bg:#112218; --pale-green-text:#86C098; --pale-yellow-bg:#2B2010; --pale-yellow-text:#D9A85F; --pale-stone-bg:#232220; --pale-stone-text:#B4B1AB; --code-bg:#1E2127; --code-text:#ECEAE6; --card-shadow:0 2px 8px rgba(0,0,0,.3); --modal-shadow:0 20px 60px rgba(0,0,0,.5); }
    * { box-sizing:border-box; } html { scroll-behavior:smooth; } body { margin:0; min-width:320px; background:var(--canvas); color:var(--ink); font:400 15px/1.6 var(--font-sans); -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; } a { color:inherit; } button,input,select { font:inherit; } h1,h2,h3 { font-family:var(--font-serif); font-weight:400; }
    ::selection { background:var(--accent-soft); }
    .skill-lab-page { min-height:100vh; padding-left:var(--sidebar); }
    .skill-lab-sidebar { position:fixed; inset:0 auto 0 0; z-index:4; width:var(--sidebar); display:flex; flex-direction:column; padding:26px 0 20px; border-right:1px solid var(--line); background:var(--canvas); } .lab-brand { display:flex; gap:11px; align-items:center; text-decoration:none; margin:0 26px; padding-bottom:24px; border-bottom:1px solid var(--line); } .lab-mark { display:grid; place-items:center; width:34px; height:34px; border-radius:8px; color:#fff; background:var(--accent); font-size:19px; flex-shrink:0; } .lab-brand strong { display:block; font-family:var(--font-serif); font-size:21px; font-weight:400; letter-spacing:-.02em; line-height:1.1; } .lab-brand small { display:block; margin-top:3px; color:var(--ink-tertiary); font:500 10px/1.4 var(--font-mono); letter-spacing:.1em; text-transform:uppercase; }
    .lab-side-label { margin:26px 26px 10px; color:var(--ink-tertiary); font:500 10px var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .lab-side-nav { display:grid; gap:2px; padding:0 14px; } .lab-side-nav a { position:relative; padding:9px 14px; border-radius:6px; color:var(--ink-secondary); font-size:13.5px; text-decoration:none; transition:color .15s, background .15s; } .lab-side-nav a:hover { color:var(--ink); background:var(--line-soft); } .lab-side-nav a[aria-current="page"] { color:var(--ink); font-weight:600; background:var(--line-soft); } .lab-side-nav a[aria-current="page"]::before { content:""; position:absolute; left:0; top:8px; bottom:8px; width:2px; border-radius:1px; background:var(--accent); }
    .lab-side-note { margin:22px 26px 0; margin-top:auto; padding:14px 16px; border:1px solid var(--line); border-radius:8px; background:var(--surface); font-size:12px; line-height:1.6; color:var(--ink-secondary); } .lab-side-note strong { display:block; margin-bottom:6px; color:var(--ink-tertiary); font:500 10px var(--font-mono); letter-spacing:.12em; text-transform:uppercase; }
    .theme-toggle { width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); cursor:pointer; transition:all .2s; font-size:14px; line-height:1; padding:0; flex-shrink:0; } .theme-toggle:hover { background:var(--line-soft); border-color:var(--ink-tertiary); } .theme-toggle .icon-sun { display:none; } .theme-toggle .icon-moon { display:inline; } :root[data-theme="dark"] .theme-toggle .icon-sun { display:inline; } :root[data-theme="dark"] .theme-toggle .icon-moon { display:none; }
    .lab-content { max-width:1320px; margin:0 auto; padding:26px 48px 72px; } .lab-topline { display:flex; justify-content:space-between; gap:18px; align-items:center; padding-bottom:16px; border-bottom:1px solid var(--line); } .lab-topline span,.lab-topline a { color:var(--ink-tertiary); font:500 10px var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .lab-topline a { text-decoration:none; transition:color .15s; } .lab-topline a:hover { color:var(--accent); } .lab-topline-actions { display:flex; gap:14px; align-items:center; } .lab-topline-actions a { font-size:11px; }
    .lab-hero { display:grid; grid-template-columns:minmax(0,1fr) 300px; gap:44px; align-items:end; padding:58px 0 36px; } .lab-eyebrow,.recipe-kicker { color:var(--accent); font:500 11px var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .lab-hero h1 { max-width:760px; margin:14px 0 18px; font-size:clamp(44px,5.2vw,68px); line-height:1.06; letter-spacing:-.02em; } .lab-hero h1 .accent-text { color:var(--accent); } .lab-hero .lead { max-width:640px; margin:0; color:var(--ink-secondary); font-size:17px; line-height:1.7; }
    .lab-hero-aside { padding:26px; border:1px solid var(--line); border-radius:8px; background:var(--surface); } .lab-hero-aside .aside-label { display:block; color:var(--ink-tertiary); font:500 10px/1 var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .lab-hero-aside strong { display:block; margin:12px 0 10px; font-family:var(--font-serif); font-size:64px; font-weight:400; line-height:.9; letter-spacing:-.03em; color:var(--ink); } .lab-hero-aside p { margin:0; color:var(--ink-secondary); font-size:12.5px; line-height:1.7; }
    .lab-rule { display:flex; gap:14px; align-items:center; margin:0 0 28px; padding:12px 16px; border:1px solid rgba(149,100,0,.15); border-radius:6px; background:var(--pale-yellow-bg); color:var(--pale-yellow-text); } .lab-rule strong { font:500 11px var(--font-mono); letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; } .lab-rule span { font-size:12.5px; }
    .workflow-section-head { display:flex; justify-content:space-between; align-items:end; gap:20px; margin:0 0 16px; } .workflow-section-head h2 { margin:8px 0 0; font-size:30px; letter-spacing:-.02em; } .workflow-section-head p { margin:0; color:var(--ink-tertiary); font-size:12px; }
    .workflow-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; } .workflow-card { position:relative; min-height:242px; display:flex; flex-direction:column; padding:24px; border:1px solid var(--line); border-radius:8px; background:var(--surface); overflow:hidden; cursor:pointer; transition:box-shadow .2s, transform .2s; } .workflow-card:hover { box-shadow:var(--card-shadow); transform:translateY(-1px); }
    .workflow-card-head,.workflow-card-foot { display:flex; justify-content:space-between; align-items:center; gap:10px; } .recipe-count { color:var(--ink-tertiary); font:500 10px var(--font-mono); letter-spacing:.08em; } .workflow-card h2 { max-width:460px; margin:26px 0 9px; font-size:26px; line-height:1.15; letter-spacing:-.02em; } .workflow-card p { max-width:520px; min-height:43px; margin:0; color:var(--ink-secondary); font-size:13px; line-height:1.6; }
    .workflow-flow { display:flex; align-items:center; margin:24px 0 20px; } .flow-node { display:grid; place-items:center; width:28px; height:28px; border:1px solid var(--line); border-radius:6px; background:var(--surface-soft); color:var(--accent); font:500 10px var(--font-mono); } .flow-line { width:36px; height:1px; background:var(--line); } .workflow-card-foot { margin-top:auto; padding-top:14px; border-top:1px solid var(--line-soft); color:var(--ink-tertiary); font-size:11px; } .workflow-details { padding:0; border:0; color:var(--accent); background:none; cursor:pointer; font-size:12.5px; font-weight:600; } .workflow-details:hover { opacity:.72; }
    .component-library { margin-top:40px; border-top:1px solid var(--line); border-bottom:1px solid var(--line); } .component-library > summary { display:flex; align-items:center; justify-content:space-between; gap:18px; padding:22px 0; cursor:pointer; list-style:none; } .component-library > summary::-webkit-details-marker { display:none; } .component-library > summary::after { content:"＋"; font-size:20px; color:var(--ink-secondary); } .component-library[open] > summary::after { content:"－"; } .library-summary strong { display:block; font-family:var(--font-serif); font-size:22px; font-weight:400; letter-spacing:-.02em; } .library-summary span { display:block; margin-top:5px; color:var(--ink-secondary); font-size:12.5px; } .library-count { padding:5px 11px; border-radius:9999px; background:var(--accent-soft); color:var(--accent); font:500 10.5px var(--font-mono); letter-spacing:.06em; white-space:nowrap; } .library-body { padding:0 0 26px; } .library-tools { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; } .library-tools input,.library-tools select { min-height:40px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink); padding:9px 13px; outline:none; transition:border-color .15s, box-shadow .15s; } .library-tools input { flex:1 1 300px; } .library-tools input:focus,.library-tools select:focus { border-color:var(--ink); box-shadow:0 0 0 3px var(--line-soft); } .library-tools input::placeholder { color:var(--ink-tertiary); } .library-tools select { min-width:220px; cursor:pointer; }
    .component-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; } .component-grid .component-card { min-width:0; display:flex; flex-direction:column; padding:16px; border:1px solid var(--line); border-radius:8px; background:var(--surface); transition:box-shadow .2s; } .component-grid .component-card:hover { box-shadow:var(--card-shadow); } .component-card h3 { margin:0 0 7px; font:500 13.5px/1.5 var(--font-mono); overflow-wrap:anywhere; color:var(--ink); } .component-card p { min-height:36px; margin:0; color:var(--ink-secondary); font-size:12px; line-height:1.55; } .component-meta { display:flex; justify-content:space-between; gap:8px; align-items:center; margin-top:14px; padding-top:10px; border-top:1px solid var(--line-soft); color:var(--ink-tertiary); font-size:10.5px; } .component-source-link { color:var(--accent); text-decoration:none; font-weight:500; } .component-source-link:hover { opacity:.72; } .component-install { margin-top:10px; padding:0; border:0; color:var(--accent); background:none; cursor:pointer; font-size:11.5px; font-weight:600; text-align:left; } .component-install:hover { opacity:.72; } .component-style { margin:8px 0 0; padding:6px 8px; background:var(--surface-soft); border:1px solid var(--line); border-radius:6px; color:var(--ink-secondary); font-size:11.5px; line-height:1.55; } .component-dialog-styles { margin:14px 0 0; padding:10px 12px; background:var(--surface-soft); border:1px solid var(--line); border-radius:6px; color:var(--ink-secondary); font-size:13px; line-height:1.65; } .component-dialog-styles strong { color:var(--accent); font:500 10px/1.6 var(--font-mono); letter-spacing:.1em; text-transform:uppercase; display:block; margin-bottom:4px; } .library-empty { padding:28px; color:var(--ink-tertiary); border:1px dashed var(--line); border-radius:8px; text-align:center; }
    .lab-footer { display:flex; justify-content:space-between; gap:18px; margin-top:48px; padding-top:18px; border-top:1px solid var(--line); color:var(--ink-tertiary); font-size:12.5px; line-height:1.7; } .lab-footer p { max-width:680px; margin:0; } .lab-footer nav { white-space:nowrap; } .lab-footer a { text-decoration:none; } .lab-footer a:hover { color:var(--accent); }
    dialog { width:min(720px,calc(100% - 28px)); max-height:calc(100% - 28px); padding:0; border:1px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink); box-shadow:var(--modal-shadow); } dialog::backdrop { background:rgba(0,0,0,.4); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); } .workflow-dialog-body { padding:30px; background:var(--surface); } .dialog-close { float:right; display:grid; place-items:center; width:32px; height:32px; border:1px solid var(--line); border-radius:50%; background:var(--surface); color:var(--ink-secondary); cursor:pointer; font-size:16px; transition:all .15s; } .dialog-close:hover { background:var(--line-soft); color:var(--ink); } .dialog-kicker { color:var(--accent); font:500 10.5px var(--font-mono); letter-spacing:.12em; text-transform:uppercase; } .workflow-dialog-body h2 { max-width:560px; margin:12px 0 10px; font-size:32px; line-height:1.12; letter-spacing:-.02em; } .component-dialog .workflow-dialog-body h2 { font-family:var(--font-mono); font-size:22px; font-weight:500; } .dialog-intro { max-width:600px; color:var(--ink-secondary); font-size:14px; line-height:1.7; } .dialog-io { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:22px 0; } .dialog-io div { padding:14px 16px; border:1px solid var(--line); border-radius:8px; background:var(--surface-soft); } .dialog-io span { display:block; color:var(--ink-tertiary); font:500 10px var(--font-mono); letter-spacing:.1em; text-transform:uppercase; } .dialog-io strong { display:block; margin-top:7px; font-size:13px; line-height:1.5; } .recipe-steps { display:grid; gap:10px; margin:18px 0 24px; } .recipe-step { display:grid; grid-template-columns:30px minmax(0,1fr); gap:12px; padding:14px 16px; border:1px solid var(--line); border-left:2px solid var(--accent); border-radius:6px; background:var(--surface); } .recipe-step-number { color:var(--accent); font:500 12px var(--font-mono); } .recipe-step strong { display:block; font-size:14px; } .recipe-step small { display:block; margin-top:4px; color:var(--ink-secondary); line-height:1.55; } .recipe-step code { display:block; margin-top:10px; color:var(--ink-tertiary); font:400 10.5px/1.6 var(--font-mono); overflow-wrap:anywhere; } .dialog-actions { display:flex; gap:12px; flex-wrap:wrap; align-items:center; padding-top:18px; border-top:1px solid var(--line); } .primary-action { padding:10px 18px; border:1px solid var(--ink-solid); border-radius:6px; color:var(--canvas); background:var(--ink-solid); cursor:pointer; font-size:13px; font-weight:600; transition:opacity .15s; } .primary-action:hover { opacity:.85; } .muted { color:var(--ink-tertiary); font-size:12px; } .command-box { display:flex; gap:10px; align-items:center; margin:20px 0; padding:14px; border-radius:8px; background:var(--code-bg); color:var(--code-text); } .command-box code { flex:1; overflow:auto; font:400 12px/1.6 var(--font-mono); white-space:pre-wrap; }
    @media (max-width:900px) { :root { --sidebar:200px; } .lab-content { padding:24px 26px 60px; } .lab-hero { grid-template-columns:1fr; gap:24px; } .lab-hero-aside { max-width:380px; } .component-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
    @media (max-width:650px) { :root { --sidebar:0px; } .skill-lab-sidebar { position:relative; width:auto; height:auto; margin:0; padding:16px 14px; border-right:0; border-bottom:1px solid var(--line); } .lab-brand { margin:0 0 13px; padding-bottom:13px; } .lab-side-label,.lab-side-note { display:none; } .lab-side-nav { display:flex; overflow:auto; gap:3px; padding:0; scrollbar-width:none; } .lab-side-nav::-webkit-scrollbar { display:none; } .lab-side-nav a { white-space:nowrap; } .lab-content { padding:20px 16px 48px; } .lab-topline { display:none; } .lab-hero { padding:30px 0 26px; } .lab-hero h1 { font-size:38px; } .lab-hero .lead { font-size:15px; } .workflow-grid { grid-template-columns:1fr; } .workflow-card h2 { font-size:22px; } .component-grid { grid-template-columns:1fr; } .dialog-io { grid-template-columns:1fr; } .lab-footer { display:block; } .lab-footer nav { margin-top:11px; } }
    @media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; transition:none !important; } } .sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
    '''
    script = r'''
    (() => {
      const skills = JSON.parse(document.getElementById('skill-data').textContent);
      const recipes = JSON.parse(document.getElementById('recipe-data').textContent);
      const dialog = document.getElementById('workflow-dialog');
      const componentDialog = document.getElementById('component-dialog');
      const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, character => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[character]));
      const categoryLabel = value => (''' + category_map + r''')[value] || 'Skill';
      const componentGrid = document.getElementById('component-grid');
      const search = document.getElementById('skill-library-search');
      const category = document.getElementById('skill-library-category');
      const empty = document.getElementById('library-empty');
      const commandFor = skill => skill ? String(skill.cloneCommand || '').trim() : '';
      const componentCard = skill => '<article class="component-' + 'card"><h3>' + escapeHtml(skill.name) + '</h3><p>' + escapeHtml(skill.description) + '</p>' + (skill.styles && skill.styles.hasStyles && skill.styles.summary ? '<p class="component-style">' + escapeHtml(skill.styles.summary) + '</p>' : '') + '<div class="component-meta"><span>' + escapeHtml(categoryLabel(skill.category)) + '</span>' + (skill.githubUrl ? '<a class="component-source-link" href="' + escapeHtml(skill.githubUrl) + '" target="_blank" rel="nofollow noopener">GitHub ↗</a>' : '') + '</div><button class="component-install" type="button" data-skill-id="' + escapeHtml(skill.id) + '">查看安装命令 →</button></article>';
      const renderComponents = () => { const query = search.value.trim().toLowerCase(); const visible = skills.filter(skill => (!category.value || skill.category === category.value) && (!query || [skill.id, skill.name, skill.description, skill.githubUrl, ...(skill.compatibility || [])].join(' ').toLowerCase().includes(query))); componentGrid.innerHTML = visible.map(componentCard).join(''); empty.hidden = visible.length > 0; };
      const openRecipe = recipe => { if (!recipe) return; document.getElementById('workflow-dialog-kicker').textContent = recipe.kicker || 'WORKFLOW'; document.getElementById('workflow-dialog-title').textContent = recipe.title || ''; document.getElementById('workflow-dialog-description').textContent = recipe.description || ''; document.getElementById('workflow-input').textContent = recipe.input || ''; document.getElementById('workflow-output').textContent = recipe.output || ''; const steps = recipe.steps || []; document.getElementById('recipe-steps').innerHTML = steps.map((step, index) => { const skill = skills.find(item => item.id === step.skillId); return '<div class="recipe-step"><span class="recipe-step-number">' + String(index + 1).padStart(2, '0') + '</span><div><strong>' + escapeHtml(step.label || (skill && skill.name) || step.skillId) + '</strong><small>' + escapeHtml(step.detail || (skill && skill.description) || '') + '</small><code>' + escapeHtml(commandFor(skill)) + '</code></div></div>'; }).join(''); document.getElementById('copy-workflow-command').dataset.command = steps.map(step => commandFor(skills.find(item => item.id === step.skillId))).filter(Boolean).join('\n'); dialog.showModal(); };
      document.querySelectorAll('.workflow-details').forEach(button => button.addEventListener('click', () => openRecipe(recipes.find(recipe => recipe.id === button.dataset.recipeId))));
      document.querySelectorAll('.workflow-card').forEach(card => card.addEventListener('click', event => { if (event.target.closest('button')) return; openRecipe(recipes.find(recipe => recipe.id === card.dataset.recipeId)); }));
      document.querySelectorAll('[data-dialog-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
      search.addEventListener('input', renderComponents); category.addEventListener('change', renderComponents);
      componentGrid.addEventListener('click', event => { const button = event.target.closest('.component-install'); if (!button) return; const skill = skills.find(item => item.id === button.dataset.skillId); if (!skill) return; document.getElementById('component-dialog-title').textContent = skill.name; document.getElementById('component-dialog-description').textContent = skill.description; document.getElementById('component-command').textContent = commandFor(skill); const stylesNote = document.getElementById('component-dialog-styles'); const entry = (skill.styles && typeof skill.styles === 'object') ? skill.styles : null; if (entry && (entry.hasStyles || entry.summary)) { stylesNote.hidden = false; stylesNote.innerHTML = '<strong>' + (document.documentElement.lang === 'en' ? 'OUTPUT STYLE' : '呈现样式') + '</strong>' + escapeHtml([entry.format, entry.summary].filter(Boolean).join(' · ')); } else { stylesNote.hidden = true; } const link = document.getElementById('component-github'); link.href = skill.githubUrl || '#'; link.hidden = !skill.githubUrl; componentDialog.showModal(); });
      const copy = async (button, value) => { try { await navigator.clipboard.writeText(value); button.textContent = '已复制 ✓'; } catch { button.textContent = '请手动复制'; } setTimeout(() => { button.textContent = button.dataset.label || '复制命令'; }, 1600); };
      document.getElementById('copy-workflow-command').addEventListener('click', event => copy(event.currentTarget, event.currentTarget.dataset.command || ''));
      document.getElementById('copy-component-command').addEventListener('click', event => copy(event.currentTarget, document.getElementById('component-command').textContent));
      const adaptFileNavigation = () => { if (window.location.protocol !== 'file:') return; document.querySelectorAll('.lab-side-nav a[href^="/"], .lab-topline a[href^="/"]').forEach(link => { const path = link.getAttribute('href').split(/[?#]/, 1)[0]; if (path === '/') link.setAttribute('href', '../index.html'); else if (path.endsWith('/')) link.setAttribute('href', '../' + path.slice(1) + 'index.html' + window.location.search); }); };
      document.querySelectorAll('[data-copy-label]').forEach(button => { button.dataset.label = button.textContent; });
      adaptFileNavigation(); renderComponents();
    })();
    '''
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title><meta name="description" content="{_esc(description)}"><link rel="canonical" href="{_esc(page_url)}">{_social_meta(site_url, path, title, description, "website")}{_analytics_script()}{ADSENSE_SCRIPT}{STATIC_LOCALE_STYLE}{STATIC_LOCALE_SCRIPT}<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script><script type="application/json" id="skill-data">{serialized_skills}</script><script type="application/json" id="recipe-data">{serialized_recipes}</script>{SKILLS_THEME_ASSETS}<style>{style}</style></head><body data-static-locale="true"><main class="skill-lab-page"><aside class="skill-lab-sidebar"><a class="lab-brand" href="/"><span class="lab-mark">✦</span><span><strong>FreeLLM</strong><small>SKILL LAB / 2026</small></span></a><div class="lab-side-label">EXPLORE</div><nav class="lab-side-nav" aria-label="Skill Lab 导航"><a href="/skills/" aria-current="page">工作流配方</a><a href="#component-library">组件库</a><a href="/models/">模型目录</a><a href="/logs/">每日更新</a></nav><div class="lab-side-note"><strong>{len(skills)} COMPONENTS</strong><span>组件是积木，配方才是做事的方法。先从结果出发。</span></div></aside><section class="lab-content"><div class="lab-topline"><span>FREE AI INDEX / SKILL LAB</span><div class="lab-topline-actions"><a href="/">返回 FreeLLM 首页 ↗</a><button id="theme-toggle" class="theme-toggle" type="button" aria-label="切换深色模式"><span class="icon-moon">☾</span><span class="icon-sun">☀</span></button></div></div><header class="lab-hero"><div><div class="lab-eyebrow">AGENT SKILLS / WORKFLOW RECIPES</div><h1>让模型<br><span class="accent-text">把事情做完。</span></h1><p class="lead">模型决定上限，Skill 决定执行路径。我们把零散能力编排成 6 套可直接复用的工作流配方，先选你要交付的结果。</p></div><aside class="lab-hero-aside"><span class="aside-label">WORKFLOW RECIPES / 工作流</span><strong>06</strong><p>套经过人工编排的工作流<br>{len(skills)} 个可检索的底层组件<br>每个条目都核验过 SKILL.md 原文</p></aside></header><div class="lab-rule"><strong>HOW TO USE / 使用方式</strong><span>选一套配方 → 查看步骤 → 复制安装命令 → 把输入交给 Agent</span></div><section aria-labelledby="workflow-heading"><div class="workflow-section-head"><div><div class="lab-eyebrow">START WITH THE OUTCOME</div><h2 id="workflow-heading">你现在要完成什么？</h2></div><p>首屏只保留 6 个高频结果</p></div><div class="workflow-grid">{"".join(recipe_cards)}</div></section><details id="component-library" class="component-library"><summary><span class="library-summary"><strong>组件库 / Component library</strong><span>不确定从哪开始？搜索 {len(skills)} 个底层 Skill，按用途挑一块积木。</span></span><span class="library-count">{len(skills):03d} COMPONENTS</span></summary><div class="library-body"><div class="library-tools"><label class="sr-only" for="skill-library-search">搜索组件</label><input id="skill-library-search" type="search" placeholder="搜索名称、用途、仓库或框架"><label class="sr-only" for="skill-library-category">按分类筛选</label><select id="skill-library-category"><option value="">全部分类</option>{category_options}</select></div><div id="component-grid" class="component-grid" aria-live="polite"></div><div id="library-empty" class="library-empty" hidden>没有找到匹配的组件。</div></div></details><footer class="lab-footer"><p>提示：组件均来自已核验的 GitHub 仓库，页面内可直接查看 SKILL.md 原文。安装前请确认目标 Agent 的 skills 目录结构和权限要求。</p>{_static_locale_nav()}</footer></section></main><dialog id="workflow-dialog"><div class="workflow-dialog-body"><button class="dialog-close" type="button" data-dialog-close aria-label="关闭">×</button><div id="workflow-dialog-kicker" class="dialog-kicker">WORKFLOW</div><h2 id="workflow-dialog-title"></h2><p id="workflow-dialog-description" class="dialog-intro"></p><div class="dialog-io"><div><span>INPUT / 输入</span><strong id="workflow-input"></strong></div><div><span>OUTPUT / 产出</span><strong id="workflow-output"></strong></div></div><div id="recipe-steps" class="recipe-steps"></div><div class="dialog-actions"><button id="copy-workflow-command" class="primary-action" type="button" data-copy-label="复制整套安装命令">复制整套安装命令</button><span class="muted">命令按步骤顺序排列</span></div></div></dialog><dialog id="component-dialog" class="component-dialog"><div class="workflow-dialog-body"><button class="dialog-close" type="button" data-dialog-close aria-label="关闭">×</button><div class="dialog-kicker">COMPONENT / 组件</div><h2 id="component-dialog-title"></h2><p id="component-dialog-description" class="dialog-intro"></p><p id="component-dialog-styles" class="component-dialog-styles" hidden></p><div class="command-box"><code id="component-command"></code></div><div class="dialog-actions"><button id="copy-component-command" class="primary-action" type="button" data-copy-label="复制安装命令">复制安装命令</button><a id="component-github" class="component-source-link" href="#" target="_blank" rel="nofollow noopener">打开 GitHub ↗</a></div></div></dialog><script>{script}</script></body></html>'''


def render_skill_lab_page(skills: list[dict], recipes: list[dict], site_url: str) -> str:
    page = _render_skill_lab_page(skills, recipes, site_url)
    return page.replace(
        '<a href="/skills/" aria-current="page">工作流配方</a>',
        '<a href="/skills/lab/" aria-current="page">工作流配方</a><a href="/skills/">Skill 目录</a>',
    )


SITEMAP_SECTIONS: tuple[str, ...] = ("pages", "offers", "providers", "models")


def sitemap_section_paths(
    offers: list[dict],
    categories: list[str],
    models: list[dict] | None = None,
    providers: list[dict] | None = None,
) -> dict[str, list[str]]:
    """Split sitemap URLs per section so GSC reports indexing progress per group.

    Single-record model aggregate pages and thin category landing pages are
    noindex, so they stay out of their section and do not dilute the crawl
    budget on pages worth indexing.
    """
    page_paths = [
        "/",
        "/about/",
        "/links/",
        "/terms/",
        "/privacy/",
        "/submit/",
        guide_url(),
        OPENAI_ALTERNATIVES_GUIDE_PATH,
        CLAUDE_CODE_ALTERNATIVES_GUIDE_PATH,
        MODELS_PAGE_PATH,
        ALL_MODELS_PAGE_PATH,
        MODEL_CENTER_PAGE_PATH,
        PROVIDERS_PAGE_PATH,
        CHANGE_LOG_PAGE_PATH,
        SKILLS_PAGE_PATH,
        SKILL_LAB_PAGE_PATH,
    ] + [f'/guides/{definition["slug"]}/' for definition in THEME_GUIDE_DEFINITIONS] + [
        category_url(category)
        for category in categories
        if category in indexable_category_slugs(offers)
    ]
    if models:
        total_pages = (len(models) + MODELS_PER_PAGE - 1) // MODELS_PER_PAGE
        page_paths += [f"{ALL_MODELS_PAGE_PATH}page/{page_num}/" for page_num in range(2, total_pages + 1)]
    indexable_slugs = indexable_model_slugs(models or [])
    sections = {
        "pages": page_paths,
        "offers": [offer_url(offer) for offer in offers],
        "providers": [provider_url(provider) for provider in (providers or [])],
        "models": [f"/models/{slug}/" for slug in sorted(indexable_slugs)],
    }
    return {section: list(dict.fromkeys(paths)) for section, paths in sections.items()}


def render_url_sitemap(paths: list[str], site_url: str) -> str:
    urls = "\n".join(f"  <url><loc>{_esc(_absolute(site_url, path))}</loc></url>" for path in paths)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
'''


def render_sitemap_index(site_url: str, sections: dict[str, list[str]]) -> str:
    entries = "\n".join(
        f"  <sitemap><loc>{_esc(_absolute(site_url, f'/sitemap-{section}.xml'))}</loc></sitemap>"
        for section in SITEMAP_SECTIONS
        if sections.get(section)
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</sitemapindex>
'''


def render_sitemaps(
    offers: list[dict],
    categories: list[str],
    site_url: str,
    models: list[dict] | None = None,
    providers: list[dict] | None = None,
) -> dict[Path, str]:
    sections = sitemap_section_paths(offers, categories, models, providers)
    files = {
        Path(f"sitemap-{section}.xml"): render_url_sitemap(paths, site_url)
        for section, paths in sections.items()
    }
    files[Path("sitemap.xml")] = render_sitemap_index(site_url, sections)
    return files


FEED_PATH = "feed.xml"
FEED_ENTRY_LIMIT = 50


def render_feed(offers: list[dict], site_url: str) -> str:
    """Render an Atom feed of the newest catalog entries for feed readers and aggregators."""
    feed_url = _absolute(site_url, "/" + FEED_PATH)
    site_root = _absolute(site_url, "/")

    def added_on(offer: dict) -> str:
        return str(offer.get("date") or "")

    ordered = sorted(
        (offer for offer in offers if offer.get("id")),
        key=added_on,
        reverse=True,
    )[:FEED_ENTRY_LIMIT]

    feed_updated = added_on(ordered[0]) if ordered else "1970-01-01"
    entries = []
    for offer in ordered:
        link = _absolute(site_url, offer_url(offer))
        title = offer.get("titleZh") or offer.get("title") or offer.get("id")
        summary = offer.get("freeSummary") or offer.get("why") or ""
        entry_date = added_on(offer) or feed_updated
        entries.append(
            "  <entry>\n"
            f"    <title>{_esc(title)}</title>\n"
            f'    <link href="{_esc(link)}"/>\n'
            f"    <id>{_esc(link)}</id>\n"
            f"    <updated>{_esc(entry_date)}T00:00:00Z</updated>\n"
            f"    <summary>{_esc(summary)}</summary>\n"
            "  </entry>"
        )

    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="zh-CN">\n'
        "  <title>FreeLLM · 免费 AI 资源新增</title>\n"
        "  <subtitle>逐条记录免费额度、地区限制与官方入口的 AI 资源目录</subtitle>\n"
        f'  <link href="{_esc(feed_url)}" rel="self"/>\n'
        f'  <link href="{_esc(site_root)}"/>\n'
        f"  <id>{_esc(site_root)}</id>\n"
        f"  <updated>{_esc(feed_updated)}T00:00:00Z</updated>\n"
        f"  <author><name>FreeLLM</name><uri>{_esc(site_root)}</uri></author>\n"
        f"{body}\n"
        "</feed>\n"
    )


def _skill_content_files(skills: list[dict], data_dir: Path | None) -> dict[Path, str]:
    """Serve every collected SKILL.md as a lazily fetched JSON document under /skills/content/."""
    base_dir = Path(data_dir) if data_dir else Path("data")
    files: dict[Path, str] = {}
    for skill in skills:
        relative = str(skill.get("contentPath") or "").strip()
        if not relative:
            continue
        md_path = Path(relative) if Path(relative).is_absolute() else base_dir / relative
        if not md_path.is_file():
            raise SystemExit(f"skill content file missing: {md_path}")
        text = md_path.read_text(encoding="utf-8")
        files[Path("skills") / "content" / f"{skill['id']}.json"] = json.dumps(
            {
                "id": skill.get("id"),
                "githubUrl": skill.get("githubUrl"),
                "contentUrl": skill.get("contentUrl"),
                "fetchedAt": skill.get("contentFetchedAt"),
                "bytes": len(text.encode("utf-8")),
                "content": text,
            },
            ensure_ascii=False,
        )
    return files


def _expected_files(offers: list[dict], site_url: str, models: list[dict] | None = None, operations: list[dict] | None = None, daily_logs: list[dict] | None = None, skills: list[dict] | None = None, recipes: list[dict] | None = None, data_dir: Path | None = None, vendor_directory: list[dict] | None = None) -> tuple[dict[Path, str], list[str]]:
    categories = [
        category
        for category in CATEGORY_DEFINITIONS
        if any(category in categorize_offer(offer) for offer in offers)
    ]
    model_catalog = models or []
    providers = _provider_catalog_from_models(model_catalog, operations)
    provider_access, _, model_access = _load_access_context()
    files: dict[Path, str] = {
        **render_sitemaps(offers, categories, site_url, model_catalog, providers),
        Path(FEED_PATH): render_feed(offers, site_url),
        Path("skills") / "index.html": render_skills_page(skills or [], site_url),
        Path("skills") / "lab" / "index.html": render_skill_lab_page(skills or [], recipes or [], site_url),
        Path("models") / "index.html": render_models_landing_page(offers, model_catalog, providers, site_url),
        Path("models") / "all" / "index.html": render_models_page(offers, site_url, models, page_num=1, total_pages=max(1, (len(model_catalog) + MODELS_PER_PAGE - 1) // MODELS_PER_PAGE) if models else 1),
        Path("models") / "center" / "index.html": render_model_center_page(offers, site_url, model_catalog),
        Path("providers") / "index.html": render_providers_page(providers, model_catalog, site_url),
        Path("logs") / "index.html": render_daily_log_page(daily_logs if daily_logs is not None else _load_daily_logs(ACCESS_DATA_DIR / "offers.json"), site_url, offers),
        Path("guides") / "free-llm" / "index.html": render_guide_page(site_url),
        Path("guides") / "free-openai-api-alternatives" / "index.html": render_openai_alternatives_page(offers, site_url),
        Path("guides") / "claude-code-free-alternatives" / "index.html": render_claude_code_alternatives_page(offers, site_url),
    }
    files.update(_skill_content_files(skills or [], data_dir))
    if models:
        total_pages = (len(model_catalog) + MODELS_PER_PAGE - 1) // MODELS_PER_PAGE
        for page_num in range(2, total_pages + 1):
            files[Path("models") / "all" / f"page/{page_num}" / "index.html"] = render_models_page(offers, site_url, models, page_num=page_num, total_pages=total_pages)
    for definition in THEME_GUIDE_DEFINITIONS:
        path = Path("guides") / definition["slug"] / "index.html"
        files[path] = _render_theme_guide_page_expanded(offers, model_catalog, site_url, definition["slug"])
    for offer in offers:
        files[Path("offers") / _slug(offer["id"]) / "index.html"] = render_offer_page(offer, offers, site_url, operations)
    for legacy_id, target_id in LEGACY_OFFER_REDIRECTS.items():
        files[Path("offers") / legacy_id / "index.html"] = render_legacy_offer_redirect(legacy_id, target_id, site_url)
    for category in categories:
        files[Path("category") / category / "index.html"] = render_category_page(category, offers, site_url)
    aggregate_groups = model_record_groups(model_catalog)
    for model_slug_key in sorted(aggregate_groups):
        records = aggregate_groups[model_slug_key]
        display_name = str(records[0].get("model") or "").strip() or model_slug_key
        files[Path("models") / model_slug_key / "index.html"] = render_model_aggregate_page(display_name, records, offers, site_url, provider_access, model_access)
    for provider in providers:
        files[Path("providers") / _safe_slug(provider.get("id"), "provider") / "index.html"] = render_provider_page(provider, model_catalog, offers, site_url, operations, provider_access, model_access)
    static_root = Path(__file__).resolve().parents[1]
    for relative in (
        "about/index.html", "links/index.html", "privacy/index.html", "terms/index.html",
        "favorites/index.html", "submit/index.html", "tools/index.html",
    ):
        source = static_root / relative
        if source.is_file():
            files[Path(relative)] = source.read_text(encoding="utf-8")
    if Path("about/index.html") in files:
        about = files[Path("about/index.html")]
        active_provider_id_count = len({str(item.get("providerId") or "").strip() for item in model_catalog if item.get("providerId")})
        replacement = (
            '<div class="stat-row">'
            f'<div class="stat"><strong>{len(offers)}</strong><span><span lang="zh-CN">已核验资源条目</span><span lang="en">verified offers</span></span></div>'
            f'<div class="stat"><strong>{len(model_catalog)}</strong><span><span lang="zh-CN">模型目录记录</span><span lang="en">model records</span></span></div>'
            f'<div class="stat"><strong>{len(providers)}</strong><span><span lang="zh-CN">厂家目录</span><span lang="en">vendor directory</span></span></div>'
            f'<div class="stat"><strong>{active_provider_id_count}</strong><span><span lang="zh-CN">当前数据 Provider ID</span><span lang="en">active provider IDs</span></span></div>'
            '</div>'
        )
        about = re.sub(r'<div class="stat-row">.*?</div>\s*</section>', replacement + '\n    </section>', about, count=1, flags=re.S)
        files[Path("about/index.html")] = about
    for path, page in list(files.items()):
        if path.suffix != ".html":
            continue
        if path.parts[:1] == ("offers",) and len(path.parts) > 1 and path.parts[1] in LEGACY_OFFER_REDIRECTS:
            continue
        page_path = "/" + path.as_posix()
        if page_path.endswith("index.html"):
            page_path = page_path[:-len("index.html")]
        files[path] = _normalize_seo_metadata(_inject_hreflang_links(page, site_url, page_path))
    return files, categories


def validate_skills(source: str | Path | list[dict]) -> list[str]:
    """Validate the small, publishable contract used by the Skills directory."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            return [f"skills file does not exist: {path}"]
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [f"skills file cannot be read: {error}"]
    if not isinstance(source, list):
        return ["skills data must be a JSON array"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(source):
        prefix = f"skills[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = [field for field in SKILL_REQUIRED_FIELDS if field not in item]
        if missing:
            errors.append(f"{prefix} missing required fields: {', '.join(missing)}")
        skill_id = str(item.get("id") or "").strip()
        if skill_id in seen_ids:
            errors.append(f"{prefix}.id must be unique: {skill_id}")
        if skill_id:
            seen_ids.add(skill_id)
        if item.get("category") not in SKILL_CATEGORY_DEFINITIONS:
            errors.append(f"{prefix}.category is unknown: {item.get('category')!r}")
        if item.get("status") not in SKILL_STATUS_LABELS:
            errors.append(f"{prefix}.status is unknown: {item.get('status')!r}")
        if not isinstance(item.get("compatibility"), list) or not item.get("compatibility"):
            errors.append(f"{prefix}.compatibility must be a non-empty array")
        github_url = str(item.get("githubUrl") or "")
        if github_url and not github_url.startswith("https://github.com/"):
            errors.append(f"{prefix}.githubUrl must use https://github.com/")
        link_check = item.get("linkCheck")
        if link_check is not None and link_check not in SKILL_LINK_CHECK_VALUES:
            errors.append(f"{prefix}.linkCheck is unknown: {link_check!r}")
        content_path = item.get("contentPath")
        if content_path is not None:
            if not isinstance(content_path, str) or not content_path or content_path.startswith("/") or ".." in content_path:
                errors.append(f"{prefix}.contentPath must be a relative path inside the data directory")
        reviews = item.get("reviews")
        if reviews is not None:
            if not isinstance(reviews, list) or len(reviews) > 6:
                errors.append(f"{prefix}.reviews must be an array of at most 6 items")
            else:
                for review_index, review in enumerate(reviews):
                    review_prefix = f"{prefix}.reviews[{review_index}]"
                    if not isinstance(review, dict) or not {"source", "url", "quote"} <= review.keys():
                        errors.append(f"{review_prefix} must be an object with source/url/quote")
                    elif not str(review.get("url") or "").startswith(("https://", "http://")):
                        errors.append(f"{review_prefix}.url must be an absolute http(s) URL")
                    elif not str(review.get("quote") or "").strip():
                        errors.append(f"{review_prefix}.quote must not be empty")
    return errors


def validate_skill_translations(source: str | Path | dict, skills: list[dict]) -> list[str]:
    """Validate the Chinese display-description overlay for every catalog entry."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            return [f"skill translations file does not exist: {path}"]
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [f"skill translations file cannot be read: {error}"]
    if not isinstance(source, dict):
        return ["skill translations data must be an object keyed by skill id"]

    errors: list[str] = []
    skill_ids = {str(item.get("id") or "").strip() for item in skills if isinstance(item, dict)}
    for skill_id, entry in source.items():
        prefix = f"skillTranslations[{skill_id}]"
        if skill_id not in skill_ids:
            errors.append(f"{prefix} references unknown skill id")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        description = entry.get("description_zh")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{prefix}.description_zh must be a non-empty string")
    missing = sorted(skill_ids - set(source))
    if missing:
        errors.append("skill translations must cover every catalog entry; missing: " + ", ".join(missing))
    return errors


def validate_skill_recipes(source: str | Path | list[dict], skills: list[dict]) -> list[str]:
    """Validate curated workflow recipes and their references into the component catalog."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            return [f"skill recipes file does not exist: {path}"]
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [f"skill recipes file cannot be read: {error}"]
    if not isinstance(source, list):
        return ["skill recipes data must be a JSON array"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    skill_ids = {str(item.get("id") or "").strip() for item in skills if isinstance(item, dict)}
    for index, item in enumerate(source):
        prefix = f"skillRecipes[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = [field for field in SKILL_RECIPE_REQUIRED_FIELDS if field not in item]
        if missing:
            errors.append(f"{prefix} missing required fields: {', '.join(missing)}")
        recipe_id = str(item.get("id") or "").strip()
        if recipe_id in seen_ids:
            errors.append(f"{prefix}.id must be unique: {recipe_id}")
        if recipe_id:
            seen_ids.add(recipe_id)
        steps = item.get("steps")
        if not isinstance(steps, list) or len(steps) < 3:
            errors.append(f"{prefix}.steps must contain at least 3 steps")
            continue
        for step_index, step in enumerate(steps):
            step_prefix = f"{prefix}.steps[{step_index}]"
            if not isinstance(step, dict):
                errors.append(f"{step_prefix} must be an object")
                continue
            skill_id = str(step.get("skillId") or "").strip()
            if skill_id not in skill_ids:
                errors.append(f"{step_prefix}.skillId references unknown component: {skill_id}")
    return errors


SKILL_STYLE_REQUIRED_FIELDS = ("format", "summary")
SKILL_STYLE_MAX_ITEMS = 30


def validate_skill_styles(source: str | Path | dict, skills: list[dict]) -> list[str]:
    """Validate the curated presentation-style overlay for the skill catalog."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            return [f"skill styles file does not exist: {path}"]
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [f"skill styles file cannot be read: {error}"]
    if not isinstance(source, dict) or not isinstance(source.get("entries"), dict):
        return ["skill styles data must be an object with an 'entries' mapping"]

    errors: list[str] = []
    entries = source["entries"]
    skill_ids = {str(item.get("id") or "").strip() for item in skills if isinstance(item, dict)}
    for skill_id, entry in entries.items():
        prefix = f"skillStyles[{skill_id}]"
        if skill_id not in skill_ids:
            errors.append(f"{prefix} references unknown skill id")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in SKILL_STYLE_REQUIRED_FIELDS:
            if not str(entry.get(field) or "").strip():
                errors.append(f"{prefix}.{field} must not be empty")
        if not isinstance(entry.get("hasStyles"), bool):
            errors.append(f"{prefix}.hasStyles must be a boolean")
        items = entry.get("items")
        if items is not None:
            if not isinstance(items, list) or not all(isinstance(item, str) and item.strip() for item in items):
                errors.append(f"{prefix}.items must be a list of non-empty strings")
            elif len(items) > SKILL_STYLE_MAX_ITEMS:
                errors.append(f"{prefix}.items must contain at most {SKILL_STYLE_MAX_ITEMS} entries")
        total = entry.get("total")
        if total is not None and (isinstance(total, bool) or not isinstance(total, int) or total < 1):
            errors.append(f"{prefix}.total must be a positive integer")
    missing = sorted(skill_ids - set(entries))
    if missing:
        errors.append("skill styles must cover every catalog entry; missing: " + ", ".join(missing))
    return errors


def _load_skills(data_path: Path) -> list[dict]:
    skills_path = data_path.parent / "skills.json"
    if not skills_path.is_file():
        return []
    errors = validate_skills(skills_path)
    if errors:
        raise SystemExit("Invalid skills data:\n" + "\n".join(errors))
    skills = json.loads(skills_path.read_text(encoding="utf-8"))
    translations_path = data_path.parent / "skills-i18n.json"
    errors = validate_skill_translations(translations_path, skills)
    if errors:
        raise SystemExit("Invalid skill translations data:\n" + "\n".join(errors))
    translations = json.loads(translations_path.read_text(encoding="utf-8"))
    return [{**skill, **translations[skill["id"]]} for skill in skills]


def _load_skill_styles(data_path: Path, skills: list[dict]) -> dict[str, dict]:
    styles_path = data_path.parent / "skill-styles.json"
    if not styles_path.is_file():
        return {}
    errors = validate_skill_styles(styles_path, skills)
    if errors:
        raise SystemExit("Invalid skill styles data:\n" + "\n".join(errors))
    return json.loads(styles_path.read_text(encoding="utf-8")).get("entries") or {}


def _merge_skill_styles(skills: list[dict], styles: dict[str, dict]) -> list[dict]:
    """Attach each skill's presentation-style entry so cards, dialogs and search can use it."""
    if not styles:
        return skills
    return [{**skill, "styles": styles[skill["id"]]} if skill.get("id") in styles else skill for skill in skills]


def _load_skill_tests(data_path: Path, skills: list[dict]) -> dict[str, dict]:
    tests_path = data_path.parent / "skill-tests.json"
    if not tests_path.is_file():
        return {}
    payload = json.loads(tests_path.read_text(encoding="utf-8"))
    entries = payload.get("entries") or {}
    known = {skill.get("id") for skill in skills}
    unknown = sorted(set(entries) - known)
    missing = sorted(known - set(entries))
    if unknown or missing:
        details = []
        if unknown:
            details.append("unknown: " + ", ".join(unknown))
        if missing:
            details.append("missing: " + ", ".join(missing))
        raise SystemExit("Invalid skill test data: " + "; ".join(details))
    return entries


def _merge_skill_tests(skills: list[dict], tests: dict[str, dict]) -> list[dict]:
    if not tests:
        return skills
    return [{**skill, "freeLLMTest": tests.get(skill.get("id"), {})} for skill in skills]


def _load_skill_recipes(data_path: Path, skills: list[dict]) -> list[dict]:
    recipes_path = data_path.parent / "skill-recipes.json"
    if not recipes_path.is_file():
        return []
    errors = validate_skill_recipes(recipes_path, skills)
    if errors:
        raise SystemExit("Invalid skill recipes data:\n" + "\n".join(errors))
    return json.loads(recipes_path.read_text(encoding="utf-8"))


def _load_vendor_directory(data_path: Path) -> list[dict]:
    path = data_path.parent / "provider-catalog.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else []


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


def _clean_previous_pages(output_root: Path, keep: set[str] | None = None) -> int:
    """Remove pages from the previous build that this build no longer produces.

    `keep` holds every relative path the current build writes. Anything absent
    from it is a retired page and gets deleted; passing an empty set deletes
    every managed page, so callers must always write the new pages first.
    """
    removed = 0
    for relative in _read_manifest(output_root):
        if keep is not None and relative in keep:
            continue
        path = (output_root / relative).resolve()
        root = output_root.resolve()
        try:
            relative_path = path.relative_to(root)
        except ValueError:
            continue
        if root not in path.parents or path.name != "index.html" or relative_path.parts[0] not in {"offers", "category", "guides", "models", "providers", "logs", "skills"}:
            # 深度不限：models/all/page/N/index.html 这类分页页（5 段路径）也是受管页面，
            # 目录瘦身、分页数变少时同样要随 manifest 清理，否则会留下带死链的陈旧分页。
            continue
        if path.is_file():
            path.unlink()
            removed += 1
        try:
            path.parent.rmdir()
        except OSError:
            pass
    return removed


LEGAL_FOOTER_LINKS = (
    '<p><a href="/about/">{zh}关于本站{/zh}{en}About{/en}</a>'
    ' · <a href="/links/">{zh}友链与相关资源{/zh}{en}Links{/en}</a>'
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



def _visual_section_for_path(path: Path) -> str:
    parts = path.parts
    first = parts[0] if parts else ""
    if first == "skills":
        return "workflow" if len(parts) > 1 and parts[1] == "lab" else "skills"
    if first == "tools":
        return "tools"
    if first == "logs":
        return "logs"
    if first in {"models", "providers", "offers", "category", "guides"}:
        return "models"
    if first in {"about", "links", "privacy", "terms"}:
        return "about"
    if first in {"favorites", "submit"}:
        return ""
    return "home"


def _ensure_visual_classes(content: str, path: Path) -> str:
    """Make the design system work even if the shared JS is blocked or cached."""
    if path.suffix != ".html":
        return content
    updated = content
    html_match = re.search(r"<html([^>]*)>", updated, flags=re.I)
    if html_match:
        attrs = html_match.group(1)
        class_match = re.search(r'class="([^"]*)"', attrs)
        if class_match:
            classes = class_match.group(1).split()
            if "fl-pastel-ui" not in classes:
                attrs = attrs[:class_match.start()] + f'class="{class_match.group(1)} fl-pastel-ui"' + attrs[class_match.end():]
        else:
            attrs += ' class="fl-pastel-ui"'
        replacement = f"<html{attrs}>"
        updated = updated[:html_match.start()] + replacement + updated[html_match.end():]

    body_match = re.search(r"<body([^>]*)>", updated, flags=re.I)
    if body_match:
        attrs = body_match.group(1)
        class_match = re.search(r'class="([^"]*)"', attrs)
        if class_match:
            classes = class_match.group(1).split()
            if "fl-ui-v2" not in classes:
                attrs = attrs[:class_match.start()] + f'class="{class_match.group(1)} fl-ui-v2"' + attrs[class_match.end():]
        else:
            attrs += ' class="fl-ui-v2"'
        if "data-fl-section=" not in attrs:
            attrs += f' data-fl-section="{_visual_section_for_path(path)}"'
        replacement = f"<body{attrs}>"
        updated = updated[:body_match.start()] + replacement + updated[body_match.end():]
    return updated


def _remove_legacy_global_nav(content: str) -> str:
    return re.sub(r'<nav class="top-nav"[^>]*>.*?</nav>', "", content, flags=re.I | re.S)


def _ensure_static_site_chrome(content: str, path: Path) -> str:
    if path.suffix != ".html":
        return content
    section = _visual_section_for_path(path)
    items = [
        ("/", "⌂", "首页", "home"),
        ("/models/", "▣", "模型", "models"),
        ("/skills/", "✦", "Skills", "skills"),
        ("/tools/", "⌘", "工具", "tools"),
        ("/skills/lab/", "⌁", "工作流", "workflow"),
        ("/logs/", "◷", "更新", "logs"),
        ("/about/", "ⓘ", "关于", "about"),
    ]
    def render_link(item: tuple[str, str, str, str]) -> str:
        href, icon, label, key = item
        current = ' aria-current="page"' if key == section else ""
        return f'<a href="{href}" data-site-nav="{key}"{current}><span class="fl-site-nav-icon" aria-hidden="true">{icon}</span><span>{label}</span></a>'
    links = "".join(render_link(item) for item in items)
    chrome = (
        '<aside class="fl-site-rail" aria-label="FreeLLM 主导航">'
        '<a class="fl-site-brand" href="/"><span class="fl-site-brand-mark" aria-hidden="true">AI</span>'
        '<span class="fl-site-brand-copy"><strong>FreeLLM</strong><small>让 AI 更自由地被使用</small></span></a>'
        f'<nav class="fl-site-nav">{links}</nav>'
        '<div class="fl-site-rail-note"><span>好的 AI 资源</span><br>让更多人真正受益 ♡</div></aside>'
        '<div class="fl-site-ribbon"><span class="fl-site-ribbon-title">FREE AI INDEX / 统一产品界面</span>'
        '<span class="fl-site-ribbon-actions"><a href="/favorites/">我的收藏</a><a href="/submit/">提交资源 ↗</a></span></div>'
    )
    shell_pattern = r'<aside class="fl-site-rail"[^>]*>.*?</aside>\s*<div class="fl-site-ribbon"[^>]*>.*?</div>'
    normalized = re.sub(shell_pattern, "", content, count=1, flags=re.I | re.S)
    return re.sub(r'(<body[^>]*>)', lambda match: match.group(1) + chrome, normalized, count=1, flags=re.I)


def _ensure_model_section_tabs(content: str, path: Path) -> str:
    if path.suffix != ".html" or 'class="model-section-tabs"' in content:
        return content
    parts = path.parts
    if not parts or parts[0] not in {"models", "providers"}:
        return content
    route = "/" + "/".join(parts[:-1]) + "/" if parts[-1] == "index.html" else "/" + "/".join(parts) + "/"
    current = "overview"
    if route.startswith("/models/all/"):
        current = "all"
    elif route.startswith("/providers/"):
        current = "providers"
    elif route.startswith("/models/center/"):
        current = "center"
    items = [
        ("overview", MODELS_PAGE_PATH, "概览"),
        ("all", ALL_MODELS_PAGE_PATH, "全部模型"),
        ("providers", PROVIDERS_PAGE_PATH, "按厂家"),
        ("offers", "/category/api/", "免费 API / Offer"),
    ]
    links = []
    for key, href, label in items:
        current_attr = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    tabs = '<nav class="model-section-tabs" aria-label="模型页面">' + "".join(links) + "</nav>"
    ribbon_end = content.find("</div>", content.find('class="fl-site-ribbon"'))
    if ribbon_end >= 0:
        ribbon_end += len("</div>")
        return content[:ribbon_end] + tabs + content[ribbon_end:]
    return re.sub(r'(<body[^>]*>)', lambda match: match.group(1) + tabs, content, count=1, flags=re.I)


def build_site(data_path: str | Path, output_root: str | Path, site_url: str = SITE_URL, check: bool = False) -> BuildResult | bool:
    data_path = Path(data_path)
    offers = _load_data(data_path)
    models = _load_models(data_path)
    models = _exclude_retired_models(models, _load_model_access(data_path))
    operations = _load_operations(data_path)
    skills = _load_skills(data_path)
    skills = _merge_skill_styles(skills, _load_skill_styles(data_path, skills))
    skills = _merge_skill_tests(skills, _load_skill_tests(data_path, skills))
    recipes = _load_skill_recipes(data_path, skills)
    daily_logs = _load_daily_logs(data_path)
    vendor_directory = _load_vendor_directory(data_path)
    files, categories = _expected_files(offers, site_url.rstrip("/"), models, operations, daily_logs, skills, recipes, data_dir=data_path.parent, vendor_directory=vendor_directory)
    files = {
        relative: (_append_legal_links(content) if relative.suffix == ".html" else content)
        for relative, content in files.items()
    }
    theme_tag = '<link rel="stylesheet" href="/css/freellm-pastel-ui.css?v=20260920c">'
    files = {
        relative: (content if (relative.suffix != ".html" or "freellm-pastel-ui.css" in content or "</head>" not in content)
                   else content.replace("</head>", theme_tag + "</head>", 1))
        for relative, content in files.items()
    }
    files = {
        relative: _ensure_visual_classes(content, relative)
        for relative, content in files.items()
    }
    files = {
        relative: _ensure_static_site_chrome(_remove_legacy_global_nav(content), relative)
        for relative, content in files.items()
    }
    files = {
        relative: _ensure_model_section_tabs(content, relative)
        for relative, content in files.items()
    }
    sync_tag = '<script src="/js/freellm-sync.js"></script>'
    files = {
        relative: (content if (relative.suffix != ".html" or "freellm-sync.js" in content or "</body>" not in content)
                   else content.replace("</body>", sync_tag + "</body>", 1))
        for relative, content in files.items()
    }
    output_root = Path(output_root)
    if check:
        stale = []
        for relative, content in files.items():
            path = output_root / relative
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != content:
                stale.append(str(relative))
                if current is not None and len(stale) <= 3:
                    limit = min(len(current), len(content))
                    offset = next((i for i in range(limit) if current[i] != content[i]), limit)
                    left = max(0, offset - 180)
                    right = offset + 260
                    print(f"stale detail {relative} @ char {offset}")
                    print("  current :", repr(current[left:right]))
                    print("  expected:", repr(content[left:right]))
        if stale:
            print("stale SEO output: " + ", ".join(stale))
            return False
        print(f"current SEO output: {len(files)} files")
        return True

    managed = {path.as_posix() for path in files if path.parts and path.parts[0] in {"offers", "category", "guides", "models", "providers", "logs", "skills"}}
    # Write the new pages before deleting retired ones: a crash or an external
    # delete guard must never leave the output tree emptied.
    for relative, content in files.items():
        path = output_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    removed = _clean_previous_pages(output_root, keep=managed)
    manifest = {"files": sorted(managed)}
    (output_root / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if removed:
        print(f"removed {removed} retired page(s)")
    # page_count counts published pages (HTML + sitemap.xml); data files such as
    # skills/content/*.json are written and checked but are not pages.
    page_count = sum(1 for path in files if path.suffix in {".html", ".xml"})
    result = BuildResult(offer_count=len(offers), category_count=len(categories), page_count=page_count)
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
