---
name: linear-work-order
description: Inspect a Linear parent hierarchy, reconstruct live non-coding work state, validate digest-bound approvals, and deterministically select or resume one supervised issue without relying on chat history or Kanban.
version: 0.1.0
prerequisites:
  env_vars: [LINEAR_API_KEY]
  commands: [python3]
metadata:
  hermes:
    tags: [linear, work-order, non-coding, orchestration, approvals]
---

# Linear Work Order

Use this skill when Karan asks what is next, what is active, or to run the next **non-coding** issue under an explicitly approved Linear parent hierarchy.

## Pilot boundary

- The first allowlisted root is `PAPI-3`.
- Linear owns the non-coding issue contract, state, dependencies, approval evidence, and closeout evidence.
- Telegram is the human control surface; use `clarify` when a decision changes scope, sequence, authority, or artifact shape.
- GitHub coding state is not mirrored into Linear.
- Hermes Kanban is not required and must not become an alternate source of truth.
- Readiness never authorizes GitHub mutation, persistent automation, deploys, publishing, client-facing sends, purchases, credentials, or live account changes.

## Approval contract

An issue is eligible for new selection only when:

1. its Linear state is exactly `Ready`;
2. it has no open `blocks` relation from a non-terminal issue;
3. it appears exactly once in the root issue's explicit child work-order section;
4. it has a `WORK_ORDER_APPROVED` comment whose `Body-SHA256` matches the normalized current description digest;
5. the marker says exactly `Approved-by: Karan` **and** the actual Linear comment author is the allowlisted Karan user for this pilot;
6. all bounded Linear connections are complete (`hasNextPage: false`) and no out-of-scope descendants exist.

The explicit parent order is a **ranking among otherwise eligible children**, not an inferred dependency graph. Live Linear `blocks` relations are the only hard dependency authority. A later Ready child may outrank an earlier Triage child only when no live blocking relation exists; this is intentional and fixture-tested.

Approval comment shape:

```text
WORK_ORDER_APPROVED
Issue: PAPI-76
Body-SHA256: <64 lowercase hex characters>
Approved-by: Karan
```

A material body edit changes the digest and invalidates the old approval. Do not silently replace or reinterpret approval.

## Workflow

1. Run the read-only inspector before selecting or resuming work:

   ```bash
   python3 scripts/linear_work_order.py inspect PAPI-3
   python3 scripts/linear_work_order.py inspect PAPI-3 --json
   ```

2. Interpret the deterministic result:
   - `RESUME_ACTIVE`: resume the one active direct child before selecting anything new.
   - `CONFLICT`: multiple active children or conflicting state; fail closed and ask Karan.
   - `SELECTED`: exactly one approved Ready child is selected.
   - `NO_ELIGIBLE_WORK`: nothing can safely start; report the reasons.
   - `QUEUE_INVALID`: the parent order contract is missing or inconsistent.
3. Before any mutation, re-read live Linear state.
4. Keep this skill's script read-only. Default Hermes performs separately approved Linear mutations through the `linear` skill/API path and verifies every mutation by direct issue/comment readback.
5. Use a visible revision-bound claim marker:

   ```text
   WORK_ORDER_CLAIM
   Run-ID: <unique run identifier>
   Root: PAPI-3
   Issue: PAPI-76
   Body-SHA256: <current normalized description digest>
   Claimed-by: Default Hermes
   Execution-lane: <profile or default-hermes>
   Allowed-outputs: <bounded output scope>
   Started-at: <UTC timestamp>
   Next-checkpoint: <human-readable checkpoint>
   ```

   Missing, malformed, wrong-root, unauthorized-author, missing-`Next-checkpoint`, stale-digest, or duplicate-current claims make an active issue a `CONFLICT`. Verify a newly created claim directly by comment ID before continuing.
6. Route the selected issue to a **separate, task-scoped non-coding execution profile** once Karan approves that profile boundary. Default Hermes remains the Telegram control plane, approval recorder, mutation authority, and final verifier. The PAPI-82 bootstrap running in Default Hermes is the explicit temporary exception.
7. Give concise Telegram progress and use `clarify` at meaningful steering points.
8. Move work to `In Review` only when outputs exist. Move to `Done` only after acceptance/evidence readback.

