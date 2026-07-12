# 2026-05-25 Prototype Packaging Notes

## Context

Karan asked to package the Hermes closeout dreaming workflow as a prototype skill and run it every morning at 5 AM. The workflow produces a read-only HTML report plus raw JSON/zip artifacts.

## Durable Lessons

- Treat closeout dreaming as **pattern maturation**, not one-off extraction.
- Single-night observations should stay low-confidence and staged.
- Repeated dreams should increase confidence only when the same idea recurs across time and/or source types.
- Promotion targets are review recommendations only: standard memory, Hindsight, Obsidian, skill patch, or no-op/source-of-truth.
- The prototype must remain read-only. No durable writes without explicit approval.

## Gateway Packaging Pattern

Telegram/gateway attachments should be staged under:

```text
~/.hermes/cache/documents/<report-name>/
~/.hermes/cache/documents/<report-name>.zip
```

Avoid relying on `~/Downloads` for delivery. Keep Downloads as a local review copy if useful, but emit `MEDIA:` lines from `~/.hermes/cache/documents/...`.

## Daily Runner Pattern

Use a `no_agent=true` cron for deterministic HTML generation when the script already writes the report and produces final message text. This avoids unnecessary LLM rewriting and keeps delivery stable.

Expected cron shape:

```text
name: Daily Closeout Dream Report Prototype
schedule: 0 5 * * *
script: daily_closeout_dream_report.sh
no_agent: true
deliver: origin
```

## Verification Notes

Before declaring setup complete:

1. Validate shell wrapper syntax with `bash -n`.
2. Compile the Python generator with `python3 -m py_compile`.
3. Run the wrapper once and inspect that it emits `MEDIA:` lines from `~/.hermes/cache/documents`.
4. Verify HTML and zip artifacts are nonzero.
5. Confirm the cron exists with schedule `0 5 * * *` and `no_agent: true`.
