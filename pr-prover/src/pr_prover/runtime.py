"""Fresh per-lane runtime directories, and trusted resolution of every program.

Two shared mutable surfaces used to sit between lanes.

The first was the capability shim. One directory was written once per
:class:`~.launchers.LaunchBroker` and put on the front of every lane's ``PATH``,
so reviewer A ran, then the builder ran, then reviewer B ran — all three
executing the same file. A lane that could write to it could hand the next lane
a different program under the name the next lane trusts. Now every launch gets
its own :class:`LaneRuntime`: a fresh directory, inside that launch's own lane
directory, with a freshly written shim.

The write bits come off once it is built, and that is worth stating precisely:
it is not the boundary. A lane's descendants run as the same user that owns
these files, and the same user can put a mode bit back. What actually keeps a
lane out of its own runtime — and out of every other lane's — is that the
runtime is not in the lane's writable set in the sandbox document
(:mod:`.sandbox`), which the OS enforces against the process rather than against
the file. The mode bits are the second lock, and :meth:`LaneRuntime.assert_intact`
is a tripwire on it: a runtime found writable immediately before a spawn means
something reopened it, and the launch stops.

The second was ``PATH`` itself. A child inherited the operator's, so a lane
resolved ``git``, ``gh``, ``node``, and its own agent program through whatever
directories the operator happened to have — including writable ones, and
including another lane's runtime if it were ever put there. A child's ``PATH``
is now this lane's runtime followed by :data:`TRUSTED_SYSTEM_PATH` and nothing
else.

Removing the operator's ``PATH`` from the child does not by itself say which
file ``claude`` or ``make`` meant, so the launcher resolves every configured
program to an absolute path *before* the launch, checks it, and passes that
absolute path as ``argv[0]``. :func:`resolve_program` requires the resolved path
to be a regular file the owner may execute, not group- or world-writable, not
inside any lane runtime, and it records a :class:`Fingerprint` — device, inode,
size, mode, and modification time. :meth:`Fingerprint.assert_unchanged` is
called again immediately before the spawn, so a program swapped between
validation and launch fails closed rather than running.
"""
from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

from .capabilities import SHIM_NAME, write_shim
from .errors import LaunchPolicyError

# The child's whole system ``PATH``. Short, absolute, and owned by root on every
# platform this runs on. The operator's ``PATH`` is not part of it.
TRUSTED_SYSTEM_PATH = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")

_GROUP_OR_WORLD_WRITABLE = stat.S_IWGRP | stat.S_IWOTH


@dataclass(frozen=True)
class Fingerprint:
    """Identity of one executable at the moment it was checked."""

    path: str
    device: int
    inode: int
    size: int
    mode: int
    mtime_ns: int

    @classmethod
    def of(cls, path: Path) -> Fingerprint:
        info = Path(path).lstat()
        return cls(
            path=str(path),
            device=info.st_dev,
            inode=info.st_ino,
            size=info.st_size,
            mode=stat.S_IMODE(info.st_mode),
            mtime_ns=info.st_mtime_ns,
        )

    def assert_unchanged(self, *, what: str) -> None:
        """Re-check the file. Anything different is a different program."""
        try:
            current = Fingerprint.of(Path(self.path))
        except OSError as exc:
            raise LaunchPolicyError(
                "the program this lane validated is no longer readable",
                evidence={"what": what, "program": self.path, "error": str(exc)},
            ) from exc
        if current != self:
            raise LaunchPolicyError(
                "the program this lane validated changed between validation and launch",
                evidence={
                    "what": what,
                    "program": self.path,
                    "validated": self.as_dict(),
                    "found": current.as_dict(),
                },
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "device": self.device,
            "inode": self.inode,
            "size": self.size,
            "mode": oct(self.mode),
            "mtime_ns": self.mtime_ns,
        }


@dataclass(frozen=True)
class TrustedProgram:
    """One configured program, resolved to an absolute path and fingerprinted."""

    requested: str
    path: str
    fingerprint: Fingerprint

    def assert_unchanged(self, *, what: str) -> None:
        self.fingerprint.assert_unchanged(what=what)


