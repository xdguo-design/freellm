import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "test_mimo_v26_live.py"

spec = importlib.util.spec_from_file_location("test_mimo_v26_live_script", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_live_routes_point_to_verified_mimo_ids():
    assert module.ROUTES["opencode"]["model"] == "mimo-v2.6-flash-free"
    assert module.ROUTES["opencode"]["endpoint"] == "https://opencode.ai/zen/v1/chat/completions"
    assert module.ROUTES["opencode"]["env"] == "OPENCODE_API_KEY"
    assert module.ROUTES["puter"]["model"] == "xiaomi/mimo-v2.6-flash"
    assert module.ROUTES["puter"]["endpoint"] == "https://api.puter.com/puterai/openai/v1/chat/completions"
    assert module.ROUTES["puter"]["env"] == "PUTER_AUTH_TOKEN"


def test_live_payload_uses_small_deterministic_smoke_request():
    payload = module.json.loads(module.build_payload(module.ROUTES["opencode"], module.DEFAULT_PROMPT))
    assert payload["max_tokens"] == 32
    assert payload["temperature"] == 0
    assert payload["messages"][0]["content"] == "Reply with exactly: MiMo OK"


def test_extract_text_supports_string_and_typed_parts():
    assert module.extract_text({"choices":[{"message":{"content":"MiMo OK"}}]}) == "MiMo OK"
    assert module.extract_text({"choices":[{"message":{"content":[{"text":"MiMo "},{"text":"OK"}]}}]}) == "MiMo OK"
