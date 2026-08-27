# Byte-bound evidence closeout

Use this when a repository packet contains captured upstream pages, raw responses, direct text extractions, or other evidence whose exact bytes were independently reviewed and accepted.

## Principle

Exact evidence fidelity outranks cosmetic lint. Once reviewers accept a SHA-256-bound artifact, changing whitespace, line endings, encoding, metadata, or formatting creates new bytes and invalidates that verdict. Never “clean up” accepted evidence merely to make a broad lint command pass.

## File classes

Before staging, classify each path:

1. **Authored files** — reports, acceptance sidecars, manifests, provenance JSON, and operator-written summaries. These should pass applicable syntax and whitespace checks.
2. **Immutable evidence** — captured HTML, raw API responses, downloaded documents, and direct source extractions preserved for reconstruction. Validate these by exact hash, byte count, provenance, and reviewer binding; do not normalize them after acceptance.

A derived extraction may still be immutable evidence when its exact bytes and hash were part of the reviewed packet.

## Closeout sequence

1. Freeze the accepted path list and expected hashes. Use an explicit pathspec file; never `git add .`.
2. Confirm every staged path equals the declared list and unrelated files are absent.
3. Run whitespace/syntax checks only on authored paths, for example:

   ```bash
   git diff --cached --check -- outputs/report.md outputs/acceptance.md evidence/provenance.json
   ```

4. If a broad `git diff --cached --check` reports only trailing whitespace or EOF formatting in immutable evidence:
   - inspect enough output to prove every finding belongs to a declared immutable path;
   - do not edit those bytes;
   - rerun the gate against authored paths only.
5. Stop if any authored path fails, any unexpected path is staged, or any accepted hash changed.
6. Commit the explicit packet.
7. Verify the commit itself, not just the worktree:
   - committed path set exactly equals the declared list;
   - each committed blob (`git show COMMIT:path`) hashes to the accepted SHA-256;
   - unrelated artifacts remain excluded;
   - no push occurred unless separately authorized.
8. Only after committed-blob verification should tracker acceptance/state reconciliation proceed.

## Reviewer validity

Any byte change to a reviewed report or immutable evidence packet supersedes the previous verdict. Repair narrowly, compute new hashes, and obtain a fresh exact-byte review. A separate acceptance sidecar may record the verdict without changing the reviewed report, but it must bind all accepted artifact hashes.

## Pitfalls

- Normalizing source HTML after review to satisfy `git diff --check`.
- Assuming a direct text extraction is safe to reformat because it is “only derived.”
- Trusting worktree hashes after commit without hashing committed blobs.
- Treating a scoped lint exception as permission to skip checks on authored files.
- Letting unrelated untracked files enter the packet through broad staging.
