#!/usr/bin/env python3.11
"""Mirror Hermes skills classified as local into this repository.

The selection matches ``hermes skills list --source local``: hub-installed and
bundled skills are excluded. A deterministic manifest is written alongside the
snapshot so an unchanged collection does not create a weekly Git commit.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = REPO_ROOT / "Karan-skills"
SKILLS_DIR = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser() / "skills"
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
    skills = local_skill_directories()
    if not skills:
        raise RuntimeError("No local Hermes skills were discovered; refusing to replace the snapshot.")

    with tempfile.TemporaryDirectory(prefix="karan-skills-", dir=REPO_ROOT) as temp:
        staging = Path(temp) / "Karan-skills"
        staging.mkdir()
        resolved_skills = []
        for name, source_dir in skills:
            try:
                relative = source_dir.relative_to(SKILLS_DIR)
            except ValueError as exc:
                raise RuntimeError(f"Skill {name} is outside {SKILLS_DIR}: {source_dir}") from exc
            resolved_skills.append((name, source_dir, relative))

        # Some umbrella skills contain separately-discoverable child skills. Copy
        # each enclosing directory once, then still record every discovered skill
        # in the manifest without duplicating its files.
        copy_roots = [
            entry for entry in resolved_skills
            if not any(
                entry[1] != candidate[1] and entry[1].is_relative_to(candidate[1])
                for candidate in resolved_skills
            )
        ]
        for _, source_dir, relative in copy_roots:
            shutil.copytree(source_dir, staging / relative, symlinks=False, ignore=ignored)

        manifest_skills = []
        for name, _, relative in resolved_skills:
            digest, file_count = sha256_tree(staging / relative)
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
            "schema_version": 1,
            "selection": "Hermes skills classified as local; hub-installed and bundled skills are excluded.",
            "source": "~/.hermes/skills",
            "skill_count": len(manifest_skills),
            "skills": manifest_skills,
        }
        (staging / ".sync-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        replace_snapshot(staging)

    print(f"Synced {len(skills)} local Hermes skills ({copied_files} files) into {TARGET_DIR}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Karan skills sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
