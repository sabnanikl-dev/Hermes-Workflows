---
name: pull-request-review-preflight
description: "Preflight an implementation PR before independent review: issue-lifecycle metadata, exact-head equality, immutable credential-free review packets, and bounded reviewer execution."
version: 1.0.1
---

# Pull Request Review Preflight

## Trigger

Use after a builder has opened or updated a PR and before launching independent reviewer lanes. This skill applies when correctness depends on the exact PR head, issue-closing behavior, frozen GitHub evidence, reviewer credential isolation, or reproducible verification packets.

It complements end-to-end build/review orchestration skills. Those skills choose and supervise lanes; this skill proves the artifact handed to those lanes is the right PR, head, lifecycle state, and evidence snapshot.

## Required outcome

Do not start technical review until all of these are true:

- the PR's live base/head/draft state matches the task contract;
- local HEAD, remote branch head, PR `headRefOid`, and final PR commit are identical;
- live issue-closing relationships match the lifecycle contract;
- canonical verification was run at that exact head;
- the review packet is credential-free, complete, digest-verifiable, and read-only;
- reviewer worktrees are detached, clean, and bound to the packet head;
- reviewer write needs are deliberately classified as read-only, `/tmp` evidence-only, or bounded disposable-worktree writes.

## Preflight sequence

1. **Reconstruct the lifecycle contract.** Determine which issue the PR implements and whether merge should close it, merely reference it, or leave an umbrella/parent issue open.
2. **Query live GitHub state.** Read the PR body, commits, `headRefOid`, final commit, closing references, base/head names, draft state, mergeability/checks, reviews, comments, inline comments, and review threads.
3. **Prove exact-head equality.** Require local = remote = PR head = final PR commit. Stop on any mismatch.
4. **Prove issue behavior from structured state.** Inspect `closingIssuesReferences`; do not infer lifecycle behavior only from title/body keyword scans. If any required acceptance criterion can only be proven after merge or deployment (for example, production MIME behavior, crawler refresh, or validation on real external surfaces), a PR that uses `Closes #N` is lifecycle-blocked while that evidence remains open. Prefer `Refs #N`, keep the issue open through deployment, and close it only after recording the live evidence. If this is repaired by editing only the PR body, preserve exact-head implementation reviews: re-read the live body and `closingIssuesReferences`, confirm the code head is unchanged, and perform a metadata-focused recheck rather than restarting technical review.
5. **Run canonical repository verification.** Capture real command output at the exact head. A green suite does not override metadata or contract blockers.
6. **Prepare isolated review worktrees.** Use clean disposable detached worktrees at the exact head. Reviewer processes receive no builder session history or mutation authority.
7. **Freeze the adapter-native credential-free packet.** Include the issue/PR contract, exact-head identity, all review surfaces, checks, changed paths, canonical verification output, and UI evidence manifest when applicable. If the repository owns a packet builder, binding string, schema validator, or lane sequence field, use that implementation directly; a structurally rich lookalike packet is not interchangeable with the adapter's protocol.
8. **Verify packet integrity and launch compatibility.** Hash payloads without self-referential checksum entries, record the manifest digest outside the packet, make the packet read-only, and exercise the exact reviewer adapter's cheap preflight/binding checks before spending a model run.
9. **Launch reviewers with bounded write policy.** Prefer read-only. Use the approved `/tmp` evidence area or a wrapper's disposable workspace-write mode only when tests inherently create files.
10. **Recheck before relay.** Any head change invalidates packet and reviewer artifacts. Re-query the live head immediately before transporting signed review results.

## Fail-closed conditions

Stop review launch when:

- structured closing linkage contradicts the issue lifecycle contract;
- any exact-head identity differs;
- the packet contains credentials, broad environment dumps, or mutable live-source pointers instead of frozen evidence;
- the packet is a hand-built approximation that does not satisfy the repository adapter's canonical binding/schema/sequence checks;
- the checksum manifest cannot verify its payloads;
- the reviewer needs unsafe sandbox expansion or credentials merely to run tests;
- a disposable worktree is dirty before review;
- the PR changed after packet generation.

Classify environment-only test failures separately from product failures. A reviewer unable to create temporary files has not demonstrated a product regression.

## Recovery principles

- Metadata contamination with an unchanged trusted code head is a metadata/transport repair, not automatically a new builder cycle.
- Branch-derived issue-closing linkage may require a clean replacement branch and PR; editing prose alone may not remove it.
- Preserve supersession evidence: close the bad PR unmerged with a pointer to the verified replacement.
- Never weaken reviewer credential isolation to compensate for packet or temporary-directory mistakes.

## Support reference

- `references/metadata-linkage-packet-and-sandbox-pitfalls.md` — hidden issue-closing linkage recovery, checksum-manifest construction, and read-only reviewer temp-file policy.
- `references/adapter-native-packets-and-live-transport-smoke.md` — canonical repository packet protocols, cheap adapter preflight, exact shipped-adapter smoke, and per-lane ordered packet refresh.

## Verification certificate

Before reviewer launch, record:

- repository + PR;
- packet timestamp;
- base/head branch;
- full exact SHA;
- local/remote/PR/final-commit equality result;
- closing-reference count and intended issue lifecycle;
- canonical verification commands/results;
- packet path + payload-manifest digest;
- reviewer worktree paths and cleanliness;
- write/sandbox mode chosen for each lane.

This certificate is evidence for orchestration, not merge approval.
