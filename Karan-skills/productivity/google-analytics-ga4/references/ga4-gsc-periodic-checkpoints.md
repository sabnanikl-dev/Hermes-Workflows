# GA4 + Search Console periodic checkpoints

Use this pattern for a read-only weekly or milestone observation after an analytics deployment, attribution repair, or site migration.

## Isolation and authority

1. Read the owning issue and last independently accepted checkpoint before collecting anything.
2. If the canonical checkout is dirty or contains unrelated work, preserve it untouched and create a clean, named worktree from the accepted checkpoint commit. Record the original head/status outside the worktree; never reset, stash, or clean unknown WIP.
3. Keep the run read-only: OAuth refresh and report/list/inspection calls are allowed; configuration, sitemap submission, campaign activation, deploys, and public/client sends remain separately gated. If worktree/repository mutation is separately gated, use an isolated local ticket-evidence workspace rather than creating a git worktree. Recover accepted artifacts from their exact commit with `git show <sha>:<path>` when an old temporary worktree is missing/prunable; do not recreate, prune, or repair unrelated worktrees. Label canonical promotion/commit/tracker updates as pending approval.
4. A checkpoint captured before the issue's minimum evidence date is an observation, not closeout—even when the metrics are healthy.

## Freshness and comparison windows

Determine the latest populated date separately for GA4 and GSC from daily date-series probes. Do not force both providers onto one end date: normal processing lag differs.

For each provider, derive from its own latest populated date:

- latest 7 calendar days ending on that provider's latest populated date;
- preceding non-overlapping 7 days;
- latest 14 calendar days and preceding non-overlapping 14 days;
- post-cutover or post-activation window.

Calendar-window completeness is not provider finalization; apply the freshness qualifications below.

Record requested-through date, latest-populated date, and lag. Never fill a missing provider day with an estimate. GA4's latest populated day is not automatically finalized; label yesterday's standard-report rows provisional/subject to processing rather than calling the whole window complete. GSC can explicitly request `dataState: final`. When comparing successive checkpoint headlines, disclose overlapping rolling windows; use the current capture's non-overlapping paired windows for week-over-week claims. Count genuine dated monitoring observations separately from start notices, attribution reconciliations, and synthetic activation proofs—elapsed four weeks does not prove four weekly observations.

### Compare captures without inventing independent weeks

1. Read the prior accepted packet's actual start/end dates rather than assuming a seven-day shift from the scheduled cadence.
2. Compute inclusive overlap in code: `max(0, (min(end_a, end_b) - max(start_a, start_b)).days + 1)`. Report it separately for each provider and window length; a catch-up capture can create different overlaps for GA4 and GSC.
3. When a current window exactly matches a prior window, compare their no-dimension totals directly. Record any difference as a same-window reporting revision before attributing headline movement to new activity; do not silently replace the prior accepted capture.
4. Calculate week-over-week changes from the current capture's paired windows, not from the preceding report's headline. Keep missing or proposed observations explicit instead of backdating them.

## Collector reuse and bounded analysis

1. Inspect the accepted collector plus one saved raw/normalized report before adapting it. Identify the actual window/report wrapper keys and whether normalized dimensions are flat or nested; do not assume an Admin resource such as data streams was collected merely because Data API reports succeeded.
2. Run collection in a new dated workspace. Preserve raw requests/responses, then write a derived summary containing dates, no-dimension totals, paired deltas, overlap, watched-page results and relevant source/event rows. Print that bounded summary rather than entire page bodies or every cross-dimension row; full provenance stays in the packet.
3. Verify row-count/pagination completion and returned sampling, thresholding or data-loss metadata before treating a missing row as zero observed. Preserve unavailable fields as UNKNOWN rather than defaulting them to favorable states.
4. Reconstruct normalized rows from raw headers/values and compare them before report generation. Keep query/page aggregation differences visible rather than forcing dimensional sums to equal property totals.

## OAuth identity truthfulness

Treat API access and caller identity as separate claims. A successful GA4 property report proves that the token can read the property; it does not, by itself, prove which Google user owns the token.

