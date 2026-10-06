import json
from pathlib import Path
from unittest.mock import patch

from crawler.schema import validate_models
from scripts.build_model_catalog import build_model_catalog, build_provider_catalog, build_source_health_report
from scripts.sync_model_catalog import sync_model_catalog
from scripts.build_model_catalog import main as build_model_catalog_main
from crawler.official_model_discovery import discover_official_model_sources


def valid_model():
    return {
        "id": "example-provider/example-model",
        "providerId": "example-provider",
        "provider": "Example Provider",
        "model": "Example Model",
        "score": 92,
        "context": "128K",
        "maxOutput": "8K",
        "modality": ["text", "reasoning"],
        "rateLimit": "10 RPM",
        "released": "2026-09-01",
        "usageActivity": "—",
        "status": "online",
        "sourceUrl": "https://example.com/models/example-model",
        "sourceKind": "third_party_directory",
        "lastSeenAt": "2026-09-09",
    }


def test_model_catalog_file_has_a_valid_model_contract():
    assert validate_models(Path("data/models.json")) == []


def test_model_catalog_keeps_provider_and_model_level_fields():
    errors = validate_models([valid_model()])
    assert errors == []


def test_model_catalog_rejects_duplicate_ids_and_invalid_scores():
    model = valid_model()
    errors = validate_models([model, model | {"score": 101}])
    assert "duplicate id: example-provider/example-model" in errors
    assert "models[1]: score must be an integer from 0 to 100 or null" in errors


def test_catalog_builder_normalizes_discovery_rows_for_querying():
    # Parser rows arrive already normalized; the builder assigns ids from
    # providerId+modelSlug, stamps lastSeenAt, and drops the derived slug.
    rows = [{
        "providerId": "example-provider",
        "provider": "Example Provider",
        "model": "Example Model",
        "modelSlug": "example-model",
        "sourceUrl": "https://example.com/models/example-model",
        "score": 92,
        "context": "128K",
        "maxOutput": "8K",
        "modality": ["text", "reasoning"],
        "rateLimit": "10 RPM",
        "released": "2026-09-01",
        "usageActivity": "—",
        "status": "online",
        "sourceKind": "official",
    }]
    models = build_model_catalog(rows, "2026-09-09")
    assert models[0]["id"] == "example-provider/example-model"
    assert models[0]["lastSeenAt"] == "2026-09-09"
    assert "modelSlug" not in models[0]
    assert validate_models(models) == []


def test_catalog_builder_fails_when_any_source_failed(tmp_path):
    rows = [{
        "id": "example-provider/example-model",
        "providerId": "example-provider",
        "provider": "Example Provider",
        "model": "Example Model",
        "context": "",
        "maxOutput": "",
        "modality": ["text"],
        "rateLimit": "",
        "released": "",
        "usageActivity": "",
        "status": "online",
        "sourceUrl": "https://example.com/models/example-model",
        "sourceKind": "official",
    }]
    with patch("scripts.build_model_catalog.discover_rows", return_value={
        "models": rows,
        "failures": [{"providerId": "failed-provider", "url": "https://example.com/models", "status": "failed", "reason": "timeout"}],
        "sourceResults": [
            {"id": "working-source", "url": "https://example.com/working", "status": "success", "rowCount": 1, "truncated": False},
            {"id": "failed-provider", "url": "https://example.com/models", "status": "failed", "reason": "timeout", "rowCount": 0, "truncated": False},
        ],
    }):
        exit_code = build_model_catalog_main([
            "--models-out", str(tmp_path / "models.json"),
            "--providers-out", str(tmp_path / "providers.json"),
            "--health-out", str(tmp_path / "source-health.json"),
            "--date", "2026-10-06",
        ])

    assert exit_code != 0
    health = json.loads((tmp_path / "source-health.json").read_text(encoding="utf-8"))
    assert health["status"] == "partial"
    assert health["complete"] is False
    assert health["enabledSourceIds"] == ["failed-provider", "working-source"]


