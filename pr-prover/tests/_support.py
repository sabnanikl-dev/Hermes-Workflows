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
from pr_prover.github import Comment, PullRequest, Review
from pr_prover.identities import IdentityFacts
from pr_prover.launchers import LaunchBroker
from pr_prover.prompts import review_tag

HEAD_A = "a" * 40
HEAD_B = "b" * 40
HEAD_C = "c" * 40
SIGNATURE = "Fixed by: Claude Code via Hermes orchestration"
BRANCH = "feat/example"
BUILDER_LOGIN = "sabnanikl-dev"
REVIEWER_LOGIN = "karanagent1"
BUILDER_TOKEN = "ghp_" + "b" * 36
REVIEWER_TOKEN = "ghp_" + "r" * 36


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


def review_body(role: str, head: str, *, repo: str = "example/repo", pr: int = 7) -> str:
    """A reviewer artifact whose exact first line is the binding tag."""
    return f"{review_tag(repo=repo, pr=pr, role=role, head=head)}\n\nLooks fine to me.\n"


# -- fakes ----------------------------------------------------------------
@dataclass
class FakeRemote:
    """The remote branch head plus the PR conversation, in one place."""

    head: str = HEAD_A
    branch: str = BRANCH
    base: str = "main"
    number: int = 7
    state: str = "OPEN"
    is_draft: bool = True
    comments: list[Comment] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    _next_comment_id: int = 1
    _next_review_id: int = 1

    def push(self, head: str, *, comment: str | None = None, author: str = BUILDER_LOGIN) -> None:
        self.head = head
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

    def review(
        self,
        body: str,
        *,
        head: str,
        author: str = REVIEWER_LOGIN,
        state: str = "COMMENTED",
    ) -> Review:
        """Append a submitted review with a fresh id, bound to the commit it reviewed."""
        posted = Review(
            identifier=f"PRR_review{self._next_review_id}",
            author=author,
            body=body,
            commit_oid=head,
            state=state,
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

    def reviews(self, repo: str, number: int) -> tuple[Review, ...]:
        self.review_calls += 1
        return tuple(self.remote.reviews)


class FakeVerifier:
    """Reports whatever GitHub is pretending this credential resolves to."""

    def __init__(
        self,
        logins: Mapping[str, str] | None = None,
        permissions: Mapping[str, Mapping[str, bool]] | None = None,
    ) -> None:
        self.logins = dict(logins or {BUILDER_TOKEN: BUILDER_LOGIN, REVIEWER_TOKEN: REVIEWER_LOGIN})
        self.permissions = dict(
            permissions
            or {
                BUILDER_LOGIN: {"pull": True, "push": True, "maintain": False, "admin": False},
                REVIEWER_LOGIN: {"pull": True, "push": False, "maintain": False, "admin": False},
            }
        )
        self.calls: list[dict[str, str]] = []

    def facts(self, env: Mapping[str, str], *, repo: str) -> IdentityFacts:
        token = env.get("GH_TOKEN", "")
        self.calls.append({"repo": repo, "token_present": str(bool(token))})
        login = self.logins.get(token, "somebody-else")
        return IdentityFacts(login=login, permissions=self.permissions.get(login, {"pull": True}))


@dataclass(frozen=True)
class Call:
    argv: tuple[str, ...]
    cwd: str | None
    env: Mapping[str, str] | None = None


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
        # Porcelain status per worktree kind. A worktree is a checkout of one
        # commit, so an attempt worktree and a reviewer worktree are different
        # trees and answer separately — which is the whole point of giving each
        # reviewer its own.
        self.worktree_status = ""
        self.reviewer_status = ""
        self.fetch_failures = 0
        # The commit each worktree was created at. A worktree does not follow
        # the remote, so `rev-parse HEAD` inside one must not answer with it.
        self.worktree_heads: dict[str, str] = {}

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        checked = validate_argv(argv)
        self.calls.append(
            Call(
                argv=checked,
                cwd=str(cwd) if cwd is not None else None,
                env=dict(env) if env is not None else None,
            )
        )
        if checked[0] == "git":
            return self._git(checked)
        return self.script(checked, str(cwd) if cwd is not None else None)

    # -- git --------------------------------------------------------------
    def _git(self, argv: tuple[str, ...]) -> CommandResult:
        if argv[1] != "-C":
            raise AssertionError(f"git call is not pinned to a directory: {list(argv)}")
        target = str(Path(argv[2]).resolve())
        rest = argv[3:]
        if rest[0] == "fetch":
            if self.fetch_failures:
                self.fetch_failures -= 1
                return CommandResult(argv=argv, returncode=1, stdout="", stderr="fetch refused")
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "rev-parse":
            head = self.worktree_heads.get(target, self.remote.head)
            return CommandResult(argv=argv, returncode=0, stdout=head + "\n", stderr="")
        if rest[0] == "worktree" and rest[1] == "add":
            path = Path(rest[3])
            path.mkdir(parents=True, exist_ok=False)
            (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
            self.worktree_heads[str(path.resolve())] = rest[4]
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "worktree" and rest[1] == "remove":
            path = Path(rest[3])
            self.worktree_heads.pop(str(path.resolve()), None)
            shutil.rmtree(path, ignore_errors=True)
            return CommandResult(argv=argv, returncode=0, stdout="", stderr="")
        if rest[0] == "status":
            dirty = self.reviewer_status if "-review-" in Path(target).name else self.worktree_status
            return CommandResult(argv=argv, returncode=0, stdout=dirty, stderr="")
        raise AssertionError(f"unexpected git call: {list(argv)}")

    # -- assertions -------------------------------------------------------
    def git_subcommands(self, repo_path: Path) -> list[str]:
        target = str(Path(repo_path).resolve())
        return [call.argv[3] for call in self.calls if call.argv[0] == "git" and call.argv[2] == target]


def parent_env(**extra: str) -> dict[str, str]:
    """A parent environment holding both scoped credentials and a lot of authority."""
    env = {
        "HOME": "/tmp/pr-prover-home",
        "PATH": "/usr/bin:/bin",
        "LANG": "en_GB.UTF-8",
        "PR_PROVER_BUILDER_TOKEN": BUILDER_TOKEN,
        "PR_PROVER_REVIEWER_TOKEN": REVIEWER_TOKEN,
        # Everything below must never reach a child.
        "GH_TOKEN": "ghp_" + "0" * 36,
        "GITHUB_TOKEN": "ghp_" + "1" * 36,
        "KARAN_APPROVAL_TOKEN": "approve-" + "2" * 32,
        "JMD_DEPLOY_KEY": "jmd-" + "3" * 32,
        "VERCEL_TOKEN": "vercel-" + "4" * 32,
        "SANITY_WRITE_TOKEN": "sanity-" + "5" * 32,
        "AWS_SECRET_ACCESS_KEY": "aws-" + "6" * 32,
        "N8N_API_KEY": "n8n-" + "7" * 32,
        "ANTHROPIC_API_KEY": "sk-ant-" + "8" * 32,
        "SSH_AUTH_SOCK": "/private/tmp/ssh-agent.sock",
        "STRIPE_SECRET": "sk_live_" + "9" * 24,
    }
    env.update(extra)
    return env


FORBIDDEN_VALUES = tuple(
    value
    for name, value in parent_env().items()
    if name not in {"HOME", "PATH", "LANG", "PR_PROVER_BUILDER_TOKEN", "PR_PROVER_REVIEWER_TOKEN"}
)


def make_broker(
    config: RunConfig,
    runner: object,
    *,
    env: Mapping[str, str] | None = None,
    verifier: object | None = None,
    scratch_root: Path | None = None,
) -> LaunchBroker:
    return LaunchBroker(
        runner=runner,
        policy=config.launch.policy,
        identities=config.launch.identities,
        verifier=FakeVerifier() if verifier is None else verifier,
        parent_env=parent_env() if env is None else env,
        worktree_root=config.worktree_root,
        scratch_root=scratch_root,
    )


def make_config(
    tmp: Path,
    *,
    source_repo: Path,
    gates: Sequence[Mapping[str, object]] = (),
    visual_qa_required: bool = False,
    comment_author: str = BUILDER_LOGIN,
    branch: str | None = BRANCH,
    reviewer_login: str = REVIEWER_LOGIN,
) -> RunConfig:
    """A valid run configuration. Every lane is bound to a scoped identity.

    There is no unscoped variant, because there is no unscoped configuration the
    loader will accept any more; :func:`legacy_unscoped_payload` builds the
    rejected shape for the migration tests.
    """
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
    payload["launch"] = {
        "identities": {
            "builder": {
                "login": comment_author,
                "capabilities": ["push-branch", "comment-pr"],
                "token_env": "PR_PROVER_BUILDER_TOKEN",
            },
            "reviewer": {
                "login": reviewer_login,
                "capabilities": ["comment-pr", "review-pr"],
                "token_env": "PR_PROVER_REVIEWER_TOKEN",
            },
        }
    }
    payload["builder"]["identity"] = "builder"  # type: ignore[index]
    for reviewer in payload["reviewers"]:  # type: ignore[attr-defined]
        reviewer["identity"] = "reviewer"
    return RunConfig.from_mapping(payload, base_dir=tmp)


def legacy_unscoped_payload(tmp: Path, *, source_repo: Path) -> dict[str, object]:
    """The pre-PAPI-90 shape: script lanes with no identities at all.

    Kept so the migration refusal is tested against the exact configuration
    operators may still have on disk, rather than against an invented one.
    """
    return {
        "schema_version": 1,
        "repo": "example/repo",
        "pr": 7,
        "branch": BRANCH,
        "base": "main",
        "source_repo": str(source_repo),
        "worktree_root": str(tmp / "worktrees"),
        "state_file": str(tmp / "state.json"),
        "lock_file": str(tmp / "run.lock"),
        "gates": [],
        "reviewers": [
            {"name": "A", "argv": ["lane-reviewer-A", "--head", "{head}"]},
            {"name": "B", "argv": ["lane-reviewer-B", "--head", "{head}"]},
        ],
        "builder": {
            "argv": ["lane-builder", "--head", "{head}"],
            "signature": SIGNATURE,
            "comment_author": BUILDER_LOGIN,
        },
    }


def make_source_repo(tmp: Path) -> Path:
    """A directory that looks enough like a checkout for :class:`SourceRepo`."""
    path = tmp / "clone"
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").write_text("gitdir: fake\n", encoding="utf-8")
    return path.resolve()
