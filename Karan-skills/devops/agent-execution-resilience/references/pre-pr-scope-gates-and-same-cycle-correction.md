# Pre-PR Scope Gates and Same-Cycle Builder Correction

Use this when an approved issue-to-PR plan carries measurable implementation boundaries such as maximum runtime lines, per-module limits, allowed subsystem count, changed-path boundaries, or a requirement to remain materially smaller than a failed predecessor.

## Why this gate belongs before the PR

A builder can produce correct code and green tests while still exceeding the approved architecture. Opening the PR first turns an implementation-boundary miss into public review churn and may invite reviewers to debate a scope Karan already froze. Treat quantitative scope like tests and trailers: it must pass before the candidate PR is opened.

## Pre-PR sequence

1. Freeze the approved plan, exact base SHA, fresh branch, and worktree before mutation.
2. Put each measurable boundary in the builder packet, including how it will be counted. Distinguish runtime modules, tests, hand-written docs/config, and generated lockfiles.
3. After the builder pushes, independently read back:
   - local and remote branch SHA equality;
   - clean worktree;
   - every commit trailer;
   - changed paths and `git diff --numstat`;
   - physical lines per runtime module and total;
   - deterministic test names/counts and full-suite result.
4. If any approved limit is exceeded, **withhold the PR**. Do not call the branch merge-ready merely because behavior is green.
5. Freeze one narrow scope-correction packet for Claude. It should name the exact overage and forbid weakened tests, snapshots, minification, history rewrites, new subsystems, or error-message degradation.
6. Treat the correction as the same initial build cycle when no PR exists and the blocker is a direct omission from the approved builder contract. Require a new normal commit with the repository trailers; never amend or force-push to hide the miss.
7. Re-run the complete exact-head proof, not only the line count. Confirm required tests remain present and unchanged in meaning.
8. Open the conversation-linked PR only after the scope, trailer, cleanliness, and full-suite gates all pass.

## Counting without gaming

- Count physical runtime lines because they represent review surface, but inspect non-comment/non-blank lines as diagnostic context.
- A reduction is legitimate when it removes duplicated control flow, redundant narration already owned by a contract doc, unnecessary parallel state, or repetitive adapters through clear data-driven structure.
- A reduction is not legitimate when it removes boundary rationale, weakens failure messages, folds statements unnaturally, deletes former-red probes, renames tests to hide coverage loss, or moves runtime code into a misleading category.
- Keep generated lockfile churn separate from hand-written scope. Tests and docs do not count against a runtime-only cap, but they also cannot be used to claim a total hand-written diff is small when it is not.

## Proposed-file deviations

A small additional module can be safer than forcing unrelated responsibilities together. When the approved plan's file list was explicitly frozen, eliminate the deviation if it can be done cleanly. Otherwise preserve the better boundary only when all quantitative caps pass, every module remains cohesive, the extra file introduces no new subsystem, and the PR describes the rationale for human/reviewer judgment.

## Launcher recovery is separate

If a noninteractive builder exits before mutation because the hardened launcher denied an approved read/edit surface, verify the clean base, absence of commits/pushes/PR changes, and unchanged blocker packet. Then correct the launcher once under the main skill's launcher-recovery rules. That is launcher recovery, not a scope-correction or repair cycle.

## Proof checklist

- [ ] PR does not exist while a frozen pre-PR scope gate is failing.
- [ ] Builder correction is Claude-owned and limited to the exact overage.
- [ ] No amend, reset, rebase, force-push, or trailer rewrite occurred.
- [ ] Every original deterministic regression remains and still passes.
- [ ] Runtime total and each module pass the approved limits.
- [ ] Hand-written additions remain materially within the approved comparison boundary.
- [ ] Local, remote, and eventual GitHub PR head equality is freshly proved after the correction.
