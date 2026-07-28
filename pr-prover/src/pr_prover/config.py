"""Strict run configuration.

One JSON file names the PR, the clone to borrow objects from, where the local
state/lock live, and the argv templates for baseline gates, the reviewer lanes,
and the builder lane. Unknown keys are rejected: a typo that silently disables a
gate is exactly the kind of quiet drift this loop must not have.

Placeholders available to every template::

    {repo} {owner} {name} {pr} {branch} {base} {head} {worktree}

Reviewer templates also get ``{reviewer}``, ``{role}``, and ``{artifact_file}``;
builder templates also get ``{attempt}``, ``{mode}`` (``initial`` or
``corrective``), and ``{blockers_file}``. Both file paths live under the OS temp
directory, never inside a repo.

``schema_version`` is ``2``. Version 1 described a genuinely different shape —
reviewers were a free list of lanes with no required role, artifact author, or
artifact signature — so the version was bumped rather than left describing two
incompatible files. A v1 config is refused with the ordered upgrade steps rather
than migrated: there are four of them, they are mechanical, and a migration
layer would be more machinery than the break is worth. The state journal's own
schema version is independent and unaffected.

The ``reviewers`` array is the acceptance lifecycle, not a free list of lanes:
it must be exactly ``reviewer-a``, ``reviewer-b``, and ``integration-auditor``,
in that order. The loop runs the lanes in the order given, and the auditor's job
is to reconcile the artifacts the other two publish, so a missing, duplicated,
or reordered required role is a configuration error rather than a run that
quietly proves less than it claims.

A reviewer may publish its own artifact, or — the shipped default — declare a
``relay``: the reviewer writes its finished artifact to ``{artifact_file}`` with
no GitHub credential in its environment, and the separately configured relay
argv publishes it under the reviewer identity. The relay is an ordinary command;
it is given no credential by this tool and uses whatever ``gh`` session it
already has. Its own ``{artifact_file}`` resolves to the *redacted* copy of what
the lane wrote — see :func:`pr_prover.reviewers.publication_copy` — because an
artifact is child output and the relay is what publishes it under a name that is
not the lane's.

A relayed lane's argv must also receive ``{evidence_packet}``. Having no GitHub
identity is not a detail it can work around — it cannot read the PR at all — so
a relayed lane with nowhere to read its evidence from is as misconfigured as one
with nowhere to write its artifact, and both are refused here rather than
discovered by a lane that quietly reviewed nothing.

``governing_issues`` is where the task contract comes from, and it is required.
The reviewers are handed those issue bodies in the same packet, because a lane
judging scope, acceptance criteria, or shrunken fixes needs the document those
are written in. It is configuration rather than something parsed out of the PR
for one reason: a PR body is untrusted prose that names whichever issue its
author typed, and "which contract am I held to" is not a question the thing
under review gets to answer.

The argv arrays are where the trusted agents are named. Hermes writes the exact
invocation of the installed Claude/Codex wrapper it wants — model, empty MCP
config, task-scoped tools, pointer-first prompt — and the loop runs it
unchanged. There is no role abstraction between the two.

Two identities are pinned rather than inferred:

* ``builder.comment_author`` — the login the fix comment must come from;
* each reviewer's ``artifact_author`` — the login its published review or
  comment must come from, alongside the ``ROLE=`` line and the exact head that
  artifact must carry.

Both are required. A signature and a head SHA are public the moment an artifact
is posted, so on their own they prove only that somebody read the PR; the login
is the part an arbitrary account cannot supply. There is no "any author will do"
configuration to fall into.

``operator_acknowledgements`` is the one optional, strict seam through which a
human operator can pin acknowledgement posts *before* a run starts. It is a list
of exact immutable GitHub artifact ids, each paired with a digest of the exact
body that id held when the operator read it — no logins, no patterns, no bearer
tokens, no third identity. Its only effect is on :mod:`pr_prover.feedback`: a
post whose author is one of this run's own publishing logins may spend
acknowledgement lines when, and only when, its own immutable id is listed here
*and* the post still says what the pinned digest was taken over. Absent or
empty, every publisher-authored post is refused acknowledgement authority
exactly as before.

It exists because the publishing logins and the human operator can be the same
GitHub accounts. When they are, the fail-closed rule that a lane may not clear
the feedback aimed at it leaves the operator with no identity that can
acknowledge anything, and a run that cannot be answered is not safer than one
that can — it is just stuck. Pinning is the operator saying "I read that exact
post, and I authorize what it says", which is a decision made on a post that
already exists rather than a login granted standing authority.

The id alone cannot carry that decision. A GitHub post keeps its id through
every later edit, so an authorization stored as an id is an authorization of
whatever the post is changed to say afterwards — and on the repository this seam
exists for, the account that can make that edit is the publishing login itself.
So each pin carries ``body_evidence``: the digest
:func:`pr_prover.feedback.publication_evidence` takes over the body, and the
review state, the operator authorized. The id stays the identity — it is still the only field nobody but
GitHub assigns, and matching is still exact — and the digest is what makes the
authorization about a body somebody read rather than about a post somebody owns.
A pinned post whose current evidence differs from the pinned evidence is refused
and stays unresolved feedback, which is the direction that stops the run.

Everything else about the acknowledgement contract is untouched: the exact line
grammar, immutable-id matching, chronology, the single unresolved-to-cleared
transition, residual prose, native review/thread resolution, and the refusal to
let this run's own verified artifacts acknowledge anything at all.

``env``/``env_unset`` are a small named overlay on the inherited environment,
not a replacement for it: the trusted lanes run as the operator's own user with
the normal Claude OAuth/keychain session, so the session variables cannot be
retargeted and credential values do not belong in this file.

``state_file`` and ``lock_file`` must live outside ``source_repo``. The loop
writes both of them while it is also asserting that the operational clone is
never modified and that an attempt worktree is clean, so a control file placed
inside that clone would have the run contaminating exactly the tree it is
judging. ``worktree_root`` is held to the same rule where the worktrees are
created.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .commands import validate_argv
from .errors import ConfigError
from .reviewers import CREDENTIAL_ENV

# Version 2 is the acceptance-lifecycle shape. Version 1 described a config
# whose reviewers were a free list of lanes; this one requires each lane to
# declare its ``role``, ``artifact_author``, and ``artifact_signature``, requires
# exactly the three ordered roles, and gives a relayed lane an artifact-file
# handoff. A v1 file is not a v1 file with a few fields missing — it denotes a
# different, incompatible shape — so the discriminator says so rather than
# leaving the old version number over new semantics.
SCHEMA_VERSION = 2
# What a v1 config has to gain to become a v2 one. Deterministic, ordered, and
# free of anything read out of the file, because this text is printed by the
# same structured failure path an operator sees for any other config stop.
_V1_UPGRADE_STEPS = (
    "give every reviewer lane a 'role' of exactly reviewer-a, reviewer-b, or "
    "integration-auditor, one each, listed in that order",
    "give every reviewer lane an 'artifact_author' login and an "
    "'artifact_signature' line its published artifact must carry",
    "point each relayed lane's argv at '{artifact_file}' and '{evidence_packet}', "
    "and give it a 'relay' command that publishes that file",
    "list the issue number(s) that govern this work in 'governing_issues'",
    "set 'schema_version' to 2",
)
# How many governing issues one run may name. A slice is measured against its
# own contract and the umbrella it refers to, not against a reading list: the
# bound exists so a misconfiguration cannot quietly turn every reviewer packet
# into a document dump.
MAX_GOVERNING_ISSUES = 8
# How many acknowledgement posts one operator may pin for one run. The seam is a
# preauthorization of specific posts somebody has read, so the bound is the size
# of a list a human can still check by eye; a config that needs more than this is
# describing a policy rather than a decision, and policy is not what this field
# is for.
MAX_OPERATOR_ACKNOWLEDGEMENTS = 16
# One immutable GitHub artifact id, as the surfaces this tool reads can produce
# it: a REST comment id (``5107483039``), a namespaced review id
# (``review:2938...``), or a GraphQL node id (``IC_kwDOM...==``). Matched
# exactly and bounded, because this value is compared against ids GitHub
# assigned and is never a pattern, a prefix, or a login.
_ARTIFACT_ID = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:=-]{0,199}\Z")
# The digest of the body the operator authorized: exactly what
# ``feedback.publication_evidence`` produces for that post, which is a SHA-256
# hex digest. Matched as strictly as the id is, and in one case only — lower
# case, sixty-four hex characters — because a near-miss digest is an operator
# who believes a post is pinned while nothing is.
_BODY_EVIDENCE = re.compile(r"\A[0-9a-f]{64}\Z")
# The two keys one pin carries, and no others. A typo here would silently pin a
# post to nothing, which is the shape of authorization this field exists to
# refuse.
_ACKNOWLEDGEMENT_KEYS = frozenset({"id", "body_evidence"})
GATE_KINDS = ("baseline", "visual")
# The acceptance lifecycle, as configuration rather than operator convention.
#
# The mission fixes one ordered review sequence for a merge-readiness run:
# Reviewer A, then Reviewer B, then the Integration Auditor — whose whole job is
# to reconcile the two artifacts that must already exist when it runs. The loop
# executes reviewer lanes in the order the config lists them, so "the auditor
# ran last" is only true if the schema says it must be; a config with two lanes,
# a duplicated role, or the auditor first would otherwise pass ``check-config``
# and produce a run that never integrated anything.
REQUIRED_REVIEWER_ROLES = ("reviewer-a", "reviewer-b", "integration-auditor")
# A trusted builder reads the live PR, edits, runs verification, commits,
# pushes, and comments. Twenty minutes is the floor of a realistic budget for
# that; anything shorter tends to be killed mid-verification and misread as a
# hang. Advisory, not enforced: a repo with a two-minute suite may know better.
REALISTIC_BUILDER_BUDGET = 1200.0
REALISTIC_REVIEWER_BUDGET = 900.0
_REPO = re.compile(r"\A[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\Z")
_NAME = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}\Z")
# A GitHub login: alphanumerics and single hyphens, 39 characters at most, with
# the "[bot]" suffix apps carry. Matched exactly, so no near-login gets through.
_LOGIN = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}(?:\[bot\])?\Z")

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "repo",
        "pr",
        "branch",
        "base",
        "source_repo",
        "worktree_root",
        "state_file",
        "lock_file",
        "visual_qa_required",
        "governing_issues",
        "operator_acknowledgements",
        "gates",
        "reviewers",
        "builder",
    }
)
_GATE_KEYS = frozenset({"name", "argv", "kind", "timeout", "env", "env_unset"})
_REVIEWER_KEYS = frozenset(
    {
        "name",
        "argv",
        "timeout",
        "role",
        "artifact_author",
        "artifact_signature",
        "relay",
        "env",
        "env_unset",
    }
)
_RELAY_KEYS = frozenset({"argv", "timeout", "env", "env_unset"})
# The token every relayed lane has to be handed, on both sides of the handoff:
# the reviewer needs somewhere to write, and the relay needs something to post.
_ARTIFACT_FILE = "{artifact_file}"
# The other half of what a relayed lane is handed. It runs with no GitHub
# credential and cannot inspect the PR for itself, so a lane whose argv never
# receives the frozen packet has been asked to judge a pull request it has no
# way to read.
_EVIDENCE_PACKET = "{evidence_packet}"
_BUILDER_KEYS = frozenset(
    {"argv", "signature", "comment_author", "timeout", "env", "env_unset"}
)
_ENV_NAME = re.compile(r"\A[A-Za-z_][A-Za-z0-9_]{0,63}\Z")
# The variables that carry the logged-in session the trusted agents
# authenticate through. Overriding or clearing any of them is how a lane ends up
# running against a synthetic home with no Claude OAuth/keychain session.
_SESSION_ENV = frozenset({"HOME", "USER", "LOGNAME", "SHELL"})
_CREDENTIAL_PREFIXES = ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_")


@dataclass(frozen=True)
class LaneEnv:
    """A named overlay on the environment a lane inherits.

    Empty by default, and empty means "inherit exactly what this process has".
    The overlay can add a variable a lane needs and remove one it must not see
    — ``GH_TOKEN``, so a trusted agent uses its own configured ``gh`` identity
    rather than the operator's — but it cannot touch the session variables and
    it may not carry a credential value: tokens belong in the keychain and in
    ``gh``'s own auth, not in a run config that ends up in evidence.
    """

    set: tuple[tuple[str, str], ...] = ()
    unset: tuple[str, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.set and not self.unset

    def apply(self, base: Mapping[str, str]) -> dict[str, str] | None:
        """The environment for one lane, or ``None`` to inherit untouched."""
        if self.empty:
            return None
        env = dict(base)
        for name in self.unset:
            env.pop(name, None)
        env.update(self.set)
        return env


@dataclass(frozen=True)
class OperatorAcknowledgement:
    """One acknowledgement post the operator authorized before launch.

    ``identifier`` is the exact immutable id GitHub assigned the post, and it is
    the identity: nothing here is a login, a pattern, or a prefix.

    ``body_evidence`` is what that authorization is *about* — the
    :func:`~pr_prover.feedback.publication_evidence` digest of the body, and the
    review state, the post held when the operator read it. The pair is needed
    because an id survives every edit: a post pinned by id alone is a post whose
    author, who on this repository is the publishing login itself, may rewrite
    into different acknowledgement lines after the authorization was given. Two
    fields make the authorization say what it means — *this post, saying this*.
    """

    identifier: str
    body_evidence: str


@dataclass(frozen=True)
class GateConfig:
    """One baseline gate, or one browser/visual QA gate."""

    name: str
    argv: tuple[str, ...]
    kind: str = "baseline"
    timeout: float | None = None
    env: LaneEnv = LaneEnv()


@dataclass(frozen=True)
class RelayConfig:
    """The trusted command that publishes one reviewer's prepared artifact.

    It runs after the reviewer lane has exited and its prepared artifact has
    validated, under whatever GitHub identity its own session already holds.
    This tool hands it a file path and nothing else.
    """

    argv: tuple[str, ...]
    timeout: float | None = None
    env: LaneEnv = LaneEnv()


@dataclass(frozen=True)
class ReviewerConfig:
    """One exact-head reviewer lane, and the artifact it must publish.

    ``role`` is what the lane is: Reviewer A, Reviewer B, Integration Auditor.
    It is substituted into the argv template and it must appear on its own line
    in the published artifact, so one reviewer's post can never be read back as
    another's.

    With a ``relay``, the lane itself is credential-free: it writes its artifact
    to ``{artifact_file}`` and the relay publishes the redacted copy of it.
    Without one, the lane publishes for itself, which is also supported.
    """

    name: str
    argv: tuple[str, ...]
    artifact_author: str
    artifact_signature: str
    role: str
    timeout: float | None = None
    env: LaneEnv = LaneEnv()
    relay: RelayConfig | None = None


@dataclass(frozen=True)
class BuilderConfig:
    """The fix lane, plus who its PR comment must come from and what it must say.

    ``comment_author`` is required, not optional. The signature and the head SHA
    are both public the moment the builder comments, so on their own they prove
    only that somebody read the PR. The expected login is the part an arbitrary
    commenter cannot supply.
    """

    argv: tuple[str, ...]
    signature: str
    comment_author: str
    timeout: float | None = None
    env: LaneEnv = LaneEnv()


@dataclass(frozen=True)
class RunConfig:
    """Everything one ``pr-prover run`` needs."""

    repo: str
    pr: int
    source_repo: Path
    worktree_root: Path
    state_file: Path
    lock_file: Path
    builder: BuilderConfig
    reviewers: tuple[ReviewerConfig, ...]
    governing_issues: tuple[int, ...]
    gates: tuple[GateConfig, ...] = ()
    branch: str | None = None
    base: str | None = None
    visual_qa_required: bool = False
    # Exact immutable acknowledgement post ids the operator authorized before
    # launch, each bound to the body they authorized. Empty is the default and
    # means what it always meant: no post written under a publishing login may
    # acknowledge anything.
    operator_acknowledgements: tuple[OperatorAcknowledgement, ...] = ()
    source: Path | None = field(default=None, compare=False)

    @property
    def owner(self) -> str:
        return self.repo.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.repo.split("/", 1)[1]

    @property
    def baseline_gates(self) -> tuple[GateConfig, ...]:
        return tuple(gate for gate in self.gates if gate.kind == "baseline")

    @property
    def visual_gates(self) -> tuple[GateConfig, ...]:
        return tuple(gate for gate in self.gates if gate.kind == "visual")

    @property
    def publisher_logins(self) -> tuple[str, ...]:
        """Every login this run's own lanes publish under, deduplicated in order."""
        seen: list[str] = []
        for login in (
            self.builder.comment_author,
            *(reviewer.artifact_author for reviewer in self.reviewers),
        ):
            if login not in seen:
                seen.append(login)
        return tuple(seen)

    def advisories(self) -> tuple[str, ...]:
        """Non-fatal notes ``check-config`` prints before a real run.

        The budgets are the ones that matter operationally: a trusted agent cut
        off mid-verification looks exactly like a hang, and that misreading is
        what the two-cycle loop pays for. An omitted budget is the other end of
        the same problem — nothing will ever end that lane — so it is said out
        loud here rather than quietly capped somewhere the report cannot see.

        A pinned acknowledgement is the other kind of note worth printing before
        a run rather than reading about afterwards. It is the one field that lets
        a post written under a publishing login clear human feedback, so
        ``check-config`` names every id it was handed: the seam is auditable
        exactly to the extent an operator can see, before launch, which posts
        they preauthorized. The bodies those ids were pinned to are not printed —
        a digest read back to the person who wrote it proves nothing, and the run
        itself compares them against what GitHub currently serves.
        """
        notes: list[str] = []
        if self.operator_acknowledgements:
            notes.append(
                f"{len(self.operator_acknowledgements)} operator-pinned acknowledgement "
                "post id(s) may acknowledge earlier feedback even though a configured "
                "publishing login wrote them: "
                + ", ".join(pin.identifier for pin in self.operator_acknowledgements)
                + "; pin only exact posts you have read on this pull request, since "
                "each one is an authorization rather than a login-wide exemption, and "
                "each is refused if the post no longer says what its pinned "
                "body_evidence was taken over"
            )
        for lane, timeout in self._budgets():
            if timeout is None:
                notes.append(
                    f"{lane} has no timeout, so nothing but the lane itself will ever end it; "
                    "the run log will report its budget as unbounded"
                )
        if self.builder.timeout is not None and self.builder.timeout < REALISTIC_BUILDER_BUDGET:
            notes.append(
                f"builder timeout is {self.builder.timeout:.0f}s; a trusted builder that reads "
                f"the PR, edits, verifies, pushes, and comments usually needs "
                f"{REALISTIC_BUILDER_BUDGET:.0f}s or more"
            )
        for reviewer in self.reviewers:
            if reviewer.timeout is not None and reviewer.timeout < REALISTIC_REVIEWER_BUDGET:
                notes.append(
                    f"reviewer {reviewer.name!r} timeout is {reviewer.timeout:.0f}s; "
                    f"exact-head review usually needs {REALISTIC_REVIEWER_BUDGET:.0f}s or more"
                )
        return tuple(notes)

    def _budgets(self) -> tuple[tuple[str, float | None], ...]:
        """Every lane that runs a child, and the budget it will actually get."""
        return (
            ("builder", self.builder.timeout),
            *((f"gate {gate.name!r}", gate.timeout) for gate in self.gates),
            *(
                (f"reviewer {reviewer.name!r}", reviewer.timeout)
                for reviewer in self.reviewers
            ),
            *(
                (f"reviewer {reviewer.name!r} relay", reviewer.relay.timeout)
                for reviewer in self.reviewers
                if reviewer.relay is not None
            ),
        )

    @classmethod
    def load(cls, path: Path) -> RunConfig:
        path = Path(path).expanduser().resolve()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ConfigError(f"config file is unreadable: {exc}", evidence={"config": str(path)}) from exc
        except json.JSONDecodeError as exc:
            raise ConfigError(f"config file is not valid JSON: {exc}", evidence={"config": str(path)}) from exc
        return cls.from_mapping(raw, base_dir=path.parent, source=path)

    @classmethod
    def from_mapping(
        cls, raw: object, *, base_dir: Path | None = None, source: Path | None = None
    ) -> RunConfig:
        if not isinstance(raw, Mapping):
            raise ConfigError("config must be a JSON object")
        unknown = sorted(set(raw) - _TOP_LEVEL_KEYS)
        if unknown:
            raise ConfigError("config has unknown keys", evidence={"unknown_keys": unknown})
        found = raw.get("schema_version")
        if found != SCHEMA_VERSION:
            # A v1 file is the one unsupported version this tool can name, so it
            # gets the upgrade rather than the generic refusal. Nothing from the
            # file is echoed: the version is a small integer the operator wrote,
            # and the steps are fixed text. ``True == 1`` in Python, so the type
            # is checked exactly — a boolean here is a malformed field, not a
            # previous release.
            if type(found) is int and found == 1:
                raise ConfigError(
                    "config schema_version 1 is no longer supported: version 2 requires "
                    "the ordered reviewer-a, reviewer-b, integration-auditor lifecycle "
                    "with a declared role, artifact author, and artifact signature per "
                    "lane. Upgrade this file: "
                    + "; ".join(f"({index}) {step}" for index, step in enumerate(_V1_UPGRADE_STEPS, 1)),
                    evidence={
                        "found": 1,
                        "expected": SCHEMA_VERSION,
                        "upgrade": list(_V1_UPGRADE_STEPS),
                    },
                )
            raise ConfigError(
                "config schema_version is not supported",
                evidence={"found": found, "expected": SCHEMA_VERSION},
            )

        repo = raw.get("repo")
        if not isinstance(repo, str) or not _REPO.match(repo):
            raise ConfigError("config repo must be 'owner/name'", evidence={"repo": repo})
        pr = raw.get("pr")
        if not isinstance(pr, int) or isinstance(pr, bool) or pr < 1:
            raise ConfigError("config pr must be a positive integer", evidence={"pr": pr})

        root = Path(base_dir).resolve() if base_dir is not None else Path.cwd()

        def resolve(key: str) -> Path:
            """One configured path field, or a structured stop.

            "Valid JSON" and "a usable path" are not the same claim, and the gap
            between them is reachable from an ordinary file: ``"bad\\u0000path"``
            is a perfectly good JSON string that ``Path.resolve`` refuses with a
            raw ``ValueError``, which the CLI — catching only ``PrProverError`` —
            would let out as a traceback instead of the documented
            ``invalid-config`` record and exit 64. So every way this can fail is
            translated here, and the value itself is never echoed: a path is
            operator-supplied text that may carry a token or a credential-shaped
            segment, and the key alone says which field to fix.
            """
            value = raw.get(key)
            if not isinstance(value, str) or not value:
                raise ConfigError(f"config {key} must be a non-empty path", evidence={"key": key})
            if "\x00" in value:
                raise ConfigError(
                    f"config {key} contains a NUL byte and is not a usable path",
                    evidence={"key": key},
                )
            try:
                candidate = Path(value).expanduser()
                return (
                    candidate.resolve()
                    if candidate.is_absolute()
                    else (root / candidate).resolve()
                )
            except (OSError, RuntimeError, ValueError) as exc:
                raise ConfigError(
                    f"config {key} could not be resolved to a filesystem path",
                    evidence={"key": key, "error": type(exc).__name__},
                ) from exc

        visual_required = raw.get("visual_qa_required", False)
        if not isinstance(visual_required, bool):
            raise ConfigError(
                "config visual_qa_required must be a boolean",
                evidence={"visual_qa_required": visual_required},
            )

        gates = tuple(_gate(item, index) for index, item in enumerate(_sequence(raw, "gates", required=False)))
        _reject_duplicates([gate.name for gate in gates], what="gate")
        reviewers = tuple(
            _reviewer(item, index) for index, item in enumerate(_sequence(raw, "reviewers", required=True))
        )
        _reject_duplicates([reviewer.name for reviewer in reviewers], what="reviewer")
        # Two lanes sharing a role could each satisfy the other's artifact
        # readback, which is exactly the independence the lanes exist for; and
        # the required sequence is the acceptance lifecycle itself, so a missing
        # auditor or a reordered one is rejected here rather than discovered
        # afterwards in a run that already reported.
        _reject_duplicates([reviewer.role for reviewer in reviewers], what="reviewer role")
        roles = tuple(reviewer.role for reviewer in reviewers)
        if roles != REQUIRED_REVIEWER_ROLES:
            raise ConfigError(
                "config reviewers must be exactly "
                + ", ".join(REQUIRED_REVIEWER_ROLES)
                + ", in that order: the Integration Auditor reconciles the Reviewer A "
                "and Reviewer B artifacts, so it cannot be missing, duplicated, or run first",
                evidence={
                    "required_roles": list(REQUIRED_REVIEWER_ROLES),
                    "configured_roles": list(roles),
                },
            )

        if visual_required and not any(gate.kind == "visual" for gate in gates):
            raise ConfigError(
                "visual_qa_required is set but no gate of kind 'visual' is configured",
                evidence={"gate_kinds": sorted({gate.kind for gate in gates})},
            )

        governing_issues = _governing_issues(raw)
        operator_acknowledgements = _operator_acknowledgements(raw)

        branch = _optional_text(raw, "branch")
        base = _optional_text(raw, "base")

        source_repo = resolve("source_repo")
        state_file = resolve("state_file")
        lock_file = resolve("lock_file")
        _reject_control_paths_inside(source_repo, state_file=state_file, lock_file=lock_file)

        return cls(
            repo=repo,
            pr=pr,
            source_repo=source_repo,
            worktree_root=resolve("worktree_root"),
            state_file=state_file,
            lock_file=lock_file,
            builder=_builder(raw.get("builder")),
            reviewers=reviewers,
            governing_issues=governing_issues,
            gates=gates,
            branch=branch,
            base=base,
            visual_qa_required=visual_required,
            operator_acknowledgements=operator_acknowledgements,
            source=source,
        )


