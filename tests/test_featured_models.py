from scripts.featured_models import comparable_benchmark, normalize_capabilities, normalize_region


def test_unverified_region_is_unknown():
    assert normalize_region({}) == {
        "regions": [],
        "label": "待核实",
        "filterValue": "unknown",
    }


def test_both_verified_regions_are_labeled_as_both():
    model = {
        "accessEndpoint": "https://provider.example/v1/chat/completions",
        "verifiedRegions": ["domestic", "international"],
        "regionEvidenceUrl": "https://provider.example/docs/regions",
        "regionCheckedAt": "2026-10-04",
    }
    assert normalize_region(model)["label"] == "国内外均可调用"


def test_region_evidence_does_not_transfer_to_a_different_api_route():
    model = {
        "accessEndpoint": "https://provider.example/v1/chat/completions",
        "servicePath": "https://provider.example/v2/chat/completions",
        "verifiedRegions": ["domestic", "international"],
        "regionEvidenceUrl": "https://provider.example/docs/regions",
        "regionCheckedAt": "2026-10-04",
    }
    assert normalize_region(model)["filterValue"] == "unknown"


def test_modality_alone_does_not_claim_media_generation():
    labels = normalize_capabilities({"modality": ["image", "audio", "video"]})
    assert labels == ["图片·方向待核实", "音频·方向待核实", "视频·方向待核实"]


def test_verified_output_direction_is_rendered_as_generation():
    model = {
        "verifiedCapabilities": [{
            "name": "image",
            "direction": "output",
            "evidenceUrl": "https://provider.example/docs/image-generation",
            "checkedAt": "2026-10-04",
        }]
    }
    assert normalize_capabilities(model) == ["图片生成"]


def test_explicit_speech_and_video_generation_names_are_supported():
    model = {
        "verifiedCapabilities": [
            {"name": "speech_generation", "direction": "output", "evidenceUrl": "https://provider.example/docs/tts", "checkedAt": "2026-10-04"},
            {"name": "video_generation", "direction": "output", "evidenceUrl": "https://provider.example/docs/video", "checkedAt": "2026-10-04"},
        ]
    }
    assert normalize_capabilities(model) == ["语音生成", "视频生成"]


def test_incomplete_benchmark_is_not_comparable():
    assert comparable_benchmark({"ttftMsMedian": 420, "outputTokensPerSecondMedian": 36.4}) is None


def test_benchmark_is_not_reused_for_a_different_api_route():
    model = {
        "accessEndpoint": "https://provider.example/v2/chat/completions",
        "benchmark": {
            "protocolVersion": "text-stream-v1", "taskId": "short-answer-zh-v1", "language": "zh",
            "temperature": 0, "maxOutputTokens": 256, "warmups": 1, "sampleCount": 3,
            "ttftMsMedian": 420, "outputTokensPerSecondMedian": 36.4, "testRegion": "domestic",
            "servicePath": "https://provider.example/v1/chat/completions", "testedAt": "2026-10-04",
            "rawResultRef": "data/benchmarks/example.json",
        },
    }
    assert comparable_benchmark(model) is None


def test_complete_benchmark_retains_only_comparable_fields():
    model = {
        "benchmark": {
            "protocolVersion": "text-stream-v1",
            "taskId": "short-answer-zh-v1",
            "language": "zh",
            "samplingMode": "temperature-0",
            "temperature": 0,
            "maxOutputTokens": 256,
            "warmups": 1,
            "sampleCount": 3,
            "ttftMsMedian": 420,
            "outputTokensPerSecondMedian": 36.4,
            "testRegion": "domestic",
            "servicePath": "https://provider.example/v1/chat/completions",
            "testedAt": "2026-10-04",
            "rawResultRef": "data/benchmarks/example.json",
        }
    }
    normalized = comparable_benchmark(model)
    assert normalized["ttftMsMedian"] == 420
    assert normalized["outputTokensPerSecondMedian"] == 36.4
    assert normalized["sampleCount"] == 3
    assert normalized["samplingMode"] == "temperature-0"


def test_provider_default_benchmark_requires_and_retains_actual_temperature():
    model = {
        "benchmark": {
            "protocolVersion": "text-stream-v1", "taskId": "short-answer-zh-v1", "language": "zh",
            "samplingMode": "provider-default", "temperature": 0.7,
            "maxOutputTokens": 256, "warmups": 1, "sampleCount": 3,
            "ttftMsMedian": 420, "outputTokensPerSecondMedian": 36.4,
            "testRegion": "domestic", "servicePath": "https://provider.example/v1/chat/completions",
            "testedAt": "2026-10-04", "rawResultRef": "data/benchmarks/example.json",
        }
    }
    assert comparable_benchmark(model)["temperature"] == 0.7


def test_benchmark_rejects_invalid_calendar_date():
    model = {
        "benchmark": {
            "protocolVersion": "text-stream-v1", "taskId": "short-answer-zh-v1", "language": "zh",
            "samplingMode": "temperature-0", "temperature": 0,
            "maxOutputTokens": 256, "warmups": 1, "sampleCount": 3,
            "ttftMsMedian": 420, "outputTokensPerSecondMedian": 36.4,
            "testRegion": "domestic", "servicePath": "https://provider.example/v1/chat/completions",
            "testedAt": "2026-99-99", "rawResultRef": "data/benchmarks/example.json",
        }
    }
    assert comparable_benchmark(model) is None
