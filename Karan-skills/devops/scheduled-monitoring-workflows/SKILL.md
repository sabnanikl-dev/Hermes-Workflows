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
8. **Failure mode:** fail closed unless the user explicitly wants health/error alerts. For requested checkpoint/report jobs, report missing evidence or failed execution explicitly; silence is appropriate only for a verified duplicate or a contractually defined no-op.
9. **Authority:** separate permission to schedule and collect from permission to publish, change tracker state, close work, or mutate the monitored system. A previous packet's publication approval does not authorize publication of future packets.
10. **Finite horizon:** when the task ends at a data boundary, distinguish that boundary from the last capture time. Allow a disclosed processing-lag review, cap query dates before requests, and define a hard expiry and incomplete-data outcome rather than silently extending the monitoring period.

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

For local automations that depend on a long-running server, use the availability-ensure pattern in `references/local-service-availability-crons.md`: health/listener checks, read-only active-state and latest-execution verification, fail-closed port handling, and Hermes-tracked background startup without manually taking over the dependent workflow.

When an approved reconciliation must run immediately, use `references/controlled-automation-reconciliation.md`: invoke the automation through its native runtime, restore the exact scheduled graph afterward, and verify target convergence independently without manually reproducing the automation's content work.

For approved high-risk operations with finite monitoring windows—DNS cutovers, deployment promotions, migration switches, or certificate changes—use the executor/watchdog split and external-verification pattern in `references/time-bounded-live-operation-watchdogs.md`.

For website DNS flips that must preserve mail and need independent HTTPS vantage points, also use `references/dns-cutover-external-verification.md`. It defines authoritative/public resolver quorums, old-TTL propagation handling, fresh completed Globalping evidence, deployed-feature-state checks, local-network limitations, and deadline/final-recommendation behavior.

## Human-response reminders

1. Bind each reminder to the original request, recipient, channel/thread and exact artifact revision. Link back to the existing request rather than resending the approval packet each day.
2. Define the local-time slot, first eligible date and stop condition before scheduling. Distinguish the scheduler's next check from the first actual reminder when a start-date guard suppresses an earlier tick.
3. Use deterministic script-only execution for fixed nudges and reply checks. Enforce every stop/date/deduplication gate in executable code, not merely the job prompt, because no-agent execution does not interpret prompt instructions.
4. Check recipient responses before sending. A reply can stop a reminder without approving the underlying work; edits, questions and voice notes must leave the approval gate unresolved. Hold uncertain replies for review rather than inferring approval.
5. Fixture-test due/not-due runs, duplicate suppression, recipient replies, unrelated authors and stopped state. Perform a read-only live probe without sending an extra reminder, then use the paused-create/readback/resume procedure below.
6. Report script testing, scheduler configuration and actual scheduled delivery as distinct evidence levels. Do not describe a script's local stopped flag as a paused cron job.

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

1. List jobs and identify the real job ID; check for equivalent scheduled work before creating another job.
2. Read the referenced script, prompt, verifier, and any state file. Record the settings outside the requested scope that must remain unchanged.
3. For agent-backed jobs, resolve the unattended model/provider from the job pin, cron override and global default—not from the interactive chat model. Run a tiny tool-free authentication probe on that exact route rather than firing the real job as an auth test. If a different route is needed, obtain explicit approval for the per-job pin; do not repair the whole fleet or change the global default by implication.
4. Fix both the semantic layer (prompt/contract) and deterministic enforcement. When job configuration needs multiple steps, create paused, apply the approved settings, verify them, then resume; this prevents a partially configured job from firing.
5. Run syntax/static checks and verify executable permissions where scripts are used.
6. Run isolated fixture tests, including the historical failure. For finite report schedules, test deadline-day, post-deadline processing-lag and late-execution date caps without querying future data.
7. Re-read scheduler state in a dedicated read-only call, separate from artifact writes or script execution, so a blocked mutation cannot obscure whether scheduling succeeded. Confirm:
   - enabled/paused state;
   - script or prompt reference;
   - schedule and recurrence semantics;
   - resolved model/provider and authorized pin scope;
   - success and failure delivery targets;
   - future next-run time.
8. Verify protected defaults and unrelated job configuration remain unchanged; ignore normal scheduler run-state churn when comparing configuration.
9. Save the job IDs, source/contract locator, schedules, delivery and verification results in the task's operational artifact, not durable user memory.
10. Summarize what is scheduled and verified versus what has actually executed. Disclose host/gateway availability requirements; a passing authentication probe is not end-to-end proof of the future report.

For finite evidence checkpoints, lag-aware cutoffs and the approved per-job model recipe, use `references/artifact-producing-cron-verification.md`.

## Scheduler Result and Delivery Verification

A scheduler-level `ok` proves that the run completed; it does not prove that useful work occurred. For ingestion, reconciliation, or artifact-producing jobs, inspect the exact run output plus the workflow's durable state/ledger and read back the claimed destinations. Understand the source lifecycle before using inbox contents as a failure signal: immutable standalone sources may intentionally remain visible after successful processing.

For the full four-layer proof, immutable-inbox interpretation, per-source-hash bounded projection pattern, and quiet delivery matrix, use `references/artifact-producing-cron-verification.md`.

When the user wants notifications only for material changes, update both halves of the contract:

1. set delivery to the explicitly requested chat/channel;
2. require the job to emit a concise changed-layer/destination summary only when it created or updated something, and otherwise return the scheduler's silent sentinel.

After editing, re-read the stored delivery target and prompt/no-op behavior. Changing only delivery causes noisy no-op alerts; changing only the prompt leaves useful results local or undelivered.

## Expiry / Takedown Reconciler Checks

For approved temporary publishing with scheduled removal:
- Journal a unique intent marker and desired artifact hashes **before** a remote deployment. On retry, recover only the exact marker; do not mistake a successful remote write followed by failed local readback for unrelated drift.
- An expired source file need not still exist or match its original hash to remove its hosted copy. Validate identity/approval/expiry first; read source bytes only for still-active artifacts.
- A command named `verify` must not publish, delete, adopt state, or save operational state. Report reconciliation due instead.
- Cleanup must reject additions, changed active content, and removals not backed by explicit expired entries. Scope historical deletion to recorded deployment IDs; verify old URLs as well as API inventory.
- Test interrupted remote success, missing expired sources, read-only verification, and quiet pre-expiry execution using fixtures. Disclose host-online dependency and that downloaded copies cannot be revoked.

## Scheduler Pitfalls

- Duration syntax can represent a one-shot rather than a recurring interval; verify the displayed schedule and next run.
- A previously successful cron run does not validate a newly edited script or prove that an artifact-producing run changed its target.
- Editing a script may require re-verifying its executable mode.
- For external cron scripts importing Hermes internals, reproduce the exact failing imports before assuming the Python interpreter is wrong. An editable install can expose existing packages while omitting newly added top-level modules (for example `hermes_yaml`), even with Hermes's own venv. Resolve the live launcher, then scope the verified venv PATH and Hermes source PYTHONPATH to that job's local shim; clear inherited PYTHONHOME rather than changing global Python or installing guessed packages. Exercise the real script with output redirected into scratch storage, verify manifest hashes and a deterministic rerun, then run the authorized cron and read back its actual destination.
- Manual live runs can create duplicate or false notifications; fixtures are the safer first proof.
- If a human advances an approved live-operation window and the mutation is performed manually, remove the still-future one-shot executor before acting, then reschedule only the read-only watchdog from the actual mutation time through the TTL horizon.
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
