# Post-edit verification-denial takeover

Use this when a scoped builder edited the intended files but stopped before commit because its execution policy denied tests or shell commands.

## Classification

| Observed state | Classification | Next action |
|---|---|---|
| No edits, commit, push, or external mutation | Launcher failure | Correct only the task-scoped launcher contract and rerun inside the same cycle. |
| Bounded uncommitted edits; required gates unrun | Incomplete builder candidate | Preserve the diff; default Hermes may independently verify and finish only under existing authorization. |
| Commit exists but no push | Incomplete handoff | Verify the exact commit, then push/read back if already authorized. |
| Push or comment may have happened before a later command failed | Ambiguous external side effect | Never retry blindly; query the target by SHA/ID/body first. |
| Candidate fails required gates | Unverified repair | Preserve evidence and route a fresh bounded builder or stop at the cycle cap. |

## Takeover checklist

1. **Freeze process state**
   - Read the complete builder log, not only the completion summary.
   - Confirm the process exited and no writer remains.
   - Record starting SHA, exit status, and which commands were denied or unrun.

2. **Prove absence or presence of side effects**
   - Compare local HEAD, remote branch SHA, PR `headRefOid`, and PR final commit.
   - Read current comments/reviews when the builder was authorized to publish.
   - Do not infer “nothing happened” from an exit code.

3. **Inspect WIP without cleaning**
   - Capture status, changed paths, full diff, diff statistics, and `git diff --check`.
   - Confirm the diff matches the frozen repair scope and does not alter protected product/evidence surfaces.
   - Exclude temporary probes from any future commit.

4. **Verify the candidate before documentation claims**
   - Run the deterministic suite and the exact former-red reproduction.
   - Include a repair-safety probe proving the fix did not overcorrect.
   - Derive test counts and documentation wording from actual output; never copy an unverified expected count from the worker prompt.

5. **Create and verify one exact commit**
   - Commit only the inspected bounded paths.
   - Preserve worker attribution when appropriate.
   - Rerun the required suite against the committed SHA, including diff checks and evidence binders.

6. **Push once, then verify separately**
   - Push the already-tested commit once.
   - Re-query local SHA, remote branch, PR head, final PR commit, and commit-list presence.
   - If a compound `push && verify` command fails after the push, split out read-only verification. A failed post-push parser or CLI flag is not permission to push again.

7. **Re-enter exact-head review**
   - Any new commit invalidates previous exact-head approvals.
   - Freeze fresh packets/worktrees and rerun only the risk-tier-required reviewers and dependent auditor.

## Stop conditions

Stop rather than taking over when authorization did not include commit/push, the diff exceeds the frozen ledger, another process may still be writing, required gates cannot be run independently, or the repair-cycle cap is exhausted.
