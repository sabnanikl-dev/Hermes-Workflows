# Mission Plan Capture Checklist

Use when the user asks to preserve a proposed cross-system mission architecture without implementing it.

## Required Sections

1. **Proposal-only warning**
   - State that the note does not authorize tracker cleanup, scripts, automation, cron jobs, repository work, merges, deploys, DNS, account changes, or client-facing communication.

2. **Overview and target user experience**
   - Include the natural-language mission command.
   - Describe what the controller should do after that command.

3. **Current context**
   - Separate observed current capabilities from missing control-plane capabilities.
   - Name source-of-truth boundaries.
   - Avoid copying live issue lists into the wiki; trackers own current status.

4. **Existing capabilities**
   - Live-system tools.
   - Specialist profiles/roles.
   - Relevant execution, review, and knowledge skills.
   - Hardened launchers and known wiring requirements.

5. **Authority envelope**
   - Routine autonomous actions.
   - Explicit human-only actions.
   - Decision-ready pause format.

6. **Proposed architecture**
   - Mission root/manifest.
   - Read-only inspector and deterministic outcomes.
   - Cross-system mapping contract.
   - Bounded execution state machine.
   - Durable supervisor.
   - Natural-language trigger skill if useful.

7. **Tracker preparation**
   - Reconcile stale open/completed state.
   - Resolve conflicting active work.
   - Add real dependencies and mappings.
   - Separate parent trackers from executable children.
   - Mark human/live/account gates explicitly.

8. **Routing and verification**
   - Route each class of work to the least-privilege role-native worker.
   - Require independent review and direct readback.
   - Include durable-knowledge closeout.

9. **Phases**
   - Contract freeze.
   - Tracker normalization.
   - Inspector and fixtures.
   - Runner.
   - Durable supervision.
   - Low-risk dogfood.
   - Full activation after acceptance.

10. **Evaluation**
    - Fixture matrix.
    - Runtime smoke tests.
    - Acceptance criteria grouped by contract, sequencing, execution, verification, continuity, knowledge, and safety.

11. **Risks, non-actions, and recommendation**
    - Name predictable failure modes and mitigations.
    - Explicitly state what not to build or mutate yet.
    - Recommend the smallest focused control-plane layer rather than more generic agents.

## Wiki Hygiene

- Use draft frontmatter for unapproved proposals.
- Put reusable plans in the user-named domain folder.
- Add lightweight index navigation when catalog-worthy.
- Update the activity log and current daily log when wiki state changes.
- Verify file existence, final newline, no trailing whitespace, link targets, and index/daily-log size budgets.
- Report exact path and explicitly confirm that no project or tracker implementation occurred.