def test_source_health_report_is_complete_only_when_every_enabled_source_is_complete():
    report = build_source_health_report("2026-10-06", {
        "models": [],
        "sourceResults": [
            {"id": "source-a", "url": "https://a.example/models", "status": "success", "rowCount": 0, "truncated": False},
            {"id": "source-b", "url": "https://b.example/models", "status": "success", "rowCount": 2, "truncated": False},
        ],
        "failures": [],
    })
    assert report["status"] == "complete"
    assert report["complete"] is True
    assert report["observationKind"] == "official_model_source_scan"
    assert report["enabledSourceIds"] == ["source-a", "source-b"]
    assert report["sources"][0]["rowCount"] == 0


def test_source_health_report_preserves_partial_failures_and_truncation():
    report = build_source_health_report("2026-10-06", {
        "models": [],
        "sourceResults": [
            {"id": "source-a", "url": "https://a.example/models", "status": "success", "rowCount": 1, "truncated": False},
            {"id": "source-b", "url": "https://b.example/models", "status": "failed", "reason": "timeout", "rowCount": 0, "truncated": False},
            {"id": "source-c", "url": "https://c.example/models", "status": "success", "rowCount": 10, "truncated": True},
        ],
        "failures": [{"providerId": "source-b", "url": "https://b.example/models", "status": "failed", "reason": "timeout"}],
    })
    assert report["status"] == "partial"
    assert report["complete"] is False
    assert report["failures"]
    assert report["sources"][2]["truncated"] is True


def test_source_health_report_fails_closed_for_malformed_source_results_or_failures():
    for source_results, failures in [
        ([{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 0}], []),
        (["not-an-object"], []),
        ([{"id": "a", "url": "https://a.example/models", "status": "failed", "rowCount": 0, "truncated": False, "reason": "timeout"}], []),
        ([{"id": "a", "url": "https://a.example/models", "status": "success", "rowCount": 0, "truncated": False}], [{"providerId": "a", "url": "https://wrong.example", "status": "failed", "reason": "timeout"}]),
        ([{"id": "a", "url": "https://a.example/models", "status": "failed", "rowCount": 0, "truncated": False, "reason": "timeout"}], [
            {"providerId": "a", "url": "https://a.example/models", "status": "failed", "reason": "timeout"},
            {"providerId": "a", "url": "https://a.example/models", "status": "failed", "reason": "timeout"},
        ]),
        ([{"id": "a", "url": "https://a.example/models", "status": "failed", "rowCount": 0, "truncated": False, "reason": "timeout"}], [
            {"providerId": "a", "url": "https://a.example/models", "reason": "timeout"},
        ]),
    ]:
        report = build_source_health_report("2026-10-06", {"sourceResults": source_results, "failures": failures})
        assert report["complete"] is False
        assert report["status"] != "complete"


def test_source_discovery_reports_zero_row_success_separately_from_failure():
    sources = [
        {"id": "empty", "providerId": "empty", "provider": "Empty", "kind": "official", "type": "openai_models",
         "url": "https://empty.example/v1/models", "allowedDomains": ["empty.example"],
         "modelPageTemplate": "https://empty.example/models/{id}", "enabled": True},
        {"id": "failed", "providerId": "failed", "provider": "Failed", "kind": "official", "type": "openai_models",
         "url": "https://failed.example/v1/models", "allowedDomains": ["failed.example"],
         "modelPageTemplate": "https://failed.example/models/{id}", "enabled": True},
        {"id": "malformed", "providerId": "malformed", "provider": "Malformed", "kind": "official", "type": "openai_models",
         "url": "https://malformed.example/v1/models", "allowedDomains": ["malformed.example"],
         "modelPageTemplate": "https://malformed.example/models/{id}", "enabled": True},
    ]
    def fetcher(url, *_):
        if "empty.example" in url:
            return {"status": "ok", "content": '{"data": []}'}
        if "malformed.example" in url:
            return {"status": "ok", "content": '{"error": "maintenance"}'}
        return {"status": "failed", "reason": "timeout"}

    result = discover_official_model_sources(sources, fetcher=fetcher)
    assert result["sourceResults"] == [
        {"id": "empty", "url": "https://empty.example/v1/models", "status": "success", "rowCount": 0, "truncated": False},
        {"id": "failed", "url": "https://failed.example/v1/models", "status": "failed", "reason": "timeout", "rowCount": 0, "truncated": False},
        {"id": "malformed", "url": "https://malformed.example/v1/models", "status": "failed", "reason": "unexpected response schema for openai_models", "rowCount": 0, "truncated": False},
    ]


