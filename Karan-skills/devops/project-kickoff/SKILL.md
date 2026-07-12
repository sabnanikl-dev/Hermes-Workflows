---
name: project-kickoff
description: Interview-driven project kickoff — clone harness template, ask Karan vision questions, draft spec.md, populate docs/, create repo + issues, wait for greenlight before coding.
version: 2.0.0
author: Hermes Agent
---

# Project Kickoff Workflow

## When to Use

When Karan says "let's start a new project" or similar. This workflow runs before any code is written.

## Umbrella Scope: Agentic Project Lifecycle

This is the class-level skill for starting agentic development projects: kickoff interview, project spec, scaffold/template selection, docs population, repo creation, issue generation, and approval gates before coding.

Absorbed workflows:
- `agentic-dev-scaffold`: full Next.js 15 + Tailwind v4 + TypeScript scaffold with progressive-disclosure AGENTS.md.
- `project-scaffold-workflow`: config → populate scaffold → create repo → push → generate initial issues.
- `project-scaffold-population`: older strict config-driven scaffold population flow; retained as historical/reference material, but prefer the interview-driven kickoff unless the user explicitly wants config files.
- `project-brain-architecture`: two-brain context model, with repo `docs/` as execution brain and Obsidian as knowledge brain.

Full source details are preserved under `references/` with matching filenames.

Additional reference:
- `references/harness-process-audit.md` — post-pilot/process audit pattern for reviewing a task harness, GitHub issues/PRs/comments, and deciding lean reusable-template fixes without overengineering.

## Philosophy

Karan talks. Hermes writes. No forms, no YAML frontmatter, no config files. Karan answers 5–6 open questions in plain English. Hermes drafts the spec and populates the docs. Karan reviews and says "go."

This replaces the old config-driven approach (`~/project-config.md`) which required Karan to fill out structured data upfront. That approach missed things and felt like homework. This approach is conversational and adaptive.

---

## Phase 1: Clone the Harness Template

```bash
cd ~
gh repo clone sabnanikl-dev/agentic-harness-template <project-name>
cd <project-name>
rm -rf .git          # strip template git history
git init
```

The template already has:
- `AGENTS.md` — process rules (slim, reusable)
- `docs/spec.md` — living project context (template, needs filling)
- `docs/design/README.md` — placeholder
- `docs/api/README.md` — placeholder
- `docs/friction/README.md` — with example format
- `docs/conventions/golden-principles.md` — expanded rules
- `docs/conventions/code-style.md` — template

---

## Phase 2: Vision Interview (Conversational)

Ask Karan one question at a time. Let them answer in their own words. Ask follow-ups to clarify. Do NOT dump all questions at once.

### Core Questions (ask all)

1. **"What is this? Describe it in one sentence."**
   - Follow-up: "Who is it for? What problem does it solve?"

2. **"What does it need to do?"**
   - Follow-up: "What pages or sections? Any forms, dashboards, user flows?"
   - Follow-up: "Any special features — booking, payment, login, blog, admin?"

3. **"What's the vibe?"**
   - Follow-up: "Any reference sites you like? Colors, feel, aesthetic?"
   - Follow-up: "Existing brand assets — logo, colors, fonts, photos?"

4. **"Any tech constraints?"**
   - Follow-up: "Framework preference? (Next.js, React, Astro, etc.)"
   - Follow-up: "Hosting? (Vercel, Netlify, GitHub Pages, self-hosted?)"
   - Follow-up: "Domain name? Do you own it?"

5. **"Any APIs or third-party integrations?"**
   - Follow-up: "Contact forms (Formspree, Resend), payments (Stripe), auth (Clerk, Auth0), CMS (Sanity, Strapi)?"
   - Follow-up: "Any existing backend or database?"

6. **"Anything else I should know?"**
   - Follow-up: "Timelines, must-haves vs nice-to-haves, known blockers?"

### Probing Rules

- If Karan is vague, ask for examples ("like what? give me one page you'd want")
- If Karan mentions a feature, ask if it needs a backend or if static works
- If Karan mentions a brand, ask for hex codes or a brand guide link
- If Karan says "I don't know yet" — note it as an open question in spec.md

---

## Phase 3: Draft spec.md

Write the first pass of `docs/spec.md` based on the interview. Do not show Karan the template — write it from scratch using the conversation.

### Structure (match the template)

