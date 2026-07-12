# Repo-Local Autonomy Lab Pattern

Use this when Karan asks to make Hermes more autonomous/proactive inside a low-risk personal or infrastructure repository.

## Pattern

Build autonomy as a small inspectable lab, not as vague scheduled agent activity:

1. **Make the repo useful to forks/humans first**
   - Add or maintain docs that explain the autonomy pattern, not just private instructions.
   - Prefer plain Markdown and dependency-free scripts.
   - Good artifacts: `docs/autonomy-lab.md`, reusable prompts, checklists, small validators, examples.

2. **Quiet deterministic watchdog first**
   - Script-only cron (`no_agent=True`) should print nothing when healthy.
   - It should alert only when an objective invariant fails.
   - Typical checks: clean worktree, remote sync, local validator, `git diff --check`, risky tracked filenames.
   - The watchdog reports and stops; it does not auto-fix.

3. **Scout second**
   - LLM cron can run on a bounded schedule, e.g. twice daily for a low-risk personal repo.
   - It should inspect a compact evidence packet from a deterministic context script.
   - It chooses exactly one: direct commit, open/auto-merge a PR, report one concrete proposal, or report no useful move.
   - Let it be interesting/useful/fun, but keep one run to one coherent change.

4. **Autonomous landings with hard boundaries**
   - If Karan has not granted repo-local autonomy, stop at proposals/PRs that require manual approval.
   - If Karan explicitly says he does not want to approve/merge PRs in this repo, allow direct commits to `main` for small safe changes and auto-merged PRs for larger repo-local changes.
   - Verify remote branch/main commit matches local HEAD before reporting pushed.
   - If merging a PR, re-query GitHub and confirm `mergedAt != null` or `state == MERGED` before reporting success.
   - Keep changes reviewable in under five minutes.

## Useful repo files

- `scripts/autonomy_watchdog.py` — quiet health check; healthy stdout is empty.
- `scripts/proposal_scout_context.py` — emits JSON evidence for the scout.
- `scripts/loop_audit.py` — executable readiness score for autonomy scaffolding.
- `prompts/proposal-scout.md` — reusable scheduled-agent prompt.
- `docs/autonomy-lab.md` — fork-friendly explanation of the pattern.
- `docs/autonomy-policy.md` — tiered rules for direct commit, auto-merge, and stop-the-line boundaries.
- `docs/rubrics/autonomy-change-rubric.md` — distinguishes useful autonomous changes from busywork.
- `templates/autonomy-contract.md` — scope/risk/verification contract for larger autonomous changes.
- `examples/proposal-scout-report.md` — copyable closeout examples for direct commit, PR auto-merge, proposal-only, and no-useful-move outcomes.

## Marketed value lane

If Karan says value should be marketed so real money can flow in, encode that as a repo-local lane, not as permission to sell or contact people.

Autonomous repo-local work may create:

- `docs/marketed-value-lane.md` — how internal utility becomes market-facing value;
- `docs/rubrics/marketed-value-rubric.md` — audience/pain/outcome/proof/distribution/revenue scoring;
- `templates/revenue-experiment.md` — offer, pricing, channel, validation-question template;
- `examples/revenue-opportunity-report.md` — proof-backed offer sketch using only repo-local artifacts;
- landing-page drafts, lead-magnet outlines, validation interview prompts, pricing hypotheses, demo narratives.

Hard stop: do not publish, send outreach, create payment/checkout links, buy domains/tools/lists, contact third parties, or make revenue/ROI promises without Karan's explicit release approval.

## Proposal scout prompt shape

Include:

- repo path and GitHub owner/repo;
- hard boundaries: no global config/profile/tool authority changes, no credentials, no external messages, no private data ingestion;
- if repo-local autonomy was granted: direct commit and auto-merge are allowed only after validator/audit checks and remote SHA verification;
- if marketed value is in scope: repo-local offer/landing/pricing/validation drafts are allowed, but publication/outreach/payment setup remains a human-release boundary;
- required orientation: `git status`, remote verification, context packet, open issues/PRs;
- decision policy: direct commit vs auto-merged PR vs proposal vs no useful move;
- landing path: one change, validate, diff check, loop audit, commit, push, verify remote commit; if using PR, verify merge state and restore clean `main`;
- final format: decision, inspected evidence, change/proposal, verification, risk/next step.

## Closeout report examples

For fork-friendly proposal scouts, consider adding `examples/proposal-scout-report.md` with copyable reports for the three normal outcomes:

- **PR opened** — include repo/issue/PR inspection, changed files, validation commands, PR URL, and local-vs-remote commit SHA match.
- **Proposal** — include the concrete proposal, why it needs human taste/policy/authority approval, and evidence that no duplicate issue/PR exists.
- **No useful move** — include the clean/current evidence and why opening a PR would duplicate work or create noise.

Reserve `[SILENT]` only for delivery channels that explicitly suppress genuinely empty reports; do not combine it with content.

## Pitfalls

- Do not keep behaving conservatively after Karan explicitly grants repo-local autonomy. In `Hermes-personal`, his "I don't want to approve PRs/merges" correction means complete the loop: validate, land, push, and verify — while keeping stop-the-line boundaries.
- Do not mistake "autonomy" for frequent noisy summaries. A healthy watchdog should be silent.
- Do not overfit to Karan-only private context if the repo is meant to be forkable; make artifacts useful to other agent operators.
- Do not treat "make money" as permission for spammy or external action. Package marketed value as repo-local proof/offers/drafts; stop before publication, outreach, checkout/payment setup, purchases, or third-party contact.
- Do not let scheduled jobs broaden authority. Repo-local autonomy is not permission to mutate global Hermes config, credentials, profiles, client systems, or external communications.
- Do not use raw memory/session/Obsidian/email/chat exports as scout input unless explicitly approved. Use repo-local state and deterministic summaries.
- If the repo is dirty or out of sync, the scout should block/report instead of editing.
