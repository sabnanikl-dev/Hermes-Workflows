# Follow-up Implementation Issues After Approval/Scaffold PRs

Use this when a repo has a scaffold PR/issue and a later approval/data PR unlocks implementation work (example pattern: SEO/JSON-LD scaffold + verified business-data ledger).

## Pattern

1. Re-read the scaffold issue/PR body and any source-of-truth approval doc on `main`.
2. Identify fields now unblocked versus still deferred. Do not collapse all remaining work into one mega-issue.
3. Create a small number of focused implementation issues:
   - one issue to fill newly approved data into the scaffold/code;
   - one later issue for still-dependent metadata/assets/domain work, if applicable;
   - keep existing deferred stakeholder/content issues separate.
4. In each issue body, include:
   - context and source-of-truth file(s);
   - exact allowed fields to implement;
   - explicit `Must not implement` list for unverified/deferred fields;
   - dependency notes (e.g. scaffold PR must land first);
   - acceptance criteria grounded in validation, not vibes.
5. Before recommending builder skills, inspect repo-local staged skill guidance if present:
   - `skills/staged-external-skills.md`
   - `.hermes/skills/`
   - `AGENTS.md`
6. Suggest both local Hermes skills and staged external skill links. External skills should be framed as optional and source-reviewed before use.

## Safety gates

- Do not install external skills just because an issue mentions them.
- Do not broaden tool/profile allowlists as part of issue creation.
- Do not include live-account/DNS/deploy mutations unless the issue explicitly scopes them and approval exists.
- Keep repo docs/source of truth as the authority; do not make the issue body into a parallel tracker.

## Example issue sections

```markdown
## Context
<scaffold PR/issue> added the conservative scaffold. <approval PR/doc> now unlocks specific fields.

## Goal
Populate the scaffold with only approved fields.

## Approved fields to implement
- ...

## Must not implement in this issue
- ...

## Recommended builder skills
Local Hermes:
- `skill_view(name="...")`

Staged external skills from `skills/staged-external-skills.md`:
- [seo](...)

Safety: review external skill sources before use; do not blindly import commands/hooks/automation.

## Acceptance criteria
- ...
```
