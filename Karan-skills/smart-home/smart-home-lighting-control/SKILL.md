---
name: smart-home-lighting-control
description: "Control smart-home lighting systems from Hermes, especially Philips Hue via OpenHue CLI: discovery, pairing, rooms, scenes, brightness, color, and scheduled lighting."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [smart-home, hue, lights, iot, automation, openhue, scenes, rooms]
---

# Smart-home Lighting Control

Use this skill when the user asks Hermes to control, inspect, automate, or schedule smart-home lights. The current implementation playbook is Philips Hue via the OpenHue CLI, but keep the class-level goal broader: discover controllable lighting resources, make the requested change safely, and verify the visible/device state where possible.

## When to use

- "Turn on/off the lights."
- "Dim the living room lights."
- "Set movie mode / bedtime / work mode."
- "List my Hue rooms/scenes/lights."
- Scheduled lighting via cron jobs.
- Diagnosing why Hue lights are not controllable from Hermes.

## OpenHue prerequisites

```bash
# macOS
brew install openhue/cli/openhue-cli

# Linux pre-built binary
curl -sL https://github.com/openhue/openhue-cli/releases/latest/download/openhue-linux-amd64 -o ~/.local/bin/openhue && chmod +x ~/.local/bin/openhue
```

First use requires pressing the physical Hue Bridge button to pair. The Hermes machine must be on the same local network as the bridge.

Check availability before promising control:

```bash
which openhue
openhue get light
```

## Discovery commands

```bash
openhue get light       # List lights
openhue get room        # List rooms
openhue get scene       # List scenes
```

Use discovery output for exact names; light and room names can be case-sensitive.

## Control commands

### Lights

```bash
openhue set light "Bedroom Lamp" --on
openhue set light "Bedroom Lamp" --off
openhue set light "Bedroom Lamp" --on --brightness 50
openhue set light "Bedroom Lamp" --on --temperature 300
openhue set light "Bedroom Lamp" --on --color red
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
```

### Rooms

```bash
openhue set room "Bedroom" --off
openhue set room "Bedroom" --on --brightness 30
```

### Scenes

```bash
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

## Useful presets

```bash
# Bedtime: dim warm
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# Work mode: bright cool
openhue set room "Office" --on --brightness 100 --temperature 250

# Movie mode: dim
openhue set room "Living Room" --on --brightness 10

# Everything off, adjusted to discovered rooms
openhue set room "Bedroom" --off
openhue set room "Office" --off
openhue set room "Living Room" --off
```

## Verification

After changing state, read the relevant resource again:

```bash
openhue get light
openhue get room
```

For scheduled/cron automations, write prompts self-contained with exact room/light names and desired state. If using a script-only cron, keep stdout silent unless an alert is needed.

## Pitfalls

- Do not guess exact light/room/scene names. Discover first.
- First pairing requires a physical bridge-button press; ask the user only when the CLI reports pairing is needed.
- Color commands only work for color-capable bulbs. Use brightness/temperature for white-only bulbs.
- If the bridge is on another network/VLAN, OpenHue discovery may fail even when the user can control lights from a phone app.
