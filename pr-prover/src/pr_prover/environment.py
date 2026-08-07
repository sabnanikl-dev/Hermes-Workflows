"""The one bounded artifact that can bind a gate's environment to this head.

A gate that sends HTTP requests to a named preview URL proves that something
answered at that URL. It does not prove that what answered was built from the
commit this run is bound to, and no amount of reading the gate's argv changes
that: ``{head}`` and a URL are strings the operator typed, not evidence about
what a deployment served.

So the elevation is earned, once, by a file:

.. code-block:: text

    operator declares gates[i].environment.binding_evidence
      ->  the gate is handed {environment_evidence_file}, outside its worktree
      ->  the gate observes the environment's own revision and writes it there
      ->  the gate exits and its worktree is proved clean and on the bound SHA
      ->  this module reads that file back and reconciles it with the run

Only that last step produces ``head-bound-environment``. Everything short of it
— no file, an unreadable one, one bound to another repository, PR, gate, or
environment, one whose externally observed revision is not this run's head — is
a stop, because a gate that was configured to prove revision binding and did not
is a misconfiguration this run must not report around.

The envelope is deliberately narrow. It answers one question — *which revision
did the environment this gate observed say it was serving, and when* — and it
is not a general diagnostic ingestion format: no findings, no severities, no
free-form records, no nested payloads. Every key is required, no key is
optional, and an unknown key means this is not the file this tool asked for.

Every scalar it carries is also held to the shape a *report* can state. A
timestamp is parsed as a real UTC instant rather than pattern-matched, and the
two free-text fields must be single-line printable text, because this envelope's
contents are rendered back to a human: a value that is not a moment, or one that
carries its own line breaks, is not bounded evidence that happens to look odd —
it is a claim the reader would have to reconstruct.

What this establishes is bounded in one further way, and the report says so
rather than leaving it implied: the revision is what an operator-owned gate
observed and wrote down. ``pr-prover`` reconciles that claim against the run's
own head; it does not attest the deployment, the provider, or the gate.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import EnvironmentEvidenceError
from .redaction import evidence as redact_evidence
from .reviewers import is_full_sha

ENVIRONMENT_SCHEMA_VERSION = 1

# One environment observation is a handful of short scalars. Sixteen kilobytes
# is far more than any of them and small enough that a runaway gate cannot fill
# the scratch directory or the report with what it wrote.
MAX_ENVIRONMENT_EVIDENCE_BYTES = 16_384

# Exactly the keys one envelope carries. Missing means the gate did not answer
# the question; extra means this is some other document that happened to land at
# the path, and neither is evidence this run may elevate on.
ENVIRONMENT_EVIDENCE_KEYS = (
    "schema_version",
    "repo",
    "pr",
    "gate",
    "environment",
    "url",
    "revision",
    "binding_source",
    "observed_at",
    "head",
)

# How long the two free-text fields may be. They are rendered into every report,
# so they are bounded here rather than clipped later into something that reads
# like a complete statement.
MAX_URL_CHARACTERS = 512
MAX_BINDING_SOURCE_CHARACTERS = 200

# The one timestamp grammar this tool reads and writes: second-resolution UTC,
# exactly as :func:`pr_prover.findings.utc_now` produces it. A gate that offers
# an offset, a fractional second, or a local time is offering a value two
# readers could disagree about, which is not what an observation time is for.
#
# The shape is only half of that. ``\d{2}`` is satisfied by a 99th month and a
# 61st second, so this pattern *alone* accepted ``9999-99-99T99:99:99Z`` and
# promoted it into a head-bound binding's observation time — a value that is not
# a moment, printed in the report as the instant an environment was observed.
# :func:`_observation_time` therefore parses the value as a real UTC instant and
# requires it to render back byte for byte, so shape, calendar, and canonical
# formatting all have to agree before anything is bound on it.
_OBSERVED_AT = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_OBSERVED_AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# What a gate wrote and this tool prints back has to be one printable line.
# Refused here, at the boundary, rather than escaped at the end of the pipeline:
# a URL or a binding source carrying its own line breaks is not a bounded scalar
# this envelope describes, and the renderer is not the right place to discover
# that. The report escapes what reaches it as well — this is the half that keeps
# such a value from being called validated evidence in the first place.
#
# Written as escapes rather than as the characters themselves: U+2028 and U+2029
# are line breaks a reader of this file cannot see, and a character class nobody
# can read is a character class nobody can review.
_UNPRINTABLE = re.compile("[\\x00-\\x1f\\x7f-\\x9f\\u2028\\u2029]")


@dataclass(frozen=True)
class EnvironmentBinding:
    """One validated observation of an external environment's own revision."""

    gate: str
    environment: str
    url: str
    revision: str
    binding_source: str
    observed_at: str


