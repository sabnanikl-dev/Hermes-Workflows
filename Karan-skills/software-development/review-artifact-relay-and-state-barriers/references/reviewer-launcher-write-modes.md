# Reviewer launcher write modes

Use this reference when credential-free reviewer lanes need both strong sandboxing and durable `/tmp` artifacts.

## Why the mode matters

Reviewer prompts commonly require two kinds of writes:

- test/runtime scratch (`TemporaryDirectory`, bytecode caches, generated fixtures);
- a signed relay body under `/tmp`.

A filesystem read-only child can reason correctly yet fail both. That is a launcher-contract mismatch, not a PR defect. Choose the write mode before launch instead of recovering every artifact from terminal output.

## Capability matrix

| Lane | Normal launcher shape | Bounded write behavior | Do not assume |
|---|---|---|---|
| Codex Reviewer A/B | `codex-reviewer --role A|B --workdir <detached> --prompt-file <file>` | Use `--workspace-write` when temp-based tests or `/tmp` artifact creation are required. Prompt restricts writes to `/tmp`; verify detached worktree remains clean. | Read-only can write `/tmp`; Hermes reviewer flags are accepted. |
| Hermes Integration Auditor | `reviewer --workdir <detached> --prompt-file <file>` | Wrapper may set `HERMES_WRITE_SAFE_ROOT=/tmp` itself. Use the wrapper's native flags only. | Codex `--workspace-write` or `--read-only` flags are accepted. |

Always inspect the installed wrapper or `--help` when the interface may have changed.

## Recommended A/B launch

```bash
codex-reviewer --role A \
  --workdir /absolute/path/to/clean-detached-worktree \
  --prompt-file /tmp/review-a-prompt.md \
  --workspace-write
```

Prompt requirements:

- repository files are read-only by policy even though the sandbox can write;
- temporary evidence and final artifact may be written only under `/tmp`;
- no credentials, fetch/ref creation, commit, push, posting, or external mutation;
- final `git status --porcelain` must be clean;
- artifact path, exact head, role, runtime, verdict, and blocker count are mandatory.

Use `--read-only` only for genuinely write-free probes where an inline artifact is acceptable.

## Recommended Auditor launch

```bash
reviewer \
  --workdir /absolute/path/to/clean-detached-worktree \
  --prompt-file /tmp/integration-audit-prompt.md
```

Do not append Codex sandbox flags unless the installed Hermes wrapper explicitly documents them. The wrapper's `/tmp` safe-root policy is the write boundary.

## Read-only recovery fallback

If a reviewer already completed in read-only mode and returned a complete signed body inline:

1. Capture only the fenced/declared artifact body, excluding surrounding explanation and token/runtime logs.
2. Materialize it under `/tmp` in the parent process.
3. Validate exactly one role marker, canonical full head, verdict, blocker count, reviewer signature, and runtime line.
4. Re-query the live PR head.
5. Add a transport-only disclosure without changing the substantive findings.
6. Relay under the verified reviewer account and directly read back the immutable ID.

If the final output contains only a summary and no exact body, rerun a focused artifact-recovery lane in bounded write mode. Do not invent detailed reviewer prose from a summary.

## Test and compile hygiene

Read-only sandboxes can fail for reasons unrelated to product code:

- no writable temporary directory;
- `__pycache__` creation denied;
- compiler/cache output denied.

Recovery options, in preference order:

1. rerun the reviewer in bounded workspace-write mode on a disposable detached worktree;
2. redirect caches to `/tmp` when supported;
3. use in-memory syntax compilation for a write-free secondary check.

Never count sandbox-only write failures as test failures or PR blockers. Record the infrastructure limitation and rely on independent parent verification plus the corrected reviewer run.

## Verification checklist

- [ ] A/B worktrees are separate, detached, exact-head, and clean before launch.
- [ ] Launcher mode matches test/artifact write needs.
- [ ] No reviewer credential is present.
- [ ] A/B complete before the Auditor packet is refreshed.
- [ ] Worktrees remain clean after exit.
- [ ] Prepared artifacts exist or are explicitly recovered from exact stdout.
- [ ] Live head still matches before relay.
- [ ] Relay author/type/head/role/verdict is directly read back by immutable ID.
