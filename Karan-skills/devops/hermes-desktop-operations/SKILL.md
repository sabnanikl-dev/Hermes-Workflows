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

Use this for **operating** Hermes Desktop: diagnosing a stale installed app, rebuilding a git-installed desktop, locating current GUI features, and assigning skills/tools/MCP capabilities to profiles. It complements the protected `hermes-agent` umbrella. Use `hermes-desktop-plugins` to author plugins and `inspecting-hermes-desktop-dom` for live DOM/CSS inspection; neither owns update/install operations.

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

For exact probes, artifact paths, and a verified stale-install pattern, read `references/update-and-profile-capabilities.md`.

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
