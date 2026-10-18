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
hermes profile show <profile>
```

Use the CLI to verify or recover configuration, not to claim the GUI write succeeded without checking the GUI/profile state.

## Connecting a specialist to Telegram

1. Distinguish the existing local Hermes profile from a Telegram bot account: creating one does not create the other. Keep the default bot's token and routing untouched.
2. Direct the user to **main left sidebar → Messaging** (speech-bubble icon), not the bot's Edit Profile panel. The current Desktop command palette also exposes **Open messaging**; on macOS its default shortcut is **⌘K**. Check the installed version before asserting a missing UI element is present.
3. On Messaging, choose the target in **Configuring:**, then **Telegram → Create with QR** where supported. This user-interactive flow handles Telegram bot creation, token storage, and user allowlisting without copying a token through chat. If unavailable, use the official BotFather flow and a secure profile-local token entry path.
4. Have the user open the resulting Telegram bot and tap **Start**. Verify the target bot identity, profile routing, restricted user access, and an actual response before claiming the connection works. QR completion or a saved token alone is not end-to-end verification.
5. Treat gateway changes as a separate operational step; do not restart the default gateway or create a competing standalone gateway merely because a profile inspection reports stopped.

## Recovering a rejected profile model

1. Read the exact provider, model identifier, HTTP detail, and retryable flag. An explicit model-entitlement rejection means the selected model is unsupported for that account/route; it does not by itself imply expired login, broken Telegram, or a broken picker.
2. Run `hermes profile list` and `hermes profile show <profile>`, then read that profile's `config.yaml`. Compare the persisted provider/model with the rejected request. Inspect only relevant recent logs, not whole log files.
3. If the saved setting and Desktop behavior disagree, inspect the affected session rows read-only in the profile's `state.db`: `model`, `source`, and parsed `model_config`. `follow_profile_config: true` is evidence that the conversation follows profile settings; an old row's model is historical evidence, not proof of the live agent's current selection. Check explicit session/composer overrides before changing any stored session state. Ask whether the picker fails to open, rejects the selection, or reverts when the symptom is still ambiguous.
4. For an authorized recovery, restore a previously verified model on the same provider with `hermes -p <profile> config set model.default '<verified-model-id>'`. Do not silently change provider, billing route, credentials, or unrelated profiles.
5. Exercise the saved setting without a command-line model override:
   ```bash
   hermes -p <profile> chat --oneshot --quiet --toolsets '' \
     --max-turns 2 --run-budget 90 \
     -q 'Do not use tools. Reply exactly: MODEL_OK'
   hermes profile show <profile>
   ```
   A real `MODEL_OK` response plus profile readback proves the saved route works. A tool-free test does not prove the specialist's tools or Desktop model picker work.
6. Separately verify the affected Desktop conversation. If direct observation is unavailable, report the successful CLI recovery and the unverified Desktop behavior explicitly; do not present reopening the chat or a slash command as an already-proven picker repair. Preserve the conversation rather than deleting it or resetting the profile as a first response.
