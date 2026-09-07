# Discovery App Outline Readiness Review

Use this reference for internal product/technical outlines that combine a proposed workflow, data sources, application architecture, diagrams, implementation phases, and polished HTML/PDF companions.

## Readiness classes

Keep the verdict scoped:

- **Discovery-ready:** facts, assumptions, recommendations, and open questions are distinguishable; no implementation authority is implied.
- **Decision-ready:** the next decision, decision-maker, commercial/build authority, prerequisites, and non-goals are explicit.
- **Pilot-ready:** approved source contracts, authoritative inventories, access controls, operational recovery, privacy lifecycle, and measurable acceptance criteria exist.
- **Production-ready:** deployment, support, incident, backup/restore, retention/deletion, monitoring, cutover, and sponsor gates are proven.

Do not let a synthetic UI or algorithm jump readiness classes. It can prove workflow usability, deterministic behavior, and technical feasibility; it cannot by itself prove business value, source feasibility, or production suitability.

## Source-grounding matrix

### Authority and provenance

- Label each material statement as source fact, owner decision, recommendation, estimate/hypothesis, or open question.
- Bind important source claims to claim-level references, not only a bulk bibliography.
- Record owner decisions with date and scope.
- Treat external-model critiques as planning input, never as business authority.
- Name the actor who may authorize build/commercial scope. Stakeholder agreement is not authorization unless the source says so.
- Keep proposed participants unresolved until they accept or an authorized sponsor defines their role.

### Operating contract

- Parameterize cadence until assignment duration, cutoffs, and rerun rules are known.
- Name who may open, lock, run, override, approve, publish, and close.
- Define whether maker-checker separation is required and whether self-approval needs a recorded exception.
- Define what “publish” means, who receives it, and whether any post-approval change invalidates approval.

### Data and source contract

- Draw every real source as gated until access, fields, terms, retention, and owner are approved. Manual export does not make a real source part of the synthetic slice.
- Distinguish an opportunity list or provider allocation from an authoritative inventory assignable to reps.
- Require the inventory owner, artifact, allocation semantics, capacity, cutoff/as-of time, correction behavior, and conflict rules.
- Add ISP/product scope, canonical outcome definitions, cancellations/late events, ownership/reallocation, eligibility, and inactive-record rules.

### Scope and claims

- Mark time and volume ranges as unvalidated sizing hypotheses unless grounded in measured samples and staffing.
- Present vendor/framework choices as prototype candidates until production constraints and source contracts are known.
- Avoid speculative multi-tenancy. Use a single-client deployment until a second customer creates a real isolation/data-rights requirement.
- Prefer immutable versions plus focused actor/reason audit events for an early proof; require general event sourcing only when correction/replay behavior justifies it.

## Real-data gate

Before an adapter accepts real production data, require:

- authenticated principal → membership/role → service authorization → deny-by-default database grants/RLS, with negative IDOR/cross-role tests;
- atomic approval/publication bound to exact draft, ruleset, input batches/hash, recommendation digest, actor, and output artifact, with stale/concurrent requests rejected;
- bounded synchronous execution or a durable worker contract with leases/checkpoints, retry classes, poison quarantine/dead letter, transactional commit/outbox, reconciliation-before-retry, cancellation, and operator recovery;
- erasable-PII versus durable-audit classification, retention/deletion/legal hold, backup expiry, and deletion verification;
- privileged-session controls, file-size/row/MIME/encoding/parser limits, CSV formula neutralization, source/sender/range allowlists, stable IDs, and locale/date normalization;
- byte-exact determinism (ordering, ties, nulls, decimals, timezones, canonical serialization/hashing, runtime versions, golden fixtures);
- rate/payload limits, backup/restore and credential-revocation objectives, redacted monitoring, alert latency, and named incident/support owners.

## Multi-format artifact integrity

- Declare one canonical editable source. HTML and PDF are derivatives unless the workflow says otherwise.
- Reviewers must receive exact hashes. Any source, HTML, citation, diagram, or provenance edit invalidates the prior review for that artifact.
- After applying reviewer findings, either rerun reviewers against final hashes or phrase the outcome honestly as “findings incorporated and independently/deterministically verified.” Never say the final bytes received reviewer PASS when they did not.
- Regenerate PDF after every material HTML change, then verify metadata/text and render representative pages including the cover, diagrams, dense tables/phases, recommendation, and last page.
- Refresh screenshots after material edits; stale screenshots are not final evidence.

## Diagram and responsive checks

- Give solid versus dotted/gated edges explicit semantics, then assert that every real source uses the intended edge class in both source and rendered formats.
- A Chrome CLI `--window-size=390,...` capture can be cropped by browser minimum-window behavior and is not exact mobile proof.
- Prefer Playwright viewport configuration or CDP `Emulation.setDeviceMetricsOverride` for exact mobile evidence. Record `window.innerWidth`, `document.documentElement.scrollWidth`, and require `scrollWidth <= innerWidth` before calling the layout overflow-free.
- Inspect the resulting screenshot visually; a DOM assertion does not prove typography, wrapping, or contrast.

## Closure language

A strong handoff states:

- canonical source and derivative paths;
- final hashes and page/diagram counts;
- which reviewer findings were fixed;
- whether final hashes received a fresh reviewer verdict;
- deterministic, responsive, and PDF evidence;
- remaining readiness class and explicit non-authorization boundaries.
