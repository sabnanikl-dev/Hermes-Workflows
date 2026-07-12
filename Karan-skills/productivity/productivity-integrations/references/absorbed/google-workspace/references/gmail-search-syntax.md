# Gmail Search Syntax

Standard Gmail search operators work in the `query` argument.

## Common Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `is:unread` | `is:unread` | Unread messages |
| `is:starred` | `is:starred` | Starred messages |
| `is:important` | `is:important` | Important messages |
| `in:inbox` | `in:inbox` | Inbox only |
| `in:sent` | `in:sent` | Sent folder |
| `in:drafts` | `in:drafts` | Drafts |
| `in:trash` | `in:trash` | Trash |
| `in:anywhere` | `in:anywhere` | All mail including spam/trash |
| `from:` | `from:alice@example.com` | Sender |
| `to:` | `to:bob@example.com` | Recipient |
| `cc:` | `cc:team@example.com` | CC recipient |
| `subject:` | `subject:invoice` | Subject contains |
| `label:` | `label:work` | Has label |
| `has:attachment` | `has:attachment` | Has attachments |
| `filename:` | `filename:pdf` | Attachment filename/type |
| `larger:` | `larger:5M` | Larger than size |
| `smaller:` | `smaller:1M` | Smaller than size |

## Date Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `newer_than:` | `newer_than:7d` | Within last N days (d), months (m), years (y) |
| `older_than:` | `older_than:30d` | Older than N days/months/years |
| `after:` | `after:2026/02/01` | After date (YYYY/MM/DD) |
| `before:` | `before:2026/03/01` | Before date |

## Combining

| Syntax | Example | Description |
|--------|---------|-------------|
| space | `from:alice subject:meeting` | AND (implicit) |
| `OR` | `from:alice OR from:bob` | OR |
| `-` | `-from:noreply@` | NOT (exclude) |
| `()` | `(from:alice OR from:bob) subject:meeting` | Grouping |
| `""` | `"exact phrase"` | Exact phrase match |

## Common Patterns

```
# Unread emails from the last day
is:unread newer_than:1d

# Emails with PDF attachments from a specific sender
from:accounting@company.com has:attachment filename:pdf

# Important unread emails (not promotions/social)
is:unread -category:promotions -category:social

# Emails in a thread about a topic
subject:"Q4 budget" newer_than:30d

# Large attachments to clean up
has:attachment larger:10M older_than:90d
```

## Important Pitfalls

### `thread:<messageId>` does NOT work with `gmail search`

The `thread:` operator doesn't return results when used with the Gmail API's `list` messages endpoint via `google_api.py gmail search`. To check if a sent email has replies:
1. Use `gmail search "in:anywhere from:<recipient> newer_than:7d"` instead
2. Or search broadly for unread: `is:unread in:anywhere newer_than:7d`

### Sent emails have empty `to` and `subject` in `gmail get` output

When retrieving sent messages via `gmail get`, the API often returns empty `to` and `subject` fields. Recipient info must be inferred from the body content or by searching for replies from the other party.
