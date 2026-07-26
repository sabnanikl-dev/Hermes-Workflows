"""The reviewer artifact lifecycle: audit, prepare, relay, read back.

A Codex reviewer is trusted to read one exact head and reach a verdict. It is
not given a GitHub credential to publish with, because the reviewer identity is
not the identity the lane runs as. So the artifact takes one explicit route::

    credential-free audit  ->  prepared artifact under the OS temp directory
      ->  trusted relay command publishing under the reviewer identity
      ->  GitHub readback of what actually landed

Each step is separately checkable, and this module holds the checks:

* :func:`credential_free` is what the reviewer lane's environment is put through
  — the named GitHub credential variables are removed, and nothing else about
  the inherited session is touched;
* :func:`read_prepared` holds the file the reviewer wrote to the same predicates
  readback will later apply to what is published, so a lane that produced
  nothing, produced something enormous, or produced an artifact about another
  head can never reach GitHub at all;
* :func:`artifact_matches` is that published-artifact predicate itself, shared
  by the relayed and the self-publishing lanes so both are read back the same
  way.

Only the relay command touches GitHub, and only after the prepared artifact has
passed. Nothing here brokers, mints, or forwards a credential: the relay is an
ordinary configured argv array that runs under the identity its own ``gh``
session already has.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from .errors import ReviewerRelayError

# The variable names that carry a GitHub credential. A reviewer lane in the
# relayed lifecycle never sees one; it writes a file and the relay publishes it.
CREDENTIAL_ENV = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
)

# A review artifact is prose. A quarter of a megabyte is far more than any real
# one and small enough that a runaway lane cannot fill the relay's argv or the
# report with it.
MAX_PREPARED_BYTES = 262_144


@dataclass(frozen=True)
class PreparedArtifact:
    """A reviewer's finished artifact, on disk and not yet published."""

    path: Path
    body: str

    @property
    def size(self) -> int:
        return len(self.body.encode("utf-8"))


def credential_free(
    env: Mapping[str, str] | None, *, base: Mapping[str, str]
) -> dict[str, str]:
    """The lane environment with every GitHub credential dropped by name.

    ``env`` is the lane's own overlay result, or ``None`` for "inherit
    untouched" — which still has to become a concrete mapping here, because
    inheriting untouched is exactly how the operator's token would reach a lane
    that must not have one.
    """
    resolved = dict(base if env is None else env)
    for name in CREDENTIAL_ENV:
        resolved.pop(name, None)
    return resolved


def artifact_path(scratch: Path, *, reviewer: str, head: str) -> Path:
    """A fresh path for one reviewer's prepared artifact at one head.

    Under the OS temp directory, never inside a repository, and cleared first:
    a file left by an earlier lane must never be mistaken for this one's work.
    """
    slug = "".join(character if character.isalnum() else "-" for character in reviewer)
    path = scratch / f"reviewer-{slug}-{head[:12]}.artifact.md"
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ReviewerRelayError(
            f"could not clear the prepared-artifact path for reviewer {reviewer}: {exc}",
            evidence={"reviewer": reviewer, "artifact_file": str(path)},
        ) from exc
    return path


def read_prepared(
    path: Path, *, reviewer: str, role: str, signature: str, head: str
) -> PreparedArtifact:
    """Read and validate what the reviewer prepared, before anything publishes it.

    The predicates are the readback predicates minus the ones only GitHub can
    answer (who posted it, and whether the id is new). Checking them here means
    a relay never publishes an artifact that readback would then reject, so a
    reviewer lane that fell over silently stops the run rather than putting
    something unusable on the PR under the reviewer's name.
    """
    evidence: dict[str, Any] = {
        "reviewer": reviewer,
        "role": role,
        "head": head,
        "artifact_file": str(path),
    }
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ReviewerRelayError(
            f"reviewer {reviewer} prepared no artifact to relay",
            evidence=evidence,
        ) from exc
    except OSError as exc:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact could not be read: {exc}",
            evidence={**evidence, "error": type(exc).__name__},
        ) from exc
    if not raw.strip():
        raise ReviewerRelayError(
            f"reviewer {reviewer} prepared an empty artifact",
            evidence=evidence,
        )
    if len(raw) > MAX_PREPARED_BYTES:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact is larger than an artifact can be",
            evidence={**evidence, "bytes": len(raw), "limit": MAX_PREPARED_BYTES},
        )
    try:
        body = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact is not UTF-8 text",
            evidence=evidence,
        ) from exc
    if signature not in body:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact does not carry its configured signature",
            evidence={**evidence, "expected_signature": signature},
        )
    if not _carries_role(body, role):
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact does not carry its role on its own line",
            evidence={**evidence, "expected_role_line": f"ROLE={role}"},
        )
    if head not in body:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact is not bound to this exact head",
            evidence=evidence,
        )
    return PreparedArtifact(path=path, body=body)


def artifact_matches(artifact: Any, *, author: str, signature: str, role: str, head: str) -> bool:
    """Is this published comment or review the artifact that lane owed?

    The role is matched as a whole line — read as a substring, ``ROLE=Auditor``
    would satisfy ``ROLE=A`` — and the head by the review's own ``commit_id``
    wherever GitHub records one, because that is the binding an author cannot
    retype.
    """
    if artifact.author != author:
        return False
    if signature not in artifact.body:
        return False
    if not _carries_role(artifact.body, role):
        return False
    if artifact.commit_id:
        return artifact.commit_id == head
    return head in artifact.body


def _carries_role(body: str, role: str) -> bool:
    line = f"ROLE={role}"
    return any(candidate.strip() == line for candidate in body.splitlines())


__all__ = [
    "CREDENTIAL_ENV",
    "MAX_PREPARED_BYTES",
    "PreparedArtifact",
    "artifact_matches",
    "artifact_path",
    "credential_free",
    "read_prepared",
]
