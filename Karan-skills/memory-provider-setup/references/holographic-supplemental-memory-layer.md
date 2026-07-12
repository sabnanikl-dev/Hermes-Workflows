# Holographic as a Supplemental Memory Layer

Use this when Karan wants to experiment with Holographic memory **without replacing** the existing memory stack.

## Positioning

Do **not** treat Holographic as a replacement for the current architecture unless Karan explicitly asks for a migration.

Preferred architecture:

- **Standard memory**: tiny, always-visible durable facts and preferences.
- **Hindsight**: long-range semantic recall across sessions/projects.
- **Obsidian / Hermes Brain**: structured project and business knowledge.
- **Skills**: reusable procedures and workflow lessons.
- **Holographic**: local, trust-scored staging and quality-control layer.

## Best Uses

Holographic is useful as a supplement for:

1. **Dream/closeout staging**
   - Store candidate lessons from recent sessions, completed Linear issues, and merged GitHub PRs.
   - Let repeated evidence raise confidence before promotion.

2. **Trust scoring**
   - Track confidence in candidate facts before they graduate to standard memory, Hindsight, Obsidian, or skills.

3. **Contradiction detection**
   - Surface conflicts between older assumptions and newer source-of-truth evidence.
   - Example: stale domain/deployment status, closed-vs-open tracker state, or changed workflow preferences.

4. **Memory hygiene**
   - Keep noisy/transient facts out of standard memory.
   - Use low trust or contradiction signals to recommend no-op, decay, or removal.

## Safe Experiment Pattern

Prefer testing in an isolated profile first:

```bash
hermes profile create memory-lab --clone default
hermes -p memory-lab memory setup
# choose holographic
hermes -p memory-lab memory status
```

Then run dry-run dream/closeout experiments only. Do not allow the lab profile to mutate the default profile's memory, skills, wiki, Linear, or GitHub unless Karan explicitly approves the scope.

## Dream Layer Shape

```text
Sessions + Linear + GitHub
        ↓
Closeout collector
        ↓
Holographic staging + trust scoring
        ↓
Dry-run dream report
        ↓
Approved promotion to:
  - Standard memory
  - Hindsight
  - Obsidian
  - Skills
  - No-op
```

## Guardrails

- Do not flip the default profile from Hindsight to Holographic casually.
- Do not duplicate Linear/GitHub task state into durable memory.
- Use Holographic to help decide what should graduate, not as the final source of truth.
- If a future Hermes version supports multiple external providers simultaneously, keep the same boundary: Holographic stages and scores; Hindsight remains semantic long-range recall unless Karan changes the architecture.
