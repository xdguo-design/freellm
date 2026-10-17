import json
from pathlib import Path

import pytest

from scripts.sync_model_catalog import sync_model_catalog
from scripts.build_seo_pages import _model_catalog_row


def _record(provider_id: str, model_id: str, source_url: str, **extra):
    record = {
        "id": f"{provider_id}/{model_id}",
        "providerId": provider_id,
        "modelId": model_id,
        "provider": provider_id.title(),
        "model": model_id,
        "sourceUrl": source_url,
        "sourceKind": "third_party_directory",
        "status": "online",
    }
    record.update(extra)
    return record


def test_sync_marks_new_current_and_missing_models():
    previous = [
        _record("alpha", "kept", "https://directory.example/kept", lastSeenAt="2026-09-08"),
        _record("alpha", "removed", "https://directory.example/removed", lastSeenAt="2026-09-08"),
    ]
    discovered = [
        _record("alpha", "kept", "https://directory.example/kept"),
        _record("alpha", "new", "https://directory.example/new"),
    ]

    synced = sync_model_catalog(discovered, previous, "2026-09-09")
    by_id = {item["id"]: item for item in synced}

    assert by_id["alpha/kept"]["freshnessStatus"] == "current"
    assert by_id["alpha/new"]["freshnessStatus"] == "new"
    assert by_id["alpha/removed"]["freshnessStatus"] == "stale"
    assert by_id["alpha/removed"]["lastSeenAt"] == "2026-09-08"


def test_sync_preserves_manual_verification_fields_when_directory_changes():
    previous = [_record(
        "alpha",
        "kept",
        "https://directory.example/kept",
        score=91,
        verificationStatus="official_verified",
        lastVerifiedAt="2026-09-08",
        manualNote="人工核验过 API 文档",
    )]
    discovered = [_record("alpha", "kept", "https://directory.example/kept", score=88, context="128K")]

    synced = sync_model_catalog(discovered, previous, "2026-09-09")
    item = synced[0]

    assert item["score"] == 88
    assert item["context"] == "128K"
    assert item["verificationStatus"] == "official_verified"
    assert item["lastVerifiedAt"] == "2026-09-08"
    assert item["manualNote"] == "人工核验过 API 文档"


def test_sync_rejects_invalid_date():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        sync_model_catalog([], [], "yesterday")


def test_sync_cli_contract_files_are_documented():
    script = Path(__file__).parents[1] / "scripts" / "sync_model_catalog.py"
    assert script.is_file()
    assert "--input" in script.read_text(encoding="utf-8")
    assert "--output" in script.read_text(encoding="utf-8")
    assert "--as-of" in script.read_text(encoding="utf-8")


def test_model_directory_exposes_catalog_freshness_status():
    row = _model_catalog_row(_record(
        "alpha",
        "removed",
        "https://directory.example/removed",
        freshnessStatus="stale",
    ))
    assert "Stale" in row
    assert "freshness-stale" in row


def test_sync_collapses_moved_directory_url_for_same_model_id():
    # 2026-10-10: ollama.com moved library URLs to tagged paths; the same model id
    # must not survive twice (once stale, once new) or SEO page builds fail.
    previous = [_record("ollama", "m-0813", "https://directory.example/m", lastSeenAt="2026-09-19", score=80)]
    discovered = [_record("ollama", "m-0813", "https://directory.example/m:0813")]

    synced = sync_model_catalog(discovered, previous, "2026-10-10")

    assert [item["id"] for item in synced] == ["ollama/m-0813"]
    assert synced[0]["freshnessStatus"] == "current"
    assert synced[0]["sourceUrl"] == "https://directory.example/m:0813"
