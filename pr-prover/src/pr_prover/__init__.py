"""``pr-prover`` — the repository-owned executable PR prove loop.

Inspect the live PR, bind everything to the exact ``headRefOid``, run baseline
(and when required, browser/visual) gates, launch exact-head reviewer lanes,
classify what comes back, allow at most two isolated fix attempts, verify the
builder's push and comment through GitHub, and report merge-ready, blocked, or
needs-Karan against the final exact head.

Stdlib only. Every child is an argv array. Every ambiguity fails closed.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .config import RunConfig
from .errors import FailClosed, FailureRecord, PrProverError
from .findings import (
    Classification,
    ClassificationEvent,
    Finding,
    FindingLocation,
    FindingProvenance,
    classify,
)
from .loop import BLOCKED, MERGE_READY, NEEDS_KARAN, ProverLoop, RunResult
from .state import MAX_ATTEMPTS, RunLock, RunState

__all__ = [
    "BLOCKED",
    "MAX_ATTEMPTS",
    "MERGE_READY",
    "NEEDS_KARAN",
    "Classification",
    "ClassificationEvent",
    "FailClosed",
    "FailureRecord",
    "Finding",
    "FindingLocation",
    "FindingProvenance",
    "PrProverError",
    "ProverLoop",
    "RunConfig",
    "RunLock",
    "RunResult",
    "RunState",
    "__version__",
    "classify",
]
