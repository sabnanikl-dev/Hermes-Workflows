# Interrupted-run handoff and resume packet

## Resume packet

A fresh session/job should receive all of this explicitly:

```markdown
# Resume <issue/task>

## Identity
- Repo:
- PR / tracker issue:
- Dedicated worktree:
- Branch:
- Last committed local SHA:
- Last verified remote/PR SHA:

## Preserved WIP
- Modified files:
- Untracked files:
- Diff statistics:
- `git diff --check` result:
- Known probe strays that must not be committed:
- Processes confirmed exited/running:

## Frozen blockers
1. ...
2. ...

## Artifacts
- Builder prompt:
- Settings:
- Empty MCP:
- Reviewer artifacts/transcripts:
- Probe scripts/results:

## Proof boundary
- Results proven for committed head:
- Results not yet rerun on WIP:

## Resume steps
1. Inspect state; never reset/clean/stash/checkout-over.
2. Smoke exact pinned model/runtime.
3. Complete existing WIP under frozen blockers.
4. Independently inspect scope and remove verified strays.
5. Run deterministic + live former-red verification.
6. Commit/push only if authorized; verify remote/PR exact head.
7. Run fresh exact-head reviewers.
8. Update/read back tracker and PR evidence.

## Authority
- Authorized:
- Explicitly forbidden:
```

A scheduled resume prompt must be self-contained because cron runs in a fresh session. It must explicitly forbid recursive scheduling.

## Linear handoff comment

Use this structure:

```markdown
## Paused handoff — <short reason>

**Handoff timestamp:** <timezone-aware timestamp>
**Issue status:** <live status>
**Repository / PR:** ...
**Dedicated worktree:** ...
**Branch:** ...
**Last committed/pushed head:** `<full sha>`

### Why this is paused
<quota/auth/timeout/sandbox/frozen blocker summary>

### Preserved local state
- No destructive Git operation occurred.
- Exact modified/untracked scope.
- Diff size and `git diff --check`.
- Known temporary strays.
- Process exit reasons.

### Resume artifacts
- Prompt/settings/MCP/reviewer/probe paths.
- Scheduled continuation job ID/time, if any.

### Mandatory resume sequence
1. ...

### Last known proof boundary
<what passed on committed head; what is unverified on WIP>

**Current conclusion:** <not merge-ready / blocked / resumable>
```

## Direct verification

After mutation:

1. Capture `commentCreate.comment.id`.
2. Query `comment(id: "<id>")` directly.
3. Confirm issue identifier, issue state, and two unique handoff phrases.
4. Report the verified comment ID.

Do not use `comments(last:1)` as proof; ordering can be surprising.

## Scheduled continuation

When the provider gives a near-term reset:

- schedule once just after the reset;
- attach delivery to the originating session when follow-up is conversational;
- include exact workdir and required skills/toolsets;
- state existing external-action authorization and no-merge boundary;
- require an exact-model smoke before resuming;
- require the job to report/preserve state if quota remains blocked;
- forbid the cron-run session from creating more cron jobs.

## Common handoff errors

- saying “WIP preserved” without listing untracked files;
- quoting prior-head test counts as if they cover WIP;
- omitting the committed/remote SHA split;
- omitting model pin or auth-safe launch shape;
- failing to name uncertain external side effects;
- omitting no-merge/deploy/credential boundaries;
- leaving a comment but not verifying its returned ID.
