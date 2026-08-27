---
name: tracker-artifact-closeout
description: "Attach locally generated artifacts to issue trackers, reconcile linked GitHub work, complete acceptance checklists, and close tracker issues with direct readback evidence."
version: 1.3.2
author: Hermes Agent
metadata:
  hermes:
    tags: [issue-trackers, linear, artifacts, attachments, closeout, github]
    related_skills: [linear, github-operations, productivity-integrations, creative-html-visual-artifacts]
---

# Tracker Artifact Closeout

## Purpose

Use this class-level workflow when a tracker issue needs one or more of the following as part of completion:

- a local PNG, PDF, HTML report, diagram, or proof packet uploaded and attached;
- an inline visual comment plus a durable named attachment;
- a linked pull request merged and its branch/worktree cleaned up;
- acceptance checkboxes updated from verified evidence;
- the tracker issue moved to Done/Completed with a final evidence note.

This skill coordinates the closeout seam. Provider-specific tracker CRUD remains governed by the provider skill (for example `linear`), GitHub merge mechanics by `github-operations`, and artifact generation/visual QA by the relevant creative or productivity skill.

## Core invariants

1. **Read before write.** Fetch the current issue body, state, attachments, comments, workflow states, linked PR, and relevant review surfaces before mutating.
2. **Artifact bytes must be durable.** A local path or chat upload is not a tracker attachment. Upload the actual bytes to a tracker-supported durable URL.
3. **Attach and render are separate proofs.** When the user asks to attach an image, prefer both a formal attachment object and an inline Markdown image comment when the tracker supports both.
4. **Evidence precedes checkmarks.** Check only criteria proven by repository, review, merge, or artifact readback. Never use a status change to paper over a missing acceptance gate.
5. **Merge must be re-queried.** A successful merge command is not proof. Confirm `merged: true` or equivalent from the live PR API before tracker completion.
6. **Deletion means all requested scopes.** If branch deletion is requested, verify remote branch, local branch, remote-tracking ref, feature worktree, and any clean task-owned disposable reviewer worktrees independently. Sync the clean default branch first. Prefer `git branch -d` when ancestry proves the branch merged; for a verified squash merge, `git branch -D` is allowed only after proving the merged commit's tree exactly equals the reviewed feature-head tree, preserving the feature tip, and proving every owning worktree clean.
7. **Closeout is directly readable.** Capture attachment IDs, comment IDs, merge commit, final tracker state, and checkbox counts, then read them back by stable IDs.
8. **Successor wiring precedes terminal closure.** When closeout creates a re-pilot, qualification, or follow-up, create and verify the successor, wire predecessor/related-target relations, and update the open parent train before moving the predecessor to Done. Keep the earlier terminal pilot closed and the target execution tracker canonical; issue creation is not execution authority.
9. **Separate implementation completion from rollout proof.** An implementation issue may be complete even when real content, production data, deployment, or cutover smoke is deliberately out of scope. Conversely, passing fixture tests must never be described as live rollout proof. Inspect the issue's actual acceptance criteria, suggested/manual verification, out-of-scope boundary, merged PR language, current source data, and deployed surface; then either keep the issue open for an in-scope missing gate or create a verified successor for the separately authorized rollout before closing the implementation issue. When the same issue intentionally remains open until post-deploy checks finish, the implementation PR must use a non-closing reference such as `Refs #N`, not `Closes/Fixes/Resolves #N`. Verify the live structured closing relationship rather than trusting body text alone; after a PR-body edit, allow for GitHub metadata propagation and re-query before escalating to commit rewriting or force-push.
10. **Make deferred closeout executable.** If the user requires a tracker comment only after a currently open PR closes, do not rely on chat memory. Create a bounded, idempotent watcher that stays silent while the PR is open, detects merged versus closed-unmerged outcomes, searches for a unique marker before posting, and records the exact remaining acceptance work. Dry-run it against the open state, verify no comment was created, and read back the scheduled job. The eventual comment must preserve the open issue and distinguish shipped-but-needs-rollout-proof from implementation-not-shipped.
11. **Separate policy approval from implementation and activation.** A policy/decision child may close once the approved rule, durable source, and repository handoff are proven even when a consent UI, account setting, deploy, or production proof remains intentionally separate. Never erase the residual gate or silently check wording that claims live behavior. Create and verify the implementation/operations successor first, transfer the exact gate to its downstream owner, rewrite the completed criterion to say what was actually approved, and state the no-live/no-activation boundary in both the body and closeout comment.
12. **Closeout discovery can change the gate.** The original checklist is not permission to ignore a material risk found during fresh production/account/readback verification. If all original criteria pass but a directly relevant residual is discovered, add one explicit unchecked gate or create and verify a bounded successor before terminal closure. Name the new evidence and required authority; do not silently broaden into implementation or mark Done because the old checklist reached zero. Use `references/residual-gates-during-closeout.md` for classification, authority fallback, and readback sequence.
13. **Transport multiline Markdown as argv/file content, never shell-interpolated text.** Tracker bodies and comments commonly contain backticks, dollar signs, quotes, and newlines. Passing them through a shell command string can trigger command substitution while the helper still exits `0`. Prefer a non-shell subprocess argument vector that reads the body from a file, or a provider API call with JSON variables. Treat helper exit success as insufficient: refetch the issue and verify unique headings, identifiers, event names, hashes, authority clauses, and amendment count before accepting the mutation.
14. **A failed write may have partially mutated live state.** Do not blindly retry. Refetch the live body first, reconstruct the intended body from the last verified pre-mutation snapshot, apply one argument-safe full-body repair, then compare normalized semantics. Preserve historical content and ensure the amendment marker appears exactly once.
15. **Reconcile conditional branches explicitly.** When an owner selected one branch of an either/or gate (for example, waiving a legacy baseline), do not leave the unselected branch unchecked and do not convert it into an unexplained checkmark. Rewrite it as checked `Not applicable by owner decision` wording that cites the decision; reconcile dependent conditional verification the same way.
16. **A continuity child may close while monitoring stays open.** Cutover-day implementation/deployment/runtime proof can satisfy a child issue and one parent criterion without satisfying the parent’s four-to-eight-week monitoring contract. Update only the proven parent criterion and preserve the parent’s active state.
17. **Exact-byte evidence outranks cosmetic lint.** For SHA-256-reviewed captures, raw responses, and direct source extractions, do not normalize whitespace or line endings after acceptance merely to satisfy a broad diff check. Classify authored versus immutable paths, lint authored files, preserve accepted evidence bytes, and verify committed blobs against the accepted hashes. Follow `references/byte-bound-evidence-closeout.md`.

