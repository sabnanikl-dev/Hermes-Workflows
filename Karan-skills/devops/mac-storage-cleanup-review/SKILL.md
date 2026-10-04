---
name: mac-storage-cleanup-review
description: "Use when auditing Mac storage for approved cleanup."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [macos, storage, cleanup, approval, html]
---

# Mac storage audit and cleanup approval

## When to Use

Use for user-owned Mac storage audits with interactive HTML approvals returned before implementation. Load `artifact-output-governance`, `creative-html-visual-artifacts` and `github-operations` as relevant. This procedure grants no deletion authority.

## Read-only audit

- Start with live `df` and targeted `du`. Verify the runtime host, persist batches as JSON, and aggregate/deduplicate with code.
- Prioritize large replaceable caches/installers over personal files. Inspect personal metadata only within scope; never bulk-read vaults or credentials.
- Record permission errors and coverage limitations. Do not elevate or bypass protections. Explain APFS shared-container semantics and allocated footprint versus guaranteed reclaimed space.
- Modification dates do not prove last use. Directory mtime does not prove latest child-file activity.
- Cache names are not safety boundaries: npx can host running MCP/CLI processes; browser cache trees can contain persistent profiles; executable runtimes can live in `.cache`. Separate regenerable data from state/runtime data.
- Hardlinks, APFS clones/snapshots and active open files can reduce savings. For prune-only proposals, label full store footprint an upper bound; never authorize whole-store deletion.
- Historical databases, snapshots and checkpoints are not redundant without preservation proof. Verify a newer restorable alternative and unique-history retention first.

## Git preservation

- Discover nested worktrees beyond shallow project roots. Use `GIT_OPTIONAL_LOCKS=0` for read-only git; avoid initial fetch/prune, checkout or index changes.
- Check HEAD, branch, tracked/untracked state, ignored-file inventory, stashes and shared gitdir links. Clean status excludes ignored credentials, local data and evidence.
- Commits absent from cached remote refs are not necessarily unpushed: refs may be stale, deleted, squash-merged or force-pushed. Label uncertainty rather than claiming loss.
- A merged PR proves only its merge. Require current commit preservation and unique-file checks before worktree removal. Protect dirty/unresolved paths. Keep branches/shared Git history; use Git-aware removal, never force removal.

## Portable review artifact

- Keep original inventory/evidence and standalone HTML in a task-specific project directory, not scratch. Freeze the manifest before owner review; fresh scans require a separate revision.
- Every item needs a stable ID, exact paths, footprint, rationale, action, caveats and eligibility. Check eligible paths for ancestor overlaps before summing; exclude protected/reference rows from reclaim totals.
- Default all items to Unreviewed. Only Approve cleanup after checks grants removal permission; Keep, Investigate and Unreviewed do not. Protected items must lack an approval option. Notes may narrow/block scope; conflicts require clarification.
- State whether removal is permanent. Approval excludes surrounding directories, changed/new unique content, service shutdowns, remote branches and unrelated changes.
- Export newly named reviewed HTML with embedded JSON decisions/notes and original-manifest digest. Do not depend on localStorage or Save Page. Offer JSON backup/share fallback; warn that unexported edits vanish on reload.
- Escape `<` and script terminators in embedded JSON; render paths/notes as escaped text. Include no deletion code.
- Test select → download → fresh isolated file reopen → independent parse. Test protected/default decisions, literal HTML notes, filters, counts, tampering, responsive overflow, JS errors and external requests. QA fixture approvals are NON-AUTHORITATIVE and must never be delivered as user decisions. Desktop fallback tests do not establish native mobile sharing support.

## Returned approvals

- Verify direct user provenance. Digests bind integrity, not identity or signatures.
- Parse returned JSON without executing returned HTML. Map IDs to original targets; ignore supplied path/action/code substitutions. Reject unknown/missing IDs, protected approvals, mismatched digests and inconsistent totals.
- Recheck exact path identity, symlinks, nested contents, active consumers and preservation. New/changed unique content requires re-review; unresolved gates mean skip. Coordinate app/service shutdown separately.
- Respect partial-prune actions and literal enumerated targets. Do not broadly empty Trash; moving data to same-volume Trash does not reclaim space.
- Verify per-item outcomes and actual `df` change. Distinguish removed footprint from new free capacity; report skipped/blocked items honestly.

## Closeout

Transient inventory/approvals belong in task artifacts, not vault notes or permanent memory. Save reusable procedures here. Deliver the original zero-approval HTML with open → decide → export → return instructions.
