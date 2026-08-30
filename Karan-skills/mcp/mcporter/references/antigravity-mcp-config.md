<!-- Archived source skill consolidated into `mcporter` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: antigravity-mcp-config
description: How to configure MCP servers in Antigravity IDE -- works around Docker unavailability and macOS GUI PATH inheritance issues.
version: 1.0.0
author: Hermes Agent
---

# MCP Server Configuration in Antigravity IDE

Antigravity's MCP configuration requires specific patterns due to environment constraints.

## Key Constraints

1. **No Docker available** -- `docker` is not on the PATH in Antigravity. Any MCP config using `docker` as the command will fail with `exec: "docker": executable file not found in $PATH`.
2. **Shell PATH not inherited** -- Antigravity MCP subprocesses do NOT inherit the user's shell PATH. Commands like `npx` and `node` may not be found unless you specify full paths and explicitly set PATH in env.
3. **Node.js available via Homebrew** -- Node and npm are installed at `/opt/homebrew/bin/`.

## Working Configuration Pattern

For any Node.js-based MCP server (e.g., GitHub, filesystem, etc.), use this exact pattern:

```json
"server-name": {
  "$typeName": "exa.cascade_plugins_pb.CascadePluginCommandTemplate",
  "command": "/opt/homebrew/bin/npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-github"
  ],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here",
    "PATH": "/opt/homebrew/bin:/usr/bin:/bin"
  }
}
```

### Critical Rules

1. **`command`** must be the full path `/opt/homebrew/bin/npx` -- not bare `npx`
2. **`args`** must be ONLY npx flags + package name: `["-y", "package-name"]`
   - NEVER include Docker flags like `-i`, `--rm`, `-e`, or `ghcr.io/...` images
   - These are Docker arguments that npx doesn't understand
3. **`env`** MUST include `"PATH": "/opt/homebrew/bin:/usr/bin:/bin"` so npx can find node
4. **`env`** includes any tokens required by the MCP server
5. **No Docker containers** -- use `npx` directly, not `docker run`

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `exec: "docker": executable file not found` | Using Docker-based config | Switch to npx config pattern above |
| `env: node: No such file or directory` | PATH not set in env, npx can't find node | Add `PATH` to env block |
| `exec: "npx": executable file not found` | Bare `npx` without full path | Use `/opt/homebrew/bin/npx` as command |
| `npm error code ENOENT ... package.json` | Docker flags in args confusing npm | Remove all Docker flags from args |

## Verified Working: GitHub MCP Server

```json
"github-mcp-server": {
  "$typeName": "exa.cascade_plugins_pb.CascadePluginCommandTemplate",
  "command": "/opt/homebrew/bin/npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_or_github_pat_...",
    "PATH": "/opt/homebrew/bin:/usr/bin:/bin"
  }
}
```

This was tested and confirmed working on April 15, 2026 with Antigravity IDE on macOS arm64 (Apple Silicon).