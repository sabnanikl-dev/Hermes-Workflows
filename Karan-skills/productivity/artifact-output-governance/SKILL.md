---
name: artifact-output-governance
description: Govern agent-produced findings, documents, images, spreadsheets, presentations, scripts, datasets, reports, and external artifacts from purpose through canonical storage, verification, handoff, and durable promotion.
version: 1.1.1
author: Hermes Agent
metadata:
  hermes:
    tags: [artifacts, outputs, ai-os, linear, verification, provenance, handoff]
    related_skills: [linear-issue-specs, ops-execution-harness, knowledge-memory-workflows]
---

# Artifact and Output Governance

## Purpose

Use this skill whenever agent execution produces a material output: findings, research, documents, images, diagrams, spreadsheets, presentations, scripts, plans, reports, datasets, media, or an artifact written to an external system.

This is a class-level delivery standard. It applies whether the work originates in Linear, GitHub, a project harness, Telegram, or a delegated profile. It complements tracker/execution skills by governing **what happens to the output** after and during creation.

The governing AI OS principle is:

> An output is not complete because an agent generated it. It is complete when it serves a named user, lives in the right canonical system, preserves provenance, has been exercised in its real form, survives fresh-session handoff, and passes independent acceptance.

## Trigger conditions

Load this skill when:

- a Linear or GitHub issue names one or more deliverables;
- execution will produce files, findings, media, data, reports, or external objects;
- an agent needs to decide where an output belongs;
- closeout must prove that outputs are usable and discoverable;
- temporary work may need promotion into GitHub, an approved project system, or Hermes Brain/Obsidian;
- NotebookLM/AI OS guidance must be converted into durable delivery rules.

Skip only when the task genuinely produces no material output beyond a short conversational answer.

## Mandatory output contract

Every material output must:

1. **Serve a named user and purpose.** State who will use it, which decision/action it supports, and what usable completion means.
2. **Use the right artifact form.** Choose Markdown, document, image, spreadsheet, presentation, script, dataset, or another medium based on the work. Do not force non-text outputs into Markdown.
3. **Land in the canonical source of truth.** Linear owns issue state, approval, dependencies, and closeout evidence; GitHub owns code/PR truth; Hermes Brain/Obsidian owns conservatively promoted durable knowledge; approved project/client systems own operational artifacts. Chat and temporary run folders are never final authority.
4. **Preserve provenance and limits.** Identify sources, evidence, assumptions, confidence, limitations, and relevant timestamps/versions. Unsupported inference must not become a business fact.
5. **Receive independent acceptance.** The executor may self-check, but final acceptance requires a separate skeptical review against acceptance criteria, intended-user usefulness, factual grounding, and artifact quality.
6. **Be exercised and read back.** Verification must match the artifact type; file existence alone is insufficient.
7. **Remain discoverable.** Link every final artifact from its tracker/control surface by exact path, ID, or URL. Update an existing project index/map for major durable outputs when one exists; do not create a competing index merely for process compliance.
8. **Declare a lifecycle.** Classify the output as ephemeral evidence, ticket-specific deliverable, reusable project asset, or durable knowledge.
9. **Support fresh-session handoff.** A new executor/reviewer must understand purpose, source, status, verification, owner, and next action from the tracker and canonical links without chat history.
10. **Respect privacy and authority.** Redact secrets and unnecessary PII. Public/client-facing publication, sends, uploads, and live account changes require approval for the exact action and artifact version.

## Source-of-truth routing

| Output class | Canonical owner | Required closeout evidence |
| --- | --- | --- |
| Issue state, approval, dependency, decision | Linear/GitHub tracker as applicable | Direct issue/comment/relation readback |
| Code, tests, technical implementation | GitHub/repository | Commit/PR/check URL and exact revision |
| Durable reusable business/project knowledge | Hermes Brain/Obsidian or approved wiki | Exact note path plus readback/search evidence |
| Operational/client artifact | Approved project/client system | Object ID/URL, version, owner, direct readback |
| Temporary run evidence | Bounded workspace until summarized | Redacted result promoted to tracker; temporary artifact deleted or de-authorized |

Do not duplicate the same authority across systems. A tracker comment may link canonical evidence without replacing its owner.

## Workflow

### 1. Define the output before execution

For each expected deliverable, record:

- intended user;
- decision/action supported;
- artifact type;
- canonical destination;
- provenance requirements;
- approval/publication mode;
- verification/readback method;
- lifecycle classification.

If these are unclear and materially change the work, stop and route a bounded clarification rather than generating a generic artifact.

#### Durable-knowledge placement checkpoint

