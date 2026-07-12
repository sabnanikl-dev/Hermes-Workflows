# Initial Client Ontology Spec Session Notes

## Context

Karan researched agent ontologies and wanted to explore whether an ontology layer would level up client systems such as Femme Events and JMD Menswear.

The resulting work created an initial `client-ontologies` GitHub repo spec with:

- `README.md`
- `docs/spec.md`

The spec was intentionally **agent-agnostic** and **ontology-consumer agnostic**: useful for Hermes, other coding/research agents, apps, workflows, and future runtimes rather than only one assistant.

## Sources Consulted Pattern

The useful pattern was to gather context from multiple existing operating sources before drafting the ontology standard:

- Obsidian/Hermes Brain client notes:
  - client overview
  - brand guide
  - project-specific source-of-truth notes
- Local project docs:
  - README files
  - AGENTS files
  - implementation plans/specs
- GitHub repos:
  - active client websites
  - visibility/SEO repos
  - holding-page or harness repos
- Linear/PAPI/JMD issues:
  - active project requirements
  - historical decisions
  - blockers and planned work

Important: Linear/GitHub issue IDs and PR numbers are usually transient. Use them as sources/evidence, but avoid encoding them as durable ontology entities unless they represent a stable project artifact.

## Design Decisions That Worked

- Start with `docs/spec.md` before generating client YAML modules.
- Include starter Femme/JMD examples only as seeds, with source/confidence metadata.
- Define models for:
  - clients
  - modules
  - entities
  - relationships/triples
  - rules
  - approvals
  - evidence
  - projections
- Treat projections as first-class: different consumers need different slices of the ontology.
- Keep canonical storage as YAML/JSON under git; discuss SQLite/Postgres/Sanity/RDF as runtime/export options.
- Make validation part of the spec, including JSON Schema and simple deterministic validator sketches.

## Good Spec Sections

A complete ontology spec should include:

1. Purpose and non-goals.
2. Agent-agnostic principles.
3. Evidence/source requirements.
4. Canonical repo layout.
5. Client/module/projection file models.
6. Entity and relationship model.
7. Rule and approval model.
8. Runtime storage/export guidance.
9. Validation strategy.
10. Governance workflow.
11. Client starter seeds.
12. Open decisions and implementation phases.

## Verification Pattern

For repo-backed ontology/spec work, verify before reporting:

- Markdown code fences balanced.
- `git diff --check` or equivalent whitespace check passed.
- Basic secret-marker scan passed.
- Commit created.
- Remote commit/PR state verified after push.

## Next-Step Pattern

After the spec, recommended module implementation order was:

1. `clients/femme-events/client.yaml`
2. `clients/femme-events/modules/local-visibility.yaml`
3. `clients/femme-events/modules/website.yaml`
4. `clients/jmd-menswear/client.yaml`
5. `clients/jmd-menswear/modules/inventory-images.yaml`

This order starts with well-known, already-documented client context before moving into more operational or automation-heavy modules.
