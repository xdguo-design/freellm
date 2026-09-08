"""Command-line entry point for validation, public scans, diffs and snapshots."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .diff import build_review_queue, compare_offers
from .community_signals import merge_signals, validate_signals
from .discovery import build_candidates, build_coverage_report, merge_candidates, scan_provider_sources, validate_provider_registry
from .fetch import fetch_public_page, fetch_public_text_resource
from .freellm_net_discovery import discover_freellm_net_sources, validate_source_registry
from .github_discovery import (
    discover_global_github_sources,
    fetch_github_document,
    fetch_github_json,
    scan_github_peer,
    validate_peer_registry,
)
from .schema import validate_offers
from scripts.build_discovery_report import build_discovery_report


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="free-ai-index")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("path")

    diff = commands.add_parser("diff")
    diff.add_argument("--previous", required=True)
    diff.add_argument("--current", required=True)
    diff.add_argument("--out", required=True)

    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--input", required=True)
    snapshot.add_argument("--dir", required=True)

    scan = commands.add_parser("scan")
    scan.add_argument("--sources", required=True)
    scan.add_argument("--out", required=True)
    scan.add_argument("--timeout", type=int, default=8)

    discover = commands.add_parser("discover")
    discover.add_argument("--providers", required=True)
    discover.add_argument("--out", required=True)
    discover.add_argument("--scan-out", default=None)
    discover.add_argument("--max-links", type=int, default=20)
    discover.add_argument("--max-pages", type=int, default=100)
    discover.add_argument("--github-peers", default=None)
    discover.add_argument("--github-max-repositories", type=int, default=20)
    discover.add_argument("--github-max-files", type=int, default=80)
    discover.add_argument("--global-queries", default=None)
    discover.add_argument("--global-max-repositories", type=int, default=20)
    discover.add_argument("--third-party-sources", default=None)
    discover.add_argument("--third-party-max-models", type=int, default=305)
    discover.add_argument("--timeout", type=int, default=8)

    report = commands.add_parser("report")
    report.add_argument("--candidates", required=True)
    report.add_argument("--out", required=True)

    coverage = commands.add_parser("coverage")
    coverage.add_argument("--providers", required=True)
    coverage.add_argument("--scan", action="append", required=True)
    coverage.add_argument("--candidates", required=True)
    coverage.add_argument("--out", required=True)

    signals = commands.add_parser("signals")
    signals.add_argument("--input", required=True)
    signals.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    if args.command == "validate":
        errors = validate_offers(args.path)
        if errors:
            print("invalid:")
            print("\n".join(f"- {error}" for error in errors))
            return 1
        count = len(_read_json(args.path))
        print(f"valid: {count} offers")
        return 0
    if args.command == "diff":
        changes = compare_offers(_read_json(args.previous), _read_json(args.current))
        queue = build_review_queue(changes)
        _write_json(args.out, queue)
        print(f"review queue: {len(queue)} changes")
        return 0
    if args.command == "snapshot":
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = Path(args.dir) / f"offers-{timestamp}.json"
        _write_json(target, _read_json(args.input))
        print(f"snapshot: {target}")
        return 0
    if args.command == "scan":
        results = []
        for source in _read_json(args.sources):
            for url in source["urls"]:
                results.append({
                    "offerId": source["offerId"],
                    "providerId": source.get("providerId", source["offerId"]),
                    **fetch_public_page(url, source["allowedDomains"], timeout=args.timeout),
                })
        _write_json(args.out, results)
        failed = sum(1 for result in results if result["status"] != "ok")
        print(f"scan: {len(results)} sources, {failed} failed or rejected")
        return 1 if failed else 0
    if args.command == "discover":
        providers = _read_json(args.providers)
        registry_errors = validate_provider_registry(providers)
        if registry_errors:
            print("invalid provider registry:")
            print("\n".join(f"- {error}" for error in registry_errors))
            return 1
        existing = _read_json(args.out) if Path(args.out).exists() else []
        discovered_scan = scan_provider_sources(
            providers,
            lambda url, domains: fetch_public_page(url, domains, timeout=args.timeout),
            max_links_per_provider=args.max_links,
            max_total_pages=args.max_pages,
        )
        github_scan = []
        if args.github_peers:
            peers = _read_json(args.github_peers)
            peer_registry_errors = validate_peer_registry(peers)
            if peer_registry_errors:
                print("invalid GitHub peer registry:")
                print("\n".join(f"- {error}" for error in peer_registry_errors))
                return 1
            enabled_peers = [peer for peer in peers if peer.get("enabled")]
            for peer in enabled_peers[:args.github_max_repositories]:
                github_scan.extend(
                    scan_github_peer(
                        peer,
                        fetch_json=lambda url: fetch_github_json(url, timeout=args.timeout),
                        fetch_document=lambda url: fetch_github_document(url, timeout=args.timeout),
                        max_files=args.github_max_files,
                    )
                )
            discovered_scan.extend(github_scan)
        if args.global_queries:
            global_queries = _read_json(args.global_queries)
            if not isinstance(global_queries, list) or not all(isinstance(query, str) for query in global_queries):
                print("invalid global discovery queries: expected a JSON list of strings")
                return 1
            discovered_scan.extend(
                discover_global_github_sources(
                    global_queries,
                    fetch_json=lambda url: fetch_github_json(url, timeout=args.timeout),
                    fetch_document=lambda url: fetch_github_document(url, timeout=args.timeout),
                    max_repositories=args.global_max_repositories,
                    max_files=args.github_max_files,
                )
            )
        if args.third_party_sources:
            third_party_sources = _read_json(args.third_party_sources)
            source_registry_errors = validate_source_registry(third_party_sources)
            if source_registry_errors:
                print("invalid third-party source registry:")
                print("\n".join(f"- {error}" for error in source_registry_errors))
                return 1
            discovered_scan.extend(
                discover_freellm_net_sources(
                    third_party_sources,
                    fetcher=lambda url, domains: fetch_public_text_resource(
                        url,
                        domains,
                        timeout=args.timeout,
                        max_bytes=2_000_000,
                    ),
                    max_models=args.third_party_max_models,
                )
            )
        if args.scan_out:
            _write_json(args.scan_out, discovered_scan)
        discovered = build_candidates(discovered_scan)
        candidates = merge_candidates(existing, discovered)
        _write_json(args.out, candidates)
        print(f"discover: {len(candidates)} candidates")
        if args.github_peers:
            peer_documents = sum(1 for result in github_scan if result.get("path"))
            print(f"github peer documents: {peer_documents}")
        return 0
    if args.command == "report":
        candidates = _read_json(args.candidates)
        if not isinstance(candidates, list):
            print("invalid candidates: expected a JSON list")
            return 1
        Path(args.out).write_text(build_discovery_report(candidates), encoding="utf-8")
        print(f"report: {len(candidates)} candidates")
        return 0
    if args.command == "coverage":
        providers = _read_json(args.providers)
        registry_errors = validate_provider_registry(providers)
        if registry_errors:
            print("invalid provider registry:")
            print("\n".join(f"- {error}" for error in registry_errors))
            return 1
        scan_results = []
        for scan_path in args.scan:
            scan_results.extend(_read_json(scan_path))
        report = build_coverage_report(providers, scan_results, _read_json(args.candidates))
        _write_json(args.out, report)
        print(f"coverage: {report['successfulSourceCount']}/{report['sourceCount']} sources healthy")
        return 0
    if args.command == "signals":
        incoming = _read_json(args.input)
        errors = validate_signals(incoming)
        if errors:
            print("invalid community signals:")
            print("\n".join(f"- {error}" for error in errors))
            return 1
        existing = _read_json(args.out) if Path(args.out).exists() else []
        existing_errors = validate_signals(existing)
        if existing_errors:
            print("invalid existing community signals:")
            print("\n".join(f"- {error}" for error in existing_errors))
            return 1
        captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        merged = merge_signals(existing, incoming, captured_at=captured_at)
        _write_json(args.out, merged)
        rejected_count = sum(1 for record in incoming if validate_signals([record]))
        print(f"signals: {len(merged)} records, {rejected_count} rejected")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
