---
name: apple-macos-automation
description: "Use when automating macOS-native personal apps and desktop workflows: Notes, Reminders, iMessage/SMS, Find My, and background computer-use. Class-level umbrella for Apple-specific CLI and automation playbooks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [apple, macos, automation, notes, reminders, imessage, findmy, computer-use]
    related_skills: [hermes-agent]
---

# Apple / macOS Automation

## Overview
Use this umbrella when the task depends on macOS-native apps, Apple ecosystem data, or desktop control on the user's Mac. It consolidates formerly separate one-tool skills into one discoverable class-level workflow.

## When to Use
- Manage Apple Notes: create, search, or edit notes via `memo`.
- Manage Apple Reminders: list, create, or complete reminders via `remindctl`.
- Send/read iMessage or SMS via the local `imsg` CLI.
- Locate Apple devices/AirTags through Find My on macOS.
- Drive the macOS desktop in the background without stealing focus.

## Subworkflows

### Notes
Prefer the local Notes CLI (`memo`) when present. Search before creating duplicates, quote exact note titles in the final answer, and verify writes by reading the resulting note/listing.

### Reminders
Use `remindctl` for reminders. For ambiguous list names or dates, inspect existing lists first. After creating or completing a reminder, verify with a filtered list command.

### Messages
Use `imsg` for iMessage/SMS. Resolve recipients cautiously; do not send to a contact match without user confirmation when multiple plausible people exist. Report the exact recipient and send status.

### Find My
Use the Find My workflow only on macOS with the required local app/session available. Treat location data as sensitive; summarize minimally and avoid persisting coordinates unless requested.

### Background computer use
Use background-safe macOS automation for GUI tasks. Prefer app-specific CLIs first, screenshots/automation second. Verify visually or with app state after actions.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/` for detailed command examples and pitfalls.

## Verification Checklist
- [ ] Confirm the host is macOS before using Apple-only commands.
- [ ] Prefer app-specific CLIs before GUI automation.
- [ ] Verify every write/send/complete action with a readback or status check.
- [ ] Avoid exposing private note/message/location content beyond what the user requested.
