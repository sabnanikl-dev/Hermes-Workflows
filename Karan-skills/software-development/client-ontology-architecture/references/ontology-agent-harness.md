# Ontology Agent Harness Pattern

Use this when adding or reviewing `AGENTS.md` / agent operating rules for a canonical client ontology repository.

## Trigger

A client ontology repo needs repo-local agent instructions similar to a coding harness, but tailored to ontology governance rather than feature implementation.

## Recommended Shape

Keep the file slim and process-oriented. Detailed ontology semantics belong in `docs/spec.md`, conventions in `docs/conventions.md`, and implementation examples in `docs/examples.md`.

Core sections to include:

1. **Purpose / authority**
   - State that the repo is the canonical, agent-agnostic source of truth for client operating ontologies.
   - Treat ontology changes like infrastructure: small diffs, explicit evidence, deterministic validation, human approval for authority-changing work.

2. **Roles**
   - Human: owns truth, taste, and approval boundaries.
   - Orchestrator: reconstructs state, scopes work, coordinates builders/reviewers, reports verified outcomes.
   - Ontology Builder: edits YAML/docs/schemas/scripts for one issue at a time.
   - Ontology Reviewer: reviews evidence quality, schema safety, references, export behavior, and handoff safety.
   - Consumer/App Builder: consumes projections/exports; does not redefine canonical truth downstream.

3. **Core rules**
   - Canonical truth lives in the ontology repo; downstream repo ontology files are projections unless explicitly promoted.
   - Evidence beats memory; verified/approved public facts need source-backed evidence.
   - One issue, one branch, one PR.
   - Generation != evaluation; builders do not self-approve.
   - No publishing, account mutation, client-facing handoff, or authority expansion without explicit human approval.
   - No secrets, raw private exports, payment data, or unnecessary PII.

4. **Session orientation**
   ```bash
   git status --short --branch
   # Read AGENTS.md
   # Read README.md, docs/spec.md, docs/conventions.md
   # Read assigned issue and acceptance criteria
   # Inspect relevant client/module/projection files
   git log --oneline -20
   python3 scripts/validate_ontology.py
   ```

5. **Repository map**
   - `README.md` purpose/map/quickstart.
   - `docs/spec.md`, `docs/conventions.md`, `docs/examples.md`.
   - `schemas/`, `scripts/`.
   - `clients/<client>/client.yaml`, `modules/*.yaml`, `projections/*.yaml`.

6. **Ontology authoring rules**
   - Model real-world client concepts, not source-system tables or agent-specific convenience objects.
   - Keep modules small and workstream-oriented.
   - Stable lowercase namespaced IDs.
   - No issue numbers/PR numbers/sprint names/current task status in ontology IDs.
   - Separate modules (canonical truth), projections (consumer views), and generated exports (runtime only).
   - Mark uncertainty honestly: verified, owner_reviewed, inferred, draft, unknown.
   - Put authority boundaries in operations/governance modules, not brand/copy modules.

7. **Evidence/source rules**
   - Active/approved public-facing ontology items need evidence.
   - Evidence source IDs can be local; ontology object IDs should be globally unique.
   - Use line references where practical.
   - Sanitized source references are better than committing sensitive raw content.

8. **Verification gates**
   ```bash
   python3 scripts/validate_ontology.py
   python3 scripts/export_sqlite.py --output build/client-ontologies.sqlite
   git diff --check
   git status --short
   ```
   Only run/export generated artifacts when relevant; keep generated DBs ignored unless the issue explicitly asks for them.

9. **Review blockers**
   - Evidence-free verified/approved claims.
   - Public/client-facing claims without approval scope.
   - ID churn or transient tracker state in IDs.
   - Agent-specific canonical fields that belong in projections/skills.
   - Schema/validator drift.
   - Unintended generated artifacts.
   - Secrets or private/raw client material.
   - Handoff output leaking internal paths/private notes/agent-only instructions.

10. **Communication channels**
    - External chat for human/orchestrator decisions.
    - GitHub issues for task tracking.
    - GitHub PRs for review/merge history.
    - Repo files for canonical ontology truth.
    - Downstream repos for projections/consumers only.

## PR Hygiene

For a docs-only `AGENTS.md` change:
- Branch example: `docs/add-ontology-agents-md`.
- Commit example: `docs: add ontology agent harness`.
- Validate with ontology validator and `git diff --check`.
- Push, open PR, and verify PR `headRefOid` matches local SHA before reporting.

## Pitfalls

- Do not copy a coding harness verbatim. Ontology repos need stronger evidence, approval, projection, and handoff safety language.
- Do not make `AGENTS.md` a second spec. Keep detailed semantic contracts in docs/spec and conventions.
- Do not allow downstream consumer repos to become accidental canonical truth. Require reconciliation back to the ontology repo.