```markdown
# Project Specification

*Living document. Update as work progresses.*

## What This Is

[1-paragraph description from interview]

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | [from interview] | |
| Backend | [from interview or "None — static site"] | |
| Database | [from interview or "None"] | |
| Styling | [Tailwind / CSS-in-JS / etc.] | |
| Testing | [Jest / Playwright / etc.] | |

## Design System

### Colors
[Only if Karan gave colors. Otherwise: "TBD — see docs/design/brand-guidelines.md when ready"]

### Typography
[Only if Karan mentioned fonts]

## Architecture

[Brief overview based on pages/features discussed]

## Current State

- [ ] Phase 1: [initial feature set]
- [ ] Phase 2: [expansion]
- [ ] Phase 3: [nice-to-haves]

## Open Issues / Blockers

| Issue | Blocker | Status |
|-------|---------|--------|
| | | |

## Acceptance Criteria Template

Every issue should have testable ACs. Example:

```
- [ ] Renders correctly at 375px, 768px, 1440px
- [ ] All fields have validation
- [ ] Form submits to correct endpoint
- [ ] Success + error states handled
- [ ] Uses design tokens (no hardcoded values)
```

## Spec Drift Convention

Every PR that changes architecture MUST update this file.

## Links

- Design docs: `docs/design/`
- API docs: `docs/api/`
- Friction log: `docs/friction/`
- Conventions: `docs/conventions/`
```

### Rules for Drafting

- Be concise. Karan can expand later.
- If Karan was vague on something, write "TBD" and add it to Open Issues.
- Do NOT invent details Karan didn't mention. If you need to make an assumption, flag it: *(Assumption: using Tailwind — confirm?)*

---

## Phase 4: Iterate with Karan

Show Karan the draft `spec.md`. Ask for feedback in plain English.

**Sample message:**
> Here's the first draft of spec.md based on what we discussed. Let me know what's off, what's missing, or what needs more detail. Don't worry about formatting — just tell me in your own words.

Karan will say things like:
- "Actually it's more like X" → update spec.md
- "You missed the Y feature" → add to spec.md
- "I don't know about the tech stack" → leave TBD, add to open questions
- "The colors are wrong" → update design system section

Iterate until Karan says "looks good" or similar.

---

## Phase 5: Populate docs/ Subdirectories

Based on the finalized spec and interview, populate only what's relevant. Don't dump everything.

### docs/design/

If Karan mentioned brand assets, colors, or reference sites:
- `docs/design/brand-guidelines.md` — colors, typography, spacing tokens
- `docs/design/inspiration.md` — reference sites, screenshots, mood board
- If Karan provided hex codes or font names, write them here

If Karan had no brand assets yet:
- Leave `docs/design/README.md` as-is
- Add to `docs/spec.md` Open Issues: "Brand assets needed — colors, logo, typography"

### docs/api/

If Karan mentioned APIs, endpoints, or integrations:
- `docs/api/endpoints.md` — if there's a backend
- `docs/api/integration-<service>.md` — for each third-party service

If no APIs:
- Leave `docs/api/README.md` as-is

### docs/conventions/

Always customize these for the project:
- `docs/conventions/golden-principles.md` — review and add project-specific rules (e.g., "All components use femme-* Tailwind tokens")
- `docs/conventions/code-style.md` — fill in the tech stack from the interview (TypeScript rules if using TS, Python rules if using Django, etc.)

### docs/friction/

Leave empty except the README. This is for future use.

---

## Phase 6: Create GitHub Repo

1. Create the repo:
   - **Option A (preferred):** `gh repo create sabnanikl-dev/<project-name> --public --source=. --remote=origin --push`
   - **Option B (if PAT fails):** Ask Karan to create empty repo at github.com/new, then `git remote add origin https://github.com/sabnanikl-dev/<project-name>.git && git push -u origin main`

2. Verify the push: `gh repo view sabnanikl-dev/<project-name> --json url`

---

## Phase 7: Create Initial GitHub Issues

Derive Issues from the spec. One Issue per discrete task.

**Examples based on interview:**
- If Karan mentioned 4 pages → 4 Issues (one per page)
- If Karan mentioned a contact form → 1 Issue for form + integration
- If Karan mentioned a design system → 1 Issue for design system setup
- If Karan mentioned auth → 1 Issue for auth flow

**Issue template:**
```
Title: [Page/Feature name]
Body:
- Acceptance criteria from spec
- Link to relevant docs/spec.md section
- Label: `phase:1` or `phase:2` or `phase:3`
```

