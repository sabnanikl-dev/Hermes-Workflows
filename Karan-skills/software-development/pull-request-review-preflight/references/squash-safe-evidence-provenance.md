# Squash-safe evidence provenance

Use this reference when a PR commits generated QA/evidence archives and a binder resolves repository state through a Git commit ID, tree, path inventory, or content hash.

## The false-green pattern

A PR can be completely green while its evidence points to a source commit that exists only on the feature branch. The binder passes because the branch ref keeps that object reachable. If the repository then squash-merges and deletes the branch, the source commit is not part of `main`; a fresh clone cannot resolve `git show <bound-commit>:<path>`, so mandatory binders and the full suite become red immediately after merge.

This is an integration defect, not a post-merge housekeeping item. A later pointer-repair PR may be truthful about identical bytes, but it still creates a broken-main interval and closes the implementation issue before its proof is durable.

## Preflight questions

Before independent review, establish:

1. What merge strategy will actually be used: squash, merge commit, or rebase?
2. Does any committed archive record a commit that is not already durable on the base branch?
3. Does a binder require that commit object to remain resolvable, or does it verify a merge-strategy-independent content identity?
4. After the intended merge and branch deletion, can a fresh repository run every mandatory binder without fetching the deleted feature ref?

Checking the current PR worktree is insufficient: it proves only that the feature branch currently supplies the object.

## Acceptable repair classes

- Prefer a narrow, fail-closed content provenance contract over the enumerated behavior-controlling files: stable path + byte hash inventory, deterministic aggregate identity, and negative tests for path/hash/inventory drift. The identity must not depend on a branch-only commit surviving integration.
- Alternatively, use a commit-preserving merge only when Karan explicitly approves that merge strategy and a fresh-clone verification proves the referenced object remains durable.
- Do not treat “merge first, repair the pointers afterward” as merge-ready for a high-risk activation, migration, consent, deployment, or control-plane PR.

A content-derived repair must continue to reject changed bytes, missing or additional behavior-controlling surfaces, rewritten provenance fields, and mismatched producer/binder expectations. Do not weaken exactness merely to make squash pass.

## Verification boundary

The terminal proof is the post-integration shape, not the feature branch:

- exercise the repository’s intended integration strategy in a disposable environment;
- ensure the original feature ref is unavailable;
- run the same binders and required suite a fresh clone of merged `main` would run;
- keep the implementation issue open until this passes.

## Evidence-producing gate hygiene

Browser/evidence producers often rewrite capture timestamps, volatile external-placeholder observations, or PNG encoding metadata even when rendered pixels and semantic assertions are unchanged. Run those producers in a disposable exact-head worktree or preserve a clean snapshot first. Afterward:

- verify the semantic report, binder, request accounting, and image pixels as applicable;
- classify tracked rewrites before cleanup;
- never auto-commit timestamp/placeholder/encoding churn as stronger evidence;
- restore only after proving the changes are generated evidence rather than product/source edits.

A producer passing and a worktree becoming dirty are separate facts; record both honestly.