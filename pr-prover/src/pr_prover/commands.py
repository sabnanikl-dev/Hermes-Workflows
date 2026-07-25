"""The single child-process boundary: argv arrays only, never a shell string.

Every child the loop launches — baseline gates, reviewer lanes, the builder
lane, ``git``, ``gh`` — is built here as a validated argv array. Templates
substitute only a closed set of ``{placeholder}`` tokens, so no configured or
reviewer-supplied value can ever be re-parsed as syntax.

:class:`CommandRunner` is the injection seam. PAPI-90 replaces
:class:`SubprocessRunner` with a credential-scoped launcher; PAPI-88 only
requires that the boundary exists and that argv discipline is enforced here.

**In-flight children are cancellable.** :class:`LaunchWatch` is an optional
handle a caller passes in to learn which process groups a runner currently has
open, and to tear all of them down at once. The capability broker uses it so
that closing a lane's channel does not return while a ``git push`` or a ``gh
api`` it accepted is still running (see :mod:`.capabilities`). A runner that
supports it advertises ``supports_watch``; one that does not — every test double
in this package, for instance — is simply called without it.

**A lane is a process group, not a process.** An agent lane runs shells, which
run build tools, which run servers. Killing only the process the runner started
leaves those descendants alive holding the lane's working directory, its
capability channel, and whatever the timeout was meant to stop. So every child
is started in its own session (:func:`os.setsid` via ``start_new_session``), and
the group is torn down on *every* exit path — normal completion, timeout,
``KeyboardInterrupt``, and any other exception — with ``SIGTERM`` first, a
bounded wait, then ``SIGKILL``. :meth:`SubprocessRunner.run` does not return
until the group is gone, which is what lets a caller remove the lane's scratch
and capability socket knowing nothing is still holding them.
"""
from __future__ import annotations

import errno
import os
import re
import signal
import subprocess
import threading
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .errors import CommandContractError

_PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")

# How long a process group gets to honour SIGTERM before it is killed, and how
# long the whole teardown may take. Both are small: by the time a group is being
# torn down the run has already decided it is finished with that lane.
TERM_GRACE_SECONDS = 5.0
KILL_GRACE_SECONDS = 5.0


