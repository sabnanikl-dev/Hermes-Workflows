# Mission Activation Wiring — Tracker Mutation Recipe

Session-specific detail from activating the JMD Visibility mission (2026-07-24). Reusable as a checklist when turning an approved mission contract into live tracker structure.

## Sequence that worked

1. **Freeze the contract first.** Compute SHA-256 of pre-freeze bytes; write it into frontmatter (`content-digest`), the approval banner, and the approval block; set `status: approved`. Only then touch the tracker.
2. **Create the mission-root issue** in the tracker's project, body carrying: contract path, revision, approved digest, project_id, operational-clone decision, definition-of-complete summary, authority envelope summary, supervisor startup contract. Set it to the team's active state (see state-by-type trap below).
3. **Re-parent everything.** Set `parentId` = mission root on every top-level in-scope issue. Then verify rollup chains for *transitive* children and hunt for **orphans** — in JMD, JMD-46 was parented to JMD-11, a stale backlog issue *outside* the project with no parent; it did not roll up. Fix: re-parent the child directly to the mission root (don't re-parent mid-level parents blindly — that can flatten structure the team intended).
4. **Encode hard dependencies as native `blocks` relations**, then verify from the *blocked* side via `inverseRelations` — the blocker's `relations` view alone can look empty/misleading.
5. **Two-way cross-system links.** Tracker issues get comments naming the repo issues + gates; repo issues get an appended mapping block naming the tracker issues + mission root. Append (fetch body → append → `--body-file`), never rewrite, and re-read to confirm. Prose mentions alone are not deterministic; use a consistent marker string (e.g. `Cross-system mapping (<mission> rev N §x)`) so future inspections can grep for presence.
6. **Draft fast-start issues** as children of the root: controller build stages with `blocks` chains between them, plus resume-first repair loops for already-open PRs. Give each acceptance criteria + a durable-knowledge DoD line.

## Linear state-by-type trap (real mistake this session)

Teams can have **multiple workflow states of the same `type`** — e.g. JMD team has both "In Progress" and "In Review" as type `started`, plus "Triage" and "Ready" as type `unstarted`. Selecting the *first* state matching a type put the mission root in "In Review" instead of "In Progress". Always list the team's states (ordered by `position`) and pick the **named** state you intend; never index by type alone.

## Verification pattern

After all mutations, one readback script: mission root children list, `inverseRelations` on each blocked issue, direct `comment(id:)` lookup for each evidence comment (never trust `comments(last:1)` ordering), and `gh issue view --json body` grep for the mapping marker on each linked repo issue.
