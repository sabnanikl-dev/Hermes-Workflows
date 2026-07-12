#!/usr/bin/env python3.11
"""Mirror recently used local Hermes skills into this repository.

A skill qualifies when Hermes classifies it as ``local`` and either:

* a successful ``skill_view`` result for it was recorded in the default or a
  specialist profile session during the rolling usage window; or
* a cron job that explicitly attaches it ran during the rolling usage window.

Bundled and hub-installed skills are excluded. The manifest intentionally has
no generation timestamp, cutoff timestamp, usage count, or last-used timestamp:
re-running with the same selected skill set and source bytes must produce no
Git diff.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = REPO_ROOT / "Karan-skills"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
SKILLS_DIR = HERMES_HOME / "skills"
CRON_JOBS_FILE = HERMES_HOME / "cron" / "jobs.json"
USAGE_WINDOW_DAYS = int(os.environ.get("KARAN_SKILLS_USAGE_WINDOW_DAYS", "60"))
EXCLUDED_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp", ".swo"}


def ignored(_directory: str, names: list[str]) -> set[str]:
    """Exclude local caches, VCS data, and secret-bearing dotenv/key files."""
    skipped: set[str] = set()
    for name in names:
        lower = name.lower()
        if (
            name in EXCLUDED_NAMES
            or name == ".env"
            or lower.startswith(".env.")
            or lower.endswith((".pem", ".key", ".p12", ".pfx"))
            or Path(name).suffix.lower() in EXCLUDED_SUFFIXES
        ):
            skipped.add(name)
    return skipped


def sha256_tree(root: Path) -> tuple[str, int]:
    """Return a stable digest and file count for a copied skill bundle."""
    digest = hashlib.sha256()
    files = [path for path in root.rglob("*") if path.is_file()]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), len(files)


def local_skill_directories() -> list[tuple[str, Path]]:
    """Resolve active default-profile skills whose provenance is ``local``."""
    try:
        from agent.skill_utils import iter_skill_index_files
        from tools.skills_hub import HubLockFile
        from tools.skills_sync import _read_manifest
        from tools.skills_tool import _parse_frontmatter
    except ImportError as exc:
        raise RuntimeError(
            "Hermes Python modules are unavailable. Run with the Python used by Hermes."
        ) from exc

    if not SKILLS_DIR.is_dir():
        raise RuntimeError(f"Hermes skills directory does not exist: {SKILLS_DIR}")

    hub_names = {entry["name"] for entry in HubLockFile().list_installed()}
    bundled_names = set(_read_manifest())
    selected: dict[str, Path] = {}

    for skill_md in iter_skill_index_files(SKILLS_DIR, "SKILL.md"):
        skill_dir = skill_md.parent
        try:
            frontmatter, _ = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        name = str(frontmatter.get("name") or skill_dir.name).strip()
        if not name or name in hub_names or name in bundled_names:
            continue
        # Hermes discovery resolves duplicate names by the first on-disk match.
        selected.setdefault(name, skill_dir)

    return sorted(selected.items(), key=lambda item: item[0].casefold())


def session_databases() -> list[Path]:
    """Return default and specialist-profile session stores."""
    databases = [HERMES_HOME / "state.db"]
    profiles_dir = HERMES_HOME / "profiles"
    if profiles_dir.is_dir():
        databases.extend(sorted(profiles_dir.glob("*/state.db")))
    return [path for path in databases if path.is_file()]


def skill_view_usage(cutoff_epoch: float) -> set[str]:
    """Read successful skill_view results from all available session stores."""
    used: set[str] = set()
    databases = session_databases()
    if not databases:
        raise RuntimeError("No Hermes session databases were found; refusing to prune skills.")

    readable = 0
    for database in databases:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        try:
            rows = connection.execute(
                "SELECT content FROM messages "
                "WHERE tool_name = 'skill_view' AND timestamp >= ? "
                "AND content IS NOT NULL",
                (cutoff_epoch,),
            )
            readable += 1
            for (content,) in rows:
                try:
                    result = json.loads(content)
                except (TypeError, json.JSONDecodeError):
                    continue
                name = result.get("name")
                if result.get("success") is True and isinstance(name, str) and name.strip():
                    used.add(name.strip())
        except sqlite3.DatabaseError as exc:
            raise RuntimeError(f"Could not read skill usage from {database}: {exc}") from exc
        finally:
            connection.close()

    if readable == 0:
        raise RuntimeError("No Hermes session database could be read; refusing to prune skills.")
    return used


def parse_iso_epoch(value: object) -> float | None:
    """Parse Hermes ISO timestamps, including timezone offsets and trailing Z."""
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def executed_cron_skill_usage(cutoff_epoch: float) -> set[str]:
    """Include skills attached to cron jobs that actually ran in the window."""
    if not CRON_JOBS_FILE.is_file():
        return set()
    try:
        payload = json.loads(CRON_JOBS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read cron skill usage from {CRON_JOBS_FILE}: {exc}") from exc

    used: set[str] = set()
    for job in payload.get("jobs", []):
        last_run_epoch = parse_iso_epoch(job.get("last_run_at"))
        if last_run_epoch is None or last_run_epoch < cutoff_epoch:
            continue
        candidates = list(job.get("skills") or [])
        if job.get("skill"):
            candidates.append(job["skill"])
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                used.add(candidate.strip())
    return used


def recently_used_skill_names(now_epoch: float | None = None) -> set[str]:
    """Return names with recorded use during the rolling configured window."""
    if USAGE_WINDOW_DAYS < 1:
        raise RuntimeError("KARAN_SKILLS_USAGE_WINDOW_DAYS must be at least 1.")
    now_epoch = time.time() if now_epoch is None else now_epoch
    cutoff_epoch = now_epoch - (USAGE_WINDOW_DAYS * 86400)
    return skill_view_usage(cutoff_epoch).union(executed_cron_skill_usage(cutoff_epoch))


def replace_snapshot(staging: Path) -> None:
    """Atomically replace only Karan-skills, preserving sibling repository data."""
    backup = REPO_ROOT / ".Karan-skills.backup"
    if backup.exists():
        shutil.rmtree(backup)
    if TARGET_DIR.exists():
        TARGET_DIR.rename(backup)
    try:
        staging.rename(TARGET_DIR)
    except Exception:
        if backup.exists():
            backup.rename(TARGET_DIR)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def main() -> int:
    all_local_skills = local_skill_directories()
    if not all_local_skills:
        raise RuntimeError("No local Hermes skills were discovered; refusing to replace the snapshot.")

    used_names = recently_used_skill_names()
    skills = [entry for entry in all_local_skills if entry[0] in used_names]
    if not skills:
        raise RuntimeError(
            f"No local Hermes skills have recorded use in the last {USAGE_WINDOW_DAYS} days; "
            "refusing to replace the snapshot."
        )

    with tempfile.TemporaryDirectory(prefix="karan-skills-", dir=REPO_ROOT) as temp:
        staging = Path(temp) / "Karan-skills"
        staging.mkdir()

        all_resolved: list[tuple[str, Path, Path]] = []
        for name, source_dir in all_local_skills:
            try:
                relative = source_dir.relative_to(SKILLS_DIR)
            except ValueError as exc:
                raise RuntimeError(f"Skill {name} is outside {SKILLS_DIR}: {source_dir}") from exc
            all_resolved.append((name, source_dir, relative))

        resolved_skills = [entry for entry in all_resolved if entry[0] in used_names]

        # Some umbrella skills contain separately discoverable child skills. Copy
        # each selected enclosing directory once, then prune any unselected child
        # skill directory that arrived only because its used parent was copied.
        copy_roots = [
            entry
            for entry in resolved_skills
            if not any(
                entry[1] != candidate[1] and entry[1].is_relative_to(candidate[1])
                for candidate in resolved_skills
            )
        ]
        for _, source_dir, relative in copy_roots:
            shutil.copytree(source_dir, staging / relative, symlinks=False, ignore=ignored)

        selected_paths = {entry[2] for entry in resolved_skills}
        for name, _, relative in sorted(all_resolved, key=lambda item: len(item[2].parts), reverse=True):
            if name in used_names:
                continue
            destination = staging / relative
            contains_selected_descendant = any(
                selected != relative and selected.is_relative_to(relative)
                for selected in selected_paths
            )
            if destination.is_dir() and not contains_selected_descendant:
                shutil.rmtree(destination)

        manifest_skills = []
        for name, _, relative in resolved_skills:
            destination = staging / relative
            skill_md = destination / "SKILL.md"
            if not skill_md.is_file():
                raise RuntimeError(f"Selected skill {name} was not copied correctly: {skill_md}")
            digest, file_count = sha256_tree(destination)
            manifest_skills.append(
                {
                    "name": name,
                    "path": relative.as_posix(),
                    "files": file_count,
                    "sha256": digest,
                }
            )

        copied_files = sum(1 for path in staging.rglob("*") if path.is_file())
        manifest = {
            "schema_version": 2,
            "selection": (
                "Hermes skills classified as local with recorded use during the rolling "
                f"last {USAGE_WINDOW_DAYS} days; hub-installed and bundled skills are excluded."
            ),
            "usage_window_days": USAGE_WINDOW_DAYS,
            "usage_evidence": [
                "successful skill_view results in default and specialist-profile session databases",
                "skills attached to cron jobs whose last_run_at falls within the usage window",
            ],
            "source": "~/.hermes/skills",
            "skill_count": len(manifest_skills),
            "skills": manifest_skills,
        }
        (staging / ".sync-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        replace_snapshot(staging)

    print(
        f"Synced {len(skills)} recently used local Hermes skills "
        f"({copied_files} files; rolling {USAGE_WINDOW_DAYS}-day window) into {TARGET_DIR}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Karan skills sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
