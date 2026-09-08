import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crawler.discovery import build_coverage_report
from crawler.github_discovery import (
    extract_peer_document_evidence,
    fetch_github_document,
    fetch_github_json,
    select_document_paths,
    discover_github_repositories,
    scan_github_peer,
    validate_peer_registry,
)


class GitHubRegistryTests(unittest.TestCase):
    def test_seed_registry_contains_devansh_freellm(self):
        peers = json.loads(Path("data/github-peers.json").read_text(encoding="utf-8"))
        self.assertTrue(any(
            peer["owner"] == "Devansh-365" and peer["repo"] == "freellm"
            for peer in peers
        ))
        self.assertEqual(validate_peer_registry(peers), [])

    def test_registry_rejects_non_github_hosts_and_duplicate_ids(self):
        errors = validate_peer_registry([
            {
                "id": "peer-a",
                "owner": "owner",
                "repo": "repo",
                "repoUrl": "https://evil.example/repo",
                "kind": "gateway",
                "discoveryQueries": ["free llm gateway"],
                "allowedHosts": ["github.com"],
                "enabled": True,
            },
            {
                "id": "peer-a",
                "owner": "owner",
                "repo": "repo-two",
                "repoUrl": "https://github.com/owner/repo-two",
                "kind": "gateway",
                "discoveryQueries": ["llm router"],
                "allowedHosts": ["github.com"],
                "enabled": True,
            },
        ])
        self.assertIn("duplicate peer id: peer-a", errors)
        self.assertTrue(any("github.com" in error for error in errors))


class GitHubDocumentFetchTests(unittest.TestCase):
    @patch("crawler.fetch.fetch_public_text_resource")
    def test_fetch_github_json_allows_bounded_large_tree_indexes(self, fetch_text):
        fetch_text.return_value = {
            "status": "ok",
            "content": "{}",
        }

        self.assertEqual(fetch_github_json("https://api.github.com/repos/owner/repo"), {})
        self.assertEqual(fetch_text.call_args.kwargs["max_bytes"], 2_000_000)

    def test_fetch_github_document_accepts_markdown(self):
        result = fetch_github_document(
            "https://raw.githubusercontent.com/owner/repo/main/README.md",
            fetcher=lambda url, allowed_hosts, timeout, max_bytes: {
                "url": url,
                "status": "ok",
                "contentType": "text/markdown",
                "content": "# Free models\nProvider docs",
                "bytes": 31,
            },
            max_bytes=1024,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["contentType"], "text/markdown")
        self.assertEqual(result["content"], "# Free models\nProvider docs")

    def test_fetch_github_document_rejects_unsafe_url(self):
        result = fetch_github_document(
            "https://evil.example/owner/repo/README.md",
            fetcher=lambda *args, **kwargs: self.fail("unsafe URL must not be fetched"),
        )

        self.assertEqual(result["status"], "rejected")

    def test_fetch_github_document_preserves_source_limit(self):
        result = fetch_github_document(
            "https://raw.githubusercontent.com/owner/repo/main/README.md",
            fetcher=lambda url, allowed_hosts, timeout, max_bytes: {
                "url": url,
                "status": "source_limit",
                "reason": "response exceeds maximum size",
                "bytes": max_bytes + 1,
            },
            max_bytes=10,
        )

        self.assertEqual(result["status"], "source_limit")
        self.assertEqual(result["bytes"], 11)


class GitHubEvidenceTests(unittest.TestCase):
    def test_select_document_paths_prefers_docs_and_excludes_executable_files(self):
        paths = select_document_paths([
            "src/router.py",
            "README.md",
            "docs/providers.md",
            "package.json",
            "scripts/install.sh",
            ".env.example",
            "CHANGELOG.md",
        ], max_files=5)

        self.assertEqual(
            paths,
            ["README.md", "CHANGELOG.md", ".env.example", "docs/providers.md", "package.json"],
        )

    def test_extract_peer_document_evidence_keeps_provenance_and_peer_level(self):
        result = extract_peer_document_evidence(
            repository="Devansh-365/freellm",
            path="README.md",
            commit_sha="abc123",
            content=(
                "Gemini and Groq free tiers.\n"
                "See https://ai.google.dev/gemini-api/docs for official docs.\n"
                "Use model free-fast.\n"
                "GROQ_API_KEY=gsk_should_not_be_saved"
            ),
        )

        self.assertEqual(result["sourceKind"], "github_peer")
        self.assertEqual(result["officiality"], "peer_discovery")
        self.assertEqual(result["repository"], "Devansh-365/freellm")
        self.assertEqual(result["path"], "README.md")
        self.assertEqual(result["commitSha"], "abc123")
        self.assertIn("ai.google.dev", result["officialLinks"][0])
        self.assertIn("free-fast", result["mentionedModels"])
        self.assertNotIn("gsk_should_not_be_saved", result["evidence"])


