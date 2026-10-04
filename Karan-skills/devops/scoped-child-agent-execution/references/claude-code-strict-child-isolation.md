# Strict Claude Code Child Isolation

Use this reference when Claude Code receives `Bash`, consumes untrusted issue/PR/web content, or runs on a workstation containing unrelated credentials. This complements the ordinary scoped non-interactive launcher; it is the stronger path for authority-sensitive work.

Authoritative Claude source: https://code.claude.com/docs/en/sandboxing

## Core distinction

A synthetic `HOME`, scrubbed environment, empty MCP configuration, and narrow `--allowedTools` list are credential/configuration hygiene. They are **not** an operating-system filesystem boundary. Without OS confinement, a same-UID Bash process can name absolute paths, inspect shared runtime surfaces, or connect to discoverable same-UID Unix sockets.

Claude Code's sandbox is the enforceable Bash boundary:

- macOS: Seatbelt;
- Linux/WSL2: Bubblewrap, plus the documented socket-filter dependency where Unix-socket denial matters;
- settings: `sandbox.enabled`, `sandbox.failIfUnavailable`, `sandbox.allowUnsandboxedCommands`;
- filesystem: `sandbox.filesystem.denyRead`, `allowRead`, `denyWrite`, `allowWrite`;
- network: explicit domains and Unix sockets only.

## Hardened settings

Generate a fresh launcher-owned settings file for each lane. PR-controlled files and caller arguments must not supply or replace it. Check the **current authoritative Claude settings documentation** before coding: validate supported effective keys and their exact nesting, not plausible-looking custom fields that Claude may ignore.

```json
{
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "allowUnsandboxedCommands": false,
    "excludedCommands": [],
    "filesystem": {
      "disabled": false,
      "denyRead": ["/operator/home", "/operator/home/.ssh"],
      "allowRead": ["/operator/home/projects/worktrees/exact-lane", "/exact/lane/runtime"],
      "denyWrite": ["/launcher/global-scratch", "/exact/lane/runtime", "/exact/lane/settings.json"],
      "allowWrite": ["/operator/home/projects/worktrees/exact-lane", "/exact/lane/scratch", "/exact/lane/home"]
    },
    "network": {
      "allowedDomains": [],
      "deniedDomains": ["*"],
      "allowLocalBinding": false,
      "allowUnixSockets": ["/exact/lane/capability.sock"]
    }
  }
}
```

The exact schema can change, so the documentation wins over this example. In particular, do not substitute decorative checks such as `filesystem.enabled`, root-level `allowLocalBinding`, or invented `allowAll`/`allowedHosts` fields when the runtime documents `filesystem.disabled` and nested network controls.

For **read** rules, a broad operator-home `denyRead` may coexist with a more-specific `allowRead` for the exact authorized worktree beneath it. Do not assume the same exception behavior for writes: a live Claude Code 2.1.273 macOS probe denied a worktree write when `denyWrite` covered `/Users/creator`, despite an exact worktree `allowWrite`; denying `/private/tmp` also broke Bash heredoc temporary files. Treat read/write precedence separately. Keep launcher control paths outside child-writable roots, deny those exact control paths, and require a successful authorized-write plus denied-control-write probe before launching implementation. A proposed policy correction is not verified until the new runtime probes pass; honor any operator approval timeout without retrying through another tool. Require exact credential-subpath denies and reject unrelated home subpaths. Add a real-topology regression using the deployment path shape; fixtures such as `/work/tree` can hide a production launcher that always refuses `<operator-home>/projects/worktrees/...`.

For Claude's internal temp files, `TMPDIR` alone may be insufficient on macOS: Claude Code 2.1.273 still attempted shell-wrapper bookkeeping under `/tmp/claude-501`, causing a trailing command failure after successful probes when that shared path was denied. Current authoritative environment-variable docs specify `CLAUDE_CODE_TMPDIR` (Claude appends `claude-{uid}`). Setting both `TMPDIR` and `CLAUDE_CODE_TMPDIR` to the same existing task-scoped scratch root fixed the live probe without granting shared-temp access. Verify the actual tool-result exit/output, not only the model summary.

