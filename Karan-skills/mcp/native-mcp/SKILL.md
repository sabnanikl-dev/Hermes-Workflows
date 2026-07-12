---
name: native-mcp
description: Built-in MCP (Model Context Protocol) client that connects to external MCP servers, discovers their tools, and registers them as native Hermes Agent tools. Supports stdio and HTTP transports with automatic reconnection, security filtering, and zero-config tool injection.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) static HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP OAuth (OAuth 2.1 / PKCE)

Hermes also supports OAuth for HTTP MCP servers. Use `auth: oauth` plus an `oauth:` block. Field names are snake_case (not Gemini CLI's camelCase):

```yaml
mcp_servers:
  server_name:
    url: "https://provider.example.com/mcp/v1"
    auth: oauth
    oauth:
      client_id: "OAUTH_CLIENT_ID"        # optional for dynamic-registration providers; required for pre-registered clients such as Google
      client_secret: "OAUTH_CLIENT_SECRET"# confidential/desktop clients only
      scope: "scope.one scope.two"        # space-separated OAuth scope string
      redirect_port: 0                    # 0 = auto-pick local callback port; or pin a port
      client_name: "Hermes Agent"         # optional
      timeout: 300                        # optional OAuth flow timeout seconds
```

OAuth tokens/client info are stored per MCP server under Hermes' MCP OAuth storage. Initial authorization requires an interactive browser/local callback flow; after that, cached tokens refresh automatically. In non-interactive gateways, complete OAuth once from an interactive CLI session before expecting tools to connect at startup.

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `auth`            | string | `""`   | Set to `oauth` for HTTP OAuth/PKCE servers        |
| `oauth`           | dict   | `{}`    | OAuth settings: `client_id`, `client_secret`, space-separated `scope`, `redirect_port`, `client_name`, `timeout` |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Proven Setup Workflow

For multi-server MCP rollouts, use this sequence:

1. Research each server's current official transport/package. Do not assume an MCP server has an npm package; verify with `npm view <package> version` or the official README.
2. For rapidly moving Python MCP packages, verify the **stable published package**, not only GitHub `main` docs: check PyPI `provides_extra`, install into an isolated `uv tool` env, and confirm the expected executable exists with `command -v <server-command>`. Some READMEs describe unreleased extras or entrypoints before they are available on PyPI.
3. Inspect existing `~/.hermes/config.yaml` and `.env` for structure and variable names, but never print secret values.
4. Create a timestamped backup before editing:
   ```bash
   cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)
   ```
4. Add servers under top-level `mcp_servers:`.
5. Validate YAML with an available parser, for example:
   ```bash
   ruby -e 'require "yaml"; c=YAML.load_file(File.expand_path("~/.hermes/config.yaml")); puts c.fetch("mcp_servers").keys.sort.join(",")'
   ```
   Do not rely on system `python3` having PyYAML; in one setup attempt `import yaml` failed outside the Hermes venv.
6. Test each server before claiming success:
   ```bash
   hermes mcp list
   hermes mcp test <server_name>
   ```
7. If native MCP tools are already injected in the current session, verify one low-risk tool call directly (for example `mcp_filesystem_list_allowed_directories` or `mcp_github_get_me`).
8. Store durable environment findings in Hindsight or compact memory, not as temporary task progress.

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Google Workspace MCP: discovery works but tool calls timeout or OAuth says protected resource mismatch

Google Workspace MCP discovery is not enough to prove the server is usable. Google's servers may initialize and list tools even when cached OAuth tokens are missing or stale, so always verify one low-risk real tool call before reporting success. If actual calls hang until timeout while `hermes mcp test` succeeds, inspect `~/.hermes/mcp-tokens/`: `.client.json` and `.meta.json` files are only client/metadata; the usable cached token is `~/.hermes/mcp-tokens/<server>.json`. See `references/google-workspace-oauth-tool-call-timeouts.md` for the diagnostic and re-auth workflow.

For Workspace operations where MCP OAuth remains flaky or you need a CLI-first, auditable control plane, use the Google Workspace CLI (`gws`) as the fallback/primary operator. See `references/google-workspace-gws-fallback.md` for install, OAuth client setup, narrow-scope login, callback timing, and verification commands.

For NotebookLM MCP/CLI selection and auth workflows, see `references/notebooklm-mcp-selection.md`. Key pitfall: verify PyPI extras and entrypoints before wiring an MCP server; `notebooklm-py` may have CLI support before stable MCP support, while another NotebookLM package may expose the same `notebooklm-mcp` executable name.

Google's Workspace MCP endpoints are path-based resources such as `https://gmailmcp.googleapis.com/mcp/v1`, `https://drivemcp.googleapis.com/mcp/v1`, and `https://calendarmcp.googleapis.com/mcp/v1`. If logs show:

```text
Protected resource https://gmailmcp.googleapis.com/mcp/v1 does not match expected https://gmailmcp.googleapis.com
```

then the client is stripping the `/mcp/v1` path before passing the server URL into the MCP SDK OAuth provider. Root fix in Hermes: `tools/mcp_oauth.py::_parse_base_url()` must preserve the path and only remove URL fragments. Add/verify a regression test for path preservation.

Also distinguish **server discovery** from **authenticated tool calls**: `hermes mcp test google_*` may list tools without proving a real Gmail/Drive/Calendar call can read data. Verify with one low-risk actual tool call after OAuth, e.g. `mcp_google_people_get_user_profile`, `mcp_google_gmail_list_labels`, or `mcp_google_calendar_list_calendars`.

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### CodeGraph MCP connects but cannot answer project questions

If `hermes mcp test codegraph` succeeds but CodeGraph tools report no project loaded or no `.codegraph/` directory, distinguish three layers before declaring the MCP broken:

1. **Server availability:** `hermes mcp test codegraph` only proves the MCP server starts and exposes tools.
2. **Workspace/path resolution:** CodeGraph may be launched from `$HOME` unless the MCP config passes `serve --mcp --path /absolute/project` or the client provides roots.
3. **Project index:** CodeGraph still needs a per-project `.codegraph/` index created by `codegraph init` / `codegraph init -i` somewhere.

When the user prefers CLI over MCP, do not fight the MCP path/root issue. Use `codegraph` as a global CLI (`npm i -g @colbymchenry/codegraph` or `npx -y @colbymchenry/codegraph@<version> ...`) and run commands from the intended project directory. The CLI can be global, but the semantic index is project-specific, like `git` vs `.git/`.

Do not initialize `.codegraph/` in a repo without user approval. Offer safe options:
- add `.codegraph/` to the user's global gitignore, then initialize locally;
- create/index a temporary mirror for read-only exploration;
- or skip CodeGraph and use normal file/search tools for repos where no index is wanted.

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

Scope filesystem access narrowly; do not expose the whole home directory. For Karan's Hermes setup, the proven safe baseline is projects plus the Hermes Brain vault:

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem@2026.1.14"
      - "/Users/creator/projects"
      - "/Users/creator/obsidian-vault/hermes-brain"
    connect_timeout: 60
    timeout: 120
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`. Verify the scope with `mcp_filesystem_list_allowed_directories` after restart/discovery.

### GitHub Server with Authentication

The official `github/github-mcp-server` does **not** currently provide a reliable npm/npx package. Prefer the official remote endpoint when available, using a token from `.env` rather than hardcoding secrets:

```yaml
mcp_servers:
  github:
    url: "https://api.githubcopilot.com/mcp/"
    headers:
      Authorization: "Bearer ${GITHUB_TOKEN}"
    connect_timeout: 60
    timeout: 120
```

Local fallback options are the official Docker image or building the Go binary from source. Do not assume `@modelcontextprotocol/server-github` or `@github/github-mcp-server` exists on npm without checking `npm view` first.

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)
