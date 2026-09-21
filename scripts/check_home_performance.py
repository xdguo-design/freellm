from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import tarfile
import tempfile
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = os.environ.get("FREELLM_PERF_BASELINE", "1bb5a89cadd2a55b4e775e15e8ad42aff3996411")
PUBLIC_URL = os.environ.get("FREELLM_PERF_URL", "https://freellm.top/")
MOBILE_VIEWPORT = {"width": 390, "height": 844}
RUNS = 2

INIT_SCRIPT = r"""
(() => {
  window.__perfProbe = { lcp: 0, cls: 0, longTasks: [] };
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) {
        window.__perfProbe.lcp = Math.max(window.__perfProbe.lcp, e.startTime || e.renderTime || e.loadTime || 0);
      }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (_) {}
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) {
        if (!e.hadRecentInput) window.__perfProbe.cls += e.value || 0;
      }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (_) {}
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) window.__perfProbe.longTasks.push(e.duration || 0);
    }).observe({ type: 'longtask', buffered: true });
  } catch (_) {}
})();
"""


class PerfHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        return

    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=0, must-revalidate")
        super().end_headers()


class LocalSite:
    def __init__(self, root: Path):
        handler = partial(PerfHandler, directory=str(root))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}/design/free-china-ai-index.html"

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def archive_baseline(destination: Path) -> None:
    tar_path = destination / "baseline.tar"
    paths = [
        "design/free-china-ai-index.html",
        "design/assets",
        "css/freellm-pastel-ui.css",
        "js/freellm-sync.js",
        "data/offers.json",
        "data/community-signals.json",
    ]
    with tar_path.open("wb") as handle:
        subprocess.run(
            ["git", "archive", "--format=tar", BASELINE_COMMIT, *paths],
            cwd=ROOT,
            stdout=handle,
            check=True,
        )
    with tarfile.open(tar_path) as archive:
        archive.extractall(destination / "baseline")


def read_metrics(page) -> dict:
    return page.evaluate(
        r"""() => {
          const nav = performance.getEntriesByType('navigation')[0];
          const paint = Object.fromEntries(performance.getEntriesByType('paint').map(e => [e.name, e.startTime]));
          const origin = location.origin;
          const resources = performance.getEntriesByType('resource').filter(r => r.name.startsWith(origin));
          const important = resources
            .filter(r => /homepage|freellm-pastel-ui|freellm-sync|offers\.(json|js)/.test(r.name))
            .map(r => ({
              name: new URL(r.name).pathname,
              duration: Math.round(r.duration),
              transferSize: r.transferSize,
              encodedBodySize: r.encodedBodySize,
              responseStart: Math.round(r.responseStart),
              responseEnd: Math.round(r.responseEnd),
            }));
          const p = window.__perfProbe || { lcp: 0, cls: 0, longTasks: [] };
          return {
            fcp: Math.round(paint['first-contentful-paint'] || 0),
            lcp: Math.round(p.lcp || 0),
            cls: Number((p.cls || 0).toFixed(4)),
            ttfb: Math.round(nav?.responseStart || 0),
            domContentLoaded: Math.round(nav?.domContentLoadedEventEnd || 0),
            load: Math.round(nav?.loadEventEnd || 0),
            navTransferSize: nav?.transferSize || 0,
            resourceTransferSize: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
            resourceEncodedSize: resources.reduce((sum, r) => sum + (r.encodedBodySize || 0), 0),
            requests: resources.length,
            longTaskCount: p.longTasks.length,
            longTaskTotal: Math.round(p.longTasks.reduce((sum, value) => sum + value, 0)),
            dataSource: document.body?.dataset?.dataSource || null,
            horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
            important,
          };
        }"""
    )


