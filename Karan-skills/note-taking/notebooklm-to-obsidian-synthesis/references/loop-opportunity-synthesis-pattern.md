# Loop Opportunity Synthesis Pattern

Use this reference when NotebookLM is asked to identify leverage loops, workflow opportunities, or operational improvements from a strategic/research notebook.

## Pattern

1. **Query broadly first**
   - Ask NotebookLM for principles, candidate loops/opportunities, actors, durable state, gates, stop conditions, risks, and smallest experiments.
   - Require source titles/citations.

2. **Cross-check live/current state outside NotebookLM**
   - Inspect current source-of-truth systems before accepting recommendations: Obsidian Project Status, relevant playbooks, cron/job list, Linear/GitHub/repo docs when applicable.
   - Identify what already exists, what is redundant, and which gaps are live/urgent.

3. **Run a second NotebookLM refinement pass**
   - Feed NotebookLM a concise current-state digest.
   - Ask explicitly:
     - Which loops are redundant because we already have them?
     - Which workflows are missing the highest-leverage loop component?
     - Rank the top opportunities with trigger, durable state, objective gate, stop condition, and forbidden mutations.
     - List tempting but low-ROI loops not to build yet.

4. **Hermes final synthesis**
   - Prefer low-risk, objective-gate loops before autonomous mutation loops.
   - Preserve human approval boundaries for merges, live/client-facing changes, account mutations, credentials, purchases, and public posts.
   - Promote a concise distilled note to Obsidian when the output is durable.

## Prompt fragment

```text
Using the notebook's loop-engineering principles and this current state, refine the recommendations:
1. Which loops are redundant because we already have them?
2. Which current workflows are missing the highest-leverage loop component?
3. Give a ranked top 5 with exact trigger, durable state, gate, stop condition, and what the loop is NOT allowed to mutate without approval.
4. Include a short 'do not build yet' list for tempting but low-ROI loops.
```

## Pitfall

Do not treat scheduled notifications as loops automatically. A cron that only reports is an automation; a loop needs a trigger, action, durable state, verification/gate, iteration or escalation behavior, and a stop condition.
