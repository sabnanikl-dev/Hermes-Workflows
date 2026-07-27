"""Findings, the provenance they carry, and the four-way classification.

A reviewer lane or a baseline gate produces :class:`Finding` objects with a
claimed severity. Classification maps each one into exactly one of the four
categories the mission contract names:

``blocking`` / ``non-blocking`` / ``false-positive`` / ``needs-karan``

The default adjudicator is deterministic and conservative: it accepts the
claimed severity and never invents a false positive. :data:`Adjudicator` is the
seam where Hermes' judgment (or a Karan decision) can downgrade a finding to
``false-positive`` or escalate it to ``needs-karan``; an adjudicator that
returns anything outside the vocabulary fails the run closed.

Every finding also carries its :class:`FindingProvenance`, and it carries it
from the moment it is constructed. An escalation that cannot say *who* found
*what*, *where*, and *on which head* forces Karan to re-derive the reviewer's
reasoning from raw output, so provenance is a construction-time requirement
rather than something a later renderer reconstructs from display strings:

* ``agent_id`` and ``role`` — the exact lane and the mission role it ran as;
* ``head`` — the full 40-hex commit the finding was produced against;
* ``location`` — a typed artifact surface, never free text (see
  :data:`LOCATION_KINDS`);
* ``evidence_excerpt`` — the verbatim text the lane emitted.

A finding whose provenance is incomplete cannot be built at all: the
constructor raises :class:`~pr_prover.errors.StateError` naming the field that
is missing, so an incomplete finding fails the run closed instead of reaching
classification, the frozen blocker set, or a report as a plausible-looking blank.

:func:`classify` adds the other half of the same question. Each classification
decision appends a :class:`ClassificationEvent` — who decided, what they decided
it about, from which category to which, and when — so a finding that two lanes
raised at different severities, or that an adjudicator moved, records the
decision rather than only its result. The clock is injected so the lineage is
deterministic under test.

Deduplication chooses which claim *governs* a finding id; it does not decide
that the other lane's evidence stops existing. Every originating finding is kept
whole in :attr:`ClassifiedFinding.origins`, with its own location and excerpt,
and ``sources`` is read off that list rather than stored beside it — so a
``needs-Karan`` packet can still show where each lane looked and what each one
actually said. The record is held to its own identity in both directions: an
origin or a lineage event attributed to a different finding id, and a governing
finding that is not one of the origins it was chosen from, are refused rather
than believed.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .errors import StateError

SEVERITIES = ("blocking", "non-blocking", "needs-karan")
CATEGORIES = ("blocking", "non-blocking", "false-positive", "needs-karan")

# Who produced a finding. ``role`` is the mission role the lane ran as;
# ``agent_id`` is the configured identity of the exact lane inside that role.
ROLES = ("reviewer", "gate", "builder", "hermes")

# Where a finding actually lives. Every kind names a concrete artifact surface a
# reader can open. There is deliberately no free-text kind: a location that
# cannot be typed is one nobody can act on.
LOCATION_KINDS = (
    "file-line",
    "review",
    "thread",
    "comment",
    "gate-command",
    "lane-output",
)

# What one classification decision did. ``classified`` accepts the claim the
# lane made; ``reclassified`` records that the category moved away from it.
ACTIONS = ("classified", "reclassified")

# Highest precedence first: an escalation from either lane wins, and a blocking
# claim is never silently softened by another lane's milder claim.
_PRECEDENCE = {"needs-karan": 0, "blocking": 1, "non-blocking": 2, "false-positive": 3}

_LOCATION_KEYS = frozenset({"kind", "reference", "line"})
_PROVENANCE_KEYS = frozenset({"agent_id", "role", "head", "location", "evidence_excerpt"})
_EVENT_KEYS = frozenset(
    {"finding_id", "actor", "action", "from_category", "to_category", "at", "rationale"}
)
_FINDING_KEYS = frozenset({"id", "severity", "summary", "source", "head", "detail", "provenance"})
_CLASSIFIED_KEYS = _FINDING_KEYS | {"category", "sources", "origins", "lineage"}

Clock = Callable[[], str]


def utc_now() -> str:
    """One second-resolution UTC timestamp, injectable so lineage stays testable."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _incomplete(what: str, field: str, evidence: Mapping[str, Any] | None = None) -> StateError:
    """The one fail-closed shape for provenance that cannot be acted on."""
    return StateError(
        f"{what} is incomplete: {field} is missing or unusable",
        evidence={"what": what, "incomplete_field": field, **dict(evidence or {})},
    )


