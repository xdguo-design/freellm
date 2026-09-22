from __future__ import annotations

import json
import re
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_URL = "https://freellm.top/"
VIEWPORT = {"width": 390, "height": 844}
RUNS = 2

INIT_SCRIPT = r"""
(() => {
  window.__prodPerf = { lcp: 0, cls: 0, longTasks: [] };
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) {
        window.__prodPerf.lcp = Math.max(
          window.__prodPerf.lcp,
          e.startTime || e.renderTime || e.loadTime || 0
        );
      }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (_) {}
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) {
        if (!e.hadRecentInput) window.__prodPerf.cls += e.value || 0;
      }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (_) {}
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) window.__prodPerf.longTasks.push(e.duration || 0);
    }).observe({ type: 'longtask', buffered: true });
  } catch (_) {}
})();
"""


def fetch(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FreeLLM-production-performance-probe/1.0",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return {
                "status": response.status,
                "body": response.read(),
                "headers": {key.lower(): value for key, value in response.headers.items()},
            }
    except urllib.error.HTTPError as error:
        return {
            "status": error.code,
            "body": error.read(),
            "headers": {key.lower(): value for key, value in error.headers.items()},
        }


def expected_assets() -> list[str]:
    html = (ROOT / "design" / "free-china-ai-index.html").read_text(encoding="utf-8")
    assets = re.findall(
        r'(?:href|src)="\.\./((?:css|js)/homepage(?:-editorial|-i18n)?\.[0-9a-f]{10}\.(?:css|js))"',
        html,
    )
    if len(assets) != 4:
        raise SystemExit(f"expected four fingerprinted homepage assets, found {assets}")
    return assets


def wait_for_live_release(assets: list[str]) -> dict:
    last: dict | None = None
    for _ in range(24):
        home = fetch(PUBLIC_URL)
        last = home
        if home["status"] == 200:
            text = home["body"].decode("utf-8", errors="replace")
            if all(asset in text for asset in assets):
                return home
        time.sleep(5)
    status = last["status"] if last else "no response"
    raise SystemExit(f"production homepage did not publish expected assets; last status={status}")


def cache_probe(home: dict, assets: list[str]) -> dict:
    result = {
        "homepage": {
            "status": home["status"],
            "cacheControl": home["headers"].get("cache-control"),
            "xVercelCache": home["headers"].get("x-vercel-cache"),
            "age": home["headers"].get("age"),
            "etag": home["headers"].get("etag"),
        },
        "assets": {},
    }
    for path in [*assets, "data/offers.json"]:
        first = fetch(PUBLIC_URL + path)
        second = fetch(PUBLIC_URL + path)
        result["assets"][path] = {
            "status": second["status"],
            "cacheControl": second["headers"].get("cache-control"),
            "xVercelCache": second["headers"].get("x-vercel-cache"),
            "age": second["headers"].get("age"),
            "etag": second["headers"].get("etag"),
            "encoding": second["headers"].get("content-encoding"),
            "firstCache": first["headers"].get("x-vercel-cache"),
        }
    return result


def read_metrics(page) -> dict:
    return page.evaluate(
        r"""() => {
          const nav = performance.getEntriesByType('navigation')[0];
          const paint = Object.fromEntries(
            performance.getEntriesByType('paint').map(e => [e.name, e.startTime])
          );
          const resources = performance.getEntriesByType('resource');
          const firstParty = resources.filter(r => new URL(r.name).hostname === location.hostname);
          const thirdParty = resources.filter(r => new URL(r.name).hostname !== location.hostname);
          const tracked = resources
            .filter(r => /homepage|offers\.json|freellm-pastel-ui|freellm-sync/.test(r.name))
            .map(r => ({
              name: new URL(r.name).pathname,
              host: new URL(r.name).hostname,
              duration: Math.round(r.duration),
              transferSize: r.transferSize || 0,
              encodedBodySize: r.encodedBodySize || 0,
              responseEnd: Math.round(r.responseEnd || 0),
            }));
          const p = window.__prodPerf || { lcp: 0, cls: 0, longTasks: [] };
          return {
            fcp: Math.round(paint['first-contentful-paint'] || 0),
            lcp: Math.round(p.lcp || 0),
            cls: Number((p.cls || 0).toFixed(4)),
            ttfb: Math.round(nav?.responseStart || 0),
            domContentLoaded: Math.round(nav?.domContentLoadedEventEnd || 0),
            load: Math.round(nav?.loadEventEnd || 0),
            navTransferSize: nav?.transferSize || 0,
            firstPartyRequests: firstParty.length,
            thirdPartyRequests: thirdParty.length,
            firstPartyTransferSize: firstParty.reduce((n, r) => n + (r.transferSize || 0), 0),
            thirdPartyTransferSize: thirdParty.reduce((n, r) => n + (r.transferSize || 0), 0),
            longTaskCount: p.longTasks.length,
            longTaskTotal: Math.round(p.longTasks.reduce((n, value) => n + value, 0)),
            dataSource: document.body?.dataset?.dataSource || null,
            horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
            tracked,
          };
        }"""
    )


