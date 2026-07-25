"""``pr-prover`` — the repository-owned executable PR prove loop.

Inspect the live PR, bind everything to the exact ``headRefOid``, run baseline
(and when required, browser/visual) gates, launch exact-head reviewer lanes,
classify what comes back, allow at most two isolated fix attempts, verify the
builder's push and comment through GitHub, and report merge-ready, blocked, or
needs-Karan against the final exact head.

Every child is launched by one broker that builds its environment from nothing
and hands it at most one scoped identity: push to the bound branch and comment
for the builder, comment and review for the reviewers, nothing at all for a
gate. No child gets merge, approval, deploy, or live-system authority.

Stdlib only. Every child is an argv array. Every ambiguity fails closed.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .childenv import EnvironmentPolicy
from .config import RunConfig
from .errors import FailClosed, PrProverError
from .findings import Classification, Finding, classify
from .identities import IdentitySpec
from .launchers import BoundContext, LaunchBroker
from .loop import BLOCKED, MERGE_READY, NEEDS_KARAN, ProverLoop, RunResult
from .state import MAX_ATTEMPTS, RunLock, RunState

__all__ = [
    "BLOCKED",
    "MAX_ATTEMPTS",
    "MERGE_READY",
    "NEEDS_KARAN",
    "BoundContext",
    "Classification",
    "EnvironmentPolicy",
    "FailClosed",
    "Finding",
    "IdentitySpec",
    "LaunchBroker",
    "PrProverError",
    "ProverLoop",
    "RunConfig",
    "RunLock",
    "RunResult",
    "RunState",
    "__version__",
    "classify",
]
