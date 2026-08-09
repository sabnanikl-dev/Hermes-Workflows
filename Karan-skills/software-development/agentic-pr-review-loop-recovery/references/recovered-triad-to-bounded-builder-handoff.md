# Recovered triad to bounded builder handoff

Use this after a transport/control-plane failure was recovered manually and the full ordered Reviewer A → Reviewer B → Integration Auditor lifecycle is now published and read back on one unchanged exact head. This is the bridge from recovered review evidence to the **remaining** bounded builder attempt; it is not permission to reopen the attempt budget.

## Eligibility barrier

Do not freeze a repair ledger until all are true:

- one complete exact-head gate run is preserved;
- local worktree HEAD, remote feature ref, and PR `headRefOid` still agree;
- Reviewer A, Reviewer B, and Integration Auditor each have a canonical artifact on that exact head;
- every artifact was parsed locally, sanitized through the shipped publication-copy path, relayed under the configured publisher identity, fetched by immutable GitHub ID, and matched against the lane verdict;
- the packet for each later lane was freshly built, written, read back, and proved to contain the earlier verified artifact IDs;
- the global repair-attempt count is known from actual repair commits, not launcher failures.

A Reviewer A artifact alone is never enough to launch a repair when the contract requires the ordered triad.

## 1. Reconstruct the full finding set with shipped parsers

Parse each lane's authoritative final-message file using the repository's verdict parser and exact expected head. Do not reconstruct findings from prose or use the GitHub body as a substitute for the lane output.

Feed every parsed `Finding` from all three lanes into the shipped classifier. Preserve all origins and lineage while deduplicating by finding ID. The Integration Auditor may add a new blocker; do not discard it merely because A/B did not report it.

Hermes must adjudicate each unique finding before freezing the ledger:

- reproduce code/data claims where practical;
- for tracker/status/documentation claims, read the authoritative live tracker or source directly rather than trusting reviewer prose or an older packet snapshot;
- classify false positives explicitly instead of silently omitting them;
- stop for `needs-karan` rather than routing it to the builder.

## 2. Freeze the ledger without inventing evidence

Prefer the repository's own blocker writer. If the terminal control-plane path cannot be resumed safely, construct the same current-schema payload with repository-owned model objects and validators:

- current blocker schema version;
- repo, PR, branch, base, exact head;
- truthful cumulative `attempt` and mode;
- `omitted_from_previous_run` exactly as proven;
- full classified blocker records, including origins and lineage;
- `next_instructions` only from real repository failure records—never fabricate commands, evidence, or remediation to make the array look complete;
- the repository's `ADDRESSED:` and final `DONE:` contracts.

Run the entire payload through the shipped recursive sanitizer, write it outside every repository, read it back, and round-trip the classified records through the shipped `Classification.from_dict` (or current equivalent). Verify the deduplicated ID set and per-ID origin counts before launching a builder.

An empty `next_instructions` array is preferable to invented failure records when the repository's normal writer would have no gate failure records for reviewer-only blockers; the classified blocker records remain the bounded repair specification.

## 3. Open only the remaining attempt

Create a fresh exact-head worktree and verify it is clean. Re-read the live PR head immediately before launch. Invoke the repository-owned builder adapter with:

- the truthful remaining attempt number;
- the frozen ledger path;
- the exact head and branch;
- the configured signature and task-scoped tool/MCP settings.

Do not edit a terminal journal to pretend the manual triad occurred inside it. Do not initialize a new attempt-zero run after repair work has already consumed attempts. The recovery handoff preserves the global cap; it does not reset it.

## 4. Verify the builder and invalidate old evidence

After the builder exits:

1. Parse its authoritative final marker and `ADDRESSED:` lines against the frozen ID set.
2. Require every frozen blocker to be addressed or a bounded corrective rerun/refusal path to fire according to the repository contract.
3. Verify the new commit independently in the builder worktree, remote branch, PR commit list, and PR `headRefOid`.
4. Fetch the signed builder comment posted after launch and verify author, signature, and new full SHA by immutable ID.
5. Confirm the worktree is clean and no unrelated paths changed.

The push invalidates the recovered gate and A/B/Auditor evidence. Run the complete configured gates and a fresh ordered triad on the new head. Never carry a pass or blocker disposition forward merely because the code change was narrow.

## Readback distinctions

- Submitted reviews carry GitHub `commit_id`; require it to equal the exact head.
- Conversation comments do not carry `commit_id`; require the canonical `HEAD=` declaration and exact body parity instead.
- A relay or watchdog exit code proves only transport/process completion, not artifact validity.

## False-success traps

- Launching cycle 2 from A/B consensus before the Integration Auditor is published and read back.
- Treating three repeated finding lines as three blockers instead of one blocker with three origins.
- Dropping an auditor-only blocker without checking its authoritative source.
- Writing a simplified hand-made JSON list that loses provenance, lineage, sanitizer guarantees, or attempt accounting.
- Fabricating `next_instructions` to satisfy prompt prose.
- Reusing an old builder worktree or blocker file after the PR head drifts.
- Treating manual recovery as permission for a third repair cycle.
