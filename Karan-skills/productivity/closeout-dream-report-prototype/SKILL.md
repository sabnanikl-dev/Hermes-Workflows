---
name: closeout-dream-report-prototype
description: Use when running or maintaining the prototype Hermes closeout dreaming report that reviews recent sessions, GitHub PRs, and Linear items, stages memory patterns conservatively, and outputs a gateway-safe HTML report.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memory, closeout, dreaming, reports, cron, holographic, prototype]
    related_skills: [hermes-agent, daily-log, claude-design]
---

# Closeout Dream Report Prototype

## Overview

This prototype runs a read-only Hermes "dreaming" closeout pass over recent work signals and produces a self-contained HTML report. It currently reads:

- Hermes session history from `~/.hermes/state.db`
- merged GitHub PRs via `gh search prs`
- completed/canceled Linear issues via the Linear GraphQL API

It does **not** write to standard memory, Hindsight, Obsidian, skills, GitHub, or Linear. The report is a staging and review artifact only.

The core doctrine is pattern-first: one-off observations should not become durable memory. Candidates start conservative and only mature after repeated, distinct evidence appears across time and/or source types. Re-running the report against the same evidence must not artificially mature a pattern.

The prototype is now backend-aware. It detects `memory.provider` from `~/.hermes/config.yaml` and labels staged routes differently for built-in memory, Holographic, Hindsight, and other providers. Karan's current default profile uses Hindsight, so the report should distinguish compact standard-memory preferences from Hindsight/Obsidian entity-temporal context and skill-worthy procedures instead of calling everything "Holographic staging."

## When to Use

Use this skill when:

- Karan asks for the daily/overnight Hermes memory closeout or dream report.
- You need to inspect or adjust the prototype report generator.
- A cron run fails or the report attachment is missing.
- You are tuning conservative scoring, pattern history, or promotion thresholds.
- You need to explain what should become standard memory, Hindsight, Obsidian, or skill material.

Do **not** use this skill to automatically promote candidates into durable memory. Promotion is approval-gated and should remain conservative.

## Current Files

- Generator script: `~/.hermes/scripts/closeout_dream_report.py`
- Daily runner: `~/.hermes/scripts/daily_closeout_dream_report.sh`
- Reports: `~/.hermes/reports/closeout-dream/`
- Pattern history: `~/.hermes/reports/closeout-dream/candidate-pattern-history.json`
- Backend config source: `~/.hermes/config.yaml` (`memory.provider`)
- Gateway-safe attachment folder: `~/.hermes/cache/documents/closeout-dream-report-daily/`

A copy of the generator script is also kept in this skill under `scripts/closeout_dream_report.py` as the prototype source snapshot. The gateway-safe wrapper is kept under `scripts/daily_closeout_dream_report.sh`.

Session-specific packaging and cron setup notes live in `references/2026-05-25-prototype-packaging.md`.

For a polished visual infrastructure explainer with diagrams, flows, embedded script snippets, gateway-safe packaging, and verification steps, use `references/dream-architecture-explainer.md`.

## Backend-Aware Routing Doctrine

Hardening based on `nexus9888/hermes-memory-skills` and the Hindsight/Holographic comparison:

- Detect `memory.provider` before scoring or labeling candidates.
- **Built-in memory:** compact prompt-injected facts/preferences only; respect char pressure and avoid procedure bloat.
- **Holographic:** local, lightweight, trust-scored, entity-bound staging; promotion would require `fact_store` with entities and `fact_feedback` for decay, but this prototype remains read-only.
- **Hindsight:** richer structured recall across sessions, entities, relationships, time, tools, and agents; project/entity/temporal patterns should route toward Hindsight or Obsidian review, not flat standard memory.
- **Skills:** reusable procedures, pitfalls, verification checklists, and tool workflows.
- **Fallback/other providers:** stage and report backend notes; do not assume Holographic semantics.

## Pattern-First Scoring Doctrine

Karan's preference is explicit: the more Hermes dreams, the more patterns it should recognize. One run should surface possibilities, not strong recommendations.

Initial scoring should stay low:

- memory-like one-off: around `0.40`
- possible skill pattern: around `0.38`
- possible wiki/Hindsight pattern: around `0.34`
- source-of-truth/tracker noise: around `0.18–0.30`

