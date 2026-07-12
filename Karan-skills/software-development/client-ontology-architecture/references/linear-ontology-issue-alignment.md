# Linear ontology issue alignment pattern

Use this reference when ontology architecture changes and existing Linear issues still point at stale source-of-truth paths or workflows.

## Durable lesson

When the canonical ontology location changes, update the whole related issue set in Linear — not just the issue currently being discussed. Otherwise future agents may execute stale paths from sibling/child issues.

## Current PAPI/Femme/JMD ontology direction

Canonical ontology repo:

```text
https://github.com/sabnanikl-dev/client-ontologies
```

Current foundation:

```text
README.md
docs/spec.md
```

Canonical client paths should follow:

```text
clients/femme-events/
  client.yaml
  modules/
    brand.yaml
    website.yaml
    local-visibility.yaml
    operations.yaml
  projections/
    agent-context.yaml
    website-build.yaml
    local-seo.yaml

clients/jmd-menswear/
  client.yaml
  modules/
    brand.yaml
    website.yaml
    inventory-images.yaml
    operations.yaml
  projections/
    agent-context.yaml
    website-build.yaml
    inventory-workflow.yaml
  handoff/
    glossary.md
    website-maintenance.md
    inventory-workflow.md
    cms-data-dictionary.md
    approval-guide.md
```

## Issue cleanup workflow

1. Search Linear for ontology-related issues by title/description terms:
   - ontology
   - semantic contract
   - projection
   - handoff ontology
2. Inspect parent/child relationships so updates stay coherent.
3. Update active parent issues to reference the canonical repo and current build order.
4. Update discovery issues to write inventories into the canonical repo, e.g. `clients/<client>/sources.md` or `sources.yaml`.
5. Update projection issues to clarify:
   - projections are authored in canonical repo first
   - repo-local projections are consumer views
   - projection drift must be reconciled back to canonical
6. Leave canceled issues canceled if their original implementation path is stale, but rewrite the description to explain what superseded them.
7. Re-query every mutated issue and verify title, state, and source-of-truth language before reporting done.

## Recommended status behavior

- Move issues with newly changed architecture assumptions to **Triage** if they need re-review before execution.
- Keep parent/backlog implementation issues in **Backlog** if they are still valid but not actively being worked.
- Keep stale local-path implementation tickets **Canceled** when superseded, with a clear cancellation explanation.

## Pitfalls

- Do not leave old local project paths described as canonical in active issues.
- Do not silently resurrect a canceled issue whose implementation path is wrong; either rewrite it as superseded or create a fresh clean implementation issue.
- Do not encode temporary PR/issue/sprint status as ontology facts.
- For canceled issues, it is okay to mention the old stale path as the reason for cancellation, but make clear it is not the active canonical path.
