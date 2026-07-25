"""Fresh isolated worktrees, and the guards that keep other checkouts safe.

:class:`SourceRepo` is a deliberately narrow view of the clone the run borrows
objects from. Only ``fetch``, ``rev-parse``, and ``worktree`` are reachable
through it, so the loop structurally cannot check out, commit, reset, or clean
in the operational clone. Everything else happens inside worktrees this run
created and owns.

Each worktree is created detached at one exact verified SHA. An existing path
is never reused: "fresh isolated worktree" means the path did not exist.
"""
from __future__ import annotations

import os
import stat
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .commands import CommandRunner
from .errors import StaleHead, WorktreeError
from .redaction import evidence as redact_evidence

_ALLOWED_GIT_SUBCOMMANDS = frozenset({"fetch", "rev-parse", "worktree"})
_WRITE_BITS = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


@dataclass
class SourceRepo:
    """Read-and-worktree-only access to the clone that supplies git objects."""

    runner: CommandRunner
    path: Path
    git: str = "git"
    timeout: float = 300.0

    def __post_init__(self) -> None:
        self.path = Path(self.path).expanduser().resolve()
        if not self.path.is_dir():
            raise WorktreeError(
                "source repository path is not a directory", evidence={"source_repo": str(self.path)}
            )
        if not (self.path / ".git").exists():
            raise WorktreeError(
                "source repository path is not a git checkout",
                evidence={"source_repo": str(self.path)},
            )

    def _git(self, args: Sequence[str], *, what: str) -> str:
        if not args or args[0] not in _ALLOWED_GIT_SUBCOMMANDS:
            raise WorktreeError(
                "git subcommand is not permitted against the source repository",
                evidence={
                    "subcommand": args[0] if args else "",
                    "allowed": sorted(_ALLOWED_GIT_SUBCOMMANDS),
                },
            )
        result = self.runner.run(
            [self.git, "-C", str(self.path), *args], timeout=self.timeout
        )
        if not result.ok:
            raise WorktreeError(
                f"git {what} failed in the source repository",
                evidence={
                    "argv": list(result.argv),
                    "returncode": result.returncode,
                    "stderr": redact_evidence(result.stderr, limit=1000),
                },
            )
        return result.stdout.strip()

    def fetch_branch(self, branch: str) -> None:
        """Update only this branch's remote-tracking ref. Nothing is checked out."""
        refspec = f"+refs/heads/{branch}:refs/remotes/origin/{branch}"
        self._git(["fetch", "--no-tags", "origin", refspec], what="fetch")

    def remote_head(self, branch: str) -> str:
        raw = self._git(
            ["rev-parse", "--verify", f"refs/remotes/origin/{branch}^{{commit}}"], what="rev-parse"
        )
        head = raw.strip().lower()
        if not _is_full_sha(head):
            raise WorktreeError(
                "remote head is not a full 40-hex SHA",
                evidence={"branch": branch, "rev_parse": redact_evidence(raw, limit=200)},
            )
        return head

    def verified_head(self, branch: str, expected_oid: str) -> str:
        """Fetch the branch and prove the remote head is exactly ``expected_oid``."""
        if not _is_full_sha(expected_oid):
            raise StaleHead(
                "expected head is not a full lowercase 40-hex SHA",
                evidence={"branch": branch, "expected_head": expected_oid},
            )
        self.fetch_branch(branch)
        actual = self.remote_head(branch)
        if actual != expected_oid:
            raise StaleHead(
                "remote branch head does not match the PR head this run is bound to",
                evidence={"branch": branch, "expected_head": expected_oid, "remote_head": actual},
            )
        return actual

    def add_worktree(self, path: Path, oid: str) -> None:
        self._git(["worktree", "add", "--detach", str(path), oid], what="worktree add")

    def remove_worktree(self, path: Path) -> None:
        self._git(["worktree", "remove", "--force", str(path)], what="worktree remove")


