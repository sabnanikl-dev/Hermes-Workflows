# Facebook Marketplace Local Product Research

Use for one-time local sourcing checks on Facebook Marketplace when the user provides a product shortlist, shopping sheet, target price bands, and a radius.

## Workflow

1. **Recover the exact buy criteria first.** Read the source sheet/local backup or prior session context. Normalize each tier into model, capacity, form factor/interface, allowed substitutes, price band, condition, and priority order. Do not silently broaden an exact-model tier.
2. **Use a lean deterministic search pipeline for live inventory.** When the user shares a monitoring/scraping repository for a one-off task, first borrow its architecture—URL construction, bulk DOM extraction, filtering, caching, and deduplication—rather than assuming the full product should be installed. A public Marketplace search page may remain usable after closing the login modal. Search every exact recommended model first, then the allowed budget and premium alternatives.
3. **Start broad enough to preserve relevant inventory.** For an initial one-time pass, use the exact model phrase plus location/radius and local pickup, while leaving Facebook on its suggested/all-results behavior. Newest sorting combined with server-side price filters can suppress an older relevant listing and return noisy cards. Enforce model and price bands locally; reserve newest/date-limited searches for incremental follow-up passes.
4. **Set and verify the radius in the rendered UI.** Marketplace's `radius` URL value can behave as kilometres even when the UI displays miles. For a 30-mile search, `radius=48` produced `Within 30 mi`; always read the rendered filter text rather than trusting the URL parameter. Treat this as live behavior to re-check, not a permanent conversion rule.
5. **Extract the rendered result cards in bulk.** Load each search page once, then use browser DOM inspection for anchors containing `/marketplace/item/`; collect card text and canonical URLs before opening candidates. Strip query parameters and deduplicate by listing ID across search phrases. Search snippets are discovery only.
6. **Reject non-local noise with local validation.** Facebook can inject distant suggestions even while the sidebar says `Within 30 mi`. Exclude `Ships to you`, `Partner listing`, sold/unavailable pages, unrelated accessories/HDDs/SATA drives, ambiguous capacities/models, and clearly distant cities. When a candidate sits near a hard radius boundary, verify its approximate distance independently and label it borderline rather than treating the sidebar as proof.
6. **Open each promising listing and verify:** current displayed price, exact model/capacity, condition, listed age, location, description, and whether the listing still exposes Message/Save controls. Prefer exact model numbers. If title and description prices disagree, report the displayed current price and flag the stale description.
7. **Classify instead of mixing:**
   - qualifying matches inside the source price band;
   - exact-model near-misses above/below the band;
   - ambiguous listings that require photo/model-number confirmation.
8. **Return direct canonical listing links.** Include only a short reason each listing qualifies and a concise risk note.

## SSD-specific verification

For used/open-box NVMe drives, recommend asking for:
- CrystalDiskInfo, smartctl, or DriveDx SMART screenshot;
- total host writes, power-on hours, health percentage, and critical warnings;
- clear label/model-number photo and proof of purchase when warranty matters.

Treat seller-selected `New` cautiously when the prose says “very good condition,” “barely used,” or similar. Flag the inconsistency rather than resolving it in the seller's favor.

## Tool strategy

- Classify a shared repository's intended role before acting:
  - **Architecture/reference intent:** borrow the smallest useful search/extraction pattern for the current task.
  - **Deployment intent:** install or operate the full tool only when the user explicitly asks for recurring monitoring or setup.
- A rendered browser is still generally required because Marketplace is dynamic, but this does not justify click-by-click automation. Prefer one load per search phrase, one bulk DOM extraction, and detail navigation only for shortlisted candidates.
- A normal browser session is sufficient for a one-time check; do not install a monitoring project unnecessarily or pivot into Docker, credentials, notifications, and daemon setup merely because the repository supports them.
- Search-engine `site:facebook.com/marketplace/item/` results can supplement discovery but may expose sold or stale pages; direct rendered-page verification wins.
- `web_extract` may not support Facebook. Fall back to browser rendering rather than converting that provider limitation into a general rule.
- Do not enter credentials, solve CAPTCHA, or automate account login without explicit approval. Do not build evasion around platform controls.
- If source code—not just architectural ideas—will be copied, inspect and respect the upstream license first.
- For recurring monitoring, evaluate a dedicated monitor separately, including login/session handling, privacy, notification deduplication, and Marketplace terms/rate-limit risk.

## Output shape

Lead with verified matches and links. Then add a small `Near misses` section only when useful. State the checked time and that the rendered radius filter was verified. Do not dump the full raw search result set.