---
name: scheduled-monitoring-workflows
description: Design, harden, test, and verify recurring watchers and quiet scheduled monitors that research or poll live state and notify only on actionable changes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [cron, watchers, monitoring, alerts, polling, validation, automation]
    related_skills: [hermes-agent, agent-workflow-orchestration, research-workflow]
---

# Scheduled Monitoring Workflows

## Overview

Use this umbrella for recurring watchers, deal scouts, availability monitors, threshold alerts, and quiet scheduled checks. The central requirement is not merely “the job ran”; it is that the monitor emits a message only when live evidence satisfies an actionable contract.

## When to Use

- Create or modify a cron-backed deal, price, stock, travel, status, or availability watcher.
- Fix a recurring alert that was technically within budget but not actually worth acting on.
- Turn model-assisted research into a quiet, deterministic notification pipeline.
- Add regression fixtures to an unattended script.
- Verify a scheduled monitor still points to the intended script, schedule, and destination after edits.

## Operating Contract

Define these before implementation:

1. **Trigger:** schedule or polling interval.
2. **Source:** live page, API, command, or model-assisted research.
3. **Eligibility:** what exact entities/variants/conditions can qualify.
4. **Actionability:** threshold or change that makes an alert worth interrupting the user.
5. **Evidence:** what must be verified from the original source at alert time.
6. **Delivery:** destination and exact user-facing payload.
7. **Silence:** empty output or explicit no-op behavior when nothing qualifies.
8. **Failure mode:** fail closed unless the user explicitly wants health/error alerts.

## Architecture

Prefer a layered pipeline:

```text
live discovery or polling
→ strict machine-readable candidate
→ deterministic shape validation
→ eligibility/denylist checks
→ original-source state verification
→ threshold/change detection
→ formatted alert or empty stdout
```

For script-only jobs, stdout is the delivery contract: non-empty output should already be the exact message; empty output should mean silence. For model-assisted jobs, constrain model output and independently enforce the important invariants in code.

## Deal and Availability Watchers

Do not confuse a nominal range with an actionable recommendation. Separate:

- **Eligibility:** exact model/route/date/capacity/technology/condition/seller constraints.
- **Value:** tier-specific price, availability, or quality threshold.

Prompt-only rules are insufficient for unattended notifications. Re-check model, capacity, route/date, retailer/host, active offer, and range in deterministic code where possible. Parse source URLs and normalize hostnames instead of trusting model-provided retailer labels.

See `references/product-deal-watcher-validation.md` for the full layered deal-watcher pattern and regression matrix.

## Testability

Design dependency overrides into scripts so a fixture can replace live components without touching external systems, for example:

- `SCOUT_BIN` or `HERMES_BIN`
- `VERIFIER` or `PRICE_VERIFIER`
- fixture input/output paths

Minimum regression matrix:

- the original false positive is silently rejected;
- an ineligible candidate from an allowed source is rejected;
- an eligible candidate from a disallowed source is rejected;
- an over-threshold candidate is rejected;
- a valid candidate produces exactly one correctly formatted alert;
- malformed or ambiguous source state produces no alert.

Fixture-test before triggering a live job that could message the user.

## Safe Modification Workflow

1. List jobs and identify the real job ID; never guess it.
2. Read the referenced script, prompt, verifier, and any state file.
3. Fix both the semantic layer (prompt/contract) and deterministic enforcement.
4. Run syntax/static checks.
5. Verify executable permissions and restore the intended mode if needed.
6. Run isolated fixture tests, including the historical failure.
7. Re-list scheduler state and confirm:
   - enabled/paused state;
   - script or prompt reference;
   - schedule and recurrence semantics;
   - delivery target;
   - future next-run time.
8. Summarize what changed, what was rejected/accepted in tests, and what remains.

## Scheduler Pitfalls

- Duration syntax can represent a one-shot rather than a recurring interval; verify the displayed schedule and next run.
- A previously successful cron run does not validate a newly edited script.
- Editing a script may require re-verifying its executable mode.
- Manual live runs can create duplicate or false notifications; fixtures are the safer first proof.
- A broad “other established sources allowed” exception defeats an explicit allowlist.
- Search snippets, crossed-out prices, installment amounts, recommendation cards, and stale metadata are not active offers.
- Marketplace hosts require seller-level verification even when the hostname itself is approved.

## Verification Checklist

- [ ] The alert contract describes actionability, not merely data availability.
- [ ] Original-source evidence is checked at alert time.
- [ ] Important eligibility and threshold rules are deterministic.
- [ ] Unknown or conflicting state fails closed.
- [ ] No-result behavior is silent.
- [ ] Historical false positives are regression fixtures.
- [ ] Positive fixtures emit exactly one final message.
- [ ] Script syntax and executable mode are verified.
- [ ] Scheduler state is re-read after the edit.
- [ ] No purchase, booking, posting, or other live mutation occurs without approval.
