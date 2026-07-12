# CodeGraph adoption for agent workflows

Use this reference when evaluating or rolling out CodeGraph-style repository indexing/static-analysis tools for builder and reviewer agents.

## Deep-dive pattern

1. Split discovery agents by durable concern, not file count:
   - upstream tool architecture and CLI/MCP surface
   - parser/index/data model and language coverage
   - UI/export/reporting surface
   - operational fit: install, cache/index location, config, CI implications
   - target repo fit: GodMode, Femme Events, JMD, Hermes-related repos
2. Require each agent to return:
   - exact files inspected
   - commands run
   - what was verified vs inferred
   - limitations and repo-specific risks
   - concrete adoption recommendation
3. Synthesize into an artifact that can be handed to both humans and agents: TL;DR, tool explanation, repo-by-repo fit, adoption roadmap, smoke tests, caveats.

## External agent rollout pattern

For manual external coding agents, distinguish the agent host from Hermes profiles:

- **Claude Code builder**: configure Claude's own MCP config, not Hermes profile config.
- **Codex reviewer**: configure Codex's own MCP config, not Hermes profile config.
- Keep the server invocation pinned, e.g. `npx -y @colbymchenry/codegraph@<version> serve --mcp`.
- Create timestamped backups before changing manual-agent configs.
- Verify config syntax and runtime registration independently:
  - Claude: JSON parses and `mcpServers.codegraph` exists; runtime-test if `claude` CLI is available.
  - Codex: `codex mcp list` shows `codegraph` enabled.

## Repo onboarding guidance

- Add `.codegraph/` or equivalent local index/cache directory to `.gitignore` unless the tool explicitly documents a safe checked-in artifact.
- Keep generated indexes local per repo; do not commit unless a deliberate architecture decision says otherwise.
- Give builder/reviewer agents read-only smoke prompts before permitting edits:
  - Builder: explain a known lifecycle or feature path using CodeGraph and name key files.
  - Reviewer: identify regression risks around a known function or API surface and call out missing tests.

## Pitfalls

- Do not report a tool as adopted until both the config file and agent-specific registration are verified.
- Do not treat local MCP availability inside Hermes as proof that Claude Code/Codex can see the same server; each host has its own config boundary.
- Do not preserve environment-specific failures as durable rules. Capture the reusable fix or verification pattern instead.
