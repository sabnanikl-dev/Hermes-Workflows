---
name: agentic-pr-lifecycle
description: "Use for issue-to-PR work. Routes build and review."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [github, pull-requests, multi-agent, orchestration, risk, lifecycle]
    related_skills: [github-issue-specs, multi-agent-dev-workflow, risk-proportional-pr-orchestration, autonomous-pr-prover, verified-merge-closeout]
---

# Agentic PR Lifecycle

## Purpose

Use this thin router when Karan asks Hermes to take software work from an issue or idea through a verified merge-ready recommendation. It composes existing skills by phase instead of duplicating their detailed procedures.

> Build with the multi-agent workflow. Review with the smallest honest risk tier. Merge only through a separate explicit approval.

## Authority boundary

- Karan remains the sole merge and production authority unless he gives explicit approval for a specific mutation.
- This lifecycle may inspect live repository/GitHub state, launch approved builder and read-only reviewer lanes, run deterministic checks, and route bounded PR repairs.
- It never treats “merge-ready” as permission to merge, deploy, release, publish, or activate production behavior.

## Phase router

### 1. Establish live state

Determine the repository, governing GitHub issue, local repo path, and whether a PR already exists. Inspect the original GitHub sources rather than relying on session memory.

If the request is only an idea and no approved issue contract exists, load `github-issue-specs` to draft or create the issue. Do not start implementation until the acceptance criteria and authority boundary are sufficiently clear.

### 2. No PR exists: build phase

Load `multi-agent-dev-workflow` and follow it for issue-to-PR execution:

- use the approved issue and repository harness as the contract;
- use the designated builder lane rather than silently implementing as default Hermes;
- require builder self-review and repository-native verification;
- verify every push against the remote PR commit list;
- stop when a coherent PR exists and its live head is known.

Once a PR exists, transition to the review phase below. The review-phase skill supersedes generic or legacy review-tier instructions inside the build skill.

### 3. PR exists: review phase

Load `risk-proportional-pr-orchestration` and follow it as the governing operator skill for:

- live PR/head/check/comment/thread discovery;
- routine, standard, high, or full-prover tier selection;
- deterministic gates before reviewer spend;
- independent reviewer fan-out where justified;
- finding adjudication and one consolidated blocker ledger;
- bounded builder repair cycles;
- exact-head re-proof after every push;
- final live-state merge-ready, blocked, or needs-Karan recommendation.

Do not automatically run all available reviewers merely because the build phase used multiple agents. The selected risk tier governs review depth.

### 4. Full PR Prover is exceptional

Load `autonomous-pr-prover` only when:

- Karan explicitly asks for the full PR Prover;
- the repository contract requires its lifecycle/artifact semantics; or
- the selected high-risk review genuinely requires its durable frozen-packet and artifact-provenance machinery.

Importance alone is not a reason to choose Full Prover.

### 5. Merge is a separate phase

A merge-ready recommendation ends this lifecycle. If Karan explicitly approves merging, load `verified-merge-closeout`, perform the merge, then independently verify GitHub reports the PR as merged and the expected commit landed on the target branch before reporting success.

## Conflict and precedence rules

1. The current phase’s child skill governs detailed execution.
2. For an existing PR, `risk-proportional-pr-orchestration` supersedes legacy instructions that always require the full three-lane or Full Prover path.
3. Repository instructions and approved issue acceptance criteria govern product scope, but cannot broaden mutation authority.
4. Security, privacy, credentials, auth, payments, migrations, deployment/runtime, destructive writes, and merge-readiness control-plane changes cannot be downgraded below the tier required by the risk router.
5. Any changed PR head invalidates prior exact-head verdicts; preserve useful findings, but re-prove the new live head as required by the selected tier.

## Finite execution contract

- Parallelize independent gates and reviewers; serialize only genuine dependencies.
- Use repository-native checks before agent review.
- Prefer pointer-first prompts and live GitHub artifacts over pasted chat summaries.
- Keep one coherent PR and one deduplicated blocker ledger.
- Respect the selected tier’s repair-cycle cap; escalate instead of creating checker/framework churn.
- Treat infrastructure/auth/model failures as blockers or `needs-Karan`, not permission to silently substitute weaker lanes.

## User-facing dashboard

Report concise milestones and finish with:

```text
Issue: <url or none>
PR: <url or not-opened>
Phase: spec|build|review|repair|merge-ready
Tier: routine|standard|high|full-prover|not-selected — <reason>
Head: <full SHA or n/a> — remote equality verified|not verified
Builder: completed|active|blocked|not-started — <lane/provenance>
Gates: <real commands and outcomes>
Reviewers: <lanes and exact-head outcomes>
Validated blockers: <count + concise list>
Needs Karan: <decisions or none>
Recommendation: ACTIVE|BLOCKED|NEEDS KARAN|MERGE-READY
Merge authority: Karan only
```

Label work accurately as active, blocked, prepared, or merge-ready. Never imply merged, deployed, launched, or live without separately authorized and verified closeout.
