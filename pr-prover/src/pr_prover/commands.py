"""The single child-process boundary: argv arrays only, never a shell string.

Every child the loop launches — baseline gates, reviewer lanes, the builder
lane, ``git``, ``gh`` — is built here as a validated argv array. Templates
substitute only a closed set of ``{placeholder}`` tokens, so no configured or
reviewer-supplied value can ever be re-parsed as syntax.

:class:`CommandRunner` is the injection seam. :class:`SubprocessRunner` is the
one implementation the CLI uses, and it launches trusted agents the way they
actually behave:

* **The session is inherited, never rebuilt.** ``env=None`` means the child gets
  the operator's real environment, so the normal macOS Claude OAuth/keychain
  session keeps working. There is no ``env -i``, no synthetic ``HOME``, and no
  generated sandbox policy here; a lane that needs a variable added or removed
  says so as a small named overlay in its configuration.
* **Silence is not a hang.** A builder reading a PR, editing, and running
  verification can buffer its stdout for twenty minutes. Only the lane's own
  wall-clock budget ever ends a child. Quiet time is measured and reported so
  Hermes can see it, never acted on.
* **The budget that is reported is the budget that is enforced.** A caller that
  names ``timeout=None`` is saying "no deadline", and gets exactly that; the
  runner's ``default_timeout`` applies only to callers that name no budget at
  all — the short ``git``/``gh`` calls. There is no hidden cap underneath a lane
  the report describes as unbounded, which is the single-value half of the
  timeout invariant.
* **A lane is a process tree, not a process.** Each child starts in its own
  process group, so when a budget runs out the whole group is ended rather than
  just the one process the runner can see. A builder that spawned a test suite
  cannot keep mutating its worktree after the loop has reported it stopped.
  This is ordinary process hygiene for a trusted agent — the point is that the
  loop owns what it started, not that the child is contained.
* **The state stays observable.** While a child runs, ``progress`` reports
  elapsed time, bytes produced, and how long it has been quiet; when it ends,
  :class:`CommandResult` says whether it exited or timed out, and how long it
  took. That is what lets Hermes tell running, exited, and timed out apart.

Output goes to files rather than pipes, so a long lane can print megabytes
without the loop having to drain it, and the byte count can be watched while the
child is still alive.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Union

from .errors import CommandContractError

_PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")

EXITED = "exited"
TIMED_OUT = "timed-out"
# Signalling a whole process group is POSIX; on anything else the runner falls
# back to the single child it holds, which is still better than nothing.
_POSIX = os.name == "posix"


class _RunnerDefault:
    """The "no budget was named" sentinel.

    ``timeout=None`` has to mean one thing only — no deadline — or a lane the
    report calls unbounded can be killed by a default nobody asked for. So the
    runner's own default is reachable only by omitting the argument, which is
    what the short internal ``git``/``gh`` calls do.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<runner default>"


RUNNER_DEFAULT = _RunnerDefault()
Budget = Union[float, None, _RunnerDefault]


@dataclass(frozen=True)
class Progress:
    """One observation of a child that is still running."""

    argv: tuple[str, ...]
    elapsed: float
    output_bytes: int
    quiet_seconds: float


ProgressCallback = Callable[[Progress], None]


@dataclass(frozen=True)
class CommandResult:
    """The outcome of one child process, including how it got there."""

    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration: float = 0.0
    quiet_seconds: float = 0.0

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    @property
    def state(self) -> str:
        """``exited`` or ``timed-out`` — never inferred from how quiet it was."""
        return TIMED_OUT if self.timed_out else EXITED


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
    """Injection seam for launching children."""

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: Budget = RUNNER_DEFAULT,
        progress: ProgressCallback | None = None,
    ) -> CommandResult: ...


