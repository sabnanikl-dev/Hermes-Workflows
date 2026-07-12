# Hermes Personal MUA Control Room Handoff Pattern

Use this when Product 001 or a similar passive-revenue product is stuck between useful artifact polish and buyer trust/value clarity.

## Trigger

A NotebookLM product/revenue answer, adversarial review, or human feedback says the product still feels like:

- an AI/prompt/info pack instead of a job the buyer can use;
- too abstract or too far from the pain-holder;
- risky because the buyer/end customer fears autonomous AI messages;
- missing a concrete human-in-the-loop control surface.

## One-run move

Treat `product format` as the single experiment surface and create one private buyer-deliverable that answers:

```text
Trigger -> Context -> Drafted next step -> Human approval -> Escalation -> Log -> Do not automate
```

For Product 001, the artifact was:

```text
products/local-service-missed-call-recovery-pack/buyer-deliverables/mua-control-room-and-handoff-rules.md
```

## Why it works

- The AI-money notebook framed the sellable unit as a minimal useful agent / control room, not raw AI prompts.
- Strategic notebooks reinforced evaluator-style discipline: make the qualitative trust gap explicit enough to verify.
- The artifact gives the agency-side buyer a safer thing to show a skeptical local-service owner: staff approval, edge-case handoff, and review logs before any automation pitch.

## Experiment contract

Use one ledger row only:

- `surface`: `product format`
- `primary_metric`: `objection coverage`
- `baseline`: no standalone handoff/control artifact for owner control objections
- `result`: number of objections covered, typically 3/3
- `decision`: `promote` only if no public claims or setup posture are added

Recommended objection set:

1. “I do not want a bot texting customers without approval.”
2. “We already have a receptionist, phone system, or CRM.”
3. “What if the message is wrong or the caller is an edge case?”

## Guardrails

- Do not rebuild dist artifacts unless the run’s single move is artifact rebuild.
- Do not change buyer, price, CTA, platform, public posture, or approval request in the same run.
- Do not add revenue, ROI, savings, legal, compliance, booked-job, or guarantee claims.
- Keep the artifact private-draft unless Karan approves a specific external use.

## Verification

Run a small deterministic check before validators:

- TSV row width remains consistent.
- The new artifact contains approval, existing-process compatibility, escalation/edge-case, and no-guarantee language.
- `validate_repo.py`, `git diff --check`, and the product/loop audits still pass.