When an output is classified as durable knowledge:

1. search the existing repository/wiki/client-system structure and indexes first;
2. identify the named future user and repeated reuse case;
3. choose the canonical owner by source-of-truth boundary, not convenience;
4. prefer updating an existing page or project document over creating a parallel note/index;
5. if the canonical destination is not already explicit, recommend an exact path/system and ask Karan to confirm placement before creating a new durable file, folder, index, ontology, or knowledge-store boundary;
6. make the question decision-ready: include the recommended location, why it fits, up to three meaningful alternatives, and the consequence of each;
7. after approval/placement, update the existing index/map when appropriate and verify both the artifact and its discoverability by readback/search.

Default routing guidance:

- repository-owned technical/product knowledge → the project repository;
- curated cross-session business/project knowledge, lessons, playbooks, and source-backed syntheses → Hermes Brain/Obsidian;
- live issue state and decisions → Linear;
- client operational truth → the approved client system;
- personal operating knowledge → Karan OS, never duplicated into Hermes Brain;
- procedures the agent should repeatedly execute → a skill, not only a wiki note;
- compact stable preferences/facts → memory/Hindsight, not a rich file.

Do not turn the placement question into ceremony when an established canonical mapping already answers it; use the mapping and disclose it. Do not create durable knowledge merely to check a box—`Durable knowledge: none` is a valid closeout result when supported.

### 2. Produce in the appropriate medium

Use the medium that best supports the user and task. Portable/editable formats are preferred when useful, but output shape follows purpose—not process convenience.

### 3. Verify in the artifact's real form

- Documents/PDFs: open/render, inspect layout and key text, confirm metadata/version.
- Images/diagrams: visually inspect, confirm dimensions/format, legibility, and intended placement.
- Spreadsheets: open workbook, inspect formulas/types/sheets, validate representative calculations and exports.
- Presentations: render slides, inspect overflow/order/visual hierarchy, verify citations.
- Scripts/CLIs: execute with safe fixtures, test failure paths, verify exit codes and resulting state.
- Datasets/reports: validate schema, counts, deduplication, provenance, and known edge cases.
- External writes: capture object ID and directly read back exact content/state/version.

### 4. Run independent acceptance

A separate reviewer evaluates:

- acceptance-criteria coverage;
- intended-user usefulness;
- factual/source fidelity;
- artifact-specific quality;
- canonical placement and discoverability;
- safety, privacy, and approval boundaries.

Do not require a brittle role name such as `QAS`; independent skeptical review is the invariant.

### 4.1 Preserve the acceptance threshold and bound review convergence

Independent acceptance must judge the artifact against the governing issue—not an accidentally stricter rubric invented by the operator or reviewer.

- Record which severities are blocking before review starts. If the issue says P0/P1 block, P2 remains advisory unless it directly violates an acceptance criterion, safety boundary, or intended-user usability requirement.
- Preserve explicit `Continue / Narrow / Stop` outcomes. `Narrow` is a valid accepted result when the artifact is safe and useful but bounded implementation or repository-specific decisions remain.
- For architecture contracts, review behavioral invariants, interfaces, ownership, failure behavior, and authority boundaries. Do not demand implementation-total details such as exact byte encodings, exhaustive runtime type systems, or internal identity algorithms unless the issue explicitly requires them.
- After the first broad review, freeze one blocker ledger. Repair that ledger holistically; re-review verifies closure and checks for new acceptance-criteria or safety regressions rather than reopening an unlimited critique tournament.
- Default maximum: two repair/re-review cycles. At the cap, stop and present the exact artifact, remaining ledger, and a decision: accept `Narrow`, split follow-up work, or authorize one explicitly bounded exception.
- Structural validators based on headings, keywords, or substring presence are smoke tests only and must never be presented as semantic acceptance.

For the reusable contract card, abstraction/size budget, exact-hash reviewer packet, frozen-ledger protocol, same-hash promotion, and superseded-artifact authority marker, use `references/bounded-architecture-contract-review.md`.

### 5. Close out with an output inventory

For every material output record:

