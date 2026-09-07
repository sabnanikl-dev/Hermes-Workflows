# GA4 + Search Console periodic checkpoints

Use this pattern for a read-only weekly or milestone observation after an analytics deployment, attribution repair, or site migration.

## Isolation and authority

1. Read the owning issue and last independently accepted checkpoint before collecting anything.
2. If the canonical checkout is dirty or contains unrelated work, preserve it untouched and create a clean, named worktree from the accepted checkpoint commit. Record the original head/status outside the worktree; never reset, stash, or clean unknown WIP.
3. Keep the run read-only: OAuth refresh and report/list/inspection calls are allowed; configuration, sitemap submission, campaign activation, deploys, and public/client sends remain separately gated.
4. A checkpoint captured before the issue's minimum evidence date is an observation, not closeout—even when the metrics are healthy.

## Freshness and comparison windows

Determine the latest populated date separately for GA4 and GSC from daily date-series probes. Do not force both providers onto one end date: normal processing lag differs.

For each provider, derive from its own latest populated date:

- latest 7 complete days;
- preceding 7 days;
- latest 14 days;
- post-cutover or post-activation window.

Record requested-through date, latest-populated date, and lag. Never fill a missing provider day with an estimate.

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

## Interpretation and artifact closeout

- Segment clicks versus impressions before calling a search regression.
- Separate GSC Search, consented GA4 traffic, and GBP performance; never blend them into one total.
- Preserve low-volume and traffic-quality uncertainty. Large week-over-week percentages from tiny baselines are observations, not causal growth claims. Quantify concentration when one landing page dominates sessions, then pair its session share with views and key actions; a high-share, near-one-view, zero-action spike is a watch item, not customer-growth proof.
- When clicks and impressions both decline, honor the investigation guardrail. Fresh passing URL Inspection, aligned canonicals, a healthy sitemap, and successful public retrieval can rule out an obvious watched-surface indexing outage, but they do not erase the performance decline; classify it as a bounded watch condition until another complete window confirms or refutes it.
- Store raw machine evidence as JSON and the decision narrative as Markdown. Verify JSON parsing, metric parity, watch-set counts, no-secret markers, and report/hash consistency.
- Commit only the checkpoint artifacts in the isolated worktree if local commit authority is in scope. Push only when explicitly approved.
- Add the tracker comment by captured comment ID and read it back directly. Keep weekly metrics out of durable wiki pages; promote only enduring measurement rules or stable architecture changes.
