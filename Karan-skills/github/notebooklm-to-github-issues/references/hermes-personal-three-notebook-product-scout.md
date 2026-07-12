# Hermes Personal Three-Notebook Product Scout Pattern

Use this reference when a Hermes Personal product/revenue cron needs NotebookLM grounding for both product work and the repo/harness loop that supports it.

## Pattern

Query the notebooks separately every run, then synthesize outside NotebookLM:

| Notebook | ID | Lane |
|---|---|---|
| AI OS | `7442a0ae-5a2d-4863-ac9b-b0a8bccea6f3` | loop engineering, operating-system design, agent workflow/harness improvements |
| Strategic Engineering: Harnessing AI as a Force Multiplier | `95758f68-a24f-442b-8973-bf542052b267` | harness engineering, verification discipline, work-system improvements |
| Ai money | `c5c73a43-3ad5-489b-8f57-354ad6bfe7f2` | product/revenue artifacts, buyer insight, offer clarity, pricing, distribution, experiment metrics |

## Prompt contract

NotebookLM cannot see live repo state. Before querying, provide a compact current-state digest: repo/ref, active product workspace, launch-readiness gaps, experiment ledger status, validators, and relevant open issues when checked.

For AI OS / Strategic Engineering ask for:

```text
single highest-leverage repo-local loop/harness/work-system improvement; source-grounded principle; current gap; recommended artifact; risk/caveat; verification metric
```

For Ai money ask for:

```text
single highest-leverage product/revenue-generating repo-local artifact or experiment; buyer insight; offer/product implication; risk/caveat; recommended artifact; suggested experiment metric
```

## Execution rule

The cron should still choose exactly one concrete move per run. The three notebooks are grounding inputs, not permission to do three tasks.

Allowed outcome lanes:

- product/revenue work;
- loop/harness/work-system improvement that directly accelerates the product loop;
- approval/blocker report when no safe repo-local move remains.

## Pitfall

Do not implement an every-2nd-run NotebookLM cadence for this class of scout when Karan wants every-run grounding. Also avoid persistent run-counter state files unless the user explicitly asks for staggered cadence; stale counters can silently preserve obsolete behavior.