See `references/implementation-vs-rollout-closeout.md` for the evidence matrix, policy-child variant, and successor pattern. For production-proof reconciliation across GitHub, Linear, artifacts, durable knowledge, and an open monitoring parent, use `references/cross-system-production-proof-reconciliation.md`.

## Workflow

### 1. Freeze the pre-closeout packet

Record:

- issue ID/identifier, title, full description, current workflow state, and Done-state ID;
- acceptance section boundaries and unchecked count;
- linked PR URL, base/head branches, exact head, draft status, mergeability, reviews, comments, review threads, and checks;
- local feature worktree status and branch ownership;
- local artifact path, MIME type, dimensions/size when relevant, and source evidence.

Stop if the PR head moved after the final review, unresolved blockers remain, the worktree is dirty, or the artifact is missing/blank.

### 2. Upload and attach the artifact

Use the tracker's native upload flow rather than a temporary localhost URL or chat media path.

For a visual artifact:

1. request a signed upload slot using exact filename, MIME type, and byte size;
2. upload the exact bytes with strict signed-header parity;
3. create a named issue attachment using the returned durable asset URL;
4. add an inline image comment with a concise explanation and exact evidence key/SHA;
5. capture attachment and comment IDs;
6. query the intended issue and verify both objects exist.

For Linear's GraphQL/GCS flow, use `references/linear-file-upload-and-checklist-closeout.md`.

### 3. Merge the linked PR only under explicit authority

Before merge:

- verify repository identity and authentication;
- inspect all review surfaces and unresolved threads;
- confirm the live PR head equals the reviewed exact head;
- confirm mergeability and required checks;
- mark a draft ready only when the user has explicitly authorized the merge.

After invoking merge:

1. re-query the PR through REST/API and require `merged: true`;
2. capture the merge commit and merge timestamp, then verify the remote default ref and merge ancestry/parents;
3. fetch and fast-forward a clean local default branch to the verified merge commit before deleting the local feature branch;
4. prove the feature worktree and any disposable reviewer worktrees selected for cleanup are clean and task-owned, then remove them;
5. capture the feature-branch tip. Use `git branch -d` when the verified merge method preserves ancestry. For a squash merge, first prove the merged commit has the pre-merge base as its parent and its tree exactly equals the reviewed feature-head tree; only then may `git branch -D` remove the now-redundant local branch;
6. delete the remote branch, then `git fetch --prune origin`;
7. verify local default and remote default SHAs match;
8. independently verify remote branch, local branch, remote-tracking ref, and every requested worktree path are absent.

Do not close an umbrella GitHub issue when the PR intentionally used `Refs` rather than a closing keyword. For detailed cleanup ordering, load `verified-merge-closeout` and its `references/branch-and-worktree-cleanup.md`.

### 4. Complete the tracker contract

Refetch the issue body and state after external work is complete; GitHub integrations may have already moved the issue to a completed workflow state while leaving acceptance boxes and completion evidence untouched. Treat state and body contract as independent surfaces. Restrict checkbox edits to the acceptance section:

