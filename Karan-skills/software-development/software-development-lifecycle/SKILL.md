---
name: software-development-lifecycle
description: "Use for software development methodology across planning, spikes, TDD, systematic debugging, Python/Node debugging, code review requests, and subagent-driven implementation."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [software-development, planning, debugging, tdd, code-review, subagents]
    related_skills: [github-operations, autonomous-coding-agents]
---

# Software Development Lifecycle

## Overview
This umbrella covers the class-level development process: plan, spike, implement, debug, test, review, and delegate. Load it when the user asks for coding work where process discipline matters more than a single framework.

## When to Use
- Write or follow an implementation plan.
- Run a throwaway spike before committing to a build.
- Apply test-driven development.
- Debug Python, Node.js, Hermes TUI commands, or complex root-cause issues.
- Request or perform pre-commit code review.
- Coordinate subagent-driven development.

## Workflow
1. **Understand and plan:** capture acceptance criteria, constraints, files, and risks.
2. **Spike if uncertain:** validate the riskiest assumption cheaply, then discard or promote learning.
3. **Build with tests:** prefer RED-GREEN-REFACTOR for logic-heavy changes.
4. **Debug systematically:** reproduce, isolate, explain root cause, then patch.
5. **Review before handoff:** inspect diff, tests, security, and user-visible behavior.
6. **Delegate carefully:** subagents can implement or review, but Hermes verifies.

## Subworkflows

### Planning
Plans belong in `.hermes/plans/` when plan-mode is requested; otherwise keep plans concise and immediately executable.

### Debugging
Do not guess. Reproduce the issue, observe logs/state, form hypotheses, test one at a time, and verify the fix with the failing case.

### Review
Use security and correctness gates before style comments. If adding GitHub review comments, target real diff lines.

For behavior-preserving exporter/serializer/database refactors with a narrow additive change, use `references/additive-export-refactor-parity.md`: generate artifacts from exact base and PR heads, compare every legacy schema plus normalized complete rows, then assert the additive surface separately. Equal row counts alone are not preservation proof.

### Repo contract/spec PRs with no live scaffold
When an issue asks for a schema/API/query contract but the live scaffold does not exist yet (for example a future CMS schema in an otherwise static repo), avoid stopping at prose. Make the contract executable inside the repo:
1. Add a human-readable contract under the repo's existing contract/API docs path (for example `docs/api/*-contract.md`) with field lists, lifecycle states, query contract, forbidden fields/non-goals, and explicit live-change boundaries.
2. Add sanitized fixtures covering positive and negative states (published/live, archived/excluded, failed/excluded, duplicate/idempotency risks where appropriate).
3. Add a zero-dependency validation script when the repo has no test framework; simulate the documented query/selection rules and fail on missing required fields, invalid enums, duplicate idempotency keys, forbidden commerce/live-availability fields, or unsafe URL sources.
4. Wire the validation into the repo's baseline test command so future builders cannot drift the contract silently.
5. Record verification evidence in the repo when the harness expects evidence artifacts.

When the user says an external reviewer (Codex/Claude/etc.) “left a review,” inspect all three GitHub surfaces before assuming there are no findings:
- PR review objects: `gh api repos/<owner>/<repo>/pulls/<N>/reviews`
- Inline review comments: `gh api repos/<owner>/<repo>/pulls/<N>/comments`
- Regular PR conversation comments: `gh pr view <N> --json comments,reviews,latestReviews`

### Static-analysis tool adoption for external agents
When adopting a repo-understanding tool such as CodeGraph for builder/reviewer workflows, distinguish the host boundaries: Hermes profile config, Claude Code config, and Codex config are separate. Configure the actual manual agent host the user named, create backups before edits, pin package versions where practical, and verify both syntax and runtime registration before saying the agent can use the tool. Keep generated indexes/caches local and gitignored unless there is an explicit reason to commit them. For first-pass rollout, prefer local `.git/info/exclude` for `.codegraph/` and only add tracked repo docs/`.gitignore` by PR after smoke tests prove value. Audit CodeGraph fit from `status`/`files`: static HTML/CSS/Markdown-heavy repos may index too little source to justify making CodeGraph mandatory. See `references/codegraph-adoption-for-agent-workflows.md` for the reusable rollout pattern and `references/codegraph-manual-agent-rollout-kit.md` for the fuller Claude Code/Codex rollout kit pattern, prompt contracts, smoke tests, and weak-fit handling.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/` as reference packages with `README.md` entry points, not active skills. `simplify-code` is retained there as a narrow cleanup/delegation pattern rather than a separately discoverable skill.

## Verification Checklist
- [ ] Real commands/tests were run when build/verify was requested.
- [ ] If no canonical test/lint/build command exists, run a focused temporary ad-hoc verifier from the OS temp directory using a `hermes-verify-` filename prefix, clean it up, and report it explicitly as ad-hoc verification rather than suite green.
- [ ] If the runtime injects an “unverified changed paths” notice after code edits, treat it as authoritative: create the requested temp verifier in the specified OS temp directory with `tempfile`, exercise the changed behavior directly, clean up verifier/generated caches, and explicitly label the result ad-hoc verification.
- [ ] If the verifier request repeats, do **not** cite the previous ad-hoc verifier as sufficient. Run a fresh `hermes-verify-*.py` script in the exact requested temp directory, print a unique `RUN_ID`, include expected-red assertions that would catch the old behavior, verify cleanup with `TEMP_SCRIPT_EXISTS_AFTER_CLEANUP=False`, and report it as **fresh ad-hoc verification, not suite green**.
- [ ] When an ad-hoc verifier exercises helpers that format file paths, include a fixture outside the repo (under the requested temp directory) so code using `Path.relative_to(repo_root)` without a guard fails red. The robust pattern is a small display helper that falls back to the absolute path for external files.
- [ ] Root cause is stated for bug fixes.
- [ ] Diff is reviewed before final handoff.
- [ ] Delegated work is independently verified.
