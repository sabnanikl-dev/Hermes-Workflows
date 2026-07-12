---
name: obsidian
description: Read, search, and create notes in the Obsidian vault.
---

# Obsidian Vault

**Location:** ~/obsidian-vault/hermes-brain/

**Note:** The vault is the Hermes Brain wiki, not a general workspace. See the `obsidian-wiki-maintenance` skill for full maintenance routines.

## Scripts

- `references/absorbed/obsidian/scripts/obsidian_hermes.sh` — Hermes wrapper for Obsidian CLI. It expands `OBSIDIAN_VAULT_PATH` safely, `cd`s into the Hermes Brain vault, and runs `obsidian` so commands target the correct vault without needing `vault=` every time.

```bash
GOB="~/.hermes/skills/note-taking/obsidian/scripts/obsidian_hermes.sh"
$GOB version
$GOB vault info=name
$GOB files total
```

## Default access pattern

Use Hermes file tools first for deterministic, headless-safe work:

- `read_file` for reading specific notes
- `search_files(target="files")` for listing/finding notes
- `search_files(target="content")` for content search
- `write_file` for creating full notes
- `patch` for targeted edits/appends

Do **not** use shell `cat`/`find`/`grep`/`ls`/heredocs for normal vault work; Hermes has safer tools for those.

## Optional Obsidian CLI backend

Obsidian CLI (`obsidian`) can complement file tools when Obsidian-native behavior matters. It is especially useful for link graph and metadata operations that raw filesystem tools do not understand.

**Requirements:**
- Obsidian 1.12.7+ installer
- Enable Settings → General → Command line interface
- Obsidian app must be running for normal CLI commands
- macOS registration creates `/usr/local/bin/obsidian`; Linux uses `~/.local/bin/obsidian`

Check availability:

```bash
command -v obsidian && obsidian version
GOB="~/.hermes/skills/note-taking/obsidian/scripts/obsidian_hermes.sh"
$GOB vault info=name
```

**Use Obsidian CLI for:**

```bash
GOB="~/.hermes/skills/note-taking/obsidian/scripts/obsidian_hermes.sh"

# Vault-native search/read/write
$GOB search query="meeting notes" format=json
$GOB read path="wiki/shared/projects/Project Status.md"
$GOB append path="wiki/shared/projects/Project Status.md" content="\n- New note"

# Link graph and health checks
$GOB unresolved format=json
$GOB unresolved total
$GOB orphans
$GOB deadends
$GOB backlinks path="wiki/shared/projects/Project Status.md" format=json
$GOB links path="wiki/shared/projects/Project Status.md"

# Obsidian-aware moves/renames (can update internal links if the vault setting is enabled)
$GOB rename path="wiki/shared/Old Name.md" name="New Name"
$GOB move path="wiki/shared/Old Name.md" to="wiki/shared/projects/New Name.md"

# Metadata, tags, tasks, templates
$GOB properties format=json
$GOB property:set path="wiki/shared/projects/Project Status.md" name=updated value=2026-05-01 type=date
$GOB tags counts format=json
$GOB tasks verbose format=json
$GOB create path="wiki/consultancy/research/New Tool.md" template=Research
```

**Default rule:** direct file tools remain the normal backend. Use Obsidian CLI only when the operation benefits from Obsidian's own link resolution, backlinks, unresolved-link detection, properties, tasks, templates, file history, or link-safe rename/move behavior.

## Obsidian-native authoring patterns

Use these condensed rules from `kepano/obsidian-skills` when creating or editing vault files. Do not import the full upstream skills by default; keep this skill compact and load extra references only when needed.

### Markdown notes

- Use `[[wikilinks]]` for internal vault notes and `[text](url)` only for external URLs.
- Common wikilink forms:
  - `[[Note Name]]`
  - `[[Note Name|Display Text]]`
  - `[[Note Name#Heading]]`
  - `[[Note Name#^block-id]]`
  - `[[#Heading in same note]]`
- Embeds use `![[...]]`, e.g. `![[image.png|300]]`, `![[document.pdf#page=3]]`, or `![[Note Name#Heading]]`.
- Callouts use quote syntax:
  ```markdown
  > [!note] Optional Title
  > Content here.

  > [!warning]- Collapsed by default
  > Details here.
  ```
- Properties/frontmatter belong at the top of notes. Keep Hermes Brain pages aligned with SCHEMA.md (`title`, `domain`, `type`, `status`, `created`, `updated`).
- Tags can be inline (`#nested/tag`) or in frontmatter. Tags may contain letters, underscores, hyphens, slashes, and numbers only after the first character.
- Obsidian comments use `%%hidden%%`; highlights use `==text==`; Mermaid diagrams render in fenced `mermaid` blocks.

### JSON Canvas (`.canvas`)

Use when Karan asks for a visual map, mind map, flowchart, or architecture canvas inside Obsidian.

- File shape: JSON object with `nodes` and `edges` arrays.
- IDs: unique 16-character lowercase hex strings.
- Nodes require `id`, `type`, `x`, `y`, `width`, `height`.
- Node types: `text` (`text` field), `file` (`file` path + optional `subpath`), `link` (`url`), `group` (`label` + optional background/color).
- Edges use `fromNode`, `toNode`, optional `fromSide`/`toSide` (`top|right|bottom|left`), optional `fromEnd`/`toEnd` (`none|arrow`), and optional `label`.
- Layout: `x` grows right, `y` grows down; align to 10/20px grid; leave 50-100px between nodes and 20-50px padding in groups.
- Validate before saving: JSON syntax, unique IDs, edge references point to existing nodes, required fields match node type.

### Obsidian Bases (`.base`)

Use only when Karan wants an Obsidian-native dashboard/database view. Do not replace Linear/GitHub/project repos as execution source of truth.

- Bases are YAML files with filters, formulas, properties, summaries, and views.
- Typical view types: `table`, `cards`, `list`, `map`.
- Quote strings containing YAML-special characters like `:`, `{`, `[`, `>`, `!`.
- Wrap formulas in single quotes when they contain double quotes: `status: 'if(done, "✅", "⏳")'`.
- Duration math needs a field: `(now() - file.ctime).days.round(0)`, not `(now() - file.ctime).round(0)`.
- Guard missing properties in formulas: `if(due_date, (date(due_date) - today()).days, "")`.
- Embed a base with `![[MyBase.base]]` or `![[MyBase.base#View Name]]`.

## Cost-effective backend hierarchy

1. **Direct Hermes file tools** — default for simple read/search/write/patch operations. Cheapest in tokens, deterministic, headless-safe, and does not require Obsidian to be open.
2. **Obsidian CLI through `references/absorbed/obsidian/scripts/obsidian_hermes.sh`** — use when Obsidian-native behavior saves work or improves correctness: unresolved links, backlinks, outgoing links, tags, properties, tasks, templates, screenshots/DOM for plugin work, and link-safe rename/move. Requires Obsidian app running and CLI enabled.
3. **Skills** — instruction/context layer, not an execution backend. Keep skills compact; load them when they prevent mistakes. Avoid importing large upstream skills wholesale because every loaded skill consumes context.
4. **MCP/plugins** — use only when they provide capabilities direct tools/CLI do not.

## Important
- Always start with index.md to navigate the wiki
- Never read the entire vault into context
- Load only specific pages needed for the current task
- Update index.md after adding/removing pages