# Hermes Personal Autonomy Cron Planning Pattern

Use this reference when Karan asks to make Hermes more autonomous/proactive in `sabnanikl-dev/Hermes-personal` or a similar personal-infrastructure repo.

## Situation

`Hermes-personal` is a small, durable operating repo for Hermes' own working habits: principles, prompts, checklists, validation scripts, safety rails, and repo-local skill bundles. It is **not** a dumping ground for private data, session logs, raw Hindsight/Obsidian/email exports, client deliverables, or broad autonomous mutation.

Karan may grant this repo more freedom than normal project repos. When he explicitly says he does not want to approve/merge PRs in this repo, treat that as repo-local autonomy only: direct commits or auto-merged PRs are allowed after deterministic checks, but do not widen authority elsewhere.

Karan may also make money/marketed value an experiment axis for this repo. Treat that as permission to create repo-local offer sketches, landing-page drafts, pricing hypotheses, lead-magnet outlines, validation prompts, and revenue opportunity reports. It is **not** permission to publish, send outreach, create checkout/payment links, buy domains/tools/lists, contact third parties, or make revenue/ROI promises without explicit release approval.

## Research + grounding workflow

1. **Query the required notebooks, not a generic notebook.**
   - Required for the live Proposal Scout: `Agent sdk` (`185f25cd-44e5-48ff-90a4-d319b71ffc31`) and `Strategic Engineering: Harnessing AI as a Force Multiplier` (`95758f68-a24f-442b-8973-bf542052b267`).
   - Use `Agent sdk` for concrete agent-loop/tool/handoff/tracing/guardrail/evaluation implementation patterns.
   - Use `Strategic Engineering` for prioritization, leverage, autonomy boundaries, stop conditions, and operating-model strategy.
   - Optional complements only when clearly useful: `AI OS`, `Hermes Profiles`.
   - Ask for loop principles, candidate routines, gates, stop conditions, forbidden mutations, and a 1–2 week smallest experiment.
2. **Ground against live repo state before recommending.**
   - Verify local clone/remote/default branch status.
   - Read `AGENTS.md`, `README.md`, `docs/authority-boundaries.md`, `docs/ask-vs-act.md`, `checklists/self-directed-change.md`, `scripts/validate_repo.py`, and any repo-local workflow skill bundle.
   - Run `python3 scripts/validate_repo.py` when available.
   - Check open GitHub issues/PRs and existing Hermes cron jobs.
3. **Run a second NotebookLM refinement pass.**
   - Feed a concise current-state digest back to each relevant notebook.
   - Ask which loops are redundant/premature, which candidate should be first, and what requires Karan approval.
4. **Synthesize by autonomy tier.**
   - If no explicit autonomy grant exists, prefer a script-only/no-agent read-only watchdog before LLM cron loops.
   - If Karan grants repo-local autonomy, build toward an autonomous lab: quiet watchdog + proposal/context scout + loop-readiness audit + direct commit/auto-merge policy.
   - Prefer quiet success: no stdout/no delivery when healthy.
   - Keep cron bounded by repo-local authority and clear stop conditions.

## Recommended phased experiment

### Live cron prompt sync

When a NotebookLM-derived repo artifact changes the behavior of an existing scheduled loop, update the live cron job prompt in the same task, not just the repo docs. For `Hermes-personal`, this especially applies to `Hermes Personal Proposal Scout`: if you add or change a gate, rubric, contract, landing policy, or required verification step, run `cronjob(action='list')`, update the matching job prompt, and verify the stored prompt contains the new required phrases. This keeps the autonomous loop aligned with the repo artifact it is supposed to follow.

Verification evidence should include both repo evidence (validator/audit/remote SHA or merge state) and scheduler evidence (job id/name, enabled state, next run, and prompt substring checks). Do not change schedule/cadence/delivery unless the user explicitly asked.

### Phase 1 — Silent integrity watchdog

- **Mode:** `no_agent=True` script-only cron.
- **Allowed actions:** read repo state, `git fetch --prune`, run deterministic validators.
- **Typical checks:** clean worktree, local branch not behind/diverged, `python3 scripts/validate_repo.py`, `git diff --check`, obvious forbidden files/patterns.
- **Healthy behavior:** print nothing so cron delivers nothing.
- **Failure behavior:** alert with command evidence; do not clean/reset/pull/commit.
- **Forbidden:** file writes, commits, pushes, merges, global config/profile/tool changes, moving private data into the repo.

