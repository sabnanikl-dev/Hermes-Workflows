---
name: hermes-desktop-operations
description: "Use when operating Hermes Desktop profiles or updates."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, desktop, updates, profiles, skills, capabilities]
    related_skills: [hermes-agent, hermes-desktop-plugins, inspecting-hermes-desktop-dom]
---

# Hermes Desktop Operations

## Purpose

Use this for **operating** Hermes Desktop: diagnosing a stale installed app, rebuilding a git-installed desktop, locating current GUI features, assigning skills/tools/MCP capabilities to profiles, and safely retiring unused profiles/Bot Mode bots. It complements the protected `hermes-agent` umbrella. Use `hermes-desktop-plugins` to author plugins and `inspecting-hermes-desktop-dom` for live DOM/CSS inspection; neither owns update/install operations.

## Core distinction

Hermes has separate artifacts and clocks:

- The Hermes Agent CLI/source checkout.
- The packaged Desktop build under the source checkout.
- The installed macOS app, commonly `/Applications/Hermes.app`.

A successful `hermes update` or an “up to date” CLI does **not by itself prove** that the installed Desktop app contains the current source. Desktop and CLI version strings may also differ intentionally, and two Desktop builds can carry the same `CFBundleShortVersionString`. Verify the actual installed artifact and requested feature rather than reasoning from one version number.

## Update and stale-feature workflow

1. **Establish the symptom.** Name the missing feature or behavior; do not treat a version mismatch alone as the bug.
2. **Inspect before mutating.** Check the CLI/source revision, installed app path, packaged build path, app version strings, binary modification times, and whether current source actually contains the requested feature.
3. **Check upstream state.** Use `hermes update --check` and, when services are live, `hermes update --plan`. Do not run the mutating update just to diagnose Desktop.
4. **Build the current source when needed.** For a git install whose source already contains the feature:
   ```bash
   hermes desktop --build-only --force-build
   ```
   The macOS ARM artifact is normally:
   `~/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app`.
5. **Separate build from install.** A successful build does not replace `/Applications/Hermes.app`. Replacing an installed app quits a user-facing process and mutates `/Applications`; obtain explicit approval, preserve a rollback copy, then install the packaged artifact.
6. **Relaunch and verify the requested feature.** Read back the installed app metadata and confirm the actual UI feature is present. Never report success from build output alone.

For exact probes, artifact paths, profile-scoped Telegram setup, and model-entitlement recovery, read `references/update-and-profile-capabilities.md`.

## Navigation and troubleshooting evidence

- Give the complete entry point when directing Karan through Desktop: main sidebar versus Edit Profile versus Settings, then the target profile selector. A page name alone is insufficient when the user is inside a bot editor.
- When a control is missing, inspect the live UI if available; otherwise offer the command-palette route supported by the installed version and ask for a screenshot if it still differs. Do not repeat speculative click paths or infer that the app needs updating solely from a missing control.
- Separate provider rejection, saved profile configuration, session overrides, and picker behavior. Recover the bounded configuration problem with a real profile-scoped request, but do not report the Desktop picker fixed until an actual Desktop switch and response have been observed.
- Keep recovery narrowly scoped to the affected profile. Preserve the exact rejected model identifier in diagnostics; choose a separately verified supported model rather than guessing spelling or capitalization repairs. Do not reset credentials or restart shared services for a model-specific entitlement rejection.
- When a fresh profile can call Codex but its Desktop model editor shows only Anthropic, compare profile-scoped `hermes_cli.inventory.build_model_options_payload(load_picker_context(), explicit_only=True)` with default, then test `refresh=True`. A Codex row with `models: []` is hidden by `ModelVisibilityDialog`'s nonempty-model filter. Inspect `model_switch_providers._auth_store_has_provider` / `_credential_pool_is_usable`: picker-local auth discovery can miss root-shared OAuth even though the runtime's provider-state fallback succeeds. Treat this as a discovery/runtime mismatch, not proof of lost entitlement. Do not copy single-use OAuth tokens or promise a cache refresh fixes it; require a verified scoped fix.

## Assigning skills to profiles in Desktop

A Bot Mode bot is a Hermes profile. Each profile owns an independent skills directory and enable/disable state.

### Main Capabilities page (preferred)

1. Open **Capabilities** from the Desktop sidebar.
2. Use the **Configuring:** selector to choose the target profile. The selector appears when more than one profile is available.
3. Open **Skills**.
4. Toggle an installed skill on or off.
5. If absent, install it from the Skills Hub shown beneath the installed-skills list while the target profile is selected.
6. Start a **new session** for that profile.

The same selected profile scopes the Skills, Tools, and MCP tabs. Do not switch the whole app merely to configure another profile.

### Bot Mode route

1. Right-click the bot row.
2. Choose **Edit Profile**.
3. Expand **Advanced — model, skills, toolsets, SOUL.md**.
4. In **Capabilities**, enable/install Skills and configure Tools or MCP for that bot.
5. Save model/SOUL edits. Capability toggles on current builds apply immediately to profile configuration.
6. Start a new bot chat/session to receive the new capability catalog.

### New Bot route

In **New Bot → Advanced**, choose whether to clone another profile or start fresh. Opening **Capabilities** materializes the draft profile so installations and toggles have a real profile target. Avoid enabling a broad default set merely because it is available; keep specialist profiles role-scoped and least-privilege.

## Retiring unused profiles and Bot Mode bots

