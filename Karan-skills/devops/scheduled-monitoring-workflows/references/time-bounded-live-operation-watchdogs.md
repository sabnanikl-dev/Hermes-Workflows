# Time-Bounded Live Operation + Watchdog Pattern

Use this pattern for an explicitly approved, high-risk operation that starts in a future window and needs finite monitoring afterward (DNS cutover, deployment promotion, migration, certificate switch, or similar).

## Split execution from observation

Create two jobs rather than one broad autonomous mission:

1. **One-shot executor** shortly before the window. It performs read-only requalification, waits for the exact start boundary, mutates only the approved surface, verifies direct readback, and fails closed on drift, missing authenticated access, permission prompts, or failed gates.
2. **Finite read-only watchdog** on the monitoring cadence. It checks original-source state, classifies propagation/health/anomalies, and reports through the requested channel. It must not silently inherit mutation authority from the executor.

This separation keeps repeated monitoring from becoming repeated mutation authority and makes the executor's approval envelope auditable.

### When the human advances the window

An explicit supervised “go live now” can supersede a previously recorded future start while preserving the same immutable revision, exact mutation set, protected adjacent surfaces, and rollback contract. Before performing the immediate mutation:

1. Re-read live state and record the superseding authorization with an exact timestamp.
2. Remove the future one-shot executor so it cannot replay the mutation later.
3. Reschedule the read-only watchdog from the actual mutation time through the original TTL/monitoring horizon.
4. Update evidence artifacts that still say “prepared” or “scheduled”; distinguish the old scheduling checkpoint from the actual execution record.

Never leave a still-enabled future executor behind after a supervised manual cutover.

## Bind approval durably before scheduling

Record and directly read back the human approval in the governing tracker before creating jobs. The approval packet should name:

- exact window and timezone;
- immutable revision/deployment;
- exact before/after values for every allowed mutation;
- records/systems that must remain untouched;
- rollback values and triggers;
- operator and manual validation responsibilities;
- whether follow-on actions such as analytics activation, sitemap submission, email sending, or deployment are excluded.

A generic “continue” can authorize preparation, but the scheduled mutation job should be bound to an explicit live-operation choice.

## Executor prompt contract

Make the cron prompt self-contained because cron sessions have no chat context. Require it to:

1. Read the immutable tracker approval/comment IDs.
2. Reconstruct live tracker, revision, deployment, account/UI, and public-source state.
3. Refuse to mutate before the exact start time.
4. Re-run the complete preflight immediately before mutation.
5. Use only an already-authenticated UI; never type credentials or approve security/permission prompts.
6. Stop without mutation on unexplained drift or unavailable access.
7. Change only the exact approved values.
8. Verify saved UI state plus authoritative/original-source readback.
9. Recheck protected adjacent surfaces immediately after mutation.
10. Publish evidence by immutable tracker comment ID and verify it directly.
11. Deliver a final status containing ACTIVE/PASS/BLOCKED/ROLLED BACK, exact mutations or blocker, verification results, remaining manual gates, and PID (normally none after completion).

If rollback is authorized, require conclusive trigger evidence and restrict rollback to the recorded values. Never let a vague failure expand rollback into unrelated systems.

## Watchdog schedule and classification

For a finite window, use a cron expression plus a bounded `repeat`; do not use duration syntax and assume `repeat` makes it recurring. Verify `next_run_at`, delivery, enabled state, schedule, and repeat count after creation.

Example: a 15-minute cadence from 20:00 through 22:30 is 11 ticks (`*/15 20-22 <day> <month> *`, `repeat=11`). Account for the executor/watchdog race at the first tick: classify it as `STARTING` when no verified mutation exists yet rather than raising a false incident.

Useful classifications:

- `STARTING`: executor has not yet published verified mutation evidence.
- `PROPAGATING`: authoritative state is correct; some caches remain on the recorded old value; no unexplained target exists.
- `HEALTHY`: acceptance threshold is met, protected adjacent surfaces are unchanged, and required human checks pass. For a web-only DNS cutover that preserves hosted email, this means a cellular site smoke plus a post-cutover message in each direction through the preserved mailbox—not merely unchanged MX syntax.
- `ALERT`: protected-state drift, unexplained target, externally reproduced critical service failure, authority expansion, or contradictory evidence.
- `FINAL`: deadline-bound continue/rollback recommendation with manual gates named.

A cached old value within the recorded TTL is not by itself an alert. Unknown or conflicting state fails closed.

## Delivery routing

When the user asks for cron output on a different platform than the current chat, resolve the exact configured destination instead of guessing. Reuse a verified existing destination or the gateway's configured home chat, then set `deliver` explicitly (for example `telegram:<chat_id>`). Re-list jobs and verify both executor and watchdog show the requested destination.

Use `attach_to_session=true` for the one-shot executor when the user may need to reply to its result. Monitoring alerts can remain fire-and-forget unless conversational follow-up is useful.

## Evidence artifact hygiene

If a local readiness packet exists, update it after approval and scheduling so it does not still say “prepared, not scheduled.” Record job IDs, next-run times, repeat count, delivery target, exact approval evidence, and a clear `liveMutationPerformedAtSchedulingCheckpoint=false`. Parse machine-readable artifacts, run focused parity assertions, and scan for secret markers before closeout.

## External verification when the operator network is untrustworthy

A local browser or `curl` failure is not a rollback trigger when the operator network is known to intercept TLS, retain stale resolver answers, or route through filtering infrastructure. One especially misleading signature is a direct connection to the approved destination IP on port 443 returning plaintext HTTP (for example, a safety-filter redirect), which surfaces as `ERR_SSL_PROTOCOL_ERROR` even while public TLS is healthy. Keep the monitor read-only and obtain fresh evidence from an external measurement service instead. Require a phone-cellular smoke with Wi-Fi disabled before classifying the discrepancy as local-only.

For each tick:

1. Query every authoritative nameserver directly, then the contract's named public resolvers. Keep the authoritative result separate from recursive-cache observations.
2. Create fresh HTTPS measurements from at least three external probes for each required hostname. Do not reuse an old measurement as current proof.
3. Require the expected status, redirect target, server/origin identity, authorized TLS, certificate subject hostname, and a small content marker from the original site. Report only the safe certificate facts the contract permits—not serials, fingerprints, or full certificates.
4. When a safety property lives inside a shipped static asset (for example a production-disable constant), fetch that asset externally too. Reuse the completed page measurement's probe set when the API supports it so page and asset observations come from the same networks.
5. Treat an old, explicitly recorded target within its TTL as propagation when authoritative state is correct and the acceptance threshold is still met. Any unexplained third target, protected-record drift, or externally reproduced TLS/canonical/content failure is an alert.
6. Public recursive resolvers are anycast systems; two checks can hit different cache nodes. A later old-but-approved rollback answer is not automatically contradictory evidence. Judge it against authoritative truth, TTL, the allowed old/new set, and the required resolver threshold.

Keep the measurement IDs in the user-facing report so every claimed second-network result has a completed, auditable handle. If external evidence also verifies a disabled runtime or other safety gate, name the measurement separately from the page/redirect measurements.
