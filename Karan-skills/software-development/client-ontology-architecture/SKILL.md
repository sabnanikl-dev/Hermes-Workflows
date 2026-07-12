---
name: client-ontology-architecture
description: Design and implement client operating ontology layers for businesses/projects, with evidence-backed entities, relationships, rules, projections, validation, and agent-agnostic runtime exports.
---
# Client Ontology Architecture

## When to Use

Use this skill when Karan asks to design, review, build, or extend an ontology layer for a client or operating system, especially for:

- Femme Events, JMD Menswear, Papi AI, or similar client knowledge systems.
- Turning scattered wiki/project/Linear/GitHub context into a structured client ontology.
- Defining canonical entities, relationships, operating rules, approvals, evidence, and projections.
- Creating an ontology repo/spec that multiple agents, apps, automations, or dashboards can consume.
- Moving from prose knowledge docs to machine-readable YAML/JSON/SQLite/Postgres/RDF-style knowledge layers.

## Core Principle

A client ontology is not just a knowledge base. It is a **governed operating model** for a client: what exists, how it relates, what rules constrain work, what evidence supports each fact, and which projections different tools/agents should consume.

Design it to be:

- **Agent-agnostic:** usable by Hermes, Codex, Claude, browser automations, web apps, n8n workflows, and future tools.
- **Consumer-agnostic:** canonical source should not be locked to a single runtime, CMS, vector DB, or graph engine.
- **Evidence-backed:** durable facts must point to source material or a human confirmation state.
- **Approval-aware:** rules should encode when an agent may act, draft, ask, or block.
- **Diffable and reviewable:** default canonical files should be plain text under git.

## Recommended Canonical Shape

Prefer a repo shape like:

```text
client-ontologies/
  README.md
  docs/
    spec.md
  schemas/
    ontology.schema.json
  clients/
    <client-slug>/
      client.yaml
      modules/
        brand.yaml
        website.yaml
        local-visibility.yaml
        operations.yaml
      projections/
        agent-context.yaml
        website-build.yaml
        crm-sync.yaml
```

Canonical source should usually be YAML or JSON first. Add generated exports only after the canonical model is stable.

## Required Model Concepts

### 1. Entity

Every durable thing should have a stable ID and enough metadata to be trusted.

```yaml
id: femme-events.brand.voice
kind: brand_voice
label: Femme Events brand voice
status: active
source_confidence: verified
sources:
  - type: obsidian
    path: "branding/Femme Events Brand Guide.md"
fields:
  adjectives:
    - stylish
    - personal
    - trend-forward
    - non-traditional
```

### 2. Relationship / Triple

Represent important connections explicitly, not only inside prose.

```yaml
subject: femme-events.website
predicate: uses_brand_voice
object: femme-events.brand.voice
confidence: verified
sources:
  - type: github
    repo: sabnanikl-dev/Femme-Events-Website
```

### 3. Rule

Rules should state scope, severity, approval behavior, and evidence.

```yaml
id: femme-events.rules.no-unapproved-client-facing-send
scope:
  clients: [femme-events]
severity: blocking
condition: "agent_action.kind in ['email_send', 'social_post', 'external_message']"
requirement: "draft_only_until_human_approval"
evidence:
  - type: user_preference
    note: "Security-first; approval always for client-facing actions."
```

### 4. Projection

A projection is a curated view for a particular consumer. Do not make every agent parse the entire ontology if it only needs rules or brand context.

```yaml
id: femme-events.projections.website-build
consumer: website_builder_agent
includes:
  entities:
    - femme-events.brand.*
    - femme-events.services.*
  rules:
    - femme-events.rules.*
outputs:
  format: markdown_context
  max_tokens: 6000
```

## Workflow

### 0. Confirm Canonical vs Projection Location

Before writing or updating ontology files, confirm where canonical truth lives for this client/system.

For Karan's current PAPI/Femme/JMD operating ontology work, the canonical repo is:

```text
sabnanikl-dev/client-ontologies
```

Use repo-local ontology files only as projections, handoff views, or implementation context unless the user explicitly changes the source-of-truth decision. Typical canonical paths are:

```text
client-ontologies/
  clients/<client-slug>/
    client.yaml
    modules/*.yaml
    projections/*.yaml
    handoff/*.md   # only when client handoff is required
```

Typical repo-local projection paths are:

```text
<working-repo>/docs/ontology/*.yaml
<working-repo>/ontology/*.yaml
<working-repo>/.hermes/ontology-context.md
```

If a repo-local projection changes, treat it as a proposed delta — not canonical truth. Reconcile it back to the canonical repo by classifying the change as verified fact, inferred fact needing review, changed rule, projection-only formatting/context, or stale/incorrect projection drift. Update canonical YAML only when the fact/rule belongs there, then regenerate or patch projections from canonical.

### 1. Gather Existing Context First

Before inventing the ontology, inspect trusted sources that already exist:

- Hermes Brain / Obsidian notes for client overview, brand guide, lessons, and operating decisions.
- Local project docs such as README, AGENTS, specs, or implementation plans.
- GitHub repos for current file structure, branches, and committed context.
- Linear/PAPI/JMD issues for active work, but do not encode transient issue numbers as durable ontology facts unless they represent a stable project or requirement.
- User-provided article/research material, especially if the user is exploring an ontology pattern.

### 2. Separate Verified Facts from Draft Assumptions

For each proposed entity/rule, mark one of:

- `verified`: backed by source or explicit user confirmation.
- `inferred`: reasonable synthesis from multiple sources, needs review.
- `draft`: proposed design, not yet a client fact.
- `deprecated`: retained for history but not active.

