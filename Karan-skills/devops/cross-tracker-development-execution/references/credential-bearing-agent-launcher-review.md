# Security Review for Credential-Bearing Agent Launchers

Use this reference when a cross-tracker coding mission claims that autonomous builder/reviewer children are least-privilege, merge-free, branch-bound, credential-isolated, read-only, or prompt-injection resistant.

A green unit suite is necessary but insufficient. Review **effective OS and provider authority**, not only local capability enums, prompts, or post-action readback.

## Five proof layers

1. **Declared policy:** roles, capability names, prompt wording, docs.
2. **Launch shape:** argv, environment, cwd, HOME, tools, MCP/plugins, timeout.
3. **Effective authority:** what the real credential/account/provider permits.
4. **Containment:** reachable files, processes, network endpoints, refs, repos, accounts.
5. **Readback:** what remote state proves actually landed.

Readback detects some violations after the fact; it does not prevent unauthorized side effects. “Do not merge” in a prompt is not merge denial.

## Blocking probe matrix

### Provider authority

- Check current provider documentation for the effective permission model.
- Ask whether the permission required for the intended operation also grants forbidden actions. For GitHub, ordinary repository Write access can include push, approval/request-changes, and merge; rejecting only Maintain/Admin does not prove merge denial.
- Verify exact repository/ref restriction, not merely that tests use the expected ref.
- Negative probes: another branch/ref, another repository, merge, approval, close/retarget, force push.
- Accept “branch-only, merge-free” only when enforced by a narrow broker/wrapper or independently verified server-side policy. Local enums and prompt text do not constrain a raw provider token.

### Credential exposure and model auth

- Inspect child env, argv, helpers, temp files, sockets, inherited descriptors, and subprocesses.
- A child with general Bash plus a raw token can read, print, retain, or misuse it.
- Prefer launcher-owned capability operations bound to repo/PR/ref/head, keeping provider credentials outside the model process.
- Model authentication must use a closed typed/provider mechanism. An arbitrary env-name exception must not bypass GitHub/JMD/deploy/cloud/client/account/approval secret denials.

### HOME and filesystem discovery

- Redirecting only GitHub/Git config is not full HOME isolation.
- Parent HOME may expose SSH keys, cloud configs, registries, browser/session data, and client files through Read/Bash.
- Use a launcher-owned synthetic HOME populated only with reviewed runtime material.
- Probe direct reads of representative parent-home files and common discovery paths.

### Process lifecycle

- A timeout on one PID may leave descendants alive.
- Launch untrusted lanes in a new process session/group; reap the group on completion, timeout, cancellation, and exceptions with bounded TERM→KILL escalation.
- Remove scratch credentials/capability endpoints only after the group is gone.
- Add a real descendant-survival regression.

### Reviewer isolation

- Omitting Edit/Write is not read-only when unrestricted Bash remains.
- Give independent reviewers fresh exact-head worktrees or immutable views.
- Verify HEAD/tree/cleanliness after every reviewer and probe shell mutation/cross-reviewer contamination.

### Artifact semantics

- Verify author, new stable ID, exact commit, repo/PR/role/head binding, and artifact state.
- If reviewers may not approve/request changes, accept only the intended neutral formal-review state (normally GitHub `COMMENTED`); reject `APPROVED`, `CHANGES_REQUESTED`, `PENDING`, `DISMISSED`, and unknown states.
- Require the binding tag at the exact documented location, not as an arbitrary substring.
- For credential-free relay, refresh the live head before transport and read back login, state, commit ID, marker, and URL.

### Legacy/script parity

- Script/argv compatibility must not bypass scoped identity, credential mediation, artifact readback, or fail-closed requirements.
- Reject unscoped legacy configs with a migration error when the new contract requires identities.
- Add a whole-run negative test proving no identity/no artifact cannot reach merge-ready.

## Evidence format

Each blocker should contain a stable ID, `file:line`, concrete failure path, prevention-vs-detection distinction, bounded fix, and former-red probe. Separate deterministic/static proof from missing live qualification; synthetic doubles do not prove live credentials, models, branch restrictions, or remote artifacts.
