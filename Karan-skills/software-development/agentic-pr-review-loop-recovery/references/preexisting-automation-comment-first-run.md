# Preflight automation comments before the first prover run

Use this when a PR already contains deployment/status bot comments before Reviewer A starts.

## Preventive sequence

1. Read conversation comments, reviews, inline comments, and review threads to completion before launching the expensive A → B → Auditor lifecycle.
2. Distinguish actionable feedback from pure automation metadata. A bot author is not itself a waiver; read the body.
3. Resolve actionable material normally.
4. If a pure status post requires no action, publish a later acknowledgement containing only:

   ```text
   PR-PROVER: ACKNOWLEDGED <immutable artifact id>
   ```

5. Read that acknowledgement back from GitHub. Derive `body_evidence` from the exact API body (including a trailing newline) and empty review state:

   ```bash
   gh api repos/OWNER/REPO/issues/comments/ACK_ID | python3 -c '
   import hashlib, json, sys
   post = json.load(sys.stdin)
   payload = json.dumps([post["body"], ""], ensure_ascii=False)
   print(hashlib.sha256(payload.encode("utf-8")).hexdigest())'
   ```

6. Put the exact `{id, body_evidence}` pin in `operator_acknowledgements` **before the initial run**, then require `check-config` to print that id.
7. Run the repository's reconciliation preflight and require zero unresolved items before spending reviewer lanes.

## Why before launch

A terminal `needs-Karan` journal cannot be resumed. Resetting creates a fresh run that no longer owns the first run's reviewer comments, so those exact-head artifacts become ordinary historical feedback and require a larger ACK bridge. Preventing a status-bot stop is safer and cheaper than recovering after the triad has already published.

## Boundaries

- The pin authorizes one exact post/body version, never a login or bot class.
- Edited acknowledgements require fresh readback and evidence.
- Keep the ACK post pure; residual prose becomes new unresolved feedback.
- Never acknowledge objections, change requests, or ambiguous human prose merely to advance the loop.
