#!/usr/bin/env bash
# Weekly no-agent cron entry point for the rolling 60-day Karan-skills snapshot.
# It intentionally refuses to overwrite a dirty or diverged main worktree.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

blocked() {
  printf 'Karan skills sync blocked: %s\n' "$1"
  exit 0
}

[[ "$(git branch --show-current)" == "main" ]] || blocked "repository is not on main"
[[ -z "$(git status --porcelain)" ]] || blocked "repository has uncommitted changes"

git fetch origin main --quiet
LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse origin/main)"
if [[ "$LOCAL_SHA" != "$REMOTE_SHA" ]]; then
  git merge-base --is-ancestor HEAD origin/main || blocked "local main has diverged from origin/main"
  git pull --ff-only origin main --quiet || blocked "could not fast-forward main"
fi

python3.11 scripts/sync_karan_skills.py >/dev/null
# The snapshot is byte-for-byte source content, including any pre-existing
# whitespace in custom skill reference files. Check only the sync-controlled
# files here; the Python sync + manifest validate the mirrored skill tree.
git diff --check -- README.md scripts Jake-skills

if git diff --quiet -- Karan-skills; then
  exit 0
fi

SKILL_COUNT="$(python3.11 -c 'import json; print(json.load(open("Karan-skills/.sync-manifest.json"))["skill_count"])')"
git add Karan-skills
git commit -m "chore: sync Karan skills"
git push origin main --quiet

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$LOCAL_SHA" == "$REMOTE_SHA" ]] || { printf 'Karan skills sync failed: remote main verification mismatch\n' >&2; exit 1; }

printf 'Karan skills sync: pushed %s recently used local skills from the rolling 60-day window (%s).\n' "$SKILL_COUNT" "$LOCAL_SHA"