def _reject_control_paths_inside(source_repo: Path, **control_files: Path) -> None:
    """Keep this run's own bookkeeping out of the clone it is judging.

    ``RunState.save`` and ``RunLock`` write these paths, while the loop
    separately guarantees that the operational clone is never modified and that
    an attempt worktree is clean. A control file equal to, or nested inside, the
    source clone would break both guarantees the moment the run started, so the
    overlap is refused at configuration time rather than discovered as a dirty
    tree later. Sibling and outside paths are untouched by this rule.
    """
    for key, path in sorted(control_files.items()):
        if path == source_repo or path.is_relative_to(source_repo):
            raise ConfigError(
                f"config {key} is inside the operational clone; "
                "state and lock files must live outside source_repo",
                evidence={key: str(path), "source_repo": str(source_repo)},
            )


def _governing_issues(raw: Mapping[str, Any]) -> tuple[int, ...]:
    """The issue numbers whose bodies are this run's task contract.

    Required, and required to be non-empty. The reviewer lanes are handed these
    bodies in place of GitHub, and a lane with no contract in front of it can
    still write a confident review — of whether the code looks nice. Which issue
    governs is also exactly the question a PR body must not be allowed to answer
    for itself, so it is asked here, of the operator, once.
    """
    value = raw.get("governing_issues")
    if not isinstance(value, list) or not value:
        raise ConfigError(
            "config governing_issues must list at least one issue number: it is the "
            "task contract every credential-free reviewer is handed in place of "
            "GitHub, and it comes from this file rather than from the PR's own prose",
            evidence={"governing_issues": value if isinstance(value, (list, int, str)) else None},
        )
    if len(value) > MAX_GOVERNING_ISSUES:
        raise ConfigError(
            f"config governing_issues names more than {MAX_GOVERNING_ISSUES} issues",
            evidence={"count": len(value), "limit": MAX_GOVERNING_ISSUES},
        )
    numbers: list[int] = []
    for index, item in enumerate(value):
        if not isinstance(item, int) or isinstance(item, bool) or item < 1:
            raise ConfigError(
                f"config governing_issues[{index}] must be a positive issue number",
                evidence={"index": index, "value": item if isinstance(item, int) else None},
            )
        if item in numbers:
            raise ConfigError(
                "config governing_issues names the same issue twice",
                evidence={"issue": item},
            )
        numbers.append(item)
    return tuple(numbers)


