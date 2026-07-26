# Read-command `--out` safety in PR prover loops

Use this when a PR adds or changes a CLI that is advertised as read-only but supports `--out`, `--output`, or similar packet/export flags.

## Durable lesson

A command can be semantically “read-only” but still mutate files through output redirection flags. Treat `--out` as a write surface during review, especially when the tool is intended for agents that may run from arbitrary working directories or with root override environment variables.

## Review probes to request or run

For a CLI with workspace root override support, reviewers/builders should cover at least these cases:

1. **Inside canonical workspace root**
   - `tool context client --out path/inside/workspace.json` must refuse.
2. **Relative path under invocation cwd/repo**
   - From a repo subdirectory, `--out ../CLAUDE.md` / `../README.md` must refuse if it would clobber project files.
3. **Root override / fixture root**
   - With `SEO_AGENT_ROOT` or equivalent pointing at a fixture, relative `--out` paths must not be allowed to overwrite the invocation repo just because the logical tool root moved elsewhere.
4. **Git unavailable / repo discovery unavailable**
   - Simulate `git` missing/unavailable and confirm the safety check fails closed, not open. A useful pattern is a temp `PATH` containing only required interpreters but no `git`, then run from a nested cwd with `--out ../CLAUDE.md` against a fixture root.
5. **Allowed external output**
   - Absolute external temp paths such as `/tmp/tool-packet.json` should still work if the contract intends to support disk handoff packets.

## Why this matters

In one PR-prover run, two fix cycles cleared obvious `--out` safety and JSON error blockers, but final re-review found a remaining edge case: when `git` was unavailable, repo-top discovery returned `None`, so the guard only rejected the logical control-center root and immediate cwd. From a subdirectory, a relative `--out ../CLAUDE.md` escaped cwd and overwrote a repo file in a controlled writable temp fixture.

The important reusable pattern is not the specific PR: **when output path safety depends on repo discovery, test the no-repo/no-git path and require fail-closed behavior.**

## Handling it in a review

- A late-surfacing `--out` edge case is a real current-head blocker, not a nit. Whether another builder pass is allowed is a cycle-cap question `pr-prover/MISSION.md` answers, not one this reference decides.
- Reproduce it inside a controlled writable fixture, never against the real repo files. The exact command, root override, and refusal/exit behavior are what make the finding durable; where that evidence is published is `pr-prover`'s concern.
- The fail-closed no-git/relative-path case is not closed until it is fixed and re-proved on the current head.
