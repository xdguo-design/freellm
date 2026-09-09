from crawler.freellm_net_discovery import (
    discover_freellm_net_sources,
    parse_llms_links,
    parse_model_directory,
    validate_source_registry,
)
from crawler.cli import main as cli_main
from scripts.build_discovery_report import build_discovery_report
from unittest.mock import patch
import unittest
import json
from pathlib import Path
import tempfile


HTML_FIXTURE = """
<table id="modelsTable">
  <tbody>
    <tr class="model-row" data-name="example/example-flash" data-provider="Example Provider"
        data-provider-slug="example-provider" data-modality="text,reasoning" data-free="1"
        data-nocard="1" data-verified="1" data-context="128K" data-tier-type="permanent">
      <td><a href="/providers/example-provider">Example Provider</a></td>
      <td><a href="/models/example-provider/example-flash" class="model-link">Example Flash</a></td>
      <td>92</td>
      <td>128K</td>
      <td>text, reasoning</td>
      <td>10 RPM, 100 RPD</td>
      <td>Sep 1, 2026</td>
      <td>—</td>
      <td><span class="status-badge status-online">Online</span></td>
    </tr>
  </tbody>
</table>
"""


def test_parse_model_directory_returns_free_model_metadata():
    rows = parse_model_directory(HTML_FIXTURE, "https://freellm.net/models/")

    assert rows == [{
        "directoryProvider": "Example Provider",
        "directoryProviderSlug": "example-provider",
        "model": "Example Flash",
        "modelId": "example/example-flash",
        "modelSlug": "example-flash",
        "directoryUrl": "https://freellm.net/models/example-provider/example-flash",
        "directoryFree": True,
        "directoryNoCard": True,
        "directoryVerified": True,
        "score": "92",
        "context": "128K",
        "maxOutput": "",
        "modality": "text,reasoning",
        "rateLimit": "10 RPM, 100 RPD",
        "released": "Sep 1, 2026",
        "usageActivity": "—",
        "status": "Online",
        "tierType": "permanent",
    }]


def test_parse_model_directory_does_not_turn_missing_release_into_epoch_date():
    html = HTML_FIXTURE.replace(
        'data-tier-type="permanent">',
        'data-tier-type="permanent" data-released="0">',
    )

    rows = parse_model_directory(html, "https://freellm.net/models/")

    assert rows[0]["released"] == ""


def test_parse_llms_links_rejects_external_and_sensitive_urls():
    links = parse_llms_links(
        "[Models](https://freellm.net/models/)\n"
        "[Bad](https://evil.example/x)\n"
        "[Key](https://freellm.net/x?api_key=secret)",
        "https://freellm.net/llms.txt",
    )

    assert links == ["https://freellm.net/models/"]


def test_parse_model_directory_skips_paid_and_duplicate_rows():
    paid = HTML_FIXTURE.replace('data-free="1"', 'data-free="0"')
    duplicate = HTML_FIXTURE + HTML_FIXTURE

    assert parse_model_directory(paid, "https://freellm.net/models/") == []
    assert len(parse_model_directory(duplicate, "https://freellm.net/models/")) == 1


def test_source_registry_accepts_freellm_net_config():
    assert validate_source_registry([{
        "id": "freellm-net",
        "allowedDomains": ["freellm.net"],
        "urls": ["https://freellm.net/models/", "https://freellm.net/llms.txt"],
        "enabled": True,
    }]) == []


def test_discovery_returns_model_candidates_without_publishing_offers():
    sources = [{
        "id": "freellm-net",
        "allowedDomains": ["freellm.net"],
        "urls": ["https://freellm.net/models/", "https://freellm.net/llms.txt"],
        "enabled": True,
    }]
    pages = {
        "https://freellm.net/models/": {"status": "ok", "content": HTML_FIXTURE},
        "https://freellm.net/llms.txt": {"status": "ok", "content": "[Models](https://freellm.net/models/)"},
    }

    records = discover_freellm_net_sources(
        sources,
        fetcher=lambda url, domains: pages[url],
        max_models=10,
    )

    assert len(records) == 1
    assert records[0]["providerId"] == "freellm-net"
    assert records[0]["sourceKind"] == "third_party_directory"
    assert records[0]["officiality"] == "third_party_discovery"
    assert records[0]["status"] == "needs_review"
    assert records[0]["model"] == "Example Flash"
    assert records[0]["directoryProvider"] == "Example Provider"
    assert records[0]["directoryStatus"] == "Online"
    assert records[0]["officialLinks"] == ["https://freellm.net/models/example-provider/example-flash"]


