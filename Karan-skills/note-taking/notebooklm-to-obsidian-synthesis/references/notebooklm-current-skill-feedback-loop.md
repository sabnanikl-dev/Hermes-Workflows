# NotebookLM Current-Skill Feedback Loop

Use this when Karan asks to share one or more current Hermes skills with a specific NotebookLM notebook for critique, leaning, or workflow improvement.

## Pattern

1. **Load the relevant skills first**
   - Load the NotebookLM workflow skill plus every skill being critiqued.
   - Prefer the current local skill files over stale prior NotebookLM sources.

2. **Refresh NotebookLM auth and identify the exact notebook**
   - Check auth first.
   - If expired, refresh from the approved Chrome profile/account.
   - List notebooks and source list before uploading.

3. **Upload current skill snapshots as text sources**
   - Large `SKILL.md` files may need to be split into parts.
   - Title sources with skill name + date, e.g. `Hermes autonomous-pr-prover current YYYY-MM-DD`.
   - Wait for every uploaded source to reach `ready` before querying.
   - Preserve source IDs in the final wiki note.

4. **Ask for operational critique, not generic summary**
   - Ask where the loop/procedure can be leaned out without weakening safety.
   - Require: ranked improvements, waste removed, smallest experiment, objective gate, stop condition, forbidden mutations, redundant recommendations, and do-not-build-yet items.

5. **Run a refinement pass**
   - Feed back a concise digest of current local constraints and what is already implemented in the skills.
   - Ask NotebookLM to mark recommendations as Adopt / Experiment / Reject and to say what should not be deleted.
   - This prevents generic advice like “use progressive disclosure” when the actual Hermes runtime loads full `SKILL.md` content.

6. **Promote distilled output**
   - Create/update a concise Hermes Brain note with source IDs, recommendations, guardrails, and concrete skill edit ideas.
   - Update index/log/daily log when durable wiki state changes.
   - Do not patch the critiqued skills automatically unless the requested task includes skill maintenance or the critique reveals a clear missing step.

## Pitfalls

- Do not rely on older NotebookLM skill bundle sources when the local skill has changed; upload a fresh dated snapshot.
- Do not accept NotebookLM recommendations blindly. Cross-check against the current skill text and local Hermes constraints.
- Do not preserve raw NotebookLM answers wholesale; distill into a durable note.
- Treat “leaning” as removing operator/context waste, not removing safety rails such as human approval, reviewer identity, PR-bus coordination, current-head verification, or fallback disclosure.
