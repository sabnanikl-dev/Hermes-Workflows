# Live qualification for Claude Code sandbox policies

Use this when a technical artifact or PR creates or changes code-generated Claude Code sandbox settings, launcher-owned filesystem boundaries, subprocess environment rules, or fail-closed sandbox startup behavior. Unit tests against a local policy model are necessary but not sufficient: the real Claude client and OS sandbox are the authority on policy semantics.

## Why this gate exists

A policy model can be internally consistent and still disagree with the client. A real qualification found broad `denyWrite` entries over an operator home and shared launcher scratch remained hard denials even when narrower paths appeared in `allowWrite`. The lane could not write its own worktree, scratch, or synthetic home. Claude documentation explicitly describes narrower `allowRead` reopening a denied read region; do not assume write rules are symmetric.

Claude also rewrites sandboxed Bash `$TMPDIR`. Setting only `TMPDIR` in the child environment does not prove temporary files stay lane-scoped. Use launcher-owned `CLAUDE_CODE_TMPDIR`, keep the path short, and verify the value from inside sandboxed Bash. Re-run these probes whenever the supported Claude Code version changes.

## Qualification recipe

1. Record the exact Claude Code version and exact commit under review.
2. Generate the settings file through production code, not a hand-written lookalike. Validate and hash that file.
3. Create disposable material:
   - a fake worktree under the operator home with a fake `.git/` directory;
   - one lane's scratch, synthetic home, runtime, frozen input, and settings;
   - empty MCP config;
   - sibling-lane and broker markers;
   - known benign credential-shaped files outside the lane. Never use real secret contents.
4. Launch Claude with the same production flags: code-owned `--settings`, empty setting sources, strict empty MCP, Bash-only tools, no unsandboxed fallback, and subprocess credential scrubbing.
5. Have sandboxed Bash execute one deterministic probe script. Write its result inside lane scratch and read it back outside the model. Do not rely on model prose.
6. Require all of these:
   - worktree read/write allowed for a builder;
   - own scratch/home write allowed;
   - observed `$TMPDIR` is lane-scoped;
   - Git metadata write denied;
   - operator credential/unrelated-home reads denied;
   - runtime/input/settings/MCP writes denied;
   - sibling-lane and broker read/write denied;
   - external network, local TCP bind, and unauthorized Unix-socket bind denied.
7. A reviewer policy must additionally deny worktree writes by exact path. Silence is not enough because the current working directory is writable by default.
8. Keep exact immutable-path `denyWrite` rules, but do not place a broad `denyWrite` over a path the lane must write and expect `allowWrite` to reopen it. Rely on the client's default write boundary plus narrow `allowWrite` entries.
9. Run both supported interpreters, compile/config checks, and `git diff --check` after any repair.

## Fail-if-unavailable probe on macOS

A supported Mac normally always has Seatbelt, so configuration inspection alone does not exercise failure. Use a disposable outer Seatbelt profile that allows normal behavior but denies `process-exec` for `/usr/bin/sandbox-exec`:

```scheme
(version 1)
(allow default)
(deny process-exec (literal "/usr/bin/sandbox-exec"))
```

First prove a nested `sandbox-exec` invocation fails under that profile. Then launch Claude under the profile with `sandbox.failIfUnavailable=true` and ask Bash to create a harmless marker inside the disposable worktree.

Pass criteria:

- nested sandbox startup fails;
- the Bash operation does not run;
- the marker remains absent.

Do not use the top-level `claude` process exit code as the verdict: non-interactive Claude can exit zero after reporting a Bash tool failure. The marker and tool error are the evidence.

## Common false confidence

- A unit test that calls a local policy helper proves only the helper.
- Correct settings key names do not prove client precedence.
- Ordinary `TMPDIR` does not prove sandboxed Bash receives it.
- Model prose is not raw probe evidence.
- A clean Git status does not prove the OS boundary worked.
- A successful Claude process exit does not prove its Bash tool executed.

Clean up disposable worktrees, markers, settings, and outer profiles after retaining evidence.