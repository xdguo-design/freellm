# FreeLLM UI/UX + performance audit remediation · 2026-10-09

**Scope:** Home, Models, Skills, Tools, Workflow, Updates, About, category pages.  
**Source:** User-provided desktop/mobile audit, cross-checked with `dev` source.  
**Rules:** Keep FACT / INFERENCE / UNKNOWN separate; always ship and validate on `dev` before requesting a `main` release. `vercel.json` disables automatic `dev` deployment.

## Confirmed facts

- Workflow topbar search sits inside `.ref-topbar`; multiple style sheets use transparent backgrounds and conflicting `!important` rules.
- Workflow hero mobile clipping was caused by fixed height and `white-space:nowrap!important` in prototype styles.
- `/updates/` had no Vercel redirect. Shared navigation already linked `/logs/` in `dev`, so add compatibility redirect rather than blindly rewriting correct links.
- `/models/all/` already has server-side pagination: `MODELS_PER_PAGE = 26` in `scripts/build_seo_pages.py`. Treat the report's “no pagination” statement as a production/stale-build observation, not proof of a missing `dev` feature.
- PhanthyCode previously existed only in `data/review-queue.json` and editorial notes. It is now listed in `data/daily-log/2026-10-09.json`, and `dev` `logs/index.html` includes the item.
- Oct 9 is a curated-only discovery date. Automatic scan data is last from Oct 8. The generated `data/scan-summary.json` preserves the latest scan counts and flags `scanRunToday=false`.

## Work items and status

| ID | Issue | Status on dev | Acceptance |
| --- | --- | --- | --- |
| P0-1 | Workflow search / eyebrow overlap | Code fixed; browser QA outstanding | Search input stays opaque and readable while scrolling and on small screens |
| P0-2 | Mobile workflow hero clipping | Code fixed; browser QA outstanding | Entire heading visible at 320, 375, 390 and 750 px without horizontal overflow |
| P0-3 | /updates/ dead link | Redirects committed; deployed QA outstanding | /updates and /updates/ permanently redirect to /logs/; English routes also covered |
| DATA-10-09 | PhanthyCode not in web updates | Dev source + rendered HTML available; not on production | /logs/ displays dated, official-source-backed pending-verification item with no API claim |
| P1-4 | Slow long lists / oversized homepage | OPEN; model pagination existed already | Home initial DOM and JSON footprint reduced; no loss of filter/search functionality |
| P1-5 | Home first-screen overload | OPEN | One clear search CTA; other modules follow without losing useful stats |
| P1-6 | Inconsistent headers and side rails | OPEN | Shared responsive shell across home, models, category, tools, skills, workflow, logs, about |
| P1-7 | Card/grid inconsistencies | OPEN | Common tokens, summary clamp, maximum visible tags, aligned actions |
| P1-8 | Decorative hero collision | Workflow guarded; other pages OPEN | Decorations never obstruct interactive content or clip essential text |
| P1-9 | Mobile topbar crowding | OPEN | Primary actions touch-accessible, secondary actions consolidated |
| P1-10 | Mobile tools category chip wall | CSS fix on dev; browser QA outstanding | Single horizontally scrolling row, no massive first-screen wrap |
| P1-11 | Mobile stats density | OPEN | 2×2 or horizontal compact stats with legible numerals |
| P2-12 | Chinese/English visual noise | OPEN | Decorative copy de-emphasized in Chinese locale |
| P2-13 | Category-page visual drift | OPEN | Shares topbar and side rail geometry with primary sections |
| P2-14 | Red dot always on | Unread state in JS; browser QA outstanding | Red dot only for new unvisited daily changes, disappears after visiting |
| P2-15 | Fonts / AdSense overhead | OPEN | Verify network waterfall and policy-safe lazy strategies |
| P2-16 | Excessive home length | OPEN | Measure post-list improvements, collapse or link lower-priority modules |

## Verification performed

- Static checks (11/11): redirect mapping, CSS selector priority, mobile heading wrap, mobile tools category overflow, red-dot read state, JS syntax parse, curated event and scan provenance, generated dev log HTML presence, 26-row model pagination, regression test file existence.
- Added `tests/test_ux_20261009_regressions.py`. No claim of full CI or 1920×900 / 390×844 browser visual regression passes yet.
- Live production `/logs/` currently remains on Oct 8 (verified 2026-10-09). This is expected until an approved `main` deployment; do not mark production resolved.

## Next implementation sequence

1. Run live local/browser screenshots at desktop 1920×900 and phone widths 320/375/390/750; verify P0 and the new chip scroller. Fix regressions before any main merge.
2. Address homepage DOM footprint and runtime 74-card render through an incremental list strategy with filtering/search/sort preservation; do not repeat already-present model pagination.
3. Consolidate shell/layout tokens across section generators and CSS sources, then mobile CTA and language menu.
4. Defer ad scheduling changes until consent, AdSense policy and Core Web Vitals implications are validated.
5. Release dev-tested changes to main only after passing build checks and smoke tests.

## Source trail

- `css/primary-menu.css`, `js/site-navigation.js`, `vercel.json`
- `data/daily-log/2026-10-09.json`, `data/scan-summary.json`, `scripts/build_seo_pages.py`
- `logs/index.html`, `tests/test_ux_20261009_regressions.py`