class LaunchWatch:
    """The process groups one owner currently has open, and a way to end them.

    A runner registers each group as it starts and forgets it once the group is
    gone. :meth:`cancel` latches: after it returns, every group registered so far
    has been terminated and any group registered later is terminated as soon as
    it appears, so there is no window in which a caller that has already decided
    to stop can still acquire a live child.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._open: dict[int, "subprocess.Popen[str] | None"] = {}
        self._cancelled = False
        self.terminated: list[int] = []

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    @property
    def open_groups(self) -> tuple[int, ...]:
        with self._lock:
            return tuple(sorted(self._open))

    def opened(self, group: int | None, process: "subprocess.Popen[str] | None" = None) -> bool:
        """Register a group. False when the owner has already cancelled."""
        if group is None:
            return not self.cancelled
        with self._lock:
            if not self._cancelled:
                self._open[group] = process
                return True
        # Cancelled while this child was starting, so it never gets to run.
        terminate_group(group, process)
        with self._lock:
            self.terminated.append(group)
        return False

    def closed(self, group: int | None) -> None:
        if group is None:
            return
        with self._lock:
            self._open.pop(group, None)

    def cancel(
        self,
        *,
        term_grace: float = TERM_GRACE_SECONDS,
        kill_grace: float = KILL_GRACE_SECONDS,
    ) -> tuple[int, ...]:
        """Terminate every open group and refuse every future one. Returns the groups."""
        with self._lock:
            self._cancelled = True
            pending = dict(self._open)
            self._open.clear()
        for group, process in pending.items():
            terminate_group(group, process, term_grace=term_grace, kill_grace=kill_grace)
        with self._lock:
            self.terminated.extend(pending)
        return tuple(sorted(pending))


@dataclass(frozen=True)
class CommandResult:
    """The outcome of one child process."""

    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def validate_argv(argv: object, *, what: str = "command") -> tuple[str, ...]:
    """Accept only a non-empty sequence of non-empty strings.

    A ``str`` is rejected explicitly: accepting one is exactly how a shell
    string sneaks back into the loop.
    """
    if isinstance(argv, (str, bytes)):
        raise CommandContractError(
            f"{what} must be an argv array, not a string",
            evidence={"what": what, "type": type(argv).__name__},
        )
    if not isinstance(argv, (list, tuple)):
        raise CommandContractError(
            f"{what} must be an argv array",
            evidence={"what": what, "type": type(argv).__name__},
        )
    if not argv:
        raise CommandContractError(f"{what} argv array is empty", evidence={"what": what})
    parts: list[str] = []
    for index, item in enumerate(argv):
        if not isinstance(item, str):
            raise CommandContractError(
                f"{what} argv[{index}] is not a string",
                evidence={"what": what, "index": index, "type": type(item).__name__},
            )
        if item == "":
            raise CommandContractError(
                f"{what} argv[{index}] is empty", evidence={"what": what, "index": index}
            )
        if "\x00" in item:
            raise CommandContractError(
                f"{what} argv[{index}] contains a NUL byte",
                evidence={"what": what, "index": index},
            )
        parts.append(item)
    return tuple(parts)


class ConfigPlaceholderError(CommandContractError):
    """A template referenced a placeholder the loop does not provide."""

    reason = "invalid-command"

    def __init__(self, key: str, what: str, known: Iterable[str]) -> None:
        super().__init__(
            f"{what} template uses unknown placeholder {{{key}}}",
            evidence={"what": what, "placeholder": key, "known": list(known)},
        )


def render_argv(
    template: Sequence[str], values: Mapping[str, str], *, what: str = "command"
) -> tuple[str, ...]:
    """Substitute ``{placeholder}`` tokens from a closed vocabulary.

    Unknown placeholders fail closed rather than rendering literally, and no
    format specs, indexing, or attribute access are supported, so a value can
    never reach through into the template.
    """
    rendered: list[str] = []
    for item in validate_argv(template, what=what):

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in values:
                raise ConfigPlaceholderError(key, what, sorted(values))
            return values[key]

        rendered.append(_PLACEHOLDER.sub(replace, item))
    return validate_argv(rendered, what=what)


class CommandRunner(Protocol):
    """Injection seam for launching children.

    ``watch`` is deliberately absent from this signature: it is an optional
    extension a runner opts into by setting ``supports_watch``, so that the
    doubles in this package's tests stay the two-line objects they are.
    """

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult: ...


def run_watched(
    runner: CommandRunner,
    argv: Sequence[str],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
    watch: LaunchWatch | None = None,
) -> CommandResult:
    """Call ``runner.run``, passing ``watch`` only to a runner that accepts it."""
    if watch is not None and getattr(runner, "supports_watch", False):
        return runner.run(argv, cwd=cwd, env=env, timeout=timeout, watch=watch)  # type: ignore[call-arg]
    return runner.run(argv, cwd=cwd, env=env, timeout=timeout)


class SubprocessRunner:
    """Default runner: one process group per child, torn down on every exit path.

    ``shell=False``, no inherited stdin, captured output, and
    ``start_new_session=True`` so the child leads its own process group. The
    group — not just the child — is what gets terminated, and :meth:`run` waits
    for it to be gone before returning.
    """

    # Callers may hand this runner a :class:`LaunchWatch`. Advertised as an
    # attribute so a caller can ask rather than guess, and so the test doubles
    # in this package keep working untouched.
    supports_watch = True

    def __init__(
        self,
        *,
        default_timeout: float | None = 1800.0,
        term_grace: float = TERM_GRACE_SECONDS,
        kill_grace: float = KILL_GRACE_SECONDS,
    ) -> None:
        self.default_timeout = default_timeout
        self.term_grace = term_grace
        self.kill_grace = kill_grace

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        watch: LaunchWatch | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        effective_timeout = self.default_timeout if timeout is None else timeout
        if watch is not None and watch.cancelled:
            raise CommandContractError(
                "refusing to launch a child for an owner that has already been cancelled",
                evidence={"argv": list(checked)},
            )
        try:
            process = subprocess.Popen(  # noqa: S603 - argv array, shell=False
                list(checked),
                cwd=str(cwd) if cwd is not None else None,
                env=dict(env) if env is not None else None,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                start_new_session=True,
            )
        except OSError as exc:
            raise CommandContractError(
                f"could not launch {checked[0]}: {exc}",
                evidence={"argv": list(checked)},
            ) from exc

        group = _group_of(process)
        if watch is not None and not watch.opened(group, process):
            # The owner cancelled between the Popen and the registration. The
            # group has already been torn down by the watch; report it as a
            # cancelled child rather than waiting on something that is gone.
            for handle in (process.stdout, process.stderr):
                if handle is not None:
                    handle.close()
            return CommandResult(
                argv=checked, returncode=125, stdout="", stderr="cancelled before start\n"
            )
        # Drain both pipes in threads and wait on the *process*, not on end of
        # output. A backgrounded descendant inherits the lane's stdout, so
        # waiting for EOF would block until that descendant exited — which is
        # exactly the process this method exists to stop.
        streams = {"stdout": [], "stderr": []}  # type: dict[str, list[str]]
        readers = [
            threading.Thread(target=_drain, args=(handle, streams[name]), daemon=True)
            for name, handle in (("stdout", process.stdout), ("stderr", process.stderr))
            if handle is not None
        ]
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            try:
                process.wait(timeout=effective_timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            # Every exit path: normal completion, timeout, cancellation, and any
            # unexpected exception. A lane that returned cleanly can still have
            # left a descendant holding its worktree and capability channel.
            terminate_group(group, process, term_grace=self.term_grace, kill_grace=self.kill_grace)
            if watch is not None:
                watch.closed(group)
            for reader in readers:
                reader.join(timeout=self.term_grace + self.kill_grace + 5.0)
            for handle in (process.stdout, process.stderr):
                if handle is not None:
                    handle.close()

        return CommandResult(
            argv=checked,
            returncode=124 if timed_out else (process.returncode or 0),
            stdout="".join(streams["stdout"]),
            stderr="".join(streams["stderr"]),
            timed_out=timed_out,
        )


def _drain(handle: object, into: list[str]) -> None:
    """Read one pipe to EOF. Never raises: a closed pipe is just the end."""
    try:
        for line in handle:  # type: ignore[attr-defined]
            into.append(line)
    except (OSError, ValueError):  # pragma: no cover - the pipe was closed under us
        return


def _group_of(process: subprocess.Popen[str]) -> int | None:
    """The child's process-group id, when this platform has one."""
    getpgid = getattr(os, "getpgid", None)
    if getpgid is None:  # pragma: no cover - POSIX only in practice
        return None
    try:
        return getpgid(process.pid)
    except OSError:  # pragma: no cover - the child exited before we looked
        return None