class SubprocessRunner:
    """Default runner: ``shell=False``, no inherited stdin, inherited session."""

    def __init__(
        self,
        *,
        default_timeout: float | None = 1800.0,
        poll_interval: float = 0.25,
        progress_interval: float = 30.0,
        kill_grace: float = 5.0,
    ) -> None:
        self.default_timeout = default_timeout
        self.poll_interval = poll_interval
        self.progress_interval = progress_interval
        self.kill_grace = kill_grace

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: Budget = RUNNER_DEFAULT,
        progress: ProgressCallback | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        # A named budget is honoured exactly, ``None`` included; the default is
        # for callers that named nothing at all.
        effective_timeout = (
            self.default_timeout if isinstance(timeout, _RunnerDefault) else timeout
        )
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="pr-prover-io-") as scratch:
            out_path = Path(scratch) / "stdout"
            err_path = Path(scratch) / "stderr"
            with out_path.open("wb") as out_file, err_path.open("wb") as err_file:
                try:
                    child = subprocess.Popen(  # noqa: S603 - argv array, shell=False
                        list(checked),
                        cwd=str(cwd) if cwd is not None else None,
                        # None means "inherit the real session", which is what
                        # the trusted Claude/Codex lanes need in order to reach
                        # their own OAuth/keychain credentials.
                        env=dict(env) if env is not None else None,
                        stdin=subprocess.DEVNULL,
                        stdout=out_file,
                        stderr=err_file,
                        shell=False,
                        # Its own process group, so everything this lane starts
                        # can be ended with it rather than outliving it.
                        start_new_session=_POSIX,
                    )
                except OSError as exc:
                    raise CommandContractError(
                        f"could not launch {checked[0]}: {exc}",
                        evidence={"argv": list(checked)},
                    ) from exc
                try:
                    timed_out, quiet_seconds = self._supervise(
                        child,
                        argv=checked,
                        timeout=effective_timeout,
                        progress=progress,
                        outputs=(out_path, err_path),
                    )
                except BaseException:
                    # An interrupt, or a progress callback that raised, still
                    # leaves this run owning the tree it started.
                    self._stop(child)
                    raise
            stdout = _read_text(out_path)
            stderr = _read_text(err_path)
        return CommandResult(
            argv=checked,
            returncode=124 if timed_out else child.returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            duration=time.monotonic() - started,
            quiet_seconds=quiet_seconds,
        )

    def _supervise(
        self,
        child: subprocess.Popen,
        *,
        argv: tuple[str, ...],
        timeout: float | None,
        progress: ProgressCallback | None,
        outputs: tuple[Path, Path],
    ) -> tuple[bool, float]:
        """Wait for the child, reporting progress. Only the budget can end it.

        The wait is what blocks, so a short child — ``git``, ``gh`` — returns as
        soon as it exits, and a long one wakes this loop often enough to keep
        the progress reports honest. A stretch of silence is measured and handed
        to the callback; it is never a reason to stop anything.
        """
        started = time.monotonic()
        last_bytes = 0
        last_output = started
        last_report = started
        while True:
            try:
                child.wait(timeout=self.poll_interval)
                break
            except subprocess.TimeoutExpired:
                pass
            now = time.monotonic()
            written = sum(_size(path) for path in outputs)
            if written != last_bytes:
                last_bytes = written
                last_output = now
            if timeout is not None and now - started >= timeout:
                self._stop(child)
                return True, now - last_output
            if progress is not None and now - last_report >= self.progress_interval:
                last_report = now
                progress(
                    Progress(
                        argv=argv,
                        elapsed=now - started,
                        output_bytes=written,
                        quiet_seconds=now - last_output,
                    )
                )
        now = time.monotonic()
        if sum(_size(path) for path in outputs) != last_bytes:
            last_output = now
        return False, now - last_output

    def _stop(self, child: subprocess.Popen) -> None:
        """End a lane that ran out of budget: ask the tree first, then insist.

        The lane is its whole process group. A builder that started a test suite
        or an agent of its own can exit politely while what it started keeps
        running, so the group is always ended — not only when the direct child
        ignored the polite stop — before the runner reports the lane stopped.
        """
        group = self._group(child)
        self._signal(child, group, hard=False)
        try:
            child.wait(timeout=self.kill_grace)
        except subprocess.TimeoutExpired:
            pass
        self._signal(child, group, hard=True)
        try:
            child.wait(timeout=self.kill_grace)
        except subprocess.TimeoutExpired:  # pragma: no cover - SIGKILL is not refusable
            pass

    def _group(self, child: subprocess.Popen) -> int | None:
        """This lane's process group, or ``None`` when it cannot be one safely.

        A lane that somehow shares this process's own group is never signalled
        as a group: ending it that way would end the prover with it.
        """
        if not _POSIX:
            return None
        try:
            group = os.getpgid(child.pid)
        except OSError:  # already reaped, or no such process
            return None
        return None if group == os.getpgrp() else group

    def _signal(self, child: subprocess.Popen, group: int | None, *, hard: bool) -> None:
        """Signal the whole group, falling back to the one child it holds."""
        if group is not None:
            try:
                os.killpg(group, signal.SIGKILL if hard else signal.SIGTERM)
                return
            except ProcessLookupError:
                return
            except OSError:  # pragma: no cover - permission loss mid-run
                pass
        try:
            if hard:
                child.kill()
            else:
                child.terminate()
        except OSError:  # pragma: no cover - the child is already gone
            pass


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:  # pragma: no cover - the file is created before the child starts
        return 0


def _read_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8", "replace")
    except OSError:  # pragma: no cover - defensive
        return ""


__all__ = [
    "EXITED",
    "RUNNER_DEFAULT",
    "TIMED_OUT",
    "Budget",
    "CommandResult",
    "CommandRunner",
    "ConfigPlaceholderError",
    "Progress",
    "ProgressCallback",
    "SubprocessRunner",
    "render_argv",
    "validate_argv",
]