def _operator_acknowledgements(
    raw: Mapping[str, Any],
) -> tuple[OperatorAcknowledgement, ...]:
    """The acknowledgement posts the operator authorized before launch.

    Optional, and absent means the strictest thing this tool can mean: no post
    written under a configured publishing login may acknowledge anything. What
    the field adds is per-post, not per-account — an operator who has read one
    exact post says so by naming the id GitHub assigned it and the digest of what
    it said — so everything here is checked as an id and a digest, and nothing is
    accepted as a rule about authors.

    Both halves are required, and neither is a default. An id with no
    ``body_evidence`` would be an authorization of whatever that post is edited
    to say later, which is the one thing an operator cannot have read; a digest
    with no id would be an authorization of any post that happens to match. So a
    pin is a mapping of exactly those two keys, and an entry missing one, or
    carrying a third, is refused rather than half-applied.

    Strictness is the point of each refusal below. A non-string, a whitespace or
    control character, or an over-long value is not an id this tool could ever
    match against a GitHub artifact; anything but a lower-case sixty-four
    character hex digest is not evidence it could ever match either, and
    accepting one would leave an operator believing a post was pinned when
    nothing was. A repeated id is a file whose author has lost track of what they
    authorized. The count is bounded for the same reason ``governing_issues`` is:
    a list a human cannot check by eye has stopped being a list of decisions.

    A malformed entry is never echoed back. It is operator-supplied text of
    unknown provenance, and the index says which entry to fix.
    """
    value = raw.get("operator_acknowledgements")
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ConfigError(
            "config operator_acknowledgements must be a list of {'id', "
            "'body_evidence'} pins; it preauthorizes specific acknowledgement "
            "posts and is never a login, a pattern, or a prefix",
            evidence={"key": "operator_acknowledgements"},
        )
    if len(value) > MAX_OPERATOR_ACKNOWLEDGEMENTS:
        raise ConfigError(
            f"config operator_acknowledgements names more than "
            f"{MAX_OPERATOR_ACKNOWLEDGEMENTS} artifacts",
            evidence={"count": len(value), "limit": MAX_OPERATOR_ACKNOWLEDGEMENTS},
        )
    pins: list[OperatorAcknowledgement] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != _ACKNOWLEDGEMENT_KEYS:
            raise ConfigError(
                f"config operator_acknowledgements[{index}] must be an object with "
                "exactly 'id' and 'body_evidence': the exact immutable GitHub "
                "artifact id, and the sha256 publication-evidence digest of the "
                "body that post held when you read it",
                evidence={"index": index},
            )
        identifier = item["id"]
        evidence = item["body_evidence"]
        if not isinstance(identifier, str) or not _ARTIFACT_ID.match(identifier):
            raise ConfigError(
                f"config operator_acknowledgements[{index}].id must be one exact "
                "immutable GitHub artifact id: a bounded string of letters, digits, "
                "'.', '_', ':', '=', or '-', with no whitespace in it",
                evidence={"index": index},
            )
        if not isinstance(evidence, str) or not _BODY_EVIDENCE.match(evidence):
            raise ConfigError(
                f"config operator_acknowledgements[{index}].body_evidence must be "
                "one lower-case sha256 hex digest of the exact post body you "
                "authorized; a post whose current body does not match it is refused",
                evidence={"index": index},
            )
        if any(pin.identifier == identifier for pin in pins):
            raise ConfigError(
                "config operator_acknowledgements names the same artifact twice",
                evidence={"artifact_id": identifier},
            )
        pins.append(
            OperatorAcknowledgement(identifier=identifier, body_evidence=evidence)
        )
    return tuple(pins)


