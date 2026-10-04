# Desktop update and profile-capability runbook

## Why version strings are insufficient

Hermes Desktop can be stale even when the CLI reports “up to date.” A git update refreshes the source/CLI, while the packaged Desktop artifact and `/Applications/Hermes.app` may remain older. The Desktop package version can also remain unchanged across many source commits, so comparing `CFBundleShortVersionString` alone cannot prove feature parity.

Use the requested feature as the acceptance criterion. For Bot Mode, current source should contain `apps/desktop/src/plugins/hermes-bots/` and the built renderer should include that plugin.

## Read-only probes

```bash
hermes --version
hermes update --check
hermes update --plan

/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  /Applications/Hermes.app/Contents/Info.plist

/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  ~/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app/Contents/Info.plist

stat -f '%Sm' /Applications/Hermes.app/Contents/MacOS/Hermes
stat -f '%Sm' ~/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app/Contents/MacOS/Hermes
```

Also inspect current source for the named feature. A newer packaged binary timestamp than the installed binary is evidence of a stale installation, not proof by itself that the feature works.

## Build

```bash
hermes desktop --build-only --force-build
```

Success must identify the packaged executable under `apps/desktop/release/`. Build warnings about an unchanged package version do not invalidate a feature build; build/test errors do.

## Install boundary

Building is internal. Quitting Desktop and replacing `/Applications/Hermes.app` is an external, user-visible mutation. Obtain approval and preserve rollback. After replacement:

1. Read back the installed app version and binary timestamp.
2. Relaunch the installed path.
3. Verify the feature in the GUI.
4. If the feature is still absent, check whether the app launched from another path or whether the relevant plugin/capability is disabled; do not rebuild repeatedly without new evidence.

## Profile capability routes

### Global page

**Sidebar → Capabilities → Configuring: `<profile>` → Skills**

- Toggle installed skills.
- Install missing skills from the Hub while the correct profile is selected.
- The same scope controls Tools and MCP.
- Start a new profile session after changes.

### Bot Mode

**Right-click bot → Edit Profile → Advanced — model, skills, toolsets, SOUL.md → Capabilities → Skills**

A bot row maps to a profile. Embedded Capabilities is pinned to that bot/profile, avoiding accidental writes to `default`.

## CLI fallback for verification

When the GUI state is ambiguous, inspect the target explicitly:

```bash
hermes -p <profile> skills list
hermes -p <profile> skills config
hermes -p <profile> profile
```

Use the CLI to verify or recover configuration, not to claim the GUI write succeeded without checking the GUI/profile state.