- `tokeninfo` may expose scopes while omitting both email and subject/user ID when the token lacks identity scopes. In that case, record the live caller identity as `UNKNOWN` and keep any expected account/file mapping in a separate `expectedAccount` field—never promote the filename or prior documentation into live identity proof.
- When a paired Google token exposes a verified email and both tokens expose subject IDs, equality can corroborate that they belong to the same Google user. Compare in memory and store only the boolean/verdict; do not persist raw subject IDs.
- If either subject is absent, do not call it a mismatch and do not infer a match. Preserve the limitation explicitly.
- Do not broaden OAuth scopes or reauthorize merely to improve a read-only checkpoint unless that credential change is separately approved.

## GA4 Data API packet

Treat a no-dimension report as the authoritative property total. For every window collect:

- totals: sessions, users, page views, events, key events;
- default channel group;
- session source/medium;
- session campaign + source/medium;
- landing page;
- event name;
- hostname.

Dimensional rows can be non-additive or thresholded; do not sum them to replace property totals. Use hostname rows to look for preview/developer contamination, source rows for self-referrals, and event/page-view relationships only as anomaly signals—not proof of human quality.

For an attribution repair, add a narrow cross-dimension read such as date + session source/medium + landing page (and device category when useful). One ordinary `google / organic` row proves that the repaired path can classify at least one consented session; it does **not** prove complete attribution, explain a traffic spike, or make GA4 equal GSC. If no approved GBP campaign tuple is active or no matching campaign row appears, GBP attribution remains `UNKNOWN`, not zero.

## Search Console packet

Collect separate totals, query rows, and page rows for each window, plus:

- exact property/permission readback;
- submitted sitemap list/readback;
- URL Inspection for the migration watch set;
- explicit `UNKNOWN` for API-inaccessible Crawl Stats and aggregate Page Indexing totals.

Query and page dimensions may be privacy-thresholded and need not reconcile to property totals.

### Aggregation compatibility pitfall

Do not force `aggregationType: byProperty` on every Search Analytics request. Google rejects `BY_PROPERTY` when the request includes the `page` dimension. For a generic collector, omit `aggregationType` and record the API's returned aggregation type, or choose a documented compatible value per dimension. A successful totals query does not prove the same body is valid for page rows.

## Public redirect probe compatibility

Use non-JavaScript GETs for read-only route checks so monitoring does not create synthetic Analytics traffic. Verify the HTTP client handles both 301 and 308 redirects: the host's older Python `urllib` handler may raise `HTTPError: 308` without following it. That is a collector limitation, not a broken production route. Preserve the actual status and Location, use a compatible redirect handler or curl, and rerun before freezing evidence. A sampled redirect matrix does not prove the full inventory or consent behavior. GSC browser login walls remain explicit UI-only coverage gaps; working API access does not imply an authenticated browser session.

## Interpretation and artifact closeout

- Segment clicks versus impressions before calling a search regression.
- Separate GSC Search, consented GA4 traffic, and GBP performance; never blend them into one total.
- Preserve low-volume and traffic-quality uncertainty. Large week-over-week percentages from tiny baselines are observations, not causal growth claims. Quantify concentration when one landing page dominates sessions, then pair its session share with views and key actions; a high-share, near-one-view, zero-action spike is a watch item, not customer-growth proof.
- When clicks and impressions both decline, honor the investigation guardrail. Fresh passing URL Inspection, aligned canonicals, a healthy sitemap, and successful public retrieval can rule out an obvious watched-surface indexing outage, but they do not erase the performance decline; classify it as a bounded watch condition until another comparable, sufficiently mature window confirms or refutes it. If the latest week declines while the paired fortnight improves, state both signals explicitly rather than collapsing them into a single recovery or regression verdict.
- Distinguish an inspection retrieval timestamp from Google's returned `lastCrawlTime`. Compare stored crawl dates with the prior packet; a successful fresh inspection read does not prove a page was recrawled today.
- Store raw machine evidence as JSON and the decision narrative as Markdown. Verify JSON parsing, metric parity, watch-set counts, no-secret markers, and report/hash consistency.
- Commit only the checkpoint artifacts in the isolated worktree if local commit authority is in scope. Push only when explicitly approved.
- Add the tracker comment by captured comment ID and read it back directly. Keep weekly metrics out of durable wiki pages; promote only enduring measurement rules or stable architecture changes.