def _sequence(raw: Mapping[str, Any], key: str, *, required: bool) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise ConfigError(f"config {key} must be a list", evidence={"key": key})
    if required and not value:
        raise ConfigError(f"config {key} must not be empty", evidence={"key": key})
    return value


def _optional_text(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigError(f"config {key} must be a non-empty string when present", evidence={"key": key})
    return value


def _timeout(raw: Mapping[str, Any], *, what: str) -> float | None:
    value = raw.get("timeout")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"{what} timeout must be a positive number", evidence={"timeout": value})
    return float(value)


def _checked_name(raw: Mapping[str, Any], *, what: str, index: int) -> str:
    value = raw.get("name")
    if not isinstance(value, str) or not _NAME.match(value):
        raise ConfigError(f"{what}[{index}] name is missing or unusable", evidence={"name": value})
    return value


def _gate(item: object, index: int) -> GateConfig:
    if not isinstance(item, Mapping):
        raise ConfigError(f"gates[{index}] must be an object")
    unknown = sorted(set(item) - _GATE_KEYS)
    if unknown:
        raise ConfigError(f"gates[{index}] has unknown keys", evidence={"unknown_keys": unknown})
    kind = item.get("kind", "baseline")
    if kind not in GATE_KINDS:
        raise ConfigError(
            f"gates[{index}] kind must be one of {list(GATE_KINDS)}", evidence={"kind": kind}
        )
    return GateConfig(
        name=_checked_name(item, what="gates", index=index),
        argv=validate_argv(item.get("argv"), what=f"gates[{index}].argv"),
        kind=kind,
        timeout=_timeout(item, what=f"gates[{index}]"),
        env=_lane_env(item, what=f"gates[{index}]"),
    )


