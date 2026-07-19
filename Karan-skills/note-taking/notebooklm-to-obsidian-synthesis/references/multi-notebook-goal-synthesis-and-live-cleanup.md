# Multi-Notebook `/goal` Synthesis and Live Cleanup

Use when Karan asks several NotebookLM notebooks to design a Hermes `/goal`, operating loop, or orchestration plan.

## Workflow

1. **Identify exact notebooks and inspect sources.** Query each notebook separately; do not blend them before they answer.
2. **Give every notebook the same current-state digest.** Include the desired queue, dependencies, approval gates, source systems, and output schema. NotebookLM cannot see live Linear/GitHub/repo state.
3. **Ask for one ready-to-paste `/goal`.** Require mission, source-of-truth rules, dependency lanes, approval boundaries, delegation/review expectations, deterministic evidence, stop conditions, durable-knowledge closeout, and completion criteria.
4. **Use the compact/plain retry pattern.** If a long JSON ask returns `No parseable chunks in streaming chat response`, compress the prompt to roughly 1–3 KB and retry in plain-text mode. Preserve the critical path and gates; report the retry honestly.
5. **Synthesize outside NotebookLM.** Extract consensus and useful differences rather than selecting one answer wholesale.
6. **Revalidate live state before cleanup.** Re-read Linear, GitHub issues/PRs, current PR heads/checks/reviews, repo architecture, and the actual Hermes role/profile workflow.
7. **Remove notebook inventions.** Common examples:
   - roles/profiles that do not exist (`QAS`, `RTE`, `BSA`, `TDM`);
   - wrong integration paths such as “Linear MCP” when the environment uses the Linear API skill;
   - wrong stack assumptions (for example Next.js when the repo is static HTML on Vercel);
   - unrelated brand constraints copied from another project;
   - automatic merge/deploy/account authority not granted by the human;
   - arbitrary timeout/escalation rules unsupported by the real workflow.
8. **Resolve dependency circularity.** If a checklist spans pre-cutover and post-cutover proof, split it into readiness and post-action sections rather than requiring full completion before the action it verifies.
9. **Match the actual agent workflow.** For current JMD repo coding: Hermes integrates/verifies, Claude Code builds/fixes, current required Codex reviewer lanes evaluate the live PR head, and Karan retains final merge/live authority unless explicitly delegated.
10. **Return one clean artifact.** Prefer the final `/goal` only, with no raw notebook transcript unless Karan asks for it.

## Quality checks

- Linear/GitHub remain execution truth; Obsidian receives durable summaries only.
- Every status transition has tool-verifiable evidence.
- Pushes and merges require live remote readback.
- Non-critical lanes cannot consume migration-critical capacity.
- Live/client/account/DNS/deploy actions retain explicit approval gates.
- The goal has milestone-aware completion when monitoring continues after launch.
