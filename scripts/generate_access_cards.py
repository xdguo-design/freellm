"""Generate provider registration cards and per-model access cards.

Provider cards inherit the registration requirements; model cards only record
per-model overrides. The generator is idempotent: hand-verified fields in the
output files always win over regenerated defaults, and retired model cards are
kept as tombstones even after the model leaves the upstream directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler.schema import (
    validate_model_access_file,
    validate_provider_access_file,
    validate_region_policies,
)

DIRECTORY_SOURCES = ["https://freellm.net/models/"]

# Official sign-up entry points. Providers without a confident entry point stay
# null until phase-2 verification instead of guessing a domain.
REGISTER_URLS = {
    "agnes-ai": "https://agnes-ai.com/",
    "aion-labs": "https://www.aionlabs.ai/",
    "cerebras": "https://cloud.cerebras.ai/",
    "chutes-ai": "https://chutes.ai/",
    "cline": "https://cline.bot/",
    "cloudflare-workers-ai": "https://dash.cloudflare.com/sign-up",
    "cohere": "https://dashboard.cohere.com/",
    "freebuff": "https://freebuff.ai/",
    "glhf-chat": "https://glhf.chat/",
    "google-gemini": "https://aistudio.google.com/",
    "grok-(xai)": "https://x.ai/",
    "groq": "https://console.groq.com/",
    "hugging-face": "https://huggingface.co/join",
    "kilo-code": "https://kilo.ai/",
    "llm7-io": "https://llm7.io/",
    "longcat": "https://longcat.ai/platform/",
    "mistral-ai": "https://console.mistral.ai/",
    "modelscope": "https://www.modelscope.cn/",
    "nvidia-nim": "https://build.nvidia.com/",
    "ollama-cloud": "https://ollama.com/",
    "opencode": "https://opencode.ai/",
    "openrouter": "https://openrouter.ai/",
    "ovhcloud-ai-endpoints": "https://www.ovhcloud.com/en/ai-endpoints/",
    "siliconflow": "https://cloud.siliconflow.cn/",
    "z-ai-zhipu-ai": "https://z.ai/",
}

SEARCH_METHODS = {
    "agnes-ai": "official_model_catalog",
    "aion-labs": "official_model_catalog",
    "cerebras": "official_model_catalog",
    "chutes-ai": "official_model_catalog",
    "cline": "client_model_selector",
    "cloudflare-workers-ai": "official_model_catalog",
    "cohere": "official_docs",
    "github-models": "retired_service",
    "glhf-chat": "official_model_catalog",
    "google-gemini": "official_model_catalog",
    "grok-(xai)": "official_model_catalog",
    "groq": "official_model_api",
    "hugging-face": "official_model_catalog",
    "kilo-code": "client_model_selector",
    "llm7-io": "official_model_catalog",
    "mistral-ai": "official_docs",
    "modelscope": "official_model_catalog",
    "nvidia-nim": "official_model_catalog",
    "ollama-cloud": "official_model_catalog",
    "opencode": "client_model_selector",
    "openrouter": "official_model_catalog",
    "ovhcloud-ai-endpoints": "official_model_catalog",
    "siliconflow": "official_model_catalog",
    "freebuff": "official_website_console",
    "longcat": "official_model_api",
    "z-ai-zhipu-ai": "official_model_catalog",
}

# Providers that host third-party or openly licensed models, where license
# acceptance depends on the specific model.
MODEL_DEPENDENT_LICENSE = {
    "cline", "cloudflare-workers-ai", "hugging-face", "kilo-code",
    "nvidia-nim", "ollama-cloud", "openrouter", "opencode",
    "ovhcloud-ai-endpoints", "modelscope",
}

REGION_POLICY_IDS = {
    "github-models": "github-models-retired",
    "google-gemini": "google-gemini-allowlist",
    "mistral-ai": "mistral-regional-endpoints",
    "ovhcloud-ai-endpoints": "ovhcloud-endpoints-regions",
}

GITHUB_MODELS_REPLACEMENT = "Azure AI Foundry or GitHub Copilot"
GITHUB_MODELS_SOURCE = "https://docs.github.com/en/github-models"

_ACCOUNT_HINTS = ("注册", "账号", "账户", "登录")
_KEY_HINTS = ("api key", "api token", "密钥", "token", "访问令牌")
_GPU_HINTS = ("gpu", "显存", "docker")


def _load_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _operation_hints(operations_dir: str | Path) -> dict[str, dict]:
    """Derive already-verified requirement hints from the operation guides."""
    hints: dict[str, dict] = {}
    operation_dir = Path(operations_dir)
    if not operation_dir.is_dir():
        return hints
    for path in sorted(operation_dir.glob("*.json")):
        guide = json.loads(path.read_text(encoding="utf-8"))
        provider_id = str(guide.get("providerId") or "").strip()
        if not provider_id:
            continue
        prerequisites = [
            str(prerequisite).strip().lower()
            for path_entry in guide.get("paths", [])
            for prerequisite in (path_entry.get("prerequisites") or [])
            if str(prerequisite).strip()
        ]
        sources = [url for path_entry in guide.get("paths", []) for url in (path_entry.get("sourceUrls") or [])]
        negative_account = ("无需注册", "不需要注册", "无需账号", "不需要账号", "无需登录", "不需要登录")
        negative_key = ("无需 api key", "不需要 api key", "无需apikey", "不需要apikey", "无需密钥", "不需要密钥")
        account_positive = any(any(hint in item for hint in _ACCOUNT_HINTS) for item in prerequisites)
        key_positive = any(any(hint in item for hint in _KEY_HINTS) for item in prerequisites)
        account_negative = any(any(marker in item for marker in negative_account) for item in prerequisites)
        key_negative = any(any(marker in item for marker in negative_key) for item in prerequisites)
        hints[provider_id] = {
            "accountRequired": "yes" if account_positive and not account_negative else None,
            "apiKeyRequired": "yes" if key_positive and not key_negative else None,
            "gpuRequired": "yes" if any(any(hint in item for hint in _GPU_HINTS) for item in prerequisites) else None,
            "sourceUrls": list(dict.fromkeys(sources)),
            "lastVerifiedAt": guide.get("lastVerifiedAt"),
        }
    return hints


def _provider_card(provider_id: str, hints: dict, as_of: str) -> dict:
    hint = hints.get(provider_id, {})
    curated_region = REGION_POLICY_IDS.get(provider_id, "policy-unknown-default")
    retired = provider_id == "github-models"
    card = {
        "providerId": provider_id,
        "profileId": f"{provider_id}-api",
        "registerUrl": None if retired else REGISTER_URLS.get(provider_id),
        "accountRequired": hint.get("accountRequired") or "unknown",
        "emailRequired": "unknown",
        "phoneRequired": "unknown",
        "identityRequired": "unknown",
        "cardRequired": "unknown",
        "billingRequired": "unknown",
        "apiKeyRequired": hint.get("apiKeyRequired") or "unknown",
        "licenseAcceptance": "model_dependent" if provider_id in MODEL_DEPENDENT_LICENSE else "unknown",
        "modelApproval": "unknown",
        "gpuRequired": hint.get("gpuRequired") or "unknown",
        "overageBehavior": "unknown",
        "searchMethod": SEARCH_METHODS.get(provider_id, "official_model_catalog"),
        "regionPolicyId": curated_region,
        "registrationSteps": [],
        "registrationStatus": "unavailable" if retired else "available",
        "replacement": GITHUB_MODELS_REPLACEMENT if retired else None,
        "sourceUrls": hint.get("sourceUrls") or DIRECTORY_SOURCES,
        "lastVerifiedAt": hint.get("lastVerifiedAt"),
        "verificationStatus": "partial" if hint else "unverified",
        "confidence": "high" if retired else ("medium" if hint else "low"),
        "notes": (
            "GitHub Models 已于 2026-07-30 完全退役，官方建议替代为 Azure AI Foundry 或 GitHub Copilot。"
            if retired
            else "邮箱/手机号/实名/信用卡/地区要求尚未核验，页面必须显示“待核验”。"
        ),
    }
    if retired:
        card["sourceUrls"] = [GITHUB_MODELS_SOURCE]
        card["lastVerifiedAt"] = as_of
        card["verificationStatus"] = "partial"
    return card


def _model_card(model: dict, as_of: str) -> dict:
    return {
        "modelId": model["id"],
        "providerId": model["providerId"],
        "registrationProfileId": f"{model['providerId']}-api",
        "modelSearchName": model["model"],
        "extraRequirements": [],
        "regionOverridePolicyId": None,
        "quotaOverride": None,
        "accessStatus": "needs_review",
        "replacement": None,
        "sourceUrls": [model["sourceUrl"]] if model.get("sourceUrl") else DIRECTORY_SOURCES,
        "lastVerifiedAt": None,
        "verificationStatus": "unverified",
        "notes": "",
    }


def _retired_card(model: dict, as_of: str) -> dict:
    return {
        "modelId": model["id"],
        "providerId": model["providerId"],
        "registrationProfileId": f"{model['providerId']}-api",
        "modelSearchName": model["model"],
        "extraRequirements": [],
        "regionOverridePolicyId": "github-models-retired",
        "quotaOverride": None,
        "accessStatus": "retired",
        "replacement": GITHUB_MODELS_REPLACEMENT,
        "sourceUrls": [GITHUB_MODELS_SOURCE],
        "lastVerifiedAt": as_of,
        "verificationStatus": "verified",
        "notes": "GitHub Models 已于 2026-07-30 完全退役，不能再注册或调用。",
    }


def generate(
    models: list[dict],
    catalog: list[dict],
    hints: dict[str, dict],
    policies: dict,
    existing_provider_cards: list[dict],
    existing_model_cards: list[dict],
    as_of: str,
) -> tuple[list[dict], list[dict]]:
    policy_ids = {policy["id"] for policy in policies.get("policies", [])}

    provider_cards: dict[str, dict] = {}
    for provider in catalog:
        provider_id = str(provider["id"])
        provider_cards[provider_id] = _provider_card(provider_id, hints, as_of)
    for provider_id in hints:
        provider_cards.setdefault(provider_id, _provider_card(provider_id, hints, as_of))
    for card in existing_provider_cards:
        provider_id = str(card.get("providerId") or "")
        if provider_id in provider_cards:
            provider_cards[provider_id] = card
    missing_policies = {
        card.get("regionPolicyId")
        for card in provider_cards.values()
        if card.get("regionPolicyId") not in policy_ids
    }
    if missing_policies:
        raise SystemExit(f"provider cards reference unknown region policies: {sorted(missing_policies)}")

    catalog_by_id = {str(model["id"]): model for model in models}
    model_cards: dict[str, dict] = {}
    for model in models:
        if model["providerId"] == "github-models":
            model_cards[str(model["id"])] = _retired_card(model, as_of)
        else:
            model_cards[str(model["id"])] = _model_card(model, as_of)
    for card in existing_model_cards:
        model_id = str(card.get("modelId") or "")
        if model_id not in model_cards:
            if card.get("accessStatus") == "retired":
                model_cards[model_id] = card  # tombstone survives directory removal
            else:
                print(f"warning: dropping stale access card without catalog model: {model_id}")
            continue
        merged = model_cards[model_id]
        for key, value in card.items():
            merged[key] = value
        source = catalog_by_id[model_id]
        merged["providerId"] = source["providerId"]
        merged["registrationProfileId"] = f"{source['providerId']}-api"
        merged["modelSearchName"] = source["model"]
    unknown_providers = {
        card.get("providerId") for card in model_cards.values() if card.get("providerId") not in provider_cards
    }
    if unknown_providers:
        raise SystemExit(f"model cards reference unknown providers: {sorted(p for p in unknown_providers if p)}")
    return list(provider_cards.values()), list(model_cards.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="data/models.json")
    parser.add_argument("--catalog", default="data/provider-catalog.json")
    parser.add_argument("--operations", default="data/operations")
    parser.add_argument("--policies", default="data/region-policies.json")
    parser.add_argument("--provider-access-out", default="data/provider-access.json")
    parser.add_argument("--model-access-out", default="data/model-access.json")
    parser.add_argument("--date", default=date.today().isoformat(), help="Generation date in YYYY-MM-DD format")
    args = parser.parse_args(argv)

    models = _load_json(args.models)
    catalog = _load_json(args.catalog)
    policies = _load_json(args.policies)
    hints = _operation_hints(args.operations)
    existing_provider_cards = _load_json(args.provider_access_out) if Path(args.provider_access_out).is_file() else []
    existing_model_cards = _load_json(args.model_access_out) if Path(args.model_access_out).is_file() else []

    provider_cards, model_cards = generate(
        models, catalog, hints, policies, existing_provider_cards, existing_model_cards, args.date
    )

    for label, errors in (
        ("region-policies", validate_region_policies(policies)),
        ("provider-access", validate_provider_access_file(provider_cards)),
        ("model-access", validate_model_access_file(model_cards)),
    ):
        if errors:
            raise SystemExit(f"Invalid {label} data:\n" + "\n".join(errors))

    _write_json(args.provider_access_out, provider_cards)
    _write_json(args.model_access_out, model_cards)
    retired = sum(1 for card in model_cards if card["accessStatus"] == "retired")
    print(
        f"access cards: {len(provider_cards)} providers, {len(model_cards)} models "
        f"({retired} retired, {len(model_cards) - retired} needs_review)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
