# GBP Performance and Search-Demand Research

Use this when Business Profile Performance data will influence a local SEO page roadmap, profile-optimization priority, acquisition-channel assessment, or visibility-decline investigation.

## Capture sequence

1. **Re-run access discovery immediately before capture.** Manager access may have changed since the prior audit. Verify OAuth identity, `business.manage`, target location resource, open status, and Voice of Merchant before treating an old blocker as current.
2. **Pull search keywords in non-overlapping six-month windows.** The monthly search-keyword endpoint accepts at most six months per request. Request consecutive windows, include one older back-check window, and record requested versus populated months and row counts.
3. **Preserve the `InsightsValue` union exactly.** A row is either:
   - `value`: exact impressions aggregated over that monthly range.
   - `threshold`: an upper-bound marker; `threshold: 15` means fewer than 15, not 15.
   Never coerce threshold rows into counts, rank them numerically with exact rows, or silently sum them. For aggregation, report an **exact lower bound** from `value` rows plus a separate threshold-row count.
4. **Separate branded and non-branded rows.** Report exact lower bounds, exact-row counts, and threshold-row counts for each. Branded discovery validates recognition/navigation, not demand for a new service page.
5. **Pull daily metrics over the widest accepted window:**
   - `BUSINESS_IMPRESSIONS_MOBILE_SEARCH`
   - `BUSINESS_IMPRESSIONS_DESKTOP_SEARCH`
   - `BUSINESS_IMPRESSIONS_MOBILE_MAPS`
   - `BUSINESS_IMPRESSIONS_DESKTOP_MAPS`
   - `CALL_CLICKS`
   - `BUSINESS_DIRECTION_REQUESTS`
   - `WEBSITE_CLICKS`
