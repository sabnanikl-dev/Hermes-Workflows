"""Parse the machine-readable markers reviewer and builder lanes must emit.

Child output is untrusted. Anything that could be read two ways is rejected:

* exactly one ``DONE:`` marker may appear, and it must be the last non-empty
  line, so a finding body that quotes a marker cannot forge a verdict;
* a marker that nearly matches (wrong field order, short SHA, stray leading
  whitespace) is malformed, not "close enough";
* the head in the marker must equal the exact bound head, byte for byte;
* the declared ``BLOCKING`` count must reconcile with the parsed findings;
* a finding summary is 1 to :data:`MAX_SUMMARY` characters — exactly what the
  prompt and the README state — and what is accepted inside that bound is kept
  exactly as written, secret redaction aside. A parser that took one character
  more than it asked for would then have to shorten it to store it, and a
  record that is not the record cannot be reconciled with anything.

:func:`finding_records` is the single reader for the ``FINDING:`` grammar, and it
is deliberately not private: :mod:`pr_prover.reviewers` reads the artifact a lane
prepared with the same function that read that lane's final message, so the two
surfaces cannot be held to two grammars and one of them cannot quietly become
the looser one.

Reviewer contract::

    FINDING: SEVERITY=blocking|non-blocking|needs-karan ID=<slug> -- <summary>
    DONE: STATUS=pass|fail BLOCKING=<count> HEAD=<40-hex>

Builder contract::

    ADDRESSED: ID=<slug>
    DONE: PR=<number> BRANCH=<branch> STATUS=success|failure HEAD=<40-hex>
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import MalformedVerdict, ScopeContamination, StaleHead
from .findings import SEVERITIES, Finding, FindingLocation, FindingProvenance
from .redaction import evidence as redact_evidence
from .redaction import scrub

FULL_SHA = re.compile(r"\A[0-9a-f]{40}\Z")

# How long a finding summary may be, in total characters on its own line. The
# reviewer prompt and the README both state 1–300, so this is the number that
# has to be exact in all three places: a parser that accepts what the prompt
# forbids is a grammar the two surfaces do not share.
MAX_SUMMARY = 300

_DONE_CANDIDATE = re.compile(r"\ADONE\s*:", re.IGNORECASE)
_FINDING_CANDIDATE = re.compile(r"\AFINDING\s*:", re.IGNORECASE)
_ADDRESSED_CANDIDATE = re.compile(r"\AADDRESSED\s*:", re.IGNORECASE)

_REVIEWER_DONE = re.compile(
    r"\ADONE: STATUS=(?P<status>pass|fail) BLOCKING=(?P<blocking>\d{1,4}) HEAD=(?P<head>[0-9a-fA-F]{40})\Z"
)
_BUILDER_DONE = re.compile(
    r"\ADONE: PR=(?P<pr>\d{1,9}) BRANCH=(?P<branch>\S+) STATUS=(?P<status>success|failure) "
    r"HEAD=(?P<head>[0-9a-fA-F]{40})\Z"
)
# ``\S`` already spends the first of the permitted characters, so the tail is
# one shorter than the limit. Written as ``\S.{0,300}`` it accepts 301 — a
# record the prompt forbids, parsed anyway and then clipped into something that
# is no longer what the lane wrote.
_FINDING = re.compile(
    r"\AFINDING: SEVERITY=(?P<severity>blocking|non-blocking|needs-karan) "
    r"ID=(?P<id>[a-z0-9][a-z0-9._-]{0,63}) -- "
    rf"(?P<summary>\S.{{0,{MAX_SUMMARY - 1}}})\Z"
)
_ADDRESSED = re.compile(r"\AADDRESSED: ID=(?P<id>[a-z0-9][a-z0-9._-]{0,63})\Z")


@dataclass(frozen=True)
class ReviewerVerdict:
    """One reviewer lane's result, bound to one exact head."""

    reviewer: str
    status: str  # "pass" | "fail"
    head: str
    findings: tuple[Finding, ...]

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity == "blocking")


