# Clean Hermes → Claude Code → CodexReviewer Loop Validation

Use this when dogfooding or validating the full multi-agent GitHub loop. A clean pass means the assigned agent performs each external mutation itself; Hermes verifies, but does not silently substitute.

## Clean-pass criteria

- Builder process is Claude Code, not Hermes fallback.
- Builder GitHub identity is the expected builder account.
- Reviewer process is CodexReviewer, not Hermes fallback.
- Reviewer GitHub identity is the expected separate reviewer account.
- Builder opens/pushes/comments on its own PR.
- Reviewer submits its own GitHub review (`APPROVE` or `REQUEST_CHANGES`).
- Hermes independently verifies PR author, reviewer author, commit SHA, review state, issue labels, and scope before reporting success.

## Failure/fallback cases

Mark the loop test as failed/fallback if any of these happen, even if the final PR state looks good:

- Hermes writes, commits, pushes, opens the PR, or posts the builder report after the builder could not.
- Hermes posts the review body after CodexReviewer could not submit it.
- Claude opens the PR using the reviewer token/account.
- The local commit is not verified in the remote PR commit list.
- Review state is inferred from agent output instead of live GitHub reviews API / `gh pr view`.

## Identity gates

Before Claude builder mutation:

```bash
env -u GH_TOKEN gh api user --jq .login
```

Expected: builder account.

Run Claude with reviewer token removed from the environment:

```bash
env -u GH_TOKEN claude --model 'claude-opus-4-8[1m]' --print --dangerously-skip-permissions --system-prompt-file AGENTS.md "..."
```

Before CodexReviewer mutation:

```bash
# Use the configured separate reviewer identity. Karan's default reviewer account is KaranAgent1.
# Current macOS Keychain location: service `hermes-codex-reviewer-github-token`, account `codex-reviewer`.
# Fetch reviewer tokens per process and do not export globally.
REVIEWER_TOKEN="$(security find-generic-password -s hermes-codex-reviewer-github-token -a codex-reviewer -w)"
GH_TOKEN="$REVIEWER_TOKEN" gh api user --jq .login
GH_TOKEN="$REVIEWER_TOKEN" codex exec --sandbox workspace-write "..."
```

Expected: `karanagent1` / KaranAgent1, not the builder/default `sabnanikl-dev` account. If the expected reviewer token cannot be found or the smoke test returns the builder account, stop and report the identity misconfiguration instead of silently falling back to same-account PR comments.

Do not rely on `gh auth status` inside Codex sandbox; use concrete `gh api user` / `gh pr view` calls.

## Reviewer submission fallback that still counts

If CodexReviewer itself cannot submit with `gh pr review` because of a transient transport/path issue, it may submit the review itself through the GitHub Reviews API:

```bash
cat > /tmp/review.json <<'JSON'
{
  "event": "APPROVE",
  "body": "...signed review body..."
}
JSON

gh api -X POST repos/<owner>/<repo>/pulls/<pr>/reviews --input /tmp/review.json
```

This still counts only if CodexReviewer executed the mutation and verified the result.

## Verification readback

Use both PR view and reviews API when possible:

```bash
gh pr view <pr> --repo <owner>/<repo> \
  --json author,headRefOid,commits,reviewDecision,latestReviews,mergeStateStatus

gh api repos/<owner>/<repo>/pulls/<pr>/reviews \
  --jq '[.[] | {user:.user.login,state:.state,commit_id,submitted_at,html_url}]'
```

Report the loop as clean only after the live PR author/reviewer/commit states match the expected accounts and SHAs.