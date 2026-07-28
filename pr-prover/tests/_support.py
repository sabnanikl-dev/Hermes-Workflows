"""Deterministic doubles for the prove loop.

No network, no ``gh``, and no real ``git``: the fake runner services the small
set of git calls the loop is allowed to make and hands every other argv array
to a scripted lane. A shared :class:`FakeRemote` is the single source of truth
for the head, the PR comments, and the submitted reviews, so "the builder
pushed" is one call that moves the remote head, the remote-tracking ref, and the
conversation together.

The reviewer artifact lifecycle is modelled here too, because it is now part of
every run rather than an option. A reviewer lane call writes a conforming
artifact to its ``--artifact-file``, and the relay program publishes that file to
the remote under the configured reviewer login. Both are defaults a test can
override: :attr:`FakeRunner.reviewer_artifact` replaces the body a lane writes,
:attr:`FakeRunner.relay_body` replaces the body the relay publishes — the two
are separate on purpose, because a transport that posts something other than
what it was handed is exactly what validating the prepared file cannot see — and
:attr:`FakeRunner.relay_failures` makes the transport half fail.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pr_prover.commands import (
    RUNNER_DEFAULT,
    Budget,
    CommandResult,
    Progress,
    validate_argv,
)
from pr_prover.config import RunConfig
from pr_prover.errors import MalformedVerdict
from pr_prover.findings import Finding, FindingLocation, FindingProvenance
from pr_prover.github import (
    CheckRun,
    Comment,
    GoverningIssue,
    InlineComment,
    LinkedIssue,
    PullRequest,
    ReviewEvidence,
    ReviewThread,
)
from pr_prover.verdicts import MAX_SUMMARY, finding_records

HEAD_A = "a" * 40
HEAD_B = "b" * 40
HEAD_C = "c" * 40
ROOT = "0" * 40
SIGNATURE = "Fixed by: Claude Code via Hermes orchestration"
BRANCH = "feat/example"
BUILDER_LOGIN = "sabnanikl-dev"
REVIEWER_LOGIN = "karanagent1"
REVIEWER_SIGNATURE = "Reviewed by: CodexReviewer via Hermes orchestration"
REVIEWER_RUNTIME = "codex-exec/test"
# The three lanes the acceptance lifecycle requires, in order, as
# ``(lane name, role, lane program)``.
REVIEWER_LANES = (
    ("A", "reviewer-a", "lane-reviewer-A"),
    ("B", "reviewer-b", "lane-reviewer-B"),
    ("Auditor", "integration-auditor", "lane-reviewer-Auditor"),
)
RELAY_PROGRAM = "lane-relay"
# The task contract a run is configured against, and the two bodies a
# credential-free reviewer is handed in place of reading GitHub itself. They
# carry distinctive text so a test can prove which document reached the lane.
GOVERNING_ISSUE = 1
GOVERNING_ISSUE_BODY = "ACCEPTANCE: the governing issue contract body"
PR_BODY = "This change claims: the live pull request body"


def reviewer_artifact(
    *,
    role: str,
    head: str,
    status: str = "pass",
    blocking: int = 0,
    runtime: str = REVIEWER_RUNTIME,
    signature: str = REVIEWER_SIGNATURE,
    kill_switches: Sequence[str] = ("tried to find a weakened test; found none",),
    findings: Sequence[tuple[str, str, str]] = (),
    extra: str = "",
) -> str:
    """One conforming reviewer artifact body.

    ``findings`` are the same ``(severity, id, summary)`` triples
    :func:`reviewer_output` builds a lane's final message from, written in the
    grammar the parser reads. A real artifact restates the findings its lane
    reported, and the relay holds it to exactly that, so the double does too.
    """
    lines = [
        f"ROLE={role}",
        f"RUNTIME={runtime}",
        f"HEAD={head}",
        f"STATUS={status}",
        f"BLOCKING={blocking}",
        *(f"KILL-SWITCH: {entry}" for entry in kill_switches),
        *(
            f"FINDING: SEVERITY={severity} ID={identifier} -- {summary}"
            for severity, identifier, summary in findings
        ),
        signature,
    ]
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"

# ``push(parent=...)`` default: the pushed commit sits on the head it replaced,
# which is what an ordinary non-destructive push does.
_INHERIT = object()


# -- the finding-summary boundary -----------------------------------------
# Where the varying region sits inside a maximum-length summary. Chosen to land
# inside the window clipping to MAX_SUMMARY would elide, not in either end it
# keeps — which is what makes two summaries built with different markers a real
# collapse pair rather than merely two long strings.
_VARY_AT = 150


def secret_bearing_summary(marker: str) -> str:
    """One exactly-``MAX_SUMMARY`` summary carrying a real secret, varying at ``marker``.

    Two summaries built with different equal-length markers differ only in a
    region that clipping to ``MAX_SUMMARY`` throws away. That matters because
    scrubbing the secret makes the text *longer* than the limit, so a parser that
    clips after scrubbing does not merely shorten the record — it collapses two
    different records into one stored value, and a one-to-one comparison against
    a stored value that lost the difference cannot tell them apart.

    The tests assert both halves of that rather than trusting this construction:
    that the pair really does collapse under the old clip, and that the shipped
    parser keeps them distinct.
    """
    prefix = "the lane pasted a header: "
    secret = " Authorization: bearer x"
    head_filler = _VARY_AT - len(prefix)
    tail_filler = MAX_SUMMARY - _VARY_AT - len(marker) - len(secret)
    if head_filler < 0 or tail_filler < 0:  # pragma: no cover - marker is a constant
        raise AssertionError(f"marker {marker!r} does not fit one summary")
    summary = f"{prefix}{'z' * head_filler}{marker}{'z' * tail_filler}{secret}"
    assert len(summary) == MAX_SUMMARY, len(summary)
    return summary


# -- lane output builders -------------------------------------------------
def reviewer_output(head: str, findings: Sequence[tuple[str, str, str]] = (), *, extra: str = "") -> str:
    """Build reviewer output from ``(severity, id, summary)`` triples."""
    lines = [f"FINDING: SEVERITY={severity} ID={identifier} -- {summary}" for severity, identifier, summary in findings]
    if extra:
        lines.append(extra)
    blocking = sum(1 for severity, _, _ in findings if severity == "blocking")
    lines.append(f"DONE: STATUS={'fail' if blocking else 'pass'} BLOCKING={blocking} HEAD={head}")
    return "\n".join(lines) + "\n"


def builder_output(
    head: str,
    *,
    pr: int = 7,
    branch: str = BRANCH,
    addressed: Sequence[str] = (),
    status: str = "success",
) -> str:
    lines = [f"ADDRESSED: ID={identifier}" for identifier in addressed]
    lines.append(f"DONE: PR={pr} BRANCH={branch} STATUS={status} HEAD={head}")
    return "\n".join(lines) + "\n"


def fix_comment(head: str) -> str:
    return f"Fixed the blockers on this head.\n\n---\n{SIGNATURE}\nHEAD: {head}\n"


# -- finding builders -----------------------------------------------------
def make_provenance(
    source: str = "reviewer:A",
    *,
    head: str = HEAD_A,
    kind: str = "lane-output",
    reference: str | None = None,
    line: int | None = 1,
    excerpt: str = "FINDING: SEVERITY=blocking ID=x -- s",
) -> FindingProvenance:
    """Provenance from a ``role:agent`` source label, the way lanes spell it."""
    role, _, agent_id = source.partition(":")
    return FindingProvenance(
        agent_id=agent_id or source,
        role=role,
        head=head,
        location=FindingLocation(kind=kind, reference=reference or source, line=line),
        evidence_excerpt=excerpt,
    )


def make_finding(
    identifier: str,
    severity: str = "blocking",
    source: str = "reviewer:A",
    *,
    head: str = HEAD_A,
    summary: str = "s",
    detail: str = "",
    provenance: FindingProvenance | None = None,
) -> Finding:
    return Finding(
        id=identifier,
        severity=severity,
        summary=summary,
        provenance=provenance or make_provenance(source, head=head),
        detail=detail,
    )


# -- fakes ----------------------------------------------------------------
@dataclass
class FakeRemote:
    """The remote branch head, the PR commit list, and the PR conversation."""

    head: str = HEAD_A
    branch: str = BRANCH
    base: str = "main"
    number: int = 7
    state: str = "OPEN"
    is_draft: bool = True
    comments: list[Comment] = field(default_factory=list)
    reviews: list[Comment] = field(default_factory=list)
    threads: list[ReviewThread] = field(default_factory=list)
    commit_oids: list[str] = field(default_factory=list)
    # The read-only surfaces a credential-free lane is handed in a frozen packet
    # instead of reading them itself. Empty is the ordinary case for this PR;
    # a test fills them in to prove they reach the lane.
    inline_comments: list[InlineComment] = field(default_factory=list)
    check_runs: list[CheckRun] = field(default_factory=list)
    linked_issues: list[LinkedIssue] = field(default_factory=list)
    # The change's own stated contract and the contract it is measured against.
    # Both are ordinary here, because both are on the shipped path: every real
    # PR has a body, and every configured run names a governing issue.
    body: str = PR_BODY
    governing_issues: list[GoverningIssue] = field(
        default_factory=lambda: [
            GoverningIssue(
                number=GOVERNING_ISSUE,
                title="mission contract",
                state="OPEN",
                body=GOVERNING_ISSUE_BODY,
                url="https://example.invalid/issues/1",
            )
        ]
    )
    governing_issues_complete: bool = True
    # Commit -> its first parent. This is the only thing that makes "the new
    # head descends from the old one" a question the doubles can answer, so a
    # force-pushed replacement is expressible rather than indistinguishable
    # from an ordinary push.
    parents: dict[str, str | None] = field(default_factory=dict)
    _next_comment_id: int = 1

    def __post_init__(self) -> None:
        if not self.commit_oids:
            self.commit_oids = [self.head]
        self.parents.setdefault(self.head, None)

    def push(
        self,
        head: str,
        *,
        comment: str | None = None,
        author: str = BUILDER_LOGIN,
        parent: object = _INHERIT,
    ) -> None:
        """Move the head. ``parent`` names the history the new commit sits on.

        The default is the head being replaced, i.e. an ordinary push. Passing
        ``None`` models an unrelated root, and passing an earlier commit models
        a force-pushed rewrite that drops what used to be on top.
        """
        self.parents[head] = self.head if parent is _INHERIT else parent
        self.head = head
        if head not in self.commit_oids:
            self.commit_oids.append(head)
        if comment is not None:
            self.comment(comment, author=author)

    def is_ancestor(self, old: str, new: str) -> bool:
        """``git merge-base --is-ancestor old new`` over the recorded parents."""
        cursor: str | None = new
        seen: set[str] = set()
        while cursor is not None and cursor not in seen:
            if cursor == old:
                return True
            seen.add(cursor)
            cursor = self.parents.get(cursor)
        return False

    def comment(
        self, body: str, *, author: str = BUILDER_LOGIN, created_at: str | None = None
    ) -> Comment:
        """Append a comment with a fresh, never-reused GitHub-style node id."""
        posted = Comment(
            identifier=f"IC_comment{self._next_comment_id}",
            author=author,
            body=body,
            created_at=self._stamp() if created_at is None else created_at,
        )
        self._next_comment_id += 1
        self.comments.append(posted)
        return posted

    def review(
        self,
        body: str,
        *,
        author: str = REVIEWER_LOGIN,
        commit_id: str = "",
        state: str = "COMMENTED",
        created_at: str | None = None,
    ) -> Comment:
        """Append a submitted review, in the namespaced id space reviews use."""
        posted = Comment(
            identifier=f"review:{self._next_comment_id}",
            author=author,
            body=body,
            kind="review",
            commit_id=commit_id,
            state=state,
            created_at=self._stamp() if created_at is None else created_at,
        )
        self._next_comment_id += 1
        self.reviews.append(posted)
        return posted

    def thread(
        self,
        body: str,
        *,
        author: str = "karan",
        resolved: bool = False,
        outdated: bool = False,
        path: str = "src/thing.py",
    ) -> ReviewThread:
        """Append one inline review thread carrying a single comment."""
        posted = ReviewThread(
            identifier=f"PRRT_thread{self._next_comment_id}",
            is_resolved=resolved,
            is_outdated=outdated,
            path=path,
            comments=(
                Comment(
                    identifier=f"PRRC_reply{self._next_comment_id}",
                    author=author,
                    body=body,
                    kind="review-thread-comment",
                    created_at=self._stamp(),
                ),
            ),
        )
        self._next_comment_id += 1
        self.threads.append(posted)
        return posted

    def _stamp(self) -> str:
        """One UTC-aware GitHub-style timestamp per post, strictly increasing.

        Real posts arrive in order and say so, so the default double does too.
        A test that needs missing, equal, naive, or reordered chronology passes
        ``created_at`` explicitly rather than fighting this.
        """
        minute, second = divmod(self._next_comment_id, 60)
        return f"2026-07-27T{minute:02d}:{second:02d}:00Z"

    def review_evidence(self) -> ReviewEvidence:
        """What the boundary can tell a lane that cannot read GitHub itself.

        The completeness flags mirror the shipped ``gh`` boundary's own: every
        surface here is read to its last page.
        """
        return ReviewEvidence(
            inline_comments=tuple(self.inline_comments),
            check_runs=tuple(self.check_runs),
            linked_issues=tuple(self.linked_issues),
            governing_issues=tuple(self.governing_issues),
            inline_comments_complete=True,
            check_runs_complete=True,
            linked_issues_complete=True,
            governing_issues_complete=self.governing_issues_complete,
            conversation_comments_complete=True,
            reviews_complete=True,
        )

    def pull_request(self) -> PullRequest:
        return PullRequest(
            number=self.number,
            state=self.state,
            is_draft=self.is_draft,
            title="example",
            url=f"https://github.com/example/repo/pull/{self.number}",
            head_ref_name=self.branch,
            head_ref_oid=self.head,
            base_ref_name=self.base,
            body=self.body,
        )


class FakeGitHub:
    """Reads only, from the shared remote."""

    def __init__(self, remote: FakeRemote) -> None:
        self.remote = remote
        self.pull_request_calls = 0
        self.comment_calls = 0
        self.commit_calls = 0
        self.review_calls = 0
        self.thread_calls = 0
        self.review_evidence_calls = 0
        self.governing_issues_asked_for: list[tuple[int, ...]] = []

    def pull_request(self, repo: str, number: int) -> PullRequest:
        self.pull_request_calls += 1
        return self.remote.pull_request()

    def commits(self, repo: str, number: int) -> tuple[str, ...]:
        self.commit_calls += 1
        return tuple(self.remote.commit_oids)

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        self.comment_calls += 1
        return tuple(self.remote.comments)

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]:
        self.review_calls += 1
        return tuple(self.remote.reviews)

    def review_threads(self, repo: str, number: int) -> tuple[ReviewThread, ...]:
        self.thread_calls += 1
        return tuple(self.remote.threads)

    def review_evidence(
        self, repo: str, number: int, head: str, governing_issues: Sequence[int]
    ) -> ReviewEvidence:
        self.review_evidence_calls += 1
        self.governing_issues_asked_for.append(tuple(governing_issues))
        return self.remote.review_evidence()


@dataclass(frozen=True)
class Call:
    argv: tuple[str, ...]
    cwd: str | None


@dataclass(frozen=True)
class ScriptedResult:
    """One queued lane outcome: what it printed and how the process ended.

    ``duration``/``quiet_seconds`` are what the real runner measures while a
    child runs, and ``progress`` is what it reported *during* the run as
    ``(elapsed, output_bytes, quiet_seconds)`` observations. All three default
    to "instant and talkative", which is what almost every test wants; a test
    about a lane that went quiet for twenty minutes sets them explicitly.
    """

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    after: Callable[[], None] | None
    duration: float = 0.0
    quiet_seconds: float = 0.0
    progress: tuple[tuple[float, int, float], ...] = ()


class LaneScript:
    """Queued outputs per lane program, keyed by ``argv[0]``."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[ScriptedResult]] = {}

    def add(
        self,
        program: str,
        stdout: str,
        *,
        returncode: int = 0,
        stderr: str = "",
        timed_out: bool = False,
        after: Callable[[], None] | None = None,
        duration: float = 0.0,
        quiet_seconds: float = 0.0,
        progress: Sequence[tuple[float, int, float]] = (),
    ) -> LaneScript:
        self._queues.setdefault(program, deque()).append(
            ScriptedResult(
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                timed_out=timed_out,
                after=after,
                duration=duration,
                quiet_seconds=quiet_seconds,
                progress=tuple(progress),
            )
        )
        return self

    def __call__(
        self,
        argv: tuple[str, ...],
        cwd: str | None,
        progress: Callable[[Progress], None] | None = None,
    ) -> CommandResult:
        queue = self._queues.get(argv[0])
        if not queue:
            if argv[0].startswith("lane-reviewer-"):
                # The acceptance lifecycle is three lanes, and most tests are
                # about one of them. An unscripted reviewer lane passes on the
                # head it was handed, so a test only scripts the lane it is
                # actually making a point about.
                return CommandResult(
                    argv=argv, returncode=0, stdout=reviewer_output(_flag(argv, "--head")), stderr=""
                )
            raise AssertionError(f"unscripted lane call: {list(argv)}")
        scripted = queue.popleft()
        # Replayed before ``after``, in the order the real runner reports them:
        # a progress observation is something said *while* the child is alive.
        if progress is not None:
            for elapsed, output_bytes, quiet in scripted.progress:
                progress(
                    Progress(
                        argv=argv,
                        elapsed=elapsed,
                        output_bytes=output_bytes,
                        quiet_seconds=quiet,
                    )
                )
        if scripted.after is not None:
            scripted.after()
        return CommandResult(
            argv=argv,
            returncode=scripted.returncode,
            stdout=scripted.stdout,
            stderr=scripted.stderr,
            timed_out=scripted.timed_out,
            duration=scripted.duration,
            quiet_seconds=scripted.quiet_seconds,
        )

    @property
    def exhausted(self) -> bool:
        return all(not queue for queue in self._queues.values())


