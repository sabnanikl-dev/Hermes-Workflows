# Client-Facing Audit Presentation Pattern

Use this reference when turning an internal audit, Linear issue, ops harness output, or evidence folder into a polished HTML client report.

## Source Inputs
- Issue comments / final comments: extract status, blockers, approvals, and recommended next actions.
- Audit output markdown: use it as the factual source of truth.
- Evidence notes: use for confidence and metrics, but do not expose private/internal tooling unless the client should see it.
- Client context skill/docs: confirm tone, constraints, approved claims, and what must remain approval-gated.

## Client-Facing Transformation
- Lead with the business decision, not the audit mechanics.
- Keep it concise: executive snapshot, priority actions, baseline metrics, approval checklist, next-step sequence.
- Remove internal artifacts: Codex/Hermes/browser-token details, repo paths, raw evidence filenames, implementation chatter, Linear metadata unless explicitly requested.
- Preserve safety language when important: “no live changes were made,” “approval needed before publishing,” “verify before claiming.”
- Convert long audit tables into 3-6 high-impact cards or action rows.
- Mark draft copy clearly as draft / approval-needed.
- Avoid unsupported client claims, fake metrics, or decorative stats.

## Visual/Interaction Pattern
- Single self-contained HTML file is usually best for delivery portability.
- Use a polished editorial/deck feel: strong hero, restrained palette, section rhythm, large readable type, sparse copy.
- For client-facing “beautiful animations,” use purposeful motion: reveal-on-scroll, count-up metrics, subtle bars/tiles, hover affordances.
- Add `prefers-reduced-motion` handling when motion is substantial.
- Include print-friendly CSS for reports that may be saved as PDF.
- Include a data-URI favicon to avoid local 404 console noise during verification.

## Verification Checklist
- File exists at the requested deliverables path.
- Open via local HTTP server if browser tools block `file://` URLs.
- Check browser console; favicon 404s count as cleanup-worthy if easy to fix.
- Confirm internal/tooling details are not visible in client copy.
- Confirm the report includes all user-requested qualities: clean, actionable, concise, elegant, animated.
- If a screenshot/visual inspection tool is available, inspect the primary viewport before reporting done.

## Report Skeleton
1. Hero: client name + audit type + one-line outcome.
2. Verdict: “strong foundation / biggest gap / opportunity.”
3. Key findings: 3 concise cards.
4. Priority actions: numbered rows with status pills.
5. Baseline metrics: only real sourced numbers.
6. Draft copy/assets: concise approval-ready copy where applicable.
7. Approval checklist: facts/assets to confirm before live changes.
8. Rollout: 3-4 next steps.
