# Reviewer Identity Relay and Shared-Account Review State

Use this pattern when two independent reviewer lanes share one GitHub reviewer account, or when a reviewer subprocess completes its audit but cannot post because its sandbox temporarily loses GitHub API access.

## Identity recovery without switching the operator account

The dedicated legacy keychain item may be stale even when `gh` has a valid reviewer login. Prefer a scoped token obtained from the current `gh` keyring:

```bash
REVIEWER_TOKEN=$(gh auth token -u karanagent1)
GH_TOKEN="$REVIEWER_TOKEN" gh api user --jq .login
# expected: karanagent1
```

Use `GH_TOKEN="$REVIEWER_TOKEN"` only on reviewer-posting/readback commands. Leave the operator's active `gh` account unchanged.

Do not preserve a transient `401` as a belief that the reviewer identity is unavailable. Verify the fallback token and continue only when the identity readback matches the configured reviewer account.

## Two reviewer roles sharing one GitHub account

GitHub collapses the effective review state by account. A later formal approval from Reviewer B can neutralize Reviewer A's live `CHANGES_REQUESTED` state before the blocker is fixed.

Use this durable artifact split:

- **Reviewer A:** formal review (`--request-changes` or `--approve`).
- **Reviewer B:** signed PR conversation comment containing verdict, current head SHA, blockers, checks, and reviewer-role signature.
- After a fix, Reviewer A submits a new formal approval on the new head, superseding its own old change request; Reviewer B posts a new signed current-head comment.

Use the full reviews API plus role signatures and commit IDs when proving both lanes:

```bash
gh api repos/<owner>/<repo>/pulls/<pr>/reviews

gh api repos/<owner>/<repo>/issues/<pr>/comments
```

Do not count a pass artifact tied to the old head.

## Reviewer completed, posting failed

If the reviewer audit completes with a machine-readable zero-blocker/pass result but its sandbox cannot POST to GitHub:

1. Read the reviewer's final result and confirm it is tied to the expected current head.
2. Confirm the reviewer worktree is clean.
3. Use the parent Hermes lane to relay the completed artifact with the scoped reviewer token above.
4. Preserve the intended artifact type: Reviewer A formal review; Reviewer B signed conversation comment.
5. Add an `Artifact note` stating that the independent reviewer completed the audit and Hermes relayed it under the configured reviewer identity because the reviewer sandbox could not post.
6. Read the live artifact back and verify author, commit/head reference, verdict, and URL.
7. Disclose the relay in the final prover report. Never silently post it from the PR author's/operator account.

This is a degraded posting path, not a degraded review, when the independent reviewer completed the full audit and only transport failed.

## Idle reviewer after final output

A Codex reviewer can finish reasoning yet remain alive because long-lived MCP/CodeGraph children do not exit. Before terminating the reviewer:

- inspect process tree and CPU;
- inspect reviewer worktree status;
- check whether a result file or complete review body exists;
- query GitHub directly to see whether the artifact posted despite stale subprocess output.

If the worktree is idle and only MCP/CodeGraph children remain, terminate the CodeGraph/MCP child first and wait for the parent to exit. Do not kill an active reviewer merely because stdout is quiet.
