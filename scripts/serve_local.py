#!/usr/bin/env python3
"""Serve the static site locally with the same home route as Vercel."""

from __future__ import annotations

import argparse
import logging
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
HOME_DOCUMENT = "/design/free-china-ai-index.html"


class LocalSiteHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        if urlsplit(path).path == "/":
            path = HOME_DOCUMENT
        return super().translate_path(path)

    def end_headers(self) -> None:
        # Local preview must always reflect the working tree: without this the
        # browser heuristically caches HTML/CSS and stale pages keep rendering
        # after edits until a hard refresh.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8901)
    args = parser.parse_args()

    handler = partial(LocalSiteHandler, directory=str(ROOT))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.info("FreeLLM local preview: http://127.0.0.1:%s/", args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