6. **Create an exact-date comparison window.** If GSC has a shorter populated cohort, recompute GBP totals for those same dates. This supports directional funnel comparison without pretending the units are equivalent.
7. **Aggregate daily metrics by calendar month.** Inspect first/last returned dates before making year-over-year claims.
8. **Distinguish omitted zero values from missing data and retired metrics.** In a present `datedValues` row, Google omits `value` when the count is zero ([TimeSeries definition](https://developers.google.com/my-business/reference/performance/rest/v1/TimeSeries)). Normalize that omission to zero only after validating the series and date coverage; missing series/dates remain UNKNOWN. Conversely, a zero-filled `BUSINESS_CONVERSATIONS` response does not establish working chat with zero leads: [Google Help](https://support.google.com/business/answer/14919056?hl=en) says the legacy chat feature and conversations Performance metric were retired. Mark legacy chat performance unavailable; evaluate account-eligible text/WhatsApp separately. Reserve with Google booking zeros are not total business bookings and do not establish integration eligibility.
9. **Read dated follow-ups before reusing a stale baseline summary.** A May parent artifact can still say unsubmitted/not indexed after a June submission closeout. Reconcile the latest dated evidence and live tracker/provider state, then add an explicit supersession pointer rather than repeating a completed approval request. Preserve historical no-row responses without treating them as proven zero-traffic growth denominators.

## Unit and surface discipline

- GBP Search impressions count the **Business Profile appearing on Google Search**, not organic website-result impressions.
- GBP Maps impressions count the profile appearing in Maps.
- Search-versus-Maps share therefore says where the profile surfaced; it does **not** by itself rank website-page work against profile optimization.
- GBP daily impression metrics deduplicate repeated impressions from the same user within a day. GSC impressions count search-result appearances.
- Never add GBP and GSC impressions, place them in a shared total, or infer organic position from GBP keyword rows.
- GBP keyword impressions provide neither position nor per-keyword clicks.
- GBP website clicks, call clicks, and direction requests are separate profile interaction funnels. Do not add them to GSC clicks.
- A convenience sum of website/call/direction counts is a **profile interaction count**, not unique customers or confirmed conversions; the same person may contribute more than once.
- Directional funnel comparison is still useful when labeled. If profile interactions materially exceed non-branded GSC clicks, the website is not the whole acquisition path, but no combined conversion total exists.

Official metric definitions: https://developers.google.com/my-business/reference/performance/rest/v1/DailyMetric

## Year-over-year trend method

1. Confirm the observed date range for every metric.
2. Aggregate raw daily values by calendar month.
3. Compare only complete matched months in the primary headline.
4. If the historical series begins mid-month, do not compare that partial month with a full current month. Either exclude it or compare identical day ranges separately.
5. Prefer percentage change in matched-period totals over an unweighted mean of monthly percentage changes. If both are shown, label both.
6. Report Search, Maps, website clicks, call clicks, direction requests, and calls+directions over the same matched periods.
7. Preserve the exact period beside every percentage.

Useful patterns:

- Search impressions down, Maps stable/up, calls+directions stable: lost visibility may be disproportionately low-value, but the profile decline still warrants diagnosis.
- Search and Maps both down with interactions down: investigate broader relevance, prominence, completeness, competition, availability, or profile-state problems.
- Impressions stable while interactions fall: investigate conversion/profile-content issues.

## Threshold compression

When many exact keywords become `<15` during a profile-wide impression decline:

- call it **threshold compression inside a broader decline**;
- do not calculate term-by-term percentage collapses;
- do not infer that a specific intent disappeared;
- do not describe the recent threshold as stable current volume;
- combine threshold state with fresher GSC clicks/position, seasonality, and business proof before changing a page decision.

A historical exact value followed by a threshold means only that the latest aggregate is unknown below the threshold. It does not explain why.

## Roadmap decision rules

- **Large profile trend issue:** name it before page-level findings and decide whether a read-only profile audit should precede page work.
- **Search-dominant profile surfaces:** on-site relevance may support local ranking, but the split alone does not make pages the primary lane.
- **Maps-dominant profile surfaces:** inspect profile completeness, categories, photos, reviews, and local-pack factors before expanding page count.
- **Exact current keyword values:** strengthen evidence for an existing page when intent and real business scope align.
- **Threshold-only cluster:** use for intent coverage, not numerical priority or volume claims.
- **No returned rows:** scope the absence to API-returned rows; it is not proof of zero market demand.
- **Business-proof gate remains authoritative:** search evidence never authorizes inventory, availability, rental, tailoring, or service claims.
- **Preserve still-valid page issues:** revise evidence and priority rather than discarding scope solely because a larger profile diagnostic emerged.

## Divergence-led live SERP diagnosis

When Profile Search impressions fall while Maps impressions rise, use the **divergence** as the discriminating observation, not as causal proof.

- A Search-side layout change, AI/answer surface, or smaller local pack may reduce Profile Search impressions without reducing Maps exposure.
- Competitive displacement remains possible; Search and Maps do not have to move identically. Do not assume the divergence settles the cause.
- Freeze a small query × geography panel before observing it. For each sample record exact query, geography, time, device/tool context, AI/answer-surface presence, local-pack presence, visible local-result count before expansion, JMD/client presence, and limitations.
- A current snapshot cannot prove what caused a historical year-over-year change. Require a confidence statement and permit `insufficient evidence`.
- Define success conditionally:
  - if local-surface availability is stable, measure client presence relative to recurring competitors and test bounded corrective actions;
  - if the surface itself contracted, absolute recovery to the old impression count may be impossible, so measure presence frequency/share in the fixed panel plus retained high-intent actions;
  - if surface availability cannot be established, do not select a cause or promise recovery.

## HTTP profile URI and TLS triage

If the profile points to `http://`:

1. Record it as a redirect/consistency issue.
2. Do not infer that HTTPS is broken from the profile field alone.
3. Test HTTPS through an independent external service or several geographically distributed nodes.
4. Corroborate with certificate-transparency data when useful.
5. If external probes return HTTPS 200 and a current certificate exists, remove active TLS failure from the leading hypotheses while retaining the stale URI as an approval-gated cleanup.
6. If external probes fail, escalate to DNS/TLS/cutover triage before changing the profile.

Profile URL edits are public account mutations and require explicit approval.

### Ticketing and executing an HTTPS profile-URL cleanup

Once HTTPS and the production cutover are independently healthy:

1. Re-read the live profile field immediately; never rely on an old audit value.
2. Route the candidate into the existing approval-gated GBP mutation/quick-fix issue when one exists. Do not hide it inside the read-only decline audit or create a duplicate implementation ticket.
3. Preserve exact values (`http://…` → `https://…`) and state explicitly that this is redirect-hop/cross-surface consistency cleanup, not a proven cause or cure for a visibility decline.
4. Creating/updating the ticket does not approve the write. Require explicit human approval naming the exact before/after values.
5. Immediately before the approved mutation, re-prove the current profile value and that HTTPS serves the intended production content.
6. Write only the one approved field; do not bundle categories, hours, description, products, or other profile edits.
7. Verify through direct API/dashboard readback and confirm the public profile action reaches HTTPS without a protocol-upgrade redirect hop.
8. If the before-state drifted, HTTPS validation fails, the API requests additional fields, or write/readback is ambiguous, stop without retrying or changing another field.

## Verification checklist

- Raw keyword-window row counts equal normalized output counts.
- Every raw `value`/`threshold` maps to the same normalized kind and amount.
- Threshold meanings remain explicit in JSON and Markdown.
- Every requested daily metric is present with the same observed range and expected dated-value count.
- Search/Maps totals recompute from raw mobile + desktop series.
- Monthly and matched-period totals recompute from raw daily values.
- Partial months are excluded or date-matched explicitly.
- Branded split and cluster summaries recompute from normalized rows.
- GSC and GBP units are never summed.
- Interaction counts are not presented as unique customers or conversions.
- External HTTPS claims include a verifiable report URL.
- Human-readable and structured artifacts agree on windows, totals, interpretation, and approval boundaries.
- Stale blocker and superseded interpretation language is removed from same-topic artifacts.
- Secret scan covers generated reports; raw OAuth/token material is never copied into artifacts.
- Label the check as ad-hoc verification when the docs workspace has no canonical suite.

## Artifact pattern

Keep three layers:

1. Raw keyword capture preserving API union fields.
2. Raw daily-metric capture preserving dated series.
3. Normalized JSON plus concise Markdown with exact windows, unit rules, branded split, matched-window funnel metrics, year-over-year trend, roadmap impact, external diagnostics, sources, and approval boundaries.

When an earlier report said access was blocked or carried a superseded interpretation, update or explicitly supersede it so downstream agents do not act on stale state.