| Output | Intended user / decision | Artifact type | Canonical path, ID, or URL | Provenance | Verification/readback | Lifecycle | Approval/publication status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<name>` | `<who / why>` | `<type>` | `<exact locator>` | `<sources/version>` | `<real check>` | `ephemeral / ticket / reusable / durable` | `<private / approval needed / approved version>` |

Closeout is incomplete when a material output:

- is absent from the inventory;
- exists only in chat or a temporary folder;
- lacks provenance;
- has not been exercised in its real form;
- cannot be found by a fresh reviewer;
- is public/client-facing without exact-version approval.

### 6. Promote conservatively

- Promote durable, reusable, source-backed knowledge—not raw transcripts, transient metrics, temporary task state, or every intermediate artifact.
- Link the canonical artifact instead of copying it into several stores.
- If no durable knowledge emerged, state that instead of manufacturing a wiki update.
- Remove or clearly de-authorize temporary artifacts after their redacted evidence is captured.

## Notebook/AI OS distillation guardrail

Treat NotebookLM output as grounded input, not literal issue prose. Query the notebook when current grounding is requested, then encode durable guidance directly so future executors do not need notebook access.

Reject brittle prescriptions that do not fit live state, including:

- forcing every output into `.md`;
- requiring a named reviewer role when independent review is the invariant;
- creating a new central index when an existing canonical map already exists;
- promoting every ticket-specific finding into Obsidian;
- treating research guidance as authorization for public/live action.

For portable AIOS/control-plane architecture, apply the **Sovereign Rig** interpretation: the owner-controlled body is the plans, contracts, registries, templates, authority envelopes, recovery instructions, and verification; models are replaceable execution adapters. Portability does not require physically relocating every canonical artifact beneath one root. Prefer stable logical IDs plus ignored machine-local path resolution, preserve GitHub/Linear/repository/Hermes Brain/Karan OS authority boundaries, treat worktrees and caches as disposable, and require an exercised recovery drill rather than documentation-only portability claims.

Distill the invariant, preserve source-of-truth and authority boundaries, and make compliance observable in acceptance criteria.

## Linear issue integration

For decision-only Linear issues whose downstream implementation is separately owned—especially when a planned destination is canceled—follow `references/decision-issue-closeout-and-retirement.md`. It covers explicit retirement semantics, literal source-inventory census, downstream-tracker parity, exact-head verification, bounded independent re-review, wiki promotion, helper CLI syntax, and direct state/comment readback.

For an output-producing Linear issue, add acceptance criteria that prove:

- every material artifact appears in the output inventory;
- no accepted artifact exists only in chat or a temporary run folder;
- exact paths/IDs/URLs and artifact-specific readbacks are present;
- provenance and lifecycle classification are explicit;
- a fresh reviewer can locate, understand, exercise, and judge the output without session history;
- publication/live-action status is explicit.

Linear owns the contract and closeout evidence, not the artifact itself when another canonical system owns it.

## References

- See `references/ai-os-output-contract.md` for the condensed AI OS source themes, artifact verification matrix, promotion rules, and issue-insertion checklist.
- See `references/sovereign-rig-portable-control-plane.md` when designing AIOS/filesystem portability, replaceable model adapters, canonical-system registries, worktree-safe migration, and exercised new-computer recovery.
- See `references/immutable-evidence-corrections.md` when correcting a semantic overstatement in a content-addressed bundle: preserve history, publish a new canonical manifest, explicitly supersede old hashes, rerun independent review, and verify tracker corrections by direct ID.

## Common pitfalls

- Treating generation as completion.
- Saving everything as Markdown regardless of purpose.
- Leaving the only usable result in chat.
- Putting code truth in Linear or tracker truth in a local file.
- Accepting an output because its creator self-reported success.
- Verifying only file existence rather than rendering/executing/reading back.
- Editing an immutable/hash-addressed artifact in place or reusing a review bound to superseded bytes.
- Correcting a claim without explicitly marking the old manifest/review as non-canonical for future decisions.
- Creating duplicate indexes or knowledge stores.
- Promoting transient task state into durable memory.
- Omitting provenance, limitations, or version context.
- Publishing or sending an artifact without exact-version approval.

## Verification checklist

- [ ] Intended user, decision, and usable outcome are named.
- [ ] Artifact form matches the work.
- [ ] Canonical destination is correct and non-duplicative.
- [ ] Any new durable knowledge structure had a decision-ready placement recommendation and Karan confirmation; established mappings were used without unnecessary ceremony.
- [ ] Durable knowledge is reusable/source-backed, or closeout explicitly states that none emerged.
- [ ] Provenance, assumptions, limitations, and version are recorded.
- [ ] Artifact was exercised in its real form.
- [ ] Independent acceptance passed.
- [ ] Exact canonical path/ID/URL is linked from the control surface.
- [ ] Lifecycle classification is explicit.
- [ ] Fresh-session handoff is sufficient.
- [ ] Privacy and exact-version approval boundaries are preserved.
- [ ] Output inventory is complete.
- [ ] Temporary artifacts are deleted or de-authorized after evidence capture.