class GitHubRepositoryScanTests(unittest.TestCase):
    def test_discover_github_repositories_deduplicates_queries_and_excludes_forks(self):
        calls = []

        def fetch_json(url):
            calls.append(url)
            return {
                "items": [
                    {"full_name": "owner/peer", "html_url": "https://github.com/owner/peer", "fork": False},
                    {"full_name": "owner/fork", "html_url": "https://github.com/owner/fork", "fork": True},
                ]
            }

        repositories = discover_github_repositories(
            ["free llm gateway", "free llm gateway"],
            fetch_json=fetch_json,
        )

        self.assertEqual(len(calls), 1)
        self.assertEqual([repo["full_name"] for repo in repositories], ["owner/peer"])

    def test_scan_github_peer_reads_only_selected_documents(self):
        peer = {
            "id": "peer-a",
            "owner": "owner",
            "repo": "repo",
            "repoUrl": "https://github.com/owner/repo",
            "kind": "gateway",
        }
        fetched_urls = []

        def fetch_json(url):
            if "/git/trees/" in url:
                return {
                    "tree": [
                        {"path": "README.md", "type": "blob", "sha": "readme-sha", "size": 80},
                        {"path": "src/router.py", "type": "blob", "sha": "code-sha", "size": 80},
                    ]
                }
            return {"default_branch": "main", "sha": "head-sha"}

        def fetch_document(url):
            fetched_urls.append(url)
            return {"status": "ok", "content": "Free tier. See https://ai.google.dev/gemini-api/docs"}

        results = scan_github_peer(peer, fetch_json=fetch_json, fetch_document=fetch_document)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["path"], "README.md")
        self.assertEqual(results[0]["commitSha"], "head-sha")
        self.assertEqual(results[0]["sourceKind"], "github_peer")
        self.assertEqual(len(fetched_urls), 1)
        self.assertIn("raw.githubusercontent.com/owner/repo/head-sha/README.md", fetched_urls[0])

    def test_scan_github_peer_resolves_branch_to_commit_for_provenance(self):
        peer = {
            "id": "peer-a",
            "owner": "owner",
            "repo": "repo",
            "repoUrl": "https://github.com/owner/repo",
            "kind": "gateway",
        }
        calls = []

        def fetch_json(url):
            calls.append(url)
            if url.endswith("/commits/main"):
                return {"sha": "resolved-sha"}
            if "/git/trees/" in url:
                return {"tree": [{"path": "README.md", "type": "blob"}]}
            return {"default_branch": "main"}

        results = scan_github_peer(
            peer,
            fetch_json=fetch_json,
            fetch_document=lambda url: {"status": "ok", "content": "Free tier"},
        )

        self.assertEqual(results[0]["commitSha"], "resolved-sha")
        self.assertTrue(any(url.endswith("/commits/main") for url in calls))
        self.assertIn("/resolved-sha/README.md", results[0]["url"])

    def test_peer_evidence_can_be_merged_into_review_candidates_with_provenance(self):
        from crawler.discovery import build_candidates

        candidates = build_candidates([
            {
                "providerId": "peer-a",
                "repository": "owner/repo",
                "path": "README.md",
                "commitSha": "head-sha",
                "url": "https://raw.githubusercontent.com/owner/repo/head-sha/README.md",
                "sourceKind": "github_peer",
                "officiality": "peer_discovery",
                "status": "needs_review",
                "title": "Free LLM gateway",
                "evidence": "Free tier with Gemini and Groq",
                "matchedKeywords": ["free"],
            }
        ], now="2026-09-07T00:00:00+00:00")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["sourceKind"], "github_peer")
        self.assertEqual(candidates[0]["officiality"], "peer_discovery")
        self.assertEqual(candidates[0]["repository"], "owner/repo")
        self.assertEqual(candidates[0]["commitSha"], "head-sha")
        self.assertEqual(candidates[0]["status"], "needs_review")

    def test_coverage_report_separates_peer_sources_from_official_sources(self):
        from crawler.discovery import build_coverage_report

        report = build_coverage_report(
            providers=[{"id": "official-a"}],
            scan_results=[
                {"providerId": "official-a", "url": "https://official.example/docs", "sourceKind": "official", "status": "ok"},
                {"providerId": "peer-a", "repository": "owner/repo", "url": "https://raw.githubusercontent.com/owner/repo/main/README.md", "sourceKind": "github_peer", "status": "needs_review"},
                {"providerId": "peer-b", "repository": "owner/other", "url": "https://raw.githubusercontent.com/owner/other/main/README.md", "sourceKind": "github_peer", "status": "source_unavailable", "reason": "HTTP 404"},
            ],
            candidates=[],
            now="2026-09-07T00:00:00+00:00",
        )

        self.assertEqual(report["officialSourceCount"], 1)
        self.assertEqual(report["peerSourceCount"], 2)
        self.assertEqual(report["successfulPeerSourceCount"], 1)
        self.assertEqual(report["failedPeerSourceCount"], 1)
        self.assertEqual(report["peerRepositoryCount"], 2)

    def test_coverage_report_separates_third_party_directory_sources(self):
        report = build_coverage_report(
            providers=[{"id": "official-a"}],
            scan_results=[
                {"providerId": "official-a", "url": "https://official.example/docs", "sourceKind": "official", "status": "ok"},
                {"providerId": "freellm-net", "url": "https://freellm.net/models/", "sourceKind": "third_party_directory", "status": "ok"},
                {"providerId": "freellm-net", "url": "https://freellm.net/llms.txt", "sourceKind": "third_party_directory", "status": "failed"},
            ],
            candidates=[],
            now="2026-09-08T00:00:00+00:00",
        )

        self.assertEqual(report["officialSourceCount"], 1)
        self.assertEqual(report["thirdPartySourceCount"], 2)
        self.assertEqual(report["successfulThirdPartySourceCount"], 1)
        self.assertEqual(report["failedThirdPartySourceCount"], 1)

    def test_discover_cli_can_append_github_peer_scan_results(self):
        providers = [{
            "id": "official-a",
            "name": "Official A",
            "aliases": [],
            "allowedDomains": ["official.example"],
            "discoveryUrls": ["https://official.example/docs"],
        }]
        peers = [{
            "id": "peer-a",
            "owner": "owner",
            "repo": "repo",
            "repoUrl": "https://github.com/owner/repo",
            "kind": "gateway",
            "discoveryQueries": ["free llm gateway"],
            "allowedHosts": ["github.com", "api.github.com", "raw.githubusercontent.com"],
            "enabled": True,
        }]
        official_result = {
            "providerId": "official-a",
            "url": "https://official.example/docs/promo",
            "sourceKind": "candidate",
            "status": "ok",
            "evidence": "Free quota",
            "matchedKeywords": ["free"],
        }
        peer_result = {
            "providerId": "peer-a",
            "repository": "owner/repo",
            "path": "README.md",
            "commitSha": "head-sha",
            "url": "https://raw.githubusercontent.com/owner/repo/head-sha/README.md",
            "sourceKind": "github_peer",
            "officiality": "peer_discovery",
            "status": "needs_review",
            "evidence": "Free tier",
            "matchedKeywords": ["free"],
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            providers_path = root / "providers.json"
            peers_path = root / "github-peers.json"
            output_path = root / "candidates.json"
            scan_path = root / "scan.json"
            providers_path.write_text(json.dumps(providers), encoding="utf-8")
            peers_path.write_text(json.dumps(peers), encoding="utf-8")

            with patch("crawler.cli.scan_provider_sources", return_value=[official_result]), patch(
                "crawler.cli.scan_github_peer", return_value=[peer_result]
            ):
                from crawler.cli import main as cli_main

                exit_code = cli_main([
                    "discover",
                    "--providers", str(providers_path),
                    "--github-peers", str(peers_path),
                    "--out", str(output_path),
                    "--scan-out", str(scan_path),
                ])

            self.assertEqual(exit_code, 0)
            scan_results = json.loads(scan_path.read_text(encoding="utf-8"))
            self.assertEqual({result["sourceKind"] for result in scan_results}, {"candidate", "github_peer"})
            candidates = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(len(candidates), 2)
            self.assertTrue(all(candidate["status"] == "needs_review" for candidate in candidates))


if __name__ == "__main__":
    unittest.main()
