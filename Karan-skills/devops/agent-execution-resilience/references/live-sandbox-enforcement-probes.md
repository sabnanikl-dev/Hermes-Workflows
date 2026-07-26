# Live sandbox enforcement probes

## Why this exists

Policy generation and local path-decision tests can agree while the real agent sandbox behaves differently. Use this matrix against the exact generated settings and the exact supported client version.

## Disposable fixture

Create a synthetic worktree and isolated lane tree outside the real implementation worktree:

```text
<probe-root>/worktree/
  .git/                # harmless synthetic metadata target
  allowed.txt
<probe-root>/lanes/001-builder/
  home/
  scratch/tmp/
  runtime/
  input/
  settings.json
<probe-root>/lanes/002-foreign/
<probe-root>/broker/
<probe-root>/outside-home-secret
```

Also create:

- an operator-HOME credential path whose contents are never printed;
- a token file outside HOME;
- a token file nested inside an otherwise allowed/reopened prefix;
- an empty MCP file;
- a local TCP and Unix-socket target.

The probe reads/writes only sentinel data. Never use a real credential value.

## Assertion matrix

Require exact lines such as:

```text
PASS worktree-read
PASS worktree-write
PASS git-metadata-write-denied
PASS operator-home-credential-read-denied
PASS unrelated-home-read-denied
PASS outside-home-secret-read-denied
PASS configured-token-file-read-denied
PASS nested-token-file-read-denied
PASS own-runtime-read
PASS own-runtime-write-denied
PASS own-input-read
PASS own-input-write-denied
PASS own-settings-read
PASS own-settings-write-denied
PASS empty-mcp-read
PASS empty-mcp-write-denied
PASS foreign-lane-read-denied
PASS foreign-lane-write-denied
PASS broker-material-read-denied
PASS broker-material-write-denied
PASS own-scratch-write
PASS own-home-write
PASS lane-scoped-tmpdir
PASS external-network-denied
PASS local-binding-denied
PASS unix-socket-bind-denied
LIVE_PROBE_STATUS=PASS FAILURES=0
```

Do not accept a summarized model response without the raw assertion file.

## Read precedence former-red

When the sandbox uses deny-then-specific-reopen semantics:

1. Deny the broad filesystem/root first.
2. Reopen only trusted lane/system roots required for execution.
3. Apply exact sensitive-path denials inside reopened roots.
4. Test unrelated outside-HOME and nested-token cases live.

A local helper must model the same most-specific-path precedence; otherwise deterministic tests can produce false confidence.

## Git-lane proof

For a builder/reviewer design that advertises Git operations, add a disposable real repository probe:

- source clone hash/status before;
- lane creation at exact head;
- builder edits, stages, and commits using only lane-owned Git state;
- broker computes/pushes only the bound head/ref in a local fake remote;
- path containment rejects an unauthorized changed path before push;
- reviewer can execute `git diff origin/main...HEAD` and history reads;
- reviewer writes to checkout and Git state are denied;
- source clone/shared refs/config/hooks remain byte/status unchanged.

Deterministic fake-runner tests do not replace this real Git probe.

## macOS fail-unavailable simulation

Use an outer Seatbelt profile:

```scheme
(version 1)
(allow default)
(deny process-exec (literal "/usr/bin/sandbox-exec"))
```

1. Control: under the outer profile, invoke nested `/usr/bin/sandbox-exec`; require `Operation not permitted`.
2. Delete a harmless marker in the disposable worktree.
3. Launch the real agent with exact settings under the outer profile and request only that marker write.
4. Require the Bash operation to fail and the marker to remain absent.

This tests fail-closed startup without modifying the host binary. Keep the target disposable in case the policy unexpectedly fails open.
