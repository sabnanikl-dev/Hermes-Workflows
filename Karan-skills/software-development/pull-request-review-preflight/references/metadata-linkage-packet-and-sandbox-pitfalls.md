# Metadata linkage, packet integrity, and reviewer sandbox pitfalls

## 1. Hidden closing linkage from issue-linked branches

A non-closing PR body such as `Refs #123` is not proof that the PR will leave the issue open. A branch created or attached through GitHub's issue Development surface can create an implicit `closingIssuesReferences` relationship. GitHub may retain it even when the PR title, body, and commit messages contain no closing keyword.

### Gate

Before packet freeze or reviewer launch:

1. Query live `headRefOid`, `closingIssuesReferences`, base/head branches, draft state, and final commit.
2. If an umbrella/parent issue must remain open, assert `closingIssuesReferences | length == 0`.
3. Verify local HEAD = remote branch head = PR head = final PR commit.
4. Stop technical review while lifecycle linkage is wrong.

### Recovery

Editing PR prose cannot reliably remove branch-derived linkage. Preserve the trusted builder commit without rebuilding it:

1. Create a clean branch directly from the verified builder commit, without the GitHub issue-development association.
2. Push and open a replacement draft PR using only non-closing references.
3. Verify the replacement has the same exact commit/tree and zero live closing references.
4. Close the contaminated PR unmerged, explaining that it was superseded for metadata linkage rather than rejected code.
5. Switch the active worktree/upstream to the clean branch.
6. Remove the obsolete remote branch only after replacement verification and only within authorized cleanup scope.
7. Synchronize tracker/issue ledgers to the replacement while preserving supersession history.

When the code head is byte-for-byte unchanged, this is a metadata transport repair rather than a builder fix cycle. Review only the replacement PR.

## 2. Do not create self-referential checksum manifests

Broken pattern:

```text
hash every file in packet directory > packet/SHA256SUMS
```

The shell opens `SHA256SUMS` before enumeration completes, so the manifest can include a digest of its own empty or partial bytes. Reviewers then see a checksum mismatch while all substantive payloads are intact.

Use either:

- a named payload allowlist that explicitly excludes the checksum manifest; or
- a temporary manifest outside the packet, then an atomic move into the packet.

Afterward:

1. verify every listed payload digest;
2. hash the completed manifest separately and store that digest outside the packet/run ledger;
3. make the packet read-only;
4. bind packet timestamp, full head SHA, and manifest digest into reviewer prompts.

A self-check defect is packet-generation failure, not product failure, when substantive payloads independently verify. Repair it before generating the next-head packet.

## 3. Read-only reviewer test policy

Credential-free read-only sandboxes may not expose a writable temporary directory. Suites using `tempfile`, caches, compiler output, or worktree-local fixtures can fail before product code executes.

Deliberate policy:

- Default Hermes runs the complete canonical suite at the exact head and places real output in the packet.
- Read-only reviewers run non-writing focused tests, source compilation, static checks, and deterministic probes writing only to approved `/tmp` evidence paths.
- If independent full-suite execution is required and inherently writes files, use the hardened reviewer's bounded disposable `--workspace-write` mode. Keep credentials absent and discard/verify the worktree afterward.

Do not label a temp-directory setup failure as a product blocker. Do not broaden GitHub credentials or bypass hardened launchers merely to obtain writable storage.

## 4. Packet payload minimum

Include:

- repository, PR, timestamp, base/head names, exact full SHA;
- issue and PR contracts;
- draft/mergeability/closing-linkage state;
- commit and changed-path inventory;
- formal reviews, conversation comments, inline comments, review threads, and checks;
- canonical exact-head test/build/validation output;
- visual-evidence manifest when UI-affecting;
- worktree path and clean/detached-head assertion.

Exclude tokens, credential paths, shell environment dumps, mutable live-account state, and unrelated private data.
