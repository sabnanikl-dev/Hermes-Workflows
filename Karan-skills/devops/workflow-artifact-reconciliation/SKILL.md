---
name: workflow-artifact-reconciliation
description: "Use when reconciling workflow templates and exports."
version: 1.0.0
---

# Workflow Artifact Reconciliation

## Trigger

Use when an automation exists in several forms, such as:

- a canonical template or builder output;
- a sanitized repository export;
- a live n8n or comparable workflow instance;
- a downstream generated feed or website consumer.

This skill governs source-of-truth selection, bounded graph repairs, sanitization, repository handoff, and proof that downstream work is actually necessary.

## Core principle

> Fix the authoritative workflow behavior first, preserve the reviewed artifact's unrelated behavior, and do not broaden into downstream deployment unless the real consumption path requires it.

## 1. Reconstruct the artifact chain

Identify each copy and label it explicitly:

- **canonical build source** — intended editable template or generator;
- **reviewed repository artifact** — credential-free export under version control;
- **live runtime copy** — imported/active operational workflow;
- **downstream consumer** — CMS, API, generated static feed, or deployed UI.

Record hashes, node counts, active state, credentials shape, and relevant graph connections before editing. Do not assume the file named `template` is newer than the repository artifact.

## 2. Compare behavior before choosing a source

Compare more than JSON shape:

- node code and versions;
- connections and input indexes;
- policy constants and thresholds;
- deletion/archive guards;
- restore and convergence behavior;
- trigger/schedule state;
- settings, credential slots, and metadata.

If the template is behind the reviewed artifact, do not regenerate the reviewed artifact wholesale. Treat that as a source-of-truth conflict, not permission to discard shipped behavior.

## 3. Make the smallest deterministic repair

Isolate the intended transform, such as one node insertion plus exact connection rewiring. Apply it consistently only where the pre-transform seam is demonstrably equivalent.

For multi-branch source ingestion, synchronize branches before any run-once normalization or destructive reconciliation. See `references/mixed-source-fan-in.md`.

Do not change unrelated thresholds, guards, credentials, schedule behavior, or policy logic to make the workflow pass.

## 4. Prove the graph and the data flow

Use two layers:

1. **Structural contract** — exact node type/version/configuration, exact input indexes, exact output edge, and no bypass into reconciliation.
2. **Behavior contract** — credential-free fixtures for each source topology, executing the committed normalization/planning code where practical.

Minimum topology matrix for direct-plus-nested sources:

- direct only;
- nested only;
- mixed direct and nested;
- reversed branch append order.

The mixed case must prove one reconciliation pass sees the complete union exactly once. Include a former-red mutation of the old graph and require a categorized failure.

## 5. Preserve safety invariants

For workflows that can archive, delete, replace, or mutate many records:

- keep mass-mutation thresholds unchanged unless the issue explicitly owns them;
- prove a partial/empty source cannot reach mutation planning as a valid complete universe;
- prefer soft archive and convergence checks over hard deletion;
- preserve dry-run and inactive-by-default behavior;
- run one safe convergence readback after any separately approved live import.

A guard that aborts a partial-source run is working correctly. Fix the incomplete source fan-in; do not weaken the guard.

## 6. Sanitize the repository handoff

The repository-bound artifact must be:

- inactive;
- credential-free;
- stripped of execution data, ownership metadata, local paths, tokens, and environment values;
- validated offline;
- a fixed point of the sanitizer.

If canonical and reviewed copies have unrelated drift, apply the bounded transform to both only when safe, and log the broader drift separately. Do not hide source reconciliation inside a narrow operational fix.

## 7. Check downstream architecture before frontend work

After source-to-CMS reconciliation succeeds, inspect the website's actual data path:

- **Dynamic CMS/API consumer:** verify endpoint/content and stop. No site rebuild or deployment is needed.
- **Generated static feed is authoritative:** rebuild/deploy only with explicit authority.
- **Static file is only a fallback:** do not treat it as the primary update path.

A local feed comparison is verification, not deployment. State that clearly, and revert temporary generated changes when no handoff is needed.

## 8. Repository lifecycle

For a durable fix:

1. Create or use a scoped issue with frozen acceptance criteria.
2. Build in an isolated worktree or bounded build lane.
3. Commit only the sanitized artifact, deterministic validator/tests, and narrowly necessary docs.
4. Verify local HEAD = remote branch = PR head = final PR commit.
5. Use risk-proportional exact-head review.
6. Keep live import, schedule activation, deployment, and merge behind their own explicit authority gates.

## Pitfalls

- Editing only the live workflow and leaving the source artifact defective.
- Regenerating from a stale template and deleting newer reviewed behavior.
- Sending partition branches independently into a run-once normalization node.
- Testing only a handwritten simulator rather than the committed Code node.
- Adding a large validator without former-red mutations or proportionate scope review.
- Assuming a website deploy is necessary after a CMS sync without checking the real consumer path.
- Calling a local generated-file comparison a deployment or implying live mutation.

## Verification checklist

- [ ] Artifact roles and hashes recorded.
- [ ] Source-of-truth drift assessed.
- [ ] Minimal graph transform reviewed.
- [ ] Direct-only, nested-only, mixed, and order-independence cases pass.
- [ ] Former-red graph fails deterministically.
- [ ] Safety guards and thresholds unchanged.
- [ ] Sanitized artifact is inactive and credential-free.
- [ ] Sanitizer fixed point proved.
- [ ] Downstream dynamic/static path verified before rebuild/deploy.
- [ ] Repo/remote/PR exact-head equality verified.
- [ ] No merge, live import, activation, or deploy without explicit approval.