1. locate the exact section start and next heading;
2. count unchecked acceptance lines before mutation;
3. replace only criteria now proven by evidence;
4. append a dated completion section with attachment, PR, exact head, merge commit, validation/review evidence, branch cleanup, umbrella issue boundary, and durable-knowledge disposition;
5. set the workflow state to Done/Completed only if no acceptance checkbox remains unchecked and the issue is not already completed; omit a redundant `stateId` mutation when automation already completed it;
6. if closeout explicitly includes a parent train/roll-up, update only the completed child’s sequence/acceptance row and add a parent checkpoint while preserving the parent workflow state;
7. if closeout also creates a successor, wire and verify the successor plus parent sequence **before** moving the predecessor to Done. Keep the earlier terminal pilot closed, leave the target execution tracker canonical, and add only a concise pointer there. Use `references/successor-issue-and-parent-train.md`.

Use one full-description mutation when the tracker stores Markdown bodies. Preserve all unrelated issue text.

### 5. Add and verify the final closeout note

The final comment should name:

- attachment ID/title;
- PR URL and reviewed exact head;
- verified merge commit and live merged state;
- remote/local branch and worktree cleanup;
- acceptance count and final tracker state;
- intentionally still-open parent/umbrella issues;
- durable-knowledge outcome.

Capture the created comment ID and query it directly. Do not rely on `comments(last: 1)` ordering.

## Pitfalls

- Treating a successful signed-slot request as proof the upload bytes landed.
- Omitting the signed MIME header and receiving a storage signature mismatch.
- Reusing an expired signed URL after correcting headers; request a fresh slot.
- Creating only an inline image comment when the user explicitly asked for an attachment.
- Assuming GraphQL HTTP 200 means success without checking `errors` and mutation `success`.
- Parsing a successful helper response at the wrong JSON path and retrying a mutation that already landed; inspect the response before retrying.
- Treating an exact string mismatch caused only by tracker normalization (for example, stripping one trailing newline or normalizing checked-box case) as a failed mutation. Re-fetch the object by stable ID, compare normalized semantics and key counts, and never repeat the mutation until live state proves it did not land.
- Verifying only lowercase `- [x]` after a tracker normalizes checked boxes to uppercase `- [X]`.
- Counting checkboxes across the whole issue instead of the acceptance section.
- Reporting branch deletion when the remote ref is gone but the local branch, remote-tracking ref, feature worktree, or task-owned reviewer worktrees remain.
- Deleting the local branch before syncing the default branch, or force-deleting after a squash based only on GitHub's merged state. A squash lacks branch ancestry: require exact reviewed-head binding plus merged-tree equality before `-D`; otherwise stop.
- Treating an integration-driven Done transition as proof the acceptance body and completion evidence were reconciled.
- Moving a predecessor to Done before a newly requested successor, dependency direction, and parent train are verified—then needing to amend a completed child after the fact.
- Reopening a completed terminal pilot or duplicating the target execution tracker instead of creating one bounded, non-executing successor.
- Marking Done before live merge verification or while an acceptance criterion is still unproven.

## Verification checklist

- [ ] Current issue, workflow states, linked PR, and review surfaces were read before mutation.
- [ ] Artifact bytes uploaded successfully with correct MIME type and byte count.
- [ ] Formal attachment ID and inline comment ID were captured and directly read back.
- [ ] PR was re-queried and `merged: true` verified.
- [ ] Merge commit captured; local and remote default branches match when synced.
- [ ] Requested remote branch, local branch, remote-tracking ref, feature worktree, and task-owned reviewer worktree deletion each verified.
- [ ] Acceptance section has the expected checked count and zero unchecked criteria, independent of any automatic workflow-state transition.
- [ ] Final tracker state is a completed-type workflow state.
- [ ] Final child and authorized parent closeout comments were queried directly by ID.
- [ ] Parent/umbrella issue and durable-knowledge boundaries are explicit.
- [ ] When a successor was created: predecessor, successor, parent train, relation direction, target-tracker pointer, and non-execution authority were each read back.
- [ ] For a policy-child closeout: the approved decision/source, coding successor, downstream operations gate, durable-knowledge readback, and explicit no-live/no-activation statement were each verified independently.

## References

- `references/linear-file-upload-and-checklist-closeout.md` — Linear signed upload, formal attachment, inline comment, acceptance, and completion readback.
- `references/implementation-vs-rollout-closeout.md` — evidence matrix plus implementation/rollout and policy/approval successor patterns.
- `references/residual-gates-during-closeout.md` — classify material risks discovered during final proof, preserve authority boundaries, and close only after direct remediation readback.
- `references/successor-issue-and-parent-train.md` — ordered predecessor/successor/terminal-pilot/target-tracker reconciliation before terminal closure.
- `references/byte-bound-evidence-closeout.md` — preserve independently accepted source bytes, scope cosmetic lint to authored files, and verify committed blobs against exact hashes.
- `references/safe-multiline-tracker-mutations.md` — argument-safe Markdown body/comment transport, suspicious-write repair, and normalized semantic readback.
- `references/cross-system-production-proof-reconciliation.md` — reconcile merged implementation, deployment/runtime proof, conditional tracker branches, durable knowledge, and a still-open monitoring parent.