def _text(value: Any, *, what: str, field: str, evidence: Mapping[str, Any] | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _incomplete(what, field, evidence)
    return value


def _mapping(value: Any, *, what: str, field: str, allowed: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise _incomplete(what, field)
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise StateError(
            f"{what} carries unknown keys",
            evidence={"what": what, "unknown_keys": unknown},
        )
    return dict(value)


def _is_full_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class FindingLocation:
    """The concrete artifact surface a finding points at.

    ``reference`` is read in the light of ``kind``: a repository path for
    ``file-line``, GitHub's own id for ``review``/``thread``/``comment``, the
    rendered command for ``gate-command``, and the emitting lane for
    ``lane-output``. ``line`` is required for ``file-line`` — a file location
    with no line is not a location — and optional elsewhere.
    """

    kind: str
    reference: str
    line: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in LOCATION_KINDS:
            raise StateError(
                f"unknown finding location kind {self.kind!r}",
                evidence={"kind": str(self.kind), "known_kinds": list(LOCATION_KINDS)},
            )
        _text(self.reference, what="finding location", field="reference", evidence={"kind": self.kind})
        if self.line is not None and (
            not isinstance(self.line, int) or isinstance(self.line, bool) or self.line < 1
        ):
            raise _incomplete("finding location", "line", {"kind": self.kind, "line": self.line})
        if self.kind == "file-line" and self.line is None:
            raise _incomplete("finding location", "line", {"kind": self.kind})

    def describe(self) -> str:
        """One human-readable line naming exactly where to look."""
        if self.kind == "file-line":
            return f"{self.reference}:{self.line}"
        if self.line is not None:
            return f"{self.kind} {self.reference} line {self.line}"
        return f"{self.kind} {self.reference}"

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind, "reference": self.reference}
        if self.line is not None:
            payload["line"] = self.line
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> FindingLocation:
        raw = _mapping(payload, what="finding location", field="location", allowed=_LOCATION_KEYS)
        return cls(
            kind=raw.get("kind"),
            reference=raw.get("reference"),
            line=raw.get("line"),
        )


@dataclass(frozen=True)
class FindingProvenance:
    """Who produced a finding, against which head, where, and on what evidence."""

    agent_id: str
    role: str
    head: str
    location: FindingLocation
    evidence_excerpt: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise StateError(
                f"unknown finding provenance role {self.role!r}",
                evidence={"role": str(self.role), "known_roles": list(ROLES)},
            )
        _text(self.agent_id, what="finding provenance", field="agent_id", evidence={"role": self.role})
        if not _is_full_sha(self.head):
            raise _incomplete(
                "finding provenance",
                "head",
                {"role": self.role, "agent_id": str(self.agent_id), "head": str(self.head)},
            )
        if not isinstance(self.location, FindingLocation):
            raise _incomplete(
                "finding provenance",
                "location",
                {"role": self.role, "agent_id": str(self.agent_id)},
            )
        _text(
            self.evidence_excerpt,
            what="finding provenance",
            field="evidence_excerpt",
            evidence={"role": self.role, "agent_id": str(self.agent_id)},
        )

    @property
    def source_label(self) -> str:
        """``role:agent`` — the one spelling of a finding's origin."""
        return f"{self.role}:{self.agent_id}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "head": self.head,
            "location": self.location.as_dict(),
            "evidence_excerpt": self.evidence_excerpt,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> FindingProvenance:
        raw = _mapping(
            payload, what="finding provenance", field="provenance", allowed=_PROVENANCE_KEYS
        )
        return cls(
            agent_id=raw.get("agent_id"),
            role=raw.get("role"),
            head=raw.get("head"),
            location=FindingLocation.from_dict(raw.get("location")),
            evidence_excerpt=raw.get("evidence_excerpt"),
        )


@dataclass(frozen=True)
class ClassificationEvent:
    """One classification decision: who moved what, from where to where, when."""

    finding_id: str
    actor: str
    action: str
    from_category: str
    to_category: str
    at: str
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise StateError(
                f"unknown classification action {self.action!r}",
                evidence={"action": str(self.action), "known_actions": list(ACTIONS)},
            )
        for field, value in (
            ("finding_id", self.finding_id),
            ("actor", self.actor),
            ("at", self.at),
        ):
            _text(value, what="classification lineage", field=field, evidence={"action": self.action})
        for field, value in (("from_category", self.from_category), ("to_category", self.to_category)):
            if value not in CATEGORIES:
                raise StateError(
                    f"classification lineage {field} is not a known category",
                    evidence={"field": field, "value": str(value), "known": list(CATEGORIES)},
                )

    def describe(self) -> str:
        """One human-readable line of lineage."""
        detail = f" ({self.rationale})" if self.rationale else ""
        return (
            f"{self.at} — {self.actor} {self.action} "
            f"{self.from_category} → {self.to_category}{detail}"
        )

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "finding_id": self.finding_id,
            "actor": self.actor,
            "action": self.action,
            "from_category": self.from_category,
            "to_category": self.to_category,
            "at": self.at,
        }
        if self.rationale:
            payload["rationale"] = self.rationale
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> ClassificationEvent:
        raw = _mapping(
            payload, what="classification lineage", field="lineage", allowed=_EVENT_KEYS
        )
        return cls(
            finding_id=raw.get("finding_id"),
            actor=raw.get("actor"),
            action=raw.get("action"),
            from_category=raw.get("from_category"),
            to_category=raw.get("to_category"),
            at=raw.get("at"),
            rationale=raw.get("rationale") or "",
        )