Also set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`. Reject runtime overrides for `--settings`, `--setting-sources`, sandbox disablement, extra directories, weaker isolation, excluded commands, Apple Events, MCP/policy sources, and unsandboxed fallback. Probe the flag's behavior with a fake value before claiming it prevents descendant environment inheritance: the lane's capability secret must still reach its broker shim.

Array settings can merge across user/project/local scopes. Use controlled empty setting sources (verify the installed CLI's exact syntax, such as the single-token `--setting-sources=` form) or managed policy when broader inherited `allowRead`, `allowWrite`, domain, or excluded-command entries would violate the lane.

## Tool boundary

The OS sandbox applies to `Bash` and Bash descendants. Claude's built-in `Read`, `Edit`, `Write`, `Glob`, `Grep`, `WebFetch`, and similar tools use Claude's permission system instead.

When the safety claim depends on OS confinement:

1. expose `Bash` only and edit/test through sandboxed shell commands; or
2. add exact permission rules for every non-Bash tool and prove them with former-red tests.

Never describe a `Read,Edit,Write,...` allowlist as a filesystem sandbox.

## No-credential repair worker

For a sensitive repair cycle:

1. Claude edits and tests in a disposable worktree under strict sandboxing.
2. Deny writes to Git metadata if Claude does not need to commit.
3. Give Claude no GitHub/Linear token and no outbound Bash network.
4. Hermes inspects the full diff, reruns checks, commits, pushes the authorized branch, and verifies the remote PR commit list.
5. Disclose transport accurately; do not attribute Hermes' commit/push to Claude.

Minimal launch shape:

```bash
CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 claude --print \
  --model 'claude-opus-5' \
  --permission-mode auto \
  --allowedTools Bash \
  --disallowedTools Read Edit Write Glob Grep WebFetch WebSearch \
  --setting-sources= \
  --settings /launcher-owned/lane-settings.json \
  --strict-mcp-config \
  --mcp-config /launcher-owned/empty-mcp.json \
  --max-turns <bounded> \
  --max-budget-usd <bounded> \
  '<prompt>'