1. **Inventory before choosing deletions.** Run `hermes profile list`; inspect each candidate's cron store, running work, service registrations, and command wrappers. A stopped standalone gateway does not prove inactivity: shared Desktop/gateway scheduling can still execute profile-local jobs. Check default-profile jobs for dependencies on the candidates. Distinguish local Bot Mode profiles from external Telegram/Discord bot accounts; shared platform credentials must not be revoked when keeping default Hermes.
2. **Approve an explicit keep/delete set.** Keep `default` and its existing messaging connections, credentials, skills, memories, and scheduled jobs intact. Include obsolete custom launchers in the scope, but do not equate retiring a Hermes profile with retiring Claude/Codex tools. Record hashes of protected default files and stable job definitions for after-change comparison; do not compare changing run timestamps as configuration drift.
3. **Back up to Karan's external NVMe before deletion.** Discover the actual mount with `diskutil list external physical` and inspect it with `diskutil info <mount>`; do not assume a remembered path is mounted or silently fall back to the internal disk. Create one clearly named recovery directory containing profile archives, affected launcher copies, and a verification manifest. Use `hermes profile export <name> --output '<backup-dir>/<name>.tar.gz'`. Treat these as credential-redacted recovery exports, not exact credential-complete snapshots: the exporter excludes credential files and redacts staged text. Explain that restoration needs credential setup. ExFAT does not enforce macOS Unix permissions; do not describe chmod as backup protection or imply redaction removes every sensitive business datum.
4. **Verify backups before removing sources.** Fully read every gzip/tar stream, check expected profile roots and identity files, and record archive sizes plus SHA-256 hashes. A successful export or a nonempty file alone is insufficient. Preserve custom wrapper scripts separately because profile exports do not include `~/.local/bin` launchers.
5. **Decouple retained tools first.** Search launchers and their helper scripts for candidate-profile paths. An independently used Codex launcher may store its isolated HOME inside a Hermes reviewer profile. Relocate that retained directory outside `profiles/`, such as `~/.local/share/codex-reviewer/home`, update the launcher, check shell syntax, and run a bounded live smoke test. Separate verified relocation from model-service authentication success; an unrelated sign-in failure must not be reported as a passing runtime test or prompt credential copying.
6. **Delete through the supported CLI, one profile at a time.** Use `hermes profile delete <name> --yes` only for the approved set. Prefer individually observable calls over a nested bulk deletion script, so a partial failure has an exact recovery boundary. The native command handles services, tombstones, wrappers, and identity cleanup; do not substitute raw directory removal. Check for leftover custom wrappers that the CLI did not recognize and remove only the specifically approved, backed-up ones.
7. **Settle partial deletions without repeating destructive work.** If the directory is gone but the CLI reports pending session/routing identity settlement, inspect `hermes profile purge-identity --help`, run `hermes profile purge-identity <name>`, and verify success and continued directory absence. Do not recreate the profile to clear this error. If the tool approval gate blocks deletion, stop mutations and report exactly which profiles were removed and which remain; ordinary chat approval does not justify retrying a denied command through another mechanism.
8. **Close out against live state.** Re-run `hermes profile list`, verify retired directories/wrappers are absent, compare protected default files and job definitions, and confirm default Telegram/Discord connection state. Report the external backup path, what was actually removed, and any separately blocked smoke test. Do not claim the Desktop roster refreshed unless observed. Include restoration guidance using `hermes profile import <archive>` with explicit warnings to review restored cron jobs and reconnect credentials before resuming operation.

## CLI-created Bot Mode specialists

When creating a minimal specialist without the GUI, use `hermes profile create <name> --no-skills --description '...'` instead of cloning broad credentials, memory, and capabilities. Read the generated config before changing it; a fresh profile may already inherit the selected model at creation. Verify authentication with a real bounded read-only turn rather than copying OAuth files.

For roster presentation, set the profile-local `profile.yaml` mapping `ui_meta.hermes-bots.title` (and `hidden: false`). Current canonical Bot Chats are identified by the exact session title `Bot Chat`, not a stored session-id pointer. A real setup/intro session can be named with `hermes -p <name> sessions rename <id> 'Bot Chat'`, pinned with `sessions pin`, and hidden through the native profile-scoped `SessionDB.set_session_hidden(id, True)` API; read back title/hidden/pinned afterward. Do not add legacy `ui_meta.hermes-bots.chat` pointers. Verify the live version's canonical-chat contract before using this path.

Recheck the actual installed skill catalog after a fresh launch: `--no-skills` / `.no-bundled-skills` can still coexist with the runtime-provided core `hermes-agent` skill. Report the observed catalog rather than promising exactly one skill. A successful model reply is not proof of tool execution; inspect persisted tool calls and successful results in the profile state DB when session JSON is absent. Desktop metadata and canonical-chat verification do not prove a rendered roster was visually inspected.

## Semantics that prevent confusion

- **Installed** means the skill exists in that profile’s skill tree.
- **Enabled** means it appears in the profile’s available skill catalog.
- **Available** does not mean forced into every response; the agent loads a relevant skill when triggered.
- `/skill <name>` is a session-level explicit load, not a substitute for installing/enabling the skill on the profile.
- Existing conversations retain their original prompt/tool catalog for cache correctness. Profile capability changes apply cleanly to new sessions.

## Verification checklist

- [ ] The selected GUI profile is the intended target, including its gateway/connection when remote.
- [ ] The skill is installed in that profile, not only in `default`.
- [ ] The skill toggle reads enabled after the write.
- [ ] A fresh session for that profile lists or can load the skill.
- [ ] For Desktop updates, the installed app—not only the release build—was read back.
- [ ] The originally missing feature is visible after relaunch.

## Safety

- Do not silently quit Desktop, overwrite `/Applications/Hermes.app`, broaden profile allowlists, or install third-party/sensitive skills without the user’s approval.
- Prefer role-native capabilities. Default Hermes/Karan remains the authority for permanent profile allowlist expansion.
- Do not infer a stale app from `0.17.0` versus CLI `0.21.0`; verify source, build, installed artifact, and feature presence.
