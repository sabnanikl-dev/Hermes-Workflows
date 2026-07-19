# Design-inspiration issue grooming

Use this checklist when updating an existing UI/design issue from a visual reference.

## 1. Reconstruct the live target before preserving old scope

- Re-read the live issue immediately before editing.
- Inspect the remote default branch, not only the current local branch.
- Count and identify the current siblings in the target layout (cards, sections, routes, CTAs).
- Check adjacent merged/open issues and PRs that may have changed the page since the issue was written.
- Treat numerical assumptions such as “add a fourth card” as hypotheses. If the page already has four cards, reframe the solution instead of forcing stale geometry or displacing shipped work.

## 2. Inspect the reference as both content and composition

Use page extraction for accessible text, links, code samples, and metadata. Also inspect the rendered preview visually when hierarchy, media treatment, spacing, or responsive behavior matters.

Record the transferable traits:

- information hierarchy;
- copy/media relationship;
- spacing and density;
- CTA hierarchy;
- image framing and aspect treatment;
- desktop-to-mobile stacking behavior.

If component source is unavailable or locked, do not invent it. A rendered visual plus public usage API is sufficient for an inspiration contract when the target does not need a source-code port.

## 3. Write an adaptation contract, not a copy request

Split the reference into:

- **Adapt:** composition, hierarchy, interaction model, or responsive behavior worth carrying over.
- **Do not copy:** framework, placeholder content, exact palette, pixel values, dependency stack, or redundant actions that conflict with the target product.

Preserve the target repository’s stack, tokens, semantics, and brand. For a plain HTML/CSS site, explicitly prohibit introducing React/Tailwind/Shadcn merely because the inspiration uses them.

## 4. Reconcile the inspiration with product boundaries

- Prefer the target’s internal destination before external commerce/configurator handoffs.
- Do not inherit extra buttons from the reference when they create duplicate or unsafe pathways.
- Reuse approved claims and existing approved imagery.
- Keep stock, price, checkout, availability, and delivery claims fail-closed unless separately approved.
- Distinguish a standalone feature spotlight from a service-card/grid addition when the current layout already has a coherent set of cards.

## 5. Make the visual outcome reviewable

Specify observable criteria for:

- exact insertion point relative to existing sections;
- semantic heading order and stable section hook;
- desktop split versus mobile stack;
- image count, alt text, intrinsic dimensions, object fitting, and loading behavior;
- no-JavaScript behavior when applicable;
- keyboard focus, touch targets, reduced motion, and horizontal overflow;
- regression checks that prove the link/feature exists in the intended section—not merely somewhere in header/footer/main.

## 6. Verify the edit

- Run the target repository’s baseline checks against the same remote ref cited in the issue when practical.
- Edit the issue only after grounding is complete.
- Re-read the live title/body/labels after mutation.
- Report the stale assumption that changed, the new adaptation, and the verification evidence.