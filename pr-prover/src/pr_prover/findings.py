"""Findings and the four-way classification Hermes acts on.

A reviewer lane or a baseline gate produces :class:`Finding` objects with a
claimed severity. Classification maps each one into exactly one of the four
categories the mission contract names:

``blocking`` / ``non-blocking`` / ``false-positive`` / ``needs-karan``

The default adjudicator is deterministic and conservative: it accepts the
claimed severity and never invents a false positive. :data:`Adjudicator` is the
seam where Hermes' judgment (or a Karan decision) can downgrade a finding to
``false-positive`` or escalate it to ``needs-karan``; an adjudicator that
returns anything outside the vocabulary fails the run closed.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .errors import StateError

SEVERITIES = ("blocking", "non-blocking", "needs-karan")
CATEGORIES = ("blocking", "non-blocking", "false-positive", "needs-karan")

# Highest precedence first: an escalation from either lane wins, and a blocking
# claim is never silently softened by another lane's milder claim.
_PRECEDENCE = {"needs-karan": 0, "blocking": 1, "non-blocking": 2, "false-positive": 3}


@dataclass(frozen=True)
class Finding:
    """One reviewer or gate finding, bound to the head it was produced against."""

    id: str
    severity: str
    summary: str
    source: str
    head: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise StateError(
                f"unknown finding severity {self.severity!r}",
                evidence={"finding_id": self.id, "severity": self.severity},
            )

    def as_dict(self) -> dict[str, str]:
        payload = {
            "id": self.id,
            "severity": self.severity,
            "summary": self.summary,
            "source": self.source,
            "head": self.head,
        }
        if self.detail:
            payload["detail"] = self.detail
        return payload


@dataclass(frozen=True)
class ClassifiedFinding:
    """A finding plus the category Hermes assigned it, and every lane that raised it."""

    finding: Finding
    category: str
    sources: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = dict(self.finding.as_dict())
        payload["category"] = self.category
        payload["sources"] = list(self.sources)
        return payload


@dataclass(frozen=True)
class Classification:
    """The four buckets, deduplicated by finding id."""

    blocking: tuple[ClassifiedFinding, ...] = ()
    non_blocking: tuple[ClassifiedFinding, ...] = ()
    false_positive: tuple[ClassifiedFinding, ...] = ()
    needs_karan: tuple[ClassifiedFinding, ...] = ()

    @property
    def blocking_ids(self) -> frozenset[str]:
        return frozenset(item.finding.id for item in self.blocking)

    def as_dict(self) -> dict[str, list[dict[str, object]]]:
        return {
            "blocking": [item.as_dict() for item in self.blocking],
            "non-blocking": [item.as_dict() for item in self.non_blocking],
            "false-positive": [item.as_dict() for item in self.false_positive],
            "needs-karan": [item.as_dict() for item in self.needs_karan],
        }


Adjudicator = Callable[[Finding], str]


def default_adjudicator(finding: Finding) -> str:
    """Accept the claimed severity verbatim; never invent a false positive."""
    return finding.severity


def classify(findings: Iterable[Finding], *, adjudicator: Adjudicator = default_adjudicator) -> Classification:
    """Deduplicate findings by id and bucket them into the four categories."""
    chosen: dict[str, ClassifiedFinding] = {}
    for finding in findings:
        try:
            category = adjudicator(finding)
        except StateError:
            raise
        except Exception as exc:  # an adjudicator must not decide by crashing
            raise StateError(
                f"adjudicator failed on finding {finding.id!r}: {exc}",
                evidence={"finding_id": finding.id, "source": finding.source},
            ) from exc
        if category not in CATEGORIES:
            raise StateError(
                f"adjudicator returned unknown category {category!r}",
                evidence={"finding_id": finding.id, "category": str(category)},
            )
        candidate = ClassifiedFinding(finding=finding, category=category, sources=(finding.source,))
        previous = chosen.get(finding.id)
        if previous is None:
            chosen[finding.id] = candidate
            continue
        sources = previous.sources + tuple(
            source for source in candidate.sources if source not in previous.sources
        )
        winner = previous if _PRECEDENCE[previous.category] <= _PRECEDENCE[category] else candidate
        chosen[finding.id] = ClassifiedFinding(
            finding=winner.finding, category=winner.category, sources=sources
        )

    buckets: dict[str, list[ClassifiedFinding]] = {name: [] for name in CATEGORIES}
    for identifier in sorted(chosen):
        item = chosen[identifier]
        buckets[item.category].append(item)
    return Classification(
        blocking=tuple(buckets["blocking"]),
        non_blocking=tuple(buckets["non-blocking"]),
        false_positive=tuple(buckets["false-positive"]),
        needs_karan=tuple(buckets["needs-karan"]),
    )


__all__ = [
    "CATEGORIES",
    "SEVERITIES",
    "Adjudicator",
    "Classification",
    "ClassifiedFinding",
    "Finding",
    "classify",
    "default_adjudicator",
]
