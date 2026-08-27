# Cross-System Production-Proof Reconciliation

Use when a deployment/activation issue is technically complete but Linear, GitHub, durable knowledge, and a still-open monitoring parent must be reconciled from verified production evidence.

## Evidence classes

Keep these distinct:

1. **Implementation evidence** — reviewed exact head, merged PR, merge commit, repository checks.
2. **Deployment evidence** — production deployment ID/status and deployed-revision binding.
3. **Runtime evidence** — live browser/network behavior and provider-side readback.
4. **Durable knowledge** — stable operating rules promoted to the canonical wiki; never transient counts or task state.
5. **Monitoring work** — post-launch interpretation that remains open after cutover-day continuity passes.

Do not let one class stand in for another.

## Reconciliation sequence

1. **Freeze fresh live state.** Re-read the tracker bodies/states/comments, GitHub PR and implementation issue, proof artifacts and hashes, canonical wiki page, and any parent/successor criterion before writing.
2. **Classify every unchecked line.** For each checkbox choose exactly one:
   - satisfied by cited evidence;
   - not applicable because an explicit recorded decision selected the other conditional branch;
   - deferred to a named open successor/monitoring issue;
   - still blocking.
3. **Rewrite conditional branches truthfully.** Do not silently turn an unexecuted conditional into a bare checkmark. Replace it with checked wording such as `Not applicable by owner decision: <decision and evidence>`. Conditional verification tied to that branch should be closed the same way.
4. **Reconcile the implementation issue.** If the merged PR did not create a structured closing relationship, update only criteria proven by implementation plus production evidence, add a closeout comment with proof locators/hashes and limits, close it explicitly as completed, then re-query state/reason/checklist/comment URL.
5. **Promote durable knowledge before terminal tracker closure.** Update the established canonical page, read back stable facts, update required activity/daily logs, and verify size/index rules. Keep PR SHAs, synthetic event counts, raw captures, and task status out of the wiki.
6. **Update the child and parent separately.** Complete the cutover/continuity child only when its checklist and knowledge gate are satisfied. Check only the parent criterion now proven; preserve the parent `In Progress` when its monitoring-duration or reporting criteria remain open.
7. **Publish an output inventory.** Name intended user/purpose, exact canonical paths/IDs/URLs, hashes or revisions, verification method, lifecycle, and honest limits. Mark temporary captures non-canonical after their redacted evidence is promoted.
8. **Directly read back all writes.** Verify tracker comments by captured comment IDs, issue state/type and checkbox counts, GitHub merge/close state, artifact hashes/schema, wiki semantic needles, and remaining parent state.

## Mutation safety

- Prepare full issue bodies in files or safe argument vectors; never shell-interpolate multiline Markdown containing backticks or dollar signs.
- If a helper launched inside a restricted subprocess lacks the credential environment that a direct terminal invocation has, preserve the prepared artifact and run the same verified helper from the credential-loaded terminal context. The durable lesson is to separate deterministic body construction from credentialed mutation.
- A failed multi-step closeout may have partially landed. Before retrying, re-read every target and resume from verified live state; do not repeat comments or status changes blindly.

## Honest-boundary examples

- Provider Realtime receipt does not prove raw payload parameters when that API does not expose them.
- Synthetic activation traffic is proof traffic, not a business baseline.
- Redirect preservation can be proven even when an unapproved campaign tuple is correctly omitted by the analytics runtime.
- A cutover-day child can be Done while a four-week monitoring parent remains active.

## Final readback packet

Record at minimum:

- PR merged state, reviewed head, merge/deployment commit;
- GitHub implementation issue state/reason and unchecked count;
- child tracker state/type, unchecked count, closeout comment ID;
- parent tracker state/type and exact criterion transitioned;
- proof artifact paths and hashes/schema validation;
- canonical wiki path, readback hash/semantic keys, and log-size compliance;
- remaining successor/monitoring boundary;
- active process/watchdog state.