# NotebookLM Profile Operating Model Audit Pattern

Use this when Karan asks to add a current-state source to a specific NotebookLM notebook, then query that notebook for optimization/recommendations.

## Trigger

Requests like:

- "Create a new source in the Hermes Profiles NotebookLM detailing our current profiles... then query it."
- "Audit our configured Hermes profiles and ask NotebookLM how to optimize them."
- "Add the current state to NotebookLM first, then ask it for recommendations."

## Procedure

1. **Identify the exact notebook**
   - Check NotebookLM auth.
   - List notebooks.
   - Select the named notebook by title/id.
   - List existing sources before adding anything.

2. **Ground the source in live Hermes state**
   - Inspect configured profiles with `hermes profile list` and `hermes profile show <profile>`.
   - Read profile SOUL files and profile-local skill lists/summaries.
   - Check profile usage signals if useful: session DB counts, Kanban stats/history, current ready/running tasks.
   - Avoid reading or preserving secrets from `.env`, auth files, cookies, tokens, or credential stores.

3. **Write a concise source artifact**
   Include:
   - purpose of the source;
   - verification snapshot and commands used;
   - profile-by-profile purpose/current use/not-use/better-use;
   - cross-profile strengths/gaps/risks;
   - recommended operating model;
   - explicit open questions for NotebookLM.

4. **Add it as a NotebookLM text source**
   - Prefer `source add --type text --title ...` for generated Markdown content.
   - For long content, pass the content via a small local Python/subprocess wrapper or prompt file approach rather than fragile shell quoting.
   - Then run `notebooklm source wait -n <notebook_id> <source_id> --timeout ... --json`.
   - Verify `source list` shows the new source as `ready`.

5. **Query the notebook after the source is ready**
   Ask for an operator playbook, not generic docs. Useful answer shape:
   - top 5 optimization moves;
   - routing decision tree;
   - profile-by-profile recommendations;
   - Karan interaction phrases;
   - delegation templates;
   - low-risk experiment;
   - what not to automate.

6. **Report verification and synthesis**
   Final answer should include:
   - notebook name;
   - source title/id/status;
   - local artifact path if created;
   - key NotebookLM recommendations;
   - any proposed live mutations that still need Karan approval.

## Pitfalls

- Do not query the notebook before the new source is `ready`; NotebookLM may answer from stale sources.
- Do not dump raw profile files wholesale. Curate them into an audit source that NotebookLM can reason over.
- Do not include secrets or environment-specific credential material.
- If NotebookLM suggests live config/profile changes, treat those as recommendations only. Default Hermes/Karan approval is still required before changing SOULs, profile descriptions, models, skills, or tool access.
- If a protected/bundled skill would be the ideal place to encode a lesson, do not edit it; update the nearest user-owned umbrella or add a reference instead.