### Phase 2 — Proposal/context scout

- **Mode:** LLM cron with narrow toolsets and repo-local evidence packet.
- **Output:** one concise proposal, direct repo-local landing, auto-merged PR, or “nothing worth doing,” depending on autonomy tier.
- **Allowed actions without autonomy grant:** inspect repo-local durable files and recent commits; report one proposal.
- **Allowed actions with explicit Hermes-personal autonomy grant:** make one small repo-local change, validate, commit, push, and either direct-land to `main` or auto-merge a PR.
- **Forbidden:** crossing stop-the-line boundaries, broad rewrites, costly/broad research, or copying private data into the repo.

### Phase 3 — Autonomous lab loop

Use after Phase 1/2 are working and Karan has granted repo-local autonomy.

- **Add executable gates:** a `loop_audit.py`-style readiness score in addition to the repo validator.
- **Add decision artifacts:** autonomy policy, autonomy-change rubric, contract template, example reports/simulation logs.
- **Landing policy:** direct commits for safe hygiene/small lab artifacts; auto-merged PRs when a visible coordination artifact is useful.
- **Verification:** `validate_repo.py`, `git diff --check`, `loop_audit.py --min-score N`, remote SHA verification, and merge-state verification when PRs are merged.

## Marketed value extension

If Karan says the value should be marketed so real money can flow in, add this to the NotebookLM/current-state prompt:

- ask how proven repo-local autonomy artifacts could become market-facing proof, offers, demos, or lead magnets;
- ask for audiences, pains, concrete outcomes, proof artifacts, distribution hypotheses, and pricing hypotheses;
- ask what must remain human-approved release work.

Then implement repo-local market packaging only:

- `docs/marketed-value-lane.md` — stack from working loop → proof/demo → offer draft → human-approved release → market feedback → money;
- `docs/rubrics/marketed-value-rubric.md` — score audience clarity, pain intensity, outcome clarity, proof, distribution, safety/trust, revenue plausibility, and reusability;
- `templates/revenue-experiment.md` — offer/pricing/channel/validation template;
- `examples/revenue-opportunity-report.md` — proof-backed sample report using only repo-local artifacts.

Stop before any external release: no publishing, outreach, checkout/payment setup, purchases, third-party contact, or revenue/ROI promises without Karan.

## Stop-the-line boundaries even in Hermes-personal

- Secrets, OAuth material, cookies, provider credentials, or raw private exports.
- Global Hermes config, profile allowlists, sensitive tool access, third-party skill installs.
- Live/client/business systems, payments, DNS, deploys, external messages/posts/emails.
- Broad/costly external research without a concrete target artifact.
- Moving private memory, Hindsight, Obsidian, email, Discord, Telegram, or session exports into the repo.

## Useful/fun repo additions surfaced by the strategic notebooks

- Autonomy policy with landing tiers.
- Change rubric to separate useful work from busywork.
- Contract template for larger autonomous changes.
- Loop readiness score/audit script.
- Example scout reports and safe-fail simulation logs.
- Prompt harnesses such as “grill me”/adversarial spec review.
- Lightweight pattern library for reusable loops.
- Bounded external-research playbook: one NotebookLM query or a few public pages, distilled into a small artifact.
- Marketed-value lane: offer sketches, landing-page drafts, revenue experiment templates, and opportunity reports that package repo-local proof without external release.

## Premature loops to avoid early

- Autonomous lesson harvesting from Telegram/session history/Hindsight/Obsidian into the repo.
- Spec-drift cron when the repo has no `docs/spec.md` or product architecture surface.
- Full multi-agent builder/reviewer orchestration for small Markdown/checklist hygiene.
- Self-mutating provider/model/billing logic.
- Cross-repo dependency updates or client/live automations.

## Success metrics for the trial

- Zero unapproved global authority changes.
- Zero alerts when the repo is healthy.
- 100% of alerts include real command evidence.
- Autonomous landings are small, reviewable, and verified against GitHub.
- No secrets or private/raw exports enter the repo.
- At least one workflow discovered here is reusable in another repo/workflow.

## Reporting pattern

Final report should include:

- Notebooks queried and whether auth had to be refreshed.
- Live repo state checked and validator/audit result.
- Existing cron/job context.
- What was created/updated and why.
- Verification evidence, including remote SHA or merge-state checks if a repo mutation occurred.
- Explicit boundary statement for anything not touched.
