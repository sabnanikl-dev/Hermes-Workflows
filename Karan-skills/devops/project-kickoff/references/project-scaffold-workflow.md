<!-- Archived source skill consolidated into `project-kickoff` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: project-scaffold-workflow
description: Create new dev projects from the Agentic-dev template — populate config, create repo, populate docs/, generate issues.
version: 1.0.0
author: Hermes Agent
---

# Project Scaffold Workflow

Create new dev projects from the reusable Agentic-dev template at `sabnanikl-dev/Agentic-dev`.

## The Pipeline

```
config (from Karan) → populate scaffold → create repo → push → generate issues
```

## When to Use

Starting a new dev project from the Agentic-dev template. **NOTE:** For client consulting engagements, prefer `sabnanikl-dev/agentic-harness-template` (slim: AGENTS.md + docs/) over the full Agentic-dev scaffold which includes Next.js boilerplate. Use the full scaffold only when building a Next.js/Tailwind website from scratch.

- Karan provides either:
- A filled-out `project-config.yaml` from the Config Frontend
- A manual description of the project

### Step 2: Populate the Scaffold

Copy files from `~/agentic-dev-scaffold/` into a new local directory. Then customize:

**ALWAYS customize:**
- `package.json` — set project name/description
- `AGENTS.md` — project name, agent roles, branch prefixes
- `docs/design-system/index.md` — brand colors, typography, component patterns
- `docs/infrastructure/index.md` — deployment instructions for chosen provider
- `docs/product-specs/index.md` — page structure from config
- `src/styles/globals.css` — `@theme` block with brand colors
- `README.md` — project description, quick start

**ONLY if needed:**
- `next.config.js` — set `output: 'export'` if `ssr: false`
- `.github/workflows/` — deployment-specific CI steps
- Add/remove deps in `package.json` based on `tech.plugins`

### Step 3: Create Repo and Push

Try `gh repo create org/name --public --source=. --push` first. If it fails with "Resource not accessible by personal access token (createRepository)", the PAT lacks org repo creation permission. In that case:

1. Ask Karan to create the empty repo manually in browser
2. Then: `git remote add origin https://github.com/org/name.git && git push -u origin main`

### Step 4: Generate Initial Issues

One issue per page from config + infra issues (SEO, deploy, etc.).

### Step 5: Verify Push

```bash
gh api repos/org/name/commits --jq '.[0].sha[:7] + " " + .[0].commit.message'
```

## PAT Scope Requirements

| Operation | Required PAT Scopes |
|-----------|-------------------|
| Clone, push existing repo | `repo` |
| Create/update `.github/workflows/` files | `repo` + `workflow` |
| Create repos under organization | `admin:org` (or create in browser manually) |
| Create PRs | `repo` (classic PAT, not fine-grained) |
| Branch protection rules | `repo` |

**Common errors:**
- `refusing to allow PAT to create workflow` → needs `workflow` scope
- `Resource not accessible (createRepository)` → needs `admin:org` for org repos, or create manually in browser
- `403` on PR creation → using fine-grained PAT, need classic PAT

## Pitfalls

- **Route groups vs routes:** `(name)` is a route group (no URL segment), `name/` is a real route. `/(new)/page.tsx` resolves to `/`, conflicting with `/(site)/page.tsx` also at `/`. For `/new`, use `src/app/new/page.tsx`.
- **pnpm/action-setup@v4 version conflict:** Do NOT specify `version:` in the workflow action if `package.json` already has `"packageManager": "pnpm@X.Y.Z"`. The v4 action auto-detects the version from `packageManager` and passing both causes: `ERR_PNPM_BAD_PM_VERSION: Multiple versions of pnpm specified`. Remove the `version:` block from the action entirely.
- **Deprecated `next lint` with ESLint 9:** ESLint 9 flat config (`eslint.config.mjs`) is incompatible with `next lint` (deprecated, crashes with `module is not defined in ES module scope`). Use `eslint .` in the lint script instead. Also ensure `eslint.config.mjs` uses `export default [`, not `module.exports = [`.
- **ESM config files:** `.mjs` must use `export default`, not `module.exports`. Error: `module is not defined in ES module scope` means wrong export syntax.
- **Turbopack deprecated syntax:** Use `turbopack: {}` not `experimental: { turbo: {} }`.
- **Always verify build:** Run `pnpm build` before pushing. Next.js catches type errors, route conflicts, and import issues at build time.
- **Commit identity:** Always set `git config user.name "Karan Sabnani"` and `git config user.email "sabnani.kl@gmail.com"` before the initial commit, otherwise commits show as `creator <creator@hostname>`.
- **Static export:** `output: 'export'` in `next.config.js` generates a fully portable `out/` folder. Use when `ssr: false` in config.
