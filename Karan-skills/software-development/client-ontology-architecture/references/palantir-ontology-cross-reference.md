# Palantir Ontology Cross-Reference for Client Ontologies

Use this reference when Karan asks to compare `sabnanikl-dev/client-ontologies` against Palantir Foundry Ontology concepts or when designing enterprise-grade improvements to the client ontology repo.

## Source pattern summarized

Palantir Foundry Ontology separates:

- **Semantic layer:** object types, properties, link types, interfaces, object views.
- **Kinetic layer:** action types and functions that capture decisions, writebacks, and workflow orchestration.
- **Governance layer:** permissions, markings, change review, usage/dependency views, restore/history, cleanup/deprecation.
- **Consumer layer:** OSDK apps, subscriptions, MCP exposure, semantic search/OAG workflows, object views/app-specific projections.

Useful source URLs:

- Core concepts: `https://www.palantir.com/docs/foundry/ontology/core-concepts`
- Overview: `https://www.palantir.com/docs/foundry/ontology/overview`
- Best practices and anti-patterns: `https://www.palantir.com/docs/foundry/ontology/ontology-best-practices-and-anti-patterns`
- Ontology Manager save/review: `https://palantir.com/docs/foundry/ontology-manager/save-changes/`
- Usage/dependencies: `https://palantir.com/docs/foundry/ontology-manager/view-usage/`
- Cleanup/deprecation: `https://palantir.com/docs/foundry/ontology-manager/cleanup/`
- Semantic search overview: `https://www.palantir.com/docs/foundry/ontology/overview-semantic-search`
- Document processing/chunking: `https://palantir.com/docs/foundry/ontology/document-processing/`
- Ontology augmented generation: `https://www.palantir.com/docs/foundry/ontology/ontology-augmented-generation`
- OSDK overview: `https://palantir.com/docs/foundry/ontology-sdk/overview/`
- OSDK subscriptions: `https://palantir.com/docs/foundry/ontology-sdk/typescript-subscriptions/`
- Ontology MCP overview: `https://palantir.com/docs/foundry/ontology-mcp/overview/`

## What `client-ontologies` already does well

- Canonical source is Git/YAML rather than private chat memory or runtime DB.
- Client/module/projection structure is clear and portable.
- Evidence/source confidence/status conventions are explicit.
- Validation catches YAML parse errors, IDs, duplicate object IDs, references, evidence references, and obvious secrets.
- SQLite export provides a lightweight runtime projection.
- Approval rules exist as rules/prose, which is safer than leaving authority boundaries implicit.

## Palantir-inspired gaps to consider

### 1. Manifest-first ontology entry points

Add `clients/<client>/ontology.yaml` as the reviewable index for modules, projections, handoff outputs, templates, and runtime exports. This mirrors Palantir’s managed ontology resource graph and gives agents/scripts one stable entry point.

### 2. Split and enforce schemas

The repo’s JSON Schema should become executable, not mostly documentary. Split by resource kind (`client`, `ontology`, `module`, `projection`, `evidence`, `rule`, `approval`, `state_machine`) and run schema validation before cross-reference checks.

### 3. CI and regression fixtures

Ontology Manager blocks unsafe saves with errors/warnings. GitHub Actions should do the same for PRs: validate YAML, run schema checks, test invalid fixtures, and verify SQLite export.

### 4. Kinetic resources: actions/functions/operations

Palantir models action types and functions separately from objects/properties/links. Add first-class `actions`, `functions`, or `operations` for business operations, agent-exposed tools, idempotency, preconditions, side effects, approval gates, and implementation pointers.

### 5. Interfaces and shared properties

Use interfaces/shared properties to avoid God objects, duplicate fields, and department/client-specific drift. Examples: `brand_governed_content`, `public_account_surface`, `client_handoff_artifact`, `inventory_media_asset`.

### 6. Usage, impact, lifecycle, cleanup

Add optional `usage`, `dependents`, and `lifecycle` metadata with `deprecated`, `deprecation_date`, `replacement`, and `migration_notes`. Add cleanup reporting for stale names, missing descriptions, deprecated-past-date resources, and unreferenced resources.

### 7. Semantic search/OAG contracts

Do not treat vector stores as loose blobs. Define document objects, chunk objects, chunk IDs, source-object links, text properties, embedding properties, embedding model/dimension, refresh policy, retrieval mode, and evaluation sets. Start simple; only add HyDE/hybrid/rerank complexity when needed.

### 8. Projection provenance/version metadata

Projections should record source ontology version/commit and consumer contract version. SQLite export should include build metadata and git commit when available.

### 9. Approval gates and approval records

Approval boundaries are central to Karan’s client work. Promote them from prose/rules into first-class validated objects that rules/actions reference. Export them to SQLite for runtime lookup.

### 10. State machines

Workflow lifecycles such as JMD inventory-image processing should be validated/exported. State machines need entity refs, states, transitions, guards, terminal/error paths, and SQLite tables.

### 11. Machine-checkable rule execution

Rules like disallowed copy terms should be executable deterministically (`scripts/check_rules.py`) rather than relying on agent judgment. Validate `machine_check` payloads and include passing/failing fixtures.

### 12. Client-safe handoff generation

Generate handoff packages from curated projections, not raw ontology dumps. Default to excluding local paths, private notes, credentials, raw exports, and internal execution context. Mark generated docs as requiring human review before external sharing.

## Anti-patterns to encode as lint/docs

From Palantir’s ontology design guidance:

- **System Silos:** object types mirror source systems instead of one real-world concept.
- **Kitchen Sink:** exposing every source field/metadata column.
- **Department Silos:** duplicate concepts owned separately by teams/workstreams.
- **God Object:** one overloaded sparse object instead of focused objects + interfaces.
- **Golden Hammer:** using functions/actions/pipelines for everything rather than the right layer.
- **Action Sprawl:** many single-property `SetX` operations instead of meaningful business actions.
- **Time Machine:** separate object/object type per historical version instead of history/time-series/audit patterns.
- **Misnomer:** vague names like `Item`, `value`, `type`, `date`, `relatedTo`.

## Issue drafting pattern from the session

When turning a Palantir-style cross-reference into GitHub issues:

1. Crawl/map the docs section first; save raw/cleaned docs to temp files if needed.
2. Inspect repo architecture and existing issues/labels before creating anything.
3. Group improvements into implementation-sized class-level issues rather than one issue per doc page.
4. Each issue should include: context, Palantir reference URLs, recommended approach, likely files, and acceptance criteria.
5. Use existing repo labels only; verify issue readback (`number`, `title`, `state`, `url`, `labels`, body substrings) before reporting success.