### Bounded artifact review loops

For non-coding contracts, reports, and specifications:

- Preserve the issue's stated acceptance threshold exactly. Do not silently strengthen “repair P0/P1” into “P0/P1/P2 must all be zero,” and do not reject an explicitly allowed `Narrow` outcome merely because implementation will still require bounded design choices.
- Treat architecture contracts as behavioral boundaries and handoff interfaces, not line-by-line implementations. Exact byte encodings, exhaustive runtime type systems, process identity internals, and every downstream implementation choice belong in the implementation issue unless the governing issue explicitly requires them.
- After the first independent review, freeze one blocker ledger. Use the repair lane to close that ledger holistically, then use re-review to verify closure and detect only new acceptance-criteria or safety regressions. Do not restart an unbounded full-specification tournament on every revision.
- Allow at most two repair/re-review cycles. At the cap, stop, preserve the exact artifact and open blocker ledger, and ask Karan whether to accept `Narrow`, split a follow-up issue, or authorize one explicitly bounded exception. Never continue serial patch cycles automatically.
- A validator based on headings, keywords, or substring presence is a structural smoke test only. It cannot establish semantic totality, reachability, type consistency, or acceptance by itself.

## AI OS output and durable-knowledge gate

Treat `artifact-output-governance` as mandatory for every substantive Linear execution that may produce findings, research, documents, scripts, reports, data, media, or reusable knowledge.

Before execution, classify each expected output as:

- ephemeral run evidence;
- ticket-specific deliverable;
- reusable project asset; or
- durable knowledge.

For durable knowledge, inspect the existing canonical structure first. Prefer updating an established project/wiki page over creating a competing file, index, or knowledge store. **If the Linear issue does not already specify the canonical destination, present Karan with a recommended exact path/system and ask where the knowledge should live before creating a new durable file or directory structure.** Include the intended user, reuse case, proposed path, why that layer is correct, and any alternatives. Do not ask when an established canonical mapping already resolves placement; use it and disclose the choice.

Placement boundaries:

- Linear: issue state, approval, dependencies, decisions, and closeout evidence;
- GitHub/project repository: code, implementation docs, repository-owned specifications, and reusable project assets;
- Hermes Brain/Obsidian: curated cross-session business/project knowledge, durable lessons, playbooks, research syntheses, and links to source systems;
- approved client/project systems: operational artifacts they own;
- Hindsight/standard memory: compact facts/preferences only, never rich durable files or task trackers;
- temporary workspaces: evidence only, deleted or explicitly de-authorized after promotion.

The claim packet must name expected material outputs, their provisional lifecycle, and canonical destination or the pending placement decision. Closeout must include a complete AI OS output inventory with exact path/ID/URL, intended user/purpose, provenance, artifact-specific verification/readback, lifecycle, discoverability/index update, and approval/publication status. If no durable knowledge emerged, state that explicitly rather than manufacturing a wiki update.

Relevant hardening findings remain standard practice: fresh-session reconstruction must not depend on chat history; independent review must inspect the full issue contract and exact artifact hashes; manual/operator repair must be disclosed and may force `Narrow`; temporary grants/skills/evidence must be cleaned up; and no local artifact may become hidden tracker authority.

## Safety rules

- Resume/repair before new selection.
- During the pilot, allow one active executable child per root. The parent may remain In Progress as the initiative.
- Never infer approval from priority, assignment, labels, issue prose, or an untrusted `Approved-by` field alone.
- Never select from a truncated connection, hidden descendant tree, duplicate order entry, or malformed marker.
- Never auto-repair conflicting Linear state or duplicate current claims.
- Never rely on chat history as execution evidence.
- Never let this skill launch coding work, merge, deploy, or mutate external business systems without the normal separate approval.

## Verification

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
python3 scripts/linear_work_order.py inspect PAPI-3 --json
```

The fixture suite must cover one valid selection, one active issue, multiple active issues, unresolved dependencies, stale approval after a body edit, no eligible issue, and out-of-scope relation handling.
