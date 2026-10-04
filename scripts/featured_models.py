"""Evidence-aware display rules for the hand-curated model collection."""

from __future__ import annotations

import math
import re
from datetime import date
from urllib.parse import urlparse


_REGION_LABELS = {
    "domestic": "中国大陆可调用",
    "international": "海外可调用",
}
_MODALITY_LABELS = {
    "text": "文本",
    "reasoning": "推理",
    "image": "图片·方向待核实",
    "audio": "音频·方向待核实",
    "video": "视频·方向待核实",
}
_VERIFIED_CAPABILITY_LABELS = {
    ("text", "input"): "文本输入",
    ("text", "output"): "文本生成",
    ("image", "input"): "图片理解",
    ("image", "output"): "图片生成",
    ("audio", "input"): "音频输入",
    ("audio", "output"): "语音生成",
    ("speech_recognition", "input"): "语音识别",
    ("video", "input"): "视频理解",
    ("video", "output"): "视频生成",
    ("image_generation", "output"): "图片生成",
    ("audio_generation", "output"): "语音生成",
    ("speech_generation", "output"): "语音生成",
    ("video_generation", "output"): "视频生成",
}
_CAPABILITY_BASE_BY_NAME = {
    "image_generation": "image",
    "audio_generation": "audio",
    "speech_generation": "audio",
    "speech_recognition": "audio",
    "video_generation": "video",
}
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _valid_date(value: object) -> bool:
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def normalize_region(model: dict) -> dict:
    """Return a verified route region; documentation-only or missing claims stay unknown."""
    route = str(model.get("servicePath") or model.get("accessEndpoint") or "").strip()
    model_route = str(model.get("accessEndpoint") or model.get("servicePath") or "").strip()
    evidence_url = model.get("regionEvidenceUrl")
    checked_at = model.get("regionCheckedAt")
    raw_regions = model.get("verifiedRegions")
    regions = []
    same_route = not model_route or route == model_route
    if same_route and route and _valid_http_url(route) and _valid_http_url(evidence_url) and _valid_date(checked_at) and isinstance(raw_regions, list):
        regions = list(dict.fromkeys(
            region for region in raw_regions
            if region in _REGION_LABELS
        ))

    if len(regions) == 2:
        label, filter_value = "国内外均可调用", "both"
    elif regions:
        filter_value = regions[0]
        label = _REGION_LABELS[filter_value]
    else:
        label, filter_value = "待核实", "unknown"
    return {"regions": regions, "label": label, "filterValue": filter_value}


def normalize_capabilities(model: dict) -> list[str]:
    """Use directional evidence when available; otherwise avoid claiming media generation."""
    modalities = model.get("modality") if isinstance(model.get("modality"), list) else []
    evidenced = model.get("verifiedCapabilities")
    labels = []
    verified_names = set()
    if isinstance(evidenced, list):
        for capability in evidenced:
            if not isinstance(capability, dict):
                continue
            name = str(capability.get("name") or "").strip()
            direction = str(capability.get("direction") or "").strip()
            label = _VERIFIED_CAPABILITY_LABELS.get((name, direction))
            if label and _valid_http_url(capability.get("evidenceUrl")) and _valid_date(capability.get("checkedAt")):
                if label not in labels:
                    labels.append(label)
            verified_names.add(_CAPABILITY_BASE_BY_NAME.get(name, name))

    for modality in modalities:
        modality = str(modality).strip().lower()
        label = _MODALITY_LABELS.get(modality)
        if label and modality not in verified_names and label not in labels:
            labels.append(label)
    return labels


def comparable_benchmark(model: dict) -> dict | None:
    """Return benchmark data only when it has a complete, route-bound, repeatable protocol record."""
    benchmark = model.get("benchmark")
    if not isinstance(benchmark, dict):
        return None

    numeric_fields = ("ttftMsMedian", "outputTokensPerSecondMedian")
    numeric_values = [benchmark.get(key) for key in numeric_fields]
    if not all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in numeric_values):
        return None

    route = str(benchmark.get("servicePath") or "").strip()
    model_route = str(model.get("accessEndpoint") or model.get("servicePath") or "").strip()
    required_text = ("protocolVersion", "taskId", "language", "testedAt", "rawResultRef")
    if not all(isinstance(benchmark.get(key), str) and benchmark[key].strip() for key in required_text):
        return None
    if not _valid_http_url(route) or not _valid_date(benchmark.get("testedAt")):
        return None
    if model_route and route != model_route:
        return None
    if benchmark.get("testRegion") not in _REGION_LABELS:
        return None
    if benchmark.get("warmups") != 1 or benchmark.get("sampleCount") != 3 or benchmark.get("maxOutputTokens") != 256:
        return None

    temperature = benchmark.get("temperature")
    sampling_mode = benchmark.get("samplingMode")
    if not (isinstance(temperature, (int, float)) and math.isfinite(temperature) and temperature >= 0):
        return None
    if sampling_mode == "temperature-0" and temperature != 0:
        return None
    if sampling_mode not in {"temperature-0", "provider-default"}:
        return None

    return {
        key: benchmark[key]
        for key in (
            "protocolVersion", "taskId", "language", "samplingMode", "temperature", "maxOutputTokens",
            "warmups", "sampleCount", "ttftMsMedian", "outputTokensPerSecondMedian",
            "testRegion", "servicePath", "testedAt", "rawResultRef",
        )
    }
