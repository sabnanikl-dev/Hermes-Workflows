---
name: research-intelligence-workflows
description: "Use for research intelligence workflows: academic paper search/writing, arXiv, RSS/blog monitoring, prediction-market data, and local LLM wiki knowledge retrieval."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, arxiv, papers, blogs, polymarket, wiki]
    related_skills: [research-workflow]
---

# Research Intelligence Workflows

## Overview
This umbrella consolidates research-source and research-output skills. Use it when the task is to discover, monitor, synthesize, or write from external knowledge sources.

## When to Use
- Search arXiv by keyword, author, category, or paper ID.
- Monitor blogs/RSS feeds for updates.
- Query Polymarket markets, prices, orderbooks, and history.
- Build or query a local LLM wiki.
- Draft ML/research papers with venue-style checklists and experiment structure.

## Subworkflows

### Academic discovery and writing
Search first, preserve citations/IDs, separate evidence from interpretation, and use paper-writing templates/checklists for manuscript structure.

### Monitoring
For recurring feeds, prefer explicit source lists and durable scripts. Record last-seen state outside the skill, not in memory.

### Market intelligence
Treat market prices as probabilistic signals, not facts. Capture market IDs, timestamps, and liquidity/volume context.

### Local research wiki
Use wiki retrieval for persistent domain knowledge, but verify current facts with live sources when recency matters.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] Cite source URLs/IDs and timestamps for live data.
- [ ] Use multiple sources for high-stakes claims.
- [ ] Distinguish summary, synthesis, and recommendation.
- [ ] Keep recurring monitoring state out of the skill body.
