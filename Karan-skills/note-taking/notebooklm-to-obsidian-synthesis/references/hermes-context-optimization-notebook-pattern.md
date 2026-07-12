# Hermes Context Optimization Notebook Pattern

Use this reference when querying a NotebookLM notebook about Hermes Agent startup token cost, context optimization, tool schemas, skill loading, or prompt bloat.

## Pattern

1. **Measure first, then ask NotebookLM**
   - Run or use an existing startup-token budget report before querying NotebookLM.
   - Separate system/developer prompt text from serialized tool schemas.
   - Treat saved session samples as potentially stale; prefer a fresh `/reset` or new session measurement when deciding config changes.

2. **Prompt NotebookLM with concrete local numbers**
   Include:
   - system prompt rough tokens;
   - tool schema rough tokens;
   - number of tools;
   - largest tool/MCP groups;
   - whether a lean session already exists for comparison.

3. **Cross-check against current Hermes state**
   NotebookLM sources may mention generic routers or older docs. Before recommending changes, inspect the current source/config when available:
   - `tools.tool_search.enabled` and whether progressive disclosure already exists;
   - platform toolset resolution (`no_mcp`, explicit MCP allowlists);
   - `agent.disabled_toolsets`;
   - configured global MCP servers;
   - whether prompt caching/compression affects billing/history but not first-turn schema footprint.

4. **Preserve operator intelligence**
   Do not recommend stripping core operator tools merely to save tokens unless there is a replacement operator path. For Karan's default Hermes, these are usually core: terminal, file, code execution, web, browser, skills, memory, session search, clarify, delegation, and todo.

5. **Distinguish safe config from product architecture**
   - Safe now: measure, keep `tool_search`/progressive disclosure enabled, use platform-level `no_mcp` or explicit MCP allowlists, and disable niche non-core toolsets only after confirming they are not needed.
   - Product work: dynamic tool routing, recall-on-miss, compact skill manifest, memory tiers, and compact identity modes.
   - Reject/postpone: disabling safety checks, removing core operator tools, aggressive compression as a first-turn fix, and mid-session toolset mutation that breaks prompt caching.

## Final synthesis shape

Return:
- measured baseline;
- NotebookLM source-grounded takeaways;
- current-state cross-check;
- prioritized reversible experiments;
- explicit risks and what not to change;
- verification metrics.

## Pitfall

Do not confuse *input token footprint* with *billed cost after prompt caching*. Caching can make repeated prefixes cheaper but does not remove first-turn context. Compression helps long sessions, not fresh-start tool schema bloat.
