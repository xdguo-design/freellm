"""Fail CI when the deployable payload exceeds the Vercel storage budget.

Vercel bills Deployment Storage cumulatively across retained deployments, so
the per-deployment upload size is the only storage lever this repo controls.
The measurement mirrors .vercelignore (git-tracked files minus ignore rules),
which is what a Git-integration deployment actually uploads.
"""

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MIB = 1048576


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def load_ignore_patterns():
    patterns = []
    for raw in (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def is_ignored(path, patterns):
    for pattern in patterns:
        if pattern.endswith("/"):
            prefix = pattern[:-1]
            if prefix.startswith("**/"):
                if f"/{prefix[3:]}/" in f"/{path}/":
                    return True
            elif path == prefix or path.startswith(prefix + "/"):
                return True
        elif "/" in pattern:
            if fnmatch.fnmatch(path, pattern):
                return True
        elif fnmatch.fnmatch(path.rsplit("/", 1)[-1], pattern):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-total-mb", type=float, default=60.0,
                        help="hard budget: exit 1 when the payload exceeds this")
    parser.add_argument("--warn-total-mb", type=float, default=35.0,
                        help="warn when the payload approaches the budget")
    parser.add_argument("--warn-file-mb", type=float, default=1.5,
                        help="warn per file above this size")
    parser.add_argument("--top", type=int, default=10,
                        help="how many largest files to print")
    args = parser.parse_args()

    patterns = load_ignore_patterns()
    sizes = []
    for path in tracked_files():
        if is_ignored(path, patterns):
            continue
        full = ROOT / path
        if not full.is_file():
            print(f"ERROR: tracked file missing from working tree: {path}", file=sys.stderr)
            return 1
        sizes.append((full.stat().st_size, path))

    total_mb = sum(size for size, _ in sizes) / MIB
    sizes.sort(reverse=True)

    print(f"Deployable payload: {len(sizes)} files, {total_mb:.1f} MB "
          f"(budget {args.max_total_mb:.0f} MB)")
    for size, path in sizes[: args.top]:
        print(f"  {size / MIB:7.2f} MB  {path}")

    failed = False
    for size, path in sizes:
        if size > args.warn_file_mb * MIB:
            print(f"WARNING: {path} is {size / MIB:.2f} MB (> {args.warn_file_mb:g} MB per file)")
    if total_mb >= args.warn_total_mb:
        print(f"WARNING: payload {total_mb:.1f} MB is approaching the "
              f"{args.max_total_mb:.0f} MB budget")
    if total_mb > args.max_total_mb:
        print(f"ERROR: payload {total_mb:.1f} MB exceeds the {args.max_total_mb:.0f} MB budget; "
              f"trim assets or extend .vercelignore before deploying")
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