@dataclass(frozen=True)
class Finding:
    """One reviewer or gate finding, carrying the provenance it was created with.

    ``head`` and ``source`` are read off the provenance rather than stored
    beside it: one origin, one spelling, and no way for a display string to
    disagree with the record it came from.
    """

    id: str
    severity: str
    summary: str
    provenance: FindingProvenance
    detail: str = ""

    def __post_init__(self) -> None:
        _text(self.id, what="finding", field="id")
        if self.severity not in SEVERITIES:
            raise StateError(
                f"unknown finding severity {self.severity!r}",
                evidence={"finding_id": self.id, "severity": str(self.severity)},
            )
        _text(self.summary, what="finding", field="summary", evidence={"finding_id": self.id})
        if not isinstance(self.provenance, FindingProvenance):
            raise _incomplete("finding", "provenance", {"finding_id": self.id})

    @property
    def head(self) -> str:
        """The exact head this finding was produced against."""
        return self.provenance.head

    @property
    def source(self) -> str:
        """``role:agent`` — the lane that raised it."""
        return self.provenance.source_label

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "severity": self.severity,
            "summary": self.summary,
            "source": self.source,
            "head": self.head,
            "provenance": self.provenance.as_dict(),
        }
        if self.detail:
            payload["detail"] = self.detail
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> Finding:
        raw = _mapping(payload, what="finding", field="finding", allowed=_FINDING_KEYS)
        finding = cls(
            id=raw.get("id"),
            severity=raw.get("severity"),
            summary=raw.get("summary"),
            provenance=FindingProvenance.from_dict(raw.get("provenance")),
            detail=raw.get("detail") or "",
        )
        # ``source`` and ``head`` are rendered for readers, never read back as
        # authority: a stored copy that disagrees with the provenance it was
        # rendered from means one of the two was edited, and neither can be
        # trusted to say which.
        for field, rendered in (("source", finding.source), ("head", finding.head)):
            stored = raw.get(field)
            if stored is not None and stored != rendered:
                raise StateError(
                    f"stored finding {field} disagrees with its provenance",
                    evidence={
                        "finding_id": finding.id,
                        "field": field,
                        "stored": str(stored),
                        "provenance": rendered,
                    },
                )
        return finding