def test_discover_cli_accepts_third_party_source_registry():
    providers = [{
        "id": "official-a",
        "name": "Official A",
        "aliases": [],
        "allowedDomains": ["official.example"],
        "discoveryUrls": ["https://official.example/docs"],
    }]
    sources = [{
        "id": "freellm-net",
        "allowedDomains": ["freellm.net"],
        "urls": ["https://freellm.net/models/", "https://freellm.net/llms.txt"],
        "enabled": True,
    }]
    third_party_record = {
        "providerId": "freellm-net",
        "url": "https://freellm.net/models/example-provider/example-flash",
        "sourceKind": "third_party_directory",
        "officiality": "third_party_discovery",
        "status": "needs_review",
        "directoryStatus": "Online",
        "evidence": "Example Provider lists Example Flash as free",
        "matchedKeywords": ["free"],
        "model": "Example Flash",
        "directoryProvider": "Example Provider",
    }

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        providers_path = root / "providers.json"
        sources_path = root / "sources.json"
        output_path = root / "candidates.json"
        scan_path = root / "scan.json"
        providers_path.write_text(json.dumps(providers), encoding="utf-8")
        sources_path.write_text(json.dumps(sources), encoding="utf-8")

        with patch("crawler.cli.scan_provider_sources", return_value=[]), patch(
            "crawler.cli.discover_freellm_net_sources", return_value=[third_party_record]
        ):
            exit_code = cli_main([
                "discover",
                "--providers", str(providers_path),
                "--third-party-sources", str(sources_path),
                "--out", str(output_path),
                "--scan-out", str(scan_path),
            ])

        assert exit_code == 0
        candidates = json.loads(output_path.read_text(encoding="utf-8"))
        assert len(candidates) == 1
        assert candidates[0]["sourceKind"] == "third_party_directory"
        assert candidates[0]["directoryStatus"] == "Online"
        assert candidates[0]["model"] == "Example Flash"


def test_discovery_report_exposes_third_party_model_metadata():
    report = build_discovery_report([{
        "providerId": "freellm-net",
        "sourceKind": "third_party_directory",
        "officiality": "third_party_discovery",
        "sourceUrl": "https://freellm.net/models/example-provider/example-flash",
        "directoryProvider": "Example Provider",
        "model": "Example Flash",
        "context": "128K",
        "rateLimit": "10 RPM, 100 RPD",
        "status": "needs_review",
        "evidence": "Example Provider lists Example Flash as free",
        "seenCount": 1,
    }])

    assert "Directory provider: Example Provider" in report
    assert "Model: Example Flash" in report
    assert "Context: 128K" in report
    assert "Rate limit: 10 RPM, 100 RPD" in report
    assert "third-party directory" in report


class FreeLLMNetDiscoveryTests(unittest.TestCase):
    def test_parse_model_directory_returns_free_model_metadata(self):
        test_parse_model_directory_returns_free_model_metadata()

    def test_parse_llms_links_rejects_external_and_sensitive_urls(self):
        test_parse_llms_links_rejects_external_and_sensitive_urls()

    def test_parse_model_directory_skips_paid_and_duplicate_rows(self):
        test_parse_model_directory_skips_paid_and_duplicate_rows()

    def test_source_registry_accepts_freellm_net_config(self):
        test_source_registry_accepts_freellm_net_config()

    def test_discovery_returns_model_candidates_without_publishing_offers(self):
        test_discovery_returns_model_candidates_without_publishing_offers()

    def test_discover_cli_accepts_third_party_source_registry(self):
        test_discover_cli_accepts_third_party_source_registry()

    def test_discovery_report_exposes_third_party_model_metadata(self):
        test_discovery_report_exposes_third_party_model_metadata()
