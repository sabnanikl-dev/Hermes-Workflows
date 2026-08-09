# Commission a Backlog Linear coding child into GitHub execution

Use this when Karan says “work on `<Linear ID>`” and the live Linear child is still Backlog because it requires a linked GitHub implementation issue before coding.

## Authority interpretation

- Re-read the live Linear body first. An issue’s historical note that “creating this issue does not authorize coding/publication” remains true for the earlier creation event.
- A new, direct instruction from Karan to **work on that exact child** is fresh task authority for the bounded repository implementation workflow: create the required GitHub issue, branch/PR, tests, and repository-scoped review artifacts.
- It does **not** silently authorize merge, tag, release, install, deploy, force-push, client/live/account mutation, credentials, purchases, or public/client communication. Preserve those gates.
- If the target repo or intended implementation boundary is ambiguous, stop and ask. Do not treat “work on” as authority to guess a repository.

## Commissioning sequence

1. **Reconstruct live state**
   - Read the complete Linear child, parent, comments, relations, current state, and explicit prerequisite language.
   - Inspect the target repo identity, `origin/main`, operational-clone cleanliness, worktrees, repository instructions, current issues/PRs, and likely implementation seams.
   - Inspect the incident/pilot artifacts named by the Linear issue when they define the defect. Convert them into acceptance evidence, not copied chat lore.

2. **Create the GitHub implementation contract**
   - Search for duplicates and adjacent completed/open work.
   - Create one agent-ready GitHub issue grounded in the current default-branch SHA and exact repo files/tests.
   - Link the Linear source, incident evidence, scope, negative cases, authority boundaries, required commands, and fresh-session reconstruction criteria.
   - Re-read the issue with `gh issue view`; creation output alone is not proof.

3. **Make authority and source boundaries durable in Linear**
   - Update the current Linear body to replace the pending-destination text with the exact GitHub issue URL.
   - Record that Karan’s new instruction authorizes the bounded issue/branch/PR/review workflow while merge/install/release/live gates remain separate.
   - Preserve the rest of the body and acceptance criteria; do not rewrite the mission merely to make it executable.
   - Read the body back and verify the exact link, authority sentence, state name/type, and unchanged safety gates. Expect Linear Markdown normalization.

4. **Publish a revision-bound claim**
   - Include: run ID, Linear ID, current body digest, GitHub issue URL, baseline SHA, execution lane, allowed outputs, forbidden effects, start time, and next checkpoint.
   - Capture the returned Linear comment ID and verify it directly with `comment(id:)` plus author/body readback.
   - A local claim file is preparation only; the verified Linear comment is the durable claim.

5. **Advance to active execution**
   - Once the prerequisite GitHub issue exists and the new user instruction supplies authority, move the child to `In Progress` rather than parking it in `Ready` while work is already starting.
   - Re-read state as both name and type. Do not claim active work from the mutation response alone.

6. **Create visible GitHub pickup**
   - Prefer `gh issue develop` from the verified default-branch head.
   - Verify issue association and the remote ref separately.
   - Create one isolated tracking worktree from that remote branch; verify the worktree’s branch and head inside the new worktree (not from the operational clone’s cwd).
   - Launch the builder only after the linked issue, baseline, remote branch, worktree, and authority packet all agree.

## Bug/pilot hardening issue quality

When the source is a failed real-world pilot:

- Preserve what worked, what failed closed, and which later stages were never reached.
- Distinguish repository-owned product seams from pilot-only wrappers/config/scripts.
- Turn the observed mismatch into one end-to-end contract: adapter output channel, prompt grammar, parser expectations, artifact validation, and failure behavior must be tested together.
- For visual evidence, separate artifact existence/integrity from semantic proof. Screenshots/PDFs can be human evidence while the configured repository gate proves required print content, mobile labels, and contrast/accessibility semantics.
- Avoid moving client-specific semantics into a generic orchestrator. Keep them in operator/repository-owned gates and add contract-level proof that existence alone is insufficient.

## Verification checklist

- Linear source and parent re-read live.
- GitHub issue exists, is unique, and was re-read.
- Linear body links the exact GitHub issue and records the bounded fresh authority.
- Claim comment verified by immutable comment ID and expected author.
- Linear state verified as `In Progress` / `started`.
- Remote issue-linked branch exists at the intended baseline.
- Isolated worktree is on that branch and baseline.
- Merge/tag/install/deploy/live gates remain explicitly unapproved.
