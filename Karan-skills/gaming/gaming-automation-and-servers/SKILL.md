---
name: gaming-automation-and-servers
description: "Use for gaming-related automation: hosting modded Minecraft servers and playing/automating games through headless emulators and RAM/state inspection."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gaming, minecraft, emulator, automation, servers]
    related_skills: []
---

# Gaming Automation and Servers

## Overview
Use this umbrella for gaming infrastructure and game-playing automation. It covers two recurring classes: hosting game servers and controlling games through emulators/state inspection.

## When to Use
- Set up or operate a modded Minecraft server from CurseForge/Modrinth packs.
- Automate or play a game through a headless emulator, including RAM reads or state probes.

## Subworkflows

### Modded servers
Identify modpack source/version, Java version, server requirements, memory, ports, EULA, and backup strategy. Start the server under a tracked process and verify readiness from logs or a connection check.

### Emulator play/automation
Use emulator state/RAM reads for grounded decisions. Save state frequently and verify actions with screenshots or memory values.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] Server/emulator process is actually running when claimed.
- [ ] Required files/modpacks/ROMs are present and legal to use.
- [ ] Readiness/progress is verified from logs, screenshots, or state probes.
