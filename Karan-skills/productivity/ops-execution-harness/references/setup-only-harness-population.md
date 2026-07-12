# Setup-Only Harness Population Pattern

Use when Karan asks to clone/populate an ops harness but explicitly says not to complete the underlying ops task yet.

## Trigger Example
- "don't complete the task for now lets just clone the repo and populate the files for now"

## Correct Behavior
1. Clone the template into the target issue workspace.
2. Populate the required harness files (`task.md`, `context.md`, `constraints.md`, `playbook.md`, `skills/manifest.md`).
3. Add only lean task-relevant local checklists/skills.
4. Ensure `evidence/` and `outputs/` exist.
5. Create placeholder evidence/output files if useful, but label them clearly as not executed / not completed.
6. Verify the files and no-live-change approval rules.
7. Report that the harness is ready and ask before committing/pushing or executing the full audit.

## Placeholder Conventions
- `evidence/unavailable-evidence-note.md`: explain that evidence was intentionally not captured during setup.
- `outputs/<primary-deliverable>.md`: scaffold the expected structure and mark status as "template prepared, audit/research not executed yet".
- `outputs/final-linear-comment.md`: setup-pass draft only; do not post as a completion comment.

## Things Not To Do
- Do not run the downstream audit/research/outreach.
- Do not collect dashboard/API evidence unless that is included in the user's current scope.
- Do not mark Linear acceptance criteria as completed if the underlying deliverable is only templated.
- Do not imply placeholders are final evidence-backed outputs.
- Do not make live client/account/dashboard changes.

## Verification
- Required files exist.
- Required folders exist.
- Placeholder output states are unambiguous.
- Approval mode/no-live-change rules are present.
- Git status is reported without assuming commit/push is desired.