@dataclass(frozen=True)
class FindingRecord:
    """One ``FINDING:`` line, as the single accepted grammar reads it.

    A lane states its findings twice — once in the final message the loop
    classifies from, once in the artifact Karan and the next reviewer read —
    and the two have to be the same claim. That is only checkable if both are
    read by the same code, so this is what :func:`finding_records` returns and
    what :mod:`pr_prover.reviewers` reconciles an artifact against. ``line`` and
    ``excerpt`` are kept because provenance is taken at the only moment the
    surface is still known.
    """

    id: str
    severity: str
    summary: str
    line: int
    excerpt: str


@dataclass(frozen=True)
class BuilderReport:
    """One builder lane's result, naming the head it claims to have pushed."""

    status: str  # "success" | "failure"
    head: str
    pr: int
    branch: str
    addressed: frozenset[str]


def _lines(output: str) -> list[str]:
    return [line.rstrip("\r") for line in (output or "").splitlines()]


def _sole_marker(output: str, *, lane: str) -> str:
    """Return the single ``DONE:`` line, or fail closed.

    Detection is deliberately loose (case-insensitive, leading whitespace
    tolerated) so that a forged or duplicated near-marker is *seen* and
    rejected instead of being silently skipped in favour of the real one.
    """
    lines = _lines(output)
    candidates = [(index, line) for index, line in enumerate(lines) if _DONE_CANDIDATE.match(line.lstrip())]
    if not candidates:
        raise MalformedVerdict(
            f"{lane} emitted no DONE: marker",
            evidence={"lane": lane, "output": redact_evidence(output)},
        )
    if len(candidates) > 1:
        raise MalformedVerdict(
            f"{lane} emitted {len(candidates)} DONE: markers; exactly one is required",
            evidence={
                "lane": lane,
                "marker_count": len(candidates),
                "markers": [redact_evidence(line, limit=200) for _, line in candidates],
            },
        )
    index, line = candidates[0]
    if any(later.strip() for later in lines[index + 1 :]):
        raise MalformedVerdict(
            f"{lane} printed content after its DONE: marker",
            evidence={"lane": lane, "output": redact_evidence(output)},
        )
    return line


def _reject_near_misses(lines: list[str], candidate: re.Pattern[str], strict: re.Pattern[str], *, lane: str, kind: str) -> None:
    for line in lines:
        if candidate.match(line.lstrip()) and not strict.match(line):
            raise MalformedVerdict(
                f"{lane} emitted a malformed {kind} line",
                evidence={"lane": lane, "line": redact_evidence(line, limit=300)},
            )


def finding_records(text: str, *, lane: str) -> tuple[FindingRecord, ...]:
    """Every ``FINDING:`` line in ``text``, or fail closed.

    The one reader for the grammar the reviewer prompt states. A near-miss is
    rejected rather than skipped over in favour of the well-formed lines around
    it, and a repeated id is refused, because both are ways one surface can be
    read two ways — and the whole point of reading a lane's final message and
    its artifact with the same function is that neither can be held to a looser
    grammar than the other.
    """
    lines = _lines(text)
    _reject_near_misses(lines, _FINDING_CANDIDATE, _FINDING, lane=lane, kind="FINDING")
    records: list[FindingRecord] = []
    seen: set[str] = set()
    for number, line in enumerate(lines, start=1):
        found = _FINDING.match(line)
        if found is None:
            continue
        identifier = found.group("id")
        if identifier in seen:
            raise MalformedVerdict(
                f"{lane} repeated finding id {identifier!r}",
                evidence={"lane": lane, "finding_id": identifier},
            )
        seen.add(identifier)
        records.append(
            FindingRecord(
                id=identifier,
                severity=found.group("severity"),
                # Scrubbed, deliberately not clipped. The grammar above already
                # bounds this to MAX_SUMMARY characters, so there is no runaway
                # log to truncate — and truncating anyway is how the record
                # stops being the record. Two summaries that differ only inside
                # a clipped window collapse to one stored value, which makes the
                # artifact parity check below read two different claims as the
                # same one. A secret is the only thing that may change here.
                summary=scrub(found.group("summary")),
                line=number,
                excerpt=redact_evidence(line.strip(), limit=400),
            )
        )
    return tuple(records)