class FakeRunner:
    """Services the loop's permitted git calls; delegates lanes to a script."""

    def __init__(self, remote: FakeRemote, script: LaneScript | None = None) -> None:
        self.remote = remote
        self.script = script or LaneScript()
        self.calls: list[Call] = []
        # ``git status --porcelain`` inside an *attempt* worktree. Lane
        # worktrees are not covered by this: each gate and reviewer lane now has
        # a checkout of its own, and the only honest way to model "the lane
        # dirtied its own tree" is to report what is really in that directory,
        # which is what :meth:`_porcelain` does.
        self.worktree_status = ""
        # ``git rev-parse HEAD`` inside a gate or reviewer worktree. ``None``
        # answers with the SHA that worktree was actually created at, the way a
        # detached checkout does — it does not follow the branch. A test pins
        # this to model a lane whose checkout moved underneath it.
        self.lane_worktree_head: str | None = None
        # Where each run-owned worktree was checked out, recorded by
        # ``git worktree add`` exactly as the real command's ``<commit-ish>``
        # argument would fix it.
        self.worktree_oids: dict[str, str] = {}
        self.fetch_failures = 0
        # ``git merge-base --is-ancestor`` runs this many times as an error
        # (exit 128) before answering, so "the ancestry question could not be
        # answered" is testable separately from "the answer was no".
        self.merge_base_failures = 0
        # ``git rev-parse HEAD`` inside a run-owned worktree. ``None`` models a
        # builder that really did commit and push from that worktree, so the
        # local HEAD follows the remote; a test sets it to pin a stale one.
        self.worktree_head: str | None = None
        # What ``git rev-parse <remote ref>`` answers. ``None`` follows the
        # remote object; a test pins it to model the branch moving underneath
        # the run without disturbing what GitHub reports or where a relay posts.
        self.remote_ref_head: str | None = None
        # What a reviewer lane writes to its ``--artifact-file``. ``None`` is a
        # conforming artifact derived from the lane's own arguments and verdict;
        # a callable takes ``(argv, status, blocking)`` and returns a body, and
        # returning ``None`` from it models a lane that wrote nothing at all.
        self.reviewer_artifact: Callable[..., str | None] | None = None
        # What the relay actually publishes, given the prepared bytes it was
        # handed. ``None`` publishes the file unchanged. A callable models
        # relay-side truncation or substitution: the transport reports success
        # and a *different* body lands on the pull request, which is the one
        # thing validating the prepared file cannot rule out.
        self.relay_body: Callable[[str], str] | None = None
        # How many relay calls fail before one succeeds.
        self.relay_failures = 0
        # How many relay calls report success while publishing nothing. This is
        # the transport that looks fine from the outside and left the PR
        # untouched — the one an artifact posted by somebody else could
        # otherwise be mistaken for.
        self.relay_noops = 0
        # Every prepared artifact path a relay was asked to publish.
        self.relayed_files: list[str] = []
        # What each reviewer lane was actually handed as frozen evidence, read
        # at call time. The scratch directory is cleaned up after a clean run,
        # so a test that waits until afterwards has nothing left to read.
        self.evidence_packets: list[dict] = []
        # The login the relay publishes under. Changing it models a relay that
        # reported success while the artifact landed as somebody else.
        self.relay_author = REVIEWER_LOGIN
        # Every environment the runner was handed, per lane program.
        self.lane_env: list[tuple[str, Mapping[str, str] | None]] = []
        # What ``GH_CONFIG_DIR`` actually pointed at when each lane was
        # launched, as ``(program, path, was an empty directory)``. Observed
        # here rather than after the run, because a clean run removes its
        # scratch directory and "the path is gone now" is not the question.
        self.lane_gh_config: list[tuple[str, str, bool]] = []
        # Every budget the runner was handed, per lane program.
        self.lane_budgets: list[tuple[str, Budget]] = []
        # What each builder invocation was actually handed, read at call time.
        # The scratch directory is cleaned up after a clean run, so a test that
        # waits until afterwards has nothing left to read.
        self.blocker_files: list[dict] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: Budget = RUNNER_DEFAULT,
        progress: Callable[..., None] | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        self.calls.append(Call(argv=checked, cwd=str(cwd) if cwd is not None else None))
        if checked[0] == "git":
            return self._git(checked)
        self.lane_env.append((checked[0], env))
        self.lane_budgets.append((checked[0], timeout))
        configured = (env or {}).get("GH_CONFIG_DIR")
        if configured is not None:
            directory = Path(configured)
            self.lane_gh_config.append(
                (checked[0], configured, directory.is_dir() and not any(directory.iterdir()))
            )
        if checked[0] == RELAY_PROGRAM:
            return self._relay(checked)
        blockers = _flag(checked, "--blockers")
        if blockers:
            self.blocker_files.append(
                json.loads(Path(blockers).read_text(encoding="utf-8"))
            )
        result = self.script(checked, str(cwd) if cwd is not None else None, progress)
        if checked[0].startswith("lane-reviewer-"):
            packet = _flag(checked, "--evidence-packet")
            if packet:
                self.evidence_packets.append(
                    json.loads(Path(packet).read_text(encoding="utf-8"))
                )
            self._prepare_artifact(checked, result)
        return result

    # -- the reviewer artifact lifecycle ----------------------------------
    def _prepare_artifact(self, argv: tuple[str, ...], result: CommandResult) -> None:
        """Write what this reviewer lane prepared, the way a real lane would."""
        target = _flag(argv, "--artifact-file")
        if not target:
            return
        status, blocking = _verdict_of(result.stdout)
        if self.reviewer_artifact is not None:
            body = self.reviewer_artifact(argv=argv, status=status, blocking=blocking)
        else:
            body = reviewer_artifact(
                role=_flag(argv, "--role"),
                head=_flag(argv, "--head"),
                status=status,
                blocking=blocking,
                findings=_findings_of(result.stdout),
            )
        if body is None:
            return
        Path(target).write_text(body, encoding="utf-8")

    def _relay(self, argv: tuple[str, ...]) -> CommandResult:
        """Publish a prepared artifact to the remote under the reviewer login."""
        if self.relay_failures:
            self.relay_failures -= 1
            return CommandResult(argv=argv, returncode=1, stdout="", stderr="relay refused")
        self.relayed_files.append(_flag(argv, "--file"))
        if self.relay_noops:
            self.relay_noops -= 1
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        source = Path(_flag(argv, "--file"))
        body = source.read_text(encoding="utf-8")
        if self.relay_body is not None:
            body = self.relay_body(body)
        self.remote.comment(body, author=self.relay_author)
        return CommandResult(argv=argv, returncode=0, stdout="", stderr="")

    # -- git --------------------------------------------------------------
    def _git(self, argv: tuple[str, ...]) -> CommandResult:
        if argv[1] != "-C":
            raise AssertionError(f"git call is not pinned to a directory: {list(argv)}")
        rest = argv[3:]
        if rest[0] == "fetch":
            if self.fetch_failures:
                self.fetch_failures -= 1
                return CommandResult(argv=argv, returncode=1, stdout="", stderr="fetch refused")
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "rev-parse" and rest[1] == "HEAD":
            if _is_attempt(argv[2]):
                head = self.remote.head if self.worktree_head is None else self.worktree_head
            elif self.lane_worktree_head is not None:
                head = self.lane_worktree_head
            else:
                head = self.worktree_oids.get(str(Path(argv[2]).resolve()), self.remote.head)
            return CommandResult(argv=argv, returncode=0, stdout=head + "\n", stderr="")
        if rest[0] == "rev-parse":
            head = self.remote.head if self.remote_ref_head is None else self.remote_ref_head
            return CommandResult(argv=argv, returncode=0, stdout=head + "\n", stderr="")
        if rest[0] == "merge-base" and rest[1] == "--is-ancestor":
            if self.merge_base_failures:
                self.merge_base_failures -= 1
                return CommandResult(
                    argv=argv,
                    returncode=128,
                    stdout="",
                    stderr="fatal: Not a valid object name",
                )
            ancestor = self.remote.is_ancestor(rest[2], rest[3])
            # git's own convention: 0 means "yes", 1 means "no", anything else
            # means the question was not answered.
            return CommandResult(
                argv=argv, returncode=0 if ancestor else 1, stdout="", stderr=""
            )
        if rest[0] == "worktree" and rest[1] == "add":
            path = Path(rest[3])
            path.mkdir(parents=True, exist_ok=False)
            (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
            self.worktree_oids[str(path.resolve())] = rest[4]
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "worktree" and rest[1] == "remove":
            path = Path(rest[3])
            self.worktree_oids.pop(str(path.resolve()), None)
            shutil.rmtree(path, ignore_errors=True)
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "status":
            status = (
                self.worktree_status if _is_attempt(argv[2]) else _porcelain(Path(argv[2]))
            )
            return CommandResult(argv=argv, returncode=0, stdout=status, stderr="")
        raise AssertionError(f"unexpected git call: {list(argv)}")

    # -- assertions -------------------------------------------------------
    def git_subcommands(self, repo_path: Path) -> list[str]:
        target = str(Path(repo_path).resolve())
        return [call.argv[3] for call in self.calls if call.argv[0] == "git" and call.argv[2] == target]


_ATTEMPT = re.compile(r"-attempt\d+\Z")


def _is_attempt(path: str) -> bool:
    """Is this the builder's attempt worktree rather than a gate/reviewer lane's?

    The two are modelled differently on purpose. An attempt worktree's ``git``
    answers are scripted, because the tests there are about a builder that
    pushed from somewhere else or left the tree dirty. A lane worktree's answers
    are read off the real directory, because the tests there are about one lane
    writing a file the next lane must not be able to see.
    """
    return bool(_ATTEMPT.search(Path(path).name))


def _porcelain(path: Path) -> str:
    """``git status --porcelain`` over what is actually in a lane's checkout."""
    if not path.is_dir():
        return ""
    return "".join(
        f"?? {item.name}\n" for item in sorted(path.iterdir(), key=lambda item: item.name)
        if item.name != ".git"
    )


def _flag(argv: Sequence[str], name: str) -> str:
    """The value of ``--flag value`` in an argv array, or ``""``."""
    for index, item in enumerate(argv[:-1]):
        if item == name:
            return argv[index + 1]
    return ""


def _findings_of(stdout: str) -> tuple[tuple[str, str, str], ...]:
    """The findings a lane's marker declared, read with the shipped grammar.

    Tolerant on purpose. A test that scripts a deliberately malformed lane is
    making a point about the parser the *loop* runs, and this double must not
    raise before the loop ever gets there — so an output the grammar refuses
    contributes no artifact findings and the loop stops where it should.
    """
    try:
        records = finding_records(stdout, lane="scripted reviewer lane")
    except MalformedVerdict:
        return ()
    return tuple((record.severity, record.id, record.summary) for record in records)


def _verdict_of(stdout: str) -> tuple[str, int]:
    """The ``STATUS``/``BLOCKING`` a reviewer lane's marker declared."""
    for line in reversed(stdout.splitlines()):
        if line.startswith("DONE: STATUS="):
            parts = dict(
                piece.split("=", 1) for piece in line[len("DONE: ") :].split() if "=" in piece
            )
            return parts.get("STATUS", "pass"), int(parts.get("BLOCKING", 0))
    return "pass", 0


def reviewer_lane(name: str, role: str, program: str) -> dict[str, object]:
    """One reviewer lane in the shipped relayed lifecycle."""
    return {
        "name": name,
        "role": role,
        "argv": [
            program,
            "--role",
            "{role}",
            "--head",
            "{head}",
            "--repo",
            "{repo}",
            "--pr",
            "{pr}",
            "--artifact-file",
            "{artifact_file}",
            "--evidence-packet",
            "{evidence_packet}",
        ],
        "artifact_author": REVIEWER_LOGIN,
        "artifact_signature": REVIEWER_SIGNATURE,
        "relay": {"argv": [RELAY_PROGRAM, "--file", "{artifact_file}", "--pr", "{pr}"]},
    }


def make_config(
    tmp: Path,
    *,
    source_repo: Path,
    gates: Sequence[Mapping[str, object]] = (),
    visual_qa_required: bool = False,
    comment_author: str = BUILDER_LOGIN,
    branch: str | None = BRANCH,
    state_file: str | None = None,
    lock_file: str | None = None,
    reviewers: Sequence[Mapping[str, object]] | None = None,
    governing_issues: Sequence[int] = (GOVERNING_ISSUE,),
    operator_acknowledgements: Sequence[str] | None = None,
) -> RunConfig:
    payload: dict[str, object] = {
        "schema_version": 2,
        "repo": "example/repo",
        "pr": 7,
        "branch": branch,
        "base": "main",
        "governing_issues": list(governing_issues),
        "source_repo": str(source_repo),
        "worktree_root": str(tmp / "worktrees"),
        "state_file": state_file or str(tmp / "state.json"),
        "lock_file": lock_file or str(tmp / "run.lock"),
        "visual_qa_required": visual_qa_required,
        "gates": list(gates),
        "reviewers": (
            list(reviewers)
            if reviewers is not None
            else [reviewer_lane(name, role, program) for name, role, program in REVIEWER_LANES]
        ),
        "builder": {
            "argv": ["lane-builder", "--blockers", "{blockers_file}", "--mode", "{mode}", "--head", "{head}"],
            "signature": SIGNATURE,
            "comment_author": comment_author,
        },
    }
    if branch is None:
        payload.pop("branch")
    # Absent unless a test pins something, so every other config in this suite
    # keeps proving the default publisher denial rather than a relaxed one.
    if operator_acknowledgements is not None:
        payload["operator_acknowledgements"] = list(operator_acknowledgements)
    return RunConfig.from_mapping(payload, base_dir=tmp)


def make_source_repo(tmp: Path) -> Path:
    """A directory that looks enough like a checkout for :class:`SourceRepo`."""
    path = tmp / "clone"
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
    return path.resolve()
