<!-- Archived source skill consolidated into `project-kickoff` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: agentic-dev-scaffold
description: Scaffold a complete agentic development repository with Next.js 15, Tailwind v4, TypeScript, progressive disclosure AGENTS.md, and multi-agent workflow docs. Clone-ready template for all new dev projects.
category: software-development
---

# Agentic Dev Scaffold

Builds a complete Next.js 15 + Tailwind v4 + TypeScript project with progressive disclosure AGENTS.md and docs/ knowledge base. Clone `sabnanikl-dev/Agentic-dev` for new projects, or rebuild from scratch.

## When to Use
- Starting a new website project (client sites, Femme Events sub-sites, Papi AI landing pages)
- The `Agentic-dev` repo doesn't exist or needs a fresh clone
- Building a project that Claude Code and Codex will work on together

## Stack (always fixed)

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5.7 (strict mode) |
| Styling | Tailwind CSS v4 |
| Package Manager | pnpm |
| Linting | ESLint 9 flat config + next/core-web-vitals |
| Formatting | Prettier 3 + tailwindcss plugin |
| Deployment | Vercel |
| CI | GitHub Actions |

## Scaffold Steps

### 1. Repository Structure

```
src/
├── app/                    # Next.js App Router
│   └── (site)/             # Route group for customer-facing pages
├── components/
│   ├── ui/                 # Reusable UI primitives
│   └── layout/             # Layout components
├── lib/
│   ├── config/             # Site configuration
│   ├── hooks/              # Custom React hooks
│   ├── utils/              # Utility functions (cn, etc.)
│   └── api/                # API clients / server actions
├── styles/                 # globals.css with @theme tokens
└── types/                  # Shared TypeScript interfaces
docs/                       # System of record (progressive disclosure)
docs/conventions/           # Code style, naming, commits
docs/workflows/             # PR process, merge rules
docs/design-system/         # Colors, typography, components
docs/infrastructure/        # Deploy, env, CI
docs/product-specs/         # Feature requirements
docs/exec-plans/            # Active plans + tech debt tracker
docs/generated/             # Auto-generated each session
docs/references/            # Tool documentation links
.github/workflows/          # CI pipelines
.github/ISSUE_TEMPLATE/     # Bug report, feature request
.claude/skills/             # End-session audit checklist
```

### 2. Package.json Essentials

Use `pnpm` as `packageManager`, Node 22+, Next.js 15, React 19, TypeScript strict. Include scripts: `dev` (--turbopack), `build`, `start`, `lint`, `lint:fix`, `format`, `format:check`, `typecheck`.

### 3. Config Files
- `next.config.js` — standalone output, reactStrictMode
- `tsconfig.json` — strict, path aliases @/*, next plugin
- `postcss.config.js` — @tailwindcss/postcss
- `eslint.config.mjs` — flat config with next/core-web-vitals, no-console warn
- `.prettierrc.js` — singleQuotes, tailwind plugin last
- `.gitignore` — node_modules, .next, .env, .DS_Store, IDE dirs
- `.editorconfig` — 2-space, lf, trailing newline
- `.node-version` — 22
- `.npmrc` — engine-strict=true

### 4. App Framework

- Root `layout.tsx` — metadata, html/body structure, globals.css import
- `(site)/page.tsx` — default landing component
- `src/styles/globals.css` — @theme block with design tokens
- `src/lib/utils/cn.ts` — class name merger
- `src/components/ui/button.tsx` — baseline UI component with variants

### 5. CI Pipeline

Runs on PR to main: install → typecheck → lint → format:check → build. Written to `.github/workflows/pr-checks.yml`.

### 6. AGENTS.md (Progressive Disclosure)

**Keep ~100 lines max** — table of contents pointing to docs/ subfiles. Context is scarce; a giant instruction file crowds out the task. Include: agent identification, core rules, documentation system table, branch naming, quick reference commands, end-session protocol pointer.

### 7. docs/ Knowledge Base

- `docs/conventions/` — code style, naming, commit rules, forbidden patterns
- `docs/workflows/` — PR process, cross-review, merge verification, end-session audit
- `docs/design-system/` — color tokens, typography, spacing, component patterns
- `docs/infrastructure/` — dev setup, deployment, env var rules, CI
- `docs/product-specs/` — feature requirement templates
- `docs/exec-plans/` — active plans + tech debt tracker

### 8. ARCHITECTURE.md

Dependency direction rules (types → config → utils → hooks → components → app/pages, never violate), server vs client component rules (push use client to leaves), state management strategy (URL first, hooks second, no global state default).

### 9. Push to GitHub

Configure git identity first. Push to main. Requires `workflow` scope on PAT for `.github/workflows/` files — if lacking, push everything except workflows and add manually.

## Pitfalls

- **PAT without workflow scope** — GitHub rejects `.github/workflows/` push. Most common failure. Update PAT or add file via GitHub UI.
- **Don't bloat AGENTS.md** — progressive disclosure or agents lose task context.
- **pnpm required** — never use npm or yarn.
- **@theme block mandatory** — design tokens in globals.css, never hardcoded in JSX.
- **Commit identity** — configure `git config user.name` and `git config user.email` before first commit or it uses machine hostname.
