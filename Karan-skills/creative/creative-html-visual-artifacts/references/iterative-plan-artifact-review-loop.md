# Iterative Plan Artifact Review Loop

Use when producing a high-stakes standalone HTML plan/report that will later drive real operations, especially filesystem cleanup, agent harnesses, migrations, or workflow changes.

## Pattern

1. **Build the first real artifact**
   - Create a standalone HTML file with clear sections, tables, risk matrix, implementation brief, and verification notes.
   - Verify the artifact exists and renders locally.

2. **Send the plan back to source-grounding systems**
   - If the plan was based on NotebookLM or another research workspace, query each relevant notebook/source independently with a compact summary of the plan.
   - Ask for: missing risks, misalignments, overbuilt/under-specified parts, and prioritized patches.
   - Do not send the entire HTML if it causes tool/API failures; send a compact extracted summary instead.

3. **Patch before adversarial review**
   - Incorporate source-grounded feedback before running adversarial reviewers so they review the improved plan, not the first draft.

4. **Run adversarial reviewers by lane**
   - Use at least two distinct lenses when risk is high:
     - Technical/filesystem/security reviewer: schemas, rollback, permissions, git/worktrees, TOCTOU, verification.
     - Systems/human/harness reviewer: operator burden, approval fatigue, governance, stale maps, inbox decay, identity overreach, partial migration risk.
   - If a reviewer lane is unavailable, disclose it in the artifact and add an availability/auth preflight; rerun when fixed rather than fabricating the review.

5. **Patch with findings, not raw dumps**
   - Add concise sections summarizing each review verdict and the concrete plan changes.
   - Update the implementation `/goal`, not only the prose sections.
   - Keep “done” objective and operational: schemas, approval artifacts, stop conditions, rollback, evidence, and safe first-run scope.

6. **Render and verify again**
   - Re-run deterministic checks for required phrases/sections.
   - Render via local HTTP server.
   - Check browser console.
   - Visually inspect the new sections for clipping/overflow.
   - Stop preview servers before delivery.

## Hard-won review findings to consider for cleanup/harness plans

- “Moved to inbox” is not done. Use one intake queue with owner/SLA and metrics such as unresolved count and oldest age.
- Identity/preference files should be human-authored or clearly marked `unverified-draft`; do not let agent-written identity become authoritative ground truth.
- Same-lineage subagents are not fully independent reviewers. For execution gates, prefer a different model/process or disclose degraded mode.
- Maps used for token efficiency must be regenerated from manifests after moves; hand-authored maps go stale during migrations.
- First execution should be a tiny pilot with no or very low-risk moves; broad cleanup belongs after the loop proves itself.
- Durable approval should bind a human-readable batch to hashes/artifacts so approval cannot drift from the reviewed plan.
