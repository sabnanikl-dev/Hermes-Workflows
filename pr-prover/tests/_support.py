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
BRANCH = "feat/example"
BUILDER_LOGIN = "sabnanikl-dev"


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
    commit_oids: list[str] = field(default_factory=list)
    _next_comment_id: int = 1

    def __post_init__(self) -> None:
        if not self.commit_oids:
            self.commit_oids = [self.head]

    def push(self, head: str, *, comment: str | None = None, author: str = BUILDER_LOGIN) -> None:
        self.head = head
        if head not in self.commit_oids:
            self.commit_oids.append(head)
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
        self.commit_calls = 0

    def pull_request(self, repo: str, number: int) -> PullRequest:
        self.pull_request_calls += 1
        return self.remote.pull_request()

    def commits(self, repo: str, number: int) -> tuple[str, ...]:
        self.commit_calls += 1
        return tuple(self.remote.commit_oids)

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        self.comment_calls += 1
        return tuple(self.remote.comments)


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
    """Services the loop's permitted git calls; delegates lanes to a script."""

    def __init__(self, remote: FakeRemote, script: LaneScript | None = None) -> None:
        self.remote = remote
        self.script = script or LaneScript()
        self.calls: list[Call] = []
        self.worktree_status = ""
        self.fetch_failures = 0
        # ``git rev-parse HEAD`` inside a run-owned worktree. ``None`` models a
        # builder that really did commit and push from that worktree, so the
        # local HEAD follows the remote; a test sets it to pin a stale one.
        self.worktree_head: str | None = None

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        self.calls.append(Call(argv=checked, cwd=str(cwd) if cwd is not None else None))
        if checked[0] == "git":
            return self._git(checked)
        return self.script(checked, str(cwd) if cwd is not None else None)

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
            head = self.remote.head if self.worktree_head is None else self.worktree_head
            return CommandResult(argv=argv, returncode=0, stdout=head + "\n", stderr="")
        if rest[0] == "rev-parse":
            return CommandResult(argv=argv, returncode=0, stdout=self.remote.head + "\n", stderr="")
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

    # -- assertions -------------------------------------------------------
    def git_subcommands(self, repo_path: Path) -> list[str]:
        target = str(Path(repo_path).resolve())
        return [call.argv[3] for call in self.calls if call.argv[0] == "git" and call.argv[2] == target]


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
) -> RunConfig:
    payload: dict[str, object] = {
        "schema_version": 1,
        "repo": "example/repo",
        "pr": 7,
        "branch": branch,
        "base": "main",
        "source_repo": str(source_repo),
        "worktree_root": str(tmp / "worktrees"),
        "state_file": state_file or str(tmp / "state.json"),
        "lock_file": lock_file or str(tmp / "run.lock"),
        "visual_qa_required": visual_qa_required,
        "gates": list(gates),
        "reviewers": [
            {"name": "A", "argv": ["lane-reviewer-A", "--head", "{head}", "--repo", "{repo}"]},
            {"name": "B", "argv": ["lane-reviewer-B", "--head", "{head}", "--pr", "{pr}"]},
        ],
        "builder": {
            "argv": ["lane-builder", "--blockers", "{blockers_file}", "--mode", "{mode}", "--head", "{head}"],
            "signature": SIGNATURE,
            "comment_author": comment_author,
        },
    }
    if branch is None:
        payload.pop("branch")
    return RunConfig.from_mapping(payload, base_dir=tmp)


def make_source_repo(tmp: Path) -> Path:
    """A directory that looks enough like a checkout for :class:`SourceRepo`."""
    path = tmp / "clone"
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
    return path.resolve()
