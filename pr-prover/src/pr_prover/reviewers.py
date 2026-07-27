"""The reviewer artifact lifecycle: prepare, validate, relay, read back.

A trusted reviewer lane is trusted to *judge* one exact head. It is not given a
GitHub credential to publish with, because the identity a reviewer publishes
under is not the identity its lane happens to run as. So the artifact takes one
explicit route::

    credential-free audit  ->  prepared artifact under the OS temp directory
      ->  trusted relay command publishing under the reviewer identity
      ->  GitHub readback of what actually landed

Each step is separately checkable, and this module holds the checks:

* :func:`credential_free` is what a relayed lane's environment is put through —
  the named GitHub credential variables are removed, and nothing else about the
  inherited session is touched, because the trusted lanes authenticate through
  the operator's own logged-in session;
* :func:`parse_artifact` is the one canonical parser for the declaration block
  every artifact must carry, so the file a lane wrote and the post that reached
  GitHub are read by exactly the same code;
* :func:`read_prepared` holds the prepared file to the predicates readback will
  later apply, minus the two only GitHub can answer (who posted it, and whether
  the id is new). A lane that fell over silently therefore stops the run instead
  of putting something unusable on the PR under the reviewer's name;
* :func:`artifact_matches` is the published-artifact predicate itself.

Nothing here brokers, mints, or forwards a credential. The relay is an ordinary
configured argv array that runs under whatever GitHub session it already has.

The declaration block
---------------------

An artifact must carry, each on a line of its own::

    ROLE=<the lane's configured role>
    RUNTIME=<the model or runtime the lane actually ran as>
    HEAD=<the full 40-hex lowercase commit reviewed>
    STATUS=pass|fail
    BLOCKING=<number of blocking findings>
    KILL-SWITCH: <what the reviewer tried in order to kill the fix, and what it found>

plus the reviewer's configured signature somewhere in the body.

Every one of those is matched as a whole line, and ``HEAD``/``ROLE``/``RUNTIME``/
``STATUS``/``BLOCKING`` must each appear exactly once. Prose never counts:
scope paragraphs, command transcripts, and quoted history all legitimately
mention a SHA or a role name, so an artifact could satisfy a substring test
while stating on its own line that it reviewed something else entirely. A
missing, malformed, duplicated, or conflicting declaration is rejected before
anything is published.

``STATUS`` and ``BLOCKING`` are declared as well as parsed from the lane's
stdout marker, and the two must agree. The marker is what the loop classifies
from; the artifact is what Karan and the next reviewer read. An artifact that
says ``pass`` over a lane that reported blockers is not a formatting slip, it is
two different stories about one head.

``KILL-SWITCH:`` is the adversarial mandate made checkable. A reviewer's job on
a fix cycle is to try to *kill* the builder's fix — to hunt for a bad-faith
pass, a weakened or deleted test, a gamed metric, a shrunken scope, stale
evidence — rather than to confirm that it looks right. What is enforced here is
deliberately structural, not semantic: at least one line saying what was
attempted. This module does not read English, and an artifact that lists no
attempted kill-switch has not done the job the prompt asked for.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

# The declaration keys, and the line shape each one is matched as.
ROLE_PREFIX = "ROLE="
RUNTIME_PREFIX = "RUNTIME="
HEAD_PREFIX = "HEAD="
STATUS_PREFIX = "STATUS="
BLOCKING_PREFIX = "BLOCKING="
KILL_SWITCH_PREFIX = "KILL-SWITCH:"

DECLARATION_PREFIXES = (
    ROLE_PREFIX,
    RUNTIME_PREFIX,
    HEAD_PREFIX,
    STATUS_PREFIX,
    BLOCKING_PREFIX,
)

_STATUSES = ("pass", "fail")
_BLOCKING = re.compile(r"\A\d{1,4}\Z")


def is_full_sha(value: str) -> bool:
    """Is this exactly a full 40-character lowercase hex SHA?"""
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True)
class ArtifactClaim:
    """What one artifact declares about the review it reports."""

    role: str
    runtime: str
    head: str
    status: str
    blocking: int
    kill_switches: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactReading:
    """The result of parsing one artifact body: a claim, or why there is none."""

    claim: ArtifactClaim | None = None
    problem: str = ""
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.claim is not None

    @property
    def note(self) -> str:
        """A short, body-free explanation fit for evidence."""
        if self.ok:
            return "the body declares one complete, well-formed artifact block"
        return self.detail or self.problem


def declarations(body: str, prefix: str) -> tuple[str, ...]:
    """Every standalone ``<prefix>`` declaration in ``body``, in order.

    Whole lines only. A key mentioned inside a sentence is prose, and prose is
    exactly what an artifact must not be able to bind itself with.
    """
    found: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            found.append(stripped[len(prefix) :].strip())
    return tuple(found)


def _sole(body: str, prefix: str) -> tuple[str | None, str]:
    """The single declaration for ``prefix``, or the reason there is not one."""
    found = declarations(body, prefix)
    if not found:
        return None, f"the body carries no standalone {prefix}<value> line"
    if len(found) > 1:
        return None, (
            f"the body carries {len(found)} standalone {prefix} lines; exactly one is required"
        )
    return found[0], ""


def parse_artifact(body: str) -> ArtifactReading:
    """Parse the canonical declaration block, or say precisely what is wrong.

    One parser for the prepared file and for the post that reached GitHub, so
    the two checks cannot drift apart: an artifact that would fail readback is
    the same artifact this refuses to let a relay publish.
    """
    values: dict[str, str] = {}
    for prefix in DECLARATION_PREFIXES:
        value, problem = _sole(body, prefix)
        if value is None:
            return ArtifactReading(problem="declaration", detail=problem)
        values[prefix] = value

    head = values[HEAD_PREFIX]
    if not is_full_sha(head):
        return ArtifactReading(
            problem="head",
            detail=f"the {HEAD_PREFIX} line is not a full 40-hex lowercase SHA",
        )
    role = values[ROLE_PREFIX]
    if not role:
        return ArtifactReading(problem="role", detail=f"the {ROLE_PREFIX} line names no role")
    runtime = values[RUNTIME_PREFIX]
    if not runtime:
        return ArtifactReading(
            problem="runtime",
            detail=(
                f"the {RUNTIME_PREFIX} line names no model or runtime, so the artifact "
                "does not say what actually reviewed this head"
            ),
        )
    status = values[STATUS_PREFIX]
    if status not in _STATUSES:
        return ArtifactReading(
            problem="status",
            detail=f"the {STATUS_PREFIX} line must be one of {list(_STATUSES)}",
        )
    blocking = values[BLOCKING_PREFIX]
    if not _BLOCKING.match(blocking):
        return ArtifactReading(
            problem="blocking",
            detail=f"the {BLOCKING_PREFIX} line is not a plain count",
        )
    count = int(blocking)
    if (status == "pass") != (count == 0):
        return ArtifactReading(
            problem="status-count",
            detail=(
                f"the artifact declares {STATUS_PREFIX}{status} alongside "
                f"{BLOCKING_PREFIX}{count}, which contradict each other"
            ),
        )
    kill_switches = tuple(
        entry for entry in declarations(body, KILL_SWITCH_PREFIX) if entry
    )
    if not kill_switches:
        return ArtifactReading(
            problem="kill-switch",
            detail=(
                f"the body carries no {KILL_SWITCH_PREFIX} line; an adversarial review "
                "has to state what it tried in order to kill the change, not only what "
                "it confirmed"
            ),
        )
    return ArtifactReading(
        claim=ArtifactClaim(
            role=role,
            runtime=runtime,
            head=head,
            status=status,
            blocking=count,
            kill_switches=kill_switches,
        )
    )


def artifact_disagreement(
    claim: ArtifactClaim, *, role: str, head: str, status: str, blocking: int
) -> str:
    """Why this claim is not the one the lane owed, or ``""`` when it is.

    Kept as one function because the prepared file and the published post are
    judged against exactly the same expectations; only the surfaces differ.
    """
    if claim.role != role:
        return f"the artifact declares {ROLE_PREFIX}{claim.role}, not {ROLE_PREFIX}{role}"
    if claim.head != head:
        return "the declared head is not the head this run is bound to"
    if claim.status != status:
        return (
            f"the artifact declares {STATUS_PREFIX}{claim.status} while the lane "
            f"reported {status}"
        )
    if claim.blocking != blocking:
        return (
            f"the artifact declares {BLOCKING_PREFIX}{claim.blocking} while the lane "
            f"reported {blocking} blocking finding(s)"
        )
    return ""


@dataclass(frozen=True)
class PreparedArtifact:
    """A reviewer's finished artifact, on disk and not yet published."""

    path: Path
    body: str
    claim: ArtifactClaim

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
    that must not have one. Nothing else is rebuilt: the session variables the
    trusted agents authenticate through are left exactly as they are.
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
    path: Path,
    *,
    reviewer: str,
    role: str,
    signature: str,
    head: str,
    status: str,
    blocking: int,
) -> PreparedArtifact:
    """Read and validate what the reviewer prepared, before anything publishes it.

    The predicates are the readback predicates minus the ones only GitHub can
    answer (who posted it, and whether the id is new). Checking them here means
    a relay never publishes an artifact readback would then reject, so a
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
            f"reviewer {reviewer} prepared no artifact to relay", evidence=evidence
        ) from exc
    except OSError as exc:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact could not be read: {exc}",
            evidence={**evidence, "error": type(exc).__name__},
        ) from exc
    if not raw.strip():
        raise ReviewerRelayError(
            f"reviewer {reviewer} prepared an empty artifact", evidence=evidence
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
            f"reviewer {reviewer}'s prepared artifact is not UTF-8 text", evidence=evidence
        ) from exc
    if signature not in body:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact does not carry its configured signature",
            evidence={**evidence, "expected_signature": signature},
        )
    reading = parse_artifact(body)
    if reading.claim is None:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact is not a well-formed review "
            f"artifact: {reading.note}",
            evidence={
                **evidence,
                "problem": reading.problem,
                "expected_block": expected_block(
                    role=role, head=head, status=status, blocking=blocking
                ),
            },
        )
    disagreement = artifact_disagreement(
        reading.claim, role=role, head=head, status=status, blocking=blocking
    )
    if disagreement:
        raise ReviewerRelayError(
            f"reviewer {reviewer}'s prepared artifact does not report the review this "
            f"lane just produced: {disagreement}",
            evidence={
                **evidence,
                "declared_role": reading.claim.role,
                "declared_head": reading.claim.head,
                "declared_status": reading.claim.status,
                "declared_blocking": reading.claim.blocking,
                "lane_status": status,
                "lane_blocking": blocking,
            },
        )
    return PreparedArtifact(path=path, body=body, claim=reading.claim)


def artifact_matches(
    artifact: Any, *, author: str, signature: str, role: str, head: str, status: str, blocking: int
) -> bool:
    """Is this published comment or review the artifact that lane owed?

    Author, signature, and the whole declaration block have to agree together.
    Where GitHub records a review's own ``commit_id`` it must agree too: that is
    the one head binding an author cannot retype, so it is checked *in addition
    to* the canonical body declaration rather than instead of it.
    """
    if artifact.author != author:
        return False
    if signature not in artifact.body:
        return False
    reading = parse_artifact(artifact.body)
    if reading.claim is None:
        return False
    if artifact_disagreement(
        reading.claim, role=role, head=head, status=status, blocking=blocking
    ):
        return False
    commit_id = getattr(artifact, "commit_id", "")
    return not commit_id or commit_id == head


def expected_block(*, role: str, head: str, status: str, blocking: int) -> list[str]:
    """The declaration block an artifact for this lane and head must carry."""
    return [
        f"{ROLE_PREFIX}{role}",
        f"{RUNTIME_PREFIX}<the model or runtime that reviewed this head>",
        f"{HEAD_PREFIX}{head}",
        f"{STATUS_PREFIX}{status}",
        f"{BLOCKING_PREFIX}{blocking}",
        f"{KILL_SWITCH_PREFIX} <what you tried in order to kill this change, and what it found>",
    ]


__all__ = [
    "BLOCKING_PREFIX",
    "CREDENTIAL_ENV",
    "DECLARATION_PREFIXES",
    "HEAD_PREFIX",
    "KILL_SWITCH_PREFIX",
    "MAX_PREPARED_BYTES",
    "ROLE_PREFIX",
    "RUNTIME_PREFIX",
    "STATUS_PREFIX",
    "ArtifactClaim",
    "ArtifactReading",
    "PreparedArtifact",
    "artifact_disagreement",
    "artifact_matches",
    "artifact_path",
    "credential_free",
    "declarations",
    "expected_block",
    "is_full_sha",
    "parse_artifact",
    "read_prepared",
]
