# Worktree cold storage on an external volume

Use only after owner approval of the destination and bounded source scope. The parent skill's preservation, changed-content, active-consumer, and deletion gates still apply.

## Storage format

- Resolve the exact mount and record the volume UUID with `diskutil info -plist`; recheck both before external writes and before source removal. Do not silently normalize a misspelled user-supplied volume name.
- Use archive containers on ExFAT rather than loose Git checkouts. ExFAT does not provide Unix symlink/permission semantics, and its allocation units may waste space on many small files. Restore tests belong on APFS or another suitable local filesystem.
- Separate redundant merged checkouts from historical work needing preservation. Dirty worktrees and broken Git pointers remain protected until their unique state has its own verified preservation plan; do not use force removal to simplify the job.

## Capture Git history independently

A linked worktree's `.git` file is only a pointer. A filesystem archive of that folder alone is not independently restorable.

1. In a task-created local verification directory, `git clone --mirror --no-hardlinks <common-git-dir> <temporary-mirror.git>`.
2. In the temporary mirror only, add `refs/archive/<stable-item-id>` for every exact worktree HEAD to preserve. This keeps detached or superseded commits explicitly reachable without modifying source refs.
3. Create an external bundle with `git --git-dir=<temporary-mirror.git> bundle create <archive.bundle> --all`.
4. Verify it with `git bundle verify`, clone the bundle into a separate temporary mirror, and verify every archived ref resolves to its expected HEAD.
5. Do not export original Git configs/hooks/credentials merely to preserve code. Shared stashes and ordinary refs are included by `--all`; staged/untracked working state requires separate capture and is not preserved by a bundle alone.

A stale local object database may not contain a merged PR's final head. Before calling a candidate unpreserved, a read-only GitHub comparison can establish exact ancestry: compare `<local-HEAD>...<verified-merged-PR-head>` and require `behind_by == 0` plus `merge_base_commit.sha == local-HEAD`. Never substitute PR association alone for preservation proof.

## Capture and test the files

- Record source identity, HEAD, index flags, full tracked/untracked status, ignored inventory, and visible open-file/cwd consumers. Keep `GIT_OPTIONAL_LOCKS=0` for read-only inspections.
- Inventory every retained regular file by SHA-256, size and mode; record directory modes and symlink targets without following symlinks. Refuse special files or unsupported submodules rather than silently dropping them.
- Archive the working files under one fixed relative prefix, omitting only the machine-specific top-level `.git` pointer. Preserve ignored review evidence; do not equate ignored with disposable.
- Re-scan the source after capture. New or changed content invalidates the removal decision.
- Hash and read back the external archive. Fully extract it in a task-owned local directory and compare the restored inventory with the source manifest. Validate archive paths and prevent writes through symlink ancestors.
- Reconstruct a temporary Git checkout from the verified bundle at the recorded HEAD, overlay the restored files without the old `.git` pointer, and verify tracked content matches. A temporary restore repository may use an alternates file referencing the independently cloned bundle mirror; documented user restoration should use a standalone bundle clone.
- Include an external manifest and `RESTORE.md` linking each snapshot to its history bundle, exact ref/HEAD, and checksums. Explain that preserved absolute dependency symlinks may require regenerating dependencies on another machine.

## Source removal and evidence

Immediately before removal, revalidate the volume, archive/bundle hashes, exact source identity and HEAD, file manifest, status, and active consumers. Use non-force `git worktree remove` only; retain anything Git refuses. Keep main checkouts, branches, shared history, and stashes.

Read back both source-path absence and registry absence. Compare source branch/ref snapshots before and after. Save an execution ledger locally and on the external volume, then remove only the task-created restore-test directories. Report original allocated footprint separately from observed `df` change; concurrent filesystem activity means the latter is not an exact attributable savings calculation.

Cold storage becomes the sole copy of any otherwise unpublished files after local removal. It is not redundant backup; unique work needs a second independent copy.

## Standalone repositories and macOS restore pitfalls

- Check `git rev-parse --is-shallow-repository` before bundling. `git bundle verify` alone can pass a shallow bundle that fails a fresh clone because parent objects are missing. Require an independent bundle clone. If approved-scope archival needs complete history, unshallow only a task-created mirror from the verified original remote; never alter the source checkout merely to archive it.
- Preserve `.git/info/exclude` separately and restore it before comparing porcelain status. A byte-identical working tree can appear dirty after reconstruction if repository-local ignore rules are missing. Do not compensate by deleting the newly visible files.
- Preserve private original Git administrative state locally when a standalone checkout is removed and that metadata matters; do not export configs/hooks/credentials solely to preserve code. Count retained metadata against reported local savings. Full history bundles and working-file snapshots remain independently restore-tested.
- Compare file bytes, paths, modes, symlink targets, and portable extended attributes during macOS restore tests. macOS may regenerate `com.apple.provenance` on extraction; record its original hash but exclude only that documented OS-managed attribute from equality. Never reset security metadata just to make a test pass. Other mismatches remain blockers.
- Use Darwin `listxattr`/`getxattr` APIs or the native `xattr` utility on macOS; Python `os.listxattr` may be unavailable. Native macOS tar preserves extended attributes in archive containers, subject to OS-managed restore behavior.
- Treat project-history/trust references differently from executable consumers. A path under Claude's project history or Codex's `[projects."..."]` trust entries is not itself a running service dependency; inspect structure without printing credential values. Visible open-handle absence is still only one safety check.
