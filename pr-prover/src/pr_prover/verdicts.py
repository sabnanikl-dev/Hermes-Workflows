"""Parse the machine-readable markers reviewer and builder lanes must emit.

Child output is untrusted. Anything that could be read two ways is rejected:

* exactly one ``DONE:`` marker may appear, and it must be the last non-empty
  line, so a finding body that quotes a marker cannot forge a verdict;
* a marker that nearly matches (wrong field order, short SHA, stray leading
  whitespace) is malformed, not "close enough";
* the head in the marker must equal the exact bound head, byte for byte;
* the declared ``BLOCKING`` count must reconcile with the parsed findings.

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

FULL_SHA = re.compile(r"\A[0-9a-f]{40}\Z")

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
_FINDING = re.compile(
    r"\AFINDING: SEVERITY=(?P<severity>blocking|non-blocking|needs-karan) "
    r"ID=(?P<id>[a-z0-9][a-z0-9._-]{0,63}) -- (?P<summary>\S.{0,300})\Z"
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

    lines = _lines(output)
    _reject_near_misses(lines, _FINDING_CANDIDATE, _FINDING, lane=lane, kind="FINDING")
    findings: list[Finding] = []
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
        findings.append(
            Finding(
                id=identifier,
                severity=found.group("severity"),
                summary=redact_evidence(found.group("summary").strip(), limit=300),
                # Provenance is taken here, at the only moment the surface is
                # still known: which lane printed it, on which head, on which
                # line of its output, and exactly what it said. Reconstructing
                # any of that later means reading it back out of a rendered
                # summary, which is the thing an escalation cannot rely on.
                provenance=FindingProvenance(
                    agent_id=reviewer,
                    role="reviewer",
                    head=head,
                    location=FindingLocation(
                        kind="lane-output",
                        reference=f"reviewer:{reviewer}",
                        line=number,
                    ),
                    evidence_excerpt=redact_evidence(line.strip(), limit=400),
                ),
            )
        )

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
    "SEVERITIES",
    "BuilderReport",
    "ReviewerVerdict",
    "parse_builder_report",
    "parse_reviewer_verdict",
]
