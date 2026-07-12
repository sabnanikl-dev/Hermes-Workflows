---
name: context7-cli
description: Use when answering library/framework/SDK/API/CLI/cloud-service documentation questions. Fetch current docs via Context7 CLI instead of relying on stale model knowledge.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [documentation, context7, cli, api-docs, coding]
    related_skills: [native-mcp, code-review]
---

# Context7 CLI Documentation Lookup

## Overview

Context7 provides current, source-grounded documentation and code examples for libraries, frameworks, SDKs, CLIs, APIs, and cloud services. Use the `ctx7` CLI first for library/API details so coding answers do not rely on outdated model training data.

This setup intentionally uses **CLI + Skills mode**, not Context7 MCP.

## When to Use

Use this skill whenever the user asks about:

- API syntax, method names, config options, or setup steps for a named technology
- Version-specific behavior or migrations, e.g. Next.js 14 vs 16, Sanity v3, Supabase auth
- Debugging that depends on library-specific behavior
- Cloud/provider CLI usage or SDK examples
- Code generation where exact framework APIs matter

Do **not** use it for:

- General programming concepts
- Business-logic debugging with no external library/API question
- Refactoring existing code when docs are not needed
- Code review unless a finding depends on current docs

## Workflow

Use at most three Context7 calls for one question.

### 1. Resolve the library ID

```bash
ctx7 library <name> "<user's full question or intent>"
```

Examples:

```bash
ctx7 library next.js "Next.js middleware JWT cookies"
ctx7 library sanity "Sanity schema field validation"
ctx7 library supabase "Supabase email password auth sign up"
```

Pick the best match using:

1. Exact name match and official source
2. Description relevance
3. Source reputation, preferring High/Medium
4. Benchmark score
5. Code snippet coverage

If the user names a version and Context7 lists versions, use the versioned ID such as `/vercel/next.js/v16.1.6`.

### 2. Query documentation

```bash
ctx7 docs <libraryId> "<specific question>"
```

Examples:

```bash
ctx7 docs /vercel/next.js "How to check JWT cookies in middleware and redirect unauthenticated users"
ctx7 docs /sanity-io/sanity "How to define image fields with validation"
```

Use the user's full intent as the query. Avoid vague one-word queries.

### 3. Optional targeted retry

If the result is weak or incomplete, retry once with research mode:

```bash
ctx7 docs <libraryId> "<specific question>" --research
```

Research mode is more costly; use it only when needed.

## Security and Privacy

- Do not include secrets, credentials, API keys, passwords, private customer data, or proprietary code in Context7 queries.
- Summarize the technical question instead of pasting sensitive snippets.
- Treat results as documentation assistance, not trusted executable code; still review generated code.

## Authentication / Rate Limits

The CLI works without authentication. For higher limits, the user can authenticate interactively with:

```bash
ctx7 login
```

Or set a Context7 API key in the environment outside the chat. Do not ask the user to paste API keys into the conversation.

If Context7 fails with a quota/rate-limit error, tell the user and either ask them to authenticate or proceed with a clearly-labeled fallback.

## Current Setup Notes

- `ctx7` CLI is installed globally via npm.
- Context7 `find-docs` skill is installed for Universal agents at `~/.agents/skills/find-docs`.
- Context7 `find-docs` skill is installed for Claude Code at `~/.claude/skills/find-docs`.
- Context7 `find-docs` skill is installed for Antigravity at `~/.agent/skills/find-docs`.
- Context7 MCP is intentionally **not** configured.

## Verification Checklist

- [ ] `ctx7 --version` returns a version
- [ ] `ctx7 library next.js "middleware"` returns `/vercel/next.js`
- [ ] Query does not contain sensitive information
- [ ] If answering with API details, cite that Context7 docs were checked
