# Fallback builder disclosure + doc-stewardship closeout

Session pattern from JMD issue #143 / PR #149.

## Trigger

Use this when the intended builder lane (usually Claude Code) starts correctly but hangs/timeouts after producing a partial local draft, and the approved degraded builder lane also fails to make progress.

## Durable lessons

1. **Do not silently relabel direct Hermes completion as a clean builder-lane pass.**
   - If Claude Code timed out/hung after making a draft and Hermes finishes the implementation directly, disclose that in the PR body and final report.
   - Use wording like: `Hermes completed the repo-side implementation directly after Claude Code and builder-profile fallback hung/timed out.`
   - Treat this as technically reviewable work, but **not** clean dogfood evidence for the multi-agent builder loop.

2. **A partial draft from a hung builder can be salvaged only with explicit provenance.**
   - Inspect `git status`, diff, and generated files.
   - Keep/fix/revert the draft as normal implementation input.
   - The final PR must say which lane actually finished the work.

3. **Doc-stewardship blockers are common when an issue turns “future work” into current architecture.**
   - After landing a new endpoint/data path/controller, search nearby component docs for language like “future issue”, “future CMS path”, “TODO when #N lands”, or “owned by #N”.
   - Update those docs in the same PR so future builders don’t treat landed behavior as still unbuilt.
   - If a reviewer flags stale docs, patch the source doc, rerun tests, push a follow-up commit, comment with exact verification, and rerun the same reviewer lane.

4. **Reviewer process hangs are not a pass.**
   - If a reviewer process runs too long with no useful progress after a sibling reviewer has already produced a blocker, kill it rather than claiming review completion.
   - Fix known blockers, push, verify PR head, then rerun reviewer lanes against the current head.

## Closeout checklist for this fallback shape

- [ ] PR body explicitly discloses fallback/direct-completion provenance.
- [ ] Local tests/build passed after the final direct/fallback commit.
- [ ] Push verified by matching local `HEAD` to PR `headRefOid`.
- [ ] Reviewers rerun on the latest head, not the stale pre-fix head.
- [ ] GitHub review objects/comments verified for role signatures on the latest `headRefOid`.
- [ ] Any stale “future work” docs updated before merge-readiness is reported.
