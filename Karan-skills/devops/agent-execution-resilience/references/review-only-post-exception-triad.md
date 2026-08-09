# Review-only post-exception PR triad

Use this after the normal PR-Prover repair budget is exhausted, Karan authorizes one narrow manual exception repair, and the authorization explicitly requires the next exact-head pass to be **review-only**.

## Why a derived at-cap continuation state is required

A fresh zero-attempt state restores the normal builder budget. A finished prover state (`outcome: "blocked"` or another terminal outcome) cannot be resumed either: the current tool deliberately stops with `unexpected-state` and says the finished run must be reviewed before another run. Do not claim that the finished file can be reused directly.

Preserve the finished state unchanged as the audit record. For the authorized review-only pass, create a **separate derived continuation state** at a new path whose values are mechanically copied from that reviewed terminal state, with only these lifecycle fields reopened:

- keep `attempt == max_attempts`;
- keep the pre-exception `head` so the loop invalidates it against the new live head;
- set `outcome` to `null`;
- set `phase` to `"idle"` and `attempt_head` to `null`;
- set `classification` to `null` so stale findings are not carried onto the new head;
- preserve `repo`, `pr`, `schema_version`, `corrective_rerun_attempts`, and the exact `verified_artifacts` map;
- point a copied config at the new continuation `state_file` and a new `lock_file`.

Do not call `reset` on the original audit state, do not delete it, and do not create a zero-attempt file. Validate the copied state fields and run `check-config` before launch. The at-cap counter prevents the builder lane from reopening: a clean triad can report merge-ready, while a blocker reports blocked/needs-Karan without mutation.

## Preconditions

Before the exception builder starts, freeze:

- exact old PR head;
- exhausted `attempt` and configured `max_attempts`;
- complete blocker ledger and finding IDs;
- allowed files and required former-red probes;
- no-merge/deploy/activation/account-mutation boundaries;
- the instruction that any later blocker is reported, not repaired.

After the builder exits, independently verify:

1. worktree is clean;
2. local HEAD, remote branch SHA, and PR `headRefOid` are one identical full SHA;
3. the PR commit list contains the exception commit(s);
4. issue closing linkage and PR body remain correct;
5. the builder handoff comment is read back by exact ID;
6. every new bot/builder conversation comment is reconciled under the configured strict-feedback policy.

## Exact-post acknowledgement sequence

When the only authenticated GitHub identity is also a configured publisher:

1. Read the substantive builder or bot comment by ID and adjudicate it.
2. Post a **pure** bookkeeping comment containing only `PR-PROVER: ACKNOWLEDGED <target-id>`.
3. Read that ACK comment back by its own ID.
4. Compute `body_evidence` with the checked-out prover's own `publication_evidence` helper over the live readback object. Do not hand-roll or remember the serialization: exact body whitespace and review state are part of the digest.
5. Read the current config parser before editing the pin. For the present schema, each entry is exactly `{"id": "<immutable GitHub id>", "body_evidence": "<64-hex digest>"}`; do not invent aliases such as `post_id`, coerce the ID to a number, or reuse a digest calculated from prose instead of live readback.
6. Run `check-config` and require it to print every intended pin. If it rejects the shape or digest, re-read the schema and recompute from GitHub readback rather than weakening strict feedback.

Do not mix explanatory prose into the ACK post; mixed posts create their own unresolved feedback surface.

## Review-only launch proof

Inspect the preserved state directly immediately before launch and require:

- `attempt == max_attempts`;
- stored outcome is bounded/blocked rather than merge-ready;
- stored head is the pre-exception head;
- live local/remote/PR head is the new exception head;
- original finished state is preserved unchanged and the copied config points to the separate derived continuation state plus a new lock path;
- derived state has `outcome == null`, `phase == "idle"`, `attempt_head == null`, `classification == null`, and preserves the reviewed terminal state's identity, attempt counter, old head, rerun ledger, and verified artifact map;
- no `reset` of the original state, original-state deletion, zero-attempt state, or max-attempt increase occurred.

Then run the normal prover command. Expected behavior:

- stale prior-head evidence is invalidated;
- all deterministic gates rerun on the new head;
- Reviewer A → Reviewer B → Integration Auditor rerun serially with relay/readback;
- no builder launches because the attempt budget remains exhausted;
- a blocker ends as blocked/needs-Karan, not as another repair.

If the tool attempts to launch a builder despite these preconditions, stop the exact process and inspect state/config behavior. Do not let the supposedly review-only run mutate the repository.

## Runtime-bound browser evidence pattern

For a production-disabled browser integration whose acceptance criteria include an eligible loader path:

1. Commit the runtime/test/docs repair first.
2. Record that runtime commit, tree hash, and changed asset checksum.
3. Serve committed bytes verbatim for the disabled pass.
4. Create a temporary eligible tree with one machine-verified literal change only (for example, `productionEnabled: false` → `true`).
5. Intercept and abort every provider/analytics/ads request before egress.
6. Exercise desktop and mobile, representative events, repeat boot, safe location/referrer values, and duplicate-loader prevention.
7. Save real screenshots and a report that identifies both byte sets and all interceptions.
8. Commit evidence only; verify the evidence commit changes no runtime/script/library bytes.

This makes the final head contain evidence for an immutable runtime without claiming the disabled production artifact itself made a live provider request.

## Validate evidence semantics, not only runtime identity

A checksum and source-commit match prove which bytes were exercised; they do not prove the recorded browser run passed. Before review-only closeout, require the repository gate to reject explicit failure results, non-empty problems/page errors, missing or duplicate runs, removed required viewport/scenario pairs, contradictory activation booleans, missing screenshots, unexpected provider traffic, and broken loader/config/event-count invariants.

Drive those cases through the public validation command as direct evidence-envelope mutants. Include one real producer-generated positive control. Keep runtime/checker changes in a commit before browser evidence, regenerate desktop/mobile evidence against that immutable runtime, and prove the evidence-only commit changes no runtime, checker, library, or template bytes.

When route classification participates in the evidence, treat `window.location.pathname` as mutable: pre-init `history.pushState()` and `history.replaceState()` can change it without a fetch. Require a former-red probe proving a same-document URL rewrite plus forged DOM facts cannot promote an unknown/stale fetched route. If the runtime cannot identify an actually fetched route under the governing threat model, redesign the build/server handoff or fail closed rather than documenting the live pathname as immutable.

Guard against a vacuous browser pass: a pre-init History API rewrite can change how a relative `<script src>` resolves, causing the runtime request to 404 before the classifier is exercised. For every rewritten-route case, assert that the intended runtime actually loaded and reached the expected eligible sentinel (for example, exactly one config with `page_kind: not_found`), not merely that no forbidden event appeared. Serve the tested asset independently of rewritten document depth or use a root-stable URL, and keep a negative mutation proving the sentinel fails when the runtime is absent.
