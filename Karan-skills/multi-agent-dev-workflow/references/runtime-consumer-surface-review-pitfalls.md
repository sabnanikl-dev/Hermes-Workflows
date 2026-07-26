# Runtime consumer surface review pitfalls

Use this when a PR adds a read-only CLI/service over canonical YAML plus a compiled SQLite snapshot, especially when the CLI is meant to run from another repository.

## Fail-closed backend identity

A database is not trustworthy merely because expected table names and columns exist. Before any operation can return a clean result, validate the artifact contract:

- required tables exist and core tables are non-empty;
- normalized row IDs equal IDs inside `raw_json`;
- resource `kind` and client ownership are valid;
- manifests/resources are internally complete enough for the advertised operations;
- normalized entities/rules agree with the module documents the service actually consumes;
- an empty, partial, forged, or internally drifted snapshot fails with structured usage/error output.

Include adversarial regressions where a schema-shaped database deliberately removes or reroutes a blocking rule. The copy check must fail closed rather than return zero violations.

## Close every duplicated representation, not only rule IDs

Compiled snapshots often preserve the same meaning in normalized columns/tables and embedded `raw_json`. Validation must cover every representation the runtime actually reads:

| Contract edge | Required comparison/probe |
|---|---|
| Module rule/entity content | Full canonical JSON equality with normalized rows, including status, severity, evidence, and `machine_check`; preserve IDs while mutating content. |
| Projection membership | `projections.includes_json` must equal embedded `raw_json.includes`; empty only the embedded includes and prove projection-scoped enforcement exits 2. |
| Client/workstream routing | A requested workstream must resolve to at least one module owned by that client; adding a client-only workstream must not create a clean zero-rule pass. |
| Row envelope | Normalized row `client_id`/`module_id` must agree with embedded ownership and the containing module, not only with a globally valid client/module ID. |
| Manifest closure | Every declared module/projection exists, and unexpected unmanifested clients/resources are either rejected or explicitly supported by the artifact contract. Test correlated parent+child deletion and rogue additions. |
| Positive control | A genuine exporter-produced snapshot still validates and preserves the expected blocking/warning behavior. |

Choose one source of truth for each field. If two representations remain, compare canonical full content before exposing operations. ID-set equality alone is insufficient because same-ID semantic mutation, correlated deletion, and cross-owner reassignment all preserve apparently valid shapes.

For enforcement selectors, distinguish “recognized label” from “enforceable scope.” A client declaration cannot make a scope safe when no owned module contributes rules to it. Fail with structured exit 2 rather than returning `violations: []`.

## Consumer installation and snapshot discovery

A package that installs only Python modules does not automatically include canonical client YAML or a compiled ontology snapshot. Test the documented consumer flow from a directory outside the ontology checkout.

Require one explicit data contract:

1. a pinned SQLite artifact passed with `--source sqlite --sqlite-path ...`; or
2. an explicit ontology checkout passed with `--source yaml --root ...`.

Do not document a git hook that relies on ambient `.` unless client data is intentionally vendored there. Exercise the installed console entry point from a foreign working directory, and prove SQLite mode still works with Ruby/YAML tooling absent.

## Provenance must belong to the artifact

Never derive SQLite ontology provenance from the process working directory. If the snapshot does not carry validated source-commit metadata, return `repo_commit: null` rather than stamping the consumer repository's HEAD. Add a regression that runs in a different Git repository or with a dataset that has no root.

## Structured CLI errors

If the contract promises machine-readable errors, `argparse` failures count too. Put argument parsing inside the structured-error boundary or override parser error handling so unknown flags, missing subcommands/options, and mutually exclusive arguments emit deterministic JSON and exit 2. Tests must parse stderr, not merely assert the exit code.

Scope selectors used for enforcement must fail closed. An unknown or misspelled workstream/projection must never select zero rules and return success.

## Competency tests must traverse public operations

Outcome/competency parity tests should call the same public service operations consumers call. A test that invokes private scope helpers and re-encodes result rows can stay green while `get_client_context` or `get_projection` regresses. Map corpus questions from public operation payloads, then compare normalized YAML and SQLite answers.

## Documentation and PR metadata sweep

When the runtime surface lands, synchronize:

- package/install and snapshot-location guidance;
- hook examples;
- YAML-vs-SQLite/Ruby boundaries;
- structured error and provenance claims;
- current roadmap state for dependencies already merged;
- PR-body test counts and architecture claims.

Treat stale present-tense roadmap entries as blockers when the PR itself edits that roadmap and claims current-state accuracy.