def parse_reviewer_verdict(reviewer: str, output: str, *, expected_head: str) -> ReviewerVerdict:
    """Parse one reviewer lane's output, bound to ``expected_head``."""
    lane = f"reviewer {reviewer}"
    if not FULL_SHA.match(expected_head):
        raise StaleHead(
            "expected head is not a full lowercase 40-hex SHA",
            evidence={"lane": lane, "expected_head": expected_head},
        )
    marker = _sole_marker(output, lane=lane)
    match = _REVIEWER_DONE.match(marker)
    if match is None:
        raise MalformedVerdict(
            f"{lane} DONE: marker does not match the reviewer contract",
            evidence={"lane": lane, "marker": redact_evidence(marker, limit=300)},
        )
    head = match.group("head").lower()
    if head != expected_head:
        raise StaleHead(
            f"{lane} reported a verdict for a different head",
            evidence={"lane": lane, "expected_head": expected_head, "reported_head": head},
        )

    findings = [
        Finding(
            id=record.id,
            severity=record.severity,
            summary=record.summary,
            # Provenance is taken here, at the only moment the surface is still
            # known: which lane printed it, on which head, on which line of its
            # output, and exactly what it said. Reconstructing any of that later
            # means reading it back out of a rendered summary, which is the
            # thing an escalation cannot rely on.
            provenance=FindingProvenance(
                agent_id=reviewer,
                role="reviewer",
                head=head,
                location=FindingLocation(
                    kind="lane-output",
                    reference=f"reviewer:{reviewer}",
                    line=record.line,
                ),
                evidence_excerpt=record.excerpt,
            ),
        )
        for record in finding_records(output, lane=lane)
    ]

    declared = int(match.group("blocking"))
    counted = sum(1 for item in findings if item.severity == "blocking")
    if declared != counted:
        raise MalformedVerdict(
            f"{lane} declared BLOCKING={declared} but emitted {counted} blocking findings",
            evidence={"lane": lane, "declared": declared, "counted": counted},
        )
    status = match.group("status")
    if (status == "pass") != (counted == 0):
        raise MalformedVerdict(
            f"{lane} STATUS={status} contradicts {counted} blocking findings",
            evidence={"lane": lane, "status": status, "blocking": counted},
        )
    return ReviewerVerdict(reviewer=reviewer, status=status, head=head, findings=tuple(findings))


def parse_builder_report(
    output: str,
    *,
    expected_pr: int,
    expected_branch: str,
    frozen_ids: frozenset[str],
) -> BuilderReport:
    """Parse the builder lane's output and bind it to the frozen blocker set."""
    lane = "builder"
    marker = _sole_marker(output, lane=lane)
    match = _BUILDER_DONE.match(marker)
    if match is None:
        raise MalformedVerdict(
            "builder DONE: marker does not match the builder contract",
            evidence={"lane": lane, "marker": redact_evidence(marker, limit=300)},
        )
    if int(match.group("pr")) != expected_pr:
        raise MalformedVerdict(
            "builder reported a different PR number",
            evidence={"expected_pr": expected_pr, "reported_pr": int(match.group("pr"))},
        )
    if match.group("branch") != expected_branch:
        raise MalformedVerdict(
            "builder reported a different branch",
            evidence={"expected_branch": expected_branch, "reported_branch": match.group("branch")},
        )
    head = match.group("head").lower()

    lines = _lines(output)
    _reject_near_misses(lines, _ADDRESSED_CANDIDATE, _ADDRESSED, lane=lane, kind="ADDRESSED")
    addressed: set[str] = set()
    for line in lines:
        found = _ADDRESSED.match(line)
        if found is None:
            continue
        identifier = found.group("id")
        if identifier in addressed:
            raise MalformedVerdict(
                f"builder repeated ADDRESSED id {identifier!r}",
                evidence={"finding_id": identifier},
            )
        addressed.add(identifier)
    unknown = sorted(addressed - frozen_ids)
    if unknown:
        raise ScopeContamination(
            "builder claimed work outside the frozen blocker set",
            evidence={"unknown_ids": unknown, "frozen_ids": sorted(frozen_ids)},
        )
    return BuilderReport(
        status=match.group("status"),
        head=head,
        pr=expected_pr,
        branch=expected_branch,
        addressed=frozenset(addressed),
    )


__all__ = [
    "FULL_SHA",
    "MAX_SUMMARY",
    "SEVERITIES",
    "BuilderReport",
    "FindingRecord",
    "ReviewerVerdict",
    "finding_records",
    "parse_builder_report",
    "parse_reviewer_verdict",
]
