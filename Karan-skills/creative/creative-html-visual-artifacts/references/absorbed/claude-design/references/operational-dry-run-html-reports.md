# Operational Dry-Run HTML Reports

Use this reference when turning a deterministic collector/dry-run output into a reviewable HTML report, especially for internal operations like Hermes closeout/dream reports, source-health checks, or approval-gated automation previews.

## Core pattern

1. **Collect read-only evidence first**
   - Pull from authoritative sources without mutating them.
   - Record source health explicitly: available, unavailable, partial, auth/config issue, or zero results.
   - Keep a raw JSON companion for auditability.

2. **Separate signal from promotion**
   - A candidate appearing in one run is not automatically durable knowledge.
   - Stage one-off observations conservatively.
   - Promote only after repeated runs reveal a stable pattern, or after explicit user approval.

3. **Design the report around decisions**
   - Executive summary: what was checked, what was found, what changed since prior run if available.
   - Source-health section: sessions, GitHub, Linear, docs, APIs, etc.
   - Candidate board: staged items with score, route, evidence, and promotion readiness.
   - Decision gate: what is safe to do now vs what needs more runs/approval.

4. **Use diagrams where they clarify routing**
   - Inline SVG is preferred for standalone portability.
   - Good diagrams: collection → staging → approval/promotion; source coverage; routing buckets; trust evolution.
   - Avoid decorative diagrams that do not help decide.

## Conservative pattern-first scoring

For memory/dreaming reports, score *patterns*, not isolated sightings.

Recommended starting posture:
- One-off memory-like observation: low/staged, around `0.35–0.45`.
- One-off skill/workflow observation: low/staged, around `0.35–0.45`.
- One-off wiki/Hindsight/project observation: lower/staged, around `0.30–0.40`.
- Tracker/source-of-truth item: no-op/source-truth only unless it reveals a reusable lesson.

Promotion readiness should depend on recurrence:
- **1–2 observations:** `needs more dreams` — keep staged.
- **3+ observations:** `emerging pattern` — mention but do not promote by default.
- **5+ observations + sufficient score/source diversity:** `ready for approval` — recommend memory, Hindsight, Obsidian, or skill route.

Useful fields in the raw JSON:
- `candidate`
- `route`
- `trust`
- `promotion_readiness`
- `pattern_key`
- `pattern_observations`
- `pattern_sources`
- `source_type`
- `source`
- `rationale`

## Routing doctrine

- **Standard memory:** tiny durable preferences/facts that prevent repeated steering.
- **Hindsight:** contextual recall and cross-session relationship/project patterns.
- **Obsidian:** structured project/business knowledge and durable summaries.
- **Skills:** repeatable procedures, pitfalls, verification patterns, or reusable workflows.
- **No-op/source-truth only:** PR numbers, issue statuses, one-off task state, and anything better left in GitHub/Linear.

## Packaging for gateway review

- Create a clean review folder with human-readable filenames.
- Include both the HTML and a `.zip` fallback.
- For Telegram/gateway delivery, stage attachments under `~/.hermes/cache/documents/...` before emitting `MEDIA:` lines.
- Verify each staged file exists and has nonzero size.

## Pitfalls

- Do not over-score the first dry run. Early reports should mostly say `needs more dreams`.
- Do not conflate repeated task churn with durable memory. Recurrence must mean a repeated preference, workflow, domain fact, or decision pattern.
- Do not duplicate Linear/GitHub into memory; use them as evidence.
- Do not hide source failures. A report with partial source coverage is still useful if disclosed clearly.
