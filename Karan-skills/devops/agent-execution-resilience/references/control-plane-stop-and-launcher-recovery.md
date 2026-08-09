# Control-plane stop and launcher recovery

Use this reference when a prover/agent produced retained state but orchestration around it failed, when `needs-karan` is caused by contradictory governing text, or when a hardened launcher exits before useful work is produced.

## Artifact truth outranks wrapper status

An outer shell, process supervisor, or notification can fail after the inner tool has already completed. Before rerunning anything:

1. Read the retained JSON report, stderr, and state file.
2. Re-read the live PR head, reviews, comments, threads, draft state, and commit list.
3. Compare local HEAD, remote feature ref, and live `headRefOid`.
4. Treat relayed artifact IDs in state plus GitHub readback as authoritative. Never relay the same artifact again merely because the wrapper exited nonzero.

For portable exit capture, avoid shell-reserved names such as zsh's `status`:

```sh
pr-prover/bin/pr-prover run --config "$config" --json >"$report" 2>"$stderr"
rc=$?
printf 'PR_PROVER_EXIT=%s\n' "$rc"
exit "$rc"
```

The durable rule is to separate the inner tool's retained outcome from the wrapper's exit and verify both.

## Contract-caused `needs-karan`

`needs-karan` is a deliberate judgment barrier, not a blocker to silently send to a builder.

If the user has explicitly authorized continued execution and the finding exposes an internal contradiction rather than a new product choice:

1. Reproduce or inspect the contradiction against the live governing issue and mission lifecycle.
2. Choose the narrow interpretation that preserves the stronger safety invariant and existing normative lifecycle.
3. Add a dated clarification; do not rewrite or erase the original requirement.
4. State exactly which phrase the clarification supersedes and what remains unchanged.
5. Apply the same additive clarification to every governing tracker surface future packets will read.
6. Directly read back each mutation before proceeding.
7. Freeze the genuine code-blocker ledger separately. Do not mislabel the contract clarification as a code blocker.

If resolution would choose new scope, authority, UX, policy, or risk tolerance, stop for Karan.

## Freeze and deduplicate the repair ledger

Independent lanes can assign different IDs to the same defect. Collapse them only when mechanism, reproduction, and remediation are genuinely identical. Preserve aliases and provenance from every lane.

A manual recovery blocker packet should contain:

- repo, PR, exact old head, attempt, and mode;
- one canonical blocker ID plus aliases;
- every source artifact ID;
- exact reproduction and affected invariant;
- bounded `next_instructions`;
- explicit escalation conditions;
- non-blocking findings marked out of repair scope; and
- any verified additive contract clarification.

Never include unresolved `needs-karan` findings in the builder packet.

## Repair-cycle accounting

Do not consume a repair cycle merely because a launcher command was attempted.

- Usage/schema/path rejection before the agent starts, with a clean unchanged worktree and no commit/push/comment: **no cycle consumed**.
- Agent started but produced uncommitted edits: the cycle is open; inspect and recover it rather than launching a duplicate.
- Commit or push exists: the cycle is consumed even if the final marker or wrapper failed.
- A partial fix inside the same open cycle follows the parent skill's corrective-rerun rule; launcher recovery is not an unlimited retry loophole.

Verify cycle state from worktree cleanliness, local logs, actual process state, remote PR commits, and signed fix-comment readback—not process status alone.

## Hardened launcher preflight

Before launching a repository-owned adapter:

1. Read its current usage block; do not reuse an earlier run's argv.
2. Confirm every required argument, especially branch and exact head.
3. Discover and validate the repository-owned empty MCP config rather than hardcoding a stale path.
4. Validate model/CLI availability with a bounded smoke when needed.
5. Keep stdout/stderr in retained files and use a realistic timeout.

If the process supervisor reports an ambiguous exit (`null`, missing marker, empty logs), check the actual child process before retrying. If the child is alive, attach a separate completion watchdog and do not launch a duplicate. Quiet is expected.

## Post-builder proof

A builder run is not successful until all of these agree:

- signed terminal marker;
- clean worktree;
- local HEAD;
- remote feature ref;
- live PR `headRefOid`;
- new commit present in `gh pr view --json commits`; and
- signed exact-head fix comment directly read back.

Any head change invalidates all prior exact-head reviewer evidence. Refresh packets and rerun the complete ordered triad.
