"""Deterministic doubles for the prove loop.

No network, no ``gh``, and no real ``git``: the fake runner services the small
set of git calls the loop is allowed to make and hands every other argv array
to a scripted lane. A shared :class:`FakeRemote` is the single source of truth
for the head and the PR comments, so "the builder pushed" is one call that
moves the remote head, the remote-tracking ref, and the comment list together.
"""
from __future__ import annotations

import shutil
import sys
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pr_prover.commands import CommandResult, validate_argv
from pr_prover.config import RunConfig
from pr_prover.github import Comment, PullRequest

HEAD_A = "a" * 40
HEAD_B = "b" * 40
HEAD_C = "c" * 40
SIGNATURE = "Fixed by: Claude Code via Hermes orchestration"
REVIEWER_SIGNATURE = "Reviewed by: CodexReviewer via Hermes orchestration"
BRANCH = "feat/example"
BUILDER_LOGIN = "sabnanikl-dev"
REVIEWER_LOGIN = "karanagent1"


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


def reviewer_artifact(role: str, head: str, *, signature: str = REVIEWER_SIGNATURE) -> str:
    """The artifact body a reviewer lane is expected to publish on the PR."""
    return f"Reviewed the diff at this head.\n\n---\n{signature}\nROLE={role}\nHEAD: {head}\n"


# -- fakes ----------------------------------------------------------------
@dataclass
class FakeRemote:
    """The remote branch head, its history, and the published PR artifacts."""

    head: str = HEAD_A
    branch: str = BRANCH
    base: str = "main"
    number: int = 7
    state: str = "OPEN"
    is_draft: bool = True
    comments: list[Comment] = field(default_factory=list)
    reviews: list[Comment] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    _next_comment_id: int = 1
    _next_review_id: int = 1

    def __post_init__(self) -> None:
        if not self.history:
            self.history = [self.head]

    def push(self, head: str, *, comment: str | None = None, author: str = BUILDER_LOGIN) -> None:
        self.head = head
        self.history.append(head)
        if comment is not None:
            self.comment(comment, author=author)

    def comment(self, body: str, *, author: str = BUILDER_LOGIN) -> Comment:
        """Append a comment with a fresh, never-reused GitHub-style node id."""
        posted = Comment(
            identifier=f"IC_comment{self._next_comment_id}", author=author, body=body
        )
        self._next_comment_id += 1
        self.comments.append(posted)
        return posted

    def review(self, body: str, *, author: str = REVIEWER_LOGIN, commit_id: str = "") -> Comment:
        """Append a submitted review, which carries the commit it was made against."""
        posted = Comment(
            identifier=f"review:{self._next_review_id}",
            author=author,
            body=body,
            kind="review",
            commit_id=commit_id,
        )
        self._next_review_id += 1
        self.reviews.append(posted)
        return posted

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
        )


class FakeGitHub:
    """Reads only, from the shared remote."""

    def __init__(self, remote: FakeRemote) -> None:
        self.remote = remote
        self.pull_request_calls = 0
        self.comment_calls = 0
        self.review_calls = 0

    def pull_request(self, repo: str, number: int) -> PullRequest:
        self.pull_request_calls += 1
        return self.remote.pull_request()

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        self.comment_calls += 1
        return tuple(self.remote.comments)

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]:
        self.review_calls += 1
        return tuple(self.remote.reviews)


@dataclass(frozen=True)
class Call:
    argv: tuple[str, ...]
    cwd: str | None


