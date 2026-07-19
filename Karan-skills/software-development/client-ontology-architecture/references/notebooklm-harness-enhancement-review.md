# NotebookLM-Grounded Ontology Harness Enhancement Review

Use this pattern when research notebooks are asked to improve the `client-ontologies` harness or roadmap.

## Grounding packet

Give each notebook the same compact live-state digest:

- verified repo/ref and current CI/test state;
- canonical resource kinds and runtime/export boundaries;
- corpus counts only when useful;
- every open issue title plus a one-line scope/dependency summary;
- observed gaps, clearly labeled as observations rather than predetermined solutions;
- approval, privacy, and no-SaaS/no-premature-infrastructure boundaries.

Query strategic-engineering and ontology-development notebooks separately. The former should critique loop quality, evaluation, resumability, and drift; the latter should critique competency coverage, semantic integrity, evidence, and consumer usefulness.

## Adjudication rules

Notebook answers are research input, not issue architecture authority.

1. Map each recommendation to `UPDATE existing issue`, `NEW focused issue`, or `DO NOT BUILD YET`.
2. Reject cross-domain scope pollution. Agent builder/reviewer contracts do not belong in client approval-gate structures; semantic regression does not belong in lifecycle/deprecation reporting merely because both are called “impact.”
3. Prefer competency questions plus deterministic outcome tests over transcript/model grading.
4. Keep competency questions under `tests/`; they are test requirements, not canonical ontology facts, evidence, or authority.
5. Preserve privacy: exact source highlights are useful for sanitized fixtures and retrieval benchmarks, but private source quotes must not be required in canonical files.
6. Add formal ontology constraints only where the current model supports them. Controlled predicate domain/range checks can be appropriate; class disjointness/OWL-style hierarchy is premature without a real class model.
7. Keep semantic retrieval off until a real consumer plus benchmark proves full-projection or filtered-SQLite modes inadequate.
8. Prefer bounded docs-contract cleanup over a scheduled AI “doc gardener” after a first drift incident.
9. Do not commit loop/sprint state when GitHub Issues/PRs already own transient execution state.

## Strong default outcome

A high-value review often yields:

- one new competency-question/semantic-regression issue;
- one documentation-contract cleanup issue when spec/roadmap drift is directly verified;
- bounded refinements to runtime parity, relationship constraints, evidence-hash semantics, and retrieval activation gates;
- explicit non-updates for approval gates, lifecycle reports, or extraction pilots that already cover the recommendation.

## Safe GitHub mutation order

When approved to file and update issues in one pass:

1. Re-read live repo, issues, PRs, labels, and default-branch state.
2. Search all issues for duplicates.
3. Create new issues first so their real issue numbers can be linked from existing issues.
4. Update existing bodies with a dated, clearly titled refinement/activation-gate section that states whether it is additive or supersedes an earlier clause.
5. Retitle an issue only when the old title materially misstates readiness or scope.
6. Re-read every created/updated issue and assert state, title, labels, required clauses, and cross-links.
7. Report live open-issue/PR counts and confirm no unrelated repo worktree change.

Do not paste raw NotebookLM output into issue bodies. Distill source-backed principles into repo-grounded contracts and preserve rejected recommendations in the user-facing synthesis, not as issue noise.
