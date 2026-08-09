# Feedback-barrier replay and credential-error probes

Use this when an exact-head technical triad passes but the final feedback barrier stops, or when a reviewed request path carries a secret/capability.

## Publisher-authored acknowledgement replay

1. Read the completed report's feedback totals before using its excerpts. `fail_closed.evidence.unresolved` is intentionally bounded; when `unresolved_not_described` is non-zero, the displayed IDs are not the full acknowledgement set.
2. Reconcile the live PR with PR Prover's shipped `feedback.reconcile` implementation rather than reimplementing its truth table. Supply the live comments/reviews/threads and the state's retained `verified_artifacts` plus configured publishing login(s).
3. For a **replacement** operator pin, compute the target set from a no-pin baseline (`operator_acknowledgements={}`). Removing the old pin can revive both the targets it had cleared and the old acknowledgement post itself, whose now-ineffective ACK lines become residual publisher-authored prose. Reusing only the latest report excerpt can therefore create a long chain of partial replays.
4. Build one cumulative pure post from that complete no-pin unresolved set: one `PR-PROVER: ACKNOWLEDGED <artifact id>` line per item, with no heading or prose. Freeze the immutable-ID/state set used to build it, then re-read every live feedback surface immediately before publication. If any comment, review, thread, or state changed, discard the proposed body and recompute/re-simulate from the new no-pin baseline; never append one guessed line to a stale acknowledgement set.
5. Before publishing, add a synthetic later comment carrying the proposed body, pin it with the shipped `publication_evidence`, rerun `reconcile`, and require zero unresolved items. This proves every line performs exactly one eligible unresolved-to-cleared transition and that no historical post was omitted.
6. Publish the exact simulated body and read the immutable comment ID back from GitHub. For a conversation comment, `body_evidence` is SHA-256 over the UTF-8 JSON serialization of `[body, ""]` with `ensure_ascii=False`; hashing the raw body is incorrect.
7. Replace the config pin with that exact ID/digest, then independently rerun reconciliation over the real live comment and pin. Require the expected live comment count, cumulative cleared count, and `unresolved_count = 0` before spending another expensive reviewer run.
8. Prove launchability before reporting the replay active. A state file with non-null `outcome` is finished and will fail closed. Clear only the terminal outcome through the narrow shipped re-entry path while retaining the exhausted attempt count and `verified_artifacts`; do **not** call a broad reset command that removes the state file. Losing that ownership journal makes prior run-owned lane artifacts look like new publisher-authored feedback and can create a self-amplifying comment/ACK loop.
9. Reconfirm exact local/remote/PR head equality, clean worktree, open/unmerged state, and no active process. Run config validation, then launch with credentials scrubbed.
10. Treat a replay as a real configured run: it may rerun gates and A/B/Auditor, create new immutable artifacts, or discover a real blocker. Read the JSON report, state, live PR, and every returned artifact ID back before closeout.

### Recovery when the ownership journal was already lost

Use this only after the technical triad completed at an unchanged exact head and the remaining stop is feedback bookkeeping:

1. Fetch each prior reviewer artifact by immutable GitHub ID. Revalidate exact role, full head, runtime/signature, `STATUS=pass`, `BLOCKING=0`, canonical parser shape, and the exact publication-evidence/body digest. Do not reconstruct a body from summaries.
2. Freeze those exact bytes outside the worktree and use a deterministic role-bound replay adapter that refuses any repo/PR/base/head/role/digest mismatch, verifies a clean exact-head checkout and current frozen-packet binding, copies only the frozen artifact into the run-owned artifact slot, and emits the matching zero-blocker `DONE:` marker.
3. Keep the normal repository/preview gates, relay/readback, ordered A → B → Auditor packet barriers, and final stable feedback reconciliation. Replay is evidence recovery, not permission to skip verification or merge.
4. Derive the cumulative ACK target from the complete live no-pin unresolved set **after** including every historical reviewer replay and earlier bookkeeping post. Publish only ACK lines—no heading, explanation, or disposition prose—because residual text in a pinned publisher-authored post is itself unresolved feedback.
5. Compute the conversation-comment pin with the shipped evidence shape: SHA-256 of `json.dumps([body, ""], ensure_ascii=False).encode("utf-8")`. A raw-body SHA-256 is the wrong digest and makes the pin appear edited.
6. Simulate the exact later post and pin through the shipped reconciler before publication, then read the real immutable ID/body back and rerun reconciliation. Launch the final replay only after it proves zero unresolved.

This fallback was validated end-to-end, but preserving `verified_artifacts` is the preferred path because it avoids duplicate reviewer comments and cumulative bookkeeping growth.

### Pitfalls

- A pin authorizes one immutable post at one exact body, never the publisher login or its next post.
- A pinned post can spend valid acknowledgement lines but is not globally exempt from feedback classification; residual prose remains feedback.
- Do not chase the first bounded set of IDs repeatedly. Check the total and `unresolved_not_described`, then reconcile the no-pin baseline for a cumulative replacement.
- Do not assume clearance survives pin replacement. Reconciliation is recomputed from the currently authorized post(s).
- Do not discard retained `verified_artifacts` when replaying: otherwise prior run-owned lane artifacts re-enter feedback and the cumulative set changes again.
- Separate the substantive result from the control-plane result: report “technical triad passed; formal feedback barrier stopped” until the cumulative replay itself exits `0` with `merge-ready / no-blocking-findings`.
- Do not announce `active` merely because config and state are prepared. Require a live tracked process/PID that survived preflight.

## Credential non-reporting probe

Credential safety includes local request-construction failures, not only network transmission.

For a secret inserted into an HTTP header:

1. Use synthetic sentinels only.
2. Test a header-safe sentinel for exact-origin forwarding and absence from observations, summaries, stdout, and stderr.
3. Also test a parser-accepted but header-invalid sentinel, such as one containing a newline, through the shipped parser → binder → observer → evaluator/reporting path.
4. Put the transport counter after native `Request`/header construction. If native validation throws, assert transport starts remain zero.
5. Assert the exact sentinel is absent from returned reasons, serialized summaries, logs, stdout, and stderr.
6. Never propagate raw request-layer exception messages from credential-bearing operations. Use generic secret-free errors at the reporting boundary. Earlier header-value validation is useful, but retain downstream sanitization as defense in depth.

A native header-validation exception that echoes the value is a credential-disclosure defect even when no packet leaves the machine.