def measure_once(browser, site: LocalSite) -> dict:
    context = browser.new_context(
        viewport=MOBILE_VIEWPORT,
        is_mobile=True,
        device_scale_factor=3,
        locale="zh-CN",
    )
    context.add_init_script(INIT_SCRIPT)
    page = context.new_page()
    page.route(
        "**/*",
        lambda route: route.continue_()
        if route.request.url.startswith(site.origin)
        else route.fulfill(status=204, body=""),
    )
    cdp = context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 150,
            "downloadThroughput": 1.6 * 1024 * 1024 / 8,
            "uploadThroughput": 750 * 1024 / 8,
            "connectionType": "cellular3g",
        },
    )
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})

    page.goto(site.url, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_function("document.body && document.body.dataset.dataSource", timeout=20_000)
    page.wait_for_timeout(800)
    cold = read_metrics(page)

    page.reload(wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_function("document.body && document.body.dataset.dataSource", timeout=20_000)
    page.wait_for_timeout(800)
    warm = read_metrics(page)
    context.close()
    return {"cold": cold, "warm": warm}


def median_profile(samples: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for phase in ("cold", "warm"):
        rows = [sample[phase] for sample in samples]
        numeric = [
            "fcp",
            "lcp",
            "cls",
            "ttfb",
            "domContentLoaded",
            "load",
            "navTransferSize",
            "resourceTransferSize",
            "resourceEncodedSize",
            "requests",
            "longTaskCount",
            "longTaskTotal",
        ]
        out[phase] = {key: statistics.median(row[key] for row in rows) for key in numeric}
        out[phase]["dataSource"] = rows[-1]["dataSource"]
        out[phase]["horizontalOverflow"] = any(row["horizontalOverflow"] for row in rows)
        out[phase]["important"] = rows[-1]["important"]
    return out


def fetch_remote(url: str, etag: str | None = None) -> dict:
    headers = {"User-Agent": "FreeLLM-performance-probe/1.0", "Accept-Encoding": "gzip, br"}
    if etag:
        headers["If-None-Match"] = etag
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read()
            return {
                "status": response.status,
                "body": body,
                "headers": {k.lower(): v for k, v in response.headers.items()},
            }
    except urllib.error.HTTPError as error:
        return {
            "status": error.code,
            "body": error.read(),
            "headers": {k.lower(): v for k, v in error.headers.items()},
        }


def remote_cache_probe() -> dict:
    result: dict = {"url": PUBLIC_URL, "available": False, "assets": {}}
    try:
        home = fetch_remote(PUBLIC_URL)
        if home["status"] != 200:
            result["error"] = f"homepage returned {home['status']}"
            return result
        result["available"] = True
        local_home = (ROOT / "design" / "free-china-ai-index.html").read_bytes()
        result["homepageMatchesDev"] = hashlib.sha256(home["body"]).hexdigest() == hashlib.sha256(local_home).hexdigest()
        decoded = home["body"].decode("utf-8", errors="replace")
        result["homepageSplitRefs"] = all(
            needle in decoded for needle in ("homepage.css", "homepage.js")
        )
        for path in (
            "css/homepage.css",
            "css/homepage-editorial.css",
            "js/homepage.js",
            "js/homepage-i18n.js",
            "data/offers.json",
        ):
            url = PUBLIC_URL.rstrip("/") + "/" + path
            first = fetch_remote(url)
            headers = first["headers"]
            etag = headers.get("etag")
            second = fetch_remote(url, etag=etag) if etag else fetch_remote(url)
            result["assets"][path] = {
                "firstStatus": first["status"],
                "revalidateStatus": second["status"],
                "cacheControl": headers.get("cache-control"),
                "etag": etag,
                "age": headers.get("age"),
                "xVercelCache": headers.get("x-vercel-cache"),
                "contentEncoding": headers.get("content-encoding"),
                "contentLength": headers.get("content-length"),
            }
    except Exception as error:
        result["error"] = repr(error)
    return result


def main() -> int:
    current_path = ROOT / "design" / "free-china-ai-index.html"
    current_size = current_path.stat().st_size
    current_html = current_path.read_text(encoding="utf-8")
    if current_size > 100_000:
        raise SystemExit(f"homepage HTML budget exceeded: {current_size} bytes")
    for ref in ("../css/homepage.css", "../js/homepage.js"):
        if ref not in current_html:
            raise SystemExit(f"split homepage reference missing: {ref}")

    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        archive_baseline(temp)
        baseline_root = temp / "baseline"
        baseline_site = LocalSite(baseline_root)
        current_site = LocalSite(ROOT)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                baseline_samples = [measure_once(browser, baseline_site) for _ in range(RUNS)]
                current_samples = [measure_once(browser, current_site) for _ in range(RUNS)]
                browser.close()
        finally:
            baseline_site.close()
            current_site.close()

    baseline = median_profile(baseline_samples)
    current = median_profile(current_samples)
    comparison = {}
    for phase in ("cold", "warm"):
        comparison[phase] = {}
        for metric in (
            "fcp",
            "lcp",
            "domContentLoaded",
            "load",
            "navTransferSize",
            "resourceTransferSize",
            "resourceEncodedSize",
            "requests",
            "longTaskTotal",
        ):
            before = baseline[phase][metric]
            after = current[phase][metric]
            comparison[phase][metric] = {
                "before": before,
                "after": after,
                "delta": round(after - before, 3),
                "ratio": round(after / before, 3) if before else None,
            }

    report = {
        "baselineCommit": BASELINE_COMMIT,
        "mobileProfile": {
            "viewport": MOBILE_VIEWPORT,
            "latencyMs": 150,
            "downloadMbps": 1.6,
            "cpuThrottle": 4,
            "runs": RUNS,
            "thirdPartyRequests": "blocked for deterministic first-party comparison",
        },
        "files": {
            "baselineHtmlBytes": len(
                subprocess.check_output(
                    ["git", "show", f"{BASELINE_COMMIT}:design/free-china-ai-index.html"],
                    cwd=ROOT,
                )
            ),
            "currentHtmlBytes": current_size,
            "homepageCssBytes": (ROOT / "css" / "homepage.css").stat().st_size,
            "homepageEditorialCssBytes": (ROOT / "css" / "homepage-editorial.css").stat().st_size,
            "homepageJsBytes": (ROOT / "js" / "homepage.js").stat().st_size,
            "homepageI18nJsBytes": (ROOT / "js" / "homepage-i18n.js").stat().st_size,
            "offersJsonBytes": (ROOT / "data" / "offers.json").stat().st_size,
        },
        "baseline": baseline,
        "current": current,
        "comparison": comparison,
        "remoteCache": remote_cache_probe(),
    }
    print("HOME_PERFORMANCE_REPORT=" + json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if current["cold"]["horizontalOverflow"] or current["warm"]["horizontalOverflow"]:
        raise SystemExit("mobile horizontal overflow detected")
    if current["cold"]["fcp"] > baseline["cold"]["fcp"] * 1.35:
        raise SystemExit("cold mobile FCP regressed by more than 35%")
    if current["cold"]["lcp"] > baseline["cold"]["lcp"] * 1.35:
        raise SystemExit("cold mobile LCP regressed by more than 35%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