def test_source_discovery_rejects_partial_catalogue_with_invalid_rows():
    source = {"id": "mixed", "providerId": "mixed", "provider": "Mixed", "kind": "official", "type": "openai_models",
        "url": "https://mixed.example/v1/models", "allowedDomains": ["mixed.example"],
        "modelPageTemplate": "https://mixed.example/models/{id}", "enabled": True}
    result = discover_official_model_sources([source], fetcher=lambda *_: {
        "status": "ok", "content": '{"data": [{"id":"valid-model"}, {"name":"missing-id"}]}'
    })
    assert result["models"] == []
    assert result["failures"][0]["providerId"] == "mixed"
    assert result["sourceResults"][0]["status"] == "failed"
    assert result["sourceResults"][0]["reason"] == "one or more model rows are missing a valid identifier"


def test_ollama_discovery_falls_back_to_trimmed_model_name_and_counts_the_row():
    source = {"id": "ollama", "providerId": "ollama", "provider": "Ollama", "kind": "official", "type": "ollama_tags",
        "url": "https://ollama.example/api/tags", "allowedDomains": ["ollama.example"],
        "modelPageTemplate": "https://ollama.example/library/{name}", "enabled": True}
    result = discover_official_model_sources([source], fetcher=lambda *_: {
        "status": "ok", "content": '{"models": [{"name":" ", "model":"llama3"}]}'
    })
    assert result["failures"] == []
    assert result["models"][0]["model"] == "llama3"
    assert result["sourceResults"][0]["status"] == "success"
    assert result["sourceResults"][0]["rowCount"] == 1


def test_provider_catalog_groups_models_without_collapsing_model_rows():
    rows = [valid_model(), valid_model() | {"id": "example-provider/other-model", "model": "Other Model"}]
    providers = build_provider_catalog(rows, "2026-09-09")
    assert providers == [{
        "id": "example-provider",
        "name": "Example Provider",
        "modelCount": 2,
        "modelIds": ["example-provider/example-model", "example-provider/other-model"],
        "sourceKind": "catalog",
        "lastSeenAt": "2026-09-09",
    }]


def test_sync_is_idempotent_for_same_day_new_records():
    discovered = [{
        "id": "provider/new-model",
        "providerId": "provider",
        "model": "New Model",
        "sourceUrl": "https://freellm.net/models/provider/new-model",
    }]
    first = sync_model_catalog(discovered, [], "2026-09-12")
    second = sync_model_catalog(discovered, first, "2026-09-12")
    assert first[0]["freshnessStatus"] == "new"
    assert second[0]["freshnessStatus"] == "new"


# Agnes AI publishes no machine-readable model catalogue: its official docs are
# prose pages whose shapes differ page by page, so the rows below are
# hand-verified against the mainland-China docs and pricing page and live in the
# curated overlay. These tests pin the verified facts so a later edit cannot
# silently drift them.
AGNES_MODELS = {
    # id: (canonical model string, context, maxOutput, modality)
    "agnes-ai/agnes-2-5-flash": ("agnes-2.5-flash", "512000", "65536", ["text", "image", "reasoning"]),
    "agnes-ai/agnes-2-5-pro": ("agnes-2.5-pro", "1000000", "65536", ["text", "image", "reasoning"]),
    "agnes-ai/agnes-2-5-pro-beta": ("agnes-2.5-pro-beta", "1000000", "65536", ["text", "image", "reasoning"]),
    "agnes-ai/agnes-3-0-flash": ("agnes-3.0-flash", "512000", "65536", ["text", "image"]),
    "agnes-ai/agnes-image-2-0-flash": ("agnes-image-2.0-flash", "", "", ["text", "image"]),
    "agnes-ai/agnes-image-2-1-flash": ("agnes-image-2.1-flash", "", "", ["text", "image"]),
    "agnes-ai/agnes-image-2-5-flash": ("agnes-image-2.5-flash", "", "", ["text", "image"]),
    "agnes-ai/agnes-video-v2-0": ("agnes-video-v2.0", "", "", ["text", "image", "video"]),
    "agnes-ai/agnes-video-2-5": ("agnes-video-2.5", "", "", ["text", "image", "video"]),
    "agnes-ai/agnes-video-2-5-flash": ("agnes-video-2.5-flash", "", "", ["text", "image", "video"]),
}


