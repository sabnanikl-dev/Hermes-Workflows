# GitHub-visible claims and progressive acceptance sync

Use when a tracker acceptance slice drives one shared GitHub implementation issue/PR and Karan expects the coding lane to be visible in GitHub immediately.

## Make the claim visible before implementation

A local branch or isolated worktree is invisible to GitHub. Its issue Development panel becomes useful only after a remote branch is explicitly associated or a linked PR exists.

Default:

1. Re-read the live tracker issue, GitHub issue, duplicate search, repo/default branch, remote head, open PRs, and local worktrees.
2. Create the isolated local branch/worktree from the verified remote base.
3. When branch push is authorized, push the baseline branch immediately or create/link it through GitHub's issue branch action. Do not wait for the first implementation commit merely to avoid an empty branch: the remote claim is operational evidence.
4. Verify the remote ref and issue association. If the API cannot expose a direct branch association, open a draft PR as soon as the first coherent commit exists and use a plain closing keyword.
5. If policy requires local-first work, disclose that GitHub will show no branch until push/PR. Never imply the issue is GitHub-visible while only a local worktree exists.

The builder owns implementation commits and push handoff; Hermes independently verifies the remote SHA and PR linkage.

## Exact-head review and bounded repair

After the builder pushes:

1. Verify local HEAD = remote branch SHA = PR `headRefOid`; confirm the expected commit is in the PR list.
2. Run repository verification independently.
3. Launch a credential-free/read-only Codex review bound to that exact SHA. Require blocking findings with stable IDs, `file:line` evidence, and a machine-readable final marker.
4. When authorized, post/relay the review under the configured independent reviewer identity. Read back reviewer login, review state, and bound commit SHA.
5. Freeze the first blocker ledger. Route only that ledger to the original builder for a bounded repair cycle; do not restart an architecture tournament.
6. Any push invalidates the old verdict. Re-run review on the new exact head. Old-head `CHANGES_REQUESTED` evidence remains historical, not current approval.

Builder self-tests never replace independent review. Keep the draft blocked while exact-head blockers remain.

## Progressively synchronize tracker acceptance criteria

The tracker owns acceptance, not detailed coding execution. Check criteria when evidence becomes definitive rather than checking everything at closeout or optimistically at PR creation.

For each update:

1. Fetch the live full issue description immediately before editing.
2. Map each criterion to concrete evidence: implementation path, independently run command, remote/PR readback, or exact-head reviewer verdict.
3. Replace only the exact satisfied checkbox line(s), but submit the full description in one mutation.
4. Re-read the full description. Verify intended checked labels, remaining unchecked count, and unchanged unrelated text. Treat Linear `[X]` and `[x]` as equivalent; verify case-insensitively.
5. Keep behavioral/safety criteria unchecked while the exact-head reviewer has relevant blockers. Structural criteria (one shared issue/PR, untouched operational clone) may be checked earlier when independently proven.
6. Check the parent roll-up only after the child is fully accepted—not merely because a branch, draft PR, or builder test exists.

Do not mirror every commit/review into Linear. Use state, evidence comments, and acceptance boxes; GitHub remains the code journal.

## Verification checklist

- [ ] Remote claim is visible, or local-first invisibility was disclosed.
- [ ] Local, remote, and PR heads match before review.
- [ ] Reviewer verdict is bound to the exact head and read back under the expected identity.
- [ ] Old-head blockers are frozen and repaired without scope expansion.
- [ ] Tracker boxes reflect only verified evidence and were read back after every edit.
- [ ] Parent acceptance remains honest until the child is fully accepted.