```

The launcher-owned `/launcher-owned/empty-mcp.json` must contain the MCP envelope, even with no servers:

```json
{"mcpServers": {}}
```

### Schema-correction and effective-runtime preflight

A verified launch recovery corrected a bare `{}` MCP file to the envelope above, then reran the same strict preflight successfully without changing sandbox policy, tool scope, credentials or workflow authority. Treat this as a narrow control-file correction, not grounds to disable strict MCP configuration or isolation. Check current CLI help when reusing a launcher; historical example flags are not a compatibility guarantee.

Before expensive work, run harmless boundary probes and inspect the actual tool-result record, not just the model's final summary:

- authorized project read and task-scratch write succeed;
- a parent-private nonsecret fixture read is denied;
- operator-control write is denied, and parent readback confirms unchanged bytes;
- unrelated-domain egress is denied;
- when explicitly allowed, anonymous access to the exact public PR returns the expected head.

Also inspect the runtime initialization record. In the verified run, subprocess hardening forced requested `dontAsk` mode to effective `default`; Bash remained the only exposed tool, its explicit allowance worked, and all six boundary probes passed with tool exit status zero. Preserve hardening rather than disabling environment scrubbing to make the requested mode label appear. An effective mode label alone neither proves nor disproves sandbox enforcement. Passing preflight proves those tested launch boundaries only—not implementation completion, test success, or remote mutation.

## Capability and runtime isolation

Mode 0700 on a random Unix-socket directory does not isolate one process from another process running as the same UID.

For launcher-owned capabilities:

- one cryptographically random authentication secret per lane;
- constant-time validation before parsing/dispatch;
- only that lane's exact socket allowed by sandbox policy;
- wrong/missing/replayed-after-close requests fail closed;
- stop accepting, terminate broker subprocesses, drain handlers, and join threads before `close()` returns.

For runtimes and scratch material:

- create a fresh launcher-owned runtime/shim directory **and writable scratch/home** per lane;
- deny the launcher/global scratch root, then narrowly re-allow only the current lane's exact writable scratch/home and authorized builder worktree;
- keep settings JSON, strict empty-MCP config, runtime/shim, broker payloads, and every other lane's material outside the child's write authority;
- account for sandbox defaults that may permit OS temp paths: a control file under `/tmp` is not protected until a more-specific deny covers it;
- point `TMPDIR` at the lane's own scratch when tools need temporary files;
- use a minimal trusted PATH and pre-resolved absolute executables;
- never reuse a child-writable runtime across lanes;
- treat owner-only mode bits and `chmod` as hygiene, not same-UID confinement—a same-UID process can restore write bits unless the OS sandbox denies the write;
- prefer inherited socketpair/file-descriptor designs over discoverable listener paths when practical.

A surviving self-detached process is a downstream lifetime concern, but the current launcher must still prevent that sandboxed survivor from writing later lanes' control material.

## Reviewer and diff integrity

- `git status` alone does not prove exact reviewer bytes. Verify exact HEAD, tracked bytes/tree, index entries, skip-worktree/assume-unchanged flags, and relevant execution-affecting Git config before and after review.
- After a builder reports a new head, compare the committed old-head→new-head path set with the frozen allowed-path packet before advancing the loop.

## Residual lifetime limit

A process group is not a complete lifetime domain. A malicious descendant can call `setsid()` and escape ordinary group termination.

Strict sandboxing should keep inherited filesystem/network/socket restrictions on descendants, reducing authority, but it does not prove every process is gone at the wall-clock deadline. Full destruction requires a container/VM, Linux cgroup, Windows job object, separate supervised OS identity, or equivalent supervisor-owned process domain.

If that primitive is absent:

- state the limitation precisely;
- do not claim full descendant cleanup;
- move live containment qualification to a downstream gate or stop for a human scope decision;
- do not paper over it with extra synthetic-`HOME` or process-group tests.

## Live verification and interrupted-worker recovery

Do not let generated-policy unit tests validate themselves in a circle. Before accepting the implementation:

1. compare every security-sensitive key with the current Claude docs;
2. inspect the final generated settings, argv, environment, and path precedence;
3. run harmless live probes with fake values: authorized worktree read, denied private-path read, denied external-domain access, exact socket reach, and capability-secret availability to the shim;
4. run the policy against the real worktree/home/scratch topology, not only synthetic paths;
5. rerun the full deterministic suite in the trusted parent environment;
6. after commit/push, obtain fresh detached exact-head independent review.

A strict repair-worker sandbox may intentionally block AF_UNIX bind, localhost, browser startup, OS temp writes, or test-created subprocesses. That makes the worker's test result **unverified**, not automatically a code pass or a code failure. Rerun those tests in the trusted verifier environment and preserve the distinction.

If a worker reaches a turn/time limit, treat its final state as unknown: confirm no process/descendant remains, inspect HEAD/status/diff/changed paths, run the parent suite, and only then decide whether the uncommitted delta is coherent enough for one bounded corrective continuation. Keep commit, push, PR comments, and tracker mutation parent-owned until independent verification is green. A later exit-zero or `DONE` marker is still a handoff signal, never acceptance evidence.

## Non-Claude/script lanes

Claude's OS sandbox governs Claude Bash and its descendants. It does not automatically sandbox an arbitrary legacy `argv` reviewer, builder, or gate. Do not describe such lanes as Claude-sandboxed. Either route them through a separately proven hardened launcher, reject them for the security-sensitive role, or scope the claim explicitly and require independent review of the residual boundary.

## Former-red probes

Require tests for:

- worktree read succeeds; private absolute-path read fails;
- sandbox-unavailable and unsandboxed-retry paths fail closed;
- non-Bash file/network tools are unavailable or equivalently denied;
- cross-lane socket authentication fails;
- one lane cannot replace another lane's runtime;
- server close drains in-flight work and leaves no broker subprocess;
- hidden reviewer mutations cannot pass via index flags or modify/restore tricks;
- one allowed plus one unrelated committed path fails containment;
- self-`setsid` either dies inside the qualified OS process domain or yields explicit unsupported/needs-human status.