def _reviewer(item: object, index: int) -> ReviewerConfig:
    if not isinstance(item, Mapping):
        raise ConfigError(f"reviewers[{index}] must be an object")
    unknown = sorted(set(item) - _REVIEWER_KEYS)
    if unknown:
        raise ConfigError(f"reviewers[{index}] has unknown keys", evidence={"unknown_keys": unknown})
    name = _checked_name(item, what="reviewers", index=index)
    role = item.get("role")
    if not isinstance(role, str) or not _NAME.match(role):
        raise ConfigError(
            f"reviewers[{index}].role is required and names the mission role this lane "
            "runs as; it is substituted into the lane's argv and must appear on its own "
            "line in the published artifact",
            evidence={"role": role, "required_roles": list(REQUIRED_REVIEWER_ROLES)},
        )
    author = item.get("artifact_author")
    if not isinstance(author, str) or not _LOGIN.match(author):
        raise ConfigError(
            f"reviewers[{index}].artifact_author is required and must be the exact GitHub "
            "login this reviewer publishes under; without it a review cannot be told "
            "apart from any other account's",
            evidence={"artifact_author": author},
        )
    signature = item.get("artifact_signature")
    if not isinstance(signature, str) or len(signature.strip()) < 8:
        raise ConfigError(
            f"reviewers[{index}].artifact_signature must be a distinctive string to read back",
            evidence={"artifact_signature": signature},
        )
    argv = validate_argv(item.get("argv"), what=f"reviewers[{index}].argv")
    env = _lane_env(item, what=f"reviewers[{index}]")
    relay = _relay(item.get("relay"), what=f"reviewers[{index}].relay")
    if relay is not None:
        # The handoff only works if both halves are handed the file: a reviewer
        # with nowhere to write, or a relay with nothing to post, would fail at
        # readback with no way to tell which half was misconfigured.
        if not any(_ARTIFACT_FILE in part for part in argv):
            raise ConfigError(
                f"reviewers[{index}] has a relay but its argv never receives "
                f"{_ARTIFACT_FILE}, so the lane has nowhere to prepare its artifact",
                evidence={"reviewer": name},
            )
        if not any(_ARTIFACT_FILE in part for part in relay.argv):
            raise ConfigError(
                f"reviewers[{index}].relay argv never receives {_ARTIFACT_FILE}, "
                "so it has no prepared artifact to publish",
                evidence={"reviewer": name},
            )
        # A relayed lane is the credential-free one. Naming a token for it in
        # the config contradicts the lifecycle rather than tightening it.
        for variable, _ in env.set:
            if variable in CREDENTIAL_ENV:
                raise ConfigError(
                    f"reviewers[{index}] uses the relay lifecycle, so it runs without a "
                    f"GitHub credential; remove {variable} from its env and let the relay publish",
                    evidence={"reviewer": name, "name": variable},
                )
        # ...and having no credential is not a limitation the lane can work
        # around: with no way to reach GitHub it needs the frozen packet, so a
        # relayed lane that is never handed one is refused here rather than
        # discovered as a lane that confidently reviewed nothing.
        if not any(_EVIDENCE_PACKET in part for part in argv):
            raise ConfigError(
                f"reviewers[{index}] uses the relay lifecycle, so its lane runs with no "
                f"GitHub credential and cannot read the PR; its argv must receive "
                f"{_EVIDENCE_PACKET} to be given the frozen evidence instead",
                evidence={"reviewer": name},
            )
    return ReviewerConfig(
        name=name,
        argv=argv,
        artifact_author=author,
        artifact_signature=signature.strip(),
        role=role,
        timeout=_timeout(item, what=f"reviewers[{index}]"),
        env=env,
        relay=relay,
    )


