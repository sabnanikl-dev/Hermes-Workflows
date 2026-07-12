<!-- Archived source skill consolidated into `multi-agent-dev-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: handling-codex-reviews
description: Workflow for processing code reviews from another agent (Codex, Claude Code, etc.) — categorizing findings, fixing on the correct branch, and pushing updates.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Code-Review, Multi-Agent, Cross-Agent, PR-Workflow]
    related_skills: [github-pr-workflow, github-code-review]
---

# Handling Cross-Agent Reviews

When another agent (Codex, Claude Code) reviews your PRs, follow this workflow to process feedback efficiently across multiple PRs.

## Step 1: Fetch all reviews

```bash
# Get reviews for each PR
gh pr view <number> --comments --repo <owner>/<repo>
```

## Step 2: Categorize findings by type

Separate feedback into buckets:

1. **CSS/token mismatches** — Using classes that don't exist in your theme (e.g., `text-muted-foreground` when only `text-muted` is defined). Fix: swap to the token that exists.
2. **Wiring bugs** — Components imported but commented out or not rendered in the parent. Fix: uncomment and wire them into the step array/rendering logic.
3. **Schema ↔ UI type mismatches** — Zod schema expects `z.array(z.string())` but the UI uses a `<textarea>` which produces a plain string. Fix: add `setValueAs` to convert.
4. **Nit / follow-up** — Non-blocking suggestions (e.g., `@types/js-yaml` in deps vs devDeps). Track separately.

## Step 3: Fix on the correct branch

Each PR maps to a specific branch. Check out each branch, apply the fix, commit with a message referencing the reviewer, and push:

```bash
git checkout <branch-name>
# apply fix
git add -A
git commit -m "fix: <description>

Addresses Codex review on PR #<number>"
git push origin <branch-name>
```

### Cross-branch propagation

When you fix an issue (e.g., `text-muted-foreground` → `text-muted`) on one branch, **grep all other open PR branches for the same issue**. Shared files like form components, globals.css, and utility modules often drift across branches. Fix it everywhere in one pass:

```bash
# After fixing branch A, check branch B
git checkout <other-branch>
grep -rn "text-muted-foreground" src/ --include="*.tsx"
# fix if found, commit, push
```

### Prop interface consistency

When a parent component passes props to a child (e.g., `<StepPages form={form}>`), verify the child's interface matches. Cross-agent reviews often catch this after the fact. Before pushing, do a quick interface check:

```bash
# Check what the parent passes
grep "StepPages" src/app/new/page.tsx
# Check what the child expects
head -20 src/components/form/step-pages.tsx | grep "interface\|Props"
```

If they don't match, update the child to accept the prop the parent is already passing.

## Step 4: Verify before reporting complete

After applying cross-agent feedback, do not rely on local commits alone. Run quick quality gates, push, and verify the PR's remote head includes the follow-up commit before telling the user it is updated:

```bash
# Basic local checks; adapt to repo type
git diff --staged --check
# For docs-only repos, at minimum run markdown/link/structure validation if available
# For code repos, run the relevant lint/test command from the repo docs

# Push and verify remote PR commits
git push origin <branch-name>
gh pr view <number> --repo <owner>/<repo> --json commits,mergeStateStatus,isDraft
```

If the review feedback came through a PR conversation comment rather than a formal review, still treat it as actionable review input: read it with `gh pr view --comments`, implement each requested change, then leave a concise PR comment summarizing what changed and the verification performed.

When the PR is tied to an external tracker such as Linear, update the linked issue only after the remote PR commit is verified.

## Step 5: Common pitfalls

### CSS token mismatches
Always verify Tailwind color tokens exist in `globals.css` before using semantic classes like `text-muted-foreground`, `bg-card`, `border-muted`, etc. When in doubt, use the base token (`text-muted`, `border-border`).

### Commented-out code in PRs
Don't ship features as "TODO for later" and claim they work in the PR description. Either implement them fully or omit the claim. If you comment out a step/component, the PR body should reflect that it's partial.

### Prop interface drift
When wiring a component into a parent (wizard, layout, etc.), the parent may pass `form={form}` while the child still expects `{ register, errors }`. This happens when you write the child first with one API, then wire it later with a different one. Always verify both sides match before pushing — reviewers will catch this immediately.

### Schema ↔ UI type mismatches
When a zod schema defines an array but the form control produces a string, use `setValueAs` on the `register()` call:

```tsx
{...register("tech.plugins", {
  setValueAs: (v: string) => v.split("\n").map(s => s.trim()).filter(Boolean)
})}
```

This converts the textarea value from `"next\nreact"` to `["next", "react"]`.

## Step 6: PR comment signatures

Every PR comment should be signed to identify the agent who left it:

```
## Review Summary
(findings here)
---
*— Hermes*      or      *— Claude Code*      or      *— Codex*
```

This convention keeps multi-agent threads readable and accountable.