class LaneRuntime:
    """One launch's own runtime directory: a fresh shim, then stripped of writes.

    The directory is created inside that launch's own lane directory, the shim is
    written into it, and both are then stripped of their write bits. No other
    lane has it on its ``PATH``, no other lane can reach it through the sandbox,
    and this lane cannot write it either. The mode bits are defence in depth
    rather than the boundary — a same-user process can restore them, which is why
    the sandbox document is what the claim rests on.
    """

    def __init__(self, root: Path, *, label: str, sequence: int) -> None:
        self.label = label
        self.directory = Path(root) / f"{sequence:03d}-{label}"
        if self.directory.exists():
            raise LaunchPolicyError(
                "this lane's runtime directory already exists; every launch gets a "
                "fresh one, so an existing path is another lane's runtime",
                evidence={"lane": label, "runtime": str(self.directory)},
            )
        self.bin = self.directory / "bin"
        self.bin.mkdir(parents=True)
        self.shim = write_shim(self.bin)
        if self.shim.name != SHIM_NAME:  # pragma: no cover - a build-time invariant
            raise LaunchPolicyError(
                "the capability shim was written under an unexpected name",
                evidence={"expected": SHIM_NAME, "found": self.shim.name},
            )
        self.shim.chmod(0o500)
        self.bin.chmod(0o500)
        self.directory.chmod(0o500)

    def child_path(self) -> str:
        """The child's whole ``PATH``: this lane's runtime, then trusted system paths."""
        return os.pathsep.join([str(self.bin), *TRUSTED_SYSTEM_PATH])

    def assert_intact(self) -> None:
        """Prove nothing replaced the shim or reopened the directory for writing."""
        for path, what in ((self.shim, "capability shim"), (self.bin, "runtime directory")):
            try:
                info = Path(path).lstat()
            except OSError as exc:
                raise LaunchPolicyError(
                    f"this lane's {what} is missing",
                    evidence={"lane": self.label, "path": str(path), "error": str(exc)},
                ) from exc
            if stat.S_ISLNK(info.st_mode):
                raise LaunchPolicyError(
                    f"this lane's {what} is a symbolic link",
                    evidence={"lane": self.label, "path": str(path)},
                )
            if stat.S_IMODE(info.st_mode) & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
                raise LaunchPolicyError(
                    f"this lane's {what} is writable; a later lane could replace what "
                    "this one runs",
                    evidence={"lane": self.label, "path": str(path), "mode": oct(info.st_mode)},
                )

    def release(self) -> None:
        """Give the write bits back so the launcher can remove its scratch tree."""
        for path in (self.shim, self.bin, self.directory):
            try:
                Path(path).chmod(stat.S_IMODE(Path(path).lstat().st_mode) | stat.S_IWUSR)
            except OSError:  # pragma: no cover - a vanished path is already released
                continue