@dataclass(frozen=True)
class ClassifiedFinding:
    """A finding, the category Hermes assigned it, every lane that raised it, and why.

    ``finding`` is the claim that governs the bucket. ``origins`` is every lane's
    claim about this id, each one whole: its own typed location and its own
    verbatim excerpt. Losing the runner-up would leave an escalation able to say
    that a second lane agreed and unable to say where it looked or what it saw,
    so the governing claim is a choice made *among* the origins rather than a
    replacement for them, and ``sources`` is read back off that list.
    """

    finding: Finding
    category: str
    origins: tuple[Finding, ...]
    lineage: tuple[ClassificationEvent, ...] = ()

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise StateError(
                f"unknown finding category {self.category!r}",
                evidence={"finding_id": self.finding.id, "category": str(self.category)},
            )
        if not self.origins:
            raise _incomplete("classified finding", "origins", {"finding_id": self.finding.id})
        seen_sources: list[str] = []
        for origin in self.origins:
            if not isinstance(origin, Finding):
                raise _incomplete("classified finding", "origins", {"finding_id": self.finding.id})
            if origin.id != self.finding.id:
                raise StateError(
                    "classified finding carries an origin for a different finding",
                    evidence={
                        "finding_id": self.finding.id,
                        "origin_finding_id": origin.id,
                        "origin_source": origin.source,
                    },
                )
            if origin.source in seen_sources:
                raise StateError(
                    "classified finding records the same origin lane twice",
                    evidence={"finding_id": self.finding.id, "source": origin.source},
                )
            seen_sources.append(origin.source)
        # The governing claim has to be one of the claims actually made. A
        # ``finding`` that is not among its own origins is a record whose
        # provenance describes lanes that never raised it.
        if not any(origin == self.finding for origin in self.origins):
            raise StateError(
                "the governing finding is not among the origins it was chosen from",
                evidence={
                    "finding_id": self.finding.id,
                    "governing_source": self.finding.source,
                    "sources": list(seen_sources),
                },
            )
        if not self.lineage:
            raise _incomplete("classified finding", "lineage", {"finding_id": self.finding.id})
        # Lineage is only decision history if it is *this* finding's decision
        # history. Without the identity check a journal can claim that one
        # finding's escalation was decided about another one, and the bucket
        # check below would still pass.
        for event in self.lineage:
            if event.finding_id != self.finding.id:
                raise StateError(
                    "classification lineage is attributed to a different finding",
                    evidence={
                        "finding_id": self.finding.id,
                        "lineage_finding_id": event.finding_id,
                        "actor": event.actor,
                        "at": event.at,
                    },
                )
        if self.lineage[-1].to_category != self.category:
            raise StateError(
                "classification lineage does not end at the assigned category",
                evidence={
                    "finding_id": self.finding.id,
                    "category": self.category,
                    "lineage_ends_at": self.lineage[-1].to_category,
                },
            )

    @property
    def sources(self) -> tuple[str, ...]:
        """``role:agent`` for every lane that raised this id, in first-seen order."""
        return tuple(origin.source for origin in self.origins)

    @property
    def heads(self) -> frozenset[str]:
        """Every exact head any origin of this finding was produced against."""
        return frozenset(origin.head for origin in self.origins)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = dict(self.finding.as_dict())
        payload["category"] = self.category
        payload["sources"] = list(self.sources)
        payload["origins"] = [origin.as_dict() for origin in self.origins]
        payload["lineage"] = [event.as_dict() for event in self.lineage]
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> ClassifiedFinding:
        raw = _mapping(
            payload, what="classified finding", field="classified finding", allowed=_CLASSIFIED_KEYS
        )
        sources = raw.get("sources")
        if not isinstance(sources, (list, tuple)) or not sources:
            raise _incomplete("classified finding", "sources")
        origins = raw.get("origins")
        if not isinstance(origins, (list, tuple)) or not origins:
            raise _incomplete("classified finding", "origins")
        lineage = raw.get("lineage")
        if not isinstance(lineage, (list, tuple)) or not lineage:
            raise _incomplete("classified finding", "lineage")
        finding = Finding.from_dict(
            {key: value for key, value in raw.items() if key in _FINDING_KEYS}
        )
        classified = cls(
            finding=finding,
            category=raw.get("category"),
            origins=tuple(Finding.from_dict(origin) for origin in origins),
            lineage=tuple(ClassificationEvent.from_dict(event) for event in lineage),
        )
        # ``sources`` is rendered for readers, exactly as a finding's ``source``
        # is: stored so a report can be read without reassembling it, and never
        # read back as authority over the origins it was rendered from.
        stored = [str(source) for source in sources]
        if stored != list(classified.sources):
            raise StateError(
                "stored classified finding sources disagree with its origins",
                evidence={
                    "finding_id": classified.finding.id,
                    "stored": stored,
                    "origins": list(classified.sources),
                },
            )
        return classified


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

    def all(self) -> tuple[ClassifiedFinding, ...]:
        """Every classified finding, in bucket order."""
        return self.blocking + self.non_blocking + self.false_positive + self.needs_karan

    def as_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "blocking": [item.as_dict() for item in self.blocking],
            "non-blocking": [item.as_dict() for item in self.non_blocking],
            "false-positive": [item.as_dict() for item in self.false_positive],
            "needs-karan": [item.as_dict() for item in self.needs_karan],
        }

    @classmethod
    def from_dict(cls, payload: Any) -> Classification:
        """Rebuild a classification, refusing anything a writer could not produce."""
        raw = _mapping(
            payload, what="classification", field="classification", allowed=frozenset(CATEGORIES)
        )
        missing = sorted(set(CATEGORIES) - set(raw))
        if missing:
            raise _incomplete("classification", ", ".join(missing))
        buckets: dict[str, tuple[ClassifiedFinding, ...]] = {}
        seen: set[str] = set()
        for name in CATEGORIES:
            items = raw[name]
            if not isinstance(items, list):
                raise StateError(
                    "classification bucket is not a list",
                    evidence={"bucket": name, "type": type(items).__name__},
                )
            parsed: list[ClassifiedFinding] = []
            for item in items:
                classified = ClassifiedFinding.from_dict(item)
                if classified.category != name:
                    raise StateError(
                        "classified finding sits in the wrong bucket",
                        evidence={
                            "finding_id": classified.finding.id,
                            "bucket": name,
                            "category": classified.category,
                        },
                    )
                if classified.finding.id in seen:
                    raise StateError(
                        "classification records the same finding id twice",
                        evidence={"finding_id": classified.finding.id},
                    )
                seen.add(classified.finding.id)
                parsed.append(classified)
            buckets[name] = tuple(parsed)
        return cls(
            blocking=buckets["blocking"],
            non_blocking=buckets["non-blocking"],
            false_positive=buckets["false-positive"],
            needs_karan=buckets["needs-karan"],
        )


