# Neutral ontology branding + future UI direction

Use this when a client ontology repo/spec starts drifting toward Papi/PAPI/papi.ai branding or SaaS/platform language.

## Durable preference

Karan wants to interact with client ontologies in a UI eventually, but does not necessarily want a SaaS platform. Treat future UI/admin/dashboard/browse/edit surfaces as consumers or interfaces over the canonical ontology repo unless an explicit architecture decision changes the source of truth.

## What to keep

- PAPI Linear issue IDs and URLs may remain when they are real planning/evidence history.
- Operator/company context may be mentioned if the document is explicitly about Papi AI Consulting operations.
- Future UI affordances are valid: browse, edit, validate, preview handoff, show provenance/staleness, display rule check failures.

## What to neutralize

- Schema `$id` values or JSON Schema `$ref`s using `https://papi.ai/...` when they identify generic client ontology contracts.
- RDF/Turtle prefixes that brand generic ontology concepts under `papi.ai`.
- Phrases like “future hosted Papi systems” or “reusable Papi patterns” in generic ontology docs.
- Issue acceptance criteria that assume SaaS, hosted telemetry, product branding, or app database canonical truth.

## Preferred replacements

- Schema IDs: `https://client-ontologies.local/schemas/<name>.schema.json` or another neutral namespace.
- RDF/ontology examples: `urn:client-ontologies:ontology:client#` and `urn:client-ontologies:ontology:clients:<client>#`.
- Product wording: “future hosted ontology UIs, dashboards, and client-work systems.”
- Pattern wording: “reusable client-ontology patterns.”

## PR pattern

1. Search docs, schemas, scripts, and examples for `papi`, `PAPI`, and `papi.ai`.
2. Classify each hit:
   - evidence/history Linear reference: usually keep;
   - generic schema/namespace: neutralize;
   - product/platform implication: reword;
   - operator-specific business context: keep only if scope explicitly requires it.
3. Add or update a UI-without-SaaS section in the spec:
   - future UI is allowed;
   - canonical truth remains reviewed repo files;
   - UI metadata describes views/forms/actions/provenance;
   - dashboards/admin panels are consumers/projections by default.
4. Update validator/schema dispatch IDs together with schema `$id` changes.
5. Update open issue bodies when needed so future work includes expected outcome, non-goals, and acceptance criteria that preserve neutral naming and UI-as-consumer semantics.
6. Run validator, export, fixture tests when present, diff check, push, and verify PR head SHA remotely before reporting.
