<!-- Archived source skill consolidated into `project-kickoff` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: project-brain-architecture
description: Multi-agent shared context architecture — execution brain in repo docs/, knowledge brain in Obsidian wiki, spec.md as central hub.
tags: [agents, context, architecture, multi-agent, spec]
triggers:
  - "project brain"
  - "agent context"
  - "shared context"
  - "spec.md"
  - "docs structure"
---

# Project Brain Architecture

## The Problem
Multiple agents (Claude Code, Codex, Hermes) need the same context when working on issues. Linear issue descriptions can't carry full project knowledge (design system, constraints, voice rules, competitive landscape).

## The Solution: Two Brains

### Execution Brain (repo `docs/`)
Lives in the client repo. Read by ALL agents (Claude Code, Codex, Hermes).
Version controlled. No external dependencies.

```
client-repo/
├── AGENTS.md                          ← Slim rules (~100 lines)
├── docs/
│   ├── spec.md                        ← THE BRAIN ENTRY POINT
│   ├── client/
│   │   ├── profile.md                 ← Owners, business model, voice
│   │   ├── competitive-landscape.md   ← Competitors, white space, keywords
│   │   ├── constraints.md             ← Hard rules, guardrails
│   │   └── systems.md                 ← POS, CRM, automation tools
│   ├── design/
│   │   ├── brand.md                   ← Colors, typography, tokens
│   │   └── components.md              ← UI patterns
│   ├── strategy/
│   │   ├── seo.md                     ← Keywords, location pages, citations
│   │   ├── content.md                 ← Calendar, pipeline, style guide
│   │   └── review-generation.md       ← Automation templates
│   ├── friction/                      ← What broke, how we fixed it
│   └── api/                           ← External API notes
├── src/                               ← Code
└── ...
```

### Knowledge Brain (Obsidian wiki)
Lives at `~/obsidian-vault/hermes-brain/`. Read by Hermes + Karan.
Cross-client knowledge, research, strategy, status tracking.

```
hermes-brain/
├── wiki/
│   ├── consultancy/
│   │   ├── clients/Client JMD Menswear.md
│   │   ├── research/JMD Competitor Landscape.md
│   │   └── business-plan.md
│   └── shared/
│       └── projects/Project Status.md
```

## spec.md as Hub
Every agent session starts with `Read docs/spec.md`. It contains:
- Quick context (what is this project)
- Key constraints (READ FIRST section)
- Design system summary (colors, typography)
- Current status
- Detailed references (links to all other docs)

## The Flow
```
Linear issue: "Build JMD homepage hero"
    ↓
Hermes reads issue + clones/updates repo
    ↓
Claude Code: reads AGENTS.md → reads spec.md → reads docs/design/brand.md
    ↓
Codex: reads same files → checks against constraints
    ↓
Both agents have full context without needing Obsidian
```

## For Non-Code Tasks (GBP audit, content strategy)
Do not assume Hermes should always execute these directly or headlessly. Karan's preferred V1 for ops work is a lean, manual execution harness:

1. Hermes + Karan scope/rewrite the Linear issue using the Agent Delegated Issue template.
2. Hermes creates or populates a small task-specific harness folder (for example `jmd-2-gbp-audit-harness/`).
3. The harness includes only the relevant context, constraints, playbook, expected outputs, and evidence folders.
4. Karan opens that folder in Codex Desktop or Claude Desktop, where the agent reads the live Linear issue through its own integration and executes inside the harness.
5. Hermes can review outputs and help post the final Linear comment.

Lean ops harness shape:

```text
<issue>-<task>-harness/
  AGENTS.md
  task.md
  context.md
  playbook.md
  constraints.md
  outputs/
  evidence/
```

Use this before building automated routing/webhooks/headless execution. The future unified Papi OS can combine code and ops harnesses later, but V1 should stay small and reusable.

## Where Obsidian-Linear Plugin Fits
Plugin: https://github.com/casals/obsidian-linear-integration-plugin
Useful for Karan's human workflow (linking issues to wiki pages).
NOT the agent context solution. Agents read files, not Obsidian vaults.

## Layer Summary
| Layer | Where | Who Reads | Purpose |
|-------|-------|----------|---------|
| Execution brain | Repo `docs/` | Claude Code, Codex, Hermes | Design, constraints, specs, strategy |
| Knowledge brain | Obsidian wiki | Hermes, Karan | Profiles, research, cross-client |
| Task queue | Linear | Hermes, Karan | Issues, status, ownership |
| Code | Repo `src/` | Claude Code, Codex | The actual deliverable |