Promotion readiness:

- `needs more dreams`: default for one-off candidates
- `emerging pattern`: repeated across several distinct evidence observations
- `ready for approval`: only after enough repeated observations and high score
- `source-truth only`: keep in GitHub/Linear/session evidence, not memory

Current prototype thresholds:

- 1–2 unique evidence observations: stage only
- 3+ unique evidence observations with sufficient score: emerging pattern
- 5+ unique evidence observations with sufficient score: ready for approval

Pattern history stores evidence keys derived from source type, source identifier, and candidate fingerprint. This is intentional: a manual rerun against the same session/PR/issue should not increase maturity.

A candidate that mentions a PR number, issue number, commit SHA, phase status, or temporary task state should usually remain source-of-truth only unless it clearly encodes a reusable workflow lesson.

## Manual Run

```bash
~/.hermes/scripts/closeout_dream_report.py --since 7d --dry-run
```

Manual dry-runs do **not** update pattern history by default. Use this for review/testing so repeated manual runs do not mature the same evidence.

Scheduled runs should add `--update-history`:

```bash
~/.hermes/scripts/closeout_dream_report.py --since 7d --dry-run --update-history
```

The script prints JSON with `html`, `json`, and `summary` fields.

## Daily Gateway Runner

The cron should call:

```bash
~/.hermes/scripts/daily_closeout_dream_report.sh
```

The runner:

1. Runs the generator for the last 7 days with `--update-history`.
2. Copies HTML and JSON into `~/.hermes/cache/documents/closeout-dream-report-daily/`.
3. Creates `~/.hermes/cache/documents/closeout-dream-report-daily.zip`.
4. Emits a concise Telegram/gateway-safe message with `MEDIA:` lines for the HTML and zip.

Gateway-safe paths matter. Do not attach directly from `~/Downloads`; use `~/.hermes/cache/documents/...`.

## Cron Schedule

The intended prototype schedule is every morning at 5 AM:

```cron
0 5 * * *
```

Use a no-agent cron job for this prototype so the script output is delivered directly and no LLM rewrites the report.

Expected cron shape:

- Name: `Daily Closeout Dream Report Prototype`
- Schedule: `0 5 * * *`
- Script: `daily_closeout_dream_report.sh`
- `no_agent`: true
- Delivery: origin/current chat unless Karan asks for another destination

## Verification Checklist

After setup or edits:

- [ ] `python3 -m py_compile ~/.hermes/scripts/closeout_dream_report.py`
- [ ] `~/.hermes/scripts/closeout_dream_report.py --since 7d --dry-run` returns JSON with HTML/JSON paths
- [ ] Manual dry-run JSON has `history_updated: false` and `writes_performed: []`
- [ ] Backend detection appears in JSON/report (`backend.provider`, `summary.memory_backend`)
- [ ] HTML file exists and is nonzero
- [ ] JSON file exists and is nonzero
- [ ] `~/.hermes/scripts/daily_closeout_dream_report.sh` prints `MEDIA:` lines using `~/.hermes/cache/documents/`
- [ ] Zip exists and is nonzero
- [ ] Cron job exists and is scheduled at 5 AM
- [ ] No durable writes were performed by the report generator

## Common Pitfalls

1. **Over-scoring one-offs.** If a single user message or session snippet gets a high score, lower the base score and require more dream observations.

2. **Confusing tracker truth with memory.** GitHub PRs and Linear issues are evidence. They should not become memory unless they reveal reusable patterns.

3. **Sending attachments from the wrong folder.** Telegram/gateway delivery should use `~/.hermes/cache/documents/...` paths.

4. **Letting the report mutate memory.** This prototype is read-only. Memory/Hindsight/Obsidian/skill promotion requires explicit approval.

5. **Running an LLM cron unnecessarily.** The prototype already generates the HTML. Use `no_agent=true` unless Karan explicitly asks for an LLM-authored summary layer.

6. **Artificially inflating pattern history.** Manual dry-runs omit `--update-history`; scheduled runs use it. The generator also tracks unique evidence keys so repeated runs over the same session/PR/issue do not increase promotion readiness.

7. **Hard-coding Holographic language.** Holographic is local/trust-scored/entity-bound; Hindsight is structured/entity/temporal/shared recall. Detect the backend and keep route labels honest.
