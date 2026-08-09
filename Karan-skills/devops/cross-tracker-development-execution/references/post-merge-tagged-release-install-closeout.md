# Post-Merge Tagged Release and Active-Install Closeout

Use this reference when a final cross-tracker child begins **after Karan has merged the accepted integration PR** and governs a bounded sequence such as: verify merge → tag → back up active files → install exact tagged bytes → smoke → reconcile Linear.

This is a release/install lane, not another implementation PR. Keep merge authority, release authority, active installation, deploys, and downstream pilots as separate gates.

## 1. Reconstruct the release authority and source

Read live sources before mutation:

- Linear release child, parent, predecessor, relations, comments, state, and complete pagination;
- merged GitHub PR, former exact reviewed head, merge method/commit, final reviews/comments/threads, and closing linkage;
- repository instructions, package/skill version markers, existing tags/releases, operational clone, active install targets, and rollback conventions.

A direct request to execute the named release child can authorize only the actions explicitly contained in that live child contract. It does not silently authorize merge, deploy, downstream client/pilot mutation, credentials, accounts, or publication.

Create a revision-bound Linear claim before mutation. Name the exact tag/merge, active paths, backup destination class, expected artifacts, excluded systems, and next checkpoint. The claim's output inventory should distinguish:

- immutable Git tag/repository assets;
- private rollback evidence;
- active user-facing installation;
- Linear acceptance evidence;
- any still-pending downstream child.

## 2. Re-qualify before tagging

Do not treat the predecessor's `Done` state as release proof. Verify:

1. PR REST/API readback says `merged: true` and identifies the exact merge commit and former reviewed head.
2. Final Reviewer A/B/Integration Auditor artifacts are bound to that reviewed head, use the expected identities/roles/states, and report zero blockers.
3. Conversation, formal review, inline-comment, review-thread, and check surfaces are complete; unresolved human feedback is absent or explicitly resolved.
4. The operational clone is clean and `HEAD == origin/main == verified merge commit`.
5. The full supported test/check suite passes again on the release source.
6. Any required real-agent smoke launches trusted builder/reviewer CLIs against a disposable or read-only approved surface. Agent output proves launch/auth/repository grounding only; Hermes still performs GitHub readback and the go/no-go synthesis.

Keep the construction review independent: the newly installed control surface must not certify the reviews that accepted its own construction.

## 3. Create and prove the remote tag

Choose the tag from repository-owned version markers and existing tag conventions. If the repository has no prior convention, prefer a scoped semantic tag such as `<tool>-vX.Y.Z` over an ambiguous bare version.

Before creation, assert the local tag and remote ref do not already exist. Create an annotated tag on the verified merge commit, push only that ref, then verify all layers:

- `git ls-remote --tags origin refs/tags/<tag> refs/tags/<tag>^{}`;
- GitHub `GET /repos/{owner}/{repo}/git/ref/tags/{tag}`;
- for an annotated tag, dereference the returned tag object with `GET /repos/{owner}/{repo}/git/tags/{object_sha}` and require its target commit to equal the merge commit;
- re-read the merged PR after the tag push.

Listing tags uses `GET /repos/{owner}/{repo}/git/matching-refs/tags/`; `git/ref/tags` without a concrete ref is not the collection endpoint.

A remote tag ref object is not the release commit when the tag is annotated. Always peel it.

## 4. Resolve the actual install surface

Inspect the accepted repository contract before inventing an installation shape.

- If the tool is intentionally repo-local and the router says to run `path/to/bin` from the repository root, **do not fabricate a PATH wrapper or global binary** merely because the release issue says “install.”
- Replace only active files the accepted contract actually designates, such as the active skill directory.
- Treat the clean operational clone at the verified tag as the executable installation when that is the contract.
- Back up a repo-local executable for evidence if useful, but do not rewrite it when it already byte-matches the tag.

Record the resolved active targets and explicitly state any intentionally absent install surface.

## 5. Stage from the tag, not from the working tree

Materialize release bytes with `git archive <verified-tag> <approved-paths>` into a disposable staging directory. Reject:

- absolute or parent-traversing archive paths;
- symlinks or non-regular members unless explicitly expected;
- missing expected skill/bin paths;
- unexpected file inventory;
- source/tag/merge drift;
- partial-copy or post-copy hash mismatch.

Hash every tagged file and preserve path, size, and mode. The current working tree may equal the tag, but it is not the installation source of record.

## 6. Back up and atomically replace active files

Use a timestamped private location **outside active skill discovery**, for example a dedicated `~/.hermes/backups/<mission>/...` tree. Default evidence permissions:

- backup directory: `0700`;
- manifests/evidence: `0600`.

Before replacement, preserve:

- complete active file inventory and SHA-256 hashes;
- file sizes/modes;
- exact release tag and peeled commit;
- current active skill/bin versions;
- rollback source paths and procedure.

Build the replacement as a hidden sibling on the same filesystem, verify it equals the tagged tree, then rename the old active directory into the private backup and rename the staged directory into place. On any exception, restore the old directory before reporting failure. Remove hidden staging residue after success or rollback.

## 7. Exercise restore without destabilizing the live install

The release contract may allow either a live restore/reinstall cycle or deterministic disposable proof. Prefer a disposable target when the active surface is already correct:

1. copy the tagged installation into the disposable target;
2. replace it using the backed-up pre-install tree;
3. hash the restored tree and require equality with the pre-install manifest;
4. retain the exact live restore procedure in the private manifest.

This proves rollback mechanics without briefly downgrading the active control surface.

## 8. Run installed-path smokes

Verify from the actual active paths, not only staging:

- load the active skill through `skill_view` and confirm linked references are discoverable;
- read the active skill version;
- run the repository-local executable via its documented path;
- read the package/tool version from the installed/tagged code;
- run config validation plus focused adapter/router/integration tests on every supported runtime;
- require active file hashes and repo-local executable bytes to match the tagged manifest;
- confirm the operational clone remains clean and exact.

A green pre-install suite does not replace installed-path readback.

## 9. Close Linear and the parent train safely

Prepare one ticket-specific release-evidence packet containing URLs/IDs, heads/commits/tag objects, test counts, versions, active/backup paths, hashes, restore result, boundaries, and durable-knowledge disposition. Keep it with the private rollback packet unless the live contract names another canonical destination.

Then:

1. fetch fresh child and parent bodies; do not edit from cached bodies after a transient API failure;
2. check every release-child criterion supported by evidence and append a completion checkpoint;
3. read back the child body while it is still active and assert exact checked/unchecked counts;
4. update only the now-proven predecessor/release rows and active-sequence lines in the parent;
5. preserve the downstream pilot/future child unchecked and unchanged;
6. add child and parent comments, capture returned comment IDs, and verify each directly by `comment(id:)` with exact body readback;
7. move the release child to `Done` only after artifacts, bodies, and comments are proven;
8. re-read final child state by both name and type, complete relations, parent body/state, downstream child state, remote tag, merged PR, active hashes, and backup evidence.

Linear mutation responses are acknowledgements, not proof. If an API call fails mid-batch, re-read both bodies and report landed versus staged changes exactly before retrying.

## Pitfalls

- Do not report the annotated tag object's SHA as the release commit; peel it.
- Do not create a global executable that contradicts the accepted repo-local routing contract.
- Do not copy from `main` merely because it currently equals the tag; archive the tag.
- Do not leave the only rollback copy under active skill discovery.
- Do not mark the parent or downstream pilot complete when only the release child is proven.
- Do not manufacture a Hermes Brain page when GitHub, Linear, the tag, and private rollback packet already form the canonical record; state that no separate durable-knowledge artifact was needed.
