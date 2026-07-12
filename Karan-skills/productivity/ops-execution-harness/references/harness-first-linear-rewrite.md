# Harness-First Linear Rewrite Pattern

Use when an existing ops Linear issue is too broad or still reads like a loose checklist, but the user wants execution through the Papi ops execution harness.

## Rewrite Shape

Update the issue so the first deliverable is a cloned, populated harness. The actual ops work then runs inside that workspace.

Include these fields in the Linear description:

- Context: client, issue purpose, current access/status, safety notes.
- Goal: clone/populate harness, then execute task deliverables.
- Source template: `sabnanikl-dev/papi-ops-execution-harness-template`.
- Target workspace: client-specific path, e.g. `/Users/creator/projects/consultancy/<Client>/ops-harnesses/<issue-key>-<slug>`.
- Harness setup tasks:
  - clone template
  - populate `task.md`
  - populate `context.md`
  - populate `constraints.md`
  - populate `playbook.md`
  - populate `skills/manifest.md`
  - confirm `evidence/` and `outputs/`
- Execution plan after harness setup.
- Output requirements with exact paths inside the harness.
- Approval gates.
- Acceptance criteria.
- Verification.
- Definition of done.

## Acceptance Criteria Checklist

- [ ] Template repo cloned into target workspace.
- [ ] `task.md`, `context.md`, `constraints.md`, `playbook.md`, and `skills/manifest.md` populated.
- [ ] `evidence/` and `outputs/` exist.
- [ ] Approval mode explicit.
- [ ] No live/client-facing changes without approval.
- [ ] Final output path explicit.
- [ ] Final Linear comment draft saved in outputs.

## JMD-2 Example

JMD-2 was rewritten from a GBP audit checklist into:

- title: `Clone ops execution harness for GBP audit and quick-fix plan`
- source template: `sabnanikl-dev/papi-ops-execution-harness-template`
- target workspace: `/Users/creator/projects/consultancy/JMD-Menswear/ops-harnesses/jmd-2-gbp-audit`
- final output: `outputs/gbp-audit.md`

The GBP API/no-API audit logic remained, but became the execution plan after harness setup.
