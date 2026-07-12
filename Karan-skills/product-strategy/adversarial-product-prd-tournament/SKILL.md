---
name: adversarial-product-prd-tournament
description: Research a connected product ecosystem, run a six-role idea tournament, and prove a PRD through independent adversarial review.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [product-strategy, research, prd, adversarial-review, tournament]
---

# Adversarial Product PRD Tournament

## Use when

A sponsor needs a researched, implementation-ready product concept rather than generic ideation, with a defensible winner, documented ecosystem fit, and independent hostile review.

## Workflow

1. **Research the real ecosystem first.** Use multiple first-party sources. Create `research/<ecosystem>.json` with products, customer roles, workflow stages, documented integrations, source URLs, confidence limits, and overlap/dependency risks. State clearly when public material does not prove internal implementation or feature absence.
2. **Add a tournament rubric before generating ideas.** Score Unique Knowledge Alpha, pain/frequency, workflow fit, feasibility, economics and risk. Require an explicit high-alpha threshold; disqualify chatbot framing, undocumented data/API assumptions, unowned dashboards, unexplainable recommendations and regulated decisioning.
3. **Separate entrants from evaluation.** Launch six role-specific entrant lanes. If model selection is not exposed, record that limitation instead of claiming the requested model ran. Use an independent controller/reviewer to score head-to-head rounds and preserve every elimination reason in `tournament_log.json`.
4. **Run a collision diff.** For the winning concept, name nearest existing capabilities and specify exactly where they end. Do not infer product absence from marketing silence.
5. **Use Maker/Checker separation.** A Maker drafts the PRD; a distinct Claude Code reviewer acts as Skeptical Investor/Ruthless Competitor. The reviewer must inspect the ecosystem map before each round.
6. **Lock one canonical concept before polishing.** Treat the corrected tournament winner record as the naming/scope source of truth. Assert that the PRD title, seam audit, report title/body, metrics, and reviewer decision all describe that exact concept. If post-win drafting introduces an adjacent idea, either fold it into a clearly bounded calibration/evaluation loop or re-run collision scoring—do not silently rename the product.
7. **Make the PRD build-facing as well as evidence-safe.** Include goals/user goals/non-goals; personas, permissions and authority limits; entry points and core UX; explicit incomplete/stale/expired/rejected states; prioritized traceable functional requirements; security/privacy/access requirements; technical considerations; milestone sequencing; and testable user stories covering primary, alternative, edge, expiry and revocation paths. Preserve the harder evidence, seam, metric and kill gates rather than replacing them with a generic PRD template.
8. **Require real adversarial repairs.** Preserve at least two Hell No objections and show their exact fixes in the PRD. Typical high-value checks:
   - feature novelty must be verified, not asserted;
   - read-only exports cannot imply a native embedded UI/API;
   - pilot metric must be causally movable and symmetrically observable in control;
   - sample-size claims must respect assignment clustering;
   - every exception state and disposition must be defined;
   - ownership is a named accountable party, not a role noun.
7. **Add hard pre-build gates where evidence is unavailable.** Create a seam-verification audit requiring current capability/license review, field-level report confirmation, user interviews, ownership commitments and an explicit stop/re-score path.
8. **Build a director-level HTML report.** Use a clear editorial layout, real caveats, workflow and tournament tables, pilot gates, adversarial history and sources. Avoid generic AI gradients. Serve via local HTTP for QA; inspect visually, check console errors and assert no horizontal overflow.
9. **Verify deterministically.** Include a script that asserts artifact paths, valid JSON, six entrants, high-alpha winner, PRD sections/signature/Hell No count, seam-audit reference, required report sections and banned style markers.

## Non-negotiables

- Do not call a product feature novel merely because its public page omits it.
- Do not fabricate interviews, API access, report headers, license access, baseline volumes or model identity.
- Conditional approval is not launch authorization. Preserve unresolved evidence as explicit pre-build gates.
- Stop local preview servers after QA.
