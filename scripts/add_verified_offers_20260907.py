# -*- coding: utf-8 -*-
"""Append officially verified free-model offers (2026-09-07 scan) to the public data files.

Every entry below is backed by an official page snapshot saved under
data/snapshots/verify-20260907/ during this session. Entries whose official
evidence could not be captured (NVIDIA NIM, iFlytek Spark free quota, MiniMax,
Moonshot, Xiaomi MiMo, Baidu Qianfan) are NOT added here and stay in the
candidate / review queue per the publication gate.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.schema import validate_offers

TODAY = "2026-09-07"

NEW_PROVIDERS = [
    {
        "id": "google-ai-studio",
        "name": "Google AI Studio",
        "aliases": ["Google AI Studio", "Gemini API", "Google Gemini"],
        "region": "global",
        "allowedDomains": ["ai.google.dev", "aistudio.google.com", "developers.google.com"],
        "discoveryUrls": [
            "https://ai.google.dev/gemini-api/docs/pricing",
            "https://ai.google.dev/gemini-api/docs/quickstart",
        ],
    },
    {
        "id": "groq",
        "name": "Groq",
        "aliases": ["Groq", "GroqCloud"],
        "region": "global",
        "allowedDomains": ["console.groq.com", "groq.com"],
        "discoveryUrls": [
            "https://console.groq.com/docs/rate-limits",
            "https://console.groq.com/docs/openai",
        ],
    },
    {
        "id": "cerebras",
        "name": "Cerebras",
        "aliases": ["Cerebras Inference", "Cerebras"],
        "region": "global",
        "allowedDomains": ["www.cerebras.ai", "inference-docs.cerebras.ai"],
        "discoveryUrls": [
            "https://www.cerebras.ai/pricing",
            "https://inference-docs.cerebras.ai/quickstart",
        ],
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "aliases": ["OpenRouter"],
        "region": "global",
        "allowedDomains": ["openrouter.ai"],
        "discoveryUrls": [
            "https://openrouter.ai/docs/api_reference/limits",
            "https://openrouter.ai/docs/quickstart",
        ],
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "aliases": ["Mistral", "La Plateforme", "Mistral AI Studio"],
        "region": "global",
        "allowedDomains": ["docs.mistral.ai", "help.mistral.ai", "console.mistral.ai"],
        "discoveryUrls": [
            "https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them",
            "https://docs.mistral.ai/api",
        ],
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "aliases": ["Cohere", "Cohere Trial API key"],
        "region": "global",
        "allowedDomains": ["cohere.com", "docs.cohere.com", "dashboard.cohere.com"],
        "discoveryUrls": [
            "https://cohere.com/pricing",
            "https://docs.cohere.com/reference/chat",
        ],
    },
    {
        "id": "huggingface",
        "name": "Hugging Face",
        "aliases": ["HuggingFace", "HF Inference Providers", "Hugging Face Inference Providers"],
        "region": "global",
        "allowedDomains": ["huggingface.co"],
        "discoveryUrls": [
            "https://huggingface.co/docs/inference-providers/index",
            "https://huggingface.co/docs/inference-providers/pricing",
        ],
    },
]


def offer_common():
    return {
        "date": TODAY,
        "lastVerifiedAt": TODAY,
        "checkedBy": "manual",
        "status": "verified",
        "phoneRequired": "unknown",
        "cardRequired": "unknown",
        "commercialUse": "Check the provider's official terms",
        "productType": "api",
        "capabilities": ["model_api"],
    }


NEW_OFFERS = []

# 28 Google AI Studio / Gemini API free tier
o = offer_common()
o.update({
    "id": "google-ai-studio-free",
    "order": 28,
    "name": "Google AI Studio / Gemini API free tier",
    "providerMark": "GM",
    "provider": "Google AI Studio",
    "providerMeta": "Google · International",
    "model": "Gemini 3.8 Flash (gemini-3.8-flash) and other Gemini models on the free tier",
    "modelMeta": "Hosted Gemini API models",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Call Gemini models through the official Gemini API free tier",
        "prerequisites": ["Google account", "API key created in Google AI Studio"],
        "steps": [
            "Sign in to Google AI Studio and create an API key",
            "Send a generateContent request with the key and read the rate-limit page for current free tier limits",
        ],
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
        "method": "POST",
        "authentication": "API key via x-goog-api-key header",
        "examples": {
            "curl": "curl https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent --header 'x-goog-api-key: ${GEMINI_API_KEY}' --header 'Content-Type: application/json' -X POST --data '{\"contents\":[{\"parts\":[{\"text\":\"Hello\"}]}]}'"
        },
        "docsUrl": "https://ai.google.dev/gemini-api/docs/quickstart",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["FREE TIER", "RATE LIMITED"],
    "freeSummary": "Free tier: input, output and context caching listed as Free of charge",
    "validitySummary": "Ongoing free tier; limits and terms can change",
    "accessSummary": "Google account; availability may vary by region",
    "checkedSummary": "Today / official Gemini API pricing page",
    "title": "Google AI Studio · Gemini API free tier",
    "why": "Google's official Gemini API pricing page shows a Free Tier column where input, output and context caching prices are listed as 'Free of charge'. The free tier is rate limited and, per the same page, free-tier data may be used to improve Google products.",
    "mechanism": "Rate-limited free tier on the Gemini API",
    "validity": "Ongoing, but limits and model coverage can change; recheck the official pricing page",
    "access": "Google account and API key from AI Studio; free tier availability may vary by region",
    "command": "curl https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent --header 'x-goog-api-key: ${GEMINI_API_KEY}' --header 'Content-Type: application/json' -X POST --data '{\"contents\":[{\"parts\":[{\"text\":\"Hello\"}]}]}'",
    "register": "https://aistudio.google.com/",
    "registerLabel": "Google AI Studio",
    "links": [
        ["Official Gemini API pricing", "https://ai.google.dev/gemini-api/docs/pricing"],
        ["Quickstart", "https://ai.google.dev/gemini-api/docs/quickstart"],
    ],
    "originCountry": "International",
    "availability": "Global; free tier and model availability may vary by region",
    "freeMechanism": "permanent",
    "pricingModel": "free_rate_limited",
    "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
    "quota": "Rate-limited free usage; exact RPM/TPM limits are shown in the official rate limits documentation",
    "renewal": "No renewal; the free tier is the default no-cost tier of the API",
    "sourceUrls": [
        "https://ai.google.dev/gemini-api/docs/pricing",
        "https://ai.google.dev/gemini-api/docs/quickstart",
    ],
    "evidence": "Official pricing page: 'Gemini 3.8 Flash ... Free Tier ... Input price Free of charge ... Output price (including thinking tokens) Free of charge ... Context caching price Free of charge', and free tier 'Used to improve our products: Yes'.",
    "confidence": "high",
    "notes": "International option included in the China-first global directory. Free-tier terms (including training-data usage) differ from the paid tier.",
})
NEW_OFFERS.append(o)

# 29 Groq free plan
o = offer_common()
o.update({
    "id": "groq-free",
    "order": 29,
    "name": "Groq free plan",
    "providerMark": "GQ",
    "provider": "Groq",
    "providerMeta": "Groq · International",
    "model": "gpt-oss-120b / gpt-oss-20b · qwen3.x-27b · groq/compound · llama-prompt-guard · whisper-large-v3",
    "modelMeta": "Hosted OpenAI-compatible models",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Call hosted models on Groq's OpenAI-compatible API under the free plan limits",
        "prerequisites": ["Groq account", "API key from the Groq console"],
        "steps": [
            "Create a Groq account and generate an API key in the console",
            "Send an OpenAI-compatible chat completion request and stay within the per-model free plan rate limits",
        ],
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "method": "POST",
        "authentication": "API key via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://api.groq.com/openai/v1/chat/completions --header 'Authorization: Bearer ${GROQ_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"openai/gpt-oss-20b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://console.groq.com/docs/rate-limits",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["FREE PLAN", "RATE LIMITED"],
    "freeSummary": "Free plan with per-model RPM / RPD / TPM limits (e.g. gpt-oss-120b: 30 RPM · 1K RPD · 8K TPM)",
    "validitySummary": "Ongoing free plan; exact limits per model can change",
    "accessSummary": "Groq account; rate limits apply at organization level",
    "checkedSummary": "Today / official Groq rate limits docs",
    "title": "Groq · free plan rate limits",
    "why": "Groq's official rate limits documentation publishes a 'Free Plan Limits' table with per-model RPM, RPD and TPM caps (for example openai/gpt-oss-120b: 30 RPM, 1K RPD, 8K TPM), alongside a paid Developer plan for higher limits.",
    "mechanism": "Free plan with per-model rate limits on the OpenAI-compatible API",
    "validity": "Ongoing free plan; the published limits table can change at any time",
    "access": "Groq account; limits apply per organization, not per user",
    "command": "curl https://api.groq.com/openai/v1/chat/completions --header 'Authorization: Bearer ${GROQ_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"openai/gpt-oss-20b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://console.groq.com/",
    "registerLabel": "Groq Console",
    "links": [
        ["Official rate limits (free plan table)", "https://console.groq.com/docs/rate-limits"],
        ["OpenAI compatibility", "https://console.groq.com/docs/openai"],
    ],
    "originCountry": "International",
    "availability": "Global; model availability may vary by region",
    "freeMechanism": "permanent",
    "pricingModel": "free_rate_limited",
    "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
    "quota": "Per-model free plan limits, e.g. 30 RPM / 1K RPD / 8K TPM for gpt-oss models; 250 RPD / 70K TPM for groq/compound",
    "renewal": "Daily and per-minute limits reset automatically",
    "sourceUrls": [
        "https://console.groq.com/docs/rate-limits",
        "https://console.groq.com/docs/openai",
    ],
    "evidence": "Official docs: 'Free Plan Limits ... MODEL ID RPM RPD TPM TPD ... openai/gpt-oss-120b 30 1K 8K 200K ... groq/compound 30 250 70K'; 'Need higher rate limits? Upgrade to Developer plan'.",
    "confidence": "high",
    "notes": "International option included in the China-first global directory.",
})
NEW_OFFERS.append(o)

# 30 Cerebras free trial credits
o = offer_common()
o.update({
    "id": "cerebras-free",
    "order": 30,
    "name": "Cerebras Inference free credits",
    "providerMark": "CE",
    "provider": "Cerebras",
    "providerMeta": "Cerebras · International",
    "model": "All Cerebras-powered hosted models while free credits last",
    "modelMeta": "Hosted wafer-scale inference",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Use the free credits granted after creating a Cerebras account",
        "prerequisites": ["Cerebras account", "API key generated in the Cerebras console"],
        "steps": [
            "Create a Cerebras account to receive the free credits",
            "Generate an API key and send an OpenAI-compatible chat completion request",
        ],
        "endpoint": "https://api.cerebras.ai/v1/chat/completions",
        "method": "POST",
        "authentication": "API key via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://api.cerebras.ai/v1/chat/completions --header 'Authorization: Bearer ${CEREBRAS_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"qwen-3.8-27b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://inference-docs.cerebras.ai/quickstart",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["FREE CREDITS"],
    "freeSummary": "Free trial: $5 in free credits after account creation",
    "validitySummary": "One-time credits; consumed by usage",
    "accessSummary": "Cerebras account",
    "checkedSummary": "Today / official Cerebras pricing page",
    "title": "Cerebras · free inference credits",
    "why": "The official Cerebras pricing page lists an 'Inference API access / Free Trial' tier: 'Get started with $5 in free credits after making an account. Access to all Cerebras powered models'. The docs also note free accounts have lower per-minute limits than paid accounts.",
    "mechanism": "One-time $5 free credits granted after account creation",
    "validity": "Credits are consumed by usage; check the official pricing page for current terms",
    "access": "Cerebras account required",
    "command": "curl https://api.cerebras.ai/v1/chat/completions --header 'Authorization: Bearer ${CEREBRAS_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"qwen-3.8-27b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://cloud.cerebras.ai/",
    "registerLabel": "Cerebras cloud console",
    "links": [
        ["Official pricing (free trial)", "https://www.cerebras.ai/pricing"],
        ["Quickstart", "https://inference-docs.cerebras.ai/quickstart"],
    ],
    "originCountry": "International",
    "availability": "Global; availability may vary by region",
    "freeMechanism": "trial",
    "pricingModel": "free_credits",
    "freePolicy": {"type": "one_time_credits", "amount": 5, "unit": "USD credits", "period": None},
    "quota": "$5 in one-time free credits",
    "renewal": "No automatic renewal of the free credits",
    "sourceUrls": [
        "https://www.cerebras.ai/pricing",
        "https://inference-docs.cerebras.ai/quickstart",
    ],
    "evidence": "Official pricing page: 'Free Trial Get started with $5 in free credits after making an account Access to all Cerebras powered models'; docs: 'Free accounts have lower per-minute limits than paid accounts'.",
    "confidence": "high",
    "notes": "International option included in the China-first global directory. Credits are a one-time trial, not a permanent free tier.",
})
NEW_OFFERS.append(o)

# 31 OpenRouter :free variants
o = offer_common()
o.update({
    "id": "openrouter-free",
    "order": 31,
    "name": "OpenRouter free model variants",
    "providerMark": "OR",
    "provider": "OpenRouter",
    "providerMeta": "OpenRouter · International",
    "model": "Model variants whose ID ends in :free (free model variants)",
    "modelMeta": "Multi-provider free variants",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Call models with :free variant IDs through the OpenRouter API within the free usage limits",
        "prerequisites": ["OpenRouter account", "API key from the OpenRouter dashboard"],
        "steps": [
            "Create an OpenRouter account and generate an API key",
            "Send chat completion requests to model IDs ending in :free and observe the published per-day request caps",
        ],
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "method": "POST",
        "authentication": "API key via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://openrouter.ai/api/v1/chat/completions --header 'Authorization: Bearer ${OPENROUTER_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"inclusionai/ling-3.0-flash-fin:free\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://openrouter.ai/docs/api_reference/limits",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["FREE VARIANTS", "DAILY CAP"],
    "freeSummary": ":free variants: 20 req/min; 50 req/day (under 10 credits purchased) or 1000 req/day (10+ credits)",
    "validitySummary": "Ongoing free usage limits; caps can change",
    "accessSummary": "OpenRouter account; daily caps depend on lifetime credit purchases",
    "checkedSummary": "Today / official OpenRouter limits docs",
    "title": "OpenRouter · free model variants",
    "why": "OpenRouter's official limits documentation defines free usage limits for model variants whose ID ends in ':free': 20 requests per minute, and 50 requests per day for accounts that purchased less than 10 credits (1000 requests per day at 10 or more credits).",
    "mechanism": "Platform-level free usage limits applied to :free model variants",
    "validity": "Ongoing; the limits table is subject to change by OpenRouter",
    "access": "OpenRouter account and API key; free daily cap scales with lifetime credits purchased",
    "command": "curl https://openrouter.ai/api/v1/chat/completions --header 'Authorization: Bearer ${OPENROUTER_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"inclusionai/ling-3.0-flash-fin:free\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://openrouter.ai/",
    "registerLabel": "OpenRouter",
    "links": [
        ["Official credit and rate limits", "https://openrouter.ai/docs/api_reference/limits"],
        ["Quickstart", "https://openrouter.ai/docs/quickstart"],
    ],
    "originCountry": "International",
    "availability": "Global; :free variant catalog changes frequently",
    "freeMechanism": "daily_quota",
    "pricingModel": "free_rate_limited",
    "freePolicy": {"type": "daily_quota", "amount": 50, "unit": "requests", "period": "day"},
    "quota": "20 requests per minute; 50 requests per day (less than 10 credits purchased) or 1000 requests per day (at least 10 credits)",
    "renewal": "Daily caps reset each day",
    "sourceUrls": [
        "https://openrouter.ai/docs/api_reference/limits",
        "https://openrouter.ai/docs/quickstart",
    ],
    "evidence": "Official docs table: 'Credits purchased (all time) | Requests per minute | Requests per day; Less than 10 | 20 | 50; At least 10 | 20 | 1000', applied to 'a free model variant (with an ID ending in :free)'. The official GET /api/v1/models catalog currently lists 18 model IDs ending in :free (e.g. inclusionai/ling-3.0-flash-fin:free).",
    "confidence": "high",
    "notes": "International option included in the China-first global directory. Example model ID should be verified against the live :free catalog before use.",
})
NEW_OFFERS.append(o)

# 32 Mistral free mode
o = offer_common()
o.update({
    "id": "mistral-free-mode",
    "order": 32,
    "name": "Mistral La Plateforme free mode",
    "providerMark": "MI",
    "provider": "Mistral AI",
    "providerMeta": "Mistral AI · International",
    "model": "Mistral API models under free mode rate limits",
    "modelMeta": "Hosted Mistral models",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Use the Mistral API in free mode, the default tier for evaluation and prototyping",
        "prerequisites": ["Mistral account (La Plateforme / AI Studio)", "API key"],
        "steps": [
            "Create a Mistral account and generate an API key",
            "Call the chat completions endpoint within free mode limits; check the Limits page of the Admin panel for your current tier",
        ],
        "endpoint": "https://api.mistral.ai/v1/chat/completions",
        "method": "POST",
        "authentication": "API key via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://api.mistral.ai/v1/chat/completions --header 'Authorization: Bearer ${MISTRAL_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"mistral-small-latest\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["FREE MODE", "RATE LIMITED"],
    "freeSummary": "Free mode (default): lowest rate limits, intended for evaluation and prototyping",
    "validitySummary": "Ongoing default tier; limits can change",
    "accessSummary": "Mistral account",
    "checkedSummary": "Today / official Mistral help center",
    "title": "Mistral · La Plateforme free mode",
    "why": "The official Mistral help center states: 'Free mode (the default) has the lowest limits, intended for evaluation and prototyping', with pay-as-you-go tiers unlocking higher limits.",
    "mechanism": "Default free mode of the developer API with limited rate limits (RPS, tokens per minute, tokens per month)",
    "validity": "Ongoing default tier; Mistral can change the limits",
    "access": "Mistral account; per-organization limits",
    "command": "curl https://api.mistral.ai/v1/chat/completions --header 'Authorization: Bearer ${MISTRAL_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"mistral-small-latest\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://console.mistral.ai/",
    "registerLabel": "Mistral console",
    "links": [
        ["Official rate limits article", "https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them"],
        ["API reference", "https://docs.mistral.ai/api"],
    ],
    "originCountry": "International",
    "availability": "Global; availability may vary by region",
    "freeMechanism": "permanent",
    "pricingModel": "free_rate_limited",
    "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
    "quota": "Lowest-tier rate limits: requests per second, tokens per minute and tokens per month, shown in the Admin panel Limits page",
    "renewal": "Monthly token caps reset per billing period",
    "sourceUrls": [
        "https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them",
        "https://docs.mistral.ai/api",
    ],
    "evidence": "Official help article: 'Free mode (the default) has the lowest limits, intended for evaluation and prototyping ... Rate limits depend on your plan and usage tier'.",
    "confidence": "medium",
    "confidenceReason": "Free mode is confirmed as the default tier, but the article does not publish numeric free-mode limits; treat exact quota as unconfirmed.",
    "notes": "International option included in the China-first global directory.",
})
NEW_OFFERS.append(o)

# 33 Cohere trial key
o = offer_common()
o.update({
    "id": "cohere-trial-key",
    "order": 33,
    "name": "Cohere trial API key",
    "providerMark": "CO",
    "provider": "Cohere",
    "providerMeta": "Cohere · International",
    "model": "Command chat models (trial key rate limits)",
    "modelMeta": "Hosted Cohere models",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Use a free Trial API key for evaluation of Cohere models",
        "prerequisites": ["Cohere account (personal accounts start with trial access)"],
        "steps": [
            "Sign up in the Cohere dashboard; every account starts with Trial API key access",
            "Call the chat endpoint with the trial key within its rate limits (non-production use)",
        ],
        "endpoint": "https://api.cohere.com/v2/chat",
        "method": "POST",
        "authentication": "API key via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://api.cohere.com/v2/chat --header 'Authorization: Bearer ${COHERE_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"command-a-plus-05-2026\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://docs.cohere.com/reference/chat",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["TRIAL KEY", "NON-COMMERCIAL"],
    "freeSummary": "Trial API key: free, rate-limited, not permitted for production or commercial use",
    "validitySummary": "Ongoing trial keys; rate limits apply",
    "accessSummary": "Cohere personal account",
    "checkedSummary": "Today / official Cohere pricing page",
    "title": "Cohere · free trial API key",
    "why": "Cohere's official pricing page FAQ states: 'API calls made from a Trial API key are free. However, trial keys are rate limited and are not permitted to be used for production or commercial purposes.' Every new account begins with trial access.",
    "mechanism": "Free rate-limited Trial API key for evaluation",
    "validity": "Ongoing while the trial program exists; non-production only",
    "access": "Cohere personal account; production keys require an application",
    "command": "curl https://api.cohere.com/v2/chat --header 'Authorization: Bearer ${COHERE_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"command-a-plus-05-2026\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://dashboard.cohere.com/",
    "registerLabel": "Cohere dashboard",
    "links": [
        ["Official pricing FAQ (trial keys)", "https://cohere.com/pricing"],
        ["Chat API reference", "https://docs.cohere.com/reference/chat"],
    ],
    "originCountry": "International",
    "availability": "Global; availability may vary by region",
    "freeMechanism": "trial",
    "pricingModel": "free_rate_limited",
    "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
    "quota": "Rate limited (exact trial RPM/RPM caps published in the Cohere docs rate limits page)",
    "renewal": "Trial keys remain usable within rate limits; not time-boxed to a calendar period on the pricing page",
    "commercialUse": "Not permitted with a Trial API key",
    "sourceUrls": [
        "https://cohere.com/pricing",
        "https://docs.cohere.com/reference/chat",
    ],
    "evidence": "Official pricing FAQ: 'API calls made from a Trial API key are free. However, trial keys are rate limited and are not permitted to be used for production or commercial purposes.'",
    "confidence": "high",
    "notes": "International option included in the China-first global directory.",
})
NEW_OFFERS.append(o)

# 34 Hugging Face Inference Providers
o = offer_common()
o.update({
    "id": "hf-inference-free",
    "order": 34,
    "name": "Hugging Face Inference Providers free tier",
    "providerMark": "HF",
    "provider": "Hugging Face",
    "providerMeta": "Hugging Face · International",
    "model": "Open models served via multi-provider inference (chat, embeddings, image and more)",
    "modelMeta": "Hosted via partner providers",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Call open models through the Inference Providers router with the free tier included in every account",
        "prerequisites": ["Hugging Face account", "Hugging Face access token"],
        "steps": [
            "Create a Hugging Face account and generate an access token",
            "Send an OpenAI-compatible chat completion request to the router endpoint within the free monthly credits",
        ],
        "endpoint": "https://router.huggingface.co/v1/chat/completions",
        "method": "POST",
        "authentication": "Hugging Face token via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://router.huggingface.co/v1/chat/completions --header 'Authorization: Bearer ${HF_TOKEN}' --header 'Content-Type: application/json' --data '{\"model\":\"openai/gpt-oss-120b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://huggingface.co/docs/inference-providers/index",
    },
    "kicker": "GLOBAL FREE MODELS",
    "badges": ["FREE TIER", "MONTHLY CREDITS"],
    "freeSummary": "Generous free tier included; additional credits for PRO users and organizations",
    "validitySummary": "Monthly included credits; unused quota does not roll over",
    "accessSummary": "Hugging Face account",
    "checkedSummary": "Today / official Inference Providers docs",
    "title": "Hugging Face · Inference Providers free tier",
    "why": "The official Inference Providers documentation states: 'Get Started for Free: Inference Providers includes a generous free tier, with additional credits for PRO users and Team & Enterprise organizations.'",
    "mechanism": "Platform free tier with included credits on a single OpenAI-compatible router API across providers",
    "validity": "Ongoing free tier; credit amounts can change",
    "access": "Hugging Face account and access token",
    "command": "curl https://router.huggingface.co/v1/chat/completions --header 'Authorization: Bearer ${HF_TOKEN}' --header 'Content-Type: application/json' --data '{\"model\":\"openai/gpt-oss-120b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://huggingface.co/",
    "registerLabel": "Hugging Face",
    "links": [
        ["Official Inference Providers docs", "https://huggingface.co/docs/inference-providers/index"],
        ["Pricing and billing", "https://huggingface.co/docs/inference-providers/pricing"],
    ],
    "originCountry": "International",
    "availability": "Global; provider routing may vary by region",
    "freeMechanism": "monthly_quota",
    "pricingModel": "monthly_quota",
    "freePolicy": {"type": "monthly_credits", "amount": None, "unit": "credits", "period": "month"},
    "quota": "Monthly free credits (amount published on the official pricing page); PRO adds more credits",
    "renewal": "Credits refresh monthly while the program runs",
    "sourceUrls": [
        "https://huggingface.co/docs/inference-providers/index",
        "https://huggingface.co/docs/inference-providers/pricing",
    ],
    "evidence": "Official docs: 'Get Started for Free: Inference Providers includes a generous free tier, with additional credits for PRO users and Team & Enterprise organizations.'",
    "confidence": "medium",
    "confidenceReason": "Free tier confirmed officially, but the exact monthly credit amount was not captured on the fetched page; verify the number on the pricing page before relying on it.",
    "notes": "International option included in the China-first global directory.",
})
NEW_OFFERS.append(o)

# 35 SiliconFlow free listed models (China)
o = offer_common()
o.update({
    "id": "siliconflow-free-models",
    "order": 35,
    "name": "SiliconFlow free listed models",
    "providerMark": "SF",
    "provider": "SiliconFlow",
    "providerMeta": "SiliconFlow 硅基流动 · China",
    "model": "PaddleOCR-VL-1.5 · Hunyuan-MT-7B · BAAI bge-m3 / bge-reranker-v2-m3 / bge-large · Kwai-Kolors (¥0 listed)",
    "modelMeta": "¥0-priced models on the official price list",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Call the models listed at ¥0 on the official price list via the SiliconFlow API",
        "prerequisites": ["SiliconFlow account", "API key from the SiliconFlow cloud console"],
        "steps": [
            "Register on the SiliconFlow cloud platform and create an API key",
            "Call the OpenAI-compatible chat or embeddings endpoint with a model ID listed at ¥0 on the official price page",
        ],
        "endpoint": "https://api.siliconflow.cn/v1/chat/completions",
        "method": "POST",
        "authentication": "API key via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://api.siliconflow.cn/v1/chat/completions --header 'Authorization: Bearer ${SILICONFLOW_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"tencent/Hunyuan-MT-7B\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://docs.siliconflow.cn/cn/userguide/quickstart",
    },
    "kicker": "FREE MODELS",
    "badges": ["¥0 MODELS", "CHINA"],
    "freeSummary": "Selected models listed at ¥0 (free) on the official price list, plus paid models",
    "validitySummary": "Free listing can change; recheck the price page",
    "accessSummary": "SiliconFlow account; China registration",
    "checkedSummary": "Today / official SiliconFlow price page",
    "title": "SiliconFlow · ¥0 listed models",
    "why": "The official SiliconFlow price page lists multiple models at 免费/¥0 — including PaddleOCR-VL-1.5, Hunyuan-MT-7B, BAAI bge-m3, bge-reranker-v2-m3, bge-large-zh/en-v1.5 and Kwai-Kolors — alongside paid models.",
    "mechanism": "Selected models permanently listed at ¥0 on the official price list",
    "validity": "Ongoing while listed; the ¥0 list can change at any time",
    "access": "SiliconFlow account; registration via the China platform",
    "command": "curl https://api.siliconflow.cn/v1/chat/completions --header 'Authorization: Bearer ${SILICONFLOW_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"tencent/Hunyuan-MT-7B\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://cloud.siliconflow.cn/",
    "registerLabel": "SiliconFlow 云平台",
    "links": [
        ["官方价格页（¥0 模型列表）", "https://siliconflow.cn/pricing"],
        ["快速开始文档", "https://docs.siliconflow.cn/cn/userguide/quickstart"],
    ],
    "originCountry": "China",
    "availability": "China platform; API reachable globally",
    "freeMechanism": "permanent",
    "pricingModel": "permanent_free",
    "freePolicy": {"type": "permanent_free", "amount": None, "unit": None, "period": None},
    "quota": "¥0 unit price for the listed models; subject to platform fair-use and rate limits",
    "renewal": "No quota period; the ¥0 price applies per request for listed models",
    "sourceUrls": [
        "https://siliconflow.cn/pricing",
        "https://docs.siliconflow.cn/cn/userguide/quickstart",
    ],
    "evidence": "官方价格页列出 PaddleOCR-VL-1.5、Hunyuan-MT-7B、BAAI/bge-m3、bge-reranker-v2-m3、bge-large-zh-v1.5、bge-large-en-v1.5、Kwai-Kolors 价格为「免费」；官方快速开始文档给出 Base URL https://api.siliconflow.cn/v1。",
    "confidence": "high",
    "notes": "China-first entry. Embedding/reranker and OCR models at ¥0 complement paid chat models on the same platform.",
})
NEW_OFFERS.append(o)

# 36 ModelScope API-Inference (China)
o = offer_common()
o.update({
    "id": "modelscope-api-inference-free",
    "order": 36,
    "name": "ModelScope API-Inference",
    "providerMark": "MS",
    "provider": "ModelScope",
    "providerMeta": "ModelScope 魔搭社区 · Alibaba · China",
    "model": "Hosted open models (LLM · MLLM · text-to-image) marked with the API-Inference badge",
    "modelMeta": "Free OpenAI-compatible inference for registered users",
    "type": ["api", "free"],
    "usageGuide": {
        "summary": "Call open models free via ModelScope API-Inference after binding an Aliyun account",
        "prerequisites": [
            "ModelScope account",
            "ModelScope account bound to an Aliyun account that has passed real-name verification",
        ],
        "steps": [
            "Bind your ModelScope account to a real-name verified Aliyun account, then create an access token in ModelScope",
            "Send OpenAI-compatible requests to the API-Inference endpoint within the dynamic rate limits",
        ],
        "endpoint": "https://api-inference.modelscope.cn/v1/chat/completions",
        "method": "POST",
        "authentication": "ModelScope access token via Authorization: Bearer header",
        "examples": {
            "curl": "curl https://api-inference.modelscope.cn/v1/chat/completions --header 'Authorization: Bearer ${MODELSCOPE_TOKEN}' --header 'Content-Type: application/json' --data '{\"model\":\"Qwen/Qwen3.5-35B-A3B\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
        },
        "docsUrl": "https://modelscope.cn/docs/model-service/API-Inference/intro",
    },
    "kicker": "FREE API INFERENCE",
    "badges": ["FREE FOR REGISTERED USERS", "ALIYUN BINDING"],
    "freeSummary": "API-Inference is free for registered users; dynamic rate limits and 魔粒 (MoLi) deduction apply",
    "validitySummary": "Ongoing free service; model list iterates as new open models release",
    "accessSummary": "ModelScope account + Aliyun binding + real-name verification",
    "checkedSummary": "Today / official ModelScope docs (intro + limits)",
    "title": "ModelScope · API-Inference free calls",
    "why": "Official docs state API-Inference is provided free to ModelScope registered users ('API-Inference面向ModelScope注册用户免费提供'), backed by Aliyun compute; usage requires Aliyun account binding with real-name verification, applies dynamic per-model rate limits, and supports 魔粒 deduction tiers (0.5 / 1 / 2 per call by model size).",
    "mechanism": "Free OpenAI-compatible inference endpoint for registered users, funded by Aliyun, with dynamic rate limits and 魔粒 points deduction",
    "validity": "Ongoing service; individual models may be delisted as newer models release",
    "access": "Requires ModelScope account bound to a real-name verified Aliyun (China) account; non-commercial use",
    "command": "curl https://api-inference.modelscope.cn/v1/chat/completions --header 'Authorization: Bearer ${MODELSCOPE_TOKEN}' --header 'Content-Type: application/json' --data '{\"model\":\"Qwen/Qwen3.5-35B-A3B\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'",
    "register": "https://modelscope.cn/my/myaccesstoken",
    "registerLabel": "ModelScope 访问令牌",
    "links": [
        ["API推理介绍（官方文档）", "https://modelscope.cn/docs/model-service/API-Inference/intro"],
        ["API-Inference 使用限制（官方文档）", "https://modelscope.cn/docs/model-service/API-Inference/limits"],
    ],
    "originCountry": "China",
    "availability": "Requires China Aliyun account with real-name verification",
    "freeMechanism": "permanent",
    "pricingModel": "free_rate_limited",
    "freePolicy": {"type": "rate_limited", "amount": None, "unit": None, "period": None},
    "quota": "Dynamic per-model rate limits; 魔粒 deduction: 轻量模型 0.5/次 · 主流模型 1/次 · 旗舰模型 2/次",
    "renewal": "No fixed quota window; limits adjust dynamically with platform load",
    "phoneRequired": "yes",
    "commercialUse": "Non-commercial; docs direct commercial workloads to paid APIs",
    "sourceUrls": [
        "https://modelscope.cn/docs/model-service/API-Inference/intro",
        "https://modelscope.cn/docs/model-service/API-Inference/limits",
    ],
    "evidence": "官方文档：「API-Inference面向ModelScope注册用户免费提供」「免费推理API由阿里云提供算力支持，要求您的ModelScope账号必须首先绑定阿里云账号…对应云账号需已通过实名认证」「魔粒扣减分为三档：轻量模型（0.5 魔粒/次），主流模型（1 魔粒/次），旗舰模型（2 魔粒/次）」。",
    "confidence": "high",
    "notes": "China-first entry. Matches the freellmapi peer lead that ModelScope free inference 'needs Aliyun cn binding'; now verified against official ModelScope docs.",
})
NEW_OFFERS.append(o)


def main():
    offers_path = Path("data/offers.json")
    providers_path = Path("data/providers.json")

    offers = json.loads(offers_path.read_text(encoding="utf-8"))
    existing_ids = {o["id"] for o in offers}
    added = [o for o in NEW_OFFERS if o["id"] not in existing_ids]
    offers.extend(added)

    errors = validate_offers(offers)
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print("-", e)
        return 1

    offers_path.write_text(json.dumps(offers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"offers.json: added {len(added)} offers, total {len(offers)}")

    providers = json.loads(providers_path.read_text(encoding="utf-8"))
    existing_pids = {p["id"] for p in providers}
    added_providers = [p for p in NEW_PROVIDERS if p["id"] not in existing_pids]
    providers.extend(added_providers)
    providers_path.write_text(json.dumps(providers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"providers.json: added {len(added_providers)} providers, total {len(providers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
