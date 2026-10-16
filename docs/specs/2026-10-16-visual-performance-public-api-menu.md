# Visual, Navigation, and Public API Directory Update

## Goals

- Keep primary menu navigation on the current document so route changes replace the right-side page content without reloading the shared rail.
- Restore the October 15 Public API directory and its seven reviewed detail pages, data, styles, scripts, links, and sitemap entries from `origin/main`.
- Add a left-rail `公益站` entry targeting `/public-api/` and include that route in the existing navigation lifecycle.
- Retain the previously approved homepage-only hero compression.
- Improve perceived navigation speed only where inspection identifies an avoidable wait or repeated resource load; preserve browser history, focus/accessibility, and full-load fallback for unsupported routes.

## Constraints and assumptions

- The checkout is based on October 9 `main`; fetched `origin/main` is October 15 and contains the missing directory.
- The working tree has roughly 400 pre-existing modified files. Preserve them; do not merge or reset the entire branch as part of this task.
- The current Public API page is static HTML and has its own styles and filtering script. The existing navigation code already fetches supported routes and preserves shared navigation.
- The shared menu is rendered both by `js/site-navigation.js` and the static shell builders in `scripts/build_static.py` and `scripts/build_seo_pages.py`; reviewed pages are emitted by `scripts/build_public_api_reviews.cjs`.
- Only the homepage hero has an approved visual change. This task does not redesign every page.
- No deployment or push is included.

## Chosen approach

Port the directory's October 15 data, styles, filtering script, directory page, seven review pages, and review-page generator into the current checkout. Exclude the optional monitoring/probing workflow and history automation because the user asked to restore visible page content, not background monitoring. Add `/public-api/` to the client menu, static shell builders, and the SPA route map; mark the directory and review pages as the `public-api` section so the menu state stays correct. The review detail links remain ordinary content navigation; selecting the global `公益站` menu always opens `/public-api/` without a full-page reload. Keep the established static site and navigation code; do not introduce a routing dependency or rewrite the site shell. Keep the existing 240px homepage desktop hero target and compressed mobile treatment.

For performance, inspect the existing fetch, stylesheet reuse, and script mounting sequence. Avoid loading already-present assets twice and avoid waiting on non-critical resources beyond the current bounded stylesheet wait. Do not remove page initialization or fallback behavior for the sake of a superficial speed score.

## Alternatives considered

1. Fast-forward the entire checkout to October 15 `origin/main`. This would bring in 351 commits while 400+ local files are modified, creating a broad conflict surface unrelated to this request.
2. Restore only a homepage link to the directory. This would leave the reviewed directory/detail content absent and would not satisfy the requested global menu.

The selected targeted port keeps the change scoped and preserves the working tree while restoring the complete feature family.

## Failure modes and safeguards

- A menu link exists but SPA route allowlists omit `/public-api/`: add the route key/path, active-state mapping, static-shell entries, and review-page generator output together.
- The route loads but directory filtering breaks after SPA navigation: preserve and execute the page script at mount; keep the native links/forms usable without JavaScript.
- Rapid clicks or back/forward leave stale styles or route state: retain request cancellation, route guards, and history handling; manually exercise menu switches and history in a browser if available.
- The large dirty tree masks unrelated edits: restrict edits to the navigation/build sources, homepage hero styles, and files needed by the Public API feature; inspect the final changed-file list before finishing.
- A slow stylesheet blocks transitions: retain a bounded wait and ensure failed/late stylesheet loads cannot deadlock navigation.

## Verification plan

- Inspect route wiring, generated shell consistency, static links, and changed-file scope.
- Run only focused local checks if needed to validate the implementation; do not deploy or push.
- Manually navigate Home → Public API → another menu route → Back/Forward, checking that the rail persists and the directory filter initializes.
- Compare homepage hero height at desktop and mobile widths.

## Out of scope

- Syncing all 351 remote commits, redesigning all routes, changing the site's content policy, or deploying the result.
