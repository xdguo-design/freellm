"""Copyable curl examples must actually expand the API-key variable.

Bash leaves ``$VAR`` / ``${VAR}`` untouched inside single quotes, so
``-H 'Authorization: Bearer ${KEY}'`` sends a literal string and gets a 401.
These tests cover the quoting helper, the source data, the page templates and
every generated HTML page.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pytest

from scripts.shell_examples import (
    curl_env_vars,
    fix_curl_quoting,
    single_quoted_curl_vars,
    with_env_exports,
)
from scripts import fix_curl_quoting_data

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIRS = ["offers", "providers", "guides", "en", "category", "models", "design", "evaluations", "logs"]
BLOCK_RE = re.compile(r"<(pre|code)\b[^>]*>(.*?)</\1>", re.S)


def _code_blocks(text: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", match.group(2))) for match in BLOCK_RE.finditer(text)]


def _generated_pages() -> list[Path]:
    pages: list[Path] = []
    for name in GENERATED_DIRS:
        base = ROOT / name
        if base.exists():
            pages.extend(sorted(base.rglob("*.html")))
    return pages


# --- helper ---------------------------------------------------------------

def test_header_variable_moves_to_double_quotes():
    cmd = "curl https://api.groq.com/openai/v1/chat/completions --header 'Authorization: Bearer ${GROQ_API_KEY}' --header 'Content-Type: application/json' --data '{\"model\":\"openai/gpt-oss-20b\"}'"
    fixed = fix_curl_quoting(cmd)
    assert '--header "Authorization: Bearer $GROQ_API_KEY"' in fixed
    # JSON body and static headers keep their single quotes.
    assert "--header 'Content-Type: application/json'" in fixed
    assert "--data '{\"model\":\"openai/gpt-oss-20b\"}'" in fixed
    assert single_quoted_curl_vars(fixed) == []
    assert fix_curl_quoting(fixed) == fixed  # idempotent


def test_non_header_vars_and_continuations():
    cmd = "curl 'https://x.test/v1?key=${GEMINI_API_KEY}' \\\n  -H 'x-goog-api-key: ${GEMINI_API_KEY}'"
    fixed = fix_curl_quoting(cmd)
    assert '"https://x.test/v1?key=$GEMINI_API_KEY"' in fixed
    assert '-H "x-goog-api-key: $GEMINI_API_KEY"' in fixed
    assert curl_env_vars(fixed) == ["GEMINI_API_KEY"]


def test_non_curl_commands_keep_literal_single_quotes():
    # NVIDIA NGC's docker username is literally "$oauthtoken".
    cmd = "echo ${NGC_API_KEY} | docker login nvcr.io --username '$oauthtoken' --password-stdin"
    assert fix_curl_quoting(cmd) == cmd
    assert single_quoted_curl_vars(cmd) == []


def test_export_preamble_added_once():
    out = with_env_exports("curl https://a.test -H 'Authorization: Bearer ${A_KEY}'")
    assert out.splitlines()[0] == 'export A_KEY="你的 Key"'
    assert 'Bearer $A_KEY"' in out
    assert with_env_exports(out) == out
    assert with_env_exports("python -m pip install openai") == "python -m pip install openai"


# --- source data ----------------------------------------------------------

def test_source_data_has_no_single_quoted_curl_vars(capsys):
    assert fix_curl_quoting_data.main(["--check"]) == 0, capsys.readouterr().out


# --- templates ------------------------------------------------------------

def test_offer_template_fixes_bad_data_and_adds_export():
    from scripts.build_seo_pages import render_offer_page

    offers = json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8"))
    offer = dict(next(item for item in offers if item["id"] == "groq-free"))
    guide = dict(offer.get("usageGuide") or {})
    bad = "curl https://api.groq.com/openai/v1/chat/completions -H 'Authorization: Bearer ${GROQ_API_KEY}' --data '{}'"
    guide["examples"] = {"curl": bad}
    offer["usageGuide"] = guide
    offer["command"] = bad
    page = render_offer_page(offer, offers, "https://freellm.top")
    curl_blocks = [block for block in _code_blocks(page) if "curl " in block]
    assert curl_blocks
    for block in curl_blocks:
        assert single_quoted_curl_vars(block) == [], block
    quick = next(block for block in curl_blocks if "chat/completions" in block)
    assert 'export GROQ_API_KEY="你的 Key"' in quick
    assert '"Authorization: Bearer $GROQ_API_KEY"' in quick


def test_reference_sdk_examples_read_key_from_env_and_use_data_model():
    page = (ROOT / "guides" / "free-llm" / "index.html").read_text(encoding="utf-8")
    alt = (ROOT / "guides" / "free-openai-api-alternatives" / "index.html").read_text(encoding="utf-8")
    offers = json.loads((ROOT / "data" / "offers.json").read_text(encoding="utf-8"))
    groq = next(item for item in offers if item["id"] == "groq-free")
    groq_models = {m.get("model") for m in groq.get("freeModels") or []}
    for text in (page, alt):
        sdk = next(block for block in _code_blocks(text) if "from openai import OpenAI" in block)
        assert 'os.environ["GROQ_API_KEY"]' in sdk
        assert 'api_key="GROQ_API_KEY"' not in sdk and "YOUR_PROVIDER_KEY" not in sdk
        model = re.search(r'model="([^"]+)"', sdk).group(1)
        assert model in groq_models, model
        assert 'base_url="https://api.groq.com/openai/v1"' in sdk


# --- every generated page -------------------------------------------------

def test_generated_pages_have_no_dollar_vars_inside_single_quoted_curl_args():
    pages = _generated_pages()
    assert pages, "no generated pages found"
    offenders: dict[str, list[str]] = {}
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="ignore")
        if "curl" not in text:
            continue
        for block in _code_blocks(text):
            bad = single_quoted_curl_vars(block)
            if bad:
                offenders.setdefault(str(page.relative_to(ROOT)), []).extend(bad)
    assert not offenders, f"{len(offenders)} page(s) with $VAR in single quotes: " + json.dumps(dict(list(offenders.items())[:5]), ensure_ascii=False)


@pytest.mark.parametrize("folder", ["offers", "providers"])
def test_offer_and_provider_curl_blocks_export_their_variables(folder):
    missing: list[str] = []
    for page in sorted((ROOT / folder).rglob("index.html")):
        for block in _code_blocks(page.read_text(encoding="utf-8", errors="ignore")):
            if "curl " not in block or not block.lstrip().startswith(("curl", "export")):
                continue
            for name in curl_env_vars(block):
                if not re.search(rf"(?m)^export {name}=", block):
                    missing.append(f"{page.relative_to(ROOT)}:{name}")
    assert not missing, missing[:10]
