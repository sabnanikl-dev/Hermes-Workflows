# Exact-Head Blocked PR Handoff

Use this reference when a GitHub implementation PR is governed by a Linear issue, exact-head review remains blocking, and the authorized repair budget is exhausted or the human chooses to keep the PR blocked.

## Distinguish mechanical and accepted state

GitHub `MERGEABLE` / `CLEAN` is mechanical merge information only. A PR is not review-ready or merge-ready when current-head reviewer artifacts still contain confirmed blockers, the PR is draft, required checks are missing, or human feedback remains unresolved.

Write both states explicitly:

```text
GitHub mechanics: MERGEABLE / CLEAN
Acceptance state: BLOCKED by <count> exact-head findings
```

Do not move the Linear issue to Done or check affected acceptance criteria merely because tests pass or GitHub reports a clean merge base. Preserve `In Progress` while mandatory review or behavioral evidence remains open.

## Blocked closeout sequence

1. Freeze the full current PR SHA.
2. Finish and publish the authorized exact-head reviewer evidence.
3. Verify each artifact by direct readback:
   - formal review: author, state, exact GitHub `commit_id`, body marker, URL;
   - conversation artifact: author, role, canonical head marker, verdict, URL.
4. Verify local branch SHA = remote branch SHA = live PR `headRefOid`.
5. Record full test/check/smoke results and worktree cleanliness.
6. Keep the PR open/draft; do not merge or mark ready.
7. Update the PR body from stale “delivered/review pending” language to current blocked status, current-head artifact links, and the exact remaining ledger.
8. If the human says to keep it blocked, stop implementation and write a Linear handoff comment.
9. Verify the Linear comment by the returned comment ID with a direct `comment(id:)` readback; never rely on comment list order.

## Linear handoff contents

A useful handoff includes:

- repository and PR link;
- frozen exact head;
- Linear issue and preserved state;
- mechanical GitHub state versus review/acceptance state;
- real verification results and installed-adapter/smoke evidence;
- Reviewer A, Reviewer B, and Integration artifact URLs/counts;
- one frozen unique blocker ledger;
- repair-cycle and exception budget consumed;
- explicit human decision to stop/keep blocked;
- exact resumption contract;
- explicit statement that no merge, ready-marking, deploy, or branch deletion occurred.

## Resumption contract

When the work is later reauthorized:

1. Treat the frozen blocker ledger as the only repair scope unless the human approves expansion.
2. Use a fresh isolated builder lane and produce a new exact head.
3. Re-run the complete repository suite, focused former-red probes, compile/static/config/diff checks, and real adapter smoke.
4. Treat every old-head review artifact as historical.
5. Run fresh exact-head Reviewer A, Reviewer B, and Integration Auditor lanes.
6. Preserve the merge gate; technical readiness is not merge authority.

## Adversarial contract-boundary probes for trusted-agent control planes

When the implementation itself decides merge readiness, ordinary tests are necessary but insufficient. Include probes for:

- **Acknowledgement chronology:** a pre-existing acknowledgement targeting a future feedback ID must not clear later feedback; ordering requires immutable timestamps, not list order or ID shape.
- **Top-level GraphQL completeness:** reject partial-data errors, null/missing connections or nodes, invalid page metadata, and a final captured page that still says `hasNextPage`.
- **Artifact-level identity:** do not ignore an entire shared publishing login; only validated builder/reviewer artifacts are agent output, while other posts from the same account remain human feedback.
- **Required role order:** if the contract requires A, B, then Integration Auditor, reject no-auditor and auditor-first configs at the schema/public-loop boundary.
- **Fail-closed setup:** configured worktree/scratch/artifact root failures must become sanitized stable results rather than raw filesystem exceptions.

These probes are contract classes, not a reason to build a generic policy framework. Keep fixes narrow and repository-specific.