Do not smuggle guesses into the ontology as verified truth.

### 3. Start with the Spec Before Module Explosion

For a new ontology repo or client layer, create the standard first:

1. `README.md` — purpose, status, quickstart, repo map.
2. `docs/spec.md` — concepts, schema, governance, examples, validation strategy.
3. Starter client/module examples only if clearly marked as draft or verified.
4. Validation scripts/schema after the shape is agreed.

This avoids a pile of inconsistent YAML modules.

### 4. Keep Runtime Options Secondary

Recommended progression:

1. YAML/JSON canonical files under git.
2. JSON Schema + deterministic validator.
3. SQLite export for local agent runtime and quick joins.
4. Postgres/graph/RDF exports only when query volume or integration needs justify it.
5. Sanity/CMS relationships only for editorial/content surfaces, not as the canonical operating ontology unless chosen deliberately.

### 5. Verify Like a Repo Change

Before reporting completion:

- Run whitespace/diff checks where possible.
- Run the ontology validator and a direct YAML syntax pass over every client/module/projection file.
- If validation tooling compiles Python scripts, ignore or remove `__pycache__/` before committing.
- Generate runtime exports only after canonical YAML validates; keep generated SQLite/build outputs ignored unless the user explicitly asks to commit them.
- Scan for accidental secrets or private raw content.
- Commit changes on a named branch or directly only when appropriate.
- If the user asked for a commit but not a push, stop after local commit and report the branch-ahead state; pushing is an external repo mutation requiring explicit approval.
- After pushing, verify the remote commit/PR state before claiming success.

## Validation Implementation Notes

- Treat canonical YAML validation as a deterministic repo hygiene layer, not just JSON Schema validation. Check parse success, required fields, namespaced stable IDs, duplicate ontology object IDs, practical references, evidence/source references, and obvious secret patterns.
- Evidence source IDs should be local to their file's `source_registry` / `evidence_sources`. It is normal and useful for multiple modules to reuse a source ID such as `femme-local-seo-sot`; do not reject those as global duplicates. Reserve global duplicate checks for ontology object IDs such as clients, modules, entities, relationships, rules, projections, claims, approval gates, and state machines.
- If Python YAML libraries are unavailable, Ruby stdlib YAML can be used as a dependency-light parser from Python subprocesses. Prefer broadly compatible calls such as `YAML.load_file(ARGV[0])`; avoid newer Psych keyword arguments unless verified on the host.

## Pitfalls

- **Ontology sprawl:** one YAML file per idea becomes unusable. Create a spec and module boundaries first.
- **Harness bloat:** repo `AGENTS.md` files should stay slim and operational. If asked to compress one, preserve the load-bearing rules (canonical truth, evidence, stewardship/docs-in-PR, human approval, validation, PR verification) and move detail to `docs/spec.md`, `docs/conventions.md`, examples, or references rather than duplicating the full ontology spec.
- **Docs drift during issue work:** agents are ontology stewards. When issue work changes ontology concepts, module boundaries, schema expectations, validator/export behavior, or consumer semantics, the same PR should update the relevant docs (`docs/spec.md`, `docs/conventions.md`, and/or `docs/examples.md`) or explicitly state why no doc change was needed.
- **Product/SaaS namespace drift:** keep schema IDs, ontology namespaces, RDF prefixes, and docs neutral unless Karan explicitly asks to brand the system. PAPI/Linear issue IDs may remain as evidence/history, but `papi.ai` schema URLs or language like “future hosted Papi systems” incorrectly imply a SaaS/platform direction. Future UI interaction is desired, but the UI should be described as a consumer/interface over canonical repo YAML, not the source of truth or a SaaS commitment.
- **Agent lock-in:** avoid fields that only make sense for Hermes unless the module is explicitly a Hermes projection.
- **Evidence-free facts:** if the source is not known, mark it draft/inferred.
- **Encoding temporary tracker state:** issue IDs, PR numbers, and sprint status usually belong in Linear/GitHub, not the ontology.
- **Mixing brand voice with operational authority:** a brand ontology can guide copy; an authority/rules ontology controls what agents may do.
- **Overbuilding graph tech too early:** RDF/OWL/vector/graph DBs are exports or runtimes, not the first source of truth.

## Support Files

- `references/initial-client-ontology-spec-session.md` — session-derived notes from the first client ontology repo/spec build for Femme Events and JMD Menswear.
- `references/linear-ontology-issue-alignment.md` — pattern for updating a whole Linear issue set when ontology source-of-truth paths or projection semantics change.
- `references/v01-femme-jmd-implementation-pattern.md` — implementation pattern from building the first usable v0.1 Femme/JMD ontology system, including validator/export design, source-ID locality, dependency-free YAML parsing fallback, and verification checklist.
- `references/palantir-ontology-cross-reference.md` — condensed Palantir Foundry Ontology research mapped to `sabnanikl-dev/client-ontologies` improvements: manifests, schema/CI, actions/functions, interfaces, cleanup, semantic search/OAG, projection provenance, approvals, state machines, machine-checkable rules, and handoff generation.
- `references/ontology-agent-harness.md` — pattern for adding an ontology-tailored `AGENTS.md` harness: roles, canonical-truth rules, evidence/source requirements, projection boundaries, approval gates, validation commands, review blockers, and PR hygiene.
- `references/neutral-ontology-branding-and-ui-direction.md` — guidance for removing accidental Papi/SaaS branding while preserving Karan's desired future UI interaction model over canonical YAML.