def resolve_program(
    program: str,
    *,
    search_path: str | None,
    what: str,
    base: Path | str | None = None,
    forbidden_roots: tuple[Path, ...] = (),
) -> TrustedProgram:
    """Resolve one configured program name to a trusted absolute path.

    A bare name is looked up on ``search_path``. A path is resolved against
    ``base`` — the lane's working directory — so that a repository-owned gate may
    still be written as ``./scripts/gate.sh`` and yet be launched as one absolute
    path chosen now, rather than as a name re-resolved later against a directory
    the lane itself could change.

    Either way the result is fully resolved, so what comes back is the file that
    will actually be executed rather than the symbolic link that names it, and
    that file is then checked: a regular file, executable by its owner, not
    writable by group or world, reached only through directories that are not
    group- or world-writable without the sticky bit, and not inside a lane
    runtime this launcher owns.
    """
    if not program or program.strip() != program:
        raise LaunchPolicyError(
            "a configured program name must be a bare, unpadded string",
            evidence={"what": what, "program": program},
        )
    if os.sep in program or program.startswith("~"):
        candidate = Path(program).expanduser()
        if not candidate.is_absolute():
            if base is None:
                raise LaunchPolicyError(
                    "a configured program given as a relative path needs a lane working "
                    "directory to resolve against",
                    evidence={"what": what, "program": program},
                )
            candidate = Path(base) / candidate
        found: str | None = str(candidate)
    else:
        found = shutil.which(program, path=search_path)
    if not found:
        raise LaunchPolicyError(
            "this lane's program is not on the launcher's trusted search path",
            evidence={"what": what, "program": program, "search_path": search_path or ""},
        )

    resolved = Path(found).resolve()
    try:
        info = resolved.lstat()
    except OSError as exc:
        raise LaunchPolicyError(
            "this lane's program could not be inspected",
            evidence={"what": what, "program": program, "path": str(resolved), "error": str(exc)},
        ) from exc
    if stat.S_ISLNK(info.st_mode):  # pragma: no cover - resolve() removed every link
        raise LaunchPolicyError(
            "this lane's program still resolves to a symbolic link",
            evidence={"what": what, "path": str(resolved)},
        )
    if not stat.S_ISREG(info.st_mode):
        raise LaunchPolicyError(
            "this lane's program is not a regular file",
            evidence={"what": what, "path": str(resolved), "mode": oct(info.st_mode)},
        )
    if not info.st_mode & stat.S_IXUSR:
        raise LaunchPolicyError(
            "this lane's program is not executable by its owner",
            evidence={"what": what, "path": str(resolved), "mode": oct(info.st_mode)},
        )
    if info.st_mode & _GROUP_OR_WORLD_WRITABLE:
        raise LaunchPolicyError(
            "this lane's program is writable by group or world, so another process "
            "could replace what this lane runs",
            evidence={"what": what, "path": str(resolved), "mode": oct(info.st_mode)},
        )
    text = str(resolved)
    _assert_trusted_parents(resolved, what=what)
    for root in forbidden_roots:
        try:
            resolved.relative_to(Path(root).resolve())
        except ValueError:
            continue
        raise LaunchPolicyError(
            "this lane's program resolves inside a launcher-owned lane runtime; a lane "
            "cannot be handed a program another lane could have written",
            evidence={"what": what, "path": text, "runtime_root": str(root)},
        )
    if resolved.name == SHIM_NAME:
        raise LaunchPolicyError(
            "this lane's program is the capability shim; the shim is the launcher's, "
            "not a lane's command line",
            evidence={"what": what, "path": text},
        )
    return TrustedProgram(requested=program, path=text, fingerprint=Fingerprint.of(resolved))


def _assert_trusted_parents(resolved: Path, *, what: str) -> None:
    """No directory on the way to a program may be swappable by another user.

    Group- or world-writable is the test, with one exception: a sticky directory
    (``/tmp`` and friends) lets anyone create files but lets only the owner
    replace or remove one, which is exactly the property that matters here.
    """
    for parent in resolved.parents:
        try:
            info = parent.lstat()
        except OSError:  # pragma: no cover - a parent of an existing file exists
            return
        mode = stat.S_IMODE(info.st_mode)
        if mode & _GROUP_OR_WORLD_WRITABLE and not mode & stat.S_ISVTX:
            raise LaunchPolicyError(
                "this lane's program is reached through a directory another user can "
                "write to, so what runs is not decided by the launcher",
                evidence={"what": what, "path": str(resolved), "directory": str(parent), "mode": oct(mode)},
            )


def resolution_path(parent_path: str | None) -> str:
    """Where the launcher looks a configured program name up.

    The operator's ``PATH`` is used to *find* a program, because the operator is
    who named it, and then dropped: it never becomes the child's. Trusted system
    directories are appended so a lookup still works when the launcher itself was
    started with an empty environment.
    """
    parts = [part for part in (parent_path or "").split(os.pathsep) if part]
    parts.extend(entry for entry in TRUSTED_SYSTEM_PATH if entry not in parts)
    return os.pathsep.join(parts)


__all__ = [
    "TRUSTED_SYSTEM_PATH",
    "Fingerprint",
    "LaneRuntime",
    "TrustedProgram",
    "resolution_path",
    "resolve_program",
]