def environment_evidence_path(scratch: Path, *, gate: str, head: str) -> Path:
    """A fresh path for one gate's binding evidence at one head.

    Under the OS temp directory and never inside a repository, for the same
    reason a prepared artifact is: the file a gate writes is an output, and an
    output landing in the checkout it was judging is indistinguishable from the
    contamination the post-lane check exists to catch.

    Cleared first, because the failure this guards against is the loudest one
    available: a file an earlier cycle left at this path would let a gate that
    wrote nothing at all inherit a previous head's binding.
    """
    slug = "".join(character if character.isalnum() else "-" for character in gate)
    path = scratch / f"environment-{slug}-{head[:12]}.binding.json"
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise EnvironmentEvidenceError(
            f"could not clear the environment binding evidence path for gate {gate!r}: {exc}",
            evidence={"gate": gate, "environment_evidence_file": str(path)},
        ) from exc
    return path


def read_binding(
    path: Path, *, repo: str, pr: int, gate: str, environment: str, head: str
) -> EnvironmentBinding:
    """Read one gate's binding evidence back, or stop the run.

    Every check below is the difference between "a live endpoint answered" and
    "the environment this gate observed was serving the commit under review".
    The order is: the file exists and is a bounded, readable JSON object of
    exactly this tool's keys; the envelope names this repository, this pull
    request, this gate, and the environment the operator declared; and the
    revision it observed externally is the head this run is bound to.

    The last one is the whole point, and it is checked against ``head`` rather
    than against the envelope's own ``head`` field alone: a file that agrees
    with itself about the wrong commit is exactly the evidence this refuses.
    """
    context: dict[str, Any] = {
        "gate": gate,
        "environment": environment,
        "head": head,
        "environment_evidence_file": str(path),
    }
    payload = _payload(path, gate=gate, context=context)

    version = payload.get("schema_version")
    # ``type(...) is int`` rather than ``isinstance``: ``True == 1`` in Python,
    # so an ordinary comparison would read a JSON boolean as this schema.
    if type(version) is not int or version != ENVIRONMENT_SCHEMA_VERSION:
        raise EnvironmentEvidenceError(
            f"gate {gate!r} wrote environment binding evidence in a schema this tool "
            "does not read",
            evidence={
                **context,
                "expected_schema_version": ENVIRONMENT_SCHEMA_VERSION,
                "found": redact_evidence(str(version), limit=80),
            },
        )
    for key, expected in (("repo", repo), ("gate", gate), ("environment", environment)):
        found = payload.get(key)
        if not isinstance(found, str) or found != expected:
            raise EnvironmentEvidenceError(
                f"gate {gate!r}'s environment binding evidence was not produced for this "
                f"run's {key}",
                evidence={
                    **context,
                    "field": key,
                    "expected": expected,
                    "found": redact_evidence(str(found), limit=200),
                },
            )
    found_pr = payload.get("pr")
    if type(found_pr) is not int or found_pr != pr:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence was not produced for this "
            "run's pull request",
            evidence={
                **context,
                "field": "pr",
                "expected": pr,
                "found": redact_evidence(str(found_pr), limit=80),
            },
        )
    declared_head = payload.get("head")
    if not isinstance(declared_head, str) or declared_head != head:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence is bound to a different head "
            "than this run is proving",
            evidence={
                **context,
                "field": "head",
                "expected": head,
                "found": redact_evidence(str(declared_head), limit=80),
            },
        )
    revision = payload.get("revision")
    if not isinstance(revision, str) or not is_full_sha(revision):
        raise EnvironmentEvidenceError(
            f"gate {gate!r} recorded no full 40-hex lowercase revision for the "
            "environment it observed",
            evidence={**context, "revision": redact_evidence(str(revision), limit=80)},
        )
    if revision != head:
        # The one failure this whole file exists to catch: the endpoint answered,
        # and it was serving something else.
        raise EnvironmentEvidenceError(
            f"the revision gate {gate!r} observed in its environment is not the head "
            "this run is bound to, so the endpoint it checked was not serving this "
            "pull request's head",
            evidence={
                **context,
                "observed_revision": revision,
                "expected_revision": head,
                "resolution": (
                    "wait for the environment to serve this exact head and re-run, or "
                    "stop declaring binding_evidence for a gate that cannot observe one"
                ),
            },
        )
    url = _bounded_text(
        payload.get("url"),
        field="url",
        limit=MAX_URL_CHARACTERS,
        gate=gate,
        what="the URL or environment endpoint it observed",
        context=context,
    )
    binding_source = _bounded_text(
        payload.get("binding_source"),
        field="binding_source",
        limit=MAX_BINDING_SOURCE_CHARACTERS,
        gate=gate,
        what="how it read that revision out of the environment",
        context=context,
    )
    observed_at = _observation_time(
        payload.get("observed_at"), gate=gate, context=context
    )
    return EnvironmentBinding(
        gate=gate,
        environment=environment,
        url=url,
        revision=revision,
        binding_source=binding_source,
        observed_at=observed_at,
    )


