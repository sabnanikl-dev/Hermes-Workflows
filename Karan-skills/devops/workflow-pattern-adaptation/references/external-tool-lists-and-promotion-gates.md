# External tool lists and promotion gates

Depth for two recurring shapes: (a) a social post listing many repos/"skills" to evaluate, and (b) deciding whether an experimental local component (e.g. a model-based advisor) should become a default.

## (a) Many-repo social lists
1. `web_extract` the post; read replies too — they often add the most relevant item.
2. Resolve shortened links by HEAD redirect in one loop (`curl -sI -m 10 https://t.co/<id> | grep -i '^location'`); never infer repo from a name.
3. Grep the canonical wiki page for each name first; report overlap and research only new entries.
4. Batch `gh api repos/<o>/<r>` (description, stars, created, license) + `gh api repos/<o>/<r>/readme -H 'Accept: application/vnd.github.raw'` in one `execute_code` loop; page the spill file instead of re-running.
5. Classify each: actual form (plugin/MCP/CLI/demo), whether it truly depends on the named tech (created before the tech launched = unrelated), license (none = no reuse), and what its README concedes (simulation vs measured, experiment, limits). Stars = attention, not quality.
6. Flag install hazards: `curl | sh`, auto-registration across agent clients, installers writing keys into every Hermes profile `.env` or enabling plugins fleet-wide, per-turn model overrides. Review such repos read-only by cloning into the scratch dir.
7. A same-named external repo is not our local project — say so.
8. Wiki write-up: immutable excerpts in `raw/shared/<topic>-research-<date>/`; one section on the existing canonical page with a `# | Project | README says | Our read` table, a hazard callout, 2–3 takeaways ending in "no adoption decision"; sources, `updated:`, `log.md`, daily log; read back.
9. "Any of these useful to us?" → lead with the honest verdict (usually "very little"), rank worth-a-look items tied to a concrete weak spot of ours, one-line skips with reasons, and one bounded read-only next step awaiting approval.

## (b) Promoting an experimental component to default
Karan's rule: use it more by default only once proven better for us; not promoted before proof.
- **Baseline against the current unaided behavior**, not revision-vs-revision. Three arms on one frozen set: current default, current experiment, candidate.
- **Fix coverage before tuning precision.** A curated subset catalog silently caps recall for everything omitted; rank the full real library and report anything dropped by caps.
- **Diagnose where misses originate.** If the right candidate never reached the shortlist, widen first-stage recall (e.g. more finalists); verification thresholds cannot recover omitted candidates. Keep a verification stage that catches confidently-wrong first-stage picks.
- Add free local guards (skip trivial acknowledgement turns; refuse/redact secret-, contact-, card-shaped input) instead of relying only on manual sanitization.
- Weigh third-party scorecards by sample size and who wrote the labels; borrow mechanics, not conclusions. Don't adopt tricks (e.g. option-order averaging) that published measurement showed can amplify a wrong majority.
- **Fresh blind holdout per tuning round**; a seen holdout is retired. Realistic sanitized task shapes incl. compound multi-skill tasks; freeze labels and the pass bar before live calls.
- **Rollout ladder, each rung separately approved:** offline eval pass → shadow logging (suggestion vs what was actually used; needs a hook → ask) → nonbinding default hint → never binding/blocking.
- Offer the plan as numbered steps with explicit cost/network scope, and ask approval for the first bounded tranche.

### Running the comparison (execution recipe)
1. **Pre-register first.** Write `<PROJECT>/…_EVAL_PLAN.md` with arms, metrics, and numbered pass gates (candidate beats current experiment; adds value on top of unaided default; could replace default — report-only) *before* any candidate live call. The negative-result wording goes in the plan too, so a failed gate is reported rather than tuned away.
2. **Build the candidate beside the installed version** (new module + tests; reuse v1 transport/validation by import). Leave the installed skill/adapter untouched until gates pass — the baseline arm must still be the real current behavior.
3. **Sanitize what leaves the machine at build time**: build the full catalog through the host's own enable/platform filters over the local root only, and apply a deterministic redaction map (client/person names → readable placeholders like `EventCo`, vault paths → generic). Grep the output for the originals and eyeball phrasing — naive substitution produces garbage like "a … client client engagement". Add a unit test asserting no original names remain.
4. **Label authorship is blind and two-person.** One subagent writes the holdout seeing only the catalog file (explicitly forbidden from reading code/results/evidence), with `required`, `required_any` groups for genuine near-duplicate skills (any one satisfies), `acceptable`, category, one-line note. A second blind subagent audits it and emits `must_fix|suggest` changes without editing the file. Before any arm has run, apply the audit changes: all must_fix, plus any suggest items that only widen `acceptable`/`required_any` for genuine near-duplicate or umbrella skills. No model output has been seen at that point, and missing near-duplicates are the most common mis-score. Log each change as old/new, then record the fixture SHA256 and commit to freeze it. After runs, never relabel; report disputed labels instead.
5. **Pre-check the holdout against the candidate's local gates** (trivial-turn skip, sensitive-input refusal) so no case is silently short-circuited, and for leaked names/URLs.
6. **Arm for the unaided default** = a blind subagent given the production-style skill index (names + truncated descriptions), no labels/candidate output; returns `{case_id: [skills]}`.
7. **Score deployment value, not just accuracy:** compute the union (default ∪ candidate hint) and report required occurrences recovered that the default missed plus noise added on tasks the default got fully right. That, not standalone recall, decides whether a hint is worth shadow mode.
9. **Interpret honestly.**
   - Read the replace-default gate separately from the add-a-hint gate. A candidate can fail replacement and still pass as a complement; say which.
   - A gate passed at exactly its threshold is suggestive, not proof. State the margin in cases, and propose real-traffic shadow logging rather than promotion.
   - Name where residual misses cluster (typically the second skill on compound tasks).
   - Mark the holdout exposed.
10. **Pause/closeout.**
    - Commit results (`…_RESULTS.md` + rows) in the project.
    - Put a durable summary page in the topic folder under Hermes Brain `wiki/shared/research/<topic>/`. Move the related research page into that folder, and fix path-explicit wikilinks in logs and in skill provenance files.
    - Mark the page's status `paused` with the next unapproved step.
    - If listing the pages would push `index.md` past 3,000 chars, point the index at the folder.
- **Before step 7's full run:** smoke the runner offline (keyword arm + tiny fixture) and do a 1–2 task live smoke saved to `evidence/` before the full run; record resolved model IDs and provider-reported cost per call (missing = unknown, not zero).
