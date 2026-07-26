# Trusted-Agent Launch Recovery

Use this when the mission trusts a scoped builder/reviewer to perform repository work directly and the failure is launch reliability—not evidence that the agent must be treated as a hostile same-UID tenant.

## Calibrate the boundary first

Write the actual role contract before hardening the launcher:

- Claude Code may edit, test, commit, push to the bound branch, and post its fix summary.
- Codex reviewers may publish their scoped exact-head artifacts under the configured reviewer identity.
- Hermes verifies live GitHub evidence and advises `merge-ready`, `blocked`, or `needs-Karan`.
- Karan alone merges.

Keep isolated worktrees, exact-head readback, bounded cycles, no force push, and no deploy/client/account authority. Do not introduce custom credential RPC, synthetic HOME, same-UID isolation proofs, runtime attestation, or container/VM qualification unless the mission explicitly requires hostile-tenant containment.

## Reliable Claude launch

1. Smoke-test the exact requested model and auth before the long run.
2. Preserve the normal macOS OAuth/keychain session; never use `env -i` for subscription-authenticated Claude Code.
3. Use empty MCP when optional servers cause startup drift, an explicit task-scoped `--allowedTools` list, and an isolated worktree.
4. Run non-trivial work in the background with completion notification and a realistic 20–30 minute budget.
5. Expect `claude --print` to buffer output. Check process liveness/CPU/children plus `git status` and `git diff --stat`; quiet stdout alone is not a stall.
6. If `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` explicitly forces `--permission-mode dontAsk` back to default and the trusted lane cannot edit, terminate only that exact process, verify the worktree state, and relaunch once with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0` plus the explicit allowlist. Do not disable scrubbing globally or treat this as a blanket permission bypass.
7. If edits/tests are progressing, allow the bounded run to finish.

## Verify direct work

After every builder push or reviewer publication, independently read back:

- local worktree HEAD;
- remote branch SHA;
- PR `headRefOid` and expected commit list;
- signed builder comment or reviewer artifact;
- artifact author, role/signature, and exact reviewed head;
- worktree cleanliness and required gates.

Any push invalidates prior review verdicts. A direct trusted artifact is the default when configured; Hermes transport-only relay is a disclosed fallback, not a mandatory security architecture.

## Recovering from an overengineered attempt

Preserve evidence instead of force-rewriting it:

1. stop obsolete workers and scheduled continuations;
2. record dirty worktree status and save a checksum-backed patch without resetting;
3. preserve the old draft PR, reviews, and remote branch;
4. create a clean replacement branch from the last independently approved head;
5. publish and verify the replacement draft;
6. close the old PR as superseded without deleting its branch;
7. rebuild only the narrowed trusted-agent slice.