def _payload(path: Path, *, gate: str, context: dict[str, Any]) -> dict[str, Any]:
    """The file as a JSON object of exactly this tool's keys, or a stop."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise EnvironmentEvidenceError(
            f"gate {gate!r} declares that it observes an external environment and binds "
            "it to this head, but it produced no binding evidence",
            evidence={
                **context,
                "resolution": (
                    "have the gate write its environment binding evidence to the path it "
                    "is handed as {environment_evidence_file}, or remove "
                    "environment.binding_evidence from its configuration and let the run "
                    "report the endpoint as unbound"
                ),
            },
        ) from exc
    except OSError as exc:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence could not be read: {exc}",
            evidence={**context, "error": type(exc).__name__},
        ) from exc
    if not raw.strip():
        raise EnvironmentEvidenceError(
            f"gate {gate!r} wrote empty environment binding evidence", evidence=context
        )
    if len(raw) > MAX_ENVIRONMENT_EVIDENCE_BYTES:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence is larger than this envelope "
            "can be",
            evidence={
                **context,
                "bytes": len(raw),
                "limit": MAX_ENVIRONMENT_EVIDENCE_BYTES,
            },
        )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence is not readable JSON: {exc}",
            evidence=context,
        ) from exc
    if not isinstance(payload, dict):
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence is not a JSON object",
            evidence=context,
        )
    expected = set(ENVIRONMENT_EVIDENCE_KEYS)
    missing = sorted(expected - set(payload))
    unknown = sorted(set(payload) - expected)
    if missing or unknown:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence is not this tool's envelope",
            evidence={
                **context,
                "missing_keys": missing,
                "unknown_keys": unknown,
                "required_keys": list(ENVIRONMENT_EVIDENCE_KEYS),
            },
        )
    return payload


def _bounded_text(
    value: Any, *, field: str, limit: int, gate: str, what: str, context: dict[str, Any]
) -> str:
    """One required, non-empty, bounded, single-line string field, or a stop."""
    if not isinstance(value, str) or not value.strip():
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence does not say {what}",
            evidence={**context, "field": field},
        )
    if len(value) > limit:
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence states {field} longer than "
            "this envelope allows",
            evidence={**context, "field": field, "characters": len(value), "limit": limit},
        )
    text = value.strip()
    if _UNPRINTABLE.search(text):
        # A line break here is not cosmetic. This value is printed back into the
        # report as one bullet's worth of evidence, and a field carrying its own
        # newlines is a field that can write bullets of its own.
        raise EnvironmentEvidenceError(
            f"gate {gate!r}'s environment binding evidence states {field} with line "
            "breaks or control characters; this envelope carries single-line printable "
            "text, because every field in it is rendered back into the run's report",
            evidence={**context, "field": field},
        )
    return text


def _observation_time(value: Any, *, gate: str, context: dict[str, Any]) -> str:
    """The one moment this envelope is allowed to be dated at, or a stop.

    Shape, calendar, and canonical formatting each have to agree. The shape
    regex is not enough on its own — it accepts a 99th month and a 61st second —
    and :func:`datetime.strptime` is not enough on its own either, because it
    reads an unpadded ``2026-8-3T...`` that this tool never writes. Parsing the
    value and requiring it to render back byte for byte is both checks at once,
    so nothing is bound on a timestamp that is not a real UTC instant.
    """
    if not isinstance(value, str) or not _OBSERVED_AT.match(value):
        raise EnvironmentEvidenceError(
            f"gate {gate!r} recorded no usable UTC observation time for the environment "
            "it observed; the required form is YYYY-MM-DDTHH:MM:SSZ",
            evidence={**context, "observed_at": redact_evidence(str(value), limit=80)},
        )
    try:
        moment = datetime.strptime(value, _OBSERVED_AT_FORMAT)
    except ValueError as exc:
        raise EnvironmentEvidenceError(
            f"gate {gate!r} recorded an observation time that is not a real UTC moment: "
            f"{exc}",
            evidence={**context, "observed_at": redact_evidence(value, limit=80)},
        ) from exc
    if moment.strftime(_OBSERVED_AT_FORMAT) != value:
        raise EnvironmentEvidenceError(
            f"gate {gate!r} recorded an observation time that is not in this tool's "
            "canonical UTC form; the required form is YYYY-MM-DDTHH:MM:SSZ",
            evidence={**context, "observed_at": redact_evidence(value, limit=80)},
        )
    return value


__all__ = [
    "ENVIRONMENT_EVIDENCE_KEYS",
    "ENVIRONMENT_SCHEMA_VERSION",
    "MAX_BINDING_SOURCE_CHARACTERS",
    "MAX_ENVIRONMENT_EVIDENCE_BYTES",
    "MAX_URL_CHARACTERS",
    "EnvironmentBinding",
    "environment_evidence_path",
    "read_binding",
]
