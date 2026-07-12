# NotebookLM Scout Degraded Mode

Use this when a scheduled repo-local scout is required to query NotebookLM before choosing a move, but `notebooklm ask` is temporarily rate-limited/rejected.

## Pattern

1. Still run the required auth check first:

```bash
/Users/creator/.local/bin/notebooklm auth check --test --json
```

2. Attempt the required `notebooklm ask` calls with the compact repo digest. If they fail due rate-limit/rejection, retry once after a short wait with a shorter prompt.

3. If `ask` still fails, gather lower-impact NotebookLM grounding instead of inventing an answer:

```bash
/Users/creator/.local/bin/notebooklm metadata --notebook <NOTEBOOK_ID> --json
/Users/creator/.local/bin/notebooklm summary --notebook <NOTEBOOK_ID> --json
```

4. Treat this as degraded grounding:

- use only broad durable principles from metadata/summary;
- do not claim the notebook recommended a specific change;
- note the ask failure in the final report;
- choose only a small, reversible, repo-local improvement backed by live repo/adversarial state;
- do not commit raw NotebookLM output.

## What to avoid

- Do not keep hammering `notebooklm ask` in a loop.
- Do not skip NotebookLM grounding silently.
- Do not convert rate-limit failures into a durable claim that NotebookLM is broken.
- Do not use degraded mode to justify risky product/launch/payment/outreach actions.

## Good fit example

A product/autonomy scout reads adversarial reviewer findings, gets NotebookLM summaries about legible repo state and adversarial evaluator loops, then lands a small repo-local gate/validator/checklist that turns the reviewer finding into an executable stop condition.
