"""The single child-process boundary: argv arrays only, never a shell string.

Every child the loop launches — baseline gates, reviewer lanes, the builder
lane, ``git``, ``gh`` — is built here as a validated argv array. Templates
substitute only a closed set of ``{placeholder}`` tokens, so no configured or
reviewer-supplied value can ever be re-parsed as syntax.

:class:`CommandRunner` is the injection seam. PAPI-90 replaces
:class:`SubprocessRunner` with a credential-scoped launcher; PAPI-88 only
requires that the boundary exists and that argv discipline is enforced here.
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .errors import CommandContractError

_PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


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
    """Injection seam for launching children."""

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult: ...


class SubprocessRunner:
    """Default runner: ``subprocess.run`` with ``shell=False`` and no inherited stdin."""

    def __init__(self, *, default_timeout: float | None = 1800.0) -> None:
        self.default_timeout = default_timeout

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        effective_timeout = self.default_timeout if timeout is None else timeout
        try:
            completed = subprocess.run(
                list(checked),
                cwd=str(cwd) if cwd is not None else None,
                env=dict(env) if env is not None else None,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                shell=False,
                timeout=effective_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                argv=checked,
                returncode=124,
                stdout=_decode(exc.stdout),
                stderr=_decode(exc.stderr),
                timed_out=True,
            )
        except OSError as exc:
            raise CommandContractError(
                f"could not launch {checked[0]}: {exc}",
                evidence={"argv": list(checked)},
            ) from exc
        return CommandResult(
            argv=checked,
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )


def _decode(raw: object) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", "replace")
    return str(raw)
