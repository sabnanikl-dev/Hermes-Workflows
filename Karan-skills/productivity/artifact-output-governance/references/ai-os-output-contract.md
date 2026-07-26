# AI OS Output Contract — Condensed Reference

## Source themes

This reference condenses durable output-handling guidance from the AI OS NotebookLM source set. It is not a raw notebook transcript.

- **The 3-File AI System That Works With ANY MODEL** — externalize purpose, operating context, and next actions into portable artifacts rather than relying on model memory.
- **llm-wiki** — preserve useful knowledge with source links and structure so it compounds across sessions.
- **Harness design for long-running application development** — leave clear progress, verification, and recovery state that a fresh session can reconstruct.
- **SAW — SAFe Agentic Workflow AI Agent Harness** — bind completion to evidence and independent gates rather than self-reported success.
- **OTR Analytics Agent: HTML Slide Deck Generation Framework** — artifact quality must be judged in the medium and for the audience that will consume it.

## Artifact verification matrix

| Artifact | Minimum real-form verification | Common false proof |
| --- | --- | --- |
| Markdown/text document | Read back final content; inspect headings, links, sources, and audience fit | File exists |
| DOCX/PDF | Render/open; inspect layout, pagination, text, metadata, and links | Text extraction alone |
| Image/diagram | Visual inspection; dimensions, format, legibility, placement, alt/context | Image file opens |
| Spreadsheet | Open workbook; inspect sheet names, formulas, types, representative calculations, export | Row count only |
| Presentation | Render slides; inspect overflow, ordering, hierarchy, citations | Source file parses |
| Script/CLI | Execute safe happy/failure fixtures; verify exit codes and resulting state | Syntax check only |
| Dataset/report | Validate schema, counts, deduplication, provenance, edge cases | Non-empty file |
| External object/write | Capture ID/version and directly read back exact content/state | Mutation returned HTTP 200 |
| Research/finding | Trace claim to source span/URL/time; label inference and limits | Plausible prose |

## Lifecycle classes

- **Ephemeral evidence:** temporary run material used to prove execution. Promote a redacted result, then delete or de-authorize the temporary artifact.
- **Ticket-specific deliverable:** useful for this issue but not a reusable knowledge asset. Keep in the approved project location and link it from the tracker.
- **Reusable project asset:** a template, script, report, dataset, or artifact intended for repeated use. Place in the canonical project system and index it in an existing map when one exists.
- **Durable knowledge:** stable, source-backed business/project knowledge worth preserving across sessions. Promote conservatively to Hermes Brain/Obsidian with exact path/readback.

## Output inventory template

```markdown
## AI OS output inventory

| Output | Intended user / decision | Type | Canonical path, ID, or URL | Provenance/version | Verification/readback | Lifecycle | Approval/publication status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

## Linear issue insertion checklist

For an output-producing Linear issue, ensure its body or execution packet names:

- [ ] expected outputs and their intended users;
- [ ] appropriate formats rather than blanket Markdown;
- [ ] canonical destinations;
- [ ] provenance and version requirements;
- [ ] artifact-specific verification/readback;
- [ ] independent acceptance gate;
- [ ] output inventory at closeout;
- [ ] lifecycle and conservative knowledge-promotion rules;
- [ ] fresh-session discoverability;
- [ ] privacy and exact-version public/client approval gates.

Suggested acceptance criteria:

```markdown
- [ ] Every material output appears in the AI OS output inventory with purpose, type, canonical locator, provenance, real-form verification, lifecycle, and approval status.
- [ ] No accepted output exists only in chat or a temporary run folder.
- [ ] A fresh reviewer can locate, understand, exercise, and judge every final output from tracker links without session history.
- [ ] Public/client-facing actions remain blocked until the exact artifact version receives human approval.
```

## Distillation guardrail

Do not copy NotebookLM responses wholesale. Translate source-backed ideas into live-system invariants. In particular:

- “portable files” does not mean every artifact must be `.md`;
- “independent QA” does not require a role with a specific name;
- “discoverability” does not require creating a duplicate index;
- “compounding knowledge” does not mean promoting transient task material;
- “human-in-the-loop” does not authorize a live action merely because an issue exists.

When notebook advice conflicts with current tracker, source-of-truth, or approval boundaries, preserve the boundary and encode the narrower invariant.