class WorktreeProvider:
    """Creates and removes the run's own worktrees, and only those."""

    def __init__(self, source: SourceRepo, root: Path) -> None:
        self.source = source
        self.root = Path(root).expanduser().resolve()
        if _contains(self.source.path, self.root) or _contains(self.root, self.source.path):
            raise WorktreeError(
                "worktree root overlaps the source repository; choose a path outside it",
                evidence={"worktree_root": str(self.root), "source_repo": str(self.source.path)},
            )
        self._created: list[Path] = []

    def create(self, label: str, oid: str) -> Path:
        """Create one fresh detached worktree at ``oid``."""
        if not label or any(character in label for character in "/\\ \t"):
            raise WorktreeError("worktree label must be a simple name", evidence={"label": label})
        if not _is_full_sha(oid):
            raise StaleHead(
                "refusing to create a worktree at a non-exact head",
                evidence={"label": label, "oid": oid},
            )
        path = (self.root / label).resolve()
        if not _contains(self.root, path):
            raise WorktreeError(
                "worktree path escaped the worktree root",
                evidence={"label": label, "path": str(path)},
            )
        if path.exists():
            raise WorktreeError(
                "worktree path already exists; every attempt needs a fresh worktree",
                evidence={"path": str(path)},
            )
        self.root.mkdir(parents=True, exist_ok=True)
        self.source.add_worktree(path, oid)
        self._created.append(path)
        return path

    def seal(self, path: Path) -> None:
        """Clear every write bit under ``path``. Used for reviewer worktrees.

        A linked worktree keeps its index and refs in the main repository's
        ``.git/worktrees/<name>`` directory, not in the checkout, so ``git
        status`` and ``git rev-parse`` still work against a sealed tree while an
        accidental edit, build artefact, or stray ``>`` fails at the filesystem.

        This is a guard, not a jail: on POSIX the owner of a file may always
        restore its write bit, so a determined same-user process can undo it.
        What makes reviewer isolation hold is structural — each reviewer gets a
        worktree of its own, so it has nothing of another reviewer's to touch —
        and what catches a reviewer that unsealed its own tree is the exact
        HEAD/tree/cleanliness check the loop runs afterwards.
        """
        self._own(path)
        for target in _walk(path):
            _chmod(target, lambda mode: mode & ~_WRITE_BITS)

    def unseal(self, path: Path) -> None:
        """Give the owner write access back, so the worktree can be removed."""
        self._own(path)
        for target in _walk(path):
            _chmod(target, lambda mode: mode | stat.S_IWUSR)

    def remove(self, path: Path) -> None:
        """Remove a worktree this provider created. Foreign paths are refused."""
        path = Path(path).resolve()
        if path not in self._created:
            raise WorktreeError(
                "refusing to remove a worktree this run did not create",
                evidence={"path": str(path)},
            )
        if path.exists():
            self.unseal(path)
        self.source.remove_worktree(path)
        self._created.remove(path)

    def _own(self, path: Path) -> Path:
        resolved = Path(path).resolve()
        if resolved not in self._created:
            raise WorktreeError(
                "refusing to change permissions on a worktree this run did not create",
                evidence={"path": str(resolved)},
            )
        return resolved

    @property
    def created(self) -> tuple[Path, ...]:
        return tuple(self._created)


def _walk(path: Path) -> list[Path]:
    """Every path under ``path``, deepest first, with ``path`` itself last."""
    root = Path(path)
    found: list[Path] = []
    for directory, subdirectories, files in os.walk(root, topdown=False, followlinks=False):
        base = Path(directory)
        found.extend(base / name for name in files)
        found.extend(base / name for name in subdirectories)
    found.append(root)
    return found


def _chmod(target: Path, change) -> None:
    """Apply ``change`` to a path's mode, skipping symlinks and vanished paths."""
    try:
        info = target.lstat()
    except OSError:  # pragma: no cover - the path vanished under us
        return
    if stat.S_ISLNK(info.st_mode):
        return
    try:
        target.chmod(stat.S_IMODE(change(info.st_mode)))
    except OSError:  # pragma: no cover - not worth failing a run over one path
        return


__all__ = ["SourceRepo", "WorktreeProvider"]
