# Gate-evidence-preserving review transport recovery

Use this reference when a fresh PR-Prover run cannot finish because of reviewer artifact transport drift or an unchanged timing-sensitive gate, but an earlier run on the **same exact head and unchanged contract surfaces** already completed every required gate successfully.

This is a narrow recovery path. It preserves real complete evidence; it does not waive, synthesize, replay, or weaken a failed gate.

## Eligibility

All conditions are required:

1. One retained run completed every configured gate on the exact current PR head.
2. The PR head, branch, base, PR body, governing issue/contract text, configured acknowledgements, and gate commands have not changed since that successful gate run.
3. The retained gate report, packet, worktree/head binding, and logs are readable and internally consistent.
4. The terminal failure after those gates was transport/control-plane only—for example final-message/prepared-artifact finding-summary drift—not a substantive blocker.
5. Any later gate failure is confined to an unchanged timing/process test whose test file and implementation path have no base-to-head diff; changed-surface gates and independent full-suite runs remain green.
6. No builder cycle, commit, push, or mutation occurred after the successful gate evidence was produced.

If any condition is false, stop fail-closed. Do not use this path to rescue a run that never had one complete all-gates pass.

## Recovery sequence

1. **Freeze the evidence root.** Record the successful run directory, exact head, complete gate outcomes, retained Reviewer A packet path/digest, and repair-attempt count.
2. **Do not restart gate roulette.** One justified identical review-only retry is acceptable. If it fails again only on the same unchanged timing seam—or alternates between supported runtimes—do not keep relaunching until green and do not edit commands, thresholds, timeouts, discovery, or tests.
3. **Rerun only the affected reviewer role.** Use a fresh detached clean worktree at the exact head, the repository-owned credential-free launcher, and the retained packet from the successful gate run. Use a unique absent artifact path. If the prior failure was finding parity, explicitly require each `FINDING:` line to be byte-for-byte identical in the final message and prepared artifact.
4. **Validate with shipped code.** Parse the final machine verdict; validate the prepared body, exact role/head/runtime/signature/status/blocker count, adversarial declarations, and complete finding-record parity. Never hand-edit reviewer-owned output.
5. **Use configured transport.** Re-query the live head, sanitize through the shipped publication-copy path, invoke the configured trusted relay, capture its returned immutable artifact ID, and read that exact ID back through the repository boundary. Verify author, surface, commit/head binding, exact publication bytes/digest, and canonical parser claims.
6. **Refreeze after each publication.** Build Reviewer B's packet only after Reviewer A readback. Build the Integration Auditor packet only after both A and B readbacks. Use one stable live GitHub read for each packet and run the shipped packet writer **and reader** so repo/PR/base/head/sequence/reviewer/role/governing-issue bindings are revalidated.
7. **Preserve order and isolation.** Reviewer A → readback → Reviewer B → readback → Integration Auditor → readback. Each lane gets its own clean detached worktree and credential-free environment. Watcher exit proves termination only; authoritative stdout/artifact/state/readback decides acceptance.
8. **Finish normal closeout.** Reconcile all feedback surfaces to a stable two-read observation, verify local/remote/PR head equality and worktree cleanliness, preserve the consumed repair cap, then recommend ready or blocked. Karan remains sole merge authority.

## What counts as governed lower-level operation

Prefer the repository's shipped boundaries rather than ad hoc shell reconstruction:

- GitHub boundary for pull/comments/reviews/threads/checks/governing issues;
- packet `build`/`write`/`read` functions;
- repository-owned reviewer launchers;
- canonical verdict and prepared-artifact parsers;
- publication-copy/redaction path;
- configured relay command;
- immutable-ID readback verifier.

Private helper methods may change between repository revisions. If an operator script must call them, bind the script to the exact reviewed checkout, keep it outside the repository, validate its inputs/outputs, and treat it as disposable orchestration—not durable product code.

## Hard stops

- No complete exact-head all-gates run exists.
- Any code, PR contract, governing issue, ACK evidence, or head changed after the successful run.
- The reviewer surfaces disagree substantively rather than only in transport grammar.
- Canonical prepared-artifact validation, relay attribution, or immutable-ID readback fails.
- A changed-path test fails, focused reproduction remains red, or the environment explanation is unproved.
- Completing the chain would require hand-authored artifacts, direct reviewer publication, altered gates, a hidden third builder cycle, or inferred success from a watcher.

## Relationship to other skills

Load `review-artifact-relay-and-state-barriers` for the detailed canonical parser, sanitation, identity, ordered packet, and readback barriers—especially `references/background-review-budget-and-flake-triage.md` and `references/canonical-artifact-parser-preflight.md`. This reference only decides when prior complete gate evidence may safely anchor that lower-level lifecycle.
