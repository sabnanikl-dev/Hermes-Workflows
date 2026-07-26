---
name: autonomous-pr-prover
description: "Route an existing GitHub PR through the pr-prover tool: trusted Claude builder and Codex reviewers at one exact head, Hermes judgment, Karan merge authority."
version: 2.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [github, pull-requests, multi-agent, review-loop, claude-code, codex]
    related_skills: [multi-agent-dev-workflow, integration-audit-review, github-operations, code-review]
---

# Autonomous PR Prover

## Trigger and non-goals

Karan asks to get an **existing** PR merge-ready: "run the reviewer loop on PR #N", "send this back to Claude to fix the review feedback", "babysit this PR".

Not for turning an idea into an issue, building a feature before a PR exists, or merging. No PR yet? Use `multi-agent-dev-workflow` first.

## Route it into the tool

The loop is executable and lives in `pr-prover/`. Do not re-run it by hand.

```bash
pr-prover/bin/pr-prover check-config --config <run.json>   # gates and reviewer lanes
pr-prover/bin/pr-prover run --config <run.json> --json     # 0 merge-ready | 1 blocked | 2 needs-Karan
```

Run it from the repository root: there is no install step, so nothing named `pr-prover` is on `PATH`. Mechanics stay in the tool — `pr-prover/examples/run.example.json` is the config shape, `pr-prover/MISSION.md` is the normative product boundary and lifecycle, and `pr-prover/README.md` documents the lane/marker contract, the push agreement, and fix-comment readback. Hermes' judgment sits either side of the run: write the config, read the report, advise Karan.

## Trusted roles

- **Claude Code** — builder/fix lane. Reads the live PR itself, edits, verifies, commits, pushes to the PR branch, posts its signed fix comment.
- **Codex Reviewer A/B and Integration Auditor** — independent review lanes judging one exact head. Configure all three, in that order.
- **Hermes** — operator and integrator. Verifies live GitHub evidence, classifies findings, reports merge-ready / blocked / needs-Karan.
- **Karan** — sole merge authority.

Quiet is not stuck: a trusted lane may print nothing for twenty minutes. Give each lane a realistic timeout instead of killing a silent one.

## Classify every finding

- **blocking** — must be fixed before merge-ready;
- **non-blocking** — becomes a follow-up issue or comment;
- **false positive** — say why, with evidence;
- **needs Karan** — taste, product, or scope judgment. Never send these to the builder.

Unresolved **human** PR comments are blocking even when checks are green and reviews are approved.

## Cycles and escalation

Two fix cycles, maximum; a partial builder fix gets one corrective rerun inside the open cycle, not a new one. Stop and ask Karan when two cycles have not cleared blockers, reviewers disagree on a judgment call, auth or environment blocks verification, the head/repo/branch is not what the run is bound to, or the PR carries unrelated changes.

## Conditional references

- Static-site / SEO copy, sitemap, canonical, or schema blockers → `references/static-site-current-head-review-loop.md`, `references/static-copy-pr-current-head-closeout.md`, `references/static-contract-review-edge-cases.md`; crawlable FAQ/GEO accordions → `references/static-faq-accordion-geo-pr-loop.md`.
- Visual contract, screenshots, or a human visual reference → `references/current-head-visual-contract-review-loop.md`, `references/human-visual-reference-map-alignment.md`, `references/pr-contract-surfaces-and-visual-pause.md`.
- CLI output-path safety (`--out`/`--output` as a write surface) → `references/read-command-output-path-safety-pr-loop.md`.
- A read-only validator or checker that could false-pass on missing, empty, or malformed input → `references/deterministic-validator-false-pass-probes.md`.
- Two reviewer lanes sharing one GitHub account, or a lane that finished reasoning but will not exit → `references/shared-reviewer-account-state-and-quiet-lanes.md`.
- Builder fixed only part of the blocker set → `references/partial-builder-fix-cycle-recovery.md`.
- Human "not mergeable" after green reviews, or a live CMS source of truth → `references/human-review-live-cms-source-of-truth.md`.
- A human changed a page's purpose, copy, or conversion goal → `references/human-copy-goal-contract-cascade.md`.
- Optional injected clocks, or reviewer scratch files contaminating the diff → `references/injected-clock-and-reviewer-scratch-hygiene.md`.
- Partial evidence runs with independently complete rows → `references/partial-run-independent-row-contract.md`.

## Merge authority

"Merge-ready" is a recommendation to Karan, never permission. Karan alone merges.
