import json
from pathlib import Path

from crawler.schema import validate_models
from scripts.build_model_catalog import build_model_catalog, build_provider_catalog


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


def test_catalog_builder_normalizes_directory_rows_for_querying():
    rows = [{
        "directoryProvider": "Example Provider",
        "directoryProviderSlug": "example-provider",
        "model": "Example Model",
        "modelId": "example/model",
        "modelSlug": "example-model",
        "directoryUrl": "https://freellm.net/models/example-provider/example-model",
        "directoryFree": True,
        "directoryNoCard": True,
        "directoryVerified": True,
        "score": "92",
        "context": "128K",
        "maxOutput": "8K",
        "modality": "text, reasoning",
        "rateLimit": "10 RPM",
        "released": "2026-09-01",
        "usageActivity": "—",
        "status": "Online",
        "tierType": "permanent",
    }]
    models = build_model_catalog(rows, "2026-09-09")
    assert models[0]["id"] == "example-provider/example-model"
    assert models[0]["score"] == 92
    assert models[0]["modality"] == ["text", "reasoning"]
    assert validate_models(models) == []


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
