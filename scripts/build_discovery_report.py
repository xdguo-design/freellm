"""Render a safe, human-readable report for automatically discovered candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _text(value: object, fallback: str = "—") -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return text or fallback


def build_discovery_report(candidates: list[dict]) -> str:
    lines = [
        "# Automated AI discovery candidates",
        "",
        f"{len(candidates)} candidates found. All entries remain `needs_review` until an official source is verified.",
        "",
        "## Candidate queue",
        "",
    ]
    if not candidates:
        lines.append("No new candidates were found in this run.")
        return "\n".join(lines) + "\n"

    for index, candidate in enumerate(candidates, start=1):
        if candidate.get("sourceKind") == "third_party_directory":
            provider = _text(candidate.get("directoryProvider"), "unknown provider")
            model = _text(candidate.get("model"), "unknown model")
            source_url = _text(candidate.get("sourceUrl"), "source URL unavailable")
            lines.extend([
                f"### {index}. {provider} · {model}",
                "",
                "- Source kind: third-party directory (discovery only)",
                f"- Status: `{_text(candidate.get('status'), 'needs_review')}`",
                f"- Source: [{source_url}]({source_url})",
                f"- Directory provider: {provider}",
                f"- Model: {model}",
                f"- Context: {_text(candidate.get('context'))}",
                f"- Rate limit: {_text(candidate.get('rateLimit'))}",
                f"- Directory status: {_text(candidate.get('directoryStatus'))}",
                f"- Evidence: {_text(candidate.get('evidence'))}",
                f"- Seen count: {_text(candidate.get('seenCount'), '1')}",
                "",
            ])
            continue
        repository = _text(candidate.get("repository"), "unknown repository")
        path = _text(candidate.get("path"), "document path unavailable")
        source_url = _text(candidate.get("sourceUrl"), "source URL unavailable")
        models = ", ".join(str(model) for model in candidate.get("mentionedModels", []) if str(model).strip())
        providers = ", ".join(str(provider) for provider in candidate.get("mentionedProviders", []) if str(provider).strip())
        queries = _text(candidate.get("query"), "configured provider scan")
        lines.extend([
            f"### {index}. {repository} · {path}",
            "",
            f"- Status: `{_text(candidate.get('status'), 'needs_review')}`",
            f"- Source: [{source_url}]({source_url})",
            f"- Discovery query: {_text(queries)}",
            f"- Mentioned providers: {_text(providers)}",
            f"- Mentioned models: {_text(models)}",
            f"- Evidence: {_text(candidate.get('evidence'))}",
            f"- Seen count: {_text(candidate.get('seenCount'), '1')}",
            "",
        ])
    lines.extend([
        "## Review checklist",
        "",
        "- Confirm the provider owns or officially endorses the source.",
        "- Confirm the free mechanism, quota, region, expiry, payment behavior and model IDs.",
        "- Treat third-party directory rows as leads only; verify each model against the provider's official documentation.",
        "- Add only verified evidence to `data/offers.json`; do not copy secrets or execute repository code.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        raise SystemExit("candidates must be a JSON list")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(build_discovery_report(candidates), encoding="utf-8")
    print(f"report: {len(candidates)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
