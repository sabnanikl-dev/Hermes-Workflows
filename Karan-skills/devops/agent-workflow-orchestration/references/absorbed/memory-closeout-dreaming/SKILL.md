---
name: memory-closeout-dreaming
description: Design and operate conservative memory closeout/dreaming workflows that stage patterns before promoting to memory, Hindsight, Obsidian, or skills.
category: productivity
---

# Memory Closeout Dreaming

Use this skill when building, running, reviewing, or tuning Hermes closeout/dream reports that inspect sessions, Linear issues, GitHub PRs, notes, or other work evidence and recommend what should become durable knowledge.

This skill governs the *memory-quality workflow*, not the visual design of the report. If the deliverable is an HTML report, also use `claude-design` and its `references/absorbed/memory-closeout-dreaming/references/operational-dry-run-html-reports.md` reference.

## Core Principle

Dreaming should recognize patterns over time, not promote one-off observations.

A single session may reveal a possible signal, but it should usually remain staged. The more Hermes dreams, the more repeated preferences, procedures, project facts, and contradictions can mature into stronger recommendations.

## Backend-Aware Routing

Before recommending a target, detect the active memory provider and keep route labels honest:

- **Built-in memory:** compact stable preferences/facts only; watch char pressure.
- **Holographic:** local SQLite/HRR-style facts with entities and trust decay; repeated confirmations can strengthen trust, contradictions should decay.
- **Hindsight:** structured cross-session recall with entities, relationships, temporal context, reranking, and shared agent/tool memory; route project/entity/time patterns here or to Obsidian summaries.
- **Unsupported/other providers:** stage and report provider notes rather than assuming Holographic or built-in behavior.

## Routing Targets

- **Standard memory:** compact durable facts/preferences that prevent repeated steering.
- **Hindsight:** broader contextual recall, relationships, cross-session decisions, and project patterns.
- **Obsidian:** structured project/business knowledge, source-linked summaries, and wiki pages.
- **Skills:** repeatable procedures, tool pitfalls, verification patterns, and reusable workflows.
- **No-op/source-of-truth only:** task state, PR/issue numbers, transient statuses, and details better left in GitHub/Linear.

## Workflow

1. **Collect read-only evidence**
   - Sessions, recent corrections, completed Linear issues, merged GitHub PRs, relevant Obsidian notes, existing memory, Hindsight, and skills.
   - Do not mutate memory or trackers during dry run.

2. **Normalize candidate observations**
   - Preference-like observation.
   - Workflow/procedure lesson.
   - Project/domain fact.
   - Contradiction or stale-memory warning.
   - Tracker/source-of-truth noise.

3. **Fingerprint patterns**
   - Strip dates, issue numbers, PR numbers, URLs, and one-off identifiers.
   - Keep the recurring semantic shape: e.g. “gateway attachments need approved cache folder,” “dreaming scores should start conservative,” “GitHub PRs are implementation evidence, not memory.”

4. **Stage conservatively**
   - One-off observations should start low.
   - Prefer `needs more dreams` over `recommend promotion` on first sighting.

5. **Strengthen with recurrence**
   - Increase confidence only when the same pattern appears across multiple distinct evidence observations or source types.
   - Do not let repeated manual/test runs over the same session, PR, or issue increase maturity; track evidence keys such as source type + source id + candidate fingerprint.
   - Track observation count, source diversity, examples, first_seen, last_seen, and route history.

6. **Recommend only after pattern maturity**
   - Surface approval-ready recommendations only when recurrence and score are both strong.
   - Keep explicit approval gates before writing standard memory, Hindsight, Obsidian, or skills.

7. **Verify any approved write**
   - Re-read memory/skill/wiki targets after writing.
   - Report what changed and what remains staged.

## Conservative Scoring Guidance

Use scoring to rank pattern maturity, not to make one-off observations look important.

Suggested starting scores:
- One-off possible standard-memory pattern: `0.35–0.45`.
- One-off possible skill/workflow pattern: `0.35–0.45`.
- One-off possible wiki/Hindsight pattern: `0.30–0.40`.
- Source-of-truth tracker item: `0.15–0.30` and no-op by default.

Promotion readiness:
- **1–2 observations:** `needs more dreams`.
- **3+ observations:** `emerging pattern`.
- **5+ observations + high score/source diversity:** `ready for approval`.

Do not use high scores merely because text matches words like “prefer,” “remember,” “verify,” or “skill.” Those are candidate triggers, not proof of durability.

## Report Shape

A good dry-run report includes:
- Executive summary.
- Source health and coverage.
- Pattern-staging diagram.
- Candidate board with route, score, evidence, pattern observations, and promotion readiness.
- Ignored/no-op section with rationale.
- Recommended next gate.
- Raw JSON companion for auditability.

## Pitfalls

- **Over-scoring first runs:** early dreams should mostly stage, not recommend.
- **Memory bloat:** PR numbers, issue statuses, and “we did X today” do not belong in durable memory.
- **Duplicate trackers:** Obsidian summarizes source systems; it should not become a second Linear/GitHub.
- **Procedure in memory:** repeatable workflows belong in skills, not imperative memory entries.
- **Silent source gaps:** disclose missing/partial sources instead of pretending the report is complete.

## Support Files

- `references/absorbed/memory-closeout-dreaming/references/pattern-first-closeout.md` — detailed notes from the first Holographic closeout dry-run tuning session.
