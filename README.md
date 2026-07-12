# Hermes Workflows

## Skill snapshots

- `Karan-skills/` — Hermes skills that the local Hermes installation classifies as **local** (custom). Bundled and hub-installed skills are intentionally excluded. `scripts/sync_karan_skills.py` produces its deterministic manifest; the weekly sync only commits when that snapshot changes.
- `Jake-skills/` — reserved empty folder for Jake’s skills. Its `.gitkeep` exists only because Git does not track empty directories.

The scheduled `Weekly Karan skills sync` job runs `scripts/weekly_sync_karan_skills.sh`. It refuses to overwrite a dirty or diverged `main` worktree and verifies the pushed commit against `origin/main`.
