---
name: agent-workflow-orchestration
description: "Use for orchestrating agent/automation workflows: Kanban orchestrator and worker roles, webhook-triggered agent runs, deterministic n8n automations, and conservative closeout/dreaming pipelines."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, orchestration, webhooks, n8n, workflows, automation]
    related_skills: [hermes-agent, productivity-integrations]
---

# Agent Workflow Orchestration

## Overview
Use this umbrella when Hermes is operating an agentic workflow rather than a single task: Kanban decomposition/worker execution, webhook-triggered runs, deterministic n8n automations, or closeout/dreaming reports.

## When to Use
- Route work through Kanban orchestrator/worker roles.
- Trigger agents from webhooks or event subscriptions.
- Design deterministic n8n file/API reconciliation workflows.
- Run conservative closeout/dreaming reports that stage knowledge before promotion.

## Workflow
1. Define the operating boundary: trigger, owner, state store, approval gates, and expected outputs.
2. Make state explicit and inspectable.
3. Keep worker/orchestrator responsibilities separate.
4. Verify external side effects and record evidence.
5. Close out with concise status, blockers, and next actions.

## Repo-local autonomy labs
When Karan asks to make Hermes more proactive inside a low-risk personal/infrastructure repo, prefer an autonomy-lab shape: fork-friendly docs + quiet deterministic watchdog + bounded scout + executable loop audit + explicit autonomy tiers. If Karan grants repo-local autonomy, direct commits and auto-merged PRs are allowed after deterministic checks; do not keep forcing manual approval. If Karan wants real money to flow, add a marketed-value lane that packages proven repo artifacts into offers/drafts while treating publication, outreach, payments, purchases, and third-party contact as human-release boundaries. See `references/repo-local-autonomy-lab.md`.

When a scheduled scout must query strategic notebooks before choosing a move, use notebook output to create **mechanical invariants**, not raw notes: distill one principle into a validator, checklist, contract, or template that future runs can execute. Prefer small dependency-free validators that block known drift (for example consumer-facing artifacts referencing internal experiment/tracker files) and verify them with an ad-hoc red/green fixture before committing.

When a scheduled scout is required to inspect an external/adversarial reviewer report before acting, make the reviewer state **metadata-visible** in the repo context instead of copying raw reviewer prose into prompts or artifacts. Include presence, generated time, decision, report commit/HEAD, current repo HEAD, stale-vs-current status, and P0/P1 counts; then force the scout to re-check live repo state before acting on stale findings. This preserves the maker/checker split without letting old reviews become ungrounded authority. See `references/adversarial-report-freshness.md`.

If the NotebookLM `ask` endpoint is temporarily rate-limited/rejected, do not hammer it or silently skip grounding. Retry once with a shorter prompt after a short wait, then fall back to `notebooklm metadata --json` and `notebooklm summary --json` as degraded grounding. In that mode, use only broad durable principles, report the degradation, and choose only a small reversible repo-local improvement backed by live repo state. See `references/notebooklm-scout-degraded-mode.md`. Do not encode the transient failure as “NotebookLM is broken.”

When Karan asks to stop recurring crons from querying NotebookLM/external research every run, convert prior findings into a repo-local `research/` corpus and update the **whole loop**, not just docs: cron prompts, scheduler job config, repo validators/audits, product/governor docs, and final-report formats. If Karan delegates manual approval to an adversarial review, make the reviewer emit an explicit clean decision such as `READY_FOR_PUBLIC_LIVE`; downstream crons can act on that gate while preserving hard stops for KYC, paid purchases, credentials/CAPTCHA/phone, private data, unsupported claims, unrelated accounts/repos, and global Hermes authority changes. For repo-local public-output skills, vendor them under the repo `skills/` tree and point crons at file paths rather than installing global Hermes skills. See `references/repo-local-research-corpus-and-adversarial-gate.md`.

When Karan asks for robust autonomous-agent evals in a repo-local experiment, add a small dependency-free eval harness rather than only prose: `docs/agent-evals.md` for primitives and maker/checker policy; `evals/tasks.json` for outcome-driven task/trial/trace/outcome/grader contracts; `templates/agent-done-contract.md` and `templates/agent-trial-record.json`; and `scripts/agent_eval_audit.py` wired into repo validators, loop audits, cron prompts, and adversarial reviewer context. The suite should cover no-live-NotebookLM grounding, adversarial public-live gates, one-move experiments, claim/public-output safety, remote verification, trace completeness, and saturation/frontier behavior. Require pass@k/pass^k, accept rate, blocked rate, and cost-per-accepted-change metrics, while treating 100% eval score as a regression guard that needs harder frontier tasks as capability grows.

## n8n live-smoke pattern
For gated n8n automations that need credentialed proof without schedule activation: save the live workflow first, assert `active=false`, PUT a temporary manual-trigger graph with only the nodes needed for the smoke, run the exact limited scope, read back external writes, then restore the original workflow before parsing/reporting. On restore via the n8n API, do not blindly replay every `settings` key from a GET response: instance/read-only keys such as `binaryMode` can make PUT fail. Preserve only PUT-accepted workflow settings (for example `executionOrder`) plus `name`, `nodes`, `connections`, `staticData`, and `pinData` as needed. Verify after restore that `active=false`, expected node count/shape is back, and no temp manual trigger remains.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] Workflow state and assignee/trigger are visible.
- [ ] Automations are deterministic/idempotent where possible.
- [ ] External writes are backed up or read back.
- [ ] Closeout promotes only durable patterns, not stale task logs.
