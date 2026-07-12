# Multi-Agent Loop Leaning from Strategic Engineering NotebookLM — 2026-07-01

Session-derived synthesis after sharing current `multi-agent-dev-workflow` and `autonomous-pr-prover` snapshots with the Strategic Engineering NotebookLM.

## Core Finding

The loop should be leaned by reducing context/operator waste, not by removing guardrails or increasing autonomy. The useful direction is:

- smaller root procedures;
- bulky historical pitfalls moved to references;
- clearer done-contracts before expensive fix turns;
- harsher reviewer rubrics;
- explicit budget/checkpoint gates;
- builder-only compaction experiments only after fresh reviewer independence is preserved.

## Adopt / Experiment / Reject

| Recommendation | Status | Notes |
|---|---|---|
| Physically decouple root skill procedures from bulky historical pitfalls/references | Adopt carefully | Hermes currently loads full matching skills; root `SKILL.md` size is direct context tax. Keep critical invariants visible. |
| Add pre-implementation done-contracts for non-trivial fix loops | Adopt/experiment | Builder and reviewer agree on what done means + verification before expensive implementation. Skip for tiny obvious fixes. |
| Add lightweight harshness/rubric guidance for reviewers | Adopt/experiment | Rubric should sharpen critique, not replace concrete file/line blockers. |
| Add deterministic budget/tool-call checkpoints around fix lanes | Experiment | Prevent doom loops and unknown state. Stop/checkpoint before another fix cycle if verification budget is insufficient. |
| Builder-only compaction | Delay/experiment | Fresh reviewer sessions remain the default; compaction must not replace PR-bus state. |
| Generic “progressive disclosure” advice | Reject as advice-only | It only helps if skills are physically refactored, because current Hermes skill loading reads full `SKILL.md`. |
| Treat background polling as new | Reject | Already covered in `autonomous-pr-prover`; maintain, don’t duplicate. |
| Fully autonomous merge | Reject | Karan remains final merge authority. |

## Guardrails Not To Optimize Away

- Karan final merge authority.
- PR as coordination bus.
- Separate reviewer identity when possible.
- Maker/checker split.
- Current-head verification.
- No direct Hermes code edits unless explicitly approved and disclosed as fallback/degraded.

## Practical Refactor Guidance

When slimming `multi-agent-dev-workflow` or `autonomous-pr-prover`:

1. Keep root `SKILL.md` focused on trigger, invariants, procedure, gates, and stop conditions.
2. Move session-specific lessons, long tool quirks, PR-specific pitfalls, and historical incident detail into `references/`.
3. Add a one-line pointer in root for each support file so future agents can load it only when relevant.
4. Do not remove high-frequency safety checks from root: reviewer identity, PR-bus pointer-first prompts, launch discipline, MCP-safe syntax, current-head verification, fallback disclosure, and human approval gates.
