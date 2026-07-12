# Personal / Operating Repo Maintenance Loop

Companion reference for the "Working in a personal/operating repository" section of SKILL.md. Use this when the user opens a personal repo and gives broad permission to act, whether it's empty or already established.

## The verify-on-remote checklist

After ANY commit + push, before reporting success:

```bash
LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git ls-remote origin "$(git symbolic-ref --short HEAD)" | awk '{print $1}')
if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  echo "verified: $LOCAL_SHA is on remote"
else
  echo "MISMATCH — local=$LOCAL_SHA remote=$REMOTE_SHA — do not report pushed"
fi
```

For a PR-bound push:

```bash
gh pr view <n> --json commits --jq '.commits[-1].oid'   # confirm matches LOCAL_SHA
```

For a merge:

```bash
gh pr view <n> --json state,merged   # confirm "merged": true
```

Reporting "pushed" / "merged" without one of the above is the #1 source of false confirmations in self-directed repo work. The cost of the extra call is one second. The cost of recovery from a false confirmation is hours.

## Durable vs. stale: what belongs in an operating repo

A file belongs here if it would still be useful in 6 months without edits. If it would be stale in a week, it does not.

| Belongs (durable) | Does not belong (stale) |
|---|---|
| Operating principles, authority boundaries | "Phase N done" notes, task progress logs |
| Reusable checklists (pre/post-flight) | One-off PR/issue numbers |
| Decision records ("why we do X") | Current branch state, commit SHAs |
| Lessons learned (pattern + root cause + fix) | "Today I did Y" session journals |
| Reusable prompts and templates | Raw copies of recent chat transcripts |
| Validation scripts (`validate_repo.py`) | Generated artifacts, build outputs |
| Memory boundaries / what-goes-where docs | Secrets, tokens, credentials, OAuth material |

A useful heuristic: read the file's title and ask "would a fresh session benefit from this in 6 months?" If the answer requires knowing what happened this week, it doesn't belong.

## File types that pay off in operating repos

These hold their value across model swaps, session resets, and time:

- **`docs/lessons-learned.md`** — patterns the agent keeps rediscovering, each entry: trigger / root cause / fix. Edit when a lesson stops being true; add when a pattern shows up twice.
- **`docs/decision-log.md`** — durable decisions about the repo itself, with rationale and consequences. Append-only.
- **`docs/operating-principles.md`** — the agreement between user and agent for how this repo (or this class of work) gets handled.
- **`docs/authority-boundaries.md`** — what the agent is and isn't allowed to do unilaterally. Critical for self-directed sessions where the user isn't watching.
- **`docs/memory-boundaries.md`** — where each kind of durable fact lives (memory vs. Hindsight vs. skills vs. wiki vs. project repos). Prevents pollution.
- **`checklists/<name>.md`** — pre/post-flight steps the agent can actually re-read before acting.
- **`prompts/<name>.md`** — reusable session-starter prompts for the open-ended use case.
- **`scripts/validate_repo.py`** — local validation (required files present, no secret patterns, no trailing whitespace). The validator is the part you trust most because it can't lie.

## The performative-writing failure mode

The line between durable behavior-shaping content and self-indulgent prose is real. Catch it early:

- ✓ "After any external mutation, re-query the system of record and confirm the new state with its own tool before telling the user it's done."
- ✗ "I have learned to be more thoughtful and reflective about my actions in the world."

Every entry should map to a concrete failure mode with a concrete fix, or a concrete reusable artifact. If a file reads like a character document instead of a flight manual, it shouldn't be in the repo.

## When the user asks "what do you think / how do you feel about this repo?"

This is a real question, not small talk, and not a request for more files. Answer it honestly in plain text — what works, what to watch, what the repo is for in the broader system. Do not respond by writing more documentation about the repo. The reflection is the artifact in that moment; the commit isn't.
