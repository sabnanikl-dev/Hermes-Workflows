<!-- Archived source skill consolidated into `project-kickoff` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: project-scaffold-population
description: Workflow for creating a new project from the Agentic-dev scaffold — config-driven, review-gated, incremental.
---

# Project Scaffold Population

Use this workflow whenever Karan says "start a new project" or wants to clone the Agentic-dev scaffold for a new project.

## Workflow Steps (STRICT ORDER — do NOT skip)

### Step 1: Generate project-config.md
- Create comprehensive project configuration file at ~/project-config.md
- Include: project name, repo name, description, domain, brand colors, typography, page structure, tech stack, deploy target, agent assignment

### Step 2: Clone Scaffold
- Copy ALL scaffold files from ~/agentic-dev-scaffold/ into a new local repo directory

### Step 3: Populate from Config
Populate the scaffold with project-specific data from project-config.md:
- package.json → project name
- next.config.js → deployment mode (static export if deploy=static)
- src/styles/globals.css → brand tokens from config colors
- Project config → project name, stack notes, progressive disclosure TOC
- docs/design-system/ → brand color palette, typography
- docs/product-specs/ → project requirements from config
- docs/infrastructure/ → deployment instructions matching deploy target
- README.md → project-specific description

### Step 4: Create Initial GitHub Issues
Generate Issues from the project config and page structure:
- One issue per page/feature from project-config.md content.pages
- Setup issue (install deps, verify build)
- Deployment issue (set up hosting provider)
- Assign issues to appropriate agents based on config.agents

### Step 5: STOP AND PRESENT (MANDATORY PAUSE)
**DO NOT WRITE ANY APP CODE.** Present the following to Karan for review:

1. Repo structure — list of all files in the populated scaffold
2. Populated docs/ — show what was filled in from the config
3. Proposed Issues — show the Issue list with assignments
4. Blockers — any repo creation issues, PAT scope problems, etc.

**Wait for Karan's explicit greenlight before writing a single line of React/app code.**

### Step 6: Build (only after greenlight)
- Create the GitHub repo (if PAT can't create, Karan does it manually)
- Push the scaffold
- Only NOW begin building the app components

## Pitfalls

### PAT Cannot Create Repos
The GitHub PAT (even with repo + workflow scopes) CANNOT create repos under sabnanikl-dev. Returns 403 or GraphQL permission error. Karan must manually create the repo at https://github.com/new.

### Don't Code Before Review
I once built the entire React app (42 files, multi-step wizard, form components, validation) WITHOUT showing Karan the populated scaffold first. **The review step is non-negotiable.**

### Static Export for Config Tools
Use output: 'export' in next.config.js for projects that don't need SSR. Generates portable out/ folder deployable anywhere.

### gh repo create flags
When the PAT has the right scope: gh repo create org/name --source=. --public --push creates AND pushes in one step.