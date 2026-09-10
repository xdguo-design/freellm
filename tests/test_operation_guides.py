import json
from pathlib import Path

import pytest

from crawler.schema import validate_operation_guides
from scripts.build_model_catalog import build_provider_catalog, load_operation_guides
from scripts.build_seo_pages import build_site


def _valid_path():
    return {
        "id": "api",
        "label": "API 调用",
        "productType": "api",
        "prerequisites": ["已注册账号", "已创建 API key"],
        "steps": [
            {"title": "打开控制台", "detail": "进入官方控制台。"},
            {"title": "创建密钥", "detail": "创建并保存密钥。"},
            {
                "title": "发送请求",
                "detail": "使用环境变量中的密钥发送请求。",
                "command": "curl https://example.com/v1/models -H 'Authorization: Bearer ${API_KEY}'",
                "expected": "返回 HTTP 200。",
            },
        ],
        "endpoint": "https://example.com/v1",
        "auth": "Bearer API key",
        "example": "curl https://example.com/v1/models -H 'Authorization: Bearer ${API_KEY}'",
        "validation": "GET /v1/models 返回 HTTP 200。",
        "sourceUrls": ["https://example.com/docs"],
    }


def test_operation_guides_require_steps_sources_and_validation():
    guide = {"providerId": "example", "paths": [_valid_path()]}
    assert validate_operation_guides(guide) == []

    broken = json.loads(json.dumps(guide))
    broken["paths"][0]["steps"] = []
    broken["paths"][0]["sourceUrls"] = ["http://example.com/docs"]
    broken["paths"][0]["validation"] = ""
    errors = validate_operation_guides(broken)
    assert any("steps" in error for error in errors)
    assert any("HTTPS" in error for error in errors)
    assert any("validation" in error for error in errors)


def test_api_operation_guides_reject_placeholder_commands_and_missing_contract():
    guide = {"providerId": "example", "paths": [_valid_path()]}
    guide["paths"][0]["example"] = "curl https://example.com -H 'Authorization: Bearer YOUR_API_KEY'"
    guide["paths"][0].pop("endpoint")
    guide["paths"][0].pop("auth")
    errors = validate_operation_guides(guide)
    assert any("endpoint" in error for error in errors)
    assert any("auth" in error for error in errors)
    assert any("placeholder" in error for error in errors)


def test_operation_coverage_includes_named_platforms():
    operation_dir = Path(__file__).parents[1] / "data" / "operations"
    ids = {json.loads(path.read_text(encoding="utf-8"))["providerId"] for path in operation_dir.glob("*.json")}
    assert {
        "ollama-cloud",
        "openrouter",
        "groq",
        "nvidia-nim",
        "modelscope",
        "siliconflow",
        "opencode",
        "freebuff",
        "longcat",
    } <= ids


def test_provider_catalog_builder_keeps_operation_only_entries():
    root = Path(__file__).parents[1]
    guides = load_operation_guides(root / "data" / "operations")
    providers = build_provider_catalog([], "2026-09-09", guides)
    ids = {provider["id"] for provider in providers}
    assert {"freebuff", "longcat"} <= ids


def test_build_site_renders_operation_guides_on_offer_page(tmp_path):
    root = Path(__file__).parents[1]
    build_site(
        data_path=root / "data" / "offers.json",
        output_root=tmp_path,
        site_url="https://freellm.top",
    )
    html = (tmp_path / "offers" / "longcat-2-0" / "index.html").read_text(encoding="utf-8")
    assert 'id="operation-guides"' in html
    assert "操作步骤" in html
    assert "验证动作" in html
    assert "复制命令" in html
    assert "https://longcat.ai/platform/" in html


def test_operation_only_providers_are_discoverable(tmp_path):
    root = Path(__file__).parents[1]
    build_site(root / "data" / "offers.json", tmp_path, site_url="https://freellm.top")
    providers_page = (tmp_path / "providers" / "index.html").read_text(encoding="utf-8")
    freebuff_page = (tmp_path / "providers" / "freebuff" / "index.html").read_text(encoding="utf-8")
    longcat_page = (tmp_path / "providers" / "longcat" / "index.html").read_text(encoding="utf-8")
    assert '/providers/freebuff/' in providers_page
    assert '/providers/longcat/' in providers_page
    assert 'id="operation-guides"' in freebuff_page
    assert 'id="operation-guides"' in longcat_page
    assert 'No catalog model records are synced yet' in freebuff_page
    assert 'Operation guide' in freebuff_page


def test_promoted_offers_have_reproducible_operation_paths():
    root = Path(__file__).parents[1]
    offers = json.loads((root / "data" / "offers.json").read_text(encoding="utf-8"))
    guides = load_operation_guides(root / "data" / "operations")
    required = {
        "codebuddy", "qoder", "trae", "comate", "doubao", "glm",
        "aliyun-qwen-free-quota", "cursor-hobby",
    }
    linked = {
        offer_id
        for guide in guides
        for offer_id in guide.get("offerIds") or []
    }
    assert required <= linked

    for guide in guides:
        if not required.intersection(guide.get("offerIds") or []):
            continue
        for path in guide["paths"]:
            assert path.get("validation", "").strip()
            assert path.get("limits", "").strip()
            assert path.get("commonIssues")
            assert path.get("sourceUrls")


def test_operation_markup_renders_limits_and_common_issues(tmp_path):
    root = Path(__file__).parents[1]
    build_site(root / "data" / "offers.json", tmp_path, site_url="https://freellm.top")
    page = (tmp_path / "offers" / "codebuddy" / "index.html").read_text(encoding="utf-8")
    assert "额度与限制" in page
    assert "常见问题" in page
