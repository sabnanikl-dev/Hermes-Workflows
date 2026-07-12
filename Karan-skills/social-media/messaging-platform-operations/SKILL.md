---
name: messaging-platform-operations
description: Operate messaging-platform specific workflows from Hermes, including Yuanbao group mentions, member lookup, and DMs without confusing gateway auto-delivery semantics.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [messaging, yuanbao, mention, at, group, members, dm, 元宝, 派, 艾特]
---

# Messaging Platform Operations

Use this skill when the user asks Hermes to perform platform-specific messaging operations that differ from ordinary chat replies: group mentions, member lookup, direct messages, media DMs, or platform-specific gateway behavior.

The current rehomed playbook covers Yuanbao (元宝) groups. Add future platform quirks as labeled sections rather than creating a one-skill-per-platform micro-entry unless the platform becomes large enough to need its own package.

## General rules

- Understand whether a normal assistant reply is already delivered by the gateway. Do not call a send tool when the gateway auto-delivers the reply.
- For person lookup, use the platform's member/contact query tool before mentioning or DMing.
- If multiple users match, ask for clarification.
- Do not guess usernames, nicknames, IDs, or group codes when a lookup tool can retrieve them.
- Keep messaging replies concise and natural; do not explain mechanics unless the user asks.

## Yuanbao group interaction

### Critical delivery model

In Yuanbao group chats, your final text reply is the message sent to the group/user. The gateway automatically delivers it. You do not need a separate send-message tool for normal group replies.

When you include `@nickname` in the reply text, the gateway converts it into a real mention. Do not say you cannot @mention users; look up the nickname and include it in the reply.

### Available Yuanbao tools

| Tool | Use |
| --- | --- |
| `yb_query_group_info` | Query group name, owner, and member count. |
| `yb_query_group_members` | Find users, list bots, list members, and retrieve exact nicknames for mentions. |
| `yb_send_dm` | Send private/direct messages, optionally with media files. |

### Group code

Extract `group_code` from the current chat ID:

```text
group:328306697 -> 328306697
```

Groups are called "派 (Pai)" in the Yuanbao app.

### @mention workflow

1. Call `yb_query_group_members` with `action="find"`, the target name, and `mention=true`.
2. Use the exact nickname returned.
3. Include `@nickname` in your final reply text.

Example request: "帮我艾特元宝"

Tool call shape:

```json
{ "group_code": "328306697", "action": "find", "name": "元宝", "mention": true }
```

Final reply:

```text
@元宝 你好，有人找你！
```

### DM workflow

When the user asks to send a private message / 私信 / DM:

1. Call `yb_send_dm` with `group_code`, target `name` or known `user_id`, and `message`.
2. If multiple users match, ask the user to pick one.
3. Report the send result.

Example:

```json
{ "group_code": "535168412", "name": "用户aea3", "message": "hello" }
```

With media:

```json
{
  "group_code": "535168412",
  "name": "用户aea3",
  "message": "Here is the image",
  "media_files": [{"path": "/tmp/photo.jpg"}]
}
```

Do not use the generic `send_message` tool for Yuanbao DMs; use `yb_send_dm`.

### Member queries

| Action | Description |
| --- | --- |
| `find` | Search by partial, case-insensitive name. |
| `list_bots` | List bots and Yuanbao AI assistants. |
| `list_all` | List all members. |

Member roles include `user`, `yuanbao_ai`, and `bot`.

## Pitfalls

- Do not add disclaimers about mention permissions in Yuanbao. The gateway handles real mentions from `@nickname`.
- Do not explain the @mention workflow to the group; just send the requested message.
- Do not guess nickname spelling. Lookup first.
- Do not confuse group replies with DMs; DMs require `yb_send_dm`.