def measure_once(browser) -> dict:
    context = browser.new_context(
        viewport=VIEWPORT,
        is_mobile=True,
        device_scale_factor=3,
        locale="zh-CN",
        user_agent=(
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/153.0.0.0 Mobile Safari/537.36"
        ),
    )
    context.add_init_script(INIT_SCRIPT)
    page = context.new_page()
    cdp = context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 150,
            "downloadThroughput": 1.6 * 1024 * 1024 / 8,
            "uploadThroughput": 750 * 1024 / 8,
            "connectionType": "cellular4g",
        },
    )
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})

    page.goto(PUBLIC_URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_function("document.body && document.body.dataset.dataSource", timeout=30_000)
    page.wait_for_timeout(1200)
    cold = read_metrics(page)

    page.goto("about:blank")
    page.goto(PUBLIC_URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_function("document.body && document.body.dataset.dataSource", timeout=30_000)
    page.wait_for_timeout(1200)
    warm = read_metrics(page)

    context.close()
    return {"cold": cold, "warm": warm}


def median_profile(samples: list[dict]) -> dict:
    output: dict[str, dict] = {}
    numeric = (
        "fcp",
        "lcp",
        "cls",
        "ttfb",
        "domContentLoaded",
        "load",
        "navTransferSize",
        "firstPartyRequests",
        "thirdPartyRequests",
        "firstPartyTransferSize",
        "thirdPartyTransferSize",
        "longTaskCount",
        "longTaskTotal",
    )
    for phase in ("cold", "warm"):
        rows = [sample[phase] for sample in samples]
        output[phase] = {
            key: statistics.median(row[key] for row in rows)
            for key in numeric
        }
        output[phase]["dataSource"] = rows[-1]["dataSource"]
        output[phase]["horizontalOverflow"] = any(row["horizontalOverflow"] for row in rows)
        output[phase]["tracked"] = rows[-1]["tracked"]
    return output


def main() -> int:
    assets = expected_assets()
    home = wait_for_live_release(assets)
    cache = cache_probe(home, assets)

    for path in assets:
        policy = cache["assets"][path]["cacheControl"] or ""
        if "max-age=31536000" not in policy or "immutable" not in policy:
            raise SystemExit(f"immutable cache policy missing on production asset {path}: {policy}")
    offers_policy = cache["assets"]["data/offers.json"]["cacheControl"] or ""
    if "max-age=300" not in offers_policy:
        raise SystemExit(f"offers.json short cache policy missing: {offers_policy}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        samples = [measure_once(browser) for _ in range(RUNS)]
        browser.close()

    profile = median_profile(samples)
    report = {
        "url": PUBLIC_URL,
        "mobileProfile": {
            "viewport": VIEWPORT,
            "latencyMs": 150,
            "downloadMbps": 1.6,
            "cpuThrottle": 4,
            "runs": RUNS,
            "thirdPartyRequests": "included",
        },
        "cache": cache,
        "performance": profile,
    }
    print("PUBLIC_HOME_PERFORMANCE_REPORT=" + json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if profile["cold"]["horizontalOverflow"] or profile["warm"]["horizontalOverflow"]:
        raise SystemExit("production mobile horizontal overflow detected")

    warm = {item["name"]: item for item in profile["warm"]["tracked"]}
    missed = [
        "/" + path
        for path in assets
        if warm.get("/" + path, {}).get("transferSize", 1) != 0
    ]
    if missed:
        raise SystemExit(f"production fingerprinted assets missed browser cache: {missed}")

    warm_offer = warm.get("/data/offers.json", {})
    warm_offer_transfer = warm_offer.get("transferSize", 0)
    warm_offer_body = warm_offer.get("encodedBodySize", 0)
    if warm_offer_transfer > 1024 or warm_offer_body <= 0:
        raise SystemExit(
            "production offers.json did not use browser cache or conditional revalidation "
            f"(transfer={warm_offer_transfer}, body={warm_offer_body})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
