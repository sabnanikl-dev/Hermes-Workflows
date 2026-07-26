# Task-scoped capability launcher hardening

Use this reference when a Hermes execution profile receives temporary credentials, skills, or tools for one bounded work packet.

## Threat model

The launcher must prevent accidental or adversarial authority expansion through:

- CLI flag smuggling or alternate subcommands;
- stale, replayed, replaced, linked, or symlinked grant files;
- concurrent launches sharing temporary capability state;
- standing profile `.env` credentials reappearing after parent-environment scrubbing;
- skill-name ambiguity, unsafe symlinks, or copied skill residue;
- source revision drift between approval, grant creation, and execution;
- worker self-approval, claim creation, status advancement, or gate crossing;
- logs, grant files, or output artifacts containing credential values.

A local profile remains a policy/launcher boundary unless the terminal or process runs in a real OS/container sandbox. State that boundary explicitly rather than implying kernel isolation.

## Required launcher invariants

### Exact CLI allowlist

Parse allowed arguments structurally. For a one-shot worker, prefer an exact grammar such as:

```text
chat (-q|--query) <one query string> [--quiet]
```

Reject everything else. A denylist alone is insufficient because CLIs often accept:

- attached short flags such as `-pdefault` or `-tmessaging`;
- `--flag=value` forms;
- resume/session modes;
- profile/model/provider/toolset overrides;
- API-key or base-URL overrides;
- skill injection and rule-bypass flags;
- trailing tokens interpreted as another command or positional mode.

Test the real wrapper and the downstream argument parser, not only the helper function.

### Revision-bound grant schema

A grant should contain names and bindings, never secret values:

```json
{
  "version": 1,
  "grant_id": "<unique-id>",
  "root": "<root-id>",
  "issue": "<issue-id>",
  "body_sha256": "<64 lowercase hex source-body digest>",
  "run_id": "<run-id>",
  "created_at": "<timezone-aware ISO-8601>",
  "expires_at": "<timezone-aware ISO-8601 within policy maximum>",
  "credential_env": ["<allowlisted environment name>"],
  "skills": ["<exact skill name>"]
}
```

`body_sha256` means the normalized source issue/object body digest. It is not the execution packet file hash. If the packet file itself must be integrity-bound, use a separate `packet_sha256` field.

### Safe open and one-time consumption

Before capability exposure:

1. Require an absolute direct-child path under the private grant root.
2. Reject symlinks, non-regular files, wrong owner, group/world permissions, excessive size, and hard-link count other than one.
3. Open with `O_NOFOLLOW`/`O_CLOEXEC` when available and validate with `fstat`.
4. Parse and validate the already-open bytes.
5. Require `<grant_id>.json` to match the payload.
6. Compare device/inode immediately before consumption.
7. Atomically rename to a non-`.json` consumed path before injecting credentials or skills.
8. Hold an exclusive nonblocking process lock through install, execution, and cleanup.
9. Remove the consumed file after normal or handled exit.
10. If a crash leaves a consumed file or temporary skill tree, fail closed for operator inspection instead of silently continuing.

### Standing environment audit

Clearing the parent process environment is not enough if Hermes reloads a profile-local `.env` or other credential store. Validate the profile `.env` itself:

- user-owned;
- private mode;
- not a symlink;
- only explicitly permitted non-capability keys.

Also inventory file-based auth and keychain access. If those remain reachable, describe the launcher as policy isolation and use a container/restricted backend when hard enforcement is required.

### Temporary skill resolution

- Resolve exact frontmatter `name`, not a guessed path.
- Reject ambiguous matches.
- Support symlinked skill roots only through an explicit approved-root list.
- Reject broken or escaping symlinks inside the selected skill tree.
- Install under a grant-specific directory.
- Write a grant-specific residue manifest that binds grant ID, run ID, root, issue, source digest, and skill names.
- Explicitly chmod the manifest to the same private mode required by the diagnostic/recovery reader; do not rely on `umask` defaults.
- Validate real generated manifests for owner, mode, hard-link count, regular-file type, bounded size, and no-follow semantics. Synthetic test helpers must use the production writer or independently assert that their bytes and metadata match production.
- Clear skill prompt snapshots after install and cleanup.
- Remove the grant-specific directory in `finally`.

## Verification matrix

Require all of the following before declaring the architecture operational:

1. Unit tests and syntax/compile checks pass.
2. Exact reviewed hashes match before and after independent review.
3. Real-wrapper CLI smuggling probes fail with the expected blocked status.
4. Underlying parser probes cannot reinterpret accepted wrapper arguments as profile/tool/credential overrides.
5. A temporary-directory E2E probe proves atomic consumption, exact environment injection, revision metadata, copied skill availability, and cleanup.
6. A real sanitized producer/consumer dogfood run verifies the live consumed grant, task-skill manifest metadata, and diagnostic classification while the wrapper lock is active.
7. A controlled forced wrapper-and-child interruption leaves inspectable residue; a fresh process/session reconstructs both live tracker state and local recovery state without chat history.
8. Exact-bound recovery refuses an active lock, wrong confirmation, unsafe/unknown residue, unrelated residue, no-op retry, and consumed-grant replay; successful cleanup reads back global clean state.
9. A bounded live read or explicitly approved mutation proves operational usefulness and direct readback.
10. Post-run inventory reports zero grant files, zero consumed residue, zero temporary skill entries, and the exact permanent-skill count.
11. A fresh ungranted run cannot load the temporary skill or see the task credential.
12. The source tracker/object body digest and state remain as expected.
13. The worker output is evidence only; Default Hermes or the designated control plane decides review/final status.

## Reviewer-loop pitfall

A timed-out reviewer may still have completed valuable probes. Do not call the result green and do not discard it. Read the live transcript, extract concrete findings, patch P0/P1 issues, freeze new hashes, and launch a narrower blocker-only re-review. The final reviewer must emit a machine-readable marker such as:

```text
DONE: STATUS=pass|fail P0=<n> P1=<n> P2=<n>
```
