# Pattern-First Closeout Tuning

Session learning: the first dry-run closeout report over-scored one-off observations as if they were durable memory recommendations. Karan clarified the intended model:

> The more Hermes dreams, the more patterns it recognizes. Candidates for memory, Hindsight, Obsidian, and skills should arise from repeated patterns, not one-off noticed things.

## Implementation shape

A dry-run collector can still surface candidates immediately, but the route should be staged:

- `Holographic staging: possible memory pattern`
- `Holographic staging: possible skill pattern`
- `Holographic staging: possible wiki/Hindsight pattern`
- `No-op / source-of-truth only`

Each candidate should carry:

```json
{
  "candidate": "...",
  "route": "Holographic staging: possible memory pattern",
  "trust": 0.40,
  "promotion_readiness": "needs more dreams",
  "pattern_key": "normalized recurring semantic shape",
  "pattern_observations": 1,
  "pattern_sources": 1,
  "source_type": "Hermes session",
  "source": "session id or URL",
  "rationale": "why it is staged and what would make it stronger"
}
```

Persist a lightweight pattern history such as `candidate-pattern-history.json` so future runs can raise scores only when the same pattern recurs.

## Threshold model

- First sighting: low score and `needs more dreams`.
- 3+ sightings: `emerging pattern`.
- 5+ sightings with sufficient score/source diversity: `ready for approval`.

The exact thresholds can change, but the principle should not: recurrence beats keyword matching.

## Good signs of a real pattern

- The same preference is expressed or corrected across sessions.
- The same verification/pitfall shows up in multiple tasks.
- A project fact matters in more than one workstream.
- A workflow lesson would prevent repeated user steering.
- Multiple source types agree: session correction + GitHub evidence + Obsidian note, etc.

## Bad signs / keep staged or no-op

- The candidate is just a PR title, issue status, branch name, or commit detail.
- The candidate says “we completed X today.”
- The candidate depends on a temporary environment failure.
- The candidate is simply a keyword match for “remember,” “prefer,” “skill,” or “verify.”

## Reporting language

Prefer language like:

- “Needs more dreams”
- “Emerging pattern”
- “Ready for approval”
- “Source-truth only”

Avoid implying that early-stage candidates should be written immediately.
