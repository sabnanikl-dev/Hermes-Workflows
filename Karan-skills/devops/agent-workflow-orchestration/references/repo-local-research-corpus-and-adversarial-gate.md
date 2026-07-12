# Repo-local research corpus + adversarial gate pattern

Use when a repo-local autonomy experiment has recurring crons that previously queried an external research tool (NotebookLM, notebooks, docs workspace, etc.) and Karan asks to make the repo self-contained and faster.

## Trigger
- User asks to capture prior external research into repo documents.
- User wants scheduled runs to stop querying the external research source every run.
- User delegates a human approval gate to an adversarial/reviewer loop.
- User asks for repo-local skills to be used by crons instead of global Hermes skills.

## Workflow
1. **Create repo-local research corpus**
   - Add `research/README.md` explaining that routine crons read the repo corpus instead of live external research.
   - Add one distilled file per source/notebook/topic, e.g. `research/aios.md`, `research/strategic-engineering.md`, `research/ai-money.md`.
   - Capture durable principles, current synthesis, already-applied repo translations, cron decision rules, and anti-patterns.
   - Do not commit raw NotebookLM/chat transcripts or private memory/session exports.

2. **Vendor repo-local skills as files, not global skills**
   - Put imported skills under the repo's `skills/` tree.
   - Update `skills/manifest.md` with trigger rules and paths future crons should read directly.
   - Strip vendored trailing whitespace if repo validators enforce clean markdown.
   - Keep third-party license/readme files where practical.

3. **Change prompts/docs/validators together**
   - Update cron prompts and repo docs so the new source of truth is `research/`, not live NotebookLM.
   - Patch local validators/audits that still expect old phrases like “NotebookLM grounding every run” or old human-approval language.
   - Update product/governor docs that could otherwise keep instructing future crons to wait for manual approval.

4. **Reconfigure scheduled jobs, not just repo files**
   - Use `cronjob(action='list')` to identify exact job IDs.
   - Update each relevant Hermes-personal experiment cron prompt so it:
     - reads `research/*.md`;
     - states live NotebookLM queries are not used during routine runs;
     - reads repo-local skill files for public-output work;
     - reads the latest adversarial report before public/live action;
     - reports the research corpus and adversarial gate state in final output.
   - For script-only review jobs, update the script and the cron prompt/schedule.

5. **Adversarial review as delegated approval gate**
   - Make the reviewer output a machine-readable/grep-friendly clean decision such as `READY_FOR_PUBLIC_LIVE`.
   - Downstream crons may proceed only when the latest report explicitly says no blocking findings and ready for public-live movement.
   - Preserve hard stops even after a clean review: bank/tax/KYC, paid purchases, credential/CAPTCHA/phone/passkey/account recovery, private/client data, unsupported revenue/ROI/legal/compliance claims, unrelated accounts/repos, and global Hermes/profile/tool authority changes.

6. **Verify both repo and scheduler state**
   - Run repo validators and `git diff --check`.
   - Inspect cron job prompts/config directly for live-command patterns, e.g. `/notebooklm ask|notebooklm auth|NotebookLM grounding every run/`.
   - Verify the adversarial script syntax with `bash -n` when changed.
   - Commit/push repo changes and verify remote HEAD equals local HEAD.

## Pitfalls
- Updating only prompts but not validators leaves false failures that pressure future agents to restore outdated behavior.
- Updating only repo docs but not `~/.hermes/cron/jobs.json`/cron job prompts means scheduled runs keep old behavior.
- Treating a clean adversarial review as unlimited authority is wrong; keep hard blockers explicit.
- Do not encode transient NotebookLM/API failures as a durable “tool is broken” rule. The durable rule is: once findings are captured in repo, routine crons read the repo corpus unless Karan asks for a manual refresh.
