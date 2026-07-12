# Hermes Workflows

## Skill snapshots

- `Karan-skills/` — Hermes skills that are both classified as **local/custom** and recorded as used during the rolling last **60 days**. Usage means a successful `skill_view` load in the default or a specialist-profile session, or attachment to a cron job that ran in the window. Bundled and hub-installed skills are excluded. `scripts/sync_karan_skills.py` produces a deterministic manifest without timestamps or usage counts, so an unchanged selected set and unchanged source bytes produce no weekly commit.
- `Jake-skills/` — reserved empty folder for Jake’s skills. Its `.gitkeep` exists only because Git does not track empty directories.

The scheduled `Weekly Karan skills sync` job runs `scripts/weekly_sync_karan_skills.sh`. It refuses to overwrite a dirty or diverged `main` worktree and verifies the pushed commit against `origin/main`.