def group_is_alive(group: int | None) -> bool:
    """True when any process in ``group`` still exists."""
    if group is None or not hasattr(os, "killpg"):  # pragma: no cover - POSIX only
        return False
    try:
        os.killpg(group, 0)
    except OSError as exc:
        return exc.errno == errno.EPERM
    return True


def terminate_group(
    group: int | None,
    process: subprocess.Popen[str] | None = None,
    *,
    term_grace: float = TERM_GRACE_SECONDS,
    kill_grace: float = KILL_GRACE_SECONDS,
) -> None:
    """Terminate a whole process group: SIGTERM, bounded wait, then SIGKILL.

    Returns once the group is gone or the kill grace is spent. Reaping the
    direct child is what keeps a zombie from holding the group id alive, so the
    process handle is waited on before the group is re-checked.
    """
    if group is None or not hasattr(os, "killpg"):  # pragma: no cover - POSIX only
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        return
    if group == os.getpgrp():  # pragma: no cover - start_new_session makes this impossible
        raise CommandContractError(
            "refusing to signal the launcher's own process group",
            evidence={"group": group},
        )
    for signal_number, grace in ((signal.SIGTERM, term_grace), (signal.SIGKILL, kill_grace)):
        if not group_is_alive(group):
            break
        try:
            os.killpg(group, signal_number)
        except OSError as exc:
            if exc.errno in (errno.ESRCH, errno.EPERM):
                break
            raise  # pragma: no cover - an unexpected signal failure must not be swallowed
        _reap(process)
        if _wait_for_group(group, grace):
            break
    _reap(process)


def _reap(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    try:
        process.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        pass


def _wait_for_group(group: int, grace: float) -> bool:
    """Poll until the group is gone or ``grace`` is spent. True when it is gone."""
    deadline = time.monotonic() + max(0.0, grace)
    while True:
        if not group_is_alive(group):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)
