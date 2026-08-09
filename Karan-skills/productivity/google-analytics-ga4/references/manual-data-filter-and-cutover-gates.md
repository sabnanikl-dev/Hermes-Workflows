# Manual GA4 DataFilter Evidence and Migration Cutover Gates

Use this when Developer/Internal Traffic configuration is UI-only, or when GA4 activation is part of a hosting/domain migration.

## Manual Developer Traffic filter closeout

1. Select the intended GA4 account and property; record the property ID.
2. Open **Admin → Data collection and modification → Data filters**.
3. Reuse an existing equivalent filter rather than creating a duplicate.
4. Verify or create:
   - Filter name: `Developer Traffic`
   - Filter type: `Developer traffic`
   - Operation: `Exclude`
   - State: `Testing`
5. Keep the filter in **Testing** until a separately approved decision changes it. Do not silently promote it to Active.
6. Capture the saved state, not only the unsaved creation form. Prefer a detail view or list row that shows the property context, name, type, operation, and state.
7. Record a tracker readback with the exact values and attach the screenshots.

### Evidence boundary

If authenticated tracker attachments cannot be downloaded through an unauthenticated artifact URL, directly read back the tracker comment and attachment links, then state the limitation precisely. Accept the human operator's manual UI readback as manual evidence when the governing issue allows it, but do not claim independent pixel-level screenshot inspection.

When updating a machine-readable readiness artifact, replace `UNKNOWN` with a structured object containing verifier, timestamp, account/property identity, name/type/operation/state, evidence locator, API boundary, and attachment-access limitation. Remove only the DataFilter blocker; keep production publication, consent, activation, and cutover gates open.

## GA4 activation during a domain/hosting migration

Use staged gates so analytics failure does not force a website/DNS rollback:

1. **Prepare, not schedule:** recommend a window and checklist, but label it `prepared-not-scheduled` until the human records the exact window, deployment, operator, rollback owner, and email validator.
2. **Bind exact deployment:** record project, immutable deployment ID/URL, Git revision, and mutable production alias. Rerun the complete migration preflight against that bound deployment. For an unprotected production-stage preflight, explicitly clear any inherited preview-bypass environment (`VERCEL_AUTOMATION_BYPASS_SECRET`, `MIGRATION_BYPASS_SECRET`, `MIGRATION_BYPASS_CAPABILITY`, and `MIGRATION_BASE_URL`) before invoking the checker. A fail-closed checker may correctly reject stale parent-session credentials even after the repository suite passes; rerun only the affected public preflight with those variables unset, never by weakening the checker or passing a credential to a public alias.
3. **Publish production-disabled first:** verify the public privacy disclosure and consent control, and prove absent/declined/dismissed consent produces zero GA requests.
4. **Second activation approval:** bind approval to a separately reviewed exact revision. The human merge/deploy gate remains load-bearing.
5. **Alias-level analytics proof before DNS:** verify one loader after Allow, no pre-consent requests, no duplicate page views, no PII/form values, approved events only, and DebugView/Realtime receipt.
6. **Web-record cutover only:** change only the approved apex/`www` records. Preserve nameservers, MX, mail A, SPF, DKIM, and verification TXT records.
7. **Production proof:** repeat consent/network, event, UTM, hostname, self-referral, preview-contamination, redirect, TLS/canonical, and email-continuity checks.

## Two rollback tiers

- **Analytics-only rollback:** for pre-consent collection, PII, duplicate loader/page views, unapproved events, or material analytics errors, redeploy the production-disabled revision while leaving healthy website DNS unchanged.
- **Website/DNS rollback:** for TLS/canonical failure, critical migration-preflight failure, prolonged hosting failure, mail-record drift, or cutover-caused email failure, restore only the recorded web records and leave mail records untouched.

Always record trigger, action, timestamp, resulting deployment/DNS state, and verification outcome. A planning packet is not authorization for deploy, domain, SSL, analytics activation, DNS, sitemap, or cutover mutations.
