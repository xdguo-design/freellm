# SEO checks and daily update archive repair

## Goal

Restore reliable SEO regression checks after syncing `dev` with the latest remote branch, and ensure daily update history retains the detailed registration and source information already assembled by the renderer.

## Current findings

- `/models/center/` and `/skills/lab/` are legacy routes that intentionally redirect to `/models/` and `/workflow/`, respectively. `/skills/` remains an indexable directory. Tests still expect the redirect routes to be indexable pages.
- The generated sitemap correctly includes the generated `/health/` page, but the test's explicit static URL set omits it.
- The SiliconFlow catalog now contains seven free model entries; the test still assumes six.
- LongCat copy has changed while its test still asserts the previous wording.
- `render_daily_log_page` builds per-day detail sections, but the final page currently inserts only the new reference modules and a summary archive, dropping those detail sections.
- The SEO generator check finds 77 generated pages stale against the current generator and catalog data.
- The full suite also exposed access-card records missing for four catalog models, an active Puter model whose provider is absent from the provider catalog, and latency coverage that predates seven catalog providers.
- The featured-offer checker compares serialized bytes, so Windows line endings and formatting make unchanged data appear stale; its homepage test checks the static fallback instead of the JavaScript-rendered offer card.
- The About page does not disclose the ranking weights now used by the catalog, and the canonical URL test scans a local Chrome extension profile as if it were public site content.

## Decision

Keep current redirects, catalog facts, and the redesigned update overview. Update regression checks to cover the current route and data contracts. Place the existing per-day detail sections inside an expandable full-history archive so registration steps, evidence, and source links remain available without duplicating them in the overview. Regenerate checked-in SEO output from the current generator and catalog so the CI freshness check matches the same source of truth. Complete catalog access metadata with explicitly unverified records where evidence is absent, preserve only real latency measurements, disclose the configured ranking method on the About page, and keep local browser artifacts outside the published-page scan.

## Acceptance checks

- `/skills/` is tested as an indexable directory; `/models/center/` and `/skills/lab/` are tested as noindex redirects to their canonical destinations, and replacement pages carry indexable crawler and social metadata.
- Sitemap assertions include every generated indexable URL, including `/health/`.
- Catalog tests validate the current seven SiliconFlow model entries and current LongCat access wording.
- Every active provider/model has a corresponding access record; missing measurements remain explicitly unknown rather than fabricated.
- The homepage feature test checks the runtime script that hydrates the static fallback, and featured-offer check mode compares data semantics independent of JSON formatting.
- The About page's ranking weights and scoring description match the checked-in ranking configuration and implementation.
- Canonical URL scans exclude local browser profiles while still covering every published page.
- The update overview remains present, while expanding full history exposes event cards, registration guidance, sources, and health data for each day.
- The complete pytest suite, SEO generated-output check, and static page build check pass.
