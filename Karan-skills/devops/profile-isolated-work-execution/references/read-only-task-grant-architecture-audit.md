# Read-only task-grant architecture audit

Use this verifier when reviewing a hardened one-shot worker launcher without consuming a live grant, starting a real worker session, or mutating profile state.

## Audit objective

Prove that task credentials and temporary skills are issue/revision/run bounded, exposed only to the fixed worker profile, and removed after execution. Keep optional OS-level sandboxing separate from P0/P1 correctness when the architecture explicitly discloses that profiles are policy/state isolation rather than filesystem sandboxes.

## Read-only sequence

1. **Freeze the review set.** Record SHA-256 hashes for the launcher, tests, wrapper, profile configuration/SOUL, worker protocol skill, and control-plane routing documents.
2. **Inspect exact artifacts.** Trace grant validation, path/owner/mode/single-link checks, atomic consumption, lock ownership, clean environment construction, fixed profile invocation, skill resolution/copying, cleanup, stale-state fail-closure, and the control-plane/worker authority split.
3. **Inspect live state without values.** Report only counts, paths, modes, ownership booleans, and environment key names. Verify zero available/consumed grants, zero task-scoped skill residue, the expected permanent skill count, the bundled-skill suppression marker, and a private non-symlink profile `.env` containing only allowlisted keys. Never print credential values.
4. **Run local tests without workspace bytecode.** Set `PYTHONDONTWRITEBYTECODE=1` and direct `PYTHONPYCACHEPREFIX` to a temporary directory. Compile to an explicit temporary `.pyc`. Remove the temporary directory on exit.
5. **Probe CLI fail-closure.** Exercise attached and split forms of profile, toolset, resume, skill, API/base-URL, yolo, ignore-rules, and grant overrides. Require the wrapper to return its blocked exit code before acquiring the live lock or launching Hermes. Also parse flag-shaped query values against the underlying CLI parser to ensure they cannot smuggle authority.
6. **Run a temp-only end-to-end grant probe.** Import the launcher, redirect grant/profile/task-skill/lock constants to a temporary directory, provide a synthetic grant, and replace `subprocess.run` with an assertion stub. Verify:
   - the command fixes `-p linear-worker`;
   - `LINEAR_WORKER_CLEAN_ENV=1` is present;
   - only the named credential is injected;
   - issue/body-digest/run metadata is exact;
   - the named skill is copied and symlinks are dereferenced;
   - the grant and temporary skill copy are removed after return.
7. **Re-read state and hashes.** Require the final counts and every review-set hash to match the pre-audit values.

## Severity rules

- **P0/P1:** authority expansion, profile/toolset override, ungranted credential exposure, replay, cross-run residue usable by a later worker, loss of revision/run binding, cleanup failure that preserves capability, or executor control over approval/claim/review/final status.
- **P2:** disclosed absence of an OS/filesystem/process sandbox when policy isolation is the accepted architecture. Report it separately; do not use it to fail an otherwise green task-grant audit.
- Missing evidence for a required P0/P1 invariant is blocking rather than assumed safe.

## Reporting contract

Return a concise status with test/probe counts, initial/final residue counts, hash equality, files changed (normally none), and any P2 limitation. End with:

```text
DONE: STATUS=pass|fail P0=<count> P1=<count> P2=<count>
```

Do not rerun a live external smoke test when prior local evidence is supplied and the review contract is strictly read-only.