def _relay(item: object, *, what: str) -> RelayConfig | None:
    if item is None:
        return None
    if not isinstance(item, Mapping):
        raise ConfigError(f"{what} must be an object")
    unknown = sorted(set(item) - _RELAY_KEYS)
    if unknown:
        raise ConfigError(f"{what} has unknown keys", evidence={"unknown_keys": unknown})
    return RelayConfig(
        argv=validate_argv(item.get("argv"), what=f"{what}.argv"),
        timeout=_timeout(item, what=what),
        env=_lane_env(item, what=what),
    )


def _builder(item: object) -> BuilderConfig:
    if not isinstance(item, Mapping):
        raise ConfigError("config builder must be an object")
    unknown = sorted(set(item) - _BUILDER_KEYS)
    if unknown:
        raise ConfigError("config builder has unknown keys", evidence={"unknown_keys": unknown})
    signature = item.get("signature")
    if not isinstance(signature, str) or len(signature.strip()) < 8:
        raise ConfigError(
            "config builder.signature must be a distinctive string to read back",
            evidence={"signature": signature},
        )
    author = item.get("comment_author")
    if not isinstance(author, str) or not _LOGIN.match(author):
        raise ConfigError(
            "config builder.comment_author is required and must be the exact GitHub "
            "login the builder comments under; a signature alone is public and forgeable",
            evidence={"comment_author": author},
        )
    return BuilderConfig(
        argv=validate_argv(item.get("argv"), what="builder.argv"),
        signature=signature.strip(),
        comment_author=author,
        timeout=_timeout(item, what="builder"),
        env=_lane_env(item, what="builder"),
    )


