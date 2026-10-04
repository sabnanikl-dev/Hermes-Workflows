# Provenance

- User request: September 22, 2026, implement highest-value Jev use for Hermes through OpenRouter `typesafe/jev-1.13` based on the established Jev research page.
- Source and compiled knowledge: Hermes Brain `wiki/shared/research/jev/Jev and TypeSafe AI.md`, especially advisory skill selection and OpenRouter integration findings.
- Implementation: `/Users/creator/projects/hermes-jev-skills/`; see `SPEC.md`, `RESULTS.md`, `OPERATIONS.md`, tests and actual synthetic API evidence.
- Validation: live Decisions API, 80 synthetic selector invocations, default-profile adapter smoke, unit/boundary tests, independent review and bounded repairs. Not production calibration.
- Review lesson: broad `_find_all_skills` discovery can read project/external directories and write scan attestations. This workflow uses a contained local scan and reviewed generic summaries instead.
- Scope: default-profile opt-in only; no toolset/allowlist expansion, auto upload, action authority or other profile changes.
- Rollback: stop invoking or disable the skill. No hooks, daemons or model settings to undo.
- Ledger: SE-2026-09-22-JEV-001.