@dataclass(frozen=True)
class ScriptedResult:
    """One queued lane outcome: what it printed and how the process ended."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    after: Callable[[], None] | None


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
    ) -> LaneScript:
        self._queues.setdefault(program, deque()).append(
            ScriptedResult(
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                timed_out=timed_out,
                after=after,
            )
        )
        return self

    def __call__(self, argv: tuple[str, ...], cwd: str | None) -> CommandResult:
        queue = self._queues.get(argv[0])
        if not queue:
            raise AssertionError(f"unscripted lane call: {list(argv)}")
        scripted = queue.popleft()
        if scripted.after is not None:
            scripted.after()
        return CommandResult(
            argv=argv,
            returncode=scripted.returncode,
            stdout=scripted.stdout,
            stderr=scripted.stderr,
            timed_out=scripted.timed_out,
        )

    @property
    def exhausted(self) -> bool:
        return all(not queue for queue in self._queues.values())


class FakeRunner:
    """Services the loop's permitted git calls; delegates lanes to a script.

    A real reviewer lane publishes its own artifact on the PR, so this runner
    does that for any ``lane-reviewer-*`` program it launches. The knobs are the
    ways that can go wrong: not publishing at all, publishing under the wrong
    login, with the wrong role, or bound to the wrong head.
    """

    def __init__(self, remote: FakeRemote, script: LaneScript | None = None) -> None:
        self.remote = remote
        # Where reviewer artifacts are published. Held separately from
        # ``remote`` so a test can swap the branch out from under the run —
        # remote drift — without also moving the PR the artifacts land on.
        self.artifacts = remote
        self.script = script or LaneScript()
        self.calls: list[Call] = []
        self.envs: list[Mapping[str, str] | None] = []
        self.worktree_status = ""
        self.fetch_failures = 0
        self.local_head: str | None = None
        self.publish_reviewer_artifacts = True
        self.reviewer_artifact_author = REVIEWER_LOGIN
        self.reviewer_artifact_signature = REVIEWER_SIGNATURE
        self.reviewer_artifact_role: str | None = None
        self.reviewer_artifact_head: str | None = None
        self.reviewer_artifact_kind = "comment"

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        progress: Callable[[object], None] | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        self.calls.append(Call(argv=checked, cwd=str(cwd) if cwd is not None else None))
        if checked[0] == "git":
            return self._git(checked)
        self.envs.append(env)
        result = self.script(checked, str(cwd) if cwd is not None else None)
        if checked[0].startswith("lane-reviewer") and self.publish_reviewer_artifacts:
            self._publish_reviewer_artifact(checked)
        return result

    # -- reviewer artifacts -------------------------------------------------
    def _publish_reviewer_artifact(self, argv: tuple[str, ...]) -> None:
        role = self.reviewer_artifact_role or _flag(argv, "--role") or argv[0]
        head = self.reviewer_artifact_head or _flag(argv, "--head") or self.artifacts.head
        body = reviewer_artifact(role, head, signature=self.reviewer_artifact_signature)
        if self.reviewer_artifact_kind == "review":
            self.artifacts.review(body, author=self.reviewer_artifact_author, commit_id=head)
        else:
            self.artifacts.comment(body, author=self.reviewer_artifact_author)

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
        if rest[0] == "rev-parse":
            if rest[1:] == ("HEAD",):
                head = self.local_head or self.remote.head
                return CommandResult(argv=argv, returncode=0, stdout=head + "\n", stderr="")
            return CommandResult(argv=argv, returncode=0, stdout=self.remote.head + "\n", stderr="")
        if rest[0] == "rev-list":
            left, _, right = rest[-1].partition("..")
            listed = "\n".join(self._rev_list(left, right))
            return CommandResult(argv=argv, returncode=0, stdout=listed + "\n", stderr="")
        if rest[0] == "worktree" and rest[1] == "add":
            path = Path(rest[3])
            path.mkdir(parents=True, exist_ok=False)
            (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "worktree" and rest[1] == "remove":
            shutil.rmtree(Path(rest[3]), ignore_errors=True)
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "status":
            return CommandResult(argv=argv, returncode=0, stdout=self.worktree_status, stderr="")
        raise AssertionError(f"unexpected git call: {list(argv)}")

    def _rev_list(self, left: str, right: str) -> list[str]:
        """``git rev-list left..right`` over the fake branch history, newest first."""
        history = self.remote.history
        if right not in history:
            # Not reachable from anything on this branch: it is the whole answer.
            return [right]
        end = history.index(right)
        start = history.index(left) if left in history else -1
        if end <= start:
            return []
        return list(reversed(history[start + 1 : end + 1]))

    # -- assertions -------------------------------------------------------
    def git_subcommands(self, repo_path: Path) -> list[str]:
        target = str(Path(repo_path).resolve())
        return [call.argv[3] for call in self.calls if call.argv[0] == "git" and call.argv[2] == target]


def _flag(argv: Sequence[str], name: str) -> str | None:
    for index, item in enumerate(argv):
        if item == name and index + 1 < len(argv):
            return argv[index + 1]
    return None


def make_config(
    tmp: Path,
    *,
    source_repo: Path,
    gates: Sequence[Mapping[str, object]] = (),
    visual_qa_required: bool = False,
    comment_author: str = BUILDER_LOGIN,
    reviewer_author: str = REVIEWER_LOGIN,
    branch: str | None = BRANCH,
    builder_env: Mapping[str, object] | None = None,
    reviewer_env: Mapping[str, object] | None = None,
) -> RunConfig:
    payload: dict[str, object] = {
        "schema_version": 1,
        "repo": "example/repo",
        "pr": 7,
        "branch": branch,
        "base": "main",
        "source_repo": str(source_repo),
        "worktree_root": str(tmp / "worktrees"),
        "state_file": str(tmp / "state.json"),
        "lock_file": str(tmp / "run.lock"),
        "visual_qa_required": visual_qa_required,
        "gates": list(gates),
        "reviewers": [
            {
                "name": "A",
                "role": "reviewer-a",
                "argv": [
                    "lane-reviewer-A", "--role", "{role}", "--head", "{head}", "--repo", "{repo}"
                ],
                "artifact_author": reviewer_author,
                "artifact_signature": REVIEWER_SIGNATURE,
            },
            {
                "name": "B",
                "role": "reviewer-b",
                "argv": [
                    "lane-reviewer-B", "--role", "{role}", "--head", "{head}", "--pr", "{pr}"
                ],
                "artifact_author": reviewer_author,
                "artifact_signature": REVIEWER_SIGNATURE,
            },
        ],
        "builder": {
            "argv": ["lane-builder", "--blockers", "{blockers_file}", "--mode", "{mode}", "--head", "{head}"],
            "signature": SIGNATURE,
            "comment_author": comment_author,
        },
    }
    if branch is None:
        payload.pop("branch")
    if builder_env:
        payload["builder"].update(builder_env)  # type: ignore[union-attr]
    if reviewer_env:
        for lane in payload["reviewers"]:  # type: ignore[union-attr]
            lane.update(reviewer_env)
    return RunConfig.from_mapping(payload, base_dir=tmp)


def make_source_repo(tmp: Path) -> Path:
    """A directory that looks enough like a checkout for :class:`SourceRepo`."""
    path = tmp / "clone"
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
    return path.resolve()
