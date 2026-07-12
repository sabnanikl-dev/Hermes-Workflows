# NotebookLM → Obsidian Research Promotion Pattern

Use when Karan asks Hermes to query a specific NotebookLM notebook and turn the findings into durable workflow/product knowledge.

## Pattern

1. **Query the specific notebook, not a generic brain.** Use NotebookLM as the grounded synthesis layer for the named notebook/topic.
2. **Ask for actionable synthesis.** Prompt for principles, opportunities, next experiments, and product/workflow implications rather than a generic summary.
3. **Cross-check existing durable context.** Before writing, inspect the relevant Obsidian wiki pages/index and any existing lessons so the new page extends the knowledge graph instead of duplicating it.
4. **Promote only distilled durable knowledge.** Create/update a concise Obsidian wiki page when the output is reusable across future sessions. Do not dump raw NotebookLM answers or long citation JSON into the wiki.
5. **Preserve source traceability.** In frontmatter, cite the NotebookLM notebook and the durable upstream sources it synthesized when known.
6. **Update navigation and chronology.** Add the page to `index.md` when it belongs in the wiki catalog, and update the daily log if wiki state changed.
7. **Verify readback/search.** Read the created page and confirm it appears through Obsidian/search before reporting success.

## Output shape

A good promoted page has:

- Overview: why the synthesis matters.
- Durable principles: reusable rules, not session narrative.
- Workflow/product opportunities: concrete levers mapped to current systems.
- Small next experiments: bounded, verifiable trials.
- Related links: existing wiki pages/lessons/project dashboards.

## Pitfalls

- Do not create a new NotebookLM notebook unless the user explicitly asks; Karan prefers using specific notebooks as tools and Obsidian as memory.
- Do not treat NotebookLM as source of truth for live project state; verify current GitHub/Linear/repo status separately when making project recommendations.
- Do not save transient auth failures or expired cookies as durable negative rules. If auth refresh via browser cookies works, the durable lesson is the refresh/verification pattern, not that auth failed.
