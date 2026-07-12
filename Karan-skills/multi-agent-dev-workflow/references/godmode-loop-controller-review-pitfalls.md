# GodMode loop-controller review/fix pitfalls

Use this reference when building or reviewing GodMode's automatic review/fix loop, or any dashboard/controller that chains async agent stages from observable run state.

## Session-derived lessons

### 1. Long builder prompts can stall before edits; prefer pointer-first prompts
When delegating a large GitHub issue to Claude Code, avoid pasting the entire issue body unless needed. A long prompt that included the full issue body stalled with no stdout and no file changes. A shorter pointer-first prompt worked: tell the builder the repo path, branch, PR/issue number, governing rules, and require it to read the live issue/PR itself.

Pattern:
- Provide repo path, branch, GitHub repo, issue/PR number.
- Tell the builder to read `AGENTS.md`, docs, and `gh issue view` / `gh pr view` itself.
- Keep completion marker + verification requirements explicit.
- Verify the worktree is moving (`git status`, `git diff --stat`, process tree) before killing a quiet run.

### 2. Watchers must surface verification failure; no silent polling loops
For fix-commit watchers, `needs_refresh`, partial verification, `gh`/network/auth failures, or thrown watcher errors must not leave the UI silently polling forever. Use the same visible halt surface as other stage failures.

Safe pattern:
- Permit at most one logged transient retry when the failure class is explicitly transient.
- If the retry also fails, disarm the watcher, set `waitingOn: halted` / `lastError`, and stop auto-advancement.
- Reset retry budget only after a complete verification poll.
- Test: partial verification -> one retry -> visible halt and watcher inactive.
- Test: thrown watcher error -> one retry -> visible halt and watcher inactive.
- Test: transient partial followed by complete poll -> no halt, watcher continues.

### 3. Async stage preemption must cover both stop-state and same-stage manual dispatch
It is not enough to re-check that the run id/root still match after an awaited verification call. Operator pause/cancel is one preemption case, but manual same-stage dispatch can also advance the run while the loop-owned stage is awaiting.

Risk example:
1. Auto loop starts `start_reviewers` from `pr_opened`.
2. Handler awaits live #9 verification.
3. Operator/manual dispatch also advances the run to `reviewers_running`.
4. Original loop stage resumes and still passes a too-broad guard because `reviewers_running` is launch-legal in general.
5. Duplicate reviewer sessions/PTYs/artifacts can be installed after manual preemption.

Safe pattern:
- Capture enough stage identity/generation before the await (status, transition generation, or a controller preemption token).
- After every await and before any side effect, re-read live run state and abort if the captured stage no longer owns the transition.
- Treat operator/manual preemption as a stop, not a halt/retry error.
- Add regression tests for pause/cancel **and** manual same-stage dispatch during an in-flight awaited stage.

### 4. Pre-await helpers must not mutate stale run state before the caller's post-await guard
When reviewing async recovery/fix paths, check not only the final destructive side effect (for example `openPtySession`) but also any awaited helper that records global run state before returning. A caller-level post-await guard is too late if the helper already persisted or emitted stale data.

Safe pattern:
- Snapshot run id and operated-project/root before awaits.
- Re-check identity inside helpers immediately before any global/persistent write.
- Pass `expectedRunId`/expected project root into recording helpers, or split “prepare” from “record” so the caller records only after revalidation.
- Add regression tests where the active run/project changes while worktree prep or another async helper is in flight, and assert no stale worktree/session metadata is attached to the new current run.

### 5. Re-review should target the exact previous blocker
After a fix commit, launch reviewer-specific re-reviews that name the prior blocker and ask whether it is fully resolved, plus a quick scan for new regressions. Do not ask for a full fresh review unless the diff scope changed substantially; targeted re-review keeps the loop tight and makes remaining blockers precise.

### 5. Final “mergeable” is a synthesis gate, not just a GitHub field
For same-account reviewer loops, Codex may post signed PR conversation comments rather than formal GitHub review objects. `latestReviews` / `reviewDecision` can be empty even after both reviewers passed, and earlier `BLOCKING` comments remain in the conversation history. The closeout must synthesize the full sequence:

- Verify PR `headRefOid` equals local `HEAD`, and the PR commit list contains the latest fix commit.
- Verify CI/checks are green on that head.
- Re-read PR conversation comments and confirm every earlier signed `BLOCKING` finding has a later signed pass/fix/re-review comment that explicitly resolves it.
- Check formal reviews, inline review comments, and GraphQL review threads too; “empty” there is useful evidence that no unresolved inline/formal blocker remains.
- Only then report “mergeable / agent-clean.” Keep “Karan retains merge authority” separate from GitHub’s `MERGEABLE` field.

## Useful verification checklist

- PR head SHA equals local `HEAD` and PR commit list contains the fix commit.
- CI is green on the new head.
- Local `npm run typecheck`, `npm test`, `npm run build`, and smoke/e2e command pass when relevant.
- For GodMode app PRs that touch Electron main/preload/renderer UI, IPC, PTY launching, project selection, resume/discard surfaces, or operated-project/app-repo boundaries, run `npm run smoke` after the production build. The smoke test verifies the packaged Electron path, selected operated-project root, preload bridge/API surface, PTY launch cwd, dogfooding badge, graceful GitHub degradation, and stray-process cleanup — coverage that typecheck/unit/build alone do not provide.
- Reviewer comments were posted to GitHub and then re-read from the PR comments/reviews surfaces.
- Earlier signed blocker comments have later signed pass/fix comments on the same head or a newer fix head.
- If tool-call budget is low, stop at a verified checkpoint instead of launching another builder/fix cycle you cannot observe through verification.
