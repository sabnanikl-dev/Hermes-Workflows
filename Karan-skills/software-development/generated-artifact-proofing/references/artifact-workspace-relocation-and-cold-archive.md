# Evidence-preserving workspace relocation and cold archival

## Use

Use for reorganizing document/research/demo workspaces, separating deliverables from build intermediates, or putting an existing artifact folder into Git for the first time. This is not application implementation authority.

## 1. Establish the boundary and baseline

- Inspect the actual filesystem and Git state; an elaborate engineering packet may not be a repository or implemented product.
- Classify canonical sources, research captures, current deliverables, tools, generated evidence and history. A small root README and thin agent contract often suffice; avoid empty app folders, duplicate state documents and idle orchestration scaffolds.
- If the user requests a proposal first, give explicit keep/move/archive/delete actions and wait for approval before mutations. Archiving and publishing are distinct scope decisions.
- Capture every original relative path, byte size and SHA-256. Make a rollback snapshot outside the mutation root, verify CRC/member sets and re-hash every restored/read-back member. Preserve it through closeout.

## 2. Inspect dependencies before moving

Inventory `__file__.parent`, chained `.parent`, `with_name`, `with_suffix`, dynamic path joins, Markdown image roots, localhost serving directories, hardcoded URLs and packaging globs. Moving source Markdown separately from HTML/PDF invalidates sibling-suffix assumptions; moving a server root without its URL breaks rendering.

Keep an already coherent research subtree together when fragmentation would add complexity. A small explicit project-relative resolver can replace brittle location assumptions. One documented relative resource alias can preserve canonical Markdown hashes; do not build an entire shadow legacy tree. Confirm aliases resolve after cloning, not merely on the original machine.

## 3. Preserve evidence identity

- Do not rewrite old review hashes or paths and call them newly verified. Record translation separately.
- Inspect nested handoff ZIP manifests. A curated bundle can hold the only surviving context document or deliberately bind an older brief. Repacking from live files is not equivalent preservation; retain the original ZIP and use a distinct rebuilt-package path.
- Preserve both sides of historical comparison proofs, including shared CSS/images outside the historical folder. A historical checker may correctly fail on today's revision because it compares a different stage pair; do not weaken its assertions.
- Treat commands named `verify-*` as potentially mutating: they may overwrite fixtures, encoded frames, screenshots and sidecars. Exercise them in disposable copies.
- Keep current hash-bound captures and active verifier inputs unpacked unless a tested restore mechanism exists. A final MP4 alone may not suffice: the verifier can require mixed narration WAV, storyboard, timing, CSV, scenario proof and browser-reference frames.

## 4. Lossless cold storage

Choose eligible intermediates by consumer dependency, not extension alone. Per-scene narration files and genuinely obsolete render sets can be cold-archived while keeping final narration and cited current frames loose.

ZIP members should have explicit new-layout relative paths. Reject absolute/traversal paths and duplicate member names; verify each member's SHA-256 against the frozen inventory before removing its loose copy. Actually restore into an empty temporary directory and compare the restored bytes. Document restoration without overwriting accepted or modified files.

Recommended per-original manifest fields:

```json
{
  "old_path": "former/path",
  "new_path": "current/path",
  "original_bytes": 123,
  "original_sha256": "...",
  "new_sha256": "...",
  "classification": "preserved | path-repaired-tool | cold-archived",
  "original_copy": "archive/original-tooling/...",
  "archive": "archive/cold/intermediates.zip",
  "archive_member": "current/path"
}
```

Include optional fields only when applicable. Require exact-once coverage of the original path set. For edited tools, preserve the original version and verify its original digest. Check both exact destinations and independent hash conservation; finding a hash somewhere inside a bundle alone does not prove the intended active path exists.

## 5. Prove relocated execution

1. Establish original generator output parity in a disposable baseline copy.
2. Execute relocated commands from an unrelated working directory in another disposable copy.
3. Require expected output existence, content invariants and complete hashes. A builder that exits zero when its source is missing is not a passing reproduction.
4. Separate frozen-evidence binding from regeneration. Run binders against accepted bytes before screenshot/PDF producers replace disposable outputs.
5. Record deterministic HTML parity separately from metadata/font/browser-sensitive PDF and screenshot regeneration. Visually inspect new responsive captures; retain their provenance rather than replacing historical acceptance.
6. Preserve the invariant when repairing a validator: no horizontal overflow means content must not exceed available viewport width, not that scrollbar-sensitive widths are always equal. Diagnose baseline geometry first; retain other clipping, label and content assertions.
7. State unrun branches precisely. Rendering all scenes plus decoding an existing MP4 does not claim a full new MP4 encoding run.

## 6. First Git publication and fresh-clone proof

- Get explicit repository/push authorization. For internal client evidence, choose private visibility unless instructed otherwise, verify the authenticated owner and check name collisions.
- Define binary tracking deliberately. A preserved archive can belong in the initial snapshot; inspect blob sizes against current host limits, and avoid silently excluding required evidence. Keep the separate rollback snapshot outside Git.
- Scan candidate files and nested archives for credentials; report only finding locations, never secret values. A pattern scan is bounded evidence, not a guarantee. Verify ignores for caches and secret files while ensuring deliverables remain included.
- Verify local HEAD against both remote branch and GitHub commit readback.
- Clone from the actual remote into a fresh disposable directory. Reconcile every migration entry, read cold members, verify original versions of edited tools, resolve resource aliases and rerun deterministic generators there. This catches omitted/ignored inputs that local-copy tests cannot.
- End with a clean canonical worktree and distinguish cleanup acceptance from product/deployment acceptance.

## Observed validation example

A discovery workspace migration preserved 398 originals: 316 unchanged loose files, 68 verified cold members and 14 repaired tools with exact original copies. Fifteen scoped commands passed; four HTML generators reproduced accepted bytes. After private publication, a fresh GitHub clone independently reconciled all 398 entries and reproduced those four HTML outputs. These counts illustrate the evidence pattern, not fixed acceptance thresholds.