**STOP rule:** Do NOT create Issues for things Karan said "maybe later" or "nice to have unless we have time." Only create Issues for committed scope.

---

## Phase 8: STOP AND WAIT (Non-Negotiable)

Present Karan with:
1. Repo URL
2. Summary of populated docs ("spec.md has X pages, design/ has colors, api/ has endpoints...")
3. List of initial Issues created
4. Any open questions or TBD items

**Sample message:**
> Repo is live: [URL]
> 
> **Created:**
> - spec.md — 4 pages, tech stack, design system
> - docs/design/brand-guidelines.md — colors + fonts from your mood board
> - docs/api/endpoints.md — Formspree + Stripe integrations
> - 6 initial Issues (Phase 1 only)
> 
> **Open questions:**
> - You weren't sure about the footer layout — I left it TBD in spec.md
> - No brand colors yet — I used placeholders, you'll need to update
> 
> **Next step:** Review the Issues. When you're ready, say "go" and I'll start building.

**DO NOT write any app code until Karan gives greenlight.**

---

## Phase 9: Build (After Greenlight Only)

Once Karan says "go":
1. Follow the `multi-agent-dev-workflow` skill
2. Assign Issues to agents (Claude Code for UI-heavy, Codex for backend)
3. Hermes orchestrates, reviews, reports back to Karan

---

## Phase 10: Post-Pilot Harness Audit (When Requested or After Meaningful Learning)

When a task harness produces reusable lessons, review the task repo and the reusable template together before changing the template. Use `references/harness-process-audit.md` for the full pattern.

Rules:
1. Treat GitHub issues/PRs/comments as the execution source of truth; the wiki should contain synthesis, not a parallel tracker.
2. Identify what actually protected the project: approval gates, issue sizing, cross-review, verification, source/asset constraints, friction capture.
3. Propose the smallest reusable template changes that would prevent repeated mistakes.
4. Keep template language class-level and role-based. Do not copy client names, Linear IDs, Hermes-local skill requirements, or tool-specific defaults into the generic template unless explicitly needed.
5. Include a "What Not To Add" section when Karan warns against overengineering.

---

## Complete Workflow Diagram

```
Karan: "let's start a new project"
  ↓
Hermes: clone harness template
  ↓
Hermes: interview Karan (5–6 questions, one at a time)
  ↓
Hermes: draft spec.md from interview
  ↓
Hermes: show Karan draft, iterate until "looks good"
  ↓
Hermes: populate docs/ subdirectories (only what's relevant)
  ↓
Hermes: create GitHub repo, push everything
  ↓
Hermes: create initial Issues from spec
  ↓
Hermes: STOP — present repo + docs + issues, wait for greenlight
  ↓
Karan: "go"
  ↓
Hermes: follow multi-agent-dev-workflow, build begins
```

---

## Rules

1. **Never skip the interview.** Even if Karan seems to know exactly what they want, ask the questions. They always surface things.
2. **Never write app code before greenlight.** The STOP gate is non-negotiable.
3. **Never dump all questions at once.** Ask one at a time. Conversational flow matters.
4. **Never invent details.** If Karan didn't mention it, flag it as TBD or assumption.
5. **Never create Issues for "maybe" scope.** Only committed features get Issues.
6. **Always iterate on spec.md.** First draft is never final. Karan needs to see it and react.

---

## Pitfalls

- **PAT scope issues** — Classic PAT needs `repo`, `public_repo`, `workflow` scopes. Without these, repo creation and Issues creation fail.
- **If PAT cannot create repos**: Have Karan create empty repo via browser at github.com/new, then add remote and push.
- **If gh auth is cleared**: Re-run `echo "$GITHUB_TOKEN" | gh auth login --with-token`
- **gh CLI and GitHub token are separate** — `gh auth logout` wipes the keyring. The `.env` GITHUB_TOKEN does not auto-populate gh.
- **Interview fatigue** — If Karan seems rushed, ask the 3 most critical questions only (what is it, what does it do, what's the vibe). Fill in the rest from context or mark TBD.
- **Over-engineering the spec** — spec.md should be concise. Don't write a novel. Karan can expand it later as the project evolves.
- **Forgetting to strip template git history** — Always `rm -rf .git && git init` after cloning the harness template. Otherwise the new repo inherits the template's commit history.
- **Populating docs/ too early** — Don't populate design/ or api/ until the spec is finalized. It's wasted work if Karan changes direction during spec review.
