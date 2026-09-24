#!/usr/bin/env python3
"""Real browser smoke test for Xiaomi MiMo-V2.6-Flash through Puter.js.

This test intentionally uses Puter.js in a browser, matching the public
User-Pays integration path. It does not require or expose a repository API key.
A temporary Puter user is requested only when the browser is not already
authenticated. This is a required release gate: success requires real assistant text\nfrom xiaomi/mimo-v2.6-flash and never degrades to a skip.
"""

from __future__ import annotations

import json
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

MODEL = "xiaomi/mimo-v2.6-flash"
PROMPT = "Reply with exactly: MiMo OK"
TIMEOUT_MS = 120_000

HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>FreeLLM MiMo live smoke</title>
  <script src="https://js.puter.com/v2/"></script>
</head>
<body>
  <button id="run" type="button">Run MiMo live test</button>
  <pre id="status">idle</pre>
  <script>
    window.__mimoResult = { status: "idle" };

    function extractText(response) {
      const content = response?.message?.content;
      if (typeof content === "string") return content.trim();
      if (Array.isArray(content)) {
        return content.map(part => {
          if (typeof part === "string") return part;
          if (part && typeof part.text === "string") return part.text;
          return "";
        }).join("").trim();
      }
      if (typeof response?.text === "string") return response.text.trim();
      return "";
    }

    document.getElementById("run").addEventListener("click", async () => {
      const status = document.getElementById("status");
      window.__mimoResult = { status: "running" };
      status.textContent = "running";
      const started = performance.now();

      try {
        if (!window.puter) throw new Error("Puter.js did not load");

        if (!puter.auth.isSignedIn()) {
          await puter.auth.signIn({ attempt_temp_user_creation: true });
        }

        const user = await puter.auth.getUser();
        const response = await puter.ai.chat("Reply with exactly: MiMo OK", {
          model: "xiaomi/mimo-v2.6-flash"
        });
        const text = extractText(response);
        if (!text) throw new Error("MiMo returned no assistant text");

        window.__mimoResult = {
          status: "passed",
          model: "xiaomi/mimo-v2.6-flash",
          latencyMs: Math.round(performance.now() - started),
          userType: user?.is_temp ? "temporary" : "authenticated",
          output: text.slice(0, 240)
        };
        status.textContent = JSON.stringify(window.__mimoResult);
      } catch (error) {
        window.__mimoResult = {
          status: "failed",
          model: "xiaomi/mimo-v2.6-flash",
          error: String(error?.message || error)
        };
        status.textContent = JSON.stringify(window.__mimoResult);
      }
    });
  </script>
</body>
</html>
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        pass


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="freellm-mimo-live-") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text(HTML, encoding="utf-8")

        handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        url = f"http://127.0.0.1:{server.server_port}/"
        console_lines: list[str] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.on("console", lambda msg: console_lines.append(f"{msg.type}: {msg.text}"))
                page.on("pageerror", lambda err: console_lines.append(f"pageerror: {err}"))

                page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
                page.wait_for_function("() => !!window.puter", timeout=TIMEOUT_MS)
                page.click("#run")
                page.wait_for_function(
                    "() => window.__mimoResult && !['idle', 'running'].includes(window.__mimoResult.status)",
                    timeout=TIMEOUT_MS,
                )
                result = page.evaluate("() => window.__mimoResult")
                browser.close()
        finally:
            server.shutdown()
            server.server_close()

    if result.get("status") != "passed":
        diagnostic = {
            "status": "failed",
            "model": MODEL,
            "error": result.get("error", "unknown browser failure"),
            "console": console_lines[-20:],
        }
        print(json.dumps(diagnostic, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
