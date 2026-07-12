# NotebookLM Artifact Feedback Loop

Use this when Karan asks to send an existing plan/report/artifact back to one or more specific NotebookLM notebooks for critique, then revise the artifact.

## Pattern

1. **Extract a compact review payload from the artifact**
   - For HTML, strip `script`/`style` and extract headings, paragraphs, table text, and pre blocks.
   - If the extracted artifact is long or NotebookLM returns an empty/parse error, retry with a short structured summary rather than pushing the whole artifact again.
   - Preserve exact artifact path and current version in the prompt.

2. **Query each notebook independently**
   - Use a separate prompt per notebook, tailored to the notebook's perspective.
   - Ask for: missing pieces, risks, misalignment, overbuilt/under-specified areas, and a prioritized patch list.
   - Keep outputs separate so the final artifact can label which feedback came from which source.

3. **Patch the artifact visibly**
   - Add a concise section such as `NotebookLM Feedback Incorporated`.
   - Include the source notebook names, major critiques, and concrete patch decisions.
   - Do not bury the feedback only in prose; make it auditable with tables/checklists.

4. **Use adversarial review after NotebookLM synthesis when requested**
   - Run separate reviewer lanes where available.
   - Treat external-agent summaries as self-reports; preserve exact blocker counts/verdicts when they are useful.
   - If a requested reviewer lane is blocked by auth/setup, do not fake it. Record the blocked lane as an implementation preflight finding and say a true review remains pending after auth is repaired.

5. **Verify the revised artifact**
   - Deterministically check required sections/terms exist.
   - Render locally when it is HTML and check console/layout.
   - Stop preview servers before handoff.

## Pitfalls

- NotebookLM may return `No parseable chunks` or empty streaming output for oversized prompts. Retry with a shorter structured summary of the artifact.
- Do not claim two independent adversarial reviews if one lane could not run. Use honest wording such as `Codex review completed; Claude review blocked by auth`.
- Keep NotebookLM feedback and adversarial feedback separate; NotebookLM is research synthesis, adversarial agents are execution risk review.
