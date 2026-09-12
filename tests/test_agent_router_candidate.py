import json
from pathlib import Path

from crawler.github_discovery import extract_peer_document_evidence


ROOT = Path(__file__).resolve().parents[1]


def _read(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def test_agent_router_is_registered_for_bounded_discovery():
    providers = _read("providers.json")
    provider = next(item for item in providers if item["id"] == "agent-router")
    assert provider["allowedDomains"] == ["agentrouter.org"]
    assert "https://agentrouter.org/" in provider["discoveryUrls"]

    peers = _read("github-peers.json")
    peer = next(item for item in peers if item["id"] == "agent-router")
    assert peer["repoUrl"] == "https://github.com/justbiar/agent-router"
    assert peer["enabled"] is True


def test_agent_router_candidate_is_review_only_and_not_a_public_offer():
    candidates = _read("candidates.json")
    candidate = next(item for item in candidates if item.get("providerId") == "agent-router")
    assert candidate["status"] == "needs_review"
    assert candidate["sourceKind"] == "github_peer"
    assert candidate["repository"] == "justbiar/agent-router"
    assert {"claude-opus-5", "claude-opus-4-8", "gpt-5.6-sol"}.issubset(set(candidate["mentionedModels"]))

    offers = _read("offers.json")
    assert not any(item["id"] == "agent-router-free" for item in offers)


def test_peer_evidence_extracts_agent_router_model_ids():
    result = extract_peer_document_evidence(
        repository="justbiar/agent-router",
        path="README.md",
        commit_sha="abc123",
        content="Use `claude-opus-5`, `claude-opus-4-8`, and `gpt-5.6-sol` through AgentRouter.",
    )

    assert {"claude-opus-5", "claude-opus-4-8", "gpt-5.6-sol"}.issubset(set(result["mentionedModels"]))
