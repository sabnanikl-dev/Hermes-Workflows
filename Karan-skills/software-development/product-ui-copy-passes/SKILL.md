---
name: product-ui-copy-passes
description: "Use when de-slopping a web app's UI copy via PR."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [copy, prose, stop-slop, ui-text, web-app, pull-requests]
    related_skills: [writing-humanization-and-voice-editing, agentic-pr-lifecycle, multi-agent-dev-workflow, risk-proportional-pr-orchestration]
---

# Product UI Copy Passes

Use this when Karan asks for a prose check, Stop Slop pass, or copy cleanup on an app's UI and wants it shipped as a PR. For the editorial rules themselves, use `writing-humanization-and-voice-editing`. When Stop Slop is named, read the upstream SKILL.md plus references/phrases.md, structures.md, and examples.md; don't install it. This skill covers turning that into a safe code change.

## Procedure

1. **Isolate.** If the canonical checkout has uncommitted work, run `git worktree add -b chore/<slug> ../<repo>-<slug> origin/main`, then do a fresh `npm ci` inside the worktree. Uncommitted package changes in the main checkout must not leak into the gates.
2. **Inventory every user-visible string**: page title and description maps, eyebrows and captions, sidebar and footer taglines, welcome and empty states, toasts and success messages, modal titles and descriptions, form hints and placeholders, client-facing error strings in the API client and context, `<title>` and meta description, and generated outputs such as PDF and email-draft text. Slogan copy clusters in heading maps, sidebars, onboarding, empty states, and footers.
3. **Classify the findings.**
   - Slogan and filler copy: replace it with plain functional labels that say what the screen does. Treat one word repeated across screens ("good work", "a little") as a single tell to eliminate app-wide.
   - Awkward functional copy (implementation jargon like "snapshot", "reconciled", "schema validation"; overlong safety notices): tighten it and keep the facts.
   - Em dashes in user-visible strings.
4. **Freeze the facts list** before rewriting: every behavior or safety promise the copy makes (for example: never sends email, doesn't process payments, nothing stored in the browser, import is all-or-nothing, retries don't duplicate, locked records, numbers never reused). New copy must keep each one. Cutting a disclaimer for rhythm changes a product claim.
5. **Grep the tests for asserted copy** before editing: `getByText`, `getByRole(..., { name })`, `getByLabel`, `toContainText`, `hasText`, `toThrow(/.../)`. Keep accessible names used as selectors unless they're flagged. For flagged copy, update the assertion to the new exact text, and never delete or loosen it.
6. **Exclude server error strings matched by error-mapping regexes** (such as a `toAppError` prefix match). Rewording them silently changes HTTP status mapping.
7. **Write the contract issue**: audit ledger grouped by screen, the facts list, the selector-preserving rules, the text-only constraint (no className/CSS/ARIA/logic changes; replace decorative slogan text with neutral text instead of deleting layout wrappers), and the gates. Open it before the builder starts.
8. **Build** through the Claude builder lane (`multi-agent-dev-workflow`). Keep prompts and output tables in `~/.hermes/cache/scratch/`, never in the worktree, and grant access with `--add-dir`. Always put `--` before the prompt: `--mcp-config` takes a variable number of arguments and will swallow the prompt as a file path. Require the builder to write a before/after copy table outside the repo and to grep its diff for em dashes and banned filler.
9. **PR body**: before/after copy table grouped by screen, plus fresh exact-head desktop and mobile screenshots of the main screens. Karan reviews public copy as before/after, not raw diffs.
10. **Review tier**: routine by default (native gates + Hermes review + one focused Codex reviewer on fact preservation and selector/test integrity). Escalate only if the diff touches logic, auth, or data paths.

## Pitfalls

- Don't let "plain" become "stripped". Keep the safety and scope statements, just said once and briefly.
- Don't rewrite docs, README, or landing-page copy in the same PR unless asked. It widens review scope and mixes audiences.
- Don't trust a green e2e run alone. Re-read the rendered screens, because copy can pass tests and still read badly in the layout.
