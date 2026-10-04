# Activation preflight and partial approval records

## Purpose and evidence limit

Use when the human moves from fixture/visual acceptance to live analytics activation. This is a validated read-only discovery and approval-recording pattern, not a claim that activation or deployment succeeded.

## Resolve current state before mutation

- Read the live implementation PR, activation issue, and policy tracker. Older tracker prose may still say “build not authorized” after later approvals and verified implementation; preserve chronology and distinguish stale status from still-valid policy gates.
- If the previous operation was interrupted, directly query whether its merge/deploy occurred. Never infer completion from the user's next instruction. Keep prior merge/branch-deletion authority distinct from the new activation scope.
- Inspect the actual activation module and configuration resolver. A source-level `false` gate cannot be enabled by setting a build-time Measurement ID alone. Identify independent gates for GA collection versus attribution fields sent to a form backend.
- Match account → property → stream → Measurement ID to the selected destination. A similarly named property is not an interchangeable fallback.

## Read-only provider inventory

Use the authenticated helper without printing credentials:

- `/v1beta/properties/{property}` and `/dataStreams` for destination identity.
- `/v1beta/properties/{property}/dataRetentionSettings` for all returned retention fields and reset behavior.
- `/v1alpha/properties/{property}/dataStreams/{stream}/enhancedMeasurementSettings` for the master switch and individual collectors, especially form interactions, outbound clicks, and history pageviews.
- The stream's `/dataRedactionSettings` for email and query redaction evidence.
- `/v1alpha/properties/{property}/googleSignalsSettings` for direct Signals state.
- `/v1alpha/properties/{property}/googleAdsLinks` for linked Ads accounts; honor pagination when present.
- Account/property `/accessBindings` for roles when permitted. A 403 is an evidence gap, not proof of a low role, absent owner, or permission to broaden access. Use existing authoritative evidence first; if still necessary, ask for the business Administrator's identity and confirmation of the operator role, never credentials.

**`userDataRetention=TWO_MONTHS` is rejected on standard properties** (HTTP 400 `invalid enum value TWO_MONTHS`, Femme property 554551982, 2026-09-25) even though the enum doc lists it; user-level retention stays `FOURTEEN_MONTHS`. PATCH the other fields separately (a combined mask fails atomically), record the deviation against any "two-month user retention" policy, and note mitigations (e.g. session-only `cookie_expires: 0`) instead of claiming compliance.

A successful read found `eventDataRetention=TWO_MONTHS` alongside `resetUserDataOnNewActivity=true` and `userDataRetention=FOURTEEN_MONTHS`. Preserve such fields separately; do not collapse the result to “two-month retention verified” or invent a tested PATCH for an unexamined field.

## Scope and approval

When exact live-action scope is unresolved, present the concrete findings and a bounded plan covering settings, disclosure version, reviewed activation code, deployment, test traffic, and rollback. Do not repeatedly seek approval already clearly granted. Missing destination/deployment details still require discovery before mutation.

If GA-only activation is proposed while form/email retention remains unresolved, explicitly obtain that staged scope rather than silently overriding a combined activation gate. Keep backend attribution fields off. Analytics test traffic, a real business inquiry, GBP edits, role changes, and unrelated account cleanup are distinct actions.

Batch independent approval/ownership questions. If only one is answered, retain that answer exactly. A timeout is neither consent nor refusal on the unanswered question. Record a concise project-local artifact with:

- exact approved question/answer and disclosed exclusions;
- selected target IDs and inspected implementation head;
- provider GET findings and evidence limitations;
- remaining gate and actions actually performed.

Never store tokens or current task progress in durable user memory. Before resuming, recheck mutable state; the artifact preserves approval, not perpetual readiness.

## Closeout wording

State what is approved, what changed, and the precise missing answer. Do not say “activated” from policy approval, saved configuration, fixture tests, or a mounted tag. Real activation needs deployment binding, consent-negative checks, positive network collection, and provider-side proof under the approved protocol. Use the main skill's live-proof references for execution.