Adjudicator = Callable[[Finding], str]


def default_adjudicator(finding: Finding) -> str:
    """Accept the claimed severity verbatim; never invent a false positive."""
    return finding.severity


def classify(
    findings: Iterable[Finding],
    *,
    adjudicator: Adjudicator = default_adjudicator,
    actor: str = "hermes",
    clock: Clock = utc_now,
) -> Classification:
    """Deduplicate findings by id, bucket them, and record how each was decided."""
    chosen: dict[str, ClassifiedFinding] = {}
    for finding in findings:
        if not isinstance(finding, Finding):
            raise _incomplete("classification input", "finding")
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
        decided = ClassificationEvent(
            finding_id=finding.id,
            actor=actor,
            action="classified" if category == finding.severity else "reclassified",
            from_category=finding.severity,
            to_category=category,
            at=clock(),
            rationale=f"{finding.source} claimed {finding.severity} on {finding.head}",
        )
        previous = chosen.get(finding.id)
        if previous is None:
            chosen[finding.id] = ClassifiedFinding(
                finding=finding, category=category, origins=(finding,), lineage=(decided,)
            )
            continue
        keep_previous = _PRECEDENCE[previous.category] <= _PRECEDENCE[category]
        winning_finding = previous.finding if keep_previous else finding
        winning_category = previous.category if keep_previous else category
        # Every lane keeps its own claim whole. A second lane appends its
        # finding — location, excerpt and all — and a lane restating an id it
        # already raised replaces its own earlier claim only when that later
        # claim is the one that governs, so ``origins`` stays one entry per lane
        # and still contains whatever ``winning_finding`` is.
        if finding.source not in previous.sources:
            origins = previous.origins + (finding,)
        elif keep_previous:
            origins = previous.origins
        else:
            origins = tuple(
                finding if origin.source == finding.source else origin
                for origin in previous.origins
            )
        lineage = previous.lineage + (decided,)
        # Two lanes disagreeing about one id is itself a decision, and it is
        # recorded as one rather than left to be inferred from the bucket that
        # survived. Either the merged category moved to the stronger claim, or
        # the milder second claim was not accepted — and the lineage says which.
        if winning_category != previous.category:
            lineage += (
                ClassificationEvent(
                    finding_id=finding.id,
                    actor=actor,
                    action="reclassified",
                    from_category=previous.category,
                    to_category=winning_category,
                    at=clock(),
                    rationale=(
                        f"{finding.source} outranked {previous.finding.source}; "
                        "the stronger claim governs"
                    ),
                ),
            )
        elif decided.to_category != winning_category:
            lineage += (
                ClassificationEvent(
                    finding_id=finding.id,
                    actor=actor,
                    action="reclassified",
                    from_category=decided.to_category,
                    to_category=winning_category,
                    at=clock(),
                    rationale=(
                        f"{previous.finding.source} already claimed {previous.category}; "
                        "the stronger claim governs"
                    ),
                ),
            )
        chosen[finding.id] = ClassifiedFinding(
            finding=winning_finding,
            category=winning_category,
            origins=origins,
            lineage=lineage,
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


def provenance_lines(payload: Mapping[str, Any], *, indent: str = "") -> list[str]:
    """Render one already-sanitized classified finding's provenance as Markdown bullets.

    The escalation report and any other reader share this one rendering, so a
    ``needs-Karan`` packet shows who found what, where, and on what evidence
    without anybody re-deriving it from the raw lane output. Every origin is
    rendered, not only the claim that governs the bucket: two lanes raising one
    id looked at two places and quoted two excerpts, and an escalation that
    printed one of them would be asking Karan to decide on half the evidence.
    """
    # Rendered from the sanitized payload rather than the live object, so the
    # renderer never re-validates — a redacted or elided value is displayed as
    # what it is instead of failing the report that carries it. A payload with
    # no ``origins`` (a bare finding rather than a classified one) is its own
    # single origin.
    origins: Sequence[Any] = payload.get("origins") or (payload,)
    lines: list[str] = []
    for origin in origins:
        if not isinstance(origin, Mapping):
            continue
        provenance = origin.get("provenance") or {}
        location = provenance.get("location") or {}
        kind = location.get("kind", "unknown")
        reference = location.get("reference", "unknown")
        line = location.get("line")
        if kind == "file-line":
            where = f"{reference}:{line}"
        elif line is not None:
            where = f"{kind} {reference} line {line}"
        else:
            where = f"{kind} {reference}"
        lines += [
            f"{indent}- found by `{provenance.get('agent_id', 'unknown')}` "
            f"(role `{provenance.get('role', 'unknown')}`) on head "
            f"`{provenance.get('head', 'unknown')}`",
            f"{indent}- location: {where}",
            f"{indent}- evidence: `{provenance.get('evidence_excerpt', '')}`",
        ]
    lineage: Sequence[Any] = payload.get("lineage") or ()
    for event in lineage:
        if not isinstance(event, Mapping):
            continue
        detail = f" ({event['rationale']})" if event.get("rationale") else ""
        lines.append(
            f"{indent}- lineage: {event.get('at', 'unknown')} — {event.get('actor', 'unknown')} "
            f"{event.get('action', 'classified')} {event.get('from_category', '?')} → "
            f"{event.get('to_category', '?')}{detail}"
        )
    return lines


__all__ = [
    "ACTIONS",
    "CATEGORIES",
    "LOCATION_KINDS",
    "ROLES",
    "SEVERITIES",
    "Adjudicator",
    "Classification",
    "ClassificationEvent",
    "ClassifiedFinding",
    "Clock",
    "Finding",
    "FindingLocation",
    "FindingProvenance",
    "classify",
    "default_adjudicator",
    "provenance_lines",
    "utc_now",
]
