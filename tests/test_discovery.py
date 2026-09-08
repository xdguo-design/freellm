import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from crawler.discovery import (
    build_coverage_report,
    build_candidates,
    build_source_review_events,
    discover_public_sources,
    extract_discovery_links,
    merge_candidates,
    scan_provider_sources,
    validate_provider_registry,
    matched_keywords,
)
from crawler.cli import main as cli_main
from scripts.build_discovery_report import build_discovery_report


class DiscoveryTests(unittest.TestCase):
    def test_global_discovery_queries_cover_unknown_offer_surfaces(self):
        queries = json.loads(Path("data/discovery-queries.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(queries), 8)
        joined = " ".join(queries).lower()
        for keyword in ("free", "api", "openai-compatible", "image", "video", "coding", "rate", "catalog"):
            self.assertIn(keyword, joined)
        self.assertTrue(all(isinstance(query, str) and query.strip() for query in queries))

    def test_global_github_discovery_scans_unknown_repository_docs(self):
        from crawler.github_discovery import discover_global_github_sources

        search_url = "https://api.github.com/search/repositories?q=free+AI+API&per_page=30"
        repo_url = "https://api.github.com/repos/newco/free-api"
        commit_url = "https://api.github.com/repos/newco/free-api/commits/main"
        tree_url = "https://api.github.com/repos/newco/free-api/git/trees/main?recursive=1"
        raw_url = "https://raw.githubusercontent.com/newco/free-api/abc123/README.md"

        json_pages = {
            search_url: {
                "items": [{
                    "full_name": "newco/free-api",
                    "html_url": "https://github.com/newco/free-api",
                    "default_branch": "main",
                    "description": "OpenAI-compatible free API gateway",
                    "stargazers_count": 42,
                }]
            },
            repo_url: {"default_branch": "main"},
            commit_url: {"sha": "abc123"},
            tree_url: {"tree": [{"type": "blob", "path": "README.md"}]},
        }

        def fetch_json(url):
            return json_pages[url]

        def fetch_document(url):
            self.assertEqual(url, raw_url)
            return {
                "status": "ok",
                "content": "Free API with OpenAI-compatible endpoint and rate limit. See https://newco.ai/docs/pricing",
                "bytes": 104,
            }

        records = discover_global_github_sources(
            ["free AI API"],
            fetch_json=fetch_json,
            fetch_document=fetch_document,
            max_repositories=1,
            max_files=3,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sourceKind"], "github_global")
        self.assertEqual(records[0]["repository"], "newco/free-api")
        self.assertEqual(records[0]["path"], "README.md")
        self.assertEqual(records[0]["commitSha"], "abc123")
        self.assertEqual(records[0]["query"], "free AI API")
        self.assertIn("OpenAI-compatible", records[0]["evidence"])

    def test_global_candidates_merge_and_report(self):
        candidates = build_candidates([
            {
                "providerId": "github-global",
                "url": "https://raw.githubusercontent.com/newco/free-api/abc123/README.md",
                "sourceKind": "github_global",
                "repository": "newco/free-api",
                "path": "README.md",
                "commitSha": "abc123",
                "query": "free AI API",
                "mentionedModels": ["agnes-2.5-flash"],
                "evidence": "OpenAI-compatible free API with rate limit",
                "matchedKeywords": ["api_key", "rate_limit"],
                "status": "ok",
            },
            {
                "providerId": "github-global",
                "url": "https://raw.githubusercontent.com/newco/free-api/def456/README.md",
                "sourceKind": "github_global",
                "repository": "newco/free-api",
                "path": "README.md",
                "commitSha": "def456",
                "query": "free multimodal API",
                "mentionedModels": ["agnes-video-v2.0"],
                "evidence": "Free multimodal API with video model",
                "matchedKeywords": ["free"],
                "status": "ok",
            },
        ], now="2026-09-08T00:00:00+00:00")

        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(item["sourceKind"] == "github_global" for item in candidates))
        report = build_discovery_report(candidates)
        self.assertIn("2 candidates", report)
        self.assertIn("newco/free-api", report)
        self.assertIn("README.md", report)
        self.assertIn("needs_review", report)
    def test_provider_registry_covers_china_and_global_peer_sources(self):
        providers = json.loads(Path("data/providers.json").read_text(encoding="utf-8"))
        ids = {provider["id"] for provider in providers}

        for provider_id in {
            "xiaomi-mimo",
            "tencent-tokenhub",
            "baidu-qianfan",
            "aliyun-bailian",
            "sensecore",
            "volcengine-ark",
            "zhipu-glm",
            "meituan-longcat",
            "qwen",
            "deepseek",
            "minimax",
            "moonshot-kimi",
            "china-ai-ides",
            "opencode",
            "github-copilot",
            "cursor",
            "amazon-q-developer",
            "google-antigravity",
        }:
            self.assertIn(provider_id, ids)

        self.assertEqual(validate_provider_registry(providers), [])

    def test_web_infrastructure_mvp_providers_are_registered(self):
        providers = json.loads(Path("data/providers.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in providers}
        self.assertTrue({
            "keenable", "tinyfish", "tavily", "exa",
            "you-com", "firecrawl", "brave-search", "browserbase",
        } <= ids)

    def test_discover_cli_writes_candidate_queue(self):
        providers = [{
            "id": "xiaomi-mimo",
            "name": "Xiaomi MiMo",
            "aliases": ["小米"],
            "allowedDomains": ["mimo.mi.com"],
            "discoveryUrls": ["https://mimo.mi.com/docs/home"],
        }]
        scan_results = [{
            "providerId": "xiaomi-mimo",
            "url": "https://mimo.mi.com/docs/promo",
            "status": "ok",
            "title": "MiMo promotion",
            "evidence": "注册即得 ¥10 体验金",
            "matchedKeywords": ["体验金"],
        }]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            providers_path = root / "providers.json"
            output_path = root / "candidates.json"
            providers_path.write_text(json.dumps(providers), encoding="utf-8")

            with patch("crawler.cli.scan_provider_sources", return_value=scan_results):
                exit_code = cli_main(["discover", "--providers", str(providers_path), "--out", str(output_path)])

            self.assertEqual(exit_code, 0)
            output = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0]["providerId"], "xiaomi-mimo")
            self.assertEqual(output[0]["status"], "needs_review")

    def test_coverage_report_exposes_failed_sources_and_missing_providers(self):
        providers = [
            {"id": "xiaomi-mimo", "allowedDomains": ["mimo.mi.com"], "discoveryUrls": ["https://mimo.mi.com/docs/home"]},
            {"id": "tencent-tokenhub", "allowedDomains": ["cloud.tencent.com"], "discoveryUrls": ["https://cloud.tencent.com/docs"]},
        ]
        scan_results = [
            {"providerId": "xiaomi-mimo", "url": "https://mimo.mi.com/docs/home", "status": "ok"},
            {"providerId": "tencent-tokenhub", "url": "https://cloud.tencent.com/docs", "status": "failed", "reason": "HTTP 503"},
        ]

        report = build_coverage_report(providers, scan_results, [], now="2026-09-06T00:00:00+00:00")

        self.assertEqual(report["providerCount"], 2)
        self.assertEqual(report["sourceCount"], 2)
        self.assertEqual(report["failedSourceCount"], 1)
        self.assertEqual(report["failedSources"][0]["providerId"], "tencent-tokenhub")
        self.assertEqual(report["missingProviderIds"], [])

    def test_source_failure_is_not_classified_as_expired(self):
        events = build_source_review_events([
            {"providerId": "xiaomi-mimo", "url": "https://mimo.mi.com/docs/home", "status": "failed", "reason": "timeout"}
        ], now="2026-09-06T00:00:00+00:00")

        self.assertEqual(events[0]["changeType"], "source_unavailable")
        self.assertEqual(events[0]["needsReview"], True)
        self.assertNotEqual(events[0]["changeType"], "expired")

    def test_coverage_cli_writes_report(self):
        providers = [{
            "id": "xiaomi-mimo",
            "name": "Xiaomi MiMo",
            "aliases": ["小米"],
            "allowedDomains": ["mimo.mi.com"],
            "discoveryUrls": ["https://mimo.mi.com/docs/home"],
        }]
        scan = [{"providerId": "xiaomi-mimo", "url": "https://mimo.mi.com/docs/home", "status": "ok"}]
        candidates = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            providers_path = root / "providers.json"
            scan_path = root / "scan.json"
            discovery_scan_path = root / "discovery-scan.json"
            candidates_path = root / "candidates.json"
            output_path = root / "coverage.json"
            providers_path.write_text(json.dumps(providers), encoding="utf-8")
            scan_path.write_text(json.dumps(scan), encoding="utf-8")
            discovery_scan_path.write_text(json.dumps(scan), encoding="utf-8")
            candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

            exit_code = cli_main([
                "coverage",
                "--providers", str(providers_path),
                "--scan", str(scan_path),
                "--scan", str(discovery_scan_path),
                "--candidates", str(candidates_path),
                "--out", str(output_path),
            ])

            self.assertEqual(exit_code, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["providerCount"], 1)
            self.assertEqual(report["sourceCount"], 2)

    def test_provider_registry_requires_unique_official_discovery_sources(self):
        providers = [
            {
                "id": "xiaomi-mimo",
                "name": "Xiaomi MiMo",
                "aliases": ["小米", "MiMo"],
                "allowedDomains": ["mimo.mi.com"],
                "discoveryUrls": ["https://mimo.mi.com/docs/zh-CN/updates/feature/platform"],
            },
            {
                "id": "xiaomi-mimo",
                "name": "Duplicate",
                "aliases": [],
                "allowedDomains": ["mimo.mi.com"],
                "discoveryUrls": [],
            },
        ]

        errors = validate_provider_registry(providers)

        self.assertIn("duplicate provider id: xiaomi-mimo", errors)
        self.assertIn("providers[1]: discoveryUrls must contain at least one HTTPS URL", errors)

    def test_build_candidates_requires_review_and_keeps_evidence(self):
        scan_results = [
            {
                "providerId": "xiaomi-mimo",
                "url": "https://mimo.mi.com/docs/zh-CN/updates/feature/platform",
                "status": "ok",
                "title": "Xiaomi MiMo 开放平台",
                "evidence": "注册即得 ¥10 体验金；非高峰期 0.8x 消耗系数",
                "matchedKeywords": ["体验金", "非高峰期"],
                "checkedAt": "2026-09-06T00:00:00+00:00",
            }
        ]

        candidates = build_candidates(scan_results, now="2026-09-06T00:00:00+00:00")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["providerId"], "xiaomi-mimo")
        self.assertEqual(candidates[0]["status"], "needs_review")
        self.assertEqual(candidates[0]["seenCount"], 1)
        self.assertEqual(candidates[0]["matchedKeywords"], ["体验金", "非高峰期"])

    def test_merge_candidates_deduplicates_source_and_preserves_first_seen(self):
        existing = [
            {
                "id": "candidate-x",
                "providerId": "xiaomi-mimo",
                "sourceUrl": "https://mimo.mi.com/docs/zh-CN/updates/feature/platform#now",
                "status": "needs_review",
                "firstSeenAt": "2026-09-05T00:00:00+00:00",
                "lastSeenAt": "2026-09-05T00:00:00+00:00",
                "seenCount": 1,
            }
        ]
        discovered = [
            {
                "id": "candidate-new",
                "providerId": "xiaomi-mimo",
                "sourceUrl": "https://mimo.mi.com/docs/zh-CN/updates/feature/platform",
                "status": "needs_review",
                "firstSeenAt": "2026-09-06T00:00:00+00:00",
                "lastSeenAt": "2026-09-06T00:00:00+00:00",
                "seenCount": 1,
            }
        ]

        merged = merge_candidates(existing, discovered, now="2026-09-06T00:00:00+00:00")

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["firstSeenAt"], "2026-09-05T00:00:00+00:00")
        self.assertEqual(merged[0]["lastSeenAt"], "2026-09-06T00:00:00+00:00")
        self.assertEqual(merged[0]["seenCount"], 2)

    def test_extract_discovery_links_only_returns_keyworded_allowed_urls(self):
        html = """
        <a href="/docs/pricing">免费额度与价格</a>
        <a href="https://mimo.mi.com/docs/updates">更新日志</a>
        <a href="https://evil.example/free">免费</a>
        <a href="/about">关于我们</a>
        <loc>https://mimo.mi.com/docs/promo</loc>
        """

        links = extract_discovery_links(html, "https://mimo.mi.com/docs/home", ["mimo.mi.com"])

        self.assertEqual(
            links,
            [
                "https://mimo.mi.com/docs/pricing",
                "https://mimo.mi.com/docs/promo",
            ],
        )

    def test_extract_discovery_links_rejects_control_characters_and_spaces(self):
        html = '<a href="/docs/free plan">免费</a><a href="/docs/free">免费</a>'

        links = extract_discovery_links(html, "https://mimo.mi.com/docs/home", ["mimo.mi.com"])

        self.assertEqual(links, ["https://mimo.mi.com/docs/free"])

    def test_discover_public_sources_returns_candidates_without_publishing(self):
        providers = [
            {
                "id": "xiaomi-mimo",
                "name": "Xiaomi MiMo",
                "aliases": ["小米", "MiMo"],
                "allowedDomains": ["mimo.mi.com"],
                "discoveryUrls": ["https://mimo.mi.com/docs/home"],
            }
        ]

        pages = {
            "https://mimo.mi.com/docs/home": {
                "url": "https://mimo.mi.com/docs/home",
                "status": "ok",
                "title": "MiMo updates",
                "evidence": "优惠入口",
                "links": ["https://mimo.mi.com/docs/promo"],
            },
            "https://mimo.mi.com/docs/promo": {
                "url": "https://mimo.mi.com/docs/promo",
                "status": "ok",
                "title": "MiMo promotion",
                "evidence": "注册即得 ¥10 体验金",
                "matchedKeywords": ["体验金"],
            },
        }

        results = discover_public_sources(providers, fetcher=lambda url, domains: pages[url])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["providerId"], "xiaomi-mimo")
        self.assertEqual(results[0]["sourceUrl"], "https://mimo.mi.com/docs/promo")
        self.assertEqual(results[0]["status"], "needs_review")

    def test_scan_provider_sources_isolates_one_page_failure(self):
        providers = [{
            "id": "xiaomi-mimo",
            "name": "Xiaomi MiMo",
            "aliases": ["小米"],
            "allowedDomains": ["mimo.mi.com"],
            "discoveryUrls": ["https://mimo.mi.com/docs/home"],
        }]

        def fetcher(url, domains):
            if url.endswith("/broken"):
                raise RuntimeError("simulated page failure")
            return {
                "url": url,
                "status": "ok",
                "title": "MiMo",
                "evidence": "免费额度",
                "links": ["https://mimo.mi.com/docs/broken", "https://mimo.mi.com/docs/good"],
            }

        results = scan_provider_sources(providers, fetcher=fetcher, max_links_per_provider=2)

        failures = [result for result in results if result["status"] != "ok"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["changeType"], "source_unavailable")

    def test_web_keywords_find_rate_limit_and_quickstart_pages(self):
        text = "Search API quickstart, 30 RPM, wallet, auto reload, fetch URL"
        self.assertIn("quickstart", matched_keywords(text))
        self.assertIn("rate_limit", matched_keywords(text))
        self.assertIn("wallet", matched_keywords(text))


if __name__ == "__main__":
    unittest.main()
