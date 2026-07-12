<!-- Archived source skill consolidated into `research-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: subagent-research-report
description: Spawn parallel sub-agents for deep research, synthesize findings into a polished HTML report, and deliver as a file. Used for deep dives on tools, frameworks, or strategy topics.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, subagents, html, reports, synthesis]
    related_skills: [research-workflow, writing-plans, subagent-driven-development]
---

# Sub-Agent Research & Report Workflow

When the user asks for a "deep dive" into a topic and wants a polished deliverable, use this pattern.

## When to Use

- User says "deep dive", "research", "compare", "evaluate"
- Topic has 2+ distinct research angles that benefit from parallel exploration
- User wants a polished deliverable (HTML report, not just bullet points)
- Topic is complex enough that single-agent research would hit context limits

## Workflow

### Step 1: Identify Research Streams

Break the topic into 2–4 independent research angles. Each becomes a sub-agent task.

Example:
- **Topic:** "Codex + Linear for Papi AI"
- **Stream 1:** Codex docs (features, browser, automations, integrations)
- **Stream 2:** Linear MCP + issue model (kanban, triage, GitHub sync)
- **Stream 3:** Multi-agent workflow patterns (Hermes vs Codex vs Claude Code)

### Step 2: Spawn Parallel Sub-Agents

Use `delegate_task` with `role: leaf` for each research stream. Pass explicit context and goal.

```
delegate_task(
  tasks=[
    { goal: "Research X...", toolsets: ["web", "browser"] },
    { goal: "Research Y...", toolsets: ["web", "browser"] },
    { goal: "Design Z...", toolsets: ["web"] }
  ]
)
```

**Max 3 concurrent** (default limit). If more needed, batch in waves.

### Step 3: Validate Source Files

After sub-agents return, verify all output files exist and have content:
```
mcp_filesystem_get_file_info(path=...)
```

### Step 4: Synthesize into HTML Report

Read the sub-agent outputs, extract key findings, and build a single polished HTML file.

**HTML report requirements:**
- Mobile-first responsive design
- Dark mode with light mode fallback (`prefers-color-scheme`)
- CSS variables for theming
- Scroll-triggered fade-in animations (`IntersectionObserver`)
- Executive summary at top
- Clear section headers
- Comparison tables where relevant
- Source citations with links
- Actionable recommendations
- No external dependencies (inline CSS/JS)

**Save to:** `/Users/creator/projects/<topic-slug>.html`

### Step 5: Preview + Deliver File

1. Open the HTML in browser to verify rendering
2. Take a screenshot for preview (`browser_vision` or `browser_navigate` + screenshot)
3. Send the **actual file** using `MEDIA:/path/to/file.html` in your response
4. On Telegram: the `MEDIA:` tag delivers the file natively to the user's phone

**IMPORTANT:** Always send the actual file, not just a preview screenshot. The user wants to open it on their phone/desktop. If vision analysis fails (rate limit), the screenshot is still capturable and shareable.

### Step 6: Save Supporting Artifacts

- Save research notes to Obsidian wiki if reusable
- Update project tracker if task was project-related
- Create a checklist/playbook if the research leads to implementation

## Pitfalls

- **Don't show only previews.** User explicitly asked "send me the actual file" after seeing only screenshots. Always deliver the .html via `MEDIA:` path.
- **Sub-agent file writes may fail** on first attempt due to allowed-directory resolution. Sub-agents should call `mcp_filesystem_list_allowed_directories()` before writing.
- **Vision analysis may hit rate limits.** Screenshot still works even when AI analysis fails. Fall back to screenshot-only preview.
- **Don't use `send_message` tool** — it doesn't exist. Use `MEDIA:` path in response for file delivery.
- **Extract key quotes from source docs** for credibility. Use `browser_console` to pull text content from documentation pages.
- **Web search/extraction may fail** (payment required). Fall back to `browser_navigate` + `browser_console` for content extraction.

## Example Output Structure

```
/Users/creator/projects/
  codex-linear-deep-dive.html          # main report
  papi-ai-operating-model.html         # operating model
  papi-ai-week1-review.html            # plan review packet
  openai-codex-research-summary.md     # sub-agent output
  linear-mcp-research.md               # sub-agent output
  codex-hermes-linear-workflows.html    # sub-agent output
```

## Related
- [[research-workflow]]
- [[writing-plans]]
- [[subagent-driven-development]]
