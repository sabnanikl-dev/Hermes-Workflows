# Claude Code Cron: Read-Only Adversarial Review Loop

Use this pattern when Karan wants an external coding/review agent (especially Claude Code/Opus) to periodically critique a repo/product lane, while other Hermes crons consume the findings.

## Shape

- Create a **script-only Hermes cron** (`no_agent=true`) that runs a wrapper under `~/.hermes/scripts/`.
- The wrapper calls `claude --print --model opus` with a bounded, read-only prompt.
- Store each timestamped report outside the repo, e.g. `~/.hermes/reports/<project>/adversarial/YYYY-MM-DD_HH-MM-SS-review.md`.
- Copy the newest report to a stable pointer, e.g. `~/.hermes/reports/<project>/adversarial/latest.md`.
- Update downstream product/build crons to read the stable pointer before choosing their next move.

This gives the system a durable reviewer lane without granting the reviewer write authority.

## Wrapper requirements

1. Start in the target repo and collect a compact repo/validator snapshot.
2. Use a hard read-only prompt:
   - no edits, creates, deletes, commits, pushes, PRs/issues;
   - no external publishing, outreach, payment/listing activation, or account/config mutation;
   - no private memory/session/email/chat exports;
   - proxy metrics must not be described as revenue or real market validation.
3. Prefer `--permission-mode plan` and explicit tool allow/deny lists.
4. Write both a timestamped report and `latest.md`.
5. On Claude failure, write a `BLOCKED` report to `latest.md` so downstream crons know the reviewer lane was unavailable instead of silently using stale assumptions.

Example Claude invocation shape:

```bash
claude \
  --print \
  --model opus \
  --effort high \
  --permission-mode plan \
  --allowedTools "Read,Glob,Grep,LS" \
  --disallowedTools "Edit,Write,NotebookEdit,Bash,WebFetch,WebSearch" \
  --max-budget-usd "${CLAUDE_MAX_BUDGET_USD:-4}" \
  --no-session-persistence \
  "$(cat "$PROMPT_FILE")"
```

Do not assume every deny-list tool name exists in the installed Claude CLI. If Claude reports an unknown deny rule but still completes, remove that nonexistent tool name from the wrapper and clean future report output.

## Downstream cron integration

Patch every relevant Hermes cron prompt with a short required-read block:

```text
Adversarial Claude findings — REQUIRED IF PRESENT:
Before choosing a product/revenue/value-clarity move, check `<latest.md path>`. Treat it as read-only reviewer input, not source of truth. Prioritize unresolved P0/P1 findings when they are repo-local, buyer-useful, and inside this cron's authority. Do not copy raw Claude findings directly into buyer-facing copy; distill them into repo-local docs/product files. If the file is missing, stale, or unavailable, note that and continue with existing validators and clarity gates.
```

## Good output contract

Ask Claude for structured Markdown with:

- `Decision: PASS_TO_BUILD | NEEDS_CLARITY | BLOCK_PUBLIC_LAUNCH | BLOCKED`
- executive verdict;
- blocking P0/P1 findings, each with buyer impact, repo evidence, and safe repo-local fix;
- exactly 3 ranked next moves with file paths;
- copy/positioning notes;
- approval/safety gates;
- measurable signals to check next run;
- risk if nothing changes.

## Verification

After creating the cron:

1. Run `bash -n` on the wrapper.
2. Run the wrapper once manually.
3. Verify `latest.md` exists and contains the expected heading/decision.
4. Verify downstream cron prompts contain the required-read block.
5. List the cron and confirm schedule, enabled state, script path, and `no_agent=true`.

## Pitfalls

- Do not make the reviewer cron a builder. It should not mutate the repo.
- Do not store reports inside the repo unless the repo explicitly wants durable examples; default to `~/.hermes/reports/...` to avoid dirty working trees.
- Do not let downstream crons treat reviewer findings as source of truth; they are adversarial input to be reconciled with repo state and validators.
- Avoid asking Claude to browse the web unless explicitly needed and approved by the lane policy; product/repo critique should usually stay repo-local.
