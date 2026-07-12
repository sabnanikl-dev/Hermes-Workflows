# Dream Architecture Explainer Pattern

Session learning from generating a visual architecture HTML for the closeout dream report prototype.

## When to use

Use this reference when Karan asks to understand the closeout/dreaming infrastructure visually, especially requests like:

- "gen a dream architecture html"
- "include diagrams, flows, and scripts"
- "help me understand the infrastructure visually"

## Artifact shape

Create a standalone HTML report staged under a gateway-safe cache path, plus a zip fallback:

- HTML: `~/.hermes/cache/documents/dream-architecture/Hermes Closeout Dream Architecture.html`
- ZIP: `~/.hermes/cache/documents/dream-architecture.zip`

Recommended sections:

1. Hero/status summary
   - current memory backend from `~/.hermes/config.yaml`
   - cron schedule
   - read-only / approval-gated posture
2. System map diagram
   - inputs: sessions, GitHub PRs, Linear issues
   - generator: `closeout_dream_report.py`
   - outputs: pattern history, reports, gateway cache
   - runner/cron: `daily_closeout_dream_report.sh`, no-agent cron
   - read-only boundary showing blocked durable writes
3. Execution flow
   - cron wakes runner
   - runner invokes generator with `--update-history`
   - generator reads evidence
   - backend-aware staging / fingerprinting
   - artifact packaging
   - Telegram/gateway delivery
4. Memory routing model
   - Standard memory: compact stable preferences/facts
   - Hindsight: structured entity/relationship/temporal/shared recall
   - Obsidian/Hermes Brain: human-readable structured knowledge
   - Skills: repeatable procedures, commands, pitfalls, verification patterns
5. Pattern maturity funnel
   - 1–2 unique observations: stage low
   - 3+ unique observations: emerging pattern
   - 5+ strong score/source diversity: ready for approval
   - emphasize distinct evidence keys; repeated manual runs do not mature evidence
6. Scripts/code section
   - manual safe command: `closeout_dream_report.py --since 7d --dry-run`
   - scheduled command: `closeout_dream_report.py --since 7d --dry-run --update-history`
   - runner snippet
   - backend detection snippet
   - pattern history snippet
   - cron shape
7. Ops checklist
   - HTML/JSON nonzero
   - manual run has `history_updated: false`
   - backend label appears correctly
   - `MEDIA:` lines point at `~/.hermes/cache/documents/`

## Design guidance

- Dark architecture-diagram aesthetic works well for Karan-facing infrastructure explainers.
- Use inline SVG diagrams, not screenshots or Mermaid dependencies.
- Add sticky nav for long reports.
- Include code tabs for script snippets, but set `white-space: pre-wrap; word-break: break-word` to avoid clipped long lines on Telegram/mobile review.
- Diagrams can be horizontally scrollable on small screens; keep section text responsive.

## Verification checklist

Before delivery:

- Parse/save HTML successfully.
- Verify HTML and ZIP exist and are nonzero.
- Open through local HTTP server if `file://` is blocked by browser tooling.
- Check browser console for JavaScript errors.
- Click at least one code tab and verify the visible block changes.
- Use a visual/browser inspection pass for obvious layout breakage.
- Deliver both HTML and ZIP with `MEDIA:` lines.

## Pitfalls

- Do not only send an on-disk path in Telegram; attach both HTML and ZIP from gateway cache.
- Do not let code snippets horizontally clip without wrapping.
- Do not hard-code "Holographic" in the visual model when the active profile uses Hindsight.
- Do not imply the architecture performs durable writes; it is a staging/reporting layer unless Karan explicitly approves promotion actions.
