"""The allowed-path contract a fix attempt is frozen against.

A builder is told to fix exactly the blockers in its frozen repair packet and
to widen nothing. Until now that was a sentence in a prompt: the loop checked
that the attempt worktree was clean and that the push resolved to one new head,
neither of which says anything about *which files* the new commit touched. A
builder that fixed its blocker and also committed an unrelated file left a clean
worktree, a valid marker, and a readable fix comment, and the run carried on.

So the packet carries a path contract, and the loop compares the committed
old-head-to-new-head path set against it before any of that new head's gates or
reviewers run.

The vocabulary is deliberately small, because a matcher with interesting
semantics is a matcher whose corner cases nobody has read:

``pr-prover/src/thing.py``
    exactly that path, and nothing else.

``pr-prover/``
    that directory and everything under it. The trailing slash is what makes it
    a directory rule, so a path entry can never accidentally match a sibling
    whose name merely starts the same way.

``**``
    the whole repository. Only meaningful on its own, and only when the packet
    actually says it: this is the explicit whole-repository allowance, and it
    has to be written down. Absence is not it, and neither is ambiguity — a
    contract that cannot be parsed is a contract that fails the attempt.

There is no other wildcard, no negation, no character class, and no regular
expression. Every entry is repo-relative, forward-slashed, and free of ``..``,
so no contract can name a path outside the repository or reach one by walking
out of it.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .errors import ConfigError

# The one entry that means "this attempt may commit anywhere in the repository".
WHOLE_REPOSITORY = "**"

_FORBIDDEN_FRAGMENTS = ("\\", "\x00", "//")


@dataclass(frozen=True)
class PathContract:
    """The set of repository paths one fix attempt is allowed to commit."""

    entries: tuple[str, ...]

    @property
    def whole_repository(self) -> bool:
        return self.entries == (WHOLE_REPOSITORY,)

    def allows(self, path: str) -> bool:
        """True when ``path`` — repo-relative, forward-slashed — is in contract."""
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            return False
        if self.whole_repository:
            return True
        for entry in self.entries:
            if entry.endswith("/"):
                if path.startswith(entry):
                    return True
            elif path == entry:
                return True
        return False

    def rejected(self, paths: Iterable[str]) -> tuple[str, ...]:
        """Every path this contract does not allow, in order, without duplicates."""
        seen: set[str] = set()
        outside: list[str] = []
        for path in paths:
            if path in seen or self.allows(path):
                continue
            seen.add(path)
            outside.append(path)
        return tuple(outside)

    def as_dict(self) -> dict[str, object]:
        """The contract as it appears in the frozen repair packet."""
        return {
            "allowed_paths": list(self.entries),
            "whole_repository": self.whole_repository,
        }

    @classmethod
    def parse(cls, raw: object, *, what: str) -> PathContract:
        """Read a contract, or refuse. There is no permissive default."""
        if raw is None:
            raise ConfigError(
                f"{what} declares no allowed_paths. A fix attempt is compared against "
                "the paths its frozen repair packet allows, so a packet that names none "
                "cannot be checked; write the paths this lane may commit, or the single "
                f"entry {WHOLE_REPOSITORY!r} to allow the whole repository explicitly",
                evidence={"what": what, "whole_repository_entry": WHOLE_REPOSITORY},
            )
        if not isinstance(raw, (list, tuple)) or not raw:
            raise ConfigError(
                f"{what}.allowed_paths must be a non-empty list of repository paths",
                evidence={"what": what, "allowed_paths": raw},
            )
        entries: list[str] = []
        for index, item in enumerate(raw):
            entries.append(_entry(item, what=what, index=index))
        if WHOLE_REPOSITORY in entries and len(entries) > 1:
            raise ConfigError(
                f"{what}.allowed_paths mixes the whole-repository entry with specific "
                "paths; the whole-repository allowance is explicit and stands alone",
                evidence={"what": what, "allowed_paths": entries},
            )
        deduplicated: list[str] = []
        for entry in entries:
            if entry not in deduplicated:
                deduplicated.append(entry)
        return cls(entries=tuple(deduplicated))


def _entry(item: object, *, what: str, index: int) -> str:
    if not isinstance(item, str) or not item or item.strip() != item:
        raise ConfigError(
            f"{what}.allowed_paths[{index}] must be a non-empty, unpadded path",
            evidence={"what": what, "entry": item if isinstance(item, str) else type(item).__name__},
        )
    if item == WHOLE_REPOSITORY:
        return item
    if any(fragment in item for fragment in _FORBIDDEN_FRAGMENTS):
        raise ConfigError(
            f"{what}.allowed_paths[{index}] is not a plain forward-slashed repository path",
            evidence={"what": what, "entry": item},
        )
    if "*" in item or "?" in item or "[" in item:
        raise ConfigError(
            f"{what}.allowed_paths[{index}] uses a wildcard. The vocabulary is one exact "
            f"path, one 'directory/' prefix, or the single entry {WHOLE_REPOSITORY!r}",
            evidence={"what": what, "entry": item},
        )
    if item.startswith("/") or item.startswith("./") or item.startswith("~"):
        raise ConfigError(
            f"{what}.allowed_paths[{index}] must be relative to the repository root",
            evidence={"what": what, "entry": item},
        )
    if ".." in item.split("/"):
        raise ConfigError(
            f"{what}.allowed_paths[{index}] walks outside the repository",
            evidence={"what": what, "entry": item},
        )
    return item


def changed_paths(text: str) -> tuple[str, ...]:
    """Read ``git diff --name-only -z`` output into a path tuple."""
    return tuple(part for part in (text or "").split("\x00") if part)


def contract_from(entries: Sequence[str]) -> PathContract:
    """Build a contract from already-validated entries. For the packet reader."""
    return PathContract.parse(list(entries), what="frozen repair packet")


__all__ = ["WHOLE_REPOSITORY", "PathContract", "changed_paths", "contract_from"]