def _lane_env(raw: Mapping[str, Any], *, what: str) -> LaneEnv:
    """Validate one lane's environment overlay."""
    overlay = raw.get("env", {})
    if not isinstance(overlay, Mapping):
        raise ConfigError(f"{what} env must be an object of NAME: value pairs")
    pairs: list[tuple[str, str]] = []
    for name, value in overlay.items():
        _checked_env_name(name, what=what)
        if not isinstance(value, str) or "\x00" in value:
            raise ConfigError(
                f"{what} env {name} must be a string value", evidence={"name": name}
            )
        if value.startswith(_CREDENTIAL_PREFIXES):
            raise ConfigError(
                f"{what} env {name} looks like a credential; keep tokens in the keychain "
                "and in gh's own auth, and let the lane read them there",
                evidence={"name": name},
            )
        pairs.append((name, value))
    names = raw.get("env_unset", [])
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise ConfigError(f"{what} env_unset must be a list of variable names")
    for name in names:
        _checked_env_name(name, what=what)
    return LaneEnv(set=tuple(pairs), unset=tuple(names))


def _checked_env_name(name: object, *, what: str) -> str:
    if not isinstance(name, str) or not _ENV_NAME.match(name):
        raise ConfigError(f"{what} environment variable name is unusable", evidence={"name": name})
    if name in _SESSION_ENV:
        raise ConfigError(
            f"{what} may not set or clear {name}: the trusted lanes run in the operator's "
            "own session and need the real Claude OAuth/keychain environment",
            evidence={"name": name, "session_variables": sorted(_SESSION_ENV)},
        )
    return name


def _reject_duplicates(names: list[str], *, what: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ConfigError(f"duplicate {what} name {name!r}", evidence={"name": name})
        seen.add(name)


__all__ = [
    "GATE_KINDS",
    "MAX_GOVERNING_ISSUES",
    "MAX_OPERATOR_ACKNOWLEDGEMENTS",
    "REALISTIC_BUILDER_BUDGET",
    "REALISTIC_REVIEWER_BUDGET",
    "REQUIRED_REVIEWER_ROLES",
    "SCHEMA_VERSION",
    "BuilderConfig",
    "GateConfig",
    "LaneEnv",
    "OperatorAcknowledgement",
    "RelayConfig",
    "ReviewerConfig",
    "RunConfig",
]