def _agnes_rows(path: str) -> dict[str, dict]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return {row["id"]: row for row in rows if row.get("providerId") == "agnes-ai"}


def test_curated_overlay_carries_every_official_agnes_model():
    rows = _agnes_rows("data/models-curated.json")
    assert set(rows) == set(AGNES_MODELS)
    for model_id, (canonical, context, max_output, modality) in AGNES_MODELS.items():
        row = rows[model_id]
        assert row["canonicalModelId"] == canonical
        assert row["context"] == context
        assert row["maxOutput"] == max_output
        assert row["modality"] == modality
        assert row["sourceKind"] == "official"
        assert row["status"] == "online"
        assert row["lastVerifiedAt"] == "2026-09-19"
        # The mainland route is the primary entry point for this provider.
        assert row["accessRegion"] == "domestic"
        assert row["accessEndpoint"] == "https://api.agnes-ai.cn/v1"
        assert row["sourceUrl"].startswith("https://agnes-ai.cn/zh-Hans/docs/")
        assert validate_models([row]) == []


def test_published_catalog_contains_the_verified_agnes_rows():
    published = {row["id"]: row for row in json.loads(Path("data/models.json").read_text(encoding="utf-8"))}
    for model_id, (canonical, _, _, _) in AGNES_MODELS.items():
        assert model_id in published, f"{model_id} never reached the published catalog"
        assert published[model_id]["providerId"] == "agnes-ai"
        assert published[model_id]["canonicalModelId"] == canonical
        assert published[model_id]["sourceKind"] == "official"
        assert published[model_id]["freshnessStatus"] in {"new", "current"}


def test_catalog_excludes_agnes_models_the_cn_docs_no_longer_publish():
    # The mainland pricing page lists neither, and the 2.5 Flash page states
    # agnes-2.0-flash is deprecated. Only the global catalogue ever carried them,
    # so they must not be asserted as current mainland models.
    published = {row["id"] for row in json.loads(Path("data/models.json").read_text(encoding="utf-8"))}
    assert "agnes-ai/agnes-1-5-flash" not in published
    assert "agnes-ai/agnes-2-0-flash" not in published


def test_agnes_free_models_match_the_official_cn_pricing_page():
    # Official CN pricing page, 2026-09-19: these are billed at ¥0 today. The
    # paid siblings stay in the catalog (it is a model directory, not a free-only
    # list) but must never be presented as free.
    free = {"agnes-2.5-flash", "agnes-3.0-flash", "agnes-image-2.0-flash",
            "agnes-image-2.1-flash", "agnes-image-2.5-flash", "agnes-video-v2.0"}
    promo = {"agnes-video-2.5-flash"}
    paid = {"agnes-2.5-pro", "agnes-2.5-pro-beta", "agnes-video-2.5"}
    rows = _agnes_rows("data/models-curated.json")
    notes = {row["canonicalModelId"]: row.get("manualNote", "") for row in rows.values()}
    assert set(notes) == free | promo | paid
    for model in free:
        assert "¥0" in notes[model], model
    for model in promo:
        assert "限时免费" in notes[model], model
    for model in paid:
        assert "付费" in notes[model], model
